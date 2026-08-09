# Timberborn C# Mod Creation & Technical Pitfalls Wiki

This wiki documents the core architecture, design patterns, common pitfalls, and step-by-step debugging procedures for building C# mods for **Timberborn 1.0 & 1.1** using **Bindito**, **UI Toolkit**, **Harmony**, and **ModSettings**.

---

## 1. Core Mod Architecture & Lifecycle

Timberborn uses **Bindito** (a custom IoC/Dependency Injection framework) to wire components and singletons across scenes.

### 1.1 Scene Contexts
Components and singletons are bound within specific execution contexts:
* **`[Context("Game")]`**: Active during gameplay. Bound singletons implement `ILoadableSingleton`, `IUpdatableSingleton`, `ITickableSingleton`, `IAwakableSingleton`, etc.
* **`[Context("MainMenu")]`**: Active on the main menu screen.
* **`[Context("All")]`**: Active across both MainMenu and Game contexts.

```csharp
using Bindito.Core;

namespace SouvyShortCommute.Overlay {
  [Context("Game")]
  public class CommuteOverlayConfigurator : Configurator {
    protected override void Configure() {
      Bind<CommuteOverlayToggle>().AsSingleton();
      Bind<CommuteOverlayRenderer>().AsSingleton();
      Bind<CommuteOverlayPatcher>().AsSingleton();
    }
  }
}
```

### 1.2 Singleton Lifecycle Interfaces
* **`ILoadableSingleton`**: Implements `void Load()`. Called once when the context container finishes instantiating all singletons.
* **`IUpdatableSingleton`**: Implements `void UpdateSingleton()`. Called every Unity frame (`Update()`).
* **`ITickableSingleton`**: Implements `void TickSingleton()`. Called on fixed simulation ticks (`10 ticks/sec`).
* **`EventBus` Subscriptions**: Add `[OnEvent]` attributes to public event handlers and register `_eventBus.Register(this)` inside `Load()`.

---

## 2. Technical Pitfalls & Gotchas

### Pitfall 1: Bindito Dependency Injection Chain Failures
* **Symptom:** `BinditoException: UnstuckifyTickableSingleton isn't instantiable due to missing dependency: UnstuckifySettingsOwner`.
* **Cause:** A singleton requests a dependency in its constructor (e.g. `SettingsOwner`), but that dependency was not bound in the corresponding `Configurator`, or was bound under a different `Context`.
* **Solution:** Ensure every parameter in a singleton's constructor is registered in the `Configurator` under the matching `[Context(...)]`.

---

### Pitfall 2: Duplicate `ModSettingsOwner` Registration Crash
* **Symptom:** Mod crashes on load with `ArgumentException: An item with the same key has already been added` or `KeyNotFoundException` in `ModSettingsOwnerRegistry`.
* **Cause:** When multiple singletons take `ModSettingsOwner` in their constructor, Bindito or ModSettings attempts to re-register the settings owner into `ModSettingsOwnerRegistry._modSettingOwners`.
* **Solution:** Add `CleanupDuplicateRegistrations` inside the `ModSettingsOwner` constructor to remove duplicate instances:

```csharp
public class CommuteOverlaySettings : ModSettingsOwner {
  public CommuteOverlaySettings(ISettings settings,
      ModSettingsOwnerRegistry modSettingsOwnerRegistry, ModRepository modRepository)
      : base(settings, modSettingsOwnerRegistry, modRepository) {
    CleanupDuplicateRegistrations(modSettingsOwnerRegistry);
  }

  private void CleanupDuplicateRegistrations(ModSettingsOwnerRegistry registry) {
    var field = typeof(ModSettingsOwnerRegistry).GetField("_modSettingOwners", BindingFlags.NonPublic | BindingFlags.Instance);
    if (field != null) {
      if (field.GetValue(registry) is System.Collections.IDictionary dict) {
        foreach (System.Collections.IList list in dict.Values) {
          if (list != null && list.Contains(this) && list.Count > 1) {
            list.Remove(this);
            break;
          }
        }
      }
    }
  }
}
```

---

### Pitfall 3: `ModId` Mismatch with `manifest.json`
* **Symptom:** Log warning: `Could not find mod with id SouvyShortCommute for SouvyShortCommute.Overlay.CommuteOverlaySettings`.
* **Cause:** `protected override string ModId` in `ModSettingsOwner` returns `"SouvyShortCommute"`, but `manifest.json` defines `"Id": "Souvy.ShortCommute"` (with a dot).
* **Solution:** `ModId` MUST match `"Id"` in `manifest.json` character-for-character.

---

