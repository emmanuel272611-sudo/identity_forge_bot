"""
📋 Identity Forge Bot - Professional Document Generator
Generate ID Cards, NIN, Driver's Licenses, and more!
Convert and validate identity documents
"""

import os
import io
import re
import json
import logging
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ==================== LOGGING ====================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

# Try multiple possible token variable names
BOT_TOKEN = (
    os.environ.get("TELEGRAM_TOKEN") or
    os.environ.get("TELEGRAM_BOT_TOKEN") or
    os.environ.get("BOT_TOKEN")
)

# If token is not set, try reading from .env file
if not BOT_TOKEN:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        BOT_TOKEN = (
            os.environ.get("TELEGRAM_TOKEN") or
            os.environ.get("TELEGRAM_BOT_TOKEN") or
            os.environ.get("BOT_TOKEN")
        )
    except:
        pass

# If still no token, show error
if not BOT_TOKEN:
    logger.error("=" * 60)
    logger.error("❌ ERROR: No Telegram Bot Token found!")
    logger.error("=" * 60)
    raise ValueError("❌ No Telegram Bot Token found in environment variables!")

BOT_NAME = "Identity Forge Bot"
BOT_USERNAME = "identity_forge_bot"
BOT_VERSION = "1.0.0"

# ==================== CONSTANTS ====================

# Document types
DOCUMENT_TYPES = {
    "id_card": {"name": "🪪 ID Card", "prefix": "ID"},
    "nin": {"name": "🔢 NIN", "prefix": "NIN"},
    "drivers_license": {"name": "🚗 Driver's License", "prefix": "DL"},
    "passport": {"name": "🛂 Passport", "prefix": "PP"},
    "voter_id": {"name": "🗳️ Voter ID", "prefix": "VID"},
    "student_id": {"name": "🎓 Student ID", "prefix": "SID"},
}

# Nigerian states for NIN generation
NIGERIAN_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa",
    "Benue", "Borno", "Cross River", "Delta", "Ebonyi", "Edo",
    "Ekiti", "Enugu", "FCT", "Gombe", "Imo", "Jigawa",
    "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara",
    "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun",
    "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara"
]

# ==================== USER DATA ====================

user_data: Dict[int, Dict] = {}

def get_user_data(user_id: int) -> Dict:
    """Get or create user data"""
    if user_id not in user_data:
        user_data[user_id] = {
            "total_generated": 0,
            "history": [],
            "settings": {
                "default_document": "id_card",
                "color_scheme": "blue",
            }
        }
    return user_data[user_id]

# ==================== KEYBOARDS ====================

