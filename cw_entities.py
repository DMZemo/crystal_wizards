
"""
Crystal Wizards - Game Entities (Wizards, Spells, etc.)
"""

import random
import pygame

class Wizard:
    ''' A wizards starting location is the rectangle that matchs their color.'''

    def __init__(self, color, health=6):
        self.color = color
        self.health = health
        self.max_health = 6
        self.crystals = {'red': 0, 'blue': 0, 'green': 0, 'yellow': 0, 'white': 0}
        self.max_crystals = 6
        self.location = None
        self.hand = []  # Spell cards in hand (hidden)
        self.cards_laid_down = []  # Spell cards laid down (visible, being charged)
        self.max_hand_size = 3
        
        # Crystal blocking highlight animation
        self.is_blocking_highlighted = False
        self.blocking_highlight_timer = 0

        # set starting location, based on color, start on rectangle that matches color
        self.starting_location = {
            'red': (0, 0),
            'blue': (1, 0),
            'green': (0, 1),
            'yellow': (1, 1),
        }.get(color, (0, 0))
        
        
        
    def add_crystals(self, color, amount):
        """Add crystals to the wizard's reserve, respecting max capacity"""
        current_total = sum(self.crystals.values())
        space_available = self.max_crystals - current_total
        amount_to_add = min(amount, space_available)
        
        if amount_to_add > 0:
            self.crystals[color] += amount_to_add
        
        return amount_to_add

    
    def remove_crystals(self, color, amount):
        """Remove crystals from the wizard's reserve"""
        amount_to_remove = min(amount, self.crystals[color])
        self.crystals[color] -= amount_to_remove
        return amount_to_remove
    
    def can_hold_more_crystals(self):
        """Check if wizard can hold more crystals"""
        return sum(self.crystals.values()) < self.max_crystals

    def get_total_crystals_for_blocking(self):
        """Get total crystals available for blocking (including white crystals as wildcards)"""
        return sum(self.crystals.values())

    def can_block_damage(self):
        """Check if wizard has any crystals available for blocking"""
        return self.get_total_crystals_for_blocking() > 0

    def _spend_crystals_normal_priority(self, crystals_spent, remaining_to_spend):
        """Helper method to spend crystals in normal priority order"""
        # First spend colored crystals (non-white)
        for color in ['red', 'blue', 'green', 'yellow']:
            if remaining_to_spend <= 0:
                break
            available = self.crystals[color]
            to_spend = min(remaining_to_spend, available)
            if to_spend > 0:
                self.crystals[color] -= to_spend
                crystals_spent[color] = to_spend
                remaining_to_spend -= to_spend
        
        # Then spend white crystals if needed
        if remaining_to_spend > 0:
            available = self.crystals['white']
            to_spend = min(remaining_to_spend, available)
            if to_spend > 0:
                self.crystals['white'] -= to_spend
                crystals_spent['white'] = to_spend
                remaining_to_spend -= to_spend
        
        return remaining_to_spend

    def spend_crystals_for_blocking(self, amount, game=None, attacker=None):
        """
        Spends crystals to block damage.
        Crystals are sent back to the board after blocking.
        """
        if amount <= 0:
            return 0
        
        crystals_to_spend = min(amount, self.get_total_crystals_for_blocking())
        remaining_to_spend = crystals_to_spend
        crystals_spent = {'red': 0, 'blue': 0, 'green': 0, 'yellow': 0, 'white': 0}
        
        # Use normal priority for all players - spend crystals in standard order
        remaining_to_spend = self._spend_crystals_normal_priority(crystals_spent, remaining_to_spend)
        
        # All blocking crystals return to board
        if game and crystals_spent:
            crystals_to_return = {color: amount for color, amount in crystals_spent.items() if amount > 0}
            if crystals_to_return:
                game.return_crystals_to_board(crystals_to_return, self.location)
        
        return crystals_to_spend, crystals_spent
    
    def take_damage(self, damage, gui=None, caster=None, game=None):
        """Take damage and reduce health, with optional crystal blocking"""
        if damage <= 0:
            return
            
        actual_damage = damage
        blocked_amount = 0
        
        # Check if wizard can block and has crystals
        if self.can_block_damage():
            from sound_manager import sound_manager
            
            if isinstance(self, AIWizard):
                # AI blocking strategy based on difficulty
                crystals_to_use = self._calculate_ai_blocking_amount(damage, game, caster)
                if crystals_to_use > 0:
                    blocked_amount, crystals_spent = self.spend_crystals_for_blocking(crystals_to_use, game, caster) # type: ignore
                    actual_damage = max(0, damage - blocked_amount)
                    
                    # Play blocking sound and trigger highlight
                    sound_manager.play_twinkle()
                    self._start_blocking_highlight()
                    
            else:
                # Human player - trigger blocking dialog if GUI is available
                if gui is not None:
                    blocked_amount = gui.show_blocking_dialog(self, damage, caster, game)
                    actual_damage = max(0, damage - blocked_amount)
                    
                    if blocked_amount > 0:
                        sound_manager.play_sound('twinkle')
                        self._start_blocking_highlight()
        
        # Apply the final damage
        self.health = max(0, self.health - actual_damage)

    def _calculate_ai_blocking_amount(self, damage, game, attacker=None):
        """Calculate how many crystals AI should use for blocking based on difficulty"""
        if not hasattr(self, 'difficulty'):
            # Default to maximum blocking if no difficulty set
            return min(damage, self.get_total_crystals_for_blocking())
        
        available_crystals = self.get_total_crystals_for_blocking()
        max_blockable = min(damage, available_crystals)
        
        if self.difficulty == 'easy': # type: ignore
            # Easy AI: Random blocking amount (0 to max)
            import random
            return random.randint(0, max_blockable)
        
        elif self.difficulty in ['medium', 'hard']: # type: ignore
            # Medium/Hard AI: Strategic blocking
            
            # Calculate crystals needed for spells in hand and laid down
            crystals_needed_for_spells = 0
            for card in self.hand + self.cards_laid_down:
                if not card.is_fully_charged():
                    # Calculate remaining cost: total cost minus crystals already used
                    remaining_cost = sum(card.cost.values()) - sum(card.crystals_used.values())
                    crystals_needed_for_spells += remaining_cost
            
            # Keep some white crystals as they're versatile
            white_crystals_to_keep = min(2, self.crystals.get('white', 0))
            
            # Calculate how many crystals we can afford to spend
            crystals_to_reserve = crystals_needed_for_spells + white_crystals_to_keep
            crystals_available_for_blocking = max(0, available_crystals - crystals_to_reserve)
            
            # Block as much as possible without compromising spell casting
            return min(damage, crystals_available_for_blocking, max_blockable)
        
        # Fallback to maximum blocking
        return max_blockable

    def _start_blocking_highlight(self):
        """Start visual highlight effect for blocking (brief animation)"""
        # This will be handled by the GUI - we just set a flag
        self.is_blocking_highlighted = True
        self.blocking_highlight_timer = pygame.time.get_ticks()
    
    def heal(self, amount):
        """Heal the wizard up to max health"""
        self.health = min(self.max_health, self.health + amount)
    
    def lay_down_spell_card(self, card_index):
        """Move a spell card from hand to laid down cards"""
        if 0 <= card_index < len(self.hand):
            card = self.hand.pop(card_index)
            self.cards_laid_down.append(card)
            return True
        return False
    
    def charge_spell_card(self, card, crystal_color, amount):
        """Add crystals to a laid down spell card"""
        if card in self.cards_laid_down:
            return card.add_crystals(crystal_color, amount, self)
        return False
    
    def has_charged_spells(self):
        """Check if wizard has any fully charged spells"""
        return any(card.is_fully_charged() for card in self.cards_laid_down)
    
    def get_total_crystals(self):
        """Get total number of crystals held"""
        return sum(self.crystals.values())

