# Email Configuration and Forgot Password Implementation

This document describes the email configuration setup and the implementation of the forgot password functionality for the Jarvistrade application.

## Overview

The application now includes comprehensive email functionality for:

- Welcome emails to newly registered users
- Email verification for new accounts
- Password reset functionality
- Payment confirmations
- Download notifications
- Project request confirmations

## Features Implemented

### 1. User Registration with Email Verification

- New users receive a welcome email with verification link
- Email verification token expires after 24 hours
- Users can request new verification emails

### 2. Forgot Password System

- Secure password reset via email
- Reset tokens expire after 1 hour
- Password reset emails with secure links

### 3. Email Templates

- Professional HTML email templates
- Responsive design for mobile and desktop
- Branded with Jarvistrade styling

## Database Changes

### New User Table Fields

The following fields have been added to the `users` table:

```sql
-- Password reset fields
password_reset_token TEXT
password_reset_expires DATETIME

-- Email verification fields
email_verified BOOLEAN DEFAULT 0
email_verification_token TEXT
email_verification_expires DATETIME
```

### Migration Script

Run the migration script to add these fields:

```bash
cd backend
python add_password_reset_fields.py
```

## Environment Configuration

### Required Environment Variables

Add these to your `.env` file:

```bash
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@jarvistrade.com

# Application Configuration
APP_NAME=JarvisTrade
FRONTEND_URL=http://localhost:3000
```

**Note:** The email service now uses `fastapi-mail` instead of the standard `smtplib` library for better integration with FastAPI and improved reliability.

### Gmail Setup (Recommended)

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
3. Use the generated password as `SMTP_PASSWORD`

### Other SMTP Providers

The system supports any SMTP provider. Update the configuration accordingly:

```bash
# For Outlook/Hotmail
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587

# For Yahoo
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587

# For custom SMTP server
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587
```

## API Endpoints

### Authentication Endpoints

#### 1. Forgot Password

```http
POST /api/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**

```json
{
  "message": "If an account with that email exists, a password reset link has been sent.",
  "success": true
}
```

#### 2. Reset Password

```http
POST /api/auth/reset-password
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "new_password": "new-password-123"
}
```

**Response:**

```json
{
  "message": "Password has been reset successfully.",
  "success": true
}
```

#### 3. Verify Email

```http
POST /api/auth/verify-email
Content-Type: application/json

{
  "token": "verification-token-from-email"
}
```

**Response:**

```json
{
  "message": "Email verified successfully.",
  "success": true,
  "email_verified": true
}
```

#### 4. Resend Verification

```http
POST /api/auth/resend-verification
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**

```json
{
  "message": "If an account with that email exists, a verification link has been sent.",
  "success": true
}
```

## Email Service Functions

### Core Email Functions

#### 1. Welcome Email

```python
email_service.send_welcome_email(
    user_email="user@example.com",
    user_name="John Doe",
    verification_url="https://app.com/verify?token=abc123"
)
```

#### 2. Password Reset Email

```python
email_service.send_password_reset_email(
    user_email="user@example.com",
    user_name="John Doe",
    reset_url="https://app.com/reset?token=abc123",
    expires_at=datetime.utcnow() + timedelta(hours=1)
)
```

#### 3. Email Verification Email

```python
email_service.send_email_verification_email(
    user_email="user@example.com",
    user_name="John Doe",
    verification_url="https://app.com/verify?token=abc123",
    expires_at=datetime.utcnow() + timedelta(hours=24)
)
```

### Existing Email Functions

The service also includes:

- `send_download_email()` - Product download notifications
- `send_payment_success_email()` - Payment confirmations
- `send_project_request_confirmation()` - Project request confirmations
- `send_project_request_notification()` - Admin notifications

## Security Features

### 1. Token Security

- All tokens are UUID4-based for uniqueness
- Tokens have configurable expiration times
- Tokens are cleared after use

### 2. User Enumeration Protection

- API responses don't reveal if an email exists
- Consistent response messages for security

### 3. Rate Limiting

