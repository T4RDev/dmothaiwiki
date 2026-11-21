import json
from pathlib import Path

weekly_dungeons = [
    {
        "id": "kimeramon_dungeon",
        "name": "ดันเจี้ยนคิเมรามอน (ฐานทัพของไกเซอร์)",
        "sub_name": "คิเมรามอน ระดับง่าย & ระดับยาก (CDG Normal / Hard)",
        "category": "ดันเจี้ยนเครื่องประดับ (ต่างหู) & ฟาร์มเงิน Bit",
        "difficulty": "ปานกลาง - ยาก (Normal / Hard)",
        "badge_color": "cyan",
        "party_size": "ปาร์ตี้ 4 คน (ดันเจี้ยนอินสแตนซ์)",
        "level_recommended": "Lv. 100 - 130+",
        "map_id": 401,
        "map_name": "ฐานทัพของไกเซอร์ (Kaiser's Base)",
        "map_image": "/images/maps/401_mini.png",
        "boss_name": "คิเมรามอน (Chimairamon)",
        "boss_icon": "/images/bosses/kimeramon.png",
        "ticket_requirement": "เข้าผ่าน NPC 'ดาร์คทาวเวอร์ ดินแดนต้องห้าม' หรือพอร์ทัลฐานทัพไกเซอร์ (ใช้บัตรผ่านฐานทัพของไกเซอร์ [Normal/Hard])",
        "why_weekly": "ดันเจี้ยนทำเงินและทำของประจำสัปดาห์อันดับ 1 ของสายฟาร์ม! เคลียร์จบได้เงินสดรอบละ 30 T - 50 T ต่อสัปดาห์ทันที และเป็นทางเดียวที่จะได้รับ 'พลังชั่วร้ายของคิเมรามอน' สำหรับนำไปคราฟต์และอัปเกรด 'ต่างหูคิเมรามอน' ซึ่งเป็นต่างหูระดับท็อปที่เพิ่ม Max HP และค่าสเตตัสป้องกัน/โจมตีสูงที่สุดสายเครื่องประดับ",
        "drops": [
            {
                "id": 47471,
                "name": "ต่างหูคิเมรามอน (Chimairamon Earring)",
                "count": "ดรอปสุ่ม",
                "icon": "/images/client_items/47471.png",
                "desc": "ต่างหูระดับ Endgame ให้ค่า Max HP, Critical และ Attribute Damage มหาศาล"
            },
            {
                "id": 47450,
                "name": "พลังชั่วร้ายของคิเมรามอน",
                "count": "1 - 3 ชิ้น / รอบ",
                "icon": "/images/client_items/47450.png",
                "desc": "วัตถุดิบหัวใจหลักของดันเจี้ยน ใช้สำหรับคราฟต์และเลื่อนขั้นต่างหูคิเมรามอนที่ พาตามอน [D-เทอร์มินัล]"
            },
            {
                "id": 47005,
                "name": "ทองคำ 30 T - 50 T",
                "count": "30,000,000,000 Bit",
                "icon": "/images/ui/ui_money.png",
                "desc": "เงินสดก้อนโตประจำสัปดาห์ เข้ากระเป๋าผู้เล่นโดยตรงเมื่อเคลียร์บอส"
            },
            {
                "id": 47005,
                "name": "หินเปลี่ยนออฟชั่น (OCS) & เปลี่ยนค่า (NCS)",
                "count": "การันตี",
                "icon": "/images/client_items/Option_Change_Stone.png",
                "desc": "หินสำหรับสุ่มออฟชั่นและปรับเปอร์เซ็นต์เครื่องประดับ"
            }
        ],
        "crafting": [
            {
                "target": "ต่างหูคิเมรามอนระดับสูง (Radiant Aural Earring of Chimairamon)",
                "materials": "พลังชั่วร้ายของคิเมรามอน x50 + ต่างหูคิเมรามอนตั้งต้น + หินออฟชั่น",
                "result_desc": "ต่างหู 4 ออฟชั่นที่บวกค่า Max HP หลักพันและสเตตัสท็อปเทียร์ จำเป็นอย่างยิ่งในการเอาชีวิตรอดในดันเจี้ยนเลทเกม"
            },
            {
                "target": "อุปกรณ์และดิจิไวซ์พลังมืด",
                "materials": "พลังชั่วร้ายของคิเมรามอน + เหรียญดันเจี้ยน",
                "result_desc": "เซ็ตเครื่องประดับสายมืดที่เสริมสเตตัสให้ดิจิมอนสายความมืดและไวรัสอย่างมหาศาล"
            }
        ],
        "strategy": "รวมปาร์ตี้ 4 คน ดาเมจ Burst ไว ลุยเข้าไปจัดการลูกน้องและเสาดาร์คทาวเวอร์ก่อน จากนั้นรวมตัวกันที่ห้องบอสใหญ่ ระดมสกิล F2/F3 เผด็จศึกคิเมรามอน ระวังจังหวะสกิลหมู่พ่นพิษของบอสที่ตัดเลือดรุนแรง"
    },
    {
        "id": "blackmetal_dungeon",
        "name": "ดันเจี้ยนแบล็คเมทัล (ดิจิมอนไกเซอร์ - Trace of Black Steel)",
        "sub_name": "ดันเจี้ยนเมทัล (MDG) / บอส แบล็คเมทัลเกรย์มอน",
        "category": "ดันเจี้ยนอุปกรณ์สวมใส่ (แว่นตาไกเซอร์) & ฟาร์มสเตตัส HT",
        "difficulty": "ยากระดับเลทเกม (High Endgame Raid)",
        "badge_color": "amber",
        "party_size": "ปาร์ตี้ 4 คน (ดันเจี้ยนอินสแตนซ์)",
        "level_recommended": "Lv. 140 - 150+",
        "map_id": 410,
        "map_name": "พื้นที่ของไกเซอร์ (Kaiser's Domain / Digital World)",
        "map_image": "/images/maps/410_mini.png",
        "boss_name": "แบล็คเมทัลเกรย์มอน (BlackMetalGreymon RaidBoss)",
        "boss_icon": "/images/bosses/blackmetalgreymon.png",
        "ticket_requirement": "รับบัตรผ่านร่องรอยแห่งเหล็กกล้า (Pass: Trace of Black Steel) จาก NPC เรนามอน หรือทางเข้าพื้นที่ของไกเซอร์",
        "why_weekly": "ดันเจี้ยนประจำสัปดาห์ระดับเลทเกมยอดนิยมอันดับ 1 ของเซิร์ฟไทย! เป็นแหล่งเดียวที่ดรอป 'กล่องแว่นตาของดิจิมอนไกเซอร์ (Kaiser Goggles)' อุปกรณ์ส่วนหน้าที่เพิ่มค่า Hit Rate (HT) และ Attack (AT) สูงที่สุดในเกม แก้ปัญหาการตีบอสเลทเกมไม่โดนอย่างเด็ดขาด พร้อมรับเงิน Bit รวม 35 T - 50 T ต่อสัปดาห์",
        "drops": [
            {
                "id": 47636,
                "name": "กล่องแว่นตาของดิจิมอนไกเซอร์ที่ถูกผนึก (Sealed Kaiser Goggles)",
                "count": "ดรอปสุ่มจากบอส",
                "icon": "/images/client_items/47636.png",
                "desc": "เปิดผนึกสุ่มรับแว่นตาไกเซอร์สายต่างๆ เช่น HT, AT, CT หรือ HP"
            },
            {
                "id": 47627,
                "name": "แว่นตาของดิจิมอนไกเซอร์ [HT / AT] (Kaiser Goggles)",
                "count": "การันตีสะสม",
                "icon": "/images/client_items/Kaiser_Goggles.png",
                "desc": "อุปกรณ์ส่วนหน้าท็อปเมต้า เพิ่ม Hit Rate (HT) หลักพัน แก้ปัญหาการโจมตีบอสเลทเกมไม่โดน"
            },
            {
                "id": 75379,
                "name": "บัตรผ่านร่องรอยแห่งเหล็กกล้า (Pass: Trace of Black Steel)",
                "count": "รับเควสรายวัน/สัปดาห์",
                "icon": "/images/client_items/Pass_Traces_of_Black_Steel.png",
                "desc": "ตั๋วผ่านทางเข้าสู่ดันเจี้ยนแบล็คเมทัล"
            },
            {
                "id": 47005,
                "name": "ทองคำ 35 T - 50 T",
                "count": "35,000,000,000 Bit",
                "icon": "/images/ui/ui_money.png",
                "desc": "เงินสดก้อนโตประจำสัปดาห์ เข้ากระเป๋าผู้เล่นโดยตรงเมื่อจบดันเจี้ยน"
            }
        ],
        "crafting": [
            {
                "target": "แว่นตาของดิจิมอนไกเซอร์ ระดับ Lv 1 - Lv 9 (Kaiser Goggles [HT / AT / CT])",
                "materials": "กล่องแว่นตาไกเซอร์ + ชิ้นส่วนพลังงานไกเซอร์ + หินออฟชั่น",
                "result_desc": "สุดยอดอุปกรณ์สวมใส่ส่วนหน้า (Glasses) ที่บวกค่า Hit Rate (HT) มหาศาล จำเป็นที่สุดสำหรับลงบอสระดับ Endgame"
            },
            {
                "target": "กล่องเครื่องแต่งกายดิจิมอนไกเซอร์ (Kaiser Clothes Package [AT / HP / SCD])",
                "materials": "ชิ้นส่วนพลังงานไกเซอร์ + เหรียญดันเจี้ยน",
                "result_desc": "ชุดเครื่องแต่งกายประจำตัวไกเซอร์ เพิ่ม Max HP, Attack และลดคูลดาวน์สกิล"
            }
        ],
        "strategy": "ผู้เล่นต้องมีดิจิมอนเลเวล 140 - 150+ และเตรียมค่า Hit Rate (HT) ขั้นต่ำ 7,000 - 8,000+ และ Critical (CT) 250%+ รวมตี้ 4 คน ดาเมจหลัก 3 ตัว + ตัวซัพพอร์ต 1 ตัว ระดมสกิล F2/F3 เบิร์สดาเมจใส่แบล็คเมทัลเกรย์มอน หลบวงสกิลระเบิดกิกะเดสทรอยเยอร์สีดำที่พื้น"
    },
    {
        "id": "susanoomon_dungeon",
        "name": "ดันเจี้ยนซูซาโนะโอมอน (การทำลายล้างและการฟื้นฟู)",
        "sub_name": "การทำลายล้างและการฟื้นฟู (Susanoomon Shin Raid)",
        "category": "ดันเจี้ยนสุดยอดดิจิไวซ์สปิริต (Susanoomon Shin Digivice)",
        "difficulty": "ยากระดับสูง (Master Tier)",
        "badge_color": "rose",
        "party_size": "ปาร์ตี้ 4 คน (ดันเจี้ยนอินสแตนซ์)",
        "level_recommended": "Lv. 120 - 140+",
        "map_id": 1312,
        "map_name": "การทำลายล้างและการฟื้นฟู (Destruction & Regeneration)",
        "map_image": "/images/maps/1312_mini.png",
        "boss_name": "ซูซาโนะโอมอน (ชิน) (Susanoomon Shin RaidBoss)",
        "boss_icon": "/images/bosses/susanoomon.png",
        "ticket_requirement": "เข้าผ่าน NPC 'โบโกมอน' ที่ D-เทอร์มินัล (ใช้บัตรผ่านการทำลายล้างและการฟื้นฟู)",
        "why_weekly": "ดันเจี้ยนรายสัปดาห์โควต้าจำกัด แหล่งเดียวในการหาชิ้นส่วน 'ซูซาชิน ดิจิไวซ์ (Susanoomon Shin Digivice)' ซึ่งเป็นดิจิไวซ์สายสปิริตที่ดีที่สุดในเกม มี 4 ช่องชิปเซ็ต พร้อมบัฟสเตตัสเฉพาะตัว และดรอปเงินสดก้อนโต 40 T",
        "drops": [
            {
                "id": 47260,
                "name": "ร่องรอยของซูซาโนะโอมอน",
                "count": "1 - 2 ชิ้น",
                "icon": "/images/client_items/47260.png",
                "desc": "ชิ้นส่วนจิตวิญญาณแห่งการฟื้นฟู สำหรับคราฟต์ดิจิไวซ์ซูซาชิน"
            },
            {
                "id": 47463,
                "name": "จิตวิญญาณแห่งการฟื้นฟู",
                "count": "การันตี",
                "icon": "/images/client_items/47463.png",
                "desc": "วัตถุดิบเควสประจำสัปดาห์สำหรับแลกของรางวัลระดับไฮเอนด์"
            },
            {
                "id": 110285,
                "name": "ซีลซูซาโนะโอมอน ชิน",
                "count": "ดรอปสุ่มการันตี",
                "icon": "/images/client_items/110285.png",
                "desc": "ซีลสุดยอดเทพนักรบ เพิ่มค่า AT และ Defense ให้ตัวละครถาวร"
            },
            {
                "id": 47005,
                "name": "ทองคำ 40 T",
                "count": "40,000,000,000 Bit",
                "icon": "/images/ui/ui_money.png",
                "desc": "เงินรางวัลประจำสัปดาห์ก้อนโต"
            }
        ],
        "crafting": [
            {
                "target": "ซูซาชิน ดิจิไวซ์ (Susanoomon Shin Digivice - Cross Loader)",
                "materials": "ร่องรอยของซูซาโนะโอมอน x30 + จิตวิญญาณแห่งการฟื้นฟู + ดิจิไวซ์ตั้งต้น",
                "result_desc": "ดิจิไวซ์สปิริตระดับท็อป ปลดล็อค 4 ช่องชิปเซ็ต และมอบสเตตัสพลังโจมตีธาตุแสง/สายฟ้าขั้นสูงสุด"
            },
            {
                "target": "แพ็คเกจหินเปลี่ยนออฟชั่น OCS / NCS รายสัปดาห์",
                "materials": "เหรียญซูซาโนะโอมอน",
                "result_desc": "แหล่งแลกหินเปลี่ยนออฟชั่นเครื่องประดับประจำสัปดาห์"
            }
        ],
        "strategy": "ตี้ 4 คน ดาเมจสูง ต้องมีสายซัพพอร์ตคอยล้างดีบัฟและฮีลเลือด จัดการเสาสปิริตรอบห้องเพื่อปลดบาเรียอมตะของบอส จากนั้นระดมสกิลเบิร์สดาเมจปิดฉากซูซาโนะโอมอน"
    },
    {
        "id": "royal_base_hard",
        "name": "ดันเจี้ยนรอยัลเบส (ระดับยาก - Royal Base Hard)",
        "sub_name": "รอยัลเบสยาก (RBH) / บอส เดธ X มอน (DeathXmon)",
        "category": "ดันเจี้ยนแว่นตานักผจญภัย & ชิปเซ็ตดับเบิล R16 - R18",
        "difficulty": "มหาโหดระดับ Endgame สูงสุด (Extreme Endgame)",
        "badge_color": "purple",
        "party_size": "ปาร์ตี้ 4 คน (ดันเจี้ยนอินสแตนซ์)",
        "level_recommended": "Lv. 150 - 170+",
        "map_id": 1707,
        "map_name": "ฐานทัพรอยัลเบส [ยาก] (Royal Base Hard)",
        "map_image": "/images/maps/1707_mini.png",
        "boss_name": "เดธ X มอน (DeathXmon RaidBoss)",
        "boss_icon": "/images/bosses/dexmon.png",
        "ticket_requirement": "ผ่านเควสเนื้อเรื่อง X-แอนติบอดี้ และมีบัตรผ่านรอยัลเบส [ยาก] (รับเควสประจำวัน/สัปดาห์ที่ เวอร์ซันดิเทอร์มินัล)",
        "why_weekly": "ดันเจี้ยน Endgame สูงสุดของเซิร์ฟไทยที่ทุกตี้ต้องลงทุกสัปดาห์! เป็นแหล่งเดียวที่ได้วัตถุดิบคราฟต์ 'แว่นตานักผจญภัย (Adventure's Goggles)' และ 'กล่องดับเบิลอัพเกรดชิปเซ็ต (Double Chipset R16-R18)' พร้อมดรอปซีลโอเมกามอน MM และเงิน 50 T",
        "drops": [
            {
                "id": 47253,
                "name": "วัตถุดิบแว่นตานักผจญภัย (Adventure's Goggles Material)",
                "count": "1 - 2 ชิ้น",
                "icon": "/images/client_items/47253.png",
                "desc": "วัตถุดิบสำคัญในการคราฟต์แว่นตานักผจญภัยระดับ Endgame"
            },
            {
                "id": 47255,
                "name": "กล่องดับเบิลอัพเกรดชิปเซ็ต (Double Upgrade Chipset Box)",
                "count": "การันตี",
                "icon": "/images/client_items/47255.png",
                "desc": "กล่องวัตถุดิบคราฟต์ชิปเซ็ต 2 แถวสเตตัสระดับสูง R16 - R18 ที่ศูนย์บัญชาการ DATS"
            },
            {
                "id": 110285,
                "name": "ซีลโอเมกามอน MM / ซีลรอยัลไนท์",
                "count": "ดรอปสุ่มการันตี",
                "icon": "/images/client_items/110285.png",
                "desc": "ซีลมอนสเตอร์ระดับตำนาน เพิ่มค่าพลังโจมตี (AT) ถาวรให้ตัวละครอย่างมหาศาล"
            },
            {
                "id": 47005,
                "name": "ทองคำ 50 T",
                "count": "50,000,000,000 Bit",
                "icon": "/images/ui/ui_money.png",
                "desc": "เงินสดก้อนโตที่สุดในเกม 50 Tera ต่อรอบ"
            }
        ],
        "crafting": [
            {
                "target": "แว่นตานักผจญภัย (Adventure's Goggles)",
                "materials": "วัตถุดิบ RBH + แกนพลังงาน X + แว่นตาตั้งต้น",
                "result_desc": "แว่นตาระดับสูงสุดของเกม เพิ่มสเตตัสทุกสายแบบก้าวกระโดด"
            },
            {
                "target": "กล่องดับเบิลชิปเซ็ตระดับสูง R16 - R18 (Double Upgrade Chipsets)",
                "materials": "กล่องดับเบิลอัพเกรดชิปเซ็ต + ชิปเซ็ตพื้นฐาน",
                "result_desc": "ชิปเซ็ตใส่ดิจิไวซ์ที่เพิ่มทั้ง AT และ HP พร้อมกันในช่องเดียว เพิ่มความโหดระดับขีดสุด"
            }
        ],
        "strategy": "ต้องการดิจิมอนร่าง Jogress SSS+ หรือ U-Rank เลเวล 150 - 170 ค่า HT 8,000+ และ CT 310%+ ต้องมีตัวซัพพอร์ต Goatmon หยุดสกิลบอส และสายฮีลคอยเติมเลือด จังหวะบอสปล่อยคลื่นลบดีบัฟต้องกดยาป้องกันทันที"
    },
    {
        "id": "dark_web",
        "name": "ดันเจี้ยนดาร์คเว็บ (Dark Web Dungeon)",
        "sub_name": "ดาร์คเว็บ (DW) / บอส เดียโบโรมอน & อาร์มาเกดเดมอน",
        "category": "ดันเจี้ยนดิจิโซล เซอร์กิต (Digisoul Circuit) & ชุดดาร์คเว็บ",
        "difficulty": "ยากระดับสูง (Very Hard)",
        "badge_color": "emerald",
        "party_size": "ปาร์ตี้ 4 คน (ดันเจี้ยนอินสแตนซ์)",
        "level_recommended": "Lv. 130 - 150+",
        "map_id": 406,
        "map_name": "ดาร์คเว็บ (Dark Web)",
        "map_image": "/images/maps/406_mini.png",
        "boss_name": "เดียโบโรมอน & อาร์มาเกดเดมอน (Diablomon / Armageddemon RaidBoss)",
        "boss_icon": "/images/bosses/diablomon.png",
        "ticket_requirement": "รับบัตรผ่านเครือข่ายดาร์คเว็บจาก NPC คุรามอน หรือพอร์ทัล D-เทอร์มินัล",
        "why_weekly": "แหล่งฟาร์มกล่อง 'ดิจิโซล เซอร์กิต (Digisoul Circuit Boxes SS~SS+)' ประจำสัปดาห์เพื่อปลดล็อคบอร์ดสเตตัสดิจิมอน และฟาร์มวัตถุดิบชุดเซ็ตดาร์คเว็บ พร้อมรับเงิน 40 T ต่อรอบ",
        "drops": [
            {
                "id": 47488,
                "name": "กล่องดิจิโซล เซอร์กิตระดับสูง (Digisoul Circuit Box SS+)",
                "count": "การันตี",
                "icon": "/images/client_items/47488.png",
                "desc": "ไอเทมสำหรับระบบเซอร์กิตบอร์ด เพิ่มสเตตัส AT, CT และ HP"
            },
            {
                "id": 47005,
                "name": "ข้อมูลคุรามอนที่ถูกบีบอัด",
                "count": "10 - 20 ชิ้น",
                "icon": "/images/client_items/47005.png",
                "desc": "ชิ้นส่วนแลกเปลี่ยนไอเทมดาร์คเว็บและหินออฟชั่น"
            },
            {
                "id": 47005,
                "name": "ทองคำ 40 T",
                "count": "40,000,000,000 Bit",
                "icon": "/images/ui/ui_money.png",
                "desc": "เงินรางวัลประจำสัปดาห์ก้อนโต"
            }
        ],
        "crafting": [
            {
                "target": "ดิจิโซล เซอร์กิตเกรดท็อป (High-Tier Circuit Module)",
                "materials": "กล่องเซอร์กิตดาร์คเว็บ + ชิ้นส่วนข้อมูลคุรามอน",
                "result_desc": "ติดตั้งลงบอร์ดเพิ่ม AT, CT และสกิลแดเมจให้ดิจิมอนทุกตัวในไอดี"
            },
            {
                "target": "ชุดเครื่องแต่งกายดาร์คเว็บ (Dark Web Costume Set)",
                "materials": "วัตถุดิบดาร์คเว็บ + เหรียญเครือข่าย",
                "result_desc": "แฟชั่นเพิ่ม Max HP 2,000 และ AT 500 ถาวร"
            }
        ],
        "strategy": "ต้องการดิจิมอนเลือด 180k+ ค่า HT 26,000+ และ CT สูง ปาร์ตี้ 4 คน ดาเมจตัวท็อปอย่าง OMM / CMA ลุยเคลียร์ฝูงคุรามอนและเดียโบโรมอนร่างแยกก่อน แล้วรุมเบิร์สอาร์มาเกดเดมอนก่อนสกิลกวาดล้างทำงาน"
    },
    {
        "id": "neverland_eosmon",
        "name": "ดันเจี้ยนเนเวอร์แลนด์ (Neverland - Eosmon)",
        "sub_name": "เนเวอร์แลนด์ / บอส อีออสมอน ร่างสุดยอด (Eosmon LV6)",
        "category": "ดันเจี้ยนเฟิร์สท์ ดิจิไวซ์ (First Digivice) & สร้อยเนเวอร์แลนด์",
        "difficulty": "ยากระดับสูงมาก (Extreme Raid)",
        "badge_color": "blue",
        "party_size": "ปาร์ตี้ 4 คน (ดันเจี้ยนอินสแตนซ์)",
        "level_recommended": "Lv. 140 - 160+",
        "map_id": 72,
        "map_name": "เนเวอร์แลนด์ (Neverland)",
        "map_image": "/images/maps/105_mini.png",
        "boss_name": "อีออสมอน (ร่างสุดยอด) (Eosmon LV6 RaidBoss)",
        "boss_icon": "/images/bosses/eosmon.png",
        "ticket_requirement": "ผ่านเควสเนื้อเรื่อง Last Evolution Kizuna และรับตั๋วเนเวอร์แลนด์จาก NPC เมโนอา",
        "why_weekly": "ทางเดียวในการฟาร์มชิ้นส่วน 'เฟิร์สท์ ดิจิไวซ์ (First Digivice)' ซึ่งเป็นหนึ่งในดิจิไวซ์ระดับ Endgame ที่ดีที่สุด พร้อมดรอปสร้อยคอเนเวอร์แลนด์ และเงินสด 45 T ต่อสัปดาห์",
        "drops": [
            {
                "id": 47534,
                "name": "กล่องเฟิร์สท์ ดิจิไวซ์ที่ถูกผนึก (First Digivice Box)",
                "count": "ดรอปสุ่มจากบอส",
                "icon": "/images/client_items/47534.png",
                "desc": "กล่องสุ่มหรือปลดผนึกเฟิร์สท์ดิจิไวซ์"
            },
            {
                "id": 47510,
                "name": "วงแหวนแห่งแสงอีออสมอน",
                "count": "1 - 3 ชิ้น / รอบ",
                "icon": "/images/client_items/47510.png",
                "desc": "วัตถุดิบในการอัปเกรดดิจิไวซ์และสร้อยคอเนเวอร์แลนด์"
            },
            {
                "id": 47005,
                "name": "สร้อยคอเนเวอร์แลนด์ (Neverland Necklace)",
                "count": "ดรอปสุ่ม",
                "icon": "/images/client_items/47005.png",
                "desc": "สร้อยระดับ Endgame 4 ออฟชั่น เพิ่ม Attack และ Critical Damage"
            },
            {
                "id": 47005,
                "name": "ทองคำ 45 T",
                "count": "45,000,000,000 Bit",
                "icon": "/images/ui/ui_money.png",
                "desc": "เงินรางวัลประจำสัปดาห์ก้อนโต"
            }
        ],
        "crafting": [
            {
                "target": "เฟิร์สท์ ดิจิไวซ์ระดับสมบูรณ์ (First Digivice Awakened)",
                "materials": "ชิ้นส่วนเฟิร์สท์ดิจิไวซ์ + วงแหวนแห่งแสงอีออสมอน x20",
                "result_desc": "ดิจิไวซ์ 4 ช่องชิปเซ็ต เพิ่มสเตตัสทุกค่าอย่างมหาศาล สลับใส่ชิปเซ็ตได้อิสระ"
            },
            {
                "target": "สร้อยคอเนเวอร์แลนด์ขั้นสูง (Aural Neverland Necklace)",
                "materials": "สร้อยคอเนเวอร์แลนด์ + วงแหวนแห่งแสง",
                "result_desc": "สร้อยคอเพิ่ม Attack และ Critical Damage ขั้นสูงสุด"
            }
        ],
        "strategy": "บอสมีกลไกตามเปอร์เซ็นต์เลือด (89%, 69%, 49%, 29%, 9%) จะมีวงแหวนสี (เหลือง/ดำ/เขียว/แดง) เกิดขึ้นบนพื้น ผู้เล่นทุกคนต้องวิ่งหลบเข้าวงปลอดภัยให้ทัน และรวมพลังเบิร์สดาเมจก่อนหมดเวลาเช็ค DPS"
    },
    {
        "id": "nightmare_dungeon",
        "name": "ดันเจี้ยนฝันร้าย (Nightmare Dungeon)",
        "sub_name": "ดินแดนแห่งฝันร้าย / บอส เบเรียลแวมเดมอน (BelialVamdemon)",
        "category": "ดันเจี้ยนเครื่องประดับอัลติเมท (แหวน/สร้อยไนท์แมร์)",
        "difficulty": "ยากระดับสูงมาก (Nightmare Raid)",
        "badge_color": "purple",
        "party_size": "ปาร์ตี้ 4 คน (ดันเจี้ยนอินสแตนซ์)",
        "level_recommended": "Lv. 140 - 165+",
        "map_id": 407,
        "map_name": "ดินแดนแห่งฝันร้าย (Nightmare)",
        "map_image": "/images/maps/407_mini.png",
        "boss_name": "เบเรียลแวมเดมอน (BelialVamdemon RaidBoss)",
        "boss_icon": "/images/bosses/belialvamdemon.png",
        "ticket_requirement": "รับบัตรผ่านดินแดนแห่งฝันร้ายจาก NPC ที่จุดเชื่อมมิติ หรือเควสประจำสัปดาห์",
        "why_weekly": "แหล่งดรอปวัตถุดิบคราฟต์ 'เครื่องประดับอัลติเมทแห่งฝันร้าย (Ultimate Nightmare Accessories)' ซึ่งบวกสเตตัสและออฟชั่นแถวใหม่ พร้อมเงินสด 45 T ต่อสัปดาห์",
        "drops": [
            {
                "id": 47450,
                "name": "ดอกไม้แห่งความมืด (Flower of Darkness)",
                "count": "1 - 3 ชิ้น / รอบ",
                "icon": "/images/client_items/47450.png",
                "desc": "วัตถุดิบสร้างเครื่องประดับไนท์แมร์ระดับสูง"
            },
            {
                "id": 47512,
                "name": "ผลึกแห่งความมืดบริสุทธิ์ (Seed of Darkness)",
                "count": "การันตี",
                "icon": "/images/client_items/47512.png",
                "desc": "ไอเทมป้องกันคำสาปและวัตถุดิบคราฟต์"
            },
            {
                "id": 47005,
                "name": "ทองคำ 45 T",
                "count": "45,000,000,000 Bit",
                "icon": "/images/ui/ui_money.png",
                "desc": "เงินรางวัลประจำสัปดาห์ก้อนโต"
            }
        ],
        "crafting": [
            {
                "target": "แหวนและสร้อยอัลติเมทแห่งฝันร้าย (Ultimate Nightmare Ring & Necklace)",
                "materials": "ดอกไม้แห่งความมืด + ผลึกความมืดบริสุทธิ์ + หินออฟชั่น",
                "result_desc": "เครื่องประดับระดับ Endgame สเตตัสสูงลิ่ว มอบค่า AT, Max HP และ Skill Damage"
            },
            {
                "target": "หินป้องกันคำสาปและไอเทมบัฟไนท์แมร์",
                "materials": "ผลึกแห่งความมืดบริสุทธิ์",
                "result_desc": "ใช้ป้องกันดีบัฟของบอสในดันเจี้ยนระดับสูง"
            }
        ],
        "strategy": "เบเรียลแวมเดมอนมีสกิลลบล้างบัฟ (Buff Strip) และสกิลตัดเลือดเป็นเปอร์เซ็นต์ ต้องสังเกตเครื่องหมายวงกลมสีบนพื้น (เหลือง เขียว ดำ) ให้วิ่งเข้าจุดปลอดภัยทันที และใช้สกิลป้องกันให้ตรงจังหวะการทุบพื้นของบอส"
    },
    {
        "id": "digimon_arena",
        "name": "ดิจิมอนอารีน่า (Colosseum Arena - ทั่วไป & ยาก)",
        "sub_name": "สนามประลองโคโลเซียม (Wave 1 - 40)",
        "category": "ดิจิไวซ์ OT (OT Digivice) & ฟาร์มหิน OCS / NCS ฟรีทุกสัปดาห์",
        "difficulty": "ทั่วไป ถึง มหาโหดยาก (Wave 1 - 40)",
        "badge_color": "amber",
        "party_size": "1 - 4 คน (ปาร์ตี้อารีน่า)",
        "level_recommended": "Lv. 100 - 170+",
        "map_id": 300,
        "map_name": "โคโลเซียม อารีน่า (Colosseum Arena)",
        "map_image": "/images/maps/colosseum_zone.png",
        "boss_name": "บอสเวฟอารีน่า (Arena Raid Bosses)",
        "boss_icon": "/images/bosses/arena.png",
        "ticket_requirement": "รับบัตรผ่านดิจิมอนอารีน่ารายวันได้ที่ NPC ผู้ดูแลสนามประลอง D-เทอร์มินัล",
        "why_weekly": "หัวใจสำคัญที่สุดของการพัฒนาตัวละครใน DMO เซิร์ฟไทย! อารีน่าจะรีเซ็ตแต้มและส่งของรางวัลจัดอันดับ (Ranking Reward) ทุกๆ สัปดาห์ การลงอารีน่าเป็นวิธีเดียวที่จะได้รับ 'เหรียญอารีน่า [ทั่วไป]' และ 'เหรียญอารีน่า [ยาก]' ในการนำไปแลก 'ดิจิไวซ์ OT (OT Digivice)', หินเปลี่ยนออฟชั่น OCS, หิน NCS จำนวนมหาศาล และกล่องสุ่มโจเกรสระดับท็อป!",
        "drops": [
            {
                "id": 47323,
                "name": "เหรียญอารีน่า [ทั่วไป]",
                "count": "การันตีตามเวฟที่เคลียร์ (สูงสุด 7 - 100+ เหรียญ)",
                "icon": "/images/client_items/47323.png",
                "desc": "เหรียญแลกเปลี่ยนของรางวัลอารีน่าระดับทั่วไป"
            },
            {
                "id": 47324,
                "name": "เหรียญอารีน่า [ยาก]",
                "count": "การันตีตามเวฟที่เคลียร์ (สูงสุด 9 - 150+ เหรียญ)",
                "icon": "/images/client_items/47324.png",
                "desc": "เหรียญแลกเปลี่ยนของรางวัลอารีน่าระดับยาก สำหรับของรางวัลระดับสูง"
            },
            {
                "id": 47005,
                "name": "หินเปลี่ยนออฟชั่น (OCS)",
                "count": "แลกเปลี่ยนประจำสัปดาห์",
                "icon": "/images/client_items/Option_Change_Stone.png",
                "desc": "ไอเทมจำเป็นที่สุดในการสุ่มออฟชั่นเครื่องประดับให้ได้แถวท็อป"
            },
            {
                "id": 47006,
                "name": "หินเปลี่ยนค่าออฟชั่น (NCS)",
                "count": "แลกเปลี่ยนประจำสัปดาห์",
                "icon": "/images/client_items/Number_Change_Stone.png",
                "desc": "ไอเทมสุ่มเปอร์เซ็นต์ค่าพลังของเครื่องประดับให้เต็ม 100% - 200%"
            },
            {
                "id": 152373,
                "name": "กล่องสุ่ม OT ดิจิไวซ์ (OT Digivice Box)",
                "count": "รางวัลแลกเหรียญ",
                "icon": "/images/client_items/OT_Digivice.png",
                "desc": "ดิจิไวซ์ระดับสูงที่ทุกคนต้องมีเพื่อใส่ชิปเซ็ตเสริมสเตตัส 4 ช่อง"
            }
        ],
        "crafting": [
            {
                "target": "ดิจิไวซ์ OT ระดับสูง (OT Digivice High-Tier)",
                "materials": "เหรียญอารีน่า [ยาก] x150 + เหรียญอารีน่า [ทั่วไป] x200",
                "result_desc": "ดิจิไวซ์ภาคบังคับของเทมเมอร์เซิร์ฟไทย ปลดล็อคช่องชิปเซ็ต 4 ช่องและเพิ่มค่าพลังพื้นฐาน"
            },
            {
                "target": "แพ็คเกจรวมหินเปลี่ยนออฟชั่น OCS และ NCS",
                "materials": "เหรียญอารีน่าตามจำนวนที่กำหนด",
                "result_desc": "แหล่งฟาร์มหิน OCS/NCS ฟรีที่ดีที่สุดในเกมโดยไม่ต้องเติมเงิน"
            },
            {
                "target": "บัฟอารีน่าพิเศษ (EXP +200%, AT +500)",
                "materials": "เหรียญอารีน่า",
                "result_desc": "บัฟตัวช่วยสำหรับเร่งเก็บเลเวลและลงดันเจี้ยนระดับสูง"
            }
        ],
        "strategy": "รวมทีม 4 คน จัดตำแหน่ง ดาเมจ 3 ตัว + สายฮีล/ซัพพอร์ต 1 ตัว ไต่ระดับไปจนถึงเวฟ 30 - 40 จังหวะที่มีมอนสเตอร์บัฟสะท้อนดาเมจให้หยุดตีทันที และสื่อสารเรื่องการใช้สกิลหมู่ตัดเวฟ"
    }
]

