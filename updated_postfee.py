import json

from dotenv import load_dotenv
import os


load_dotenv()
products_file = os.getenv('PRODUCTS_FILE')
def update_postfee_in_json(file_path):
    
    try:
        # Load the data
        with open(file_path, 'r', encoding='utf-8') as f:
            products = json.load(f)

        # Update function
        def calculate_postfee(products):
            for item in products:
                skus = item.get("sku", [])
                total_price = sum(float(sku.get("originalPrice", 0)) for sku in skus)
                average_price = total_price / len(skus) if skus else 0

                
                postFee = 0

                # Logic for productId starting with "f"
                if item.get("productId", "").startswith("f"):
                    if average_price < 2:
                        postFee = 0
                    elif average_price < 5:
                        postFee = 1
                    elif average_price < 8:
                        postFee = 2
                    elif average_price < 12:
                        postFee = 3
                    elif average_price < 20:
                        postFee = 4
                    elif average_price < 50:
                        postFee = 5
                    elif average_price < 100:
                        postFee = 7
                    else:
                        postFee = 30
                # Logic for productId starting with "n" or "d"
                elif item.get("productId", "").startswith(("n", "d")):
                    if average_price < 2:
                        postFee = 0
                    elif average_price < 5:
                        postFee = 1
                    elif average_price < 8:
                        postFee = 2
                    elif average_price < 12:
                        postFee = 3
                    elif average_price < 20:
                        postFee = 5
                    elif average_price < 100:
                        postFee = 10
                    else:
                        postFee = 25

               
                # Update the postFee value
                item["postFee"] = postFee / item.get("moq", 1) if item.get("moq") else postFee

            return products

        # Calculate and update postFee
        updated_products = calculate_postfee(products)

        # Write the updated data back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(updated_products, f, ensure_ascii=False, indent=4)

        #print(f"Updated data successfully saved to {file_path}.")

    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON. Please check the file's format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")




update_postfee_in_json(products_file)
