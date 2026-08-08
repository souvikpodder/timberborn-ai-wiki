#!/usr/bin/env python3
"""
Timberborn Modern AssetBundle Extractor (Timbermesh & Blueprints)
------------------------------------------------------------------
Extracts both:
  1. Blueprint JSON files (rebuilding full manifest directory hierarchy)
  2. Timbermesh 3D models (.timbermesh files)
  3. Raw CAB streams

Bypasses Unity 6 / Unity 2022+ TypeTree deserialization errors in UnityPy.

Usage:
    python timberborn_bundle_extractor.py <bundle_path> [--manifest <manifest_path>] [--output <output_dir>]

Example:
    python timberborn_bundle_extractor.py "c:\Program Files (x86)\Steam\steamapps\workshop\content\1062090\3346318229\version-1.1\AssetBundles\emberpelts_win"
"""

import sys
import os
import re
import json
import zlib
import argparse

try:
    import UnityPy
    from UnityPy.streams import EndianBinaryReader
    from UnityPy.files import BundleFile
    from UnityPy.helpers import ImportHelper
except ImportError:
    print("Error: UnityPy library is required. Install it using: pip install UnityPy")
    sys.exit(1)

# Monkey-patch UnityPy parse_file to bypass SerializedFile TypeTree unpacking errors on Unity 6 / Timberborn 1.1
old_parse_file = ImportHelper.parse_file

def raw_parse_file(reader, parent, name="", typ=None, is_dependency=False):
    try:
        return old_parse_file(reader, parent, name, typ, is_dependency)
    except Exception:
        reader.Position = 0
        raw_bytes = reader.read()
        return type('RawNode', (), {
            'raw_bytes': raw_bytes,
            'name': name,
            'bytes': raw_bytes,
            'byte_size': len(raw_bytes)
        })()

ImportHelper.parse_file = raw_parse_file

def parse_manifest(manifest_path):
    """Parses Unity manifest file to build asset filename -> relative path mapping."""
    if not manifest_path or not os.path.exists(manifest_path):
        return {}
    
    path_mapping = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        in_assets = False
        for line in f:
            line_str = line.strip()
            if line_str == "Assets:":
                in_assets = True
                continue
            if in_assets and line_str.startswith("- "):
                asset_path = line_str[2:]
                filename = os.path.basename(asset_path).lower()
                rel_path = asset_path.split("AssetBundles/", 1)[1] if "AssetBundles/" in asset_path else asset_path
                path_mapping[filename] = rel_path
                if filename.endswith('.json'):
                    path_mapping[filename[:-5]] = rel_path
                if filename.endswith('.timbermesh'):
                    path_mapping[filename[:-11]] = rel_path
    return path_mapping

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

def extract_blueprints_from_cab(cab_bytes):
    """Scans raw CAB binary stream for blueprint JSON TextAssets."""
    json_starts = [m.start() for m in re.finditer(rb'\{\r?\n\s*"(?:BuildingSpec|RecipeSpec|GoodSpec|NeedSpec|FactionSpec|SubfactionSpec|PlantSpec|BlockSpec|BlockObjectSpec|TemplateSpec|TemplateName|Id)"', cab_bytes)]
    
    blueprints = {}
    for start in json_starts:
        if start >= 4:
            s_len = int.from_bytes(cab_bytes[start-4:start], 'little')
            if 10 <= s_len <= 2000000 and start + s_len <= len(cab_bytes):
                candidate_bytes = cab_bytes[start:start+s_len]
                try:
                    candidate_text = candidate_bytes.decode('utf-8')
                    parsed_json = json.loads(candidate_text)
                    prec_snippet = cab_bytes[max(0, start-300):start]
                    
                    filename = get_blueprint_name(parsed_json, prec_snippet)
                    if filename:
                        blueprints[filename] = parsed_json
                except Exception:
                    pass
    return blueprints

def extract_timbermeshes_from_cab(cab_bytes):
    """Scans raw CAB binary stream for timbermesh 3D model zlib payloads."""
    timbermeshes = {}
    pattern = re.compile(rb'([A-Za-z0-9_.]*(?:Flat|Floodgate|Lodge|House|Shaft|Power|Tunnel|Platform|Ladder|Battery)[A-Za-z0-9_.]*\.Model)')
    
    for match in pattern.finditer(cab_bytes):
        name = match.group(1).decode("ascii", errors="ignore")
        if name in timbermeshes:
            continue
        pos_idx = match.start()
        
        # Scan next 500 bytes for zlib compression header (0x78)
        for z_pos in range(pos_idx, min(len(cab_bytes) - 2, pos_idx + 500)):
            if cab_bytes[z_pos] == 0x78 and cab_bytes[z_pos+1] in (0x01, 0x9c, 0xda):
                try:
                    decomp_tm = zlib.decompressobj().decompress(cab_bytes[z_pos : z_pos + 3000000])
                    if len(decomp_tm) > 3000:
                        timbermeshes[f"{name}.timbermesh"] = zlib.compress(decomp_tm)
                        break
                except Exception:
                    pass
    return timbermeshes

