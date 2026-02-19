import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestClassifier
import os
import threading

class PhishingModel:
    def __init__(self, dataset_path="datasets/PhiUSIIL_Phishing_URL_Dataset.csv"):
        self.dataset_path = dataset_path
        self.model = None
        self.vectorizer = None
        self._lock = threading.Lock()
        self._ready = threading.Event()

        # Train in background so server starts immediately
        self._train_thread = threading.Thread(
            target=self._train_background,
            daemon=True,
            name="MLTrainer"
        )
        self._train_thread.start()

    def _train_background(self):
        """Train the model in a background thread."""
        try:
            self.load_and_train()
        except Exception as e:
            print(f"[ML] Background training failed: {e}. Using dummy model.")
            self._train_dummy()
        finally:
            self._ready.set()

    def _train_dummy(self):
        """Fallback dummy model if dataset fails."""
        import pandas as pd
        dummy_urls = [
            "google.com", "facebook.com", "amazon.com", "github.com",
            "coinbase.com", "reddit.com", "youtube.com", "twitter.com",
            "coinbase-fake-login.xyz", "coinbase-support-help.net",
            "wallet-connect-phish.com", "verify-coinbase-kyc.net",
            "secure-coinbase-login.xyz", "coinbase-airdrop-claim.com",
            "free-crypto-coinbase.net", "coinbase-wallet-update.xyz",
        ]
        dummy_labels = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]
        df = pd.DataFrame({"url": dummy_urls, "label": dummy_labels})
        with self._lock:
            self.model = make_pipeline(
                TfidfVectorizer(analyzer='char', ngram_range=(3, 5)),
                RandomForestClassifier(n_estimators=50, random_state=42)
            )
            self.model.fit(df['url'], df['label'])
        print("[ML] Dummy model trained as fallback.")

    def load_and_train(self):
        """Loads data and trains the model."""
        if not os.path.exists(self.dataset_path):
            print(f"[ML] Dataset not found at {self.dataset_path}. Using dummy data.")
            self._train_dummy()
            return

        try:
            print(f"[ML] Loading dataset: {self.dataset_path}")
            df = pd.read_csv(self.dataset_path)

            # Auto-detect column names
            cols = {c.lower(): c for c in df.columns}

            url_col = cols.get('url') or cols.get('domain')
            if not url_col:
                raise ValueError(f"No URL column found. Columns: {list(df.columns)}")

            label_col = cols.get('label') or cols.get('type') or cols.get('status') or cols.get('result')
            if not label_col:
                raise ValueError(f"No label column found. Columns: {list(df.columns)}")

            df = df.rename(columns={url_col: 'url', label_col: 'label'})
            df = df[['url', 'label']].dropna()

            # Handle text labels
            if df['label'].dtype == 'object':
                df['label'] = df['label'].apply(
                    lambda x: 0 if str(x).lower() in ['benign', 'good', 'legitimate', '0'] else 1
                )
            elif df['label'].dtype in ['int64', 'float64']:
                # UCI PhiUSIIL: 1=Legitimate, 0=Phishing — invert
                if 'urllength' in cols and 'tldlegitimateprob' in cols:
                    print("[ML] Detected PhiUSIIL format — inverting labels")
                    df['label'] = 1 - df['label'].astype(int)

            print(f"[ML] Training on {len(df)} samples...")
            model = make_pipeline(
                TfidfVectorizer(analyzer='char', ngram_range=(3, 5)),
                RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
            )
            model.fit(df['url'].astype(str), df['label'])

            with self._lock:
                self.model = model
            print("[ML] Model trained successfully.")

        except Exception as e:
            print(f"[ML] Error loading dataset: {e}. Falling back to dummy model.")
            self._train_dummy()

    def predict(self, url: str) -> float:
        """Returns probability of being phishing (0.0 to 1.0).
        Waits up to 30s for model to be ready, then returns 0.5 (neutral)."""
        if not self._ready.wait(timeout=30):
            return 0.5  # Model not ready yet — return neutral

        with self._lock:
            if self.model is None:
                return 0.5
            try:
                prob = self.model.predict_proba([url])[0][1]
                return float(prob)
            except Exception:
                return 0.5

    @property
    def is_ready(self):
        return self._ready.is_set()


# Singleton — training starts immediately in background
phishing_model = PhishingModel()
