import os
import logging
from telegram import Update, Voice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pandas as pd
from dotenv import load_dotenv
import json
import pickle
import speech_recognition as sr
import pyttsx3
import tempfile
import requests
from io import BytesIO

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBotWithSheetsAndVoice:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        self.credentials = None
        self.service = None
        
        # Initialize speech recognition and text-to-speech
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        
        # Configure TTS voice
        voices = self.tts_engine.getProperty('voices')
        if voices:
            self.tts_engine.setProperty('voice', voices[0].id)  # Use first available voice
        self.tts_engine.setProperty('rate', 150)  # Speed of speech
        
    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets API"""
        try:
            creds = None
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists('credentials.json'):
                        raise FileNotFoundError("credentials.json not found. Please download it from Google Cloud Console.")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.scopes)
                    creds = flow.run_local_server(port=8080, open_browser=True)
                
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            self.credentials = creds
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Google Sheets authentication successful")
        except Exception as e:
            logger.error(f"Google Sheets authentication failed: {e}")
            raise
    
    def get_sheet_data(self, sheet_name='Sheet1', range_name=None):
        """Retrieve data from Google Sheets"""
        try:
            if not self.service:
                self.authenticate_google_sheets()
            
            if range_name is None:
                range_name = f'{sheet_name}!A:Z'
            
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning('No data found in the sheet')
                return pd.DataFrame()
            
            df = pd.DataFrame(values[1:], columns=values[0])
            logger.info(f"Retrieved {len(df)} rows from Google Sheets")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving data from Google Sheets: {e}")
            return pd.DataFrame()
    
    def search_data(self, query, df):
        """Search for data based on query"""
        if df.empty:
            return "No data available"
        
        df_str = df.astype(str)
        mask = df_str.apply(lambda x: x.str.contains(query, case=False, na=False)).any(axis=1)
        results = df[mask]
        
        if results.empty:
            return f"No results found for '{query}'"
        
        if len(results) == 1:
            return self.format_single_result(results.iloc[0])
        else:
            return self.format_multiple_results(results)
    
    def format_single_result(self, row):
        """Format a single result row"""
        result = "Found Result:\n\n"
        for col, value in row.items():
            if pd.notna(value) and str(value).strip():
                result += f"{col}: {value}\n"
        return result
    
    def format_multiple_results(self, results):
        """Format multiple results"""
        result = f"Found {len(results)} results:\n\n"
        
        for i, (_, row) in enumerate(results.head(5).iterrows()):
            result += f"Result {i+1}:\n"
            for col, value in row.items():
                if pd.notna(value) and str(value).strip():
                    result += f"  {col}: {value}\n"
            result += "\n"
        
        if len(results) > 5:
            result += f"... and {len(results) - 5} more results"
        
        return result
    
    def get_summary_stats(self, df):
        """Get summary statistics of the data"""
        if df.empty:
            return "No data available for summary"
        
        summary = "Data Summary:\n\n"
        summary += f"Total Records: {len(df)}\n"
        summary += f"Total Columns: {len(df.columns)}\n\n"
        
        summary += "Columns:\n"
        for col in df.columns:
            non_null_count = df[col].notna().sum()
            summary += f"  • {col} ({non_null_count} values)\n"
        
        return summary
    
    def speech_to_text(self, voice_file_path):
        """Convert speech to text"""
        try:
            with sr.AudioFile(voice_file_path) as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Speech to text: {text}")
            return text
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand the audio."
        except sr.RequestError as e:
            return f"Speech recognition service error: {e}"
        except Exception as e:
            logger.error(f"Speech to text error: {e}")
            return "Sorry, there was an error processing your voice message."
    
    def text_to_speech(self, text):
        """Convert text to speech and return audio file path"""
        try:
            # Create temporary file for audio
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.close()
            
            # Save speech to file
            self.tts_engine.save_to_file(text, temp_file.name)
            self.tts_engine.runAndWait()
            
            return temp_file.name
        except Exception as e:
            logger.error(f"Text to speech error: {e}")
            return None

# Initialize bot
bot = TelegramBotWithSheetsAndVoice()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = """
🎤 Welcome to the Voice-Enabled Google Sheets Bot!

I can help you retrieve and search data from your Google Sheets using both text and voice!

Available Commands:
/start - Show this welcome message
/help - Show help information
/summary - Get data summary
/search <query> - Search for specific data
/refresh - Refresh data from Google Sheets

Voice Features:
🎤 Send me a voice message asking about your data
🔊 I'll respond with both text and voice
📊 Ask questions like "What are my tasks?" or "Find customers from New York"

How to use:
• Type your questions normally
• Send voice messages for hands-free interaction
• I'll search your Google Sheets and respond with voice!

