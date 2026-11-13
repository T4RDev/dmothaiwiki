# -*- coding: utf-8 -*-
import json
from pathlib import Path

p = Path("Web_Scraper/web/i18n/th_text.json")
d = json.loads(p.read_text(encoding="utf-8"))

translations = {
    "Critical Damage 10% / 20% / 30% increase": "เพิ่มดาเมจคริติคอล 10% / 20% / 30%",
    ": Critical Damage 10% / 20% / 30% increase": ": เพิ่มดาเมจคริติคอล 10% / 20% / 30%",
    "Stack Effect: Critical Damage 10% / 20% / 30% increase": "ผลแบบสะสม: เพิ่มดาเมจคริติคอล 10% / 20% / 30%",
    "Is a Mega with 3 Families, getting 110% from Shadow Labyrinth buffs": "เป็นร่างสุดยอด (Mega) ที่มีถึง 3 ตระกูล ได้รับบัฟจากเขาวงกตแห่งเงา (Shadow Labyrinth) สูงถึง 110%",
    "Good ASB Ensures it deals high damage": "ระบบ ASB ดีเยี่ยม ช่วยการันตีการทำดาเมจได้มหาศาล",
    "You can also get Holydramon Awaken if you get Goddramon during the release event at no additional cost": "สามารถรับโฮลี่ดรามอน (อะเวคเค่น) เพิ่มฟรีได้ทันที หากได้รับก็อดดรามอนในช่วงกิจกรรมเปิดตัว",
    "If you do own The Our Hope, Our Light deck, it is the best in the game": "หากมีเด็ค 'ความหวังของเรา แสงสว่างของเรา' (Our Hope, Our Light) จะเป็นหนึ่งในเด็คที่ดีที่สุดในเกม",
    "Does not have a U-rank Deck unless you also own ZeedMillenniummon Awaken": "ไม่มีเด็คระดับ Rank U ให้ใช้ เว้นแต่ว่าจะมีซี๊ดมิลเลนเนียมมอน (อะเวคเค่น)",
    "Low base Critical Chance": "อัตราคริติคอลพื้นฐานค่อนข้างต่ำ",
    "Locked behind a 1400$ Gacha": "ถูกล็อกอยู่หลังระบบสุ่มกาชาที่มีมูลค่าสูงถึงประมาณ 1,400 ดอลลาร์",
    "Goddramon is a Holy Dragon Digimon with a body of glittering gold and six hardened wings. Since it wears a Holy Ring on one arm, and such rings are proof of a Digimon’s holiness, it is considered to be a kind of sacred Digimon. Goddramon is one the Four Great Dragons, of which only two ( Holydramon and Goddramon) are known. Also, Small Dragon Digimon are sealed within Goddramon’s vambraces. The one on the left holds Amon of Crimson Flame, which governs destruction, while the one on the right holds Umon of Blue Thunder, which governs regeneration. Its special move God Flame involves detonating its holy spirit to mow down all surrounding enemies in an instant.": "ก็อดดรามอนเป็นดิจิมอนมังกรศักดิ์สิทธิ์ที่มีร่างกายสีทองเปล่งประกายและมีปีกอันแข็งแกร่ง 6 ปีก เนื่องจากการสวมโฮลี่ริง (Holy Ring) ไว้ที่แขนข้างหนึ่ง ซึ่งเป็นหลักฐานยืนยันความศักดิ์สิทธิ์ของดิจิมอน จึงจัดเป็นดิจิมอนศักดิ์สิทธิ์ประเภทหนึ่ง ก็อดดรามอนเป็นหนึ่งในสี่มังกรผู้ยิ่งใหญ่ (Four Great Dragons) นอกจากนี้ ยังมีดิจิมอนมังกรขนาดเล็กถูกผนึกไว้ในปลอกแขนของก็อดดรามอน โดยข้างซ้ายผนึก 'อามอนแห่งเปลวเพลิงแดง' ซึ่งควบคุมการทำลายล้าง ส่วนข้างขวาผนึก 'อูมอนแห่งหอกสายฟ้า' ซึ่งควบคุมการฟื้นฟูและการกำเนิดใหม่ ท่าไม้ตายก็อด เฟลมคือการระเบิดพลังวิญญาณศักดิ์สิทธิ์เพื่อกวาดล้างศัตรูโดยรอบในพริบตา"
}

for k, v in translations.items():
    d[k] = v

p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OK] Added {len(translations)} Goddramon translations to th_text.json")