def get_main_keyboard():
    """Create main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🪪 ID Card Generator", callback_data="gen_id")],
        [InlineKeyboardButton("🔢 NIN Generator", callback_data="gen_nin")],
        [InlineKeyboardButton("🚗 Driver's License", callback_data="gen_license")],
        [InlineKeyboardButton("🛂 Passport", callback_data="gen_passport")],
        [InlineKeyboardButton("📋 All Documents", callback_data="all_docs")],
        [InlineKeyboardButton("🔄 Document Converter", callback_data="convert_doc")],
        [InlineKeyboardButton("✅ Document Validator", callback_data="validate_doc")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_document_keyboard():
    """Create document type selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("🪪 ID Card", callback_data="doc_id_card")],
        [InlineKeyboardButton("🔢 NIN", callback_data="doc_nin")],
        [InlineKeyboardButton("🚗 Driver's License", callback_data="doc_drivers_license")],
        [InlineKeyboardButton("🛂 Passport", callback_data="doc_passport")],
        [InlineKeyboardButton("🗳️ Voter ID", callback_data="doc_voter_id")],
        [InlineKeyboardButton("🎓 Student ID", callback_data="doc_student_id")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_color_keyboard():
    """Create color scheme selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔵 Blue", callback_data="color_blue")],
        [InlineKeyboardButton("🟢 Green", callback_data="color_green")],
        [InlineKeyboardButton("🔴 Red", callback_data="color_red")],
        [InlineKeyboardButton("🟣 Purple", callback_data="color_purple")],
        [InlineKeyboardButton("🟠 Orange", callback_data="color_orange")],
        [InlineKeyboardButton("⚫ Black", callback_data="color_black")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_document_options_keyboard(doc_type: str):
    """Create document options keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔄 Generate New", callback_data=f"gen_{doc_type}")],
        [InlineKeyboardButton("📥 Export as PNG", callback_data=f"export_{doc_type}")],
        [InlineKeyboardButton("📋 Convert Format", callback_data="convert_doc")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== DOCUMENT GENERATION FUNCTIONS ====================

def generate_nin() -> Dict:
    """Generate a Nigerian National Identification Number"""
    # Format: 11 digits with check digit
    nin = []
    for i in range(10):
        nin.append(str(random.randint(0, 9)))
    
    # Calculate check digit (simple checksum)
    total = sum(int(d) for d in nin)
    check_digit = (total * 3) % 10
    nin.append(str(check_digit))
    
    state = random.choice(NIGERIAN_STATES)
    birth_date = datetime.now() - timedelta(days=random.randint(6570, 21900))
    
    return {
        "number": "".join(nin),
        "state": state,
        "birth_date": birth_date.strftime("%d/%m/%Y"),
        "issue_date": datetime.now().strftime("%d/%m/%Y"),
        "expiry_date": (datetime.now() + timedelta(days=365*5)).strftime("%d/%m/%Y"),
    }

def generate_id_card(data: Dict = None) -> bytes:
    """Generate an ID card image"""
    if data is None:
        data = {
            "full_name": "John Doe",
            "id_number": "ID-2024-001",
            "department": "Technology",
            "role": "Software Engineer",
            "issue_date": datetime.now().strftime("%d/%m/%Y"),
            "expiry_date": (datetime.now() + timedelta(days=365*2)).strftime("%d/%m/%Y"),
            "color": "blue",
        }
    
    try:
        # Create card image
        width, height = 600, 380
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Color schemes
        colors = {
            "blue": ("#1a73e8", "#e8f0fe"),
            "green": ("#2e7d32", "#e8f5e9"),
            "red": ("#c62828", "#ffebee"),
            "purple": ("#6a1b9a", "#f3e5f5"),
            "orange": ("#e65100", "#fff3e0"),
            "black": ("#263238", "#eceff1"),
        }
        
        primary_color, bg_color = colors.get(data.get("color", "blue"), colors["blue"])
        
        # Draw background
        draw.rectangle([0, 0, width, height], fill=bg_color)
        
        # Draw header bar
        draw.rectangle([0, 0, width, 80], fill=primary_color)
        
        # Draw title
        draw.text((20, 20), "IDENTITY CARD", fill="#FFFFFF", font=font_large)
        
        # Draw photo placeholder
        draw.rectangle([30, 100, 150, 280], outline=primary_color, width=2)
        draw.text((60, 180), "PHOTO", fill="#888888", font=font_medium)
        
        # Draw details
        y_start = 110
        labels = [
            ("Name:", data.get("full_name", "John Doe")),
            ("ID Number:", data.get("id_number", "ID-2024-001")),
            ("Department:", data.get("department", "Technology")),
            ("Role:", data.get("role", "Software Engineer")),
            ("Issue Date:", data.get("issue_date", "01/01/2024")),
            ("Expiry Date:", data.get("expiry_date", "01/01/2026")),
        ]
        
        for label, value in labels:
            draw.text((180, y_start), label, fill="#666666", font=font_small)
            draw.text((280, y_start), value, fill="#333333", font=font_medium)
            y_start += 30
        
        # Draw barcode placeholder
        for i in range(300, 550, 4):
            height_bar = random.randint(10, 30)
            draw.rectangle([i, 330, i + 2, 330 + height_bar], fill="#000000")
        
        # Draw footer
        draw.text((20, height - 30), "Valid ID - Official Document", fill="#999999", font=font_small)
        draw.text((width - 200, height - 30), "www.identity.gov", fill="#999999", font=font_small)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"ID generation error: {e}")
        return None

def generate_drivers_license(data: Dict = None) -> bytes:
    """Generate a driver's license image"""
    if data is None:
        data = {
            "full_name": "Jane Smith",
            "license_number": f"DL-{random.randint(100000, 999999)}",
            "vehicle_class": "B",
            "issue_date": datetime.now().strftime("%d/%m/%Y"),
            "expiry_date": (datetime.now() + timedelta(days=365*3)).strftime("%d/%m/%Y"),
            "color": "blue",
        }
    
    try:
        width, height = 600, 400
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Color schemes
        colors = {
            "blue": ("#1565c0", "#e3f2fd"),
            "green": ("#2e7d32", "#e8f5e9"),
            "red": ("#c62828", "#ffebee"),
            "purple": ("#6a1b9a", "#f3e5f5"),
            "orange": ("#e65100", "#fff3e0"),
            "black": ("#263238", "#eceff1"),
        }
        
        primary_color, bg_color = colors.get(data.get("color", "blue"), colors["blue"])
        
        # Draw background
        draw.rectangle([0, 0, width, height], fill=bg_color)
        
        # Draw header
        draw.rectangle([0, 0, width, 80], fill=primary_color)
        draw.text((20, 20), "DRIVER'S LICENSE", fill="#FFFFFF", font=font_large)
        
        # Draw state emblem placeholder
        draw.rectangle([width - 120, 10, width - 20, 70], outline="#FFFFFF", width=2)
        draw.text((width - 100, 35), "STATE", fill="#FFFFFF", font=font_small)
        
        # Draw photo placeholder
        draw.rectangle([30, 100, 150, 280], outline=primary_color, width=2)
        draw.text((60, 180), "PHOTO", fill="#888888", font=font_medium)
        
        # Draw details
        y_start = 110
        labels = [
            ("Name:", data.get("full_name", "Jane Smith")),
            ("License #:", data.get("license_number", "DL-123456")),
            ("Class:", data.get("vehicle_class", "B")),
            ("Issue Date:", data.get("issue_date", "01/01/2024")),
            ("Expiry Date:", data.get("expiry_date", "01/01/2027")),
        ]
        
        for label, value in labels:
            draw.text((180, y_start), label, fill="#666666", font=font_small)
            draw.text((280, y_start), value, fill="#333333", font=font_medium)
            y_start += 35
        
        # Draw barcode
        for i in range(300, 550, 3):
            height_bar = random.randint(15, 35)
            draw.rectangle([i, 350, i + 2, 350 + height_bar], fill="#000000")
        
        # Draw footer
        draw.text((20, height - 30), "Driver License - Official Document", fill="#999999", font=font_small)
        draw.text((width - 200, height - 30), "www.dmv.gov", fill="#999999", font=font_small)
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"License generation error: {e}")
        return None

