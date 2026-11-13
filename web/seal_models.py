# -*- coding: utf-8 -*-
"""
Gamebryo NIF -> glTF 2.0 (.glb) converter for DMO Seal Master Leader pets.
Reuses tamer_models NIF parser and DXT/BGRA pixel decoder to export all
Digimon / NPC Seal Leader models into output/models/seals/{leader_id}.glb.
"""

from __future__ import annotations

import io
import json
import math
import os
import re
import struct
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image
try:
    import tamer_models as tm
    import mesh_hd as mhd
except ImportError:
    from web import tamer_models as tm
    from web import mesh_hd as mhd

ROOT = Path(__file__).resolve().parent.parent
CRACKDMO = Path(os.environ.get("CRACKDMO_DIR", ""))
if not (CRACKDMO / "out_decrypted").exists():
    CRACKDMO = Path(__file__).resolve().parent.parent.parent / "CrackDMO"
if not (CRACKDMO / "out_decrypted").exists():
    CRACKDMO = Path(__file__).resolve().parent.parent / "CrackDMO"
if not (CRACKDMO / "out_decrypted").exists():
    CRACKDMO = Path(r"C:\Users\T4R\Desktop\AllWorks\CrackDMO")
PACK01 = CRACKDMO / "out_pack01"
TBL_DIR = CRACKDMO / "out_decrypted" / "data" / "bin" / "table"
SEAL_MODEL_OUT = ROOT / "output" / "models" / "seals"

# Fallback map for the few sealleader IDs not indexed cleanly in Model.dat
LEADER_NIF_OVERRIDES: dict[int, str] = {
    21138: "Data/npc/culumon/culumon.nif",
    30483: "Data/npc/santa/santa.nif",
    96019: "Data/npc/santa/santa.nif",
    45167: "Data/npc/mudfrigimon_dw/mudfrigimon.nif",
}

SKIP_HELPER_KEYWORDS = (
    "bip01", "biped", "collision", "bound", "shadow", "dummy",
    "pick", "hitbox", "(hide)", "eye_closed", "blink",
)
VFX_SHELL_KEYWORDS = (
    "aure", "aura", "glow", "helix", "effect", "fx_", "wing_plane", "wing_hit",
    "wing_light", "polish", "body_line", "polymesh", "plane", "sphere",
    "geosphere", "wave_", "light0", "flare", "ring", "mark", "core_jual",
)


def _is_helper_name(name: str) -> bool:
    gl = name.lower().strip()
    if gl == "bone" or gl.startswith("bone@#"):
        return True
    return any(k in gl for k in SKIP_HELPER_KEYWORDS)


def _is_vfx_shell_name(name: str) -> bool:
    gl = name.lower().strip()
    return any(k in gl for k in VFX_SHELL_KEYWORDS)


def _parse_material_diffuse(bd: bytes) -> tuple[float, float, float] | None:
    if len(bd) < 32:
        return None
    try:
        _nidx, nex = struct.unpack_from("<iI", bd, 0)
        off = 8 + 4 * nex + 12  # skip ambient(3f) -> read diffuse(3f)
        if off + 12 <= len(bd):
            r, g, b = struct.unpack_from("<3f", bd, off)
            return (max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b)))
    except Exception:
        pass
    return None


