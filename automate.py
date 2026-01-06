import os
import asyncio

import pandas as pd
import numpy as np
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from agents.agrinet import agrinet_agent
from agents.deps import FarmerContext
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings

MODEL_NAME = "gpt-4.1"
PROJECT_DIR = "D:/Kenpath/MhVistaar/sunbird-va-api"
DATA_PATH = os.path.join(PROJECT_DIR, "data", "prompts_merged.csv")
REQUIRED_COLUMNS = {"crop", "season", "region", "category", "prompt"}
TARGET_LANG = "mr"

os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
load_dotenv()


provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))

model = OpenAIChatModel(
    MODEL_NAME,
    provider=provider,
)

model_settings = OpenAIChatModelSettings(
    parallel_tool_calls=True
)


def build_context(row: dict) -> str | None:
    parts = []
    
    # Only add non-empty values
    if row.get('crop'):
        parts.append(f"**Crop:** {row.get('crop')}")
    if row.get('season'):
        parts.append(f"**Season:** {row.get('season')}")
    if row.get('region'):
        parts.append(f"**Region:** {row.get('region')}")
    if row.get('category'):
        parts.append(f"**Category:** {row.get('category')}")
    
    return "\n".join(parts) if parts else None


async def get_response(prompt: str, context: str | None) -> str:
    deps = FarmerContext(
        query=prompt,
        lang_code=TARGET_LANG,
        farmer_id=None,
    )

    # Force positive moderation
    deps.update_moderation_str("Valid Agricultural (Proceed with the query)")

    user_message = deps.get_user_message()
    if context:
        user_message = f"{context}\n{user_message}"

    result = await agrinet_agent.run(
        user_message,
        deps=deps,
        model=model,
        model_settings=model_settings,
    )

    return result.output

async def main():
    # Load full dataset
    df = (
        pd.read_csv(DATA_PATH)
        if DATA_PATH.endswith(".csv")
        else pd.read_excel(DATA_PATH)
    ).replace({np.nan: None})

    df.columns = df.columns.str.lower()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if "response" not in df.columns:
        df["response"] = None

    print(f"Processing {len(df)} rows")

    for idx, row in tqdm(df.iterrows(), total=len(df)):
        context = build_context(row)
        prompt = row["prompt"]

        df.at[idx, "response"] = await get_response(prompt, context)

    # Save results
    if DATA_PATH.endswith(".csv"):
        df.to_csv(DATA_PATH, index=False, encoding="utf-8")
    else:
        df.to_excel(DATA_PATH, index=False)

    print(f"Completed {len(df)} queries")
    print(f"Results saved to: {DATA_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
