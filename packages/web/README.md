# Expense Tracker Web Frontend

A modern React-based web application for managing personal finances, built with Vite, TypeScript, and Tailwind CSS.

## Features

- **Authentication**: Email/password login and signup with JWT authentication
- **Telegram Integration**: Support for linking existing Telegram bot accounts
- **Transactions Management**: Create, read, update, and delete transactions with filters
- **Accounts Management**: Full CRUD operations for financial accounts
- **Categories Management**: Organize income and expenses by categories
- **Merchants Management**: Track and manage merchants/vendors
- **Analytics Dashboard**: Visual insights with charts and key metrics
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS

## Tech Stack

- **Frontend Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form with Zod validation
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios

## Getting Started

### Prerequisites

- Node.js 18 or higher
- npm or yarn

### Installation

1. Install dependencies:
```bash
cd packages/web
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Configure environment variables:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_TELEGRAM_BOT_NAME=your_bot_name
```

### Development

Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

Create a production build:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Docker Deployment

### Using Docker Compose (Recommended)

The web frontend is included in the main docker-compose configuration:

```bash
# Development
docker-compose up web

# Production
docker-compose -f docker-compose.prod.yml up web
```

### Building Standalone Docker Image

```bash
cd packages/web
docker build -t expense-tracker-web .
docker run -p 3000:80 expense-tracker-web
```

## Project Structure

```
packages/web/
├── src/
│   ├── api/              # API client and endpoint definitions
│   │   ├── client.ts     # Axios instance with interceptors
│   │   ├── auth.ts       # Authentication endpoints
│   │   ├── transactions.ts
│   │   ├── accounts.ts
│   │   ├── categories.ts
│   │   ├── merchants.ts
│   │   └── analytics.ts
│   ├── components/       # React components
│   │   ├── auth/         # Authentication components
│   │   ├── common/       # Reusable UI components
│   │   ├── layout/       # Layout components
│   │   ├── transactions/ # Transaction-specific components
│   │   └── ...
│   ├── hooks/            # Custom React hooks
│   │   └── useAuth.tsx   # Authentication hook and context
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   ├── SignUpPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── TransactionsPage.tsx
│   │   ├── AccountsPage.tsx
│   │   ├── CategoriesPage.tsx
│   │   └── MerchantsPage.tsx
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions and config
│   ├── App.tsx           # Main application component
│   ├── main.tsx          # Application entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── Dockerfile            # Multi-stage Docker build
├── nginx.conf            # Nginx configuration for production
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API Integration

The web app communicates with the REST API at the configured `VITE_API_BASE_URL`. All API calls include JWT authentication tokens automatically via Axios interceptors.

### Authentication Flow

1. User logs in with email/password
2. API returns JWT token and user info
3. Token is stored in localStorage
4. All subsequent requests include the token in Authorization header
5. On 401 responses, user is redirected to login

### Telegram Account Linking

Users who already have transactions via the Telegram bot can link their accounts:

1. Sign up or log in with email/password
2. Use the `/link-telegram` API endpoint to associate telegram_user_id
3. All existing Telegram transactions become accessible via web interface

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_TELEGRAM_BOT_NAME` | Telegram bot username for login widget | - |

## Features Details

### Transactions

- Filter by date range, account, and transaction type
- Support for income, expenses, transfers, and currency conversions
- Bulk operations and CSV export (coming soon)
- Real-time balance updates

### Dashboard

- Total income and expenses for selected period
- Net savings calculation
- Largest transactions highlights
- Visual charts with Recharts

### Accounts

- Multiple account types: bank, wallet, cash, other
- Balance tracking with multi-currency support
- Transaction history per account

### Categories & Merchants

- Organize transactions by categories
- Track spending by merchant
- Custom categories for income and expenses

## Production Considerations

### Nginx Configuration

The included `nginx.conf` provides:
- Gzip compression for better performance
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Static asset caching
- SPA routing support (HTML5 pushState)
- Health check endpoint at `/health`

### Environment Configuration

For production deployment, ensure:
1. Set `VITE_API_BASE_URL` to your production API URL
2. Configure proper CORS settings in the API
3. Use HTTPS for secure communication
4. Set appropriate JWT expiration times

## Troubleshooting

### API Connection Issues

If you see CORS errors:
1. Verify `VITE_API_BASE_URL` is correct
2. Ensure Flask-CORS is configured in the API
3. Check that the API is running and accessible

### Build Failures

If the build fails:
1. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf node_modules/.vite`
3. Ensure Node.js version is 18+

## Contributing

When adding new features:
1. Create new API endpoints in `src/api/`
2. Add corresponding React Query hooks
3. Build UI components in `src/components/`
4. Create pages in `src/pages/`
5. Update routing in `App.tsx`

## License

Part of the Expense Tracker project.
