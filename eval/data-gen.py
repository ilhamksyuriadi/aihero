"""
Synthetic Question Generation for Evaluation

This script generates synthetic questions for evaluating the documentation assistant agent.
It uses the search functionality to understand the documentation and generate relevant questions.
"""

import json
import asyncio
from pathlib import Path
from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncOpenAI
import os

# Import the search function from the app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import setup_indexes, setup_agent

class QuestionSet(BaseModel):
    questions: List[str]
    categories: List[str]

# Setup OpenRouter model (same as main agent)
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key= os.getenv("OPENROUTER_API_KEY"),  # Add your API key
)

provider = OpenAIProvider(openai_client=client)

question_gen_model = OpenAIChatModel(
    model_name="google/gemma-3-27b-it:free",
    provider=provider
)

# Question generation agent
question_generator = Agent(
    name='question_generator',
    model=question_gen_model,
    instructions="""
    You are an expert at generating evaluation questions for AI agents.

    Based on the documentation search results, generate diverse, realistic questions that users might ask about this workout recommendation repository.

    Generate questions across different categories:
    - Installation and setup
    - Configuration
    - Usage and running the app
    - Data and datasets
    - Architecture and code structure
    - Troubleshooting
    - API endpoints
    - Deployment

    Make questions specific and technical where appropriate, but also include general questions.

    Return a list of 10-15 diverse questions.
    """,
    output_type=QuestionSet
)

async def generate_synthetic_questions(num_questions: int = 15) -> List[str]:
    """
    Generate synthetic questions for evaluation

    Args:
        num_questions: Number of questions to generate

    Returns:
        List of synthetic questions
    """

    # Setup the search infrastructure
    print("Setting up search indexes for question generation...")
    text_index, vector_index, embedding_model, docs = setup_indexes()

    # Create a search function
    def search_docs(query: str) -> list:
        """Search function for getting documentation context"""
        from app.search_tools import SearchTool

        search_tool = SearchTool(
            index=text_index,
            vector_index=vector_index,
            embedding_model=embedding_model
        )

        results = search_tool.search(query=query, k=3, method='hybrid')

        # Format results
        formatted = []
        for r in results:
            formatted.append({
                'section': r.get('header', 'No section'),
                'content': r.get('chunk', '')[:200],
                'file': r.get('filename', '').split('/')[-1]
            })

        return formatted

    # Get some sample search results to understand the documentation
    sample_queries = ["installation", "API", "dataset", "running", "configuration"]
    search_results = {}

    for query in sample_queries:
        try:
            results = search_docs(query)
            search_results[query] = results
        except Exception as e:
            print(f"Error searching for {query}: {e}")
            search_results[query] = []

    # Create context from search results
    context = "Documentation Overview:\n"
    for query, results in search_results.items():
        context += f"\n{query.upper()}:\n"
        for result in results:
            context += f"- {result['section']}: {result['content'][:100]}...\n"

    # Generate questions using the agent
    prompt = f"""
    Based on this documentation overview, generate {num_questions} diverse questions that users might ask:

    {context}

    Focus on questions that would require searching the documentation to answer properly.
    Include both simple and complex questions across different categories like installation, usage, configuration, etc.
    """

    result = await question_generator.run(prompt)

    questions = result.output.questions[:num_questions]  # Limit to requested number

    return questions

async def save_questions_to_file(questions: List[str], filename: str = "synthetic_questions.json"):
    """
    Save generated questions to a JSON file

    Args:
        questions: List of questions to save
        filename: Output filename
    """

    data = {
        "generated_at": "2026-01-11T03:58:47.378Z",  # Current time
        "num_questions": len(questions),
        "questions": questions
    }

    filepath = Path(__file__).parent / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(questions)} questions to {filepath}")

async def main():
    """Main function to generate and save synthetic questions"""

    print("Generating synthetic questions for evaluation...")

    # Generate questions
    questions = await generate_synthetic_questions(15)

    print(f"Generated {len(questions)} questions:")
    for i, q in enumerate(questions, 1):
        print(f"{i:2d}. {q}")

    # Save to file
    await save_questions_to_file(questions)

    print("\nQuestion generation complete!")

if __name__ == "__main__":
    asyncio.run(main())