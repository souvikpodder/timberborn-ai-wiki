#!/usr/bin/env python3
"""
Pure Python UnityFS AssetBundle Extractor
----------------------------------------
Extracts raw CAB streams, .timbermesh 3D models, and blueprint JSON files directly
from UnityFS AssetBundle files without relying on UnityPy or AssetRipper.

Handles Unity 2020+ / 2022+ / Unity 6 16-byte header alignment padding (flags & 0x200).

Usage:
    python pure_python_unityfs_extractor.py <bundle_path> [output_dir]

Example:
    python pure_python_unityfs_extractor.py "c:\Program Files (x86)\Steam\steamapps\workshop\content\1062090\3346318229\version-1.1\AssetBundles\emberpelts_win"
"""

import sys
import os
import struct
import zlib
import re
import json

try:
    import lz4.block
except ImportError:
    print("Error: lz4 library is required. Install it using: pip install lz4")
    sys.exit(1)

def get_blueprint_name(parsed_json, fallback_binary_snippet=b""):
    """Extracts the true blueprint template name from parsed JSON or binary snippet."""
    name = None
    if isinstance(parsed_json, dict):
        if "TemplateSpec" in parsed_json and isinstance(parsed_json["TemplateSpec"], dict):
            name = parsed_json["TemplateSpec"].get("TemplateName")
        if not name:
            for spec in ["BuildingSpec", "RecipeSpec", "GoodSpec", "NeedSpec", "FactionSpec", "SubfactionSpec", "PlantSpec", "BlockSpec", "BlockObjectSpec"]:
                if spec in parsed_json and isinstance(parsed_json[spec], dict):
                    name = parsed_json[spec].get("Id") or parsed_json[spec].get("TemplateName")
                    break
        if not name:
            name = parsed_json.get("Id") or parsed_json.get("TemplateName") or parsed_json.get("Name")
    
    if not name and fallback_binary_snippet:
        matches = re.findall(rb'([A-Za-z0-9_\-\.#\+]+(?:\.Emberpelts|\.blueprint|\.json))', fallback_binary_snippet)
        if matches:
            name = matches[-1].decode('ascii', errors='ignore')

    if name:
        clean_name = re.sub(r'\.blueprint[a-zA-Z0-9_]*$', '', name)
        if not clean_name.endswith('.blueprint.json') and not clean_name.endswith('.json'):
            filename = f"{clean_name}.blueprint.json" if not clean_name.endswith('.blueprint') else f"{clean_name}.json"
        else:
            filename = clean_name
        return filename
    return None

