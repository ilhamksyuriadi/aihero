"""
Simple test script to verify the app works correctly.
Run this from the project root directory.
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ingest import index_data
from app.search_tools import setup_vector_search
from app.search_agent import init_agent


async def test_basic_functionality():
    """Test basic functionality of the app."""
    
    print("\n" + "="*60)
    print("TESTING DOCUMENTATION Q&A AGENT")
    print("="*60)
    
    # Test 1: Data ingestion
    print("\n[TEST 1] Data Ingestion")
    print("-" * 40)
    try:
        text_index, docs = index_data(
            repo_owner='ilhamksyuriadi',
            repo_name='workout-recommendation',
            filter=None,
            chunk_method='sections',
            chunking_params={'level': 2}
        )
        print(f"✅ Successfully indexed {len(docs)} document chunks")
        
        # Check chunk structure
        if docs:
            sample = docs[0]
            print(f"✅ Sample chunk has fields: {list(sample.keys())}")
            assert 'chunk' in sample, "Missing 'chunk' field"
            assert 'header' in sample, "Missing 'header' field"
            print("✅ Chunk structure is correct")
    except Exception as e:
        print(f"❌ Data ingestion failed: {e}")
        return False
    
    # Test 2: Vector search setup
    print("\n[TEST 2] Vector Search Setup")
    print("-" * 40)
    try:
        vector_index, embedding_model = setup_vector_search(
            chunks=docs[:10],  # Use only 10 chunks for quick test
            model_name='multi-qa-distilbert-cos-v1'
        )
        print("✅ Vector search index created successfully")
    except Exception as e:
        print(f"❌ Vector search setup failed: {e}")
        return False
    
    # Test 3: Text search
    print("\n[TEST 3] Text Search")
    print("-" * 40)
    try:
        results = text_index.search("installation", num_results=3)
        print(f"✅ Text search returned {len(results)} results")
        if results:
            print(f"   First result: {results[0].get('header', 'No header')}")
    except Exception as e:
        print(f"❌ Text search failed: {e}")
        return False
    
    # Test 4: Vector search
    print("\n[TEST 4] Vector Search")
    print("-" * 40)
    try:
        query_embedding = embedding_model.encode("how to install")
        results = vector_index.search(query_embedding, num_results=3)
        print(f"✅ Vector search returned {len(results)} results")
        if results:
            print(f"   First result: {results[0].get('header', 'No header')}")
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return False
    
    # Test 5: Agent initialization (without API call)
    print("\n[TEST 5] Agent Initialization")
    print("-" * 40)
    try:
        # Check if API key is available
        import os
        has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        
        if not (has_openrouter or has_openai):
            print("⚠️  No API keys found (OPENROUTER_API_KEY or OPENAI_API_KEY)")
            print("   Skipping agent initialization test")
        else:
            agent, search_tool = init_agent(
                index=text_index,
                repo_owner='ilhamksyuriadi',
                repo_name='workout-recommendation',
                vector_index=vector_index,
                embedding_model=embedding_model,
                use_openrouter=has_openrouter
            )
            print("✅ Agent initialized successfully")
            
            # Test search tool
            print("\n[TEST 6] Search Tool")
            print("-" * 40)
            results = search_tool.search("installation", k=2, method='text')
            print(f"✅ Search tool returned {len(results)} results")
            
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        print(f"   This is expected if no API keys are configured")
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    sys.exit(0 if success else 1)
