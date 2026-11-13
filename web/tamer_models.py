# -*- coding: utf-8 -*-
"""
Gamebryo NIF 20.3.0.9 -> glTF 2.0 (.glb) converter for all 21 DMO Thai Tamers.
Assembles each Tamer from their 5 base character part NIFs (head, up, down, hand, shoes)
bound to ONE canonical master skeleton (*_base.nif), with proper per-mesh NiAlphaProperty
handling and DXT/BGRA texture decoding into output/models/tamers/{tid}.glb.
"""

from __future__ import annotations

import io
import json
import math
import re
import struct
from pathlib import Path
from typing import Any

from PIL import Image
try:
    import mesh_hd as mhd
except Exception:
    try:
        from web import mesh_hd as mhd
    except Exception:
        mhd = None

ROOT = Path(__file__).resolve().parent.parent
CRACK_TAMER = Path(r"C:\Users\T4R\Desktop\AllWorks\CrackDMO\out_pack01\Data\Tamer")
MODEL_OUT = ROOT / "output" / "models" / "tamers"

PART_NAMES = ("head", "up", "down", "hand", "shoes")

# Starter Savers tamers (80001..80004) default up/down/hand/shoes are blank white undershirts;
# costume00.nif is their full-body iconic DATS / anime signature outfit (including head-to-toe).
TAMER_COSTUME_OVERRIDE: dict[int, str] = {
    80001: "costume00.nif",
    80002: "costume00.nif",
    80003: "costume00.nif",
    80004: "costume00.nif",
}

# Resting-pose blink eyelid spheres that sit over open eyeballs until keyframe idle rotates them away.
BLINK_COVER_BONES: dict[str, set[str]] = {
    "ikuto": {"Sphere01", "Sphere04"},
}

TAMER_FOLDER_MAP: dict[int, str] = {
    80001: "masaru",
    80002: "tohma",
    80003: "yoshino",
    80004: "ikuto",
    80005: "taichi",
    80006: "mimi",
    80007: "yamato",
    80008: "takeru",
    80009: "hikari",
    80010: "sora",
    80011: "takato",
    80012: "ruki",
    80013: "jyenrya",
    80014: "izmi",
    80015: "joe",
    80016: "katojury",
    80017: "akiyamaryo",
    80018: "hiro",
    80019: "ruli",
    80020: "higashimitaraikiyoshiro",
    80021: "DigimonEmperor",
}

BASE_NIF_OVERRIDE: dict[str, str] = {
    "takeru": "takeru.nif",
    "hiro": "amanokawahiro_base.nif",
    "ruli": "tsukiyono_ruli_base.nif",
    "higashimitaraikiyoshiro": "higashimitaraikiyoshiro_base.nif",
    "katojury": "katojuri_base.nif",
    "DigimonEmperor": "DigimonEmperor_Base.nif",
}


# ---------------------------------------------------------------------------
# Minimal 4x4 matrix math (row-major 4x4, M * v)
# ---------------------------------------------------------------------------
def _mat_id() -> list[float]:
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def _mat_mul(a: list[float], b: list[float]) -> list[float]:
    out = [0.0] * 16
    for r in range(4):
        r4 = r * 4
        for c in range(4):
            out[r4 + c] = (
                a[r4 + 0] * b[0 + c]
                + a[r4 + 1] * b[4 + c]
                + a[r4 + 2] * b[8 + c]
                + a[r4 + 3] * b[12 + c]
            )
    return out


def _mat_from_trs(trans: tuple[float, float, float], rot9: tuple[float, ...], scale: float) -> list[float]:
    return [
        rot9[0] * scale, rot9[1] * scale, rot9[2] * scale, trans[0],
        rot9[3] * scale, rot9[4] * scale, rot9[5] * scale, trans[1],
        rot9[6] * scale, rot9[7] * scale, rot9[8] * scale, trans[2],
        0.0, 0.0, 0.0, 1.0,
    ]


def _transform_point(m: list[float], x: float, y: float, z: float) -> tuple[float, float, float]:
    return (
        m[0] * x + m[1] * y + m[2] * z + m[3],
        m[4] * x + m[5] * y + m[6] * z + m[7],
        m[8] * x + m[9] * y + m[10] * z + m[11],
    )


def _transform_dir(m: list[float], x: float, y: float, z: float) -> tuple[float, float, float]:
    nx = m[0] * x + m[1] * y + m[2] * z
    ny = m[4] * x + m[5] * y + m[6] * z
    nz = m[8] * x + m[9] * y + m[10] * z
    ln = math.sqrt(nx * nx + ny * ny + nz * nz)
    if ln > 1e-8:
        return (nx / ln, ny / ln, nz / ln)
    return (0.0, 1.0, 0.0)


# ---------------------------------------------------------------------------
# Gamebryo NIF 20.3.0.9 parser
# ---------------------------------------------------------------------------
def _parse_nif_container(path: Path) -> tuple[list[str], list[tuple[int, str, bytes]], list[int]]:
    data = path.read_bytes()
    nl = data.find(b"\n")
    pos = nl + 1
    _ver, _end, _uver, nb = struct.unpack_from("<IBII", data, pos)
    pos += 13
    num_types = struct.unpack_from("<H", data, pos)[0]
    pos += 2
    types: list[str] = []
    for _ in range(num_types):
        ln = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        types.append(data[pos:pos + ln].decode("ascii", "replace"))
        pos += ln
    type_idxs = struct.unpack_from(f"<{nb}H", data, pos)
    pos += 2 * nb
    sizes = struct.unpack_from(f"<{nb}I", data, pos)
    pos += 4 * nb
    num_str, _max_str = struct.unpack_from("<II", data, pos)
    pos += 8
    strings: list[str] = []
    for _ in range(num_str):
        ln = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        strings.append(data[pos:pos + ln].decode("ascii", "replace"))
        pos += ln
    num_grp = struct.unpack_from("<I", data, pos)[0]
    pos += 4 + 4 * num_grp

    blocks: list[tuple[int, str, bytes]] = []
    for i in range(nb):
        sz = sizes[i]
        blocks.append((i, types[type_idxs[i]], data[pos:pos + sz]))
        pos += sz

    num_roots = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    roots = list(struct.unpack_from(f"<{num_roots}i", data, pos))
    return strings, blocks, roots


