# Simple sed replacement to disable the text handler
import re

# Read the file
with open('/Users/mramirez/personal/expense-tracker-claude/src/telegram/financial_agent_handlers.py', 'r') as f:
    content = f.read()

# Replace the decorator line to disable it
content = content.replace(
    '@financial_router.message(F.text & ~F.text.startswith("/"))',
    '# DISABLED: Interferes with original agent Spanish processing\n# @financial_router.message(F.text & ~F.text.startswith("/"))'
)

# Write back
with open('/Users/mramirez/personal/expense-tracker-claude/src/telegram/financial_agent_handlers.py', 'w') as f:
    f.write(content)

print("Successfully disabled the text expense handler")
