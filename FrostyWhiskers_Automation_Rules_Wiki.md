# FrostyWhiskers Automation Rules Technical Guide & Specification

This documentation details the architecture, signal logic, thresholds, localization resolution, and recipe generation engine for **FrostyWhiskers Automation Rules** in Timberborn.

---

## 1. Overview & Architecture

The FrostyWhiskers Automation Rule system dynamically manages faction workplaces, primary extraction machines, primitive tent craftings, start bunker salvage, advanced robotic assembly, and power generation. By evaluating district-wide inventory stock and storage capacity signals in real-time, rules automatically assign/unassign workforce or toggle continuous machine operations.

The automation rule file is written in Timberborn Automation Lisp expression syntax:
- **Rule File Path**: `C:\Users\souvi\Documents\Timberborn\Mods\Automation Rule\FrostyWhiskers automation rule.lisp`
- **Generator Utility**: `C:\Users\souvi\Documents\Timberborn\Mods\Automation Rule\generate_frostywhiskers_rules.py`

---

## 2. Threshold Mechanics & Signal Logic

All standard production rules evaluate two key signal types per district:
- Stock Quantity Signal: `(sig District.ResourceStock.<GoodId>)`
- Maximum Storage Capacity Signal: `(sig District.ResourceCapacity.<GoodId>)`

### Threshold Values

| Rule Type | Signal Threshold | Value Multiplier | Action Triggered |
|---|---|---|---|
| **Input Deficiency** | Input Stock `< 10%` Capacity | `(mul 10 (sig District.ResourceCapacity.<InputId>))` | `Workplace.RemoveWorkers` |
| **Output Fullness** | Output Stock `>= 90%` Capacity | `(mul 90 (sig District.ResourceCapacity.<OutputId>))` | `Workplace.RemoveWorkers` |
| **Work Resumption** | All Inputs `>= 10%` AND All Outputs `< 90%` | Composite `(and ...)` | `Workplace.SetWorkers {% (getvalue Workplace.MaxWorkers) %}` |
| **Petroleum Generator** | Petroleum Stock `< 10%` Capacity | `(mul 10 (sig District.ResourceCapacity.Water))` | `Pausable.Pause` |
| **Ground Heating Rail** | Fish Oil Stock `< 10%` Capacity | `(mul 10 (sig District.ResourceCapacity.Fishoil))` | `Pausable.Pause` |
| **Repair Station** | Nanobot Stock `< 10%` Capacity | `(mul 10 (sig District.ResourceCapacity.Nanobot))` | `Pausable.Pause` |
| **Bot Cap Management** | District Bots `>= 8000` | `(ge (sig District.Bots) 8000)` | `Workplace.RemoveWorkers` |

---

## 3. Expression Syntax Standard

### Removal Rule Pattern (OR Logic)
If **any** fuel or ingredient input falls below 10% capacity, **OR** **any** product output reaches 90% capacity, workers are unassigned:

```lisp
;;;;<Recipe Title> (<Input 1> + <Input 2> -> <Output 1>) (Fuel: <Fuel Name>)
condition:(or (lt (sig District.ResourceStock.<FuelId>) (mul 10 (sig District.ResourceCapacity.<FuelId>))) (or (lt (sig District.ResourceStock.<Input1Id>) (mul 10 (sig District.ResourceCapacity.<Input1Id>))) (ge (sig District.ResourceStock.<Output1Id>) (mul 90 (sig District.ResourceCapacity.<Output1Id>)))))
action:(act Workplace.RemoveWorkers)
```

### Assignment Rule Pattern (AND Logic)
When **all** required fuel and ingredients are at or above 10% capacity, **AND** **all** product output storage spaces are below 90% capacity, workers are assigned to maximum capacity:

```lisp
condition:(and (ge (sig District.ResourceStock.<FuelId>) (mul 10 (sig District.ResourceCapacity.<FuelId>))) (and (ge (sig District.ResourceStock.<Input1Id>) (mul 10 (sig District.ResourceCapacity.<Input1Id>))) (lt (sig District.ResourceStock.<Output1Id>) (mul 90 (sig District.ResourceCapacity.<Output1Id>)))))
action:(act Workplace.SetWorkers {% (getvalue Workplace.MaxWorkers) %})
```

