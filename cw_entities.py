
"""
Crystal Wizards - Game Entities (Wizards, Spells, etc.)
"""

import random

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
    
    def take_damage(self, damage):
        """Take damage and reduce health"""
        self.health = max(0, self.health - damage)
    
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
    
    def __init__(self, color, health=6):
        super().__init__(color, health)
        self.strategy = 'balanced'  # Could be 'aggressive', 'defensive', 'balanced'

    
    def should_lay_down_card(self):
        """Determine if AI should lay down a spell card"""
        # Lay down cards if we have crystals to charge them
        total_crystals = self.get_total_crystals()
        return total_crystals >= 2 and len(self.cards_laid_down) < 2
    
    def choose_card_to_lay_down(self):
        """Choose which card to lay down from hand"""
        if not self.hand:
            return None
        
        # Prefer lower cost cards that we can afford
        affordable_cards = []
        for card in self.hand:
            if self.can_afford_card(card):
                affordable_cards.append(card)
        
        if affordable_cards:
            return self.hand.index(min(affordable_cards, key=lambda c: c.get_total_cost()))
        else:
            return 0  # Just lay down first card if none are affordable
    
    def can_afford_card(self, card):
        """Check if AI can afford to charge a spell card"""
        total_cost = card.get_total_cost()
        total_crystals = self.get_total_crystals()
        return total_crystals >= total_cost
    
    def choose_spell_to_cast(self):
        """Choose a spell to cast based on current situation"""
        if not self.cards_laid_down:
            return None
        
        # Prefer casting fully charged spells
        for i, card in enumerate(self.cards_laid_down):
            if card.is_fully_charged():
                return i
    
    def choose_target(self, players):
        """Choose a target player to attack"""
        # Simple strategy: target the player with the lowest health
        target = min(players, key=lambda p: p.health)
        return target if target != self else None
    
    def decide_action(self, players):
        """Decide what action to take this turn"""
        if self.should_lay_down_card():
            card_index = self.choose_card_to_lay_down()
            if card_index is not None:
                return ('lay_down', card_index)
        
        spell_index = self.choose_spell_to_cast()
        if spell_index is not None:
            target = self.choose_target(players)
            if target:
                return ('cast_spell', spell_index, target)
        
        # Default action: do nothing or move
        return ('move', None)
    
    def perform_action(self, action, players):
        """Perform the chosen action"""
        if action[0] == 'lay_down':
            self.lay_down_spell_card(action[1])
        elif action[0] == 'cast_spell':
            spell_index = action[1]
            target = action[2]
            spell_card = self.cards_laid_down[spell_index]
            if spell_card.is_fully_charged():
                damage = spell_card.get_damage()
                target.take_damage(damage)
                self.cards_laid_down.remove(spell_card)



class SpellCard:
    def __init__(self, cost_dict):
        self.cost = cost_dict.copy()
        self.crystals_used = {color: 0 for color in cost_dict}
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
                return True

            # Use white crystal as substitute for target color
            if color == 'white' and wizard.crystals['white'] >= to_use:
                wizard.remove_crystals('white', to_use)
                self.crystals_used[target_color] += to_use
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
        # 2-damage spells (cost 2: 1 color + 1 wildcard)
        for _ in range(8):
            self.cards.append(SpellCard({'red': 1, 'wild': 1}))
            self.cards.append(SpellCard({'blue': 1, 'wild': 1}))
            self.cards.append(SpellCard({'green': 1, 'wild': 1}))
            self.cards.append(SpellCard({'yellow': 1, 'wild': 1}))

        # 3-damage spells (cost 3: 2 colors + 1 wildcard)
        for _ in range(6):
            self.cards.append(SpellCard({'red': 1, 'blue': 1, 'wild': 1}))
            self.cards.append(SpellCard({'red': 1, 'green': 1, 'wild': 1}))
            self.cards.append(SpellCard({'red': 1, 'yellow': 1, 'wild': 1}))
            self.cards.append(SpellCard({'blue': 1, 'green': 1, 'wild': 1}))
            self.cards.append(SpellCard({'blue': 1, 'yellow': 1, 'wild': 1}))
            self.cards.append(SpellCard({'green': 1, 'yellow': 1, 'wild': 1}))

        # 4-damage spells (cost 4: 3 colors + 1 wildcard)
        for _ in range(4):
            self.cards.append(SpellCard({'red': 1, 'blue': 1, 'green': 1, 'wild': 1}))
            self.cards.append(SpellCard({'red': 1, 'blue': 1, 'yellow': 1, 'wild': 1}))
            self.cards.append(SpellCard({'red': 1, 'green': 1, 'yellow': 1, 'wild': 1}))
            self.cards.append(SpellCard({'blue': 1, 'green': 1, 'yellow': 1, 'wild': 1}))

        # 5-damage spells (cost 5: all 4 colors + 1 wildcard)
        for _ in range(2):
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
        """Roll the special healing springs die (1-3, weighted toward lower values)"""
        return random.choice([1, 1, 1, 2, 2, 3])
