import os
import re
import telebot
from io import StringIO
from flask import Flask

# Load your Telegram bot token from the environment variables
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    raise Exception('Bot token is not defined')
bot = telebot.TeleBot(API_TOKEN)

# Define regex patterns for locations
patterns = {
    "Onitsha": re.compile(r'Onitsha', re.IGNORECASE),
    "Aba": re.compile(r'Aba', re.IGNORECASE),
    "Ph": re.compile(r'Ph', re.IGNORECASE),
    "Abuja": re.compile(r'Abuja', re.IGNORECASE),
    "Kano": re.compile(r'Kano', re.IGNORECASE),
    "Igbariam": re.compile(r'Igbariam', re.IGNORECASE),
    "Warri": re.compile(r'Warri', re.IGNORECASE),
    "Owerri": re.compile(r'Owerri', re.IGNORECASE),
}

# Define the rates and costs based on location
location_details = {
    "Onitsha": {"fare": 70000, "diesel_liters": 240, "rate": 1030},
    "Aba": {"fare": 50000, "diesel_liters": 240, "rate": 1030},
    "Owerri": {"fare": 50000, "diesel_liters": 150, "rate": 1030},
    "Abuja": {"fare": 470800, "diesel_liters": 1200, "rate": 1030},
    "Kano": {"fare": 470800, "diesel_liters": 1200, "rate": 1030},
    "Warri": {"fare": 70000, "diesel_liters": 340, "rate": 1030},
    "Igbariam": {"fare": 70000, "diesel_liters": 240, "rate": 1030},
    "Ph": {"fare": 25000, "diesel_liters": 75, "rate": 1030},
}

# Function to calculate diesel cost
def calculate_diesel_cost(liters, rate):
    return liters * rate

# Function to process the received message and return the formatted output
def process_message(message):
    lines = message.strip().splitlines()
    result = StringIO()
    serial_number = 1

    for line in lines:
        for location, pattern in patterns.items():
            if pattern.search(line):
                customer = line.split('--')[0].strip()
                details = location_details[location]
                diesel_cost = calculate_diesel_cost(details["diesel_liters"], details["rate"])

                # Write the formatted line
                result.write(
                    f"{serial_number}\t{customer}\t{details['fare']}\t{details['diesel_liters']}\t"
                    f"{details['rate']}\t{diesel_cost}\tDRIVER_NAME\t40FT EXP. N\n"
                )
                serial_number += 1
                break

    return result.getvalue()

# Handle incoming text messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    response = process_message(message.text)
    if response:
        bot.reply_to(message, f"Copy the following data and paste it into your Excel sheet:\n\n{response}")
    else:
        bot.reply_to(message, "No relevant data found in the message.")

# Create a simple Flask server for health checks
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running"

# Start the bot and the Flask server
if __name__ == "__main__":
    from threading import Thread

    # Start the Telegram bot in a separate thread
    Thread(target=lambda: bot.polling()).start()

    # Start the Flask server
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)