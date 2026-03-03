#!/usr/bin/env python3
"""
Generate farmer data:
- flows: only user messages
python -m simulation.generate_data -m flows -n 5 -o simulation/data/user_flows.jsonl

"""

import argparse
import asyncio
import json
import random
import re
from pathlib import Path

from simulation.agent import get_next_user_message

# -------------------- CONFIG --------------------

USE_CASES = [
    "pmkisan_status", "pmfby_status", "shc_status",
    "grievance", "scheme_info", "mandi", "weather", "advisory",
]

LANGUAGES = ["hi", "en","hinglish"]

BOT_MSGS = {
    "pmkisan_status": [
        [""],
        [
            "Please share your PM-KISAN registration number.",
            "Kindly provide your PM-KISAN ID.",
            "Enter your PM-KISAN registration number to proceed.",
        ],
        [
            "A 4-digit OTP has been sent to your registered mobile. Please enter it.",
            "Check your phone and share the 4-digit OTP.",
            "Enter the OTP sent to your mobile number.",
        ],
        [
            "Your latest installment has been credited. Do you need anything else?",
            "The payment has been processed successfully. Anything more?",
            "Installment status is updated. Would you like to check something else?",
        ],
    ],

    "pmfby_status": [
        [""],
        [
            "Please share your registered mobile number.",
            "Enter your mobile number to check policy status.",
            "Kindly provide your phone number.",
        ],
        [
            "A 6-digit OTP has been sent. Please enter it.",
            "Share the OTP received on your phone.",
            "Enter the verification OTP.",
        ],
        [
            "Please tell the year and season (e.g., Kharif 2024).",
            "Which crop season and year are you asking about?",
            "Mention the policy year and season.",
        ],
        [
            "Here is your insurance claim status. Need further help?",
            "Policy details are shown. Anything else you want to check?",
            "Your claim information is updated. Do you need more assistance?",
        ],
    ],

    "shc_status": [
        [""],
        [
            "Please provide your registered mobile number.",
            "Share your phone number to fetch Soil Health Card details.",
            "Enter your mobile number.",
        ],
        [
            "Which Soil Health Card cycle year (e.g., 2023-24)?",
            "Tell me the cycle year of your card.",
            "Mention the SHC year.",
        ],
        [
            "Here is your Soil Health Card summary. What would you like to know?",
            "Your SHC details are displayed. Need explanation?",
            "Soil Health Card fetched successfully. Any questions?",
        ],
    ],

    "grievance": [
        [""],
        [
            "Please provide your registration number or Aadhaar.",
            "Share your ID to proceed with grievance registration.",
            "Enter your registration details.",
        ],
        [
            "What is the issue about?",
            "Briefly describe your problem.",
            "Please explain the grievance.",
        ],
        [
            "Your grievance has been successfully registered.",
            "Complaint submitted. Our team will review it.",
            "Your issue is recorded. You will be notified soon.",
        ],
    ],

    "scheme_info": [
        [""],
        [
            "Which scheme would you like to know about?",
            "Please tell the scheme name.",
            "Mention the government scheme you are interested in.",
        ],
        [
            "Would you like to know eligibility details?",
            "Do you want application steps and required documents?",
            "Shall I explain how to apply?",
        ],
        [
            "Here are the required documents and steps.",
            "Application process details are shared.",
            "These are the steps to apply for the scheme.",
        ],
    ],

    "mandi": [
        [""],
        [
            "Which district or mandi are you referring to?",
            "Please tell the location of the mandi.",
            "Mention the district name.",
        ],
        [
            "Here are the latest mandi prices.",
            "Current market rates are displayed.",
            "This is today's price update.",
        ],
        [
            "Would you like advice on whether to sell now?",
            "Do you want suggestions on selling timing?",
            "Need help deciding when to sell?",
        ],
    ],

    "weather": [
        [""],
        [
            "Which village or district do you want the forecast for?",
            "Please share your location.",
            "Tell me your district for weather details.",
        ],
        [
            "Here is the weather forecast for the next few days.",
            "This is the expected weather update.",
            "Forecast details are shown below.",
        ],
        [
            "Do you need advice for spraying or irrigation?",
            "Would you like farming recommendations based on this weather?",
            "Should I suggest field activities based on forecast?",
        ],
    ],

    "advisory": [
        [""],
        [
            "Which crop and pest are you facing?",
            "Please tell the crop and problem.",
            "What issue is affecting your crop?",
        ],
        [
            "At what stage is the crop?",
            "Is the crop newly sown or flowering?",
            "Tell the growth stage of the crop.",
        ],
        [
            "Here is the recommended treatment.",
            "Suggested solution is provided below.",
            "This is the advised control method.",
        ],
        [
            "Would you like dosage details per acre?",
            "Do you want application timing guidance?",
            "Need more clarification?",
        ],
    ],
}

