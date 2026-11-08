const API_URL = ["localhost", "127.0.0.1"].includes(location.hostname)
  ? "/ask/stream"
  : "https://aquib8112--financebench-backend-api.modal.run/ask/stream";

// Keep these aliases and the default threshold in sync with backend/rag/utils.py.
const COMPANY_ALIASES = {
  "3m": ["3m"],
  "activisionblizzard": ["activision blizzard", "activision", "blizzard"],
  "adobe": ["adobe"],
  "aes": ["aes", "applied energy services"],
  "amazon": ["amazon"],
  "amcor": ["amcor"],
  "amd": ["amd", "advanced micro devices"],
  "americanexpress": ["american express", "amex"],
  "americanwaterworks": ["american water works"],
  "bestbuy": ["best buy"],
  "block": ["block", "square"],
  "boeing": ["boeing"],
  "cocacola": ["coca cola", "coke"],
  "corning": ["corning"],
  "costco": ["costco"],
  "cvshealth": ["cvs", "cvs health"],
  "footlocker": ["foot locker", "footlocker"],
  "generalmills": ["general mills"],
  "johnson_johnson": ["johnson & johnson", "jnj", "johnson johnson"],
  "jpmorgan": ["jpmorgan", "jp morgan", "jpmorgan chase", "jpm"],
  "kraftheinz": ["kraft heinz", "kraft", "heinz"],
  "lockheedmartin": ["lockheed martin"],
  "mgmresorts": ["mgm resorts", "mgm"],
  "microsoft": ["microsoft"],
  "netflix": ["netflix"],
  "nike": ["nike"],
  "paypal": ["paypal"],
  "pepsico": ["pepsico", "pepsi"],
  "pfizer": ["pfizer"],
  "ultabeauty": ["ulta beauty", "ulta"],
  "verizon": ["verizon"],
  "walmart": ["walmart"]
};

// Match RapidFuzz's partial Indel ratio for the short company names in this corpus.
function partialCompanyScore(a, b) {
  const first = Array.from(a), second = Array.from(b);
  if (!first.length || !second.length) return first.length === second.length ? 100 : 0;
  function alignment(needle, haystack) {
    let best = 0;
    for (let offset = 1 - needle.length; offset < haystack.length; offset++) {
      const start = Math.max(0, offset), end = Math.min(haystack.length, offset + needle.length);
      const row = new Uint8Array(needle.length + 1);
      for (let i = start; i < end; i++) {
        let diagonal = 0;
        for (let j = 1; j <= needle.length; j++) {
          const previous = row[j];
          row[j] = needle[j - 1] === haystack[i] ? diagonal + 1 : Math.max(row[j], row[j - 1]);
          diagonal = previous;
        }
      }
      const total = needle.length + end - start;
      best = Math.max(best, 100 * (1 - (total - 2 * row[needle.length]) / total));
      if (best === 100) break;
    }
    return best;
  }
  if (first.length < second.length) return alignment(first, second);
  if (first.length > second.length) return alignment(second, first);
  return Math.max(alignment(first, second), alignment(second, first));
}

function resolveCompany(query, threshold = 80) {
  const text = query.toLowerCase();
  for (const [company, aliases] of Object.entries(COMPANY_ALIASES)) {
    if (aliases.some(alias => text.includes(alias))) return company;
  }
  let match = null, best = -1;
  for (const company of Object.keys(COMPANY_ALIASES)) {
    const score = partialCompanyScore(text, company);
    if (score > best) { best = score; match = company; }
  }
  return best >= threshold ? match : null;
}

const form = document.querySelector("#question-form");
const textarea = document.querySelector("#userInput");
const sendBtn = document.querySelector(".send-btn");
const chatContainer = document.querySelector(".chat-container");
const chatColumn = document.querySelector(".chat-column");
const status = document.querySelector("#ui-status");
let pending = false;

function updateInput() {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
  sendBtn.disabled = pending || !textarea.value.trim();
}

function fillQuestion(question) {
  textarea.value = question;
  updateInput();
  textarea.focus();
}

