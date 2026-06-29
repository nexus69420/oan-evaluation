import os
import asyncio
import csv
import warnings
warnings.filterwarnings('ignore')
from tqdm.asyncio import tqdm
from dotenv import load_dotenv
from evaluator import evaluation_agent, format_agent_record

load_dotenv()

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV  = os.path.join(current_dir, "data", "questions.csv")
OUTPUT_CSV = os.path.join(current_dir, "data", "evaluation-gemma.csv")

CSV_FIELDNAMES = [
    "question", "answer",
    "grammar_score", "grammar_evidence",
    "marathi_terminology_score", "marathi_terminology_evidence",
    "language_purity_score", "language_purity_evidence",
    "fluency_score", "fluency_evidence",
    "language_quality_avg",
    "mix_detected", "mix_severity",
    "mixed_hindi_phrases", "summary",
]

# Load input data
data = []
with open(INPUT_CSV, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        data.append({"question": row["question"], "answer": row["answer"]})

# Load any existing evaluations so we can skip them on re-run
existing = {}
if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            q = row.get("question", "")
            if q and row.get("summary"):
                existing[q] = row
    print(f"Loaded {len(existing)} existing evaluations")


def to_csv_row(item, eval_dict):
    scores = eval_dict["dimensions"]["language_quality"]["scores"]
    return {
        "question":                     item["question"],
        "answer":                       item["answer"],
        "grammar_score":                scores["grammar"]["score"],
        "grammar_evidence":             scores["grammar"]["evidence"],
        "marathi_terminology_score":    scores["marathi_terminology"]["score"],
        "marathi_terminology_evidence": scores["marathi_terminology"]["evidence"],
        "language_purity_score":        scores["language_purity"]["score"],
        "language_purity_evidence":     scores["language_purity"]["evidence"],
        "fluency_score":                scores["fluency"]["score"],
        "fluency_evidence":             scores["fluency"]["evidence"],
        "language_quality_avg":         eval_dict["dimensions"]["language_quality"]["average"],
        "mix_detected":                 eval_dict["mix_detected"],
        "mix_severity":                 eval_dict["mix_severity"],
        "mixed_hindi_phrases":          " | ".join(eval_dict["mixed_hindi_phrases"]),
        "summary":                      eval_dict["summary"],
    }


async def evaluate_item(item):
    message = format_agent_record(item)
    try:
        eval_result = await evaluation_agent.run(message)
        return to_csv_row(item, eval_result.output.to_eval_dict())
    except Exception as e:
        print(f"Error: {item.get('question', '')[:50]}... - {e}")
        return None


async def main():
    results = []
    tasks = []

    for item in data:
        question = item.get("question", "")
        if question in existing:
            results.append(existing[question])
        else:
            tasks.append(item)

    print(f"Skipping {len(results)} already evaluated items")
    print(f"Evaluating {len(tasks)} items...")

    for item in tqdm(tasks, desc="Evaluating"):
        result = await evaluate_item(item)
        if result is not None:
            results.append(result)

    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved {len(results)} rows to {OUTPUT_CSV}")
    return results


if __name__ == "__main__":
    asyncio.run(main())
    print("Evaluation Done!")
