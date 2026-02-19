#!/usr/bin/env python3
"""Diagnostic script for Phish-Guard backend"""
import sys
import os
import traceback

# Write results to a file since terminal output is broken
output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag_output.txt")
results = []

def log(msg):
    results.append(msg)
    print(msg)  # Also try stdout

log("=== Phish-Guard Diagnostic ===")
log(f"Python: {sys.version}")
log(f"Working dir: {os.getcwd()}")
log(f"Script dir: {os.path.dirname(os.path.abspath(__file__))}")

# Test 1: Basic imports
log("\n--- Testing imports ---")
for pkg in ["fastapi", "uvicorn", "pandas", "sklearn", "pydantic"]:
    try:
        __import__(pkg)
        log(f"  ✓ {pkg}")
    except ImportError as e:
        log(f"  ✗ {pkg}: {e}")

# Test 2: ML Model
log("\n--- Testing ML Model ---")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ml_model import phishing_model
    log(f"  ✓ ML model loaded, model type: {type(phishing_model.model)}")
    prob = phishing_model.predict("http://coinbase-fake.xyz/login")
    log(f"  ✓ Prediction test: {prob:.3f}")
except Exception as e:
    log(f"  ✗ ML model error: {e}")
    log(traceback.format_exc())

# Test 3: Phishing Detector
log("\n--- Testing Phishing Detector ---")
try:
    from phishing_detector import detector
    log(f"  ✓ Detector loaded")
    log(f"  ✓ Trusted domains: {len(detector.trusted_domains)}")
    log(f"  ✓ Blocklist: {len(detector.blocklist)}")
    
    # Test some URLs
    tests = [
        "https://www.coinbase.com",
        "https://www.google.com",
        "https://coinbase-support.xyz",
        "http://coinbase-login-update.net",
    ]
    for url in tests:
        result = detector.verify_url(url)
        log(f"  {url[:40]}: {result['status']} - {result['message']}")
except Exception as e:
    log(f"  ✗ Detector error: {e}")
    log(traceback.format_exc())

# Test 4: Static files
log("\n--- Testing Static Files ---")
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
log(f"  Static dir: {static_dir}")
log(f"  Exists: {os.path.exists(static_dir)}")
if os.path.exists(static_dir):
    files = os.listdir(static_dir)
    log(f"  Files: {files}")
    index_path = os.path.join(static_dir, "index.html")
    log(f"  index.html exists: {os.path.exists(index_path)}")

# Write results to file
log("\n=== Diagnostic Complete ===")
with open(output_file, "w") as f:
    f.write("\n".join(results))
print(f"\nResults written to: {output_file}")
