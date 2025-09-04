# Personal Finance AI Agent - Features

This Telegram bot serves as your intelligent personal finance assistant, capable of understanding natural language input in both English and Spanish to help you track your financial activities.

## 🎯 Core Features

### 📝 Natural Language Transaction Processing

The bot can parse and understand natural language descriptions of financial activities without requiring strict command formats.

**Transaction Types Supported:**
- **Income** - Money received (salary, freelance, gifts, etc.)
- **Expenses** - Money spent (purchases, bills, services, etc.) 
- **Transfers** - Money moved between your accounts
- **Conversions** - Currency exchanges with automatic rate tracking

**Examples:**
- "I received 6k USD salary via Deel"
- "Gasté 400k ARS from my Galicia account"
- "I transferred 1K USD to Astropay, received 992 USD"
- "I converted 10 USDT to ARS at 1350"
- "Gasté $400 de mercadopago"

### 🌍 Bilingual Support

**Supported Languages:**
- **English** - Full support for English financial terminology
- **Spanish** - Complete Spanish support with regional variations (especially Argentina)

**Automatic Language Detection:**
- Automatically detects the language of user input
- Responds in the same language used by the user
- Handles mixed language scenarios intelligently

### 💰 Multi-Currency Management

**Supported Currency Types:**

**Fiat Currencies:**
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- JPY (Japanese Yen)
- AUD (Australian Dollar)
- CAD (Canadian Dollar)
- CHF (Swiss Franc)
- ARS (Argentine Peso)
- BRL (Brazilian Real)
- CLP (Chilean Peso)
- COP (Colombian Peso)
- MXN (Mexican Peso)
- PEN (Peruvian Sol)
- UYU (Uruguayan Peso)

**Cryptocurrencies:**
- BTC (Bitcoin)
- ETH (Ethereum)
- USDT (Tether)
- USDC (USD Coin)
- DAI (Dai Stablecoin)
- BUSD (Binance USD)
- BNB (Binance Coin)
- ADA (Cardano)
- DOT (Polkadot)
- LINK (Chainlink)
- UNI (Uniswap)
- AAVE (Aave)

**Smart Currency Symbol Resolution:**
- Supports generic currency symbols like "$", "€", "£", "¥", "₱"
- Automatically resolves symbols based on account context
- Priority system: USD > ARS > others for "$" symbol
- Example: "$400 from AstroPay" resolves to USD if account has USD balance

### 🏦 Account Management

**Account Types:**
- **Bank** - Traditional bank accounts (Galicia, BBVA, etc.)
- **Wallet** - Digital wallets (AstroPay, MercadoPago, etc.)
- **Cash** - Physical cash holdings
- **Other** - Custom account types

**Multi-Currency Account Support:**
- Each account can hold multiple currencies simultaneously
- Example: AstroPay account with both USD $1,500 and ARS $45,000
- Automatic account creation when mentioned in transactions
- Intelligent account name normalization and fuzzy matching

### 📊 Query and Reporting System

**Balance Queries:**
- View all account balances
- Check specific account balances
- Multi-currency display format

**Transaction Queries:**
- Expense tracking by date ranges
- Income analysis
- Transaction history with filters
- Largest transaction identification

**Date Range Support:**
- Natural language date parsing
- "today", "yesterday", "last week", "this month"
- Specific date formats (DD/MM/YYYY)
- Custom date ranges

**Monthly Reports:**
- Comprehensive monthly financial summaries
- Total income and expenses
- Net savings calculation
- Largest transaction highlighting
- Current balance overview

### 🔄 Exchange Rate Integration

**Automatic Rate Fetching:**
- Real-time exchange rates from multiple providers
- CoinGecko integration for cryptocurrency rates
- Specialized Argentine peso (ARS) sources:
  - Blue dollar rate (dolarapi.com)
  - Official rate
  - MEP (Mercado Electrónico de Pagos) rate

**Exchange Rate Features:**
- Automatic currency conversion when needed
- Historical rate storage
- Retry mechanism with exponential backoff
- Fallback to cached rates when APIs are unavailable

### ⏳ Pending Transaction System

**Smart Transaction Queuing:**
- Transactions queue automatically when exchange rates are unavailable
- Automatic retry every 2 hours
- Error tracking and retry count management
- User notification of pending status

### 🤖 Telegram Bot Commands

**Available Commands:**
- `/start` - Welcome message and bot introduction
- `/help` - Comprehensive help and usage examples
- `/balance` - Show all account balances
- `/balance [account]` - Show specific account balance
- `/report [YYYY-MM]` - Generate monthly report

