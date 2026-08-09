# Timberborn AI Wiki & AssetBundle Extraction Toolkit

This directory contains the verified, comprehensive documentation, C# modding guidelines, troubleshooting guides, and Python utilities for Timberborn mod development.

---

## Files in this Directory

| File | Description |
|---|---|
| [`General_CSharp_Modding_and_Pitfalls_Wiki.md`](file:///D:/Timberborn%20Mod%20development/timberborn-ai-wiki/General_CSharp_Modding_and_Pitfalls_Wiki.md) | **Generalized C# Mod Creation & Technical Pitfalls Wiki**. Documents Bindito dependency injection, singleton lifecycles, UI Toolkit toggle button styling, ModSettings owner duplication fixes (`CleanupDuplicateRegistrations`), `ModId` matching, `SelectableObject` component hierarchy traversal, and step-by-step debugging workflows. |
| [`Souvy_Mods_Architecture_and_Troubleshooting_Wiki.md`](file:///D:/Timberborn%20Mod%20development/timberborn-ai-wiki/Souvy_Mods_Architecture_and_Troubleshooting_Wiki.md) | **Souvy Mods Architecture & Troubleshooting Guide**. Documents the architecture, files, and specific troubleshooting notes for `Souvy-ShortCommute`, `Souvy-Unstuckify`, `Souvy-ZiplineCustomizer`, `Souvy-FlatFloodgates`, `Souvy-BuildersBliss`, `Souvy-Emberpelts`, and `Souvy-Whitepaws`. |
| [`Whitepaws_Automation_Rules_Wiki.md`](file:///D:/Timberborn%20Mod%20development/timberborn-ai-wiki/Whitepaws_Automation_Rules_Wiki.md) | **Whitepaws Automation Rules Technical Guide**. Details Lisp signal expressions (`District.ResourceStock.*`, `District.ResourceCapacity.*`), threshold mechanics, localized name resolution, and complete recipe coverage across mod and base game factions. |
| [`AssetBundle_Timbermesh_Blueprint_Extraction_Wiki.md`](file:///D:/Timberborn%20Mod%20development/timberborn-ai-wiki/AssetBundle_Timbermesh_Blueprint_Extraction_Wiki.md) | Comprehensive Wiki detailing root causes, AssetRipper failures, UnityPy monkey-patching, manifest directory mapping, timbermesh payload extraction, and stock game blueprints. |
| [`Material_Patcher_And_Custom_Specifications_Wiki.md`](file:///D:/Timberborn%20Mod%20development/timberborn-ai-wiki/Material_Patcher_And_Custom_Specifications_Wiki.md) | Complete Technical Guide & Specification Reference for Timberborn's Material Patcher (`BuildingPrefabMaterialPatchSpec`, `MaterialPatchSpec`, `ShaderPatchSpec`, `WaterShaderPatchSpec`, `LiquidGoodMaterialPatchSpec`), Character Customizer, and DLL extensions. |
| [`timberborn_bundle_extractor.py`](file:///D:/Timberborn%20Mod%20development/timberborn-ai-wiki/timberborn_bundle_extractor.py) | **Verified Production Extractor Utility**. Unpacks AssetBundles, bypasses Unity 6 / Timberborn 1.1 TypeTree errors, extracts blueprints and timbermeshes, and auto-builds the exact `.manifest` folder hierarchy. |
| [`pure_python_unityfs_extractor.py`](file:///D:/Timberborn%20Mod%20development/timberborn-ai-wiki/pure_python_unityfs_extractor.py) | Low-level binary header & LZ4 storage block reader for raw CAB stream inspection. |

---

## Key Modding Patterns & Guidelines

### 1. Bindito Container Wiring
* Always ensure singletons registered under `[Context("Game")]` or `[Context("MainMenu")]` have all their constructor dependencies bound in the same context container.

### 2. ModSettings Duplicate Owner Prevention
* When creating a custom `ModSettingsOwner`, include `CleanupDuplicateRegistrations` inside the constructor to prevent `ModSettingsOwnerRegistry` duplicate key crashes.

### 3. UI Toolkit HUD Buttons
* Load standard buttons via `_visualElementLoader.LoadVisualElement("Common/SquareToggle")`.
* Use `Position.Absolute` overlays with `PickingMode.Ignore` to render custom PNG icons without breaking click handlers or missing-texture question mark fallback boxes.

### 4. Timberborn 1.1 Component Traversal
* `SelectableObject` is attached to child sub-colliders in Timberborn 1.1. Always check `selectable.GetComponent<T>() ?? selectable.GameObject.GetComponentInParent<T>() ?? selectable.GameObject.GetComponentInChildren<T>()`.
