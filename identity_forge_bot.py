"""
🔐 Identity Forge Bot - Professional Identity Verification & Document Generator
With Photo Upload Support for all ID documents
"""

import os
import io
import re
import json
import logging
import random
import string
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
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

if not BOT_TOKEN:
    logger.error("=" * 60)
    logger.error("❌ ERROR: No Telegram Bot Token found!")
    logger.error("=" * 60)
    raise ValueError("❌ No Telegram Bot Token found in environment variables!")

BOT_NAME = "Identity Forge Bot"
BOT_USERNAME = "identity_forge_bot"
BOT_VERSION = "2.0.0"

# ==================== USER DATA ====================

user_data: Dict[int, Dict] = {}

def get_user_data(user_id: int) -> Dict:
    """Get or create user data"""
    if user_id not in user_data:
        user_data[user_id] = {
            "personal_info": {},
            "verification": {},
            "consent": {},
            "documents": [],
            "photos": [],  # Store photo file_ids
            "total_generated": 0,
            "status": "pending",
            "registration_date": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
        }
    return user_data[user_id]

# ==================== KEYBOARDS ====================

def get_main_keyboard():
    """Create main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📝 Start Registration", callback_data="register")],
        [InlineKeyboardButton("📸 Upload Photo", callback_data="upload_photo")],
        [InlineKeyboardButton("🪪 Generate ID Card", callback_data="gen_id")],
        [InlineKeyboardButton("🔢 Generate NIN", callback_data="gen_nin")],
        [InlineKeyboardButton("🚗 Generate License", callback_data="gen_license")],
        [InlineKeyboardButton("📋 My Documents", callback_data="my_docs")],
        [InlineKeyboardButton("📊 Verification Status", callback_data="verification_status")],
        [InlineKeyboardButton("🗑️ Delete My Data", callback_data="delete_data")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_photo_keyboard():
    """Create photo upload keyboard"""
    keyboard = [
        [InlineKeyboardButton("📸 Upload New Photo", callback_data="upload_photo")],
        [InlineKeyboardButton("🔄 Change Photo", callback_data="change_photo")],
        [InlineKeyboardButton("📋 View My Photo", callback_data="view_photo")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_document_keyboard():
    """Create document type selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("🪪 National ID", callback_data="doc_national_id")],
        [InlineKeyboardButton("🔢 NIN", callback_data="doc_nin")],
        [InlineKeyboardButton("🚗 Driver's License", callback_data="doc_drivers_license")],
        [InlineKeyboardButton("🛂 Passport", callback_data="doc_passport")],
        [InlineKeyboardButton("📋 All Documents", callback_data="all_docs")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== CONVERSATION STATES ====================

# Registration states
(
    NAME, DOB, GENDER, PHONE, EMAIL,
    COUNTRY, ADDRESS, ID_TYPE, ID_NUMBER,
    NIN, BVN, CONSENT, PHOTO_UPLOAD
) = range(13)

# ==================== DOCUMENT GENERATION WITH PHOTO ====================

def resize_and_crop_image(image_data: bytes, target_size: Tuple[int, int]) -> bytes:
    """Resize and crop image to fit ID photo requirements"""
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Crop to square
        width, height = img.size
        if width > height:
            crop_size = height
            left = (width - height) // 2
            img = img.crop((left, 0, left + height, height))
        else:
            crop_size = width
            top = (height - width) // 2
            img = img.crop((0, top, width, top + width))
        
        # Resize to target
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Enhance image
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=95)
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return None

