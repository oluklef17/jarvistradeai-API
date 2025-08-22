import os
import json
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

load_dotenv()

class EmailService:
    def __init__(self):
        self.app_name = os.getenv('APP_NAME', 'JarvisTrade')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        
        # FastAPI Mail configuration
        self.mail_config = ConnectionConfig(
            MAIL_USERNAME=os.getenv('SMTP_USERNAME'),
            MAIL_PASSWORD=os.getenv('SMTP_PASSWORD'),
            MAIL_FROM=os.getenv('FROM_EMAIL', 'noreply@jarvistrade.com'),
            MAIL_PORT=int(os.getenv('SMTP_PORT', '587')),
            MAIL_SERVER=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            MAIL_FROM_NAME=os.getenv('APP_NAME', 'JarvisTrade'),
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        
        self.fast_mail = FastMail(self.mail_config)
        print('Mail config:', self.mail_config)
    
    async def send_download_email(self, user_email: str, user_name: str, product_name: str, download_url: str, expires_at: datetime):
        """Send download link email to user"""
        try:
            subject = f"Your {product_name} Download - {self.app_name}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>Thank you for your purchase!</h2>
                <p>Dear {user_name},</p>
                
                <p>Your payment for <strong>{product_name}</strong> has been successfully processed.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Download Your Product</h3>
                    <p>Click the button below to download your product:</p>
                    <a href="{download_url}" 
                       style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Download Now
                    </a>
                </div>
                
                <p><strong>Important Notes:</strong></p>
                <ul>
                    <li>This download link expires on {expires_at.strftime('%B %d, %Y at %I:%M %p')}</li>
                    <li>Please keep this link secure and do not share it with others</li>
                    <li>If you have any issues, please contact our support team</li>
                </ul>
                
                <p>Thank you for choosing {self.app_name}!</p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This is an automated email. Please do not reply to this address.
                </p>
            </body>
            </html>
            """
            
            message = MessageSchema(
                subject=subject,
                recipients=[user_email],
                body=body,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            print(f"Download email sent to {user_email}")
            return True
                
        except Exception as e:
            print(f"Error sending email to {user_email}: {e}")
            return False
    
    async def send_download_email_with_zip(self, user_email: str, user_name: str, products: List, download_url: str, expires_at: datetime, zip_path: str):
        """Send download link email to user with zip file"""
        try:
            subject = f"Your Digital Products Download - {self.app_name}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>Thank you for your purchase!</h2>
                <p>Dear {user_name},</p>
                
                <p>Your payment for the following products has been successfully processed:</p>
                
                <ul>
            """
            
            for product in products:
                body += f"<li><strong>{product['name']}</strong> - ${product['price']}</li>"
            
            body += f"""
                </ul>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Download Your Products</h3>
                    <p>Click the button below to download your products:</p>
                    <a href="{download_url}" 
                       style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Download Now
                    </a>
                </div>
                
                <p><strong>Important Notes:</strong></p>
                <ul>
                    <li>This download link expires on {expires_at.strftime('%B %d, %Y at %I:%M %p')}</li>
                    <li>Please keep this link secure and do not share it with others</li>
                    <li>If you have any issues, please contact our support team</li>
                </ul>
                
                <p>Thank you for choosing {self.app_name}!</p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This is an automated email. Please do not reply to this address.
                </p>
            </body>
            </html>
            """
            
            message = MessageSchema(
                subject=subject,
                recipients=[user_email],
                body=body,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            print(f"Download email with zip sent to {user_email}")
            return True
                
        except Exception as e:
            print(f"Error sending email with zip to {user_email}: {e}")
            return False
    
    async def send_order_confirmation_email(self, user_email: str, user_name: str, order_details: dict):
        """Send order confirmation email to user"""
        try:
            subject = f"Order Confirmation - {self.app_name}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>Order Confirmation</h2>
                <p>Dear {user_name},</p>
                
                <p>Thank you for your order! Your order has been successfully placed and is being processed.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Order Details</h3>
                    <p><strong>Order ID:</strong> {order_details.get('order_id', 'N/A')}</p>
                    <p><strong>Order Date:</strong> {order_details.get('order_date', 'N/A')}</p>
                    <p><strong>Total Amount:</strong> ${order_details.get('total_amount', 'N/A')}</p>
                </div>
                
                <div style="background-color: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>What's Next?</h3>
                    <ul>
                        <li>You will receive a separate email with download instructions</li>
                        <li>For physical products, you'll receive shipping confirmation</li>
                        <li>Check your order status in your account dashboard</li>
                    </ul>
                </div>
                
                <p>If you have any questions about your order, please contact our support team.</p>
                
                <p>Thank you for choosing {self.app_name}!</p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This is an automated email. Please do not reply to this address.
                </p>
            </body>
            </html>
            """
            
            message = MessageSchema(
                subject=subject,
                recipients=[user_email],
                body=body,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            print(f"Order confirmation email sent to {user_email}")
            return True
                
        except Exception as e:
            print(f"Error sending order confirmation email to {user_email}: {e}")
            return False
    
    async def send_payment_failed_email(self, user_email: str, user_name: str, order_details: dict, error_message: str):
        """Send payment failed email to user"""
        try:
            subject = f"Payment Failed - {self.app_name}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>Payment Failed</h2>
                <p>Dear {user_name},</p>
                
                <p>We're sorry, but your payment for the following order could not be processed:</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Order Details</h3>
                    <p><strong>Order ID:</strong> {order_details.get('order_id', 'N/A')}</p>
                    <p><strong>Order Date:</strong> {order_details.get('order_date', 'N/A')}</p>
                    <p><strong>Total Amount:</strong> ${order_details.get('total_amount', 'N/A')}</p>
                </div>
                
                <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Error Details</h3>
                    <p><strong>Error:</strong> {error_message}</p>
                </div>
                
                <div style="background-color: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>What You Can Do</h3>
                    <ul>
                        <li>Check your payment method and try again</li>
                        <li>Ensure you have sufficient funds</li>
                        <li>Contact your bank if the issue persists</li>
                        <li>Try using a different payment method</li>
                    </ul>
                </div>
                
                <p>If you continue to experience issues, please contact our support team for assistance.</p>
                
                <p>Thank you for your patience.</p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This is an automated email. Please do not reply to this address.
                </p>
            </body>
            </html>
            """
            
            message = MessageSchema(
                subject=subject,
                recipients=[user_email],
                body=body,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            print(f"Payment failed email sent to {user_email}")
            return True
                
        except Exception as e:
            print(f"Error sending payment failed email to {user_email}: {e}")
            return False
    
    async def send_welcome_email(self, user_email: str, user_name: str, verification_url: str = None):
        """Send welcome email to newly registered user"""
        try:
            subject = f"Welcome to {self.app_name}!"
            
            # Email body
            if verification_url:
                body = f"""
                <html>
                <body>
                    <h2>Welcome to {self.app_name}!</h2>
                    <p>Dear {user_name},</p>
                    
                    <p>Thank you for creating an account with {self.app_name}! We're excited to have you on board.</p>
                    
                    <div style="background-color: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>Verify Your Email</h3>
                        <p>To complete your registration and access all features, please verify your email address:</p>
                        <a href="{verification_url}" 
                           style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            Verify Email
                        </a>
                        <p style="font-size: 14px; margin-top: 10px;">
                            If the button doesn't work, copy and paste this link into your browser:<br>
                            <a href="{verification_url}">{verification_url}</a>
                        </p>
                    </div>
                    
                    <div style="background-color: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>Getting Started</h3>
                        <ul>
                            <li>Browse our marketplace for digital products</li>
                            <li>Request custom development projects</li>
                            <li>Access your dashboard to manage orders</li>
                            <li>Get support when you need it</li>
                        </ul>
                    </div>
                    
                    <p>If you have any questions, our support team is here to help!</p>
                    
                    <p>Welcome to the {self.app_name} community!</p>
                    
                    <hr>
                    <p style="font-size: 12px; color: #666;">
                        This is an automated email. Please do not reply to this address.
                    </p>
                </body>
                </html>
                """
            else:
                body = f"""
                <html>
                <body>
                    <h2>Welcome to {self.app_name}!</h2>
                    <p>Dear {user_name},</p>
                    
                    <p>Thank you for creating an account with {self.app_name}! We're excited to have you on board.</p>
                    
                    <div style="background-color: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>Getting Started</h3>
                        <ul>
                            <li>Browse our marketplace for digital products</li>
                            <li>Request custom development projects</li>
                            <li>Access your dashboard to manage orders</li>
                            <li>Get support when you need it</li>
                        </ul>
                    </div>
                    
                    <p>If you have any questions, our support team is here to help!</p>
                    
                    <p>Welcome to the {self.app_name} community!</p>
                    
                    <hr>
                    <p style="font-size: 12px; color: #666;">
                        This is an automated email. Please do not reply to this address.
                    </p>
                </body>
                </html>
                """
            
            message = MessageSchema(
                subject=subject,
                recipients=[user_email],
                body=body,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            print(f"Welcome email sent to {user_email}")
            return True
                
        except Exception as e:
            print(f"Error sending welcome email to {user_email}: {e}")
            return False
    
    async def send_password_reset_email(self, user_email: str, user_name: str, reset_url: str, expires_at: datetime):
        """Send password reset email to user"""
        try:
            subject = f"Reset Your Password - {self.app_name}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>Reset Your Password</h2>
                <p>Dear {user_name},</p>
                
                <p>We received a request to reset your password for your {self.app_name} account.</p>
                
                <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Reset Your Password</h3>
                    <p>Click the button below to reset your password:</p>
                    <a href="{reset_url}" 
                       style="background-color: #ffc107; color: #212529; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Reset Password
                    </a>
                    <p style="font-size: 14px; margin-top: 10px;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{reset_url}">{reset_url}</a>
                    </p>
                </div>
                
                <p><strong>Important Notes:</strong></p>
                <ul>
                    <li>This reset link expires on {expires_at.strftime('%B %d, %Y at %I:%M %p')}</li>
                    <li>If you didn't request a password reset, please ignore this email</li>
                    <li>Your current password will remain unchanged until you complete the reset</li>
                    <li>For security, this link can only be used once</li>
                </ul>
                
                <p>If you have any questions or concerns, please contact our support team.</p>
                
                <p>Thank you for using {self.app_name}!</p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This is an automated email. Please do not reply to this address.
                </p>
            </body>
            </html>
            """
            
            message = MessageSchema(
                subject=subject,
                recipients=[user_email],
                body=body,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            print(f"Password reset email sent to {user_email}")
            return True
                
        except Exception as e:
            print(f"Error sending password reset email to {user_email}: {e}")
            return False

    async def send_email_verification_email(self, user_email: str, user_name: str, verification_url: str, expires_at: datetime):
        """Send email verification email to user"""
        try:
            subject = f"Verify Your Email - {self.app_name}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>Verify Your Email Address</h2>
                <p>Dear {user_name},</p>
                
                <p>Thank you for registering with {self.app_name}! To complete your registration, please verify your email address.</p>
                
                <div style="background-color: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Verify Your Email</h3>
                    <p>Click the button below to verify your email address:</p>
                    <a href="{verification_url}" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Verify Email
                    </a>
                    <p style="font-size: 14px; margin-top: 10px;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{verification_url}">{verification_url}</a>
                    </p>
                </div>
                
                <p><strong>Important Notes:</strong></p>
                <ul>
                    <li>This verification link expires on {expires_at.strftime('%B %d, %Y at %I:%M %p')}</li>
                    <li>If you didn't create an account with {self.app_name}, please ignore this email</li>
                    <li>Verifying your email helps us keep your account secure</li>
                </ul>
                
                <p>If you have any questions, please contact our support team.</p>
                
                <p>Welcome to {self.app_name}!</p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This is an automated email. Please do not reply to this address.
                </p>
            </body>
            </html>
            """
            
            message = MessageSchema(
                subject=subject,
                recipients=[user_email],
                body=body,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            print(f"Email verification email sent to {user_email}")
            return True
                
        except Exception as e:
            print(f"Error sending email verification email to {user_email}: {e}")
            return False

    async def send_project_request_confirmation(self, user_email: str, project_title: str):
        """Send project request confirmation email to user"""
        try:
            subject = f"Project Request Received - {self.app_name}"
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>Project Request Received</h2>
                <p>Thank you for submitting your project request!</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Project Details</h3>
                    <p><strong>Project Title:</strong> {project_title}</p>
                    <p><strong>Submitted:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p>We have received your custom project request and our team will review it shortly. You can expect to hear from us within 24-48 hours with:</p>
                
                <ul>
                    <li>Initial assessment and questions</li>
                    <li>Timeline and cost estimate</li>
                    <li>Next steps for project development</li>
                </ul>
                
                <p>If you have any urgent questions, please don't hesitate to reach out to us.</p>
                
                <p>Thank you for choosing {self.app_name} for your custom development needs!</p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This is an automated email. Please do not reply to this address.
                </p>
            </body>
            </html>
            """
            
            message = MessageSchema(
                subject=subject,
                recipients=[user_email],
                body=body,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            print(f"Project request confirmation email sent to {user_email}")
            return True
                
        except Exception as e:
            print(f"Error sending project request confirmation email to {user_email}: {e}")
            return False

    async def send_project_request_notification(self, admin_email: str, project_request):
        """Send project request notification to admin"""
        try:
            subject = f"New Project Request: {project_request.project_title} - {self.app_name}"
            
            # Parse platforms from JSON
            platforms = []
            if project_request.platforms:
                try:
                    platforms = json.loads(project_request.platforms)
                except:
                    platforms = [project_request.platforms]
            
            # Email body
            body = f"""
            <html>
            <body>
                <h2>New Project Request</h2>
                <p>A new custom project request has been submitted.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Project Details</h3>
                    <p><strong>Title:</strong> {project_request.project_title}</p>
                    <p><strong>Contact Email:</strong> {project_request.contact_email}</p>
                    <p><strong>Telegram:</strong> {project_request.telegram_handle or 'Not provided'}</p>
                    <p><strong>Platforms:</strong> {', '.join(platforms)}</p>
                    <p><strong>Timeline:</strong> {project_request.expected_completion_time}</p>
                    <p><strong>Budget:</strong> {project_request.budget_range or 'Not specified'}</p>
                    <p><strong>Submitted:</strong> {project_request.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Project Description</h3>
                    <p>{project_request.description}</p>
                </div>
                
                <p><strong>Action Required:</strong> Please review this request and respond to the client within 24-48 hours.</p>
                
                <hr>
                <p style="font-size: 12px; color: #666;">
                    This is an automated notification. Project ID: {project_request.id}
                </p>
            </body>
            </html>
            """
            
            message = MessageSchema(
                subject=subject,
                recipients=[admin_email],
                body=body,
                subtype=MessageType.html
            )
            
            await self.fast_mail.send_message(message)
            print(f"Project request notification sent to admin {admin_email}")
            return True
                
        except Exception as e:
            print(f"Error sending project request notification to {admin_email}: {e}")
            return False

# Create global email service instance
email_service = EmailService()