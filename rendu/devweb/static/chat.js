const ASSISTANT_AVATAR = document.body.dataset.avatar;
const USER_AVATAR = document.body.dataset.userAvatar;
const DEFAULT_MODEL = document.body.dataset.model;
const STORE = "techcorp_conversations";

const chatInner = document.getElementById("chat-inner");
const chatEl = document.getElementById("chat");
const welcomeEl = document.getElementById("welcome");
const form = document.getElementById("chat-form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const convListEl = document.getElementById("conv-list");
const searchEl = document.getElementById("search");
const newBtn = document.getElementById("new-conv");
const toggleBtn = document.getElementById("toggle-sidebar");
const sidebar = document.getElementById("sidebar");
const modelSelect = document.getElementById("model-select");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");

let conversations = JSON.parse(localStorage.getItem(STORE) || "[]");
let currentId = null;
let messages = [];
let currentModel = DEFAULT_MODEL;
let busy = false;

// Persistance
function persist() {
  localStorage.setItem(STORE, JSON.stringify(conversations.slice(0, 50)));
}

function ensureConversation(firstText) {
  if (currentId) return;
  currentId = Date.now().toString();
  conversations.unshift({
    id: currentId,
    title: firstText.slice(0, 48),
    messages: [],
    updatedAt: Date.now(),
  });
}

function syncCurrent() {
  const conv = conversations.find((c) => c.id === currentId);
  if (conv) {
    conv.messages = [...messages];
    conv.updatedAt = Date.now();
  }
  persist();
  renderConvList();
}

// Markdown (léger, échappé)
function renderMarkdown(text) {
  let h = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  h = h
    .replace(/```(\w*)\n?([\s\S]*?)```/g, "<pre><code>$2</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h4>$1</h4>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/^\s*[-*] (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>[\s\S]*?<\/li>)/g, "<ul>$1</ul>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br>");
  return "<p>" + h + "</p>";
}

// Rendu des messages
function clearMessages() {
  chatInner.querySelectorAll(".msg").forEach((n) => n.remove());
}

function addBubble(role, content, streaming = false) {
  welcomeEl.style.display = "none";
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  const img = document.createElement("img");
  img.src = role === "user" ? USER_AVATAR : ASSISTANT_AVATAR;
  img.alt = role === "user" ? "Patient" : "Assistant";
  avatar.appendChild(img);

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (role === "assistant") {
    bubble.innerHTML = streaming ? '<span class="cursor"></span>' : renderMarkdown(content);
  } else {
    bubble.textContent = content;
  }

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  chatInner.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
  return bubble;
}

function renderMessages() {
  clearMessages();
  if (messages.length === 0) {
    welcomeEl.style.display = "";
    return;
  }
  welcomeEl.style.display = "none";
  for (const m of messages) addBubble(m.role, m.content);
}

// Liste des conversations + recherche
function renderConvList() {
  const q = (searchEl.value || "").toLowerCase().trim();
  const items = conversations
    .filter((c) => {
      if (!q) return true;
      const hay = (c.title + " " + c.messages.map((m) => m.content).join(" ")).toLowerCase();
      return hay.includes(q);
    })
    .sort((a, b) => b.updatedAt - a.updatedAt);

  if (items.length === 0) {
    convListEl.innerHTML = `<div class="conv-empty">${q ? "Aucun résultat" : "Aucune conversation"}</div>`;
    return;
  }
  convListEl.innerHTML = "";
  for (const c of items) {
    const item = document.createElement("div");
    item.className = "conv-item" + (c.id === currentId ? " active" : "");
    const title = document.createElement("span");
    title.className = "title";
    title.textContent = c.title || "Conversation";
    title.onclick = () => loadConversation(c.id);
    const del = document.createElement("button");
    del.className = "del";
    del.textContent = "×";
    del.title = "Supprimer";
    del.onclick = (e) => { e.stopPropagation(); deleteConversation(c.id); };
    item.appendChild(title);
    item.appendChild(del);
    convListEl.appendChild(item);
  }
}

function loadConversation(id) {
  const conv = conversations.find((c) => c.id === id);
  if (!conv) return;
  currentId = id;
  messages = [...conv.messages];
  renderMessages();
  renderConvList();
}

function deleteConversation(id) {
  conversations = conversations.filter((c) => c.id !== id);
  persist();
  if (id === currentId) newConversation();
  else renderConvList();
}

function newConversation() {
  currentId = null;
  messages = [];
  renderMessages();
  renderConvList();
  input.focus();
}

// Envoi
async function sendMessage(text) {
  if (busy || !text.trim()) return;
  busy = true;
  sendBtn.disabled = true;

  ensureConversation(text);
  messages.push({ role: "user", content: text });
  addBubble("user", text);
  syncCurrent();

  const bubble = addBubble("assistant", "", true);
  let answer = "";
  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages, model: currentModel }),
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
          bubble.innerHTML = renderMarkdown(answer) + '<span class="cursor"></span>';
          chatEl.scrollTop = chatEl.scrollHeight;
        }
      }
    }
    bubble.innerHTML = renderMarkdown(answer);
    messages.push({ role: "assistant", content: answer });
    syncCurrent();
  } catch (e) {
    bubble.innerHTML =
      '<em style="color:#e74c3c">Erreur : ' + e.message +
      "<br>Le serveur d'inférence est-il accessible ?</em>";
  } finally {
    busy = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

// Événements
form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value;
  input.value = "";
  input.style.height = "auto";
  sendMessage(text);
});
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
});
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
});
newBtn.addEventListener("click", newConversation);
searchEl.addEventListener("input", renderConvList);
toggleBtn.addEventListener("click", () => sidebar.classList.toggle("collapsed"));
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => sendMessage(chip.textContent));
});

// Modèles
async function loadModels() {
  try {
    const r = await fetch("/api/models");
    const data = await r.json();
    modelSelect.innerHTML = "";
    for (const name of data.models) {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      modelSelect.appendChild(opt);
    }
    currentModel = data.default || data.models[0] || DEFAULT_MODEL;
    modelSelect.value = currentModel;
  } catch {
    modelSelect.innerHTML = `<option>${DEFAULT_MODEL}</option>`;
  }
}
modelSelect.addEventListener("change", () => { currentModel = modelSelect.value; });

// État de connexion
async function checkHealth() {
  try {
    const r = await fetch("/api/health");
    if (!r.ok) throw new Error();
    statusDot.className = "dot online";
    statusText.textContent = "Connecté";
  } catch {
    statusDot.className = "dot offline";
    statusText.textContent = "Déconnecté";
  }
}

// Init
renderMessages();
renderConvList();
loadModels();
checkHealth();
setInterval(checkHealth, 5000);
