from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    is_client = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Location fields for currency detection
    country = Column(String, default="US")
    currency = Column(String, default="USD")
    currency_symbol = Column(String, default="$")
    
    # Notification preferences
    notification_preferences = Column(Text, default='{"info": true, "success": true, "warning": true, "error": true, "payment": true, "order": true, "system": true, "update": true, "review_prompt": true}')
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    
    # Password reset fields
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)
    email_verification_expires = Column(DateTime, nullable=True)

class ProjectRequest(Base):
    __tablename__ = "project_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    platforms = Column(Text)  # JSON string of selected platforms
    expected_completion_time = Column(String)
    budget_range = Column(String)
    file_uploads = Column(Text)  # JSON string of file paths
    contact_email = Column(String)
    telegram_handle = Column(String)
    status = Column(String, default="Pending Review")  # Pending Review, In Progress, Completed, Cancelled
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Optional, for logged-in users
    assigned_developer_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    assigned_developer = relationship("User", foreign_keys=[assigned_developer_id])

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)  # SEO-friendly URL slug
    description = Column(Text)
    short_description = Column(String)
    price = Column(Float)
    original_price = Column(Float)  # For discounted prices
    category = Column(String, index=True)
    image = Column(String)
    tags = Column(Text)  # JSON string
    features = Column(Text)  # JSON string
    images = Column(Text)  # JSON string
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Digital product fields
    is_digital = Column(Boolean, default=True)
    file_path = Column(String)  # Path to the digital file
    file_size = Column(Integer)  # File size in bytes
    download_count = Column(Integer, default=0)
    
    # Demo and test fields
    youtube_demo_link = Column(String)  # YouTube video URL for product demo
    test_download_link = Column(String)  # Link to test version of the product
    
    # Activation fields
    max_activations = Column(Integer, default=1)  # Maximum number of simultaneous terminal activations
    
    # Version tracking
    version = Column(String, default="1.0.0")  # Product version for updates
    
    # Platform field
    platform = Column(String, default="MT4")  # MT4, MT5, or TradingView
    
    # Rental fields
    has_rental_option = Column(Boolean, default=False)  # Whether product can be rented
    rental_price = Column(Float, nullable=True)  # Monthly rental price
    rental_duration_days = Column(Integer, default=30)  # Rental duration in days

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    paystack_reference = Column(String, unique=True, index=True)
    amount = Column(Float)
    currency = Column(String, default="USD")
    status = Column(String, default="pending")  # pending, success, failed
    payment_data = Column(Text)  # JSON string of payment details
    purchased_items = Column(Text)  # JSON string of purchased items snapshot
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    order_items = relationship("OrderItem", back_populates="transaction")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"))
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    price = Column(Float)
    is_rental = Column(Boolean, default=False)  # Whether this is a rental order
    rental_duration_days = Column(Integer, nullable=True)  # Rental duration for this order
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="order_items")
    product = relationship("Product")

class DownloadToken(Base):
    __tablename__ = "download_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    product_id = Column(String, ForeignKey("products.id"), nullable=True)  # Nullable for zip files
    transaction_id = Column(String, ForeignKey("transactions.id"))
    token = Column(String, unique=True, index=True)
    is_single_use = Column(Boolean, default=True)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    file_path = Column(String, nullable=True)  # Path to file (for zip downloads)
    download_count = Column(Integer, default=0)  # Track number of downloads
    max_downloads = Column(Integer, default=1)  # Maximum allowed downloads
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    product = relationship("Product")
    transaction = relationship("Transaction")

class DownloadLog(Base):
    __tablename__ = "download_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    product_id = Column(String, ForeignKey("products.id"))
    license_id = Column(String, ForeignKey("licenses.id"), nullable=True)  # For direct downloads
    download_token_id = Column(String, ForeignKey("download_tokens.id"), nullable=True)  # For legacy token downloads
    ip_address = Column(String)
    user_agent = Column(String)
    download_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)  # Add for consistency
    download_status = Column(String, default="success")  # "success" or "failed"
    success = Column(Boolean, default=True)  # Keep for backward compatibility
    error_message = Column(String)
    
    # Relationships
    download_token = relationship("DownloadToken")
    license = relationship("License")
    user = relationship("User")
    product = relationship("Product")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    product_id = Column(String, ForeignKey("products.id"))
    rating = Column(Integer)  # 1-5 stars
    comment = Column(Text)
    is_verified_purchase = Column(Boolean, default=False)  # User actually bought the product
    is_approved = Column(Boolean, default=True)  # Admin can approve/reject reviews
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    product = relationship("Product")

