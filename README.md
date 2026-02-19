<div align="center">

<img src="extension/icons/icon128.png" alt="Phish-Guard Logo" width="96" />

# Phish-Guard

### Real-Time Phishing Detection for Coinbase Users

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Manifest_V3-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white)](https://developer.chrome.com/docs/extensions/mv3/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**A Chrome extension + FastAPI backend that verifies every link, image, and video you hover over — protecting Coinbase users from phishing attacks before they click.**

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [How It Works](#-how-it-works) · [API Reference](#-api-reference)

</div>

---

## 🎯 The Problem

Phishing attacks targeting crypto users cost billions annually. Attackers register lookalike domains (e.g., `coinbase-support.xyz`, `wallet-connect-base.org`) that are visually identical to the real thing. Users click, enter credentials, and lose funds.

**Phish-Guard solves this by verifying every link before you click it.**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔗 **Link Scanning** | Every hyperlink on every page is scanned in real-time |
| 🖼️ **Image & Ad Scanning** | Images and videos wrapped in links are scanned too |
| 📢 **iframe/Ad Detection** | Runs inside iframes — catches banner ads and embedded content |
| 🖱️ **Hover Badges** | Security status badge appears on hover — Green/Blue/Amber/Red |
| 🚨 **Right-Click Verify** | Right-click any link, image, or video to manually trigger verification |
| 📊 **Live Dashboard** | Real-time stats page showing engine status and domain counts |
| 🔴 **Report Threats** | One-click reporting from the popup — flags suspicious sites for review |
| ⚡ **LRU Cache** | 50,000-entry cache ensures repeated URLs are verified in microseconds |

---

## 🧠 Architecture

```
┌─────────────────────── Chrome Extension (MV3) ──────────────────────────┐
│                                                                          │
│  content.js          popup.html / popup.js       background.js          │
│  ─────────────────   ─────────────────────────   ─────────────────────  │
│  • IntersectionObserver  • Shows current URL     • Context menu handler  │
│    lazy link/img/video   • Report current site   • Right-click verify   │
│    scanning              • Backend status        • Shows result on page  │
│  • Hover badge display                                                   │
│                                                                          │
└────────────────────────┬─────────────────────────────────────────────────┘
                         │ POST /verify (JSON)
                         ▼
┌──────────────────── FastAPI Backend ─────────────────────────────────────┐
│                                                                          │
│  Layer 1 → Coinbase Allowlist (instant, zero false negatives)           │
│  Layer 2 → Known Phishing Blocklist (instant)                           │
│  Layer 3 → Tranco Top 1M Trusted Domains (loads async at startup)       │
│  Layer 4 → ML Model: TF-IDF + RandomForest (trains async at startup)    │
│           └─ Trained on 235,000+ real URLs from PhiUSIIL dataset        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Badge Status Guide

| Badge | Status | Meaning |
|-------|--------|---------|
| ✅ Blue | `safe` | Official Coinbase domain (coinbase.com, base.org, etc.) |
| 🛡️ Green | `trusted` | Tranco Top 1M verified popular site |
| ⚠️ Amber | `warning` | ML model flagged as likely phishing |
| 🚨 Red | `phish` | Known phishing domain — blocked |
| ⚪ Gray | `neutral` | Unverified — use caution |

---

## ⚡ Quick Start

### Prerequisites
- Python 3.9+
- Google Chrome or Brave browser

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/phish-guard.git
cd phish-guard
```

### 2. Start the Backend

```bash
./start_backend.sh
```

This script will:
- Create a Python virtual environment
- Install all dependencies automatically
- Start the FastAPI server at `http://localhost:8000`

> **First run note:** The ML model trains on 235K URLs in the background. The server is immediately available — ML kicks in after ~30-60 seconds.

### 3. Install the Chrome Extension

1. Open `chrome://extensions` in Chrome
2. Enable **Developer Mode** (top-right toggle)
3. Click **Load Unpacked**
4. Select the `extension/` folder

### 4. Browse & Stay Safe

Hover over any link on any website. The Phish-Guard badge will appear showing the security status.

---

## 🔥 How It Works

### The 4-Layer Detection Engine

```
URL Input
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Layer 1: Coinbase Allowlist                        │
│  • coinbase.com, base.org, prime.coinbase.com, etc.│
│  • Instant ✅ if matched                            │
└──────────────────────────┬──────────────────────────┘
                           │ no match
                           ▼
┌─────────────────────────────────────────────────────┐
│  Layer 2: Known Phishing Blocklist                  │
│  • coinbase-support.xyz, wallet-connect-base.org   │
│  • Instant 🚨 if matched                            │
└──────────────────────────┬──────────────────────────┘
                           │ no match
                           ▼
┌─────────────────────────────────────────────────────┐
│  Layer 3: Tranco Top 1M Trusted Domains             │
│  • 1,000,000+ globally popular domains             │
│  • Instant 🛡️ if matched                           │
└──────────────────────────┬──────────────────────────┘
                           │ no match
                           ▼
┌─────────────────────────────────────────────────────┐
│  Layer 4: ML Model (TF-IDF + RandomForest)          │
│  • Trained on 235K+ URLs (PhiUSIIL dataset)        │
│  • Character-level n-gram analysis (3-5 grams)     │
│  • Returns phishing probability 0.0–1.0            │
│  • > 65% → ⚠️  Warning                             │
│  • > 40% → ⚪ Neutral                              │
│  • ≤ 40% → 🛡️  Safe (unverified)                  │
└─────────────────────────────────────────────────────┘
```

### Performance Optimizations

- **Async Startup**: ML model trains in a background thread. Server responds in `<100ms` from launch.
- **Async Tranco Loading**: 1M domain list loads in background — initial trusted set of 40+ domains is available instantly.
- **LRU Cache**: 50,000-entry cache with O(1) lookup — repeated URLs returned in microseconds.
- **IntersectionObserver**: Only scans links entering the viewport — zero overhead for off-screen content.
- **Thread-Safe Design**: All shared data (cache, trusted domains) protected with `threading.Lock`.

---

## 📡 API Reference

### `POST /verify`
Verify a URL against all 4 detection layers.

**Request:**
```json
{ "url": "https://coinbase-support.xyz" }
```

**Response:**
```json
{
  "status": "phish",
  "message": "Known Phishing Domain",
  "confidence": 1.0,
  "badge": "red_alert"
}
```

### `POST /report`
Submit a user-reported threat.

**Request:**
```json
{ "url": "https://suspicious-site.com", "reason": "user_report" }
```

### `GET /api/stats`
Live engine statistics.

**Response:**
```json
{
  "trusted_domains": 1000044,
  "cached_predictions": 127,
  "blocklist_size": 8,
  "model_status": "active"
}
```

### `GET /health`
Health check endpoint.

```json
{ "status": "ok", "message": "Phish-Guard is running" }
```

### `GET /docs`
Interactive Swagger API documentation (auto-generated by FastAPI).

---

## 📁 Project Structure

```
phish-guard/
├── backend/
│   ├── main.py                    # FastAPI app, routes, static serving
│   ├── phishing_detector.py       # 4-layer detection engine (async)
│   ├── ml_model.py                # TF-IDF + RandomForest model (async training)
│   ├── requirements.txt           # Python dependencies
│   └── static/
│       ├── index.html             # Landing page
│       ├── style.css              # Landing page styles
│       └── script.js              # Live stats fetching
│   └── datasets/
│       ├── PhiUSIIL_Phishing_URL_Dataset.csv   # 235K URLs for ML training
│       └── top-1m.csv             # Tranco Top 1M domain list
│
├── extension/
│   ├── manifest.json              # Chrome MV3 manifest (v1.1)
│   ├── content.js                 # Link/image/video scanner (IntersectionObserver)
│   ├── background.js              # Service worker, right-click menu
│   ├── popup.html                 # Extension popup UI
│   ├── popup.js                   # Popup logic (report, URL display)
│   ├── styles.css                 # Extension styles
│   └── icons/
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
│
├── test_links.html                # Test suite for all badge types
├── start_backend.sh               # One-command backend starter
└── README.md
```

---

## 🛡️ Security & Privacy

- **No data stored**: URLs are checked in-memory and never logged to disk.
- **Local backend**: All processing happens on your machine — nothing sent to third-party servers.
- **CORS restricted**: The backend only accepts connections from the local extension (configurable).
- **Open source**: Full source available for audit.

> **Production note:** For deployment, restrict CORS origins and consider URL hashing for additional privacy.

---

## 🔭 Roadmap

- [ ] **Phase 4**: Real-time blocklist sync from threat intelligence feeds (PhishTank, OpenPhish)
- [ ] **Phase 5**: URL hashing for privacy-preserving cloud verification
- [ ] **Phase 6**: Firefox extension support
- [ ] **Phase 7**: Community-contributed blocklist with upvoting

---

## 🧰 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, FastAPI, Uvicorn |
| ML Model | scikit-learn (TF-IDF + RandomForest) |
| Dataset | PhiUSIIL (235K URLs), Tranco Top 1M |
| Extension | JavaScript, Chrome Manifest V3 |
| Frontend | HTML5, CSS3 (vanilla, no frameworks) |

---

## 👤 Author

**Shrimun Agarwal**
**Role:** Aspiring Data/ML Engineer @ Coinbase

> Built as a security tool showcase for Coinbase Trust & Safety.
> Not affiliated with Coinbase Inc.

---

<div align="center">

⭐ **Star this repo if Phish-Guard protected you!** ⭐

Made with ❤️ for the crypto community

</div>
