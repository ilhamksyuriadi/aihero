import os
from typing import Optional, List, Dict, Any
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncOpenAI

from .search_tools import SearchTool


SYSTEM_PROMPT_TEMPLATE = """
You are a helpful assistant that answers questions about documentation.

CRITICAL INSTRUCTIONS:
1. You MUST use the search tool to find information before answering
2. Do NOT describe what you would search for - actually CALL the tool
3. Use the search results to provide accurate answers
4. Always include references by citing the filename
5. Format references as: [FILENAME](https://github.com/{repo_owner}/{repo_name}/blob/main/FILENAME)

Example of CORRECT behavior:
User: "How do I install this?"
Assistant: [CALLS search(query="installation")]
Assistant: "Based on the documentation in INSTALLATION.md, here are the steps..."

You have access to a search tool. USE IT when you need specific information.
"""


def init_agent(
    index, 
    repo_owner: str, 
    repo_name: str,
    vector_index=None,
    embedding_model=None,
    use_openrouter: bool = False,
    openrouter_api_key: Optional[str] = None,
    openrouter_model: str = "google/gemma-3-27b-it:free"
):
    """
    Initialize the search agent.
    
    Args:
        index: Text search index
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        vector_index: Optional VectorSearch object for hybrid search
        embedding_model: Optional embedding model
        use_openrouter: Whether to use OpenRouter (default: False = use OpenAI)
        openrouter_api_key: OpenRouter API key (if using OpenRouter)
        openrouter_model: OpenRouter model name
    
    Returns:
        Tuple of (agent, search_tool)
    """
    # Create search tool
    search_tool = SearchTool(
        index=index, 
        vector_index=vector_index, 
        embedding_model=embedding_model
    )
    
    # Create a wrapper function that the agent can call
    def search(query: str, k: int = 5, method: str = 'hybrid') -> list:
        """
        Search the documentation for specific information.
        
        This function searches through all available documentation chunks to find relevant information.
        
        Args:
            query (str): The search query to use. Be specific with keywords.
                        Examples: "installation", "API endpoints", "machine learning model",
                        "docker deployment", "dataset source", "how to run tests"
            k (int): Number of results to return (default: 5)
            method (str): Search method - 'text', 'vector', or 'hybrid' (default: 'hybrid')
        
        Returns:
            list: A list of search results, where each result contains:
                - 'header': The documentation section header
                - 'chunk': The relevant content from that section
                - 'filename': The source filename
        
        Example:
            >>> results = search(query="installation", k=3)
            >>> print(f"Found {len(results)} installation-related sections")
        """
        print(f"🔍 Searching for: '{query}'")
        
        results = search_tool.search(query=query, k=k, method=method)
        
        # Format results for the agent
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append({
                'number': i,
                'section': r.get('header', 'No section'),
                'content': r.get('chunk', '')[:400],  # Limit content length
                'file': r.get('filename', '').split('/')[-1]
            })
        
        print(f"📊 Found {len(formatted)} results")
        return formatted
    
    # Format system prompt
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        repo_owner=repo_owner, 
        repo_name=repo_name
    )
    
    # Configure model
    if use_openrouter:
        if not openrouter_api_key:
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                raise ValueError("OpenRouter API key not provided and not in environment variables")
        
        # Create OpenRouter client
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        
        # Create provider and model
        provider = OpenAIProvider(openai_client=client)
        model = OpenAIChatModel(
            model_name=openrouter_model,
            provider=provider
        )
    else:
        # Use standard OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        client = AsyncOpenAI(api_key=openai_api_key)
        provider = OpenAIProvider(openai_client=client)
        model = OpenAIChatModel(
            model_name="gpt-4o-mini",
            provider=provider
        )
    
    # Create agent
    agent = Agent(
        name="documentation_assistant",
        instructions=system_prompt,
        tools=[search],  # Use the wrapper function
        model=model,
        retries=1
    )
    
    return agent, search_tool


# Simple synchronous wrapper for convenience
def create_agent_sync(*args, **kwargs):
    """
    Create agent for synchronous use.
    """
    agent, search_tool = init_agent(*args, **kwargs)
    return agent, search_tool
