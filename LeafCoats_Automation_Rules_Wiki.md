# Leaf Coats Automation Rules Technical Guide & Specification

This documentation details the architecture, signal logic, thresholds, localization resolution, and recipe generation engine for **Leaf Coats Automation Rules** in Timberborn.

---

## 1. Overview & Architecture

The Leaf Coats Automation Rule system dynamically manages faction workplaces, production efficiency, and resource sustainability for the Leaf Coats faction and its official extensions (**Leaf Coats: Badwater** and **Leaf Coats: Explosives**). By evaluating district-wide inventory stock and storage capacity signals in real-time, rules automatically enable/disable workforce allocation or adjust infrastructure (such as Throttling Valves and Floodgates).

The automation rule files are located at:
- **Rule File Path**: `C:\Users\souvi\Documents\Timberborn\Mods\Automation Rule\LeafCoats automation rule.lisp`
- **Generator Utility**: `C:\Users\souvi\Documents\Timberborn\Mods\Automation Rule\generate_leafcoats_rules.py`

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
| **Output-Only Production** | Output Stock `>= 90%` Capacity | `(mul 90 (sig District.ResourceCapacity.<OutputId>))` | `Workplace.RemoveWorkers` |
| **Output-Only Resumption** | Output Stock `< 90%` Capacity | `(mul 90 (sig District.ResourceCapacity.<OutputId>))` | `Workplace.SetWorkers {% (getvalue Workplace.MaxWorkers) %}` |
| **Bot Assembler Limit** | Population `>= 8000` | Fixed value `8000` | `Workplace.RemoveWorkers` |
| **Bot Assembler Resume** | Population `< 8000` | Fixed value `8000` | `Workplace.SetWorkers {% (getvalue Workplace.MaxWorkers) %}` |
| **Seasonal Throttling Valve** | Season `!= 'TemperateWeather'` | Weather signal | `ThrottlingValve.Close` |
| **Seasonal Throttling Valve** | Season `== 'TemperateWeather'` | Weather signal | `ThrottlingValve.Open` |
| **Lumberjack Ready Check** | `Collectable.Ready > 1` (100 in lisp) AND `Log < 90%` | Composite `(and ...)` | `Workplace.SetWorkers {% (getvalue Workplace.MaxWorkers) %}` |
| **Lumberjack Fullness / Out** | `Collectable.Ready <= 1` (100 in lisp) OR `Log >= 90%` | Composite `(or ...)` | `Workplace.RemoveWorkers` |
| **Harvest Ready Check** | `(sig Collectable.Ready) == 0` | Farmhouse / Flags | `Workplace.RemoveWorkers` |
| **Planting Ready Check** | `(sig Plantable.Ready) == 0` | Forester | `Workplace.RemoveWorkers` |

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

## 4. Localization Resolution Engine

Rule header comment titles are strictly formatted to display English localization names parsed from `enUS.csv`:
`;;;;<Localized Recipe Title> (<Localized Input 1> + <Localized Input 2> -> <Localized Output 1>) (Fuel: <Localized Fuel>)`

### Resolution Hierarchy
1. `DisplayLocKey` attribute in recipe JSON specification
2. `Recipe.<Id>.DisplayName` / `Recipe.<Id>.Name`
3. `Good.<Id>.DisplayName` / `Good.<Id>.Name`
4. Manual fallback dictionary (`MANUAL_GOOD_NAMES` & `MANUAL_RECIPE_NAMES`) for mod-specific internal IDs (e.g. `Branch` -> "Branch", `Bark` -> "Bark", `Shovel` -> "Shovel", `FancyApples` -> "Fancy Apple", `FermentedChestnut` -> "Fermented Chestnut", `FermentedDandelion` -> "Fermented Dandelion", `FermentedFruit` -> "Fermented Fruit", `FruitSalad` -> "Fruit Salad", `Log.Press.LeafCoats` -> "Lumber Press: Synthetic Log", `Plank.Press.LeafCoats` -> "Lumber Press: Synthetic Plank", `Shovel.LeafCoats` -> "Tool Factory: Shovel").

---

## 5. Recipe Scope & Coverage

The rule generator scans unique recipe specifications across the Leaf Coats faction mod, official extensions, and base game production assets:

```text
Leaf Coats Automation Scope (66 Generated Rules + 8 Environmental / Infrastructure Rules):
├── Leaf Coats Unique Production Recipes (15)
│   ├── Food Processor: Fancy Apple, Fruit Salad
│   ├── Fermenter: Fermented Chestnut, Fermented Dandelion, Fermented Fruit
│   ├── Lumber Press: Synthetic Log (Branch + Bark + Pine Resin), Synthetic Plank (Branch + Pine Resin)
│   ├── Tool Factory: Shovel (Branch, Fuel: Metal Block)
│   ├── Herbalist: Antidote (Bark + Dandelion + Berries)
│   ├── Refinery: Lubricant (Extract + Pine Resin)
│   ├── Grinder / Shredder: Metal Block (Scrap Metal)
│   ├── Mine: Efficient Scrap Metal (Treated Plank + Extract)
│   ├── Badwater Seep Rig: Extract
│   ├── Large Water Pump: Water
│   └── Geothermal Numbercruncher: Science Points
├── Extension & Base Production Recipes (51)
│   ├── Badwater Pump & Centrifuge (Badwater -> Extract)
│   ├── Explosives Factory (Dynamite)
│   ├── Bot Part Factory & Bot Assembler (Bot Chassis, Bot Head, Bot Limb)
│   ├── Standard Milling, Smelting, Pressing, and Brewing
│   └── Resource Extraction (Aquifer Drill, Deep Well, Scavenger Flag)
└── Environmental & Infrastructure Rules (8)
    ├── Bot Assembler Population Cap (8000)
    ├── Forester Planting Readiness Check
    ├── Farmhouse & Gatherer Harvesting Readiness Checks
    ├── Throttling Valve Seasonal Automation
    └── Automated Floodgate Seasonal Height Adjustments (30%, 70%, Badtide Isolation)
```

---

## 6. How to Regenerate Rules

To update or regenerate `LeafCoats automation rule.lisp` after adding or editing recipe JSON specifications:

```bash
cd "C:\Users\souvi\Documents\Timberborn\Mods\Automation Rule"
python generate_leafcoats_rules.py
```
