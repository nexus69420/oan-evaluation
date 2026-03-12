import os
import asyncio
import json
import warnings
warnings.filterwarnings('ignore')
from tqdm.asyncio import tqdm
from dotenv import load_dotenv
from evaluator import evaluation_agent, format_agent_record, EvaluationDeps

load_dotenv()

#model_name  = "gpt-4.1-mini"
# model_name ="Qwen/Qwen3-14b"
#model_name = "mistralai_Mistral-Small-3.2-24B-Instruct-2506"
# model_name ="kenpath/mhv_vistaar_qwen3-14b_v0.2"
#model_name = "openai/gpt-oss-120b"
# model_name = "kenpath/mhv_fsdp-vistaar_gpt-oss-120b_v0.5"
#model_name = "Qwen/Qwen3.5-27B"
model_name = "kenpath/mhv_mhv-_all_qwen3.5-27b_v0.3"
# model_name = "Qwen/Qwen3.5-122B-A10B"
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

# Load data
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load existing evaluations
existing = {}
if os.path.exists(eval_json_file):
    with open(eval_json_file, 'r', encoding='utf-8') as f:
        for item in json.load(f):
            q = item.get("question", "")
            if q and "evaluation" in item:
                existing[q] = item
    print(f"Loaded {len(existing)} existing evaluations")

# Semaphore to limit concurrent requests
MAX_CONCURRENT = 20
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def evaluate_item(item):
    """Evaluate a single item with concurrency control."""
    async with semaphore:        
        # Format message
        category = item.get("category", "")
        message = format_agent_record(item)            
        # Evaluate
        try:
            eval_result = await evaluation_agent.run(
                message,
                deps=EvaluationDeps(category=category)
            )
            item['evaluation'] = eval_result.output.to_eval_dict()
            return item
        except Exception as e:
            print(f"Error: {item.get('question', '')[:50]}... - {e}")
            return None

async def main():
    # Separate items into already evaluated and to-be-evaluated
    results = []
    tasks = []
    
    for item in data:
        question = item.get("question", "")
        
        # Skip if already evaluated
        if question in existing:
            results.append(existing[question])
        else:
            tasks.append(evaluate_item(item))
    
    print(f"Skipping {len(results)} already evaluated items")
    print(f"Evaluating {len(tasks)} items in parallel (max {MAX_CONCURRENT} concurrent)...")
    
    # Run all evaluations in parallel with progress bar
    if tasks:
        completed = await tqdm.gather(*tasks, desc="Evaluating")
        
        # Add successful evaluations to results
        for result in completed:
            if result is not None:
                results.append(result)
    
    # Save all results
    with open(eval_json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
    print("Evaluation Done!")