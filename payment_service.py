import aiohttp
import os
import json
import secrets
import zipfile
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models_mysql import Transaction, OrderItem, DownloadToken, DownloadLog, Product, User, License
from email_service import email_service
from logging_config import safe_log

load_dotenv()

class PaymentService:
    def __init__(self):
        self.paystack_secret_key = os.getenv('PAYSTACK_SECRET_KEY')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.download_token_expiry_hours = int(os.getenv('DOWNLOAD_TOKEN_EXPIRY_HOURS', '24'))
        self.digital_files_path = os.getenv('DIGITAL_FILES_PATH', './digital_products')
        
        # Download security settings - no restrictions since licensing is in place
        self.max_downloads_per_token = 999999  # Unlimited downloads
        self.enable_single_use_tokens = False  # No single-use restrictions
        self.download_token_expiry_hours = 24 * 365  # 1 year expiry (effectively unlimited)
    
    async def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify payment with Paystack"""
        try:
            url = f"https://api.paystack.co/transaction/verify/{reference}"
            headers = {
                "Authorization": f"Bearer {self.paystack_secret_key}",
                "Content-Type": "application/json"
            }
            
            safe_log("payment", "info", f"Verifying payment with Paystack for reference: {reference}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    safe_log("payment", "info", f"Paystack response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        safe_log("payment", "info", f"Paystack response data: {json.dumps(data, indent=2)}")
                        
                        # Check if verification was successful
                        if data.get("status") and data["status"]:
                            transaction_data = data["data"]
                            
                            result = {
                                "success": True,
                                "data": transaction_data,
                                "status": transaction_data["status"],
                                "amount": transaction_data["amount"],
                                "currency": transaction_data["currency"],
                                "customer_email": transaction_data["customer"]["email"],
                                "paid_at": transaction_data.get("paid_at"),
                                "reference": transaction_data["reference"],
                                "gateway_response": transaction_data.get("gateway_response", "")
                            }
                            
                            safe_log("payment", "info", f"Verification result: {json.dumps(result, indent=2)}")
                            return result
                        else:
                            safe_log("payment", "error", f"Paystack verification failed: {data}")
                            return {
                                "success": False,
                                "error": "Payment verification failed",
                                "status": "failed"
                            }
                    else:
                        safe_log("payment", "error", f"Paystack API error: {response.status} - {await response.text()}")
                        return {
                            "success": False,
                            "error": f"Paystack API error: {response.status}",
                            "status": "failed"
                        }
                
        except Exception as e:
            safe_log("payment", "error", f"Verification error: {e}")
            return {
                "success": False,
                "error": f"Verification error: {str(e)}",
                "status": "failed"
            }
    
    def create_product_zip(self, products: List[Product], user: User) -> str:
        """Create a zip file containing all purchased digital products"""
        try:
            file_logger.info(f"Creating zip file for {len(products)} products")
            
            # Create temporary directory for zip file
            temp_dir = tempfile.mkdtemp()
            zip_filename = f"jarvistrade_products_{user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            file_logger.info(f"Zip path: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for product in products:
                    file_logger.info(f"Processing product: {product.name}, file_path: {product.file_path}")
                    
                    if product.file_path and os.path.exists(product.file_path):
                        # Get the filename from the path
                        filename = os.path.basename(product.file_path)
                        file_logger.info(f"Adding file: {filename}")
                        
                        # Add product info file
                        product_info = f"Product: {product.name}\n"
                        product_info += f"Description: {product.description}\n"
                        product_info += f"Price: ${product.price}\n"
                        product_info += f"Category: {product.category}\n"
                        product_info += f"Download Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        product_info += f"Customer: {user.name} ({user.email})\n"
                        product_info += "-" * 50 + "\n"
                        
                        # Add product info to zip
                        zipf.writestr(f"{product.name}/README.txt", product_info)
                        
                        # Add the actual product file
                        zipf.write(product.file_path, f"{product.name}/{filename}")
                        
                        # If product has additional files, add them too
                        if hasattr(product, 'additional_files') and product.additional_files:
                            additional_files = json.loads(product.additional_files)
                            for file_path in additional_files:
                                if os.path.exists(file_path):
                                    additional_filename = os.path.basename(file_path)
                                    zipf.write(file_path, f"{product.name}/{additional_filename}")
                    else:
                        file_logger.warning(f"Product {product.name} has no valid file path: {product.file_path}")
                        # Create a placeholder file for products without files
                        product_info = f"Product: {product.name}\n"
                        product_info += f"Description: {product.description}\n"
                        product_info += f"Price: ${product.price}\n"
                        product_info += f"Category: {product.category}\n"
                        product_info += f"Note: This is a digital product that will be delivered separately.\n"
                        product_info += f"Download Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        product_info += f"Customer: {user.name} ({user.email})\n"
                        product_info += "-" * 50 + "\n"
                        
                        zipf.writestr(f"{product.name}/README.txt", product_info)
            
            file_logger.info(f"Zip file created successfully with size: {os.path.getsize(zip_path)} bytes")
            return zip_path
            
        except Exception as e:
            file_logger.error(f"Error creating product zip: {e}")
            return None
    
    def process_successful_payment(self, db: Session, reference: str, user: User) -> Dict[str, Any]:
        """Process successful payment and generate download tokens"""
        try:
            safe_log("payment", "info", f"Processing payment for reference: {reference}")
            
            # Get the existing transaction record
            transaction = db.query(Transaction).filter(
                Transaction.paystack_reference == reference
            ).first()
            
            if not transaction:
                safe_log("payment", "error", f"Transaction not found for reference: {reference}")
                return {
                    "success": False,
                    "error": "Transaction not found"
                }
            
            # Check if transaction was already processed
            if transaction.status == "success":
                safe_log("payment", "info", f"Transaction already processed for reference: {reference}")
                return {
                    "success": True,
                    "message": "Transaction already processed",
                    "download_token": None
                }
            
            # Get the purchased items from the transaction
            try:
                purchased_items = json.loads(transaction.purchased_items) if transaction.purchased_items else []
            except (json.JSONDecodeError, TypeError):
                safe_log("payment", "error", f"Error parsing purchased items for reference: {reference}")
                return {
                    "success": False,
                    "error": "Invalid purchased items data"
                }
            
            if not purchased_items:
                safe_log("payment", "error", f"No purchased items found for reference: {reference}")
                return {
                    "success": False,
                    "error": "No purchased items found"
                }
            
            safe_log("payment", "info", f"Found {len(purchased_items)} purchased items")
            
            # Get the actual products from the purchased items
            product_ids = [item.get("id") for item in purchased_items if item.get("id")]
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
            
            if not products:
                safe_log("payment", "error", f"No products found for IDs: {product_ids}")
                return {
                    "success": False,
                    "error": "Products not found"
                }
            
            safe_log("payment", "info", f"Found {len(products)} products")
            
            # Update transaction status to success
            transaction.status = "success"
            db.commit()
            
            # Create order items for each product
            for item in purchased_items:
                order_item = OrderItem(
                    transaction_id=transaction.id,
                    product_id=item["id"],
                    quantity=item.get("quantity", 1),
                    price=item.get("price", 0),
                    is_rental=item.get("is_rental", False),
                    rental_duration_days=item.get("rental_duration_days")
                )
                db.add(order_item)
            
            db.commit()
            
            # Create licenses for each product purchase/rental
            for item in purchased_items:
                # Generate license ID
                license_id = f"LIC-{uuid.uuid4().hex[:8].upper()}"
                
                # Check if this is a rental
                is_rental = item.get("is_rental", False)
                expires_at = None
                
                if is_rental:
                    # Set expiry date for rental based on actual rental duration
                    rental_duration = item.get("rental_duration_days", 30)
                    expires_at = datetime.utcnow() + timedelta(days=rental_duration)
                    safe_log("payment", "info", f"Creating rental license with {rental_duration} days duration, expires at: {expires_at}")
                
                license_obj = License(
                    license_id=license_id,
                    user_id=user.id,
                    product_id=item["id"],
                    transaction_id=transaction.id,
                    is_active=True,
                    expires_at=expires_at,
                    is_rental=is_rental
                )
                db.add(license_obj)
            
            db.commit()
            
            # Create zip file with purchased products
            safe_log("payment", "info", "Creating product zip file...")
            zip_path = self.create_product_zip(products, user)
            
            if not zip_path:
                safe_log("payment", "error", "Failed to create product zip file")
                return {
                    "success": False,
                    "error": "Failed to create product package"
                }
            
            safe_log("payment", "info", f"Zip file created successfully: {zip_path}")
            
            # Generate download token for the zip file
            safe_log("payment", "info", "Generating download token...")
            download_token = self.generate_download_token_for_zip(db, user, transaction, zip_path, products)
            
            if not download_token:
                safe_log("payment", "error", "Failed to generate download token")
                return {
                    "success": False,
                    "error": "Failed to generate download token"
                }
            
            safe_log("payment", "info", f"Download token generated successfully: {download_token}")
            
            return {
                "success": True,
                "message": "Payment processed successfully",
                "download_token": download_token,
                "products": [{"id": p.id, "name": p.name} for p in products]
            }
            
        except Exception as e:
            safe_log("payment", "error", f"Error processing payment: {e}")
            db.rollback()
            return {
                "success": False,
                "error": f"Payment processing error: {str(e)}"
            }
    
    def generate_download_token_for_zip(self, db: Session, user: User, transaction: Transaction, zip_path: str, products: List[Product]) -> DownloadToken:
        """Generate a secure download token for zip file"""
        # Generate unique token
        token_string = secrets.token_urlsafe(32)
        
        # Set expiry time
        expires_at = datetime.utcnow() + timedelta(hours=self.download_token_expiry_hours)
        
        # Create download token with configurable security settings
        download_token = DownloadToken(
            user_id=user.id,
            product_id=None,  # This is for a zip file containing multiple products
            transaction_id=transaction.id,
            token=token_string,
            is_single_use=self.enable_single_use_tokens,  # Use configurable setting
            expires_at=expires_at,
            file_path=zip_path,  # Store the zip file path
            download_count=0,  # Track number of downloads
            max_downloads=self.max_downloads_per_token  # Use configurable limit
        )
        
        db.add(download_token)
        db.commit()
        db.refresh(download_token)
        
        return download_token
    
    def validate_download_token(self, db: Session, token: str, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Validate download token and log download attempt"""
        try:
            # Find token
            download_token = db.query(DownloadToken).filter(
                DownloadToken.token == token
            ).first()
            
            if not download_token:
                return {
                    "success": False,
                    "error": "Invalid download token"
                }
            
            # No restrictions since licensing is in place
            # Downloads are now unlimited with proper licensing protection
            
            # Handle zip file downloads (when product_id is None)
            if download_token.product_id is None and download_token.file_path:
                # This is a zip file download
                if not os.path.exists(download_token.file_path):
                    return {
                        "success": False,
                        "error": "Product package not found"
                    }
                
                # Track download for analytics (no restrictions)
                download_token.download_count += 1
                db.commit()
                
                # Log download attempt
                download_log = DownloadLog(
                    download_token_id=download_token.id,
                    user_id=download_token.user_id,
                    product_id=None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True
                )
                
                db.add(download_log)
                db.commit()
                
                # Get file size
                file_size = os.path.getsize(download_token.file_path)
                
                return {
                    "success": True,
                    "file_path": download_token.file_path,
                    "file_size": file_size,
                    "is_zip": True,
                    "downloads_remaining": "unlimited",
                    "user_id": download_token.user_id,
                    "product_id": download_token.product_id
                }
            
            # Handle individual product downloads
            product = db.query(Product).filter(Product.id == download_token.product_id).first()
            if not product:
                return {
                    "success": False,
                    "error": "Product not found"
                }
            
            # Check if file exists
            if not product.file_path or not os.path.exists(product.file_path):
                return {
                    "success": False,
                    "error": "Product file not found"
                }
            
            # Track download for analytics (no restrictions)
            download_token.download_count += 1
            db.commit()
            
            # Log download attempt
            download_log = DownloadLog(
                download_token_id=download_token.id,
                user_id=download_token.user_id,
                product_id=download_token.product_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            
            db.add(download_log)
            
            # Update product download count
            product.download_count += 1
            
            db.commit()
            
            # Get actual file size from disk
            actual_file_size = os.path.getsize(product.file_path)
            
            return {
                "success": True,
                "product": product,
                "file_path": product.file_path,
                "file_size": actual_file_size,
                "is_zip": False,
                "downloads_remaining": "unlimited",
                "user_id": download_token.user_id,
                "product_id": download_token.product_id
            }
            
        except Exception as e:
            # Log failed download attempt
            if 'download_token' in locals():
                download_log = DownloadLog(
                    download_token_id=download_token.id,
                    user_id=download_token.user_id,
                    product_id=download_token.product_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    error_message=str(e)
                )
                db.add(download_log)
                db.commit()
            
            return {
                "success": False,
                "error": f"Validation error: {str(e)}"
            }

# Create global payment service instance
payment_service = PaymentService() 