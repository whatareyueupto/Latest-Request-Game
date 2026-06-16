WIDTH = 1280
HEIGHT = 720
TILESIZE = 16
SCALE = 4


ENEMY_DATA = {
    'ghost':    {'hp': 2, 'frames': 2, 'animation_speed': 0.01, 'exercise': 'Shoulder External Rotation', 'xp': 50},
    'skeleton': {'hp': 3, 'frames': 2, 'animation_speed': 0.01, 'exercise': 'Banded I-Y-T Raises',        'xp': 100},
    'zombie':   {'hp': 3, 'frames': 2, 'animation_speed': 0.01, 'exercise': 'Single-Arm Row to Press',    'xp': 75},
}

ENEMY_MAP = {
    'e': 'ghost',
    's': 'skeleton',
    'z': 'zombie',
}

WORLD_MAP = [
['x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x'],
['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x','x'],
['x',' ','p',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
['x',' ',' ','x',' ',' ',' ',' ',' ','x','x','x','x','x',' ',' ',' ',' ',' ','x'],
['x',' ',' ','x','x',' ',' ',' ',' ',' ',' ','x','x','x',' ',' ',' ',' ',' ','x'],
['x',' ',' ','x','x',' ',' ',' ',' ','x','x','x','x','x',' ',' ',' ',' ',' ','x'],
['x',' ',' ','x','x',' ',' ',' ',' ',' ','x','x','x','x',' ',' ',' ',' ',' ','x'],
['x',' ',' ','x','x','x',' ',' ',' ',' ',' ',' ','x','x',' ',' ',' ',' ',' ','x'],
['x',' ',' ','x',' ',' ',' ',' ',' ',' ',' ',' ',' ','x',' ',' ',' ',' ',' ','x'],
['x',' ',' ','x',' ',' ',' ',' ','s',' ',' ',' ',' ','x',' ',' ',' ',' ',' ','x'],
['x',' ',' ','x',' ',' ',' ',' ',' ',' ',' ',' ',' ','x',' ',' ',' ',' ',' ','x'],
['x',' ',' ','x',' ',' ',' ',' ',' ',' ',' ',' ',' ','x',' ',' ',' ',' ',' ','x'],
['x',' ',' ',' ',' ',' ',' ','x',' ','x',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
['x',' ',' ',' ',' ',' ','x','x','x','x','x',' ',' ',' ',' ',' ',' ',' ',' ','x'],
['x',' ',' ',' ',' ',' ',' ','x','x','x',' ',' ',' ',' ',' ','x','x',' ',' ','x'],
['x',' ',' ',' ',' ',' ',' ',' ','x',' ',' ',' ',' ','e',' ','x',' ',' ',' ','x'],
['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
['x','x',' ',' ',' ',' ',' ',' ',' ',' ','z',' ',' ',' ',' ',' ',' ',' ',' ','x'],
['x','x','x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x','x'],
['x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x','x']
]

TUTORIAL_MAP = [
    ['x','x','x','x','x','x','x','x','x','x','x','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ','p',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ','n',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ','w',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x','x','x','x','x','x','x','x','x','x','x','x'],
]


def apply_prescription():
    """Pull the prescribed exercises (name, reps, sets) from the ReQuest
    dashboard into ENEMY_DATA before the enemies are created.
    Enemy HP = reps * sets. Matched to enemies by exercise name.
    Safe if the dashboard isn't running: leaves ENEMY_DATA untouched."""
    try:
        import request_bridge
        plan = request_bridge.get_plan()
    except Exception:
        return
    by_name = {e.get('exercise'): e for e in plan}
    for data in ENEMY_DATA.values():
        p = by_name.get(data.get('exercise'))
        if p:
            data['reps'] = int(p['reps'])
            data['sets'] = int(p['sets'])
            data['hp'] = max(1, int(p['reps']) * int(p['sets']))
