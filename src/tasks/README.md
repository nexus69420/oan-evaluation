# Dataset Management Scripts

This directory contains scripts for managing HuggingFace datasets with LogFire data.

## Overview

The dataset management has been split into two separate scripts to avoid macOS multiprocessing fork issues and improve reliability:

1. **`prepare_dataset.py`** - Downloads, processes, and saves data locally
2. **`upload_dataset.py`** - Uploads the pre-processed data to HuggingFace Hub

## Workflow

### Step 1: Prepare Dataset

Download logs from LogFire, merge with existing HuggingFace data, and save locally:

```bash
python src/tasks/prepare_dataset.py --agent-name "Vistaar Agent" --hours-window 1
```

**Options:**
- `--agent-name`: Name of the agent to filter logs (default: "Vistaar Agent")
- `--hours-window`: Hours window for fetching logs (default: 1)
- `--batch-size`: Number of records to process per batch (default: 5000)

**Output:**
- Dataset saved to: `data/hf_dataset_staging/dataset/`
- README saved to: `data/hf_dataset_staging/README.md`
- Metadata saved to: `data/hf_dataset_staging/metadata.json`

### Step 2: Upload Dataset

Upload the prepared dataset to HuggingFace:

```bash
python src/tasks/upload_dataset.py
```

**Options:**
- `--max-shard-size`: Maximum size per shard (default: "500MB")
  - Use smaller values like "100MB" for unstable connections
  - Use larger values like "1GB" for fast, stable connections

### Example: Complete Update

```bash
# Step 1: Prepare the data
python src/tasks/prepare_dataset.py --agent-name "Vistaar Agent" --minutes-window 10 --batch-size 8000 --rate-limit-pause 0.5

# Step 2: Upload to HuggingFace
python src/tasks/upload_dataset.py --max-shard-size "500MB"
```

## Memory Management

The scripts include several optimizations for handling large datasets:

- **Batch processing**: Records are processed in batches (default 5,000 per batch)
- **Chunked deduplication**: Large datasets are deduplicated in chunks
- **Aggressive garbage collection**: Explicit memory cleanup after major operations
- **Disk-based storage**: Data is saved to disk between steps

### For Systems with Limited RAM

If you're running out of memory:

```bash
# Use smaller batch sizes
python src/tasks/prepare_dataset.py \
  --agent-name "Vistaar Agent" \
  --batch-size 2000
```

## Troubleshooting

### "Dataset not found" error on upload

Run `prepare_dataset.py` first to create the local dataset.

### Upload fails or times out

Try using a smaller shard size:
```bash
python src/tasks/upload_dataset.py --max-shard-size "50MB"
```

### Out of memory during preparation

Reduce the batch size:
```bash
python src/tasks/prepare_dataset.py --batch-size 2000
```

### Want to re-upload without re-downloading

Just run `upload_dataset.py` again - the prepared data is already saved locally.

## Environment Variables

Required environment variables (set in `.env`):
- `LOGFIRE_READ_TOKEN`: Token for reading from LogFire
- `HUGGINGFACE_WRITE_TOKEN`: Token for writing to HuggingFace Hub

## Legacy Script

`update_dataset.py` is deprecated but still functional. It combines both steps into a single script but may encounter macOS fork issues with large datasets.

## File Structure

```
src/tasks/
├── prepare_dataset.py    # Step 1: Download and process
├── upload_dataset.py     # Step 2: Upload to HuggingFace
└── README.md            # This file

data/hf_dataset_staging/  # Local staging area
├── dataset/             # Arrow format dataset
├── README.md           # Generated dataset card
└── metadata.json       # Dataset metadata
```