Example: Send a voice message saying "Find all products with price greater than 100"
    """
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
🎤 Voice-Enabled Bot Help Guide

Commands:
• /start - Welcome message
• /help - This help message
• /summary - Get overview of your data
• /search <query> - Search for specific information
• /refresh - Reload data from Google Sheets

Voice Features:
🎤 Send voice messages asking about your data
🔊 Get voice responses back
📊 Natural language voice queries

Voice Examples:
• "What are my tasks?"
• "Find customers from New York"
• "Show me products with high prices"
• "What's my data summary?"

Tips:
• Speak clearly for best recognition
• You can ask questions in natural language
• Search is case-insensitive
• I'll show you the most relevant results
    """
    await update.message.reply_text(help_text)

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get summary of the data"""
    try:
        df = bot.get_sheet_data()
        summary_text = bot.get_summary_stats(df)
        await update.message.reply_text(summary_text)
        
        # Also send voice response
        voice_file = bot.text_to_speech(summary_text)
        if voice_file:
            await update.message.reply_voice(voice=open(voice_file, 'rb'))
            os.unlink(voice_file)  # Clean up temp file
            
    except Exception as e:
        error_msg = f"Error getting summary: {str(e)}"
        await update.message.reply_text(error_msg)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command"""
    try:
        query = ' '.join(context.args) if context.args else ""
        if not query:
            await update.message.reply_text("Please provide a search query. Example: /search products")
            return
        
        df = bot.get_sheet_data()
        results = bot.search_data(query, df)
        await update.message.reply_text(results)
        
        # Also send voice response
        voice_file = bot.text_to_speech(results)
        if voice_file:
            await update.message.reply_voice(voice=open(voice_file, 'rb'))
            os.unlink(voice_file)  # Clean up temp file
            
    except Exception as e:
        error_msg = f"Error searching: {str(e)}"
        await update.message.reply_text(error_msg)

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Refresh data from Google Sheets"""
    try:
        if os.path.exists('token.pickle'):
            os.remove('token.pickle')
        
        bot.authenticate_google_sheets()
        df = bot.get_sheet_data()
        
        success_msg = f"Data refreshed! Retrieved {len(df)} records from Google Sheets."
        await update.message.reply_text(success_msg)
        
        # Also send voice response
        voice_file = bot.text_to_speech(success_msg)
        if voice_file:
            await update.message.reply_voice(voice=open(voice_file, 'rb'))
            os.unlink(voice_file)  # Clean up temp file
            
    except Exception as e:
        error_msg = f"Error refreshing data: {str(e)}"
        await update.message.reply_text(error_msg)

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    try:
        voice = update.message.voice
        logger.info(f"Received voice message from user")
        
        # Download voice file
        voice_file = await context.bot.get_file(voice.file_id)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg')
        await voice_file.download_to_drive(temp_file.name)
        
        # Convert speech to text
        user_query = bot.speech_to_text(temp_file.name)
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        if user_query.startswith("Sorry"):
            await update.message.reply_text(user_query)
            return
        
        # Process the query
        await update.message.reply_text(f"🎤 I heard: {user_query}")
        
        # Get data from Google Sheets
        df = bot.get_sheet_data()
        
        if df.empty:
            response = "No data available. Please check your Google Sheets configuration."
        else:
            response = bot.search_data(user_query, df)
        
        # Send text response
        await update.message.reply_text(response)
        
        # Send voice response
        voice_file = bot.text_to_speech(response)
        if voice_file:
            await update.message.reply_voice(voice=open(voice_file, 'rb'))
            os.unlink(voice_file)  # Clean up temp file
        
    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        await update.message.reply_text(f"Sorry, I encountered an error processing your voice message: {str(e)}")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    try:
        user_message = update.message.text
        logger.info(f"User query: {user_message}")
        
        # Get data from Google Sheets
        df = bot.get_sheet_data()
        
        if df.empty:
            await update.message.reply_text("No data available. Please check your Google Sheets configuration.")
            return
        
        # Search for the query
        results = bot.search_data(user_message, df)
        await update.message.reply_text(results)
        
        # Also send voice response
        voice_file = bot.text_to_speech(results)
        if voice_file:
            await update.message.reply_voice(voice=open(voice_file, 'rb'))
            os.unlink(voice_file)  # Clean up temp file
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(f"Sorry, I encountered an error: {str(e)}")

def main():
    """Start the bot."""
    try:
        if not bot.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            print("Error: TELEGRAM_BOT_TOKEN not found!")
            print("Please create a .env file with your bot token from BotFather")
            return
        
        if not bot.spreadsheet_id:
            logger.error("GOOGLE_SHEET_ID not found in environment variables")
            print("Error: GOOGLE_SHEET_ID not found!")
            print("Please add your Google Sheet ID to the .env file")
            return
        
        # Create the Application
        application = Application.builder().token(bot.bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("summary", summary))
        application.add_handler(CommandHandler("search", search_command))
        application.add_handler(CommandHandler("refresh", refresh))
        
        # Add voice message handler
        application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
        
        # Add text message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        
        # Start the bot
        logger.info("Starting Voice-Enabled Telegram bot...")
        print("🎤 Starting Voice-Enabled Telegram bot...")
        print("✅ Bot is running! Send /start to your bot to test it.")
        print("🎤 You can now send voice messages!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"Failed to start bot: {e}")
        print("Please check your configuration and try again.")

if __name__ == '__main__':
    main()
