"""
ReQuest Companion — start this once, then everything happens from the web app.

    python bridge.py --game /path/to/her_repo/her_game.py

Open http://localhost:8765 (or open request-app.html from disk) and go to Play:

  * LAUNCH GAME          -> runs her script exactly like `python her_game.py`.
                            Her own pygame window pops up, sensors and all.
                            Nothing in her repo is touched.
  * LAUNCH + MIRROR      -> same, but every frame of her window is also
                            streamed live INTO the Crystal Caverns screen.
  * Reps / sets set in the dashboard -> POST /api/session -> written to
                            session.json next to her script + pygame event,
                            so her game can read them however she likes.

API:
    GET  /                  serves request-app.html if present
    GET  /api/health
    GET  /api/game          {path, running, mirror}
    POST /api/game          {"path": "..."} set/replace the game script
    POST /api/launch        {"mirror": true|false}
    POST /api/stop
    GET/POST /api/session   session settings (reps, sets, exercise, ...)
    WS   /ws/browser        status + mirrored frames out, input in
    WS   /ws/game           runner.py pushes frames here (internal)
"""
import argparse, asyncio, json, os, subprocess, sys, threading, time
from collections import deque
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

HOST, PORT = "127.0.0.1", 8765
HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- shared state
_lock = threading.Lock()
_latest = {"jpg": None, "seq": 0}
_input_q: deque = deque()                 # browser -> runner
GAME = {"path": None, "proc": None, "mirror": False}
_session = {"patient": "Vadim", "resistance": "medium",
            "plan": [{"exercise": "Band pull-apart", "reps": 12, "sets": 3}],
            "current": 0, "updated": time.time()}
_workout = {"done": [], "xp": 0}   # exercises defeated + xp in the current workout
_results = []                  # completed records (this run)
_event_subs = deque()          # browser broadcast bus: list of asyncio.Queue


def _session_path():
    base = Path(GAME["path"]).parent if GAME["path"] else HERE
    return base / "session.json"


def _log_path():
    base = Path(GAME["path"]).parent if GAME["path"] else HERE
    return base / "workout_log.json"


def _load_log():
    try:
        return json.loads(_log_path().read_text())
    except (OSError, json.JSONDecodeError):
        return []


def _append_log(entry):
    log = _load_log()
    log.append(entry)
    try:
        _log_path().write_text(json.dumps(log, indent=2))
    except OSError:
        pass
    return log


def _broadcast(msg):
    for q in list(_event_subs):
        try:
            q.put_nowait(msg)
        except Exception:
            pass


def _write_session_file():
    try:
        _session_path().write_text(json.dumps(_session, indent=2))
    except OSError:
        pass


def _running():
    return GAME["proc"] is not None and GAME["proc"].poll() is None


def _status():
    return {"type": "status",
            "game": Path(GAME["path"]).name if GAME["path"] else None,
            "configured": GAME["path"] is not None,
            "running": _running(),
            "mirror": GAME["mirror"] and _running(),
            "streaming": _latest["jpg"] is not None}


# ---------------------------------------------------------------- web app
app = FastAPI(title="ReQuest Companion")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/")
def index():
    for name in ("request-app.html", "request-app_7.html"):
        f = HERE / name
        if f.exists():
            return FileResponse(f)
    return JSONResponse({"companion": "running"})


@app.get("/api/health")
def health():
    return {"ok": True, **_status()}


@app.get("/api/game")
def get_game():
    return {**_status(), "path": GAME["path"]}


@app.post("/api/game")
async def set_game(payload: dict):
    p = Path(payload.get("path", "")).expanduser().resolve()
    if not p.exists():
        return JSONResponse({"ok": False, "error": f"not found: {p}"}, status_code=400)
    GAME["path"] = str(p)
    _write_session_file()
    return {"ok": True, **_status()}


