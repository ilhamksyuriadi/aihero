import io
import zipfile
import requests
import frontmatter
import re
from sentence_transformers import SentenceTransformer
import numpy as np
from minsearch import Index


def read_repo_data(repo_owner, repo_name):
    """Download and extract markdown files from a GitHub repository."""
    url = f'https://codeload.github.com/{repo_owner}/{repo_name}/zip/refs/heads/main'
    resp = requests.get(url)

    repository_data = []

    zf = zipfile.ZipFile(io.BytesIO(resp.content))

    for file_info in zf.infolist():
        filename = file_info.filename.lower()

        # Only process markdown files
        if not (filename.endswith('.md') or filename.endswith('.mdx')):
            continue

        with zf.open(file_info) as f_in:
            content = f_in.read()
            post = frontmatter.loads(content)
            data = post.to_dict()

            # Extract just the filename without the repo folder prefix
            _, filename_repo = file_info.filename.split('/', maxsplit=1)
            data['filename'] = filename_repo
            repository_data.append(data)

    zf.close()
    print(f"✅ Loaded {len(repository_data)} markdown files from {repo_owner}/{repo_name}")
    return repository_data


def sliding_window(seq, size, step):
    """Create overlapping chunks using sliding window."""
    if size <= 0 or step <= 0:
        raise ValueError("size and step must be positive")

    n = len(seq)
    result = []
    for i in range(0, n, step):
        batch = seq[i:i+size]
        result.append({'start': i, 'content': batch})
        if i + size > n:
            break

    return result


def chunk_documents(docs, size=2000, step=1000):
    """Apply sliding window chunking to documents."""
    chunks = []

    for doc in docs:
        doc_copy = doc.copy()
        doc_content = doc_copy.pop('content')
        doc_chunks = sliding_window(doc_content, size=size, step=step)
        for chunk in doc_chunks:
            chunk.update(doc_copy)
        chunks.extend(doc_chunks)

    return chunks


def split_markdown_by_level(text, level=2, include_content_before_first_header=True):
    """
    Split markdown text by headers at a specific level.
    
    Parameters:
    - text: Markdown text
    - level: Header level to split on (1 for #, 2 for ##, etc.)
    - include_content_before_first_header: Whether to include text before first header
    
    Returns: List of (header, content) tuples
    """
    # Create regex pattern for the specified header level
    header_pattern = r'^(#{' + str(level) + r'} )(.+)$'
    pattern = re.compile(header_pattern, re.MULTILINE)
    
    # Find all header positions
    matches = list(pattern.finditer(text))
    
    if not matches:
        # No headers found at this level
        return [('No Header', text.strip())] if text.strip() else []
    
    sections = []
    
    # Handle content before first header
    first_match = matches[0]
    if include_content_before_first_header and first_match.start() > 0:
        before_content = text[:first_match.start()].strip()
        if before_content:
            sections.append(('Introduction', before_content))
    
    # Process each section
    for i, match in enumerate(matches):
        header_marker = match.group(1)  # e.g., "## "
        header_text = match.group(2)    # e.g., "Installation"
        full_header = header_marker + header_text
        
        # Determine the content for this section
        if i < len(matches) - 1:
            # Content is from after this header to before next header
            next_match = matches[i + 1]
            content = text[match.end():next_match.start()].strip()
        else:
            # Last section: content is from after header to end
            content = text[match.end():].strip()
        
        sections.append((full_header, content))
    
    return sections


