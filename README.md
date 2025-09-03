# Personal Finance AI Agent

A production-ready AI-powered financial tracking agent that works via Telegram chat. Built with LangChain, OpenAI, PostgreSQL, and Python 3.11+.

## Features

### 🤖 Natural Language Processing
- Record income, expenses, transfers, and currency conversions using natural language
- Automatic account creation when mentioned
- Smart parsing of amounts, dates, and transaction details

### 💰 Multi-Currency Support
- Track balances across multiple currencies (USD, ARS, USDT, BTC, etc.)
- Real-time exchange rate fetching from multiple sources
- Automatic currency conversion calculations

### 📊 Comprehensive Tracking
- Income and expense tracking
- Inter-account transfers with fee handling
- Currency conversions with exchange rate logging
- Monthly reports and analytics

### 💬 Telegram Interface
- Simple commands: `/balance`, `/report`, `/help`
- Natural language queries and transactions
- Real-time balance updates
- Formatted responses with emojis

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd finance-agent
   cp .env.example .env
   ```

2. **Configure environment**:
   Edit `.env` with your credentials:
   ```bash
   OPENAI_API_KEY=sk-your-openai-key
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   ```

3. **Start with Docker (Recommended)**:
   ```bash
   ./scripts/start.sh
   ```
   
   **Or manually:**
   ```bash
   docker build -t finance-agent .
   docker-compose up -d postgres
   docker-compose run --rm app alembic upgrade head
   docker-compose up app
   ```

4. **Or run locally** (requires Python 3.11+ and PostgreSQL):
   ```bash
   make install
   make dev
   alembic upgrade head
   python -m src.app
   ```

## Usage Examples

### Recording Transactions
```
💰 Income:
"I received 6k USD salary via Deel"
"Got paid 2500 USD freelance work"

💸 Expenses:
"I spent 400k ARS from my Galicia account"
"Bought groceries for 150 USD cash"

🔄 Transfers:
"I transferred 1K USD to Astropay, received 992 USD"
"Moved 5000 ARS from Galicia to Mercado Pago"

💱 Conversions:
"I converted 10 USDT to ARS at 1350 per USDT"
"Swapped 50 USDT for ARS in Belo"
```

### Querying Information
```
📊 Balances:
"What's my balance in Galicia?"
"Show all my accounts and balances"

📈 Analytics:
"How much did I spend in August?"
"What was my largest purchase last month?"
"Show my expenses between Sept 1 and 7"

📋 Reports:
"/report" - Current month report
"/report 2024-08" - Specific month report
```

## Architecture

### Components
- **LangChain Agent**: Natural language processing and intent recognition
- **DB Tool**: Transaction and balance management
- **FX Tool**: Real-time exchange rate fetching
- **Telegram Bot**: User interface via aiogram
- **PostgreSQL**: Persistent data storage

### Database Schema
- `accounts`: Account information (name, type)
- `account_balances`: Multi-currency balances per account
- `transactions`: Complete transaction history
- `exchange_rates`: Historical exchange rate data

### Exchange Rate Sources
- **CoinGecko**: Crypto and stablecoin rates
- **DolarApi**: USD/ARS rates (official, blue, MEP)
- **Pluggable providers**: Easy to add new sources

## Development

### Commands
```bash
make install    # Install dependencies
make dev        # Install dev dependencies
make test       # Run tests
make lint       # Run linting
make format     # Format code
make typecheck  # Run type checking
```

### Project Structure
```
src/
├── agent/          # LangChain agent and tools
│   ├── tools/      # DB and FX tools
│   ├── prompts/    # System prompts
│   └── schemas.py  # Pydantic models
├── db/             # Database layer
│   ├── models.py   # SQLAlchemy models
│   ├── crud.py     # Database operations
│   └── migrations/ # Alembic migrations
├── integrations/   # External service integrations
│   └── fx/         # Exchange rate providers
├── telegram/       # Telegram bot
└── utils/          # Utility functions

tests/              # Comprehensive test suite
```

### Running Tests
```bash
# All tests
pytest

# Specific test categories
pytest tests/test_parsing.py    # Natural language parsing
pytest tests/test_db_tool.py    # Database operations
pytest tests/test_fx_tool.py    # Exchange rate fetching
pytest tests/test_flows.py      # End-to-end flows
```

## Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Required |
| `POSTGRES_HOST` | PostgreSQL host | localhost |
| `POSTGRES_PORT` | PostgreSQL port | 5432 |
| `POSTGRES_DB` | Database name | finance |
| `POSTGRES_USER` | Database user | finance |
| `POSTGRES_PASSWORD` | Database password | finance |
| `FX_PRIMARY` | Primary FX provider | coingecko |
| `ARS_SOURCE` | ARS rate source | blue |

### Database Setup
The application uses Alembic for database migrations:
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Deployment

### Docker Production
```bash
# Build and deploy
docker-compose up -d

# View logs
docker-compose logs -f app

# Scale if needed
docker-compose up -d --scale app=2
```

### Health Checks
- Database connectivity
- OpenAI API availability
- Telegram bot webhook status
- Exchange rate provider health

## Troubleshooting

### Common Issues

**1. "Field defined on a base class was overridden" (Pydantic error)**
- This has been fixed in the current version. Make sure you're using the latest code.

**2. "ValidationError: Field required" (Missing API keys)**
- Ensure your `.env` file has valid `OPENAI_API_KEY` and `TELEGRAM_BOT_TOKEN`
- Copy from `.env.example`: `cp .env.example .env`

**3. Docker build fails**
- Ensure Docker is running: `docker --version`
- Try rebuilding: `docker build --no-cache -t finance-agent .`

**4. Database connection issues**
- Wait for PostgreSQL to be ready: `docker-compose logs postgres`
- Run migrations manually: `docker-compose run --rm app alembic upgrade head`

**5. Bot not responding on Telegram**
- Check bot token is correct in `.env`
- Verify bot is running: `docker-compose logs app`
- Test bot with `/start` command

### Debugging Commands
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs app
docker-compose logs postgres

# Test imports
docker run --rm -e OPENAI_API_KEY=sk-test -e TELEGRAM_BOT_TOKEN=123:test finance-agent python -c "from src.app import main; print('OK')"

# Connect to database
docker-compose exec postgres psql -U finance -d finance

# Run health check
python health_check.py
```

## Features Roadmap

### Phase 1 (MVP) ✅
- Natural language transaction processing
- Multi-currency account balances
- Real-time exchange rates
- Telegram bot interface
- Basic reporting

### Phase 2 (Future)
- [ ] Expense categorization
- [ ] Budget tracking and alerts
- [ ] Investment portfolio tracking
- [ ] Web dashboard
- [ ] Multi-user support
- [ ] AI financial advisor
- [ ] Export to Excel/CSV
- [ ] Recurring transaction templates

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Run quality checks: `make lint && make typecheck && make test`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push branch: `git push origin feature/amazing-feature`
7. Open Pull Request

## License

MIT License - see LICENSE file for details.

## Support

- 🐛 Report bugs: [GitHub Issues](https://github.com/user/finance-agent/issues)
- 💬 Get help: [Telegram Support](https://t.me/finance_agent_support)
- 📚 Documentation: [Wiki](https://github.com/user/finance-agent/wiki)

---

**Built with ❤️ using LangChain, OpenAI, and Python**