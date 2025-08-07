
"""
Crystal Wizards - Main Game File
A strategic board game where wizards collect crystals and cast spells to eliminate opponents.
"""

import pygame
import sys
import argparse
from cw_game import CrystalWizardsGame
from cw_gui import GameGUI
from start_screen import StartScreen

def main():
    parser = argparse.ArgumentParser(description='Crystal Wizards Board Game')
    parser.add_argument('--test', action='store_true', help='Run headless test mode')
    parser.add_argument('--players', type=int, default=None, choices=[0,1,2,3,4], help='Number of human players (0-4)')
    parser.add_argument('--ai', type=int, default=None, choices=[0,1,2,3,4], help='Number of AI players (0-4)')
    parser.add_argument('--skip-start', action='store_true', help='Skip start screen and use command line args')
    args = parser.parse_args()
    
    if args.test:
        # Quick headless test
        print("Running Crystal Wizards test mode...")
        game = CrystalWizardsGame(num_players=2, num_ai=0)
        game.initialize_game()
        
        # Test board connectivity
        print("Testing board connectivity...")
        if game.board.is_fully_connected():
            print("✓ Board is fully connected")
        else:
            print("✗ Board connectivity issues detected")
            
        # Test mine positions
        print("Testing mine positions...")
        mine_positions = game.board.mine_spaces
        print(f"Mine positions: {mine_positions}")
        
        for mine_pos in mine_positions:
            adjacent = game.board.get_adjacent_positions(mine_pos)
            print(f"  {mine_pos} connects to: {adjacent}")
            
        # Test a few turns
        for turn in range(3):
            print(f"\nTurn {turn + 1}")
            current_player = game.get_current_player()
            print(f"Current player: {current_player.color} wizard")
            print(f"Health: {current_player.health}, Crystals: {current_player.crystals}")
            print(f"Location: {current_player.location}")
            
            # Test basic actions
            if game.can_move(current_player):
                print("Player can move")
            if game.can_mine(current_player):
                print("Player can mine")
                # Test mining if at a mine position
                if game.board.is_mine(current_player.location):
                    print(f"Player is at mine: {current_player.location}")
            if game.can_cast_spell(current_player):
                print("Player can cast spell")
            
            game.end_turn()
        
        print("Test completed successfully!")
        return
    
    # Initialize pygame
    pygame.init()
    
    # Determine game configuration
    if args.skip_start and args.players is not None and args.ai is not None:
        # Use command line arguments
        num_human_players = args.players
        num_ai_players = args.ai
        
        # Validate configuration
        total_players = num_human_players + num_ai_players
        if total_players < 2 or total_players > 4:
            print("Error: Total players (human + AI) must be between 2 and 4")
            return
    else:
        # Show start screen
        start_screen = StartScreen()
        config = start_screen.run()
        
        if config is None:
            # User quit
            pygame.quit()
            return
            
        num_human_players = config['num_human_players']
        num_ai_players = config['num_ai_players']
    
    # Create and run the game
    try:
        game = CrystalWizardsGame(num_players=num_human_players, num_ai=num_ai_players)
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
