import os
import asyncio
import json
import warnings
warnings.filterwarnings('ignore')
from dotenv import load_dotenv
from evaluation.evaluator import evaluation_agent

load_dotenv()

model_name = "openai/gpt-oss-20b"
# Get the parent directory - oan-evaluation
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DATA_PATH        = os.path.join(current_dir, "data", "models", model_name.replace("/", "_"))
json_file = os.path.join(MODEL_DATA_PATH, "data.json")
data = open(json_file, 'r', encoding='utf-8').read()

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


eval_result = await evaluation_agent.run(response(item))
print(json.dumps(eval_result.output.model_dump(), indent=2, ensure_ascii=False))
