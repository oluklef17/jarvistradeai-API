#!/usr/bin/env python3
"""
Script to replace all print statements with appropriate logging calls
"""

import re
import os

def replace_print_statements():
    """Replace print statements with appropriate logging calls"""
    
    # Define the mapping of print statements to logging calls
    replacements = [
        # Payment-related prints
        (r'print\(f"Transaction (\w+) status updated to: (\w+)"\)', r'payment_logger.info(f"Transaction \1 status updated to: \2")'),
        (r'print\(f"Payment status: (\w+)"\)', r'payment_logger.info(f"Payment status: \1")'),
        (r'print\(f"Processing result: (\w+)"\)', r'payment_logger.info(f"Processing result: \1")'),
        (r'print\(f"Payment processing failed: (\w+)"\)', r'payment_logger.error(f"Payment processing failed: \1")'),
        (r'print\(f"Payment verification error: (\w+)"\)', r'payment_logger.error(f"Payment verification error: \1")'),
        (r'print\(f"Transaction (\w+) status updated from (\w+) to: (\w+)"\)', r'payment_logger.info(f"Transaction \1 status updated from \2 to: \3")'),
        (r'print\(f"Verification log saved: (\w+)"\)', r'payment_logger.info(f"Verification log saved: \1")'),
        (r'print\(f"Transaction (\w+) already successful, no update needed"\)', r'payment_logger.info(f"Transaction \1 already successful, no update needed")'),
        (r'print\(f"Transaction (\w+) status remains (\w+), Paystack returned: (\w+)"\)', r'payment_logger.info(f"Transaction \1 status remains \2, Paystack returned: \3")'),
        (r'print\(f"Manual payment verification error: (\w+)"\)', r'payment_logger.error(f"Manual payment verification error: \1")'),
        (r'print\(f"Retry payment - User country: (\w+), Currency: (\w+)"\)', r'payment_logger.info(f"Retry payment - User country: \1, Currency: \2")'),
        (r'print\(\'Paystack Response:\', (\w+)\)', r'payment_logger.info(f"Paystack Response: {\1}")'),
        (r'print\(f"Payment retry error: (\w+)"\)', r'payment_logger.error(f"Payment retry error: \1")'),
        (r'print\(f"Payment status for (\w+): (\w+)"\)', r'payment_logger.info(f"Payment status for \1: \2")'),
        (r'print\(f"Payment status error: (\w+)"\)', r'payment_logger.error(f"Payment status error: \1")'),
        (r'print\(f"Payment details error: (\w+)"\)', r'payment_logger.error(f"Payment details error: \1")'),
        
        # Download-related prints
        (r'print\(f"Download attempt - User: (\w+), Product: (\w+)"\)', r'download_logger.info(f"Download attempt - User: \1, Product: \2")'),
        (r'print\(f"User ID: (\w+)"\)', r'download_logger.info(f"User ID: \1")'),
        (r'print\(f"Purchase check - Transaction found: (\w+)"\)', r'download_logger.info(f"Purchase check - Transaction found: \1")'),
        (r'print\(f"Transaction ID: (\w+), Status: (\w+)"\)', r'download_logger.info(f"Transaction ID: \1, Status: \2")'),
        (r'print\(f"Rental license valid. Days remaining: (\w+)"\)', r'download_logger.info(f"Rental license valid. Days remaining: \1")'),
        (r'print\("Warning: No rental license found for rental product"\)', r'download_logger.warning("Warning: No rental license found for rental product")'),
        (r'print\(f"Warning: Failed to log download or update count: (\w+)"\)', r'download_logger.warning(f"Failed to log download or update count: \1")'),
        (r'print\(f"ERROR: Cannot get file size for (\w+): (\w+)"\)', r'download_logger.error(f"Cannot get file size for \1: \2")'),
        (r'print\(f"ERROR: File not found after path normalization: (\w+)"\)', r'download_logger.error(f"File not found after path normalization: \1")'),
        (r'print\(f"Original file_path: (\w+)"\)', r'download_logger.error(f"Original file_path: \1")'),
        (r'print\(f"Current working directory: (\w+)"\)', r'download_logger.error(f"Current working directory: \1")'),
        (r'print\(f"Added product file to zip: (\w+)"\)', r'download_logger.info(f"Added product file to zip: \1")'),
        (r'print\("Added README.txt to zip"\)', r'download_logger.info("Added README.txt to zip")'),
        (r'print\(f"Zip file created successfully - Size: (\w+) bytes"\)', r'download_logger.info(f"Zip file created successfully - Size: \1 bytes")'),
        (r'print\(f"Error creating zip file: (\w+)"\)', r'download_logger.error(f"Error creating zip file: \1")'),
        (r'print\("Falling back to direct file streaming..."\)', r'download_logger.info("Falling back to direct file streaming...")'),
        (r'print\(f"Fallback streaming also failed: (\w+)"\)', r'download_logger.error(f"Fallback streaming also failed: \1")'),
        (r'print\(f"Direct download - User: (\w+)"\)', r'download_logger.info(f"Direct download - User: \1")'),
        (r'print\(f"Product: (\w+)"\)', r'download_logger.info(f"Product: \1")'),
        (r'print\(f"File: (\w+)"\)', r'download_logger.info(f"File: \1")'),
        (r'print\(f"Size: (\w+) bytes"\)', r'download_logger.info(f"Size: \1 bytes")'),
        (r'print\(f"Transaction: (\w+)"\)', r'download_logger.info(f"Transaction: \1")'),
        (r'print\(f"Zip filename: (\w+)"\)', r'download_logger.info(f"Zip filename: \1")'),
        (r'print\(f"Direct download error: (\w+)"\)', r'download_logger.error(f"Direct download error: \1")'),
        (r'print\(f"Downloading file: (\w+)"\)', r'download_logger.info(f"Downloading file: \1")'),
        (r'print\(f"File size: (\w+) bytes"\)', r'download_logger.info(f"File size: \1 bytes")'),
        (r'print\(f"File exists: (\w+)"\)', r'download_logger.info(f"File exists: \1")'),
        (r'print\(f"Client IP: (\w+)"\)', r'download_logger.info(f"Client IP: \1")'),
        (r'print\(f"User Agent: (\w+)"\)', r'download_logger.info(f"User Agent: \1")'),
        (r'print\(f"WARNING: File size mismatch! Database: (\w+), Actual: (\w+)"\)', r'download_logger.warning(f"File size mismatch! Database: \1, Actual: \2")'),
        (r'print\(f"Download error: (\w+)"\)', r'download_logger.error(f"Download error: \1")'),
        
        # User-related prints
        (r'print\(f"User (\w+) location detected: (\w+), Currency: (\w+)"\)', r'user_logger.info(f"User \1 location detected: \2, Currency: \3")'),
        (r'print\(f"Error detecting user location: (\w+)"\)', r'user_logger.error(f"Error detecting user location: \1")'),
        (r'print\(f"New user (\w+) location detected: (\w+), Currency: (\w+)"\)', r'user_logger.info(f"New user \1 location detected: \2, Currency: \3")'),
        (r'print\(f"Error detecting user location during registration: (\w+)"\)', r'user_logger.error(f"Error detecting user location during registration: \1")'),
        
        # Product-related prints
        (r'print\(f"Getting product with ID: (\w+)"\)', r'product_logger.info(f"Getting product with ID: \1")'),
        (r'print\(f"Current user: (\w+)"\)', r'product_logger.info(f"Current user: \1")'),
        (r'print\(f"Error updating product: (\w+)"\)', r'product_logger.error(f"Error updating product: \1")'),
        
        # Review-related prints
        (r'print\(f"Error creating review: (\w+)"\)', r'review_logger.error(f"Error creating review: \1")'),
        
        # Notification-related prints
        (r'print\(f"Error creating notification: (\w+)"\)', r'notification_logger.error(f"Error creating notification: \1")'),
        
        # Blog-related prints
        (r'print\(f"Blog file upload error: (\w+)"\)', r'blog_logger.error(f"Blog file upload error: \1")'),
        
        # Project-related prints
        (r'print\(f"Error sending admin notification: (\w+)"\)', r'project_logger.error(f"Error sending admin notification: \1")'),
        (r'print\(f"Error getting notification stats: (\w+)"\)', r'project_logger.error(f"Error getting notification stats: \1")'),
        (r'print\(f"Error sending review prompts: (\w+)"\)', r'project_logger.error(f"Error sending review prompts: \1")'),
        (r'print\(f"Error sending review prompt: (\w+)"\)', r'project_logger.error(f"Error sending review prompt: \1")'),
        
        # Exchange rate prints
        (r'print\(f"Min price: (\w+)"\)', r'exchange_rate_logger.info(f"Min price: \1")'),
        (r'print\(f"Max price: (\w+)"\)', r'exchange_rate_logger.info(f"Max price: \1")'),
        
        # Other prints
        (r'print\(f"Success page data error: (\w+)"\)', r'app_logger.error(f"Success page data error: \1")'),
        (r'print\(f"Transaction (\w+) status updated to: (\w+)"\)', r'payment_logger.info(f"Transaction \1 status updated to: \2")'),
        (r'print\(f"Found retry payment via metadata: (\w+)"\)', r'payment_logger.info(f"Found retry payment via metadata: \1")'),
        (r'print\(f"Found retry payment via payment_data: (\w+)"\)', r'payment_logger.info(f"Found retry payment via payment_data: \1")'),
        (r'print\(f"Original transaction (\w+) marked as resolved by retry (\w+)"\)', r'payment_logger.info(f"Original transaction \1 marked as resolved by retry \2")'),
        (r'print\(f"Original transaction (\w+) not found"\)', r'payment_logger.warning(f"Original transaction \1 not found")'),
        (r'print\(f"No retry payment information found for transaction (\w+)"\)', r'payment_logger.info(f"No retry payment information found for transaction \1")'),
        (r'print\(f"Payment processed successfully: (\w+) - (\w+) - (\w+)"\)', r'payment_logger.info(f"Payment processed successfully: \1 - \2 - \3")'),
        (r'print\(f"Payment processing failed: (\w+)"\)', r'payment_logger.error(f"Payment processing failed: \1")'),
        (r'print\(f"User not found for email: (\w+)"\)', r'payment_logger.error(f"User not found for email: \1")'),
        (r'print\(f"Transaction not found for reference: (\w+)"\)', r'payment_logger.error(f"Transaction not found for reference: \1")'),
        (r'print\(f"Payment failed: (\w+)"\)', r'payment_logger.error(f"Payment failed: \1")'),
        (r'print\(f"Transaction (\w+) status updated to: (\w+)"\)', r'payment_logger.info(f"Transaction \1 status updated to: \2")'),
        (r'print\(f"Transaction not found for reference: (\w+)"\)', r'payment_logger.error(f"Transaction not found for reference: \1")'),
        (r'print\(f"Unhandled webhook event: (\w+)"\)', r'payment_logger.warning(f"Unhandled webhook event: \1")'),
        (r'print\(f"Webhook error: (\w+)"\)', r'payment_logger.error(f"Webhook error: \1")'),
        (r'print\(\'Transaction create time:\', (\w+)\)', r'payment_logger.info(f"Transaction create time: {\1}")'),
        (r'print\(f"Error updating order status: (\w+)"\)', r'payment_logger.error(f"Error updating order status: \1")'),
        (r'print\(f"DEBUG: Received token: (\w+)"\)', r'auth_logger.debug(f"Received token: \1")'),
        (r'print\(f"DEBUG: invoice_number = \'(\w+)\'"\)', r'app_logger.debug(f"invoice_number = \'\1\'")'),
        (r'print\(f"DEBUG: amount = \'(\w+)\' \(type: (\w+)\)"\)', r'app_logger.debug(f"amount = \'\1\' (type: \2)")'),
        
        # Free products processing
        (r'print\(f"Processing (\w+) free products for user (\w+)"\)', r'app_logger.info(f"Processing \1 free products for user \2")'),
        (r'print\(f"Free products processed successfully for user (\w+)"\)', r'app_logger.info(f"Free products processed successfully for user \1")'),
        (r'print\(f"Error processing free products: (\w+)"\)', r'app_logger.error(f"Error processing free products: \1")'),
        (r'print\(f"Cart items received: (\w+)"\)', r'app_logger.info(f"Cart items received: \1")'),
        (r'print\(f"Total amount: (\w+)"\)', r'app_logger.info(f"Total amount: \1")'),
        (r'print\(f"User country: (\w+), Currency: (\w+)"\)', r'app_logger.info(f"User country: \1, Currency: \2")'),
        (r'print\(f"Creating rental license with (\w+) days duration, expires at: (\w+)"\)', r'app_logger.info(f"Creating rental license with \1 days duration, expires at: \2")'),
        (r'print\(f"Checkout error: (\w+)"\)', r'app_logger.error(f"Checkout error: \1")'),
    ]
    
    # Files to process
    files_to_process = [
        'main.py',
        'payment_service.py',
        'auth.py'
    ]
    
    for filename in files_to_process:
        if os.path.exists(filename):
            print(f"Processing {filename}...")
            
            # Read the file
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply replacements
            original_content = content
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # Write back if changes were made
            if content != original_content:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated {filename}")
            else:
                print(f"ℹ️  No changes needed for {filename}")
        else:
            print(f"⚠️  File {filename} not found")

if __name__ == "__main__":
    replace_print_statements()
