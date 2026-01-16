# Documentation Q&A Agent

> An AI-powered agent that answers questions about GitHub repository documentation using RAG (Retrieval-Augmented Generation)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.52+-red.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

This project solves the problem of **finding information in large documentation repositories**. Instead of manually searching through multiple markdown files, you can ask natural language questions and get AI-powered answers with accurate citations.

### Live url
https://repo-rag-faq.streamlit.app/
_*notes: probably not working in the future because of the limitation of free api key_

### Why It's Useful

- 🔍 **Smart Search**: Combines text (BM25) and semantic (vector) search for better results
- 🤖 **AI-Powered**: Uses PydanticAI with OpenAI or OpenRouter for intelligent answers
- 📚 **Source Citations**: Every answer includes links to the original documentation
- 💬 **Two Interfaces**: Command-line tool and beautiful Streamlit web UI
- 📝 **Conversation Logging**: All interactions saved for analysis

### How It Works

```
GitHub Repo → Download Docs → Chunk & Index → AI Agent → Answer with Citations
```

1. Downloads markdown files from any GitHub repository
2. Chunks content using section-based splitting (best from notebook analysis)
3. Creates text and vector search indexes
4. AI agent searches and generates answers
5. Provides citations with GitHub links

### Showcase
1. Initializing Agent
![rag-faq-initialize-agent](https://github.com/user-attachments/assets/6e830351-e0bc-4c4e-bcbd-06e7a0eeb7e5)

2. Question Example
![rag-faq-question](https://github.com/user-attachments/assets/631efdcf-0de7-4a1b-85ee-bb54e5568bdf)

---

## Installation

### Prerequisites

- Python 3.12 or higher
- `uv` package manager (recommended) or `pip`
- OpenRouter or OpenAI API key

### Step 1: Clone the Repository

```bash
git clone https://github.com/ilhamksyuriadi/aihero.git
cd course
```

### Step 2: Install Dependencies

Using `uv` (recommended):

```bash
uv sync
```

Using `pip`:

```bash
pip install -e .
```

### Step 3: Set Up API Key

Create a `.env` file in the project root:

```bash
# Copy the example
copy .env.example .env  # Windows
# or
cp .env.example .env    # Linux/Mac
```

Edit `.env` and add your API key:

```env
# OpenRouter (Free tier available)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# OR OpenAI (Paid)
# OPENAI_API_KEY=sk-your-key-here
```

Get your API key:
- **OpenRouter**: https://openrouter.ai/keys (Free tier available)
- **OpenAI**: https://platform.openai.com/api-keys (Paid)

### Step 4: Install dotenv Support

```bash
uv add python-dotenv
```

---

## Usage

### Option 1: Streamlit Web UI (Recommended)

**Start the app:**

```bash
uv run python run_streamlit.py
```

Or directly:

```bash
uv run streamlit run app/streamlit_app.py
```

**Use the app:**

1. Open http://localhost:8501 in your browser
2. Click "🚀 Initialize Agent" in the sidebar
3. Wait 2-3 minutes for setup (first time only)
4. Start asking questions!

**Example questions:**
- "How do I install this project?"
- "What dataset does this use?"
- "How do I run the API?"

### Option 2: Command Line

**Run the CLI app:**

```bash
uv run python -m app.main
```

This will:
- Index the default repository (workout-recommendation)
- Initialize the AI agent
- Run 3 test questions
- Save logs to `logs/` folder

**Customize the repository:**

Edit [`app/main.py`](app/main.py:23) and change:

```python
REPO_OWNER = "your-username"
REPO_NAME = "your-repo"
```

### Configuration Options

**Chunking Methods:**
- `'sections'` - Split by markdown headers (recommended)
- `'sliding_window'` - Overlapping text chunks
- `'none'` - Full documents

**Search Methods:**
- `'hybrid'` - Text + vector search (recommended)
- `'text'` - Keyword-based only
- `'vector'` - Semantic search only

**AI Models:**
- OpenRouter: `google/gemma-3-27b-it:free` (free)
- OpenAI: `gpt-4o-mini` (paid, faster)

---

## Features

### Core Features

- ✅ **GitHub Integration**: Automatically downloads and indexes markdown documentation
- ✅ **Smart Chunking**: Section-based splitting preserves document structure
- ✅ **Hybrid Search**: Combines text and semantic search for best results
- ✅ **AI Agent**: Uses PydanticAI with tool calling for accurate answers
- ✅ **Source Citations**: Every answer includes GitHub links to sources
- ✅ **Conversation Logging**: All interactions saved as JSON

### User Interfaces

- ✅ **Streamlit Web UI**: Beautiful, interactive chat interface
- ✅ **Command Line**: Simple CLI for automation and testing
- ✅ **Flexible Configuration**: Change repositories and settings on the fly

### Technical Features

- ✅ **Vector Embeddings**: SentenceTransformer for semantic search
- ✅ **Text Search**: MinSearch for keyword matching
- ✅ **Async Support**: Fast, non-blocking operations
- ✅ **Error Handling**: Graceful fallbacks and clear error messages

### Roadmap

- [ ] Cache embeddings for faster startup
- [ ] Support for multiple repositories simultaneously
- [ ] Export conversations to markdown
- [ ] Custom chunking strategies
- [ ] API endpoint for integration

---

## Evaluation

We evaluate the agent using the following criteria:

- **instructions_follow**: The agent followed the user's instructions
- **instructions_avoid**: The agent avoided doing things it was told not to do
- **answer_relevant**: The response directly addresses the user's question
- **answer_clear**: The answer is clear and correct
- **answer_citations**: The response includes proper citations or sources when required
- **completeness**: The response is complete and covers all key aspects of the request
- **tool_call_search**: Is the search tool invoked?

We do this in two steps:

1. **Generate synthetic questions** (see [`eval/data-gen.py`](eval/data-gen.py))
2. **Run our agent on the generated questions and check the criteria** (see [`eval/evaluations.py`](eval/evaluations.py))

### Evaluation Results

**Latest Evaluation:** `logs/evaluation_log_20260114_221716.json`

- **Total Questions:** 15
- **Average Score:** 5.0/5.0 ✅
- **Tool Usage Rate:** 100.0% ✅

**Criteria Performance:**
- **instructions_follow:** 100.0% ✅
- **instructions_avoid:** 100.0% ✅
- **answer_relevant:** 100.0% ✅
- **answer_clear:** 100.0% ✅
- **answer_citations:** 100.0% ✅
- **completeness:** 100.0% ✅
- **tool_call_search:** 100.0% ✅

**Conclusion:** The agent achieves perfect scores across all evaluation criteria, demonstrating excellent performance in answering documentation questions with accurate, complete, and properly cited responses.

### Running Evaluations

```bash
# Generate synthetic questions
cd eval
uv run python data-gen.py

# Run evaluation on the questions
uv run python evaluations.py
```

Results are saved to the `logs/` directory as JSON files for analysis.

---

## Project Structure

```
course/
├── app/                        # Main application package
│   ├── __init__.py            # Package initialization
│   ├── ingest.py              # Data ingestion and chunking
│   ├── search_tools.py        # Search implementation
│   ├── search_agent.py        # AI agent with tool calling
│   ├── logs.py                # Conversation logging
│   ├── main.py                # CLI entry point
│   └── streamlit_app.py       # Web UI
├── eval/                       # Evaluation scripts
│   ├── data-gen.py            # Generate synthetic questions
│   └── evaluations.py         # Run evaluation on agent
├── logs/                       # Conversation logs (JSON)
├── .env                        # API keys (not in git)
├── .env.example               # API key template
├── pyproject.toml             # Dependencies
├── run_streamlit.py           # Streamlit launcher
├── test_app.py                # Test suite
├── simple_test.py             # Quick import test
└── README.md                  # This file
```

---

## Tests

### Quick Test (No API Key Required)

```bash
uv run python simple_test.py
```

Tests:
- ✅ Basic imports
- ✅ Dependencies installed
- ✅ Module structure

### Full Test Suite

```bash
uv run python test_app.py
```

Tests:
- ✅ Data ingestion
- ✅ Text search
- ✅ Vector search
- ✅ Agent initialization (requires API key)

### Manual Testing

```bash
# Test CLI app
uv run python -m app.main

# Test Streamlit app
uv run python run_streamlit.py
```

---

## Deployment

### Streamlit Cloud (Free)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Streamlit app"
   git push
   ```

2. **Deploy:**
   - Go to https://streamlit.io/cloud
   - Click "New app"
   - Select your repository
   - Set main file: `app/streamlit_app.py`
   - Add secret: `OPENROUTER_API_KEY = "your-key"`
   - Deploy!

### Other Platforms

- **Heroku**: Use `Procfile` with `web: streamlit run app/streamlit_app.py`
- **Railway**: Auto-detects Streamlit apps
- **Docker**: Create `Dockerfile` with Streamlit
- **AWS/GCP**: Use container services

---

## FAQ / Troubleshooting

### Common Issues

**Q: "ModuleNotFoundError: No module named 'app'"**

A: Make sure you're running from the project root:
```bash
cd "path/to/course"
uv run python -m app.main
```

**Q: "API key not found"**

A: Check your `.env` file:
```bash
# Windows
type .env

# Linux/Mac
cat .env
```

Should show: `OPENROUTER_API_KEY=sk-or-v1-...`

**Q: "Program seems stuck"**

A: First run takes 30-60 seconds to load sentence-transformers. This is normal! Wait 2 minutes before canceling.

**Q: "Import errors"**

A: Reinstall dependencies:
```bash
uv sync
```

### Performance Tips

- **First run is slow** (2-3 minutes): Downloads models and creates embeddings
- **Subsequent runs are faster** (~10 seconds): Models are cached
- **Each question takes 5-10 seconds**: Normal for AI processing

---

## Credits / Acknowledgments

### Built With

- **[PydanticAI](https://ai.pydantic.dev/)** - AI agent framework
- **[Streamlit](https://streamlit.io/)** - Web UI framework
- **[SentenceTransformers](https://www.sbert.net/)** - Vector embeddings
- **[MinSearch](https://github.com/alexeygrigorev/minsearch)** - Text search
- **[OpenRouter](https://openrouter.ai/)** - Free AI API access
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager

### Inspiration

- Based on exploration in [`notebook.ipynb`](notebook.ipynb)
- Part of the AI Agent email course project
- Chunking analysis showed section-based (level 2) performs best
- Hybrid search provides better coverage than text or vector alone

### Contributors

- Ilham Kurnia Syuriadi

---

## Quick Reference

### Essential Commands

```bash
# Install dependencies
uv sync

# Run Streamlit UI
uv run python run_streamlit.py

# Run CLI app
uv run python -m app.main

# Run tests
uv run python test_app.py

# Quick import test
uv run python simple_test.py
```

---

**Made with ❤️ for the AI Agent course**
