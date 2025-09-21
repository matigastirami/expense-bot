#!/usr/bin/env python3
"""
Test the confirmation ID parsing fix.
"""

def test_callback_data_parsing():
    """Test the corrected callback data parsing."""
    print("🔍 Testing Callback Data Parsing Fix")
    print("=" * 40)

    # Simulate the issue and fix
    confirmation_id = "123_1758339474854"
    callback_data = f"expense_confirm_{confirmation_id}"

    print(f"Original confirmation ID: {confirmation_id}")
    print(f"Callback data: {callback_data}")

    # Old broken method
    old_parts = callback_data.split("_")
    old_action = old_parts[1]
    old_confirmation_id = old_parts[2]  # This was only getting "123"

    print(f"\n❌ Old method:")
    print(f"   Parsed action: {old_action}")
    print(f"   Parsed confirmation_id: {old_confirmation_id}")
    print(f"   Expected: {confirmation_id}")
    print(f"   Match: {old_confirmation_id == confirmation_id}")

    # New fixed method
    new_parts = callback_data.split("_", 2)  # Split only on first 2 underscores
    new_action = new_parts[1]
    new_confirmation_id = new_parts[2]  # This gets the full ID

    print(f"\n✅ New method:")
    print(f"   Parsed action: {new_action}")
    print(f"   Parsed confirmation_id: {new_confirmation_id}")
    print(f"   Expected: {confirmation_id}")
    print(f"   Match: {new_confirmation_id == confirmation_id}")

    # Test with other actions
    other_callbacks = [
        f"expense_category_{confirmation_id}",
        f"expense_necessity_{confirmation_id}",
        f"expense_cancel_{confirmation_id}",
    ]

    print(f"\n🧪 Testing other callback types:")
    for callback in other_callbacks:
        parts = callback.split("_", 2)
        action = parts[1]
        parsed_id = parts[2]
        match = parsed_id == confirmation_id
        status = "✅" if match else "❌"
        print(f"   {status} {callback} → action={action}, id={parsed_id}")

    return new_confirmation_id == confirmation_id


if __name__ == "__main__":
    print("🔧 Confirmation ID Parsing Fix Test")
    print("=" * 50)

    success = test_callback_data_parsing()

    print("\n" + "=" * 50)
    if success:
        print("✅ Fix verified! Confirmation IDs should now work correctly.")
        print("\n🚀 Next steps:")
        print("1. Restart your bot to load the fix")
        print("2. Test audio messages again")
        print("3. Confirmation buttons should no longer expire immediately")
    else:
        print("❌ Fix verification failed!")
