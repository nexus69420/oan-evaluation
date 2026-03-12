import os
import sys
import json
import asyncio
import random
from datetime import datetime
import pandas as pd
import numpy as np

## Model name to be evaluated
#model_name = "Qwen/Qwen3-14b"
#model_name = "kenpath/mhv_vistaar_qwen3-14b_v0.1"
# model_name = 'openai/gpt-oss-120b'
# model_name = 'meta-llama/Llama-4-Scout-17B-16E-Instruct'
# model_name = 'kenpath/mhv_vistaar_gpt-oss-20b_v0.5'
# model_name = "claude-haiku-4-5"
# model_name = "Qwen/Qwen3-32B"
# model_name = "Qwen/Qwen3-30B-A3B-Instruct-2507"
# model_name = "kenpath/mhv_vistaar_all_qwen3-32b_v0.2"
# model_name = "kenpath/mhv_vistaar_all_mhv_vistaar_all_qwen3-32b_v0.2_v0.2.1"
# model_name = "Qwen/Qwen3.5-27B"
model_name = "kenpath/mhv_mhv-_all_qwen3.5-27b_v0.3"
#model_name   = "Qwen/Qwen3.5-122B-A10B"
# model_name = "Qwen/Qwen3.5-9B"
# model_name = "Qwen/Qwen3.5-397B-A17B"
# model_name = "kenpath/mhv_vistaar_last_qwen3-30b-a3b-instruct-2507_v0.2"
# model_name = "kenpath/mhv_vistaar_all_qwen3-30b-a3b-instruct-2507_v0.1"
# model_name   = "KissanAI/Dhenu2-In-Llama3.1-8B-Instruct"
#model_name = 'meta-llama/Llama-3.3-70B-Instruct'
# model_name = 'nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8'
# model_name = "openai/gpt-oss-20b_non_thinking"

## Number of concurrent workers for parallel processing
NUM_WORKERS = 50
NUM_SAMPLE  = 200

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
provider = OpenAIProvider(
# provider = AnthropicProvider(
    base_url="http://216.48.185.71:8080/v1",
    #api_key=os.getenv("ANTHROPIC_API_KEY"),
    api_key="dummy",  # vLLM doesn't need it, but some clients require a value
    # api_key=os.getenv("OPENAI_API_KEY"),
 )
model = OpenAIChatModel(
    model_name,
    provider=provider,
)

# temperature=0.7, top_p=0.8, top_k=20, min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0

settings = OpenAIChatModelSettings(
    temperature=0.7,
    min_p=0.0,
    presence_penalty=1.5,
    repetition_penalty=1.0,
    top_k=20,
    top_p=0.8,
    parallel_tool_calls=True,
    timeout=120,
    request_limit=10,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}}
)

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
                                    model_settings=settings,
    )
    assert len(res.all_messages()) > 3, "No internal messages"
    assert isinstance(res.output, str) and res.output.strip() != "", "Response is empty"
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

    # Load existing answers if data.json exists
    data_file = os.path.join(MODEL_DATA_PATH, "data.json")
    # Test model metadata is available:
    print(f"Settings: {settings}")
    metadata = {
    "provider_name": provider.name,
    "provider_base_url": provider.base_url,
    "model_name": model.model_name,
    "model_settings": settings,
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
    
    if NUM_SAMPLE is not None and NUM_SAMPLE < len(questions_df):
        questions_df = questions_df.sample(n=NUM_SAMPLE, random_state=random.randint(0, 2**32 - 1))
    
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