def process_bundle(bundle_path, manifest_path=None, output_dir=None):
    if not os.path.exists(bundle_path):
        print(f"Error: Bundle file not found at '{bundle_path}'")
        return
    
    if not manifest_path:
        possible_manifest = bundle_path + ".manifest"
        if os.path.exists(possible_manifest):
            manifest_path = possible_manifest
            print(f"Auto-detected manifest: {manifest_path}")

    if not output_dir:
        bundle_dir = os.path.dirname(bundle_path)
        bundle_name = os.path.basename(bundle_path)
        output_dir = os.path.join(bundle_dir, f"{bundle_name}_Extracted")

    print(f"Decompressing bundle: {bundle_path}")
    with open(bundle_path, "rb") as f:
        reader = EndianBinaryReader(f)
        bundle = BundleFile(reader, None)
        
        all_blueprints = {}
        all_timbermeshes = {}
        
        for name, node_file in bundle.files.items():
            if hasattr(node_file, 'raw_bytes') and node_file.raw_bytes:
                cab_bytes = node_file.raw_bytes
            elif hasattr(node_file, 'reader'):
                node_file.reader.Position = 0
                cab_bytes = node_file.reader.read()
            else:
                continue
            
            print(f"Scanning node '{name}' ({len(cab_bytes)} bytes)...")
            bp_extracted = extract_blueprints_from_cab(cab_bytes)
            tm_extracted = extract_timbermeshes_from_cab(cab_bytes)
            
            all_blueprints.update(bp_extracted)
            all_timbermeshes.update(tm_extracted)

    print(f"\nExtracted {len(all_blueprints)} unique blueprints and {len(all_timbermeshes)} timbermesh models!")
    
    path_mapping = parse_manifest(manifest_path)
    
    raw_bp_out = os.path.join(output_dir, "Blueprints")
    raw_tm_out = os.path.join(output_dir, "Timbermeshes")
    struct_out = os.path.join(output_dir, "Structured")
    
    os.makedirs(raw_bp_out, exist_ok=True)
    os.makedirs(raw_tm_out, exist_ok=True)
    os.makedirs(struct_out, exist_ok=True)

    placed_bp = 0
    for filename, json_obj in all_blueprints.items():
        raw_file = os.path.join(raw_bp_out, filename)
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(json_obj, f, indent=2)
            
        f_lower = filename.lower()
        target_rel_path = path_mapping.get(f_lower) or path_mapping.get(f_lower[:-5] if f_lower.endswith('.json') else f_lower)
        
        if not target_rel_path:
            for k, v in path_mapping.items():
                if k == f_lower or f_lower.startswith(k) or k.startswith(f_lower[:-5] if f_lower.endswith('.json') else f_lower):
                    target_rel_path = v
                    break
        
        if target_rel_path:
            dst_file = os.path.join(struct_out, target_rel_path)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            with open(dst_file, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, indent=2)
            placed_bp += 1
        else:
            dst_file = os.path.join(struct_out, "Resources", "Uncategorized", filename)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            with open(dst_file, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, indent=2)

    placed_tm = 0
    for filename, tm_bytes in all_timbermeshes.items():
        raw_file = os.path.join(raw_tm_out, filename)
        with open(raw_file, "wb") as f:
            f.write(tm_bytes)
            
        f_lower = filename.lower()
        target_rel_path = path_mapping.get(f_lower) or path_mapping.get(f_lower[:-11] if f_lower.endswith('.timbermesh') else f_lower)
        if target_rel_path:
            dst_file = os.path.join(struct_out, target_rel_path)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            with open(dst_file, "wb") as f:
                f.write(tm_bytes)
            placed_tm += 1
        else:
            dst_file = os.path.join(struct_out, "Resources", "Models", filename)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            with open(dst_file, "wb") as f:
                f.write(tm_bytes)

    print(f"\nExtraction complete!")
    print(f"- Blueprints: {raw_bp_out}")
    print(f"- Timbermeshes: {raw_tm_out}")
    print(f"- Structured Output: {struct_out} ({placed_bp}/{len(all_blueprints)} blueprints & {placed_tm}/{len(all_timbermeshes)} timbermeshes mapped)")

def main():
    parser = argparse.ArgumentParser(description="Extract Timberborn Unity 6 AssetBundle Blueprints & Timbermeshes")
    parser.add_argument("bundle_path", help="Path to Unity AssetBundle file (e.g. emberpelts_win)")
    parser.add_argument("--manifest", help="Path to .manifest file (optional)")
    parser.add_argument("--output", help="Output directory path (optional)")
    
    args = parser.parse_args()
    process_bundle(args.bundle_path, args.manifest, args.output)

if __name__ == "__main__":
    main()
