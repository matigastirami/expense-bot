# Monorepo Restructure Plan

This document outlines the plan to convert the expense tracker into a monorepo with a Flask REST API and React frontend.

## Proposed Folder Structure

```
expense-tracker-claude/
├── packages/
│   ├── api/                          # Flask REST API
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── app.py               # Flask app entry point
│   │   │   ├── config.py            # API-specific config
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── expenses.py      # GET, POST, PUT, DELETE /api/expenses
│   │   │   │   ├── reports.py       # GET /api/reports
│   │   │   │   └── health.py        # Health check endpoint
│   │   │   ├── middleware/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cors.py
│   │   │   │   └── error_handler.py
│   │   │   ├── validators/
│   │   │   │   ├── __init__.py
│   │   │   │   └── expense_validator.py
│   │   │   └── serializers/
│   │   │       ├── __init__.py
│   │   │       └── expense_serializer.py
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── web/                          # React + Vite frontend
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── main.tsx
│   │   │   ├── App.tsx
│   │   │   ├── pages/
│   │   │   │   ├── Dashboard/
│   │   │   │   │   ├── Dashboard.tsx
│   │   │   │   │   ├── Dashboard.module.css
│   │   │   │   │   ├── components/
│   │   │   │   │   │   ├── ExpenseChart.tsx
│   │   │   │   │   │   ├── CategoryBreakdown.tsx
│   │   │   │   │   │   ├── MonthlyTrends.tsx
│   │   │   │   │   │   └── DateRangeFilter.tsx
│   │   │   │   │   └── hooks/
│   │   │   │   │       └── useDashboardData.ts
│   │   │   │   └── Expenses/
│   │   │   │       ├── ExpenseList.tsx
│   │   │   │       ├── ExpenseForm.tsx
│   │   │   │       ├── ExpenseDetail.tsx
│   │   │   │       └── components/
│   │   │   │           ├── ExpenseTable.tsx
│   │   │   │           ├── ExpenseFilters.tsx
│   │   │   │           └── Pagination.tsx
│   │   │   ├── components/          # Shared components
│   │   │   │   ├── Layout/
│   │   │   │   ├── Navigation/
│   │   │   │   └── common/
│   │   │   ├── services/
│   │   │   │   └── api.ts           # Axios client
│   │   │   ├── hooks/
│   │   │   ├── types/
│   │   │   │   └── expense.ts
│   │   │   └── utils/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   └── telegram-bot/                 # Existing Telegram bot (refactored)
│       ├── src/
│       │   ├── __init__.py
│       │   ├── app.py               # Bot entry point
│       │   ├── telegram/            # From existing src/telegram/
│       │   └── config.py
│       ├── tests/
│       ├── requirements.txt
│       ├── Dockerfile
│       └── README.md
│
├── shared/                           # Shared code across packages
│   ├── database/                     # Shared DB layer
│   │   ├── __init__.py
│   │   ├── models.py                # From src/db/models.py
│   │   ├── crud.py                  # From src/db/crud.py
│   │   ├── base.py
│   │   ├── migrations/              # Alembic migrations
│   │   └── seed.py
│   ├── schemas/                      # Shared Pydantic schemas
│   │   ├── __init__.py
│   │   ├── transaction.py
│   │   └── account.py
│   ├── utils/                        # From src/utils/
│   │   ├── __init__.py
│   │   ├── date_utils.py
│   │   ├── money.py
│   │   └── language.py
│   ├── integrations/                 # From src/integrations/
│   │   └── fx/
│   ├── services/                     # Shared services
│   │   ├── __init__.py
│   │   └── audio_transcription.py
│   └── agent/                        # LangChain agent (if needed by API)
│       └── ...
│
├── infrastructure/
│   ├── docker/
│   │   └── docker-compose.yml       # Orchestrate all services
│   ├── terraform/                    # From existing terraform/
│   └── scripts/                      # From existing scripts/
│
├── docs/                             # Consolidated docs
├── alembic.ini                       # Database migrations
├── .gitignore
├── README.md                         # Main monorepo README
└── package.json                      # Root package.json for workspace
```

## Implementation Strategy

### Phase 1: Restructure Existing Code

1. **Create monorepo structure** with `packages/`, `shared/`, and `infrastructure/` directories
2. **Move shared database code** (`src/db/`) to `shared/database/`
3. **Move shared utilities** (`src/utils/`, `src/integrations/`) to `shared/`
4. **Refactor Telegram bot** into `packages/telegram-bot/`
5. **Update imports** across all moved modules

### Phase 2: Build Flask REST API (`packages/api/`)

#### API Endpoints Design

**Expenses Endpoints:**
```
GET    /api/v1/expenses              # List expenses (paginated, filterable)
POST   /api/v1/expenses              # Create new expense
GET    /api/v1/expenses/{id}         # Get single expense
PUT    /api/v1/expenses/{id}         # Update expense
DELETE /api/v1/expenses/{id}         # Delete expense
```

**Query Parameters for GET /api/v1/expenses:**
- `page` (default: 1)
- `per_page` (default: 20, max: 100)
- `description` (partial search)
- `from_date` (ISO format)
- `to_date` (ISO format)
- `account_id`
- `currency`
- `min_amount`
- `max_amount`

**Reports Endpoints:**
```
GET    /api/v1/reports/dashboard     # Dashboard JSON data
  Query params: period (YYYY-MM, YYYY, or from_date/to_date)
```

#### Dashboard JSON Response Structure

