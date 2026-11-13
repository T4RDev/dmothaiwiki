"""
DMO Thai Wiki - One-Click Data Sync Script
รันคำสั่งนี้คำสั่งเดียวเมื่อมีการอัปเดตข้อมูลเกมใหม่
1. ทำการสร้างไฟล์ JSON ฐานข้อมูลทั้งหมดใส่ web/static/data/
2. ซิงค์ขึ้น Cloudflare R2 อัตโนมัติ (เสร็จใน 5 วินาที)
"""
import subprocess
import sys

def main():
    print("==================================================")
    print("  DMO Thai Wiki - One-Click Data Sync")
    print("==================================================")
    
    print("\n[Step 1/2] สร้างไฟล์ JSON ฐานข้อมูล...")
    ret = subprocess.run([sys.executable, "build_static_export.py"])
    if ret.returncode != 0:
        print("[!] เกิดข้อผิดพลาดในการสร้างไฟล์ JSON")
        return
        
    print("\n[Step 2/2] อัปโหลดข้อมูลขึ้น Cloudflare R2...")
    ret = subprocess.run([sys.executable, "sync_data_to_r2.py"])
    if ret.returncode != 0:
        print("[!] เกิดข้อผิดพลาดในการอัปโหลดขึ้น Cloudflare R2")
        return
        
    print("\n==================================================")
    print("  [SUCCESS] ข้อมูลเกมทั้งหมดอัปเดตออนไลน์เรียบร้อยแล้ว!")
    print("==================================================")

if __name__ == "__main__":
    main()

