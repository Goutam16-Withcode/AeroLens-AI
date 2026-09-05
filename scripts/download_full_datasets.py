"""
SatQuery AI — Full Dataset Downloader
Downloads the complete datasets into E:\SatQuery AI\data\full_datasets (or a user-specified path).

Datasets:
1. VRSBench (HuggingFace: xiang709/VRSBench) ~15-20 GB
2. RSVQA (Official: rsvqa.sylvainlobry.com) LR: ~772 MB, HR: ~12.3 GB
3. CDVQA (GitHub & Dataset Archives) ~5-10 GB
4. BigEarthNet (Sentinel-1 SAR + Sentinel-2 Optical) ~65-110 GB
"""

import os
import sys
import shutil
import zipfile
import tarfile
import argparse
import requests
from tqdm import tqdm

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_DEST_DIR = r"E:\SatQuery AI\data\full_datasets"

def download_file_with_progress(url: str, dest_path: str, chunk_size: int = 1024 * 1024):
    """Downloads a file over HTTP/HTTPS with a progress bar."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    total_size = int(resp.headers.get("content-length", 0))
    
    with open(dest_path, "wb") as f, tqdm(
        desc=os.path.basename(dest_path),
        total=total_size,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))

# -----------------------------------------------------------------------------
# 1. VRSBench Full Downloader
# -----------------------------------------------------------------------------
def download_vrsbench(dest_dir: str):
    target = os.path.join(dest_dir, "vrsbench")
    os.makedirs(target, exist_ok=True)
    print("\n" + "=" * 60)
    print("📥 Downloading Full VRSBench Dataset (~15-20 GB)...")
    print(f"Destination: {target}")
    print("=" * 60)
    
    try:
        from huggingface_hub import snapshot_download
        print("Using huggingface_hub snapshot_download for 'xiang709/VRSBench'...")
        snapshot_download(
            repo_id="xiang709/VRSBench",
            repo_type="dataset",
            local_dir=target,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print("✓ VRSBench download complete!")
    except Exception as e:
        print(f"❌ Error during VRSBench download: {e}")
        print("Alternative CLI command:")
        print(f"  huggingface-cli download xiang709/VRSBench --repo-type dataset --local-dir \"{target}\"")

# -----------------------------------------------------------------------------
# 2. RSVQA Full Downloader
# -----------------------------------------------------------------------------
def download_rsvqa(dest_dir: str, mode: str = "LR"):
    target = os.path.join(dest_dir, "rsvqa")
    os.makedirs(target, exist_ok=True)
    print("\n" + "=" * 60)
    print(f"📥 Downloading RSVQA Dataset ({mode})...")
    print(f"Destination: {target}")
    print("=" * 60)
    
    # Official Sylvain Lobry dataset links
    urls = {
        "LR": "https://rsvqa.sylvainlobry.com/RSVQA_LR.zip",
        "HR": "https://rsvqa.sylvainlobry.com/RSVQA_HR.zip"
    }
    
    url = urls.get(mode, urls["LR"])
    zip_name = os.path.basename(url)
    zip_path = os.path.join(target, zip_name)
    
    try:
        print(f"Downloading from {url} ...")
        download_file_with_progress(url, zip_path)
        print("Extracting archive...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(target)
        print(f"✓ RSVQA {mode} downloaded and extracted successfully!")
    except Exception as e:
        print(f"❌ Error downloading RSVQA: {e}")
        print(f"You can manually download from: https://rsvqa.sylvainlobry.com/ into '{target}'")

# -----------------------------------------------------------------------------
# 3. CDVQA Full Downloader
# -----------------------------------------------------------------------------
def download_cdvqa(dest_dir: str):
    target = os.path.join(dest_dir, "cdvqa")
    os.makedirs(target, exist_ok=True)
    print("\n" + "=" * 60)
    print("📥 Downloading CDVQA Repository & Dataset Setup...")
    print(f"Destination: {target}")
    print("=" * 60)
    
    repo_url = "https://github.com/YZHJessica/CDVQA.git"
    try:
        import subprocess
        print(f"Cloning {repo_url} into {target}...")
        subprocess.run(["git", "clone", repo_url, target], check=False)
        print("✓ CDVQA repository cloned.")
        print("\nNote for CDVQA image archives:")
        print("The CDVQA authors host the raw bi-temporal image crops on Google Drive & Baidu Netdisk.")
        print(f"Please check the README in '{target}' for direct download links to LEVIR-CD / WHU-CD change pairs.")
    except Exception as e:
        print(f"❌ Error setting up CDVQA: {e}")

# -----------------------------------------------------------------------------
# 4. BigEarthNet Full Downloader
# -----------------------------------------------------------------------------
def download_bigearthnet(dest_dir: str):
    target = os.path.join(dest_dir, "bigearthnet")
    os.makedirs(target, exist_ok=True)
    print("\n" + "=" * 60)
    print("📥 Downloading BigEarthNet Optical-SAR Dataset...")
    print(f"Destination: {target}")
    print("=" * 60)
    
    try:
        from huggingface_hub import snapshot_download
        print("Downloading GFM-Bench/BigEarthNet from Hugging Face...")
        snapshot_download(
            repo_id="GFM-Bench/BigEarthNet",
            repo_type="dataset",
            local_dir=target,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print("✓ BigEarthNet download complete!")
    except Exception as e:
        print(f"❌ Error during BigEarthNet download: {e}")
        print("Alternative options:")
        print("1. Official BigEarthNet archive: https://bigearth.net/")
        print("2. TFDS: tensorflow_datasets.load('bigearthnet')")
        print(f"3. huggingface-cli download GFM-Bench/BigEarthNet --repo-type dataset --local-dir \"{target}\"")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="SatQuery AI Full Dataset Downloader")
    parser.add_argument(
        "--dataset", 
        choices=["vrsbench", "rsvqa", "cdvqa", "bigearthnet", "all"], 
        default="all",
        help="Which dataset to download (default: all)"
    )
    parser.add_argument(
        "--output-dir", 
        default=DEFAULT_DEST_DIR,
        help=f"Destination directory (default: {DEFAULT_DEST_DIR})"
    )
    parser.add_argument(
        "--rsvqa-mode", 
        choices=["LR", "HR"], 
        default="LR",
        help="RSVQA resolution mode: LR (Low-Res ~772MB) or HR (High-Res ~12.3GB)"
    )
    
    args = parser.parse_args()
    dest = os.path.abspath(args.output_dir)
    os.makedirs(dest, exist_ok=True)
    
    print("=" * 60)
    print("🛰️  SatQuery AI — Full Dataset Download Utility")
    print(f"Target Directory: {dest}")
    print(f"Selected:         {args.dataset.upper()}")
    print("=" * 60)
    
    if args.dataset in ["vrsbench", "all"]:
        download_vrsbench(dest)
        
    if args.dataset in ["rsvqa", "all"]:
        download_rsvqa(dest, mode=args.rsvqa_mode)
        
    if args.dataset in ["cdvqa", "all"]:
        download_cdvqa(dest)
        
    if args.dataset in ["bigearthnet", "all"]:
        download_bigearthnet(dest)
        
    print("\n" + "=" * 60)
    print(f"🎉 Dataset download tasks finished. Stored in: {dest}")
    print("=" * 60)

if __name__ == "__main__":
    main()
