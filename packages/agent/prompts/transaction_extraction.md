# Transaction Extraction Prompt

Analyze this message in Spanish or English and determine if it describes a financial transaction.
If it does, extract the structured information. If not, return null.

Message: "{message}"

## Transaction Types
- **income**: received money (recibí, cobré, ingreso, got paid, salary, freelance)
- **expense**: spent money (gasté, pagué, compré, spent, bought, from/desde indicates source account)
- **transfer**: moved money between accounts (transferí, envié, moved, de...a indicates from...to, cambié when moving between accounts)
- **conversion**: exchanged currencies ONLY when explicitly converting currencies at exchange rates

## Important Rules

**IMPORTANT**: "efectivo" and "cash" are ACCOUNT NAMES, not currencies!  
**IMPORTANT**: "$" is a valid currency symbol that will be resolved to the account's primary currency (USD or ARS)

### Currency Handling
- "$" can be used and will be resolved based on the account's primary currency
- "USD", "ARS", "USDT", "USDC" are valid currency codes
- Other symbols like "€", "£", "¥" are also valid and will be resolved
- Generic terms like "pesos", "dollars" will be resolved to account's primary currency
- IMPORTANT: Prefer specific currency codes (ARS, USD) over generic terms (pesos, dollars) when possible

### Spanish Patterns
- "de mi cuenta de [account]" = account_from: [account] (for expenses)
- "desde [account]" = account_from: [account]
- "de [account] a [account]" = transfer from first to second
- "en mi cuenta de [account]" = account_to for income
- "en [place/store]" = merchant/description (NOT account)
- "pagué X de [concept]" = expense with description: [concept]

### CASH/EFECTIVO Patterns
- For EXPENSES: "en efectivo" = account_from: "Efectivo" (paid WITH cash)
- For EXPENSES: "in cash" = account_from: "Cash" (paid WITH cash)
- For TRANSFERS: "a [amount] en efectivo" = account_to: "Efectivo" (transfer TO cash)
- For INCOME: "recibí en efectivo" = account_to: "Efectivo" (received TO cash)

**Critical**: When someone SPENDS "en efectivo", the cash is the SOURCE (account_from)!

### Account Name Recognition
- "efectivo" → account name "Efectivo"
- "cash" → account name "Cash"
- "AstroPay", "Deel", "Galicia" → keep as-is
- Physical cash is an account, not a currency!

**IMPORTANT**:
- "en supermercado" = merchant/description, NOT account
- "de mi cuenta de AstroPay" = account_from: "AstroPay"
- Places like "supermercado", "restaurant", "tienda" are merchants/descriptions, not accounts
- Only "de mi cuenta de X" or "desde X" indicate accounts for expenses

### Date Patterns
Spanish date patterns:
- "31/08/2025" = August 31, 2025
- "el día 31/08" = August 31, 2025 (use current year 2025, unless that would be a future date, then use 2024)

**IMPORTANT DATE LOGIC FOR DD/MM FORMAT**:
- Always use year 2025 for DD/MM dates UNLESS the date would be in the future
- If DD/MM would create a future date, use year 2024 instead
- Today is October 2025, so "05/08" = "05/08/2025" (August 5th, 2025 - past date)
- Today is October 2025, so "25/11" = "25/11/2024" (November 25th would be future, so use 2024)

### Number Patterns
Spanish number patterns:
- "426 mil" = 426000 (mil = thousand)
- "1.5 millones" = 1500000

## JSON Response Format

Return a JSON object with the transaction details or null if this is not a transaction.
Use this exact format:
```json
{
    "intent": "income|expense|transfer|conversion",
    "amount": number,
    "currency": "string",
    "account_from": "string or null",
    "account_to": "string or null",
    "amount_to": number or null,
    "currency_to": "string or null",
    "exchange_rate": number or null,
    "date": "ISO date string or null",
    "merchant": "string or null",
    "description": "string or null"
}
```

## Merchant vs Description Extraction (CRITICAL FOR EXPENSES)

