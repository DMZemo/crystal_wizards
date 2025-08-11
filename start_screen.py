"""
Crystal Wizards - Enhanced Start Screen (FIXED VERSION)
Features player setup, color selection, usernames, and magical effects
"""

import pygame
import sys
import math
import random
from sound_manager import sound_manager

class ShimmerEffect:
    """Handles magical shimmer effects for buttons"""
    
    def __init__(self):
        self.active_shimmers = []
    
    def add_shimmer(self, rect):
        """Add a shimmer effect to a button"""
        shimmer = {
            'rect': rect.copy(),
            'progress': 0.0,
            'duration': 1.0,
            'particles': []
        }
        
        # Create shimmer particles
        for _ in range(30):
            particle = {
                'x': rect.x + random.randint(0, rect.width),
                'y': rect.y + random.randint(0, rect.height),
                'size': random.randint(1, 3),
                'speed': random.uniform(1, 3),
                'life': random.uniform(2, 4)
            }
            shimmer['particles'].append(particle)
        
        self.active_shimmers.append(shimmer)
    
    def update(self, dt):
        """Update shimmer effects"""
        for shimmer in self.active_shimmers[:]:
            shimmer['progress'] += dt / shimmer['duration']
            
            # Update particles
            for particle in shimmer['particles']:
                particle['life'] -= dt
                particle['x'] += particle['speed'] * 50 * dt
                particle['y'] -= particle['speed'] * 30 * dt
            
            if shimmer['progress'] >= 1.0:
                self.active_shimmers.remove(shimmer)
    
    def draw(self, screen, colors):
        """Draw shimmer effects"""
        for shimmer in self.active_shimmers:
            alpha = int(255 * (1.0 - shimmer['progress']))
            
            for particle in shimmer['particles']:
                if particle['life'] > 0:
                    particle_alpha = int(alpha * particle['life'])
                    if particle_alpha > 0:
                        # Create shimmer color with alpha
                        shimmer_color = (*colors['gold'][:3], particle_alpha)
                        size = int(particle['size'] * particle['life'])
                        if size > 0:
                            pygame.draw.circle(screen, colors['gold'], 
                                             (int(particle['x']), int(particle['y'])), size)

class PlayerSetup:
    """Handles individual player configuration"""
    
    def __init__(self, player_index, is_ai=False):
        self.player_index = player_index
        self.is_ai = is_ai
        self.username = f"Player {player_index + 1}" if not is_ai else f"AI {player_index + 1}"
        self.color = None  # FIXED: Player starts with no color selected
        self.difficulty = 'medium' if is_ai else None
        self.input_active = False

