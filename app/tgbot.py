import os
import re
import telebot
import pandas as pd
from io import StringIO, BytesIO
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

# Store the diesel rate globally to use after the rate prompt
diesel_rate = None

# Function to calculate diesel cost
def calculate_diesel_cost(liters, rate):
    return liters * rate

# Function to process the received message and return the Excel file
def process_message_to_excel(message):
    lines = message.strip().splitlines()

    # Filter out irrelevant lines (like ETA or Total)
    filtered_lines = []
    for line in lines:
        if not line.strip() or line.strip().startswith("ETA") or line.strip().startswith("Total"):
            continue
        filtered_lines.append(line.strip())

    data = []
    serial_number = 1
    processing_customer = False
    current_customer = ""
    current_location = ""

    # Process the filtered lines
    for line in filtered_lines:
        # Check if the line indicates the start of a new customer block
        if "--" in line and any(pattern.search(line) for pattern in patterns.values()):
            current_customer = line.strip()
            processing_customer = True
            continue
        
        # Process container numbers within a customer block
        if processing_customer:
            for location, pattern in patterns.items():
                if pattern.search(current_customer):
                    details = location_details[location]
                    diesel_cost = calculate_diesel_cost(details["diesel_liters"], diesel_rate)

                    # Collect the data into a list of dictionaries
                    data.append({
                        "Customer": current_customer,
                        "Container": line.strip(),
                        "Fare": details['fare'],
                        "Diesel Liters": details['diesel_liters'],
                        "Diesel Rate": diesel_rate,
                        "Diesel Cost": diesel_cost
                    })
                    serial_number += 1
                    break

    # Convert the data into a pandas DataFrame
    df = pd.DataFrame(data)

    # Save the DataFrame to an Excel file in memory
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    return excel_buffer

# Handle incoming text messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    global diesel_rate

    if diesel_rate is None:
        bot.reply_to(message, "What is the rate of diesel?")
        bot.register_next_step_handler(message, set_diesel_rate)
    else:
        excel_file = process_message_to_excel(message.text)
        bot.send_document(message.chat.id, excel_file, caption="Here is your processed data in Excel format.")
        # Reset the diesel rate after processing
        diesel_rate = None

# Function to set the diesel rate after the prompt
def set_diesel_rate(message):
    global diesel_rate

    try:
        diesel_rate = float(message.text.strip())
        bot.reply_to(message, "Rate set! Now, please resend the data to be processed.")
    except ValueError:
        bot.reply_to(message, "Please enter a valid number for the diesel rate.")
        bot.register_next_step_handler(message, set_diesel_rate)  # Prompt again if the input is invalid

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