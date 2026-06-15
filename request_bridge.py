"""
Helper for the game side. Your script stays runnable on its own.

READING THE SESSION (what the dashboard pushes in -> your enemy encounters):

    import request_bridge
    plan = request_bridge.get_plan()
    # plan is the full workout: one entry per enemy/exercise
    # [
    #   {"exercise": "Shoulder External Rotation", "reps": 12, "sets": 3},
    #   {"exercise": "Banded I-Y-T Raises",        "reps": 15, "sets": 3},
    #   {"exercise": "Single-Arm Row to Press",    "reps": 10, "sets": 3},
    # ]
    # Build one enemy encounter per entry: reps/sets define how much work
    # defeats that enemy.

    cfg = request_bridge.get_session()           # whole dict (plan, current, patient...)
    active = request_bridge.current_exercise()   # {"exercise","reps","sets"} for plan[current]

It refreshes whenever the dashboard changes (cfg["updated"] is the timestamp).
get_session()/get_plan() are cached and only re-read when the file changes, so
calling them in your loop is cheap. For instant updates listen for the pygame
event request_bridge.SESSION_EVENT (USEREVENT+7); event.session is the same dict.

SAVING WHEN AN ENEMY IS DEFEATED (= one exercise completed):

    request_bridge.save_result(exercise="Shoulder External Rotation",
                               reps=12, sets=3, xp=50)

Call this once each time an enemy goes down. It records that the patient
completed that prescribed exercise (with the reps & sets done) and the XP it
earned (50 per exercise). The dashboard adds those exercises and XP to the
session.

WORKOUT DONE (automatic): the dashboard knows the full plan, so once you have
defeated every enemy in it, it automatically marks the workout complete — the
character gains +1 level and the patient is taken to their check-in. You don't
need a separate call. (If your enemy names ever differ from the plan names, you
can force it with save_result(..., workout_complete=True) on the last enemy.)

Everything is best-effort and non-blocking: if the dashboard/companion isn't
running, get_plan() returns a default and save_result() quietly does nothing, so
your game still runs with a plain `python your_game.py`.
"""
import json, os, threading, time, urllib.request
import pygame

SESSION_EVENT = pygame.USEREVENT + 7

_DEFAULTS = {"patient": "Player", "resistance": "medium",
             "plan": [{"exercise": "Band pull-apart", "reps": 10, "sets": 3}],
             "current": 0}
_URL = os.environ.get("REQUEST_BRIDGE_URL", "http://127.0.0.1:8765")

_cache = {"data": dict(_DEFAULTS), "mtime": 0.0, "checked": 0.0}


# ----------------------------------------------------------- read settings in
def get_session():
    """Return the full session dict (cached; re-reads only when the file changes)."""
    now = time.monotonic()
    if now - _cache["checked"] < 0.25:
        return dict(_cache["data"])
    _cache["checked"] = now
    path = os.environ.get("REQUEST_BRIDGE_SESSION", "session.json")
    try:
        m = os.path.getmtime(path)
        if m != _cache["mtime"]:
            with open(path) as f:
                _cache["data"] = {**_DEFAULTS, **json.load(f)}
            _cache["mtime"] = m
    except (OSError, json.JSONDecodeError):
        pass
    return dict(_cache["data"])


def get_plan():
    """Return the list of exercises (one enemy encounter each):
       [{'exercise': ..., 'reps': ..., 'sets': ...}, ...]"""
    return list(get_session().get("plan", []))


def current_exercise():
    """Return the active exercise dict {'exercise','reps','sets'} (plan[current])."""
    s = get_session()
    plan = s.get("plan", [])
    if not plan:
        return {"exercise": "Band pull-apart", "reps": 10, "sets": 3}
    i = min(max(0, s.get("current", 0)), len(plan) - 1)
    return dict(plan[i])


# ----------------------------------------------------------- save on defeat
def save_result(exercise, reps, sets, xp=50, workout_complete=False, **extra):
    """Call when an enemy is defeated (= that exercise is done).
       Records {exercise, reps, sets, xp}; fire-and-forget, never blocks the game."""
    payload = {"exercise": exercise, "reps": int(reps), "sets": int(sets),
               "xp": int(xp), "workout_complete": bool(workout_complete)}
    payload.update(extra)

    def _go():
        try:
            req = urllib.request.Request(
                _URL + "/api/result", data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=1)
        except Exception:
            pass
    threading.Thread(target=_go, daemon=True).start()
