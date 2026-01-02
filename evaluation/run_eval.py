import os
import asyncio
import json
import warnings
warnings.filterwarnings('ignore')
from tqdm.asyncio import tqdm
from dotenv import load_dotenv
from evaluator import evaluation_agent, format_agent_turns_to_markdown

load_dotenv()

model_name = "mistralai/Mistral-Small-3.2-24B-Instruct-2506"
# Get the parent directory - oan-evaluation
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DATA_PATH        = os.path.join(current_dir, "data", "models", model_name.replace("/", "_"))
json_file = os.path.join(MODEL_DATA_PATH, "data.json")
eval_json_file = os.path.join(MODEL_DATA_PATH, "evaluation.json")   

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

async def main():
    eval_results = []
    for item in tqdm(data, desc="Evaluating data")  :
        agent_turns   = format_agent_turns_to_markdown(item.get("agent_turns", []))
        message_parts = [
            "*User Question:*\n" + item.get("question", ""), 
            "*Agent Turns:*\n" + agent_turns,
            "*Final Response:*\n" + item.get("answer", "")
        ]

        message = "\n\n".join(message_parts)

        try:
            eval_result = await evaluation_agent.run(message)
            item['evaluation'] = eval_result.output.model_dump()
        except Exception as e:
            print(f"Error evaluating item {item['question']}: {e}")
            continue #skip the item and continue with the next item

        print(f"Evaluated item {item['question']} successfully")
        #append item ,not full data
        eval_results.append(item)

    return eval_results

if __name__ == "__main__":
    eval_results = asyncio.run(main())
    # save eval_results to eval_json_file
    with open(eval_json_file, 'w', encoding='utf-8') as f:
        json.dump(eval_results, f, ensure_ascii=False, indent=4)