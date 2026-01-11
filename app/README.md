# Documentation Q&A Agent

An AI-powered agent that answers questions about GitHub repository documentation using RAG (Retrieval-Augmented Generation).

## Project Structure

```
app/
├── __init__.py          # Package initialization
├── ingest.py            # Data ingestion and chunking
├── search_tools.py      # Text and vector search implementation
├── search_agent.py      # AI agent with tool calling
├── logs.py              # Conversation logging
├── main.py              # Main application entry point
└── pyproject.toml       # Package dependencies
```

## Features

- **Multiple Chunking Strategies**: Section-based, sliding window, or no chunking
- **Hybrid Search**: Combines text (BM25) and vector (semantic) search
- **AI Agent**: Uses PydanticAI with OpenAI or OpenRouter
- **Conversation Logging**: Tracks all interactions for analysis
- **GitHub Integration**: Automatically downloads and indexes markdown documentation

## Installation

### Option 1: Using the root project (Recommended)

From the project root directory:

```bash
# Install dependencies using uv (if available)
uv sync

# Or using pip
pip install -e .
```

### Option 2: Install app package separately

From the `app/` directory:

```bash
pip install -e .
```

## Configuration

### API Keys

You need either an OpenAI or OpenRouter API key:

**For OpenRouter (Free tier available):**
```bash
export OPENROUTER_API_KEY="your-key-here"
```

**For OpenAI:**
```bash
export OPENAI_API_KEY="your-key-here"
```

## Usage

### Quick Start

Run the main application:

```bash
python -m app.main
```

This will:
1. Download and index the workout-recommendation repository
2. Create text and vector search indexes
3. Initialize the AI agent
4. Run test questions

### Custom Usage

```python
import asyncio
from app import index_data, setup_vector_search, init_agent

async def main():
    # 1. Index documentation
    text_index, docs = index_data(
        repo_owner='your-username',
        repo_name='your-repo',
        chunk_method='sections',
        chunking_params={'level': 2}
    )
    
    # 2. Setup vector search
    vector_index, embedding_model = setup_vector_search(docs)
    
    # 3. Initialize agent
    agent, search_tool = init_agent(
        index=text_index,
        repo_owner='your-username',
        repo_name='your-repo',
        vector_index=vector_index,
        embedding_model=embedding_model,
        use_openrouter=True  # or False for OpenAI
    )
    
    # 4. Ask questions
    result = await agent.run(user_prompt="How do I install this?")
    print(result.output)

asyncio.run(main())
```

### Testing

Run the test script from the project root:

```bash
python test_app.py
```

This will test:
- Data ingestion
- Text search
- Vector search
- Agent initialization (if API keys are configured)

## How It Works

### 1. Data Ingestion ([`ingest.py`](ingest.py:1))

- Downloads markdown files from GitHub repository
- Applies chunking strategy (section-based recommended)
- Creates text search index using MinSearch
- Generates vector embeddings using SentenceTransformer

### 2. Search ([`search_tools.py`](search_tools.py:1))

- **Text Search**: BM25-style keyword matching
- **Vector Search**: Semantic similarity using embeddings
- **Hybrid Search**: Balanced combination of both methods

### 3. AI Agent ([`search_agent.py`](search_agent.py:1))

- Uses PydanticAI framework
- Calls search tool to find relevant documentation
- Generates answers with citations
- Supports OpenAI (gpt-4o-mini) or OpenRouter (gemma-3-27b-it:free)

### 4. Logging ([`logs.py`](logs.py:1))

- Saves all conversations to JSON files
- Tracks queries, responses, and tool usage
- Useful for debugging and analysis

## Configuration Options

### Chunking Methods

From notebook analysis, **section-based chunking (level 2)** performed best:

```python
chunk_method='sections'
chunking_params={'level': 2}
```

Other options:
- `'sliding_window'`: Overlapping text chunks
- `'none'`: Full documents

### Search Methods

- `'text'`: Keyword-based search only
- `'vector'`: Semantic search only
- `'hybrid'`: Balanced combination (recommended)

### Models

**OpenRouter (Free):**
- Model: `google/gemma-3-27b-it:free`
- No cost, rate limited

**OpenAI:**
- Model: `gpt-4o-mini`
- Paid, faster and more reliable

## Troubleshooting

### Import Errors

Make sure dependencies are installed:
```bash
pip install minsearch pydantic-ai sentence-transformers python-frontmatter requests tqdm
```

### API Key Errors

Check that your API key is set:
```bash
echo $OPENROUTER_API_KEY  # or $OPENAI_API_KEY
```

### Memory Issues

If processing large repositories, reduce the number of chunks:
```python
# Use only first N documents for testing
docs = docs[:100]
```

## Development

Based on exploration in [`notebook.ipynb`](../notebook.ipynb:1):

1. **Chunking Analysis**: Section-based (level 2) had best balance of completeness and granularity
2. **Search Comparison**: Hybrid search provides best coverage
3. **Agent Testing**: Verified tool calling works correctly

## License

Part of the AI Agent email course project.
