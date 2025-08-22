from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import json

# Project request platforms
PROJECT_PLATFORMS = [
    "MT4",
    "MT5",
    "TradingView",
    "Python",
    "Other"
]

# Project completion time options
COMPLETION_TIME_OPTIONS = [
    "3 days",
    "1 week",
    "2 weeks",
    "1 month",
    "2 months",
    "3+ months"
]

# Budget range options
BUDGET_RANGE_OPTIONS = [
    "Under $500",
    "$500 - $1,000",
    "$1,000 - $2,500",
    "$2,500 - $5,000",
    "$5,000 - $10,000",
    "$10,000+",
    "Custom"
]

# Product categories from the frontend filter sidebar
PRODUCT_CATEGORIES = [
    "trading-bot",
    "indicator",
    "analysis-tool",
    "risk-management",
    "education"
]

# Product platforms
PRODUCT_PLATFORMS = [
    "MT4",
    "MT5", 
    "TradingView"
]

# Base schemas
class UserBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_client: bool = True
    is_admin: bool = False
    notification_preferences: Optional[dict] = None
    email_notifications: bool = True
    push_notifications: bool = True

    @field_validator('notification_preferences', mode='before')
    @classmethod
    def parse_notification_preferences(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return {
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
        return v or {
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

# Password reset schemas
class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

# Response schemas
class PasswordResetResponse(BaseModel):
    message: str
    success: bool

class ProjectRequestBase(BaseModel):
    project_title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=5000)
    platforms: List[str] = Field(..., min_items=1)
    expected_completion_time: str
    budget_range: Optional[str] = None
    contact_email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    telegram_handle: Optional[str] = None
    file_uploads: Optional[List[str]] = []

    @field_validator('platforms')
    @classmethod
    def validate_platforms(cls, v):
        if not all(platform in PROJECT_PLATFORMS for platform in v):
            raise ValueError(f'Platforms must be one of: {", ".join(PROJECT_PLATFORMS)}')
        return v

    @field_validator('expected_completion_time')
    @classmethod
    def validate_completion_time(cls, v):
        if v not in COMPLETION_TIME_OPTIONS:
            raise ValueError(f'Expected completion time must be one of: {", ".join(COMPLETION_TIME_OPTIONS)}')
        return v

    @field_validator('budget_range')
    @classmethod
    def validate_budget_range(cls, v):
        if v is not None:
            # Allow any budget range that contains common patterns
            valid_patterns = [
                "Under", "$", "₦", "Custom", "500", "1000", "2500", "5000", "10000"
            ]
            if not any(pattern in v for pattern in valid_patterns):
                raise ValueError(f'Budget range must contain valid currency and amount patterns')
        return v

class ProjectRequestCreate(ProjectRequestBase):
    pass

class ProjectRequestUpdate(BaseModel):
    project_title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=20, max_length=5000)
    platforms: Optional[List[str]] = None
    expected_completion_time: Optional[str] = None
    budget_range: Optional[str] = None
    contact_email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    telegram_handle: Optional[str] = None
    status: Optional[str] = None
    assigned_developer_id: Optional[str] = None

    @field_validator('platforms')
    @classmethod
    def validate_platforms(cls, v):
        if v is not None and not all(platform in PROJECT_PLATFORMS for platform in v):
            raise ValueError(f'Platforms must be one of: {", ".join(PROJECT_PLATFORMS)}')
        return v

    @field_validator('expected_completion_time')
    @classmethod
    def validate_completion_time(cls, v):
        if v is not None and v not in COMPLETION_TIME_OPTIONS:
            raise ValueError(f'Expected completion time must be one of: {", ".join(COMPLETION_TIME_OPTIONS)}')
        return v

    @field_validator('budget_range')
    @classmethod
    def validate_budget_range(cls, v):
        if v is not None:
            # Allow any budget range that contains common patterns
            valid_patterns = [
                "Under", "$", "₦", "Custom", "500", "1000", "2500", "5000", "10000"
            ]
            if not any(pattern in v for pattern in valid_patterns):
                raise ValueError(f'Budget range must contain valid currency and amount patterns')
        return v

class ProjectRequestResponse(ProjectRequestBase):
    id: str
    status: str
    user_id: Optional[str] = None
    assigned_developer_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    responses_count: Optional[int] = 0
    invoices_count: Optional[int] = 0
    progress_count: Optional[int] = 0

    @field_validator('platforms', 'file_uploads', mode='before')
    @classmethod
    def parse_json_lists(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = None  # SEO-friendly URL slug
    description: str = Field(..., min_length=10)
    short_description: Optional[str] = None
    price: float = Field(..., ge=0)
    original_price: Optional[float] = Field(None, ge=0)  # For discounted prices
    category: str = Field(..., min_length=1)
    image: Optional[str] = None
    tags: Optional[List[str]] = []
    features: Optional[List[str]] = []
    images: Optional[List[str]] = []
    rating: Optional[float] = 0.0
    total_reviews: int = 0
    is_active: bool = True
    is_featured: bool = False
    is_digital: bool = True
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_count: int = 0
    youtube_demo_link: Optional[str] = None
    test_download_link: Optional[str] = None
    max_activations: int = Field(default=1, ge=1)  # Minimum 1 activation
    platform: str = Field(default="MT4")  # MT4, MT5, or TradingView
    currency: Optional[str] = "USD"  # Currency code (USD, NGN, EUR, GBP)
    currency_symbol: Optional[str] = "$"  # Currency symbol ($, ₦, €, £)
    
    # Rental fields
    has_rental_option: bool = False
    rental_price: Optional[float] = Field(None, ge=0)
    rental_duration_days: int = Field(default=30, ge=1)

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v not in PRODUCT_CATEGORIES:
            raise ValueError(f'Category must be one of: {", ".join(PRODUCT_CATEGORIES)}')
        return v

    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v):
        if v not in PRODUCT_PLATFORMS:
            raise ValueError(f'Platform must be one of: {", ".join(PRODUCT_PLATFORMS)}')
        return v

# Create schemas
class UserCreate(UserBase):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=6)