def section_chunk_documents(docs, level=2):
    """Apply section-based chunking to documents."""
    all_chunks = []
    
    for doc_idx, doc in enumerate(docs):
        doc_copy = doc.copy()
        doc_content = doc_copy.pop('content')
        
        sections = split_markdown_by_level(doc_content, level=level)
        
        for section_idx, (header, content) in enumerate(sections):
            if not content:
                continue
                
            chunk_info = {
                'chunk_id': f"doc_{doc_idx}_sec_{section_idx}",
                'header': header,
                'chunk': content,  # Using 'chunk' to match notebook
                'chunk_type': f'section_level_{level}',
                'section_index': section_idx,
                'length': len(content),
                'has_header': header != 'No Header' and header != 'Introduction'
            }
            
            chunk_with_metadata = doc_copy.copy()
            chunk_with_metadata.update(chunk_info)
            all_chunks.append(chunk_with_metadata)
    
    print(f"✅ Created {len(all_chunks)} section-based chunks")
    return all_chunks

def create_vector_index_from_docs(docs, model_name='all-MiniLM-L6-v2'):
    """
    Create vector embeddings for documents.
    
    Args:
        docs: List of documents
        model_name: SentenceTransformer model name
    
    Returns:
        Tuple of (vector_index, embedding_model, docs_with_ids)
    """
    print(f"🔄 Creating vector embeddings with {model_name}...")
    
    try:
        # Load embedding model
        embedding_model = SentenceTransformer(model_name)
        
        vector_index = {}
        docs_with_ids = []
        
        for i, doc in enumerate(docs):
            # Create unique ID
            chunk_id = doc.get('chunk_id', f"doc_{i}")
            doc_copy = doc.copy()
            doc_copy['chunk_id'] = chunk_id
            
            # Combine text fields for embedding
            text_parts = []
            if 'chunk' in doc_copy:
                text_parts.append(doc_copy['chunk'])
            if 'header' in doc_copy:
                text_parts.append(doc_copy['header'])
            if 'filename' in doc_copy:
                text_parts.append(doc_copy['filename'])
            
            text_to_embed = " ".join(text_parts)
            
            # Generate embedding
            embedding = embedding_model.encode(text_to_embed)
            vector_index[chunk_id] = embedding
            
            docs_with_ids.append(doc_copy)
        
        print(f"✅ Created {len(vector_index)} vector embeddings")
        return vector_index, embedding_model, docs_with_ids
        
    except Exception as e:
        print(f"❌ Failed to create vector index: {e}")
        return {}, None, []

def index_data(
        repo_owner,
        repo_name,
        filter=None,
        chunk_method='none',  # 'none', 'sliding_window', or 'sections'
        chunking_params=None,
    ):
    """
    Main function to index repository data with different chunking options.
    
    Parameters:
    - repo_owner: GitHub repository owner
    - repo_name: GitHub repository name
    - filter: Optional function to filter documents
    - chunk_method: 'none', 'sliding_window', or 'sections'
    - chunking_params: Parameters for the chunking method
    
    Returns: (index, documents)
    """
    # Load documents from repository
    docs = read_repo_data(repo_owner, repo_name)

    # Apply filter if provided
    if filter is not None:
        docs = [doc for doc in docs if filter(doc)]

    # Apply chunking based on method
    if chunk_method == 'sliding_window':
        if chunking_params is None:
            chunking_params = {'size': 2000, 'step': 1000}
        docs = chunk_documents(docs, **chunking_params)
        text_fields = ["chunk", "filename"]
        
    elif chunk_method == 'sections':
        print("🔄 Applying section-based chunking...")
        if chunking_params is None:
            chunking_params = {'level': 2}
        level = chunking_params.get('level', 2)
        docs = section_chunk_documents(docs, level=level)
        text_fields = ["chunk", "header", "filename"]
        
    else:  # 'none' - no chunking
        text_fields = ["chunk", "filename"]

    # Create and populate the search index
    index = Index(
        text_fields=text_fields,
    )

    index.fit(docs)
    return index, docs  # Return both index and documents


if __name__ == "__main__":
    # Example usage - only runs when script is executed directly
    index, docs = index_data(
        repo_owner='ilhamksyuriadi',
        repo_name='workout-recommendation',
        filter=None,
        chunk_method='sections',
    )
    print(f"✅ Indexed {len(docs)} documents")