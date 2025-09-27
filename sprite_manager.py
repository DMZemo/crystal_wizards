
"""
Crystal Wizards - Sprite Manager
Handles loading and managing wizard sprites and other game graphics
"""

import pygame
import os
from pathlib import Path
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in development mode
        base_path = Path(__file__).parent
    
    return base_path / relative_path

class SpriteManager:
    """Manages all game sprites and graphics"""
    
    def __init__(self):
        self.wizard_sprites = {}
        # Don't load sprites immediately - wait for display initialization
        
    def load_sprites(self):
        """Load all game sprites"""
        # Load wizard sprites
        wizard_colors = ['red', 'blue', 'green', 'yellow']
        
        for color in wizard_colors:
            sprite_path = resource_path(f"assets/{color}_wizard.png")
            try:
                if os.path.exists(sprite_path):
                    sprite = pygame.image.load(sprite_path)
                    # Only convert_alpha if display is initialized
                    if pygame.get_init() and pygame.display.get_surface():
                        sprite = sprite.convert_alpha()
                    # Scale sprite to appropriate size (48x48 for board display)
                    sprite = pygame.transform.scale(sprite, (48, 48))
                    self.wizard_sprites[color] = sprite
                else:
                    print(f"Warning: Wizard sprite not found: {sprite_path}")
                    # Create a fallback colored circle
                    self._create_fallback_sprite(color)
            except Exception as e:
                print(f"Error loading wizard sprite {color}: {e}")
                # Create fallback sprite
                self._create_fallback_sprite(color)
                
    def _create_fallback_sprite(self, color):
        """Create a fallback sprite for a wizard color"""
        sprite = pygame.Surface((24, 24), pygame.SRCALPHA)
        color_map = {
            'red': (220, 50, 50),
            'blue': (50, 50, 220),
            'green': (50, 220, 50),
            'yellow': (220, 220, 50)
        }
        pygame.draw.circle(sprite, color_map.get(color, (128, 128, 128)), (12, 12), 10)
        pygame.draw.circle(sprite, (0, 0, 0), (12, 12), 10, 2)
        self.wizard_sprites[color] = sprite
                
    def get_wizard_sprite(self, color: str) -> pygame.Surface:
        """Get wizard sprite for the given color"""
        # Load sprites if not already loaded
        if not self.wizard_sprites:
            self.load_sprites()
        return self.wizard_sprites.get(color, self.wizard_sprites.get('red'))
        
    def create_glowing_sprite(self, sprite: pygame.Surface, glow_color: tuple, glow_intensity: float = 1.0) -> pygame.Surface:
        """Create a glowing version of a sprite"""
        # Create a larger surface for the glow effect
        glow_size = 4
        new_size = (sprite.get_width() + glow_size * 2, sprite.get_height() + glow_size * 2)
        glow_surface = pygame.Surface(new_size, pygame.SRCALPHA)
        
        # Create glow effect by drawing the sprite multiple times with offset
        glow_alpha = int(50 * glow_intensity)
        for offset in range(1, glow_size + 1):
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx == 0 and dy == 0:
                        continue
                    temp_surface = sprite.copy()
                    temp_surface.fill((*glow_color, glow_alpha), special_flags=pygame.BLEND_RGBA_MULT)
                    glow_surface.blit(temp_surface, (glow_size + dx, glow_size + dy))
        
        # Draw the original sprite on top
        glow_surface.blit(sprite, (glow_size, glow_size))
        
        return glow_surface

# Global sprite manager instance
sprite_manager = SpriteManager()
