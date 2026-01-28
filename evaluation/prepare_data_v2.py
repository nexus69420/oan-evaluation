import os
import sys
import asyncio
from datetime import datetime
import pandas as pd
import numpy as np

model_name = "kenpath/mhv_vistaar_all_mhv_vistaar_all_qwen3-32b_v0.2_v0.2.1"
MODEL_LABEL = "FT Qwen 3 (32B) v0.2.1"
# model_name = 'gpt-4.1'
# MODEL_LABEL = "GPT-4.1"
## Number of concurrent workers for parallel processing
NUM_WORKERS = 8

# Get the parent directory - oan-evaluation
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Change path to the project root
project_dir = "/Users/adityachhabra/Github/sunbird-va-api"
os.chdir(project_dir)
sys.path.append(project_dir)

PATH_TO_QUESTIONS_DATA = os.path.join(current_dir, "data", "evaluation_questions_v2.csv")

from dotenv import load_dotenv
load_dotenv()

from tqdm.asyncio import tqdm
from agents.agrinet import agrinet_agent
from agents.deps import FarmerContext
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel , OpenAIChatModelSettings
from pydantic_ai.models.openai import OpenAIResponsesModel , OpenAIResponsesModelSettings


provider = OpenAIProvider(
    #api_key=os.getenv("OPENAI_API_KEY_V1"),
    base_url="http://216.48.185.71:8080/v1",
    # api_key="dummy",  # vLLM doesn't need it, but some clients require a value
 )
model = OpenAIChatModel(
    model_name,
    provider=provider,
)

settings = OpenAIChatModelSettings(
    temperature=0.7,
    min_p=0.01,
    top_k=20,
    top_p=0.8,
    parallel_tool_calls=True,
    timeout=60,
    request_limit=10,
#    extra_body={"chat_template_kwargs": {"enable_thinking": False}}
)

async def get_response(q, target_lang='mr'):
    deps = FarmerContext(
            query=q,
            lang_code=target_lang,
    )
    # NOTE: Forcing Positive Moderation - This is a hack to ensure the query is valid and not banned.
    deps.update_moderation_str("**Moderation Recommendation:** Proceed with the query (Valid Agricultural)")
    res = await agrinet_agent.run(deps.get_user_message(), 
                                    deps=deps, 
                                    model=model, 
                                    builtin_tools=[],
                                    model_settings=settings,
    )
    answer = res.output
    return {
        "answer": answer,
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "model_label": MODEL_LABEL
    }

async def process_row(row, semaphore):
    async with semaphore:
        for _ in range(5):
            try:
                question = row['question']
                response   = await get_response(question, target_lang='mr')
                return {**row.to_dict(), **response}
            except Exception as e:
                print(f"Error: {e}")
                continue
        return None

async def main():
    questions_df = pd.read_csv(PATH_TO_QUESTIONS_DATA).replace({np.nan: None})
    questions_df['farmer_id'] = None

    existing_results = []
    
    semaphore = asyncio.Semaphore(NUM_WORKERS)
    tasks = [process_row(row, semaphore) for _, row in questions_df.iterrows()]
    results = await tqdm.gather(*tasks, desc="Processing questions")
    
    # Merge existing + new results
    return existing_results + [r for r in results if r is not None]

if __name__ == "__main__":
    results = asyncio.run(main())
    # Create pandas dataframe from results
    results_df = pd.DataFrame(results)
    model_data_path = os.path.join(current_dir, "data", MODEL_LABEL.replace(" ", "_") + ".csv")
    results_df.to_csv(model_data_path, index=False, encoding="utf-8")
    print(f"Results saved to {model_data_path}")