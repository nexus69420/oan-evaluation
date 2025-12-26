import os
import sys
import asyncio
from pathlib import Path
import json
from argparse import ArgumentParser
import datetime as dt
import gc
from dotenv import load_dotenv
from datasets import Dataset, Features, Sequence, Value, load_dataset, concatenate_datasets

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.datautils import LogFireClient
from src.datautils.utils import create_record

# Load environment variables
load_dotenv()

# Static paths
LOCAL_DATASET_PATH = Path("data/hf_dataset_staging")
LOCAL_README_PATH = Path("data/hf_dataset_staging/README.md")


def calculate_stats(dataset):
    """Calculate statistics from the dataset."""
    total_records = len(dataset)
    
    # Extract timestamps
    timestamps = [dt.datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')) 
                  for record in dataset]
    min_date = min(timestamps).strftime('%Y-%m-%d')
    max_date = max(timestamps).strftime('%Y-%m-%d')
    last_updated = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
    
    return {
        'total_records': total_records,
        'min_date': min_date,
        'max_date': max_date,
        'last_updated': last_updated
    }


def generate_readme(agent_name: str, stats: dict, template_dir: str = "assets/docs") -> str:
    """Generate README content from template with populated statistics."""
    template_path = Path(template_dir) / f"{agent_name.lower().replace(' ', '-')}.md"
    
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        readme_content = f.read()
    
    # Replace placeholders
    replacements = {
        '{TOTAL_RECORDS}': f"{stats['total_records']:,}",
        '{MIN_DATE}': stats['min_date'],
        '{MAX_DATE}': stats['max_date'],
        '{LAST_UPDATED}': stats['last_updated']
    }
    
    for placeholder, value in replacements.items():
        readme_content = readme_content.replace(placeholder, value)
    
    return readme_content