```json
{
  "period": {
    "from": "2024-10-01",
    "to": "2024-10-31",
    "label": "October 2024"
  },
  "summary": {
    "total_income": 5000.00,
    "total_expenses": 3200.50,
    "net_balance": 1799.50,
    "currency": "USD"
  },
  "categories": [
    { "name": "Food", "amount": 800.00, "percentage": 25 },
    { "name": "Transport", "amount": 400.00, "percentage": 12.5 }
  ],
  "expenses_by_day": [
    { "date": "2024-10-01", "amount": 150.00 },
    { "date": "2024-10-02", "amount": 200.00 }
  ],
  "top_expenses": [
    { "id": 123, "description": "Rent", "amount": 1200.00, "date": "2024-10-01" }
  ],
  "accounts_breakdown": [
    { "account": "Galicia", "total": 1500.00, "currency": "ARS" }
  ]
}
```

#### Key API Features

- **Pagination**: Using Flask-SQLAlchemy's `paginate()`
- **Validation**: Custom validators for max 100 items per page
- **Search**: Partial match on description using SQL `ILIKE`
- **Error handling**: Standardized JSON error responses
- **CORS**: Flask-CORS for frontend communication
- **Health check**: `/health` endpoint for monitoring

### Phase 3: Build React Frontend (`packages/web/`)

#### Pages & Features

**1. Dashboard Page (`/`)**

- Default view: Current month
- **Date Filter Component:**
  - Quick filters: "This Month", "Last Month", "This Year"
  - Custom range picker: From/To dates
  - Month picker: YYYY-MM
  - Year picker: YYYY
- **Visualizations:**
  - Total income vs expenses (cards)
  - Category breakdown (pie chart using Recharts/Chart.js)
  - Expense trends over time (line chart)
  - Top 5 expenses (list)
  - Account balances (multi-currency aware)

**2. Expenses Page (`/expenses`)**

- **ExpenseTable**: Paginated table with sorting
- **Filters**: By date, description (search), account, category
- **CRUD Actions:**
  - Create: Modal/drawer form
  - Edit: Inline or modal edit
  - Delete: Confirmation dialog
- **Pagination**: Client-side or server-side (recommend server-side)

#### Tech Stack for Frontend

- **React 18** + **TypeScript**
- **Vite** for build tooling
- **React Router** for routing
- **TanStack Query** (React Query) for data fetching & caching
- **Axios** for HTTP client
- **Recharts** or **Chart.js** for visualizations
- **Tailwind CSS** or **Material-UI** for styling
- **React Hook Form** + **Zod** for form validation
- **date-fns** for date manipulation

### Phase 4: Infrastructure & Docker

**Docker Compose (`infrastructure/docker/docker-compose.yml`):**

```yaml
services:
  postgres:
    # Existing PostgreSQL setup
    
  api:
    build: ../../packages/api
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://...
      
  web:
    build: ../../packages/web
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:5000
      
  telegram-bot:
    build: ../../packages/telegram-bot
    environment:
      - DATABASE_URL=postgresql://...
```

### Phase 5: Shared Database Access

**Strategy:**

- All three services (`api`, `telegram-bot`, and potentially `web` SSR) share the same PostgreSQL database
- Use `shared/database/` as a Python package installed in both `api` and `telegram-bot`
- Install via local path in `requirements.txt`:
  ```
  -e ../../shared/database
  ```
- Alembic migrations run from root or shared package
- Both API and bot can write to `transactions` table
- React app only reads via API (no direct DB access)

## Key Decisions & Recommendations

### 1. Transaction Data Model

- Keep existing `Transaction` model
- Add optional `category` and `necessity` fields if not present
- Expenses are transactions with `type='expense'`

### 2. API Pagination Strategy

- Default: 20 items per page
- Max: 100 items per page (validated)
- Return metadata: `{ data: [...], total: 500, page: 1, per_page: 20, total_pages: 25 }`

### 3. Frontend State Management

- Use **TanStack Query** for server state (API data)
- Use **React Context** or **Zustand** for UI state (filters, modals)
- Cache dashboard data with 5-minute stale time

### 4. Deployment

- **Development**: Docker Compose with all services
- **Production**: Keep existing Terraform setup, add API and web services
- Consider reverse proxy (Nginx) in front of all services

### 5. Testing Strategy

- **API**: pytest with Flask test client
- **Frontend**: Vitest + React Testing Library
- **E2E**: Consider Playwright for critical flows
- **Shared**: pytest for database/utilities

## Migration Steps Summary

1. Create folder structure (packages/, shared/, infrastructure/)
2. Extract shared code (database, utils, integrations)
3. Refactor Telegram bot into its own package
4. Build Flask API with expenses CRUD + reports endpoints
5. Build React app with Dashboard + Expenses CRUD
6. Set up Docker Compose for local development
7. Update CI/CD for monorepo structure
8. Update documentation

## Benefits of This Structure

- **Separation of concerns**: Each package has clear responsibility
- **Code reuse**: Shared database/utils used by all services
- **Independent deployment**: Can deploy API, web, bot separately
- **Scalability**: Easy to add more packages (mobile app, admin panel)
- **Developer experience**: Clear boundaries, easy to navigate
- **Technology flexibility**: Can use different frameworks per package

## Next Steps

Before starting implementation, consider:

1. Which UI library to use (Tailwind CSS vs Material-UI)
2. Authentication strategy (if needed for multi-user support)
3. Whether to add categories/tags to transactions now or later
4. Deployment strategy for production environment
