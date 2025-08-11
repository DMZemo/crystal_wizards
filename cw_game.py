"""
Crystal Wizards - Core Game Logic
CORRECTED VERSION - Compatible with multi-wizard tile logic
"""

import random
import collections
from cw_entities import Wizard, AIWizard, SpellCard, SpellCardDeck, Crystal
from cw_board import GameBoard
from cw_ai import AIManager

class CrystalWizardsGame:
    def __init__(self, num_players=2, num_ai=0, players_config=None):
        # If a players_config is provided from the start screen, prefer that
        self.players_config = players_config
        if players_config:
            # Derive counts from config to stay consistent
            self.num_players = sum(1 for p in players_config if not p.get('is_ai'))
            self.num_ai = sum(1 for p in players_config if p.get('is_ai'))
        else:
            self.num_players = num_players
            self.num_ai = num_ai
        self.total_players = self.num_players + self.num_ai
        
        self.board = GameBoard()
        self.players = []
        
        self.current_player_index = 0
        self.current_actions = 0
        self.max_actions_per_turn = 3
        self.spell_deck = SpellCardDeck()
        self.game_over = False
        self.winner = None
        
        # Action counters for current turn
        self.moves_used = 0
        self.mines_used = 0
        self.spells_cast = 0
        
        # FIXED: Add an action log for the ticker tape
        self.action_log = collections.deque(maxlen=20)
        
    def initialize_game(self):
        """Initialize the game with players and board setup"""
        
        # If we have a players_config from the start screen, use that to construct players in order
        if self.players_config:
            for p in self.players_config:
                color = p.get('color')
                name = p.get('username')
                is_ai = p.get('is_ai')
                if is_ai:
                    difficulty = p.get('difficulty', 'easy')
                    player = AIWizard(color, health=6, difficulty=difficulty)
                    # Set up the AI controller based on difficulty
                    ai_controller = AIManager.create_ai(player, difficulty)
                    player.set_ai_controller(ai_controller)
                else:
                    player = Wizard(color, health=6)
                # If Wizard supports a name attribute, set it
                try:
                    player.name = name
                except Exception:
                    pass
                self.players.append(player)
        else:
            # Fallback behavior: use default color order
            colors = ['red', 'blue', 'green', 'yellow']
            # Create human players
            for i in range(self.num_players):
                wizard = Wizard(colors[i], health=6)
                self.players.append(wizard)
            # Create AI players with default medium difficulty
            for i in range(self.num_ai):
                ai_wizard = AIWizard(colors[self.num_players + i], health=6, difficulty='medium')
                ai_controller = AIManager.create_ai(ai_wizard, 'medium')
                ai_wizard.set_ai_controller(ai_controller)
                self.players.append(ai_wizard)
        
        # Initialize board and place wizards
        self.board.initialize_board()
        self.place_wizards_on_board()
        
        # Initialize spell deck
        self.spell_deck.initialize_deck()
        self.spell_deck.shuffle()
        
        # Deal initial spell cards to each player
        for player in self.players:
            for _ in range(3):  # Each player starts with 3 spell cards
                card = self.spell_deck.draw_card()
                if card:
                    player.hand.append(card)
        
        self.action_log.append("The battle for the crystals begins!")
        
    def place_wizards_on_board(self):
        """Place wizards on starting positions on the outer ring"""
        for i, player in enumerate(self.players):
            # Place players on their matching colored rectangle positions
            start_pos = self.board.get_colored_rectangle_position(player.color)
            player.location = start_pos
            # Use add_wizard_to_position to ensure it's always a list
            self.board.add_wizard_to_position(start_pos, player)
        
    def get_current_player(self):
        """Get the currently active player"""
        return self.players[self.current_player_index]
        
    def can_move(self, player):
        """Check if player can move (max 3 moves per turn)"""
        return self.moves_used < 3 and self.current_actions < self.max_actions_per_turn
        
    def can_mine(self, player):
        """Check if player can mine (max 2 mines per turn)"""
        return self.mines_used < 2 and self.current_actions < self.max_actions_per_turn
        
    def can_cast_spell(self, player):
        """Check if player can cast spell (max 1 spell per turn)"""
        return self.spells_cast < 1 and self.current_actions < self.max_actions_per_turn

    def move_player(self, player, target_position):
        """
        FIXED: Move a player to a target position. This logic is now simplified
        and correctly uses the board methods that handle multiple wizards per tile.
        """
        if not self.can_move(player):
            return False
        
        if not self.board.is_adjacent(player.location, target_position):
            return False
        
        old_location = player.location
        
        self.board.remove_wizard_from_position(old_location, player)
        player.location = target_position
        self.board.add_wizard_to_position(target_position, player)
        
        self.moves_used += 1
        self.current_actions += 1
        
        # LOGGING: Log the move action
        self.action_log.append(f"{player.color.title()} Wizard moved to {target_position}.")
        return True
        
    def mine_white_crystal(self, player, position):
        """Perform a mining action on a tile with a white crystal (no dice roll)."""
        if not self.can_mine(player):
            return False
        
        if position in self.board.white_crystals and self.board.white_crystals[position] > 0:
            # Check if player can hold more crystals before removing from board
            if not player.can_hold_more_crystals():
                return "reserve_full"  # Return special value to indicate capacity issue
            
            self.board.white_crystals[position] -= 1
            player.add_crystals('white', 1)
            
            self.mines_used += 1
            self.current_actions += 1
            
            # LOGGING: Log the mining action
            self.action_log.append(f"{player.color.title()} Wizard mined 1 white crystal.")
            return True
        return False

    def resolve_mine_with_roll(self, player, position, roll_result):
        """FIXED: Resolve a mining action using a pre-determined dice roll from the GUI."""
        if not self.can_mine(player):
            return False
        
        # CRYSTAL-MINING-BUG-FIX: Removed restrictive capacity check
        # The board-level logic in resolve_mine_with_roll handles partial collection correctly
        
        mine_result = self.board.resolve_mine_with_roll(position, player, roll_result)
        
        if mine_result:
            crystals_gained, teleport_position = mine_result
            
            # LOGGING: Log healing and crystal gains
            if position == 'center':
                self.action_log.append(f"{player.color.title()} healed for {roll_result} HP at the Springs.")
            if crystals_gained:
                for color, amount in crystals_gained.items():
                    self.action_log.append(f"{player.color.title()} mined {amount} {color} crystal(s).")
            
            # Add crystals to player's reserve
            for color, amount in crystals_gained.items():
                player.add_crystals(color, amount)
            
            # Handle teleportation if applicable
            if teleport_position:
                self.action_log.append(f"{player.color.title()} was teleported to {teleport_position}.")
                old_location = player.location
                self.board.remove_wizard_from_position(old_location, player)
                player.location = teleport_position
                self.board.add_wizard_to_position(teleport_position, player)
            
            self.mines_used += 1
            self.current_actions += 1
            return True
        else:
            # LOGGING a failed mine attempt
            self.action_log.append(f"{player.color.title()} tried to mine, but failed.")
            self.mines_used += 1
            self.current_actions += 1
            return False
        
    def cast_spell(self, player, spell_card, gui=None):
        """Cast a spell using the specified spell card"""
        if not self.can_cast_spell(player):
            return False
        if spell_card not in player.cards_laid_down or not spell_card.is_fully_charged():
            return False
        
        adjacent_positions = self.board.get_adjacent_positions(player.location)
        targets = []
        
        for pos in adjacent_positions:
            wizards_at_pos = self.board.get_wizard_at_position(pos)
            if wizards_at_pos:
                for target_wizard in wizards_at_pos:
                    if target_wizard != player:
                        targets.append(target_wizard)
        
        damage = spell_card.get_damage()
        
        # LOGGING for the spell casting action
        self.action_log.append(f"{player.color.title()} cast a {damage}-damage spell!")
        
        if not targets:
            self.action_log.append("...but no one was in range!")

        for target in targets:
            target.take_damage(damage, gui=gui, caster=player)
            self.action_log.append(f"{target.color.title()} Wizard took {damage} damage.")
            if target.health <= 0:
                self.eliminate_player(target)
        
        self.return_crystals_to_board(spell_card.crystals_used)
        player.cards_laid_down.remove(spell_card)
        
        new_card = self.spell_deck.draw_card()
        if new_card:
            player.hand.append(new_card)
        
        self.spells_cast += 1
        self.current_actions += 1
        
        self.check_game_over()
        return True
        
    def eliminate_player(self, player):
        """Remove a player from the game"""
        # LOGGING for player elimination
        self.action_log.append(f"{player.color.title()} Wizard has been eliminated!")
        
        self.board.remove_wizard_from_position(player.location, player)
        
        if player in self.players:
            player_index = self.players.index(player)
            self.players.remove(player)
            
            if player_index < self.current_player_index:
                self.current_player_index -= 1
            elif self.current_player_index >= len(self.players) and len(self.players) > 0:
                self.current_player_index = 0

    def return_crystals_to_board(self, crystals_used):
        """Return used crystals back to the board"""
        for color, amount in crystals_used.items():
            if color in ['red', 'blue', 'green', 'yellow']:
                self.board.mines[color]['crystals'] = min(9, self.board.mines[color]['crystals'] + amount)
            elif color == 'white':
                self.board.add_white_crystals_to_empty_tiles(amount)
        
    def end_turn(self):
        """End the current player's turn and move to next player"""
        current_player_name = self.get_current_player().color.title()
        
        self.current_actions = 0
        self.moves_used = 0
        self.mines_used = 0
        self.spells_cast = 0
        
        if len(self.players) > 0:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # LOGGING-FIX
        next_player_name = self.get_current_player().color.title()
        self.action_log.append(f"--- {current_player_name}'s turn ends. {next_player_name}'s turn begins. ---")
        
    def execute_ai_turn(self, ai_player):
        """Execute AI player's turn using the new strategic AI system"""
        if isinstance(ai_player, AIWizard):
            ai_player.execute_turn(self)
        else:
            # Fallback for non-AI players (should not happen)
            return
    def get_adjacent_enemies(self, player):
        """Get list of enemy wizards adjacent to the player"""
        adjacent_positions = self.board.get_adjacent_positions(player.location)
        enemies = []
        for pos in adjacent_positions:
            wizards_at_pos = self.board.get_wizard_at_position(pos)
            if wizards_at_pos:
                for wizard in wizards_at_pos:
                    if wizard != player:
                        enemies.append(wizard)
        return enemies
        

        

        

        
    def get_adjacent_enemies_at_position(self, position, player):
        """Get enemies that would be adjacent if player moved to position"""
        adjacent_positions = self.board.get_adjacent_positions(position)
        enemies = []
        for pos in adjacent_positions:
            wizards_at_pos = self.board.get_wizard_at_position(pos)
            if wizards_at_pos:
                for wizard in wizards_at_pos:
                    if wizard != player:
                        enemies.append(wizard)
        return enemies
        
    def check_game_over(self):
        """Check if the game is over (only one player remaining)"""
        if len(self.players) <= 1:
            self.game_over = True
            self.winner = self.players[0] if self.players else None
            if self.winner:
                self.action_log.append(f"GAME OVER! {self.winner.color.title()} Wizard is victorious!")
        
    def get_game_state(self):
        """Get current game state for GUI display"""
        return {
            'board': self.board,
            'players': self.players,
            'current_player': self.get_current_player(),
            'current_actions': self.current_actions,
            'max_actions': self.max_actions_per_turn,
            'moves_used': self.moves_used,
            'mines_used': self.mines_used,
            'spells_cast': self.spells_cast,
            'game_over': self.game_over,
            'winner': self.winner,
            'action_log': self.action_log
        }
        
    def get_winner(self):
        """Get the winner of the game.
        
        Returns:
            Wizard object: The winning player if game is over and there's a winner
            None: If the game is not over or there's no winner
        """
        return self.winner