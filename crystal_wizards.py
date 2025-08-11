"""
Crystal Wizards - Main Game File
A strategic board game where wizards collect crystals and cast spells to eliminate opponents.
"""

import pygame
import sys
from cw_game import CrystalWizardsGame
from cw_gui import GameGUI
from start_screen import StartScreen

def main():
    # Initialize pygame
    pygame.init()
    
    # Show start screen
    start_screen = StartScreen()
    config = start_screen.run()

    if config is None:
        #user quit
        pygame.quit()
        return
    
    num_human_players = config['num_human_players']
    num_ai_players = config['num_ai_players']
    
    # Create and run the game
    try:
        game = CrystalWizardsGame(num_players=num_human_players, num_ai=num_ai_players, players_config=config.get('players'))
        gui = GameGUI(game)
        gui.run()
    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()
    finally:
            pygame.quit()
            sys.exit(0)

    

if __name__ == "__main__":
    main()