class ProductCreate(ProductBase):
    pass

# Update schemas
class UserUpdate(BaseModel):
    name: Optional[str] = None
    is_client: Optional[bool] = None
    is_admin: Optional[bool] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = None  # SEO-friendly URL slug
    description: Optional[str] = Field(None, min_length=10)
    short_description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=1)
    image: Optional[str] = None
    tags: Optional[List[str]] = None
    features: Optional[List[str]] = None
    images: Optional[List[str]] = None
    rating: Optional[float] = None
    total_reviews: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_count: Optional[int] = None
    youtube_demo_link: Optional[str] = None
    test_download_link: Optional[str] = None
    max_activations: Optional[int] = Field(None, ge=1)
    platform: Optional[str] = None
    version: Optional[str] = None
    
    # Rental fields
    has_rental_option: Optional[bool] = None
    rental_price: Optional[float] = Field(None, ge=0)
    rental_duration_days: Optional[int] = Field(None, ge=1)

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v is not None and v not in PRODUCT_CATEGORIES:
            raise ValueError(f'Category must be one of: {", ".join(PRODUCT_CATEGORIES)}')
        return v

    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v):
        if v is not None and v not in PRODUCT_PLATFORMS:
            raise ValueError(f'Platform must be one of: {", ".join(PRODUCT_PLATFORMS)}')
        return v

# Response schemas
class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProductResponse(ProductBase):
    id: str
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator('tags', 'features', 'images', mode='before')
    @classmethod
    def parse_json_lists(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []

    @field_validator('rating', mode='before')
    @classmethod
    def handle_null_rating(cls, v):
        if v is None:
            return 0.0
        return v

    class Config:
        from_attributes = True

class CategoryResponse(BaseModel):
    id: str
    name: str
    count: int

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TransactionBase(BaseModel):
    paystack_reference: str
    amount: float
    currency: str = "USD"
    status: str = "pending"

class TransactionCreate(TransactionBase):
    user_id: str
    payment_data: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: str
    user_id: str
    payment_data: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrderItemBase(BaseModel):
    product_id: str
    quantity: int = 1
    price: float

class OrderItemCreate(OrderItemBase):
    transaction_id: str

class OrderItemResponse(OrderItemBase):
    id: str
    transaction_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class DownloadTokenBase(BaseModel):
    user_id: str
    product_id: str
    transaction_id: str
    token: str
    is_single_use: bool = True
    is_used: bool = False
    expires_at: datetime

class DownloadTokenCreate(DownloadTokenBase):
    pass

class DownloadTokenResponse(DownloadTokenBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class DownloadLogBase(BaseModel):
    user_id: str
    product_id: str
    ip_address: str
    user_agent: str
    success: bool = True
    error_message: Optional[str] = None

class DownloadLogCreate(DownloadLogBase):
    pass

class DownloadLogResponse(DownloadLogBase):
    id: str
    download_time: datetime

    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=10, max_length=1000)
    is_verified_purchase: bool = False

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=10, max_length=1000)
    is_approved: Optional[bool] = None

