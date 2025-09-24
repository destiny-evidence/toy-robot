"""Entry point script for running the toy robot in polling mode."""

import asyncio

from app.main import main

if __name__ == "__main__":
    asyncio.run(main())
