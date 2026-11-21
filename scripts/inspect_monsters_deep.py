import struct, json
from pathlib import Path

T = Path('G:/DMOWiki/CrackDMO/out_decrypted/data/bin/table')
L = Path('G:/DMOWiki/CrackDMO/out_json/language')

monname = {x['id']: x['fields'][0] if x.get('fields') else '' for x in json.loads((L / 'monstername_str.json').read_text(encoding='utf-8'))}

# Read monster.bin
b_mon = (T / 'monster.bin').read_bytes()
n_mon = struct.unpack_from('<i', b_mon, 0)[0]
monsters = {}
for i in range(n_mon):
    o = 4 + i * 70
    mid, model, unk1 = struct.unpack_from('<iii', b_mon, o)
    # Let's inspect all fields:
    # 70 bytes = 17 ints (68 bytes) + 2 bytes
    fields = struct.unpack_from('<17i2b', b_mon, o)
    # level is at offset 12 (short) or field index 3?
    # Let's unpack with different formats:
    # id(i32) @0, model(i32) @4, name_idx/unk(i32) @8, level(u16) @12, exp(u32) @14, ...
    lvl = struct.unpack_from('<H', b_mon, o + 12)[0]
    hp = struct.unpack_from('<I', b_mon, o + 20)[0]
    monsters[mid] = {
        'id': mid,
        'model': model,
        'level': lvl,
        'hp': hp,
        'raw_ints': fields,
        'raw_bytes': b_mon[o:o+70].hex()
    }

# Read mapmonster.bin to get monster IDs for target maps
b_map = (T / 'mapmonster.bin').read_bytes()
o = 0
n_maps = struct.unpack_from('<i', b_map, o)[0]; o += 4

target_maps = [401, 402, 410, 1312, 1707, 405, 72, 407, 301]

print("=== TARGET MAP MONSTERS ===")
for _ in range(n_maps):
    mp, n = struct.unpack_from('<ii', b_map, o); o += 8
    if mp in target_maps:
        print(f"\nMap {mp}:")
        for _ in range(n):
            m, c = struct.unpack_from('<ii', b_map, o); o += 8
            o += 16 * c
            m_data = monsters.get(m, {})
            name = monname.get(m, f'Mon_{m}')
            print(f"  MID: {m} | Name: {name} | Lv: {m_data.get('level')} | HP: {m_data.get('hp')} | Raw: {m_data.get('raw_ints')}")
    else:
        for _ in range(n):
            m, c = struct.unpack_from('<ii', b_map, o); o += 8
            o += 16 * c
