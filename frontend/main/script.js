let thinkingTimeout = null;
let latestThinkingMessage = null;

const sendBtn = document.querySelector(".send-btn");
const userInput = document.getElementById('userInput');
const chatColumn = document.querySelector(".chat-column");
const textarea = document.querySelector(".input-container textarea");


function disableSend() {sendBtn.disabled = true;}

function enableSend() {sendBtn.disabled = false;}

function scrollChatToBottom() {chatColumn.parentElement.scrollTop = chatColumn.parentElement.scrollHeight;}

function hideWelcomeBlockIfNeeded() {
    const block = document.getElementById("welcome-block");
    if (!block) return;
    block.classList.add("hidden");
    setTimeout(() => block.remove(), 400);
}

function createThinkingMessage() {
  const msg = document.createElement("div");
  msg.className = "message bot thinking";

  msg.innerHTML = `
      <div class="bubble">
          <div class="text">Thinking…</div>
      </div>
  `;

  return msg;
}

function createErrorMessage() {
  const msg = document.createElement("div");
  msg.className = "message bot error";

  msg.innerHTML = `
      <div class="bubble">
          <div class="text">Hmm… something went wrong. Please try again later.</div>
      </div>
  `;

  return msg;
}

function createUserMessage(text) {
  const msg = document.createElement("div");
  msg.className = "message user";

  msg.innerHTML = `
      <div class="bubble">
          <div class="text">${text}</div>
          <div class="actions user-actions">
              <img src="../resource/icons8-copy-100.png" class="action-icon action-copy">
          </div>
      </div>
  `;

  return msg;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function createBotMessage(text, messageId) {
  const msg = document.createElement("div");
  msg.className = "message bot";

  let html = "";
  try {
    html = marked.parse(text);
  } catch {
    html = escapeHtml(text);
  }

  msg.innerHTML = `
      <div class="bubble">
          <div class="text">${html}</div>
          <div class="actions bot-actions">
              <img src="../resource/icons8-copy-100.png" class="action-icon action-copy">
              <img src="../resource/icons8-thumbs-up-100.png" class="action-icon">
              <img src="../resource/icons8-thumbs-down-100.png" class="action-icon">
              <div class="sources-link" data-id="${messageId}">Sources</div>
          </div>
      </div>
  `;

  msg.querySelector(".sources-link").addEventListener("click", () => {
  const docs = sessionStorage.getItem(`sources_${messageId}`);
  if (docs) {
    sessionStorage.setItem("retrieved_sources", docs);
  }
  window.open("../sources/sources_page.html", "_blank");
  });
  
  return msg;
}

async function apiCall(userQuestion) {
  const response = await fetch("http://localhost:3000/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: userQuestion
    })
  });

  const data = await response.json();
  return data;
}

async function handleUserMessage(question, messageId) {
  const data = await apiCall(question);

  const answer = data.answer;
  const documents = data.documents;

  sessionStorage.setItem(`sources_${messageId}`, JSON.stringify(documents));

  return { answer, messageId };
}

document.addEventListener("click", async (e) => {
    if (!e.target.classList.contains("action-copy")) return;

    const bubble = e.target.closest(".bubble");
    if (!bubble) return;

    const textElement = bubble.querySelector(".text");
    const textToCopy = textElement?.innerText || "";

    try {
        await navigator.clipboard.writeText(textToCopy);
        e.target.style.opacity = "0.5";
        setTimeout(() => { e.target.style.opacity = "1"; }, 300);

    } catch (err) {
        console.error("Copy failed:", err);
    }
});

async function handleSend() {
  hideWelcomeBlockIfNeeded();
  const text = textarea.value.trim();
  if (!text) return;

  disableSend();

  chatColumn.appendChild(createUserMessage(text));

  textarea.value = "";
  textarea.style.height = "auto";

  const thinkingMsg = createThinkingMessage();
  chatColumn.appendChild(thinkingMsg);
  scrollChatToBottom();

  const messageId = Date.now().toString();

  try {
    const { answer, messageId: returnedId } = await handleUserMessage(text, messageId);

    thinkingMsg.remove();

    chatColumn.appendChild(createBotMessage(answer, returnedId));

  } catch (err) {
    thinkingMsg.remove();
    chatColumn.appendChild(createErrorMessage());
  }

  scrollChatToBottom();
  enableSend();
}

textarea.addEventListener("input", () => {
  textarea.style.height = "auto";
  textarea.style.height = textarea.scrollHeight + "px";
});

textarea.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

sendBtn.addEventListener("click", handleSend);