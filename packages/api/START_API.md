# How to Start the Expense Tracker API

## Quick Start

### From Project Root (Recommended)

```bash
# Option 1: Use the shell script
./run_api.sh

# Option 2: Use Python directly
python packages/api/run.py
```

### From packages/api Directory

```bash
cd packages/api
python run.py
```

## What You Should See

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
WARNING: This is a development server. Do not use it in production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

## Testing the API

### 1. Health Check

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "healthy": true,
  "timestamp": "2024-01-15T12:00:00"
}
```

### 2. Sign Up

```bash
curl -X POST http://localhost:5000/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test12345"
  }'
```

Expected response:
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

### 3. Run Full Test Suite

```bash
# From project root
cd packages/api
python test_api.py
```

## Environment Variables

The API uses these optional environment variables:

- `DATABASE_URL` - PostgreSQL connection string (default: from libs/db/config.py)
- `JWT_SECRET_KEY` - Secret key for JWT tokens (default: "your-secret-key-change-this")
- `ARS_SOURCE` - ARS exchange rate source (default: "blue")
- `OPENAI_API_KEY` - OpenAI API key for audio transcription (optional)

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'libs'`:

✅ **Solution**: Always run from project root or use the provided scripts

```bash
# Wrong (from packages/api)
cd packages/api/src
python app.py  # ❌ This won't work

# Correct (from project root)
python packages/api/run.py  # ✅ This works
./run_api.sh  # ✅ This also works
```

### Database Connection Errors

If you see database connection errors:

1. Check PostgreSQL is running:
   ```bash
   psql -l
   ```

2. Check DATABASE_URL environment variable:
   ```bash
   echo $DATABASE_URL
   ```

3. Run migrations:
   ```bash
   cd libs/db
   alembic upgrade head
   ```

### Port Already in Use

If port 5000 is already in use:

```bash
# Find and kill the process using port 5000
lsof -ti:5000 | xargs kill -9

# Or change the port in run.py (line: app.run(..., port=5000))
```

### OpenAI API Key Warning

The warning about OpenAI API key is **optional**:

```
⚠️ No OpenAI API key found. Audio transcription will not work.
```

This only affects audio transcription features. The API works fine without it.

To remove the warning, set the environment variable:
```bash
export OPENAI_API_KEY="your-key-here"
```

## API Documentation

- **Full API docs**: `packages/api/README.md`
- **cURL examples**: `packages/api/CURL_EXAMPLES.md`
- **Quick start**: `QUICKSTART.md`

## Next Steps

After the API is running:

1. **Test endpoints**: Use `packages/api/CURL_EXAMPLES.md`
2. **Create accounts**: `POST /accounts`
3. **Add transactions**: `POST /transactions`
4. **View analytics**: `GET /analytics`

## Development Mode

The API runs in debug mode by default, which provides:

- ✅ Auto-reload on code changes
- ✅ Detailed error messages
- ✅ Request logging

**Important**: Do not use debug mode in production!

For production, use a WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 'packages.api.src.app:app'
```

## Stop the API

Press `Ctrl+C` in the terminal where the API is running.
