#!/usr/bin/env python3
"""Verification script for New Game wizard implementation."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from core.new_game_session import NewGameSession
        print("  ✓ NewGameSession imported")
        
        from core.save_manager import SaveManager
        print("  ✓ SaveManager imported")
        
        from ui.new_game_page import NewGameView, MapSelectionView, GameplaySettingsView, ModLoadoutView
        print("  ✓ All UI views imported")
        
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_new_game_session():
    """Test NewGameSession functionality."""
    print("\nTesting NewGameSession...")
    from core.new_game_session import NewGameSession
    
    session = NewGameSession()
    
    # Test initial state
    assert session.selected_map is None, "Initial selected_map should be None"
    assert session.settings == {}, "Initial settings should be empty"
    assert session.selected_mods == [], "Initial selected_mods should be empty"
    print("  ✓ Initial state correct")
    
    # Test storing data
    session.selected_map = "test_map"
    session.settings["difficulty"] = "Hard"
    session.selected_mods.append("mod1")
    
    assert session.selected_map == "test_map"
    assert session.settings["difficulty"] == "Hard"
    assert "mod1" in session.selected_mods
    print("  ✓ Data storage working")
    
    # Test reset
    session.reset()
    assert session.selected_map is None
    assert session.settings == {}
    assert session.selected_mods == []
    print("  ✓ Reset working")
    
    return True

def test_save_manager():
    """Test SaveManager finalize_new_game method."""
    print("\nTesting SaveManager...")
    from core.save_manager import SaveManager
    from core.new_game_session import NewGameSession
    import tempfile
    import shutil
    
    # Create temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SaveManager(tmpdir)
        
        # Create a session
        session = NewGameSession()
        session.selected_map = "test_map"
        session.settings = {
            "difficulty": "Normal",
            "seasons": "Enabled",
            "economicSystem": "Realistic"
        }
        session.selected_mods = ["mod1", "mod2"]
        
        # Try to create a game
        success, message = manager.finalize_new_game(session)
        
        if success:
            print(f"  ✓ Game creation successful: {message}")
            
            # Verify files were created
            save_path = os.path.join(tmpdir, "savegame1")
            assert os.path.isdir(save_path), "Save directory should exist"
            print("  ✓ Save directory created")
            
            career_xml = os.path.join(save_path, "careerSavegame.xml")
            assert os.path.exists(career_xml), "careerSavegame.xml should exist"
            print("  ✓ careerSavegame.xml created")
            
            placeables_xml = os.path.join(save_path, "placeables.xml")
            assert os.path.exists(placeables_xml), "placeables.xml should exist"
            print("  ✓ placeables.xml created")
            
            mods_file = os.path.join(save_path, "mods.txt")
            assert os.path.exists(mods_file), "mods.txt should exist"
            print("  ✓ mods.txt created")
            
            return True
        else:
            print(f"  ✗ Game creation failed: {message}")
            return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("FS25 Manager - New Game Wizard Verification")
    print("=" * 60)
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_new_game_session():
        all_passed = False
    
    if not test_save_manager():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
