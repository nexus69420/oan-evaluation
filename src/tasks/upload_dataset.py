import os
import json
from pathlib import Path
from dotenv import load_dotenv
from datasets import load_dataset
from huggingface_hub import HfApi
from argparse import ArgumentParser

# Load environment variables
load_dotenv()

# Static paths
LOCAL_DATASET_PATH = Path("data/hf_dataset_staging")
LOCAL_README_PATH = Path("data/hf_dataset_staging/README.md")
METADATA_PATH = Path("data/hf_dataset_staging/metadata.json")


def main(max_shard_size: str = "500MB"):
    """
    Upload pre-processed dataset to HuggingFace Hub.
    
    Args:
        max_shard_size: Maximum size per shard (e.g., "100MB", "500MB")
    """
    print("="*60)
    print("📤 HuggingFace Dataset Upload")
    print("="*60)
    
    # Check if local dataset exists
    if not LOCAL_DATASET_PATH.exists():
        print(f"❌ Error: Dataset not found at {LOCAL_DATASET_PATH}")
        print(f"   Run prepare_dataset.py first!")
        return
    
    # Load metadata
    if not METADATA_PATH.exists():
        print(f"❌ Error: Metadata not found at {METADATA_PATH}")
        print(f"   Run prepare_dataset.py first!")
        return
    
    with open(METADATA_PATH, 'r') as f:
        metadata = json.load(f)
    
    dataset_name = metadata['dataset_name']
    token = os.getenv("HUGGINGFACE_WRITE_TOKEN")
    
    print(f"\nDataset: {dataset_name}")
    print(f"Total records: {metadata['total_records']:,}")
    print(f"Shard size: {max_shard_size}")
    
    # Load README
    if not LOCAL_README_PATH.exists():
        print(f"⚠️  Warning: README not found at {LOCAL_README_PATH}")
        readme_content = None
    else:
        with open(LOCAL_README_PATH, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    
    # Load dataset from Parquet file
    print(f"\nLoading dataset from parquet file...")
    dataset = load_dataset('parquet', data_files=str(LOCAL_DATASET_PATH / "dataset.parquet"), split='train')
    print(f"✓ Loaded {len(dataset)} records")
    
    # Determine commit message
    if metadata['had_existing_dataset']:
        commit_msg = f"Update: Added {metadata['new_count']} new records (Total: {metadata['total_records']})"
    else:
        commit_msg = f"Initial upload: {metadata['total_records']} records"
    
    print(f"\n⏳ Uploading to HuggingFace Hub...")
    print(f"   Commit message: {commit_msg}")
    print(f"   This may take a while for large datasets...")
    
    try:
        # Upload dataset - NO multiprocessing, simple and clean
        dataset.push_to_hub(
            repo_id=dataset_name,
            private=True,
            commit_message=commit_msg,
            token=token,
            max_shard_size=max_shard_size
        )
        print("✓ Dataset uploaded successfully!")
        
    except Exception as e:
        print(f"\n❌ Error uploading dataset: {e}")
        print(f"\n💡 Troubleshooting tips:")
        print(f"   1. Check your internet connection")
        print(f"   2. Verify your HuggingFace token is valid")
        print(f"   3. Try with a larger shard size: --max-shard-size '500MB'")
        print(f"   4. Run again - the upload will resume from where it left off")
        return
    
    # Upload README
    if readme_content:
        print(f"\n⏳ Uploading README...")
        try:
            api = HfApi()
            api.upload_file(
                path_or_fileobj=readme_content.encode('utf-8'),
                path_in_repo="README.md",
                repo_id=dataset_name,
                repo_type="dataset",
                token=token,
                commit_message="Update dataset card with latest statistics"
            )
            print("✓ README uploaded successfully!")
        except Exception as e:
            print(f"⚠️  Warning: Failed to upload README: {e}")
            print(f"   You can manually update it on HuggingFace")
    
    # Print summary
    stats = metadata['stats']
    print("\n" + "="*60)
    print("✅ Upload complete!")
    print("="*60)
    if metadata['had_existing_dataset']:
        print(f"📊 Summary:")
        print(f"   - Previous records: {metadata['existing_count']:,}")
        print(f"   - New records added: {metadata['new_count']:,}")
        print(f"   - Total records: {metadata['total_records']:,}")
        print(f"   - Date range: {stats['min_date']} to {stats['max_date']}")
    else:
        print(f"📊 Initial Dataset:")
        print(f"   - Total records: {metadata['total_records']:,}")
        print(f"   - Date range: {stats['min_date']} to {stats['max_date']}")
    print(f"\n🔗 Dataset URL:")
    print(f"   https://huggingface.co/datasets/{dataset_name}")
    print("="*60)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Upload pre-processed dataset to HuggingFace Hub. "
                    "Run prepare_dataset.py first to create the local dataset."
    )
    parser.add_argument(
        "--max-shard-size",
        type=str,
        default="500MB",
        help="Maximum size per shard for upload (default: '500MB'). "
             "Use smaller values (e.g., '100MB') for unstable connections."
    )
    
    args = parser.parse_args()
    main(args.max_shard_size)


