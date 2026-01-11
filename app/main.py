"""
Main application file for the Documentation Q&A Agent.

This module ties together all components:
- Data ingestion (ingest.py)
- Search tools (search_tools.py)
- Agent (search_agent.py)
- Logging (logs.py)
"""

import asyncio
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
print(f"🔑 Loading .env from: {env_path}")
print(f"🔑 API Key found: {'Yes' if os.getenv('OPENROUTER_API_KEY') else 'No'}")

from .ingest import index_data, create_vector_index_from_docs
from .search_tools import setup_vector_search
from .search_agent import init_agent
from .logs import ConversationLogger


# Configuration
REPO_OWNER = "ilhamksyuriadi"
REPO_NAME = "workout-recommendation"
CHUNK_METHOD = "sections"  # Best method from notebook analysis
CHUNK_LEVEL = 2  # Section level 2 was best in notebook


def setup_indexes(repo_owner: str = REPO_OWNER, 
                  repo_name: str = REPO_NAME,
                  chunk_method: str = CHUNK_METHOD,
                  use_cache: bool = True):
    """
    Setup text and vector indexes for the documentation.
    
    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        chunk_method: Chunking method ('sections', 'sliding_window', or 'none')
        use_cache: Whether to use cached indexes (not implemented yet)
    
    Returns:
        Tuple of (text_index, vector_index, embedding_model, docs)
    """
    print("\n" + "="*60)
    print("SETTING UP INDEXES")
    print("="*60)
    
    # Step 1: Index the data (text search)
    print(f"\n1. Indexing {repo_owner}/{repo_name}...")
    text_index, docs = index_data(
        repo_owner=repo_owner,
        repo_name=repo_name,
        filter=None,
        chunk_method=chunk_method,
        chunking_params={'level': CHUNK_LEVEL} if chunk_method == 'sections' else None
    )
    print(f"✅ Text index created with {len(docs)} chunks")
    
    # Step 2: Create vector search index
    print("\n2. Creating vector embeddings...")
    vector_index, embedding_model = setup_vector_search(
        chunks=docs,
        model_name='multi-qa-distilbert-cos-v1'  # Same as notebook
    )
    print(f"✅ Vector index created")
    
    return text_index, vector_index, embedding_model, docs


def setup_agent(text_index, vector_index, embedding_model,
                repo_owner: str = REPO_OWNER,
                repo_name: str = REPO_NAME,
                use_openrouter: bool = True):
    """
    Setup the documentation Q&A agent.
    
    Args:
        text_index: Text search index
        vector_index: Vector search index
        embedding_model: Embedding model
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        use_openrouter: Whether to use OpenRouter (True) or OpenAI (False)
    
    Returns:
        Tuple of (agent, search_tool)
    """
    print("\n" + "="*60)
    print("SETTING UP AGENT")
    print("="*60)
    
    # Get API key
    if use_openrouter:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        print("✅ Using OpenRouter")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        print("✅ Using OpenAI")
    
    # Initialize agent
    agent, search_tool = init_agent(
        index=text_index,
        repo_owner=repo_owner,
        repo_name=repo_name,
        vector_index=vector_index,
        embedding_model=embedding_model,
        use_openrouter=use_openrouter,
        openrouter_api_key=api_key if use_openrouter else None,
        openrouter_model="google/gemma-3-27b-it:free"
    )
    
    print("✅ Agent initialized")
    return agent, search_tool


async def ask_question(agent, question: str, logger: ConversationLogger = None):
    """
    Ask a question to the agent and optionally log the interaction.
    
    Args:
        agent: The initialized agent
        question: The question to ask
        logger: Optional logger to save the conversation
    
    Returns:
        The agent's response
    """
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")
    
    # Run the agent
    result = await agent.run(user_prompt=question)
    
    # Print response
    print(f"Answer: {result.output}\n")
    
    # Log if logger provided
    if logger:
        logger.log_interaction(
            agent=agent,
            messages=result.new_messages(),
            query=question,
            response=result.output,
            source="user"
        )
    
    return result


async def interactive_mode(agent, logger: ConversationLogger = None):
    """
    Run the agent in interactive mode where user can ask multiple questions.
    
    Args:
        agent: The initialized agent
        logger: Optional logger to save conversations
    """
    print("\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    print("Ask questions about the documentation. Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            question = input("You: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            await ask_question(agent, question, logger)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """
    Main entry point for the application.
    """
    print("\n" + "="*60)
    print("DOCUMENTATION Q&A AGENT")
    print("="*60)
    
    # Setup indexes
    text_index, vector_index, embedding_model, docs = setup_indexes()
    
    # Setup agent
    agent, search_tool = setup_agent(text_index, vector_index, embedding_model)
    
    # Setup logger
    logger = ConversationLogger()
    
    # Test with a few questions
    test_questions = [
        "How do I install this project?",
        "What dataset does this use?",
        "How do I run the API?"
    ]
    
    print("\n" + "="*60)
    print("TESTING WITH SAMPLE QUESTIONS")
    print("="*60)
    
    for question in test_questions:
        await ask_question(agent, question, logger)
    
    # Optionally start interactive mode
    # Uncomment the line below to enable interactive mode
    # await interactive_mode(agent, logger)
    
    print("\n" + "="*60)
    print("DONE!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
