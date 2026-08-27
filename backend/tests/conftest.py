import os

# Unit tests instantiate agents/settings directly without a real .env file.
# api_key has no code default on purpose (see core/config.py), so tests must
# supply one explicitly rather than the app silently accepting a blank secret.
os.environ.setdefault("API_KEY", "test-key")