function scrollChat(align = false) {
  const questions = chatColumn.querySelectorAll(".message.user");
  const question = questions[questions.length - 1];
  if (!question) return;
  const style = getComputedStyle(chatContainer);
  const inset = Math.max(24, chatContainer.clientHeight * .15);
  chatColumn.style.paddingTop = questions.length === 1 ? Math.max(0, inset - parseFloat(style.paddingTop)) + "px" : "0px";
  const top = question.getBoundingClientRect().top - chatContainer.getBoundingClientRect().top + chatContainer.scrollTop;
  const target = Math.max(0, top - inset);
  // Leave room below a short turn; a longer answer fills that space naturally.
  chatColumn.style.minHeight = Math.max(0, target + chatContainer.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom)) + "px";
  if (align) chatContainer.scrollTop = target;
}

function neutralResearchText(text) {
  return text.replace(/\byour (question|answer)\b/gi, "the $1");
}

function actionButton(icon, label, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "action-button";
  button.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#' + icon + '"/></svg><span></span>';
  button.querySelector("span").textContent = label;
  button.addEventListener("click", onClick);
  return button;
}

// Escape raw HTML, then restrict Markdown output to text-formatting elements and web links.
function renderAnswer(target, answer) {
  if (!window.marked) {
    target.textContent = answer;
    target.style.whiteSpace = "pre-wrap";
    return;
  }
  const escaped = answer.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const template = document.createElement("template");
  template.innerHTML = marked.parse(escaped);
  const allowed = new Set("P BR STRONG EM DEL CODE PRE BLOCKQUOTE UL OL LI H1 H2 H3 H4 H5 H6 TABLE THEAD TBODY TR TH TD HR A".split(" "));
  template.content.querySelectorAll("*").forEach(element => {
    if (!allowed.has(element.tagName)) {
      element.replaceWith(...element.childNodes);
      return;
    }
    const href = element.getAttribute("href");
    [...element.attributes].forEach(attribute => element.removeAttribute(attribute.name));
    if (element.tagName === "A" && href) {
      try {
        const url = new URL(href, location.href);
        if (["https:", "http:"].includes(url.protocol)) {
          element.href = url.href;
          element.target = "_blank";
          element.rel = "noopener noreferrer";
        }
      } catch { /* Leave invalid links as plain text. */ }
    }
  });
  target.append(template.content);
}

function companyDisplayName(company) {
  const key = String(company || "").toLowerCase();
  const names = { "3m": "3M", aes: "AES", amd: "AMD", cvshealth: "CVS Health",
    jpmorgan: "JPMorgan", mgmresorts: "MGM Resorts", paypal: "PayPal", pepsico: "PepsiCo", cocacola: "Coca-Cola" };
  return names[key] || (COMPANY_ALIASES[key]?.[0] || company || "Unspecified company")
    .replace(/\b[a-z]/g, letter => letter.toUpperCase());
}

function filingWindow(years) {
  const valid = Array.isArray(years) ? years.filter(Number.isInteger) : [];
  if (!valid.length) return "All available filing years";
  const first = Math.min(...valid), last = Math.max(...valid);
  return first === last ? "Filing year " + first : "Filing years " + first + "\u2013" + last;
}

function progressDetail(event) {
  if (typeof event.detail === "string") return neutralResearchText(event.detail);
  if (Number.isInteger(event.query_count)) {
    return event.query_count + (event.query_count === 1 ? " search prepared for " : " searches prepared for ") + companyDisplayName(event.company) + ".";
  }
  if (Number.isInteger(event.selected_count)) {
    return event.selected_count ? "Working from " + event.selected_count + (event.selected_count === 1 ? " selected page." : " selected pages.") : "No relevant pages were selected.";
  }
  return event.company ? companyDisplayName(event.company) + " \u00b7 " + filingWindow(event.years) : "";
}

function appendText(parent, tag, value, className = "") {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  parent.append(element);
  return element;
}

function researchPageTitle(metadata) {
  const year = metadata.fiscal_year ?? metadata.year;
  const quarter = metadata.fiscal_quarter ?? metadata.quarter;
  const period = year ? String(year) + (quarter ? " Q" + String(quarter).replace(/^q/i, "") : "") : "";
  const types = { "10k": "10-K", "10q": "10-Q", "8k": "8-K", earnings: "Earnings" };
  const type = types[String(metadata.document_type || "").toLowerCase().replace(/-/g, "")];
  const parts = [companyDisplayName(metadata.company), period, type];
  if (type === "8-K" && metadata.fiscal_date) parts.push(metadata.fiscal_date);
  if (metadata.page_in_pdf) parts.push("Page " + metadata.page_in_pdf);
  return parts.filter(Boolean).join(" \u00b7 ");
}