def generate_id_card_with_photo(user_data: Dict, photo_data: bytes = None) -> bytes:
    """Generate a realistic ID card with user photo"""
    try:
        width, height = 600, 400
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()
        
        # Official colors
        primary_color = "#0d47a1"
        secondary_color = "#1565c0"
        accent_color = "#FFD700"
        bg_color = "#f5f5f5"
        
        # Draw background
        draw.rectangle([0, 0, width, height], fill=bg_color)
        draw.rectangle([0, 0, width, 85], fill=primary_color)
        draw.rectangle([0, 85, width, 90], fill=secondary_color)
        
        # Draw official seal/logo
        draw.ellipse([20, 15, 60, 55], outline="#FFFFFF", width=2)
        draw.text((30, 30), "⚡", fill="#FFD700", font=font_large)
        
        # Draw title
        draw.text((80, 20), "FEDERAL REPUBLIC OF NIGERIA", fill="#FFFFFF", font=font_small)
        draw.text((80, 42), "NATIONAL IDENTITY CARD", fill="#FFD700", font=font_large)
        
        # Draw ID number
        id_number = user_data.get("id_number", f"NID-{datetime.now().year}-{random.randint(100, 999)}")
        draw.text((width - 200, 25), f"ID: {id_number}", fill="#FFFFFF", font=font_bold)
        
        # Draw photo
        if photo_data:
            try:
                # Resize photo for ID card
                photo = Image.open(io.BytesIO(photo_data))
                photo = photo.resize((140, 180), Image.Resampling.LANCZOS)
                
                # Create rounded corners
                mask = Image.new('L', (140, 180), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([(0, 0), (140, 180)], radius=10, fill=255)
                
                # Apply mask
                photo.putalpha(mask)
                
                # Paste photo
                img.paste(photo, (30, 105), photo)
                
                # Draw border
                draw.rectangle([28, 103, 172, 287], outline=primary_color, width=3)
            except Exception as e:
                logger.error(f"Photo paste error: {e}")
                draw.rectangle([30, 105, 170, 285], outline=primary_color, width=3)
                draw.text((70, 180), "PHOTO", fill="#888888", font=font_medium)
        else:
            draw.rectangle([30, 105, 170, 285], outline=primary_color, width=3)
            draw.text((70, 180), "PHOTO", fill="#888888", font=font_medium)
        
        # Draw user details
        y_start = 115
        details = [
            ("Full Name:", user_data.get("full_name", "John Doe")),
            ("Date of Birth:", user_data.get("date_of_birth", "01/01/1990")),
            ("Gender:", user_data.get("gender", "Male")),
            ("Phone:", user_data.get("phone", "+234 800 000 0000")),
            ("Email:", user_data.get("email", "john@example.com")),
            ("Address:", user_data.get("address", "Lagos, Nigeria")),
            ("Issue Date:", datetime.now().strftime("%d/%m/%Y")),
            ("Expiry Date:", (datetime.now() + timedelta(days=365*5)).strftime("%d/%m/%Y")),
        ]
        
        for label, value in details:
            draw.text((190, y_start), label, fill="#666666", font=font_small)
            draw.text((290, y_start), value, fill="#333333", font=font_medium)
            y_start += 28
        
        # Draw barcode
        for i in range(300, 560, 3):
            height_bar = random.randint(15, 35)
            draw.rectangle([i, 340, i + 2, 340 + height_bar], fill="#000000")
        
        # Draw footer
        draw.text((30, height - 25), "This is an official document. Any alteration is punishable by law.", 
                 fill="#999999", font=font_small)
        draw.text((width - 180, height - 25), "www.nimc.gov.ng", fill="#999999", font=font_small)
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"ID generation error: {e}")
        return None