class ReviewResponse(ReviewBase):
    id: str
    user_id: str
    product_id: str
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Include user info for display
    user_name: str
    user_email: str

    class Config:
        from_attributes = True 

# Blog Post Schemas
class BlogPostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    excerpt: str = Field(..., min_length=10, max_length=500)
    featured_image: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    is_featured: bool = False
    tags: Optional[List[str]] = []
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    youtube_links: Optional[List[str]] = []
    attached_files: Optional[List[str]] = []
    gallery_images: Optional[List[str]] = []
    like_count: int = 0
    comment_count: int = 0

class BlogPostCreate(BlogPostBase):
    pass

class BlogPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=10)
    excerpt: Optional[str] = Field(None, min_length=10, max_length=500)
    featured_image: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    is_featured: Optional[bool] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = Field(None, max_length=60)
    meta_description: Optional[str] = Field(None, max_length=160)
    published_at: Optional[datetime] = None
    youtube_links: Optional[List[str]] = None
    attached_files: Optional[List[str]] = None
    gallery_images: Optional[List[str]] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None

class BlogPostResponse(BlogPostBase):
    id: str
    slug: str
    author_id: str
    view_count: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Blog Like Schemas
class BlogLikeBase(BaseModel):
    user_id: str
    blog_post_id: str

class BlogLikeCreate(BlogLikeBase):
    pass

class BlogLikeResponse(BlogLikeBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Blog Comment Schemas
class BlogCommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_comment_id: Optional[str] = None

class BlogCommentCreate(BlogCommentBase):
    pass

class BlogCommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)

class BlogCommentResponse(BlogCommentBase):
    id: str
    user_id: str
    blog_post_id: str
    is_approved: bool
    created_at: datetime
    updated_at: datetime
    
    # Include user info for display
    user_name: str
    user_email: str
    
    class Config:
        from_attributes = True 

# Notification Schemas
class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    type: str = Field(default="info", pattern="^(info|success|warning|error|order|payment|system|update|review_prompt)$")
    data: Optional[str] = None  # JSON string for additional data


class NotificationCreate(NotificationBase):
    user_id: str


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    is_read: bool
    created_at: datetime

    @field_validator('created_at', mode='before')
    @classmethod
    def ensure_utc_datetime(cls, v):
        """Ensure datetime is treated as UTC"""
        if isinstance(v, str):
            # If it's a string without timezone info, treat it as UTC
            if not v.endswith('Z') and not v.endswith('+00:00'):
                v = v + 'Z'
        return v

    class Config:
        from_attributes = True 

# Notification Preferences Schemas
class NotificationPreferencesUpdate(BaseModel):
    notification_preferences: Optional[dict] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None

    @field_validator('notification_preferences')
    @classmethod
    def validate_notification_preferences(cls, v):
        if v is not None:
            valid_types = ["info", "success", "warning", "error", "payment", "order", "system", "update", "review_prompt"]
            for key, value in v.items():
                if key not in valid_types:
                    raise ValueError(f"Invalid notification type: {key}")
                if not isinstance(value, bool):
                    raise ValueError(f"Notification preference value must be boolean for {key}")
        return v

class NotificationPreferencesResponse(BaseModel):
    notification_preferences: dict
    email_notifications: bool
    push_notifications: bool

class ExchangeRateBase(BaseModel):
    from_currency: str
    to_currency: str
    rate: float
    is_active: bool = True

class ExchangeRateCreate(ExchangeRateBase):
    pass

class ExchangeRateUpdate(BaseModel):
    rate: Optional[float] = None
    is_active: Optional[bool] = None

