const API_URL = "http://localhost:8000";

// Show current tab URL
chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    if (tab) {
        const urlEl = document.getElementById("currentUrl");
        try {
            const u = new URL(tab.url);
            urlEl.textContent = u.hostname || tab.url;
        } catch {
            urlEl.textContent = tab.url || "Unknown";
        }
    }
});

// Report button
document.getElementById("reportBtn").addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const statusMsg = document.getElementById("statusMsg");

    if (!tab) return;

    try {
        const res = await fetch(`${API_URL}/report`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: tab.url, reason: "user_report" })
        });

        if (res.ok) {
            statusMsg.textContent = "✅ Reported to Coinbase Security Team";
            statusMsg.style.color = "#00D395";
        } else {
            throw new Error("Server error");
        }
    } catch (e) {
        statusMsg.textContent = "⚠️ Backend not reachable. Start the backend first.";
        statusMsg.style.color = "#D97706";
    }
});
