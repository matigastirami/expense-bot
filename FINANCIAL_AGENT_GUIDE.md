# Financial Analysis Agent - Implementation Guide

## Overview

The Financial Analysis Agent is a comprehensive bilingual (English/Spanish) expense tracking and analysis system that implements the requirements specified in the system prompt. It provides:

- **Expense Classification**: Automatic categorization with learning capabilities
- **Budget Management**: Percentage-based budget tracking and adherence monitoring  
- **Financial Analysis**: Period-based analysis with insights and recommendations
- **User Memory**: Learning system that remembers user corrections and preferences
- **Bilingual Support**: Full English and Spanish language support
- **Period Resolution**: Natural language date parsing ("last month", "últimos 7 días")

## Architecture

### Core Components

1. **FinancialAnalysisAgent** (`src/agent/financial_agent.py`)
   - Main agent class implementing the system prompt requirements
   - Handles expense classification, period parsing, analysis generation
   - Manages user memory and learning

2. **Telegram Integration** (`src/telegram/financial_agent_handlers.py`)
   - Bot handlers for commands like `/analyze`, `/expense`, `/budget`
   - Callback handlers for interactive confirmations
   - Message formatting for bilingual responses

3. **Data Models** 
   - `ExpenseConfirmation`: For new expense confirmation flow
   - `AnalysisReport`: For financial analysis results
   - `BudgetUpdate`: For budget management responses

## Key Features Implementation

### 1. Expense Classification

The agent automatically categorizes expenses using predefined categories:

**Default Categories:**
- **Fixed**: rent, utilities, insurance, subscriptions
- **Groceries**: food, supermercado, comida
- **Transport**: taxi, uber, gas, transporte
- **Health**: medical, salud, pharmacy
- **Education**: school, course, educacion
- **Childcare**: guarderia, daycare, nanny
- **Dining/Delivery**: restaurant, delivery, cafe
- **Leisure/Entertainment**: movies, games, entretenimiento
- **Shopping**: clothes, electronics, compras
- **Travel**: hotel, flight, viaje
- **Taxes/Fees**: impuesto, government fees
- **Debt/Loans**: credit, prestamo, deuda
- **Gifts/Donations**: regalo, charity, donacion
- **Business**: office, work, negocio
- **Misc**: other miscellaneous expenses

**Bucket Classification:**
- **Fixed**: Fixed, Taxes/Fees, Debt/Loans
- **Variable Necessary**: Groceries, Transport, Health, Education, Childcare, Business
- **Discretionary**: Dining/Delivery, Leisure/Entertainment, Shopping, Travel, Gifts/Donations, Misc

### 2. Period Resolution

Natural language date parsing supports:

**Spanish:**
- "hoy", "ayer"
- "últimos X días", "esta semana", "la semana pasada"
- "este mes", "el mes pasado", "el mes anterior"
- "este año", "el año pasado"
- Month names: "enero", "febrero", etc.
- Date ranges: "desde 2025-08-10 hasta 2025-08-31"

**English:**
- "today", "yesterday"
- "last X days", "this week", "last week"
- "this month", "last month"
- "this year", "last year"
- Month names: "january", "february", etc.
- Date ranges: "from 2025-08-10 to 2025-08-31"

### 3. User Memory and Learning

The agent maintains per-user memory for:
- **merchant_to_category**: Remembers category corrections
- **merchant_necessity_override**: Remembers necessity flag corrections
- **budget_targets**: User's budget percentage targets

When users correct classifications, the agent updates memory and never repeats the same mistake.

### 4. Budget Management

Users can set percentage-based budgets:
- Budget validation ensures totals sum to 100%
- Automatic normalization if percentages don't sum correctly
- Budget adherence tracking with variance alerts
- Recommendations when spending exceeds targets

## API Usage Examples

### 1. Expense Confirmation