class AIWizard(Wizard):
    """AI-controlled wizard with simple strategic behavior"""
    
    def __init__(self, color, health=6, difficulty='easy'):
        super().__init__(color, health)
        self.difficulty = difficulty
        self.ai_controller = None  # Will be set by AIManager

        
    def set_ai_controller(self, ai_controller):
        """Set the AI controller that manages this wizard"""
        self.ai_controller = ai_controller
        
    def execute_turn(self, game):
        """Execute the AI's turn using the strategic AI controller"""
        if self.ai_controller:
            self.ai_controller.execute_turn(game)
        else:
            # Fallback to basic behavior if no controller is set
            self._basic_ai_turn(game)
    
    def _basic_ai_turn(self, game):
        """Basic AI behavior as fallback"""
        # This is the old simple logic as a safety net
        while game.current_actions < game.max_actions_per_turn:
            action_taken = False
            
            # Try to cast spells first
            if game.can_cast_spell(self):
                for spell_card in self.cards_laid_down:
                    if spell_card.is_fully_charged():
                        adjacent_enemies = game.get_adjacent_enemies(self)
                        if adjacent_enemies:
                            game.cast_spell(self, spell_card, gui=game.gui if hasattr(game, 'gui') else None)
                            action_taken = True
                            break
                if action_taken: 
                    continue
            
            # Try to mine
            if game.can_mine(self):
                pos = self.location
                if game.board.has_crystals_at_position(pos) and not game.board.is_mine(pos):
                    game.mine_white_crystal(self, pos)
                    action_taken = True
                elif game.board.is_mine(pos) and self.get_total_crystals() < 5:
                    roll = random.randint(1, 6)
                    game.resolve_mine_with_roll(self, pos, roll)
                    action_taken = True
                if action_taken:
                    continue
            
            # Try to move
            if game.can_move(self):
                target_position = self._get_simple_move_target(game)
                if target_position:
                    game.move_player(self, target_position)
                    action_taken = True
            
            if not action_taken:
                break
    
    def _get_simple_move_target(self, game):
        """Simple movement logic for fallback AI"""
        current_pos = self.location
        adjacent_positions = game.board.get_adjacent_positions(current_pos)
        
        best_target = None
        best_score = -1
        
        for pos in adjacent_positions:
            score = 0
            
            if game.board.has_crystals_at_position(pos):
                score += 10
            
            # No longer seeking healing springs - center is now a white mine
            
            adjacent_enemies = len(game.get_adjacent_enemies_at_position(pos, self))
            if adjacent_enemies > 0 and self.has_charged_spells():
                score += 15 * adjacent_enemies
            
            if score > best_score:
                best_score = score
                best_target = pos
        
        return best_target



