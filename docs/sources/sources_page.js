const companyNames = {
  "3m": "3M", aes: "AES", amd: "AMD", activisionblizzard: "Activision Blizzard",
  americanexpress: "American Express", americanwaterworks: "American Water Works",
  bestbuy: "Best Buy", cocacola: "Coca-Cola", cvshealth: "CVS Health",
  footlocker: "Foot Locker", generalmills: "General Mills", johnson_johnson: "Johnson & Johnson",
  jpmorgan: "JPMorgan", kraftheinz: "Kraft Heinz", lockheedmartin: "Lockheed Martin",
  mgmresorts: "MGM Resorts", paypal: "PayPal", pepsico: "PepsiCo", ultabeauty: "Ulta Beauty"
};

const firstText = (...values) => values.find(value => typeof value === "string" && value.trim())?.trim() || "";
const filingTypes = { "10k": "10-K", "10q": "10-Q", "8k": "8-K", earnings: "Earnings" };

function readSources() {
  try {
    const stored = JSON.parse(sessionStorage.getItem("retrieved_sources") || "[]");
    return Array.isArray(stored) ? stored.filter(source => source && typeof source === "object") : [];
  } catch {
    return [];
  }
}

function sourceTitle(metadata) {
  const key = firstText(metadata.company).toLowerCase().replace(/\s+/g, "");
  const company = companyNames[key] || key.replace(/(^|[_-])([a-z])/g, (_, gap, letter) => (gap ? " " : "") + letter.toUpperCase()) || "Source document";
  const year = metadata.fiscal_year ?? metadata.year;
  const quarter = metadata.fiscal_quarter ?? metadata.quarter;
  const period = year ? String(year) + (quarter ? " Q" + String(quarter).replace(/^q/i, "") : "") : "";
  const type = filingTypes[firstText(metadata.document_type).toLowerCase().replace(/-/g, "")];
  return [company, period, type].filter(Boolean).join(" \u00b7 ");
}

function renderEvidence(target, metadata) {
  target.textContent = firstText(metadata.plain_text, metadata.full_text) || "Original page text is not available for this source.";
}

function renderSources() {
  const sources = readSources();
  const container = document.querySelector("#sources-container");
  document.querySelector("#source-count").textContent = sources.length
    ? sources.length + (sources.length === 1 ? " source page used" : " source pages used") + " to support this answer."
    : "Open the sources from a chat answer to explore its evidence.";
  document.querySelector(".source-note").hidden = !sources.length;
  if (!sources.length) {
    container.innerHTML = '<div class="empty-state"><h2>No source pages to display.</h2><p>Choose "View sources" beneath an answer in the chat.</p><a href="../index.html">Go to chat &rarr;</a></div>';
    return;
  }
  sources.forEach((source, index) => {
    const metadata = source.metadata && typeof source.metadata === "object" ? source.metadata : {};
    const card = document.createElement("article");
    card.className = "source-card";
    card.innerHTML = '<header class="source-heading"><div><p class="eyebrow"></p><h2></h2></div><span class="page-number"></span></header><div class="page-overview"><h3>Page overview</h3><p></p></div><details class="source-evidence"><summary>Read source page</summary><div class="evidence-content"></div></details>';
    card.querySelector(".eyebrow").textContent = "SOURCE " + String(index + 1).padStart(2, "0");
    card.querySelector("h2").textContent = sourceTitle(metadata);
    const page = Number(metadata.page_in_pdf);
    card.querySelector(".page-number").textContent = Number.isInteger(page) && page > 0 ? "Page " + page : "Page unavailable";
    card.querySelector(".page-overview p").textContent = firstText(source.page_content, metadata.summary) || "No page overview is available for this source.";
    const details = card.querySelector("details");
    const evidence = card.querySelector(".evidence-content");
    details.addEventListener("toggle", () => {
      if (details.open && !evidence.childNodes.length) renderEvidence(evidence, metadata);
    });
    container.append(card);
  });
}

renderSources();
