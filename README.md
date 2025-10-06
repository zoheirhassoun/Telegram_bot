# Telegram Bot with Google Sheets Integration

This bot allows you to ask questions and retrieve data from Google Sheets through Telegram.

## Features

- 🤖 Interactive Telegram bot interface
- 📊 Google Sheets data retrieval and search
- 🔍 Natural language query processing
- 📈 Data summary and statistics
- 🔄 Real-time data refresh

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token you receive

### 3. Set up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API
4. Go to "Credentials" and create "OAuth 2.0 Client IDs"
5. Download the credentials file as `credentials.json`
6. Place it in your project directory

### 4. Prepare Your Google Sheet

1. Create a Google Sheet with your data
2. Make sure the first row contains column headers
3. Share the sheet with the email address from your Google Cloud project
4. Copy the Sheet ID from the URL (the long string between `/d/` and `/edit`)

### 5. Configure Environment Variables

1. Copy `env_example.txt` to `.env`
2. Fill in your actual values:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather
   - `GOOGLE_SHEET_ID`: Your Google Sheet ID

### 6. Run the Bot

```bash
python telegram_bot.py
```

## Usage

### Commands

- `/start` - Welcome message and instructions
- `/help` - Show help information
- `/summary` - Get overview of your data
- `/search <query>` - Search for specific information
- `/refresh` - Reload data from Google Sheets

### Examples

- "Find all products with price > 100"
- "Show customers from New York"
- "What are the latest orders?"
- "Search for John Smith"

## File Structure

```
telegram_bot/
├── telegram_bot.py          # Main bot code
├── requirements.txt         # Python dependencies
├── env_example.txt         # Environment variables template
├── credentials.json        # Google API credentials (you need to add this)
├── token.pickle           # Google auth token (auto-generated)
└── README.md              # This file
```

## Troubleshooting

### Common Issues

1. **"No data found"**: Check if your Google Sheet ID is correct and the sheet is shared
2. **Authentication errors**: Delete `token.pickle` and run again to re-authenticate
3. **Bot not responding**: Verify your bot token is correct

### Google Sheets Format

Make sure your Google Sheet:
- Has headers in the first row
- Contains data in subsequent rows
- Is shared with your Google Cloud project email

## Security Notes

- Never commit your `.env` file or `credentials.json` to version control
- Keep your bot token secure
- Regularly rotate your API credentials

## Support

If you encounter issues:
1. Check the console logs for error messages
2. Verify all environment variables are set correctly
3. Ensure your Google Sheet is properly configured
4. Make sure all dependencies are installed