def _parse_avobj(bd: bytes) -> tuple[int, int, list[float], list[int], int]:
    pos = 0
    name_idx, num_ex = struct.unpack_from("<iI", bd, pos)
    pos += 8 + 4 * num_ex
    _ctrl, flags = struct.unpack_from("<iH", bd, pos)
    pos += 6
    trans = struct.unpack_from("<3f", bd, pos)
    pos += 12
    rot = struct.unpack_from("<9f", bd, pos)
    pos += 36
    scale, num_props = struct.unpack_from("<fI", bd, pos)
    pos += 8
    props = list(struct.unpack_from(f"<{num_props}i", bd, pos))
    pos += 4 * num_props
    _col, = struct.unpack_from("<i", bd, pos)
    pos += 4
    return name_idx, flags, _mat_from_trs(trans, rot, scale), props, pos


def _parse_avobj_trs(bd: bytes) -> tuple[int, int, tuple[float, float, float], tuple[float, ...], float, list[int], int]:
    pos = 0
    name_idx, num_ex = struct.unpack_from("<iI", bd, pos)
    pos += 8 + 4 * num_ex
    _ctrl, flags = struct.unpack_from("<iH", bd, pos)
    pos += 6
    trans = struct.unpack_from("<3f", bd, pos)
    pos += 12
    rot = struct.unpack_from("<9f", bd, pos)
    pos += 36
    scale, num_props = struct.unpack_from("<fI", bd, pos)
    pos += 8
    props = list(struct.unpack_from(f"<{num_props}i", bd, pos))
    pos += 4 * num_props
    _col, = struct.unpack_from("<i", bd, pos)
    pos += 4
    return name_idx, flags, trans, rot, scale, props, pos


def _parse_node(bd: bytes) -> dict[str, Any]:
    name_idx, flags, trans, rot, scale, props, pos = _parse_avobj_trs(bd)
    num_ch = struct.unpack_from("<I", bd, pos)[0]
    pos += 4
    children = list(struct.unpack_from(f"<{num_ch}i", bd, pos))
    return {
        "name_idx": name_idx,
        "flags": flags,
        "mat": _mat_from_trs(trans, rot, scale),
        "trs": (trans, rot, scale),
        "props": props,
        "children": children,
    }


def _parse_geometry(bd: bytes) -> dict[str, Any]:
    name_idx, flags, mat, props, pos = _parse_avobj(bd)
    data_ref, skin_ref = struct.unpack_from("<ii", bd, pos)
    return {"name_idx": name_idx, "flags": flags, "mat": mat, "props": props, "data_ref": data_ref, "skin_ref": skin_ref}


def _parse_geom_data(btype: str, bd: bytes) -> dict[str, Any]:
    pos = 4  # groupId
    num_v, _keep, _comp, has_v = struct.unpack_from("<HBBB", bd, pos)
    pos += 5
    verts: list[tuple[float, float, float]] = []
    if has_v and num_v:
        verts = [struct.unpack_from("<3f", bd, pos + i * 12) for i in range(num_v)]
        pos += 12 * num_v
    tspace_flags, has_n = struct.unpack_from("<HB", bd, pos)
    pos += 3
    num_uv_sets = tspace_flags & 63
    normals: list[tuple[float, float, float]] = []
    if has_n and num_v:
        normals = [struct.unpack_from("<3f", bd, pos + i * 12) for i in range(num_v)]
        pos += 12 * num_v
        if tspace_flags & 0xF000:
            pos += 24 * num_v
    pos += 16  # bounding sphere
    has_vc = bd[pos]
    pos += 1
    if has_vc and num_v:
        pos += 16 * num_v
    uvs: list[tuple[float, float]] = []
    if num_uv_sets > 0 and num_v:
        uvs = [struct.unpack_from("<2f", bd, pos + i * 8) for i in range(num_v)]
        pos += 8 * num_v * num_uv_sets
    pos += 6  # consistencyFlags + additionalData

    tris: list[tuple[int, int, int]] = []
    if btype == "NiTriStripsData":
        _num_tris, num_strips = struct.unpack_from("<HH", bd, pos)
        pos += 4
        lengths = struct.unpack_from(f"<{num_strips}H", bd, pos)
        pos += 2 * num_strips
        has_pts = bd[pos]
        pos += 1
        if has_pts:
            for ln in lengths:
                strip = struct.unpack_from(f"<{ln}H", bd, pos)
                pos += 2 * ln
                for j in range(ln - 2):
                    a, b, c = strip[j], strip[j + 1], strip[j + 2]
                    if a == b or b == c or a == c:
                        continue
                    if j & 1:
                        tris.append((a, c, b))
                    else:
                        tris.append((a, b, c))
    elif btype == "NiTriShapeData":
        num_tris, _num_tp, has_tris = struct.unpack_from("<HIB", bd, pos)
        pos += 7
        if has_tris and num_tris:
            for j in range(num_tris):
                a, b, c = struct.unpack_from("<3H", bd, pos + j * 6)
                if a != b and b != c and a != c:
                    tris.append((a, b, c))

    return {"verts": verts, "normals": normals, "uvs": uvs, "tris": tris}