class SpellCard:
    def __init__(self, cost_dict):
        self.cost = cost_dict.copy()
        self.crystals_used = {color: 0 for color in cost_dict}
        # Track original crystal types used (for proper return to board)
        self.original_crystals_used = {'white': 0, 'red': 0, 'blue': 0, 'green': 0, 'yellow': 0}
        self.damage = sum(cost_dict.values())

    def get_total_cost(self):
        return sum(self.cost.values())

    def get_damage(self):
        return self.damage

    def add_crystals(self, color, amount, wizard):
        """
        Add crystals to charge this spell.
        'white' crystals can fulfill any specific color requirement.
        'wild' can only be fulfilled by wizard.color or white.
        """
        # --- Handle wild requirements (must match wizard.color or be white) ---
        if color == wizard.color or color == 'white':
            if 'wild' in self.cost and self.crystals_used['wild'] < self.cost['wild']:
                needed = self.cost['wild'] - self.crystals_used['wild']
                to_use = min(amount, needed)
                if wizard.crystals[color] >= to_use:
                    wizard.remove_crystals(color, to_use)
                    self.crystals_used['wild'] += to_use
                    # Track original crystal type used
                    self.original_crystals_used[color] += to_use
                    return True

        # --- Handle standard color requirements ---
        for target_color in self.cost:
            if target_color == 'wild':
                continue
            if self.crystals_used[target_color] >= self.cost[target_color]:
                continue

            needed = self.cost[target_color] - self.crystals_used[target_color]
            to_use = min(amount, needed)

            # Direct match
            if color == target_color and wizard.crystals[color] >= to_use:
                wizard.remove_crystals(color, to_use)
                self.crystals_used[target_color] += to_use
                # Track original crystal type used
                self.original_crystals_used[color] += to_use
                return True

            # Use white crystal as substitute for target color
            if color == 'white' and wizard.crystals['white'] >= to_use:
                wizard.remove_crystals('white', to_use)
                self.crystals_used[target_color] += to_use
                # Track that white crystals were used (this is the key fix!)
                self.original_crystals_used['white'] += to_use
                return True

        return False

    def is_fully_charged(self):
        for color, required in self.cost.items():
            if self.crystals_used.get(color, 0) < required:
                return False
        return True

    def get_charging_progress(self):
        total_needed = sum(self.cost.values())
        total_used = sum(self.crystals_used.values())
        return total_used / total_needed if total_needed > 0 else 1.0


