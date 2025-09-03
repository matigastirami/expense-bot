# Cursor Prompt — Generate AI Telegram Agent for Personal Finance (Python, LangChain)

You are Cursor. Create a production-ready Python repository for a **Telegram-only AI agent** that logs income/expenses/transfers/conversions via **natural language**, keeps **multi-currency balances per account**, fetches **FX rates** when missing, and answers queries (balances, spend by period, largest purchase, monthly report). No web UI.

## High-level requirements

- **Interface**: Telegram bot only.
- **Agent**: LangChain (OpenAI API) using tools (no inline code execution by the LLM).
- **Tools**:
  1. **DB Tool** (read/write): register transactions, create accounts on the fly, query balances and reports.
  2. **FX Tool** (read): fetch real-time exchange rates for fiat/crypto/stablecoins when not provided by user.
- **DB**: PostgreSQL with SQLAlchemy 2.0 + Alembic. Persist balances per account+currency. Optional materialized balance cache.
- **Runtime**: Python 3.11+, async where possible.
- **Testing**: Pytest, fast unit tests, plus a few integration tests with a local Postgres container.
- **Ops**: Dockerfile + docker-compose for app+db, Makefile, typed (mypy), linted (ruff), formatted (black).

## Core behaviors

1. **Natural language logging**  
   Examples the agent must correctly parse and persist:
   - “I received 6k USD salary for August via Deel”
   - “I transferred 1K USD to my Astropay account and received 992 USD”
   - “I spent 400k ARS from my Galicia/Mercado Pago account”
   - “I converted 10 USDT to ARS in Belo at 1350 ARS per USDT”  
   Rules:
   - If **account** not found, **auto-create** it.
   - For **conversions**, decrease balance of (account, currency_from), increase (account, currency_to) using the rate (provided or fetched).
   - For **transfers**, move funds between two accounts in the same currency (or two currencies if a rate is provided—else error).
   - For **expenses/income**, update the single affected (account, currency).
   - Every write must be **transactional** (commit/rollback).

2. **Queries & reasoning**  
   Natural asks the agent must answer:
   - “How much did I spend on Aug 15?”
   - “Show my expenses between Sept 1 and Sept 7”
   - “What was my largest purchase in August?”
   - “How much did I save in July?” (income – expenses)
   - “What’s my balance in Galicia?”
   - “Show all my accounts and balances”  
   Output format for balance list:
   ```
   * <Account Name> – <CURRENCY> <amount>
   ```
   Multi-currency accounts show multiple lines.

3. **FX behavior**  
   - If the user omits a rate, call **FX Tool** to fetch it (fiat/stable/crypto).
   - Store resolved rates (pair, value, source, timestamp).
   - Make FX source pluggable with clear provider interfaces (e.g., CoinGecko for crypto/stables, configurable ARS sources).

4. **Monthly reports**  
   - Command or natural ask: month-end summary showing:
     - Total income, total expenses, net savings
     - Largest transaction
     - Balances by account (multi-currency)
   - Optionally include a simple ASCII table.

## Data model (SQLAlchemy 2.0)

Use Decimal for money (quantize to 2 or 6 as appropriate). UTC timestamps.

- `accounts`
  - `id` (PK)
  - `name` (str, unique per user scope; MVP is single user)
  - `type` (enum: bank, wallet, cash, other)
  - `created_at` (datetime)

- `account_balances`
  - `id` (PK)
  - `account_id` (FK → accounts.id, indexed)
  - `currency` (str, e.g., ARS, USD, USDT, BTC)
  - `balance` (Decimal)
  - `updated_at` (datetime)
  - **Unique(account_id, currency)**

- `transactions`
  - `id` (PK)
  - `type` (enum: income, expense, transfer, conversion)
  - `account_from_id` (nullable FK)
  - `account_to_id` (nullable FK)
  - `currency` (str)                # origin or single-currency txn
  - `amount` (Decimal)
  - `currency_to` (nullable str)     # for conversion
  - `amount_to` (nullable Decimal)   # for conversion
  - `exchange_rate` (nullable Decimal)
  - `description` (nullable str)
  - `date` (datetime)                # use user local date parsed; store UTC
  - `created_at` (datetime default now)

- `exchange_rates`
  - `id` (PK)
  - `pair` (str, e.g., “USDT/ARS”)
  - `value` (Decimal)
  - `source` (str)
  - `fetched_at` (datetime)

## Agent design (LangChain)

- **Approach**: ReAct-style agent with **structured output** (Pydantic) for extraction to lower errors.
- **LLM**: OpenAI chat model (config via env).
- **Tools**:
  - `DbTool`: class with explicit methods invoked via LangChain tool schema
  - `FxTool`: methods:
    - `get_rate(base: str, quote: str) -> (rate, source)`
    - Simple caching (in-memory) + DB write to `exchange_rates`.

- **Parsing**:
  - Use a **Pydantic schema** for “ParsedTransactionIntent” with fields:
    - `intent`, accounts, amounts, currencies, date, description, rate if present
  - The agent first **extracts** to this schema, then **decides** which Tool method(s) to call.

- **Safety**:
  - The LLM **must not** mutate the DB directly—only via tools.
  - Validate amounts > 0, supported currencies, and coherent combinations.
  - If info is insufficient, agent asks a **clarifying question**.

## Telegram bot

- Library: **aiogram** (async).
- Commands:
  - `/start`, `/help`, `/balance [account]`, `/report [YYYY-MM]`
  - Fallback handler forwards raw text to the agent.

## Project structure

```
finance-agent/
  pyproject.toml
  README.md
  .env.example
  Makefile
  docker-compose.yml
  Dockerfile
  src/
    app.py
    config.py
    agent/
      llm.py
      schemas.py
      tools/
        db_tool.py
        fx_tool.py
      agent.py
      prompts/
        system.md
        fewshots.md
    db/
      base.py
      models.py
      crud.py
      migrations/
      seed.py
    integrations/
      fx/
        providers/
          coingecko.py
          ars_sources.py
        service.py
    telegram/
      bot.py
      formatters.py
    utils/
      timeparse.py
      money.py
  tests/
    test_parsing.py
    test_db_tool.py
    test_fx_tool.py
    test_flows.py
```

## Environment (.env.example)

```
# OpenAI
OPENAI_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=123:abc

# Postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=finance
POSTGRES_USER=finance
POSTGRES_PASSWORD=finance

# FX
FX_PRIMARY=coingecko
ARS_SOURCE=blue
```

## Tooling & quality

- pyproject.toml: black, ruff, mypy, pytest, aiogram, langchain, pydantic-settings, SQLAlchemy 2.0 async, asyncpg, alembic, dateparser, tenacity.

## Tests

- Parsing 10+ inputs
- DbTool E2E (income, expense, transfer, conversion)
- FxTool mocked rates
- Monthly reports
- Telegram handlers

## Acceptance criteria

- `docker-compose up` launches app + Postgres
- `/start` works
- pytest all green
- lint/format/type checks pass
- Alembic creates all tables with constraints
- FX fetched when missing
