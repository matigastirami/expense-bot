# All Ways to Run the Expense Tracker API

## 🚀 Quick Start (Choose Any Method)

### Method 1: Using Make (Recommended)
```bash
make dev-api
```

### Method 2: Using Python Script
```bash
# From project root
python packages/api/run.py
```

### Method 3: Using Shell Script
```bash
# From project root
./run_api.sh
```

### Method 4: Manual Flask Run
```bash
# From project root
PYTHONPATH=. FLASK_APP=packages/api/src/app.py flask run --debug
```

---

## 📋 All Makefile Commands

### Start API
```bash
make dev-api
```

### Run Migrations
```bash
# Apply all migrations
make migrate

# Create new migration
make migration-create msg="your migration description"
```

### Run API Tests
```bash
make test-api-endpoints
```

### Run All Tests
```bash
make test
```

---

## ✅ What to Expect When Starting

```
============================================================
🚀 Starting Expense Tracker API
============================================================
📍 Server: http://localhost:5000
📍 Health check: http://localhost:5000/health
📍 Project root: /Users/your-username/expense-tracker-claude
============================================================

Press Ctrl+C to stop

 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

---

## 🧪 Quick Test After Starting

### Health Check
```bash
curl http://localhost:5000/health
```

**Expected Response:**
```json
{
  "healthy": true,
  "timestamp": "2024-01-15T12:00:00"
}
```

### Create User
```bash
curl -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test12345"
  }'
```

**Expected Response:**
```json
{
  "message": "User created successfully",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "test@example.com"
  }
}
```

### Run Full Test Suite
```bash
make test-api-endpoints

# Or manually
cd packages/api
python test_api.py
```

---

## 🔧 Environment Variables

The API uses these environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | From libs/db/config.py | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | "your-secret-key-change-this" | Yes (change in production) |
| `ARS_SOURCE` | ARS exchange rate source | "blue" | No |
| `OPENAI_API_KEY` | OpenAI API key for audio | None | No |

### Set Environment Variables

```bash
# Option 1: Export in shell
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/expense_tracker"
export JWT_SECRET_KEY="super-secret-key-for-production"

# Option 2: Create .env file
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://user:password@localhost/expense_tracker
JWT_SECRET_KEY=super-secret-key-for-production
ARS_SOURCE=blue
EOF

# Then run
make dev-api
```

---

## 🐳 Using Docker (Future)

```bash
# Start all services (API + Database)
make docker-up

# Stop all services
make docker-down
```

---

## 🛠️ Troubleshooting

### Port 5000 Already in Use

```bash
# Find process using port 5000
lsof -ti:5000

# Kill the process
lsof -ti:5000 | xargs kill -9

# Or change port in packages/api/run.py
# Change: app.run(..., port=5000)
# To:     app.run(..., port=8000)
```

### Import Errors

If you see `ModuleNotFoundError: No module named 'libs'`:

✅ **Always run from project root**
```bash
# Wrong
cd packages/api/src
python app.py  # ❌ Won't work

# Correct
make dev-api  # ✅ Works
python packages/api/run.py  # ✅ Works
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
psql -l

# Check database exists
psql -l | grep expense_tracker

# Create database if needed
createdb expense_tracker

# Run migrations
make migrate
```

### Migrations Not Found

```bash
# Wrong directory
cd libs/database  # ❌ Old location

# Correct directory
cd libs/db  # ✅ Correct location
alembic upgrade head
```

---

## 📚 Documentation Links

After starting the API, check out:

- **All cURL Examples**: `packages/api/CURL_EXAMPLES.md`
- **API Reference**: `packages/api/README.md`
- **Startup Guide**: `packages/api/START_API.md`
- **Quick Start**: `QUICKSTART.md`

---

## 🎯 Common Workflows

### 1. Start Development
```bash
# Terminal 1: Start API
make dev-api

# Terminal 2: Test endpoints
make test-api-endpoints
```

### 2. Make Database Changes
```bash
# Edit models in libs/db/models.py
# Then create migration
make migration-create msg="add new field to users"

# Apply migration
make migrate
```

### 3. Test Single Endpoint
```bash
# Start API
make dev-api

# In another terminal, test
curl http://localhost:5000/health
```

### 4. Production-like Testing
```bash
# Set production environment variables
export JWT_SECRET_KEY="production-secret-key"
export DATABASE_URL="postgresql+asyncpg://prod_user:prod_pass@prod_host/prod_db"

# Start API
make dev-api

# Run tests against production-like setup
make test-api-endpoints
```

---

## 🚀 Quick Reference

| Task | Command |
|------|---------|
| Start API | `make dev-api` |
| Test API | `make test-api-endpoints` |
| Migrate DB | `make migrate` |
| Create Migration | `make migration-create msg="description"` |
| Run All Tests | `make test` |
| Health Check | `curl http://localhost:5000/health` |

---

## 💡 Pro Tips

1. **Use Make**: It's the easiest way - `make dev-api`
2. **Check Logs**: API runs in debug mode, shows all requests
3. **Auto-reload**: Code changes auto-reload in debug mode
4. **Test First**: Run `make test-api-endpoints` to verify everything works
5. **Read Examples**: `CURL_EXAMPLES.md` has examples for every endpoint

---

## 🎉 You're Ready!

Choose any method above to start the API, then check out the documentation for examples:

```bash
# Start it
make dev-api

# Test it
curl http://localhost:5000/health

# Use it
cat packages/api/CURL_EXAMPLES.md
```

Happy coding! 🚀