def _load_external_tex(tex_name: str, nif_dir: Path, force_opaque: bool) -> bytes | None:
    if not tex_name:
        return None
    fn = os.path.basename(tex_name.replace("\\", "/"))
    cand = nif_dir / fn
    if not cand.is_file():
        # case-insensitive lookup in nif_dir
        low = fn.lower()
        for p in nif_dir.iterdir():
            if p.name.lower() == low:
                cand = p
                break
        else:
            # try stem match (.tga / .dds / .bmp)
            stem = Path(fn).stem.lower()
            for p in nif_dir.iterdir():
                if p.stem.lower() == stem and p.suffix.lower() in (".dds", ".tga", ".bmp", ".png"):
                    cand = p
                    break
    if not cand.is_file():
        return None
    try:
        img = Image.open(cand).convert("RGBA")
        if force_opaque:
            img = img.convert("RGB")
        if max(img.size) > 1024:
            img = img.resize((img.width // 2, img.height // 2), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return None


def _extract_nif_meshes(nif_path: Path) -> list[dict[str, Any]]:
    """Extract geometry chunks (idle-posed, visible, clean textures/alpha) with decoded PNGs."""
    strings, blocks, roots = tm._parse_nif_container(nif_path)
    blocks_map = {i: (bt, bd) for i, bt, bd in blocks}
    nodes: dict[int, dict[str, Any]] = {}
    geoms: dict[int, dict[str, Any]] = {}
    geom_datas: dict[int, dict[str, Any]] = {}
    tex_props: dict[int, int | None] = {}
    alpha_props: dict[int, tuple[int, int]] = {}
    mat_props: dict[int, tuple[float, float, float] | None] = {}
    src_texs: dict[int, tuple[bool, int, str]] = {}
    raw_pixel_blocks: dict[int, tuple[str, bytes]] = {}
    skin_insts: dict[int, tuple[int, int, list[int]]] = {}
    skin_datas: dict[int, Any] = {}

    for idx, bt, bd in blocks:
        if bt == "NiNode":
            nodes[idx] = tm._parse_node(bd)
        elif bt in ("NiTriStrips", "NiTriShape"):
            geoms[idx] = tm._parse_geometry(bd)
        elif bt in ("NiTriStripsData", "NiTriShapeData"):
            geom_datas[idx] = tm._parse_geom_data(bt, bd)
        elif bt == "NiTexturingProperty":
            tex_props[idx] = tm._parse_texturing_prop(bd)
        elif bt == "NiAlphaProperty":
            alpha_props[idx] = tm._parse_alpha_property(bd)
        elif bt == "NiMaterialProperty":
            mat_props[idx] = _parse_material_diffuse(bd)
        elif bt == "NiSourceTexture":
            src_texs[idx] = tm._parse_source_texture(bd)
        elif bt in ("NiPersistentSrcTextureRendererData", "NiPixelData"):
            raw_pixel_blocks[idx] = (bt, bd)
        elif bt == "NiSkinInstance":
            skin_insts[idx] = tm._parse_skin_instance(bd)
        elif bt == "NiSkinData":
            skin_datas[idx] = tm._parse_skin_data(bd)

    kf_path = tm.find_idle_kf(nif_path.parent)
    pose = tm.parse_kf_pose(kf_path) if kf_path else {}

    world_mats: dict[int, list[float]] = {}
    idle_culled_refs: set[int] = set()
    mesh_draws: list[tuple[int, dict[str, Any], list[float], int | None, str, tuple[int, int] | None, tuple[float, float, float] | None, bool, bool, bool, str]] = []

    def resolve_props(
        props: list[int],
        cur_px: int | None,
        cur_ext: str,
        cur_ap: tuple[int, int] | None,
        cur_diff: tuple[float, float, float] | None,
        cur_has_tp: bool,
    ):
        px, ext_fn, ap, diff, has_tp = cur_px, cur_ext, cur_ap, cur_diff, cur_has_tp
        for pr in props:
            if pr in tex_props:
                has_tp = True
                if tex_props[pr] is not None:
                    st = src_texs.get(tex_props[pr])
                    if st:
                        is_ext, px_ref, fn_tag = st
                        if not is_ext and px_ref in raw_pixel_blocks:
                            px = px_ref
                        elif is_ext and fn_tag.startswith("str#"):
                            s_i = int(fn_tag[4:])
                            if 0 <= s_i < len(strings):
                                ext_fn = strings[s_i]
            if pr in alpha_props:
                ap = alpha_props[pr]
            if pr in mat_props and mat_props[pr] is not None:
                diff = mat_props[pr]
        return px, ext_fn, ap, diff, has_tp

    def walk(
        ref: int,
        parent_mat: list[float],
        cur_px: int | None,
        cur_ext: str,
        cur_ap: tuple[int, int] | None,
        cur_diff: tuple[float, float, float] | None,
        cur_has_tp: bool,
        cur_hidden: bool,
        cur_culled: bool,
    ):
        if ref in nodes:
            nd = nodes[ref]
            nm = strings[nd["name_idx"]] if 0 <= nd["name_idx"] < len(strings) else ""
            lmat = nd["mat"]
            node_culled = cur_culled
            if nm and nm in pose and tm._should_apply_kf_pose(nm, nd["trs"], pose[nm]):
                tr, rot, sc = nd["trs"]
                ptr, prot, psc = pose[nm]
                if ptr is not None:
                    if max(abs(c) for c in ptr) >= 2000.0 and max(abs(c) for c in tr) < 1500.0:
                        node_culled = True
                    tr = ptr
                if prot is not None:
                    rot = prot
                if psc is not None:
                    sc = psc
                lmat = tm._mat_from_trs(tr, rot, sc)
            wmat = tm._mat_mul(parent_mat, lmat)
            world_mats[ref] = wmat
            if node_culled:
                idle_culled_refs.add(ref)
            hid = cur_hidden or bool(nd["flags"] & 1)
            px, ext_fn, ap, diff, has_tp = resolve_props(nd["props"], cur_px, cur_ext, cur_ap, cur_diff, cur_has_tp)
            for ch in nd["children"]:
                if ch >= 0:
                    walk(ch, wmat, px, ext_fn, ap, diff, has_tp, hid, node_culled)
        elif ref in geoms:
            gm = geoms[ref]
            wmat = tm._mat_mul(parent_mat, gm["mat"])
            world_mats[ref] = wmat
            nm = strings[gm["name_idx"]] if 0 <= gm["name_idx"] < len(strings) else ""
            hid = cur_hidden or bool(gm["flags"] & 1)
            px, ext_fn, ap, diff, has_tp = resolve_props(gm["props"], cur_px, cur_ext, cur_ap, cur_diff, cur_has_tp)
            mesh_draws.append((ref, gm, wmat, px, ext_fn, ap, diff, has_tp, hid, cur_culled, nm))

    for r in roots:
        if r >= 0:
            walk(r, tm._mat_id(), None, "", None, None, False, False, False)

    has_any_skinned = any(gm["skin_ref"] in skin_insts for _, gm, *_ in mesh_draws)
    default_px = next(iter(raw_pixel_blocks.keys()), None)
    png_cache: dict[tuple[Any, bool], bytes | None] = {}

    def classify_alpha(ap: tuple[int, int] | None) -> tuple[str, float, bool]:
        if ap is None:
            return ("OPAQUE", 0.5, False)
        fl, thr = ap
        blend = bool(fl & 1)
        dst = (fl >> 5) & 0xF
        atest = bool(fl & 0x0200)
        if blend and dst == 0:
            return ("ADD", 0.0, True)
        if atest or blend:
            cutoff = max(0.18, min(0.85, thr / 255.0 if thr > 0 else 0.25))
            return ("MASK", cutoff, blend)
        return ("OPAQUE", 0.5, False)

    # First pass identifies whether any non-VFX core body mesh exists
    candidates = []
    for _g_ref, gm, wmat, px_ref, ext_fn, ap, diff, has_tp, is_hidden, is_culled_node, g_name in mesh_draws:
        if is_hidden or _is_helper_name(g_name):
            continue
        alpha_mode, alpha_cutoff, is_blended = classify_alpha(ap)
        is_skinned = gm["skin_ref"] in skin_insts
        if not is_skinned and is_culled_node:
            continue
        if has_any_skinned and not is_skinned:
            # Keep rigid attached meshes ONLY if textured (eyes, swords, sleds) and not additive VFX
            if not has_tp or alpha_mode == "ADD":
                continue
        # Drop untextured glow/alpha VFX planes so body texture never leaks onto them
        if not has_tp and (alpha_mode != "OPAQUE" or _is_vfx_shell_name(g_name)):
            continue
        gdata_peek = geom_datas.get(gm["data_ref"])
        nv_peek = len(gdata_peek["verts"]) if gdata_peek else 0
        is_vfx_card = (
            (alpha_mode == "ADD" and (_is_vfx_shell_name(g_name) or nv_peek <= 8))
            or (is_blended and _is_vfx_shell_name(g_name))
        )
        candidates.append((gm, wmat, px_ref, ext_fn, alpha_mode, alpha_cutoff, diff, has_tp, g_name, is_vfx_card))

    has_core = any(not c[9] for c in candidates)
    results: list[dict[str, Any]] = []

    for gm, wmat, px_ref, ext_fn, alpha_mode, alpha_cutoff, diff, has_tp, g_name, is_vfx_card in candidates:
        if has_core and is_vfx_card:
            continue

        is_skinned = gm["skin_ref"] in skin_insts
        gdata = geom_datas.get(gm["data_ref"])
        if not gdata or not gdata["verts"] or not gdata["tris"]:
            continue

        verts = gdata["verts"]
        normals = gdata["normals"] or [(0.0, 0.0, 1.0)] * len(verts)
        uvs = gdata["uvs"] or [(0.0, 0.0)] * len(verts)

        if is_skinned:
            sdata_ref, _sroot, bone_refs = skin_insts[gm["skin_ref"]]
            if sdata_ref in skin_datas:
                _smat, bones_info = skin_datas[sdata_ref]
                acc = [[0.0, 0.0, 0.0] for _ in range(len(verts))]
                acc_n = [[0.0, 0.0, 0.0] for _ in range(len(verts))]
                w_sum = [0.0] * len(verts)
                culled_w = 0.0
                total_w = 0.0
                for b_i, bref in enumerate(bone_refs):
                    if b_i >= len(bones_info) or bref not in world_mats:
                        continue
                    boff, weights = bones_info[b_i]
                    if bref in idle_culled_refs:
                        culled_w += sum(wt for _, wt in weights)
                    total_w += sum(wt for _, wt in weights)
                    bm = tm._mat_mul(world_mats[bref], boff)
                    for vi, wt in weights:
                        if vi < len(verts):
                            px, py, pz = tm._transform_point(bm, *verts[vi])
                            acc[vi][0] += px * wt
                            acc[vi][1] += py * wt
                            acc[vi][2] += pz * wt
                            nx, ny, nz = tm._transform_dir(bm, *normals[vi])
                            acc_n[vi][0] += nx * wt
                            acc_n[vi][1] += ny * wt
                            acc_n[vi][2] += nz * wt
                            w_sum[vi] += wt
                if total_w > 1e-6 and culled_w > total_w * 0.5:
                    continue
                xformed_pos = []
                xformed_nrm = []
                for vi in range(len(verts)):
                    if w_sum[vi] > 1e-6:
                        xformed_pos.append((acc[vi][0] / w_sum[vi], acc[vi][1] / w_sum[vi], acc[vi][2] / w_sum[vi]))
                        xformed_nrm.append((acc_n[vi][0], acc_n[vi][1], acc_n[vi][2]))
                    else:
                        xformed_pos.append(tm._transform_point(wmat, *verts[vi]))
                        xformed_nrm.append(tm._transform_dir(wmat, *normals[vi]))
            else:
                xformed_pos = [tm._transform_point(wmat, *v) for v in verts]
                xformed_nrm = [tm._transform_dir(wmat, *n) for n in normals]
        else:
            xformed_pos = [tm._transform_point(wmat, *v) for v in verts]
            xformed_nrm = [tm._transform_dir(wmat, *n) for n in normals]

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
                idx_out.extend((a, b, c))
        if not idx_out:
            continue

        png_bytes = None
        if has_tp:
            force_op = (alpha_mode == "OPAQUE")
            use_px = px_ref if px_ref in raw_pixel_blocks else (default_px if not ext_fn else None)
            if use_px is not None:
                ckey = (use_px, force_op)
                if ckey not in png_cache:
                    bt_px, bd_px = raw_pixel_blocks[use_px]
                    try:
                        png_cache[ckey] = tm._decode_pixel_block(bt_px, bd_px, force_opaque=force_op, blocks_map=blocks_map)
                    except Exception:
                        png_cache[ckey] = None
                png_bytes = png_cache[ckey]
            if png_bytes is None and ext_fn:
                ckey_e = (ext_fn.lower(), force_op)
                if ckey_e not in png_cache:
                    png_cache[ckey_e] = _load_external_tex(ext_fn, nif_path.parent, force_op)
                png_bytes = png_cache[ckey_e]

        results.append({
            "png": png_bytes,
            "alpha_mode": alpha_mode,
            "alpha_cutoff": round(alpha_cutoff, 3),
            "diffuse": diff,
            "pos": pos_out,
            "nrm": nrm_out,
            "uv": uv_out,
            "idx": idx_out,
        })

    return results


def convert_nif_to_glb(nif_path: Path, out_path: Path) -> dict[str, Any] | None:
    chunks = _extract_nif_meshes(nif_path)
    if not chunks:
        return None

    buckets: dict[tuple[Any, ...], dict[str, list]] = {}
    for ch in chunks:
        mkey = (ch["png"], ch["alpha_mode"], ch["alpha_cutoff"], ch["diffuse"] if not ch["png"] else None)
        b = buckets.setdefault(mkey, {"pos": [], "nrm": [], "uv": [], "idx": []})
        bv = len(b["pos"])
        b["pos"].extend(ch["pos"])
        b["nrm"].extend(ch["nrm"])
        b["uv"].extend(ch["uv"])
        b["idx"].extend(i + bv for i in ch["idx"])

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
        (b["pos"], b["idx"]) for b in buckets.values() if b["pos"] and b["idx"]
    )
    png_hd_cache: dict[tuple[bytes, int], bytes | None] = {}

    for m_i, ((png_bytes, alpha_mode, alpha_cutoff, diff_rgb), bucket) in enumerate(buckets.items()):
        if not bucket["pos"] or not bucket["idx"]:
            continue
        r_pos, r_nrm, r_uv, r_idx = mhd.refine_chunk_hd(
            bucket["pos"],
            bucket["nrm"],
            bucket["uv"],
            bucket["idx"],
            alpha_mode=alpha_mode,
            smooth_deg=55.0,
            subdivide=True,
            spatial_guide=global_guide,
        )
        mat_name = f"add_mat_{m_i}" if alpha_mode == "ADD" else f"mat_{m_i}"
        pbr: dict[str, Any] = {"metallicFactor": 0.02, "roughnessFactor": 0.62}
        if not png_bytes and diff_rgb is not None:
            pbr["baseColorFactor"] = [round(diff_rgb[0], 3), round(diff_rgb[1], 3), round(diff_rgb[2], 3), 1.0]
        mat_def: dict[str, Any] = {
            "name": mat_name,
            "pbrMetallicRoughness": pbr,
            "doubleSided": True,
        }
        if png_bytes:
            tmax = 512 if alpha_mode == "ADD" else 1024
            hkey = (png_bytes, tmax)
            if hkey not in png_hd_cache:
                png_hd_cache[hkey] = mhd.upscale_anime_png_hd(png_bytes, target_max=tmax)
            hd_png = png_hd_cache[hkey] or png_bytes
            bv_img = add_view(hd_png)
            img_idx = len(images)
            images.append({"bufferView": bv_img, "mimeType": "image/png"})
            tex_idx = len(textures)
            textures.append({"source": img_idx})
            mat_def["pbrMetallicRoughness"]["baseColorTexture"] = {"index": tex_idx}
            if alpha_mode == "ADD":
                mat_def["alphaMode"] = "BLEND"
            elif alpha_mode == "MASK":
                mat_def["alphaMode"] = "MASK"
                mat_def["alphaCutoff"] = alpha_cutoff
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

        acc_pos = len(accessors)
        accessors.append({"bufferView": add_view(pos_raw, 34962), "componentType": 5126, "count": n_v, "type": "VEC3", "min": mn, "max": mx})
        acc_nrm = len(accessors)
        accessors.append({"bufferView": add_view(nrm_raw, 34962), "componentType": 5126, "count": n_v, "type": "VEC3"})
        acc_uv = len(accessors)
        accessors.append({"bufferView": add_view(uv_raw, 34962), "componentType": 5126, "count": n_v, "type": "VEC2"})
        acc_idx = len(accessors)
        accessors.append({"bufferView": add_view(idx_raw, 34963), "componentType": 5125, "count": len(r_idx), "type": "SCALAR"})

        primitives.append({
            "attributes": {"POSITION": acc_pos, "NORMAL": acc_nrm, "TEXCOORD_0": acc_uv},
            "indices": acc_idx,
            "material": mat_idx,
        })

    if not primitives:
        return None

    while len(bin_buf) % 4 != 0:
        bin_buf.append(0)

    gltf: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": "dmo-thai-wiki-seal-leader-nif2glb-v1"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": nif_path.stem}],
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


