import json
import re

FILE_NAME = 'sample.json'
keywords = ['自由选择', '客服']  # Pour la fonction 1
phrases = ['年后出货 出货时间联系客服', '见包装']  # Pour la fonction 2
FULL_DELETE = False  # True = efface complètement le texte pour la Fonction 3 et 4, False = Efface juste la partie trouvée

def load_json(file_path):
    """Charge un fichier JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    """Sauvegarde les données dans un fichier JSON."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def filter_skus_by_keywords(products, keywords):
    """Supprime les SKUs contenant des mots-clés spécifiques dans 'skuProps'."""
    for product in products:
        if 'sku' in product:
            skus_to_remove = []
            for sku in product['sku']:
                for prop in sku.get('skuProps', []):
                    if prop.get('key') == 'Color':
                        color_value = prop.get('value', {}).get('zh', '')
                        if any(kw in color_value for kw in keywords):
                            print(f"[SUPPRESSION] SKU {sku.get('skuId', 'UNKNOWN')} supprimé (mot-clé détecté : {color_value})")
                            skus_to_remove.append(sku)
                            break  # On sort dès qu'un mot-clé est trouvé

            # Supprimer les SKUs identifiés
            product['sku'] = [sku for sku in product['sku'] if sku not in skus_to_remove]
    return products

def filter_skus_by_exact_phrases(products, phrases):
    """Supprime les SKUs contenant des phrases exactes dans 'skuProps'."""
    for product in products:
        if 'sku' in product:
            skus_to_remove = []
            for sku in product['sku']:
                for prop in sku.get('skuProps', []):
                    if prop.get('key') == 'Color':
                        color_value = prop.get('value', {}).get('zh', '')
                        if color_value in phrases:
                            print(f"[SUPPRESSION] SKU {sku.get('skuId', 'UNKNOWN')} supprimé (phrase exacte détectée : {color_value})")
                            skus_to_remove.append(sku)
                            break  # Sortir dès qu'on trouve une correspondance

            # Supprimer les SKUs identifiés
            product['sku'] = [sku for sku in product['sku'] if sku not in skus_to_remove]
    return products

def clean_skus_by_regex_1(products):
    """Supprime ou nettoie les valeurs contenant le motif \d+-\d+斤 dans 'skuProps'."""
    pattern = re.compile(r"\d+-\d+斤")
    
    for product in products:
        if 'sku' in product:
            for sku in product['sku']:
                for prop in sku.get('skuProps', []):
                    if 'value' in prop and isinstance(prop['value'], dict):
                        for lang_key, lang_value in prop['value'].items():
                            if isinstance(lang_value, str):  # Vérifier que c'est bien un texte
                                if pattern.search(lang_value):  # Vérifie si la valeur contient le motif
                                    new_value = "" if FULL_DELETE else pattern.sub("", lang_value)

                                    if lang_value != new_value:
                                        print(f"[MODIFICATION] SKU {sku.get('skuId', 'UNKNOWN')} ({lang_key}) : '{lang_value}' → '{new_value}'")
                                        prop['value'][lang_key] = new_value
    return products

def clean_skus_by_regex_2(products):
    """Supprime ou nettoie les valeurs contenant le motif 推荐\d+-\d+斤 dans 'skuProps'."""
    pattern = re.compile(r"推荐\d+-\d+斤")
    
    for product in products:
        if 'sku' in product:
            for sku in product['sku']:
                for prop in sku.get('skuProps', []):
                    if 'value' in prop and isinstance(prop['value'], dict):
                        for lang_key, lang_value in prop['value'].items():
                            if isinstance(lang_value, str):  # Vérifier que c'est bien un texte
                                if pattern.search(lang_value):  # Vérifie si la valeur contient le motif
                                    new_value = "" if FULL_DELETE else pattern.sub("", lang_value)

                                    if lang_value != new_value:
                                        print(f"[MODIFICATION] SKU {sku.get('skuId', 'UNKNOWN')} ({lang_key}) : '{lang_value}' → '{new_value}'")
                                        prop['value'][lang_key] = new_value
    return products

def replace_brackets(obj):
    """
    Remplace 【 par ( et 】 par ) dans toutes les valeurs de type string dans un JSON.
    Affiche les valeurs modifiées pour voir les changements.
    """
    if isinstance(obj, dict):
        return {k: replace_brackets(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_brackets(v) for v in obj]
    elif isinstance(obj, str):
        new_value = obj.replace("【", "(").replace("】", ")")
        if obj != new_value:  # Afficher seulement si une modification a été faite
            print(f"[BRACKET REPLACEMENT] '{obj}' → '{new_value}'")
        return new_value
    else:
        return obj

def convert_size_notation(obj):
    """
    Convertit XXL, XXXL, etc., en 2XL, 3XL, etc., dans toutes les valeurs de type string
    trouvées dans un JSON. XL reste XL.
    Affiche les modifications pour vérification.
    """
    size_pattern = re.compile(r"^(X+L)(.*)$")  # Capture les X+L au début d'une string

    if isinstance(obj, dict):
        return {k: convert_size_notation(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_size_notation(v) for v in obj]
    elif isinstance(obj, str):
        match = size_pattern.match(obj)
        if match:
            x_part, rest = match.groups()
            if x_part == "XL":  # On garde XL tel quel
                return obj
            else:
                num_x = len(x_part) - 1  # Compter les X et retirer le L
                new_value = f"{num_x}XL{rest}"  # Reformater en 2XL, 3XL...
                if obj != new_value:
                    print(f"[XL CONVERSION] '{obj}' → '{new_value}'")
                return new_value
        return obj
    else:
        return obj
    
    
def function5():
    """Exécute le pipeline de nettoyage sur le JSON."""
    try:
        data = load_json(FILE_NAME)

        data = filter_skus_by_keywords(data, keywords)
        data = filter_skus_by_exact_phrases(data, phrases)
        data = clean_skus_by_regex_1(data)
        data = clean_skus_by_regex_2(data)
        
        # Remplacer les 【 et 】 partout dans le JSON
        data = replace_brackets(data)
        
        # Factoriser les XXL, XXXL, ...
        data = convert_size_notation(data)

        save_json(data, FILE_NAME)
        print(f"Traitement terminé. Résultat sauvegardé dans {FILE_NAME}")
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__function5__":
    function5()
