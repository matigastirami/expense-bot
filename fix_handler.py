#!/usr/bin/env python3
"""
Script to disable the Financial Analysis Agent text handler that interferes with Spanish processing.
"""

file_path = '/Users/mramirez/personal/expense-tracker-claude/src/telegram/financial_agent_handlers.py'

# Read the current file
with open(file_path, 'r') as f:
    content = f.read()

# Find and replace the problematic handler
old_decorator = '@financial_router.message(F.text & ~F.text.startswith("/"))'
new_decorator = '# DISABLED: Interferes with Spanish processing\n# @financial_router.message(F.text & ~F.text.startswith("/"))'

if old_decorator in content:
    content = content.replace(old_decorator, new_decorator)
    print(f"✅ Disabled the decorator: {old_decorator}")
else:
    print(f"❌ Decorator not found: {old_decorator}")

# Also add a return statement at the beginning of the function if not already there
function_start = 'async def handle_text_expense(message: Message, state: FSMContext):\n    """Handle text messages that might be expenses for enhanced processing."""'
function_with_return = 'async def handle_text_expense(message: Message, state: FSMContext):\n    """Handle text messages that might be expenses for enhanced processing."""\n    # DISABLED: Return early to prevent interference\n    return'

if function_start in content and 'return early to prevent interference' not in content:
    content = content.replace(function_start, function_with_return)
    print("✅ Added return statement to disable function")
else:
    print("⚠️ Function already has return or not found")

# Write the modified content back
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Handler successfully disabled!")
print("🚀 Spanish expense processing should now work with the original agent")