- Consider implementing rate limiting for email endpoints
- Prevent abuse of password reset functionality

### 4. Token Validation

- Tokens are validated against expiration time
- Invalid/expired tokens are rejected immediately

## Frontend Integration

### 1. Forgot Password Flow

```typescript
// Request password reset
const response = await fetch("/api/auth/forgot-password", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: userEmail }),
});

// Handle response
if (response.ok) {
  // Show success message
  // Redirect to login or show instructions
}
```

### 2. Reset Password Flow

```typescript
// Get token from URL parameters
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get("token");

// Reset password
const response = await fetch("/api/auth/reset-password", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    token: token,
    new_password: newPassword,
  }),
});
```

### 3. Email Verification Flow

```typescript
// Get verification token from URL
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get("token");

// Verify email
const response = await fetch("/api/auth/verify-email", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ token: token }),
});
```

## Testing

### 1. Quick Configuration Test

Test your FastAPI Mail configuration using the provided test script:

```bash
cd backend
python test_fastapi_mail.py
```

This will verify your SMTP settings without sending actual emails.

### 2. Test Email Configuration

```python
# Test email service (now async)
import asyncio
from email_service import email_service

async def test_email():
    # Test welcome email
    await email_service.send_welcome_email(
        user_email="test@example.com",
        user_name="Test User",
        verification_url="https://example.com/verify?token=test123"
    )

# Run the test
asyncio.run(test_email())
```

### 3. Testing with Real Emails

To test actual email sending:

1. **Edit `test_fastapi_mail.py`**
2. **Change `test_email` to your real email address**
3. **Uncomment the `await fast_mail.send_message(message)` line**
4. **Run the test script again**

### 4. Test API Endpoints

Use tools like Postman or curl to test the endpoints:

```bash
# Test forgot password
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Test password reset
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token": "your-token", "new_password": "newpass123"}'
```

### 3. Database Verification

Check that the new fields were added:

```sql
PRAGMA table_info(users);
```

## Troubleshooting

### Common Issues

#### 1. Email Not Sending

- Check SMTP credentials
- Verify firewall/network settings
- Check email provider's sending limits
- Review application logs for errors

#### 2. Database Errors

- Ensure migration script ran successfully
- Check database file permissions
- Verify table structure

#### 3. Token Issues

- Check token expiration times
- Verify token format (should be UUID4)
- Check database for token storage

### Debug Mode

Enable debug logging in your environment:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### Log Files

Check these log files for errors:

- `logs/app.log` - General application logs
- `logs/error.log` - Error-specific logs
- Console output for email service messages

## Production Considerations

### 1. Email Provider

- Use a reliable email service (SendGrid, Mailgun, AWS SES)
- Set up proper SPF, DKIM, and DMARC records
- Monitor email delivery rates

### 2. Security

- Use HTTPS for all frontend URLs
- Implement rate limiting
- Monitor for abuse patterns
- Regular security audits

### 3. Monitoring

- Track email delivery success rates
- Monitor API endpoint usage
- Set up alerts for failures
- Log analysis for security

### 4. Backup

- Regular database backups
- Email template backups
- Configuration backups

## Future Enhancements

### 1. Advanced Features

- Email templates customization
- Multi-language support
- Email preferences management
- Unsubscribe functionality

### 2. Integration

- Webhook notifications
- SMS integration
- Push notifications
- Slack/Discord integration

### 3. Analytics

- Email open rates
- Click-through rates
- User engagement metrics
- A/B testing for templates

## Support

For issues or questions:

1. Check the logs for error messages
2. Verify environment configuration
3. Test email service independently
4. Review this documentation
5. Check GitHub issues for known problems

## Changelog

### Version 1.1.0

- **Migrated from smtplib to fastapi-mail**
- **Improved async/await support**
- **Better FastAPI integration**
- **Enhanced error handling and reliability**
- **Updated all email functions to be async**

### Version 1.0.0

- Initial implementation of email service
- User registration with email verification
- Forgot password functionality
- Password reset via email
- Professional email templates
- Security features and token management
