"""
SatQuery AI — Fine-Tuning Execution Script
Prepares multi-task datasets from VRSBench, RSVQA, CDVQA, and BigEarthNet,
and fine-tunes Moondream2 using PEFT / QLoRA on local GPU (RTX 5050 8GB).
"""

import os
import sys
import argparse

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from satquery.training.dataset_formatter import RemoteSensingDataFormatter
from satquery.training.train import train_satquery_qlora

def main():
    parser = argparse.ArgumentParser(description="Train Moondream2 on SatQuery AI Datasets")
    parser.add_argument("--data-dir", default=r"E:\SatQuery AI\data\full_datasets", help="Path to full datasets directory")
    parser.add_argument("--output-dir", default=r"E:\SatQuery AI\checkpoints\moondream_satquery_lora", help="Checkpoint output directory")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--batch-size", type=int, default=1, help="Per-device batch size (1 recommended for 8GB VRAM)")
    parser.add_argument("--grad-accum", type=int, default=8, help="Gradient accumulation steps")
    parser.add_argument("--max-samples", type=int, default=5000, help="Max samples per dataset for balanced multi-task training")
    
    args = parser.parse_args()
    
    print("=" * 65)
    print("🛰️ SatQuery AI — Multi-Dataset Fine-Tuning Pipeline")
    print(f"Data Source: {args.data_dir}")
    print(f"Checkpoints: {args.output_dir}")
    print(f"Hardware:    NVIDIA RTX 5050 (8GB VRAM optimized)")
    print("=" * 65)
    
    # Step 1: Parse and consolidate datasets
    formatter = RemoteSensingDataFormatter(args.data_dir)
    unified_records = formatter.build_unified_training_dataset(max_samples_per_ds=args.max_samples)
    
    if not unified_records:
        print("\n⚠️ No dataset records found. Make sure the dataset download has completed in:")
        print(f"   {args.data_dir}")
        return
        
    # Step 2: Launch fine-tuning loop
    train_satquery_qlora(
        dataset_records=unified_records,
        output_dir=args.output_dir,
        epochs=args.epochs,
        lr=args.lr,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum
    )

if __name__ == "__main__":
    main()
