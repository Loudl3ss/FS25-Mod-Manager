# New Game Wizard - State Persistence Implementation

## Overview
This implementation adds complete state persistence and game creation logic to the FS25 Manager's "New Game" wizard. The wizard guides users through three steps to create a new farming save game with customized settings and mods.

## Components Implemented

### 1. **NewGameSession Class** ([core/new_game_session.py](core/new_game_session.py))

A dataclass that manages the complete state of the new game wizard:

```python
@dataclass
class NewGameSession:
    selected_map: Optional[str] = None          # Selected map ID/Name
    settings: dict = field(default_factory=dict) # Gameplay settings
    selected_mods: list[str] = field(default_factory=list) # Enabled mods
```

**Key Features:**
- Stores map selection across wizard steps
- Maintains gameplay settings (difficulty, seasons, economy)
- Tracks selected mods for the new game
- Provides `reset()` method to clear all data

---

### 2. **MapSelectionView** (Step 1) - [ui/new_game_page.py](ui/new_game_page.py)

**Features:**
- Displays available maps as a grid of ModCards
- **Visual Highlight**: Selected map gets a **3px solid white border** with semi-transparent background
- Selection is stored in `session.selected_map`
- "Next" button only enabled when a map is selected
- **Persistence**: When returning to this view, the previously selected map is automatically highlighted

**Technical Implementation:**
- Stores map objects for reference lookup
- Uses `showEvent()` to restore selection when view becomes visible
- Custom styling applied via `_apply_selection_style()` method
- Deselects all other cards when a new one is clicked

---

### 3. **GameplaySettingsView** (Step 2) - [ui/new_game_page.py](ui/new_game_page.py)

**Features:**
- Three configurable settings via dropdown menus:
  - **Difficulty**: Easy / Normal / Hard
  - **Seasons**: Enabled / Disabled
  - **Economic System**: Realistic / Simplified
- Settings are immediately stored in `session.settings` on change
- **Persistence**: When returning to this step, all previous selections are restored
- Back/Next navigation buttons

**Technical Implementation:**
- Uses `QComboBox` for each setting
- Connected signals update session on every change
- `showEvent()` restores previous values from session
- Prevents signal-triggered updates during view initialization

---

### 4. **ModLoadoutView** (Step 3) - [ui/new_game_page.py](ui/new_game_page.py)

**Features:**
- Displays all available mods (excluding maps) as checkboxes
- Each mod can be enabled/disabled for the new game
- **Persistence**: Previously selected mods remain checked when returning
- "Create Game" button triggers the finalization process
- Visual feedback with green checkboxes for selected mods

**Technical Implementation:**
- Dynamically creates checkboxes from available mods
- Tracks checked state and updates `session.selected_mods`
- Calls `finalize_new_game()` on creation button click
- Handles success/error messages via QMessageBox

---

### 5. **SaveManager.finalize_new_game()** - [core/save_manager.py](core/save_manager.py)

**Creates the actual save game with the following process:**

1. **Find Empty Slot**: Scans `savegame1` through `savegame20`
   - Empty = directory doesn't exist OR no `careerSavegame.xml`
   - Returns first available slot

2. **Create Directory**: Creates `savegameX/` directory

3. **Generate careerSavegame.xml**:
   ```xml
   <careerSavegame>
       <settings>
           <farmName>Farm X</farmName>
           <savegameName>Save X</savegameName>
           <mapId>{selected_map}</mapId>
           <difficulty>{difficulty}</difficulty>
           <seasons>{seasons}</seasons>
           <economicSystem>{economicSystem}</economicSystem>
           <playTime>0</playTime>
           <saveDateFormatted>YYYY-MM-DD HH:MM:SS</saveDateFormatted>
           ...
       </settings>
       <playerFarm money="50000"/>
   </careerSavegame>
   ```

4. **Generate placeables.xml**: Empty placeables list for user to populate

5. **Store Mod References**: Creates `mods.txt` with list of enabled mods

6. **Error Handling**: 
   - Automatic cleanup if creation fails
   - Descriptive error messages returned to UI

**Return Value:**
```python
(success: bool, message: str)
# Examples:
# (True, "New game created in save slot 1")
# (False, "All save slots are full")
```

---

### 6. **NewGameView (Wizard Container)** - [ui/new_game_page.py](ui/new_game_page.py)

