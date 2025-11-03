from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
import uuid
import shutil
from datetime import datetime, timezone
from ftplib import FTP
import io
from database import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create uploads directory
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# FTP Models
class FTPConfig(BaseModel):
    host: str
    port: str = "21"
    username: str
    password: str
    rootFolder: str = "/"
    publishOnlyChanges: bool = False

class BlockConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

class Block(BaseModel):
    id: str
    templateId: str
    config: Dict[str, Any]

class FTPUploadRequest(BaseModel):
    ftpConfig: FTPConfig
    blocks: List[Block]

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    result = await db.insert_status_check(input.client_name)
    return StatusCheck(**result)

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.get_status_checks()
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Image Upload endpoint
@api_router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image file and return the URL
    Accepts: jpg, jpeg, png, gif, webp
    """
    try:
        # Validate file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOADS_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return URL (relative to backend)
        file_url = f"/api/uploads/{unique_filename}"
        
        return {
            "success": True,
            "url": file_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Video Upload endpoint
@api_router.post("/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file and return the URL
    Accepts: mp4, webm, mov, avi, wmv
    """
    try:
        # Validate file extension
        allowed_extensions = {'.mp4', '.webm', '.mov', '.avi', '.wmv'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOADS_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return URL (relative to backend)
        file_url = f"/api/uploads/{unique_filename}"
        
        return {
            "success": True,
            "url": file_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# FTP Upload endpoint
@api_router.post("/ftp/upload")
async def upload_to_ftp(request: FTPUploadRequest):
    try:
        # Generate HTML from blocks
        html_content = generate_html_from_blocks(request.blocks)
        
        # Connect to FTP
        ftp = FTP()
        ftp.connect(request.ftpConfig.host, int(request.ftpConfig.port))
        ftp.login(request.ftpConfig.username, request.ftpConfig.password)
        
        # Change to root folder if specified
        if request.ftpConfig.rootFolder and request.ftpConfig.rootFolder != '/':
            try:
                ftp.cwd(request.ftpConfig.rootFolder)
            except Exception as e:
                logger.warning(f"Could not change to root folder {request.ftpConfig.rootFolder}: {e}")
        
        # Upload index.html
        html_bytes = html_content.encode('utf-8')
        html_file = io.BytesIO(html_bytes)
        ftp.storbinary('STOR index.html', html_file)
        
        # Close FTP connection
        ftp.quit()
        
        logger.info(f"Successfully uploaded site to FTP server: {request.ftpConfig.host}")
        
        return {
            "success": True,
            "message": "Site uploaded successfully",
            "files_uploaded": ["index.html"]
        }
        
    except Exception as e:
        logger.error(f"FTP upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"FTP upload failed: {str(e)}")

def generate_html_from_blocks(blocks: List[Block]) -> str:
    """Generate complete HTML from blocks"""
    
    # Template mapping (simplified - in production would load from templates)
    block_html_map = {
        "menu-1": '<nav class="bg-white shadow-md p-4"><div class="container mx-auto flex justify-between items-center"><div class="text-2xl font-bold">{{brandName}}</div><div class="space-x-4">{{menuItems}}</div></div></nav>',
        "menu-2": '<nav class="bg-gray-900 text-white p-4"><div class="container mx-auto flex justify-center items-center gap-8"><div class="text-xl font-bold">{{brandName}}</div><div class="space-x-6">{{menuItems}}</div></div></nav>',
        "menu-3": '<nav class="bg-transparent absolute w-full p-4 z-10"><div class="container mx-auto flex justify-between items-center"><div class="text-2xl font-bold text-white">{{brandName}}</div><div class="space-x-4 text-white">{{menuItems}}</div></div></nav>',
        "menu-4": '<nav class="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4"><div class="container mx-auto"><div class="text-2xl font-bold mb-4">{{brandName}}</div><div class="space-y-2">{{menuItems}}</div></div></nav>',
        "menu-5": '<nav class="bg-white border-b p-4"><div class="container mx-auto grid grid-cols-2 gap-8"><div><div class="font-bold mb-2">{{brandName}}</div></div><div class="text-right">{{menuItems}}</div></div></nav>',
        "menu-6": '<nav class="bg-gray-900 text-white p-6"><div class="container mx-auto flex justify-between items-center"><div class="text-xl tracking-wider">{{brandName}}</div><div class="space-x-8 text-sm uppercase">{{menuItems}}</div></div></nav>',
        
        "hero-1": '<section class="py-20 px-4" style="background-color: {{backgroundColor}}"><div class="container mx-auto" style="max-width: 1000px;"><div class="mb-12 rounded-xl overflow-hidden shadow-2xl"><img src="{{heroImage}}" alt="Hero image" style="width: 100%; height: 600px; object-fit: cover; display: block;"></div><div class="text-center"><h1 class="text-6xl font-bold mb-6" style="color: {{titleColor}}">{{title}}</h1><p class="text-xl mb-8" style="color: {{descriptionColor}}">{{description}}</p><button class="px-10 py-4 rounded-xl text-lg font-semibold transition-all hover:scale-105 shadow-lg" style="background-color: {{buttonBg}}; color: {{buttonColor}}">{{buttonText}}</button></div></div></section>',
        "hero-2": '<section class="relative h-screen flex items-center justify-center bg-gradient-to-r from-pink-500 to-orange-500 text-white"><div class="text-center z-10 px-4"><h1 class="text-7xl font-extrabold mb-6">{{headline}}</h1><p class="text-3xl mb-8">{{subheadline}}</p><button class="bg-white text-pink-600 px-10 py-5 rounded-lg text-xl font-bold hover:scale-105 transition">{{ctaText}}</button></div></section>',
        "hero-3": '<section class="relative h-screen flex items-center justify-center bg-black text-white"><video autoplay muted loop class="absolute inset-0 w-full h-full object-cover opacity-50"><source src="video.mp4" type="video/mp4"></video><div class="text-center z-10 px-4"><h1 class="text-6xl font-bold mb-6">{{headline}}</h1><p class="text-2xl mb-8">{{subheadline}}</p><button class="border-2 border-white px-8 py-4 rounded-full text-lg font-semibold hover:bg-white hover:text-black transition">{{ctaText}}</button></div></section>',
        "hero-4": '<section class="relative h-screen flex items-center justify-center bg-cover bg-center" style="background-image: url({{backgroundImage}});"><div class="absolute inset-0 bg-black opacity-40"></div><div class="text-center z-10 px-4 text-white"><h1 class="text-6xl font-bold mb-6">{{headline}}</h1><p class="text-2xl mb-8">{{subheadline}}</p><button class="bg-indigo-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-indigo-700 transition">{{ctaText}}</button></div></section>',
        "hero-5": '<section class="relative h-screen flex items-center justify-center overflow-hidden"><div class="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 animate-gradient"></div><div class="text-center z-10 px-4 text-white"><h1 class="text-7xl font-extrabold mb-6">{{headline}}</h1><p class="text-3xl mb-8">{{subheadline}}</p><button class="bg-white text-purple-600 px-10 py-5 rounded-full text-xl font-bold hover:scale-110 transition">{{ctaText}}</button></div></section>',
        "hero-6": '<section class="h-screen grid grid-cols-2"><div class="flex items-center justify-center bg-indigo-600 text-white p-12"><div><h1 class="text-5xl font-bold mb-6">{{headline}}</h1><p class="text-xl mb-8">{{subheadline}}</p><button class="bg-white text-indigo-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition">{{ctaText}}</button></div></div><div class="bg-cover bg-center" style="background-image: url({{backgroundImage}});"></div></section>',
        "hero-7": '<section class="h-screen flex items-center justify-center bg-white"><div class="text-center px-4"><h1 class="text-6xl font-light text-gray-900 mb-6">{{headline}}</h1><p class="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">{{subheadline}}</p><button class="bg-black text-white px-8 py-4 rounded text-lg hover:bg-gray-800 transition">{{ctaText}}</button></div></section>',
        "hero-8": '<section class="h-screen flex items-center justify-center bg-gray-900 text-white"><div class="text-center px-4"><h1 class="text-8xl font-black mb-6 uppercase">{{headline}}</h1><p class="text-2xl mb-8">{{subheadline}}</p><button class="bg-red-600 text-white px-12 py-5 rounded text-xl font-bold hover:bg-red-700 transition">{{ctaText}}</button></div></section>',
        "hero-9": '<section class="relative h-screen flex items-center justify-center bg-cover bg-center" style="background-image: url({{backgroundImage}});"><div class="absolute inset-0 bg-gradient-to-b from-transparent to-black opacity-70"></div><div class="text-center z-10 px-4 text-white"><h1 class="text-6xl font-bold mb-6">{{headline}}</h1><p class="text-2xl mb-8">{{subheadline}}</p><button class="bg-yellow-500 text-black px-8 py-4 rounded-full text-lg font-bold hover:bg-yellow-400 transition">{{ctaText}}</button></div></section>',
        "hero-10": '<section class="h-screen flex items-center justify-center bg-gradient-to-br from-teal-500 to-blue-600 text-white"><div class="text-center px-4"><h1 class="text-6xl font-bold mb-6">{{headline}}</h1><p class="text-2xl mb-8">{{subheadline}}</p><div class="flex gap-4 justify-center"><button class="bg-white text-teal-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-gray-100 transition">{{ctaText}}</button><button class="border-2 border-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white hover:text-teal-600 transition">Learn More</button></div></div></section>',
        
        # Generic fallback for other block types
        "default": '<section class="py-20 px-4"><div class="container mx-auto"><div class="text-center">{{content}}</div></div></section>'
    }
    
    html_blocks = []
    for block in blocks:
        template_html = block_html_map.get(block.templateId, block_html_map["default"])
        
        # Special handling for hero-1 (image-above-text layout)
        if block.templateId == "hero-1":
            template_html = template_html.replace('{{heroImage}}', block.config.get('heroImage', {}).get('src', ''))
            template_html = template_html.replace('{{backgroundColor}}', block.config.get('background', {}).get('value', '#F5F5F0'))
            template_html = template_html.replace('{{title}}', block.config.get('title', {}).get('text', ''))
            template_html = template_html.replace('{{titleColor}}', block.config.get('title', {}).get('color', '#2B2B2B'))
            template_html = template_html.replace('{{description}}', block.config.get('description', {}).get('text', ''))
            template_html = template_html.replace('{{descriptionColor}}', block.config.get('description', {}).get('color', '#6B6B6B'))
            template_html = template_html.replace('{{buttonText}}', block.config.get('button', {}).get('text', ''))
            template_html = template_html.replace('{{buttonBg}}', block.config.get('button', {}).get('color', '#A8F5B8'))
            template_html = template_html.replace('{{buttonColor}}', block.config.get('button', {}).get('textColor', '#2B2B2B'))
        else:
            # Replace placeholders with actual config values for other blocks
            for key, value in block.config.items():
                placeholder = f"{{{{{key}}}}}"
                template_html = template_html.replace(placeholder, str(value))
        
        html_blocks.append(template_html)
    
    # Combine all blocks into full HTML document
    full_html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Site creat cu Mobirise Builder</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        @keyframes gradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        .animate-gradient {{
            background-size: 200% 200%;
            animation: gradient 15s ease infinite;
        }}
    </style>
</head>
<body>
    {"".join(html_blocks)}
</body>
</html>"""
    
    return full_html


# ============ PAGES API ENDPOINTS ============

class PageCreate(BaseModel):
    project_id: str
    name: str
    blocks: List[Dict[str, Any]] = []
    is_home: bool = False

class PageUpdate(BaseModel):
    name: str = None
    blocks: List[Dict[str, Any]] = None
    is_home: bool = None

class PageDuplicate(BaseModel):
    new_name: str

class SharedMenuUpdate(BaseModel):
    shared_menu: Dict[str, Any]

@api_router.post("/pages")
async def create_page(page_data: PageCreate):
    """Create a new page"""
    try:
        page = await db.create_page(
            project_id=page_data.project_id,
            name=page_data.name,
            blocks=page_data.blocks,
            is_home=page_data.is_home
        )
        return page
    except Exception as e:
        logger.error(f"Error creating page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/pages/{project_id}")
async def get_pages(project_id: str):
    """Get all pages for a project"""
    try:
        pages = await db.get_pages(project_id)
        return pages
    except Exception as e:
        logger.error(f"Error getting pages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/page/{page_id}")
async def get_page(page_id: str):
    """Get a specific page"""
    try:
        page = await db.get_page(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return page
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/page/{page_id}")
async def update_page(page_id: str, page_data: PageUpdate):
    """Update a page"""
    try:
        page = await db.update_page(
            page_id=page_id,
            name=page_data.name,
            blocks=page_data.blocks,
            is_home=page_data.is_home
        )
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return page
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/page/{page_id}")
async def delete_page(page_id: str):
    """Delete a page"""
    try:
        deleted = await db.delete_page(page_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Page not found")
        return {"success": True, "message": "Page deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/page/{page_id}/duplicate")
async def duplicate_page(page_id: str, data: PageDuplicate):
    """Duplicate a page"""
    try:
        page = await db.duplicate_page(page_id, data.new_name)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        return page
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating page: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/project/{project_id}/shared-menu")
async def update_shared_menu(project_id: str, data: SharedMenuUpdate):
    """Update shared menu for a project"""
    try:
        updated = await db.update_shared_menu(project_id, data.shared_menu)
        if not updated:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "message": "Shared menu updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating shared menu: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/project/{project_id}/shared-menu")
async def get_shared_menu(project_id: str):
    """Get shared menu for a project"""
    try:
        menu = await db.get_shared_menu(project_id)
        return {"shared_menu": menu}
    except Exception as e:
        logger.error(f"Error getting shared menu: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ SETTINGS API ENDPOINTS ============

class SettingsData(BaseModel):
    site_name: str = None
    site_description: str = None
    site_logo: str = None
    favicon: str = None
    meta_title: str = None
    meta_description: str = None
    meta_keywords: str = None
    og_title: str = None
    og_description: str = None
    og_image: str = None
    google_analytics_id: str = None
    facebook_pixel_id: str = None
    custom_css: str = None
    custom_js: str = None
    header_scripts: str = None
    footer_scripts: str = None
    primary_font: str = None
    primary_color: str = None
    secondary_color: str = None
    accent_color: str = None
    border_radius: str = None
    spacing: str = None

@api_router.get("/settings/{project_id}")
async def get_settings(project_id: str):
    """Get settings for a project"""
    try:
        settings = await db.get_settings(project_id)
        if not settings:
            # Return default settings if none exist
            return {
                "project_id": project_id,
                "site_name": "",
                "site_description": "",
                "site_logo": "",
                "favicon": "",
                "meta_title": "",
                "meta_description": "",
                "meta_keywords": "",
                "og_title": "",
                "og_description": "",
                "og_image": "",
                "google_analytics_id": "",
                "facebook_pixel_id": "",
                "custom_css": "",
                "custom_js": "",
                "header_scripts": "",
                "footer_scripts": "",
                "primary_font": "Inter",
                "primary_color": "#3B82F6",
                "secondary_color": "#6B7280",
                "accent_color": "#10B981",
                "border_radius": "8px",
                "spacing": "16px"
            }
        return settings
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/settings/{project_id}")
async def save_settings(project_id: str, settings_data: SettingsData):
    """Save or update settings for a project"""
    try:
        # Convert to dict and remove None values
        settings_dict = {k: v for k, v in settings_data.dict().items() if v is not None}
        
        settings = await db.save_settings(project_id, settings_dict)
        if not settings:
            raise HTTPException(status_code=500, detail="Failed to save settings")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Email Configuration (can be configured via environment variables)
def send_email_notification(to_email: str, subject: str, body_html: str):
    """Send email notification using SMTP"""
    try:
        # Email configuration from environment variables
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        from_email = os.getenv('FROM_EMAIL', smtp_user)
        
        # If SMTP credentials are not configured, skip email sending
        if not smtp_user or not smtp_password:
            logger.warning("SMTP credentials not configured. Email notification skipped.")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Create HTML part
        html_part = MIMEText(body_html, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


# Contact Form Submission
class ContactFormData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    message: str
    notification_email: Optional[str] = None

@api_router.post("/contact/submit")
async def submit_contact_form(form_data: ContactFormData):
    """Handle contact form submission"""
    try:
        logger.info(f"Contact form submitted: {form_data.name} ({form_data.email})")
        
        # Send email notification if notification_email is provided
        email_sent = False
        if form_data.notification_email:
            subject = f"New Contact Form Submission from {form_data.name}"
            body_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #4F46E5; margin-bottom: 20px;">New Contact Form Submission</h2>
                        <div style="background-color: #F9FAFB; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                            <p style="margin: 10px 0;"><strong style="color: #374151;">Name:</strong> {form_data.name}</p>
                            <p style="margin: 10px 0;"><strong style="color: #374151;">Email:</strong> <a href="mailto:{form_data.email}" style="color: #4F46E5;">{form_data.email}</a></p>
                            {f'<p style="margin: 10px 0;"><strong style="color: #374151;">Phone:</strong> {form_data.phone}</p>' if form_data.phone else ''}
                        </div>
                        <div style="background-color: #F9FAFB; padding: 20px; border-radius: 8px;">
                            <p style="margin: 0 0 10px 0;"><strong style="color: #374151;">Message:</strong></p>
                            <p style="margin: 0; color: #6B7280; line-height: 1.6;">{form_data.message}</p>
                        </div>
                        <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 20px 0;">
                        <p style="color: #9CA3AF; font-size: 12px; text-align: center; margin: 0;">
                            This message was sent from your website contact form
                        </p>
                    </div>
                </body>
            </html>
            """
            email_sent = send_email_notification(form_data.notification_email, subject, body_html)
        
        return {
            "success": True,
            "message": "Form submitted successfully",
            "email_sent": email_sent,
            "data": {
                "name": form_data.name,
                "email": form_data.email
            }
        }
    except Exception as e:
        logger.error(f"Error submitting contact form: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit form")


# Include the router in the main app
app.include_router(api_router)

# Mount uploads directory for serving uploaded images
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Application shutting down")