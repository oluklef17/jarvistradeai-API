from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, case
from typing import List, Optional
import uvicorn
import json
from datetime import datetime, timedelta
import aiohttp
import os
from dotenv import load_dotenv
import uuid
import shutil
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel, Field
from pathlib import Path

load_dotenv()

# Import logging configuration
# WARNING: Do NOT redefine these loggers in functions - use the imported instances directly
from logging_config import (
    app_logger, auth_logger, payment_logger, access_logger, security_logger,
    file_logger, user_logger, product_logger, download_logger, notification_logger,
    blog_logger, project_logger, review_logger, exchange_rate_logger
)

from logging_config import get_logger, safe_log

from database import engine, get_db, Base
from models_mysql import Product, User, Transaction, OrderItem, DownloadToken, DownloadLog, Review, ProjectRequest, BlogPost, BlogLike, BlogComment, Notification, ExchangeRate, ProjectResponse, ProjectInvoice, ProjectProgress, UserProductActivation, License
from license_encryption import LicenseEncryption, LicenseSystem, create_license_data, verify_account_in_license, check_license_expiry, get_license_info
from schemas import (
    ProductCreate, ProductUpdate, ProductResponse, UserResponse, CategoryResponse, 
    PRODUCT_CATEGORIES, ReviewCreate, ReviewUpdate, ReviewResponse, 
    ProjectRequestCreate, ProjectRequestUpdate, ProjectRequestResponse, 
    BlogPostCreate, BlogPostUpdate, BlogPostResponse, BlogLikeResponse, 
    NotificationCreate, NotificationUpdate, NotificationResponse, 
    BlogCommentResponse, BlogCommentCreate, BlogCommentUpdate, 
    NotificationPreferencesResponse, NotificationPreferencesUpdate, 
    ExchangeRateCreate, ExchangeRateUpdate, ExchangeRateResponse,
    ProjectResponseCreate, ProjectResponseUpdate, ProjectResponseResponse,
    ProjectInvoiceCreate, ProjectInvoiceUpdate, ProjectInvoiceResponse,
    ProjectProgressCreate, ProjectProgressUpdate, ProjectProgressResponse,
    ProjectDashboardData,
    UserCreate, UserUpdate,
    ProductBase,
    ForgotPasswordRequest, ResetPasswordRequest, PasswordResetResponse,

    ExchangeRateCreate, ExchangeRateResponse,
    UserProductActivationCreate, UserProductActivationResponse, ProductActivationInfo, LicenseResponse, LicenseActivationInfo, AccountVerificationRequest, AccountVerificationResponse
)
from auth import get_current_user, get_current_user_optional, create_access_token, verify_token, get_password_hash, verify_password, authenticate_user
from payment_service import payment_service
from email_service import email_service

origins = [
    os.getenv('FRONTEND_URL', 'http://localhost:3000'),  # React dev server
    # You can add more allowed origins here
]

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers first (for proxy/load balancer setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    return request.client.host

async def get_user_country(request: Request) -> str:
    """Get user's country using IP geolocation"""
    try:
        client_ip = get_client_ip(request)

        if client_ip in ['127.0.0.1', 'localhost']:
            return "NG"
        
        # Use ipapi.co for geolocation (free tier available)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://ipapi.co/{client_ip}/json/", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    country_code = data.get("country_code", "US")
                    app_logger.info(f"IP: {client_ip}, Country: {country_code}")
                    return country_code
                else:
                    app_logger.warning(f"Geolocation API error: {response.status}")
                    return "US"  # Default to US
            
    except Exception as e:
        app_logger.error(f"Error getting user country: {e}")
        return "US"  # Default to US

def determine_payment_currency(country_code: str) -> str:
    """Determine payment currency based on country"""
    if country_code == "NG":
        return "NGN"
    else:
        return "USD"

def convert_blog_post_json_fields(post):
    """Convert JSON string fields back to lists for blog post responses"""
    # Convert tags from JSON string to list
    if post.tags:
        try:
            post.tags = json.loads(post.tags)
        except:
            post.tags = []
    else:
        post.tags = []
    
    # Convert youtube_links from JSON string to list
    if post.youtube_links:
        try:
            post.youtube_links = json.loads(post.youtube_links)
        except:
            post.youtube_links = []
    else:
        post.youtube_links = []
    
    # Convert attached_files from JSON string to list
    if post.attached_files:
        try:
            post.attached_files = json.loads(post.attached_files)
        except:
            post.attached_files = []
    else:
        post.attached_files = []
    
    # Convert gallery_images from JSON string to list
    if post.gallery_images:
        try:
            post.gallery_images = json.loads(post.gallery_images)
        except:
            post.gallery_images = []
    else:
        post.gallery_images = []
    
    return post

def convert_product_json_fields(product):
    """Convert JSON string fields back to lists for product responses"""
    # Convert tags from JSON string to list
    if product.tags:
        try:
            product.tags = json.loads(product.tags)
        except:
            product.tags = []
    else:
        product.tags = []
    
    # Convert features from JSON string to list
    if product.features:
        try:
            product.features = json.loads(product.features)
        except:
            product.features = []
    else:
        product.features = []
    
    # Convert images from JSON string to list
    if product.images:
        try:
            product.images = json.loads(product.images)
        except:
            product.images = []
    else:
        product.images = []
    
    return product

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory
os.makedirs("./uploads/products", exist_ok=True)

app = FastAPI(
    title="JarvisTrade API",
    description="Backend API for JarvisTrade - Premium Trading Tools & Professional Services",
    version="1.0.0"
)

# Custom static file handler with CORS headers
from fastapi.responses import FileResponse
from pathlib import Path

@app.get("/uploads/{file_path:path}")
async def serve_uploaded_file(file_path: str):
    """Serve uploaded files with CORS headers"""
    file_location = Path("uploads") / file_path
    if file_location.exists():
        return FileResponse(
            path=str(file_location),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*"
            }
        )
    else:
        raise HTTPException(status_code=404, detail="File not found")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
            allow_origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000'), "http://127.0.0.1:3000", "https://jarvistrade.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Security
security = HTTPBearer()