### Pitfall 4: UI Toolkit Missing Texture `?` Box & Custom Icon Styling
* **Symptom:** Custom HUD button displays a white diamond question mark `?` or a solid filled green square when clicked.
* **Cause:** 
  1. `Common/SquareToggle` template looks for built-in USS classes. Unstyled toggles trigger Unity UI Toolkit's missing texture fallback `?`.
  2. When checked, the toggle applies `.toggle--checked` which draws the solid green check box over child elements.
* **Solution:** 
  1. Load `Common/SquareToggle` via `_visualElementLoader.LoadVisualElement("Common/SquareToggle")`.
  2. Clear checkmark text/label and create an absolute overlay `VisualElement` (`Position.Absolute`, `left=0, right=0, top=0, bottom=0`, `ScaleMode.ScaleToFit`) with `PickingMode.Ignore` so clicks pass through:

```csharp
VisualElement iconElement = new VisualElement();
iconElement.pickingMode = PickingMode.Ignore;
iconElement.style.backgroundImage = new StyleBackground(texture);
iconElement.style.position = Position.Absolute;
iconElement.style.left = 0;
iconElement.style.right = 0;
iconElement.style.top = 0;
iconElement.style.bottom = 0;
iconElement.style.alignSelf = Align.Center;
iconElement.style.justifyContent = Justify.Center;
iconElement.style.unityBackgroundScaleMode = ScaleMode.ScaleToFit;
_toggle.Add(iconElement);
```

---

### Pitfall 5: `SelectableObject` Hierarchy Traversal in Timberborn 1.1
* **Symptom:** Clicking a building or beaver in game triggers `OnObjectSelected`, but `selectable.GetComponent<Dwelling>()` returns `null`.
* **Cause:** In Timberborn 1.1, `SelectableObject` is attached to sub-colliders/child transforms of entities rather than the root GameObject.
* **Solution:** Traverse both parent and child transform hierarchies:

```csharp
var worker = selectable.GetComponent<Worker>() ?? selectable.GameObject.GetComponentInParent<Worker>() ?? selectable.GameObject.GetComponentInChildren<Worker>();
var dwelling = selectable.GetComponent<Dwelling>() ?? selectable.GameObject.GetComponentInParent<Dwelling>() ?? selectable.GameObject.GetComponentInChildren<Dwelling>();
var workplace = selectable.GetComponent<Workplace>() ?? selectable.GameObject.GetComponentInParent<Workplace>() ?? selectable.GameObject.GetComponentInChildren<Workplace>();
```

---

### Pitfall 6: Empty Assembly.Location in In-Memory Mod Loading
* **Symptom:** File asset lookups fail with `File not found` when attempting to load mod UI images or icons.
* **Cause:** `Assembly.GetExecutingAssembly().Location` returns an **empty string (`""`)** when assemblies are loaded into memory by Timberborn's mod loader.
* **Solution:** Always check `Environment.SpecialFolder.MyDocuments` as the primary path for mod directory assets, with `Assembly.Location` as a secondary fallback:

```csharp
private string FindIconPath() {
  string userDocs = System.Environment.GetFolderPath(System.Environment.SpecialFolder.MyDocuments);
  string iconPath = System.IO.Path.Combine(userDocs, "Timberborn", "Mods", "Souvy-ShortCommute", "version-1.1.0", "UI", "commute_analysis_icon.png");
  if (System.IO.File.Exists(iconPath)) {
    return iconPath;
  }
  string execAssembly = System.Reflection.Assembly.GetExecutingAssembly().Location;
  if (!string.IsNullOrEmpty(execAssembly)) {
    string dir = System.IO.Path.GetDirectoryName(execAssembly) ?? "";
    string fallback = System.IO.Path.Combine(dir, "UI", "commute_analysis_icon.png");
    if (System.IO.File.Exists(fallback)) return fallback;
  }
  return null;
}
```

---

## 3. Step-by-Step Debugging Workflow

### Step 1: Locating & Filtering Logs
Timberborn outputs all log statements (`Debug.Log`, `Debug.LogWarning`, `Debug.LogError`) to `Player.log`:
* **Path:** `C:\Users\<User>\AppData\LocalLow\Mechanistry\Timberborn\Player.log`

Filter logs by mod prefix:
```bash
grep "Souvy" C:\Users\souvi\AppData\LocalLow\Mechanistry\Timberborn\Player.log
```

### Step 2: Runtime Reflection Inspection
When debugging internal Timberborn or ModSettings types, use a standalone C# inspector project referencing Timberborn managed DLLs (`Timberborn.CoreUI.dll`, `Timberborn.WaterSystemUI.dll`, etc.) to disassemble methods and inspect internal field names.

### Step 3: Verifying DLL Builds
After editing mod source files, always execute `dotnet build` and check for 0 errors:
```bash
dotnet build c:\Users\souvi\Documents\Timberborn\Mods\Souvy-ShortCommute\version-1.1.0\SouvyShortCommute.csproj
```
