import json

with open('web/dungeons_client_cache.json', encoding='utf-8') as f:
    dungeons = json.load(f)

keywords = ['คิเม', 'ไกเซอร์', 'แบล็ค', 'เหล็กกล้า', 'ซูซา', 'การทำลาย', 'รอยัลเบส', 'ดาร์คเว็บ', 'เนเวอร์แลนด์', 'ฝันร้าย', 'อารีน่า', 'โคโลเซียม']

for d in dungeons:
    match = False
    for kw in keywords:
        if kw in d.get('name', '') or kw in d.get('map', ''):
            match = True
            break
    if match:
        print(f"Key: {d.get('key')} | Name: {d.get('name')} | Map: {d.get('map')} (ID: {d.get('map_id')}) | Variant: {d.get('variant')}")
        print(f"   Level range: {d.get('level_range')}")
        for m in d.get('monsters', []):
            print(f"      - {m.get('name')} | Lv: {m.get('level')} | HP: {m.get('hp')} | Boss: {m.get('boss')}")
