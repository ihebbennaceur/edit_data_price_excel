import os
import time
import json
import re
import random
import pandas as pd
from dotenv import load_dotenv

def main_process():
    load_dotenv()


    
    props_file = os.getenv("DEL")
    products_file = os.getenv('PRODUCTS_FILE')

    # Запуск таймера
    start_time = time.time()

    # Загрузка JSON-файла
    with open(products_file, 'r', encoding='utf-8') as data_file:
        data = json.load(data_file)

    # Загрузка слов-паразитов
    parasitic_words = []
    with open('parasitic_title.txt', 'r', encoding='utf-8') as words_file:
        for line in words_file:
            line = line.strip()
            if line and not line.startswith("#"):  # Пропускаем комментарии
                if line.startswith("regexp:"):
                    parasitic_words.append(("regexp", line[len("regexp:"):] ))
                else:
                    parasitic_words.append(("text", line))

    # Загрузка критериев из props.xlsx
    props_df = pd.read_excel(props_file)
    props_criteria = props_df.fillna("").to_dict(orient='records')  # Заполнение пустых значений строками

    # Функция для безопасной записи в JSON-файл
    def append_to_json_file(file_path, item):
        if os.path.exists(file_path):
            with open(file_path, 'r+', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
                data.append(item)
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([item], f, ensure_ascii=False, indent=4)

    # Применение правил
    processed_data = []
    for item in data:
        # Очистка title
        if "title" in item and "zh" in item["title"]:
            original_text = item["title"]["zh"]
            cleaned_text = original_text
            for word_type, word in parasitic_words:
                if word_type == "text":
                    cleaned_text = cleaned_text.replace(word, "")
                elif word_type == "regexp":
                    cleaned_text = re.sub(word, "", cleaned_text)
            item["title"]["ru"] = cleaned_text

        # Удаление элементов из props["zh"]
        if "props" in item and "zh" in item["props"]:
            original_props = item["props"]["zh"]
            updated_props = []
            for prop in original_props:
                key = prop.get("key", "").strip()
                value = prop.get("value", "").strip()

                #Если ключ или значение содержит "null", то пропускаем этот элемент
                if "null" in key.lower() or "null" in value.lower():
                    continue

                # Проверка критериев
                remove = False
                for criteria in props_criteria:
                    crit_key = str(criteria.get("key", "")).strip()
                    crit_value = str(criteria.get("value", "")).strip()

                    # Удаляем, если совпадает ключ или значение
                    if (crit_key and key == crit_key) or (crit_value and value == crit_value):
                        remove = True
                    # Удаляем только если оба совпадают, если критерии непустые
                    if crit_key and crit_value and key == crit_key and value == crit_value:
                        remove = True
                        break

                if not remove:
                    updated_props.append(prop)
            item["props"]["zh"] = updated_props

        # Обработка rating
        if item['rating']['value'] == 0:
            item['rating']['value'] = random.choices([3, 4, 5], weights=[0.2, 0.5, 0.3], k=1)[0]
        if item['rating']['count'] == 0:
            item['rating']['count'] = round(item['soldCount'] / 1.3)

        # Обработка viewCount
        if item['viewCount'] == 0:
            item['viewCount'] = item['soldCount'] * 5

        # Обработка reviewCount
        if item['reviewCount'] == 0:
            item['reviewCount'] = round(item['soldCount'] / 1.5)

        # Обработка totalQuantity в d
        if item['productId'].startswith('d'):
            if item['totalQuantity'] < 100:
                item['totalQuantity'] += 400

        # Добавляем обработанный товар в список
        processed_data.append(item)

    # Сохранение результата обратно в файл
    with open(products_file, 'w', encoding='utf-8') as data_file:
        json.dump(processed_data, data_file, ensure_ascii=False, indent=4)

    # Вывод времени выполнения
    end_time = time.time()
    print(f"Обработка завершена за {end_time - start_time:.2f} секунд.")

    # New logic to update postFee
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
                        if average_price < 0.5:
                            postFee = 0
                        elif average_price < 1:
                            postFee = 0.5
                        elif average_price < 2:
                            postFee = 1
                        elif average_price < 5:
                            postFee = 3
                        elif average_price < 8:
                            postFee = 4
                        elif average_price < 12:
                            postFee = 5
                        elif average_price < 20:
                            postFee = 6
                        elif average_price < 50:
                            postFee = 7
                        elif average_price < 100:
                            postFee = 9
                        else:
                            postFee = 20
                    # Logic for productId starting with "n" or "d"
                    elif item.get("productId", "").startswith(("n", "d")):
                        if average_price < 0.5:
                            postFee = 0
                        elif average_price < 1:
                            postFee = 0.5
                        elif average_price < 2:
                            postFee = 1
                        elif average_price < 5:
                            postFee = 3
                        elif average_price < 8:
                            postFee = 4
                        elif average_price < 12:
                            postFee = 5
                        elif average_price < 20:
                            postFee = 6
                        elif average_price < 50:
                            postFee = 7
                        elif average_price < 100:
                            postFee = 9
                        else:
                            postFee = 10

                    # Update the postFee value
                    item["postFee"] = postFee / item.get("moq", 1) if item.get("moq") else postFee

                    # Additional processing after updating postFee
                    # Обработка moq у f 2, 0 меняем на 1
                    if item['productId'].startswith('f'):
                        if item['moq'] in [2, None]:
                            item['moq'] = 1

                    # Увеличиваем quantity для productId, начинающихся с "d"
                    for sku in item['sku']:
                        if item['productId'].startswith('d'):
                            if sku['quantity'] < 100:
                                sku['quantity'] += 200

                return products

            # Calculate and update postFee
            updated_products = calculate_postfee(products)

            # Write the updated data back to the file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(updated_products, f, ensure_ascii=False, indent=4)

        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON. Please check the file's format.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    # Call the function to update postFee
    update_postfee_in_json(products_file)

if __name__ == "__main__":
    main_process()