---

## 4. Faction Localization & Lore Resolution

The FrostyWhiskers faction alters several standard good representations and introduces specialized arctic resources. Signal evaluations retain internal engine IDs while rule comment titles display clean English names parsed from `enUS.csv`:

### Internal ID to Lore Name Mapping

| Engine Resource ID | FrostyWhiskers Lore Name | Notes |
|---|---|---|
| `Water` | **Petroleum** | Extracted via Oil Drills, burned as fuel in primitive ironworks & petroleum lamps |
| `MetalBlock` | **Iron Bar** | Produced via Primitive Ironworks or Fabricator |
| `Berries` | **Explosives** / Fakeplosives | Synthesized from Fish & Petroleum in Chem Lab |
| `Fishoil` | **Fish Oil** | Extracted from Fish or synthesized; fuels Ground Heating Rails |
| `Salt` | **Mountain Salt** | Mined/crushed from Rock + Ice Block in Chemistry Tent |
| `LargeIceShard` | **Large Ice Shard** | Crushed in Gnawing Tent / Fabricator into Ice Blocks & Snow |
| `CopperBar` / `CopperNuggets` | **Copper Bar** / **Copper Nuggets** | Excavated and smelted for advanced electronics |
| `GoldBar` / `GoldDust` | **Gold Bar** / **Gold Dust** | Smelted and printed for Nanobots & Bot Assembly |
| `NuclearFuel` / `NuclearWaste` | **Nuclear Fuel** / **Nuclear Waste** | Boiled with Badwater & Sulfuric Acid for Bot Power |

---

## 5. Recipe Scope & Coverage

The generator scans all FrostyWhiskers mod assets, override extensions, and base game production recipes (108 unique rules + continuous machine & utility rules):

```text
FrostyWhiskers Automation Rule Scope:
├── Primary Extraction & Mining (14 Rules)
│   ├── Dirt Excavator (All, Copper Nuggets, Gold Dust, Ice, Rock, Scrap Metal)
│   ├── Iceberg Quarry & Steam Vent (Ice Blocks, Sulfuric Acid)
│   ├── Oil Drills (Petroleum Extraction)
│   └── Excavation Mines & Badwater Pumps
├── Start Bunker Salvage & Cannibalization (10 Rules)
│   ├── Bunker Cannibalization & Embryo Destocking
│   └── Early Salvage (Copper Bars, Iron Bars, Nanobots, Solar Cells, Carbon Fiber, etc.)
├── Primitive Tents (11 Rules)
│   ├── Chemistry Tent (Mountain Salt, Carbon Fiber, Plastic Panes)
│   ├── Cooking Tent (Sad Soup, Grilled Bug, Fish Oil, Fake Fish Oil)
│   ├── Gnawing Tent (Crush Ice Shards, Gnaw Planks)
│   └── Primitive Ironworks (Copper Bar, Gold Bar, Iron Bar, Scrap Recycle)
├── High-Tech & Robotic Facilities (18 Rules)
│   ├── Chemical Lab & Explosives Factory
│   ├── Carbon Fiber Mill & Plexiglass Press
│   ├── Badwater Boiler & Nano Machine Printer
│   └── Frosty Whiskers Bot Assembly Tent
├── Continuous Machine & Utility Rules (10 Rules)
│   ├── Petroleum Generator & Ground Heating Rail (Fish Oil)
│   ├── Petroleum Lamp & Oil Lamp
│   ├── Nanobot Repair Station
│   └── Bot Cap Limit, Forester, Farmhouse, Throttling Valve
└── Base Game Production (55 Rules)
    ├── Shared Woodworking, Metallurgy & Milling
    └── Food & Commodity Processing
```

---

## 6. How to Regenerate Rules

To update or regenerate `FrostyWhiskers automation rule.lisp` after modifying recipes or mod blueprints:

```bash
cd "C:\Users\souvi\Documents\Timberborn\Mods\Automation Rule"
python generate_frostywhiskers_rules.py
```
