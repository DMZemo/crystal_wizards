"""
Crystal Wizards - Sound Manager
Handles all audio effects and music for the game
"""

import pygame
import os
import random

class SoundManager:
    """Manages all sound effects and music for Crystal Wizards"""
    
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self.volume = 0.7
        
        # Initialize pygame mixer
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.mixer_available = True
        except pygame.error:
            print("Warning: Sound system not available")
            self.mixer_available = False
            self.enabled = False
    
    def load_sounds(self):
        """Load all sound effects"""
        if not self.mixer_available:
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        def p(name):
            return os.path.join(base_dir, 'sounds', name)

        sound_files = {
            'twinkle': p('twinkle.wav'),
            'spell_cast': p('spell_cast.wav'),
            'teleport': p('teleport.wav'),
            'dice_roll': p('dice_roll.wav'),
            'move': p('move.wav'),
            'mine': p('mine.wav'),
            'charge': p('charge.wav'),
            'heal': p('heal.wav'),
        }

        for sound_name, file_path in sound_files.items():
            try:
                if os.path.exists(file_path):
                    sound = pygame.mixer.Sound(file_path)
                    sound.set_volume(self.volume)
                    self.sounds[sound_name] = sound
                else:
                    print(f"Sound missing: {sound_name} -> {file_path} (using beep fallback)")
                    self.sounds[sound_name] = self._create_beep_sound(sound_name)
            except pygame.error as e:
                print(f"Warning: Could not load sound {sound_name} from {file_path}: {e}")
                self.sounds[sound_name] = self._create_beep_sound(sound_name)
    
    def _create_beep_sound(self, sound_type):
        """Create a simple beep sound as fallback"""
        if not self.mixer_available:
            return None

        try:
            import numpy as np
            import math

            frequencies = {
                'twinkle': 800,
                'spell_cast': 600,
                'teleport': 400,
                'dice_roll': 300,
                'move': 200,
                'mine': 250,
                'charge': 500,
                'heal': 700
            }

            freq = frequencies.get(sound_type, 440)
            duration = 0.2
            sample_rate = 22050
            frames = int(duration * sample_rate)

            t = np.arange(frames)
            wave = (4096 * np.sin(2 * math.pi * freq * t / sample_rate)).astype(np.int16)
            stereo = np.column_stack((wave, wave))

            sound = pygame.sndarray.make_sound(stereo)
            sound.set_volume(self.volume * 0.3)
            return sound
        except ImportError:
            return self._create_simple_beep(sound_type)
        except Exception as e:
            print(f"Beep fallback error ({sound_type}): {e}")
            return None
    
    def _create_simple_beep(self, sound_type):
        """Create simple beep without numpy dependency"""
        try:
            import array, math
            frequencies = {
                'twinkle': 800,
                'spell_cast': 600,
                'teleport': 400,
                'dice_roll': 300,
                'move': 200,
                'mine': 250,
                'charge': 500,
                'heal': 700
            }
            freq = frequencies.get(sound_type, 440)
            duration = 0.2
            sample_rate = 22050
            frames = int(duration * sample_rate)

            mono = array.array('h', (int(4096 * math.sin(2 * math.pi * freq * i / sample_rate)) for i in range(frames)))
            stereo = array.array('h')
            for s in mono:
                stereo.append(s); stereo.append(s)

            snd = pygame.mixer.Sound(buffer=stereo.tobytes())
            snd.set_volume(self.volume * 0.3)
            return snd
        except Exception as e:
            print(f"Simple beep fallback error ({sound_type}): {e}")
            return None
    
    def play_sound(self, sound_name, volume_modifier=1.0):
        """Play a sound effect"""
        if not self.enabled or not self.mixer_available:
            return
    
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                sound = self.sounds[sound_name]
                sound.set_volume(self.volume * volume_modifier)
                sound.play()
            except pygame.error:
                pass  # Fail silently
    
    def play_twinkle(self):
        """Play magical twinkle sound"""
        self.play_sound('twinkle')
    
    def play_spell_cast(self, damage=1):
        """Play spell casting sound with intensity based on damage"""
        volume = min(1.0, 0.5 + (damage * 0.1))
        self.play_sound('spell_cast', volume)
    
    def play_teleport(self):
        """Play teleportation sound"""
        self.play_sound('teleport')
    
    def play_dice_roll(self):
        """Play dice rolling sound"""
        self.play_sound('dice_roll')
    
    def play_move(self):
        """Play movement sound"""
        self.play_sound('move', 0.6)
    
    def play_mine(self):
        """Play mining sound"""
        self.play_sound('mine')
    
    def play_charge(self):
        """Play crystal charging sound"""
        self.play_sound('charge', 0.8)
    
    def play_heal(self):
        """Play healing sound"""
        self.play_sound('heal')
    
    def set_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)
    
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.enabled = not self.enabled
        return self.enabled
    
    def stop_all_sounds(self):
        """Stop all currently playing sounds"""
        if self.mixer_available:
            pygame.mixer.stop()

# Global sound manager instance
sound_manager = SoundManager()