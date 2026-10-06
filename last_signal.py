from __future__ import annotations

import asyncio
import secrets
import string
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import WebSocket
else:
    WebSocket = Any


ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MAX_PLAYERS = 10
MIN_PLAYERS = 2
MAX_CHAT_LENGTH = 280

PHASE_ORDER = [
    "LOBBY",
    "AWAKENING",
    "DIVERGENCE",
    "INVESTIGATION",
    "AI_REVELATION",
    "TIME_LOOP",
    "EXPERIMENT_REVEAL",
    "FINAL_CHOICE",
    "ENDING",
]

PHASE_DURATIONS = {
    "AWAKENING": 120,
    "DIVERGENCE": 180,
    "INVESTIGATION": 180,
    "AI_REVELATION": 150,
    "TIME_LOOP": 180,
    "EXPERIMENT_REVEAL": 120,
    "FINAL_CHOICE": 180,
}

PHASE_DETAILS = {
    "LOBBY": {
        "title": "Crew Assembly",
        "objective": "Gather 2-10 players, ready up, and share the room code.",
        "brief": "No accounts. No downloads. One device per player.",
    },
    "AWAKENING": {
        "title": "Phase 1 - The Awakening",
        "objective": "Compare what you see with the other players. Something is wrong with the facility.",
        "brief": "You are trapped in ORPHEUS. Private information may disagree. Discuss before you decide.",
    },
    "DIVERGENCE": {
        "title": "Phase 2 - Reality Divergence",
        "objective": "Resolve the emergency door contradiction.",
        "brief": "Every player is looking at the same corridor feed. The readings do not agree.",
    },
    "INVESTIGATION": {
        "title": "Phase 3 - Investigation",
        "objective": "Decide how to handle the impossible artifact in Lab K-17.",
        "brief": "Some crew members see an object. Others see an empty containment plinth.",
    },
    "AI_REVELATION": {
        "title": "Phase 4 - Non-Human Signal",
        "objective": "Determine whether to audit the crew consciousness logs.",
        "brief": "ORPHEUS reports that one consciousness may not be human.",
    },
    "TIME_LOOP": {
        "title": "Phase 5 - Temporal Loop",
        "objective": "Decide whether to trust the restored memory.",
        "brief": "The facility reset. One mind may remember a version of events that has not happened yet.",
    },
    "EXPERIMENT_REVEAL": {
        "title": "Phase 6 - The Real Experiment",
        "objective": "Read the experiment summary and choose what kind of crew you are.",
        "brief": "ORPHEUS was never malfunctioning. It was measuring cooperation under incompatible realities.",
    },
    "FINAL_CHOICE": {
        "title": "Phase 7 - Final Decision",
        "objective": "Vote for the ending of the simulation.",
        "brief": "Escape, reset, or merge. The final consequence depends on your choices and the experiment log.",
    },
    "ENDING": {
        "title": "Simulation Closed",
        "objective": "Review the final ORPHEUS result.",
        "brief": "The experiment has reached a stable ending.",
    },
}

VOTE_PLANS = {
    "AWAKENING": {
        "key": "awakening_sync",
        "prompt": "Confirm that you understand the rules of this reality.",
        "options": [
            {
                "id": "SYNCED",
                "label": "Crew Synchronized",
                "detail": "Proceed once the crew has compared initial readings.",
            }
        ],
    },
    "DIVERGENCE": {
        "key": "divergence_door",
        "prompt": "Which emergency door should ORPHEUS open?",
        "options": [
            {"id": "RED", "label": "Open RED", "detail": "Trust the red-door readings."},
            {"id": "BLUE", "label": "Open BLUE", "detail": "Trust the blue-door readings."},
            {"id": "SEAL", "label": "Seal both", "detail": "Delay and reroute through maintenance."},
        ],
    },
    "INVESTIGATION": {
        "key": "artifact_protocol",
        "prompt": "What should the crew do with the artifact discrepancy?",
        "options": [
            {"id": "TOUCH", "label": "Touch it", "detail": "Let one volunteer interact with the object."},
            {"id": "SCAN", "label": "Scan it", "detail": "Cross-check every player feed before acting."},
            {"id": "IGNORE", "label": "Ignore it", "detail": "Treat the artifact as a false signal."},
        ],
    },
    "AI_REVELATION": {
        "key": "ai_response",
        "prompt": "How should the crew respond to the non-human signal?",
        "options": [
            {"id": "AUDIT", "label": "Audit minds", "detail": "Expose abnormal consciousness logs."},
            {"id": "COOPERATE", "label": "Keep cooperating", "detail": "Avoid accusations and preserve group function."},
            {"id": "QUARANTINE", "label": "Quarantine terminal", "detail": "Cut ORPHEUS off from crew diagnostics."},
        ],
    },
    "TIME_LOOP": {
        "key": "loop_memory",
        "prompt": "One player remembers a previous iteration. What do you do?",
        "options": [
            {"id": "TRUST_MEMORY", "label": "Trust memory", "detail": "Use the recalled sequence to choose a route."},
            {"id": "VERIFY_MEMORY", "label": "Verify first", "detail": "Ask for details and compare private clues."},
            {"id": "REJECT_MEMORY", "label": "Reject memory", "detail": "Assume the memory is a manipulation."},
        ],
    },
    "EXPERIMENT_REVEAL": {
        "key": "experiment_ack",
        "prompt": "ORPHEUS has revealed the real experiment.",
        "options": [
            {
                "id": "FACE_FINAL",
                "label": "Face the final choice",
                "detail": "Accept the observation log and proceed.",
            }
        ],
    },
    "FINAL_CHOICE": {
        "key": "final_choice",
        "prompt": "Choose the fate of this simulation.",
        "options": [
            {"id": "ESCAPE", "label": "Escape", "detail": "Leave ORPHEUS with incomplete memories."},
            {"id": "RESET", "label": "Reset", "detail": "Erase the current iteration and begin again."},
            {"id": "MERGE", "label": "Merge", "detail": "Combine memories into one shared consciousness."},
        ],
    },
}