def extract_bundle(bundle_path: str, output_dir: str = None):
    if not os.path.exists(bundle_path):
        print(f"Error: Bundle file not found at '{bundle_path}'")
        return

    if not output_dir:
        bundle_dir = os.path.dirname(bundle_path)
        bundle_name = os.path.basename(bundle_path)
        output_dir = os.path.join(bundle_dir, f"{bundle_name}_PureExtract")

    os.makedirs(output_dir, exist_ok=True)
    print(f"=== Pure Python UnityFS Extractor ===")
    print(f"Target bundle: {bundle_path}")

    with open(bundle_path, "rb") as f:
        raw = f.read()

    # 1. Parse Header
    pos = 0
    null_idx = raw.index(b"\x00", pos)
    sig = raw[pos:null_idx].decode("ascii"); pos = null_idx + 1

    if sig != "UnityFS":
        print(f"Error: Unsupported header signature '{sig}'. Expected 'UnityFS'.")
        return

    ver = struct.unpack(">I", raw[pos:pos+4])[0]; pos += 4
    null_idx = raw.index(b"\x00", pos)
    u_ver = raw[pos:null_idx].decode("ascii"); pos = null_idx + 1
    null_idx = raw.index(b"\x00", pos)
    u_rev = raw[pos:null_idx].decode("ascii"); pos = null_idx + 1

    file_size, c_info_size, u_info_size, flags = struct.unpack(">qIII", raw[pos:pos+20])
    pos += 20

    header_unpadded = pos
    # Crucial 16-byte alignment check for flags & 0x200
    blocks_info_offset = (header_unpadded + 15) & ~15 if (flags & 0x200) else header_unpadded

    print(f"Header: Signature={sig}, UnityVer={u_ver}, Revision={u_rev}, Flags=0x{flags:x}")
    print(f"BlocksInfo Offset: {blocks_info_offset} (Compressed Size={c_info_size}, Uncompressed Size={u_info_size})")

    # 2. Decompress Blocks Directory
    blocks_info_raw = raw[blocks_info_offset : blocks_info_offset + c_info_size]
    blocks_info = lz4.block.decompress(blocks_info_raw, uncompressed_size=u_info_size)

    b_pos = 16 # Skip GUID
    num_blocks = struct.unpack(">I", blocks_info[b_pos:b_pos+4])[0]; b_pos += 4
    blocks = []
    for _ in range(num_blocks):
        u_sz = struct.unpack(">I", blocks_info[b_pos:b_pos+4])[0]
        c_sz = struct.unpack(">I", blocks_info[b_pos+4:b_pos+8])[0]
        b_fl = struct.unpack(">H", blocks_info[b_pos+8:b_pos+10])[0]
        b_pos += 10
        blocks.append((u_sz, c_sz, b_fl))

    num_nodes = struct.unpack(">I", blocks_info[b_pos:b_pos+4])[0]; b_pos += 4
    nodes = []
    for _ in range(num_nodes):
        n_off = struct.unpack(">Q", blocks_info[b_pos:b_pos+8])[0]; b_pos += 8
        n_sz = struct.unpack(">Q", blocks_info[b_pos:b_pos+8])[0]; b_pos += 8
        n_st = struct.unpack(">I", blocks_info[b_pos:b_pos+4])[0]; b_pos += 4
        null_p = blocks_info.index(b"\x00", b_pos)
        n_name = blocks_info[b_pos:null_p].decode("utf-8"); b_pos = null_p + 1
        nodes.append((n_off, n_sz, n_st, n_name))

    print(f"Storage Blocks: {len(blocks)}, Directory Nodes: {len(nodes)}")

    # 3. Decompress Data Blocks into Unified Stream
    data_unpadded = blocks_info_offset + c_info_size
    data_start_offset = (data_unpadded + 15) & ~15 if (flags & 0x200) else data_unpadded

    decompressed_cab = bytearray()
    curr = data_start_offset
    for u_sz, c_sz, b_fl in blocks:
        chunk = raw[curr : curr + c_sz]
        curr += c_sz
        comp_type = b_fl & 0x3F
        if comp_type in (2, 3):
            decompressed_cab.extend(lz4.block.decompress(chunk, uncompressed_size=u_sz))
        else:
            decompressed_cab.extend(chunk)

    cab_stream = bytes(decompressed_cab)
    print(f"Decompressed CAB stream size: {len(cab_stream)} bytes ({len(cab_stream)/(1024*1024):.2f} MB)")

    # Save CAB Nodes
    cab_dir = os.path.join(output_dir, "CAB_Nodes")
    os.makedirs(cab_dir, exist_ok=True)
    for n_off, n_sz, n_st, n_name in nodes:
        node_bytes = cab_stream[n_off : n_off + n_sz]
        out_node_path = os.path.join(cab_dir, n_name.replace("/", "_"))
        with open(out_node_path, "wb") as f_node:
            f_node.write(node_bytes)
        print(f"Saved CAB Node: {out_node_path}")

    # Node 0 contains serialized assets
    node0_bytes = cab_stream[nodes[0][0] : nodes[0][0] + nodes[0][1]]

    # 4. Extract Timbermesh 3D Models
    tm_dir = os.path.join(output_dir, "Timbermeshes")
    os.makedirs(tm_dir, exist_ok=True)

    pattern = re.compile(rb'([A-Za-z0-9_.]*(?:Flat|Floodgate|Lodge|House|Shaft|Power|Tunnel|Platform|Ladder|Battery)[A-Za-z0-9_.]*\.Model)')
    extracted_tm = set()

    for match in pattern.finditer(node0_bytes):
        name = match.group(1).decode("ascii", errors="ignore")
        if name in extracted_tm:
            continue
        pos_idx = match.start()
        
        for z_pos in range(pos_idx, min(len(node0_bytes) - 2, pos_idx + 500)):
            if node0_bytes[z_pos] == 0x78 and node0_bytes[z_pos+1] in (0x01, 0x9c, 0xda):
                try:
                    decomp_tm = zlib.decompressobj().decompress(node0_bytes[z_pos : z_pos + 3000000])
                    if len(decomp_tm) > 3000:
                        extracted_tm.add(name)
                        tm_path = os.path.join(tm_dir, f"{name}.timbermesh")
                        with open(tm_path, "wb") as f_tm:
                            f_tm.write(zlib.compress(decomp_tm))
                        print(f"Extracted Timbermesh: {name}.timbermesh ({len(decomp_tm)} bytes decompressed)")
                        break
                except Exception:
                    pass

    # 5. Extract Blueprint JSON Assets
    bp_dir = os.path.join(output_dir, "Blueprints")
    os.makedirs(bp_dir, exist_ok=True)

    json_starts = [m.start() for m in re.finditer(rb'\{\r?\n\s*"(?:BuildingSpec|RecipeSpec|GoodSpec|NeedSpec|FactionSpec|SubfactionSpec|PlantSpec|BlockSpec|BlockObjectSpec|TemplateSpec|TemplateName|Id)"', node0_bytes)]
    extracted_bps = {}

    for start in json_starts:
        if start >= 4:
            s_len = int.from_bytes(node0_bytes[start-4:start], 'little')
            if 10 <= s_len <= 2000000 and start + s_len <= len(node0_bytes):
                candidate_bytes = node0_bytes[start:start+s_len]
                try:
                    candidate_text = candidate_bytes.decode('utf-8')
                    parsed_json = json.loads(candidate_text)
                    prec_snippet = node0_bytes[max(0, start-300):start]
                    
                    filename = get_blueprint_name(parsed_json, prec_snippet)
                    if filename and filename not in extracted_bps:
                        extracted_bps[filename] = parsed_json
                        bp_path = os.path.join(bp_dir, filename)
                        with open(bp_path, "w", encoding="utf-8") as f_bp:
                            json.dump(parsed_json, f_bp, indent=2)
                        print(f"Extracted Blueprint: {filename}")
                except Exception:
                    pass

    print(f"\nPure Extraction Complete! Saved {len(extracted_tm)} Timbermeshes and {len(extracted_bps)} Blueprints to '{output_dir}'.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python pure_python_unityfs_extractor.py <bundle_path> [output_dir]")
        sys.exit(1)
    
    bundle_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    extract_bundle(bundle_path, output_dir)

if __name__ == "__main__":
    main()