def _load_leader_nif_targets() -> tuple[dict[int, int], dict[int, Path]]:
    """Map sealleader cidx -> leader_mon_id, and leader_mon_id -> NIF path."""
    sc_path = TBL_DIR / "sealcard.bin"
    sl_path = TBL_DIR / "sealleader.bin"
    mdat_path = PACK01 / "data" / "Model.dat"
    if not (sc_path.exists() and sl_path.exists() and mdat_path.exists()):
        return {}, {}

    with sl_path.open("rb") as f:
        lcnt = struct.unpack("<I", f.read(4))[0]
        leaders = {x[0]: x[1] for x in (struct.unpack("<HHH", f.read(6)) for _ in range(lcnt))}

    with sc_path.open("rb") as f:
        scnt = struct.unpack("<I", f.read(4))[0]
        srecs = [f.read(96) for _ in range(scnt)]

    b = mdat_path.read_bytes()
    model_paths: dict[int, str] = {}
    for m in re.finditer(rb"(?s)(.{4})(Data\\[^\x00]{4,200}\.(?:kfm|nif))\x00", b, re.I):
        mid = struct.unpack_from("<I", m.group(1), 0)[0]
        if 100 <= mid <= 999999 and mid not in model_paths:
            model_paths[mid] = m.group(2).decode("ascii", "replace")

    cidx_to_leader: dict[int, int] = {}
    targets: dict[int, Path] = {}

    for r in srecs:
        cidx = struct.unpack_from("<H", r, 4)[0]
        mon_id = struct.unpack_from("<I", r, 6)[0]
        lmon = leaders.get(cidx, mon_id)
        # DATS emblem seals (mon_id=31000, lmon=31000) display Starter Agumon S (31001) as Leader in-game
        eff_mon = 31001 if mon_id == 31000 else mon_id
        eff_lmon = 31001 if lmon == 31000 else lmon

        use_id = eff_lmon if (eff_lmon in model_paths or eff_lmon in LEADER_NIF_OVERRIDES) else eff_mon
        cidx_to_leader[cidx] = use_id
        if use_id in targets:
            continue

        if use_id in LEADER_NIF_OVERRIDES:
            cand = PACK01 / LEADER_NIF_OVERRIDES[use_id]
            if cand.is_file():
                targets[use_id] = cand
                continue

        kfm = model_paths.get(eff_lmon) or model_paths.get(eff_mon)
        if not kfm:
            continue
        rel = kfm.replace("\\", "/")
        nif_cand = PACK01 / (os.path.splitext(rel)[0] + ".nif")
        if nif_cand.is_file():
            targets[use_id] = nif_cand
            continue
        fdir = PACK01 / os.path.dirname(rel)
        if fdir.is_dir():
            nifs = [x for x in fdir.iterdir() if x.suffix.lower() == ".nif" and "effect" not in x.name.lower()]
            if nifs:
                targets[use_id] = nifs[0]

    return cidx_to_leader, targets


