"""
Crystal Wizards - AI Animation Configuration
Settings for controlling AI turn animation timing and visual effects
"""

# AI Turn Timing Settings (in milliseconds)
AI_THINKING_DELAY = 1000      # Initial delay before AI starts acting
AI_ACTION_DELAY = 800         # Delay between individual AI actions
AI_MOVEMENT_DURATION = 500    # Duration of movement animations (ms)
AI_SPELL_EFFECT_DURATION = 600  # Duration of spell effect animations (ms)

# Visual Effect Settings
AI_ENABLE_PARTICLE_EFFECTS = True    # Enable particle effects for AI actions
AI_ENABLE_SOUND_EFFECTS = True       # Enable sound effects for AI actions
AI_ENABLE_MOVEMENT_ANIMATION = True  # Enable smooth movement animations

# Animation Quality Settings
AI_PARTICLE_DENSITY = 1.0    # Multiplier for particle effect density (0.5 = half, 2.0 = double)
AI_ANIMATION_SMOOTHNESS = 1.0  # Multiplier for animation smoothness

# Debug Settings
AI_DEBUG_ACTIONS = False     # Print debug info for AI actions
AI_SHOW_ACTION_LABELS = False  # Show text labels for AI actions on screen
