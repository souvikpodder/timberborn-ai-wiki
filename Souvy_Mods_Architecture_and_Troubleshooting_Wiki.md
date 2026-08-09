# Souvy Mods Architecture & Troubleshooting Wiki

This wiki documents the detailed architecture, component design, settings integration, and troubleshooting notes for custom Timberborn mods created by **Souvy**:

1. **Souvy-ShortCommute**
2. **Souvy-Unstuckify**
3. **Souvy-ZiplineCustomizer**
4. **Souvy-FlatFloodgates**
5. **Souvy-BuildersBliss**
6. **Souvy-Emberpelts**
7. **Souvy-Whitepaws**

---

## 1. Souvy-ShortCommute

### 1.1 Overview & Architecture
`Souvy-ShortCommute` optimizes beaver home assignments so that employed adult beavers live in dwellings as close to their workplace as possible by road distance, without day-start stalls or frame-rate drops.

#### Core Components:
* **`CommuteOptimizer`**: Re-evaluates worker home assignments on day start (`DaytimeStartEvent`) and per tick under a strict exploration budget (`MaxFillsPerTick = 2`).
* **`DwellingRowCache`**: Caches road distances from dwellings to all workplaces in the district to keep per-tick evaluation costs flat.
* **`CommuteCost`**: Decorator component attached to `Worker` storing settled home-to-workplace road distance.
* **`CommuteOverlayToggle`**: Top-right HUD toggle button using `Common/SquareToggle` and `UI/commute_analysis_icon.png`.
* **`CommuteOverlayRenderer`**: Drives whole-map heatmap coloring (Green ≤20, Yellow 20–40, Orange 40–60, Red >60 tiles) and selection line rendering.
* **`CommuteOverlayPatcher`**: Harmony patcher that suppresses vanilla nav/path range meshes while the commute overlay is active.
* **`CommuteOverlaySettings`**: ModSettings integration for toggling path-range mesh suppression.

#### Key Files:
* `c:\Users\souvi\Documents\Timberborn\Mods\Souvy-ShortCommute\version-1.1.0\Scripts\Overlay\CommuteOverlayToggle.cs`
* `c:\Users\souvi\Documents\Timberborn\Mods\Souvy-ShortCommute\version-1.1.0\Scripts\Overlay\CommuteOverlayRenderer.cs`
* `c:\Users\souvi\Documents\Timberborn\Mods\Souvy-ShortCommute\version-1.1.0\UI\commute_analysis_icon.png`

---

## 2. Souvy-Unstuckify

### 2.1 Overview & Architecture
`Souvy-Unstuckify` automatically detects stranded or stuck beavers (e.g. beavers stuck on isolated terrain, flooded areas, or navigation deadlocks) and safely unstucks them.

#### Core Components:
* **`UnstuckifyTickableSingleton`**: Monitored tickable singleton checking beaver navigation state per tick.
* **`StuckBeaverDetector`**: Checks beaver path validity and stranded flags.
* **`UnstuckifySettingsOwner`**: Handles ModSettings integration (`Souvy.Unstuckify.Setting.Label`). Includes `CleanupDuplicateRegistrations` to prevent Bindito duplicate owner crashes.

#### Key Files:
* `c:\Users\souvi\Documents\Timberborn\Mods\Souvy-Unstuckify\version-1.1.0\Scripts\SettingsSystem\UnstuckifySettingsOwner.cs`
* `c:\Users\souvi\Documents\Timberborn\Mods\Souvy-Unstuckify\version-1.1.0\Scripts\UnstuckifyTickableSingleton.cs`

---

## 3. Souvy-ZiplineCustomizer

### 3.1 Overview & Architecture
`Souvy-ZiplineCustomizer` provides custom configuration settings for zipline towers, balloon terminals, and relays (range, speed, energy consumption, and tower connection limits).

#### Core Components:
* **`ZiplineCustomizerSettingsOwner`**: ModSettings owner for zipline parameters.
* **`ZiplinePatcher`**: Harmony patches overriding zipline connection distance and travel speed specs.

#### Key Files:
* `c:\Users\souvi\Documents\Timberborn\Mods\Souvy-ZiplineCustomizer\version-1.1.0\ZiplineCustomizer.dll`

---

## 4. Souvy-FlatFloodgates

### 4.1 Overview & Architecture
Provides flat / compact floodgate building specifications and 3D models for water control networks.

---

## 5. Souvy-BuildersBliss & Faction Mods

### 5.1 Faction Specs & Custom Assets
* **Souvy-Emberpelts**: Custom Emberpelts faction specs, 3D `.timbermesh` models, and building specifications.
* **Souvy-Whitepaws**: Custom Whitepaws faction specs, upgraded zipline towers, and building specifications.
