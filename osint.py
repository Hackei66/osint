import requests
import re
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import asyncio

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token (replace with your bot token)
BOT_TOKEN = "8478532189:AAGAI9RcWnQz__NgHeZ1ggvar4cxKmYd-Ns"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Welcome to the Phone Number Lookup Bot!\n"
        "Use /lookup followed by a 10-digit phone number to get information.\n"
        "Example: /lookup 1234567890\n"
        "Type /start to see this message again."
    )

async def lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Extract phone number from command arguments
    if not context.args:
        await update.message.reply_text("❌ Please provide a 10-digit phone number.\nExample: /lookup 1234567890")
        return

    phone = ''.join(context.args).strip()
    num = ''.join(c for c in phone if c.isdigit())
    
    if len(num) != 10:
        await update.message.reply_text("❌ Please enter a valid 10-digit number.")
        return

    try:
        url = f"https://decryptkarnrwalebkl.wasmer.app/?key=lodalelobaby&term={num}"
        response = requests.get(url, timeout=10)
        text = response.text

        message = f"🔍 Searching for: {num}\n"
        message += "=" * 60 + "\n"

        records = extract_multiple_records(text)

        if records:
            message += f"📊 Found {len(records)} record(s)\n"
            message += "=" * 60 + "\n"
            for i, record in enumerate(records, 1):
                message += f"\n📄 Record #{i}\n"
                message += "-" * 40 + "\n"
                message += format_record_data(record)
        else:
            message += "📄 Found 1 record\n"
            message += "-" * 40 + "\n"
            message += format_single_record(text)

        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching data: {str(e)}")

def extract_multiple_records(text):
    records = []

    array_pattern = r'\[\s*\{[^]]+\}\s*\]'
    array_match = re.search(array_pattern, text, re.DOTALL)
    if array_match:
        try:
            json_data = json.loads(array_match.group())
            if isinstance(json_data, list):
                return json_data
        except:
            pass

    objects_pattern = r'\{\s*[^{}]*\s*\}'
    object_matches = re.findall(objects_pattern, text, re.DOTALL)
    
    valid_objects = []
    for obj_text in object_matches:
        if any(field in obj_text for field in ['name', 'fname', 'address', 'circle', 'number', 'phone']):
            try:
                json_obj = json.loads(obj_text)
                valid_objects.append(json_obj)
            except:
                record = extract_key_value_pairs(obj_text)
                if record and len(record) > 1:
                    valid_objects.append(record)
    
    if len(valid_objects) > 1:
        return valid_objects

    repeated_patterns = find_repeated_structures(text)
    if repeated_patterns:
        return repeated_patterns
    
    return None

def find_repeated_structures(text):
    patterns = {
        'name': r'"name"\s*:\s*"([^"]+)"',
        'fname': r'"fname"\s*:\s*"([^"]+)"',
        'address': r'"address"\s*:\s*"([^"]+)"',
        'circle': r'"circle"\s*:\s*"([^"]+)"',
    }
    
    records = []
    max_records = 0

    for field, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            max_records = max(max_records, len(matches))
    
    if max_records <= 1:
        return None

    for i in range(max_records):
        record = {}
        for field, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if i < len(matches):
                record[field] = matches[i]
            else:
                record[field] = "Not Available"

        if any(value != "Not Available" for value in record.values()):
            records.append(record)
    
    return records if len(records) > 1 else None

def extract_key_value_pairs(text):
    record = {}
    patterns = [
        r'"([^"]+)"\s*:\s*"([^"]*)"',
        r"'([^']+)'\s*:\s*'([^']*)'",
        r'"([^"]+)"\s*:\s*([^,}\s]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for key, value in matches:
            if value and value not in ['null', 'None', '']:
                record[key] = value
                
    return record

def format_record_data(record):
    message = ""
    if isinstance(record, dict):
        for key, value in sorted(record.items()):
            message += format_field(key, value)
    else:
        extracted_data = extract_key_value_pairs(str(record))
        for key, value in sorted(extracted_data.items()):
            message += format_field(key, value)
    return message

def format_single_record(text):
    name = extract_value(text, "name")
    fname = extract_value(text, "fname")
    address = extract_value(text, "address")
    circle = extract_value(text, "circle")
    id_val = extract_value(text, "id")
    number = extract_value(text, "number")
    phone = extract_value(text, "phone")

    fields = {
        'Name': name,
        "Father's Name": fname,
        'Address': address,
        'Circle': circle,
        'ID': id_val,
        'Number': number,
        'Phone': phone
    }
    
    message = ""
    for field_name, value in fields.items():
        if value != "Not Available":
            message += f"📍 {field_name}: {value}\n"

    additional_data = extract_key_value_pairs(text)
    for key, value in additional_data.items():
        if key not in ['name', 'fname', 'address', 'circle', 'id', 'number', 'phone']:
            message += format_field(key, value)
    
    return message

def format_field(key, value):
    if value and value not in ['null', 'None', '""', "''", '']:
        formatted_key = key.replace('_', ' ').title()
        return f"📍 {formatted_key}: {value}\n"
    return ""

def extract_value(text, field_name):
    patterns = [
        f'"{field_name}"\\s*:\\s*"([^"]+)"',
        f"'{field_name}'\\s*:\\s*'([^']+)'",
        f'"{field_name}"\\s*:\\s*([^,}}]+)',
    ]    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value and value not in ['null', 'None', '']:
                return value
    return "Not Available"

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    await update.message.reply_text("❌ An error occurred. Please try again later.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("lookup", lookup))
    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()