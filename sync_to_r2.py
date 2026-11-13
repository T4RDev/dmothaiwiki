import os
import sys
import boto3
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import mimetypes

# ========================================================
# CLOUDFLARE R2 CREDENTIALS (Loaded from Environment Variables)
# ========================================================
ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "dmo-assets")

if not (ACCOUNT_ID and ACCESS_KEY_ID and SECRET_ACCESS_KEY):
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k == "R2_ACCOUNT_ID" and not ACCOUNT_ID: ACCOUNT_ID = v
                    elif k == "R2_ACCESS_KEY_ID" and not ACCESS_KEY_ID: ACCESS_KEY_ID = v
                    elif k == "R2_SECRET_ACCESS_KEY" and not SECRET_ACCESS_KEY: SECRET_ACCESS_KEY = v
                    elif k == "R2_BUCKET_NAME" and not BUCKET_NAME: BUCKET_NAME = v

if not (ACCOUNT_ID and ACCESS_KEY_ID and SECRET_ACCESS_KEY):
    print("[ERROR] R2 credentials missing. Please set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY in environment or .env file.")
    sys.exit(1)

ENDPOINT_URL = f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com"

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4", max_pool_connections=50)
    )

def collect_files():
    base_dir = Path(__file__).resolve().parent / "output"
    tasks = []
    
    # 1. Images
    img_dir = base_dir / "images"
    if img_dir.exists():
        for root, _, files in os.walk(img_dir):
            for f in files:
                local_path = Path(root) / f
                rel_path = local_path.relative_to(base_dir).as_posix()
                tasks.append((local_path, rel_path))
                
    # 2. Models
    models_dir = base_dir / "models"
    if models_dir.exists():
        for root, _, files in os.walk(models_dir):
            for f in files:
                local_path = Path(root) / f
                rel_path = local_path.relative_to(base_dir).as_posix()
                tasks.append((local_path, rel_path))

    # 3. Static Data (JSON & Patch HTMLs)
    data_dir = Path(__file__).resolve().parent / "web" / "static" / "data"
    if data_dir.exists():
        for root, _, files in os.walk(data_dir):
            for f in files:
                local_path = Path(root) / f
                rel_path = "data/" + local_path.relative_to(data_dir).as_posix()
                tasks.append((local_path, rel_path))
                
    return tasks

def upload_single_file(client, local_path, r2_key):
    mime_type, _ = mimetypes.guess_type(local_path)
    if not mime_type:
        if local_path.suffix.lower() == ".glb":
            mime_type = "model/gltf-binary"
        else:
            mime_type = "application/octet-stream"
            
    extra_args = {"ContentType": mime_type}
    try:
        client.upload_file(str(local_path), BUCKET_NAME, r2_key, ExtraArgs=extra_args)
        return True, r2_key
    except Exception as e:
        return False, f"{r2_key}: {e}"

def main():
    if not ACCOUNT_ID or not ACCESS_KEY_ID or not SECRET_ACCESS_KEY:
        print("[!] กรุณากรอก R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY ก่อนรัน")
        print("    หรือรันด้วยคำสั่ง: python sync_to_r2.py <account_id> <access_key> <secret_key> <bucket_name>")
        return

    print(f"[*] เริ่มสแกนไฟล์เพื่ออัปโหลดขึ้น Cloudflare R2 [{BUCKET_NAME}]...")
    files = collect_files()
    total = len(files)
    print(f"[*] ตรวจพบไฟล์ทั้งหมด: {total} ไฟล์ (รูปภาพ + โมเดล 3D)")

    client = get_s3_client()
    success = 0
    failed = 0

    print(f"[*] เริ่มอัปโหลดแบบมัลติเธรด (30 Workers)...")
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(upload_single_file, client, lp, rk): rk for lp, rk in files}
        for future in as_completed(futures):
            ok, msg = future.result()
            if ok:
                success += 1
            else:
                failed += 1
                print(f"[!] Upload failed: {msg}")
            
            if (success + failed) % 250 == 0 or (success + failed) == total:
                pct = ((success + failed) / total) * 100
                print(f"    ความคืบหน้า: {success + failed}/{total} ({pct:.1f}%) [สำเร็จ: {success}, ผิดพลาด: {failed}]")

    print(f"\n[+] อัปโหลดเสร็จสิ้นทั้งหมด! สำเร็จ: {success}, ล้มเหลว: {failed}")

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        ACCOUNT_ID = sys.argv[1]
        ACCESS_KEY_ID = sys.argv[2]
        SECRET_ACCESS_KEY = sys.argv[3]
        if len(sys.argv) >= 5:
            BUCKET_NAME = sys.argv[4]
    main()

