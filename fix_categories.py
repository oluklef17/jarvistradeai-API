from sqlalchemy.orm import Session
from database import engine, get_db
from models_mysql import Base, Product
import json

# Create database tables
Base.metadata.create_all(bind=engine)

def fix_product_categories():
    """Fix existing product categories to match new validation rules"""
    db = next(get_db())
    
    # Category mapping from old to new values
    category_mapping = {
        'Indicator': 'indicator',
        'Trading Bot': 'trading-bot',
        'Analysis Tool': 'analysis-tool',
        'Risk Management': 'risk-management',
        'Education': 'education',
        'Expert Advisors': 'trading-bot',
        'Scripts': 'analysis-tool',
        'Utilities': 'analysis-tool'
    }
    
    try:
        # Get all products
        products = db.query(Product).all()
        
        for product in products:
            old_category = product.category
            new_category = category_mapping.get(old_category, 'indicator')  # default to indicator
            
            if old_category != new_category:
                print(f"Updating product '{product.name}' category from '{old_category}' to '{new_category}'")
                product.category = new_category
        
        db.commit()
        print(f"Successfully updated {len(products)} products")
        
        # Print summary of categories
        categories = db.query(Product.category).distinct().all()
        print("\nCurrent categories in database:")
        for category in categories:
            count = db.query(Product).filter(Product.category == category[0]).count()
            print(f"  {category[0]}: {count} products")
            
    except Exception as e:
        print(f"Error fixing categories: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_product_categories() 