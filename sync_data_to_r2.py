import os
import boto3
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import mimetypes

import sys

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

client = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4", max_pool_connections=25)
)

data_dir = Path(__file__).resolve().parent / "web" / "static" / "data"
tasks = []
for root, _, files in os.walk(data_dir):
    for f in files:
        local_path = Path(root) / f
        rel_path = "data/" + local_path.relative_to(data_dir).as_posix()
        tasks.append((local_path, rel_path))

print(f"[*] Uploading {len(tasks)} data files to Cloudflare R2 [{BUCKET_NAME}]...")

def upload(lp, rk):
    mime_type, _ = mimetypes.guess_type(lp)
    if not mime_type:
        mime_type = "application/json" if lp.suffix == ".json" else "text/html"
    extra_args = {"ContentType": mime_type}
    client.upload_file(str(lp), BUCKET_NAME, rk, ExtraArgs=extra_args)
    return rk

success = 0
with ThreadPoolExecutor(max_workers=20) as ex:
    futs = [ex.submit(upload, lp, rk) for lp, rk in tasks]
    for fut in as_completed(futs):
        try:
            fut.result()
            success += 1
        except Exception as e:
            print("Error:", e)

print(f"[+] Done! Successfully uploaded {success}/{len(tasks)} files to R2!")

