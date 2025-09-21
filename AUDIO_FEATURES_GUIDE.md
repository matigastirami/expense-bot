# 🎤 Audio Expense Entry - Complete Guide

## Overview

The Financial Analysis Agent now supports **voice message expense entry**! Users can simply send voice messages describing their expenses, and the bot will automatically transcribe and parse them into structured expense data.

## ✨ Features

- 🎤 **Voice Transcription**: Uses OpenAI Whisper API for accurate speech-to-text
- 🌍 **Bilingual Support**: Works in English and Spanish
- 💰 **Smart Parsing**: Automatically extracts amounts, currencies, merchants, and descriptions
- 🔄 **Same Workflow**: Uses the same confirmation flow as text-based expenses
- 🎯 **Intelligent Detection**: Recognizes various speaking patterns and formats

## 🚀 Quick Start

### 1. Setup OpenAI API Key

You need an OpenAI API key to enable voice transcription:

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

Or add it to your environment file:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### 2. Install Dependencies

The required dependencies are already in `pyproject.toml`:

```bash
pip install aiofiles aiohttp
```

### 3. Restart Your Bot

Restart your Telegram bot to load the new audio handlers:

```bash
# Stop your current bot process
# Then restart it
python -m src.app  # or however you start your bot
```

### 4. Start Using Voice Messages!

Send voice messages to your bot describing expenses. Examples:

**English:**
- "I spent 50 dollars at Starbucks for coffee"
- "Paid 25 USD for lunch at McDonald's"
- "5k USD for new laptop"

**Spanish:**
- "Gasté 500 pesos en el supermercado"
- "Pagué 1000 ARS en la farmacia para medicinas"
- "50k ARS en el shopping"

## 💡 How It Works

### Voice Message Flow

1. **User sends voice message** 📱➡️🎤
2. **Bot shows "Processing..."** ⏳
3. **Audio gets transcribed** 🎤➡️📝
4. **Text gets parsed for expense info** 📝➡️💰
5. **Bot shows confirmation with buttons** ✅❌
6. **User confirms or modifies** 👆
7. **Expense gets saved to database** 💾

### Transcription Process

```mermaid
graph LR
    A[Voice Message] --> B[Download Audio]
    B --> C[Send to Whisper API]
    C --> D[Get Transcription]
    D --> E[Parse Expense Data]
    E --> F[Show Confirmation]
```

### Parsing Intelligence

The system can understand various formats:

**Amount Formats:**
- `50 dollars`, `25 USD`, `$30`
- `500 pesos`, `1000 ARS`
- `80 euros`, `EUR 80`
- `5k USD` (thousands), `2.5k ARS`

**Merchant Detection:**
- "at Starbucks" → Merchant: "Starbucks"
- "en el supermercado" → Merchant: "El Supermercado"
- "from McDonald's" → Merchant: "McDonald's"

**Note Extraction:**
- "for coffee" → Note: "coffee"
- "para medicinas" → Note: "medicinas"
- Context from the full transcription

## 🎯 Supported Currencies

- **USD** - US Dollars (`dollars`, `bucks`, `$`, `USD`)
- **ARS** - Argentine Pesos (`pesos`, `peso`, `ARS`)
- **EUR** - Euros (`euros`, `EUR`)
- **BTC** - Bitcoin (`bitcoin`, `BTC`)
- **USDT** - Tether (`tether`, `USDT`)

## 📱 Usage Examples

### English Examples

| Voice Message | Parsed Result |
|---------------|---------------|
| "I spent 50 dollars at Starbucks for coffee" | $50 USD at Starbucks (coffee) |
| "Paid 25 USD for lunch at McDonald's" | $25 USD at McDonald's (lunch) |
| "Bought groceries for 150 dollars" | $150 USD (groceries) |
| "5k USD for new laptop" | $5,000 USD (new laptop) |

### Spanish Examples

| Voice Message | Parsed Result |
|---------------|---------------|
| "Gasté 500 pesos en el supermercado" | 500 ARS at El Supermercado |
| "Pagué 1000 ARS en la farmacia para medicinas" | 1,000 ARS at La Farmacia (medicinas) |
| "Compré café por 200 pesos" | 200 ARS (café) |
| "50k ARS en el shopping" | 50,000 ARS at El Shopping |

## 🔧 Technical Details

### Architecture

```
Voice Message
    ↓
Audio Transcription Service (OpenAI Whisper)
    ↓
Voice Expense Parser (Regex + NLP)
    ↓
Financial Analysis Agent (Classification)
    ↓
Telegram Confirmation Handler
    ↓
Database Storage
```

### Key Components

1. **AudioTranscriptionService** (`src/services/audio_transcription.py`)
   - Downloads voice messages from Telegram
   - Sends audio to OpenAI Whisper API
   - Returns transcribed text