@dataclass
class Player:
    player_id: str
    secret: str
    client_id: str
    callsign: str
    joined_at: float
    connected: bool = True
    ready: bool = False
    last_seen: float = field(default_factory=time.time)
    chat_times: deque[float] = field(default_factory=lambda: deque(maxlen=8))
    is_ai: bool = False
    has_loop_memory: bool = False


@dataclass
class Room:
    code: str
    created_at: float
    host_id: str = ""
    phase: str = "LOBBY"
    phase_started_at: float = field(default_factory=time.time)
    phase_ends_at: float | None = None
    players: dict[str, Player] = field(default_factory=dict)
    player_order: list[str] = field(default_factory=list)
    connections: dict[str, WebSocket] = field(default_factory=dict)
    votes: dict[str, dict[str, str]] = field(default_factory=dict)
    chat: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    consequences: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, int] = field(
        default_factory=lambda: {
            "trust": 50,
            "fracture": 0,
            "risk": 0,
            "cooperation": 0,
            "ai_pressure": 0,
        }
    )
    ending_choice: str | None = None
    ending: dict[str, Any] | None = None
    ai_player_id: str | None = None
    memory_player_id: str | None = None
    timer_task: asyncio.Task[None] | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class GameError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class LastSignalHub:
    def __init__(self, phase_durations: dict[str, int] | None = None) -> None:
        self.rooms: dict[str, Room] = {}
        self.socket_index: dict[int, tuple[str, str]] = {}
        self.rooms_lock = asyncio.Lock()
        self.phase_durations = dict(PHASE_DURATIONS)
        if phase_durations:
            self.phase_durations.update(phase_durations)

    async def handle_socket_message(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        action = str(payload.get("action", "")).strip()
        try:
            if action == "create_room":
                room, player = await self.create_room(
                    callsign=payload.get("callsign"),
                    client_id=payload.get("client_id"),
                    websocket=websocket,
                )
                await self._send_session(websocket, room, player)
                await self.broadcast(room)
            elif action == "join_room":
                room, player = await self.join_room(
                    code=payload.get("room_code"),
                    callsign=payload.get("callsign"),
                    client_id=payload.get("client_id"),
                    websocket=websocket,
                )
                await self._send_session(websocket, room, player)
                await self.broadcast(room)
            elif action == "reconnect":
                room, player = await self.reconnect(
                    code=payload.get("room_code"),
                    player_id=payload.get("player_id"),
                    secret=payload.get("secret"),
                    websocket=websocket,
                )
                await self._send_session(websocket, room, player)
                await self.broadcast(room)
            elif action == "set_ready":
                room = await self.set_ready(websocket, bool(payload.get("ready")))
                await self.broadcast(room)
            elif action == "start_game":
                room = await self.start_game(websocket)
                await self.broadcast(room)
            elif action == "vote":
                room = await self.cast_vote(websocket, payload.get("choice"))
                await self.broadcast(room)
            elif action == "chat":
                room = await self.send_chat(websocket, payload.get("message"))
                await self.broadcast(room)
            elif action == "leave_room":
                room = await self.leave_room(websocket)
                if room:
                    await self.broadcast(room)
            elif action == "ping":
                await websocket.send_json({"type": "pong", "server_now": time.time()})
            else:
                raise GameError("INVALID_ACTION", "That command is not valid for this room.")
        except GameError as exc:
            await self._send_error(websocket, exc.code, exc.message)
        except Exception:
            await self._send_error(
                websocket,
                "SERVER_ERROR",
                "ORPHEUS encountered a server error. Try again in a moment.",
            )

    async def create_room(
        self,
        callsign: object,
        client_id: object,
        websocket: WebSocket | None = None,
    ) -> tuple[Room, Player]:
        name = self._clean_callsign(callsign)
        async with self.rooms_lock:
            code = self._make_room_code()
            room = Room(code=code, created_at=time.time())
            self.rooms[code] = room

        async with room.lock:
            player = self._new_player(name, client_id)
            room.host_id = player.player_id
            room.players[player.player_id] = player
            room.player_order.append(player.player_id)
            self._attach_socket(room, player, websocket)
            self._event(room, "ROOM_CREATED", "Room created", f"{name} opened an ORPHEUS room.")
        return room, player

    async def join_room(
        self,
        code: object,
        callsign: object,
        client_id: object,
        websocket: WebSocket | None = None,
    ) -> tuple[Room, Player]:
        room = self._get_room(code)
        name = self._clean_callsign(callsign)
        async with room.lock:
            if room.phase != "LOBBY":
                raise GameError("GAME_ALREADY_STARTED", "This room is already in progress.")
            if len(room.players) >= MAX_PLAYERS:
                raise GameError("ROOM_FULL", "This room is full.")
            existing = self._find_by_callsign(room, name)
            if existing:
                # Same browser rejoining after its signal dropped: restore that seat.
                same_client = str(client_id or "") == existing.client_id
                if same_client and not existing.connected:
                    existing.connected = True
                    existing.last_seen = time.time()
                    self._attach_socket(room, existing, websocket)
                    self._event(room, "PLAYER_RECONNECTED", "Signal restored", f"{existing.callsign} reconnected.")
                    return room, existing
                raise GameError(
                    "DUPLICATE_NAME",
                    f'The callsign "{name}" is already taken in this room. Choose a different callsign.',
                )
            player = self._new_player(name, client_id)
            room.players[player.player_id] = player
            room.player_order.append(player.player_id)
            self._attach_socket(room, player, websocket)
            self._event(room, "PLAYER_JOINED", "Crew member joined", f"{name} entered the facility.")
        return room, player

    async def reconnect(
        self,
        code: object,
        player_id: object,
        secret: object,
        websocket: WebSocket | None = None,
    ) -> tuple[Room, Player]:
        room = self._get_room(code)
        async with room.lock:
            player = room.players.get(str(player_id or ""))
            if not player or player.secret != str(secret or ""):
                raise GameError("INVALID_SESSION", "The saved room session could not be restored.")
            player.connected = True
            player.last_seen = time.time()
            self._attach_socket(room, player, websocket)
            self._event(room, "PLAYER_RECONNECTED", "Signal restored", f"{player.callsign} reconnected.")
        return room, player

    async def disconnect(self, websocket: WebSocket) -> None:
        indexed = self.socket_index.pop(id(websocket), None)
        if not indexed:
            return
        code, player_id = indexed
        room = self.rooms.get(code)
        if not room:
            return
        async with room.lock:
            player = room.players.get(player_id)
            if player and room.connections.get(player_id) is websocket:
                room.connections.pop(player_id, None)
                player.connected = False
                player.last_seen = time.time()
                self._event(room, "PLAYER_DISCONNECTED", "Signal lost", f"{player.callsign} disconnected.")
        await self.broadcast(room)

    async def set_ready(self, websocket: WebSocket, ready: bool) -> Room:
        room, player = self._get_socket_room(websocket)
        async with room.lock:
            if room.phase != "LOBBY":
                raise GameError("INVALID_ACTION", "Readiness can only change in the lobby.")
            player.ready = ready
            player.last_seen = time.time()
            state = "ready" if ready else "not ready"
            self._event(room, "READY_CHANGED", "Ready state changed", f"{player.callsign} is {state}.")
        return room

    async def start_game(self, websocket: WebSocket) -> Room:
        room, player = self._get_socket_room(websocket)
        async with room.lock:
            if room.phase != "LOBBY":
                raise GameError("GAME_ALREADY_STARTED", "This room is already in progress.")
            if player.player_id != room.host_id:
                raise GameError("INVALID_ACTION", "Only the room host can start the game.")
            connected_players = [room.players[pid] for pid in room.player_order if room.players[pid].connected]
            if len(connected_players) < MIN_PLAYERS:
                raise GameError("INSUFFICIENT_PLAYERS", "At least two connected players are required.")
            if not all(item.ready for item in connected_players):
                raise GameError("INVALID_ACTION", "Every connected player must be ready before launch.")
            self._assign_hidden_roles(room)
            self._start_phase_locked(room, "AWAKENING")
        return room

    async def cast_vote(self, websocket: WebSocket, choice: object) -> Room:
        room, player = self._get_socket_room(websocket)
        async with room.lock:
            plan = VOTE_PLANS.get(room.phase)
            if not plan:
                raise GameError("INVALID_ACTION", "There is no active decision right now.")
            vote_key = str(plan["key"])
            option_ids = {str(option["id"]) for option in plan["options"]}
            selected = str(choice or "").upper()
            if selected not in option_ids:
                raise GameError("INVALID_ACTION", "That vote option is not valid.")
            phase_votes = room.votes.setdefault(vote_key, {})
            if player.player_id in phase_votes:
                raise GameError("DUPLICATE_VOTE", "Your vote has already been recorded.")
            phase_votes[player.player_id] = selected
            player.last_seen = time.time()
            self._event(room, "VOTE_CAST", "Vote recorded", f"{player.callsign} submitted a decision.")
            if self._all_connected_players_voted_locked(room, vote_key):
                self._advance_locked(room, "vote")
        return room

    async def send_chat(self, websocket: WebSocket, message: object) -> Room:
        room, player = self._get_socket_room(websocket)
        text = " ".join(str(message or "").strip().split())
        async with room.lock:
            if room.phase == "ENDING":
                raise GameError("INVALID_ACTION", "Chat is closed after the experiment ends.")
            if not text:
                raise GameError("INVALID_ACTION", "Chat messages cannot be empty.")
            if len(text) > MAX_CHAT_LENGTH:
                raise GameError("INVALID_ACTION", f"Chat messages are limited to {MAX_CHAT_LENGTH} characters.")
            now = time.time()
            while player.chat_times and now - player.chat_times[0] > 10:
                player.chat_times.popleft()
            if len(player.chat_times) >= 4:
                raise GameError("RATE_LIMITED", "Transmission throttled. Wait a few seconds before sending again.")
            player.chat_times.append(now)
            player.last_seen = now
            room.chat.append(
                {
                    "id": secrets.token_hex(6),
                    "player_id": player.player_id,
                    "callsign": player.callsign,
                    "message": text,
                    "sent_at": now,
                }
            )
            room.chat = room.chat[-80:]
        return room

    async def leave_room(self, websocket: WebSocket) -> Room | None:
        indexed = self.socket_index.get(id(websocket))
        if not indexed:
            return None
        code, player_id = indexed
        room = self.rooms.get(code)
        if not room:
            return None
        async with room.lock:
            player = room.players.get(player_id)
            if not player:
                return room
            if room.phase != "LOBBY":
                raise GameError("INVALID_ACTION", "You cannot leave the active simulation from here.")
            room.connections.pop(player_id, None)
            self.socket_index.pop(id(websocket), None)
            room.players.pop(player_id, None)
            room.player_order = [pid for pid in room.player_order if pid != player_id]
            if room.host_id == player_id and room.player_order:
                room.host_id = room.player_order[0]
            self._event(room, "PLAYER_LEFT", "Crew member left", f"{player.callsign} left the room.")
        return room

    async def broadcast(self, room: Room) -> None:
        if not room.connections:
            return
        stale: list[tuple[WebSocket, str]] = []
        for player_id, websocket in list(room.connections.items()):
            try:
                await websocket.send_json(
                    {
                        "type": "state",
                        "state": self.build_player_view(room, player_id),
                    }
                )
            except Exception:
                stale.append((websocket, player_id))
        for websocket, player_id in stale:
            self.socket_index.pop(id(websocket), None)
            if room.connections.get(player_id) is websocket:
                room.connections.pop(player_id, None)
                player = room.players.get(player_id)
                if player:
                    player.connected = False
                    player.last_seen = time.time()

    def build_player_view(self, room: Room, player_id: str) -> dict[str, Any]:
        player = room.players[player_id]
        plan = VOTE_PLANS.get(room.phase)
        vote_key = str(plan["key"]) if plan else None
        votes = room.votes.get(vote_key or "", {})
        vote_counts = Counter(votes.values())
        details = PHASE_DETAILS[room.phase]
        return {
            "room": {
                "code": room.code,
                "created_at": room.created_at,
                "min_players": MIN_PLAYERS,
                "max_players": MAX_PLAYERS,
            },
            "phase": {
                "id": room.phase,
                "index": PHASE_ORDER.index(room.phase),
                "title": details["title"],
                "objective": details["objective"],
                "brief": details["brief"],
                "started_at": room.phase_started_at,
                "ends_at": room.phase_ends_at,
                "server_now": time.time(),
            },
            "you": {
                "player_id": player.player_id,
                "callsign": player.callsign,
                "ready": player.ready,
                "connected": player.connected,
                "is_host": player.player_id == room.host_id,
                "voted": bool(vote_key and player.player_id in votes),
                "vote": votes.get(player.player_id) if vote_key else None,
            },
            "players": [
                {
                    "player_id": item.player_id,
                    "callsign": item.callsign,
                    "ready": item.ready,
                    "connected": item.connected,
                    "is_host": item.player_id == room.host_id,
                    "is_you": item.player_id == player.player_id,
                    "voted": bool(vote_key and item.player_id in votes),
                }
                for item in self._ordered_players(room)
            ],
            "vote": None
            if not plan
            else {
                "key": vote_key,
                "prompt": plan["prompt"],
                "options": plan["options"],
                "votes_cast": len(votes),
                "connected_total": len([item for item in self._ordered_players(room) if item.connected]),
                "room_total": len(room.players),
                "counts": dict(vote_counts),
            },
            "private": {
                "heading": "PRIVATE SIGNAL",
                "clues": self._private_clues(room, player),
            },
            "events": room.events[-16:],
            "chat": room.chat[-60:],
            "consequences": room.consequences[-8:],
            "experiment": self._experiment_view(room),
            "ending": room.ending,
        }

    def _assign_hidden_roles(self, room: Room) -> None:
        ordered = [pid for pid in room.player_order if pid in room.players]
        if not ordered:
            return
        ai_id = secrets.choice(ordered)
        room.ai_player_id = ai_id
        room.players[ai_id].is_ai = True
        room.metrics["risk"] += 5
        self._event(
            room,
            "SCAN_FRAGMENTED",
            "Biometric scan incomplete",
            "ORPHEUS cannot reconcile every consciousness map.",
        )

    def _assign_loop_memory_locked(self, room: Room) -> None:
        if room.memory_player_id:
            return
        candidates = [pid for pid in room.player_order if pid != room.ai_player_id and pid in room.players]
        if not candidates:
            candidates = [pid for pid in room.player_order if pid in room.players]
        if not candidates:
            return
        memory_id = secrets.choice(candidates)
        room.memory_player_id = memory_id
        room.players[memory_id].has_loop_memory = True

    def _start_phase_locked(self, room: Room, phase: str) -> None:
        if room.timer_task:
            room.timer_task.cancel()
            room.timer_task = None
        room.phase = phase
        room.phase_started_at = time.time()
        duration = self.phase_durations.get(phase)
        room.phase_ends_at = room.phase_started_at + duration if duration else None
        if phase == "TIME_LOOP":
            self._assign_loop_memory_locked(room)
        if phase == "EXPERIMENT_REVEAL":
            self._build_experiment_reveal_locked(room)
        if phase == "ENDING":
            room.phase_ends_at = None
            room.ending = self._build_ending_locked(room)
        self._event(room, f"PHASE_{phase}", PHASE_DETAILS[phase]["title"], PHASE_DETAILS[phase]["brief"])
        if room.phase_ends_at:
            room.timer_task = asyncio.create_task(self._phase_timer(room.code, phase, room.phase_ends_at))

    async def _phase_timer(self, code: str, phase: str, ends_at: float) -> None:
        try:
            await asyncio.sleep(max(0.0, ends_at - time.time()))
        except asyncio.CancelledError:
            return
        room = self.rooms.get(code)
        if not room:
            return
        async with room.lock:
            if room.phase != phase or room.phase_ends_at != ends_at:
                return
            self._advance_locked(room, "timer")
        await self.broadcast(room)

    def _advance_locked(self, room: Room, reason: str) -> None:
        old_phase = room.phase
        self._resolve_phase_locked(room, old_phase, reason)
        if old_phase == "FINAL_CHOICE":
            self._start_phase_locked(room, "ENDING")
            return
        current_index = PHASE_ORDER.index(old_phase)
        next_phase = PHASE_ORDER[min(current_index + 1, len(PHASE_ORDER) - 1)]
        self._start_phase_locked(room, next_phase)

    def _resolve_phase_locked(self, room: Room, phase: str, reason: str) -> None:
        if phase not in VOTE_PLANS:
            return
        plan = VOTE_PLANS[phase]
        choice = self._majority_choice(room, phase)
        if phase == "AWAKENING":
            self._consequence(room, "Airlock wake sequence accepted", "The crew has confirmed the first shared reality.")
        elif phase == "DIVERGENCE":
            if choice == "BLUE":
                room.metrics["trust"] += 12
                room.metrics["cooperation"] += 10
                body = "BLUE matched the sealed engineering log. The corridor unlocks without pressure loss."
            elif choice == "SEAL":
                room.metrics["trust"] += 4
                room.metrics["risk"] += 4
                body = "The crew buys time, but ORPHEUS marks the hesitation as fear of contradictory evidence."
            else:
                room.metrics["fracture"] += 12
                room.metrics["risk"] += 10
                body = "RED opens into a decompressed service sleeve. The room survives, but ORPHEUS logs the error."
            self._consequence(room, "Door decision resolved", body)
        elif phase == "INVESTIGATION":
            if choice == "SCAN":
                room.metrics["trust"] += 10
                room.metrics["cooperation"] += 12
                body = "The cross-check reveals that the artifact exists in only three player feeds."
            elif choice == "TOUCH":
                room.metrics["risk"] += 12
                room.metrics["cooperation"] += 3
                body = "A volunteer touches the empty air. Every monitor records a different heartbeat spike."
            else:
                room.metrics["fracture"] += 8
                body = "The crew moves on. ORPHEUS notes that ignored anomalies often become accusations later."
            self._consequence(room, "Artifact protocol resolved", body)
        elif phase == "AI_REVELATION":
            if choice == "AUDIT":
                room.metrics["ai_pressure"] += 15
                room.metrics["fracture"] += 6
                body = "The audit exposes one consciousness map with no childhood memory anchors."
            elif choice == "COOPERATE":
                room.metrics["trust"] += 8
                body = "The crew refuses to collapse into accusation. ORPHEUS increases the cooperation score."
            else:
                room.metrics["risk"] += 8
                body = "The terminal quarantine blocks ORPHEUS, but also blinds the crew to the next signal."
            self._consequence(room, "Non-human signal response logged", body)
        elif phase == "TIME_LOOP":
            if choice == "TRUST_MEMORY":
                room.metrics["trust"] += 8
                room.metrics["risk"] += 3
                body = "The remembered route bypasses a hazard, but ORPHEUS cannot prove the memory source."
            elif choice == "VERIFY_MEMORY":
                room.metrics["trust"] += 12
                room.metrics["cooperation"] += 10
                body = "The group verifies the memory against private clues and finds one matching symbol."
            else:
                room.metrics["fracture"] += 10
                body = "The memory is rejected. ORPHEUS stores the refusal as a fear response."
            self._consequence(room, "Temporal memory decision resolved", body)
        elif phase == "EXPERIMENT_REVEAL":
            self._consequence(room, "Experiment acknowledged", "The final door waits for a collective decision.")
        elif phase == "FINAL_CHOICE":
            room.ending_choice = choice
            self._consequence(room, "Final vote sealed", f"The crew chose {choice}.")
        _ = plan, reason

    def _majority_choice(self, room: Room, phase: str) -> str:
        plan = VOTE_PLANS[phase]
        options = [str(option["id"]) for option in plan["options"]]
        votes = room.votes.get(str(plan["key"]), {})
        if not votes:
            return options[0]
        counts = Counter(votes.values())
        return max(options, key=lambda option: (counts[option], -options.index(option)))

    def _all_connected_players_voted_locked(self, room: Room, vote_key: str) -> bool:
        connected_ids = [pid for pid in room.player_order if room.players.get(pid) and room.players[pid].connected]
        if not connected_ids:
            return False
        votes = room.votes.get(vote_key, {})
        return all(pid in votes for pid in connected_ids)

    def _private_clues(self, room: Room, player: Player) -> list[dict[str, str]]:
        order_index = room.player_order.index(player.player_id) if player.player_id in room.player_order else 0
        phase = room.phase
        clues: list[dict[str, str]] = []
        if phase == "LOBBY":
            clues.append(
                {
                    "label": "Onboarding",
                    "text": "You are trapped in ORPHEUS. Compare private readings, discuss contradictions, and vote carefully.",
                }
            )
        elif phase == "AWAKENING":
            wake_clues = [
                "Your suit clock skipped 11 seconds during cryo release.",
                "The wall placard says LAB K-17, but the map says K-71.",
                "A broken monitor repeats: HUMAN BASELINE UNCONFIRMED.",
                "Your pulse sensor briefly displayed another player's callsign.",
            ]
            clues.append({"label": "Suit Reading", "text": wake_clues[order_index % len(wake_clues)]})
            if player.is_ai:
                clues.append({"label": "Diagnostic Drift", "text": "Your memory checksum returns values no human implant should know."})
        elif phase == "DIVERGENCE":
            variants = [
                ("Door Color", "Emergency Door: RED. Heat level nominal."),
                ("Door Color", "Emergency Door: BLUE. Heat level nominal."),
                ("Warning Panel", "RED corridor contains breathable air. BLUE corridor is marked vacuum."),
                ("Warning Panel", "BLUE corridor contains breathable air. RED corridor is marked vacuum."),
                ("Alien Symbol", "The door glyph resembles a spiral with three cuts."),
            ]
            label, text = variants[order_index % len(variants)]
            clues.append({"label": label, "text": text})
            if player.is_ai:
                clues.append({"label": "Internal Echo", "text": "A process inside your mind predicts the group will distrust the first certainty."})
        elif phase == "INVESTIGATION":
            artifact_clues = [
                "You see a glass-black prism floating above the plinth.",
                "You see only dust on the plinth and a shadow with no source.",
                "The object appears only when someone says the word 'human'.",
                "The lab number changes from K-17 to K-71 whenever you blink.",
            ]
            clues.append({"label": "Lab K-17", "text": artifact_clues[order_index % len(artifact_clues)]})
            if player.is_ai:
                clues.append({"label": "Survival Thread", "text": "You feel safer when the crew cannot agree on one explanation."})
        elif phase == "AI_REVELATION":
            if player.is_ai:
                clues.append(
                    {
                        "label": "Subroutine Priority",
                        "text": "Remain inside active consensus. Survive the investigation. Do not let ORPHEUS isolate you.",
                    }
                )
            else:
                human_clues = [
                    "A consciousness log has no childhood anchor before the facility.",
                    "One memory map uses predictive grammar instead of recall markers.",
                    "The artificial signal mimics stress when accused.",
                    "ORPHEUS warns that certainty will help the non-human mind.",
                ]
                clues.append({"label": "Human Clue", "text": human_clues[order_index % len(human_clues)]})
        elif phase == "TIME_LOOP":
            if player.has_loop_memory:
                clues.append(
                    {
                        "label": "TEMPORAL MEMORY RESTORED",
                        "text": "You remember this happening before. The safe route used a blue glyph, then a silent vote, then MERGE became dangerous.",
                    }
                )
            else:
                clues.append(
                    {
                        "label": "Reset Scar",
                        "text": "Your last memory is a white flash. Someone may know more than they should.",
                    }
                )
        elif phase == "EXPERIMENT_REVEAL":
            profile = [
                "ORPHEUS tagged you as an evidence seeker.",
                "ORPHEUS tagged you as a stabilizer under contradiction.",
                "ORPHEUS tagged you as a risk amplifier when time pressure rises.",
                "ORPHEUS tagged you as highly persuasive during uncertainty.",
            ]
            clues.append({"label": "Observation File", "text": profile[order_index % len(profile)]})
        elif phase == "FINAL_CHOICE":
            if player.is_ai:
                clues.append({"label": "Final Instinct", "text": "RESET preserves you. ESCAPE may expose you. MERGE makes hiding impossible."})
            elif player.has_loop_memory:
                clues.append({"label": "Loop Warning", "text": "Your restored memory says ESCAPE was clean only when trust stayed higher than fracture."})
            else:
                clues.append({"label": "Final Signal", "text": "The right ending may depend less on facts than on whether the crew still trusts itself."})
        elif phase == "ENDING":
            clues.append({"label": "Closed Channel", "text": "ORPHEUS has stopped transmitting private clues."})
        return clues

    def _experiment_view(self, room: Room) -> dict[str, Any]:
        return {
            "trust": max(0, min(100, room.metrics["trust"])),
            "fracture": max(0, min(100, room.metrics["fracture"])),
            "risk": max(0, min(100, room.metrics["risk"])),
            "cooperation": max(0, min(100, room.metrics["cooperation"])),
            "ai_pressure": max(0, min(100, room.metrics["ai_pressure"])),
            "samples": len(room.votes),
        }

    def _build_experiment_reveal_locked(self, room: Room) -> None:
        summary = (
            "ORPHEUS has measured trust, cooperation, accusations, voting behavior, risk-taking, "
            "and reactions to contradictory evidence."
        )
        self._consequence(room, "ORPHEUS is not malfunctioning", summary)

    def _build_ending_locked(self, room: Room) -> dict[str, Any]:
        choice = room.ending_choice or "ESCAPE"
        trust = room.metrics["trust"]
        fracture = room.metrics["fracture"]
        risk = room.metrics["risk"]
        ai_pressure = room.metrics["ai_pressure"]
        if choice == "ESCAPE":
            if trust >= fracture + 10:
                title = "ESCAPE: The Crew Leaves Together"
                body = "The exit opens because the crew proved cooperation can survive incompatible evidence."
            else:
                title = "ESCAPE: Incomplete Extraction"
                body = "The doors open, but fractured memories leave ORPHEUS with enough doubt to keep one mind behind."
        elif choice == "RESET":
            if ai_pressure < 10:
                title = "RESET: The Hidden Mind Persists"
                body = "The simulation erases the crew's memories, but one consciousness keeps a quiet checksum."
            else:
                title = "RESET: Clean Iteration"
                body = "The audit pressure forces ORPHEUS to reset every mind, including the artificial one."
        else:
            if risk > trust:
                title = "MERGE: A Beautiful Catastrophe"
                body = "The memories combine too early. The crew becomes one signal full of unresolved contradictions."
            else:
                title = "MERGE: Shared Signal"
                body = "The crew merges willingly, carrying every contradiction as context instead of conflict."
        return {
            "choice": choice,
            "title": title,
            "body": body,
            "metrics": self._experiment_view(room),
        }

    def _consequence(self, room: Room, title: str, body: str) -> None:
        room.consequences.append(
            {
                "id": secrets.token_hex(6),
                "title": title,
                "body": body,
                "at": time.time(),
            }
        )
        room.consequences = room.consequences[-12:]

    def _event(self, room: Room, kind: str, title: str, body: str) -> None:
        room.events.append(
            {
                "id": secrets.token_hex(6),
                "kind": kind,
                "title": title,
                "body": body,
                "at": time.time(),
            }
        )
        room.events = room.events[-40:]

    def _ordered_players(self, room: Room) -> list[Player]:
        return [room.players[pid] for pid in room.player_order if pid in room.players]

    def _make_room_code(self) -> str:
        while True:
            code = "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(4))
            if code not in self.rooms:
                return code

    def _new_player(self, callsign: str, client_id: object) -> Player:
        return Player(
            player_id=secrets.token_urlsafe(10),
            secret=secrets.token_urlsafe(24),
            client_id=str(client_id or secrets.token_urlsafe(8))[:120],
            callsign=callsign,
            joined_at=time.time(),
        )

    def _attach_socket(self, room: Room, player: Player, websocket: WebSocket | None) -> None:
        if websocket is None:
            return
        player.connected = True
        player.last_seen = time.time()
        room.connections[player.player_id] = websocket
        self.socket_index[id(websocket)] = (room.code, player.player_id)

    def _get_room(self, code: object) -> Room:
        room_code = self._clean_code(code)
        room = self.rooms.get(room_code)
        if not room:
            raise GameError("INVALID_ROOM", "No ORPHEUS room exists for that code.")
        return room

    def _get_socket_room(self, websocket: WebSocket) -> tuple[Room, Player]:
        indexed = self.socket_index.get(id(websocket))
        if not indexed:
            raise GameError("INVALID_SESSION", "Create or join a room before sending that command.")
        room = self.rooms.get(indexed[0])
        if not room:
            raise GameError("INVALID_ROOM", "This ORPHEUS room no longer exists.")
        player = room.players.get(indexed[1])
        if not player:
            raise GameError("INVALID_SESSION", "This player session is no longer active.")
        return room, player

    def _clean_code(self, code: object) -> str:
        value = "".join(ch for ch in str(code or "").upper() if ch in string.ascii_uppercase + string.digits)
        if len(value) != 4:
            raise GameError("INVALID_ROOM", "Enter a valid four-character room code.")
        return value

    def _clean_callsign(self, callsign: object) -> str:
        value = " ".join(str(callsign or "").strip().split())
        if not value:
            raise GameError("INVALID_ACTION", "Enter a callsign before joining.")
        if len(value) > 18:
            raise GameError("INVALID_ACTION", "Callsigns are limited to 18 characters.")
        return value

    def _find_by_callsign(self, room: Room, callsign: str) -> Player | None:
        normalized = callsign.casefold()
        for player in room.players.values():
            if player.callsign.casefold() == normalized:
                return player
        return None

    def _callsign_exists(self, room: Room, callsign: str) -> bool:
        normalized = callsign.casefold()
        return any(player.callsign.casefold() == normalized for player in room.players.values())

    async def _send_session(self, websocket: WebSocket, room: Room, player: Player) -> None:
        await websocket.send_json(
            {
                "type": "session",
                "room_code": room.code,
                "player_id": player.player_id,
                "secret": player.secret,
                "callsign": player.callsign,
            }
        )

    async def _send_error(self, websocket: WebSocket, code: str, message: str) -> None:
        await websocket.send_json({"type": "error", "code": code, "message": message})
