import json
import re
import pandas as pd

# FILE_NAME = 'sample (1).json'
# EXCEL_RULES_FILE = 'rules_iheb.xlsx'  

from dotenv import load_dotenv
import os



load_dotenv()


FILE_NAME = os.getenv('PRODUCTS_FILE')
EXCEL_RULES_FILE=os.getenv('EXCEL_RULES_FILE')

class DataCleaner:
    def __init__(self, excel_file):
        """Initialise le nettoyeur avec les règles de suppression et de remplacement."""
        self.delete_keywords = {}  # Cle -> liste des mots-cles à supprimer
        self.delete_phrases = {}  # Cle -> liste des phrases à supprimer
        self.text_to_delete = []  # Liste des textes à supprimer peu importe la cle
        self.regex_rules_to_delete = []  # Liste des règles regex à supprimer peu importe la cle
        self.text_to_delete_with_key = {}  # Cle -> liste des textes à supprimer (cle importe)
        self.replacement_rules = {}  # Stocke les correspondances old -> new
        
        self.values_to_remove_in_phrase = []  # Liste des valeurs à supprimer si trouvees dans une phrase
        self.exact_values_to_remove = []  # Liste des valeurs à supprimer si elles correspondent exactement
        
        self.props_to_remove=[] #list pour les mots-cle a supprimer
        self.props_values_to_remove = []  # Liste des valeurs à supprimer dans skuProps
        self.props_to_remove_by_key_value = [] 


        print("[INFO] Chargement des règles depuis l'excel...")
        self.load_rules(excel_file)
        


        print("[INFO] Règles chargees avec succès.")
    
    
    def load_rules(self, excel_file):
        """Charge les règles de nettoyage depuis un fichier Excel."""
        df = pd.read_excel(excel_file, engine='openpyxl')
        for _, row in df.iterrows():
            # Recuperer les values qui ne doivent PAS être contain dans un sku avec sa cle
            if pd.notna(row.iloc[0]
) and pd.notna(row.iloc[1]
):
                key = str(row.iloc[0]
)
                value = str(row.iloc[1]
)
                if key not in self.delete_keywords:
                    self.delete_keywords[key] = []
                self.delete_keywords[key].append(value)
            
            # Recuperer les phrases exactes qui determinent la suppression de SKUet leur key
            if pd.notna(row.iloc[2]
) and pd.notna(row.iloc[3]
):
                key = str(row.iloc[2]
)
                value = str(row.iloc[3]
)
                if key not in self.delete_phrases:
                    self.delete_phrases[key] = []
                self.delete_phrases[key].append(value)

            # Recuperer les texte à effacer peu importe la cle
            if pd.notna(row.iloc[4]
):
                if str(row.iloc[4]
).startswith('regexp:'): # S'il contient du regex
                   pattern = str(row.iloc[4]
).replace('regexp:', '')
                   self.regex_rules_to_delete.append(re.compile(pattern))
                else:
                    self.text_to_delete.append(str(row.iloc[4]
)) #Sinon c'est un texte simple
                    
            # Recuperer les textes à effacer selon la cle
            if pd.notna(row.iloc[5]
) and pd.notna(row.iloc[6]
):
                key = str(row.iloc[5]
)
                value = str(row.iloc[6]
)
                if key not in self.text_to_delete_with_key:
                    self.text_to_delete_with_key[key] = []
                self.text_to_delete_with_key[key].append(value)
                    
            # Recuperer old (ligne 7) et new (ligne 8)
            if pd.notna(row.iloc[7]
) and pd.notna(row.iloc[8]
):  # Verifie que les colonnes old et new existent
                 old = str(row.iloc[7]
)
                 new = str(row.iloc[8]
)
                 self.replacement_rules[old] = new  # Stocke la correspondance directement

            # Recuperer les valeurs à supprimer si trouvees dans une phrase
            if pd.notna(row.iloc[9]
):  # Colonne 9 pour les valeurs dans une phrase
                self.values_to_remove_in_phrase.append(str(row.iloc[9]
))

            # Recuperer les valeurs à supprimer si elles correspondent exactement
            if pd.notna(row.iloc[10]
):  # Colonne 10 pour les valeurs exactes
                self.exact_values_to_remove.append(str(row.iloc[10]
))

            if pd.notna(row.iloc[11]
)  : #lire col 11
                self.props_to_remove.append((str(row.iloc[11]
)) )

             # Charger les valeurs de la nouvelle colonne (colonne 12)
            if pd.notna(row.iloc[12]
):  # Colonne 12 pour les valeurs à supprimer
                self.props_values_to_remove.append(str(row.iloc[12]
))   
            if pd.notna(row.iloc[13]
) and pd.notna(row.iloc[14]
):  # Colonnes 13 et 14
                key = str(row.iloc[13]
)
                value = str(row.iloc[14]
)
                self.props_to_remove_by_key_value.append((key, value)) 


    def clean_sku_props_by_key_value(self, sku):
        """Supprime les dictionnaires dans skuProps si leur clé et valeur correspondent aux règles."""
        if 'skuProps' in sku:
            original_props = sku['skuProps']
            
            sku['skuProps'] = [
                prop for prop in original_props
                if (prop.get('key'), prop.get('value', {}).get('zh')) not in self.props_to_remove_by_key_value
            ]
            
            if len(original_props) != len(sku['skuProps']):
                print(f"[SUPPRESSION PROP PAR CLE ET VALEUR] SKU ID: {sku.get('skuId', 'N/A')} - Props supprimées.")            

    def clean_sku_props_by_value(self, sku):
        """Supprime les dictionnaires dans skuProps si leur valeur correspond à props_values_to_remove."""
        if 'skuProps' in sku:
            original_props = sku['skuProps']
            
            sku['skuProps'] = [
                prop for prop in original_props
                if not any(
                    lang_value in self.props_values_to_remove  # Verifie si la valeur est à supprimer
                    for lang_value in prop.get('value', {}).values()
                )
            ]
            
            if len(original_props) != len(sku['skuProps']):
                print(f"[SUPPRESSION PROP PAR VALEUR] SKU ID: {sku.get('skuId', 'N/A')} - Props supprimees/ value.")


    def clean_sku_props_by_key(self, sku):
        """Supprime les dictionnaires dans skuProps si leur cle"""
        if 'skuProps' in sku:
          original_props = sku['skuProps']
          sku['skuProps'] = [
            prop for prop in original_props
            if prop.get('key') not in self.props_to_remove]
          
          if len(original_props) != len(sku['skuProps']):
            print(f"[SUPPRESSION PROP] SKU ID: {sku.get('skuId', 'N/A')} - Props supprimees /key.")


    def clean_json(self, data):
        """Parcourt le JSON et nettoie les donnees en fonction des règles definies."""
        print("[INFO] Debut du nettoyage des donnees...")
        for product in data:
            if 'sku' in product:
                skus_to_remove = []
                for sku in product['sku']:
                    # Nettoyer les props par cle
                    self.clean_sku_props_by_key(sku)
                    # Nettoyer les props par valeur
                    self.clean_sku_props_by_value(sku)
                    
                    self.clean_sku_props_by_key_value(sku)
                    # Anciennes logiques
                    detected_keyword = self.should_remove_sku(sku)
                    if detected_keyword:
                        print(f"[SUPPRESSION SKU] SKU ID: {sku.get('skuId', 'N/A')} - Mot cle detecte: {detected_keyword}")
                        skus_to_remove.append(sku)
                    else:
                        self.clean_sku(sku)
                    
                    if self.should_remove_sku_by_value_in_phrase(sku) or self.should_remove_sku_by_exact_value(sku):
                        skus_to_remove.append(sku)
                
                # Filtrer les SKU pour retirer ceux marques pour suppression
                product['sku'] = [s for s in product['sku'] if s not in skus_to_remove]
        
        print("[INFO] Debut du remplacement des textes...")
        cleaned_data = self.replace_text_in_json(data)
        print("[INFO] Remplacement termine.")
        print("[INFO] Nettoyage termine.")
        return cleaned_data

    def should_remove_sku(self, sku):
        """Determine si un SKU doit être supprime en fonction de ses attributs."""
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
    
    def should_remove_sku_by_value_in_phrase(self, sku):
        """Supprime le SKU si une valeur est trouvee dans une phrase."""
        for prop in sku.get('skuProps', []):
            if 'value' in prop and isinstance(prop['value'], dict):
                for lang_key, lang_value in prop['value'].items():  # Parcourt toutes les cles dans 'value'
                    if isinstance(lang_value, str):
                        for phrase in self.values_to_remove_in_phrase:
                            if phrase in lang_value:
                                print(f"[SUPPRESSION PHRASE] SKU ID: {sku.get('skuId', 'N/A')} - Phrase detectee: '{phrase}' dans '{lang_key}'")
                                return True
        return False

    def should_remove_sku_by_exact_value(self, sku):
        """Supprime le SKU si une valeur correspond exactement."""
        for prop in sku.get('skuProps', []):
            if 'value' in prop and isinstance(prop['value'], dict):
                for lang_key, lang_value in prop['value'].items():  # Parcourt toutes les cles dans 'value'
                    if isinstance(lang_value, str):
                        if lang_value in self.exact_values_to_remove:
                            print(f"[SUPPRESSION EXACTE] SKU ID: {sku.get('skuId', 'N/A')} - Valeur exacte detectee: '{lang_value}' dans '{lang_key}'")
                            return True
        return False

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
            
            return modified_data  # Retourne la version modifiee après tous les changements
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
                        
                        # Suppression de textes specifiques à la cle "row 5"
                        key = prop.get('key')
                        if key in self.text_to_delete_with_key:
                            for text in self.text_to_delete_with_key[key]:
                                 if text in lang_value:
                                     print(f"[SUPPRESSION TEXT] SKU ID: {sku.get('skuId', 'N/A')} - Suppression de '{text}' pour la cle '{key}'")
                                     lang_value = lang_value.replace(text, '')


                        # Suppression des textes selon regex peu importe la key
                        for pattern in self.regex_rules_to_delete:
                            if pattern.search(lang_value):
                                print(f"[SUPPRESSION TEXT] SKU ID: {sku.get('skuId', 'N/A')} - Regex appliquee sur '{lang_value}'")
                                lang_value =  pattern.sub('', lang_value)

                        

                        # Mise à jour de la valeur
                        prop['value'][lang_key] = lang_value
                        
                       
def convert_size_notation(obj):
    """
    Convertit XXL, XXXL, etc., en 2XL, 3XL, etc., dans toutes les valeurs de type string
    trouvees dans un JSON. XL reste XL.
    Affiche les modifications pour verification.
    """
    size_pattern = re.compile(r"^(X+L)(.*)$")  # Capture les X+L au debut d'une string

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
    """Sauvegarde des donnees dans un fichier JSON."""
    print(f"[INFO] Sauvegarde du fichier JSON: {file_path}")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main_mo():

    print("main_mov2 here")
    print("####################################################################")
    print()
    try:
        data = load_json(FILE_NAME)  # Chargement du fichier JSON
        cleaner = DataCleaner(EXCEL_RULES_FILE)  # Initialisation du nettoyeur
        cleaned_data = cleaner.clean_json(data)  # Nettoyage des donnees
        cleaned_data = convert_size_notation(cleaned_data) # Applique les regroupements pour les XXXL
        save_json(cleaned_data, FILE_NAME)  # Sauvegarde des resultats
        print("[SUCCÈS] Traitement termine. Resultat sauvegarde ")
    except Exception as e:
        print(f"[ERREUR] {e}")

# Execution du script principal si le fichier est execute directement
if __name__ == "__main__":
    main_mo()