**Interactive Features:**
- Transaction confirmation with inline keyboards
- ✅ Confirm / ❌ Cancel buttons
- Real-time typing indicators
- Message length handling for long responses

## 🧠 AI-Powered Features

### 📝 Intelligent Parsing

**Natural Language Understanding:**
- Context-aware transaction parsing
- Account name extraction and normalization
- Amount parsing with support for:
  - K/M suffixes (1K = 1,000, 1M = 1,000,000)
  - Spanish number formats ("426 mil" = 426,000)
  - Comma-separated thousands
  - Currency symbols and codes

**Smart Description Generation:**
- Automatic transaction descriptions
- Context preservation from user input
- Meaningful categorization

### 🔍 Advanced Query Processing

**Flexible Date Parsing:**
- "últimos 7 días" / "last 7 days"
- "esta semana" / "this week"
- "el mes pasado" / "last month"
- Specific months: "agosto 2024" / "August 2024"

**Query Types:**
- Balance inquiries
- Expense summaries
- Income tracking
- Savings calculations
- Transaction lists
- Largest purchase identification
- Monthly reports
- Account overviews

## 🔍 Monitoring and Analytics

### 💰 OpenAI API Usage Tracking

**Real-time Cost Monitoring:**
- Automatic token usage tracking for every message
- Detailed breakdown of input/output tokens per API call
- Estimated cost calculation based on current GPT-4o-mini pricing
- Individual operation tracking (transaction extraction vs query extraction)
- Total usage summary per message

**Usage Logging Format:**
```
💰 Transaction intent extraction - Tokens: In=1613, Out=79, Total=1692 | Cost≈$0.000289
🎯 Message processing (1 API calls) TOTAL - Tokens: In=1613, Out=79, Total=1692 | Cost≈$0.000289
```

**Cost Transparency:**
- No hidden API costs - every token is tracked and logged
- Helps monitor and optimize system usage
- Typical cost per message: $0.0003 - $0.0005 USD
- Console logging for real-time monitoring

## 🛡️ Data Management

### 💾 Database Features

**User Management:**
- Automatic user registration from Telegram
- User preference storage (language, etc.)
- Multi-user support with data isolation

**Transaction Storage:**
- Comprehensive transaction logging
- Timestamp tracking
- Currency conversion history
- Exchange rate preservation
- Description and metadata storage

**Account Balance Tracking:**
- Real-time balance updates
- Multi-currency balance support
- Balance history maintenance
- Automatic balance calculations

### 🔒 Error Handling & Resilience

**Robust Error Management:**
- API failure handling with retries
- Database transaction rollback on errors
- User-friendly error messages in appropriate language
- Graceful degradation when services are unavailable

**Data Integrity:**
- Database constraints for data consistency
- Balance validation (non-negative constraints)
- Transaction amount validation
- Exchange rate validation

## 🎨 User Experience Features

### 💬 Conversational Interface

**Natural Interaction:**
- No need to learn specific command syntax
- Supports conversational flow
- Context-aware responses
- Friendly error messages and suggestions

**Rich Formatting:**
- Emoji icons for different transaction types
- Bold text for important information
- Structured reports with clear sections
- Currency formatting with thousands separators

### 🔄 Real-Time Processing

**Immediate Feedback:**
- Instant transaction parsing and confirmation
- Real-time balance updates
- Live exchange rate fetching
- Immediate query responses

**Status Indicators:**
- Typing indicators during processing
- Transaction confirmation status
- Pending transaction notifications
- Success/error status messages

---

## 🚀 Usage Examples

### Recording Transactions
```
"Recibí 6000 USD en mi cuenta de Deel el día 31/08/2025"
"I spent 400k ARS from my Galicia account"
"Transferí 1000 USD a mi cuenta de ahorros"
"Gasté $400 de mercadopago" (automatically resolves currency)
```

### Asking Questions
```
"¿Cuánto tengo en mi cuenta Deel?"
"How much did I spend last week?"
"What was my largest purchase in August?"
"Show all my transactions from the last 7 days"
"Generate my monthly report for September 2024"
```

### Balance Checking
```
/balance
/balance AstroPay
"Show me all my account balances"
"¿Cuánto tengo en efectivo?"
```

This comprehensive feature set makes the Personal Finance AI Agent a powerful tool for managing personal finances across multiple currencies and accounts, all through simple natural language conversation.