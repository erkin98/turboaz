#!/usr/bin/env python3
"""
Setup script for Turbo.az Car Monitor Bot
"""
import os
import sys


def create_env_file():
    """Create .env file from template."""
    if os.path.exists(".env"):
        print("✅ .env file already exists")
        return

    print("🔧 Creating .env file...")
    env_content = """# Telegram Bot Configuration
# Get BOT_TOKEN from @BotFather on Telegram
BOT_TOKEN=your_bot_token_here

# Your Telegram Chat ID or Channel ID where notifications will be sent
# To get your chat ID, message @userinfobot on Telegram
CHAT_ID=your_chat_id_here
"""

    with open(".env", "w") as f:
        f.write(env_content)

    print("✅ Created .env file")
    print("📝 Please edit .env and add your BOT_TOKEN and CHAT_ID")


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")

    required_packages = [
        "python-telegram-bot",
        "requests",
        "beautifulsoup4",
        "python-dotenv",
        "lxml",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("📦 Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies are installed")
        return True


def main():
    """Main setup function."""
    print("🚗 Turbo.az Car Monitor Bot Setup")
    print("=" * 40)

    # Create .env file
    create_env_file()

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Setup incomplete. Please install dependencies first.")
        sys.exit(1)

    print("\n✅ Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your bot credentials")
    print("2. Run: python main.py")
    print("\n💡 For help getting credentials, see README.md")


if __name__ == "__main__":
    main()
