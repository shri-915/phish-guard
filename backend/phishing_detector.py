import os
import csv
import zipfile
import io
import threading
from urllib.parse import urlparse
from collections import OrderedDict

# ML model is imported lazily to avoid blocking startup
_phishing_model = None
_model_lock = threading.Lock()

def get_model():
    global _phishing_model
    if _phishing_model is None:
        with _model_lock:
            if _phishing_model is None:
                from ml_model import phishing_model
                _phishing_model = phishing_model
    return _phishing_model


class LRUCache:
    """Thread-safe LRU cache for ML prediction results."""
    def __init__(self, max_size=10000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
        return None

    def put(self, key, value):
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)


class PhishGuard:
    def __init__(self):
        # Layer 1: Official Coinbase Allowlist
        self.allowlist = {
            "coinbase.com", "base.org",
            "help.coinbase.com", "prime.coinbase.com",
            "pro.coinbase.com", "blog.coinbase.com",
            "wallet.coinbase.com", "assets.coinbase.com"
        }

        # Layer 2: Known Phishing Blocklist
        self.blocklist = {
            "coinbase-support.xyz", "wallet-connect-base.org",
            "secure-login-cb.net", "update-kyc-coinbase.com",
            "coinbase-wallet-connect.com", "coinbase-airdrop.net",
            "coinbase-pro-login.com", "coinbasepro-login.net"
        }

        # Layer 3: Trusted Domains (starts with minimal set, loads full list in background)
        self.trusted_domains = {
            "google.com", "github.com", "reddit.com", "microsoft.com",
            "apple.com", "amazon.com", "stackoverflow.com", "facebook.com",
            "twitter.com", "x.com", "youtube.com", "linkedin.com",
            "wikipedia.org", "netflix.com", "instagram.com", "tiktok.com",
            "twitch.tv", "discord.com", "slack.com", "zoom.us",
            "dropbox.com", "notion.so", "figma.com", "stripe.com",
            "paypal.com", "shopify.com", "wordpress.com", "medium.com",
            "nytimes.com", "bbc.com", "cnn.com", "reuters.com",
            "bloomberg.com", "techcrunch.com", "theverge.com",
            "ethereum.org", "bitcoin.org", "metamask.io",
            "binance.com", "kraken.com", "gemini.com", "crypto.com",
            "opensea.io", "uniswap.org", "aave.com", "compound.finance",
        }
        self._trusted_lock = threading.Lock()
        self._tranco_loaded = False

        # Layer 4: ML Prediction Cache
        self.prediction_cache = LRUCache(max_size=50000)

        # Load Tranco list in background (non-blocking)
        self._tranco_thread = threading.Thread(
            target=self._load_tranco_list,
            daemon=True,
            name="TrancoLoader"
        )
        self._tranco_thread.start()

        print("[PhishGuard] Initialized with minimal trusted set. Tranco loading in background...")

    def _load_tranco_list(self):
        """Load Tranco Top 1M list in background thread."""
        tranco_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets", "top-1m.csv")

        if not os.path.exists(tranco_path):
            print(f"[PhishGuard] Tranco list not found at {tranco_path}. Using minimal set.")
            self._tranco_loaded = True
            return

        try:
            new_domains = set()
            loaded_count = 0

            # Try reading as ZIP first
            try:
                with zipfile.ZipFile(tranco_path, 'r') as zf:
                    name = zf.namelist()[0]
                    with zf.open(name) as f:
                        reader = csv.reader(io.TextIOWrapper(f, encoding='utf-8'))
                        for row in reader:
                            if len(row) >= 2:
                                domain = row[1].strip().lower()
                                if domain:
                                    new_domains.add(domain)
                                    loaded_count += 1
                print(f"[PhishGuard] Loaded {loaded_count} domains from Tranco ZIP")
            except (zipfile.BadZipFile, Exception):
                # Read as plain CSV
                with open(tranco_path, 'r', encoding='utf-8', errors='replace') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            domain = row[1].strip().lower()
                            if domain:
                                new_domains.add(domain)
                                loaded_count += 1
                        elif len(row) == 1:
                            domain = row[0].strip().lower()
                            if domain and not domain.isdigit():
                                new_domains.add(domain)
                                loaded_count += 1
                print(f"[PhishGuard] Loaded {loaded_count} domains from Tranco CSV")

            # Thread-safe update
            with self._trusted_lock:
                self.trusted_domains.update(new_domains)
            self._tranco_loaded = True
            print(f"[PhishGuard] Tranco loading complete. Total trusted: {len(self.trusted_domains)}")

        except Exception as e:
            print(f"[PhishGuard] Error loading Tranco: {e}. Using minimal set.")
            self._tranco_loaded = True

    def _extract_domain(self, url: str) -> str:
        """Extract and normalize domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if not domain:
                # Handle bare domains like "google.com/path"
                domain = url.split('/')[0].lower()
            # Remove port
            domain = domain.split(':')[0]
            # Remove www.
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return url.lower()

    def _get_base_domain(self, domain: str) -> str:
        """Extract base domain (e.g., 'mail.google.com' -> 'google.com')."""
        parts = domain.split('.')
        if len(parts) > 2:
            return '.'.join(parts[-2:])
        return domain

    def verify_url(self, url: str) -> dict:
        """
        4-Layer verification engine:
        1. Coinbase Allowlist (instant)
        2. Known Blocklist (instant)
        3. Tranco Trusted Check (instant)
        4. ML Model with LRU Cache
        """
        domain = self._extract_domain(url)
        base_domain = self._get_base_domain(domain)

        # Layer 1: Official Coinbase
        if domain in self.allowlist or base_domain in self.allowlist:
            return {
                "status": "safe",
                "message": "Official Coinbase Domain",
                "confidence": 1.0,
                "badge": "green_shield"
            }

        # Layer 2: Known Phishing
        if domain in self.blocklist or base_domain in self.blocklist:
            return {
                "status": "phish",
                "message": "Known Phishing Domain",
                "confidence": 1.0,
                "badge": "red_alert"
            }

        # Layer 3: Tranco Trusted (thread-safe read)
        with self._trusted_lock:
            is_trusted = (domain in self.trusted_domains or base_domain in self.trusted_domains)

        if is_trusted:
            return {
                "status": "trusted",
                "message": "Verified Popular Site",
                "confidence": 0.95,
                "badge": "gray_shield"
            }

        # Layer 4: ML Model with Cache
        cached = self.prediction_cache.get(url)
        if cached is not None:
            return cached

        try:
            model = get_model()
            probability = model.predict(url)
        except Exception:
            # If ML model fails, return neutral
            return {
                "status": "neutral",
                "message": "Unverified Site",
                "confidence": 0.5,
                "badge": "neutral"
            }

        if probability > 0.65:
            result = {
                "status": "warning",
                "message": f"Suspected Phishing (ML: {probability:.0%} confidence)",
                "confidence": probability,
                "badge": "red_alert"
            }
        elif probability > 0.4:
            result = {
                "status": "neutral",
                "message": "Unverified Site — Proceed with Caution",
                "confidence": probability,
                "badge": "neutral"
            }
        else:
            result = {
                "status": "neutral",
                "message": "Likely Safe (ML: Low Risk)",
                "confidence": 1.0 - probability,
                "badge": "neutral"
            }

        self.prediction_cache.put(url, result)
        return result


# Singleton — initialized on import
detector = PhishGuard()
