// Background Service Worker — Phish-Guard v1.1
// Handles context menu and extension lifecycle events

chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "phishguard-verify",
        title: "🛡️ Verify with Phish-Guard",
        contexts: ["link", "image", "video"]
    });
    console.log("[Phish-Guard] Extension installed. Context menu created.");
});

// Right-click context menu handler
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId !== "phishguard-verify") return;

    const urlToVerify = info.linkUrl || info.srcUrl || tab.url;
    if (!urlToVerify) return;

    try {
        const res = await fetch("http://localhost:8000/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: urlToVerify })
        });
        const result = await res.json();

        // Show result as a browser notification-style alert via content script
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: (url, status, message) => {
                const icons = { safe: "✅", trusted: "🛡️", phish: "🚨", warning: "⚠️", neutral: "⚪" };
                const colors = { safe: "#0052FF", trusted: "#059669", phish: "#CF202F", warning: "#D97706", neutral: "#6B7280" };
                const div = document.createElement("div");
                div.style.cssText = `position:fixed;top:20px;right:20px;z-index:2147483647;
                    background:${colors[status] || "#6B7280"};color:white;padding:14px 18px;
                    border-radius:10px;font-family:system-ui,sans-serif;font-size:14px;
                    box-shadow:0 4px 24px rgba(0,0,0,0.4);max-width:300px;line-height:1.5;
                    animation:pgFadeIn .2s ease`;
                div.innerHTML = `<style>@keyframes pgFadeIn{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:translateY(0)}}</style>
                    <strong style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                        <span style="font-size:20px">${icons[status] || "⚪"}</span>
                        Phish-Guard Result
                    </strong>
                    <div style="opacity:.9;font-size:13px">${message}</div>
                    <div style="opacity:.6;font-size:11px;margin-top:6px;word-break:break-all">${url.slice(0, 60)}${url.length > 60 ? "…" : ""}</div>`;
                document.body.appendChild(div);
                setTimeout(() => div.remove(), 5000);
            },
            args: [urlToVerify, result.status, result.message || "Verification complete"]
        });
    } catch (e) {
        console.error("[Phish-Guard] Context menu verify failed:", e);
    }
});