class ExchangeRateResponse(ExchangeRateBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 

# Project Management Schemas
class ProjectResponseBase(BaseModel):
    response_type: str = Field(default="quote", pattern="^(quote|clarification|update|completion|message|reply)$")
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    proposed_price: Optional[float] = Field(None, gt=0)
    estimated_duration: Optional[str] = None
    terms_conditions: Optional[str] = None
    parent_response_id: Optional[str] = None
    is_approved_by_client: bool = False
    is_approved_by_admin: bool = True

class ProjectResponseCreate(ProjectResponseBase):
    pass

class ProjectResponseUpdate(BaseModel):
    response_type: Optional[str] = Field(None, pattern="^(quote|clarification|update|completion|message|reply)$")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    message: Optional[str] = Field(None, min_length=1, max_length=5000)
    proposed_price: Optional[float] = Field(None, gt=0)
    estimated_duration: Optional[str] = None
    terms_conditions: Optional[str] = None
    is_approved_by_client: Optional[bool] = None
    is_approved_by_admin: Optional[bool] = None

class ProjectResponseResponse(ProjectResponseBase):
    id: str
    project_request_id: str
    admin_id: str
    created_at: datetime
    updated_at: datetime
    
    # Include admin info for display
    admin_name: str
    admin_email: str

    class Config:
        from_attributes = True

class ProjectInvoiceBase(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^(USD|NGN)$")
    description: str = Field(..., min_length=1, max_length=1000)
    status: str = Field(default="pending", pattern="^(pending|paid|overdue|cancelled)$")
    due_date: Optional[datetime] = None
    payment_method: Optional[str] = None

class ProjectInvoiceCreate(ProjectInvoiceBase):
    project_request_id: str
    invoice_number: str = Field(..., min_length=1, max_length=50)

class ProjectInvoiceUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, pattern="^(USD|NGN)$")
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(pending|paid|overdue|cancelled)$")
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None

class ProjectInvoiceResponse(ProjectInvoiceBase):
    id: str
    project_request_id: str
    invoice_number: str
    paid_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProjectProgressBase(BaseModel):
    stage: str = Field(..., pattern="^(planning|development|testing|review|completed)$")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    percentage_complete: int = Field(..., ge=0, le=100)
    attachments: Optional[List[str]] = []
    is_milestone: bool = False

class ProjectProgressCreate(ProjectProgressBase):
    project_request_id: str
    admin_id: str

class ProjectProgressUpdate(BaseModel):
    stage: Optional[str] = Field(None, pattern="^(planning|development|testing|review|completed)$")
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    percentage_complete: Optional[int] = Field(None, ge=0, le=100)
    attachments: Optional[List[str]] = None
    is_milestone: Optional[bool] = None

class ProjectProgressResponse(ProjectProgressBase):
    id: str
    project_request_id: str
    admin_id: str
    created_at: datetime
    updated_at: datetime
    
    # Include admin info for display
    admin_name: str
    admin_email: str

    @field_validator('attachments', mode='before')
    @classmethod
    def parse_attachments(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []

    class Config:
        from_attributes = True

# Project Management Dashboard Schemas
class ProjectDashboardData(BaseModel):
    project_request: ProjectRequestResponse
    responses: List[ProjectResponseResponse]
    invoices: List[ProjectInvoiceResponse]
    progress_updates: List[ProjectProgressResponse]
    latest_progress: Optional[ProjectProgressResponse] = None
    total_invoiced: float
    total_paid: float
    overall_progress: int

    class Config:
        from_attributes = True 

class LicenseBase(BaseModel):
    license_id: str
    product_id: str
    is_active: bool = True
    expires_at: Optional[datetime] = None  # License expiry date (for rentals)
    is_rental: bool = False  # Whether this is a rental license

class LicenseCreate(LicenseBase):
    pass

class LicenseResponse(LicenseBase):
    id: str
    user_id: str
    transaction_id: str
    expires_at: Optional[datetime] = None
    is_rental: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserProductActivationCreate(BaseModel):
    license_id: str
    account_login: str = Field(..., description="MT4/MT5 account login")
    account_server: str = Field(..., description="MT4/MT5 server name")

class UserProductActivationResponse(BaseModel):
    id: str
    license_id: str
    account_login: str
    account_server: str
    is_active: bool
    activated_at: datetime
    deactivated_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductActivationInfo(BaseModel):
    license_id: str
    product_id: str
    product_name: str
    max_activations: int
    current_activations: int
    available_activations: int
    activations: List[UserProductActivationResponse] = []
    
    class Config:
        from_attributes = True

class LicenseActivationInfo(BaseModel):
    license_id: str
    product_name: str
    max_activations: int
    current_activations: int
    available_activations: int
    activations: List[UserProductActivationResponse] = []
    
    class Config:
        from_attributes = True

class AccountVerificationRequest(BaseModel):
    license_id: str
    account_login: str
    account_server: str

class AccountVerificationResponse(BaseModel):
    is_valid: bool
    message: str
    license_info: Optional[LicenseActivationInfo] = None

# Cart and Checkout Schemas
class CartItem(BaseModel):
    id: str
    quantity: int = Field(default=1, ge=1)
    price: float = Field(..., ge=0)
    is_rental: bool = False
    rental_duration_days: Optional[int] = Field(None, ge=1)
    rental_price: Optional[float] = Field(None, ge=0)

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    totalAmount: float = Field(..., ge=0)
    currency: Optional[str] = "USD" 