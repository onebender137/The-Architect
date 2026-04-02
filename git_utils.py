import subprocess

def git_manager(action: str, commit_message: str = "Update by Jules") -> str:
    """Simple git operations: push, pull, status"""
    try:
        if action == "push":
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            result = subprocess.run(["git", "push"], capture_output=True, text=True, check=True)
            return f"🚀 Pushed to GitHub:\n{result.stdout.strip()}"

        elif action == "pull":
            result = subprocess.run(["git", "pull"], capture_output=True, text=True, check=True)
            return f"📥 Pulled changes:\n{result.stdout.strip()}"

        elif action == "status":
            result = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
            return result.stdout.strip()

        return "❌ Unknown git action."

    except subprocess.CalledProcessError as e:
        error = e.stderr.strip() if e.stderr else str(e)
        return f"❌ Git Error: {error}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"
