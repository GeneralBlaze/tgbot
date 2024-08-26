from telegram.ext import Updater, MessageHandler, Filters
import re

# Define regex patterns
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

# Function to fill values based on the location
def fill_values(location):
    if patterns["Onitsha"].search(location):
        return 70000, 240, 1030
    elif patterns["Aba"].search(location):
        return 50000, 240, 1030
    elif patterns["Owerri"].search(location):
        return 50000, 150, 1030
    elif patterns["Abuja"].search(location):
        return 470800, 1200, 1030
    elif patterns["Kano"].search(location):
        return 470800, 1200, 1030
    elif patterns["Warri"].search(location):
        return 70000, 340, 1030
    elif patterns["Igbariam"].search(location):
        return 70000, 240, 1030
    elif patterns["Ph"].search(location):
        return 25000, 75, 1030
    else:
        return None

# Function to process the incoming message text
def process_text(text):
    lines = text.strip().splitlines()
    processed_data = []
    serial_number = 1
    
    for line in lines:
        match = re.search(r'--(\d+\*\d+)--', line)
        if match:
            customer = line.split('--')[0]
            location = line.split('--')[-1]
            fare, diesel_ltr, unit_price = fill_values(location)
            
            if fare:
                for next_line in lines[lines.index(line) + 1:]:
                    if not next_line or next_line.startswith("ETA") or next_line.startswith("Total"):
                        break
                    # Append to processed data
                    processed_data.append(
                        f"{serial_number}\t{customer}\t{fare}\t{diesel_ltr}\t{unit_price}\t\t{next_line}\t\t"
                    )
                    serial_number += 1
    
    return "\n".join(processed_data)

# Function to handle messages
def handle_message(update, context):
    text = update.message.text
    processed_text = process_text(text)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"```\n{processed_text}\n```", parse_mode='Markdown')

# Main function to run the bot
def main():
    TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'  # Replace with your bot token

    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add handler to process messages
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()