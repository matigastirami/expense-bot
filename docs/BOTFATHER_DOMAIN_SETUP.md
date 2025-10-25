# Fix: "Bot domain invalid" Error

## The Problem

When clicking the Telegram login button, you see: **"Bot domain invalid"**

This happens because Telegram needs to know which domains are allowed to use your bot for authentication.

## The Solution: Configure Domain in BotFather

### Step 1: Open BotFather in Telegram

1. Open Telegram app (mobile or desktop)
2. Search for `@BotFather`
3. Start a chat with BotFather

### Step 2: Set Domain

Send these commands to BotFather:

```
/setdomain
```

BotFather will reply with a list of your bots. Select your bot (`@mati_claude_expense_bot`).

### Step 3: Enter Domain

**For Local Development:**

```
localhost
```

Just type `localhost` and press enter.

**For Production (later):**

```
yourdomain.com
```

Replace with your actual domain.

### Step 4: Confirm

BotFather will confirm:
```
Success! Domain updated.
```

### Step 5: Test Again

1. Refresh your browser at http://localhost:3000/login
2. Click the Telegram login button
3. It should now open Telegram asking for permission ✅

## Full Example Conversation with BotFather

```
You: /setdomain

BotFather: Choose a bot to set the domain.

You: @mati_claude_expense_bot

BotFather: Send me the domain name. The domain must be valid and available 
via HTTPS. You can also send me an IP address like 1.2.3.4 or "localhost" 
for local testing.

You: localhost

BotFather: Success! Domain updated.
```

## Important Notes

### 🔧 Development (localhost)

- Use domain: `localhost`
- Works for: http://localhost:3000
- No HTTPS required for localhost

### 🚀 Production

- Use domain: `yourdomain.com`
- Must have HTTPS (SSL certificate)
- Don't include `http://` or `https://` prefix
- Just the domain name

### 🌐 Multiple Domains

You can only set ONE domain per bot. If you need multiple:

**Option 1: Use subdomain for all**
```
app.yourdomain.com
```

**Option 2: Create separate bots**
- One bot for development
- One bot for production

## Troubleshooting

### "Domain invalid" still appears

**Try these:**

1. **Wait a moment** - BotFather changes can take 1-2 minutes to propagate

2. **Clear browser cache** or try incognito mode

3. **Verify domain is set:**
   ```
   /setdomain
   Select your bot
   BotFather will show current domain
   ```

4. **Check exact domain match:**
   - If you're on `http://localhost:3000` → use `localhost`
   - If you're on `http://127.0.0.1:3000` → use `127.0.0.1`
   - Domain must EXACTLY match

### "HTTPS required" error (Production)

Your production domain MUST have SSL certificate:

1. **Get free SSL:** Use Let's Encrypt
2. **Use reverse proxy:** nginx, Caddy, or Traefik
3. **Or use platform SSL:** Vercel, Netlify, Cloudflare Pages

### Bot doesn't appear in list

Make sure you're chatting with the correct `@BotFather` (official Telegram bot, has verified badge).

## Alternative: Using ngrok for Development

If you want to test with a real domain in development:

### Step 1: Install ngrok
```bash
# macOS
brew install ngrok

# Or download from ngrok.com
```

### Step 2: Start ngrok tunnel
```bash
ngrok http 3000
```

### Step 3: Use ngrok domain
```
Forwarding: https://abc123.ngrok.io -> http://localhost:3000
```

Use `abc123.ngrok.io` as your domain in BotFather.

### Step 4: Update environment variable
```env
VITE_API_BASE_URL=https://abc123.ngrok.io
```

### Step 5: Rebuild
```bash
docker-compose build web
docker-compose up
```

**Note:** ngrok free tier gives you a random domain that changes each restart.

## Production Deployment Checklist

When deploying to production:

- [ ] Domain has valid SSL certificate (HTTPS)
- [ ] Set domain in BotFather: `/setdomain`
- [ ] Update `VITE_API_BASE_URL` to production URL
- [ ] Update `API_BASE_URL` in environment
- [ ] Rebuild containers with production config
- [ ] Test Telegram login on production domain

## Summary

The **"Bot domain invalid"** error happens because:
1. Telegram Login Widget requires domain authorization
2. This prevents unauthorized sites from using your bot
3. You must explicitly allow domains in BotFather

**Quick fix:**
```
1. Open @BotFather in Telegram
2. /setdomain
3. Select your bot
4. Send: localhost
5. Done!
```

After this, the Telegram login button will work! 🎉

## Need More Help?

- Check if domain is set: Send `/setdomain` to BotFather
- See all bot settings: Send `/mybots` to BotFather  
- Official docs: https://core.telegram.org/widgets/login

---

**Next Step:** Once domain is configured, test the login at http://localhost:3000/login
