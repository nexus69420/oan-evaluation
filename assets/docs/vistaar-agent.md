---
language:
- en
- hi
license: other
license_name: restricted-access
task_categories:
- question-answering
- text-generation
pretty_name: BharatVistaar Agent Conversation Dataset
tags:
- agriculture
- ai-agent
- conversational-ai
- multilingual
- hindi
- digital-public-infrastructure
---

# BharatVistaar Agent Conversation Dataset

## Dataset Description

This dataset contains real conversation logs from the **BharatVistaar AI Agent**, India's first AI-powered agricultural advisory and information system. The dataset captures authentic farmer interactions with the agent, including queries about crops, weather, market prices, government schemes, and agricultural best practices.

### Dataset Summary

- **Total Records**: {TOTAL_RECORDS}
- **Date Range**: {MIN_DATE} to {MAX_DATE}
- **Last Updated**: {LAST_UPDATED}
- **Languages**: Hindi (mr), English (en)
- **Format**: Conversational turns with tool usage traces
- **Agent Version**: Vistaar Agent v1.0

### About BharatVistaar

**BharatVistaar** is a Digital Public Infrastructure (DPI) powered by Artificial Intelligence, designed to bring expert agricultural knowledge to every farmer in clear, simple language. As the first AI-powered agricultural advisory and information system in India, it helps farmers grow better, reduce risks, and make informed choices.

This initiative is developed in collaboration with:
- **VISTAAR** (Virtually Integrated System To Access Agricultural Resources) – a national open network for agricultural advisory under the Ministry of Agriculture & Farmers Welfare
<!-- - **Maharashtra Department of Agriculture** -->

#### What BharatVistaar Helps Farmers With:

- 📊 Location-based commodity prices for crops
- 🌤️ Current and upcoming weather forecasts
- 🌾 Crop selection guidance for specific regions
- 🐛 Pest and disease management advice
- 📚 Best practices for specific crops
- 💰 Government agriculture schemes and subsidies information
- 🏦 Check eligibility, application, and payment status for central schemes such as PM-KISAN, PMFBY, and SHC
- 📝 File and track grievances for PM Kisan benefits
- 🧬 Soil health data and advisory

#### Benefits for Farmers:

- ✅ Information in their own language (Hindi or English)
- ⏰ Available 24/7, accessible from mobile or computer
- 🔗 Combines knowledge from multiple trusted sources
- 🎯 Personalized advice based on location and land holdings
- 📈 Continuous improvement based on farmer needs

#### Data Sources

BharatVistaar integrates information from verified, domain-authenticated repositories:
- **Agricultural Knowledge**: Package of Practices from agricultural universities and research institutions
- **Weather Data**: India Meteorological Department (IMD) forecasts.
- **Market Prices**: APMC (Agricultural Produce Market Committees) data
- **Government Schemes**: Ministry of Agriculture and State Government databases
- **Application Status**: PM-Kisan, PMFBY, and Soil Health Card status via central government APIs

## Dataset Structure

### Data Fields

Each record in the dataset contains:

- **`id`** (string): Unique identifier for the conversation span
- **`timestamp`** (string): ISO 8601 timestamp of the interaction
- **`messages_json`** (string): JSON string containing the full conversation history including:
  - User messages (farmer queries)
  - Assistant messages (agent responses)
  - Tool calls (API invocations for fetching data)
  - Tool results (API responses)
- **`tools`** (list of strings): List of tools/APIs used in this conversation (e.g., `["search_documents", "weather_forecast", "get_mandi_prices"]`)

### Example Record

```json
{
  "id": "abc123xyz",
  "timestamp": "2025-01-15T10:30:45Z",
  "messages_json": "[{\"role\": \"user\", \"content\": \"टोमॅटोच्या पिकावर पांढरी माशी लागली आहे. काय करावे?\"}, {\"role\": \"assistant\", \"content\": \"...\", \"tool_calls\": [...]}]",
  "tools": ["search_terms", "search_documents"]
}
```

## Usage

### Loading the Dataset

```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("kenpath/bh-vistaar-agent")

# Access a sample
sample = dataset['train'][0]
print(f"Timestamp: {sample['timestamp']}")
print(f"Tools used: {sample['tools']}")

# Parse the conversation
import json
messages = json.loads(sample['messages_json'])
for msg in messages:
    print(f"{msg['role']}: {msg['content'][:100]}...")
```

### Parsing Tool Usage

```python
import json

def extract_tool_calls(record):
    """Extract all tool calls from a conversation record"""
    messages = json.loads(record['messages_json'])
    tool_calls = []
    
    for msg in messages:
        if msg.get('role') == 'assistant' and 'tool_calls' in msg:
            for tool_call in msg['tool_calls']:
                tool_calls.append({
                    'tool': tool_call['function']['name'],
                    'arguments': json.loads(tool_call['function']['arguments'])
                })
    
    return tool_calls

# Example usage
tool_calls = extract_tool_calls(dataset['train'][0])
print(tool_calls)
```

## Use Cases

This dataset can be used for:

1. **Fine-tuning Agricultural AI Assistants**: Train models to handle farmer queries with appropriate tool usage
2. **Multilingual NLP Research**: Study code-switching and transliteration in Hindi-English agricultural contexts
3. **Tool-Use Learning**: Understand when and how AI agents invoke external APIs
4. **Agricultural Domain Analysis**: Study common farmer information needs and query patterns
5. **Conversational AI Evaluation**: Benchmark agent performance on real-world agricultural queries

## Privacy & Ethical Considerations

- ✅ **PII Protection**: All Personally Identifiable Information has been masked or removed
- ✅ **Farmer Consent**: Data collection follows appropriate consent protocols
- ✅ **Data Anonymization**: Personal details such as phone numbers, registration numbers, and Aadhaar are masked in all records
- ⚠️ **Restricted Access**: This dataset is private and access is limited to authorized users
- ⚠️ **Agricultural Context**: Information should be validated before application in real farming scenarios
