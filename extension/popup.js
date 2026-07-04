let db = [];
let currentOsFilter = "all";

document.addEventListener("DOMContentLoaded", async () => {
  const { lolbinDb } = await chrome.storage.local.get("lolbinDb");
  db = lolbinDb || [];
  document.getElementById("dbStatus").textContent = `${db.length} entries loaded`;
  renderResults(db);

  document.getElementById("searchBox").addEventListener("input", handleSearch);
  document.getElementById("syncBtn").addEventListener("click", handleSync);

  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentOsFilter = btn.dataset.os;
      handleSearch();
    });
  });
});

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
        ${(entry.references || []).map(r => `<a href="${escapeAttr(r)}" target="_blank">Reference ↗</a>`).join(" ")}
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

async function handleSync() {
  const apiKey = prompt("Enter your Pro API key to sync the live database:");
  if (!apiKey) return;

  document.getElementById("dbStatus").textContent = "Syncing...";

  chrome.runtime.sendMessage({ action: "syncProDatabase", apiKey }, (response) => {
    if (response.success) {
      chrome.storage.local.get("lolbinDb", ({ lolbinDb }) => {
        db = lolbinDb;
        document.getElementById("dbStatus").textContent =
          `${db.length} entries (${response.newCount} updated)`;
        handleSearch();
      });
    } else {
      document.getElementById("dbStatus").textContent = `Sync failed: ${response.error}`;
    }
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return String(str).replace(/"/g, """);
}
