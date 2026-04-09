"""State management for the New Game wizard."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NewGameSession:
    """Stores the state of the new game wizard across all steps."""
    
    selected_map: Optional[str] = None
    """Map ID/Path of the selected map."""
    
    settings: dict = field(default_factory=dict)
    """Dictionary containing gameplay settings (difficulty, seasons, etc.)."""
    
    selected_mods: list[str] = field(default_factory=list)
    """List of mod IDs/names to enable in the new game."""
    
    def reset(self):
        """Reset all session data to initial state."""
        self.selected_map = None
        self.settings = {}
        self.selected_mods = []
