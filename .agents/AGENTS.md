# Timberborn Modding Agent Rules

## UnityFS AssetBundle & Timbermesh Extraction Rules

When extracting 3D models (`.timbermesh`), blueprints (`*.blueprint.json`), or MonoBehaviour assets from Unity AssetBundles (e.g. `emberpelts_win`, `*.win`, `AssetBundles/*`):

1. **Do NOT rely exclusively on `UnityPy.load()`**: Unity 2022+ / Timberborn 1.1 TypeTrees throw `struct.error: iterative unpacking requires a buffer of a multiple of 32 bytes` in UnityPy.
2. **16-Byte Header Alignment Padding**: Header length is 49 bytes. If `flags & 0x200` (`BlockInfoNeedsPadding`) is set, the compressed `blocks_info` block starts at offset `(49 + 15) & ~15` = `64` (`0x40`), NOT offset 49.
3. **Decompress Data Blocks into CAB Stream First**: Never search raw `.win` files for text strings (e.g. `"Floodgate"` or `"BuildingSpec"`). Data blocks are LZ4 compressed. Decompress storage blocks first using `lz4.block.decompress()`.
4. **Timbermesh Payloads**: Located in the CAB stream immediately following asset name strings (e.g. `Floodgate.Flat.Emberpelts.Model`). Payloads are zlib-compressed streams starting with byte `0x78` (`0x78 0x01`, `0x78 0x9c`, `0x78 0xda`).
5. **Protobuf String Patching Rule**: Never perform raw byte substring replacements (e.g. `raw_bytes.replace()`) on `.timbermesh` files if string lengths differ. Protobuf uses length-delimited fields (Wire type 2); changing string lengths without re-calculating varint field length prefixes corrupts the message layout (`ProtoException: A length-based message was terminated via end-group`). Always parse the Protobuf tree, update values, and re-serialize with recalculated varint lengths.
6. **Blueprint JSON Payloads**: Text JSON strings in the CAB stream matching `\{\s*"(?:BuildingSpec|BlockObjectSpec|FactionSpec|TemplateCollectionSpec)"`.

Full guide & verified Python code: [unityfs_assetbundle_timbermesh_extraction_guide.md](file:///C:/Users/souvi/.gemini/antigravity-ide/brain/91e4fe7c-87bc-4e68-89bf-9b5b1b58293f/unityfs_assetbundle_timbermesh_extraction_guide.md)