def generate_nin_image(nin_data: Dict) -> bytes:
    """Generate a NIN card image"""
    try:
        width, height = 400, 250
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw header
        draw.rectangle([0, 0, width, 50], fill="#1a237e")
        draw.text((width//2 - 60, 15), "NATIONAL IDENTIFICATION", fill="#FFFFFF", font=font_large)
        draw.text((width//2 - 40, 35), "NUMBER (NIN)", fill="#FFD700", font=font_medium)
        
        # Draw NIN number prominently
        nin_number = nin_data.get("number", "12345678901")
        draw.text((width//2 - 80, 70), nin_number, fill="#000000", font=font_large)
        
        # Draw details
        y_start = 120
        details = [
            (f"State: {nin_data.get('state', 'Lagos')}"),
            (f"Birth Date: {nin_data.get('birth_date', '01/01/1990')}"),
            (f"Issue Date: {nin_data.get('issue_date', '01/01/2024')}"),
            (f"Expiry Date: {nin_data.get('expiry_date', '01/01/2029')}"),
        ]
        
        for detail in details:
            draw.text((20, y_start), detail, fill="#333333", font=font_small)
            y_start += 25
        
        # Draw barcode
        for i in range(50, 350, 3):
            draw.rectangle([i, 210, i + 2, 230], fill="#000000")
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"NIN image error: {e}")
        return None

def generate_passport(data: Dict = None) -> bytes:
    """Generate a passport document image"""
    if data is None:
        data = {
            "full_name": "Michael Johnson",
            "passport_number": f"PP-{random.randint(100000, 999999)}",
            "nationality": "Nigerian",
            "issue_date": datetime.now().strftime("%d/%m/%Y"),
            "expiry_date": (datetime.now() + timedelta(days=365*5)).strftime("%d/%m/%Y"),
            "color": "blue",
        }
    
    try:
        width, height = 600, 400
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        colors = {
            "blue": ("#0d47a1", "#e3f2fd"),
            "green": ("#1b5e20", "#e8f5e9"),
            "red": ("#b71c1c", "#ffebee"),
            "purple": ("#4a148c", "#f3e5f5"),
            "orange": ("#bf360c", "#fff3e0"),
            "black": ("#1a1a2e", "#eceff1"),
        }
        
        primary_color, bg_color = colors.get(data.get("color", "blue"), colors["blue"])
        
        draw.rectangle([0, 0, width, height], fill=bg_color)
        draw.rectangle([0, 0, width, 80], fill=primary_color)
        draw.text((20, 20), "PASSPORT", fill="#FFFFFF", font=font_large)
        
        draw.rectangle([30, 100, 150, 280], outline=primary_color, width=2)
        draw.text((60, 180), "PHOTO", fill="#888888", font=font_medium)
        
        y_start = 110
        labels = [
            ("Name:", data.get("full_name", "Michael Johnson")),
            ("Passport #:", data.get("passport_number", "PP-123456")),
            ("Nationality:", data.get("nationality", "Nigerian")),
            ("Issue Date:", data.get("issue_date", "01/01/2024")),
            ("Expiry Date:", data.get("expiry_date", "01/01/2029")),
        ]
        
        for label, value in labels:
            draw.text((180, y_start), label, fill="#666666", font=font_small)
            draw.text((280, y_start), value, fill="#333333", font=font_medium)
            y_start += 35
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"Passport generation error: {e}")
        return None

def generate_voter_id(data: Dict = None) -> bytes:
    """Generate a voter ID card image"""
    if data is None:
        data = {
            "full_name": "David Williams",
            "voter_id": f"VID-{random.randint(100000, 999999)}",
            "constituency": "Lagos Central",
            "issue_date": datetime.now().strftime("%d/%m/%Y"),
            "color": "green",
        }
    
    try:
        width, height = 500, 320
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        primary_color = "#1b5e20"
        draw.rectangle([0, 0, width, 60], fill=primary_color)
        draw.text((width//2 - 70, 15), "VOTER ID CARD", fill="#FFFFFF", font=font_large)
        
        y_start = 80
        labels = [
            ("Name:", data.get("full_name", "David Williams")),
            ("Voter ID:", data.get("voter_id", "VID-123456")),
            ("Constituency:", data.get("constituency", "Lagos Central")),
            ("Issue Date:", data.get("issue_date", "01/01/2024")),
        ]
        
        for label, value in labels:
            draw.text((30, y_start), label, fill="#666666", font=font_small)
            draw.text((150, y_start), value, fill="#333333", font=font_medium)
            y_start += 35
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"Voter ID error: {e}")
        return None

def generate_student_id(data: Dict = None) -> bytes:
    """Generate a student ID card image"""
    if data is None:
        data = {
            "full_name": "Emma Okonkwo",
            "student_id": f"SID-{random.randint(100000, 999999)}",
            "course": "Computer Science",
            "university": "University of Lagos",
            "issue_date": datetime.now().strftime("%d/%m/%Y"),
            "color": "purple",
        }
    
    try:
        width, height = 500, 320
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        primary_color = "#6a1b9a"
        draw.rectangle([0, 0, width, 60], fill=primary_color)
        draw.text((width//2 - 60, 15), "STUDENT ID CARD", fill="#FFFFFF", font=font_large)
        
        y_start = 80
        labels = [
            ("Name:", data.get("full_name", "Emma Okonkwo")),
            ("Student ID:", data.get("student_id", "SID-123456")),
            ("Course:", data.get("course", "Computer Science")),
            ("University:", data.get("university", "University of Lagos")),
            ("Issue Date:", data.get("issue_date", "01/01/2024")),
        ]
        
        for label, value in labels:
            draw.text((30, y_start), label, fill="#666666", font=font_small)
            draw.text((150, y_start), value, fill="#333333", font=font_medium)
            y_start += 30
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"Student ID error: {e}")
        return None

def validate_id_number(number: str, doc_type: str) -> Dict:
    """Validate an ID number format"""
    result = {"valid": False, "message": "", "type": doc_type}
    
    if doc_type == "nin":
        if len(number) == 11 and number.isdigit():
            result["valid"] = True
            result["message"] = "✅ Valid NIN format (11 digits)"
        else:
            result["message"] = "❌ Invalid NIN format. Must be 11 digits."
    
    elif doc_type == "id_card":
        if re.match(r'ID-\d{4}-\d{3}', number):
            result["valid"] = True
            result["message"] = "✅ Valid ID Card format"
        else:
            result["message"] = "❌ Invalid ID Card format. Use: ID-YYYY-XXX"
    
    elif doc_type == "drivers_license":
        if re.match(r'DL-\d{6}', number):
            result["valid"] = True
            result["message"] = "✅ Valid Driver's License format"
        else:
            result["message"] = "❌ Invalid License format. Use: DL-XXXXXX"
    
    elif doc_type == "passport":
        if re.match(r'PP-\d{6}', number):
            result["valid"] = True
            result["message"] = "✅ Valid Passport format"
        else:
            result["message"] = "❌ Invalid Passport format. Use: PP-XXXXXX"
    
    else:
        result["message"] = "❌ Unknown document type"
    
    return result

def convert_document(data: str, from_type: str, to_type: str) -> Dict:
    """Convert document data between formats"""
    # This is a simplified conversion - in production, you'd use actual conversion logic
    result = {
        "success": False,
        "converted_data": "",
        "message": ""
    }
    
    try:
        if from_type == "nin" and to_type == "id":
            # Convert NIN to ID format
            result["converted_data"] = f"ID-{data[:4]}-{data[4:7]}"
            result["success"] = True
            result["message"] = "✅ Converted NIN to ID Card format"
        elif from_type == "id" and to_type == "nin":
            # Convert ID to NIN format
            import re
            match = re.search(r'ID-(\d{4})-(\d{3})', data)
            if match:
                result["converted_data"] = f"{match.group(1)}{match.group(2)}0000"
                result["success"] = True
                result["message"] = "✅ Converted ID Card to NIN format"
        else:
            result["message"] = "❌ Conversion not supported for these types"
    except Exception as e:
        result["message"] = f"❌ Conversion error: {str(e)}"
    
    return result

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = str(user.id)
    data = get_user_data(user_id)
    
    welcome = (
        f"📋 **Welcome to {BOT_NAME}!**\n\n"
        f"👋 Hello @{user.username or user.first_name}!\n\n"
        f"Your professional identity document generator.\n\n"
        f"⚡ **Features:**\n"
        f"• 🪪 ID Card Generator\n"
        f"• 🔢 NIN Generator & Validator\n"
        f"• 🚗 Driver's License Generator\n"
        f"• 🛂 Passport Generator\n"
        f"• 🗳️ Voter ID Generator\n"
        f"• 🎓 Student ID Generator\n"
        f"• 🔄 Document Converter\n"
        f"• ✅ Document Validator\n\n"
        f"📊 **Your Stats:**\n"
        f"• Total documents generated: {data['total_generated']}\n\n"
        f"⬇️ Use the buttons below to get started!"
    )
    
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        f"📖 **{BOT_NAME} User Guide**\n\n"
        "**📋 Document Types:**\n"
        "• 🪪 ID Card - Employee/Company ID\n"
        "• 🔢 NIN - National Identification Number\n"
        "• 🚗 Driver's License - Driving permit\n"
        "• 🛂 Passport - International travel document\n"
        "• 🗳️ Voter ID - Voting identification\n"
        "• 🎓 Student ID - Academic identification\n\n"
        "**🔧 Features:**\n"
        "• Generate any document type\n"
        "• Validate document numbers\n"
        "• Convert between formats\n"
        "• Customize colors\n\n"
        "**📌 Commands:**\n"
        "/start - Main menu\n"
        "/help - This help\n"
        "/stats - Your statistics"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    # Count document types
    doc_counts = {}
    for entry in data.get("history", []):
        doc_type = entry.get("type", "unknown")
        doc_counts[doc_type] = doc_counts.get(doc_type, 0) + 1
    
    stats_text = (
        f"📊 **Your Statistics**\n\n"
        f"📋 Total documents: {data['total_generated']}\n"
        f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    )
    
    if doc_counts:
        stats_text += "📈 **Document Types:**\n"
        for doc_type, count in doc_counts.items():
            doc_name = DOCUMENT_TYPES.get(doc_type, {}).get("name", doc_type)
            stats_text += f"• {doc_name}: {count}\n"
    
    await update.message.reply_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ==================== CALLBACK HANDLERS ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    action = query.data
    
    # ===== DOCUMENT GENERATION =====
    
    if action.startswith("gen_"):
        doc_type = action.replace("gen_", "")
        
        # Generate document based on type
        if doc_type == "id_card" or doc_type == "id":
            doc_data = {
                "full_name": "John Doe",
                "id_number": f"ID-{datetime.now().year}-{random.randint(100, 999)}",
                "department": "Technology",
                "role": "Software Engineer",
                "issue_date": datetime.now().strftime("%d/%m/%Y"),
                "expiry_date": (datetime.now() + timedelta(days=365*2)).strftime("%d/%m/%Y"),
                "color": data["settings"].get("color_scheme", "blue"),
            }
            img_data = generate_id_card(doc_data)
            caption = f"🪪 **ID Card Generated!**\n\nName: {doc_data['full_name']}\nID: {doc_data['id_number']}\nDepartment: {doc_data['department']}"
            
        elif doc_type == "nin":
            nin_data = generate_nin()
            img_data = generate_nin_image(nin_data)
            caption = f"🔢 **NIN Generated!**\n\nNIN: {nin_data['number']}\nState: {nin_data['state']}\nBirth: {nin_data['birth_date']}"
            
        elif doc_type == "drivers_license":
            doc_data = {
                "full_name": "Jane Smith",
                "license_number": f"DL-{random.randint(100000, 999999)}",
                "vehicle_class": random.choice(["A", "B", "C", "D"]),
                "issue_date": datetime.now().strftime("%d/%m/%Y"),
                "expiry_date": (datetime.now() + timedelta(days=365*3)).strftime("%d/%m/%Y"),
                "color": data["settings"].get("color_scheme", "blue"),
            }
            img_data = generate_drivers_license(doc_data)
            caption = f"🚗 **Driver's License Generated!**\n\nName: {doc_data['full_name']}\nLicense: {doc_data['license_number']}\nClass: {doc_data['vehicle_class']}"
            
        elif doc_type == "passport":
            doc_data = {
                "full_name": "Michael Johnson",
                "passport_number": f"PP-{random.randint(100000, 999999)}",
                "nationality": "Nigerian",
                "issue_date": datetime.now().strftime("%d/%m/%Y"),
                "expiry_date": (datetime.now() + timedelta(days=365*5)).strftime("%d/%m/%Y"),
                "color": data["settings"].get("color_scheme", "blue"),
            }
            img_data = generate_passport(doc_data)
            caption = f"🛂 **Passport Generated!**\n\nName: {doc_data['full_name']}\nPassport: {doc_data['passport_number']}\nNationality: {doc_data['nationality']}"
            
        elif doc_type == "voter_id":
            doc_data = {
                "full_name": "David Williams",
                "voter_id": f"VID-{random.randint(100000, 999999)}",
                "constituency": random.choice(["Lagos Central", "Abuja", "Kano", "Port Harcourt"]),
                "issue_date": datetime.now().strftime("%d/%m/%Y"),
                "color": data["settings"].get("color_scheme", "green"),
            }
            img_data = generate_voter_id(doc_data)
            caption = f"🗳️ **Voter ID Generated!**\n\nName: {doc_data['full_name']}\nID: {doc_data['voter_id']}\nConstituency: {doc_data['constituency']}"
            
        elif doc_type == "student_id":
            doc_data = {
                "full_name": "Emma Okonkwo",
                "student_id": f"SID-{random.randint(100000, 999999)}",
                "course": random.choice(["Computer Science", "Engineering", "Medicine", "Law"]),
                "university": random.choice(["University of Lagos", "UNN", "OAU", "ABU"]),
                "issue_date": datetime.now().strftime("%d/%m/%Y"),
                "color": data["settings"].get("color_scheme", "purple"),
            }
            img_data = generate_student_id(doc_data)
            caption = f"🎓 **Student ID Generated!**\n\nName: {doc_data['full_name']}\nID: {doc_data['student_id']}\nCourse: {doc_data['course']}"
            
        else:
            await query.edit_message_text(
                "❌ Unknown document type.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        if img_data:
            data["total_generated"] += 1
            data["history"].append({
                "type": doc_type,
                "timestamp": datetime.now().isoformat()
            })
            
            await query.message.reply_photo(
                photo=io.BytesIO(img_data),
                caption=caption,
                parse_mode="Markdown",
                reply_markup=get_document_options_keyboard(doc_type)
            )
        else:
            await query.message.reply_text(
                "❌ Failed to generate document. Please try again.",
                reply_markup=get_main_keyboard()
            )
            
        await query.delete_message()
        
    # ===== ALL DOCUMENTS =====
    
    elif action == "all_docs":
        await query.edit_message_text(
            "📋 **All Document Types**\n\n"
            "Select a document type to generate:",
            parse_mode="Markdown",
            reply_markup=get_document_keyboard()
        )
        
    # ===== DOCUMENT SELECTION =====
    
    elif action.startswith("doc_"):
        doc_type = action.replace("doc_", "")
        await generate_document(query, doc_type, data)
        
    # ===== CONVERT DOCUMENT =====
    
    elif action == "convert_doc":
        await query.edit_message_text(
            "🔄 **Document Converter**\n\n"
            "Send me a document number to convert.\n\n"
            "Examples:\n"
            "• NIN: `12345678901`\n"
            "• ID Card: `ID-2024-001`\n"
            "• License: `DL-123456`\n\n"
            "I'll try to convert it to another format.\n\n"
            "Send /cancel to cancel.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "convert_doc"
        
    # ===== VALIDATE DOCUMENT =====
    
    elif action == "validate_doc":
        await query.edit_message_text(
            "✅ **Document Validator**\n\n"
            "Send me a document number to validate.\n\n"
            "Examples:\n"
            "• NIN: `12345678901`\n"
            "• ID Card: `ID-2024-001`\n"
            "• License: `DL-123456`\n"
            "• Passport: `PP-123456`\n\n"
            "Send /cancel to cancel.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "validate_doc"
        
    # ===== SETTINGS =====
    
    elif action == "change_color":
        await query.edit_message_text(
            "🎨 **Select Color Scheme**\n\n"
            "Choose a color for your documents:",
            parse_mode="Markdown",
            reply_markup=get_color_keyboard()
        )
        
    elif action.startswith("color_"):
        color = action.replace("color_", "")
        data["settings"]["color_scheme"] = color
        await query.edit_message_text(
            f"✅ **Color Updated!**\n\n"
            f"New color scheme: {color.capitalize()}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    # ===== STATS =====
    
    elif action == "stats":
        doc_counts = {}
        for entry in data.get("history", []):
            doc_type = entry.get("type", "unknown")
            doc_counts[doc_type] = doc_counts.get(doc_type, 0) + 1
        
        stats_text = (
            f"📊 **Your Statistics**\n\n"
            f"📋 Total documents: {data['total_generated']}\n"
            f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        )
        
        if doc_counts:
            stats_text += "📈 **Document Types:**\n"
            for doc_type, count in doc_counts.items():
                doc_name = DOCUMENT_TYPES.get(doc_type, {}).get("name", doc_type)
                stats_text += f"• {doc_name}: {count}\n"
        
        await query.edit_message_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    # ===== HELP =====
    
    elif action == "help":
        await help_command(update, context)
        
    # ===== BACK =====
    
    elif action == "back":
        await query.edit_message_text(
            "🏠 **Main Menu**\n\n"
            "What would you like to do?",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = None
        
    # ===== EXPORT =====
    
    elif action.startswith("export_"):
        await query.edit_message_text(
            "📥 **Export Feature**\n\n"
            "This feature will be available soon!\n\n"
            "You can already download images directly from Telegram.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== HELPER FUNCTIONS ====================

async def generate_document(query, doc_type, data):
    """Generate a document and send it"""
    doc_type_map = {
        "id_card": ("gen_id", "🪪 ID Card Generator"),
        "nin": ("gen_nin", "🔢 NIN Generator"),
        "drivers_license": ("gen_license", "🚗 Driver's License Generator"),
        "passport": ("gen_passport", "🛂 Passport Generator"),
        "voter_id": ("gen_voter", "🗳️ Voter ID Generator"),
        "student_id": ("gen_student", "🎓 Student ID Generator"),
    }
    
    if doc_type in doc_type_map:
        callback, label = doc_type_map[doc_type]
        await query.edit_message_text(
            f"**{label}**\n\n"
            "Generating your document...\n"
            "Please wait ⏳",
            parse_mode="Markdown"
        )
        
        # Trigger generation
        await button_handler(query.update, query.context)

# ==================== MESSAGE HANDLERS ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for validation and conversion"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    text = update.message.text.strip()
    action = context.user_data.get("action", "")
    
    if not text:
        await update.message.reply_text(
            "❌ Please send some text!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # ===== CANCEL =====
    
    if text.lower() == "/cancel":
        context.user_data["action"] = None
        await update.message.reply_text(
            "✅ Cancelled!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # ===== DOCUMENT CONVERTER =====
    
    if action == "convert_doc":
        # Try to detect document type
        doc_type = "unknown"
        if text.startswith("ID-"):
            doc_type = "id_card"
        elif len(text) == 11 and text.isdigit():
            doc_type = "nin"
        elif text.startswith("DL-"):
            doc_type = "drivers_license"
        elif text.startswith("PP-"):
            doc_type = "passport"
        elif text.startswith("VID-"):
            doc_type = "voter_id"
        elif text.startswith("SID-"):
            doc_type = "student_id"
        
        # Convert to another format
        target_type = "id_card" if doc_type != "id_card" else "nin"
        result = convert_document(text, doc_type, target_type)
        
        await update.message.reply_text(
            f"🔄 **Document Conversion**\n\n"
            f"Input: {text}\n"
            f"Type: {doc_type.upper()}\n"
            f"Converted to: {target_type.upper()}\n\n"
            f"{result['message']}\n"
            f"Result: `{result['converted_data']}`" if result['success'] else result['message'],
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = None
        
    # ===== DOCUMENT VALIDATOR =====
    
    elif action == "validate_doc":
        # Try to detect document type
        doc_type = "unknown"
        if text.startswith("ID-"):
            doc_type = "id_card"
        elif len(text) == 11 and text.isdigit():
            doc_type = "nin"
        elif text.startswith("DL-"):
            doc_type = "drivers_license"
        elif text.startswith("PP-"):
            doc_type = "passport"
        elif text.startswith("VID-"):
            doc_type = "voter_id"
        elif text.startswith("SID-"):
            doc_type = "student_id"
        
        if doc_type == "unknown":
            await update.message.reply_text(
                "❌ Could not detect document type.\n\n"
                "Please send a valid document number.",
                reply_markup=get_main_keyboard()
            )
            return
        
        result = validate_id_number(text, doc_type)
        
        await update.message.reply_text(
            f"✅ **Document Validation**\n\n"
            f"Document: {text}\n"
            f"Type: {doc_type.upper()}\n\n"
            f"{result['message']}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = None
        
    else:
        await update.message.reply_text(
            "📋 **Use the buttons below!**\n\n"
            "I can generate various identity documents.\n"
            "Just click a button to get started!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== MAIN ====================

async def post_init(application):
    """Post initialization"""
    logger.info("=" * 60)
    logger.info(f"📋 {BOT_NAME} Started Successfully!")
    logger.info(f"🤖 Username: @{BOT_USERNAME}")
    logger.info(f"📦 Version: {BOT_VERSION}")
    logger.info(f"📄 Document Types: {len(DOCUMENT_TYPES)}")
    logger.info("=" * 60)
    logger.info("✅ Bot is ready to generate documents!")
    logger.info("=" * 60)

def main():
    """Main entry point"""
    logger.info(f"🚀 Starting {BOT_NAME}...")
    logger.info(f"📡 Using token: {BOT_TOKEN[:15]}...{BOT_TOKEN[-5:]}")
    
    application = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .post_init(post_init) \
        .build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("✅ Bot is polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