out_data = {
    "version": "1.1.0",
    "title": "ไกด์การลงดันเจี้ยนประจำสัปดาห์ (Weekly Dungeons Guide)",
    "description": "คู่มือดันเจี้ยนประจำสัปดาห์ที่ต้องลง (Must-Do Weekly Dungeons) ของเซิร์ฟเวอร์ไทย อิงจากเมต้าของผู้เล่นไทยจริง 100% พร้อมเหตุผลว่าทำไมต้องลง ของดรอปที่ได้รับ และสูตรคราฟต์ไอเทมระดับ Endgame",
    "weekly_reset_note": "ดันเจี้ยนประจำสัปดาห์จะรีเซ็ตโควต้ารอบและของรางวัลทุกสัปดาห์ (ตามรอบรีเซ็ตเซิร์ฟเวอร์ประจำสัปดาห์) แนะนำให้ลงให้ครบทุกสัปดาห์เพื่อไม่ให้พลาดเงินทองคำ Bit รวมกว่า 150T+ และวัตถุดิบคราฟต์อุปกรณ์ระดับเทพ!",
    "total_dungeons": len(weekly_dungeons),
    "dungeons": weekly_dungeons
}

for out_path in [
    Path("data/weekly_dungeons_guide.json"),
    Path("web/static/data/weekly_dungeons_guide.json"),
    Path("web/weekly_dungeons_cache.json")
]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"Generated {out_path} ({len(weekly_dungeons)} dungeons)")
