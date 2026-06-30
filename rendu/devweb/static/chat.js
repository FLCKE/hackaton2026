// ===================================================================
//  TechCorp — Logique du chat (DEV WEB)
//  - historique persistant (localStorage)
//  - streaming token-par-token depuis /api/chat (NDJSON)
//  - badge d'état de connexion via /api/health
// ===================================================================

const chatEl = document.getElementById("chat");
const welcomeEl = document.getElementById("welcome");
const form = document.getElementById("chat-form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const clearBtn = document.getElementById("clear");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");

const STORAGE_KEY = "techcorp_chat_history";
let messages = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
let busy = false;

// ---- Rendu de l'historique existant ----
function renderAll() {
  chatEl.querySelectorAll(".msg").forEach((n) => n.remove());
  if (messages.length > 0) welcomeEl.style.display = "none";
  for (const m of messages) addBubble(m.role, m.content);
}

function addBubble(role, content) {
  welcomeEl.style.display = "none";
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "🧑" : "🤖";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;
  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
  return bubble;
}

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
}

// ---- Envoi d'un message ----
async function sendMessage(text) {
  if (busy || !text.trim()) return;
  busy = true;
  sendBtn.disabled = true;

  messages.push({ role: "user", content: text });
  addBubble("user", text);
  save();

  const bubble = addBubble("assistant", "");
  const cursor = document.createElement("span");
  cursor.className = "cursor";
  cursor.innerHTML = "&nbsp;";
  bubble.appendChild(cursor);

  let answer = "";
  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    if (!resp.ok) throw new Error("HTTP " + resp.status);

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        const obj = JSON.parse(line);
        if (obj.error) throw new Error(obj.error);
        if (obj.message && obj.message.content) {
          answer += obj.message.content;
          bubble.textContent = answer;
          chatEl.scrollTop = chatEl.scrollHeight;
        }
      }
    }
    messages.push({ role: "assistant", content: answer });
    save();
  } catch (e) {
    bubble.textContent = "⚠️ Erreur : " + e.message + "\n(Le serveur d'inférence est-il accessible ?)";
    bubble.style.color = "#e74c3c";
  } finally {
    busy = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

// ---- Événements UI ----
form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value;
  input.value = "";
  input.style.height = "auto";
  sendMessage(text);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
});

clearBtn.addEventListener("click", () => {
  messages = [];
  save();
  renderAll();
  welcomeEl.style.display = "";
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => sendMessage(chip.textContent));
});

// ---- Badge d'état de connexion (polling toutes les 5 s) ----
async function checkHealth() {
  try {
    const r = await fetch("/api/health");
    if (r.ok) {
      statusDot.className = "dot online";
      statusText.textContent = "Connecté";
    } else {
      throw new Error();
    }
  } catch {
    statusDot.className = "dot offline";
    statusText.textContent = "Déconnecté";
  }
}

renderAll();
checkHealth();
setInterval(checkHealth, 5000);
