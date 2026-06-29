# Automate the process of calling the agent and storing the responses in a csv file shared by Pocra team.
import os
import asyncio

import pandas as pd
import numpy as np
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from agents.agrinet import agrinet_agent
from agents.deps import FarmerContext
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel, ModelSettings


MODEL_NAME = "gpt-4.1"
TARGET_LANG = "mr"

PROJECT_DIR = "D:/Kenpath/MhVistaar/sunbird-va-api"
INPUT_PATH = os.path.join(PROJECT_DIR, "data", "prompts_merged.csv")
OUTPUT_PATH = os.path.join(PROJECT_DIR, "data", "responses_output.csv")

REQUIRED_COLUMNS = {"crop", "season", "region", "category", "prompt"}

os.makedirs(os.path.dirname(INPUT_PATH), exist_ok=True)
load_dotenv()

provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))

model = OpenAIModel(
    MODEL_NAME,
    provider=provider,
)

model_settings = ModelSettings(
    parallel_tool_calls=True
)


def build_context(row: dict) -> str | None:
    """
    Build structured context block from non-empty row fields.
    """
    parts = []

    if row.get("crop"):
        parts.append(f"**Crop:** {row['crop']}")
    if row.get("season"):
        parts.append(f"**Season:** {row['season']}")
    if row.get("region"):
        parts.append(f"**Region:** {row['region']}")
    if row.get("category"):
        parts.append(f"**Category:** {row['category']}")

    return "\n".join(parts) if parts else None


async def get_response(prompt: str, context: str | None) -> str:
    """
    Call Agrinet agent with context + user prompt.
    """
    deps = FarmerContext(
        query=prompt,
        lang_code=TARGET_LANG,
        farmer_id=None,
    )

    # Force allow (evaluation mode)
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

    df_input = (
        pd.read_csv(INPUT_PATH)
        if INPUT_PATH.endswith(".csv")
        else pd.read_excel(INPUT_PATH)
    ).replace({np.nan: None})

    df_input.columns = df_input.columns.str.lower()

    missing = REQUIRED_COLUMNS - set(df_input.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


    if os.path.exists(OUTPUT_PATH):
        df_output = pd.read_csv(OUTPUT_PATH).replace({np.nan: None})
        df_output.columns = df_output.columns.str.lower()
        processed_prompts = set(df_output["prompt"].tolist())

        print(f"Resuming run | Already processed: {len(processed_prompts)} rows")
    else:
        df_output = pd.DataFrame(
            columns=list(df_input.columns) + ["response"]
        )
        processed_prompts = set()

        print("Starting fresh run")


    for _, row in tqdm(df_input.iterrows(), total=len(df_input)):
        prompt = row["prompt"]

        # Skip completed prompts
        if prompt in processed_prompts:
            continue

        context = build_context(row)

        response = await get_response(prompt, context)

        output_row = row.to_dict()
        output_row["response"] = response

        # Append single row
        df_output = pd.concat(
            [df_output, pd.DataFrame([output_row])],
            ignore_index=True
        )

        # Persist immediately (crash-safe)
        df_output.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

        processed_prompts.add(prompt)

    print(f"Run completed")
    print(f"Total rows stored: {len(df_output)}")
    print(f"Output file: {OUTPUT_PATH}")



if __name__ == "__main__":
    asyncio.run(main())