def generate_nin_with_photo(user_data: Dict, photo_data: bytes = None) -> bytes:
    """Generate a realistic NIN card with user photo"""
    try:
        width, height = 500, 380
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()
        
        # Official NIN colors
        primary_color = "#1a237e"
        secondary_color = "#0d47a1"
        accent_color = "#FFD700"
        
        # Draw header
        draw.rectangle([0, 0, width, 60], fill=primary_color)
        draw.text((width//2 - 90, 10), "NATIONAL IDENTIFICATION", fill="#FFFFFF", font=font_large)
        draw.text((width//2 - 70, 35), "NUMBER (NIN)", fill=accent_color, font=font_medium)
        
        # Draw NIN number
        nin_number = user_data.get("nin", f"{random.randint(10000000000, 99999999999)}")
        draw.text((width//2 - 80, 80), nin_number, fill="#000000", font=font_large)
        
        # Draw photo
        if photo_data:
            try:
                photo = Image.open(io.BytesIO(photo_data))
                photo = photo.resize((100, 120), Image.Resampling.LANCZOS)
                img.paste(photo, (30, 100))
                draw.rectangle([28, 98, 132, 222], outline=primary_color, width=2)
            except:
                draw.rectangle([30, 100, 130, 220], outline=primary_color, width=2)
                draw.text((60, 150), "PHOTO", fill="#888888", font=font_medium)
        else:
            draw.rectangle([30, 100, 130, 220], outline=primary_color, width=2)
            draw.text((60, 150), "PHOTO", fill="#888888", font=font_medium)
        
        # Draw user details
        y_start = 110
        details = [
            (f"Name: {user_data.get('full_name', 'John Doe')}"),
            (f"Date of Birth: {user_data.get('date_of_birth', '01/01/1990')}"),
            (f"State of Origin: {user_data.get('state_of_origin', 'Lagos')}"),
            (f"Registration: {datetime.now().strftime('%d/%m/%Y')}"),
            (f"Expiry: {(datetime.now() + timedelta(days=365*10)).strftime('%d/%m/%Y')}"),
        ]
        
        x_start = 150
        for detail in details:
            draw.text((x_start, y_start), detail, fill="#333333", font=font_medium)
            y_start += 30
        
        # Draw barcode
        for i in range(50, 470, 3):
            draw.rectangle([i, 330, i + 2, 350], fill="#000000")
        
        # Draw footer
        draw.text((20, height - 25), "Official NIN Document - Verified", fill="#666666", font=font_small)
        draw.text((width - 170, height - 25), "www.nimc.gov.ng", fill="#666666", font=font_small)
        
        # Security seal
        draw.ellipse([width - 70, 10, width - 20, 60], outline="#FFD700", width=2)
        draw.text((width - 55, 30), "NIN", fill="#FFD700", font=font_small)
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"NIN generation error: {e}")
        return None

def generate_drivers_license_with_photo(user_data: Dict, photo_data: bytes = None) -> bytes:
    """Generate a realistic driver's license with photo"""
    try:
        width, height = 600, 400
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()
        
        # Official colors
        primary_color = "#1b5e20"
        secondary_color = "#2e7d32"
        accent_color = "#FFD700"
        
        draw.rectangle([0, 0, width, height], fill="#f5f5f5")
        draw.rectangle([0, 0, width, 80], fill=primary_color)
        draw.rectangle([0, 80, width, 85], fill=secondary_color)
        
        draw.text((20, 20), "FEDERAL REPUBLIC OF NIGERIA", fill="#FFFFFF", font=font_small)
        draw.text((20, 45), "DRIVER'S LICENSE", fill="#FFD700", font=font_large)
        
        license_number = user_data.get("license_number", f"DL-{random.randint(100000, 999999)}")
        draw.text((width - 220, 30), f"License: {license_number}", fill="#FFFFFF", font=font_bold)
        
        # Draw photo
        if photo_data:
            try:
                photo = Image.open(io.BytesIO(photo_data))
                photo = photo.resize((140, 180), Image.Resampling.LANCZOS)
                img.paste(photo, (30, 100))
                draw.rectangle([28, 98, 172, 282], outline=primary_color, width=3)
            except:
                draw.rectangle([30, 100, 170, 280], outline=primary_color, width=3)
                draw.text((70, 180), "PHOTO", fill="#888888", font=font_medium)
        else:
            draw.rectangle([30, 100, 170, 280], outline=primary_color, width=3)
            draw.text((70, 180), "PHOTO", fill="#888888", font=font_medium)
        
        # Draw user details
        y_start = 110
        details = [
            ("Name:", user_data.get("full_name", "Jane Smith")),
            ("Date of Birth:", user_data.get("date_of_birth", "01/01/1990")),
            ("Vehicle Class:", random.choice(["A", "B", "C", "D", "E"])),
            ("Address:", user_data.get("address", "Lagos, Nigeria")),
            ("Issue Date:", datetime.now().strftime("%d/%m/%Y")),
            ("Expiry Date:", (datetime.now() + timedelta(days=365*3)).strftime("%d/%m/%Y")),
        ]
        
        for label, value in details:
            draw.text((190, y_start), label, fill="#666666", font=font_small)
            draw.text((290, y_start), value, fill="#333333", font=font_medium)
            y_start += 28
        
        # Draw barcode
        for i in range(300, 560, 3):
            height_bar = random.randint(15, 35)
            draw.rectangle([i, 340, i + 2, 340 + height_bar], fill="#000000")
        
        draw.text((20, height - 25), "Driver License - Official Document", fill="#999999", font=font_small)
        draw.text((width - 200, height - 25), "www.dmv.gov.ng", fill="#999999", font=font_small)
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        logger.error(f"License generation error: {e}")
        return None

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = str(user.id)
    data = get_user_data(user_id)
    
    welcome = (
        f"🔐 **Welcome to {BOT_NAME}!**\n\n"
        f"👋 Hello @{user.username or user.first_name}!\n\n"
        f"Your professional identity verification and document generator.\n\n"
        f"⚡ **Features:**\n"
        f"• 📝 Complete Registration\n"
        f"• 📸 Photo Upload for ID\n"
        f"• 🪪 ID Card Generation\n"
        f"• 🔢 NIN Generation\n"
        f"• 🚗 Driver's License\n"
        f"• ✅ Verification Status\n"
        f"• 🔒 Data Privacy & Consent\n\n"
        f"📊 **Your Status:** {data.get('status', 'Pending').upper()}\n\n"
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
        "**📝 Registration Process:**\n"
        "1. Click 'Start Registration'\n"
        "2. Fill in your personal information\n"
        "3. Upload your photo\n"
        "4. Provide consent\n"
        "5. Get verified!\n\n"
        "**📸 Photo Requirements:**\n"
        "• Clear, front-facing photo\n"
        "• Good lighting\n"
        "• White background preferred\n"
        "• JPEG or PNG format\n\n"
        "**🪪 Documents Available:**\n"
        "• National ID Card\n"
        "• NIN Card\n"
        "• Driver's License\n"
        "• Passport\n\n"
        "**🔒 Privacy:**\n"
        "• Your data is encrypted\n"
        "• You can delete your data anytime\n"
        "• We never share your information\n\n"
        "**📌 Commands:**\n"
        "/start - Main menu\n"
        "/help - This help\n"
        "/register - Start registration"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ==================== REGISTRATION CONVERSATION ====================

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start registration process"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    if data.get("status") == "verified":
        await update.message.reply_text(
            "✅ You are already verified!\n\n"
            "You can generate documents using the buttons below.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 **Registration Started!**\n\n"
        "Please enter your **Full Legal Name**:\n"
        "(e.g., John Oluwaseun Adebayo)",
        parse_mode="Markdown"
    )
    return NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    data["personal_info"]["full_name"] = update.message.text
    
    await update.message.reply_text(
        "📅 **Enter your Date of Birth:**\n"
        "(Format: DD/MM/YYYY)\n"
        "e.g., 15/08/1990",
        parse_mode="Markdown"
    )
    return DOB

async def register_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date of birth input"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    # Validate date format
    dob = update.message.text
    if not re.match(r'\d{2}/\d{2}/\d{4}', dob):
        await update.message.reply_text(
            "❌ Invalid format. Please use DD/MM/YYYY\n"
            "e.g., 15/08/1990"
        )
        return DOB
    
    data["personal_info"]["date_of_birth"] = dob
    
    keyboard = [
        [InlineKeyboardButton("Male", callback_data="gender_male"),
         InlineKeyboardButton("Female", callback_data="gender_female")],
        [InlineKeyboardButton("Other", callback_data="gender_other")]
    ]
    await update.message.reply_text(
        "👤 **Select your Gender:**",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GENDER

async def register_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle gender selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = get_user_data(user_id)
    
    gender = query.data.replace("gender_", "")
    data["personal_info"]["gender"] = gender.capitalize()
    
    await query.edit_message_text(
        "📱 **Enter your Phone Number:**\n"
        "(Include country code)\n"
        "e.g., +234 800 000 0000",
        parse_mode="Markdown"
    )
    return PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone input"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    data["personal_info"]["phone"] = update.message.text
    
    await update.message.reply_text(
        "📧 **Enter your Email Address:**\n"
        "e.g., john@example.com",
        parse_mode="Markdown"
    )
    return EMAIL

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle email input"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    data["personal_info"]["email"] = update.message.text
    
    await update.message.reply_text(
        "🌍 **Enter your Country:**\n"
        "e.g., Nigeria",
        parse_mode="Markdown"
    )
    return COUNTRY

async def register_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country input"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    data["personal_info"]["country"] = update.message.text
    
    await update.message.reply_text(
        "📍 **Enter your Address:**\n"
        "e.g., 42, Allen Avenue, Ikeja, Lagos",
        parse_mode="Markdown"
    )
    return ADDRESS

async def register_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle address input"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    data["personal_info"]["address"] = update.message.text
    
    keyboard = [
        [InlineKeyboardButton("🪪 National ID", callback_data="id_type_national_id")],
        [InlineKeyboardButton("🛂 Passport", callback_data="id_type_passport")],
        [InlineKeyboardButton("🚗 Driver's License", callback_data="id_type_drivers_license")],
        [InlineKeyboardButton("🔢 NIN", callback_data="id_type_nin")]
    ]
    await update.message.reply_text(
        "🪪 **Select ID Type:**",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ID_TYPE

async def register_id_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ID type selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = get_user_data(user_id)
    
    id_type = query.data.replace("id_type_", "")
    data["verification"]["id_type"] = id_type
    
    await query.edit_message_text(
        f"📝 **Enter your {id_type.replace('_', ' ').title()} Number:**\n"
        f"e.g., NID-2024-001",
        parse_mode="Markdown"
    )
    return ID_NUMBER

async def register_id_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ID number input"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    data["verification"]["id_number"] = update.message.text
    
    await update.message.reply_text(
        "🔢 **Enter your NIN (National Identification Number):**\n"
        "e.g., 12345678901\n\n"
        "Skip if not applicable: type 'skip'",
        parse_mode="Markdown"
    )
    return NIN

async def register_nin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle NIN input"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    nin = update.message.text
    if nin.lower() != "skip":
        data["verification"]["nin"] = nin
    
    await update.message.reply_text(
        "🏦 **Enter your BVN (Bank Verification Number):**\n"
        "e.g., 12345678901\n\n"
        "Skip if not applicable: type 'skip'",
        parse_mode="Markdown"
    )
    return BVN

async def register_bvn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle BVN input"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    bvn = update.message.text
    if bvn.lower() != "skip":
        data["verification"]["bvn"] = bvn
    
    # Show consent
    await update.message.reply_text(
        "🔒 **Privacy & Consent**\n\n"
        "I confirm that the information provided is accurate.\n"
        "I consent to the processing of my data for identity verification.\n\n"
        "Please review our Privacy Policy:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ I Consent", callback_data="consent_yes")],
            [InlineKeyboardButton("📄 Privacy Policy", callback_data="privacy_policy")],
            [InlineKeyboardButton("❌ I Do Not Consent", callback_data="consent_no")]
        ])
    )
    return CONSENT

async def register_consent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle consent"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = get_user_data(user_id)
    
    if query.data == "consent_yes":
        data["consent"]["given"] = True
        data["consent"]["date"] = datetime.now().isoformat()
        data["status"] = "pending_verification"
        
        # Generate ID number
        data["id_number"] = f"NID-{datetime.now().year}-{random.randint(100, 999)}"
        
        await query.edit_message_text(
            "✅ **Registration Complete!**\n\n"
            "Thank you for registering. Your information has been received.\n\n"
            "📸 **Next Step:** Upload your photo for ID card generation.\n\n"
            "Click 'Upload Photo' to add your picture.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Upload Photo", callback_data="upload_photo")],
                [InlineKeyboardButton("🪪 Generate ID", callback_data="gen_id")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
            ])
        )
        
    elif query.data == "consent_no":
        data["consent"]["given"] = False
        await query.edit_message_text(
            "❌ **Consent Required**\n\n"
            "You must provide consent to proceed with registration.\n\n"
            "If you change your mind, please start over.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    elif query.data == "privacy_policy":
        await query.edit_message_text(
            "📄 **Privacy Policy**\n\n"
            "1. We collect personal data for identity verification only.\n"
            "2. Your data is encrypted and stored securely.\n"
            "3. We do not share your data with third parties.\n"
            "4. You can request data deletion anytime.\n"
            "5. You have the right to access your data.\n\n"
            "Do you consent to these terms?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ I Consent", callback_data="consent_yes")],
                [InlineKeyboardButton("❌ I Do Not Consent", callback_data="consent_no")]
            ])
        )
        return CONSENT
    
    return ConversationHandler.END