@app.get("/")
async def root():
    return {"message": "JarvisTrade API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Image upload endpoint
@app.post("/api/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload an image for product (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )
    
    # Validate file size (5MB limit)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 5MB"
        )
    
    try:
        # Create unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("./uploads/products", unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return the URL with full backend URL
        base_url = "http://localhost:8000"
        image_url = f"{base_url}/uploads/products/{unique_filename}"
        
        return {
            "success": True,
            "image_url": image_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        file_logger.error(f"Image upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload image"
        )

@app.post("/api/upload-product-file")
async def upload_product_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a digital product file (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Validate file size (100MB limit for product files)
    if file.size > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 100MB"
        )
    
    # Create uploads/products directory if it doesn't exist
    os.makedirs("./uploads/products", exist_ok=True)
    
    try:
        # Create unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("./uploads/products", unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Return the file path and size
        return {
            "success": True,
            "file_path": file_path,
            "filename": unique_filename,
            "file_size": file_size,
            "original_filename": file.filename
        }
        
    except Exception as e:
        file_logger.error(f"Product file upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload product file"
        )

# Project Request endpoints
@app.post("/api/project-requests", response_model=ProjectRequestResponse, status_code=201)
async def create_project_request(
    project_request: ProjectRequestCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Create a new project request"""
    try:
        # Convert lists to JSON strings for SQLite compatibility
        project_data = project_request.dict()
        project_data['platforms'] = json.dumps(project_data['platforms'])
        project_data['file_uploads'] = json.dumps(project_data.get('file_uploads', []))
        
        # Set user_id if user is logged in
        if current_user:
            project_data['user_id'] = current_user.id
        
        db_project_request = ProjectRequest(**project_data)
        db.add(db_project_request)
        db.commit()
        db.refresh(db_project_request)
        
        # Send email notifications
        try:
            # Send confirmation to user
            await email_service.send_project_request_confirmation(
                project_request.contact_email,
                project_request.project_title
            )
            
            # Send notification to admin
            admin_email = os.getenv("ADMIN_EMAIL", "admin@jarvistrade.com")
            await email_service.send_project_request_notification(
                admin_email,
                db_project_request
            )
        except Exception as e:
            notification_logger.error(f"Email notification error: {e}")
        
        # Create notification for project request submission
        if current_user:
            create_notification(
                db=db,
                user_id=current_user.id,
                title="Project Request Submitted",
                message=f"Your project request '{db_project_request.project_title}' has been submitted successfully. We'll review it and get back to you soon.",
                notification_type="info",
                data={"project_request_id": db_project_request.id, "title": db_project_request.project_title}
            )
            
            # Also notify admins about new project request
            admin_users = db.query(User).filter(User.is_admin == True).all()
            for admin in admin_users:
                create_notification(
                    db=db,
                    user_id=admin.id,
                    title="New Project Request",
                    message=f"New project request: '{db_project_request.project_title}' from {current_user.name}",
                    notification_type="system",
                    data={"project_request_id": db_project_request.id, "user_id": current_user.id, "title": db_project_request.project_title}
                )
        
        return db_project_request
        
    except Exception as e:
        project_logger.error(f"Project request creation error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create project request"
        )

@app.get("/api/project-requests", response_model=List[ProjectRequestResponse])
async def get_project_requests(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project requests (Admin only)"""
    
    if not current_user.is_admin:
        security_logger.warning(f"Unauthorized admin access attempt by user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    security_logger.info(f"Admin user {current_user.id} accessed project requests")
    query = db.query(ProjectRequest)
    
    if status:
        query = query.filter(ProjectRequest.status == status)
    
    project_requests = query.order_by(ProjectRequest.created_at.desc()).offset(skip).limit(limit).all()
    access_logger.info(f"Admin {current_user.id} found {len(project_requests)} project requests")
    return project_requests

@app.get("/api/project-requests/{request_id}", response_model=ProjectRequestResponse)
async def get_project_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project request (Admin or owner only)"""
    project_request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not project_request:
        raise HTTPException(status_code=404, detail="Project request not found")
    
    # Check if user is admin or the owner
    if not current_user.is_admin and project_request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return project_request

@app.put("/api/project-requests/{request_id}", response_model=ProjectRequestResponse)
async def update_project_request(
    request_id: str,
    project_update: ProjectRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project request (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db_project_request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not db_project_request:
        raise HTTPException(status_code=404, detail="Project request not found")
    
    update_data = project_update.dict(exclude_unset=True)
    
    # Convert lists to JSON strings for SQLite compatibility
    if 'platforms' in update_data:
        update_data['platforms'] = json.dumps(update_data['platforms'])
    
    for field, value in update_data.items():
        setattr(db_project_request, field, value)
    
    db.commit()
    db.refresh(db_project_request)
    
    # Send notification to user about project request update
    if db_project_request.user_id:
        user = db.query(User).filter(User.id == db_project_request.user_id).first()
        if user:
            status_message = {
                "In Progress": "Your project request is now being worked on.",
                "Completed": "Your project request has been completed!",
                "Cancelled": "Your project request has been cancelled.",
                "Pending Review": "Your project request is under review."
            }.get(db_project_request.status, f"Your project request status has been updated to {db_project_request.status}.")
            
            create_notification(
                db=db,
                user_id=user.id,
                title=f"Project Request Update: {db_project_request.project_title}",
                message=status_message,
                notification_type="order",
                data={"project_request_id": db_project_request.id, "status": db_project_request.status, "title": db_project_request.project_title}
            )
    
    return db_project_request

@app.delete("/api/project-requests/{request_id}")
async def delete_project_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project request (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    project_request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not project_request:
        raise HTTPException(status_code=404, detail="Project request not found")
    
    db.delete(project_request)
    db.commit()
    
    return {"message": "Project request deleted successfully"}

@app.post("/api/project-requests/{request_id}/upload")
async def upload_project_files(
    request_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload files for a project request (Admin or owner only)"""
    project_request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not project_request:
        raise HTTPException(status_code=404, detail="Project request not found")
    
    # Check if user is admin or the owner
    if not current_user.is_admin and project_request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/project-requests")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        if file.filename:
            # Generate unique filename
            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = upload_dir / unique_filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            uploaded_files.append({
                "filename": file.filename,
                "file_path": str(file_path),
                "size": len(content)
            })
    
    return {
        "message": f"Successfully uploaded {len(uploaded_files)} files",
        "files": uploaded_files
    }

# Admin-specific project request endpoints
@app.get("/api/admin/project-requests", response_model=List[ProjectRequestResponse])
async def get_admin_project_requests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",  # created_at, project_title, status
    sort_order: Optional[str] = "desc",  # asc, desc
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all project requests for admin (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = db.query(ProjectRequest)
    
    # Apply filters
    if status:
        query = query.filter(ProjectRequest.status == status)
    
    if search:
        search_filter = or_(
            ProjectRequest.project_title.ilike(f"%{search}%"),
            ProjectRequest.description.ilike(f"%{search}%"),
            ProjectRequest.contact_email.ilike(f"%{search}%"),
            ProjectRequest.telegram_handle.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Apply sorting
    if sort_by == "project_title":
        order_column = ProjectRequest.project_title
    elif sort_by == "status":
        order_column = ProjectRequest.status
    else:  # default to created_at
        order_column = ProjectRequest.created_at
    
    if sort_order == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())
    
    # Apply pagination
    project_requests = query.offset(skip).limit(limit).all()
    
    return project_requests

@app.get("/api/admin/project-requests/{request_id}", response_model=ProjectRequestResponse)
async def get_admin_project_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project request for admin (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    project_request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not project_request:
        raise HTTPException(status_code=404, detail="Project request not found")
    
    return project_request

@app.put("/api/admin/project-requests/{request_id}", response_model=ProjectRequestResponse)
async def update_admin_project_request(
    request_id: str,
    project_update: ProjectRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project request (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db_project_request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not db_project_request:
        raise HTTPException(status_code=404, detail="Project request not found")
    
    update_data = project_update.dict(exclude_unset=True)
    
    # Convert lists to JSON strings for SQLite compatibility
    if 'platforms' in update_data:
        update_data['platforms'] = json.dumps(update_data['platforms'])
    
    for field, value in update_data.items():
        setattr(db_project_request, field, value)
    
    db.commit()
    db.refresh(db_project_request)
    
    # Send notification to user about project request update
    if db_project_request.user_id:
        user = db.query(User).filter(User.id == db_project_request.user_id).first()
        if user:
            status_message = {
                "In Progress": "Your project request is now being worked on.",
                "Completed": "Your project request has been completed!",
                "Cancelled": "Your project request has been cancelled.",
                "Pending Review": "Your project request is under review."
            }.get(db_project_request.status, f"Your project request status has been updated to {db_project_request.status}.")
            
            create_notification(
                db=db,
                user_id=user.id,
                title=f"Project Request Update: {db_project_request.project_title}",
                message=status_message,
                notification_type="order",
                data={"project_request_id": db_project_request.id, "status": db_project_request.status, "title": db_project_request.project_title}
            )
    
    return db_project_request

@app.delete("/api/admin/project-requests/{request_id}")
async def delete_admin_project_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project request (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    project_request = db.query(ProjectRequest).filter(ProjectRequest.id == request_id).first()
    if not project_request:
        raise HTTPException(status_code=404, detail="Project request not found")
    
    db.delete(project_request)
    db.commit()
    
    return {"message": "Project request deleted successfully"}

# Payment verification endpoint
@app.get("/api/payment/verify/{reference}")
async def verify_payment(
    reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify payment with Paystack and update transaction status"""
    try:
        # Find existing transaction
        transaction = db.query(Transaction).filter(
            Transaction.paystack_reference == reference,
            Transaction.user_id == current_user.id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Verify payment with Paystack
        verification_result = await payment_service.verify_payment(reference)
        
        if not verification_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Payment verification failed: {verification_result['error']}"
            )
        
        # Update transaction status based on Paystack response
        paystack_status = verification_result["data"]["status"]
        transaction.status = paystack_status
        transaction.payment_data = json.dumps(verification_result["data"])
        db.commit()
        
        safe_log("payment", "info", f"Transaction {reference} status updated to: {paystack_status}")
        
        # If payment is successful, process the payment
        if paystack_status == "success":
            result = payment_service.process_successful_payment(db, reference, current_user)
            
            safe_log("payment", "info", f"Payment status: {paystack_status}")
            safe_log("payment", "info", f"Processing result: {result}")
            
            if result["success"]:
                # Format amount based on the actual transaction currency
                formatted_amount = format_currency_for_notification(
                    transaction.amount, 
                    transaction.currency,  # Use actual transaction currency
                    current_user.currency or transaction.currency, 
                    db
                )
                
                # Create notification for successful payment
                create_notification(
                    db=db,
                    user_id=current_user.id,
                    title="Payment Successful!",
                    message=f"Your payment of {formatted_amount} has been processed successfully. You can now download your purchased products.",
                    notification_type="payment",
                    data={"transaction_id": transaction.id, "amount": transaction.amount}
                )
                
                return {
                    "success": True,
                    "message": "Payment verified and processed successfully",
                    "status": paystack_status,
                    "download_token": result.get("download_token")
                }
            else:
                # Only show processing error if payment was actually successful but processing failed
                # This means the payment went through but there was an issue with order processing
                error_message = result.get("error", "Unknown processing error")
                safe_log("payment", "error", f"Payment processing failed: {error_message}")
                
                # Format amount based on the actual transaction currency
                formatted_amount = format_currency_for_notification(
                    transaction.amount, 
                    transaction.currency,  # Use actual transaction currency
                    current_user.currency or transaction.currency, 
                    db
                )
                
                create_notification(
                    db=db,
                    user_id=current_user.id,
                    title="Payment Received - Processing Issue",
                    message=f"Your payment of {formatted_amount} was received successfully, but there was an issue processing your order. Our team has been notified and will resolve this shortly.",
                    notification_type="warning",
                    data={"transaction_id": transaction.id, "amount": transaction.amount, "error": error_message}
                )
                
                return {
                    "success": False,
                    "message": "Payment received but processing failed - our team will contact you",
                    "status": paystack_status,
                    "error": error_message
                }
        elif paystack_status == "failed":
            # Format amount based on the actual transaction currency
            formatted_amount = format_currency_for_notification(
                transaction.amount, 
                transaction.currency,  # Use actual transaction currency
                current_user.currency or transaction.currency, 
                db
            )
            
            # Create notification for failed payment
            create_notification(
                db=db,
                user_id=current_user.id,
                title="Payment Failed",
                message=f"Your payment of {formatted_amount} was not successful. Please try again or contact support if the issue persists.",
                notification_type="error",
                data={"transaction_id": transaction.id, "amount": transaction.amount, "status": paystack_status}
            )
            
            return {
                "success": False,
                "message": "Payment failed",
                "status": paystack_status
            }
        else:
            return {
                "success": True,
                "message": f"Payment status: {paystack_status}",
                "status": paystack_status
            }
            
    except HTTPException:
        raise
    except Exception as e:
        safe_log("payment", "error", f"Payment verification error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to verify payment"
        )

# Manual payment verification endpoint for dashboard
@app.post("/api/payment/verify-manual/{reference}")
async def verify_payment_manual(
    reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually verify payment status from dashboard"""
    try:
        # Find existing transaction
        transaction = db.query(Transaction).filter(
            Transaction.paystack_reference == reference,
            Transaction.user_id == current_user.id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Verify payment with Paystack
        verification_result = await payment_service.verify_payment(reference)
        
        if not verification_result["success"]:
            return {
                "success": False,
                "message": f"Payment verification failed: {verification_result['error']}",
                "status": "verification_failed"
            }
        
        # Update transaction status based on Paystack response
        paystack_status = verification_result["data"]["status"]
        old_status = transaction.status
        
        # Extract verification log from Paystack response
        verification_log = ""
        if "log" in verification_result["data"] and verification_result["data"]["log"] is not None and "history" in verification_result["data"]["log"]:
            log_history = verification_result["data"]["log"]["history"]
            verification_log = " | ".join([item.get("message", "") for item in log_history if item.get("message")])
        elif "gateway_response" in verification_result["data"]:
            # For abandoned payments, use gateway_response as the log
            verification_log = verification_result["data"]["gateway_response"]
        
        # Only update status if it's a definitive status from Paystack
        # Don't revert successful payments back to pending
        if paystack_status in ["success", "failed", "abandoned"]:
            # Don't update if current status is already success and Paystack returns success
            if not (transaction.status == "success" and paystack_status == "success"):
                transaction.status = paystack_status
                # Store both the full verification data and the extracted log
                transaction.payment_data = json.dumps({
                    **verification_result["data"],
                    "verification_log": verification_log,
                    "verified_at": datetime.now().isoformat()
                })
                db.commit()
                safe_log("payment", "info", f"Transaction {reference} status updated from {old_status} to: {paystack_status}")
                safe_log("payment", "info", f"Verification log saved: {verification_log}")
            else:
                safe_log("payment", "info", f"Transaction {reference} already successful, no update needed")
        else:
            safe_log("payment", "info", f"Transaction {reference} status remains {old_status}, Paystack returned: {paystack_status}")
        
        # If payment is successful, process the payment
        if paystack_status == "success":
            result = payment_service.process_successful_payment(db, reference, current_user)
            
            if result["success"]:
                # Format amount based on the actual transaction currency
                formatted_amount = format_currency_for_notification(
                    transaction.amount, 
                    transaction.currency,  # Use actual transaction currency
                    current_user.currency or transaction.currency, 
                    db
                )
                
                # Create notification for successful payment
                create_notification(
                    db=db,
                    user_id=current_user.id,
                    title="Payment Successful!",
                    message=f"Your payment of {formatted_amount} has been processed successfully. You can now download your purchased products.",
                    notification_type="payment",
                    data={"transaction_id": transaction.id, "amount": transaction.amount}
                )
                
                return {
                    "success": True,
                    "message": "Payment verified and processed successfully",
                    "status": paystack_status,
                    "download_token": result.get("download_token")
                }
            else:
                return {
                    "success": False,
                    "message": "Payment received but processing failed - our team will contact you",
                    "status": paystack_status,
                    "error": result.get("error", "Unknown processing error")
                }
        elif paystack_status == "failed":
            # Format amount based on the actual transaction currency
            formatted_amount = format_currency_for_notification(
                transaction.amount, 
                transaction.currency,  # Use actual transaction currency
                current_user.currency or transaction.currency, 
                db
            )
            
            # Create notification for failed payment
            create_notification(
                db=db,
                user_id=current_user.id,
                title="Payment Failed",
                message=f"Your payment of {formatted_amount} was not successful. Please try again or contact support if the issue persists.",
                notification_type="error",
                data={"transaction_id": transaction.id, "amount": transaction.amount, "status": paystack_status}
            )
            
            return {
                "success": False,
                "message": "Payment failed",
                "status": paystack_status
            }
        else:
            return {
                "success": True,
                "message": f"Payment status updated to: {paystack_status}",
                "status": paystack_status
            }
            
    except Exception as e:
        safe_log("payment", "error", f"Manual payment verification error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to verify payment"
        )

# Retry payment endpoint
@app.post("/api/payment/retry/{reference}")
async def retry_payment(
    reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry a failed payment by creating a new checkout session"""
    try:
        # Find existing transaction
        transaction = db.query(Transaction).filter(
            Transaction.paystack_reference == reference,
            Transaction.user_id == current_user.id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Only allow retry for failed, pending, or abandoned transactions
        if transaction.status not in ["failed", "pending", "abandoned"]:
            raise HTTPException(
                status_code=400, 
                detail="Can only retry failed, pending, or abandoned payments"
            )
        
        # Get the original order items
        order_items = db.query(OrderItem).filter(
            OrderItem.transaction_id == transaction.id
        ).all()
        
        if not order_items:
            raise HTTPException(
                status_code=400, 
                detail="No order items found for this transaction"
            )
        
        # Create new checkout data
        checkout_data = {
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity
                } for item in order_items
            ]
        }
        
        # Calculate total amount from order items
        total_amount = sum(item.price * item.quantity for item in order_items)
        
        # Use stored user location and currency
        user_country = current_user.country
        currency = current_user.currency
        
        safe_log("payment", "info", f"Retry payment - User country: {user_country}, Currency: {currency}")
        
        # If USD currency, redirect to MQL5 seller page
        if currency == "USD":
            mql5_url = "https://www.mql5.com/en/users/PerpetualRalph/seller"
            return {
                "success": True,
                "redirect": True,
                "redirect_url": mql5_url,
                "message": "USD payments are currently processed through our MQL5 seller page",
                "currency": currency,
                "country": user_country
            }
        
        # For NGN payments, proceed with Paystack
        if currency == "NGN":
            # Generate unique transaction reference
            transaction_ref = f"JARVIS_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
            
            amount_in_smallest_unit = int(total_amount * 100)  # Convert to kobo for NGN
            
            # Prepare cart items for Paystack
            cart_items = [
                {
                    "id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price
                } for item in order_items
            ]
            
            # Prepare Paystack request data for NGN
            paystack_data = {
                "email": current_user.email,
                "currency": currency,
                "amount": amount_in_smallest_unit,
                "reference": transaction_ref,
                "callback_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/payment/success?reference={transaction_ref}",
                "metadata": {
                    "user_id": current_user.id,
                    "cart_items": cart_items,
                    "total_amount": total_amount,
                    "country": user_country,
                    "original_transaction_id": transaction.id,
                    "is_retry_payment": True
                }
            }
            
            # Make request to Paystack
            paystack_url = "https://api.paystack.co/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(paystack_url, json=paystack_data, headers=headers) as response:
                    response_data = await response.json()
                    safe_log("payment", "info", f"Paystack Response: {response_data}")
                    
                    if response.status == 200:
                        paystack_response = response_data
                        
                        # Create new transaction record in database
                        new_transaction = Transaction(
                            user_id=current_user.id,
                            paystack_reference=transaction_ref,
                            amount=total_amount,
                            currency=currency,
                            status="pending",
                            payment_data=json.dumps({
                                **paystack_response["data"],
                                "original_transaction_id": transaction.id,
                                "original_transaction_reference": transaction.paystack_reference,
                                "is_retry_payment": True
                            }),
                            purchased_items=json.dumps(cart_items)
                        )
                        
                        db.add(new_transaction)
                        db.commit()
                        db.refresh(new_transaction)
                        
                        # Create order items for each product
                        for item in order_items:
                            new_order_item = OrderItem(
                                transaction_id=new_transaction.id,
                                product_id=item.product_id,
                                quantity=item.quantity,
                                price=item.price
                            )
                            db.add(new_order_item)
                        
                        db.commit()
                        
                        return {
                            "success": True,
                            "message": "New payment session created",
                            "checkout_url": paystack_response["data"]["authorization_url"],
                            "reference": transaction_ref
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Failed to create payment session: {response_data}"
                        }
        else:
            return {
                "success": False,
                "message": f"Unsupported currency: {currency}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        safe_log("payment", "error", f"Payment retry error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retry payment"
        )

@app.get("/api/payment/status/{reference}")
async def get_payment_status(
    reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment status from local database"""
    try:
        transaction = db.query(Transaction).filter(
            Transaction.paystack_reference == reference,
            Transaction.user_id == current_user.id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        safe_log("payment", "info", f"Payment status for {reference}: {transaction.status}")
        
        return {
            "success": True,
            "status": transaction.status,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "created_at": transaction.created_at.isoformat(),
            "reference": transaction.paystack_reference
        }
        
    except Exception as e:
        safe_log("payment", "error", f"Payment status error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get payment status: {str(e)}"
        )

@app.get("/api/payment/details/{reference}")
async def get_payment_details(
    reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed payment information including verification log"""
    try:
        transaction = db.query(Transaction).filter(
            Transaction.paystack_reference == reference,
            Transaction.user_id == current_user.id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Parse payment data to extract verification log
        verification_log = ""
        verified_at = None
        try:
            if transaction.payment_data:
                payment_data = json.loads(transaction.payment_data)
                verification_log = payment_data.get("verification_log", "")
                verified_at = payment_data.get("verified_at")
        except (json.JSONDecodeError, KeyError):
            pass
        
        return {
            "success": True,
            "status": transaction.status,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "created_at": transaction.created_at.isoformat(),
            "reference": transaction.paystack_reference,
            "verification_log": verification_log,
            "verified_at": verified_at
        }
        
    except Exception as e:
        safe_log("payment", "error", f"Payment details error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get payment details: {str(e)}"
        )

# Direct download endpoint for purchased products
@app.get("/api/products/{product_id}/download")
async def download_product(
    product_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Direct download for purchased products"""
    try:
        # Get client IP and user agent
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        download_logger.info(f"Download attempt - User: {current_user.email}, Product: {product_id}")
        download_logger.info(f"User ID: {current_user.id}")
        
        # Check if user has purchased this product (has successful transaction)
        user_transaction = db.query(Transaction).join(OrderItem).filter(
            Transaction.user_id == current_user.id,
            Transaction.status == "success",
            OrderItem.product_id == product_id
        ).first()
        
        download_logger.info(f"Purchase check - Transaction found: {user_transaction is not None}")
        if user_transaction:
            download_logger.info(f"Transaction ID: {user_transaction.id}, Status: {user_transaction.status}")
        
        if not user_transaction:
            raise HTTPException(
                status_code=403,
                detail="You have not purchased this product"
            )
        
        # Check if this is a rental and if the license has expired
        order_item = db.query(OrderItem).filter(
            OrderItem.transaction_id == user_transaction.id,
            OrderItem.product_id == product_id
        ).first()
        
        if order_item and order_item.is_rental:
            # Check if rental license has expired
            license_obj = db.query(License).filter(
                License.transaction_id == user_transaction.id,
                License.product_id == product_id,
                License.is_rental == True
            ).first()
            
            if license_obj and license_obj.expires_at:
                if datetime.utcnow() > license_obj.expires_at:
                    raise HTTPException(
                        status_code=403,
                        detail="Your rental license has expired. Please renew to continue accessing this product."
                    )
                else:
                    days_remaining = (license_obj.expires_at - datetime.utcnow()).days
                    download_logger.info(f"Rental license valid. Days remaining: {days_remaining}")
            else:
                download_logger.warning("Warning: No rental license found for rental product")
        
        # Get the product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # if not product.is_digital:
        #     raise HTTPException(status_code=400, detail="Product is not downloadable")
        
        if not product.file_path or not os.path.exists(product.file_path):
            raise HTTPException(status_code=404, detail="Product file not found")
        
        try:
            # Log the download
            download_log = DownloadLog(
                user_id=current_user.id,
                product_id=product_id,
                license_id=None,  # No specific license required for digital downloads
                ip_address=client_ip,
                user_agent=user_agent,
                download_status="success",
                created_at=datetime.utcnow()
            )
            db.add(download_log)
            
            # Update download count
            product.download_count += 1
            db.commit()
        except Exception as e:
            download_logger.warning(f"Failed to log download or update count: {e}")
            # Continue with download even if logging fails
            db.rollback()
        
        # Prepare file for streaming
        file_path = product.file_path
        original_file_name = os.path.basename(file_path)
        
        try:
            file_size = os.path.getsize(file_path)
        except OSError as e:
            download_logger.error(f"Cannot get file size for {file_path}: {e}")
            raise HTTPException(status_code=404, detail="Product file not accessible")
        
        # Normalize file path and ensure it's absolute
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        # Double-check file exists after normalization
        if not os.path.exists(file_path):
            download_logger.error(f"File not found after path normalization: {file_path}")
            download_logger.error(f"Original file_path: {product.file_path}")
            download_logger.error(f"Current working directory: {os.getcwd()}")
            raise HTTPException(status_code=404, detail="Product file not found after path normalization")
        
        def zip_stream():
            try:
                import zipfile
                import io
                
                # Create zip file in memory
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add the product file to the zip
                    zip_file.write(file_path, original_file_name)
                    download_logger.info(f"Added product file to zip: {original_file_name}")
                    
                    # Add a README file with product information
                    readme_content = f"""Product: {product.name}
Description: {product.description}
Category: {product.category}
Download Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
File: {original_file_name}
Size: {file_size} bytes

This file was purchased from JarvisTrade.
Please ensure you have a valid license for this product.
"""
                    zip_file.writestr("README.txt", readme_content)
                    download_logger.info("Added README.txt to zip")
                    
                    # List zip contents for verification
                    zip_file.printdir()
                
                # Reset buffer position
                zip_buffer.seek(0)
                
                # Get zip file size
                zip_size = zip_buffer.tell()
                zip_buffer.seek(0)
                
                download_logger.info(f"Zip file created successfully - Size: {zip_size} bytes")
                
                # Stream the zip file
                while True:
                    chunk = zip_buffer.read(8192)
                    if not chunk:
                        break
                    yield chunk
                    
            except Exception as e:
                download_logger.error(f"Error creating zip file: {e}")
                # Fallback to direct file streaming if zip creation fails
                download_logger.info("Falling back to direct file streaming...")
                try:
                    with open(file_path, "rb") as f:
                        while chunk := f.read(8192):
                            yield chunk
                except Exception as fallback_error:
                    download_logger.error(f"Fallback streaming also failed: {fallback_error}")
                    raise
        
        # Generate zip filename
        zip_filename = f"{product.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.zip"
        
        # Log download details
        download_logger.info(f"Direct download - User: {current_user.email}")
        download_logger.info(f"Product: {product.name}")
        download_logger.info(f"File: {file_path}")
        download_logger.info(f"Size: {file_size} bytes")
        download_logger.info(f"Transaction: {user_transaction.id}")
        download_logger.info(f"Zip filename: {zip_filename}")
        
        return StreamingResponse(
            zip_stream(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=\"{zip_filename}\"",
                "Content-Type": "application/zip",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(f"Direct download error: {e}")
        # Log failed download
        if 'current_user' in locals() and 'product_id' in locals():
            download_log = DownloadLog(
                user_id=current_user.id,
                product_id=product_id,
                ip_address=client_ip,
                user_agent=user_agent,
                download_status="failed",
                error_message=str(e),
                created_at=datetime.utcnow()
            )
            db.add(download_log)
            db.commit()
        
        raise HTTPException(
            status_code=500,
            detail="Failed to download file"
        )

# Legacy download endpoint (keep for existing tokens)
@app.get("/api/download")
async def download_file(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Download file using secure token (legacy)"""
    try:
        # Get client IP and user agent
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Validate token
        result = payment_service.validate_download_token(db, token, client_ip, user_agent)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
        
        # Stream the file
        file_path = result["file_path"]
        file_name = os.path.basename(file_path)
        
        # Create download notification
        create_notification(
            db=db,
            user_id=result["user_id"],
            title="Download Successful",
            message=f"Your product has been downloaded successfully. File: {file_name}",
            notification_type="success",
            data={"product_id": result.get("product_id"), "file_name": file_name, "download_time": datetime.utcnow().isoformat()}
        )
        
        def file_stream():
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk
        
        # Log download details for debugging
        download_logger.info(f"Downloading file: {file_path}")
        download_logger.info(f"File size: {result['file_size']} bytes")
        download_logger.info(f"File exists: {os.path.exists(file_path)}")
        download_logger.info(f"Client IP: {client_ip}")
        download_logger.info(f"User Agent: {user_agent}")
        
        # Ensure the file size is correct
        actual_size = os.path.getsize(file_path)
        if actual_size != result["file_size"]:
            download_logger.warning(f"File size mismatch! Database: {result['file_size']}, Actual: {actual_size}")
        
        return StreamingResponse(
            file_stream(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=\"{file_name}\"",
                "Content-Length": str(actual_size),
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(f"Download error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download file"
        )

# Success page data endpoint
@app.get("/api/payment/success")
async def get_payment_success_data(
    reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payment success data for frontend"""
    try:
        # Verify payment with Paystack
        verification_result = await payment_service.verify_payment(reference)
        
        if not verification_result["success"]:
            raise HTTPException(
                status_code=400,
                detail="Payment verification failed"
            )
        
        # Get transaction details
        transaction = db.query(Transaction).filter(
            Transaction.paystack_reference == reference
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )
        
        # Get download tokens for this transaction
        download_tokens = db.query(DownloadToken).filter(
            DownloadToken.transaction_id == transaction.id
        ).all()
        
        download_links = []
        for token in download_tokens:
            product = db.query(Product).filter(Product.id == token.product_id).first()
            if product:
                download_links.append({
                    "product_name": product.name,
                    "download_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/download?token={token.token}",
                    "expires_at": token.expires_at.isoformat()
                })
        
        return {
            "success": True,
            "transaction": {
                "reference": transaction.paystack_reference,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "status": transaction.status,
                "created_at": transaction.created_at.isoformat()
            },
            "download_links": download_links
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Success page data error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get payment success data"
        )

# Categories endpoint
@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all product categories with counts"""
    categories = []
    
    for category_id in PRODUCT_CATEGORIES:
        # Get count of products in this category
        count = db.query(Product).filter(
            Product.category == category_id,
            Product.is_active == True
        ).count()
        
        # Map category ID to display name
        category_names = {
            "trading-bot": "Trading Bots",
            "indicator": "Indicators", 
            "analysis-tool": "Analysis Tools",
            "risk-management": "Risk Management",
            "education": "Education"
        }
        
        categories.append(CategoryResponse(
            id=category_id,
            name=category_names.get(category_id, category_id.title()),
            count=count
        ))
    
    return categories


# Notification endpoints
@app.get("/api/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's notifications"""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return notifications


@app.get("/api/notifications/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    notification_logger.info(f"Getting unread count for user: {current_user.id}")
    
    try:
        count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).count()
        notification_logger.info(f"Found {count} unread notifications for user: {current_user.id}")
        return {"unread_count": count}
    except Exception as e:
        notification_logger.error(f"Error getting unread count for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting unread count: {str(e)}")


@app.put("/api/notifications/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update notification (mark as read)"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    for field, value in notification_update.dict(exclude_unset=True).items():
        setattr(notification, field, value)
    
    db.commit()
    db.refresh(notification)
    return notification


@app.post("/api/notifications/mark-all-read")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all user's notifications as read"""
    try:
        # Update all unread notifications for the current user
        result = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).update({"is_read": True})
        
        db.commit()
        
        return {
            "message": "All notifications marked as read",
            "updated_count": result
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking notifications as read: {str(e)}")


@app.delete("/api/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted"}


# Helper function to create notifications
def create_notification(
    db: Session,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    data: Optional[dict] = None
):
    """Helper function to create notifications with preference checking"""
    try:
        # Get user and check notification preferences
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Parse user's notification preferences
        try:
            preferences = json.loads(user.notification_preferences) if user.notification_preferences else {}
        except (json.JSONDecodeError, TypeError):
            preferences = {
                "info": True,
                "success": True,
                "warning": True,
                "error": True,
                "payment": True,
                "order": True,
                "system": True,
                "update": True,
                "review_prompt": True
            }
        
        # Check if user has enabled this type of notification
        if notification_type not in preferences or not preferences.get(notification_type, True):
            return None
        
        # Check if user has enabled notifications in general
        if not user.push_notifications:
            return None
        
        notification_data = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "data": json.dumps(data) if data else None
        }

        notification = Notification(**notification_data)
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
        
    except Exception as e:
        notification_logger.error(f"Error creating notification: {e}")
        db.rollback()
        return None

def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a product name."""
    import re
    
    if not name:
        return ""
    
    # Convert to lowercase and replace special characters
    slug = name.lower()
    
    # Replace special characters with spaces
    slug = re.sub(r'[^a-z0-9\s-]', ' ', slug)
    
    # Replace multiple spaces with single space
    slug = re.sub(r'\s+', ' ', slug)
    
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Ensure slug is not empty
    if not slug:
        slug = "product"
    
    return slug

def ensure_unique_slug(db: Session, slug: str, product_id: str = None, counter: int = 0) -> str:
    """Ensure slug is unique by adding a number suffix if needed."""
    if counter == 0:
        test_slug = slug
    else:
        test_slug = f"{slug}-{counter}"
    
    # Check if slug exists for other products
    query = db.query(Product).filter(Product.slug == test_slug)
    if product_id:
        query = query.filter(Product.id != product_id)
    
    if query.first():
        return ensure_unique_slug(db, slug, product_id, counter + 1)
    
    return test_slug

# Product endpoints
@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: Optional[str] = "created_at",  # created_at, price, rating, name
    sort_order: Optional[str] = "desc",  # asc, desc
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get products with optional currency conversion"""
    query = db.query(Product).filter(Product.is_active == True)
    
    # Apply filters
    if category:
        query = query.filter(Product.category == category)
    
    if platform:
        query = query.filter(Product.platform == platform)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.short_description.ilike(search_term)
            )
        )
    
    if featured is not None:
        query = query.filter(Product.is_featured == featured)
    
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)
    
    exchange_rate_logger.info(f'Min price: {min_price}')
    exchange_rate_logger.info(f'Max price: {max_price}')
    
    # Apply price filtering
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Apply sorting
    if sort_by == "price":
        order_column = Product.price
    elif sort_by == "rating":
        order_column = Product.rating
    elif sort_by == "name":
        order_column = Product.name
    else:
        order_column = Product.created_at
    
    if sort_order == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    products = query.offset(skip).limit(limit).all()
    
    # Always convert prices to user currency if authenticated, otherwise use USD
    user_currency = "USD"
    if current_user and current_user.currency:
        user_currency = current_user.currency
    
    # Convert product prices
    converted_products = []
    for product in products:
        product_dict = {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "short_description": product.short_description,
            "price": product.price,
            "original_price": product.original_price,
            "category": product.category,
            "platform": product.platform or "MT4",
            "image": product.image,
            "tags": json.loads(product.tags) if product.tags else [],
            "features": json.loads(product.features) if product.features else [],
            "images": json.loads(product.images) if product.images else [],
            "rating": product.rating or 0.0,
            "total_reviews": product.total_reviews,
            "is_active": product.is_active,
            "is_featured": product.is_featured,
            "is_digital": product.is_digital,
            "file_path": product.file_path,
            "file_size": product.file_size,
            "download_count": product.download_count,
            "youtube_demo_link": product.youtube_demo_link,
            "test_download_link": product.test_download_link,
            "max_activations": product.max_activations,
            "version": product.version,
            "user_id": product.user_id,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            
            # Rental fields
            "has_rental_option": product.has_rental_option or False,
            "rental_price": product.rental_price,
            "rental_duration_days": product.rental_duration_days or 30
        }
        
        # Always convert price to user currency
        if user_currency != "USD":
            converted_price = convert_currency(product.price, "USD", user_currency, db)
            product_dict["price"] = converted_price
            if product.original_price:
                converted_original_price = convert_currency(product.original_price, "USD", user_currency, db)
                product_dict["original_price"] = converted_original_price
            
            # Convert rental price if available
            if product.rental_price:
                converted_rental_price = convert_currency(product.rental_price, "USD", user_currency, db)
                product_dict["rental_price"] = converted_rental_price
        
        # Add currency information
        product_dict["currency"] = user_currency
        product_dict["currency_symbol"] = get_currency_symbol(user_currency)
        
        converted_products.append(product_dict)
    
    return converted_products

@app.get("/api/products/featured", response_model=List[ProductResponse])
async def get_featured_products(
    limit: int = 6,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get featured products with currency conversion"""
    products = db.query(Product).filter(
        Product.is_active == True,
        Product.is_featured == True
    ).order_by(Product.created_at.desc()).limit(limit).all()
    
    # Always convert prices to user currency if authenticated, otherwise use USD
    user_currency = "USD"
    if current_user and current_user.currency:
        user_currency = current_user.currency
    
    # Convert product prices
    converted_products = []
    for product in products:
        product_dict = {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "short_description": product.short_description,
            "price": product.price,
            "original_price": product.original_price,
            "category": product.category,
            "platform": product.platform or "MT4",
            "image": product.image,
            "tags": json.loads(product.tags) if product.tags else [],
            "features": json.loads(product.features) if product.features else [],
            "images": json.loads(product.images) if product.images else [],
            "rating": product.rating or 0.0,
            "total_reviews": product.total_reviews,
            "is_active": product.is_active,
            "is_featured": product.is_featured,
            "is_digital": product.is_digital,
            "file_path": product.file_path,
            "file_size": product.file_size,
            "download_count": product.download_count,
            "youtube_demo_link": product.youtube_demo_link,
            "test_download_link": product.test_download_link,
            "max_activations": product.max_activations,
            "version": product.version,
            "user_id": product.user_id,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            
            # Rental fields
            "has_rental_option": product.has_rental_option or False,
            "rental_price": product.rental_price,
            "rental_duration_days": product.rental_duration_days or 30
        }
        
        # Always convert price to user currency
        if user_currency != "USD":
            converted_price = convert_currency(product.price, "USD", user_currency, db)
            product_dict["price"] = converted_price
            if product.original_price:
                converted_original_price = convert_currency(product.original_price, "USD", user_currency, db)
                product_dict["original_price"] = converted_original_price
            
            # Convert rental price if available
            if product.rental_price:
                converted_rental_price = convert_currency(product.rental_price, "USD", user_currency, db)
                product_dict["rental_price"] = converted_rental_price
        
        # Add currency information
        product_dict["currency"] = user_currency
        product_dict["currency_symbol"] = get_currency_symbol(user_currency)
        
        converted_products.append(product_dict)
    
    return converted_products

@app.get("/api/admin/products", response_model=List[ProductResponse])
async def get_admin_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: Optional[str] = "created_at",  # created_at, price, rating, name
    sort_order: Optional[str] = "desc",  # asc, desc
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all products for admin management (including inactive)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = db.query(Product)  # No filter for is_active - returns all products
    
    # Apply filters
    if category:
        if category not in PRODUCT_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {', '.join(PRODUCT_CATEGORIES)}")
        query = query.filter(Product.category == category)
    
    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%") |
            Product.description.ilike(f"%{search}%") |
            Product.short_description.ilike(f"%{search}%")
        )
    
    if featured is not None:
        query = query.filter(Product.is_featured == featured)
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)
    
    # Apply sorting
    if sort_by == "price":
        if sort_order == "asc":
            query = query.order_by(Product.price.asc())
        else:
            query = query.order_by(Product.price.desc())
    elif sort_by == "rating":
        if sort_order == "asc":
            query = query.order_by(Product.rating.asc())
        else:
            query = query.order_by(Product.rating.desc())
    elif sort_by == "name":
        if sort_order == "asc":
            query = query.order_by(Product.name.asc())
        else:
            query = query.order_by(Product.name.desc())
    else:  # default: created_at
        if sort_order == "asc":
            query = query.order_by(Product.created_at.asc())
        else:
            query = query.order_by(Product.created_at.desc())
    
    products = query.offset(skip).limit(limit).all()
    return products

@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
    ):
    """Get a specific product by ID with optional currency conversion"""
    product_logger.info(f"Getting product with ID: {product_id}")
    product_logger.info(f"Current user: {current_user}")
    
    # Try to find product by ID first, then by slug
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        # If not found by ID, try to find by slug
        product = db.query(Product).filter(Product.slug == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Always convert prices to user currency if authenticated, otherwise use USD
    user_currency = "USD"
    if current_user and current_user.currency:
        user_currency = current_user.currency
    
    product_dict = {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "short_description": product.short_description,
        "price": product.price,
        "original_price": product.original_price,
        "category": product.category,
        "platform": product.platform or "MT4",
        "image": product.image,
        "tags": json.loads(product.tags) if product.tags else [],
        "features": json.loads(product.features) if product.features else [],
        "images": json.loads(product.images) if product.images else [],
        "rating": product.rating or 0.0,
        "total_reviews": product.total_reviews,
        "is_active": product.is_active,
        "is_featured": product.is_featured,
        "is_digital": product.is_digital,
        "file_path": product.file_path,
        "file_size": product.file_size,
        "download_count": product.download_count,
        "youtube_demo_link": product.youtube_demo_link,
        "test_download_link": product.test_download_link,
        "max_activations": product.max_activations or 1,
        "version": product.version,
        "user_id": product.user_id,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        
        # Rental fields
        "has_rental_option": product.has_rental_option or False,
        "rental_price": product.rental_price,
        "rental_duration_days": product.rental_duration_days or 30
    }
    
    # Always convert price to user currency
    if user_currency != "USD":
        converted_price = convert_currency(product.price, "USD", user_currency, db)
        product_dict["price"] = converted_price
        if product.original_price:
            converted_original_price = convert_currency(product.original_price, "USD", user_currency, db)
            product_dict["original_price"] = converted_original_price
        
        # Convert rental price if available
        if product.rental_price:
            converted_rental_price = convert_currency(product.rental_price, "USD", user_currency, db)
            product_dict["rental_price"] = converted_rental_price
    
    # Add currency information
    product_dict["currency"] = user_currency
    product_dict["currency_symbol"] = get_currency_symbol(user_currency)
    
    return product_dict

@app.post("/api/products", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Convert lists to JSON strings for SQLite compatibility
    product_data = product.dict()
    if 'tags' in product_data:
        product_data['tags'] = json.dumps(product_data['tags'] or [])
    if 'features' in product_data:
        product_data['features'] = json.dumps(product_data['features'] or [])
    if 'images' in product_data:
        product_data['images'] = json.dumps(product_data['images'] or [])
    
    # Generate slug from product name if not provided, or ensure custom slug is unique
    if not product_data.get('slug'):
        base_slug = generate_slug(product_data['name'])
        product_data['slug'] = ensure_unique_slug(db, base_slug)
    else:
        # Ensure custom slug is unique
        product_data['slug'] = ensure_unique_slug(db, product_data['slug'])
    
    # Set the user_id to the current user
    product_data['user_id'] = current_user.id
    
    db_product = Product(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return convert_product_json_fields(db_product)

@app.put("/api/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a product (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check if this is a version update or bug fix
        is_version_update = False
        is_bug_fix = False
        
        if product_update.version and product_update.version != product.version:
            is_version_update = True
        if product_update.description and "bug fix" in product_update.description.lower() or "performance" in product_update.description.lower():
            is_bug_fix = True
        
        # Update product
        update_data = product_update.dict(exclude_unset=True)
        
        # Generate new slug if name is being updated, or ensure custom slug is unique
        if 'name' in update_data and update_data['name'] != product.name:
            if 'slug' not in update_data or not update_data['slug']:
                # Auto-generate slug from new name
                base_slug = generate_slug(update_data['name'])
                update_data['slug'] = ensure_unique_slug(db, base_slug, product_id)
        elif 'slug' in update_data and update_data['slug']:
            # Ensure custom slug is unique
            update_data['slug'] = ensure_unique_slug(db, update_data['slug'], product_id)
        
        for field, value in update_data.items():
            # Handle list fields by converting them to JSON strings
            if field in ['tags', 'features', 'images'] and isinstance(value, list):
                setattr(product, field, json.dumps(value) if value else None)
            else:
                setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        # Send notifications to users who purchased this product
        if is_version_update or is_bug_fix:
            # Get users who purchased this product
            purchased_users = db.query(User).join(Transaction).filter(
                Transaction.product_id == product_id,
                Transaction.status == "success"
            ).distinct().all()
            
            notification_type = "update" if is_version_update else "system"
            title = f"New Version Available: {product.name}" if is_version_update else f"Update Available: {product.name}"
            message = f"A new version of {product.name} is now available for download." if is_version_update else f"Bug fixes and performance improvements have been applied to {product.name}."
            
            for user in purchased_users:
                create_notification(
                    db=db,
                    user_id=user.id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    data={"product_id": product_id, "product_name": product.name, "version": product.version}
                )
        
        return convert_product_json_fields(product)
        
    except Exception as e:
        product_logger.error(f"Error updating product: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update product")

@app.delete("/api/products/{product_id}")
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a product (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}

# Review endpoints
@app.get("/api/products/{product_id}/reviews", response_model=List[ReviewResponse])
async def get_product_reviews(
    product_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get reviews for a specific product"""
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get approved reviews with user information
    reviews = db.query(Review).filter(
        Review.product_id == product_id,
        Review.is_approved == True
    ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert to response format with user info
    review_responses = []
    for review in reviews:
        user = db.query(User).filter(User.id == review.user_id).first()
        review_response = ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            product_id=review.product_id,
            rating=review.rating,
            comment=review.comment,
            is_verified_purchase=review.is_verified_purchase,
            is_approved=review.is_approved,
            created_at=review.created_at,
            updated_at=review.updated_at,
            user_name=user.name if user else "Anonymous",
            user_email=user.email if user else ""
        )
        review_responses.append(review_response)
    
    return review_responses

@app.post("/api/products/{product_id}/reviews", response_model=ReviewResponse)
async def create_review(
    product_id: str,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a review for a product"""
    try:
        # Check if product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check if user has purchased the product
        transaction = db.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.product_id == product_id,
            Transaction.status == "success"
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=403, detail="You can only review products you have purchased")
        
        # Check if user has already reviewed this product
        existing_review = db.query(Review).filter(
            Review.user_id == current_user.id,
            Review.product_id == product_id
        ).first()
        
        if existing_review:
            raise HTTPException(status_code=400, detail="You have already reviewed this product")
        
        # Create review
        db_review = Review(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            product_id=product_id,
            rating=review.rating,
            comment=review.comment
        )
        
        db.add(db_review)
        db.commit()
        db.refresh(db_review)
        
        # Update product average rating
        reviews = db.query(Review).filter(Review.product_id == product_id).all()
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            product.average_rating = round(avg_rating, 1)
            product.review_count = len(reviews)
            db.commit()
        
        # Send notification to admin about new review
        admin_users = db.query(User).filter(User.is_admin == True).all()
        for admin in admin_users:
            create_notification(
                db=db,
                user_id=admin.id,
                title="New Product Review",
                message=f"User {current_user.name} left a {review.rating}-star review for {product.name}",
                notification_type="system",
                data={"product_id": product_id, "review_id": db_review.id, "rating": review.rating}
            )
        
        # Send notification to user about successful review
        create_notification(
            db=db,
            user_id=current_user.id,
            title="Review Submitted",
            message=f"Thank you for your review of {product.name}! Your feedback helps other traders make informed decisions.",
            notification_type="success",
            data={"product_id": product_id, "review_id": db_review.id, "rating": review.rating}
        )
        
        return convert_review_json_fields(db_review)
        
    except HTTPException:
        raise
    except Exception as e:
        review_logger.error(f"Error creating review: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create review")

@app.put("/api/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    review_update: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a review (only by the author or admin)"""
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if user is the author or admin
    if db_review.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only update your own reviews")
    
    # Update the review
    update_data = review_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_review, field, value)
    
    db.commit()
    db.refresh(db_review)
    
    # Get user info
    user = db.query(User).filter(User.id == db_review.user_id).first()
    
    return ReviewResponse(
        id=db_review.id,
        user_id=db_review.user_id,
        product_id=db_review.product_id,
        rating=db_review.rating,
        comment=db_review.comment,
        is_verified_purchase=db_review.is_verified_purchase,
        is_approved=db_review.is_approved,
        created_at=db_review.created_at,
        updated_at=db_review.updated_at,
        user_name=user.name if user else "Anonymous",
        user_email=user.email if user else ""
    )

@app.delete("/api/reviews/{review_id}")
async def delete_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a review (only by the author or admin)"""
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if user is the author or admin
    if db_review.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only delete your own reviews")
    
    # Delete the review
    db.delete(db_review)
    db.commit()
    
    # Update product rating and total reviews
    product_id = db_review.product_id
    all_reviews = db.query(Review).filter(
        Review.product_id == product_id,
        Review.is_approved == True
    ).all()
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        if all_reviews:
            avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
            product.rating = round(avg_rating, 1)
            product.total_reviews = len(all_reviews)
        else:
            product.rating = 0.0
            product.total_reviews = 0
        db.commit()
    
    return {"message": "Review deleted successfully"}

# User endpoints
@app.get("/api/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.put("/api/users/me/password")
async def change_password(
    password_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change current user's password"""
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Current password and new password are required")
    
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(current_user)
    
    # Send password change notification
    create_notification(
        db=db,
        user_id=current_user.id,
        title="Password Changed Successfully",
        message="Your password has been updated successfully. If you didn't make this change, please contact support immediately.",
        notification_type="warning",
        data={"password_change_time": datetime.utcnow().isoformat(), "security_event": "password_change"}
    )
    
    return {"message": "Password changed successfully"}

@app.delete("/api/users/me")
async def delete_own_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete current user's own account"""
    # Check if user has any transactions or other important data
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).count()
    if transactions > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete account with existing transactions. Please contact support."
        )
    
    # Check if user has any orders
    orders = db.query(OrderItem).join(Transaction).filter(Transaction.user_id == current_user.id).count()
    if orders > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete account with existing orders. Please contact support."
        )
    
    # Check if user has any reviews
    reviews = db.query(Review).filter(Review.user_id == current_user.id).count()
    if reviews > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete account with existing reviews. Please contact support."
        )
    
    # Check if user has any project requests
    project_requests = db.query(ProjectRequest).filter(ProjectRequest.user_id == current_user.id).count()
    if project_requests > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete account with existing project requests. Please contact support."
        )
    
    # Check if user has any blog posts (if they're an admin)
    if current_user.is_admin:
        blog_posts = db.query(BlogPost).filter(BlogPost.author_id == current_user.id).count()
        if blog_posts > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete admin account with existing blog posts. Please transfer ownership first."
            )
    
    # Delete the user
    db.delete(current_user)
    db.commit()
    
    # Notify admins about account deletion
    admin_users = db.query(User).filter(User.is_admin == True).all()
    for admin in admin_users:
        create_notification(
            db=db,
            user_id=admin.id,
            title="Account Deleted",
            message=f"User {current_user.name} ({current_user.email}) has deleted their account.",
            notification_type="system",
            data={"deleted_user_id": current_user.id, "deleted_user_email": current_user.email, "deletion_time": datetime.utcnow().isoformat()}
        )
    
    return {"message": "Account deleted successfully"}

@app.get("/api/users/me/dashboard")
async def get_user_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's dashboard data"""
    
    # Get user's transactions
    total_transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).count()
    
    successful_transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.status == "success"
    ).count()
    
    total_spent = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.status == "success"
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    # Get user's reviews
    total_reviews = db.query(Review).filter(
        Review.user_id == current_user.id
    ).count()
    
    # Get user's downloads (from download logs)
    total_downloads = db.query(DownloadLog).filter(
        DownloadLog.user_id == current_user.id
    ).count()
    
    # Get recent transactions with product details
    recent_transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Get recent reviews with product details
    recent_reviews = db.query(Review).filter(
        Review.user_id == current_user.id
    ).order_by(Review.created_at.desc()).limit(10).all()
    
    # Get recent downloads
    recent_downloads = db.query(DownloadLog).filter(
        DownloadLog.user_id == current_user.id
    ).order_by(DownloadLog.download_time.desc()).limit(10).all()
    
    # Build recent activity list
    recent_activity = []
    
    # Add transactions
    for transaction in recent_transactions:
        # Get product details for this transaction
        order_items = db.query(OrderItem).filter(
            OrderItem.transaction_id == transaction.id
        ).all()
        
        if order_items:
            # If we have order items, use them
            for item in order_items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    recent_activity.append({
                        "id": f"transaction_{transaction.id}_{item.id}",
                        "type": "purchase",
                        "productName": product.name,
                        "timestamp": transaction.created_at.isoformat(),
                        "amount": float(item.price * item.quantity),
                        "status": transaction.status,
                        "reference": transaction.paystack_reference
                    })
        else:
            # If no order items, create a generic purchase entry
            recent_activity.append({
                "id": f"transaction_{transaction.id}",
                "type": "purchase",
                "productName": "Digital Products",
                "timestamp": transaction.created_at.isoformat(),
                "amount": float(transaction.amount),
                "status": transaction.status,
                "reference": transaction.paystack_reference
            })
    
    # Add reviews
    for review in recent_reviews:
        product = db.query(Product).filter(Product.id == review.product_id).first()
        if product:
            recent_activity.append({
                "id": f"review_{review.id}",
                "type": "review",
                "productName": product.name,
                "timestamp": review.created_at.isoformat(),
                "rating": review.rating
            })
    
    # Add downloads
    for download in recent_downloads:
        if download.product_id:
            product = db.query(Product).filter(Product.id == download.product_id).first()
            if product:
                recent_activity.append({
                    "id": f"download_{download.id}",
                    "type": "download",
                    "productName": product.name,
                    "timestamp": download.download_time.isoformat()
                })
        else:
            # If no product_id, create a generic download entry
            recent_activity.append({
                "id": f"download_{download.id}",
                "type": "download",
                "productName": "Digital Product",
                "timestamp": download.download_time.isoformat()
            })
    
    # Sort recent activity by timestamp (most recent first)
    recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activity = recent_activity[:10]  # Limit to 10 most recent activities
    
    # Get user's project requests
    user_projects = db.query(ProjectRequest).filter(
        ProjectRequest.user_id == current_user.id
    ).order_by(ProjectRequest.created_at.desc()).limit(5).all()
    
    # Convert projects to the expected format
    projects = []
    for project in user_projects:
        # Parse platforms from JSON string
        platforms = []
        if project.platforms:
            try:
                platforms = json.loads(project.platforms) if isinstance(project.platforms, str) else project.platforms
            except (json.JSONDecodeError, TypeError):
                platforms = []
        
        projects.append({
            "id": project.id,
            "project_title": project.project_title,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "platforms": platforms,
            "expected_completion_time": project.expected_completion_time,
            "budget_range": project.budget_range
        })
    
    return {
        "stats": {
            "totalPurchases": successful_transactions,
            "totalDownloads": total_downloads,
            "totalReviews": total_reviews,
            "totalSpent": float(total_spent),
            "totalTransactions": total_transactions
        },
        "recentActivity": recent_activity,
        "projects": projects,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "is_admin": current_user.is_admin,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    }

# Admin User Management Endpoints
@app.get("/api/admin/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,  # "admin", "client", "all"
    sort_by: Optional[str] = "created_at",  # created_at, name, email
    sort_order: Optional[str] = "desc",  # asc, desc
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all users for admin management"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = db.query(User)
    
    # Apply search filter
    if search:
        query = query.filter(
            User.name.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%")
        )
    
    # Apply role filter
    if role == "admin":
        query = query.filter(User.is_admin == True)
    elif role == "client":
        query = query.filter(User.is_client == True)
    
    # Apply sorting
    if sort_by == "name":
        if sort_order == "asc":
            query = query.order_by(User.name.asc())
        else:
            query = query.order_by(User.name.desc())
    elif sort_by == "email":
        if sort_order == "asc":
            query = query.order_by(User.email.asc())
        else:
            query = query.order_by(User.email.desc())
    else:  # default: created_at
        if sort_order == "asc":
            query = query.order_by(User.created_at.asc())
        else:
            query = query.order_by(User.created_at.desc())
    
    users = query.offset(skip).limit(limit).all()
    return users

@app.get("/api/admin/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific user by ID"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@app.post("/api/admin/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    email = user_data.get("email")
    password = user_data.get("password")
    name = user_data.get("name")
    is_admin = user_data.get("is_admin", False)
    is_client = user_data.get("is_client", True)
    
    if not email or not password or not name:
        raise HTTPException(status_code=400, detail="Email, password, and name are required")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
        is_client=is_client,
        is_admin=is_admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send welcome notification
    create_notification(
        db=db,
        user_id=new_user.id,
        title="Welcome to JarvisTrade!",
        message="Thank you for joining our platform. Explore our premium trading tools and services to enhance your trading strategy.",
        notification_type="info",
        data={"welcome": True, "registration_date": new_user.created_at.isoformat()}
    )
    
    # Create access token
    access_token = create_access_token(data={"sub": new_user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "is_client": new_user.is_client,
            "is_admin": new_user.is_admin
        }
    }

@app.put("/api/admin/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user information (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Prevent admin from removing their own admin status
    if user_id == current_user.id and user_update.get("is_admin") == False:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove your own admin privileges"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if "name" in user_update:
        user.name = user_update["name"]
    if "email" in user_update:
        # Check if email is already taken by another user
        existing_user = db.query(User).filter(
            User.email == user_update["email"],
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="Email already taken")
        user.email = user_update["email"]
    if "is_admin" in user_update:
        user.is_admin = user_update["is_admin"]
    if "is_client" in user_update:
        user.is_client = user_update["is_client"]
    if "password" in user_update and user_update["password"]:
        if len(user_update["password"]) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        user.hashed_password = get_password_hash(user_update["password"])
    
    db.commit()
    db.refresh(user)
    
    return user

@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has any transactions or other important data
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).count()
    if transactions > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete user with existing transactions. Consider deactivating instead."
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@app.get("/api/admin/users/{user_id}/stats")
async def get_user_stats(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user statistics (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user statistics
    total_transactions = db.query(Transaction).filter(Transaction.user_id == user_id).count()
    total_spent = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.status == "success"
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    total_reviews = db.query(Review).filter(Review.user_id == user_id).count()
    
    # Get recent activity
    recent_transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(Transaction.created_at.desc()).limit(5).all()
    
    recent_reviews = db.query(Review).filter(
        Review.user_id == user_id
    ).order_by(Review.created_at.desc()).limit(5).all()
    
    return {
        "user_id": user_id,
        "total_transactions": total_transactions,
        "total_spent": float(total_spent),
        "total_reviews": total_reviews,
        "recent_transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            } for t in recent_transactions
        ],
        "recent_reviews": [
            {
                "id": r.id,
                "rating": r.rating,
                "comment": r.comment[:100] + "..." if len(r.comment) > 100 else r.comment,
                "created_at": r.created_at.isoformat()
            } for r in recent_reviews
        ]
    }

@app.post("/api/auth/login")
async def login(credentials: dict, request: Request, db: Session = Depends(get_db)):
    """Login endpoint with location detection"""
    email = credentials.get("email")
    password = credentials.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Detect user's location and update currency information
    try:
        user_country = await get_user_country(request)
        currency = determine_payment_currency(user_country)
        currency_symbol = "₦" if currency == "NGN" else "$"
        
        # Update user's location information
        user.country = user_country
        user.currency = currency
        user.currency_symbol = currency_symbol
        db.commit()
        
        user_logger.info(f"User {user.email} location detected: {user_country}, Currency: {currency}")
        
    except Exception as e:
        user_logger.error(f"Error detecting user location: {e}")
        # Keep default values if location detection fails
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_client": user.is_client,
            "is_admin": user.is_admin,
            "country": user.country,
            "currency": user.currency,
            "currency_symbol": user.currency_symbol
        }
    }

@app.post("/api/auth/register")
async def register(user_data: dict, request: Request, db: Session = Depends(get_db)):
    """Register a new user with location detection"""
    email = user_data.get("email")
    password = user_data.get("password")
    name = user_data.get("name")
    
    if not email or not password or not name:
        raise HTTPException(status_code=400, detail="Email, password, and name are required")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    
    # Detect user's location for currency settings
    try:
        user_country = await get_user_country(request)
        currency = determine_payment_currency(user_country)
        currency_symbol = "₦" if currency == "NGN" else "$"
        
        user_logger.info(f"New user {email} location detected: {user_country}, Currency: {currency}")
        
    except Exception as e:
        user_logger.error(f"Error detecting user location during registration: {e}")
        user_country = "US"
        currency = "USD"
        currency_symbol = "$"
    
    # Create new user with location information
    hashed_password = get_password_hash(password)
    
    new_user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
        is_client=True,
        is_admin=False,
        country=user_country,
        currency=currency,
        currency_symbol=currency_symbol,
        email_verified=True  # Mark email as verified by default
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send welcome email
    try:
        await email_service.send_welcome_email(
            user_email=new_user.email,
            user_name=new_user.name
        )
        user_logger.info(f"Welcome email sent to {new_user.email}")
    except Exception as e:
        user_logger.error(f"Failed to send welcome email to {new_user.email}: {e}")
        # Continue with registration even if email fails
    
    # Create access token for auto-login
    access_token = create_access_token(data={"sub": new_user.id})
    
    return {
        "message": "User created successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "is_client": new_user.is_client,
            "is_admin": new_user.is_admin,
            "country": new_user.country,
            "currency": new_user.currency,
            "currency_symbol": new_user.currency_symbol
        }
    }

@app.post("/api/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email to user"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Don't reveal if user exists or not for security
            return {"message": "If an account with that email exists, a password reset link has been sent.", "success": True}
        
        # Generate password reset token
        reset_token = str(uuid.uuid4())
        reset_expires = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        
        # Update user with reset token
        user.password_reset_token = reset_token
        user.password_reset_expires = reset_expires
        db.commit()
        
        # Create reset URL
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"
        
        # Send password reset email
        email_sent = await email_service.send_password_reset_email(
            user_email=user.email,
            user_name=user.name,
            reset_url=reset_url,
            expires_at=reset_expires
        )
        
        if email_sent:
            user_logger.info(f"Password reset email sent to {user.email}")
            return {"message": "Password reset link has been sent to your email.", "success": True}
        else:
            # If email fails, still return success to prevent user enumeration
            user_logger.warning(f"Password reset email failed for {user.email}")
            return {"message": "If an account with that email exists, a password reset link has been sent.", "success": True}
            
    except Exception as e:
        user_logger.error(f"Error in forgot password for {request.email}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process password reset request")

@app.post("/api/auth/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset user password using reset token"""
    try:
        # Find user by reset token
        user = db.query(User).filter(
            User.password_reset_token == request.token,
            User.password_reset_expires > datetime.utcnow()
        ).first()
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Update password and clear reset token
        user.hashed_password = get_password_hash(request.new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.commit()
        
        user_logger.info(f"Password reset successful for {user.email}")
        return {"message": "Password has been reset successfully.", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        user_logger.error(f"Error resetting password: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password")



# Helper function to process free products
async def process_free_products(cart_items: list, current_user: User, db: Session):
    """Process free products and add them to user's purchased items"""
    try:
        app_logger.info(f"Processing {len(cart_items)} free products for user {current_user.id}")
        
        # Create a transaction record for free products
        transaction_ref = f"FREE_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
        
        transaction = Transaction(
            user_id=current_user.id,
            paystack_reference=transaction_ref,
            amount=0.0,
            currency="USD",
            status="success",  # Mark as successful immediately for free products
            payment_data=json.dumps({"type": "free_product", "items": cart_items}),
            purchased_items=json.dumps(cart_items)
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Create order items for each product
        for item in cart_items:
            order_item = OrderItem(
                transaction_id=transaction.id,
                product_id=item["id"],
                quantity=item["quantity"],
                price=0.0,  # Free products have 0 price
                is_rental=item.get("is_rental", False),
                rental_duration_days=item.get("rental_duration_days")
            )
            db.add(order_item)
        
        db.commit()
        
        # Create notification for successful free product acquisition
        product_names = [item.get("name", "Product") for item in cart_items]
        product_list = ", ".join(product_names)
        
        create_notification(
            db=db,
            user_id=current_user.id,
            title="Free Products Added!",
            message=f"Congratulations! You've successfully added {product_list} to your account. You can now download and use these products from your dashboard.",
            notification_type="success",
            data={
                "transaction_id": transaction.id,
                "products": cart_items,
                "type": "free_products"
            }
        )
        
        app_logger.info(f"Free products processed successfully for user {current_user.id}")
        
        return {
            "success": True,
            "message": f"Free products added successfully! {len(cart_items)} product(s) added to your account.",
            "transaction_id": transaction.id,
            "products": cart_items,
            "type": "free_products"
        }
        
    except Exception as e:
        app_logger.error(f"Error processing free products: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process free products: {str(e)}")

@app.post("/api/checkout")
async def checkout(
    checkout_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize Paystack payment using stored user location"""
    try:
        # Extract cart items and total from checkout data
        cart_items = checkout_data.get("items", [])
        total_amount = checkout_data.get("totalAmount", 0)
        
        app_logger.info(f"Cart items received: {cart_items}")
        app_logger.info(f"Total amount: {total_amount}")
        
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Validate cart items structure
        for item in cart_items:
            if not isinstance(item, dict):
                raise HTTPException(status_code=400, detail="Invalid cart item format")
            if "id" not in item or "quantity" not in item or "price" not in item:
                raise HTTPException(status_code=400, detail="Cart items missing required fields")
        
        # Handle free products (total_amount = 0)
        if total_amount == 0:
            return await process_free_products(cart_items, current_user, db)
        
        # Use stored user location and currency
        user_country = current_user.country
        currency = current_user.currency
        
        app_logger.info(f"User country: {user_country}, Currency: {currency}")
        
        # If USD currency, redirect to MQL5 seller page
        if currency == "USD":
            mql5_url = "https://www.mql5.com/en/users/PerpetualRalph/seller"
            return {
                "success": True,
                "redirect": True,
                "redirect_url": mql5_url,
                "message": "USD payments are currently processed through our MQL5 seller page",
                "currency": currency,
                "country": user_country
            }
        
        # For NGN payments, proceed with Paystack
        if currency == "NGN":
            # Generate unique transaction reference
            transaction_ref = f"JARVIS_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
            
            amount_in_smallest_unit = int(total_amount * 100)  # Convert to kobo for NGN
            
            # Prepare Paystack request data for NGN
            paystack_data = {
                "email": current_user.email,
                "currency": currency,
                "amount": amount_in_smallest_unit,
                "reference": transaction_ref,
                "callback_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/payment/success?reference={transaction_ref}",
                "metadata": {
                    "user_id": current_user.id,
                    "cart_items": cart_items,
                    "total_amount": total_amount,
                    "country": user_country
                }
            }
            
            # Make request to Paystack
            paystack_url = "https://api.paystack.co/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(paystack_url, json=paystack_data, headers=headers) as response:
                    response_data = await response.json()
                    safe_log("payment", "info", f"Paystack Response: {response_data}")
                    
                    if response.status == 200:
                        paystack_response = response_data
                        
                        # Create transaction record in database
                        transaction = Transaction(
                            user_id=current_user.id,
                            paystack_reference=transaction_ref,
                            amount=total_amount,
                            currency=currency,
                            status="pending",
                            payment_data=json.dumps(paystack_response["data"]),
                            purchased_items=json.dumps(cart_items)
                        )
                        
                        db.add(transaction)
                        db.commit()
                        db.refresh(transaction)
                        
                        # Create order items for each product
                        for item in cart_items:
                            order_item = OrderItem(
                                transaction_id=transaction.id,
                                product_id=item["id"],
                                quantity=item["quantity"],
                                price=item["price"],
                                is_rental=item.get("is_rental", False),
                                rental_duration_days=item.get("rental_duration_days")
                            )
                            db.add(order_item)
                        
                        db.commit()
                        
                        # Create licenses for each product purchase/rental
                        for item in cart_items:
                            # Generate license ID
                            license_id = f"LIC-{uuid.uuid4().hex[:8].upper()}"
                            
                            # Check if this is a rental
                            is_rental = item.get("is_rental", False)
                            expires_at = None
                            
                            if is_rental:
                                # Set expiry date for rental based on actual rental duration
                                rental_duration = item.get("rental_duration_days", 30)
                                expires_at = datetime.utcnow() + timedelta(days=rental_duration)
                                app_logger.info(f"Creating rental license with {rental_duration} days duration, expires at: {expires_at}")
                            
                            license_obj = License(
                                license_id=license_id,
                                user_id=current_user.id,
                                product_id=item["id"],
                                transaction_id=transaction.id,
                                is_active=True,
                                expires_at=expires_at,
                                is_rental=is_rental
                            )
                            db.add(license_obj)
                        
                        db.commit()
                        
                        return {
                            "success": True,
                            "data": paystack_response["data"],
                            "message": "Payment initialized successfully",
                            "currency": currency,
                            "country": user_country
                        }
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Paystack error: {response_data}"
                        )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported currency: {currency}"
            )
            
    except Exception as e:
        app_logger.error(f"Checkout error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize payment: {str(e)}"
        )

@app.post("/api/webhook/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack webhook callbacks"""
    try:
        # Get the webhook data
        webhook_data = await request.json()
        
        # Verify the webhook signature (you should implement this for security)
        # signature = request.headers.get("X-Paystack-Signature")
        # if not verify_signature(signature, webhook_data):
        #     raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Extract payment details
        event = webhook_data.get("event")
        data = webhook_data.get("data", {})
        
        if event == "charge.success":
            # Payment was successful
            reference = data.get("reference")
            amount = data.get("amount")
            customer_email = data.get("customer", {}).get("email")
            metadata = data.get("metadata", {})
            
            # Find existing transaction and update status
            transaction = db.query(Transaction).filter(
                Transaction.paystack_reference == reference
            ).first()
            
            if transaction:
                # Update transaction status based on Paystack data
                paystack_status = data.get("status", "success")
                transaction.status = paystack_status
                transaction.payment_data = json.dumps(data)
                db.commit()
                
                safe_log("payment", "info", f"Transaction {reference} status updated to: {paystack_status}")
                
                # Check if this is a retry payment and update original transaction
                # First check metadata from Paystack
                original_transaction_id = None
                if metadata.get("is_retry_payment") and metadata.get("original_transaction_id"):
                    original_transaction_id = metadata.get("original_transaction_id")
                    safe_log("payment", "info", f"Found retry payment via metadata: {original_transaction_id}")
                
                # If not found in metadata, check payment_data (our stored data)
                if not original_transaction_id:
                    try:
                        payment_data = json.loads(transaction.payment_data)
                        if payment_data.get("is_retry_payment") and payment_data.get("original_transaction_id"):
                            original_transaction_id = payment_data.get("original_transaction_id")
                            safe_log("payment", "info", f"Found retry payment via payment_data: {original_transaction_id}")
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                if original_transaction_id:
                    original_transaction = db.query(Transaction).filter(
                        Transaction.id == original_transaction_id
                    ).first()
                    
                    if original_transaction and paystack_status == "success":
                        # Update original transaction status to indicate it was resolved by retry
                        original_transaction.status = "resolved_by_retry"
                        original_transaction.payment_data = json.dumps({
                            "resolved_by": reference,
                            "resolved_at": datetime.now().isoformat(),
                            "original_status": original_transaction.status
                        })
                        db.commit()
                        safe_log("payment", "info", f"Original transaction {original_transaction_id} marked as resolved by retry {reference}")
                    elif not original_transaction:
                        safe_log("payment", "warning", f"Original transaction {original_transaction_id} not found")
                else:
                    safe_log("payment", "info", f"No retry payment information found for transaction {reference}")
                
                # Find user by email
                user = db.query(User).filter(User.email == customer_email).first()
                
                if user and paystack_status == "success":
                    # Process the successful payment
                    result = payment_service.process_successful_payment(db, reference, user)
                    
                    if result["success"]:
                        safe_log("payment", "info", f"Payment processed successfully: {reference} - {amount} - {customer_email}")
                        return {"status": "success", "message": "Payment processed successfully"}
                    else:
                        safe_log("payment", "error", f"Payment processing failed: {result['error']}")
                        return {"status": "error", "message": result["error"]}
                else:
                    safe_log("payment", "error", f"User not found for email: {customer_email}")
                    return {"status": "error", "message": "User not found"}
            else:
                safe_log("payment", "error", f"Transaction not found for reference: {reference}")
                return {"status": "error", "message": "Transaction not found"}
            
        elif event == "charge.failed":
            # Payment failed
            reference = data.get("reference")
            safe_log("payment", "error", f"Payment failed: {reference}")
            
            # Update transaction status to failed
            transaction = db.query(Transaction).filter(
                Transaction.paystack_reference == reference
            ).first()
            
            if transaction:
                # Update transaction status based on Paystack data
                paystack_status = data.get("status", "failed")
                transaction.status = paystack_status
                transaction.payment_data = json.dumps(data)
                db.commit()
                safe_log("payment", "info", f"Transaction {reference} status updated to: {paystack_status}")
            else:
                safe_log("payment", "error", f"Transaction not found for reference: {reference}")
            
            return {"status": "failed", "message": "Payment failed"}
            
        else:
            # Handle other events
            safe_log("payment", "warning", f"Unhandled webhook event: {event}")
            return {"status": "ignored", "message": "Event ignored"}
            
    except Exception as e:
        safe_log("payment", "error", f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

# Admin Order Management Endpoints
@app.get("/api/admin/orders", response_model=List[dict])
async def get_all_orders(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,  # "pending", "success", "failed"
    sort_by: Optional[str] = "created_at",  # created_at, amount, status
    sort_order: Optional[str] = "desc",  # asc, desc
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all orders for admin management"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = db.query(Transaction)
    
    # Apply search filter
    if search:
        query = query.join(User).filter(
            User.name.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%") |
            Transaction.paystack_reference.ilike(f"%{search}%")
        )
    
    # Apply status filter
    if status:
        query = query.filter(Transaction.status == status)
    
    # Apply sorting
    if sort_by == "amount":
        if sort_order == "asc":
            query = query.order_by(Transaction.amount.asc())
        else:
            query = query.order_by(Transaction.amount.desc())
    elif sort_by == "status":
        if sort_order == "asc":
            query = query.order_by(Transaction.status.asc())
        else:
            query = query.order_by(Transaction.status.desc())
    else:  # default: created_at
        if sort_order == "asc":
            query = query.order_by(Transaction.created_at.asc())
        else:
            query = query.order_by(Transaction.created_at.desc())
    
    transactions = query.offset(skip).limit(limit).all()
    
    # Format response with user and order item details
    orders = []
    for transaction in transactions:
        user = db.query(User).filter(User.id == transaction.user_id).first()
        
        # Get items from purchased_items field (preferred) or fallback to order_items
        items = []
        if transaction.purchased_items:
            try:
                purchased_items = json.loads(transaction.purchased_items)
                items = [
                    {
                        "id": f"item_{i}",
                        "product_name": item.get("product_name", "Unknown Product"),
                        "product_id": item.get("product_id", ""),
                        "quantity": item.get("quantity", 1),
                        "price": item.get("price", 0),
                        "total": item.get("total", 0),
                        "category": item.get("category", ""),
                        "image": item.get("image", ""),
                        "description": item.get("description", "")
                    }
                    for i, item in enumerate(purchased_items)
                ]
            except (json.JSONDecodeError, TypeError):
                # Fallback to order_items if purchased_items is invalid
                order_items = db.query(OrderItem).filter(OrderItem.transaction_id == transaction.id).all()
                for item in order_items:
                    product = db.query(Product).filter(Product.id == item.product_id).first()
                    items.append({
                        "id": item.id,
                        "product_name": product.name if product else "Unknown Product",
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "price": item.price,
                        "total": item.quantity * item.price
                    })
        else:
            # Fallback to order_items if purchased_items is not available
            order_items = db.query(OrderItem).filter(OrderItem.transaction_id == transaction.id).all()
            for item in order_items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                items.append({
                    "id": item.id,
                    "product_name": product.name if product else "Unknown Product",
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price,
                    "total": item.quantity * item.price
                })
        safe_log("payment", "info", f'Transaction create time: {transaction.created_at}')
        orders.append({
            "id": transaction.id,
            "paystack_reference": transaction.paystack_reference,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "status": transaction.status,
            "created_at": transaction.created_at.isoformat() if isinstance(transaction.created_at, datetime) else None,
            "updated_at": transaction.updated_at.isoformat() if isinstance(transaction.updated_at, datetime) else None,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            } if user else None,
            "items": items,
            "total_items": len(items)
        })
    
    return orders

@app.get("/api/admin/orders/{order_id}", response_model=dict)
async def get_order_by_id(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific order by ID"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    transaction = db.query(Transaction).filter(Transaction.id == order_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Order not found")
    
    user = db.query(User).filter(User.id == transaction.user_id).first()
    
    # Get items from purchased_items field (preferred) or fallback to order_items
    items = []
    if transaction.purchased_items:
        try:
            purchased_items = json.loads(transaction.purchased_items)
            items = [
                {
                    "id": f"item_{i}",
                    "product_name": item.get("product_name", "Unknown Product"),
                    "product_id": item.get("product_id", ""),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price", 0),
                    "total": item.get("total", 0),
                    "category": item.get("category", ""),
                    "image": item.get("image", ""),
                    "description": item.get("description", ""),
                    "product": {
                        "id": item.get("product_id", ""),
                        "name": item.get("product_name", "Unknown Product"),
                        "category": item.get("category", ""),
                        "image": item.get("image", "")
                    }
                }
                for i, item in enumerate(purchased_items)
            ]
        except (json.JSONDecodeError, TypeError):
            # Fallback to order_items if purchased_items is invalid
            order_items = db.query(OrderItem).filter(OrderItem.transaction_id == transaction.id).all()
            for item in order_items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                items.append({
                    "id": item.id,
                    "product_name": product.name if product else "Unknown Product",
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price,
                    "total": item.quantity * item.price,
                    "product": {
                        "id": product.id,
                        "name": product.name,
                        "category": product.category,
                        "image": product.image
                    } if product else None
                })
    else:
        # Fallback to order_items if purchased_items is not available
        order_items = db.query(OrderItem).filter(OrderItem.transaction_id == transaction.id).all()
        for item in order_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            items.append({
                "id": item.id,
                "product_name": product.name if product else "Unknown Product",
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
                "total": item.quantity * item.price,
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "category": product.category,
                    "image": product.image
                } if product else None
            })
    
    return {
        "id": transaction.id,
        "paystack_reference": transaction.paystack_reference,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "status": transaction.status,
        "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
        "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None,
        "payment_data": json.loads(transaction.payment_data) if transaction.payment_data else None,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        } if user else None,
        "items": items,
        "total_items": len(items)
    }

@app.put("/api/admin/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update order status (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        new_status = status_update.get("status")
        if not new_status:
            raise HTTPException(status_code=400, detail="Status is required")
        
        old_status = order.status
        order.status = new_status
        db.commit()
        
        # Send notification to user about order status change
        user = db.query(User).filter(User.id == order.user_id).first()
        if user:
            if new_status == "confirmed":
                title = "Order Confirmed"
                message = f"Your order #{order_id} has been confirmed and is being processed."
                notification_type = "order"
            elif new_status == "declined":
                title = "Order Declined"
                message = f"Your order #{order_id} has been declined. Please contact support for more information."
                notification_type = "error"
            else:
                title = f"Order Status Updated"
                message = f"Your order #{order_id} status has been updated to {new_status}."
                notification_type = "order"
            
            create_notification(
                db=db,
                user_id=user.id,
                title=title,
                message=message,
                notification_type=notification_type,
                data={"order_id": order_id, "old_status": old_status, "new_status": new_status}
            )
        
        return {"success": True, "message": f"Order status updated to {new_status}"}
        
    except Exception as e:
        safe_log("payment", "error", f"Error updating order status: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update order status")



# Blog Post Endpoints
@app.get("/api/blog/posts", response_model=List[BlogPostResponse])
async def get_blog_posts(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = "published",
    featured: Optional[bool] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get blog posts with filtering options"""
    query = db.query(BlogPost)
    
    # Filter by status (default to published)
    if status:
        query = query.filter(BlogPost.status == status)
    
    # Filter by featured
    if featured is not None:
        query = query.filter(BlogPost.is_featured == featured)
    
    # Filter by tag
    if tag:
        query = query.filter(BlogPost.tags.contains(f'"{tag}"'))
    
    # Search in title and content
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                BlogPost.title.ilike(search_term),
                BlogPost.content.ilike(search_term),
                BlogPost.excerpt.ilike(search_term)
            )
        )
    
    # Order by published_at (most recent first) or created_at for drafts
    query = query.order_by(BlogPost.created_at.desc())
    
    posts = query.offset(skip).limit(limit).all()
    
    # Convert JSON fields back to lists
    for post in posts:
        convert_blog_post_json_fields(post)
    
    return posts

@app.get("/api/blog/posts/{post_id}", response_model=BlogPostResponse)
async def get_blog_post(
    post_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific blog post by ID"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Increment view count for published posts
    if post.status == "published":
        post.view_count += 1
        db.commit()
    
    # Convert JSON fields back to lists
    convert_blog_post_json_fields(post)
    
    return post

@app.get("/api/blog/posts/slug/{slug}", response_model=BlogPostResponse)
async def get_blog_post_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get a specific blog post by slug"""
    post = db.query(BlogPost).filter(BlogPost.slug == slug).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Increment view count for published posts
    if post.status == "published":
        post.view_count += 1
        db.commit()
    
    # Convert JSON fields back to lists
    convert_blog_post_json_fields(post)
    
    return post

# Admin Blog Post Endpoints
@app.post("/api/admin/blog/posts", response_model=BlogPostResponse, status_code=201)
async def create_blog_post(
    post: BlogPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new blog post (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Generate slug from title
    slug = post.title.lower().replace(" ", "-").replace("_", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    
    # Ensure unique slug
    counter = 1
    original_slug = slug
    while db.query(BlogPost).filter(BlogPost.slug == slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    # Convert tags to JSON string
    tags_json = json.dumps(post.tags) if post.tags else None
    
    # Convert list fields to JSON strings
    youtube_links_json = json.dumps(post.youtube_links) if post.youtube_links else None
    attached_files_json = json.dumps(post.attached_files) if post.attached_files else None
    gallery_images_json = json.dumps(post.gallery_images) if post.gallery_images else None
    
    blog_post = BlogPost(
        title=post.title,
        slug=slug,
        content=post.content,
        excerpt=post.excerpt,
        featured_image=post.featured_image,
        status=post.status,
        is_featured=post.is_featured,
        tags=tags_json,
        meta_title=post.meta_title,
        meta_description=post.meta_description,
        author_id=current_user.id,
        published_at=datetime.utcnow() if post.status == "published" else None,
        youtube_links=youtube_links_json,
        attached_files=attached_files_json,
        gallery_images=gallery_images_json
    )
    
    db.add(blog_post)
    db.commit()
    db.refresh(blog_post)
    
    # Convert JSON fields back to lists
    convert_blog_post_json_fields(blog_post)
    
    return blog_post

@app.get("/api/admin/blog/posts", response_model=List[BlogPostResponse])
async def get_admin_blog_posts(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all blog posts for admin management"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = db.query(BlogPost)
    
    if status:
        query = query.filter(BlogPost.status == status)
    
    posts = query.order_by(BlogPost.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert JSON fields back to lists
    for post in posts:
        convert_blog_post_json_fields(post)
    
    return posts

@app.get("/api/admin/blog/posts/{post_id}", response_model=BlogPostResponse)
async def get_admin_blog_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific blog post for admin management"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Convert JSON fields back to lists
    convert_blog_post_json_fields(post)
    
    return post

@app.put("/api/admin/blog/posts/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: str,
    post_update: BlogPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a blog post (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Update fields
    update_data = post_update.dict(exclude_unset=True)
    
    # Handle tags conversion
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"])
    
    # Handle list fields conversion to JSON
    list_fields = ["youtube_links", "attached_files", "gallery_images"]
    for field in list_fields:
        if field in update_data:
            update_data[field] = json.dumps(update_data[field])
    
    # Handle slug generation if title is updated
    if "title" in update_data:
        slug = update_data["title"].lower().replace(" ", "-").replace("_", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        
        # Ensure unique slug
        counter = 1
        original_slug = slug
        while db.query(BlogPost).filter(
            BlogPost.slug == slug,
            BlogPost.id != post_id
        ).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        update_data["slug"] = slug
    
    # Handle published_at
    if "status" in update_data and update_data["status"] == "published" and not post.published_at:
        update_data["published_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(post, field, value)
    
    db.commit()
    db.refresh(post)
    
    # Convert JSON fields back to lists
    convert_blog_post_json_fields(post)
    
    return post

@app.delete("/api/admin/blog/posts/{post_id}")
async def delete_blog_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a blog post (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    db.delete(post)
    db.commit()
    
    return {"message": "Blog post deleted successfully"}

@app.get("/api/debug/token")
async def debug_token(request: Request):
    """Debug endpoint to check token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return {"error": "No Authorization header"}
    
    if not auth_header.startswith("Bearer "):
        return {"error": "Invalid Authorization header format"}
    
    token = auth_header.split(" ")[1]
    auth_logger.debug(f"DEBUG: Received token: {token[:20]}...")
    
    try:
        from auth import verify_token
        user_id = verify_token(token)
        if user_id:
            return {"success": True, "user_id": user_id, "token_preview": token[:20]}
        else:
            return {"error": "Token verification failed"}
    except Exception as e:
        return {"error": f"Token verification error: {str(e)}"}



# Blog Like Endpoints
@app.post("/api/blog/posts/{post_id}/like", response_model=BlogLikeResponse)
async def like_blog_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Like a blog post"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Check if user already liked this post
    existing_like = db.query(BlogLike).filter(
        BlogLike.user_id == current_user.id,
        BlogLike.blog_post_id == post_id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="You have already liked this post")
    
    # Create new like
    db_like = BlogLike(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        blog_post_id=post_id
    )
    
    db.add(db_like)
    
    # Update post like count
    post.like_count += 1
    db.commit()
    db.refresh(db_like)
    
    # Send notification to blog post author (if different from liker)
    if post.author_id != current_user.id:
        create_notification(
            db=db,
            user_id=post.author_id,
            title="New Blog Post Like",
            message=f"{current_user.name} liked your blog post '{post.title}'",
            notification_type="info",
            data={"blog_post_id": post_id, "liker_id": current_user.id, "post_title": post.title}
        )
    
    return {
        "id": db_like.id,
        "user_id": db_like.user_id,
        "blog_post_id": db_like.blog_post_id,
        "created_at": db_like.created_at
    }

@app.delete("/api/blog/posts/{post_id}/like")
async def unlike_blog_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unlike a blog post"""
    like = db.query(BlogLike).filter(
        BlogLike.user_id == current_user.id,
        BlogLike.blog_post_id == post_id
    ).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # Update like count
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if post and post.like_count > 0:
        post.like_count -= 1
    
    db.delete(like)
    db.commit()
    
    return {"message": "Post unliked successfully"}

@app.get("/api/blog/posts/{post_id}/likes")
async def get_blog_post_likes(
    post_id: str,
    db: Session = Depends(get_db)
):
    """Get likes for a blog post"""
    likes = db.query(BlogLike).filter(BlogLike.blog_post_id == post_id).all()
    return {"likes": len(likes)}

# Blog Comment Endpoints
@app.post("/api/blog/posts/{post_id}/comments", response_model=BlogCommentResponse)
async def create_blog_comment(
    post_id: str,
    comment: BlogCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a comment on a blog post"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Create comment
    db_comment = BlogComment(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        blog_post_id=post_id,
        content=comment.content,
        parent_comment_id=comment.parent_comment_id
    )
    
    db.add(db_comment)
    
    # Update post comment count
    post.comment_count += 1
    db.commit()
    db.refresh(db_comment)
    
    # Send notification to blog post author (if different from commenter)
    if post.author_id != current_user.id:
        create_notification(
            db=db,
            user_id=post.author_id,
            title="New Blog Post Comment",
            message=f"{current_user.name} commented on your blog post '{post.title}'",
            notification_type="info",
            data={"blog_post_id": post_id, "comment_id": db_comment.id, "commenter_id": current_user.id, "post_title": post.title}
        )
    
    # Send notification to parent comment author (if replying to a comment)
    if comment.parent_comment_id:
        parent_comment = db.query(BlogComment).filter(BlogComment.id == comment.parent_comment_id).first()
        if parent_comment and parent_comment.user_id != current_user.id:
            create_notification(
                db=db,
                user_id=parent_comment.user_id,
                title="New Reply to Your Comment",
                message=f"{current_user.name} replied to your comment on '{post.title}'",
                notification_type="info",
                data={"blog_post_id": post_id, "comment_id": db_comment.id, "replier_id": current_user.id, "post_title": post.title}
            )
    
    return convert_blog_comment_json_fields(db_comment)

@app.get("/api/blog/posts/{post_id}/comments")
async def get_blog_comments(
    post_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get comments for a blog post"""
    comments = db.query(BlogComment).filter(
        BlogComment.blog_post_id == post_id,
        BlogComment.is_approved == True
    ).offset(skip).limit(limit).all()
    
    # Add user info to each comment
    response_data = []
    for comment in comments:
        user = db.query(User).filter(User.id == comment.user_id).first()
        response_data.append({
            "id": comment.id,
            "user_id": comment.user_id,
            "blog_post_id": comment.blog_post_id,
            "parent_comment_id": comment.parent_comment_id,
            "content": comment.content,
            "is_approved": comment.is_approved,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "user_name": user.name if user else "Unknown User",
            "user_email": user.email if user else ""
        })
    
    return {"comments": response_data}

@app.put("/api/blog/comments/{comment_id}")
async def update_blog_comment(
    comment_id: str,
    comment_update: BlogCommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment (only by the author)"""
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    
    comment.content = comment_update.content
    comment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(comment)
    
    return comment

@app.delete("/api/blog/comments/{comment_id}")
async def delete_blog_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (only by the author or admin)"""
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    
    # Update comment count
    post = db.query(BlogPost).filter(BlogPost.id == comment.blog_post_id).first()
    if post and post.comment_count > 0:
        post.comment_count -= 1
    
    db.delete(comment)
    db.commit()
    
    return {"message": "Comment deleted successfully"}

# Blog post file upload endpoint
@app.post("/api/upload-blog-file")
async def upload_blog_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a file for blog post attachment (Admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Validate file size (10MB limit)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 10MB"
        )
    
    try:
        # Create uploads/blog directory if it doesn't exist
        os.makedirs("./uploads/blog", exist_ok=True)
        
        # Create unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("./uploads/blog", unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return the URL with full backend URL
        base_url = "http://localhost:8000"
        file_url = f"{base_url}/uploads/blog/{unique_filename}"
        
        return {
            "success": True,
            "file_url": file_url,
            "filename": unique_filename,
            "original_name": file.filename
        }
        
    except Exception as e:
        blog_logger.error(f"Blog file upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload file"
        )

# Admin notification management endpoints
@app.post("/api/admin/notifications/send")
async def send_admin_notification(
    notification_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send notification to specific users or all users (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        title = notification_data.get("title")
        message = notification_data.get("message")
        notification_type = notification_data.get("type", "info")
        user_ids = notification_data.get("user_ids", [])  # Empty list means all users
        data = notification_data.get("data")
        
        if not title or not message:
            raise HTTPException(status_code=400, detail="Title and message are required")
        
        if user_ids:
            # Send to specific users
            for user_id in user_ids:
                create_notification(
                    db=db,
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    data=data
                )
        else:
            # Send to all users
            all_users = db.query(User).filter(User.is_admin == False).all()
            for user in all_users:
                create_notification(
                    db=db,
                    user_id=user.id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    data=data
                )
        
        return {
            "success": True,
            "message": f"Notification sent to {len(user_ids) if user_ids else len(all_users)} users"
        }
        
    except Exception as e:
        project_logger.error(f"Error sending admin notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

@app.get("/api/admin/notifications/stats")
async def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification statistics (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        total_notifications = db.query(Notification).count()
        unread_notifications = db.query(Notification).filter(Notification.is_read == False).count()
        
        # Notifications by type
        type_stats = db.query(
            Notification.type,
            func.count(Notification.id).label('count')
        ).group_by(Notification.type).all()
        
        # Recent notifications (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_notifications = db.query(Notification).filter(
            Notification.created_at >= week_ago
        ).count()
        
        return {
            "total_notifications": total_notifications,
            "unread_notifications": unread_notifications,
            "recent_notifications": recent_notifications,
            "type_stats": [{"type": stat.type, "count": stat.count} for stat in type_stats]
        }
        
    except Exception as e:
        project_logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification stats")

@app.post("/api/admin/notifications/send-review-prompts")
async def send_review_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send review prompts to users who purchased products (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get users who purchased products but haven't reviewed them
        # This is a simplified version - in production you'd want to check purchase dates
        purchased_products = db.query(
            Transaction.user_id,
            Transaction.product_id
        ).filter(
            Transaction.status == "success"
        ).distinct().all()
        
        prompts_sent = 0
        for user_id, product_id in purchased_products:
            send_review_prompt(db, user_id, product_id)
            prompts_sent += 1
        
        return {
            "success": True,
            "message": f"Review prompts sent to {prompts_sent} users"
        }
        
    except Exception as e:
        project_logger.error(f"Error sending review prompts: {e}")
        raise HTTPException(status_code=500, detail="Failed to send review prompts")

# Helper function to send review prompts
def send_review_prompt(db: Session, user_id: str, product_id: str, days_after_purchase: int = 7):
    """Send a review prompt to a user who purchased a product"""
    try:
        # Check if user has already reviewed this product
        existing_review = db.query(Review).filter(
            Review.user_id == user_id,
            Review.product_id == product_id
        ).first()
        
        if existing_review:
            return  # User already reviewed
        
        # Check if we've already sent a review prompt
        existing_prompt = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.type == "review_prompt",
            Notification.data.contains(f'"product_id": "{product_id}"')
        ).first()
        
        if existing_prompt:
            return  # Already sent prompt
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return
        
        create_notification(
            db=db,
            user_id=user_id,
            title="Share Your Experience",
            message=f"How was your experience with {product.name}? Leave a review to help other traders!",
            notification_type="review_prompt",
            data={"product_id": product_id, "product_name": product.name}
        )
        
    except Exception as e:
        project_logger.error(f"Error sending review prompt: {e}")

# Notification preference endpoints
@app.get("/api/users/me/notification-preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's notification preferences"""
    try:
        # Parse notification preferences from JSON string
        preferences = {}
        if current_user.notification_preferences:
            try:
                preferences = json.loads(current_user.notification_preferences)
            except:
                preferences = {}
        
        return {
            "notification_preferences": preferences,
            "email_notifications": current_user.email_notifications,
            "push_notifications": current_user.push_notifications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification preferences: {str(e)}")

@app.put("/api/users/me/notification-preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's notification preferences"""
    try:
        # Update notification preferences
        if preferences_update.notification_preferences is not None:
            current_user.notification_preferences = json.dumps(preferences_update.notification_preferences)
        
        if preferences_update.email_notifications is not None:
            current_user.email_notifications = preferences_update.email_notifications
        
        if preferences_update.push_notifications is not None:
            current_user.push_notifications = preferences_update.push_notifications
        
        db.commit()
        
        # Return updated preferences
        preferences = {}
        if current_user.notification_preferences:
            try:
                preferences = json.loads(current_user.notification_preferences)
            except:
                preferences = {}
        
        return {
            "notification_preferences": preferences,
            "email_notifications": current_user.email_notifications,
            "push_notifications": current_user.push_notifications
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update notification preferences: {str(e)}")

# Public Exchange Rate Endpoint (for frontend currency conversion)
@app.get("/api/exchange-rates")
async def get_public_exchange_rates(db: Session = Depends(get_db)):
    """Get active exchange rates for frontend currency conversion"""
    exchange_rates = db.query(ExchangeRate).filter(ExchangeRate.is_active == True).all()
    
    # Convert to a more frontend-friendly format
    rates_dict = {}
    for rate in exchange_rates:
        if rate.from_currency == "USD":
            rates_dict[rate.to_currency] = rate.rate
    
    return {
        "rates": rates_dict,
        "base_currency": "USD",
        "timestamp": datetime.utcnow().isoformat()
    }

# Exchange Rate Management Endpoints (Admin Only)
@app.get("/api/admin/exchange-rates", response_model=List[ExchangeRateResponse])
async def get_admin_exchange_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all exchange rates (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    exchange_rates = db.query(ExchangeRate).order_by(ExchangeRate.from_currency, ExchangeRate.to_currency).all()
    return exchange_rates

@app.post("/api/admin/exchange-rates", response_model=ExchangeRateResponse)
async def create_exchange_rate(
    exchange_rate: ExchangeRateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new exchange rate (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if exchange rate already exists
    existing_rate = db.query(ExchangeRate).filter(
        ExchangeRate.from_currency == exchange_rate.from_currency,
        ExchangeRate.to_currency == exchange_rate.to_currency
    ).first()
    
    if existing_rate:
        raise HTTPException(status_code=409, detail="Exchange rate for this currency pair already exists")
    
    new_rate = ExchangeRate(
        from_currency=exchange_rate.from_currency,
        to_currency=exchange_rate.to_currency,
        rate=exchange_rate.rate,
        is_active=exchange_rate.is_active
    )
    
    db.add(new_rate)
    db.commit()
    db.refresh(new_rate)
    
    return new_rate

@app.put("/api/admin/exchange-rates/{rate_id}", response_model=ExchangeRateResponse)
async def update_exchange_rate(
    rate_id: str,
    exchange_rate_update: ExchangeRateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an exchange rate (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    rate = db.query(ExchangeRate).filter(ExchangeRate.id == rate_id).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Exchange rate not found")
    
    if exchange_rate_update.rate is not None:
        rate.rate = exchange_rate_update.rate
    
    if exchange_rate_update.is_active is not None:
        rate.is_active = exchange_rate_update.is_active
    
    db.commit()
    db.refresh(rate)
    
    return rate

@app.delete("/api/admin/exchange-rates/{rate_id}")
async def delete_exchange_rate(
    rate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an exchange rate (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    rate = db.query(ExchangeRate).filter(ExchangeRate.id == rate_id).first()
    if not rate:
        raise HTTPException(status_code=404, detail="Exchange rate not found")
    
    db.delete(rate)
    db.commit()
    
    return {"message": "Exchange rate deleted successfully"}

# Currency conversion utility function
def convert_currency(amount: float, from_currency: str, to_currency: str, db: Session) -> float:
    """Convert amount from one currency to another using stored exchange rates"""
    if from_currency == to_currency:
        return amount
    
    # Find the exchange rate
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.from_currency == from_currency,
        ExchangeRate.to_currency == to_currency,
        ExchangeRate.is_active == True
    ).first()
    
    if not rate:
        # If no direct rate, try reverse rate
        reverse_rate = db.query(ExchangeRate).filter(
            ExchangeRate.from_currency == to_currency,
            ExchangeRate.to_currency == from_currency,
            ExchangeRate.is_active == True
        ).first()
        
        if reverse_rate:
            return amount / reverse_rate.rate
        else:
            # Default fallback - return original amount
            return amount
    
    return amount * rate.rate

def get_currency_symbol(currency: str) -> str:
    """Get the currency symbol for a given currency code"""
    currency_symbols = {
        "USD": "$",
        "NGN": "₦",
        "EUR": "€",
        "GBP": "£"
    }
    return currency_symbols.get(currency, "$")

def format_currency_for_notification(amount: float, from_currency: str, to_currency: str, db: Session) -> str:
    """Format currency amount for notification messages based on user's currency preference"""
    if from_currency == to_currency:
        # Same currency, just format with appropriate symbol
        if to_currency == "USD":
            return f"${amount:,.2f}"
        elif to_currency == "NGN":
            return f"₦{amount:,.0f}"
        else:
            return f"${amount:,.2f}"  # Default to USD format
    
    # Convert currency
    converted_amount = convert_currency(amount, from_currency, to_currency, db)
    
    # Format with appropriate symbol and precision
    if to_currency == "USD":
        return f"${converted_amount:,.2f}"
    elif to_currency == "NGN":
        return f"₦{converted_amount:,.0f}"
    else:
        return f"${converted_amount:,.2f}"  # Default to USD format

# Project Management Endpoints
@app.get("/api/users/me/projects", response_model=List[ProjectRequestResponse])
async def get_user_projects(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all project requests for the current user"""
    query = db.query(ProjectRequest).filter(ProjectRequest.user_id == current_user.id)
    
    if status:
        query = query.filter(ProjectRequest.status == status)
    
    projects = query.order_by(ProjectRequest.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert JSON fields and add counts
    for project in projects:
        if project.platforms:
            project.platforms = json.loads(project.platforms)
        if project.file_uploads:
            project.file_uploads = json.loads(project.file_uploads)
        
        # Add counts for responses, invoices, and progress
        responses_count = db.query(ProjectResponse).filter(
            ProjectResponse.project_request_id == project.id
        ).count()
        
        invoices_count = db.query(ProjectInvoice).filter(
            ProjectInvoice.project_request_id == project.id
        ).count()
        
        progress_count = db.query(ProjectProgress).filter(
            ProjectProgress.project_request_id == project.id
        ).count()
        
        # Add counts as attributes
        project.responses_count = responses_count
        project.invoices_count = invoices_count
        project.progress_count = progress_count
    
    return projects

@app.get("/api/users/me/projects/{project_id}", response_model=ProjectDashboardData)
async def get_user_project_dashboard(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive project dashboard data for a specific project"""
    # Get the project request - allow admins to access any project
    if current_user.is_admin:
        project_request = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id
        ).first()
    else:
        project_request = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id,
            ProjectRequest.user_id == current_user.id
        ).first()
    
    if not project_request:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert JSON fields
    if project_request.platforms:
        project_request.platforms = json.loads(project_request.platforms)
    if project_request.file_uploads:
        project_request.file_uploads = json.loads(project_request.file_uploads)
    
    # Get project responses
    responses = db.query(ProjectResponse).filter(
        ProjectResponse.project_request_id == project_id
    ).order_by(ProjectResponse.created_at.desc()).all()
    
    # Add admin info to responses
    for response in responses:
        admin = db.query(User).filter(User.id == response.admin_id).first()
        response.admin_name = admin.name if admin else "Admin"
        response.admin_email = admin.email if admin else "admin@jarvistrade.com"
    
    # Get project invoices
    invoices = db.query(ProjectInvoice).filter(
        ProjectInvoice.project_request_id == project_id
    ).order_by(ProjectInvoice.created_at.desc()).all()
    
    # Get project progress updates
    progress_updates = db.query(ProjectProgress).filter(
        ProjectProgress.project_request_id == project_id
    ).order_by(ProjectProgress.created_at.desc()).all()
    
    # Add admin info to progress updates
    for progress in progress_updates:
        admin = db.query(User).filter(User.id == progress.admin_id).first()
        progress.admin_name = admin.name if admin else "Admin"
        progress.admin_email = admin.email if admin else "admin@jarvistrade.com"
        if progress.attachments:
            progress.attachments = json.loads(progress.attachments)
    
    # Calculate totals
    total_invoiced = sum(invoice.amount for invoice in invoices)
    total_paid = sum(invoice.amount for invoice in invoices if invoice.status == "paid")
    
    # Calculate overall progress
    latest_progress = progress_updates[0] if progress_updates else None
    overall_progress = latest_progress.percentage_complete if latest_progress else 0
    
    return ProjectDashboardData(
        project_request=project_request,
        responses=responses,
        invoices=invoices,
        progress_updates=progress_updates,
        latest_progress=latest_progress,
        total_invoiced=total_invoiced,
        total_paid=total_paid,
        overall_progress=overall_progress
    )

@app.post("/api/users/me/projects/{project_id}/responses/{response_id}/approve")
async def approve_project_response(
    project_id: str,
    response_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve a project response (quote) from admin"""
    # Verify project belongs to user or user is admin
    if current_user.is_admin:
        project = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id
        ).first()
    else:
        project = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id,
            ProjectRequest.user_id == current_user.id
        ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get the response
    response = db.query(ProjectResponse).filter(
        ProjectResponse.id == response_id,
        ProjectResponse.project_request_id == project_id
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Only allow approval for quotes
    if response.response_type != "quote":
        raise HTTPException(status_code=400, detail="Only quotes can be approved")
    
    # Approve the response
    response.is_approved_by_client = True
    db.commit()
    
    # Create notification for admin
    create_notification(
        db=db,
        user_id=response.admin_id,
        title="Project Quote Approved",
        message=f"Your quote for project '{project.project_title}' has been approved by the client.",
        notification_type="success",
        data={"project_id": project_id, "response_id": response_id}
    )
    
    return {"message": "Response approved successfully"}

@app.post("/api/users/me/projects/{project_id}/responses/{response_id}/reject")
async def reject_project_response(
    project_id: str,
    response_id: str,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a project response (quote) from admin"""
    # Verify project belongs to user or user is admin
    if current_user.is_admin:
        project = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id
        ).first()
    else:
        project = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id,
            ProjectRequest.user_id == current_user.id
        ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get the response
    response = db.query(ProjectResponse).filter(
        ProjectResponse.id == response_id,
        ProjectResponse.project_request_id == project_id
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Only allow rejection for quotes
    if response.response_type != "quote":
        raise HTTPException(status_code=400, detail="Only quotes can be rejected")
    
    # Reject the response
    response.is_approved_by_client = False
    db.commit()
    
    # Create notification for admin
    create_notification(
        db=db,
        user_id=response.admin_id,
        title="Project Quote Rejected",
        message=f"Your quote for project '{project.project_title}' was rejected. Reason: {reason}",
        notification_type="warning",
        data={"project_id": project_id, "response_id": response_id, "reason": reason}
    )
    
    return {"message": "Response rejected successfully"}

@app.get("/api/users/me/projects/{project_id}/invoices", response_model=List[ProjectInvoiceResponse])
async def get_project_invoices(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all invoices for a specific project"""
    # Verify project belongs to user or user is admin
    if current_user.is_admin:
        project = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id
        ).first()
    else:
        project = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id,
            ProjectRequest.user_id == current_user.id
        ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    invoices = db.query(ProjectInvoice).filter(
        ProjectInvoice.project_request_id == project_id
    ).order_by(ProjectInvoice.created_at.desc()).all()
    
    return invoices

@app.get("/api/users/me/projects/{project_id}/progress", response_model=List[ProjectProgressResponse])
async def get_project_progress(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all progress updates for a specific project"""
    # Verify project belongs to user or user is admin
    if current_user.is_admin:
        project = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id
        ).first()
    else:
        project = db.query(ProjectRequest).filter(
            ProjectRequest.id == project_id,
            ProjectRequest.user_id == current_user.id
        ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    progress_updates = db.query(ProjectProgress).filter(
        ProjectProgress.project_request_id == project_id
    ).order_by(ProjectProgress.created_at.desc()).all()
    
    # Add admin info to progress updates
    for progress in progress_updates:
        admin = db.query(User).filter(User.id == progress.admin_id).first()
        progress.admin_name = admin.name if admin else "Admin"
        progress.admin_email = admin.email if admin else "admin@jarvistrade.com"
        if progress.attachments:
            progress.attachments = json.loads(progress.attachments)
    
    return progress_updates

# Admin Project Management Endpoints
@app.post("/api/admin/projects/{project_id}/responses", response_model=ProjectResponseResponse)
async def create_project_response(
    project_id: str,
    response_data: ProjectResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a project response (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Verify project exists
    project = db.query(ProjectRequest).filter(ProjectRequest.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create the response
    response = ProjectResponse(
        project_request_id=project_id,
        admin_id=current_user.id,
        parent_response_id=response_data.parent_response_id,
        response_type=response_data.response_type,
        title=response_data.title,
        message=response_data.message,
        proposed_price=response_data.proposed_price,
        estimated_duration=response_data.estimated_duration,
        terms_conditions=response_data.terms_conditions,
        is_approved_by_client=response_data.is_approved_by_client,
        is_approved_by_admin=response_data.is_approved_by_admin
    )
    
    db.add(response)
    db.commit()
    db.refresh(response)
    
    # Add admin info
    response.admin_name = current_user.name
    response.admin_email = current_user.email
    
    # Create notification for client
    if project.user_id:
        create_notification(
            db=db,
            user_id=project.user_id,
            title=f"New {response_data.response_type.title()} for Your Project",
            message=f"You have received a new {response_data.response_type} for your project '{project.project_title}'.",
            notification_type="info",
            data={"project_id": project_id, "response_id": response.id, "response_type": response_data.response_type}
        )
    
    return response

@app.get("/api/admin/projects/{project_id}/responses", response_model=List[ProjectResponseResponse])
async def get_project_responses(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all responses for a project (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Verify project exists
    project = db.query(ProjectRequest).filter(ProjectRequest.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all responses for the project
    responses = db.query(ProjectResponse).filter(
        ProjectResponse.project_request_id == project_id
    ).order_by(ProjectResponse.created_at.desc()).all()
    
    # Add admin info to each response
    for response in responses:
        admin = db.query(User).filter(User.id == response.admin_id).first()
        if admin:
            response.admin_name = admin.name
            response.admin_email = admin.email
    
    return responses

@app.post("/api/users/me/projects/{project_id}/messages", response_model=ProjectResponseResponse)
async def create_user_project_message(
    project_id: str,
    message_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a message from user to admin about their project"""
    # Verify project exists and belongs to user
    project = db.query(ProjectRequest).filter(
        ProjectRequest.id == project_id,
        ProjectRequest.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create the message as a response from user
    response = ProjectResponse(
        project_request_id=project_id,
        admin_id=current_user.id,  # User is acting as the sender
        parent_response_id=message_data.get("parent_response_id"),
        response_type="message",
        title=message_data.get("title", "User Message"),
        message=message_data.get("message", ""),
        is_approved_by_client=True,
        is_approved_by_admin=True
    )
    
    db.add(response)
    db.commit()
    db.refresh(response)
    
    # Add user info to response
    response.admin_name = current_user.name
    response.admin_email = current_user.email
    
    # Create notification for admins about new user message
    admins = db.query(User).filter(User.is_admin == True).all()
    for admin in admins:
        create_notification(
            db=db,
            user_id=admin.id,
            title=f"New Message from {current_user.name}",
            message=f"User {current_user.name} sent a message about project '{project.project_title}'",
            notification_type="info",
            data={"project_id": project_id, "user_id": current_user.id, "project_title": project.project_title}
        )
    
    return response

@app.post("/api/admin/projects/{project_id}/invoices", response_model=ProjectInvoiceResponse)
async def create_project_invoice(
    project_id: str,
    invoice_data: ProjectInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a project invoice (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Verify project exists
    project = db.query(ProjectRequest).filter(ProjectRequest.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create the invoice
    invoice = ProjectInvoice(
        project_request_id=project_id,
        invoice_number=invoice_data.invoice_number,
        amount=invoice_data.amount,
        currency=invoice_data.currency,
        description=invoice_data.description,
        status=invoice_data.status,
        due_date=invoice_data.due_date,
        payment_method=invoice_data.payment_method
    )
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    # Create notification for client
    if project.user_id:
        create_notification(
            db=db,
            user_id=project.user_id,
            title="New Invoice Available",
            message=f"A new invoice has been generated for your project '{project.project_title}'.",
            notification_type="payment",
            data={"project_id": project_id, "invoice_id": invoice.id, "amount": invoice.amount}
        )
    
    return invoice

@app.post("/api/admin/projects/{project_id}/progress", response_model=ProjectProgressResponse)
async def create_project_progress(
    project_id: str,
    progress_data: ProjectProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a project progress update (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Verify project exists
    project = db.query(ProjectRequest).filter(ProjectRequest.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create the progress update
    progress = ProjectProgress(
        project_request_id=project_id,
        admin_id=current_user.id,
        stage=progress_data.stage,
        title=progress_data.title,
        description=progress_data.description,
        percentage_complete=progress_data.percentage_complete,
        attachments=json.dumps(progress_data.attachments) if progress_data.attachments else None,
        is_milestone=progress_data.is_milestone
    )
    
    db.add(progress)
    db.commit()
    db.refresh(progress)
    
    # Add admin info
    progress.admin_name = current_user.name
    progress.admin_email = current_user.email
    if progress.attachments:
        progress.attachments = json.loads(progress.attachments)
    
    # Create notification for client
    if project.user_id:
        create_notification(
            db=db,
            user_id=project.user_id,
            title="Project Progress Update",
            message=f"Your project '{project.project_title}' has been updated: {progress_data.title}",
            notification_type="info",
            data={"project_id": project_id, "progress_id": progress.id, "stage": progress_data.stage, "percentage": progress_data.percentage_complete}
        )
    
    return progress

@app.post("/api/admin/projects/{project_id}/invoices/upload")
async def upload_project_invoice(
    project_id: str,
    invoice_number: str = Form(...),
    amount: str = Form(...),
    currency: str = Form(default="USD"),
    description: str = Form(...),
    due_date: str = Form(default=""),
    payment_method: str = Form(default=""),
    pdf_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload invoice with PDF file for a project"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Debug logging to identify which validation is failing
    app_logger.debug(f"DEBUG: invoice_number = '{invoice_number}'")
    app_logger.debug(f"DEBUG: amount = '{amount}' (type: {type(amount)})")
    app_logger.debug(f"DEBUG: description = '{description}'")
    app_logger.debug(f"DEBUG: pdf_file = {pdf_file}")
    app_logger.debug(f"DEBUG: pdf_file.filename = '{pdf_file.filename if pdf_file else None}'")
    
    # Validate required fields
    if not invoice_number or not invoice_number.strip():
        app_logger.debug("DEBUG: Invoice number validation failed")
        raise HTTPException(status_code=422, detail="Invoice number is required")
    
    # Convert amount to float if it's a string
    try:
        amount = float(amount)
        app_logger.debug(f"DEBUG: Amount converted to float: {amount}")
    except (ValueError, TypeError) as e:
        app_logger.debug(f"DEBUG: Amount conversion failed: {e}")
        raise HTTPException(status_code=422, detail="Amount must be a valid number")
    
    if amount <= 0:
        app_logger.debug("DEBUG: Amount validation failed - must be > 0")
        raise HTTPException(status_code=422, detail="Amount must be greater than 0")
    
    if not description or not description.strip():
        app_logger.debug("DEBUG: Description validation failed")
        raise HTTPException(status_code=422, detail="Description is required")
    
    if not pdf_file or not pdf_file.filename:
        app_logger.debug("DEBUG: PDF file validation failed")
        raise HTTPException(status_code=422, detail="PDF file is required")
    
    # Verify project exists
    project = db.query(ProjectRequest).filter(ProjectRequest.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Save PDF file
    file_extension = pdf_file.filename.split(".")[-1].lower()
    if file_extension != "pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create unique filename
    file_id = str(uuid.uuid4())
    filename = f"invoice_{file_id}.pdf"
    file_path = f"uploads/invoices/{filename}"
    
    # Ensure directory exists
    os.makedirs("uploads/invoices", exist_ok=True)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(pdf_file.file, buffer)
    
    # Parse due_date safely
    parsed_due_date = None
    if due_date and due_date.strip():
        try:
            parsed_due_date = datetime.fromisoformat(due_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid due_date format. Use ISO format (YYYY-MM-DD)")
    
    # Create invoice record
    invoice = ProjectInvoice(
        id=str(uuid.uuid4()),
        project_request_id=project_id,
        invoice_number=invoice_number,
        amount=amount,
        currency=currency,
        description=description,
        status="pending",
        due_date=parsed_due_date,
        payment_method=payment_method,
        file_path=file_path
    )
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    # Create notification for user
    create_notification(
        db=db,
        user_id=project.user_id,
        title="New Invoice Available",
        message=f"Invoice {invoice_number} has been created for your project '{project.project_title}'",
        notification_type="invoice",
        data={"invoice_id": invoice.id, "project_id": project_id}
    )
    
    return {"message": "Invoice uploaded successfully", "invoice": invoice}

@app.get("/api/invoices/{invoice_id}/download")
async def download_invoice_pdf(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download PDF invoice file"""
    # Get invoice
    invoice = db.query(ProjectInvoice).filter(ProjectInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if user has access to this invoice
    project = db.query(ProjectRequest).filter(ProjectRequest.id == invoice.project_request_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Only allow access to invoice owner or admin
    if project.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if PDF file exists
    if not invoice.file_path or not os.path.exists(invoice.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    # Return the PDF file
    return FileResponse(
        path=invoice.file_path,
        filename=f"invoice_{invoice.invoice_number}.pdf",
        media_type="application/pdf"
    )

@app.get("/api/licenses", response_model=List[LicenseResponse])
async def get_user_licenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all licenses for the current user"""
    licenses = db.query(License).filter(
        License.user_id == current_user.id,
        License.is_active == True
    ).all()
    
    return licenses

@app.get("/api/licenses/{license_id}/activations", response_model=LicenseActivationInfo)
async def get_license_activations(
    license_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activation information for a specific license"""
    
    # Find the license
    license_obj = db.query(License).filter(
        License.license_id == license_id,
        License.user_id == current_user.id
    ).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Get product info
    product = db.query(Product).filter(Product.id == license_obj.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get all activations for this license
    activations = db.query(UserProductActivation).filter(
        UserProductActivation.license_id == license_obj.id
    ).order_by(UserProductActivation.created_at.desc()).all()
    
    current_activations = len([a for a in activations if a.is_active])
    
    return LicenseActivationInfo(
        license_id=license_obj.license_id,
        product_name=product.name,
        max_activations=product.max_activations,
        current_activations=current_activations,
        available_activations=product.max_activations - current_activations,
        activations=activations
    )

@app.post("/api/licenses/{license_id}/activate", response_model=UserProductActivationResponse)
async def activate_license(
    license_id: str,
    activation_data: UserProductActivationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate a license on a new account"""
    
    # Find the license
    license_obj = db.query(License).filter(
        License.license_id == license_id,
        License.user_id == current_user.id,
        License.is_active == True
    ).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Get product info
    product = db.query(Product).filter(Product.id == license_obj.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if account is already activated for this license
    existing_activation = db.query(UserProductActivation).filter(
        UserProductActivation.license_id == license_obj.id,
        UserProductActivation.account_login == activation_data.account_login,
        UserProductActivation.account_server == activation_data.account_server,
        UserProductActivation.is_active == True
    ).first()
    
    if existing_activation:
        raise HTTPException(
            status_code=400,
            detail="This account is already activated for this license"
        )
    
    # Count current active activations for this license
    current_activations = db.query(UserProductActivation).filter(
        UserProductActivation.license_id == license_obj.id,
        UserProductActivation.is_active == True
    ).count()
    
    # Check if user has reached max activations
    if current_activations >= product.max_activations:
        raise HTTPException(
            status_code=400,
            detail=f"You have reached the maximum number of activations ({product.max_activations}) for this license. Purchase another copy to get more activations."
        )
    
    # Create new activation
    activation = UserProductActivation(
        license_id=license_obj.id,
        account_login=activation_data.account_login,
        account_server=activation_data.account_server,
        is_active=True,
        activated_at=datetime.utcnow()
    )
    
    db.add(activation)
    db.commit()
    db.refresh(activation)
    
    return activation

@app.get("/api/products/{product_id}/activations", response_model=ProductActivationInfo)
async def get_product_activations(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activation information for a specific product"""
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get all activations for this user-product combination
    activations = db.query(UserProductActivation).filter(
        UserProductActivation.user_id == current_user.id,
        UserProductActivation.product_id == product_id
    ).order_by(UserProductActivation.created_at.desc()).all()
    
    current_activations = len([a for a in activations if a.is_active])
    
    return ProductActivationInfo(
        product_id=product.id,
        product_name=product.name,
        max_activations=product.max_activations,
        current_activations=current_activations,
        available_activations=product.max_activations - current_activations,
        activations=activations
    )

@app.get("/api/users/me/activations", response_model=List[ProductActivationInfo])
async def get_user_activations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all product activations for the current user"""
    
    # Get all products the user has purchased
    user_transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.status == "success"
    ).all()
    
    purchased_products = set()
    for transaction in user_transactions:
        order_items = db.query(OrderItem).filter(
            OrderItem.transaction_id == transaction.id
        ).all()
        for item in order_items:
            purchased_products.add(item.product_id)
    
    # Get activation info for each purchased product
    activation_info_list = []
    for product_id in purchased_products:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            activations = db.query(UserProductActivation).filter(
                UserProductActivation.user_id == current_user.id,
                UserProductActivation.product_id == product_id
            ).order_by(UserProductActivation.created_at.desc()).all()
            
            current_activations = len([a for a in activations if a.is_active])
            
            activation_info_list.append(ProductActivationInfo(
                product_id=product.id,
                product_name=product.name,
                max_activations=product.max_activations,
                current_activations=current_activations,
                available_activations=product.max_activations - current_activations,
                activations=activations
            ))
    
    return activation_info_list

@app.delete("/api/activations/{activation_id}")
async def delete_activation(
    activation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an account activation"""
    
    activation = db.query(UserProductActivation).join(License).filter(
        UserProductActivation.id == activation_id,
        License.user_id == current_user.id
    ).first()
    
    if not activation:
        raise HTTPException(status_code=404, detail="Activation not found")
    
    # Delete the activation from database
    db.delete(activation)
    db.commit()
    
    return {"message": "Account activation deleted successfully"}

@app.post("/api/licenses/{license_id}/generate-file")
async def generate_license_file(
    license_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate encrypted license file for a license"""
    
    # Find the license
    license_obj = db.query(License).filter(
        License.license_id == license_id,
        License.user_id == current_user.id,
        License.is_active == True
    ).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Get product info
    product = db.query(Product).filter(Product.id == license_obj.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get all active activations for this license
    activations = db.query(UserProductActivation).filter(
        UserProductActivation.license_id == license_obj.id,
        UserProductActivation.is_active == True
    ).all()
    
    # Convert activations to account list
    accounts = []
    for activation in activations:
        accounts.append({
            "account_login": activation.account_login,
            "account_server": activation.account_server,
            "activated_at": activation.activated_at.isoformat()
        })
    
    # Create license data
    license_data = create_license_data(
        product_name=product.name,
        license_id=license_obj.license_id,
        accounts=accounts,
        max_activations=product.max_activations,
        expiry_date=license_obj.expires_at if license_obj.expires_at else None  # Add expiry logic if needed
    )
    
    # Create license file using new binary system
    license_system = LicenseSystem()
    success = license_system.create_license_file(license_data, license_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create license file")
    
    # Create filename
    filename = f"{license_id}.lic"
    
    # Move file to licenses directory
    source_path = f"{license_id}.lic"
    file_path = f"licenses/{filename}"
    os.makedirs("licenses", exist_ok=True)
    
    if os.path.exists(source_path):
        import shutil
        shutil.move(source_path, file_path)
    
    return {
        "success": True,
        "filename": filename,
        "download_url": f"/api/licenses/{license_id}/download-file",
        "license_info": get_license_info(license_data)
    }

@app.get("/api/licenses/{license_id}/download-file")
async def download_license_file(
    license_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download license file"""
    
    # Find the license
    license_obj = db.query(License).filter(
        License.license_id == license_id,
        License.user_id == current_user.id,
        License.is_active == True
    ).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Get product info
    product = db.query(Product).filter(Product.id == license_obj.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Create filename
    filename = f"{license_id}.lic"
    file_path = f"licenses/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="License file not found")
    
    # Return file for download
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@app.post("/api/verify-account", response_model=AccountVerificationResponse)
async def verify_account(
    verification_data: AccountVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify if an account is authorized for a license (for EA use)"""
    
    # Find the license
    license_obj = db.query(License).filter(
        License.license_id == verification_data.license_id,
        License.is_active == True
    ).first()
    
    if not license_obj:
        return AccountVerificationResponse(
            is_valid=False,
            message="Invalid license ID"
        )
    
    # Get product info
    product = db.query(Product).filter(Product.id == license_obj.product_id).first()
    if not product:
        return AccountVerificationResponse(
            is_valid=False,
            message="Product not found"
        )
    
    # Check if account is activated for this license
    activation = db.query(UserProductActivation).filter(
        UserProductActivation.license_id == license_obj.id,
        UserProductActivation.account_login == verification_data.account_login,
        UserProductActivation.account_server == verification_data.account_server,
        UserProductActivation.is_active == True
    ).first()
    
    if not activation:
        return AccountVerificationResponse(
            is_valid=False,
            message="Account not authorized for this license"
        )
    
    # Get license activation info
    activations = db.query(UserProductActivation).filter(
        UserProductActivation.license_id == license_obj.id
    ).order_by(UserProductActivation.created_at.desc()).all()
    
    current_activations = len([a for a in activations if a.is_active])
    
    license_info = LicenseActivationInfo(
        license_id=license_obj.license_id,
        product_name=product.name,
        max_activations=product.max_activations,
        current_activations=current_activations,
        available_activations=product.max_activations - current_activations,
        activations=activations
    )
    
    return AccountVerificationResponse(
        is_valid=True,
        message="Account authorized",
        license_info=license_info
    )

@app.get("/api/products/{product_id}/licenses")
async def get_product_licenses(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all licenses for a specific product that the user has purchased"""
    try:
        # Verify the product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get all licenses for this product for the current user
        licenses = db.query(License).filter(
            License.user_id == current_user.id,
            License.product_id == product_id,
            License.is_active == True
        ).all()
        
        license_data = []
        for license in licenses:
            # Get activations for this license
            activations = db.query(UserProductActivation).filter(
                UserProductActivation.license_id == license.id
            ).all()
            
            activation_data = []
            for activation in activations:
                activation_data.append({
                    "id": activation.id,
                    "account_login": activation.account_login,
                    "account_server": activation.account_server,
                    "is_active": activation.is_active,
                    "activated_at": activation.activated_at.isoformat() if activation.activated_at else None,
                    "deactivated_at": activation.deactivated_at.isoformat() if activation.deactivated_at else None
                })
            
            # Get transaction details
            transaction = db.query(Transaction).filter(Transaction.id == license.transaction_id).first()
            
            license_data.append({
                "id": license.id,
                "license_id": license.license_id,
                "product_id": license.product_id,
                "is_active": license.is_active,
                "created_at": license.created_at.isoformat(),
                "updated_at": license.updated_at.isoformat(),
                "max_activations": product.max_activations,
                "current_activations": len([a for a in activations if a.is_active]),
                "activations": activation_data,
                "purchase_date": transaction.created_at.isoformat() if transaction else None,
                "purchase_reference": transaction.paystack_reference if transaction else None
            })
        
        return {
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "max_activations": product.max_activations
            },
            "licenses": license_data,
            "total_licenses": len(license_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Get product licenses error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get product licenses"
        )

@app.get("/api/users/me/purchased-products")
async def get_user_purchased_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all products purchased by the current user (grouped by product)"""
    try:
        # Get all successful transactions for the user
        successful_transactions = db.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.status == "success"
        ).all()
        
        # Group products to avoid duplicates
        product_dict = {}
        
        for transaction in successful_transactions:
            # Get order items for this transaction
            order_items = db.query(OrderItem).filter(
                OrderItem.transaction_id == transaction.id
            ).all()
            
            for item in order_items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product_id = product.id
                    
                    # If product already exists, just update the quantities and licenses
                    if product_id in product_dict:
                        product_dict[product_id]["quantity"] += item.quantity
                        product_dict[product_id]["total"] += float(item.price * item.quantity)
                        
                        # Re-query the actual license count to ensure accuracy
                        license_count = db.query(License).filter(
                            License.product_id == product.id,
                            License.user_id == current_user.id,
                            License.is_active == True
                        ).count()
                        product_dict[product_id]["license_count"] = license_count
                        
                        # Update to earliest purchase date
                        if transaction.created_at < datetime.fromisoformat(product_dict[product_id]["purchase_date"].replace('Z', '+00:00')):
                            product_dict[product_id]["purchase_date"] = transaction.created_at.isoformat()
                    else:
                        # Get download logs for this product
                        download_logs = db.query(DownloadLog).filter(
                            DownloadLog.product_id == product.id,
                            DownloadLog.user_id == current_user.id
                        ).order_by(DownloadLog.download_time.desc()).all()
                        
                        # Check if user has any licenses for this product
                        has_licenses = db.query(License).filter(
                            License.product_id == product.id,
                            License.user_id == current_user.id,
                            License.is_active == True
                        ).first() is not None
                        
                        # Count total licenses for this product
                        license_count = db.query(License).filter(
                            License.product_id == product.id,
                            License.user_id == current_user.id,
                            License.is_active == True
                        ).count()
                        
                        # Check if this is a rental and get license expiry info
                        is_rental = item.is_rental
                        license_expiry = None
                        days_remaining = None
                        
                        if is_rental:
                            # Get the rental license to check expiry
                            rental_license = db.query(License).filter(
                                License.product_id == product.id,
                                License.user_id == current_user.id,
                                License.transaction_id == transaction.id,
                                License.is_rental == True
                            ).first()
                            
                            if rental_license and rental_license.expires_at:
                                license_expiry = rental_license.expires_at.isoformat()
                                days_remaining = max(0, (rental_license.expires_at - datetime.utcnow()).days)
                        
                        product_dict[product_id] = {
                            "product_id": product.id,
                            "product_name": product.name,
                            "description": product.description,
                            "category": product.category,
                            "platform": product.platform or "MT4",
                            "image": product.image,
                            "purchase_date": transaction.created_at.isoformat(),
                            "quantity": item.quantity,
                            "price": float(item.price),
                            "total": float(item.price * item.quantity),
                            "download_count": len(download_logs),
                            "last_download": download_logs[0].download_time.isoformat() if download_logs else None,
                            "has_license": has_licenses,
                            "license_count": license_count,
                            "is_digital": product.is_digital,
                            
                            # Rental fields
                            "is_rental": is_rental,
                            "license_expiry": license_expiry,
                            "days_remaining": days_remaining
                        }
        
        # Convert dict to list
        purchased_products = list(product_dict.values())
        
        return {
            "success": True,
            "purchased_products": purchased_products
        }
        
    except Exception as e:
        app_logger.error(f"Error getting purchased products: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get purchased products"
        )

@app.post("/api/users/me/products/{product_id}/generate-download-token")
async def generate_download_token(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a new download token for a purchased product"""
    try:
        # Verify user has purchased this product
        user_transaction = db.query(Transaction).join(OrderItem).filter(
            Transaction.user_id == current_user.id,
            Transaction.status == "success",
            OrderItem.product_id == product_id
        ).first()
        
        if not user_transaction:
            raise HTTPException(
                status_code=404,
                detail="Product not found in your purchases"
            )
        
        # Get product details
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product or not product.is_digital:
            raise HTTPException(
                status_code=404,
                detail="Digital product not found"
            )
        
        # Check if product file exists
        if not product.file_path or not os.path.exists(product.file_path):
            raise HTTPException(
                status_code=404,
                detail="Product file not found"
            )
        
        # Generate new download token (unlimited downloads)
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=365)  # 1 year expiry (effectively unlimited)
        
        download_token = DownloadToken(
            user_id=current_user.id,
            product_id=product_id,
            transaction_id=user_transaction.id,
            token=token,
            is_single_use=False,  # No single-use restrictions
            max_downloads=999999,  # Unlimited downloads
            expires_at=expires_at
        )
        
        db.add(download_token)
        db.commit()
        
        # Create notification
        create_notification(
            db=db,
            user_id=current_user.id,
            title="Download Link Generated",
            message=f"New download link generated for {product.name}. Unlimited downloads available.",
            notification_type="success",
            data={"product_id": product_id, "product_name": product.name}
        )
        
        return {
            "success": True,
            "download_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/download?token={token}",
            "expires_at": expires_at.isoformat(),
            "max_downloads": "unlimited"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        download_logger.error(f"Error generating download token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate download token"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 