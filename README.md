---
title: DMO Thai Wiki
emoji: 🦖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🦖 DMO Thai Wiki (Digimon Masters Online Thailand Database)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Status](https://img.shields.io/badge/Progress-40%25%20Preview-orange.svg)]()

> เว็บสารานุกรมและฐานข้อมูลคู่มือเกม **Digimon Masters Online (DMO) เซิร์ฟเวอร์ไทย** อิงข้อมูลจริงจาก Client แพตช์ไทยล่าสุด (รองรับเลเวลสูงสุด Lv. 180) ใช้งานได้ทั้งบน PC, Tablet และ Smartphone (Responsive 100%)

---

## 🌟 ฟีเจอร์หลักของระบบ (Main Features)

1. **📖 สารานุกรมดิจิมอน (Digimon Dex)**
   - รวบรวมข้อมูลดิจิมอนทุก Rank ตั้งแต่ **Rank N ถึง Rank U**
   - แสดงสเตตัสจริง (HP, DS, DE, AT, AS, CT, EV, HT)
   - สกิล F1 - F4 (ระยะคูลดาวน์, การใช้ DS, ธาตุสกิล, เอฟเฟกต์ AoE)
   - สายวิวัฒนาการเชื่อมโยงตรงตามไคลเอนต์เซิร์ฟเวอร์ไทย

2. **🛡️ ระบบ D-ยูนิต (D-Unit System)**
   - ข้อมูลกลุ่ม D-ยูนิตครบทั้ง 42 กลุ่ม
   - รายละเอียดเงื่อนไขผลการสะสมและบัฟสเตตัสถาวร (AT, HT, SCD, CT)
   - ไอคอนแฮกกิ้งคิท (Hacking Kit) แยกตาม Rank จริงในเซิร์ฟไทย
   - ระบบตรวจสอบบัฟฉายาถาวร Master Tiers

3. **🧬 เควสโจเกรส (Jogress Quests)**
   - สรุปแนวทางการทำเควสโจเกรสทุกร่าง ทุกฝั่ง (เช่น โอเมกามอน, อัลฟามอน โอรีวเคน, มิลเลเนียมมอน ฯลฯ)
   - รายละเอียด NPC สถานที่ เงื่อนไข และไอเทมที่ต้องใช้

4. **🃏 เด็คการ์ดสะสม (Deck Buffs)**
   - รวมบัฟเด็คยอดฮิต เช่น สปีดการโจมตี (AS -8% / -12% / -15%), โอกาสคริติคอล (CT) และพลังสกิล (SCD)
   - ตารางรายชื่อดิจิมอนที่ต้องเปิดในเด็ค

5. **📜 ซีลมาสเตอร์ (Seal Master)**
   - ตารางสเตตัสที่ได้รับจากการสะสมการ์ดซีล (AT, DE, HP, HT, CT)
   - ระบบคำนวณจำนวนใบเปิดการ์ดซีลมาสเตอร์

6. **🏰 ดันเจี้ยน & บอส (Dungeons & Drops)**
   - ข้อมูลดันเจี้ยน 91 แห่ง เลเวลที่แนะนำ บอสประจำดัน เจาะลึกมอนสเตอร์ ไอเทมดรอป และ NPC แลกของ

7. **💰 เครื่องคิดเลขคำนวณเงิน T / RMT**
   - คำนวณเงิน Bit / Mega / Tera แปลงเป็นเงินบาทไทย (฿) พร้อมปุ่มลัดคิดเงินสะดวกและรวดเร็ว

8. **📢 บันทึกประวัติแพตช์ (Patch Notes)**
   - ประวัติการอัปเดตและแพตช์โน้ตภาษาไทยของเซิร์ฟเวอร์

---

## 🚀 วิธีการรันบนเครื่อง Local (Quick Start)

### 1. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 2. เริ่มต้นรันเซิร์ฟเวอร์
```bash
python web/server.py
```
เปิดบราวเซอร์ไปที่: **`http://localhost:8001`** หรือ **`http://localhost:8001/home`**

---

## ☁️ การ Deploy ขึ้น Cloud (Railway / Render / Fly.io / VPS)

โปรเจกต์นี้รองรับการ Deploy ทุกแพลตฟอร์มด้วย **Dockerfile** และ **Procfile** ในตัว:

* **Procfile (สำหรับ Render / Railway / Heroku):**
  ```text
  web: uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8001}
  ```
* **Environment Variables:**
  * `PORT`: พอร์ตที่เซิร์ฟเวอร์จะเปิดรับ (กำหนดอัตโนมัติบน Cloud)

---

## 🛠️ สแต็กเทคโนโลยี (Tech Stack)

* **Backend:** Python 3.11, FastAPI, Uvicorn, SQLite
* **Frontend:** Vanilla HTML5, CSS3, Modern JavaScript (Single Page Application architecture)
* **Assets & Data:** Decrypted client tables & localization strings directly from DMO Thai Client
