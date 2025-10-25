#!/usr/bin/env python3
"""
Standalone CLI interface for the Finance Agent.

Usage:
    python packages/agent/cli.py "I spent 50 USD at the supermarket"
    python packages/agent/cli.py "How much did I spend last week?"
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.agent.agent import FinanceAgent


async def process_query(query: str, user_id: int = 1):
    """Process a single query using the finance agent."""
    agent = FinanceAgent()

    print(f"\n🤖 Processing: {query}\n")

    response, transaction_data = await agent.process_message(query, user_id)

    print(response)

    # If there's transaction data, it means confirmation is needed
    if transaction_data:
        print("\n⚠️  Note: Transaction requires confirmation. Use the REPL or Telegram bot for interactive confirmation.")

    print()


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python packages/agent/cli.py 'Your financial query or transaction'")
        print("\nExamples:")
        print('  python packages/agent/cli.py "I received 1000 USD in my Deel account"')
        print('  python packages/agent/cli.py "How much did I spend this week?"')
        print('  python packages/agent/cli.py "Show my balance"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # Run the async query
    asyncio.run(process_query(query))


if __name__ == "__main__":
    main()
