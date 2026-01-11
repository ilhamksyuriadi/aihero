from typing import List, Dict, Any, Optional
from minsearch import Index, VectorSearch
from sentence_transformers import SentenceTransformer
import numpy as np


class SearchTool:
    def __init__(
        self, 
        index: Index, 
        vector_index: Optional[VectorSearch] = None,
        embedding_model: Optional[SentenceTransformer] = None,
    ):
        """
        Initialize search tool with text index and optional vector search.
        
        Args:
            index: MinSearch text index
            vector_index: VectorSearch object from minsearch
            embedding_model: SentenceTransformer model for embeddings
        """
        self.index = index
        self.vector_index = vector_index
        self.embedding_model = embedding_model
    
    def text_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform text-based search only.
        """
        return self.index.search(query, num_results=k)
    
    def vector_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform vector-based search using SentenceTransformer.
        """
        if not self.embedding_model or not self.vector_index:
            print("⚠️ Vector search not available (no embedding model or vector index)")
            return []
        
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query)
            
            # Use VectorSearch.search method
            results = self.vector_index.search(query_embedding, num_results=k)
            
            print(f"🔍 Vector search found {len(results)} results")
            return results
            
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            return []
    
    def hybrid_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining text and vector results.
        Balanced approach: takes equal from both methods.
        
        Args:
            query: Search query
            k: Number of results to return
        """
        # Get results from both methods
        text_results = self.text_search(query, k=k*2)
        vector_results = self.vector_search(query, k=k*2)
        
        print(f"📊 Hybrid search: {len(text_results)} text, {len(vector_results)} vector results")
        
        # If no vector results, return text results
        if not vector_results:
            return text_results[:k]
        
        # Calculate how many to take from each (balanced)
        from_each = (k + 1) // 2  # e.g., 3 for k=5, 2 for k=3
        
        combined_results = []
        seen_chunks = set()
        
        # Function to add result with deduplication
        def add_result(result, source):
            chunk_id = result.get('chunk_id', '') or result.get('chunk', '')[:100]
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                result = result.copy()  # Avoid modifying original
                result['_source'] = source
                combined_results.append(result)
                return True
            return False
        
        # Interleave: text, vector, text, vector...
        text_added = 0
        vector_added = 0
        max_attempts = max(len(text_results), len(vector_results))
        
        for i in range(max_attempts):
            # Try to add text result
            if text_added < from_each and i < len(text_results):
                if add_result(text_results[i], 'text'):
                    text_added += 1
            
            # Try to add vector result
            if vector_added < from_each and i < len(vector_results):
                if add_result(vector_results[i], 'vector'):
                    vector_added += 1
            
            # Stop if we have enough
            if len(combined_results) >= k:
                break
        
        # If still need more, take best remaining
        if len(combined_results) < k:
            all_results = text_results + vector_results
            for result in all_results:
                if len(combined_results) >= k:
                    break
                add_result(result, 'mixed')
        
        return combined_results[:k]
    
    def search(self, query: str, k: int = 5, method: str = 'hybrid') -> List[Dict[str, Any]]:
        """
        Main search method with configurable search type.
        
        Args:
            query: Search query
            k: Number of results
            method: 'text', 'vector', or 'hybrid'
        
        Returns:
            List of search results
        """
        print(f"🔍 Performing {method} search for: '{query}'")
        
        if method == 'vector':
            return self.vector_search(query, k=k)
        elif method == 'hybrid':
            return self.hybrid_search(query, k=k)
        else:  # 'text' (default)
            return self.text_search(query, k=k)
    
    def __call__(self, query: str, k: int = 5, method: str = 'hybrid') -> str:
        """
        Format search results as a string for the agent.
        
        Args:
            query: Search query
            k: Number of results
            method: Search method
        
        Returns:
            Formatted string of search results
        """
        results = self.search(query, k=k, method=method)
        
        if not results:
            return "No results found."
        
        formatted = []
        
        for i, result in enumerate(results, 1):
            filename = result.get('filename', 'Unknown')
            header = result.get('header', 'No section')
            content = result.get('chunk', '')
            chunk_type = result.get('chunk_type', '')
            
            # Truncate content for readability
            content_preview = content[:300] + "..." if len(content) > 300 else content
            
            formatted.append(
                f"\n--- Result {i} ({chunk_type}) ---\n"
                f"📁 File: {filename}\n"
                f"📑 Section: {header}\n"
                f"📝 Content: {content_preview}\n"
            )
        
        result_str = "\n".join(formatted)
        print(f"📊 Found {len(results)} results")
        return result_str


# Helper function to setup vector search (matching notebook approach)
def setup_vector_search(chunks: List[Dict[str, Any]], model_name: str = 'multi-qa-distilbert-cos-v1'):
    """
    Setup vector search with embeddings - matches notebook implementation.
    
    Args:
        chunks: List of document chunks
        model_name: SentenceTransformer model name
    
    Returns:
        Tuple of (vector_index, embedding_model)
    """
    from tqdm.auto import tqdm
    
    # Load embedding model
    print(f"Loading embedding model: {model_name}")
    embedding_model = SentenceTransformer(model_name)
    
    # Create embeddings for all chunks
    print("Creating embeddings...")
    embeddings = []
    
    for chunk in tqdm(chunks):
        # Combine relevant fields for embedding
        text = chunk.get('chunk', '')
        
        # Add header for context (if exists)
        if 'header' in chunk:
            text = chunk['header'] + " " + text
        
        # Optionally add filename for more context
        if 'filename' in chunk:
            # Extract just the filename, not full path
            filename = chunk['filename'].split('/')[-1]
            text = filename + " " + text
            
        v = embedding_model.encode(text)
        embeddings.append(v)
    
    embeddings = np.array(embeddings)
    
    # Create vector search index
    vector_index = VectorSearch()
    vector_index.fit(embeddings, chunks)
    
    print(f"✅ Vector search index created with {len(embeddings)} embeddings")
    return vector_index, embedding_model
