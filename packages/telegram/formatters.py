from typing import List

from src.agent.schemas import BalanceInfo, TransactionInfo


def format_balances_telegram(balances: List[BalanceInfo]) -> str:
    """Format balance information for Telegram display."""
    if not balances:
        return "💰 No balances found."
    
    # Group by account
    accounts = {}
    for balance in balances:
        if balance.account_name not in accounts:
            accounts[balance.account_name] = []
        accounts[balance.account_name].append(balance)
    
    lines = ["💰 <b>Account Balances:</b>", ""]
    for account_name, account_balances in accounts.items():
        if len(account_balances) == 1:
            balance = account_balances[0]
            lines.append(f"• {account_name} – {balance.currency} {balance.balance:,.2f}")
        else:
            currencies = []
            for balance in account_balances:
                currencies.append(f"{balance.currency} {balance.balance:,.2f}")
            lines.append(f"• {account_name} – {', '.join(currencies)}")
    
    return "\n".join(lines)


def format_transactions_telegram(transactions: List[TransactionInfo], title: str = "Transactions") -> str:
    """Format transaction list for Telegram display."""
    if not transactions:
        return f"📋 No {title.lower()} found."
    
    lines = [f"📋 <b>{title}:</b>", ""]
    
    for t in transactions:
        emoji = {"income": "💰", "expense": "💸", "transfer": "🔄", "conversion": "💱"}.get(t.type, "📝")
        
        account_info = ""
        if t.account_from and t.account_to:
            account_info = f" ({t.account_from} → {t.account_to})"
        elif t.account_from:
            account_info = f" from {t.account_from}"
        elif t.account_to:
            account_info = f" to {t.account_to}"
        
        date_str = t.date.strftime("%m/%d")
        amount_str = f"{t.amount:,.2f} {t.currency}"
        
        line = f"{emoji} {amount_str}{account_info} - {date_str}"
        if t.description:
            line += f" ({t.description})"
        
        lines.append(line)
    
    return "\n".join(lines)


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text