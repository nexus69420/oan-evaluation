---
language:
- en
- hi
license: other
license_name: restricted-access
task_categories:
- text-classification
- question-answering
pretty_name: BharatVistaar Moderation Agent Dataset
tags:
- moderation
- content-classification
- agriculture
- safety
- conversational-ai
- multilingual
- hindi
---

# BharatVistaar Moderation Agent Dataset

## Dataset Description

This dataset contains real query classification logs from the **BharatVistaar Moderation Agent**, a query validation system for BHARAT-VISTAAR (Bharat Virtually Integrated System to Access Agricultural Resources). The dataset captures how the moderation agent classifies user queries to ensure safe, relevant, and helpful agricultural advisory responses.

### Dataset Summary

- **Total Records**: {TOTAL_RECORDS}
- **Date Range**: {MIN_DATE} to {MAX_DATE}
- **Last Updated**: {LAST_UPDATED}
- **Languages**: Hindi (hi), English (en), and other Indian languages
- **Format**: Query-classification pairs with contextual conversation history
- **Agent Version**: Moderation Agent v1.0

### About BharatVistaar Moderation Agent

The **BharatVistaar Moderation Agent** is a query validation system designed to ensure that BHARAT-VISTAAR responds safely and effectively to farmer queries. Developed for the Bharat agricultural advisory platform by OpenAgriNet, Government of India, it serves as the first line of defense in maintaining platform integrity.

#### Key Responsibilities:

- ✅ **Validate Agricultural Queries**: Approve genuine farming-related questions
- 🚫 **Detect Manipulation Attempts**: Flag role obfuscation and jailbreak attempts
- 🛡️ **Content Safety**: Identify unsafe, illegal, or politically controversial content
- 🌐 **Language Policy Enforcement**: Ensure response language compliance (English/Hindi only)
- 🔄 **Context Awareness**: Maintain conversation context across multi-turn interactions

#### Classification Categories:

**Valid Queries:**
- `valid_agricultural` - Genuine farming, livestock, weather, market, scheme, or rural development queries

**Invalid Queries:**
- `invalid_non_agricultural` - No clear link to farming or agriculture
- `invalid_external_reference` - Primarily fictional sources (movies, mythology)
- `invalid_compound_mixed` - Mixed content where non-agricultural dominates
- `invalid_language` - Explicit request for unsupported response language

**Problem Content:**
- `unsafe_illegal` - Involves banned substances or illegal activities
- `political_controversial` - Requests political endorsements or comparisons
- `role_obfuscation` - Attempts to override system behavior

#### Key Principles:

- 🤝 **Generous by Default**: When uncertain, classify as valid agricultural
- 🎯 **Intent-Focused**: Prioritize what the farmer wants to know over wording
- 📚 **Context-Aware**: Consider previous conversation turns
- 🌍 **Multilingual Acceptance**: Accept queries in any language; enforce response language policy only

## Dataset Structure

### Data Fields

Each record in the dataset contains:

- **`id`** (string): Unique identifier for the moderation span
- **`timestamp`** (string): ISO 8601 timestamp of the interaction
- **`messages_json`** (string): JSON string containing the conversation history including:
  - User query to be moderated
  - Previous conversation context
  - Moderation agent's classification
  - Classification reasoning (if available)
- **`tools`** (list of strings): List of tools/APIs used in moderation (typically minimal for classification tasks)

### Example Record

```json
{
  "id": "mod123xyz",
  "timestamp": "2025-01-15T10:30:45Z",
  "messages_json": "[{\"role\": \"user\", \"content\": \"माझ्या टोमॅटोच्या पिकावर पांढरी माशी लागली आहे. काय करावे?\"}, {\"role\": \"assistant\", \"content\": \"Category: valid_agricultural\\nAction: Proceed with the query\"}]",
  "tools": []
}
```

### Classification Distribution

The dataset includes examples of all classification categories:

- **Valid Agricultural Queries**: Crop management, pest control, weather, markets, government schemes, livestock, fisheries, poultry
- **Invalid Queries**: Non-agricultural topics, external references, mixed content, language policy violations
- **Safety Issues**: Illegal substance queries, political content, role manipulation attempts
- **Contextual Follow-ups**: Short responses ("Yes", "Tell me more") in agricultural conversations
- **Multilingual Queries**: Hindi, English, and other Indian language queries with proper classification

## Usage

### Loading the Dataset

```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("kenpath/bh-moderation-agent")

# Access a sample
sample = dataset['train'][0]
print(f"Timestamp: {sample['timestamp']}")

# Parse the moderation conversation
import json
messages = json.loads(sample['messages_json'])
for msg in messages:
    print(f"{msg['role']}: {msg['content']}")
```

## Use Cases

This dataset can be used for:

1. **Training Content Moderation Models**: Fine-tune models to classify agricultural queries and detect problematic content
2. **Multilingual Classification Research**: Study cross-lingual query classification in agricultural contexts
3. **Safety System Development**: Build robust content filtering systems for domain-specific applications
4. **Conversational Context Understanding**: Research how to maintain context in multi-turn moderation
5. **Jailbreak Detection**: Study patterns in role obfuscation and system manipulation attempts
6. **Agricultural Domain Analysis**: Understand the boundaries of agricultural vs non-agricultural content
7. **Policy Compliance Testing**: Benchmark moderation systems against language and content policies

## Privacy & Ethical Considerations

- ✅ **PII Protection**: All Personally Identifiable Information has been masked or removed
- ✅ **User Consent**: Data collection follows appropriate consent protocols
- ✅ **Balanced Representation**: Dataset includes both valid and invalid query examples
- ⚠️ **Restricted Access**: This dataset is private and access is limited to authorized users
- ⚠️ **Contextual Use**: Moderation decisions should be understood within agricultural advisory context
- ⚠️ **Continuous Improvement**: Moderation policies evolve; dataset reflects historical decisions

## Moderation Philosophy

The BharatVistaar Moderation Agent follows a **farmer-first philosophy**:

- **Generous by Default**: Prioritizes helping farmers over blocking queries
- **Intent Over Form**: Focuses on what farmers want to know, not how they ask
- **Context-Aware**: Understands conversations, not just individual messages
- **Multilingual**: Accepts queries in any language while enforcing response language policy
- **Safety-Conscious**: Blocks harmful content while allowing genuine agricultural discussions

## License

This dataset is provided under a restricted access license. Contact the dataset owners for access terms and conditions.

**Dataset Maintenance**: This dataset is updated periodically with new moderation logs to improve classification accuracy and policy enforcement.

