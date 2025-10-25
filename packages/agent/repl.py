#!/usr/bin/env python3
"""
Interactive REPL for the Finance Agent.

Provides an interactive session where you can:
- Record transactions
- Query balances and reports
- Confirm transactions interactively

Usage:
    python packages/agent/repl.py
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.agent.agent import FinanceAgent


class FinanceAgentREPL:
    """Interactive REPL for Finance Agent."""

    def __init__(self, user_id: int = 1):
        self.agent = FinanceAgent()
        self.user_id = user_id
        self.pending_transaction = None

    async def process_input(self, user_input: str):
        """Process user input and handle responses."""
        user_input = user_input.strip()

        # Check for REPL commands
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Goodbye!")
            return False

        if user_input.lower() in ['help', 'h', '?']:
            self.show_help()
            return True

        # Check if we have a pending transaction
        if self.pending_transaction:
            if user_input.lower() in ['yes', 'y', 'si', 's', 'confirm']:
                # Confirm the transaction
                response = await self.agent.confirm_transaction(self.pending_transaction)
                print(f"\n{response}\n")
                self.pending_transaction = None
            elif user_input.lower() in ['no', 'n', 'cancel']:
                print("\n❌ Transaction cancelled.\n")
                self.pending_transaction = None
            else:
                print("\n⚠️  Please answer 'yes' or 'no' to confirm/cancel the transaction.\n")
            return True

        # Process as normal query/transaction
        try:
            response, transaction_data = await self.agent.process_message(user_input, self.user_id)
            print(f"\n{response}\n")

            # Store pending transaction if confirmation needed
            if transaction_data:
                self.pending_transaction = transaction_data

        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")

        return True

    def show_help(self):
        """Show help message."""
        print("""
📚 Finance Agent REPL - Help

TRANSACTIONS:
  Record income, expenses, transfers, and currency conversions in natural language.

  Examples:
    "I received 1000 USD in my Deel account"
    "I spent 50 USD at the supermarket"
    "I transferred 200 USD from Deel to Astropay"

QUERIES:
  Ask about balances, spending, income, and reports.

  Examples:
    "How much do I have in Deel?"
    "How much did I spend this week?"
    "Show my expenses last month"
    "What was my largest purchase this year?"

COMMANDS:
  help, h, ?     - Show this help message
  yes, y, si, s  - Confirm pending transaction
  no, n, cancel  - Cancel pending transaction
  exit, quit, q  - Exit the REPL

NOTES:
  - Supports both English and Spanish
  - Transactions require confirmation before being saved
  - Press Ctrl+C to interrupt at any time
        """)

    async def run(self):
        """Run the REPL loop."""
        print("""
╔══════════════════════════════════════════════════════════╗
║           Finance Agent - Interactive REPL               ║
║                                                          ║
║  Ask questions, record transactions, check balances     ║
║  Type 'help' for commands, 'exit' to quit               ║
╚══════════════════════════════════════════════════════════╝
        """)

        while True:
            try:
                # Show prompt
                prompt = "💰 > " if not self.pending_transaction else "⚠️  Confirm? (yes/no) > "
                user_input = input(prompt)

                # Process input
                should_continue = await self.process_input(user_input)
                if not should_continue:
                    break

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break


async def main():
    """Main REPL entry point."""
    repl = FinanceAgentREPL()
    await repl.run()


if __name__ == "__main__":
    asyncio.run(main())
