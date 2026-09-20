from db.database import SessionLocal
from db.models.product import Product

db = SessionLocal()
product = db.query(Product).filter(Product.id == 1).first()
if product:
    print(f"Deleting product {product.id}...")
    db.delete(product)
    db.commit()
    print("Deleted successfully!")
else:
    print("Product not found")
db.close()