**Features:**
- Manages the complete wizard lifecycle
- Creates shared `NewGameSession` instance
- Passes session reference to all step views
- Handles navigation between steps
- Left sidebar shows progress and allows jumping between steps
- Resets session after successful game creation

**Integration in MainWindow:**
```python
self._new_game_page = NewGameView(self._mod_manager, self._save_manager)
```

---

## Workflow

### User Journey:

1. **Step 1 - Select Map**
   - User clicks on a map card
   - Map ID stored in `session.selected_map`
   - Card highlighted with white border
   - "Next" button becomes enabled
   - Clicking "Next" advances to step 2

2. **Step 2 - Gameplay Settings**
   - User selects difficulty, seasons, and economy settings
   - Each change updates `session.settings` in real-time
   - User can click "Back" to return to map selection (selection preserved)
   - User can click "Next" to advance to step 3

3. **Step 3 - Mod Loadout**
   - User sees list of all mods (non-maps)
   - Checks boxes for mods to enable
   - Selections update `session.selected_mods`
   - User can click "Back" to return to settings (all choices preserved)
   - User clicks "Create Game" to finalize

4. **Game Creation**
   - `SaveManager.finalize_new_game(session)` is called
   - Empty save slot is found
   - All necessary files are created
   - Success notification shown
   - Session is reset for next wizard use

### Persistence Example:

User journey with back/forward navigation:
```
Step 1: Select "Sunny Valley" map
  → session.selected_map = "sunnycreekvalley"

Step 2: Set difficulty to "Hard", seasons to "Disabled"
  → session.settings = {"difficulty": "Hard", "seasons": "Disabled", ...}

[User clicks Back]
  → Step 1 shown, "Sunny Valley" still highlighted

[User clicks Next]
  → Step 2 shown, settings still show Hard/Disabled

[User clicks Next]
  → Step 3 shown, previous mods still checked

[User clicks Back twice, then Forward multiple times]
  → All previous selections maintained throughout
```

---

## File Structure

```
core/
  new_game_session.py        # NEW: Session state management
  save_manager.py            # MODIFIED: Added finalize_new_game()

ui/
  new_game_page.py           # COMPLETELY REWRITTEN: Full wizard implementation
  main_window.py             # MODIFIED: Pass save_manager to NewGameView
  
test_new_game_wizard.py      # TEST: Verification script
```

---

## Key Technical Details

### State Management
- **Session Object**: Single instance shared across all views
- **Session Passing**: Views receive session reference in `__init__`
- **Direct Updates**: Views update session directly (no complex signal chains)
- **View Synchronization**: `showEvent()` hooks restore UI state from session

### Highlighting Logic
- **Classic Style**: Default ModCard styling with green border
- **Selected Style**: White 3px border + semi-transparent background
- **Interactive**: Hover states maintained with white border
- **Deselection**: Previous card's styling reset before new selection

### XML Generation
- Pretty-printed with proper indentation
- Timezone-aware timestamps
- Complies with Farming Simulator 2025 format
- Extensible structure for custom properties

### Error Handling
- Directory creation failures
- XML generation failures
- File I/O errors
- Auto-cleanup of partially created saves
- User-friendly error messages

---

## Testing

Run the verification script:
```bash
cd /home/bazzite/.gemini/antigravity/scratch/fs25-manager
python test_new_game_wizard.py
```

**Tests Verify:**
- ✅ All imports successful
- ✅ NewGameSession state management
- ✅ SaveManager.finalize_new_game() creates valid saves
- ✅ XML files are properly generated
- ✅ Mod references are stored

---

## Future Enhancements

Potential improvements for future iterations:
1. **Copy from existing save**: Pre-fill settings from another save
2. **Mod dependency checking**: Validate mod compatibility
3. **Map previews**: Show map thumbnail in selection
4. **Custom farm names**: Allow user to name their farm
5. **Advanced settings**: Seasons length, economy tweaks
6. **Template saves**: Save/load wizard configurations
7. **Validation**: Verify map/mod availability before creation

---

## Notes

- All state is preserved when navigating backward in the wizard
- Session is automatically reset after successful game creation
- The implementation follows the existing codebase patterns
- PyQt6 signals are used for inter-component communication
- Error handling is comprehensive with user-friendly messages
