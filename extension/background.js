// background.js - Service Worker
// Seeds local storage with the bundled offline database.

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
    await chrome.storage.local.set({ lolbinDb: data });
    console.log(`Loaded ${data.length} LOLBin entries into local storage.`);
  } catch (err) {
    console.error("Failed to load local LOLBin database:", err);
  }
}
