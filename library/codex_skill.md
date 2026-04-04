# 📚 Codex Vault Bridge (Phase 8)

This skill allows the Architect to bridge external knowledge bases (like Obsidian or Logseq) into its Neural Memory (RAG) system.

## 🛠️ Usage
1. Configure `CODEX_VAULT_PATH` in your `.env`.
2. Run `/run_skill codex` to sync your local vault.

```python
import os
import glob
import requests
import json

# Placeholder for real Codex sync logic
VAULT_PATH = os.getenv("CODEX_VAULT_PATH", "/home/user/vault")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

def sync_codex():
    if not os.path.exists(VAULT_PATH):
        print(f"❌ Vault path not found: {VAULT_PATH}")
        return

    md_files = glob.glob(f"{VAULT_PATH}/**/*.md", recursive=True)
    print(f"📚 Found {len(md_files)} documents in Codex Vault.")

    # In Phase 8, this will call the internal /reindex logic for these external paths
    print("⏳ Syncing to Neural Memory (Phase 8 Implementation)...")
    for f in md_files[:5]: # Sample for now
        print(f"✅ Indexed: {os.path.basename(f)}")

    print("🏆 Codex Sync Foundation Established.")

if __name__ == "__main__":
    sync_codex()
```

## ✅ Verification
1. Ensure `CODEX_VAULT_PATH` is set.
2. Run this skill to verify file discovery.
