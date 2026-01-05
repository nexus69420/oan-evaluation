import os
import asyncio
import json
import warnings
warnings.filterwarnings('ignore')
from tqdm.asyncio import tqdm
from dotenv import load_dotenv
from evaluator import evaluation_agent, format_agent_turns_to_markdown

load_dotenv()

#model_name  = "gpt-4.1"
model_name ="mistralai/Mistral-Small-3.2-24B-Instruct-2506"
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
        question = item.get("question", "")
        
        # Format message
        agent_turns = format_agent_turns_to_markdown(item.get("agent_turns", []))
        message = "\n\n".join([
            "*User Question:* " + question,
            "*Category:* " + item.get("category", ""),
            "*Agristack Required:* " + item.get("agristack_required", "No"),
            "*Agent Turns:*\n" + agent_turns,
            "*Final Response:*\n" + item.get("answer", "")
        ])
        
        # Evaluate
        try:
            eval_result = await evaluation_agent.run(message)
            item['evaluation'] = eval_result.output.model_dump()
            return item
        except Exception as e:
            print(f"Error: {question[:50]}... - {e}")
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