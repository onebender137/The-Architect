import sys
import logging
import os

# Configure dummy logging
logging.basicConfig(level=logging.INFO)

def test_imports():
    # Set dummy env var for TOKEN that passes aiogram validation
    os.environ["BOT_TOKEN"] = "123456789:AAG_xyz123abc456def789ghiJKLMNopqrs"

    try:
        import hardware_config
        print("✅ hardware_config imported successfully.")

        import git_utils
        print("✅ git_utils imported successfully.")

        import skill_manager
        print("✅ skill_manager imported successfully.")

        import handlers
        print("✅ handlers imported successfully.")

        import coder_agent
        print("✅ coder_agent imported successfully.")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_imports():
        print("🚀 Modularization verified!")
        sys.exit(0)
    else:
        sys.exit(1)