```python
# Process a new expense
confirmation = await financial_agent.process_expense_confirmation(
    amount=50.0,
    currency="USD",
    date=None,  # Uses today
    merchant="Starbucks",
    note="morning coffee",
    user_id=123
)

# Returns ExpenseConfirmation with:
# - Detected category (e.g., "Dining/Delivery")
# - Necessity flag (False for Starbucks coffee)
# - Confidence score
# - Alternative categories
# - UI confirmation text in detected language
```

### 2. Financial Analysis

```python
# Analyze any period using natural language
analysis = await financial_agent.analyze_period("last month", user_id=123)

# Returns AnalysisReport with:
# - Parsed period dates
# - Spending totals by category and bucket
# - Budget adherence percentages
# - Insights (outliers, trends, recurring merchants)
# - Actionable recommendations
# - Human-readable summary in user's language
```

### 3. Budget Management

```python
# Update user's budget targets
budget_result = await financial_agent.update_budget(
    "50% fixed, 30% necessary, 20% discretionary", 
    user_id=123
)

# Returns BudgetUpdate with:
# - Normalized percentages
# - Validation notes
# - Confirmation in user's language
```

### 4. User Memory Updates

```python
# Update memory when user corrects classification
await financial_agent.update_user_memory(
    user_id=123,
    merchant="Starbucks",
    category="Groceries",  # User correction
    is_necessary=True      # User marked as necessary
)

# Future expenses at Starbucks will use these preferences
```

## Telegram Bot Integration

### Commands

- `/analyze [period]` - Generate financial analysis
- `/expense [amount] [currency] [merchant] [description]` - Quick expense entry
- `/budget [targets]` - Set budget percentages

### Interactive Features

- **Confirmation Flow**: All expenses require user confirmation before saving
- **Category Alternatives**: Quick buttons to change detected category
- **Necessity Toggle**: Button to toggle necessity flag
- **Learning Integration**: Corrections automatically update user memory

### Bilingual Support

The bot automatically detects language from user input and responds appropriately:

**Spanish Example:**
```
User: "Gasté 50 USD en Starbucks"
Bot: "Detecté Dining/Delivery (no necesario). ¿Cambiar?"
```

**English Example:**
```
User: "Spent 50 USD at Starbucks"
Bot: "I detected Dining/Delivery (not necessary). Change it?"
```

## Output Schemas

### ExpenseConfirmation
```json
{
  "type": "expense_confirmation",
  "resolved_language": "en|es",
  "expense": {
    "amount": 50.0,
    "currency": "USD",
    "date": "2025-09-19",
    "merchant": "Starbucks",
    "note": "morning coffee"
  },
  "classification": {
    "category": "Dining/Delivery",
    "is_necessary": false,
    "confidence": 0.8,
    "alternatives": [
      {"category": "Groceries", "reason": "Contains food-related keywords"},
      {"category": "Shopping", "reason": "Common alternative to Dining/Delivery"}
    ]
  },
  "memory_updates_if_user_confirms_changes": {
    "merchant_to_category": null,
    "merchant_necessity_override": false
  },
  "ui_confirmation_text": "I detected Dining/Delivery (not necessary). Change it?"
}
```

