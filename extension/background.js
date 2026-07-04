// background.js - Service Worker
// Handles optional sync with Pro backend and local storage caching

const API_BASE = "https://api.yourdomain.com";

chrome.runtime.onInstalled.addListener(async () => {
  console.log("LOLBin Reference Tool installed.");
  await loadLocalDatabase();
});

// onInstalled only fires on install/update. Re-seed on browser startup too so a
// cleared storage area is repopulated without requiring a reinstall.
chrome.runtime.onStartup.addListener(async () => {
  const { lolbinDb } = await chrome.storage.local.get("lolbinDb");
  if (!Array.isArray(lolbinDb) || lolbinDb.length === 0) {
    await loadLocalDatabase();
  }
});

async function loadLocalDatabase() {
  try {
    const response = await fetch(chrome.runtime.getURL("data/lolbin_db.json"));
    const data = await response.json();
    if (!Array.isArray(data)) throw new Error("bundled database is not an array");
    await chrome.storage.local.set({ lolbinDb: data, lastSynced: null });
    console.log(`Loaded ${data.length} LOLBin entries into local storage.`);
  } catch (err) {
    console.error("Failed to load local LOLBin database:", err);
  }
}

// Optional: Pro tier live sync
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "syncProDatabase") {
    syncWithBackend(message.apiKey).then(sendResponse);
    return true; // keep channel open for async response
  }
});

async function syncWithBackend(apiKey) {
  try {
    const { lastSynced } = await chrome.storage.local.get("lastSynced");
    const since = lastSynced || "2020-01-01T00:00:00";

    const response = await fetch(`${API_BASE}/v1/lolbin/updates?since=${since}`, {
      headers: { Authorization: `Bearer ${apiKey}` }
    });

    if (!response.ok) {
      return { success: false, error: `HTTP ${response.status}` };
    }

    const payload = await response.json();
    const entries = Array.isArray(payload.entries) ? payload.entries : [];
    const { lolbinDb } = await chrome.storage.local.get("lolbinDb");

    const merged = mergeEntries(Array.isArray(lolbinDb) ? lolbinDb : [], entries);
    await chrome.storage.local.set({
      lolbinDb: merged,
      lastSynced: new Date().toISOString()
    });

    return { success: true, newCount: entries.length };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

function mergeEntries(existing, updates) {
  const map = new Map(existing.map(e => [e.id, e]));
  for (const entry of updates) {
    // Skip malformed remote entries lacking a stable key.
    if (entry && typeof entry.id === "string") {
      map.set(entry.id, entry);
    }
  }
  return Array.from(map.values());
}
