# Whitepaws Automation Rules Technical Guide & Specification

This documentation details the architecture, signal logic, thresholds, localization resolution, and recipe generation engine for **Whitepaws Automation Rules** in Timberborn.

---

## 1. Overview & Architecture

The Whitepaws Automation Rule system dynamically manages faction workplaces, production efficiency, and resource sustainability. By evaluating district-wide inventory stock and storage capacity signals in real-time, rules automatically enable/disable workforce allocation or pause continuous building operations (such as Sawdust Incinerators).

The automation rule file is written in Timberborn Automation Lisp expression syntax:
- **Rule File Path**: `C:\Users\souvi\Documents\Timberborn\Mods\Automation Rule\Whitepaws automation rule.lisp`
- **Generator Utility**: `C:\Users\souvi\Documents\Timberborn\Mods\Automation Rule\generate_whitepaws_rules.py`

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
| **Excess Sawdust Incinerator** | Sawdust Stock `< 75%` Capacity | `(mul 75 (sig District.ResourceCapacity.Sawdust))` | `Pausable.Pause` |
| **Sawdust Incinerator Resume** | Sawdust Stock `>= 75%` Capacity | `(mul 75 (sig District.ResourceCapacity.Sawdust))` | `Pausable.Unpause` |

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
4. Manual fallback dictionary (`MANUAL_GOOD_NAMES`) for mod-specific internal IDs (e.g. `Apple_WP` -> "Apples", `HoomanRelic` -> "Human Relic", `Crudesawblade` -> "Crude Saw Blade", `SAquiferPumpBlueprint` -> "Aquifer Pump Blueprint", `Awfulstew` -> "Awful Stew").

---

## 5. Recipe Scope & Coverage

The rule generator scans 345 unique recipe specifications across the Whitepaws mod and base game assets:

```text
Recipe Specification Scope (345 Total Rules):
├── Whitepaws 1.1 Mod Recipes (290)
│   ├── General & Industrial Recipes (202)
│   ├── Balloon Trade Recipes (53)
│   ├── Cooking Recipes (22)
│   └── Drink Recipes (13)
└── Base Game Recipes (55)
    ├── Folktails Base & Advanced Recipes
    └── IronTeeth Base & Advanced Recipes
```

---

## 6. How to Regenerate Rules

To update or regenerate `Whitepaws automation rule.lisp` after adding or editing recipe JSON specifications:

```bash
cd "C:\Users\souvi\Documents\Timberborn\Mods\Automation Rule"
python generate_whitepaws_rules.py
```