async def main(agent_name: str, minutes_window: int, batch_size: int = 5000, rate_limit_pause: float = 1.0):
    """
    Fetch logs from LogFire, merge with existing HuggingFace dataset, and save locally.
    
    Args:
        agent_name: Name of the agent to filter logs
        minutes_window: Minutes window for fetching logs
        batch_size: Number of records to process per batch (default: 5000)
        rate_limit_pause: Pause duration between API requests in seconds (default: 1.0)
    """
    # Construct dataset name
    dataset_name = f"kenpath/mh-{agent_name.lower().replace(' ', '-')}"
    token = os.getenv("HUGGINGFACE_WRITE_TOKEN")
    
    print(f"Dataset: {dataset_name}")
    print(f"Agent: {agent_name}")
    print(f"Local output path: {LOCAL_DATASET_PATH}")
    
    # Check if dataset exists on HuggingFace
    print("\nChecking if dataset exists on HuggingFace...")
    from huggingface_hub import HfApi
    api = HfApi()
    dataset_exists = False
    
    try:
        api.dataset_info(repo_id=dataset_name, token=token)
        dataset_exists = True
        print(f"✓ Dataset exists on HuggingFace Hub")
    except Exception:
        print(f"✗ Dataset does not exist (will create new dataset)")
    
    # Load existing dataset or determine start date
    existing_dataset = None
    START_AT = None
    
    if dataset_exists:
        try:
            print("  Loading existing dataset from HuggingFace...")
            existing_dataset = load_dataset(dataset_name, token=token, split='train')
            print(f"  ✓ Loaded {len(existing_dataset)} existing records")
            
            # Get the last timestamp from existing dataset
            timestamps = [dt.datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')) 
                         for record in existing_dataset]
            last_timestamp = max(timestamps)
            START_AT = last_timestamp
            
            print(f"  Last record timestamp: {last_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
        except Exception as e:
            print(f"  ✗ Error loading dataset: {e}")
            print(f"  Will create new dataset from last 30 days")
            START_AT = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
    else:
        # New dataset - fetch last 30 days
        print(f"  Creating new dataset from last 30 days")
        START_AT = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
    
    # Calculate end date
    END_AT = dt.datetime.now(dt.timezone.utc)
    
    print(f"\nFetching new logs:")
    print(f"  From: {START_AT.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  To:   {END_AT.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Minutes window: {minutes_window}")
    print(f"  Rate limit pause: {rate_limit_pause}s")
    
    # Initialize client
    client = LogFireClient(read_token=os.getenv("LOGFIRE_READ_TOKEN"))
    
    # Fetch logs
    logs_data = await client.fetch_logs(
        columns=['span_id', 'created_at', 'attributes'],
        start_at=START_AT,
        end_at=END_AT,
        minutes_window=minutes_window,
        agent_name=agent_name,
        rate_limit_pause=rate_limit_pause,
    )
    
    print(f"Fetched {len(logs_data)} logs")
    
    # Deduplicate logs using span_id (much more memory efficient)
    seen_ids = set()
    deduped = []
    for entry in logs_data:
        span_id = entry.get('span_id')
        if span_id and span_id not in seen_ids:
            seen_ids.add(span_id)
            deduped.append(entry)
    
    print(f"After deduplication: {len(deduped)} logs")
    
    # Free memory
    del logs_data
    del seen_ids
    logs_data = deduped
    gc.collect()  # Force garbage collection
    
    # Define dataset features
    features = Features(
        id=Value("string"),
        timestamp=Value("string"),
        messages_json=Value("string"),
        tools=Sequence(Value("string")),
    )
    
    # Create new dataset from fetched logs in batches to reduce memory usage
    print(f"Creating dataset from {len(logs_data)} records (batch size: {batch_size})...")
    batches = []
    
    for i in range(0, len(logs_data), batch_size):
        batch_data = logs_data[i:i+batch_size]
        batch_records = [create_record(span) for span in batch_data]
        batch_dataset = Dataset.from_list(batch_records, features=features)
        batches.append(batch_dataset)
        print(f"  Processed batch {len(batches)}: {len(batch_dataset)} records")
        
        # Free batch memory
        del batch_data
        del batch_records
    
    # Combine all batches
    if len(batches) > 1:
        print(f"Combining {len(batches)} batches...")
        new_dataset = concatenate_datasets(batches)
        del batches  # Free memory
        gc.collect()
    else:
        new_dataset = batches[0]
    
    # Free logs_data memory
    del logs_data
    gc.collect()
    
    print(f"Created new dataset with {len(new_dataset)} records")
    
    # Combine with existing dataset if available
    if existing_dataset is not None:
        print(f"\nCombining datasets...")
        existing_count = len(existing_dataset)
        new_count = len(new_dataset)
        print(f"  Existing records: {existing_count:,}")
        print(f"  New records: {new_count:,}")
        
        # Concatenate datasets
        combined_dataset = concatenate_datasets([existing_dataset, new_dataset])
        print(f"  Combined total: {len(combined_dataset):,}")
        
        # Save flag for later
        had_existing_dataset = True
        
        # Free memory
        del existing_dataset
        del new_dataset
        gc.collect()
        
        # Deduplicate based on 'id' field - process in chunks for better memory efficiency
        print("  Deduplicating by ID...")
        seen_ids = set()
        unique_indices = []
        
        # Process in batches to reduce memory pressure
        chunk_size = 10000
        for start_idx in range(0, len(combined_dataset), chunk_size):
            end_idx = min(start_idx + chunk_size, len(combined_dataset))
            for idx in range(start_idx, end_idx):
                record_id = combined_dataset[idx]['id']
                if record_id not in seen_ids:
                    seen_ids.add(record_id)
                    unique_indices.append(idx)
            
            print(f"    Processed {end_idx:,}/{len(combined_dataset):,} records")
        
        print(f"  Found {len(unique_indices):,} unique records")
        dataset = combined_dataset.select(unique_indices)
        print(f"  After deduplication: {len(dataset):,} records")
        
        # Free memory
        del combined_dataset
        del seen_ids
        del unique_indices
        gc.collect()
        
        # Sort by timestamp (newest first)
        print("  Sorting by timestamp...")
        dataset = dataset.sort('timestamp', reverse=True)
        
    else:
        dataset = new_dataset
        had_existing_dataset = False
        new_count = len(new_dataset)
        print(f"  No existing dataset to combine with")
    
    print(f"\nFinal dataset size: {len(dataset):,} records")
    
    # Calculate statistics
    print("\nCalculating dataset statistics...")
    stats = calculate_stats(dataset)
    print(f"  - Total records: {stats['total_records']:,}")
    print(f"  - Date range: {stats['min_date']} to {stats['max_date']}")
    print(f"  - Last updated: {stats['last_updated']}")
    
    # Generate README from template with stats
    print("\nGenerating dataset card...")
    readme_content = generate_readme(agent_name, stats)
    
    # Save dataset locally
    print(f"\nSaving dataset locally to {LOCAL_DATASET_PATH}...")
    if LOCAL_DATASET_PATH.exists():
        import shutil
        shutil.rmtree(LOCAL_DATASET_PATH)
    
    LOCAL_DATASET_PATH.mkdir(parents=True, exist_ok=True)
    
    # Save as Parquet format to avoid Windows multiprocessing issues
    # Parquet is more memory efficient and avoids pickling large objects
    print("  Saving as Parquet format (more memory efficient)...")
    dataset.to_parquet(str(LOCAL_DATASET_PATH / "dataset.parquet"))
    print(f"  ✓ Dataset saved")
    
    # Save README
    with open(LOCAL_README_PATH, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  ✓ README saved")
    
    # Save metadata for upload script
    metadata = {
        'dataset_name': dataset_name,
        'agent_name': agent_name,
        'total_records': len(dataset),
        'had_existing_dataset': had_existing_dataset,
        'new_count': new_count if had_existing_dataset else len(dataset),
        'existing_count': existing_count if had_existing_dataset else 0,
        'stats': stats
    }
    
    with open(LOCAL_DATASET_PATH / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  ✓ Metadata saved")
    
    print("\n" + "="*60)
    print("✅ Dataset preparation complete!")
    print("="*60)
    if had_existing_dataset:
        print(f"📊 Summary:")
        print(f"   - Previous records: {existing_count:,}")
        print(f"   - New records added: {new_count:,}")
        print(f"   - Total records: {len(dataset):,}")
        print(f"   - Date range: {stats['min_date']} to {stats['max_date']}")
    else:
        print(f"📊 Initial Dataset:")
        print(f"   - Total records: {len(dataset):,}")
        print(f"   - Date range: {stats['min_date']} to {stats['max_date']}")
    print(f"\n📁 Local files:")
    print(f"   - Dataset: {LOCAL_DATASET_PATH / 'dataset.parquet'}")
    print(f"   - README: {LOCAL_README_PATH}")
    print(f"   - Metadata: {LOCAL_DATASET_PATH / 'metadata.json'}")
    print(f"\n🚀 Next step: Run upload_dataset.py to push to HuggingFace")
    print("="*60)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Fetch logs from LogFire and merge with existing HuggingFace dataset. "
                    "Saves everything locally for later upload."
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        default="Vistaar Agent",  # Options: Vistaar Agent, Moderation Agent, or Suggestions Agent
        help="Name of the agent to filter logs (default: 'Vistaar Agent')"
    )
    parser.add_argument(
        "--minutes-window",
        type=int,
        default=15,
        help="Minutes window for fetching logs (default: 15)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Number of records to process per batch (default: 5000). Lower values use less memory."
    )
    parser.add_argument(
        "--rate-limit-pause",
        type=float,
        default=1.0,
        help="Pause duration between API requests in seconds (default: 1.0)"
    )
    
    args = parser.parse_args()
    
    # Run async main function
    asyncio.run(main(args.agent_name, args.minutes_window, args.batch_size, args.rate_limit_pause))