def _parse_texturing_prop(bd: bytes) -> int | None:
    pos = 0
    _name_idx, num_ex = struct.unpack_from("<iI", bd, pos)
    pos += 8 + 4 * num_ex + 4
    _flags, tex_count = struct.unpack_from("<HI", bd, pos)
    pos += 6
    if tex_count > 0 and pos + 5 <= len(bd):
        has_base = bd[pos]
        pos += 1
        if has_base:
            src_ref = struct.unpack_from("<i", bd, pos)[0]
            return src_ref if src_ref >= 0 else None
    return None


def _parse_source_texture(bd: bytes) -> tuple[bool, int, str]:
    pos = 0
    _name_idx, num_ex = struct.unpack_from("<iI", bd, pos)
    pos += 8 + 4 * num_ex + 4
    use_ext = bd[pos]
    pos += 1
    fname_idx = struct.unpack_from("<i", bd, pos)[0]
    pos += 4
    if use_ext == 0:
        pixel_ref = struct.unpack_from("<i", bd, pos)[0]
        return False, pixel_ref, f"str#{fname_idx}"
    return True, -1, f"str#{fname_idx}"


def _parse_alpha_property(bd: bytes) -> tuple[int, int]:
    """Return (flags, threshold) from a NiAlphaProperty block."""
    if len(bd) < 3:
        return (0x00ed, 0)
    return struct.unpack_from("<HB", bd, len(bd) - 3)


