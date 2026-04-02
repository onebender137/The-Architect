# Security Policy

The Architect is designed with a local-first, privacy-centric approach. However, maintaining repository integrity requires robust secret scanning.

## 🛡️ TruffleHog Secret Scanning

We use [TruffleHog](https://github.com/trufflesecurity/trufflehog) to prevent sensitive information (like Telegram Bot Tokens) from being committed.

### 🐧 WSL / Linux Installation

To install TruffleHog in your WSL environment, run the following command:

```bash
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin
```

### ⚓ Setting up the Git Hook

A pre-push hook is provided in `scripts/pre-push`. This hook will scan your commits for secrets before every push.

To enable it, run:

```bash
cp scripts/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

### 🚫 Ignoring False Positives

If TruffleHog identifies a false positive, you can add the specific secret or path to `.trufflehog-ignore`.

## 🔒 Best Practices

1.  **Never commit `.env` files.** They are blocked by `.gitignore`, but double-check your staging area.
2.  **Use the pre-push hook.** Avoid using `--no-verify` unless absolutely necessary.
3.  **Modularized Code.** Logic is split into modular files to reduce the risk of large-file "rushed pushes" where secrets might hide.
