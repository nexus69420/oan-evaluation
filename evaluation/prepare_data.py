import os
import sys
import json
import asyncio
from datetime import datetime
import pandas as pd
import numpy as np

## Model name to be evaluated
#model_name = "Qwen/Qwen3-14b"
#model_name = "kenpath/mhv_vistaar_qwen3-14b_v0.1"
# model_name = 'openai/gpt-oss-120b'
# model_name = 'meta-llama/Llama-4-Scout-17B-16E-Instruct'
# model_name = 'kenpath/mhv_vistaar_gpt-oss-20b_v0.5'
model_name = "claude-opus-4-5"
#model_name = 'meta-llama/Llama-3.3-70B-Instruct'
# model_name = 'nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8'
# model_name = "openai/gpt-oss-20b_non_thinking"

## Number of concurrent workers for parallel processing
NUM_WORKERS = 8

# Get the parent directory - oan-evaluation
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Change path to the project root
project_dir = "/Users/adityachhabra/Github/sunbird-va-api"
os.chdir(project_dir)
sys.path.append(project_dir)

PATH_TO_QUESTIONS_DATA = os.path.join(current_dir, "data", "evaluation_questions.csv")
MODEL_DATA_PATH        = os.path.join(current_dir, "data", "models", model_name.replace("/", "_"))
os.makedirs(MODEL_DATA_PATH, exist_ok=True)

from dotenv import load_dotenv
load_dotenv()

from tqdm.asyncio import tqdm
from agents.agrinet import agrinet_agent
from agents.deps import FarmerContext
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel , OpenAIChatModelSettings
from pydantic_ai.models.openai import OpenAIResponsesModel , OpenAIResponsesModelSettings
from pydantic_ai.models.anthropic import AnthropicModel
#, AnthropicChatModelSettings
from pydantic_ai.providers.anthropic import AnthropicProvider
#provider = OpenAIProvider(
provider = AnthropicProvider(
    #base_url="http://216.48.185.71:8080/v1",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    #api_key="dummy",  # vLLM doesn't need it, but some clients require a value
    # api_key=os.getenv("OPENAI_API_KEY"),
)
model = AnthropicModel(
    model_name,
    provider=provider,
)

# settings = AnthropicChatModelSettings(
#     #temperature=1.0,
#     #temperature=,
#     #openai_send_reasoning_ids=True,
#     #openai_reasoning_generate_summary="detailed",
#     #openai_reasoning_summary="auto",
#     #min_p=0.01,
#     #top_k=100,
#     #top_p=1.0,
#     # max_tokens=1000,c
#     #openai_reasoning_effort='low',
#     parallel_tool_calls=True,
#     timeout=15,
#     request_limit=10,
#     # extra_body={"chat_template_kwargs": {"enable_thinking": True}}
# )

async def get_response(q, target_lang='mr', farmer_id=None):
    deps = FarmerContext(
            query=q,
            lang_code=target_lang,
            farmer_id=farmer_id
    )
    # NOTE: Forcing Positive Moderation - This is a hack to ensure the query is valid and not banned.
    deps.update_moderation_str("**Moderation Recommendation:** Proceed with the query (Valid Agricultural)")
    res = await agrinet_agent.run(deps.get_user_message(), 
                                    deps=deps, 
                                    model=model, 
                                    builtin_tools=[],
                                    #model_settings=settings,
    )
    # assert isinstance(res.output, str) and res.output.strip() != "", "Response is empty"
    answer = res.output    
    all_messages = json.loads(res.all_messages_json())
    internal_messages = all_messages[1:-1]
    return {
        'answer': answer, 
        'agent_turns': internal_messages, 
    }

async def process_row(row, semaphore):
    async with semaphore:
        for _ in range(5):
            try:
                question = row['question']
                farmer_id = row['farmer_id']
                result = await get_response(question, target_lang='mr', farmer_id=farmer_id)
                return {**row.to_dict(), **result}
            except Exception as e:
                print(f"Error: {e}")
                continue
        return None

async def main():
    questions_df = pd.read_csv(PATH_TO_QUESTIONS_DATA).replace({np.nan: None})
    questions_df['farmer_id'] = questions_df['farmer_id'].apply(lambda x: str(int(x)) if x is not None else None)
    # Shuffle the questions
    # questions_df = questions_df.sample(frac=1).reset_index(drop=True)
    # questions_df = questions_df[questions_df.category!='Advisory']
    
    # Load existing answers if data.json exists
    data_file = os.path.join(MODEL_DATA_PATH, "data.json")
    # Test model metadata is available:
    metadata = {
    "provider_name": provider.name,
    "provider_base_url": provider.base_url,
    "model_name": model.model_name,
    "model_settings": {},
    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    print(f"Metadata: {metadata}")
    existing_results = []
    answered_questions = set()
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            existing_results = json.load(f)
            answered_questions = {r['question'] for r in existing_results}
    
    # Filter to only unanswered questions
    questions_df = questions_df[~questions_df['question'].isin(answered_questions)]
    
    if questions_df.empty:
        print("All questions already answered. Nothing to process.")
        return existing_results
    
    print(f"Processing {len(questions_df)} new questions (skipping {len(answered_questions)} already answered)")
    
    semaphore = asyncio.Semaphore(NUM_WORKERS)
    tasks = [process_row(row, semaphore) for _, row in questions_df.iterrows()]
    results = await tqdm.gather(*tasks, desc="Processing questions")
    
    # Merge existing + new results
    return existing_results + [r for r in results if r is not None]

if __name__ == "__main__":
    results = asyncio.run(main())

    with open(os.path.join(MODEL_DATA_PATH, "data.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    # Metadata:
    metadata = {
        "provider_name": provider.name,
        "provider_base_url": provider.base_url,
        "model_name": model.model_name,
        "model_settings": {},
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


    with open(os.path.join(MODEL_DATA_PATH, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)