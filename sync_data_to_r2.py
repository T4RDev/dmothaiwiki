import os
import boto3
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import mimetypes

ACCOUNT_ID = "8b69ff4c369eef7750f59e8b91c3947f"
ACCESS_KEY_ID = "2dce185e223f2034a93a75d4b7ede7f1"
SECRET_ACCESS_KEY = "8e7710f1b1d881c57b3185827f2e47e1fc073677ca6d16fa3f353e5597a3e62d"
BUCKET_NAME = "dmo-assets"
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