function createResearchTrail(research) {
  const details = document.createElement("details");
  details.className = "research-trail";
  appendText(details, "summary", "How was this answer generated?");
  details.addEventListener("toggle", () => {
    scrollChat();
    if (!details.open) return;
    const top = chatContainer.scrollTop + details.getBoundingClientRect().top - chatContainer.getBoundingClientRect().top - 16;
    chatContainer.scrollTo({ top, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth" });
  });
  const card = appendText(details, "div", "", "research-card");
  const strings = values => Array.isArray(values) ? values.filter(value => typeof value === "string" && value.trim()) : [];
  function section(title) {
    const block = appendText(card, "section", "", "research-block");
    appendText(block, "h3", title);
    return block;
  }
  appendText(section("Search scope"), "p", companyDisplayName(research.company) + " \u00b7 " + filingWindow(research.years));
  for (const [title, values] of [["Search prepared", research.queries], ["What the answer needed", research.required_data_points]]) {
    const items = strings(values);
    if (!items.length) continue;
    const list = appendText(section(title), title === "Search prepared" ? "ol" : "ul", "", "research-list");
    items.forEach(item => appendText(list, "li", item));
  }
  const pages = Array.isArray(research.pages) ? research.pages.filter(page => page && typeof page === "object" && page.is_useful !== false) : [];
  const citedPages = pages.filter(page => page.is_cited);
  const counts = [];
  if (Number.isInteger(research.retrieved_count)) counts.push(research.retrieved_count + " pages retrieved");
  counts.push(pages.length + " selected by the judge", citedPages.length + " cited in the answer");
  appendText(section("Page selection"), "p", counts.join(" \u00b7 "));
  if (citedPages.length) {
    const list = appendText(section("Pages cited in the answer (" + citedPages.length + ")"), "ul", "", "research-pages");
    citedPages.forEach(page => {
      const item = appendText(list, "li", "");
      appendText(item, "h4", researchPageTitle(page.metadata || {}));
      appendText(item, "p", typeof page.analysis === "string" && page.analysis.trim() ? neutralResearchText(page.analysis) : "No page-level analysis was returned.");
    });
  }
  if (typeof research.sufficiency_reason === "string" && research.sufficiency_reason.trim()) {
    appendText(section("Context assessment"), "p", neutralResearchText(research.sufficiency_reason));
  }
  if (research.is_context_enough === false && typeof research.missing_information === "string" && research.missing_information.trim()) {
    appendText(section("What is missing"), "p", neutralResearchText(research.missing_information));
  }
  return details;
}

function createMessage(kind, text, documents = [], research = null) {
  const message = document.createElement("div");
  message.className = "message " + kind;
  message.innerHTML = '<div class="bubble"><div class="text"></div></div>';
  const bubble = message.firstElementChild;
  const content = bubble.querySelector(".text");
  if (kind === "bot") {
    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = "FINANCEBENCH / ANSWER";
    bubble.prepend(label);
    renderAnswer(content, text);
  } else {
    content.textContent = text;
  }
  if (kind === "user" || kind === "bot") {
    const actions = document.createElement("div");
    actions.className = "actions";
    actions.append(actionButton("copy", "Copy", async event => {
      const button = event.currentTarget;
      try {
        await navigator.clipboard.writeText(content.innerText);
        button.querySelector("span").textContent = "Copied";
        setTimeout(() => { button.querySelector("span").textContent = "Copy"; }, 1500);
      } catch {
        status.textContent = "Couldn't copy automatically. Select the answer text to copy it.";
      }
    }));
    if (documents.length) {
      actions.append(actionButton("book", "View sources (" + documents.length + ")", () => {
        try {
          sessionStorage.setItem("retrieved_sources", JSON.stringify(documents));
          window.open("sources/sources_page.html", "_blank");
        } catch {
          status.textContent = "Source storage is unavailable. Allow site storage and try again.";
        }
      }));
    }
    bubble.append(actions);
  }
  if (kind === "bot" && research && typeof research === "object") bubble.append(createResearchTrail(research));
  return message;
}

async function readResearchStream(response, onStatus) {
  if (!response.body) throw new Error("Missing response stream");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      let boundary;
      while ((boundary = /\r?\n\r?\n/.exec(buffer))) {
        const frame = buffer.slice(0, boundary.index);
        buffer = buffer.slice(boundary.index + boundary[0].length);
        const data = frame.split(/\r?\n/).filter(line => line.startsWith("data:"))
          .map(line => line.slice(5).trimStart()).join("\n");
        if (!data) continue; // Heartbeats contain only a comment.
        const event = JSON.parse(data);
        if (event.type === "status" && typeof event.message === "string") onStatus(event.message, event);
        if (event.type === "result") return event.data;
        if (event.type === "error") {
          const error = new Error("Research failed");
          error.userMessage = typeof event.message === "string" ? event.message : "Research failed. Please try again.";
          throw error;
        }
      }
      if (done) throw new Error("Stream ended before the answer arrived");
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

async function handleSend(event) {
  event.preventDefault();
  const question = textarea.value.trim();
  if (pending || !question) return;

  pending = true;
  document.body.classList.add("is-chatting");
  chatContainer.hidden = false;
  textarea.placeholder = "Ask another financial question…";
  chatColumn.append(createMessage("user", question));
  textarea.value = "";
  updateInput();
  sendBtn.setAttribute("aria-busy", "true");
  sendBtn.querySelector("span").textContent = "Researching…";
  const thinking = createMessage("bot thinking", "Starting research\u2026");
  thinking.setAttribute("role", "status");
  const detail = appendText(thinking.firstElementChild, "div", "", "progress-detail");
  chatColumn.append(thinking);
  scrollChat(true);

  try {
    if (!resolveCompany(question)) {
      const error = new Error("Company not identified");
      error.companyNotFound = true;
      error.userMessage = "Sorry, I couldn't identify a supported company in the question. The company may be outside this collection, or its name may be missing. Please include a company listed in the available filings.";
      throw error;
    }
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
      signal: AbortSignal.timeout(180000)
    });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await readResearchStream(response, (message, event) => {
      thinking.querySelector(".text").textContent = neutralResearchText(message);
      detail.textContent = progressDetail(event);
    });
    if (typeof data?.answer !== "string" || !data.answer.trim()) throw new Error("Missing answer");
    const documents = Array.isArray(data.documents) ? data.documents : [];
    thinking.replaceWith(createMessage("bot", data.answer, documents, data.research));
  } catch (error) {
    const text = error.userMessage || (error.name === "TimeoutError"
      ? "The research request took too long. Please try the question again."
      : "We couldn't get an answer from the research service. Please try again in a moment.");
    const message = createMessage("bot error", neutralResearchText(text));
    const actions = document.createElement("div");
    actions.className = "actions";
    actions.append(actionButton("arrow", error.companyNotFound ? "Edit question" : "Try this question again", () => fillQuestion(question)));
    if (error.companyNotFound) {
      const link = document.createElement("a");
      link.className = "action-button";
      link.href = "warning/warning_page.html";
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = "View available filings";
      actions.append(link);
    }
    message.firstElementChild.append(actions);
    thinking.replaceWith(message);
  } finally {
    pending = false;
    sendBtn.removeAttribute("aria-busy");
    sendBtn.querySelector("span").textContent = "Ask question";
    updateInput();
    scrollChat();
  }
}

new ResizeObserver(() => scrollChat()).observe(chatContainer);
form.addEventListener("submit", handleSend);
textarea.addEventListener("input", updateInput);
textarea.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});
document.querySelectorAll("[data-question]").forEach(button => {
  button.addEventListener("click", () => {
    if (pending) return;
    fillQuestion(button.dataset.question);
    form.requestSubmit();
  });
});
updateInput();

const about = document.querySelector(".about");
document.addEventListener("click", event => {
  if (!about.contains(event.target)) about.open = false;
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && about.open) {
    about.open = false;
    about.querySelector("summary").focus();
  }
});
