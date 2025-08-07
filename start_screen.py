
"""
Crystal Wizards - Start Screen Implementation
"""

import pygame
import sys
from ui import Button

class StartScreen:
    """Start screen for selecting game configuration"""
    
    def __init__(self, screen_width=1200, screen_height=900):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Crystal Wizards - Game Setup")
        
        # Fonts
        pygame.font.init()
        self.font_title = pygame.font.Font(None, 64)
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        
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
            'gold': (255, 215, 0)
        }
        
        # Game configuration
        self.num_human_players = 1
        self.num_ai_players = 1
        self.selected_config = None
        
        # Create buttons
        self.create_buttons()
        
    def create_buttons(self):
        """Create all UI buttons"""
        button_width = 200
        button_height = 50
        button_spacing = 20
        
        center_x = self.screen_width // 2
        start_y = 300
        
        # Preset game mode buttons
        self.buttons = []
        
        # 1 Player vs 3 AI
        self.btn_1p_vs_3ai = Button(
            center_x - button_width // 2, start_y,
            button_width, button_height,
            "1 Player vs 3 AI", self.font_medium,
            normal_color=self.colors['light_grey']
        )
        self.buttons.append(('1p_3ai', self.btn_1p_vs_3ai))
        
        # 2 Players vs 2 AI  
        self.btn_2p_vs_2ai = Button(
            center_x - button_width // 2, start_y + (button_height + button_spacing),
            button_width, button_height,
            "2 Players vs 2 AI", self.font_medium,
            normal_color=self.colors['light_grey']
        )
        self.buttons.append(('2p_2ai', self.btn_2p_vs_2ai))
        
        # 3 Players vs 1 AI
        self.btn_3p_vs_1ai = Button(
            center_x - button_width // 2, start_y + 2 * (button_height + button_spacing),
            button_width, button_height,
            "3 Players vs 1 AI", self.font_medium,
            normal_color=self.colors['light_grey']
        )
        self.buttons.append(('3p_1ai', self.btn_3p_vs_1ai))
        
        # 4 Players (no AI)
        self.btn_4p_no_ai = Button(
            center_x - button_width // 2, start_y + 3 * (button_height + button_spacing),
            button_width, button_height,
            "4 Players (No AI)", self.font_medium,
            normal_color=self.colors['light_grey']
        )
        self.buttons.append(('4p_0ai', self.btn_4p_no_ai))
        
        # AI only (for testing)
        self.btn_ai_only = Button(
            center_x - button_width // 2, start_y + 4 * (button_height + button_spacing),
            button_width, button_height,
            "4 AI Only (Demo)", self.font_medium,
            normal_color=self.colors['gold']
        )
        self.buttons.append(('0p_4ai', self.btn_ai_only))
        
        # Start game button
        self.btn_start = Button(
            center_x - button_width // 2, start_y + 6 * (button_height + button_spacing),
            button_width, button_height,
            "Start Game", self.font_large,
            normal_color=self.colors['green'],
            hover_color=(100, 255, 100)
        )
        self.btn_start.enabled = False  # Disabled until config selected
        
        # Exit button
        self.btn_exit = Button(
            center_x - button_width // 2, start_y + 7 * (button_height + button_spacing),
            button_width, button_height,
            "Exit", self.font_medium,
            normal_color=self.colors['red'],
            hover_color=(255, 100, 100)
        )
        
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'quit'
            
            # Handle button clicks
            for config_name, button in self.buttons:
                if button.handle_event(event):
                    self.selected_config = config_name
                    self.btn_start.enabled = True
                    
                    # Update player counts based on selection
                    if config_name == '1p_3ai':
                        self.num_human_players, self.num_ai_players = 1, 3
                    elif config_name == '2p_2ai':
                        self.num_human_players, self.num_ai_players = 2, 2
                    elif config_name == '3p_1ai':
                        self.num_human_players, self.num_ai_players = 3, 1
                    elif config_name == '4p_0ai':
                        self.num_human_players, self.num_ai_players = 4, 0
                    elif config_name == '0p_4ai':
                        self.num_human_players, self.num_ai_players = 0, 4
                    
                    break
            
            # Handle start button
            if self.btn_start.handle_event(event):
                return 'start_game'
                
            # Handle exit button  
            if self.btn_exit.handle_event(event):
                return 'quit'
                
        return None
        
    def draw(self):
        """Draw the start screen"""
        # Clear screen
        self.screen.fill(self.colors['white'])
        
        # Draw title
        title_text = self.font_title.render("Crystal Wizards", True, self.colors['black'])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.font_large.render("Select Game Configuration", True, self.colors['dark_grey'])
        subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw instructions
        instruction_lines = [
            "Choose the number of human players and AI opponents.",
            "Each game supports 2-4 total players.",
            "Crystal Wizards is a strategic board game where wizards",
            "collect crystals and cast spells to eliminate opponents."
        ]
        
        y_offset = 200
        for line in instruction_lines:
            text = self.font_medium.render(line, True, self.colors['dark_grey'])
            text_rect = text.get_rect(center=(self.screen_width // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 25
            
        # Draw configuration buttons
        for config_name, button in self.buttons:
            button.draw(self.screen)
            
            # Highlight selected configuration
            if config_name == self.selected_config:
                pygame.draw.rect(self.screen, self.colors['blue'], button.rect, 3)
        
        # Draw start and exit buttons
        self.btn_start.draw(self.screen)
        self.btn_exit.draw(self.screen)
        
        # Draw selected configuration info
        if self.selected_config:
            config_text = f"Selected: {self.num_human_players} Human, {self.num_ai_players} AI"
            text = self.font_medium.render(config_text, True, self.colors['blue'])
            text_rect = text.get_rect(center=(self.screen_width // 2, 650))
            self.screen.blit(text, text_rect)
            
        pygame.display.flip()
        
    def run(self):
        """Run the start screen and return selected configuration"""
        clock = pygame.time.Clock()
        
        while True:
            result = self.handle_events()
            
            if result == 'quit':
                return None
            elif result == 'start_game':
                return {
                    'num_human_players': self.num_human_players,
                    'num_ai_players': self.num_ai_players
                }
                
            self.draw()
            clock.tick(60)
