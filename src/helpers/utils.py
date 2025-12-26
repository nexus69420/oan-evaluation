import logging
import json
import tiktoken
import pytz
import datetime
from jinja2 import Environment, FileSystemLoader
from typing import Dict

def get_today_date_str() -> str:
    """Get today's date as a string in the format Monday, 23rd May 2025."""
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist)
    return today.strftime('%A, %d %B %Y')

def get_logger(name):
    """Get logger object."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def count_tokens_str(doc: str) -> int:
    """Count tokens in a string.

    Args:
        doc (str): String to count tokens for.
    Returns:
        int: number of tokens in the string

    """
    encoder = tiktoken.get_encoding('cl100k_base')
    return len(encoder.encode(doc, disallowed_special=()))


def count_tokens_for_part(part) -> int:
    """Count tokens for a message part, handling different part types appropriately.
    
    Args:
        part: A message part (TextPart, ToolCallPart, etc.)
    Returns:
        int: number of tokens in the part
    """
    if hasattr(part, 'content'):
        return count_tokens_str(str(part.content))
    elif hasattr(part, 'part_kind') and part.part_kind == 'tool-call':
        # For tool calls, create a string representation of the tool name and args
        tool_str = f"tool: {part.tool_name}, args: {json.dumps(part.args)}"
        return count_tokens_str(tool_str)
    elif hasattr(part, 'part_kind') and part.part_kind == 'tool-return':
        # For tool returns, use the result content
        return count_tokens_str(str(part.content))
    else:
        # For unknown part types, return 0 tokens
        return 0


def get_prompt(prompt_file: str, context: Dict = {}, prompt_dir: str = "assets/prompts") -> str:
    """Load a prompt from a file and format it with a context using Jinja2 templating.

    Args:
        prompt_file (str): Name of the prompt file.
        context (dict, optional): Context to format the prompt with. Defaults to {}.
        prompt_dir (str, optional): Path to the prompt directory. Defaults to 'assets/prompts'.

    Returns:
        str: prompt
    """
    # if extension is not .md, add it
    if not prompt_file.endswith(".md"):
        prompt_file += ".md"

    # Create Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(prompt_dir),
        autoescape=False  # We don't want HTML escaping for our prompts
    )

    # Get the template
    template = env.get_template(prompt_file)

    # Render the template with the context
    prompt = template.render(**context) if context else template.render()

    return prompt