2. **Voice Expense Parser** (`src/telegram/financial_agent_handlers.py`)
   - Parses transcription using regex patterns
   - Extracts amount, currency, merchant, and notes
   - Handles multilingual input

3. **Voice Message Handler** (`@financial_router.message(F.voice)`)
   - Processes incoming voice messages
   - Coordinates transcription and parsing
   - Shows confirmation UI

### Error Handling

The system gracefully handles various error scenarios:

- **No OpenAI API Key**: Shows helpful setup message
- **Transcription Failure**: Suggests speaking more clearly
- **Parse Failure**: Asks for specific expense details
- **API Errors**: Logs errors and shows user-friendly messages

## 🛠️ Configuration

### Environment Variables

```env
# Required for audio features
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Set language preference
DEFAULT_LANGUAGE=en  # or 'es' for Spanish
```

### OpenAI API Pricing

Voice transcription uses OpenAI's Whisper API:
- **Cost**: $0.006 per minute of audio
- **Languages**: 99+ languages supported
- **Quality**: High accuracy, especially for English and Spanish

### Performance Considerations

- **Voice Message Length**: Works best with messages under 2 minutes
- **Audio Quality**: Clear speech improves transcription accuracy
- **Background Noise**: Quiet environments work better
- **Internet Speed**: Faster upload means quicker processing

## 🔍 Troubleshooting

### Common Issues

**1. "Audio transcription not available" message**
```
Solution: Set OPENAI_API_KEY environment variable
```

**2. "Could not transcribe voice message"**
```
Possible causes:
- Poor audio quality
- Background noise
- Very quiet speech
- Unsupported audio format

Solutions:
- Speak more clearly
- Reduce background noise
- Try typing the expense instead
```

**3. "Couldn't find expense information"**
```
The transcription was successful but couldn't extract expense data.

Try including:
- Amount: "50 dollars", "25 USD"
- Location: "at Starbucks", "en el supermercado"
- Purpose: "for coffee", "para comida"
```

### Debug Mode

To see detailed logs, run your bot with debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- Transcription results
- Parsing attempts
- API call details

## 🎨 User Experience

### Confirmation Flow

After processing a voice message, users see:

```
🎤 Voice message: "I spent 50 dollars at Starbucks for coffee"

🔔 Expense Confirmation

Amount: 50 USD
Merchant: Starbucks
Description: coffee
Date: 2025-09-20

Category: Dining/Delivery (70%)
Necessity: not necessary

Confirm this transaction?

[✅ Confirm] [🏷️ Category] [🔄 Toggle Necessity] [❌ Cancel]
```

### Smart Features

- **Language Detection**: Automatically detects if user speaks English or Spanish
- **Category Classification**: Uses the same smart categorization as text expenses
- **Learning System**: Remembers user corrections for future expenses
- **Contextual Notes**: Extracts meaningful descriptions from natural speech

## 🚀 Advanced Usage

### Integration with Existing Features

Voice expenses work seamlessly with:

- **Financial Analysis** (`/analyze`) - Include voice expenses in reports
- **Budget Tracking** (`/budget`) - Voice expenses count toward budget limits
- **Expense Categories** - Same 15+ categories with learning
- **Multi-currency Support** - All supported currencies work

### API Integration

If you're building custom integrations:

```python
from src.services.audio_transcription import audio_service
from src.telegram.financial_agent_handlers import _parse_voice_expense

# Transcribe audio file
transcription = await audio_service.transcribe_voice_message(
    "path/to/audio.ogg",
    language="en"  # Optional language hint
)

# Parse expense data
expense_data = await _parse_voice_expense(transcription, user_id)
```

## 📊 Analytics & Insights

Voice expense entry provides additional analytics:

- **Transcription Accuracy**: Track successful vs failed transcriptions
- **User Preferences**: See if users prefer voice vs text entry
- **Language Distribution**: Monitor English vs Spanish usage
- **Error Patterns**: Identify common parsing failures

## 🔮 Future Enhancements

Potential improvements for voice expense entry:

- **Speaker Recognition**: Multiple users per account
- **Offline Mode**: Local speech recognition for privacy
- **Custom Vocabularies**: Learn user-specific merchant names
- **Batch Processing**: Handle multiple expenses in one voice message
- **Voice Commands**: "Show my balance", "Generate report"

## 📞 Support

If you encounter issues with voice expense entry:

1. **Check the logs** for detailed error messages
2. **Verify OpenAI API key** is set correctly
3. **Test with simple phrases** first
4. **Fall back to text entry** if voice isn't working

## 🎉 Conclusion

Voice expense entry makes financial tracking more convenient and natural. Users can simply speak their expenses while on the go, and the system intelligently processes and categorizes them.

The feature maintains all the powerful capabilities of the Financial Analysis Agent while adding the convenience of voice input - perfect for busy users who want to track expenses without typing!

---

*Last updated: September 2025*