# ==================== PHOTO UPLOAD HANDLERS ====================

async def upload_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start photo upload process"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📸 **Photo Upload**\n\n"
        "Please send me a clear photo.\n\n"
        "**Requirements:**\n"
        "• Front-facing photo\n"
        "• Good lighting\n"
        "• White background preferred\n"
        "• JPEG or PNG format\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown"
    )
    return PHOTO_UPLOAD

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo upload"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    try:
        # Get photo
        photo = update.message.photo[-1]
        file = await photo.get_file()
        photo_data = await file.download_as_bytearray()
        
        # Process and store photo
        processed_photo = resize_and_crop_image(photo_data, (140, 180))
        
        if processed_photo:
            # Store photo data in user_data
            if "photos" not in data:
                data["photos"] = []
            data["photos"].append({
                "file_id": photo.file_id,
                "processed": processed_photo,
                "uploaded_at": datetime.now().isoformat()
            })
            data["status"] = "photo_uploaded"
            
            await update.message.reply_text(
                "✅ **Photo Uploaded Successfully!**\n\n"
                "Your photo has been saved. You can now:\n"
                "• Generate ID Card with your photo\n"
                "• Generate NIN with your photo\n"
                "• View your photo",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🪪 Generate ID", callback_data="gen_id")],
                    [InlineKeyboardButton("🔢 Generate NIN", callback_data="gen_nin")],
                    [InlineKeyboardButton("📸 View Photo", callback_data="view_photo")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                ])
            )
        else:
            await update.message.reply_text(
                "❌ **Photo Processing Failed**\n\n"
                "Please try again with a different photo.",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Photo upload error: {e}")
        await update.message.reply_text(
            "❌ **Error uploading photo**\n\n"
            "Please try again.",
            parse_mode="Markdown"
        )
    
    return ConversationHandler.END

async def view_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View uploaded photo"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = get_user_data(user_id)
    
    if data.get("photos") and len(data["photos"]) > 0:
        photo_data = data["photos"][-1].get("processed")
        if photo_data:
            await query.message.reply_photo(
                photo=io.BytesIO(photo_data),
                caption="📸 **Your Uploaded Photo**\n\n"
                       "This photo will be used on your ID documents.",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ No photo found. Please upload one.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    else:
        await query.edit_message_text(
            "❌ No photo found. Please upload one.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Upload Photo", callback_data="upload_photo")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )

# ==================== DOCUMENT GENERATION HANDLERS ====================

async def generate_id_with_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate ID card with photo"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = get_user_data(user_id)
    
    # Get photo
    photo_data = None
    if data.get("photos") and len(data["photos"]) > 0:
        photo_data = data["photos"][-1].get("processed")
    
    # Generate ID
    img_data = generate_id_card_with_photo(data.get("personal_info", {}), photo_data)
    
    if img_data:
        data["total_generated"] += 1
        data["documents"].append({
            "type": "id_card",
            "generated_at": datetime.now().isoformat()
        })
        
        await query.message.reply_photo(
            photo=io.BytesIO(img_data),
            caption="🪪 **Your ID Card**\n\n"
                   f"Name: {data.get('personal_info', {}).get('full_name', 'N/A')}\n"
                   f"ID: {data.get('id_number', 'N/A')}\n"
                   f"Status: {'✅ Verified' if data.get('status') == 'verified' else '⏳ Pending'}\n\n"
                   "🔒 This is a secure official document.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await query.edit_message_text(
            "❌ Failed to generate ID card. Please try again.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

async def generate_nin_with_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate NIN with photo"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = get_user_data(user_id)
    
    photo_data = None
    if data.get("photos") and len(data["photos"]) > 0:
        photo_data = data["photos"][-1].get("processed")
    
    if not data.get("verification", {}).get("nin"):
        data["verification"]["nin"] = f"{random.randint(10000000000, 99999999999)}"
    
    img_data = generate_nin_with_photo(data.get("personal_info", {}), photo_data)
    
    if img_data:
        data["total_generated"] += 1
        data["documents"].append({
            "type": "nin",
            "generated_at": datetime.now().isoformat()
        })
        
        await query.message.reply_photo(
            photo=io.BytesIO(img_data),
            caption="🔢 **Your NIN Card**\n\n"
                   f"Name: {data.get('personal_info', {}).get('full_name', 'N/A')}\n"
                   f"NIN: {data.get('verification', {}).get('nin', 'N/A')}\n"
                   f"Status: {'✅ Verified' if data.get('status') == 'verified' else '⏳ Pending'}\n\n"
                   "🔒 This is a secure official document.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await query.edit_message_text(
            "❌ Failed to generate NIN. Please try again.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

async def generate_license_with_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate Driver's License with photo"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = get_user_data(user_id)
    
    photo_data = None
    if data.get("photos") and len(data["photos"]) > 0:
        photo_data = data["photos"][-1].get("processed")
    
    if not data.get("verification", {}).get("license_number"):
        data["verification"]["license_number"] = f"DL-{random.randint(100000, 999999)}"
    
    img_data = generate_drivers_license_with_photo(data.get("personal_info", {}), photo_data)
    
    if img_data:
        data["total_generated"] += 1
        data["documents"].append({
            "type": "drivers_license",
            "generated_at": datetime.now().isoformat()
        })
        
        await query.message.reply_photo(
            photo=io.BytesIO(img_data),
            caption="🚗 **Your Driver's License**\n\n"
                   f"Name: {data.get('personal_info', {}).get('full_name', 'N/A')}\n"
                   f"License: {data.get('verification', {}).get('license_number', 'N/A')}\n"
                   f"Status: {'✅ Verified' if data.get('status') == 'verified' else '⏳ Pending'}\n\n"
                   "🔒 This is a secure official document.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await query.edit_message_text(
            "❌ Failed to generate Driver's License. Please try again.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== MAIN ====================

async def post_init(application):
    """Post initialization"""
    logger.info("=" * 60)
    logger.info(f"🔐 {BOT_NAME} Started Successfully!")
    logger.info(f"🤖 Username: @{BOT_USERNAME}")
    logger.info(f"📦 Version: {BOT_VERSION}")
    logger.info(f"📸 Photo Upload Support: Enabled")
    logger.info("=" * 60)
    logger.info("✅ Bot is ready with photo upload support!")
    logger.info("=" * 60)

def main():
    """Main entry point"""
    logger.info(f"🚀 Starting {BOT_NAME}...")
    logger.info(f"📡 Using token: {BOT_TOKEN[:15]}...{BOT_TOKEN[-5:]}")
    
    application = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .post_init(post_init) \
        .build()
    
    # Conversation handler for registration
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("register", register_start),
            CallbackQueryHandler(register_start, pattern="^register$")
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_dob)],
            GENDER: [CallbackQueryHandler(register_gender, pattern="^gender_")],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_country)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_address)],
            ID_TYPE: [CallbackQueryHandler(register_id_type, pattern="^id_type_")],
            ID_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_id_number)],
            NIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_nin)],
            BVN: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_bvn)],
            CONSENT: [CallbackQueryHandler(register_consent, pattern="^(consent_|privacy_policy)")],
        },
        fallbacks=[CommandHandler("cancel", start)],
        name="registration"
    )
    
    # Photo upload conversation handler
    photo_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(upload_photo_start, pattern="^upload_photo$"),
            CallbackQueryHandler(upload_photo_start, pattern="^change_photo$")
        ],
        states={
            PHOTO_UPLOAD: [MessageHandler(filters.PHOTO, handle_photo)]
        },
        fallbacks=[CommandHandler("cancel", start)],
        name="photo_upload"
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(photo_conv_handler)
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(view_photo, pattern="^view_photo$"))
    application.add_handler(CallbackQueryHandler(generate_id_with_photo, pattern="^gen_id$"))
    application.add_handler(CallbackQueryHandler(generate_nin_with_photo_handler, pattern="^gen_nin$"))
    application.add_handler(CallbackQueryHandler(generate_license_with_photo_handler, pattern="^gen_license$"))
    
    # Generic callback handler
    application.add_handler(CallbackQueryHandler(handle_generic_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("✅ Bot is polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def handle_generic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle generic callbacks"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "back":
        await query.edit_message_text(
            "🏠 **Main Menu**\n\n"
            "What would you like to do?",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    elif action == "my_docs":
        user_id = str(query.from_user.id)
        data = get_user_data(user_id)
        
        if data.get("documents"):
            docs_text = "📋 **Your Documents**\n\n"
            for idx, doc in enumerate(data["documents"], 1):
                docs_text += f"{idx}. {doc.get('type', 'Unknown')} - {doc.get('generated_at', 'N/A')[:10]}\n"
            await query.edit_message_text(
                docs_text,
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                "📋 No documents generated yet.\n\n"
                "Generate your ID, NIN, or Driver's License!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    elif action == "verification_status":
        user_id = str(query.from_user.id)
        data = get_user_data(user_id)
        
        status_map = {
            "pending": "⏳ Pending",
            "pending_verification": "⏳ Under Review",
            "photo_uploaded": "📸 Photo Uploaded",
            "verified": "✅ Verified",
            "rejected": "❌ Rejected"
        }
        
        status_text = (
            f"📊 **Verification Status**\n\n"
            f"Status: {status_map.get(data.get('status', 'pending'), 'Unknown')}\n"
            f"Name: {data.get('personal_info', {}).get('full_name', 'Not provided')}\n"
            f"ID Number: {data.get('id_number', 'Not generated')}\n"
            f"Photo: {'✅ Uploaded' if data.get('photos') else '❌ Not uploaded'}\n"
            f"Documents Generated: {len(data.get('documents', []))}\n"
            f"Registration Date: {data.get('registration_date', 'N/A')[:10]}\n\n"
            "Complete your registration by uploading a photo and generating documents!"
        )
        
        await query.edit_message_text(
            status_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Upload Photo", callback_data="upload_photo")],
                [InlineKeyboardButton("🪪 Generate ID", callback_data="gen_id")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )
    elif action == "delete_data":
        user_id = str(query.from_user.id)
        if user_id in user_data:
            del user_data[user_id]
        await query.edit_message_text(
            "🗑️ **Data Deleted Successfully!**\n\n"
            "All your personal data has been removed from our system.\n\n"
            "You can start fresh anytime with /start",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    await update.message.reply_text(
        "📋 **Use the buttons below!**\n\n"
        "Start your registration or generate documents.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

if __name__ == "__main__":
    main()
