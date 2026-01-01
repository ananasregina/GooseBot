#!/usr/bin/env python3
"""
Test script to verify GooseBot setup
"""
import sys

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")

    try:
        from goosebot.config import Config
        print("✅ Config imported")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False

    try:
        from goosebot.session_manager import SessionManager
        print("✅ SessionManager imported")
    except Exception as e:
        print(f"❌ SessionManager import failed: {e}")
        return False

    try:
        from goosebot.goose_client import GooseClient
        print("✅ GooseClient imported")
    except Exception as e:
        print(f"❌ GooseClient import failed: {e}")
        return False

    try:
        from goosebot.handlers import MessageHandler, CommandHandler
        print("✅ Handlers imported")
    except Exception as e:
        print(f"❌ Handlers import failed: {e}")
        return False

    try:
        from goosebot.bot import GooseBot
        print("✅ GooseBot imported")
    except Exception as e:
        print(f"❌ GooseBot import failed: {e}")
        return False

    return True

def test_dependencies():
    """Test required dependencies"""
    print("\nTesting dependencies...")

    try:
        import discord
        print(f"✅ discord.py {discord.__version__}")
    except ImportError:
        print("❌ discord.py not installed")
        return False

    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not installed")
        return False

    return True

def test_goose_cli():
    """Test Goose CLI availability"""
    print("\nTesting Goose CLI...")

    import shutil
    goose_path = shutil.which("goose")

    if goose_path:
        print(f"✅ Goose CLI found at: {goose_path}")
        return True
    else:
        print("❌ Goose CLI not found in PATH")
        return False

def main():
    """Run all tests"""
    print("🦆 GooseBot Setup Verification")
    print("=" * 40)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Dependencies", test_dependencies()))
    results.append(("Goose CLI", test_goose_cli()))

    print("\n" + "=" * 40)
    print("Summary:")
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False

    print("=" * 40)

    if all_passed:
        print("\n🎉 All tests passed! You're ready to run GooseBot.")
        print("\nNext steps:")
        print("1. Create config.env from config.env.example")
        print("2. Add your Discord bot token")
        print("3. Run: python run.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
