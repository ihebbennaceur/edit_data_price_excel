import json

from dotenv import load_dotenv
import os


load_dotenv()


products_file = os.getenv('PRODUCTS_FILE')
categories_file = os.getenv('CATEGORIES_FILE')

# Charger category_0.0.3.json
with open(categories_file, "r", encoding="utf-8") as f:
    category_data = json.load(f)

    # Mettre à jour les valeurs de profit pour chaque catégorie
    for cat in category_data["categories"]:
        if "tax" not in cat:
            cat["tax"] = {
                "TJ": 0,
                "UZ": 0,
                "RU": 0
            }
        if "profit" not in cat:    
            cat["profit"] = {
            "TJ": [120, 90, 70, 50, 30],  # Nouvelles valeurs de profit pour TJ
            "UZ": [120, 90, 70, 50, 30]   # Nouvelles valeurs de profit pour UZ
        }


# Sauvegarder les modifications dans category_0.0.3.json
with open(categories_file, "w", encoding="utf-8") as f:
    json.dump(category_data, f, ensure_ascii=False, indent=4)

print("Mise à jour des valeurs de profit dans category_0.0.3.json terminée !")

# Charger sample.json
with open(products_file, "r", encoding="utf-8") as f:
    sample_data = json.load(f)

# Coefficients de calcul
TJsize_price = 1900
UZsize_price = 6000

TJweight_price = 21
UZweight_price = 19

TJcurrency = 1.6
UZcurrency = 1700

# Construire un mapping des catégories pour un accès rapide
category_mapping = {cat["category"]["ru"]: cat for cat in category_data["categories"]}

# Fonction pour sélectionner le bon profit en fonction de price_conditions
def get_profit(price_conditions, profit_list):
    if price_conditions < 5:
        return int(profit_list[0])  # 120%
    elif 5 <= price_conditions < 10:
        return int(profit_list[1])  # 90%
    elif 10 <= price_conditions < 20:
        return int(profit_list[2])  # 70%
    elif 20 <= price_conditions < 50:
        return int(profit_list[3])  # 50%
    else:
        return int(profit_list[4])  # 30%


# Mise à jour des prix des produits et de leurs SKU
for product in sample_data:
    categories = product["categoryName"]["ru"].split("|")  # Un produit peut appartenir à plusieurs catégories
    for category in categories:
        if category in category_mapping:
            cat_data = category_mapping[category]

            shuttle_weight = cat_data["shuttleWeight"]
            width = cat_data["width"]
            height = cat_data["height"]
            length = cat_data["length"]
            volume = width * height * length / 1000000

            tax_TJ = int(cat_data["tax"]["TJ"])
            tax_UZ = int(cat_data["tax"]["UZ"])

            post_fee = product["postFee"]

            # Mise à jour des prix dans les SKU
            for sku in product["sku"]:
                original_price = float(sku.get("originalPrice", 0))  # Convertir en float pour éviter les erreurs
                price_conditions = original_price + post_fee + max(shuttle_weight * TJweight_price, volume * TJsize_price)
                price_conditions2= original_price + post_fee + max(shuttle_weight * UZweight_price, volume * UZsize_price)

                print("price_conditions", price_conditions)
                print("shuttle_weight", shuttle_weight)
                print("volume", volume)


                # Sélectionner le bon profit en fonction de price_conditions
                profit_TJ = get_profit(price_conditions, cat_data["profit"]["TJ"])
                profit_UZ = get_profit(price_conditions2, cat_data["profit"]["UZ"])

                # price_TJ = post_fee + original_price + max(shuttle_weight * TJweight_price, volume * TJsize_price) + (profit_TJ / 100) + (tax_TJ / 100)
                # price_UZ = post_fee + original_price + max(shuttle_weight * UZweight_price, volume * UZsize_price) + (profit_UZ / 100) + (tax_UZ / 100)

                cost_TJ = post_fee + original_price + max(shuttle_weight * TJweight_price, volume * TJsize_price)
                price_TJ = cost_TJ * (1 + profit_TJ / 100 )
                price_TJ = price_TJ * (1 + tax_TJ / 100) * TJcurrency
                print("percentage profit ",profit_TJ)
                print("tax percentage" ,tax_TJ)


                cost_UZ = post_fee + original_price + max(shuttle_weight * UZweight_price, volume * UZsize_price)
               
                price_UZ = cost_UZ * (1 + profit_UZ / 100) 
                price_UZ = price_UZ *(1+ tax_UZ / 100) * UZcurrency
                print("percentage profit ",profit_UZ)
                print("tax percentage" ,tax_UZ)

                sku["price"]["TJS"] = price_TJ
                sku["price"]["UZS"] = price_UZ


# Sauvegarde du fichier mis à jour
with open(products_file, "w", encoding="utf-8") as f:
    json.dump(sample_data, f, ensure_ascii=False, indent=4)

print("Mise à jour des prix des SKU terminée !")
print("price v2 finished")
  