STATUS_TYPES = {
    "pmkisan_status": ["llm", "reg", "otp4", "llm"],
    "pmfby_status": ["llm", "phone", "otp6", "season", "llm"],
    "shc_status": ["llm", "phone", "cycle", "llm"],
}

MOBILE_PREFIX = ["70", "78", "80", "88", "90", "98"]

# -------------------- HELPERS --------------------

def random_profile(rng):
    prefix = rng.choice(MOBILE_PREFIX)
    return {
        "phone": prefix + "".join(rng.choices("0123456789", k=10-len(prefix))),
        "pm_kisan_reg_no": "".join(rng.choices("0123456789", k=11)),
        "shc_cycle": rng.choice(["2023-24", "2024-25"]),
    }

def short_reply(kind, profile, rng):
    if kind == "reg":
        return profile["pm_kisan_reg_no"]
    if kind == "otp4":
        return "".join(rng.choices("0123456789", k=4))
    if kind == "otp6":
        return "".join(rng.choices("0123456789", k=6))
    if kind == "phone":
        return profile["phone"]
    if kind == "cycle":
        return profile["shc_cycle"]
    if kind == "season":
        return rng.choice(["Kharif 2023", "Rabi 2024"])
    return ""

def write_jsonl(path, record):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# -------------------- FLOWS --------------------

async def generate_flow(use_case, lang, rng):
    profile = random_profile(rng)
    bot_msgs = BOT_MSGS[use_case]
    status_types = STATUS_TYPES.get(use_case)
    history, user_turns = [], []

    for i, bot_msg in enumerate(bot_msgs):
        # BOT_MSGS may have a list of alternatives per turn; pick one string
        if isinstance(bot_msg, list):
            bot_msg = rng.choice(bot_msg) if bot_msg else ""
        kind = status_types[i] if status_types and i < len(status_types) else "llm"

        if kind != "llm":
            user_msg = short_reply(kind, profile, rng)
        else:
            user_msg = await get_next_user_message(
                use_case=use_case,
                intent="Complete flow",
                assistant_message=bot_msg,
                language=lang,
                profile=profile,
                message_history=history or None,
            )
            user_msg = (user_msg or "").strip()

        user_turns.append(user_msg)
        history.append((user_msg, bot_msg))

    return user_turns

# -------------------- CONVERSATIONS --------------------

async def generate_conversation(use_case, lang, max_turns, rng):
    from synthetic.agrinet import agrinet_agent
    from synthetic.deps import FarmerContext
    from datetime import datetime

    profile = random_profile(rng)
    ctx = FarmerContext(query="", lang_code=lang, session_id="gen", today_date=datetime.now())

    history = []
    assistant_msg = ""

    for _ in range(max_turns):
        user_msg = await get_next_user_message(
            use_case=use_case,
            intent="Complete flow",
            assistant_message=assistant_msg,
            language=lang,
            profile=profile,
            message_history=history or None,
        )
        if not user_msg:
            break

        ctx.query = user_msg
        result = await agrinet_agent.run(user_prompt=user_msg, message_history=history, deps=ctx)
        assistant_msg = result.output or ""

        history.append((user_msg, assistant_msg))
        if not assistant_msg:
            break

    return [{"user": u, "assistant": a} for u, a in history]

# -------------------- MAIN --------------------

async def run(mode, output, num):
    Path(output).parent.mkdir(parents=True, exist_ok=True)

    for use_case in USE_CASES:
        for lang in LANGUAGES:
            for i in range(num):
                rng = random.Random(i + len(use_case))

                if mode == "flows":
                    data = await generate_flow(use_case, lang, rng)
                    record = {"use_case": use_case, "language": lang, "user_turns": data}
                else:
                    data = await generate_conversation(use_case, lang, 10, rng)
                    record = {"use_case": use_case, "language": lang, "turns": data}

                write_jsonl(output, record)
                print(f"✓ {mode} | {use_case} | {lang}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode", choices=["flows", "conversations"], default="flows")
    parser.add_argument("-n", "--num", type=int, default=1)
    parser.add_argument("-o", "--output", default="output.jsonl")
    args = parser.parse_args()

    asyncio.run(run(args.mode, args.output, args.num))

if __name__ == "__main__":
    main()