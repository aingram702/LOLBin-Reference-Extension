let db = [];
let currentOsFilter = "all";

document.addEventListener("DOMContentLoaded", async () => {
  db = await loadDatabase();
  document.getElementById("dbStatus").textContent = `${db.length} entries loaded`;
  renderResults(db);

  document.getElementById("searchBox").addEventListener("input", handleSearch);

  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentOsFilter = btn.dataset.os;
      handleSearch();
    });
  });
});

// Load the database from local storage, falling back to the bundled JSON.
// The background service worker normally seeds storage on install, but MV3
// service workers are ephemeral and onInstalled does not fire on every
// startup — so if storage was cleared the popup must self-heal.
async function loadDatabase() {
  try {
    const { lolbinDb } = await chrome.storage.local.get("lolbinDb");
    if (Array.isArray(lolbinDb) && lolbinDb.length) return lolbinDb;
  } catch (err) {
    console.error("storage read failed, falling back to bundled DB:", err);
  }
  try {
    const res = await fetch(chrome.runtime.getURL("data/lolbin_db.json"));
    const data = await res.json();
    // best-effort cache so subsequent opens are instant
    chrome.storage.local.set({ lolbinDb: data }).catch(() => {});
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error("failed to load bundled DB:", err);
    return [];
  }
}

function handleSearch() {
  const query = document.getElementById("searchBox").value.toLowerCase().trim();

  let filtered = db;

  if (currentOsFilter !== "all") {
    filtered = filtered.filter(e => e.os === currentOsFilter);
  }

  if (query) {
    filtered = filtered.filter(e =>
      e.name.toLowerCase().includes(query) ||
      e.category.toLowerCase().includes(query) ||
      e.description.toLowerCase().includes(query) ||
      e.id.toLowerCase().includes(query)
    );
  }

  renderResults(filtered);
}

function renderResults(entries) {
  const container = document.getElementById("results");
  const countEl = document.getElementById("resultsCount");
  countEl.textContent = `${entries.length} result(s)`;

  if (entries.length === 0) {
    container.innerHTML = `<div class="no-results">No matching binaries found.</div>`;
    return;
  }

  container.innerHTML = entries.map(entry => `
    <div class="entry">
      <div class="entry-header">
        <span class="entry-name">${escapeHtml(entry.name)}</span>
        <span class="entry-os ${entry.os}">${entry.os}</span>
      </div>
      <div class="entry-category">${escapeHtml(entry.category)}</div>
      <div class="entry-desc">${escapeHtml(entry.description)}</div>
      <div class="command-box" data-cmd="${escapeAttr(entry.example_command)}">
        ${escapeHtml(entry.example_command)}
      </div>
      <div class="copy-hint">Click command to copy</div>
      ${entry.detection_notes ? `<div class="detection-notes">🛡️ ${escapeHtml(entry.detection_notes)}</div>` : ""}
      <div class="references">
        ${(entry.references || [])
          .map(safeUrl)
          .filter(Boolean)
          .map(r => `<a href="${escapeAttr(r)}" target="_blank" rel="noopener noreferrer">Reference ↗</a>`)
          .join(" ")}
      </div>
    </div>
  `).join("");

  container.querySelectorAll(".command-box").forEach(box => {
    box.addEventListener("click", () => {
      const cmd = box.dataset.cmd;
      navigator.clipboard.writeText(cmd).then(() => {
        const original = box.textContent;
        box.textContent = "✅ Copied to clipboard!";
        setTimeout(() => { box.textContent = cmd; }, 1200);
      });
    });
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return String(str == null ? "" : str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Only permit http(s) reference links, so a "javascript:" or "data:" URL
// can never become a clickable href. Returns "" for anything unsafe.
function safeUrl(url) {
  try {
    const u = new URL(String(url), window.location.href);
    return (u.protocol === "http:" || u.protocol === "https:") ? u.href : "";
  } catch {
    return "";
  }
}