class StartScreen:
    """Enhanced start screen with full player configuration"""
    
    def __init__(self, screen_width=None, screen_height=None):
        # Get full screen dimensions and create fullscreen window
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("Crystal Wizards - Enhanced Setup")
        
        # Initialize sound
        sound_manager.load_sounds()
        
        # Fonts - Made much larger
        pygame.font.init()
        self.font_title = pygame.font.Font(None, 120)  # Increased from 72
        self.font_large = pygame.font.Font(None, 56)   # Increased from 36
        self.font_medium = pygame.font.Font(None, 42)  # Increased from 28
        self.font_small = pygame.font.Font(None, 32)   # Increased from 24
        
        # Colors
        self.colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (220, 50, 50),
            'blue': (50, 50, 220),
            'green': (50, 220, 50),
            'yellow': (220, 220, 50),
            'grey': (128, 128, 128),
            'light_grey': (200, 200, 200),
            'dark_grey': (64, 64, 64),
            'gold': (255, 215, 0),
            'purple': (128, 0, 128),
            'background': (0, 0, 0)
        }
        
        # Game state
        self.setup_phase = 'player_count'
        self.num_human_players = 2
        self.num_ai_players = 2
        self.player_setups = []
        self.current_setup_index = 0
        
        # UI elements
        self.buttons = {}
        self.input_boxes = {}
        self.create_ui_elements()
        
        # Animation and effects
        self.twinkle_timer = 0
        self.twinkle_particles = []
        self.shimmer_effects = ShimmerEffect()
        
        # Debug mode
        self.debug_mode = False
        
        # Welcome sound
        sound_manager.play_sound("twinkle", 0.5)
        
        if self.debug_mode:
            print("DEBUG: EnhancedStartScreen initialized")
    
    def create_ui_elements(self):
        """Create UI buttons and input elements - All centered and bigger"""
        # Calculate center area (half of middle screen)
        content_width = self.screen_width // 2
        content_height = self.screen_height // 2
        content_x = (self.screen_width - content_width) // 2
        content_y = (self.screen_height - content_height) // 2
        
        center_x = self.screen_width // 2
        
        # Player count buttons - Much bigger and centered
        button_width = 300  # Increased from 150
        button_height = 70  # Increased from 40
        y_start = content_y + 100
        
        for i, (human, ai) in enumerate([(1, 3), (2, 2), (3, 1), (4, 0)]):
            self.buttons[f'config_{i}'] = {
                'rect': pygame.Rect(center_x - button_width//2, y_start + i * 90, button_width, button_height),
                'text': f"{human} Human, {ai} AI",
                'human': human,
                'ai': ai,
                'selected': i == 1  # Default to 2H, 2AI
            }
        
        # Control buttons - Bigger and better positioned
        button_y = content_y + content_height - 80
        self.buttons['next'] = {
            'rect': pygame.Rect(center_x + 80, button_y, 180, 70),  # Bigger buttons
            'text': 'Next',
            'enabled': True
        }
        
        self.buttons['back'] = {
            'rect': pygame.Rect(center_x - 260, button_y, 180, 70),
            'text': 'Back',
            'enabled': False
        }
        
        self.buttons['start'] = {
            'rect': pygame.Rect(center_x - 90, button_y, 180, 70),
            'text': 'Start Game!',
            'enabled': False
        }
        
        # Color selection buttons - Bigger and centered
        colors = ['red', 'blue', 'green', 'yellow']
        color_start_x = center_x - (len(colors) * 100) // 2
        for i, color in enumerate(colors):
            self.buttons[f'color_{color}'] = {
                'rect': pygame.Rect(color_start_x + i * 100, content_y + 200, 80, 80),  # Bigger color buttons
                'color': color,
                'available': True
            }
        
        # Difficulty buttons for AI - Bigger and centered
        difficulties = ['easy', 'medium', 'hard']
        diff_start_x = center_x - (len(difficulties) * 120) // 2
        for i, diff in enumerate(difficulties):
            self.buttons[f'diff_{diff}'] = {
                'rect': pygame.Rect(diff_start_x + i * 120, content_y + 320, 100, 60),  # Bigger difficulty buttons
                'text': diff.title(),
                'difficulty': diff
            }
    
    def handle_events(self):
        """Handle pygame events"""
        dt = 1/60
        self.shimmer_effects.update(dt)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.debug_mode:
                    print("DEBUG: Quit event received")
                return 'quit'
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.debug_mode:
                        print("DEBUG: Escape key pressed")
                    return 'quit'
                
                # Handle text input for usernames
                if self.setup_phase == 'player_setup' and self.current_setup_index < len(self.player_setups):
                    current_setup = self.player_setups[self.current_setup_index]
                    if current_setup.input_active:
                        if event.key == pygame.K_RETURN:
                            current_setup.input_active = False
                            if self.debug_mode:
                                print(f"DEBUG: Username input finished: {current_setup.username}")
                        elif event.key == pygame.K_BACKSPACE:
                            current_setup.username = current_setup.username[:-1]
                        else:
                            if len(current_setup.username) < 15:
                                current_setup.username += event.unicode
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if self.debug_mode:
                        print(f"DEBUG: Mouse click at {event.pos}")
                    result = self.handle_click(event.pos)
                    if result:
                        return result
        
        return None
    
    def handle_click(self, pos):
        """Handle mouse clicks with shimmer effects"""
        if self.setup_phase == 'player_count':
            # Check config buttons
            for key, button in self.buttons.items():
                if key.startswith('config_') and button['rect'].collidepoint(pos):
                    # Add shimmer effect
                    self.shimmer_effects.add_shimmer(button['rect'])
                    
                    # Deselect all others
                    for k in self.buttons:
                        if k.startswith('config_'):
                            self.buttons[k]['selected'] = False
                    # Select this one
                    button['selected'] = True
                    self.num_human_players = button['human']
                    self.num_ai_players = button['ai']
                    sound_manager.play_sound('move', 0.5)
                    if self.debug_mode:
                        print(f"DEBUG: Selected config - {button['human']} Human, {button['ai']} AI")
            
            # Check next button
            if self.buttons['next']['rect'].collidepoint(pos):
                self.shimmer_effects.add_shimmer(self.buttons['next']['rect'])
                if self.debug_mode:
                    print("DEBUG: Next button clicked in player_count phase")
                self.advance_to_player_setup()
        
        elif self.setup_phase == 'player_setup':
            if self.current_setup_index >= len(self.player_setups):
                if self.debug_mode:
                    print("DEBUG: Invalid setup index, returning to player_count")
                self.setup_phase = 'player_count'
                return None
                
            current_setup = self.player_setups[self.current_setup_index]
            
            # Check username input
            center_x = self.screen_width // 2
            content_y = (self.screen_height - self.screen_height // 2) // 2
            username_rect = pygame.Rect(center_x - 200, content_y + 120, 400, 60)  # Bigger input box
            if username_rect.collidepoint(pos):
                current_setup.input_active = True
                if self.debug_mode:
                    print(f"DEBUG: Username input activated for {current_setup.username}")
            else:
                current_setup.input_active = False
            
            # Check color buttons
            for key, button in self.buttons.items():
                if key.startswith('color_') and button['rect'].collidepoint(pos) and button['available']:
                    self.shimmer_effects.add_shimmer(button['rect'])
                    
                    # Free up old color if it was assigned
                    old_color = current_setup.color
                    if old_color and f'color_{old_color}' in self.buttons:
                        self.buttons[f'color_{old_color}']['available'] = True
                        if self.debug_mode:
                            print(f"DEBUG: Freed up color {old_color}")
                    
                    # Assign new color
                    current_setup.color = button['color']
                    button['available'] = False
                    sound_manager.play_charge()
                    if self.debug_mode:
                        print(f"DEBUG: Assigned color {button['color']} to {current_setup.username}")
            
            # Check difficulty buttons (for AI)
            if current_setup.is_ai:
                for key, button in self.buttons.items():
                    if key.startswith('diff_') and button['rect'].collidepoint(pos):
                        self.shimmer_effects.add_shimmer(button['rect'])
                        current_setup.difficulty = button['difficulty']
                        sound_manager.play_sound('move', 0.5)
                        if self.debug_mode:
                            print(f"DEBUG: Set AI difficulty to {button['difficulty']}")
            
            # Check navigation buttons
            if self.buttons['next']['rect'].collidepoint(pos) and self.buttons['next']['enabled']:
                self.shimmer_effects.add_shimmer(self.buttons['next']['rect'])
                if self.current_setup_index < len(self.player_setups) - 1:
                    self.current_setup_index += 1
                    if self.debug_mode:
                        print(f"DEBUG: Advanced to player {self.current_setup_index + 1}")
                else:
                    self.setup_phase = 'ready'
                    self.buttons['start']['enabled'] = True
                    if self.debug_mode:
                        print("DEBUG: Advanced to ready phase")
                sound_manager.play_sound('move', 0.8)
            
            if self.buttons['back']['rect'].collidepoint(pos) and self.current_setup_index > 0:
                self.shimmer_effects.add_shimmer(self.buttons['back']['rect'])
                # When going back, free up the current player's chosen color
                if current_setup.color:
                    self.buttons[f'color_{current_setup.color}']['available'] = True
                    current_setup.color = None
                
                self.current_setup_index -= 1
                sound_manager.play_sound('move', 0.5)
                if self.debug_mode:
                    print(f"DEBUG: Went back to player {self.current_setup_index + 1}")
        
        elif self.setup_phase == 'ready':
            if self.buttons['start']['rect'].collidepoint(pos):
                self.shimmer_effects.add_shimmer(self.buttons['start']['rect'])
                if self.debug_mode:
                    print("DEBUG: Start button clicked!")
                    print("DEBUG: Generating final configuration...")
                    for i, setup in enumerate(self.player_setups):
                        print(f"DEBUG:   Player {i+1}: {setup.username} ({setup.color}) - {'AI' if setup.is_ai else 'Human'}")
                
                sound_manager.play_twinkle()
                return 'start_game'
            
            if self.buttons['back']['rect'].collidepoint(pos):
                self.shimmer_effects.add_shimmer(self.buttons['back']['rect'])
                self.setup_phase = 'player_setup'
                self.current_setup_index = len(self.player_setups) - 1
                sound_manager.play_sound('move', 0.5)
                if self.debug_mode:
                    print("DEBUG: Went back to player setup from ready phase")
        
        return None
    
    def advance_to_player_setup(self):
        """Move to player setup phase"""
        if self.debug_mode:
            print(f"DEBUG: Advancing to player setup - {self.num_human_players} human, {self.num_ai_players} AI")
        
        self.setup_phase = 'player_setup'
        self.player_setups = []
        
        # Reset all color availability
        for key in self.buttons:
            if key.startswith('color_'):
                self.buttons[key]['available'] = True
        
        # Create player setups
        total_players = self.num_human_players + self.num_ai_players
        
        for i in range(total_players):
            is_ai = i >= self.num_human_players
            setup = PlayerSetup(i, is_ai)
            self.player_setups.append(setup)
            
            if self.debug_mode:
                print(f"DEBUG: Created setup for {setup.username} with no color assigned yet.")
        
        self.current_setup_index = 0
        self.buttons['back']['enabled'] = True
        sound_manager.play_twinkle()
        
        if self.debug_mode:
            print("DEBUG: Player setup phase initialized")
    
    def update_twinkles(self, dt):
        """Update magical twinkle particles"""
        self.twinkle_timer += dt
        
        # Add new twinkles
        if self.twinkle_timer > 0.1: # Increased twinkle frequency
            self.twinkle_timer = 0 # Reset timer
            for _ in range(3):  # Increased twinkle frequency
                self.twinkle_particles.append({     # Create new twinkle particle
                    'x': random.randint(1, self.screen_width - 10), # Random position
                    'y': random.randint(1, self.screen_height - 10), # Random position
                    'life': 3.0,    # Increased life span
                    'max_life': 6.0, # Increased max life
                    'size': random.randint(2, 12) # Random size
                })
        
        # Update existing twinkles
        for particle in self.twinkle_particles[:]:
            particle['life'] -= dt
            if particle['life'] <= 0:
                self.twinkle_particles.remove(particle)
    
    def draw(self):
        """Draw the start screen"""
        dt = 1/60  # Assume 60 FPS for animation
        self.update_twinkles(dt)
        self.shimmer_effects.update(dt)
        
        # Clear screen with magical background
        self.screen.fill(self.colors['background'])
        
        # Draw twinkle particles
        for particle in self.twinkle_particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            color = (*self.colors['gold'][:3], alpha)
            size = int(particle['size'] * (particle['life'] / particle['max_life']))
            if size > 0:
                pygame.draw.circle(self.screen, self.colors['gold'], 
                                 (int(particle['x']), int(particle['y'])), size)
        
        # Draw title with magical glow - Bigger and more centered
        title_text = self.font_title.render("Crystal Wizards", True, self.colors['purple'])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 120))  # Moved down slightly
        
        # Enhanced glow effect
        for offset in [(3, 3), (-3, -3), (3, -3), (-3, 3), (0, 3), (0, -3), (3, 0), (-3, 0)]:
            glow_text = self.font_title.render("Crystal Wizards", True, self.colors['gold'])
            glow_rect = glow_text.get_rect(center=(title_rect.centerx + offset[0], title_rect.centery + offset[1]))
            self.screen.blit(glow_text, glow_rect)
        
        self.screen.blit(title_text, title_rect)
        
        # Draw phase-specific content
        if self.setup_phase == 'player_count':
            self.draw_player_count_phase()
        elif self.setup_phase == 'player_setup':
            self.draw_player_setup_phase()
        elif self.setup_phase == 'ready':
            self.draw_ready_phase()
        
        # Draw shimmer effects on top
        self.shimmer_effects.draw(self.screen, self.colors)
        
        pygame.display.flip()
    
    def draw_player_count_phase(self):
        """Draw player count selection - Bigger and centered"""
        subtitle = self.font_large.render("Choose Player Configuration", True, self.colors['white'])
        subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Draw config buttons
        for key, button in self.buttons.items():
            if key.startswith('config_'):
                color = self.colors['gold'] if button['selected'] else self.colors['light_grey']
                pygame.draw.rect(self.screen, color, button['rect'], border_radius=12)
                pygame.draw.rect(self.screen, self.colors['white'], button['rect'], 3, border_radius=12)
                
                text = self.font_medium.render(button['text'], True, self.colors['black'])
                text_rect = text.get_rect(center=button['rect'].center)
                self.screen.blit(text, text_rect)
        
        # Draw next button
        self.draw_button('next')
        
        # Draw instructions - Bigger text and better positioned
        instructions = [
            "Select how many human players and AI opponents you want.",
            "Each game needs 2-4 total players for the best experience.",
            "AI opponents will provide challenging strategic gameplay!"
        ]
        
        content_y = (self.screen_height - self.screen_height // 2) // 2
        y_offset = content_y + 400
        for instruction in instructions:
            text = self.font_small.render(instruction, True, self.colors['white'])
            text_rect = text.get_rect(center=(self.screen_width // 2, y_offset+ 150))
            self.screen.blit(text, text_rect)
            y_offset += 30
    
    def draw_player_setup_phase(self):
        """Draw individual player setup - Bigger and centered"""
        # Safety check
        if not self.player_setups or self.current_setup_index >= len(self.player_setups):
            if self.debug_mode:
                print("DEBUG: Invalid player setup state, falling back to player_count")
            self.setup_phase = 'player_count'
            return
            
        current_setup = self.player_setups[self.current_setup_index]
        center_x = self.screen_width // 2
        content_y = (self.screen_height - self.screen_height // 2) // 2
        
        # Progress indicator
        progress_text = f"Setting up Player {self.current_setup_index + 1} of {len(self.player_setups)}"
        progress = self.font_large.render(progress_text, True, self.colors['white'])
        progress_rect = progress.get_rect(center=(center_x, 220))
        self.screen.blit(progress, progress_rect)
        
        # Player type
        player_type = "AI Player" if current_setup.is_ai else "Human Player"
        type_text = self.font_medium.render(player_type, True, self.colors['purple'])
        type_rect = type_text.get_rect(center=(center_x, 270))
        self.screen.blit(type_text, type_rect)
        
        # Username input - Bigger and centered
        username_label = self.font_medium.render("Username:", True, self.colors['white'])
        label_rect = username_label.get_rect(center=(center_x, content_y + 80))
        self.screen.blit(username_label, label_rect)
        
        username_rect = pygame.Rect(center_x - 200, content_y + 120, 400, 60)
        color = self.colors['white'] if current_setup.input_active else self.colors['light_grey']
        pygame.draw.rect(self.screen, color, username_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.colors['gold'], username_rect, 3, border_radius=8)
        
        username_text = self.font_medium.render(current_setup.username, True, self.colors['black'])
        text_x = username_rect.x + 15
        text_y = username_rect.y + (username_rect.height - username_text.get_height()) // 2
        self.screen.blit(username_text, (text_x, text_y))
        
        if current_setup.input_active:
            # Draw cursor
            cursor_x = text_x + username_text.get_width()
            pygame.draw.line(self.screen, self.colors['black'], 
                           (cursor_x, username_rect.y + 10), (cursor_x, username_rect.bottom - 10), 3)
        
        # Color selection - Centered
        color_label = self.font_medium.render("Choose Color:", True, self.colors['white'])
        color_label_rect = color_label.get_rect(center=(center_x, content_y + 300))
        self.screen.blit(color_label, color_label_rect)
        
        for key, button in self.buttons.items():
            if key.startswith('color_'):
                color = self.colors[button['color']]
                if not button['available'] and button['color'] != current_setup.color:
                    color = self.colors['grey']
                
                pygame.draw.rect(self.screen, color, button['rect'], border_radius=12)
                
                # Highlight selected color
                if button['color'] == current_setup.color:
                    pygame.draw.rect(self.screen, self.colors['gold'], button['rect'], 5, border_radius=12)
                else:
                    pygame.draw.rect(self.screen, self.colors['white'], button['rect'], 3, border_radius=12)
        
        # AI difficulty selection - Centered
        if current_setup.is_ai:
            diff_label = self.font_medium.render("AI Difficulty:", True, self.colors['white'])
            diff_label_rect = diff_label.get_rect(center=(center_x, content_y + 400))
            self.screen.blit(diff_label, diff_label_rect)
            
            for key, button in self.buttons.items():
                if key.startswith('diff_'):
                    color = self.colors['gold'] if button['difficulty'] == current_setup.difficulty else self.colors['light_grey']
                    pygame.draw.rect(self.screen, color, button['rect'], border_radius=8)
                    pygame.draw.rect(self.screen, self.colors['white'], button['rect'], 3, border_radius=8)
                    
                    text = self.font_small.render(button['text'], True, self.colors['black'])
                    text_rect = text.get_rect(center=button['rect'].center)
                    self.screen.blit(text, text_rect)
        
        # Navigation buttons
        self.draw_button('back')
        next_text = "Next" if self.current_setup_index < len(self.player_setups) - 1 else "Finish"
        self.buttons['next']['text'] = next_text
        
        # Enable the 'next' button only if a color has been chosen
        self.buttons['next']['enabled'] = current_setup.color is not None
        
        self.draw_button('next')
    
    def draw_ready_phase(self):
        """Draw final ready screen - Bigger and centered"""
        center_x = self.screen_width // 2
        
        ready_text = self.font_large.render("Ready to Play!", True, self.colors['green'])
        ready_rect = ready_text.get_rect(center=(center_x, 250))
        self.screen.blit(ready_text, ready_rect)
        
        # Show player summary - Bigger text
        y_offset = 320
        for i, setup in enumerate(self.player_setups):
            player_info = f"{setup.username} ({setup.color.title()}"
            if setup.is_ai:
                player_info += f" AI - {setup.difficulty.title()}"
            player_info += ")"
            
            color = self.colors[setup.color] if setup.color else self.colors['white']
            text = self.font_medium.render(player_info, True, color)
            text_rect = text.get_rect(center=(center_x, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 50
        
        # Draw buttons
        self.draw_button('back')
        self.draw_button('start')
    
    def draw_button(self, button_key):
        """Draw a button with enhanced styling"""
        if button_key not in self.buttons:
            return
        
        button = self.buttons[button_key]
        enabled = button.get('enabled', True)
        
        if button_key == 'start':
            color = self.colors['green'] if enabled else self.colors['grey']
            border_color = self.colors['gold']
        else:
            color = self.colors['light_grey'] if enabled else self.colors['grey']
            border_color = self.colors['white']
        
        pygame.draw.rect(self.screen, color, button['rect'], border_radius=12)
        pygame.draw.rect(self.screen, border_color, button['rect'], 4, border_radius=12)
        
        text_color = self.colors['black'] if enabled else self.colors['dark_grey']
        text = self.font_medium.render(button['text'], True, text_color)
        text_rect = text.get_rect(center=button['rect'].center)
        self.screen.blit(text, text_rect)
    
    def run(self):
        """Run the enhanced start screen"""
        clock = pygame.time.Clock()
        
        if self.debug_mode:
            print("DEBUG: Start screen running...")
        
        while True:
            result = self.handle_events()
            
            if result == 'quit':
                if self.debug_mode:
                    print("DEBUG: Returning None (quit)")
                return None
            elif result == 'start_game':
                # Prepare game configuration
                config = {
                    'players': [],
                    'num_human_players': self.num_human_players,
                    'num_ai_players': self.num_ai_players
                }
                
                for setup in self.player_setups:
                    # Validate that each player has a color
                    if not setup.color:
                        if self.debug_mode:
                            print(f"DEBUG: ERROR - {setup.username} has no color assigned!")
                        # This fallback should not be reached with the new UI validation, but is kept for safety
                        available_colors = ['red', 'blue', 'green', 'yellow']
                        for color in available_colors:
                            if f'color_{color}' in self.buttons and self.buttons[f'color_{color}']['available']:
                                setup.color = color
                                self.buttons[f'color_{color}']['available'] = False
                                break
                        if not setup.color:
                            setup.color = 'red'  # Ultimate fallback
                    
                    player_config = {
                        'username': setup.username,
                        'color': setup.color,
                        'is_ai': setup.is_ai,
                        'difficulty': setup.difficulty if setup.is_ai else None
                    }
                    config['players'].append(player_config)
                
                if self.debug_mode:
                    print("DEBUG: Final configuration generated:")
                    for i, player_config in enumerate(config['players']):
                        print(f"DEBUG:   Player {i+1}: {player_config}")
                
                return config
            
            self.draw()
            clock.tick(60)

# Test function for standalone running
def main():
    """Main function for testing the start screen"""
    pygame.init()
    
    start_screen = StartScreen()
    config = start_screen.run()
    
    if config:
        print("Start screen completed with configuration:")
        for i, player_config in enumerate(config['players']):
            player_type = "AI" if player_config['is_ai'] else "Human"
            difficulty = f" ({player_config['difficulty']})" if player_config['is_ai'] else ""
            print(f"  Player {i+1}: {player_config['username']} ({player_config['color']}) - {player_type}{difficulty}")
    else:
        print("Start screen was cancelled")
    
    pygame.quit()

if __name__ == "__main__":
    main()