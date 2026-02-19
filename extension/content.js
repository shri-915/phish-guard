// Phish-Guard Content Script v3 — Media, Ad & Link Verification
// Scans links, images, videos, and ads (including inside iframes)

const API_URL = "http://localhost:8000/verify";
const LINK_STATUS_MAP = new WeakMap();
const PENDING = "pending";

// ─── Shared Hover Badge ──────────────────────────────────────────────────────

let hoverBadge = null;

function getHoverBadge() {
    if (!hoverBadge) {
        hoverBadge = document.createElement("div");
        hoverBadge.id = "phish-guard-badge";
        Object.assign(hoverBadge.style, {
            position: "fixed",
            zIndex: "2147483647",
            display: "none",
            pointerEvents: "none",
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            fontSize: "13px",
            lineHeight: "1.4",
            borderRadius: "8px",
            padding: "8px 14px",
            color: "white",
            boxShadow: "0 4px 20px rgba(0,0,0,0.35)",
            maxWidth: "280px",
            wordBreak: "break-word",
            transition: "opacity 0.12s ease",
            opacity: "0",
        });
        document.body.appendChild(hoverBadge);
    }
    return hoverBadge;
}

function showBadge(element, result) {
    const badge = getHoverBadge();
    let icon, color, header;
    const text = result.message || "Unknown";

    switch (result.status) {
        case "safe": icon = "✅"; color = "#0052FF"; header = "Official Coinbase"; break;
        case "phish": icon = "🚨"; color = "#CF202F"; header = "Phishing Alert"; break;
        case "trusted": icon = "🛡️"; color = "#059669"; header = "Trusted Site"; break;
        case "warning": icon = "⚠️"; color = "#D97706"; header = "Suspicious Link"; break;
        default: icon = "⚪"; color = "#6B7280"; header = "Unverified"; break;
    }

    badge.style.background = color;
    badge.style.display = "flex";
    badge.style.alignItems = "center";
    badge.style.gap = "10px";
    badge.innerHTML = `
        <span style="font-size:20px;line-height:1;flex-shrink:0">${icon}</span>
        <div>
            <div style="font-weight:700;font-size:10px;opacity:0.85;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px">${header}</div>
            <div style="font-size:12px">${text}</div>
        </div>
    `;

    // Position badge near the element, keeping it within viewport
    const rect = element.getBoundingClientRect();
    const badgeW = 270;
    const badgeH = 52;
    const margin = 8;

    let left = rect.left;
    let top = rect.top - badgeH - margin;

    // If it would go above viewport, show below
    if (top < 5) top = rect.bottom + margin;
    // If it would go off right edge, shift left
    if (left + badgeW > window.innerWidth) left = window.innerWidth - badgeW - margin;
    // Clamp to left edge
    if (left < margin) left = margin;

    badge.style.left = left + "px";
    badge.style.top = top + "px";
    badge.style.opacity = "1";
}

function hideBadge() {
    const badge = document.getElementById("phish-guard-badge");
    if (badge) {
        badge.style.opacity = "0";
        setTimeout(() => { badge.style.display = "none"; }, 120);
    }
}

// ─── URL Resolution ──────────────────────────────────────────────────────────

/**
 * Resolves the URL to verify for a given element.
 * Priority: element's own href → closest parent <a> href → element's src
 */
function resolveUrl(element) {
    // If it's a link itself
    if (element.tagName === "A" && element.href) return element.href;

    // If it's an image/video inside a link
    const parentLink = element.closest("a[href]");
    if (parentLink) return parentLink.href;

    // For images/videos with a src (e.g., ad images not wrapped in links)
    if (element.src) return element.src;

    return null;
}

// ─── Verification ────────────────────────────────────────────────────────────

async function checkAndAttach(element) {
    const url = resolveUrl(element);
    if (!url) return;
    if (url.startsWith("javascript:") || url.startsWith("#") || url.startsWith("mailto:") || url.startsWith("data:")) return;
    if (LINK_STATUS_MAP.has(element)) return;

    LINK_STATUS_MAP.set(element, PENDING);

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const result = await res.json();
        LINK_STATUS_MAP.set(element, result);

        element.addEventListener("mouseenter", () => showBadge(element, result));
        element.addEventListener("mouseleave", hideBadge);

        // For phishing links, add a subtle red border as a persistent visual cue
        if (result.status === "phish" || result.status === "warning") {
            element.style.outline = `2px solid ${result.status === "phish" ? "#CF202F" : "#D97706"}`;
            element.style.outlineOffset = "2px";
            element.style.borderRadius = "2px";
        }

    } catch {
        LINK_STATUS_MAP.set(element, { status: "error" });
    }
}

// ─── Lazy Scanning (IntersectionObserver) ────────────────────────────────────

function setupLazyScanning() {
    // Selector covers: links, images in links, videos in links, standalone ad images
    const SELECTOR = "a[href], img, video";

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                checkAndAttach(entry.target);
            }
        });
    }, { rootMargin: "300px" }); // Pre-scan 300px before element enters viewport

    function observeAll() {
        document.querySelectorAll(SELECTOR).forEach(el => {
            if (!LINK_STATUS_MAP.has(el)) {
                observer.observe(el);
            }
        });
    }

    observeAll();

    // Watch for new elements (SPAs, infinite scroll, dynamic ads)
    const mutationObserver = new MutationObserver(() => observeAll());
    mutationObserver.observe(document.documentElement, { childList: true, subtree: true });
}

// ─── Init ─────────────────────────────────────────────────────────────────────

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupLazyScanning);
} else {
    setupLazyScanning();
}