class SpellCardDeck:
    def __init__(self):
        self.cards = []
        self.discarded = []
    
    def initialize_deck(self):
        """Create the standard spell card deck with wild instead of white"""
        # 32 spell cards total
        
        # 2-damage spells (cost 2: 1 color + 1 wildcard)
        for _ in range(2):  # 2 cards of each color
            self.cards.append(SpellCard({'red': 1, 'wild': 1}))
            self.cards.append(SpellCard({'blue': 1, 'wild': 1}))
            self.cards.append(SpellCard({'green': 1, 'wild': 1}))
            self.cards.append(SpellCard({'yellow': 1, 'wild': 1}))

        # 3-damage spells (cost 3: 2 colors + 1 wildcard)
        for _ in range(2): # 2 cards of each color combination
            self.cards.append(SpellCard({'red': 1, 'blue': 1, 'wild': 1}))
            self.cards.append(SpellCard({'red': 1, 'green': 1, 'wild': 1}))
            self.cards.append(SpellCard({'red': 1, 'yellow': 1, 'wild': 1}))
            self.cards.append(SpellCard({'blue': 1, 'green': 1, 'wild': 1}))
            self.cards.append(SpellCard({'blue': 1, 'yellow': 1, 'wild': 1}))
            self.cards.append(SpellCard({'green': 1, 'yellow': 1, 'wild': 1}))

        # 4-damage spells (cost 4: 3 colors + 1 wildcard)
        for _ in range(2): # 2 card of each color combination
            self.cards.append(SpellCard({'red': 1, 'blue': 1, 'green': 1, 'wild': 1}))
            self.cards.append(SpellCard({'red': 1, 'blue': 1, 'yellow': 1, 'wild': 1}))
            self.cards.append(SpellCard({'red': 1, 'green': 1, 'yellow': 1, 'wild': 1}))
            self.cards.append(SpellCard({'blue': 1, 'green': 1, 'yellow': 1, 'wild': 1}))

        # 5-damage spells (cost 5: all 4 colors + 1 wildcard)
        for _ in range(4): # 4 cards of each color combination
            self.cards.append(SpellCard({'red': 1, 'blue': 1, 'green': 1, 'yellow': 1, 'wild': 1}))

        
    
    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)
    
    def draw_card(self):
        """Draw a card from the deck"""
        if not self.cards and self.discarded:
            # Reshuffle discarded cards back into deck
            self.cards = self.discarded.copy()
            self.discarded.clear()
            self.shuffle()
        
        if self.cards:
            return self.cards.pop()
        return None
    
    def discard_card(self, card):
        """Add a card to the discard pile"""
        self.discarded.append(card)

class Crystal:
    """Represents a crystal of a specific color, if it is white it ought to count as one of any colors."""
    def __init__(self, color):
        self.color = color
        if color == 'white':
            self.colors = ['red', 'blue', 'green', 'yellow', 'white']
        else:
            self.colors = [color]

class Die:
    @staticmethod
    def roll():
        """Roll a standard d6"""
        return random.randint(1, 6)

class HealingHotSpringsDie:
    @staticmethod
    def roll():
        """Roll the special white mine die (1-3, weighted toward higher values)"""
        return random.choice([3, 2, 2, 1, 1, 1])