@app.post("/api/launch")
async def launch(payload: dict = None):
    payload = payload or {}
    if not GAME["path"]:
        return JSONResponse({"ok": False, "error": "no game configured — start with --game or POST /api/game"}, status_code=400)
    if _running():
        return JSONResponse({"ok": False, "error": "game already running"}, status_code=409)
    mirror = bool(payload.get("mirror", False))
    _workout["done"] = []; _workout["xp"] = 0     # fresh workout each launch
    with _lock:
        _latest["jpg"], _latest["seq"] = None, 0
    _write_session_file()
    env = os.environ.copy()
    env["REQUEST_BRIDGE_SESSION"] = str(_session_path())
    env["REQUEST_BRIDGE_URL"] = f"http://{HOST}:{PORT}"
    game = Path(GAME["path"])
    cmd = ([sys.executable, str(HERE / "runner.py"), str(game)] if mirror
           else [sys.executable, str(game)])
    GAME["proc"] = subprocess.Popen(cmd, cwd=game.parent, env=env)
    GAME["mirror"] = mirror
    print(f"  launched {'(mirrored) ' if mirror else ''}{game.name}  pid={GAME['proc'].pid}")
    return {"ok": True, **_status()}


@app.post("/api/stop")
async def stop():
    if _running():
        GAME["proc"].terminate()
        try:
            GAME["proc"].wait(timeout=3)
        except subprocess.TimeoutExpired:
            GAME["proc"].kill()
    with _lock:
        _latest["jpg"] = None
    return {"ok": True, **_status()}


@app.get("/api/session")
def get_session():
    return dict(_session)


@app.post("/api/session")
async def set_session(payload: dict):
    # the workout is the plan (list of exercises); "current" is the active index
    if isinstance(payload.get("plan"), list):
        _session["plan"] = [
            {"exercise": str(e.get("exercise", "Exercise")),
             "reps": int(e.get("reps", 0) or 0),
             "sets": int(e.get("sets", 0) or 0)}
            for e in payload["plan"]]
    elif any(k in payload for k in ("reps", "sets", "exercise")):
        # legacy single-exercise push -> wrap it as a one-item plan
        _session["plan"] = [{
            "exercise": str(payload.get("exercise", "Exercise")),
            "reps": int(payload.get("reps", 0) or 0),
            "sets": int(payload.get("sets", 0) or 0)}]
        _session["current"] = 0
    if "current" in payload:
        try: _session["current"] = max(0, int(payload["current"]))
        except (TypeError, ValueError): pass
    for k in ("patient", "resistance"):
        if k in payload: _session[k] = payload[k]
    plan = _session.get("plan") or []
    if plan:
        _session["current"] = min(max(0, _session.get("current", 0)), len(plan) - 1)
    _session["updated"] = time.time()
    _write_session_file()
    _input_q.append({"type": "session", "session": dict(_session)})
    return dict(_session)


def _current_exercise_name():
    plan = _session.get("plan") or []
    if plan:
        return plan[min(max(0, _session.get("current", 0)), len(plan) - 1)]["exercise"]
    return None


# ---- the GAME reports stats back here ---------------------------------------
@app.post("/api/result")
async def post_result(payload: dict):
    """Called when an enemy is defeated = one prescribed exercise completed.
    Logs {exercise, reps, sets, xp} and, once every exercise in the plan has
    been defeated, marks the WORKOUT complete (+1 character level)."""
    # The game's finish screen sends {"finish": true} when the player presses
    # space on 'Well Done'. That is when we complete the workout and tell the
    # dashboard to jump to the check-in (using the XP/exercises tallied so far).
    if payload.get("finish"):
        summary = {
            "type": "workout",
            "patient": payload.get("patient", _session.get("patient")),
            "exercises": list(_workout["done"]),
            "xp_total": _workout["xp"], "level_gain": 1, "ts": time.time(),
        }
        _append_log(summary)
        _broadcast({"type": "workout_done", "level_gain": 1,
                    "xp_total": _workout["xp"], "exercises": list(_workout["done"])})
        _workout["done"] = []; _workout["xp"] = 0
        return {"ok": True, "finished": True}

    name = payload.get("exercise") or _current_exercise_name() or "Exercise"
    entry = {
        "type": "exercise",
        "patient": payload.get("patient", _session.get("patient")),
        "exercise": name,
        "reps": int(payload.get("reps", payload.get("reps_done", 0)) or 0),
        "sets": int(payload.get("sets", payload.get("sets_done", 0)) or 0),
        "xp": int(payload.get("xp", 0) or 0),
        "ts": time.time(),
    }
    _append_log(entry)
    if name not in _workout["done"]:
        _workout["done"].append(name)
    _workout["xp"] += entry["xp"]
    _broadcast({"type": "result", "result": entry,
                "done_count": len(_workout["done"]), "xp_session": _workout["xp"]})

    # Completion is driven by the finish screen ({"finish": true}) above, so the
    # dashboard switches to the check-in when the player presses space — not
    # mid-game. (Manual override: a save_result with workout_complete=True still
    # completes, as a fallback.)
    if payload.get("workout_complete"):
        summary = {
            "type": "workout", "patient": entry["patient"],
            "exercises": list(_workout["done"]),
            "xp_total": _workout["xp"], "level_gain": 1, "ts": time.time(),
        }
        _append_log(summary)
        _broadcast({"type": "workout_done", "level_gain": 1,
                    "xp_total": _workout["xp"], "exercises": list(_workout["done"])})
        _workout["done"] = []; _workout["xp"] = 0

    return {"ok": True, "saved": entry}


