# PRD – English Version

## 1. Objective
Build an **AI-powered financial tracking agent** that works via **Telegram chat**. The agent should allow users to record **income, expenses, transfers, and currency conversions** in natural language. It must support **multi-currency accounts** (e.g., Belo holding both USDT and ARS) and provide **real-time balances, reports, and insights**.

---

## 2. Scope (MVP)

### Core Features
1. **Natural language transaction logging**
   - Example inputs:
     - “I received 6k USD salary via Deel.”
     - “I transferred 1k USD to Astropay, received 992 USD.”
     - “I spent 400k ARS from my Galicia account.”
     - “I converted 10 USDT to ARS at 1350.”
   - Extract: type, amount, source/destination account, currency, date, exchange rate (if missing, fetch real-time).

2. **Account management**
   - Accounts (e.g., Deel, Galicia, Belo, Cash) are auto-created if not existing.
   - Each account can hold **multiple currencies**.
   - Balances are updated automatically after each transaction.

3. **Currency exchange integration**
   - Fetch rates from APIs: USD ↔ ARS (official, blue, MEP), stablecoins, crypto.
   - If rate missing, fetch in real-time.

4. **Queries and balance checks**
   - Examples:
     - “How much did I spend in August?”
     - “What’s my balance in Galicia?”
     - “Show all my accounts.”
   - Response format:
     ```
     * Deel – USD 6,000
     * Astropay – USD 992
     * Galicia – ARS 400,000
     * Belo – USDT 50, ARS 13,500
     * Cash – ARS 50,000
     ```

5. **Monthly reports**
   - Sent automatically at month-end.
   - Includes: total income, total expenses, net savings, balances by account, largest transaction.

---

## 3. Out of Scope (MVP)
- Web dashboard.
- Multi-user support.
- Expense categorization beyond account/currency.
- Investment recommendations.

---

## 4. Technology

- **Agent orchestration**: LangChain (Python) + OpenAI API.
- **Interface**: Telegram Bot API.
- **Database**: PostgreSQL with SQLAlchemy.

### Database schema
- `accounts` → id, name, type, created_at.
- `account_balances` → id, account_id (FK), currency, balance.
- `transactions` → id, type, amount, currency, account_from_id, account_to_id, currency_to, amount_to, exchange_rate, description, date.

---

## 5. Agent Design
- **LangChain ReAct agent** with Tools:
  - **DB Tool** → register/query transactions and balances.
  - **FX Tool** → fetch exchange rates.

Example flow:
```
User: "I converted 10 USDT to ARS in Belo at 1350"
Agent:
  - Detects conversion
  - Updates Belo: -10 USDT, +13,500 ARS
  - Stores transaction
Reply: "Conversion registered in Belo: -10 USDT → +13,500 ARS"
```

---

## 6. UX (Telegram)
- Natural input for transactions.
- Commands:
  - `/balance` → show all accounts.
  - `/balance <account>` → show single account.
  - `/report` → monthly report.
  - `/help` → usage guide.

---

## 7. Roadmap

**MVP**
- Transaction parsing.
- Multi-currency account balances.
- Queries + reports in Telegram.

**Phase 2**
- Categorization (food, transport, etc.).
- Consolidated net worth view (convert all to base currency).
- Web dashboard.
- Multi-user support.
- AI advisor for spending optimization and investing.

---

## 8. Success Metrics
- >90% transactions correctly classified.
- Account auto-creation works without errors.
- Balances consistent across queries.
- <5s response time per query.
