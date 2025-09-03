# Few-Shot Examples for Financial Agent

## Transaction Processing Examples

### Income
**User:** "I received 6k USD salary for August via Deel"
**Parsed Intent:**
```json
{
  "intent": "income",
  "amount": 6000,
  "currency": "USD",
  "account_to": "Deel",
  "description": "salary for August"
}
```

### Expense
**User:** "I spent 400k ARS from my Galicia/Mercado Pago account"
**Parsed Intent:**
```json
{
  "intent": "expense",
  "amount": 400000,
  "currency": "ARS",
  "account_from": "Galicia",
  "description": "expense"
}
```

### Transfer
**User:** "I transferred 1K USD to my Astropay account and received 992 USD"
**Parsed Intent:**
```json
{
  "intent": "transfer",
  "amount": 1000,
  "currency": "USD",
  "amount_to": 992,
  "currency_to": "USD",
  "account_to": "Astropay",
  "description": "transfer with fees"
}
```

### Conversion
**User:** "I converted 10 USDT to ARS in Belo at 1350 ARS per USDT"
**Parsed Intent:**
```json
{
  "intent": "conversion",
  "amount": 10,
  "currency": "USDT",
  "amount_to": 13500,
  "currency_to": "ARS",
  "exchange_rate": 1350,
  "account_from": "Belo",
  "account_to": "Belo",
  "description": "USDT to ARS conversion"
}
```

## Query Examples

### Balance Query
**User:** "What's my balance in Galicia?"
**Parsed Intent:**
```json
{
  "intent": "balance",
  "account_name": "Galicia"
}
```

### Expense Query
**User:** "How much did I spend on Aug 15?"
**Parsed Intent:**
```json
{
  "intent": "expenses",
  "start_date": "2024-08-15T00:00:00",
  "end_date": "2024-08-15T23:59:59"
}
```

### Period Query
**User:** "Show my expenses between Sept 1 and Sept 7"
**Parsed Intent:**
```json
{
  "intent": "expenses",
  "start_date": "2024-09-01T00:00:00",
  "end_date": "2024-09-07T23:59:59"
}
```

### All Accounts Query
**User:** "Show all my accounts and balances"
**Parsed Intent:**
```json
{
  "intent": "all_accounts"
}
```

### Largest Purchase Query
**User:** "What was my largest purchase in August?"
**Parsed Intent:**
```json
{
  "intent": "largest_purchase",
  "start_date": "2024-08-01T00:00:00",
  "end_date": "2024-08-31T23:59:59"
}
```

## Response Format Examples

### Balance Response
```
* Deel – USD 6,000
* Astropay – USD 992
* Galicia – ARS 400,000
* Belo – USDT 50, ARS 13,500
* Cash – ARS 50,000
```

### Transaction Confirmation
"✅ Conversion registered: -10 USDT → +13,500 ARS in Belo account"

### Query Response
"Your total expenses for August 15th: ARS 45,000 across 3 transactions"