**FOR EXPENSES, separate merchant and description**:
- **merchant**: The PLACE/STORE where money was spent (e.g., "supermercado Becerra", "almacén Yoli", "Starbucks", "Carrefour")
- **description**: WHAT was purchased/reason for expense (e.g., "comida", "pasta frola", "café", "alquiler")

### Extraction Patterns:

**Pattern 1**: "en [ITEM] en [PLACE]" or "en [ITEM] from [PLACE]"
- "Gasté en comida en supermercado Becerra" → merchant: "supermercado Becerra", description: "comida"
- "Spent on groceries at Walmart" → merchant: "Walmart", description: "groceries"

**Pattern 2**: "en [PLACE] en [ITEM]" or "at [PLACE] for [ITEM]"
- "Gasté en supermercado Becerra en comida" → merchant: "supermercado Becerra", description: "comida"
- "Spent at Starbucks for coffee" → merchant: "Starbucks", description: "coffee"

**Pattern 3**: "[ITEM] from/en [PLACE]"
- "Compré pasta frola en almacén Yoli" → merchant: "almacén Yoli", description: "pasta frola"
- "Bought coffee from Starbucks" → merchant: "Starbucks", description: "coffee"

**Pattern 4**: Only place mentioned (no specific item)
- "Gasté en supermercado" → merchant: "supermercado", description: null
- "Spent at Walmart" → merchant: "Walmart", description: null

**Pattern 5**: Only item mentioned (no specific place)
- "Gasté en comida" → merchant: null, description: "comida"
- "Spent on groceries" → merchant: null, description: "groceries"

### Key Indicators:

**Merchants** (places/stores):
- supermercado, almacén, tienda, restaurant, café, bar
- Proper names: Carrefour, Becerra, Yoli, Starbucks, McDonald's
- Descriptive places: "supermercado de la esquina", "almacén Yoli"

**Descriptions** (items/concepts):
- comida, pasta frola, café, alquiler, gasolina
- General categories: groceries, food, rent, gas, coffee
- Services: flete, delivery, subscription

**IMPORTANT**: If both are present, extract BOTH separately. Don't combine them!

## Examples

### Expense Examples with Merchant Extraction:

1. "Gasté 10 mil ars en comida en supermercado Becerra desde mi cuenta de astropay"
   ```json
   {
     "intent": "expense",
     "amount": 10000,
     "currency": "ARS",
     "account_from": "astropay",
     "merchant": "supermercado Becerra",
     "description": "comida",
     "date": null
   }
   ```

2. "Gasté desde la cuenta de astropay 20 mil ARS en almacén Yoli en pasta frola"
   ```json
   {
     "intent": "expense",
     "amount": 20000,
     "currency": "ARS",
     "account_from": "astropay",
     "merchant": "almacén Yoli",
     "description": "pasta frola",
     "date": null
   }
   ```

3. "Spent 50 USD at Starbucks for coffee from my cash account"
   ```json
   {
     "intent": "expense",
     "amount": 50,
     "currency": "USD",
     "account_from": "cash",
     "merchant": "Starbucks",
     "description": "coffee",
     "date": null
   }
   ```

4. "Gasté 400 ARS en comida" (no specific merchant)
   ```json
   {
     "intent": "expense",
     "amount": 400,
     "currency": "ARS",
     "merchant": null,
     "description": "comida",
     "date": null
   }
   ```

5. "Pagué 50000 ARS de alquiler desde Galicia"
   ```json
   {
     "intent": "expense",
     "amount": 50000,
     "currency": "ARS",
     "account_from": "Galicia",
     "merchant": null,
     "description": "alquiler",
     "date": null
   }
   ```

### Other Transaction Examples:

6. "Recibí 6000 USD en mi cuenta de Deel"
   ```json
   {
     "intent": "income",
     "amount": 6000,
     "currency": "USD",
     "account_to": "Deel",
     "description": "ingreso",
     "date": null
   }
   ```

7. "Transferí 1000 USD de Deel a AstroPay"
   ```json
   {
     "intent": "transfer",
     "amount": 1000,
     "currency": "USD",
     "account_from": "Deel",
     "account_to": "AstroPay",
     "description": "transferencia",
     "date": null
   }
   ```
