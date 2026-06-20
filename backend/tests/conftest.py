import os

# Deterministic tests: force fixture mode so importing app.config (which loads
# .env.local with a real key) never makes the suite hit live providers.
os.environ["APP_ENV"] = "fixture"
