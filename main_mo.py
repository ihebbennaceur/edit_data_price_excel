import json
import re
import pandas as pd

FILE_NAME = 'sample (1).json'
EXCEL_RULES_FILE = 'rules.xlsx'  

class DataCleaner:
    def __init__(self, excel_file):
        """Initialise le nettoyeur avec les règles de suppression et de remplacement."""
        self.delete_keywords = {}  # Clé -> liste des mots-clés à supprimer
        self.delete_phrases = {}  # Clé -> liste des phrases à supprimer
        self.text_to_delete = []  # Liste des textes à supprimer peu importe la clé
        self.regex_rules_to_delete = []  # Liste des règles regex à supprimer peu importe la clé
        self.text_to_delete_with_key = {}  # Clé -> liste des textes à supprimer (clé importe)
        self.replacement_rules = {}  # Stocke les correspondances old -> new


        print("[INFO] Chargement des règles depuis l'excel...")
        self.load_rules(excel_file)
        


        print("[INFO] Règles chargées avec succès.")
    
    
    def load_rules(self, excel_file):
        """Charge les règles de nettoyage depuis un fichier Excel."""
        df = pd.read_excel(excel_file, engine='openpyxl')
        for _, row in df.iterrows():
            # Récuperer les values qui ne doivent PAS être contain dans un sku avec sa clé
            if pd.notna(row[0]) and pd.notna(row[1]):
                key = str(row[0])
                value = str(row[1])
                if key not in self.delete_keywords:
                    self.delete_keywords[key] = []
                self.delete_keywords[key].append(value)
            
            # Récuperer les phrases exactes qui déterminent la suppression de SKUet leur key
            if pd.notna(row[2]) and pd.notna(row[3]):
                key = str(row[2])
                value = str(row[3])
                if key not in self.delete_phrases:
                    self.delete_phrases[key] = []
                self.delete_phrases[key].append(value)

            # Récuperer les texte à effacer peu importe la clé
            if pd.notna(row[4]):
                if str(row[4]).startswith('regexp:'): # S'il contient du regex
                   pattern = str(row[4]).replace('regexp:', '')
                   self.regex_rules_to_delete.append(re.compile(pattern))
                else:
                    self.text_to_delete.append(str(row[4])) #Sinon c'est un texte simple
                    
            # Récuperer les textes à effacer selon la clé
            if pd.notna(row[5]) and pd.notna(row[6]):
                key = str(row[5])
                value = str(row[6])
                if key not in self.text_to_delete_with_key:
                    self.text_to_delete_with_key[key] = []
                self.text_to_delete_with_key[key].append(value)
                    
            # Récupérer old (ligne 7) et new (ligne 8)
            if pd.notna(row[7]) and pd.notna(row[8]):  # Vérifie que les colonnes old et new existent
                 old = str(row[7])
                 new = str(row[8])
                 self.replacement_rules[old] = new  # Stocke la correspondance directement

            




    def clean_json(self, data):
        """Parcourt le JSON et nettoie les données en fonction des règles définies."""
        print("[INFO] Début du nettoyage des données...")
        for product in data:
            if 'sku' in product:
                skus_to_remove = []
                for sku in product['sku']:
                    detected_keyword = self.should_remove_sku(sku)
                    if detected_keyword:
                        print(f"[SUPPRESSION SKU] SKU ID: {sku.get('skuId', 'N/A')} - Mot clé détecté: {detected_keyword}")
                        skus_to_remove.append(sku)
                    else:
                        self.clean_sku(sku)
                
                # Filtrer les SKU pour retirer ceux marqués pour suppression
                product['sku'] = [s for s in product['sku'] if s not in skus_to_remove]
                
                
        print("[INFO] Début du remplacement des textes...")
        cleaned_data = self.replace_text_in_json(data)
        print("[INFO] Remplacement terminé.")
        print("[INFO] Nettoyage terminé.")
        return cleaned_data

    def should_remove_sku(self, sku):
        """Détermine si un SKU doit être supprimé en fonction de ses attributs."""
        for prop in sku.get('skuProps', []):
            key = prop.get('key')
            value = prop.get('value', {}).get('zh', '')

            if key in self.delete_keywords:
                for kw in self.delete_keywords[key]:
                    if kw in value:
                        return kw

            if key in self.delete_phrases:
                if value in self.delete_phrases[key]:
                    return value

        return None
    
    def replace_text_in_json(self, data):
        if isinstance(data, dict):
            return {key: self.replace_text_in_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.replace_text_in_json(item) for item in data]
        elif isinstance(data, str):
            original_data = data.strip()  # Supprime espaces avant/après
            modified_data = original_data  # Copie pour appliquer tous les remplacements
            
            for old, new in self.replacement_rules.items():
                old_norm = old.strip()  # Supprime espaces invisibles
                if old_norm in modified_data:
                    print(f"[REMPLACEMENT] '{old_norm}' → '{new}' dans '{modified_data}'")  # Debug
                    modified_data = modified_data.replace(old_norm, new)  # MAJ après chaque remplacement
            
            return modified_data  # Retourne la version modifiée après tous les changements
        else:
            return data

    def clean_sku(self, sku):
        """Nettoie un SKU en appliquant les règles regex, suppressions et remplacements."""
        for prop in sku.get('skuProps', []):
            if 'value' in prop and isinstance(prop['value'], dict):
                for lang_key, lang_value in prop['value'].items():
                    if isinstance(lang_value, str):
                        # Suppression de textes peu importe la key
                        for text in self.text_to_delete:
                            if text in lang_value:
                                print(f"[SUPPRESSION TEXT] SKU ID: {sku.get('skuId', 'N/A')} - Suppression de '{text}'")
                                lang_value = lang_value.replace(text, '')
                        
                        # Suppression de textes spécifiques à la clé "row 5"
                        key = prop.get('key')
                        if key in self.text_to_delete_with_key:
                            for text in self.text_to_delete_with_key[key]:
                                 if text in lang_value:
                                     print(f"[SUPPRESSION TEXT] SKU ID: {sku.get('skuId', 'N/A')} - Suppression de '{text}' pour la clé '{key}'")
                                     lang_value = lang_value.replace(text, '')


                        # Suppression des textes selon regex peu importe la key
                        for pattern in self.regex_rules_to_delete:
                            if pattern.search(lang_value):
                                print(f"[SUPPRESSION TEXT] SKU ID: {sku.get('skuId', 'N/A')} - Regex appliquée sur '{lang_value}'")
                                lang_value =  pattern.sub('', lang_value)

                        

                        # Mise à jour de la valeur
                        prop['value'][lang_key] = lang_value
                        
                       
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
    
# Fonctions utilitaires pour charger et sauvegarder des fichiers JSON
def load_json(file_path):
    """Charge un fichier JSON et retourne son contenu."""
    print(f"[INFO] Chargement du fichier JSON: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    """Sauvegarde des données dans un fichier JSON."""
    print(f"[INFO] Sauvegarde du fichier JSON: {file_path}")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main_mo():
    """Point d'entrée du programme: chargement, nettoyage et sauvegarde des données."""
    try:
        data = load_json(FILE_NAME)  # Chargement du fichier JSON
        cleaner = DataCleaner(EXCEL_RULES_FILE)  # Initialisation du nettoyeur
        cleaned_data = cleaner.clean_json(data)  # Nettoyage des données
        cleaned_data = convert_size_notation(cleaned_data) # Applique les regroupements pour les XXXL
        save_json(cleaned_data, FILE_NAME)  # Sauvegarde des résultats
        print("[SUCCÈS] Traitement terminé. Résultat sauvegardé dans output.json")
    except Exception as e:
        print(f"[ERREUR] {e}")

# Exécution du script principal si le fichier est exécuté directement
if __name__ == "__main__":
   
    main_mo()
