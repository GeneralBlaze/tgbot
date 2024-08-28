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

# Define the fares and diesel liters based on location
location_details = {
    "Onitsha": {"fare": 70000, "diesel_liters": 240},
    "Aba": {"fare": 50000, "diesel_liters": 240},
    "Owerri": {"fare": 50000, "diesel_liters": 150},
    "Abuja": {"fare": 470800, "diesel_liters": 1200},
    "Kano": {"fare": 470800, "diesel_liters": 1200},
    "Warri": {"fare": 70000, "diesel_liters": 340},
    "Igbariam": {"fare": 70000, "diesel_liters": 240},
    "Ph": {"fare": 25000, "diesel_liters": 75},
}

# Global variable to store diesel rate
diesel_rate = None

# Function to calculate diesel cost
def calculate_diesel_cost(liters, rate):
    return liters * rate

# Function to process the received message and return the formatted output
def process_message(message):
    global diesel_rate

    if diesel_rate is None:
        return "Please set the diesel rate first using /rate <value>."

    lines = message.strip().splitlines()
    result = StringIO()
    serial_number = 1

    current_header = None

    for line in lines:
        if '--' in line:
            current_header = line.strip()
            result.write(f"\n|     | **{current_header}** |     |     |     |     |\n")
            continue
        
        if line.strip():  # If the line is not empty, process it
            for location, pattern in patterns.items():
                if pattern.search(current_header):  # Match header location
                    container_number = line.strip()
                    details = location_details[location]
                    diesel_cost = calculate_diesel_cost(details["diesel_liters"], diesel_rate)

                    result.write(
                        f"| {serial_number} | {container_number} | {details['fare']} | "
                        f"{details['diesel_liters']} | {diesel_rate} | {diesel_cost} |\n"
                    )
                    serial_number += 1
                    break

    return result.getvalue()

# Handle the /start and /help commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Please set the diesel rate using /rate <value>, then send the container details.")

# Handle the /rate command
@bot.message_handler(commands=['rate'])
def set_diesel_rate(message):
    global diesel_rate
    try:
        diesel_rate = int(message.text.split()[1])
        bot.reply_to(message, f"Diesel rate set to {diesel_rate}. Now you can send container details.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Please provide a valid diesel rate. Usage: /rate <value>")

# Handle any text messages that aren't commands
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
    Thread(target=lambda: bot.polling(none_stop=True)).start()

    # Start the Flask server
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)