@app.get("/api/results")
def get_results():
    """All saved records (from the persistent log), newest last."""
    return {"results": _load_log(),
            "session_xp": _workout["xp"], "session_done": list(_workout["done"])}


@app.post("/api/results/clear")
async def clear_results():
    """Wipe the saved workout log + the current session counters. The dashboard
    'clear data' button calls this. The game only ever writes this file (never
    reads it), so clearing it can't affect a running game or the band/Stella."""
    _workout["done"] = []; _workout["xp"] = 0
    _results.clear()
    try:
        p = _log_path()
        if p.exists():
            p.unlink()
    except Exception:
        pass
    _broadcast({"type": "results", "results": [], "session_xp": 0})
    return {"ok": True}


# ---- runner.py connects here and pushes frames / receives input -------------
@app.websocket("/ws/game")
async def ws_game(ws: WebSocket):
    await ws.accept()

    async def pump_input():
        while True:
            while _input_q:
                await ws.send_text(json.dumps(_input_q.popleft()))
            await asyncio.sleep(0.02)

    task = asyncio.create_task(pump_input())
    try:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            if "bytes" in msg and msg["bytes"]:
                with _lock:
                    _latest["jpg"] = msg["bytes"]
                    _latest["seq"] += 1
    finally:
        task.cancel()
        with _lock:
            _latest["jpg"] = None


# ---- the web page connects here ---------------------------------------------
@app.websocket("/ws/browser")
async def ws_browser(ws: WebSocket):
    await ws.accept()
    await ws.send_text(json.dumps({"type": "session", "session": _session}))
    await ws.send_text(json.dumps({"type": "results", "results": _load_log(), "session_xp": _workout["xp"]}))

    bus = asyncio.Queue()
    _event_subs.append(bus)

    async def receiver():
        try:
            while True:
                raw = await ws.receive_text()
                try:
                    _input_q.append(json.loads(raw))
                except json.JSONDecodeError:
                    pass
        except WebSocketDisconnect:
            pass

    recv = asyncio.create_task(receiver())
    last_seq, last_status, last_ping = -1, None, 0.0
    try:
        while not recv.done():
            st = _status()
            if st != last_status or time.time() - last_ping > 1.0:
                last_status, last_ping = st, time.time()
                await ws.send_text(json.dumps(st))
            while not bus.empty():                         # forward game-reported events
                await ws.send_text(json.dumps(bus.get_nowait()))
            with _lock:
                seq, jpg = _latest["seq"], _latest["jpg"]
            if jpg is not None and seq != last_seq:
                last_seq = seq
                await ws.send_bytes(jpg)
            await asyncio.sleep(1 / 30)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        recv.cancel()
        try:
            _event_subs.remove(bus)
        except ValueError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", help="path to her pygame script (can also be set later via the API)")
    ap.add_argument("--port", type=int, default=PORT)
    args = ap.parse_args()
    if args.game:
        p = Path(args.game).expanduser().resolve()
        if not p.exists():
            sys.exit(f"Game script not found: {p}")
        GAME["path"] = str(p)
        _write_session_file()
    print(f"\n  ReQuest Companion  ->  http://{HOST}:{args.port}")
    print(f"  Game configured    ->  {GAME['path'] or '(none — set in the app or with --game)'}\n")
    uvicorn.run(app, host=HOST, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
