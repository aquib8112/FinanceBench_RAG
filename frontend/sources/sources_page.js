const sourcesJSON = sessionStorage.getItem("retrieved_sources");

let sources = [];
if (sourcesJSON) {
  sources = JSON.parse(sourcesJSON);
}

function getExcerpt(text, limit = 180) {
  if (!text) return "";
  return text.length > limit ? text.slice(0, limit) + "..." : text;
}

function tryParse(val) {
  if (typeof val !== "string") return val;
  try {
    return JSON.parse(val.replace(/'/g, '"'));
  } catch {
    return [];
  }
}

function normalizeMetadata(m) {
  return {
    ...m,
    secondary_sections: tryParse(m.secondary_sections),
    financial_metrics: tryParse(m.financial_metrics),
    entities: tryParse(m.entities),
    keywords: tryParse(m.keywords)
  };
}

// ------------------ UI Logic ------------------

function toggleFullText(i) {
  const ft = document.getElementById(`full-text-${i}`);
  const ex = document.getElementById(`excerpt-${i}`);
  const btn = ft.nextElementSibling;

  if (ft.style.display === "block") {
    ft.style.display = "none";
    ex.style.display = "block";
    btn.textContent = "Show more";
  } else {
    ft.style.display = "block";
    ex.style.display = "none";
    btn.textContent = "Show less";
  }
}

// ------------------ Main Renderer ------------------

function renderSources(sources) {
  const container = document.getElementById("sources-container");

  if (!sources || sources.length === 0) {
    container.innerHTML = `
      <div style="color:#b0bec5; font-size:14px; padding:10px;">
        No supporting documents were retrieved for this answer.
      </div>
    `;
    return;
  }

  container.innerHTML = ""; // <-- FIXED typo: was ccontainer

  sources.forEach((src, index) => {
    const m = normalizeMetadata(src.metadata);

    const card = document.createElement("div");
    card.className = "source-card";

    const header = `
      <div class="card-header">${m.document_name} — Page ${m.page_in_pdf}</div>
      <div class="card-subheader">${m.company} (${m.year}) — ${m.section}</div>
    `;

    const allTags = []
      .concat(m.secondary_sections || [])
      .concat(m.financial_metrics || [])
      .concat(m.keywords || [])
      .concat(m.entities || []);

    const tagsHTML = allTags.map(tag => `<span class="tag">${tag}</span>`).join("");

    const excerpt = getExcerpt(m.full_text);

    const content = `
      <div class="excerpt" id="excerpt-${index}">${excerpt}</div>
      <div class="full-text" id="full-text-${index}">${m.full_text}</div>
      <button class="expand-btn" onclick="toggleFullText(${index})">Show more</button>
    `;

    card.innerHTML = header +
                     `<div class="tag-container">${tagsHTML}</div>` +
                     content;

    container.appendChild(card);
  });
}

// ------------------ Auto Run ------------------

window.addEventListener("load", () => {
  renderSources(sources);
});
