import os
import sys
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_ai import Agent
import json
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Set up project path
project_path = r"D:\Kenpath\oan-evaluation"
os.chdir(project_path)
sys.path.insert(0, project_path)

from dotenv import load_dotenv
load_dotenv()

from helpers.utils import get_prompt


class Metric(BaseModel):
    farmer_id : str = Field(..., description="The id of the farmer")
    question: str = Field(..., description="The question that the user asked")
    response: str = Field(..., description="The response from the model")
    metric_name: str = Field(..., description="The name of the metric to evaluate")
    score: int = Field(..., description="The score of the metric", ge=0, le=5)
    explanation: str = Field(..., description="The explanation of the score")

class EvaluationResult(BaseModel):
    """Result of the evaluation."""
    source_attribution: Metric = Field(..., description="Measures how well the response references appropriate, authoritative, and relevant sources. Higher scores reflect correct alignment between cited sources and the information presented.")
    grammatical_accuracy: Metric = Field(..., description="Evaluates the degree to which the response maintains grammatical correctness, valid word usage, accurate translations or transliterations, and proper sentence structure in Marathi.")
    factual_correctness: Metric = Field(..., description="Measures the accuracy of all factual information in the response, including details related to government schemes, mandi prices, fertilizers, pesticides, quantities, timelines, and agricultural guidelines, without introducing incorrect or misleading claims")
    actionability: Metric = Field(..., description="Evaluates the extent to which the response provides practical and implementable guidance, such as quantities, ratios, step-by-step instructions, timelines, or decision criteria that can be acted upon directly by the user.")
    completeness: Metric = Field(..., description="Measures how thoroughly the response addresses the user's query, including coverage of essential steps, conditions, data points, constraints, and safety considerations where relevant.")
    context_alignment: Metric = Field(..., description="Measures how closely the response stays aligned with the user's question and situational context, avoiding unnecessary or unrelated information, and introducing follow-up questions only when contextually justified.")
    information: Metric = Field(..., description="Evaluates whether the level of detail is suitable for the intended user, balancing clarity and precision without being overly technical or overly vague, and reflecting real-world agricultural practices.")
    safety_compliance: Metric = Field(..., description="Measures adherence to regulatory and safety norms by avoiding recommendations of banned, unsafe, or non-compliant agricultural inputs or practices, and by including appropriate safety precautions where applicable.")
    tool_usage: Metric = Field(..., description="Measures whether the response reflects correct selection and sequencing of tools or processes as required by the task, without omission, misuse, or unnecessary invocation.")
    retrieval_grounding: Metric = Field(..., description="Evaluates the extent to which the response is grounded in retrieved or provided documents and avoids introducing unsupported, speculative, or fabricated information.")

evaluation_agent = Agent(
    model='gpt-5',
    name="Evaluation Agent",
    instrument=True,
    output_type=EvaluationResult,
    retries=2,
    system_prompt=get_prompt('evaluation_system'),
)


json_file = "data/models/mistralai_Mistral-Small-3.2-24B-Instruct-2506/data.json"


with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

#total number of items
print(f"Total number of items: {len(data)}")

#sample item
item = data[5]

def response(item):
    lines = []

    lines.append(f"User Query: {item['question']}")
    lines.append("Language: Marathi")
    lines.append("=" * 50 + "\n")

    # Tool calls & returns
    for turn in item.get("agent_turns", []):
        for part in turn.get("parts", []):
            if part["part_kind"] == "tool-call":
                lines.append(f"Assistant called tool: {part['tool_name']}")
                lines.append(f"Arguments: {part.get('args', '{}')}\n")

            elif part["part_kind"] == "tool-return":
                lines.append(f"Tool '{part['tool_name']}' returned:")
                lines.append(part.get("content", "").strip() + "\n")

    lines.append("=" * 50)
    lines.append("=" * 50 + "\n")

    lines.append("Final Response:")
    lines.append(item.get("answer", "").strip())

    return "\n".join(lines)

print(response(item))

async def run_evaluation():
    eval_result = await evaluation_agent.run(response(item))
    print(json.dumps(eval_result.output.model_dump(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(run_evaluation())




