import os
import csv
import json
import asyncio
import warnings
warnings.filterwarnings('ignore')
from tqdm.asyncio import tqdm
from dotenv import load_dotenv
from evaluator import EvalDeps, evaluation_agent, format_agent_record

load_dotenv()

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV   = os.path.join(current_dir, "data", "questions.csv")
OUTPUT_JSON = os.path.join(current_dir, "data", "evaluation-gemma.json")
CONCURRENCY = int(os.getenv("EVAL_CONCURRENCY", "8"))


def load_questions(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return [
            {"question": row["question"], "answer": row["answer"]}
            for row in csv.DictReader(f)
        ]


def load_existing(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return {row["question"]: row for row in json.load(f) if row.get("question")}


def save_results(path, results):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


async def evaluate_item(item, sem, results, lock):
    async with sem:
        message = format_agent_record(item)
        deps = EvalDeps(question=item["question"], answer=item["answer"])
        try:
            result = await evaluation_agent.run(message, deps=deps)
            record = {
                "question": item["question"],
                "answer": item["answer"],
                **result.output.model_dump(),
            }
        except Exception as e:
            print(f"Error: {item.get('question', '')[:50]}... - {e}")
            return
        async with lock:
            results.append(record)
            save_results(OUTPUT_JSON, results)


async def main():
    data = load_questions(INPUT_CSV)
    existing = load_existing(OUTPUT_JSON)
    print(f"Loaded {len(existing)} existing evaluations")

    results = []
    pending = []
    for item in data:
        if item["question"] in existing:
            results.append(existing[item["question"]])
        else:
            pending.append(item)

    print(f"Skipping {len(results)} already evaluated items")
    print(f"Evaluating {len(pending)} items with {CONCURRENCY} workers...")

    sem = asyncio.Semaphore(CONCURRENCY)
    lock = asyncio.Lock()
    tasks = [evaluate_item(item, sem, results, lock) for item in pending]
    await tqdm.gather(*tasks, desc="Evaluating")

    save_results(OUTPUT_JSON, results)
    print(f"Saved {len(results)} records to {OUTPUT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
    print("Evaluation Done!")