def _convert_seal_worker(task: tuple[int, str, str]) -> tuple[int, dict[str, Any] | None, str | None]:
    lid, nif_str, glb_str = task
    nif_path = Path(nif_str)
    glb_path = Path(glb_str)
    try:
        meta = convert_nif_to_glb(nif_path, glb_path)
        if meta:
            meta["v"] = 6
            meta["url"] = f"/models/seals/{lid}.glb"
            meta["nif"] = str(nif_path.relative_to(PACK01)).replace("\\", "/")
        return lid, meta, None
    except Exception as ex:
        return lid, None, str(ex)


def build_all_seal_models(force: bool = False) -> dict[str, Any]:
    """Ensure GLB models exist for all Seal Leader Digimon/NPC models and return manifest."""
    SEAL_MODEL_OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = SEAL_MODEL_OUT / "manifest.json"
    existing: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    cidx_to_leader, targets = _load_leader_nif_targets()
    if not targets and existing:
        return {"cidx_to_leader": cidx_to_leader, "models": existing}

    models: dict[str, Any] = dict(existing.get("models", existing)) if isinstance(existing, dict) else {}
    if "cidx_to_leader" in existing and "models" in existing:
        models = dict(existing["models"])

    new_cidx_map = {str(k): v for k, v in cidx_to_leader.items()}
    dirty = new_cidx_map != existing.get("cidx_to_leader")
    pending: list[tuple[int, str, str]] = []
    for lid, nif_path in sorted(targets.items()):
        s_lid = str(lid)
        glb_path = SEAL_MODEL_OUT / f"{lid}.glb"
        cached = models.get(s_lid)
        if not force and cached and glb_path.exists() and cached.get("v") == 6:
            continue
        pending.append((lid, str(nif_path), str(glb_path)))

    if pending:
        if len(pending) > 6:
            workers = min(6, os.cpu_count() or 4)
            with ProcessPoolExecutor(max_workers=workers) as ex:
                for lid, meta, err in ex.map(_convert_seal_worker, pending):
                    if meta:
                        models[str(lid)] = meta
                        dirty = True
                    elif err:
                        print(f"[WARN] Seal leader NIF convert failed {lid}: {err}")
        else:
            for task in pending:
                lid, meta, err = _convert_seal_worker(task)
                if meta:
                    models[str(lid)] = meta
                    dirty = True
                elif err:
                    print(f"[WARN] Seal leader NIF convert failed {lid}: {err}")

    if dirty or not manifest_path.exists():
        manifest_path.write_text(json.dumps({
            "cidx_to_leader": new_cidx_map,
            "models": models,
        }, indent=2), encoding="utf-8")

    return {"cidx_to_leader": cidx_to_leader, "models": models}


if __name__ == "__main__":
    res = build_all_seal_models(force=False)
    print(f"Seal Leader 3D models ready: {len(res['models'])} GLBs, cidx mappings: {len(res['cidx_to_leader'])}")
