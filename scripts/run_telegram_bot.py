#!/usr/bin/env python3
"""Script to run the Telegram bot independently."""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.telegram_bot import start_bot, stop_bot


async def main():
    """Run the Telegram bot."""
    print("🤖 Starting Telegram Bot...")
    print("Press Ctrl+C to stop\n")

    application = await start_bot()

    if not application:
        print("❌ Failed to start bot. Check TELEGRAM_BOT_TOKEN in .env")
        return

    print("✅ Bot is running!")
    print("Open Telegram and search for your bot\n")

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down bot...")
        await stop_bot(application)
        print("✅ Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
