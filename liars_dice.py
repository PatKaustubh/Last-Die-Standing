"""Last Die Standing: authoritative real-time bluffing-dice server (2-6 players)."""
from __future__ import annotations

import asyncio
import random
import secrets
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MIN_PLAYERS, MAX_PLAYERS, START_DICE, REVEAL_SECONDS, BOT_DELAY = 2, 6, 5, 8, 1.4
POWERS = ("peek", "shield", "double", "reroll")
DIE = "\u2680\u2681\u2682\u2683\u2684\u2685"
BOT_NAMES = ("Bot Ada", "Bot Rex", "Bot Mia", "Bot Kit", "Bot Zed")


class GameError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


@dataclass
class Player:
    pid: str
    secret: str
    cid: str
    name: str
    dice: list[int] = field(default_factory=list)
    count: int = START_DICE
    connected: bool = True
    power: str = ""
    power_used: bool = False
    shield: bool = False
    bot: bool = False
    note: str = ""


@dataclass
class Room:
    code: str
    host: str = ""
    phase: str = "LOBBY"  # LOBBY | PLAY | REVEAL | END
    players: dict[str, Player] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    turn: str = ""
    bid: tuple[int, int] | None = None
    bidder: str = ""
    round: int = 0
    reveal: dict[str, Any] | None = None
    winner: str = ""
    log: list[str] = field(default_factory=list)
    bot_busy: bool = False
    socks: dict[str, WebSocket] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class DiceHub:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}
        self.index: dict[int, tuple[str, str]] = {}

    # ---------- socket entry points ----------
    async def handle_socket_message(self, ws: WebSocket, msg: dict[str, Any]) -> None:
        act = str(msg.get("action", ""))
        try:
            if act == "ping":
                await ws.send_json({"type": "pong"})
                return
            if act in ("create_room", "join_room", "reconnect"):
                room, p = await getattr(self, act)(ws, msg)
                await ws.send_json({"type": "session", "room_code": room.code,
                                    "player_id": p.pid, "secret": p.secret, "name": p.name})
            else:
                room = await self._command(ws, act, msg)
            if room:
                await self.broadcast(room)
                self._kick_bot(room)
        except GameError as exc:
            await ws.send_json({"type": "error", "code": exc.code, "message": exc.message})
        except Exception:
            await ws.send_json({"type": "error", "code": "SERVER_ERROR",
                                "message": "Something went wrong. Try again."})

    async def disconnect(self, ws: WebSocket) -> None:
        hit = self.index.pop(id(ws), None)
        room = self.rooms.get(hit[0]) if hit else None
        if not room:
            return
        async with room.lock:
            p = room.players.get(hit[1])
            if p and room.socks.get(p.pid) is ws:
                room.socks.pop(p.pid, None)
                p.connected = False
                if room.phase == "PLAY" and room.turn == p.pid:
                    self._auto_if_away(room)
        await self.broadcast(room)

    # ---------- session actions ----------
    async def create_room(self, ws: WebSocket, msg: dict[str, Any]) -> tuple[Room, Player]:
        name = self._name(msg.get("name"))
        while (code := "".join(secrets.choice(CODE_CHARS) for _ in range(4))) in self.rooms:
            pass
        room = self.rooms[code] = Room(code=code)
        async with room.lock:
            p = self._add(room, name, msg.get("client_id"), ws)
            room.host = p.pid
            self._say(room, f"{name} opened the table.")
        return room, p

    async def join_room(self, ws: WebSocket, msg: dict[str, Any]) -> tuple[Room, Player]:
        room, name = self._room(msg.get("room_code")), self._name(msg.get("name"))
        async with room.lock:
            if room.phase != "LOBBY":
                raise GameError("STARTED", "That game has already started.")
            same = next((x for x in room.players.values() if x.name.casefold() == name.casefold()), None)
            if same:
                if str(msg.get("client_id") or "") == same.cid and not same.connected:
                    self._attach(room, same, ws)
                    return room, same
                raise GameError("NAME_TAKEN", f'"{name}" is taken at this table. Pick another name.')
            if len(room.players) >= MAX_PLAYERS:
                raise GameError("FULL", "This table is full (6 players max).")
            p = self._add(room, name, msg.get("client_id"), ws)
            self._say(room, f"{name} pulled up a chair.")
        return room, p

    async def reconnect(self, ws: WebSocket, msg: dict[str, Any]) -> tuple[Room, Player]:
        room = self._room(msg.get("room_code"))
        async with room.lock:
            p = room.players.get(str(msg.get("player_id") or ""))
            if not p or p.secret != str(msg.get("secret") or ""):
                raise GameError("INVALID_SESSION", "Could not restore your seat.")
            self._attach(room, p, ws)
        return room, p

    # ---------- in-game commands ----------
    async def _command(self, ws: WebSocket, act: str, msg: dict[str, Any]) -> Room | None:
        hit = self.index.get(id(ws))
        room = self.rooms.get(hit[0]) if hit else None
        if not room or hit[1] not in room.players:
            raise GameError("INVALID_SESSION", "Create or join a table first.")
        p = room.players[hit[1]]
        async with room.lock:
            if act == "start":
                if room.host != p.pid or room.phase != "LOBBY":
                    raise GameError("DENIED", "Only the host can start from the lobby.")
                if sum(x.connected for x in room.players.values()) < MIN_PLAYERS:
                    raise GameError("NEED_PLAYERS", "You need at least 2 players.")
                self._reset(room)
                self._say(room, "Dice are rolling. Last die standing wins.")
                self._deal(room)
            elif act == "rematch":
                if room.host != p.pid or room.phase != "END":
                    raise GameError("DENIED", "Only the host can rematch after a game ends.")
                room.phase, room.reveal, room.winner = "LOBBY", None, ""
                for x in room.players.values():
                    x.count, x.dice = START_DICE, []
            elif act == "bid":
                self._need_turn(room, p)
                try:
                    qty, face = int(msg.get("qty")), int(msg.get("face"))
                except (TypeError, ValueError):
                    raise GameError("BAD_BID", "Enter a quantity and a face.")
                if not self._legal(room, qty, face):
                    raise GameError("BAD_BID", "Raise the quantity, or keep it and raise the face.")
                self._do_bid(room, p, qty, face)
            elif act == "liar":
                self._need_turn(room, p)
                if room.bid is None:
                    raise GameError("BAD_BID", "Nobody has bid yet.")
                dbl = bool(msg.get("double")) and p.power == "double" and not p.power_used
                if dbl:
                    p.power_used = True
                    self._say(room, f"{p.name} plays Double Down!")
                self._do_liar(room, p, dbl)
            elif act == "add_bot":
                if room.host != p.pid or room.phase != "LOBBY":
                    raise GameError("DENIED", "Only the host can add bots in the lobby.")
                if len(room.players) >= MAX_PLAYERS:
                    raise GameError("FULL", "This table is full (6 players max).")
                used = {x.name.casefold() for x in room.players.values()}
                name = next((n for n in BOT_NAMES if n.casefold() not in used), "Bot " + secrets.token_hex(2))
                b = Player(pid=secrets.token_urlsafe(8), secret="", cid="", name=name, bot=True)
                room.players[b.pid] = b
                room.order.append(b.pid)
                self._say(room, f"{name} pulled up a chair.")
            elif act == "power":
                self._use_power(room, p, msg)
            elif act == "leave" and room.phase == "LOBBY":
                room.players.pop(p.pid, None)
                room.order = [x for x in room.order if x != p.pid]
                room.socks.pop(p.pid, None)
                self.index.pop(id(ws), None)
                humans = [i for i, x in room.players.items() if not x.bot]
                if not humans:
                    self.rooms.pop(room.code, None)
                    return None
                if room.host == p.pid:
                    room.host = humans[0]
            else:
                raise GameError("INVALID_ACTION", "That move isn't available right now.")
        return room

    # ---------- rules ----------
    def _alive(self, room: Room) -> list[Player]:
        return [room.players[i] for i in room.order if room.players[i].count > 0]

    def _total(self, room: Room) -> int:
        return sum(x.count for x in self._alive(room))

    def _legal(self, room: Room, qty: int, face: int) -> bool:
        if not (1 <= face <= 6 and 1 <= qty <= self._total(room)):
            return False
        if room.bid is None:
            return True
        cq, cf = room.bid
        return qty > cq or (qty == cq and face > cf)

    def _need_turn(self, room: Room, p: Player) -> None:
        if room.phase != "PLAY" or room.turn != p.pid:
            raise GameError("NOT_YOUR_TURN", "It isn't your turn.")

    def _next(self, room: Room, pid: str) -> str:
        i = room.order.index(pid)
        for k in range(1, len(room.order) + 1):
            cand = room.order[(i + k) % len(room.order)]
            if room.players[cand].count > 0:
                return cand
        return pid

    def _do_bid(self, room: Room, p: Player, qty: int, face: int) -> None:
        room.bid, room.bidder = (qty, face), p.pid
        self._say(room, f"{p.name} bids {qty} x {face}s.")
        room.turn = self._next(room, p.pid)
        self._auto_if_away(room)

    def _do_liar(self, room: Room, caller: Player, double: bool = False) -> None:
        assert room.bid
        qty, face = room.bid
        alive = self._alive(room)
        total = sum(1 for x in alive for d in x.dice if d == face or (face != 1 and d == 1))
        bidder = room.players[room.bidder]
        loser = bidder if total < qty else caller
        shielded = loser.shield
        lost = 0 if shielded else min(2 if double else 1, loser.count)
        loser.shield = False
        loser.count -= lost
        room.reveal = {"dice": {x.name: x.dice for x in alive}, "bid": [qty, face], "total": total,
                       "caller": caller.name, "bidder": bidder.name, "loser": loser.name,
                       "lost": lost, "shielded": shielded, "out": loser.count == 0}
        self._say(room, f"{caller.name} called LIAR. There were {total}. " + (f"{loser.name}'s Shield held!" if shielded else f"{loser.name} loses {lost} di{'ce' if lost > 1 else 'e'}."))
        room.turn = loser.pid if loser.count > 0 else self._next(room, loser.pid)
        left = self._alive(room)
        if len(left) == 1:
            room.phase, room.winner = "END", left[0].name
            self._say(room, f"{left[0].name} is the last die standing!")
        else:
            room.phase = "REVEAL"
            asyncio.get_running_loop().create_task(self._next_round(room.code))

    def _auto_if_away(self, room: Room) -> None:
        """If the player on turn has disconnected, play the minimum for them."""
        while room.phase == "PLAY" and not room.players[room.turn].connected:
            p = room.players[room.turn]
            if room.bid is None:
                self._do_bid(room, p, 1, 2)
                return
            qty, face = room.bid
            nq, nf = (qty, face + 1) if face < 6 else (qty + 1, 2)
            if self._legal(room, nq, nf):
                self._do_bid(room, p, nq, nf)
            else:
                self._do_liar(room, p)
            return

    async def _next_round(self, code: str) -> None:
        await asyncio.sleep(REVEAL_SECONDS)
        room = self.rooms.get(code)
        if not room:
            return
        async with room.lock:
            if room.phase != "REVEAL":
                return
            self._deal(room)
        await self.broadcast(room)
        self._kick_bot(room)

    def _reset(self, room: Room) -> None:
        for x in room.players.values():
            x.count, x.power_used, x.shield, x.note = START_DICE, False, False, ""
            x.power = "" if x.bot else random.choice(POWERS)
        room.order = list(room.players)
        room.turn, room.round = room.order[0], 0

    def _deal(self, room: Room) -> None:
        room.phase, room.reveal, room.bid, room.bidder = "PLAY", None, None, ""
        room.round += 1
        for x in self._alive(room):
            x.dice = sorted(random.randint(1, 6) for _ in range(x.count))
            x.note, x.shield = "", False
        if room.players[room.turn].count == 0:
            room.turn = self._next(room, room.turn)
        self._auto_if_away(room)

    # ---------- power cards ----------
    def _use_power(self, room: Room, p: Player, msg: dict[str, Any]) -> None:
        if room.phase != "PLAY" or not p.power or p.power_used or p.power == "double":
            raise GameError("NO_POWER", "That power isn't available right now.")
        if p.power != "shield":
            self._need_turn(room, p)
        if p.power == "peek":
            t = room.players.get(str(msg.get("target") or ""))
            if not t or t.pid == p.pid or t.count == 0:
                raise GameError("BAD_TARGET", "Pick an opponent who is still in the game.")
            p.note = f"Peek: {t.name} is holding a {DIE[random.choice(t.dice) - 1]}."
        elif p.power == "reroll":
            p.dice = sorted(random.randint(1, 6) for _ in p.dice)
            p.note = "You rerolled your dice."
        else:
            p.shield, p.note = True, "Shield armed: you cannot lose a die this round."
        p.power_used = True
        self._say(room, f"{p.name} used a power card.")

    # ---------- bots ----------
    def _kick_bot(self, room: Room) -> None:
        if room.phase == "PLAY" and room.players[room.turn].bot and not room.bot_busy:
            room.bot_busy = True
            asyncio.get_running_loop().create_task(self._bot_move(room.code))

    async def _bot_move(self, code: str) -> None:
        await asyncio.sleep(BOT_DELAY)
        room = self.rooms.get(code)
        if not room:
            return
        async with room.lock:
            room.bot_busy = False
            p = room.players.get(room.turn)
            if room.phase != "PLAY" or not p or not p.bot:
                return
            move = self._bot_decide(room, p)
            if move == "liar":
                self._do_liar(room, p)
            else:
                self._do_bid(room, p, *move)
        await self.broadcast(room)
        self._kick_bot(room)

    def _bot_decide(self, room: Room, p: Player) -> Any:
        others = self._total(room) - len(p.dice)

        def expect(f: int) -> float:
            mine = sum(1 for d in p.dice if d == f or (f != 1 and d == 1))
            return mine + others * (1 / 6 if f == 1 else 1 / 3)

        if room.bid and room.bid[0] > expect(room.bid[1]) + random.choice((0, 0.5, 1)):
            return "liar"
        total = self._total(room)
        opts = sorted((q, f) for q in range(1, total + 1) for f in range(1, 7) if self._legal(room, q, f))
        if not opts:
            return "liar"
        safe = [o for o in opts if expect(o[1]) >= o[0] - 0.6]
        if safe:
            return random.choice(safe[:3])
        return "liar" if room.bid else opts[0]

    # ---------- plumbing ----------
    def _add(self, room: Room, name: str, cid: object, ws: WebSocket) -> Player:
        p = Player(pid=secrets.token_urlsafe(8), secret=secrets.token_urlsafe(20),
                   cid=str(cid or "")[:120], name=name)
        room.players[p.pid] = p
        room.order.append(p.pid)
        self._attach(room, p, ws)
        return p

    def _attach(self, room: Room, p: Player, ws: WebSocket) -> None:
        p.connected = True
        room.socks[p.pid] = ws
        self.index[id(ws)] = (room.code, p.pid)

    def _say(self, room: Room, text: str) -> None:
        room.log.append(text)
        del room.log[:-30]

    def _room(self, code: object) -> Room:
        key = "".join(c for c in str(code or "").upper() if c.isalnum())
        if key not in self.rooms:
            raise GameError("NO_ROOM", "No table exists for that code.")
        return self.rooms[key]

    def _name(self, name: object) -> str:
        value = " ".join(str(name or "").split())
        if not value or len(value) > 16:
            raise GameError("BAD_NAME", "Enter a name (1-16 characters).")
        return value

    def _view(self, room: Room, pid: str) -> dict[str, Any]:
        me = room.players[pid]
        shown = room.phase in ("REVEAL", "END")
        return {
            "type": "state", "code": room.code, "phase": room.phase, "you": pid,
            "host": room.host, "turn": room.turn, "round": room.round,
            "bid": room.bid, "bidder": room.players[room.bidder].name if room.bidder else "",
            "total": self._total(room) if room.phase != "LOBBY" else 0,
            "dice": me.dice if room.phase == "PLAY" else [],
            "players": [{"id": x.pid, "name": x.name, "count": x.count, "away": not x.connected, "bot": x.bot}
                        for x in (room.players[i] for i in room.order)],
            "reveal": room.reveal if shown else None, "winner": room.winner,
            "log": room.log[-8:], "reveal_seconds": REVEAL_SECONDS,
            "power": me.power, "power_used": me.power_used, "shield": me.shield, "note": me.note,
        }

    async def broadcast(self, room: Room) -> None:
        for pid, ws in list(room.socks.items()):
            try:
                await ws.send_json(self._view(room, pid))
            except Exception:
                room.socks.pop(pid, None)
