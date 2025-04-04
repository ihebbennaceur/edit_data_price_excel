import sys
import os

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sc import update_product_categories

from delete_bymoq import process_products
#from updated_postfee import update_postfee_in_json
from editdatav2 import main_process
import time
import logging
from dotenv import load_dotenv




load_dotenv()


products_file = os.getenv('PRODUCTS_FILE')
categories_file = os.getenv('CATEGORIES_FILE')
excel_file = os.getenv('EXCEL_FILE')
delete_file = os.getenv('DELETE_FILE')


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logging.info(f"Loaded files: {products_file}, {categories_file}, {excel_file}, {delete_file}")

def safe_execute(func, *args):
    """Executes a function safely with exception handling."""
    try:
        func(*args)
    except Exception as e:
        logging.error(f"Error in {func.__name__}: {e}", exc_info=True)


import subprocess

def run_subprocess(script_path):
    try:
        result = subprocess.run(['python', script_path], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution du script {script_path}: {e}", exc_info=True)

def main():
    start_time = time.time()
    logging.info("Starting sequential execution...")

    safe_execute(main_process)
    safe_execute(update_product_categories, products_file, categories_file, excel_file)
    safe_execute(process_products, products_file, delete_file)

    run_subprocess('task 2 edit_data_t2_v2/price_task_v2.py')
    run_subprocess('task 2 edit_data_t2_v2/main_mo_v2.py')

    logging.info("All tasks completed!")
    end_time = time.time()
    logging.info(f"Execution Time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
   

# import subprocess

# # Exécution du script principal
# result = subprocess.run(['python', 'task 2 edit_data_t2_v2\price_task_v2.py'], capture_output=True, text=True)

# # Afficher la sortie du script exécuté
# print(result.stdout)
# print(result.stderr)
# result = subprocess.run(['python', 'task 2 edit_data_t2_v2\main_mo.py'], capture_output=True, text=True)