### AnalysisReport
```json
{
  "type": "analysis_report",
  "resolved_language": "en",
  "period": {"start": "2025-08-01", "end": "2025-09-01"},
  "totals": {
    "currency": "USD",
    "total_expenses": 2500.0,
    "by_bucket": {
      "fixed": 1250.0,
      "variable_necessary": 750.0,
      "discretionary": 500.0
    },
    "by_category": {
      "Groceries": 400.0,
      "Transport": 350.0,
      "Dining/Delivery": 300.0
    }
  },
  "budget_targets_pct": {
    "fixed": 50.0,
    "variable_necessary": 30.0,
    "discretionary": 20.0
  },
  "budget_actual_pct": {
    "fixed": 50.0,
    "variable_necessary": 30.0,
    "discretionary": 20.0
  },
  "signals": {
    "outliers": [],
    "small_leaks": [],
    "recurring_merchants": [],
    "possible_duplicates": [],
    "trends_vs_prev_period": {"total_delta_pct": 5.2}
  },
  "recommendations": [
    {
      "title": "Reduce discretionary spending",
      "rationale": "You're spending 5% more than planned on discretionary items",
      "est_monthly_savings": 125.0,
      "est_annual_savings": 1500.0,
      "category": "discretionary",
      "action_steps": [
        "Review recent transactions in this category",
        "Set spending alerts",
        "Find cheaper alternatives"
      ]
    }
  ],
  "human_summary": "• Total expenses: $2,500\n• Fixed: $1,250 (50%)\n• Variable necessary: $750 (30%)\n• Discretionary: $500 (20%)\n• Budget adherence: On target"
}
```

## Testing

### Basic Usage Test

```python
# Test expense classification
async def test_expense_classification():
    agent = FinancialAnalysisAgent()
    
    # Test English expense
    confirmation = await agent.process_expense_confirmation(
        amount=100, currency="USD", date=None, 
        merchant="Whole Foods", note="weekly groceries", user_id=1
    )
    assert confirmation.classification["category"] == "Groceries"
    assert confirmation.classification["is_necessary"] == True
    
    # Test Spanish expense  
    confirmation = await agent.process_expense_confirmation(
        amount=50, currency="ARS", date=None,
        merchant="Cine", note="película con amigos", user_id=1
    )
    assert confirmation.classification["category"] == "Leisure/Entertainment"
    assert confirmation.classification["is_necessary"] == False
```

### Period Resolution Test

```python
async def test_period_resolution():
    agent = FinancialAnalysisAgent()
    
    # Test Spanish period parsing
    start, end = agent._parse_period("el mes pasado", "es")
    expected_start = datetime(2025, 8, 1)  # Previous month start
    expected_end = datetime(2025, 9, 1)    # Current month start
    assert start == expected_start
    assert end == expected_end
    
    # Test English period parsing
    start, end = agent._parse_period("last 7 days", "en")
    # Should return last 7 days including today
```

### Memory Learning Test

```python
async def test_memory_learning():
    agent = FinancialAnalysisAgent()
    user_id = 1
    
    # Initial classification
    confirmation1 = await agent.process_expense_confirmation(
        amount=50, currency="USD", date=None,
        merchant="Starbucks", note="coffee", user_id=user_id
    )
    assert confirmation1.classification["category"] == "Dining/Delivery"
    
    # User corrects to Groceries and marks as necessary
    await agent.update_user_memory(user_id, "Starbucks", "Groceries", True)
    
    # Second expense at same merchant should use learned preferences
    confirmation2 = await agent.process_expense_confirmation(
        amount=30, currency="USD", date=None,
        merchant="Starbucks", note="breakfast", user_id=user_id
    )
    assert confirmation2.classification["category"] == "Groceries"
    assert confirmation2.classification["is_necessary"] == True
```

## Integration with Existing System

The Financial Analysis Agent is designed to work alongside the existing expense tracker:

1. **Database Integration**: Uses existing TransactionCRUD and AccountCRUD for data access
2. **User Management**: Integrates with existing UserCRUD for user handling
3. **Telegram Bot**: Adds new handlers without disrupting existing functionality
4. **Language Detection**: Uses existing language utilities
5. **Currency Support**: Compatible with existing currency and exchange rate systems

## Deployment

1. **Install Dependencies**: All required packages are already in pyproject.toml
2. **Database Migration**: No schema changes required - uses existing tables
3. **Bot Registration**: Import the integration module to register handlers
4. **Command Updates**: Update bot commands to include new functionality

```python
# In bot.py, add:
import src.telegram.bot_integration  # Registers handlers automatically
```

The Financial Analysis Agent provides a complete implementation of the system prompt requirements while maintaining compatibility with the existing codebase.