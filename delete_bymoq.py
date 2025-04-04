import json
import os

from dotenv import load_dotenv



load_dotenv()
product_file = os.getenv('PRODUCTS_FILE')
delete_file = os.getenv('DELETE_FILE')


def load_products(file_path):
    """Load products from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as prod_file:
        return json.load(prod_file)

def append_to_json_file(filename, items):
    
    if not os.path.exists(filename):
        # If the file doesn't exist, create it with the items
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=4)
    else:
        # If the file exists, load it, append new items, and overwrite
        with open(filename, 'r+', encoding='utf-8') as f:
            data = json.load(f)  
            data.extend(items)  
            f.seek(0)  
            json.dump(data, f, ensure_ascii=False, indent=4)  


def process_products(product_file, delete_file):
    """Delete products with specific conditions and save them to a separate file."""
    products = load_products(product_file)
    
    deleted_products = []
    remaining_products = []

    for product in products:
        
        if product['productId'].startswith('f'):
            if product.get('moq') in [2, None]:
                product['moq'] = 1

            
            if product.get('moq', 0) > 12:
                deleted_products.append(product)
                continue

        remaining_products.append(product)

    
    if deleted_products:
        append_to_json_file(delete_file, deleted_products)

    
    with open(product_file, 'w', encoding='utf-8') as f:
        json.dump(remaining_products, f, ensure_ascii=False, indent=4)


# Call the function to process products
process_products(product_file, delete_file)