def _decode_pixel_block(
    btype: str,
    bd: bytes,
    force_opaque: bool = False,
    blocks_map: dict[int, tuple[str, bytes]] | None = None,
) -> bytes | None:
    """Decode NiPersistentSrcTextureRendererData or NiPixelData into PNG bytes."""
    fmt = struct.unpack_from("<I", bd, 0)[0]
    comp0 = struct.unpack_from("<I", bd, 19)[0]
    num_mips = struct.unpack_from("<I", bd, 63)[0]
    if num_mips == 0:
        return None
    w0, h0, off0 = struct.unpack_from("<III", bd, 71)
    mip_end = 71 + 12 * num_mips
    px_start = mip_end + (16 if btype == "NiPersistentSrcTextureRendererData" else 8)
    data_off = px_start + off0

    if fmt == 4:
        nbytes = max(1, (w0 + 3) // 4) * max(1, (h0 + 3) // 4) * 8
        img = Image.frombytes("RGBA", (w0, h0), bd[data_off:data_off + nbytes], "bcn", 1)
    elif fmt == 5:
        nbytes = max(1, (w0 + 3) // 4) * max(1, (h0 + 3) // 4) * 16
        img = Image.frombytes("RGBA", (w0, h0), bd[data_off:data_off + nbytes], "bcn", 2)
    elif fmt == 6:
        nbytes = max(1, (w0 + 3) // 4) * max(1, (h0 + 3) // 4) * 16
        img = Image.frombytes("RGBA", (w0, h0), bd[data_off:data_off + nbytes], "bcn", 3)
    elif fmt == 0:
        nbytes = w0 * h0 * 3
        mode = "BGR" if comp0 == 2 else "RGB"
        img = Image.frombytes("RGB", (w0, h0), bd[data_off:data_off + nbytes], "raw", mode).convert("RGBA")
    elif fmt == 1:
        nbytes = w0 * h0 * 4
        mode = "BGRA" if comp0 == 2 else "RGBA"
        img = Image.frombytes("RGBA", (w0, h0), bd[data_off:data_off + nbytes], "raw", mode)
    elif fmt in (2, 3) and blocks_map is not None:
        pal_ref = struct.unpack_from("<i", bd, 59)[0]
        if pal_ref not in blocks_map or blocks_map[pal_ref][0] != "NiPalette":
            return None
        pbd = blocks_map[pal_ref][1]
        if len(pbd) < 5 + 1024:
            return None
        pal_rgba = pbd[5:5 + 1024]
        idxs = bd[data_off:data_off + w0 * h0]
        if len(idxs) < w0 * h0:
            return None
        rgba = bytearray(w0 * h0 * 4)
        for pi, idx in enumerate(idxs):
            po = idx * 4
            ro = pi * 4
            rgba[ro:ro + 4] = pal_rgba[po:po + 4]
        img = Image.frombytes("RGBA", (w0, h0), bytes(rgba))
    else:
        return None

    # DXT1 with no NiAlphaProperty uses index 3 as black RGB with alpha=0, which must render opaque.
    if force_opaque:
        img = img.convert("RGB")

    if max(img.size) > 1024:
        img = img.resize((img.width // 2, img.height // 2), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _parse_skin_instance(bd: bytes) -> tuple[int, int, list[int]]:
    data_ref, _part_ref, root_ref, num_bones = struct.unpack_from("<iiiI", bd, 0)
    bones = list(struct.unpack_from(f"<{num_bones}i", bd, 16))
    return data_ref, root_ref, bones


def _parse_skin_data(bd: bytes) -> tuple[list[float], list[tuple[list[float], list[tuple[int, float]]]]]:
    rot = struct.unpack_from("<9f", bd, 0)
    trans = struct.unpack_from("<3f", bd, 36)
    scale, num_bones, has_w = struct.unpack_from("<fIB", bd, 48)
    skin_mat = _mat_from_trs(trans, rot, scale)
    pos = 57
    bones_data = []
    for _ in range(num_bones):
        brot = struct.unpack_from("<9f", bd, pos)
        btrans = struct.unpack_from("<3f", bd, pos + 36)
        bscale = struct.unpack_from("<f", bd, pos + 48)[0]
        pos += 52 + 16 + 2
        nv = struct.unpack_from("<H", bd, pos - 2)[0]
        weights = []
        if has_w and nv:
            for _j in range(nv):
                vi, wt = struct.unpack_from("<Hf", bd, pos)
                pos += 6
                weights.append((vi, wt))
        bones_data.append((_mat_from_trs(btrans, brot, bscale), weights))
    return skin_mat, bones_data


def _quat_to_rot9(w: float, x: float, y: float, z: float) -> tuple[float, ...]:
    n = math.sqrt(w * w + x * x + y * y + z * z)
    if n < 1e-8:
        return (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    w, x, y, z = w / n, x / n, y / n, z / n
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return (
        1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz),       2.0 * (xz + wy),
        2.0 * (xy + wz),       1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx),
        2.0 * (xz - wy),       2.0 * (yz + wx),       1.0 - 2.0 * (xx + yy),
    )


def _valid_kf_float(v: float) -> bool:
    return math.isfinite(v) and abs(v) < 1e30


def find_idle_kf(folder: Path) -> Path | None:
    """Locate the canonical idle .kf animation file via .kfm table or directory glob."""
    if not folder.is_dir():
        return None
    files = list(folder.iterdir())
    by_low = {f.name.lower(): f for f in files if f.is_file()}

    # 1. Check .kfm animation names for canonical idle/*.kf
    for f in files:
        if f.suffix.lower() == ".kfm":
            try:
                data = f.read_bytes()
                kf_names = [s.decode("ascii", "ignore") for s in re.findall(rb"[A-Za-z0-9_.\-]+\.kf", data)]
                for pat in (r"^idle\.kf$", r"_idle\.kf$", r"_idl\.kf$", r"idle\.kf$"):
                    for kn in kf_names:
                        kl = kn.lower()
                        if "ride" in kl or "_c.kf" in kl or "idlec" in kl or "shk" in kl or "hre" in kl:
                            continue
                        if re.search(pat, kl) and kl in by_low:
                            return by_low[kl]
            except Exception:
                pass

    # 2. Fallback direct filenames
    for cand in (f"{folder.name.lower()}_idle.kf", "idle.kf"):
        if cand in by_low:
            return by_low[cand]
    for kl, f in sorted(by_low.items()):
        if kl.endswith(".kf") and ("_idle.kf" in kl or "_idl.kf" in kl):
            if "ride" not in kl and "_c.kf" not in kl and "idlec" not in kl and "shk" not in kl and "hre" not in kl:
                return f
    return None


def parse_kf_pose(kf_path: Path) -> dict[str, tuple[tuple[float, float, float] | None, tuple[float, ...] | None, float | None]]:
    """Extract frame-0 local (trans, rot9, scale) overrides per bone from a .kf NiControllerSequence."""
    strs, blks, rts = _parse_nif_container(kf_path)
    bmap = {i: (bt, bd) for i, bt, bd in blks}
    if not rts or rts[0] not in bmap or bmap[rts[0]][0] != "NiControllerSequence":
        return {}
    bd = bmap[rts[0]][1]
    _sidx, num_cb, _grow = struct.unpack_from("<iII", bd, 0)
    pos = 12

    bspline_cache: dict[int, tuple[list[float], list[int]]] = {}

    def get_bspline(sref: int) -> tuple[list[float], list[int]]:
        if sref in bspline_cache:
            return bspline_cache[sref]
        if sref not in bmap or bmap[sref][0] != "NiBSplineData":
            return ([], [])
        sbd = bmap[sref][1]
        n_fp = struct.unpack_from("<I", sbd, 0)[0]
        floats = list(struct.unpack_from(f"<{n_fp}f", sbd, 4)) if n_fp else []
        off = 4 + 4 * n_fp
        n_cp = struct.unpack_from("<I", sbd, off)[0]
        ints = list(struct.unpack_from(f"<{n_cp}h", sbd, off + 4)) if n_cp else []
        bspline_cache[sref] = (floats, ints)
        return floats, ints

    pose: dict[str, tuple[tuple[float, float, float] | None, tuple[float, ...] | None, float | None]] = {}
    for _ in range(num_cb):
        if pos + 28 > len(bd):
            break
        interp_ref, _ctrl, node_s, _prop_s, _ctype_s, _cid_s, _iid_s = struct.unpack_from("<7i", bd, pos)
        pos += 28
        bname = strs[node_s] if 0 <= node_s < len(strs) else ""
        if not bname or interp_ref not in bmap:
            continue
        ibt, ibd = bmap[interp_ref]
        tr = None
        rot = None
        sc = None
        if ibt == "NiTransformInterpolator" and len(ibd) >= 36:
            tx, ty, tz, qw, qx, qy, qz, s = struct.unpack_from("<8f", ibd, 0)
            dref = struct.unpack_from("<i", ibd, 32)[0]
            if _valid_kf_float(tx) and _valid_kf_float(ty) and _valid_kf_float(tz):
                tr = (tx, ty, tz)
            if _valid_kf_float(qw) and _valid_kf_float(qx) and _valid_kf_float(qy) and _valid_kf_float(qz):
                rot = _quat_to_rot9(qw, qx, qy, qz)
            if _valid_kf_float(s) and s > 0:
                sc = s
            if dref in bmap and bmap[dref][0] == "NiTransformData":
                dbd = bmap[dref][1]
                p = 0
                if p + 4 <= len(dbd):
                    n_rkeys = struct.unpack_from("<I", dbd, p)[0]
                    p += 4
                    if n_rkeys > 0 and p + 4 <= len(dbd):
                        rtype = struct.unpack_from("<I", dbd, p)[0]
                        p += 4
                        if rtype in (1, 2, 3) and p + 20 <= len(dbd):
                            _t0, kqw, kqx, kqy, kqz = struct.unpack_from("<5f", dbd, p)
                            if rot is None and _valid_kf_float(kqw):
                                rot = _quat_to_rot9(kqw, kqx, kqy, kqz)
                            ksize = 20 if rtype != 3 else 32
                            p += n_rkeys * ksize
                    # Translation keys
                    if p + 4 <= len(dbd):
                        n_tkeys = struct.unpack_from("<I", dbd, p)[0]
                        p += 4
                        if n_tkeys > 0 and p + 4 <= len(dbd):
                            ttype = struct.unpack_from("<I", dbd, p)[0]
                            p += 4
                            if ttype in (1, 2, 3) and p + 16 <= len(dbd):
                                _t0, kx, ky, kz = struct.unpack_from("<4f", dbd, p)
                                if tr is None and _valid_kf_float(kx) and _valid_kf_float(ky) and _valid_kf_float(kz):
                                    tr = (kx, ky, kz)
        elif ibt == "NiBSplineCompTransformInterpolator" and len(ibd) >= 84:
            _st, _sp, sref, _bref = struct.unpack_from("<ffii", ibd, 0)
            tx, ty, tz = struct.unpack_from("<3f", ibd, 16)
            qw, qx, qy, qz = struct.unpack_from("<4f", ibd, 28)
            s, = struct.unpack_from("<f", ibd, 44)
            to_off, ro_off, so_off, tb, thr, rb, rhr, sb, shr = struct.unpack_from("<3I6f", ibd, 48)
            _fl, cpts = get_bspline(sref)
            if to_off != 65535 and to_off + 2 < len(cpts) and _valid_kf_float(tb) and _valid_kf_float(thr):
                tr = (
                    (cpts[to_off] / 32767.0) * thr + tb,
                    (cpts[to_off + 1] / 32767.0) * thr + tb,
                    (cpts[to_off + 2] / 32767.0) * thr + tb,
                )
            elif _valid_kf_float(tx) and _valid_kf_float(ty) and _valid_kf_float(tz):
                tr = (tx, ty, tz)
            if ro_off != 65535 and ro_off + 3 < len(cpts) and _valid_kf_float(rb) and _valid_kf_float(rhr):
                q0 = (cpts[ro_off] / 32767.0) * rhr + rb
                q1 = (cpts[ro_off + 1] / 32767.0) * rhr + rb
                q2 = (cpts[ro_off + 2] / 32767.0) * rhr + rb
                q3 = (cpts[ro_off + 3] / 32767.0) * rhr + rb
                rot = _quat_to_rot9(q0, q1, q2, q3)
            elif _valid_kf_float(qw) and _valid_kf_float(qx) and _valid_kf_float(qy) and _valid_kf_float(qz):
                rot = _quat_to_rot9(qw, qx, qy, qz)
            if so_off != 65535 and so_off < len(cpts) and _valid_kf_float(sb) and _valid_kf_float(shr):
                sc = (cpts[so_off] / 32767.0) * shr + sb
            elif _valid_kf_float(s) and s > 0:
                sc = s
        pose[bname] = (tr, rot, sc)
    return pose


# ---------------------------------------------------------------------------
# Master Skeleton + Assemble 5 modular part NIFs -> single GLB
# ---------------------------------------------------------------------------
def _is_identity_rot(rot: tuple[float, ...] | list[float], tol: float = 0.08) -> bool:
    id9 = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    return all(abs(rot[i] - id9[i]) < tol for i in range(9))


def _should_apply_kf_pose(
    nm: str,
    nif_trs: tuple[tuple[float, float, float], tuple[float, ...], float],
    kf_trs: tuple[tuple[float, float, float] | None, tuple[float, ...] | None, float | None],
) -> bool:
    if not nm or nm.lower() in ("scene root", "root"):
        return False
    # Max Biped roots (Bip01 / Bip001) intentionally carry a zeroed (0,0,0)+identity track in idle.kf
    # because their offset/facing is moved into the sibling "* NonAccum" child node.
    if nm.lower().startswith(("bip01", "bip001", "bip02")):
        return True
    ptr, prot, _psc = kf_trs
    # Gamebryo accumulation roots (Main_Dummy, Dummy01, Root, com01) store an axis-conversion rotation
    # in the NIF while the idle .kf carries a zeroed (0,0,0)+identity track; applying it flattens the mesh.
    if (
        ptr is not None
        and max(abs(c) for c in ptr) < 1e-3
        and prot is not None
        and _is_identity_rot(prot)
        and not _is_identity_rot(nif_trs[1], tol=0.1)
    ):
        return False
    return True


def _load_master_bones(tamer_dir: Path) -> dict[str, list[float]]:
    """Load canonical bone world transforms from *_base.nif posed with idle .kf."""
    bfn = BASE_NIF_OVERRIDE.get(tamer_dir.name, f"{tamer_dir.name}_base.nif")
    bp = tamer_dir / bfn
    if not bp.exists():
        return {}
    kf_path = find_idle_kf(tamer_dir)
    pose = parse_kf_pose(kf_path) if kf_path else {}

    strings, blocks, roots = _parse_nif_container(bp)
    nodes = {i: _parse_node(bd) for i, bt, bd in blocks if bt == "NiNode"}
    wm: dict[str, list[float]] = {}

    def walk(ref: int, parent_mat: list[float]):
        if ref in nodes:
            nd = nodes[ref]
            nm = strings[nd["name_idx"]] if 0 <= nd["name_idx"] < len(strings) else ""
            lmat = nd["mat"]
            if nm and nm in pose and _should_apply_kf_pose(nm, nd["trs"], pose[nm]):
                tr, rot, sc = nd["trs"]
                ptr, prot, psc = pose[nm]
                if ptr is not None:
                    tr = ptr
                if prot is not None:
                    rot = prot
                if psc is not None:
                    sc = psc
                lmat = _mat_from_trs(tr, rot, sc)
            wmat = _mat_mul(parent_mat, lmat)
            if nm and nm not in wm:
                wm[nm] = wmat
            for ch in nd["children"]:
                if ch >= 0:
                    walk(ch, wmat)

    for r in roots:
        if r >= 0:
            walk(r, _mat_id())
    return wm


def _extract_part_meshes(
    part_path: Path,
    master_bones: dict[str, list[float]],
) -> list[dict[str, Any]]:
    """Extract only real skinned character meshes from one part NIF bound to master_bones."""
    strings, blocks, roots = _parse_nif_container(part_path)
    nodes: dict[int, dict[str, Any]] = {}
    geoms: dict[int, dict[str, Any]] = {}
    geom_datas: dict[int, dict[str, Any]] = {}
    tex_props: dict[int, int | None] = {}
    alpha_props: set[int] = set()
    src_texs: dict[int, tuple[bool, int, str]] = {}
    raw_pixel_blocks: dict[int, tuple[str, bytes]] = {}
    skin_insts: dict[int, tuple[int, int, list[int]]] = {}
    skin_datas: dict[int, Any] = {}

    for idx, bt, bd in blocks:
        if bt == "NiNode":
            nodes[idx] = _parse_node(bd)
        elif bt in ("NiTriStrips", "NiTriShape"):
            geoms[idx] = _parse_geometry(bd)
        elif bt in ("NiTriStripsData", "NiTriShapeData"):
            geom_datas[idx] = _parse_geom_data(bt, bd)
        elif bt == "NiTexturingProperty":
            tex_props[idx] = _parse_texturing_prop(bd)
        elif bt == "NiAlphaProperty":
            alpha_props.add(idx)
        elif bt == "NiSourceTexture":
            src_texs[idx] = _parse_source_texture(bd)
        elif bt in ("NiPersistentSrcTextureRendererData", "NiPixelData"):
            raw_pixel_blocks[idx] = (bt, bd)
        elif bt == "NiSkinInstance":
            skin_insts[idx] = _parse_skin_instance(bd)
        elif bt == "NiSkinData":
            skin_datas[idx] = _parse_skin_data(bd)

    world_mats: dict[int, list[float]] = {}
    mesh_draws: list[tuple[int, dict[str, Any], list[float], int | None, bool]] = []

    def resolve_props(props: list[int], inherited_px: int | None, inherited_alpha: bool) -> tuple[int | None, bool]:
        px = inherited_px
        has_ap = inherited_alpha
        for pr in props:
            if pr in tex_props and tex_props[pr] is not None:
                st = src_texs.get(tex_props[pr])
                if st and not st[0] and st[1] in raw_pixel_blocks:
                    px = st[1]
            if pr in alpha_props:
                has_ap = True
        return px, has_ap

    def walk(ref: int, parent_mat: list[float], inherited_px: int | None, inherited_alpha: bool):
        if ref in nodes:
            nd = nodes[ref]
            nm = strings[nd["name_idx"]] if 0 <= nd["name_idx"] < len(strings) else ""
            # Snap bone world matrix to master_bones when available so parts exported
            # under stale poses (Tohma, Ikuto, Mimi, Hiro shoes) still align seamlessly.
            if nm and nm in master_bones:
                wmat = master_bones[nm]
            else:
                wmat = _mat_mul(parent_mat, nd["mat"])
            world_mats[ref] = wmat
            px, has_ap = resolve_props(nd["props"], inherited_px, inherited_alpha)
            for ch in nd["children"]:
                if ch >= 0:
                    walk(ch, wmat, px, has_ap)
        elif ref in geoms:
            gm = geoms[ref]
            wmat = _mat_mul(parent_mat, gm["mat"])
            world_mats[ref] = wmat
            px, has_ap = resolve_props(gm["props"], inherited_px, inherited_alpha)
            mesh_draws.append((ref, gm, wmat, px, has_ap))

    for r in roots:
        if r >= 0:
            walk(r, _mat_id(), None, False)

    default_px = next(iter(raw_pixel_blocks.keys()), None)
    png_cache: dict[tuple[int, bool], bytes | None] = {}
    results: list[dict[str, Any]] = []

    blink_bone_names = BLINK_COVER_BONES.get(part_path.parent.name.lower(), set())

    blocks_map = {i: (bt, bd) for i, bt, bd in blocks}
    for _g_ref, gm, wmat, px_ref, has_ap in mesh_draws:
        is_skinned = gm["skin_ref"] in skin_insts
        if not is_skinned:
            continue

        gdata = geom_datas.get(gm["data_ref"])
        if not gdata or not gdata["verts"] or not gdata["tris"]:
            continue

        verts = gdata["verts"]
        normals = gdata["normals"] or [(0.0, 0.0, 1.0)] * len(verts)
        uvs = gdata["uvs"] or [(0.0, 0.0)] * len(verts)
        blink_verts: set[int] = set()

        if is_skinned:
            sdata_ref, _sroot, bone_refs = skin_insts[gm["skin_ref"]]
            if sdata_ref in skin_datas:
                _smat, bones_info = skin_datas[sdata_ref]
                acc = [[0.0, 0.0, 0.0] for _ in range(len(verts))]
                acc_n = [[0.0, 0.0, 0.0] for _ in range(len(verts))]
                w_sum = [0.0] * len(verts)
                for b_i, bref in enumerate(bone_refs):
                    if b_i >= len(bones_info) or bref not in world_mats:
                        continue
                    bname = ""
                    if blink_bone_names and bref in nodes:
                        ni = nodes[bref]["name_idx"]
                        bname = strings[ni] if 0 <= ni < len(strings) else ""
                    boff, weights = bones_info[b_i]
                    bm = _mat_mul(world_mats[bref], boff)
                    for vi, wt in weights:
                        if vi < len(verts):
                            if bname in blink_bone_names and wt > 0.5:
                                blink_verts.add(vi)
                            px, py, pz = _transform_point(bm, *verts[vi])
                            acc[vi][0] += px * wt
                            acc[vi][1] += py * wt
                            acc[vi][2] += pz * wt
                            nx, ny, nz = _transform_dir(bm, *normals[vi])
                            acc_n[vi][0] += nx * wt
                            acc_n[vi][1] += ny * wt
                            acc_n[vi][2] += nz * wt
                            w_sum[vi] += wt
                xformed_pos = []
                xformed_nrm = []
                for vi in range(len(verts)):
                    if w_sum[vi] > 1e-6:
                        xformed_pos.append((acc[vi][0] / w_sum[vi], acc[vi][1] / w_sum[vi], acc[vi][2] / w_sum[vi]))
                        xformed_nrm.append((acc_n[vi][0], acc_n[vi][1], acc_n[vi][2]))
                    else:
                        xformed_pos.append(_transform_point(wmat, *verts[vi]))
                        xformed_nrm.append(_transform_dir(wmat, *normals[vi]))
            else:
                xformed_pos = [_transform_point(wmat, *v) for v in verts]
                xformed_nrm = [_transform_dir(wmat, *n) for n in normals]
        else:
            xformed_pos = [_transform_point(wmat, *v) for v in verts]
            xformed_nrm = [_transform_dir(wmat, *n) for n in normals]

        pos_out = []
        nrm_out = []
        uv_out = []
        for (vx, vy, vz), (nx, ny, nz), (u, v) in zip(xformed_pos, xformed_nrm, uvs):
            gx, gy, gz = vx, vz, -vy
            gnx, gny, gnz = nx, nz, -ny
            ln = math.sqrt(gnx * gnx + gny * gny + gnz * gnz) or 1.0
            pos_out.append((gx, gy, gz))
            nrm_out.append((gnx / ln, gny / ln, gnz / ln))
            uv_out.append((u, v))

        idx_out: list[int] = []
        for a, b, c in gdata["tris"]:
            if a < len(verts) and b < len(verts) and c < len(verts):
                if blink_verts and (a in blink_verts or b in blink_verts or c in blink_verts):
                    continue
                idx_out.extend((a, b, c))

        use_px = px_ref if px_ref in raw_pixel_blocks else default_px
        png_bytes = None
        if use_px is not None:
            ckey = (use_px, not has_ap)
            if ckey not in png_cache:
                bt_px, bd_px = raw_pixel_blocks[use_px]
                png_cache[ckey] = _decode_pixel_block(bt_px, bd_px, force_opaque=not has_ap, blocks_map=blocks_map)
            png_bytes = png_cache[ckey]

        results.append({
            "png": png_bytes,
            "alpha": has_ap,
            "pos": pos_out,
            "nrm": nrm_out,
            "uv": uv_out,
            "idx": idx_out,
        })

    return results


def convert_tamer_dir_to_glb(tamer_dir: Path, out_path: Path, full_costume: str | None = None) -> dict[str, Any]:
    master_bones = _load_master_bones(tamer_dir)
    part_files = {p.stem.lower(): p for p in tamer_dir.glob("*.nif") if p.stem.lower() in PART_NAMES}
    buckets_by_mat: dict[tuple[bytes | None, bool], dict[str, list]] = {}

    nif_list: list[Path] = []
    if full_costume and (tamer_dir / full_costume).exists():
        nif_list = [tamer_dir / full_costume]
    else:
        nif_list = [part_files[k] for k in PART_NAMES if k in part_files]

    for pp in nif_list:
        for chunk in _extract_part_meshes(pp, master_bones):
            mkey = (chunk["png"], chunk["alpha"])
            b = buckets_by_mat.setdefault(mkey, {"pos": [], "nrm": [], "uv": [], "idx": []})
            base_v = len(b["pos"])
            b["pos"].extend(chunk["pos"])
            b["nrm"].extend(chunk["nrm"])
            b["uv"].extend(chunk["uv"])
            b["idx"].extend(i + base_v for i in chunk["idx"])

    bin_buf = bytearray()
    buffer_views: list[dict[str, Any]] = []
    accessors: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    textures: list[dict[str, Any]] = []
    materials: list[dict[str, Any]] = []
    primitives: list[dict[str, Any]] = []

    def add_view(raw: bytes, target: int | None = None) -> int:
        while len(bin_buf) % 4 != 0:
            bin_buf.append(0)
        off = len(bin_buf)
        bin_buf.extend(raw)
        bv: dict[str, Any] = {"buffer": 0, "byteOffset": off, "byteLength": len(raw)}
        if target is not None:
            bv["target"] = target
        buffer_views.append(bv)
        return len(buffer_views) - 1

    total_tris = 0
    total_verts = 0
    all_min = [1e9, 1e9, 1e9]
    all_max = [-1e9, -1e9, -1e9]

    global_guide = mhd.compute_global_spatial_guide(
        (b["pos"], b["idx"]) for b in buckets_by_mat.values() if b["pos"] and b["idx"]
    )
    png_hd_cache: dict[bytes, bytes | None] = {}

    for m_i, ((png_bytes, use_alpha), bucket) in enumerate(buckets_by_mat.items()):
        if not bucket["pos"] or not bucket["idx"]:
            continue

        r_pos, r_nrm, r_uv, r_idx = mhd.refine_chunk_hd(
            bucket["pos"],
            bucket["nrm"],
            bucket["uv"],
            bucket["idx"],
            alpha_mode="BLEND" if use_alpha else "OPAQUE",
            smooth_deg=55.0,
            subdivide=True,
            spatial_guide=global_guide,
        )

        mat_def: dict[str, Any] = {
            "name": f"mat_{m_i}",
            "pbrMetallicRoughness": {"metallicFactor": 0.02, "roughnessFactor": 0.62},
            "doubleSided": True,
        }
        if png_bytes:
            if png_bytes not in png_hd_cache:
                png_hd_cache[png_bytes] = mhd.upscale_anime_png_hd(png_bytes, target_max=1024)
            hd_png = png_hd_cache[png_bytes] or png_bytes
            bv_img = add_view(hd_png)
            img_idx = len(images)
            images.append({"bufferView": bv_img, "mimeType": "image/png"})
            tex_idx = len(textures)
            textures.append({"source": img_idx})
            mat_def["pbrMetallicRoughness"]["baseColorTexture"] = {"index": tex_idx}
            if use_alpha:
                mat_def["alphaMode"] = "BLEND"
        mat_idx = len(materials)
        materials.append(mat_def)

        n_v = len(r_pos)
        total_verts += n_v
        total_tris += len(r_idx) // 3
        mn = [min(p[k] for p in r_pos) for k in range(3)]
        mx = [max(p[k] for p in r_pos) for k in range(3)]
        for k in range(3):
            all_min[k] = min(all_min[k], mn[k])
            all_max[k] = max(all_max[k], mx[k])

        pos_raw = b"".join(struct.pack("<3f", *p) for p in r_pos)
        nrm_raw = b"".join(struct.pack("<3f", *n) for n in r_nrm)
        uv_raw = b"".join(struct.pack("<2f", *uv) for uv in r_uv)
        idx_raw = struct.pack(f"<{len(r_idx)}I", *r_idx)

        bv_pos = add_view(pos_raw, 34962)
        bv_nrm = add_view(nrm_raw, 34962)
        bv_uv = add_view(uv_raw, 34962)
        bv_idx = add_view(idx_raw, 34963)

        acc_pos = len(accessors)
        accessors.append({"bufferView": bv_pos, "componentType": 5126, "count": n_v, "type": "VEC3", "min": mn, "max": mx})
        acc_nrm = len(accessors)
        accessors.append({"bufferView": bv_nrm, "componentType": 5126, "count": n_v, "type": "VEC3"})
        acc_uv = len(accessors)
        accessors.append({"bufferView": bv_uv, "componentType": 5126, "count": n_v, "type": "VEC2"})
        acc_idx = len(accessors)
        accessors.append({"bufferView": bv_idx, "componentType": 5125, "count": len(r_idx), "type": "SCALAR"})

        primitives.append({
            "attributes": {"POSITION": acc_pos, "NORMAL": acc_nrm, "TEXCOORD_0": acc_uv},
            "indices": acc_idx,
            "material": mat_idx,
        })

    while len(bin_buf) % 4 != 0:
        bin_buf.append(0)

    gltf: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": "dmo-thai-wiki-nif2glb-v3"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": tamer_dir.name}],
        "meshes": [{"primitives": primitives}],
        "materials": materials,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(bin_buf)}],
    }
    if images:
        gltf["images"] = images
    if textures:
        gltf["textures"] = textures

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4 != 0:
        json_bytes += b" "

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_buf)
    header = struct.pack("<III", 0x46546C67, 2, total_len)
    json_hdr = struct.pack("<II", len(json_bytes), 0x4E4F534A)
    bin_hdr = struct.pack("<II", len(bin_buf), 0x004E4942)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(header + json_hdr + json_bytes + bin_hdr + bytes(bin_buf))
    return {
        "verts": total_verts,
        "tris": total_tris,
        "bytes": total_len,
        "textures": len(images),
        "min": all_min,
        "max": all_max,
    }


