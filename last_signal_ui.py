from __future__ import annotations


LAST_SIGNAL_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>The Last Signal</title>
    <style>
      :root {
        --bg: #071014;
        --panel: rgba(13, 24, 29, 0.92);
        --panel-strong: #102027;
        --line: rgba(135, 255, 218, 0.2);
        --ink: #f0fff9;
        --muted: #9bb8b3;
        --cyan: #68f7ce;
        --cyan-soft: rgba(104, 247, 206, 0.15);
        --red: #ff5c57;
        --red-soft: rgba(255, 92, 87, 0.14);
        --amber: #ffc857;
        --violet: #9b8cff;
        --shadow: 0 22px 70px rgba(0, 0, 0, 0.42);
      }

      * { box-sizing: border-box; }
      html { min-height: 100%; background: var(--bg); }
      body {
        background:
          linear-gradient(180deg, rgba(7, 16, 20, 0.76), rgba(7, 16, 20, 0.98)),
          repeating-linear-gradient(90deg, rgba(104, 247, 206, 0.03) 0 1px, transparent 1px 7px);
        color: var(--ink);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
        min-height: 100vh;
        overflow-x: hidden;
      }

      body::after {
        background: repeating-linear-gradient(180deg, rgba(255,255,255,0.035) 0 1px, transparent 1px 4px);
        content: "";
        inset: 0;
        opacity: 0.35;
        pointer-events: none;
        position: fixed;
        z-index: 1;
      }

      button, input { font: inherit; }
      button {
        border: 0;
        border-radius: 8px;
        cursor: pointer;
        min-height: 46px;
      }
      button:disabled {
        cursor: not-allowed;
        opacity: 0.48;
      }
      input {
        background: rgba(240, 255, 249, 0.08);
        border: 1px solid var(--line);
        border-radius: 8px;
        color: var(--ink);
        min-height: 48px;
        outline: none;
        padding: 12px 14px;
        width: 100%;
      }
      input::placeholder { color: rgba(155, 184, 179, 0.78); }
      h1, h2, h3, p { margin: 0; }
      h1 {
        font-size: clamp(2rem, 7vw, 4.6rem);
        letter-spacing: 0;
        line-height: 0.92;
        text-transform: uppercase;
      }
      h2 { font-size: 1rem; letter-spacing: 0; text-transform: uppercase; }
      h3 { font-size: 0.95rem; }

      #corridorCanvas {
        inset: 0;
        position: fixed;
        width: 100vw;
        height: 100vh;
        z-index: 0;
      }

      .app {
        display: grid;
        gap: 16px;
        margin: 0 auto;
        max-width: 1520px;
        min-height: 100vh;
        padding: 16px;
        position: relative;
        z-index: 2;
      }

      .topbar {
        align-items: center;
        display: flex;
        gap: 12px;
        justify-content: space-between;
      }
      .brand {
        display: grid;
        gap: 4px;
      }
      .kicker {
        color: var(--cyan);
        font-size: 0.75rem;
        font-weight: 900;
        letter-spacing: 0.16em;
        text-transform: uppercase;
      }
      .status-row {
        align-items: center;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
      }
      .chip {
        align-items: center;
        background: rgba(16, 32, 39, 0.82);
        border: 1px solid var(--line);
        border-radius: 999px;
        color: var(--muted);
        display: inline-flex;
        font-size: 0.78rem;
        font-weight: 800;
        gap: 8px;
        min-height: 34px;
        padding: 7px 10px;
      }
      .dot {
        background: var(--red);
        border-radius: 50%;
        box-shadow: 0 0 14px var(--red);
        height: 8px;
        width: 8px;
      }
      .dot.online { background: var(--cyan); box-shadow: 0 0 14px var(--cyan); }

      .layout {
        display: grid;
        gap: 16px;
        grid-template-columns: minmax(0, 1.22fr) minmax(330px, 0.78fr);
        align-items: start;
      }
      .surface {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: var(--shadow);
        overflow: hidden;
      }
      .main-surface {
        min-height: calc(100vh - 134px);
      }
      .side-surface {
        display: grid;
        gap: 0;
        position: sticky;
        top: 16px;
      }
      .section {
        border-bottom: 1px solid rgba(135, 255, 218, 0.13);
        display: grid;
        gap: 14px;
        padding: 18px;
      }
      .section:last-child { border-bottom: 0; }
      .panel-title {
        align-items: center;
        display: flex;
        gap: 10px;
        justify-content: space-between;
      }
      .muted {
        color: var(--muted);
        line-height: 1.45;
      }
      .primary, .secondary, .danger, .ghost {
        color: var(--ink);
        font-weight: 900;
        padding: 11px 14px;
      }
      .primary {
        background: var(--cyan);
        color: #061412;
      }
      .secondary {
        background: rgba(104, 247, 206, 0.13);
        border: 1px solid var(--line);
      }
      .danger {
        background: var(--red-soft);
        border: 1px solid rgba(255, 92, 87, 0.36);
        color: #ffd8d6;
      }
      .ghost {
        background: rgba(240, 255, 249, 0.07);
        border: 1px solid rgba(240, 255, 249, 0.14);
      }

      .join-grid {
        display: grid;
        gap: 12px;
        grid-template-columns: minmax(0, 1fr) minmax(0, 0.55fr);
      }
      .join-actions {
        display: grid;
        gap: 10px;
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .code-box {
        background: rgba(104, 247, 206, 0.1);
        border: 1px dashed rgba(104, 247, 206, 0.45);
        border-radius: 8px;
        display: grid;
        gap: 9px;
        padding: 14px;
      }
      .code {
        color: var(--cyan);
        font-size: clamp(2.25rem, 13vw, 5rem);
        font-weight: 950;
        letter-spacing: 0.12em;
        line-height: 0.9;
      }
      .warning-text {
        color: var(--amber);
        font-size: 0.8rem;
        font-weight: 950;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      .phase-grid {
        display: grid;
        gap: 16px;
        grid-template-columns: minmax(0, 1fr) minmax(220px, 0.38fr);
      }
      .phase-copy {
        display: grid;
        gap: 10px;
      }
      .phase-title {
        color: var(--cyan);
        font-size: clamp(1.35rem, 5vw, 2.6rem);
        font-weight: 950;
        line-height: 1;
        text-transform: uppercase;
      }
      .timer {
        align-content: center;
        background: linear-gradient(180deg, rgba(255, 92, 87, 0.18), rgba(104, 247, 206, 0.08));
        border: 1px solid rgba(255, 92, 87, 0.3);
        border-radius: 8px;
        display: grid;
        gap: 6px;
        justify-items: center;
        min-height: 128px;
        padding: 14px;
      }
      .timer strong {
        color: var(--amber);
        font-size: 2.4rem;
        line-height: 1;
      }
      .players {
        display: grid;
        gap: 8px;
      }
      .player {
        align-items: center;
        background: rgba(240, 255, 249, 0.055);
        border: 1px solid rgba(240, 255, 249, 0.1);
        border-radius: 8px;
        display: grid;
        gap: 8px;
        grid-template-columns: 1fr auto;
        min-height: 50px;
        padding: 9px 11px;
      }
      .badges {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        justify-content: flex-end;
      }
      .badge {
        border: 1px solid rgba(240, 255, 249, 0.15);
        border-radius: 999px;
        color: var(--muted);
        font-size: 0.68rem;
        font-weight: 900;
        padding: 3px 7px;
        text-transform: uppercase;
      }
      .badge.ready, .badge.host, .badge.voted { color: var(--cyan); border-color: rgba(104, 247, 206, 0.36); }
      .badge.lost { color: #ffb4b0; border-color: rgba(255, 92, 87, 0.34); }

      .clue-list, .event-list, .consequence-list {
        display: grid;
        gap: 10px;
      }
      .clue, .event, .consequence {
        background: rgba(240, 255, 249, 0.055);
        border: 1px solid rgba(240, 255, 249, 0.11);
        border-radius: 8px;
        display: grid;
        gap: 5px;
        padding: 12px;
      }
      .clue {
        background: rgba(104, 247, 206, 0.1);
        border-color: rgba(104, 247, 206, 0.28);
      }
      .clue strong, .consequence strong { color: var(--cyan); }
      .event strong { color: var(--amber); }

      .vote-options {
        display: grid;
        gap: 10px;
      }
      .vote-button {
        align-items: start;
        background: rgba(240, 255, 249, 0.07);
        border: 1px solid rgba(104, 247, 206, 0.22);
        color: var(--ink);
        display: grid;
        gap: 4px;
        justify-items: start;
        min-height: 68px;
        padding: 12px;
        text-align: left;
        width: 100%;
      }
      .vote-button.selected {
        background: rgba(104, 247, 206, 0.22);
        border-color: var(--cyan);
      }
      .vote-button span { color: var(--muted); font-size: 0.85rem; }
      .meter-grid {
        display: grid;
        gap: 10px;
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .meter {
        display: grid;
        gap: 6px;
      }
      .bar {
        background: rgba(240, 255, 249, 0.08);
        border-radius: 999px;
        height: 8px;
        overflow: hidden;
      }
      .bar span {
        background: var(--cyan);
        display: block;
        height: 100%;
        width: 0;
      }
      .bar.red span { background: var(--red); }
      .bar.amber span { background: var(--amber); }
      .bar.violet span { background: var(--violet); }

      .chat-log {
        display: grid;
        gap: 8px;
        max-height: 260px;
        overflow-y: auto;
        padding-right: 4px;
      }
      .message {
        background: rgba(240, 255, 249, 0.055);
        border: 1px solid rgba(240, 255, 249, 0.1);
        border-radius: 8px;
        display: grid;
        gap: 3px;
        padding: 10px;
      }
      .message strong { color: var(--cyan); }
      .chat-form {
        display: grid;
        gap: 8px;
        grid-template-columns: minmax(0, 1fr) auto;
      }
      .toast {
        background: rgba(255, 92, 87, 0.15);
        border: 1px solid rgba(255, 92, 87, 0.36);
        border-radius: 8px;
        color: #ffd8d6;
        display: none;
        padding: 12px;
      }
      .toast.active { display: block; }
      .hidden { display: none !important; }
      .ending-screen {
        background: linear-gradient(135deg, rgba(104, 247, 206, 0.16), rgba(155, 140, 255, 0.12));
        border: 1px solid rgba(104, 247, 206, 0.34);
        border-radius: 8px;
        display: grid;
        gap: 14px;
        padding: 18px;
      }

      @media (max-width: 980px) {
        .layout { grid-template-columns: 1fr; }
        .side-surface { position: static; }
        .main-surface { min-height: 0; }
      }
      @media (max-width: 680px) {
        .app { padding: 10px; }
        .topbar { align-items: stretch; flex-direction: column; }
        .status-row { justify-content: flex-start; }
        .join-grid, .join-actions, .phase-grid, .meter-grid { grid-template-columns: 1fr; }
        .code { font-size: 3.1rem; }
        .section { padding: 14px; }
        .chat-form { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <canvas id="corridorCanvas" aria-hidden="true"></canvas>
    <main class="app">
      <header class="topbar">
        <div class="brand">
          <span class="kicker">ORPHEUS FACILITY</span>
          <h1>The Last Signal</h1>
        </div>
        <div class="status-row">
          <span class="chip"><span class="dot" id="connectionDot"></span><span id="connectionText">Offline</span></span>
          <button class="ghost" id="audioButton" type="button">Audio Off</button>
          <button class="ghost" id="resetSession" type="button">Clear Session</button>
        </div>
      </header>

      <div class="toast" id="toast"></div>

      <div class="layout">
        <section class="surface main-surface">
          <div class="section" id="joinSection">
            <div class="panel-title">
              <h2>Enter Facility</h2>
              <span class="chip">2-10 players</span>
            </div>
            <p class="muted">Create a room, share the code, or join an existing crew. No account or install required.</p>
            <div class="join-grid">
              <input id="callsignInput" maxlength="18" placeholder="Callsign">
              <input id="roomCodeInput" maxlength="4" placeholder="Room code">
            </div>
            <div class="join-actions">
              <button class="primary" id="createRoom" type="button">Create Room</button>
              <button class="secondary" id="joinRoom" type="button">Join Room</button>
            </div>
          </div>

          <div class="section hidden" id="roomSection">
            <div class="code-box">
              <span class="warning-text">SHARE THIS CODE WITH YOUR CREW</span>
              <div class="code" id="roomCode">----</div>
              <button class="secondary" id="copyCode" type="button">Copy Code</button>
            </div>
          </div>

          <div class="section hidden" id="phaseSection">
            <div class="phase-grid">
              <div class="phase-copy">
                <span class="kicker" id="phaseId">LOBBY</span>
                <div class="phase-title" id="phaseTitle">Crew Assembly</div>
                <p class="muted" id="phaseBrief"></p>
                <p id="phaseObjective"></p>
              </div>
              <div class="timer">
                <span class="warning-text">Countdown</span>
                <strong id="countdown">--:--</strong>
                <span class="muted" id="timerHint">Server time</span>
              </div>
            </div>
          </div>

          <div class="section hidden" id="endingSection"></div>

          <div class="section hidden" id="privateSection">
            <div class="panel-title">
              <h2 id="privateHeading">Private Signal</h2>
              <span class="chip">Only you receive this feed</span>
            </div>
            <div class="clue-list" id="privateClues"></div>
          </div>

          <div class="section hidden" id="voteSection">
            <div class="panel-title">
              <h2>Decision</h2>
              <span class="chip" id="voteCount">0/0 voted</span>
            </div>
            <p id="votePrompt"></p>
            <div class="vote-options" id="voteOptions"></div>
          </div>

          <div class="section hidden" id="consequenceSection">
            <div class="panel-title">
              <h2>Facility Consequences</h2>
            </div>
            <div class="consequence-list" id="consequences"></div>
          </div>
        </section>

        <aside class="surface side-surface">
          <div class="section hidden" id="lobbyActions">
            <div class="panel-title">
              <h2>Lobby Controls</h2>
              <span class="chip" id="readySummary">0/0 ready</span>
            </div>
            <button class="secondary" id="readyButton" type="button">Mark Ready</button>
            <button class="primary" id="startGame" type="button">Start Simulation</button>
          </div>

          <div class="section hidden" id="playersSection">
            <div class="panel-title">
              <h2>Crew Manifest</h2>
              <span class="chip" id="playerCount">0 players</span>
            </div>
            <div class="players" id="players"></div>
          </div>

          <div class="section hidden" id="experimentSection">
            <div class="panel-title">
              <h2>Observation Metrics</h2>
            </div>
            <div class="meter-grid" id="metrics"></div>
          </div>

          <div class="section hidden" id="chatSection">
            <div class="panel-title">
              <h2>Crew Chat</h2>
              <span class="chip">Rate limited</span>
            </div>
            <div class="chat-log" id="chatLog"></div>
            <form class="chat-form" id="chatForm">
              <input id="chatInput" maxlength="280" placeholder="Transmit to crew">
              <button class="secondary" type="submit">Send</button>
            </form>
          </div>

          <div class="section hidden" id="eventsSection">
            <div class="panel-title">
              <h2>System Log</h2>
            </div>
            <div class="event-list" id="events"></div>
          </div>
        </aside>
      </div>
    </main>

    <script>
      const $ = (selector) => document.querySelector(selector);
      const state = {
        socket: null,
        game: null,
        connected: false,
        reconnectTimer: null,
        reconnectDelay: 900,
        clockOffsetMs: 0,
        lastPhase: null,
        audio: null,
        muted: true
      };
      const SESSION_KEY = "lastSignalSession";
      const CLIENT_KEY = "lastSignalClientId";

      function clientId() {
        let value = localStorage.getItem(CLIENT_KEY);
        if (!value) {
          value = crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random();
          localStorage.setItem(CLIENT_KEY, value);
        }
        return value;
      }

      function savedSession() {
        try { return JSON.parse(sessionStorage.getItem(SESSION_KEY) || "null"); }
        catch { return null; }
      }

      function saveSession(payload) {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify({
          room_code: payload.room_code,
          player_id: payload.player_id,
          secret: payload.secret,
          callsign: payload.callsign
        }));
      }

      function escapeHtml(value) {
        return String(value ?? "")
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#039;");
      }

      function attr(value) { return escapeHtml(value).replaceAll("`", "&#096;"); }

      function send(payload) {
        if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
          showToast("Connection lost. Reconnecting to ORPHEUS.");
          connect();
          return;
        }
        state.socket.send(JSON.stringify(payload));
      }

      function connect() {
        if (state.socket && [WebSocket.OPEN, WebSocket.CONNECTING].includes(state.socket.readyState)) return;
        const protocol = location.protocol === "https:" ? "wss" : "ws";
        const socket = new WebSocket(`${protocol}://${location.host}/ws/last-signal`);
        state.socket = socket;
        socket.addEventListener("open", () => {
          state.connected = true;
          state.reconnectDelay = 900;
          renderConnection();
          const session = savedSession();
          if (session) {
            send({ action: "reconnect", ...session });
          }
        });
        socket.addEventListener("message", (event) => {
          const payload = JSON.parse(event.data);
          if (payload.type === "session") {
            saveSession(payload);
            $("#callsignInput").value = payload.callsign || $("#callsignInput").value;
          } else if (payload.type === "state") {
            state.game = payload.state;
            const serverNow = Number(payload.state.phase.server_now || 0) * 1000;
            state.clockOffsetMs = serverNow - Date.now();
            if (state.lastPhase && state.lastPhase !== payload.state.phase.id) playTone(880, 0.08);
            state.lastPhase = payload.state.phase.id;
            render();
          } else if (payload.type === "error") {
            if (payload.code === "INVALID_SESSION") sessionStorage.removeItem(SESSION_KEY);
            showToast(payload.message || "ORPHEUS rejected that command.");
          }
        });
        socket.addEventListener("close", () => {
          state.connected = false;
          renderConnection();
          scheduleReconnect();
        });
        socket.addEventListener("error", () => {
          state.connected = false;
          renderConnection();
        });
      }

      function scheduleReconnect() {
        clearTimeout(state.reconnectTimer);
        state.reconnectTimer = setTimeout(() => {
          state.reconnectDelay = Math.min(state.reconnectDelay * 1.6, 6000);
          connect();
        }, state.reconnectDelay);
      }

      function renderConnection() {
        $("#connectionDot").classList.toggle("online", state.connected);
        $("#connectionText").textContent = state.connected ? "Connected" : "Reconnecting";
      }

      function showToast(message) {
        const toast = $("#toast");
        toast.textContent = message;
        toast.classList.add("active");
        clearTimeout(showToast.timer);
        showToast.timer = setTimeout(() => toast.classList.remove("active"), 4200);
      }

      function timeLeft() {
        const game = state.game;
        if (!game || !game.phase.ends_at) return "--:--";
        const serverNow = (Date.now() + state.clockOffsetMs) / 1000;
        const seconds = Math.max(0, Math.ceil(game.phase.ends_at - serverNow));
        const minutes = Math.floor(seconds / 60);
        return `${String(minutes).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
      }

      function render() {
        const game = state.game;
        const hasGame = Boolean(game);
        $("#joinSection").classList.toggle("hidden", hasGame);
        $("#roomSection").classList.toggle("hidden", !hasGame);
        $("#phaseSection").classList.toggle("hidden", !hasGame);
        $("#playersSection").classList.toggle("hidden", !hasGame);
        $("#experimentSection").classList.toggle("hidden", !hasGame);
        $("#chatSection").classList.toggle("hidden", !hasGame);
        $("#eventsSection").classList.toggle("hidden", !hasGame);
        $("#lobbyActions").classList.toggle("hidden", !hasGame || game.phase.id !== "LOBBY");
        $("#privateSection").classList.toggle("hidden", !hasGame);
        $("#voteSection").classList.toggle("hidden", !hasGame || !game.vote || game.phase.id === "ENDING");
        $("#endingSection").classList.toggle("hidden", !hasGame || game.phase.id !== "ENDING");
        $("#consequenceSection").classList.toggle("hidden", !hasGame || !game.consequences.length);
        if (!game) return;

        $("#roomCode").textContent = game.room.code;
        $("#phaseId").textContent = game.phase.id.replaceAll("_", " ");
        $("#phaseTitle").textContent = game.phase.title;
        $("#phaseBrief").textContent = game.phase.brief;
        $("#phaseObjective").textContent = game.phase.objective;
        $("#countdown").textContent = timeLeft();
        $("#timerHint").textContent = game.phase.ends_at ? "Server controlled" : "No active timer";
        renderPlayers(game);
        renderLobby(game);
        renderPrivate(game);
        renderVote(game);
        renderConsequences(game);
        renderEvents(game);
        renderChat(game);
        renderMetrics(game);
        renderEnding(game);
      }

      function renderPlayers(game) {
        $("#playerCount").textContent = `${game.players.length}/${game.room.max_players} players`;
        $("#players").innerHTML = game.players.map((player) => `
          <div class="player">
            <div>
              <strong>${escapeHtml(player.callsign)}</strong>
              <p class="muted">${player.is_you ? "Your signal" : "Crew signal"}</p>
            </div>
            <div class="badges">
              ${player.is_host ? '<span class="badge host">Host</span>' : ""}
              ${player.ready ? '<span class="badge ready">Ready</span>' : ""}
              ${player.voted ? '<span class="badge voted">Voted</span>' : ""}
              ${player.connected ? "" : '<span class="badge lost">Lost</span>'}
            </div>
          </div>
        `).join("");
      }

      function renderLobby(game) {
        const ready = game.players.filter((player) => player.ready && player.connected).length;
        const connected = game.players.filter((player) => player.connected).length;
        $("#readySummary").textContent = `${ready}/${connected} ready`;
        $("#readyButton").textContent = game.you.ready ? "Cancel Ready" : "Mark Ready";
        $("#startGame").disabled = !game.you.is_host || connected < game.room.min_players || ready < connected;
      }

      function renderPrivate(game) {
        $("#privateHeading").textContent = game.private.heading || "PRIVATE SIGNAL";
        $("#privateClues").innerHTML = game.private.clues.map((clue) => `
          <article class="clue">
            <strong>${escapeHtml(clue.label)}</strong>
            <p>${escapeHtml(clue.text)}</p>
          </article>
        `).join("");
      }

      function renderVote(game) {
        if (!game.vote) return;
        $("#votePrompt").textContent = game.vote.prompt;
        $("#voteCount").textContent = `${game.vote.votes_cast}/${game.vote.connected_total} voted`;
        $("#voteOptions").innerHTML = game.vote.options.map((option) => {
          const selected = game.you.vote === option.id;
          const count = game.vote.counts[option.id] || 0;
          return `
            <button class="vote-button ${selected ? "selected" : ""}" data-choice="${attr(option.id)}" ${game.you.voted ? "disabled" : ""} type="button">
              <strong>${escapeHtml(option.label)} ${count ? "(" + count + ")" : ""}</strong>
              <span>${escapeHtml(option.detail)}</span>
            </button>
          `;
        }).join("");
      }

      function renderConsequences(game) {
        $("#consequences").innerHTML = game.consequences.slice().reverse().map((item) => `
          <article class="consequence">
            <strong>${escapeHtml(item.title)}</strong>
            <p>${escapeHtml(item.body)}</p>
          </article>
        `).join("");
      }

      function renderEvents(game) {
        $("#events").innerHTML = game.events.slice().reverse().slice(0, 8).map((item) => `
          <article class="event">
            <strong>${escapeHtml(item.title)}</strong>
            <p class="muted">${escapeHtml(item.body)}</p>
          </article>
        `).join("");
      }

      function renderChat(game) {
        $("#chatForm").classList.toggle("hidden", game.phase.id === "ENDING");
        $("#chatLog").innerHTML = game.chat.map((message) => `
          <div class="message">
            <strong>${escapeHtml(message.callsign)}</strong>
            <p>${escapeHtml(message.message)}</p>
          </div>
        `).join("") || '<p class="muted">No transmissions yet.</p>';
        $("#chatLog").scrollTop = $("#chatLog").scrollHeight;
      }

      function renderMetrics(game) {
        const metrics = [
          ["Trust", game.experiment.trust, "cyan"],
          ["Fracture", game.experiment.fracture, "red"],
          ["Risk", game.experiment.risk, "amber"],
          ["Cooperation", game.experiment.cooperation, "violet"]
        ];
        $("#metrics").innerHTML = metrics.map(([label, value, color]) => `
          <div class="meter">
            <div class="panel-title"><span>${label}</span><strong>${value}</strong></div>
            <div class="bar ${color}"><span style="width:${Math.max(0, Math.min(100, value))}%"></span></div>
          </div>
        `).join("");
      }

      function renderEnding(game) {
        if (!game.ending) return;
        $("#endingSection").innerHTML = `
          <div class="ending-screen">
            <span class="warning-text">Final ORPHEUS Report</span>
            <div class="phase-title">${escapeHtml(game.ending.title)}</div>
            <p>${escapeHtml(game.ending.body)}</p>
            <p class="muted">Choice: ${escapeHtml(game.ending.choice)}. Trust ${game.ending.metrics.trust}. Fracture ${game.ending.metrics.fracture}. Risk ${game.ending.metrics.risk}.</p>
          </div>
        `;
      }

      function toggleAudio() {
        state.muted = !state.muted;
        $("#audioButton").textContent = state.muted ? "Audio Off" : "Audio On";
        if (!state.muted && !state.audio) startAudio();
        if (state.audio) state.audio.master.gain.setTargetAtTime(state.muted ? 0 : 0.045, state.audio.ctx.currentTime, 0.04);
      }

      function startAudio() {
        const ctx = new AudioContext();
        const master = ctx.createGain();
        const hum = ctx.createOscillator();
        const pulse = ctx.createOscillator();
        hum.type = "sawtooth";
        hum.frequency.value = 43;
        pulse.type = "sine";
        pulse.frequency.value = 0.8;
        const pulseGain = ctx.createGain();
        pulseGain.gain.value = 0.018;
        hum.connect(pulseGain).connect(master).connect(ctx.destination);
        pulse.connect(pulseGain.gain);
        master.gain.value = 0.045;
        hum.start();
        pulse.start();
        state.audio = { ctx, master };
      }

      function playTone(freq, duration) {
        if (state.muted || !state.audio) return;
        const ctx = state.audio.ctx;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "square";
        osc.frequency.value = freq;
        gain.gain.value = 0.001;
        osc.connect(gain).connect(state.audio.master);
        gain.gain.setValueAtTime(0.001, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.08, ctx.currentTime + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
        osc.start();
        osc.stop(ctx.currentTime + duration + 0.02);
      }

      function drawCorridor() {
        const canvas = $("#corridorCanvas");
        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        const w = Math.floor(innerWidth * dpr);
        const h = Math.floor(innerHeight * dpr);
        if (canvas.width !== w || canvas.height !== h) {
          canvas.width = w;
          canvas.height = h;
        }
        const t = performance.now() / 1000;
        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = "#071014";
        ctx.fillRect(0, 0, w, h);

        const cx = w / 2;
        const cy = h * 0.48;
        ctx.strokeStyle = "rgba(104,247,206,0.14)";
        ctx.lineWidth = 2 * dpr;
        for (let i = 0; i < 18; i++) {
          const y = h - i * h * 0.06;
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(cx, cy);
          ctx.lineTo(w, y);
          ctx.stroke();
        }
        for (let i = -6; i <= 6; i++) {
          const x = cx + i * w * 0.075;
          ctx.beginPath();
          ctx.moveTo(x, h);
          ctx.lineTo(cx + i * w * 0.006, cy);
          ctx.stroke();
        }
        ctx.fillStyle = `rgba(255,92,87,${0.08 + Math.sin(t * 5) * 0.03})`;
        ctx.fillRect(0, h * 0.18, w, h * 0.08);
        ctx.fillRect(0, h * 0.74, w, h * 0.05);
        ctx.fillStyle = "rgba(104,247,206,0.11)";
        ctx.font = `${18 * dpr}px monospace`;
        for (let i = 0; i < 8; i++) {
          const x = (i * 173 * dpr + (t * 12 * dpr)) % w;
          const y = h * (0.16 + (i % 4) * 0.17);
          ctx.fillText(["K-17", "ORPHEUS", "SIG-0", "HUMAN?", "LOOP"][i % 5], x, y);
        }
        requestAnimationFrame(drawCorridor);
      }

      $("#createRoom").addEventListener("click", () => {
        send({ action: "create_room", callsign: $("#callsignInput").value, client_id: clientId() });
      });
      $("#joinRoom").addEventListener("click", () => {
        send({
          action: "join_room",
          callsign: $("#callsignInput").value,
          room_code: $("#roomCodeInput").value,
          client_id: clientId()
        });
      });
      $("#readyButton").addEventListener("click", () => send({ action: "set_ready", ready: !state.game?.you.ready }));
      $("#startGame").addEventListener("click", () => send({ action: "start_game" }));
      $("#copyCode").addEventListener("click", async () => {
        if (!state.game) return;
        await navigator.clipboard.writeText(state.game.room.code);
        showToast("Room code copied.");
      });
      $("#voteOptions").addEventListener("click", (event) => {
        const button = event.target.closest("button[data-choice]");
        if (button) send({ action: "vote", choice: button.dataset.choice });
      });
      $("#chatForm").addEventListener("submit", (event) => {
        event.preventDefault();
        const input = $("#chatInput");
        const message = input.value.trim();
        if (!message) return;
        input.value = "";
        send({ action: "chat", message });
      });
      $("#audioButton").addEventListener("click", toggleAudio);
      $("#resetSession").addEventListener("click", () => {
        if (state.game && state.socket && state.socket.readyState === WebSocket.OPEN) {
          state.socket.send(JSON.stringify({ action: "leave_room" }));
        }
        sessionStorage.removeItem(SESSION_KEY);
        state.game = null;
        $("#callsignInput").value = "";
        $("#roomCodeInput").value = "";
        render();
        showToast("Session cleared. Enter a callsign and room code.");
      });
      setInterval(() => {
        if (state.game) $("#countdown").textContent = timeLeft();
      }, 500);
      renderConnection();
      render();
      connect();
      drawCorridor();
    </script>
  </body>
</html>
"""
