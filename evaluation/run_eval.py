import os
import asyncio
import json
import warnings
warnings.filterwarnings('ignore')
from tqdm.asyncio import tqdm
from dotenv import load_dotenv
from evaluator import evaluation_agent, format_conversation_record, EvaluationDeps

load_dotenv()

#model_name  = "gpt-4.1-mini"
# model_name ="Qwen/Qwen3-14b"
#model_name = "mistralai_Mistral-Small-3.2-24B-Instruct-2506"
# model_name ="kenpath/mhv_vistaar_qwen3-14b_v0.2"
#model_name = "openai/gpt-oss-120b"
model_name = "kenpath/mhv_fsdp-vistaar_gpt-oss-120b_v0.5"
# model_name = "meta-llama/Llama-4-Scout-17B-16E-Instruct"
#model_name = "Qwen/Qwen3-32B"
#model_name = "Qwen/Qwen3-30B-A3B-Instruct-2507"
#model_name = "kenpath/mhv_vistaar_all_qwen3-32b_v0.2"
# model_name = "openai/gpt-oss-20b"
#model_name = "kenpath/mhv_vistaar_qwen3-32b_v0.2"
# model_name = "kenpath/mhv_vistaar_all_qwen3-30b-a3b-instruct-2507_v0.1"
# model_name = "KissanAI/Dhenu2-In-Llama3.1-8B-Instruct"
# model_name  = "kenpath/mhv_vistaar_all_qwen3-30b-a3b-instruct-2507_v0.1"
#model_name = "kenpath/mhv_vistaar_all_mhv_vistaar_all_qwen3-32b_v0.2_v0.2.1"
#model_name = "gpt-4.1"
#model_name = "claude-haiku-4-5"


current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DATA_PATH = os.path.join(current_dir, "data", "models", model_name.replace("/", "_"))
json_file = os.path.join(MODEL_DATA_PATH, "data.json")
eval_json_file = os.path.join(MODEL_DATA_PATH, "evaluation.json")

# json_file = json_file = os.path.join("D:/Kenpath/oan-evaluation/data/synthetic/conversations_20260301_121121.jsonl")
# eval_jsonl_file = os.path.join("D:/Kenpath/oan-evaluation/data/synthetic/evaluation/conversations_20260301_121121_evaluation.jsonl")

data = []
with open(json_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():  # skip empty lines
            data.append(json.loads(line))

existing = {}
if os.path.exists(eval_json_file):
    with open(eval_json_file, "r", encoding="utf-8") as f:
        for item in json.load(f):
            conv_id = item.get("id")
            if conv_id and "evaluation" in item:
                existing[conv_id] = item

MAX_CONCURRENT = 20
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# ------------------ EVALUATION FUNCTION ------------------
async def evaluate_item(item):
    async with semaphore:
        try:
            category = item.get("category", "")
            message = format_conversation_record(item)

            result = await evaluation_agent.run(
                message,
                deps=EvaluationDeps(category=category)
            )

            item["evaluation"] = result.output.to_eval_dict()
            return item

        except Exception as e:
            print(f"Error evaluating conversation {item.get('id')} - {e}")
            return None

# ------------------ MAIN ------------------
async def main():
    results = []
    tasks = []

    for item in data:
        conv_id = item.get("id")

        if conv_id in existing:
            results.append(existing[conv_id])
        else:
            tasks.append(evaluate_item(item))

    print(f"Skipping {len(results)} already evaluated items")
    print(f"Evaluating {len(tasks)} conversations...")

    if tasks:
        completed = await tqdm.gather(*tasks, desc="Evaluating")
        for r in completed:
            if r:
                results.append(r)

    with open(eval_json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print("Evaluation Done!")

if __name__ == "__main__":
    asyncio.run(main())