import os
import json
import asyncio
import pandas as pd

# Change path to the project root
path = "/Users/adityachhabra/Github/sunbird-va-api"
PATH_TO_QUESTIONS_DATA = "data/questions.csv"
os.chdir(path)

from tqdm import tqdm
from agents.agrinet import agrinet_agent
from agents.deps import FarmerContext
from pydantic_ai.settings import ModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings

provider = OpenAIProvider(
    base_url="http://216.48.185.71:8080/v1",
    api_key="dummy",  # vLLM doesn't need it, but some clients require a value
)
model = OpenAIChatModel(
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
    provider=provider,
)

settings = OpenAIChatModelSettings(parallel_tool_calls=True)

async def get_response(q, target_lang='mr', farmer_id=None):
    deps = FarmerContext(
        query=q,
        lang_code=target_lang,
        farmer_id=farmer_id
    )
    # NOTE: Forcing Positive Moderation - This is a hack to ensure the query is valid and not banned.
    deps.update_moderation_str("Valid Agricultural (Proceed with the query)")
    res = await agrinet_agent.run(deps.get_user_message(), deps=deps, model=model, model_settings=settings)
    answer = res.output    
    all_messages = json.loads(res.all_messages_json())
    internal_messages = all_messages[1:-1]
    return {
        'answer': answer, 
        'agent_turns': internal_messages, 
    }

async def main():
    questions_df = pd.read_csv(PATH_TO_QUESTIONS_DATA)
    
    # Create tasks for parallel execution
    tasks = []
    for idx, row in questions_df.iterrows():
        question     = row['question']
        agristack_id = row['agristack_id']
        task = get_response(question, target_lang='mr', farmer_id=agristack_id)
        tasks.append((idx, row, task))
    
    # Run all tasks in parallel
    print(f"Processing {len(tasks)} questions in parallel...")
    results = await asyncio.gather(*[task for _, _, task in tasks])
    
    # Combine results with original rows
    records = []
    for (idx, row, _), output in zip(tasks, results):
        row_dict = row.to_dict()
        row_dict.update(output)
        records.append(row_dict)
    
    return records

if __name__ == "__main__":
    records = asyncio.run(main())