class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(String, nullable=False)
    featured_image = Column(String)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="draft")  # draft, published, archived
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    tags = Column(Text)  # JSON string of tags
    meta_title = Column(String)
    meta_description = Column(String)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional media fields
    youtube_links = Column(Text)  # JSON string of YouTube URLs
    attached_files = Column(Text)  # JSON string of file paths
    gallery_images = Column(Text)  # JSON string of additional image paths
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # Relationships
    author = relationship("User")

class BlogLike(Base):
    __tablename__ = "blog_likes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    blog_post_id = Column(String, ForeignKey("blog_posts.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    blog_post = relationship("BlogPost")
    
    # Ensure unique like per user per post
    __table_args__ = (UniqueConstraint('user_id', 'blog_post_id', name='unique_user_post_like'),)

class BlogComment(Base):
    __tablename__ = "blog_comments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    blog_post_id = Column(String, ForeignKey("blog_posts.id"), nullable=False)
    parent_comment_id = Column(String, ForeignKey("blog_comments.id"), nullable=True)  # For replies
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=True)  # Admin can approve/reject comments
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    blog_post = relationship("BlogPost")
    parent_comment = relationship("BlogComment", remote_side=[id])
    replies = relationship("BlogComment")


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info")  # info, success, warning, error, order, payment, system
    is_read = Column(Boolean, default=False)
    data = Column(Text)  # JSON string for additional data (order_id, product_id, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_currency = Column(String, nullable=False)  # USD
    to_currency = Column(String, nullable=False)    # NGN
    rate = Column(Float, nullable=False)            # 1500.0 (1 USD = 1500 NGN)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Ensure unique currency pair
    __table_args__ = (UniqueConstraint('from_currency', 'to_currency', name='unique_currency_pair'),)

class ProjectResponse(Base):
    __tablename__ = "project_responses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = Column(String, ForeignKey("project_requests.id"), nullable=False)
    admin_id = Column(String, ForeignKey("users.id"), nullable=False)
    parent_response_id = Column(String, ForeignKey("project_responses.id"), nullable=True)  # For threading
    response_type = Column(String, default="quote")  # quote, clarification, update, completion, message, reply
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    proposed_price = Column(Float, nullable=True)
    estimated_duration = Column(String, nullable=True)
    terms_conditions = Column(Text, nullable=True)
    is_approved_by_client = Column(Boolean, default=False)
    is_approved_by_admin = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_request = relationship("ProjectRequest")
    admin = relationship("User")
    parent_response = relationship("ProjectResponse", remote_side=[id])
    replies = relationship("ProjectResponse")

class ProjectInvoice(Base):
    __tablename__ = "project_invoices"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = Column(String, ForeignKey("project_requests.id"), nullable=False)
    invoice_number = Column(String, unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, paid, overdue, cancelled
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    payment_method = Column(String, nullable=True)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)
    file_path = Column(String, nullable=True)  # Path to uploaded PDF file
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_request = relationship("ProjectRequest")
    transaction = relationship("Transaction")

class ProjectProgress(Base):
    __tablename__ = "project_progress"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = Column(String, ForeignKey("project_requests.id"), nullable=False)
    admin_id = Column(String, ForeignKey("users.id"), nullable=False)
    stage = Column(String, nullable=False)  # planning, development, testing, review, completed
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    percentage_complete = Column(Integer, default=0)  # 0-100
    attachments = Column(Text)  # JSON string of file paths
    is_milestone = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_request = relationship("ProjectRequest")
    admin = relationship("User") 

class License(Base):
    __tablename__ = "licenses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    license_id = Column(String, unique=True, index=True)  # User-friendly license ID
    user_id = Column(String, ForeignKey("users.id"))
    product_id = Column(String, ForeignKey("products.id"))
    transaction_id = Column(String, ForeignKey("transactions.id"))
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)  # License expiry date (for rentals)
    is_rental = Column(Boolean, default=False)  # Whether this is a rental license
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    product = relationship("Product")
    transaction = relationship("Transaction")
    activations = relationship("UserProductActivation", back_populates="license")

class UserProductActivation(Base):
    __tablename__ = "user_product_activations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    license_id = Column(String, ForeignKey("licenses.id"))
    account_login = Column(String)  # MT4/MT5 account login
    account_server = Column(String)  # MT4/MT5 server name
    is_active = Column(Boolean, default=True)
    activated_at = Column(DateTime, default=datetime.utcnow)
    deactivated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    license = relationship("License", back_populates="activations") 