def build_all(force: bool = False) -> dict[int, dict[str, Any]]:
    """Ensure all 21 Tamer character .glb models exist under output/models/tamers/ and return metadata map."""
    MODEL_OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = MODEL_OUT / "manifest.json"
    existing: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    if not CRACK_TAMER.exists():
        return {int(k): v for k, v in existing.items()}

    manifest: dict[int, dict[str, Any]] = {}
    dirty = False
    for tid, dname in sorted(TAMER_FOLDER_MAP.items()):
        tdir = CRACK_TAMER / dname
        glb_path = MODEL_OUT / f"{tid}.glb"
        if not tdir.exists():
            continue
        cached = existing.get(str(tid))
        if not force and cached and glb_path.exists() and cached.get("v") == 9:
            manifest[tid] = cached
            continue
        cfile = TAMER_COSTUME_OVERRIDE.get(tid)
        meta = convert_tamer_dir_to_glb(tdir, glb_path, full_costume=cfile)
        meta["v"] = 9
        meta["url"] = f"/models/tamers/{tid}.glb"
        meta["nif"] = f"{dname}/{cfile}" if cfile else f"{dname}/ (head+up+down+hand+shoes)"
        manifest[tid] = meta
        dirty = True

    if dirty or not manifest_path.exists():
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    res = build_all(force=True)
    print(f"Converted {len(res)} v7 Tamer 3D models:")
    for tid, m in sorted(res.items()):
        h = m["max"][1] - m["min"][1]
        print(f"  {tid} ({m['nif']}): verts={m['verts']:4d} tris={m['tris']:4d} tex={m['textures']} height={h:5.1f} y0={m['min'][1]:5.1f} size={m['bytes']//1024:4d}KB")
