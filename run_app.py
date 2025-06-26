#!/usr/bin/env python3
"""
Launcher script for the Turbo.az Car Monitor Web App
"""

if __name__ == "__main__":
    try:
        from app import app, socketio

        print("🚗 Starting Turbo.az Car Monitor Web App")
        print("🌐 Open your browser to http://localhost:5000")
        print("⏹️  Press Ctrl+C to stop")

        socketio.run(app, host="0.0.0.0", port=5000, debug=False)

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("📦 Run: pip install -r requirements.txt")
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting app: {e}")
