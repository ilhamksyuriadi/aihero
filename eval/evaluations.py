"""
Evaluation Logic for Documentation Assistant Agent

This script evaluates the performance of the documentation assistant agent
using synthetic questions and various evaluation criteria.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncOpenAI

# Import the main agent and setup functions
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import setup_indexes, setup_agent

# Setup logging
LOG_DIR = Path('../logs')
LOG_DIR.mkdir(exist_ok=True)

class EvaluationResult(BaseModel):
    """Schema for evaluation results"""
    instructions_follow: int  # 0-1: Did agent follow instructions?
    instructions_avoid: int   # 0-1: Did agent avoid forbidden actions?
    answer_relevant: int      # 0-1: Is answer relevant to question?
    answer_clear: int         # 0-1: Is answer clear?
    answer_citations: int     # 0-1: Does answer include citations/sources?
    completeness: int         # 0-1: Is answer complete?
    tool_call_search: int     # 0-1: Was search tool invoked?

class EvaluationCriteria(BaseModel):
    """Detailed evaluation criteria"""
    instructions_follow: bool
    instructions_avoid: bool
    answer_relevant: bool
    answer_clear: bool
    answer_citations: bool
    completeness: bool
    tool_call_search: bool
    overall_score: int  # 1-5
    reasoning: str

# Setup evaluation model (same as main agent)
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),  # Add your API key
)

provider = OpenAIProvider(openai_client=client)

eval_model = OpenAIChatModel(
    model_name="google/gemma-3-27b-it:free",
    provider=provider
)

# Evaluation agent
evaluation_agent = Agent(
    name='evaluation_agent',
    model=eval_model,
    instructions="""
    You are an expert evaluator of AI agent responses.

    Evaluate the agent's response based on these criteria:

    instructions_follow: The agent followed the user's instructions
    instructions_avoid: The agent avoided doing things it was told not to do
    answer_relevant: The response directly addresses the user's question
    answer_clear: The answer is clear and correct
    answer_citations: The response includes proper citations or sources when required
    completeness: The response is complete and covers all key aspects of the request
    tool_call_search: Is the search tool invoked?

    For each criterion, return 1 if yes, 0 if no.

    Also provide an overall score from 1-5 and brief reasoning.

    The agent should use the search_workout_docs tool when answering questions about the repository.
    """,
    output_type=EvaluationCriteria
)

async def evaluate_single_response(question: str, answer: str, tool_used: bool) -> Dict[str, Any]:
    """
    Evaluate a single question-answer pair

    Args:
        question: The user's question
        answer: The agent's response
        tool_used: Whether the search tool was actually used

    Returns:
        Dictionary with evaluation results
    """

    eval_prompt = f"""
    Question: {question}

    Agent Response: {answer}

    Tool Used (actual): {tool_used}

    Evaluate the agent's performance on the given criteria.
    """

    eval_result = await evaluation_agent.run(eval_prompt)

    return {
        "question": question,
        "answer_preview": answer[:200] + "..." if len(answer) > 200 else answer,
        "tool_used_actual": tool_used,
        "evaluation": {
            "instructions_follow": eval_result.output.instructions_follow,
            "instructions_avoid": eval_result.output.instructions_avoid,
            "answer_relevant": eval_result.output.answer_relevant,
            "answer_clear": eval_result.output.answer_clear,
            "answer_citations": eval_result.output.answer_citations,
            "completeness": eval_result.output.completeness,
            "tool_call_search": tool_used,  # Use actual tool usage instead of AI's guess
            "overall_score": eval_result.output.overall_score,
            "reasoning": eval_result.output.reasoning
        }
    }

async def run_evaluation(questions: List[str]) -> Dict[str, Any]:
    """
    Run full evaluation on a list of questions

    Args:
        questions: List of questions to evaluate

    Returns:
        Complete evaluation results
    """

    print(f"Starting evaluation of {len(questions)} questions...")

    # Setup the agent and indexes
    print("Setting up agent and indexes...")
    text_index, vector_index, embedding_model, docs = setup_indexes()
    agent, search_tool = setup_agent(text_index, vector_index, embedding_model)

    evaluation_results = []
    log_entries = []

    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] Evaluating: {question[:60]}...")

        # Run the agent
        try:
            result = await agent.run(user_prompt=question)

            # Check if tool was actually used
            tool_used = False
            for msg in result.new_messages():
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_used = True
                    break

            # Evaluate the response
            eval_result = await evaluate_single_response(question, result.output, tool_used)
            evaluation_results.append(eval_result)

            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": result.output,
                "tool_used": tool_used,
                "evaluation": eval_result["evaluation"],
                "agent_name": "workout_agent"
            }
            log_entries.append(log_entry)

            print(f"   Score: {eval_result['evaluation']['overall_score']}/5")
            print(f"   Tool used: {tool_used}")

        except Exception as e:
            print(f"   Error: {e}")
            # Add error entry
            evaluation_results.append({
                "question": question,
                "error": str(e),
                "evaluation": None
            })

    # Calculate summary statistics
    valid_results = [r for r in evaluation_results if r.get("evaluation")]

    if valid_results:
        avg_score = sum(r["evaluation"]["overall_score"] for r in valid_results) / len(valid_results)
        tool_usage_rate = sum(1 for r in valid_results if r["tool_used_actual"]) / len(valid_results) * 100

        criteria_avg = {}
        criteria_names = ["instructions_follow", "instructions_avoid", "answer_relevant",
                         "answer_clear", "answer_citations", "completeness", "tool_call_search"]

        for criterion in criteria_names:
            criteria_avg[criterion] = sum(r["evaluation"][criterion] for r in valid_results) / len(valid_results) * 100

        summary = {
            "total_questions": len(questions),
            "valid_evaluations": len(valid_results),
            "average_score": round(avg_score, 2),
            "tool_usage_rate": round(tool_usage_rate, 1),
            "criteria_percentages": {k: round(v, 1) for k, v in criteria_avg.items()}
        }
    else:
        summary = {"error": "No valid evaluations completed"}

    # Save detailed log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"evaluation_log_{timestamp}.json"
    log_filepath = LOG_DIR / log_filename

    log_data = {
        "evaluation_summary": summary,
        "individual_results": log_entries,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "num_questions": len(questions),
            "agent_name": "workout_agent"
        }
    }

    with open(log_filepath, 'w') as f:
        json.dump(log_data, f, indent=2)

    print(f"\nEvaluation complete! Results saved to {log_filename}")

    return {
        "summary": summary,
        "results": evaluation_results,
        "log_file": str(log_filepath)
    }

async def load_synthetic_questions(filename: str = "synthetic_questions.json") -> List[str]:
    """
    Load synthetic questions from file

    Args:
        filename: JSON file with questions

    Returns:
        List of questions
    """
    filepath = Path(__file__).parent / filename

    if not filepath.exists():
        print(f"⚠️  {filename} not found. Using default test questions.")
        return [
            "How do I install this project?",
            "What dataset does this use?",
            "How do I run the API?",
            "How do I configure the application?",
            "What are the main features?"
        ]

    with open(filepath, 'r') as f:
        data = json.load(f)

    return data.get("questions", [])

async def main():
    """Main evaluation function"""

    print("DOCUMENTATION ASSISTANT EVALUATION")
    print("=" * 50)

    # Load questions
    questions = await load_synthetic_questions()
    print(f"Loaded {len(questions)} questions for evaluation")

    # Run evaluation
    results = await run_evaluation(questions)

    # Print summary
    print("\n" + "=" * 50)
    print("EVALUATION SUMMARY")
    print("=" * 50)

    summary = results["summary"]

    if "error" not in summary:
        print(f"Total Questions: {summary['total_questions']}")
        print(f"Valid Evaluations: {summary['valid_evaluations']}")
        print(f"Average Score: {summary['average_score']}")
        print(f"Tool Usage Rate: {summary['tool_usage_rate']}%")

        print("\nCriteria Performance (%):")
        for criterion, percentage in summary["criteria_percentages"].items():
            print(f"  {criterion}: {percentage}%")

    print(f"\nDetailed results saved to: {results['log_file']}")

if __name__ == "__main__":
    asyncio.run(main())