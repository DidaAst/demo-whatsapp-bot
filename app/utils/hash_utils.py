import json
import hashlib

def get_unique_key(body):
    # Сериализация объекта body в строку JSON и кодирование в байты
    body_bytes = json.dumps(body, sort_keys=True).encode()

    # Создание хеша с использованием SHA-256
    hash_object = hashlib.sha256(body_bytes)

    # Получение уникального хеш-ключа в виде шестнадцатеричной строки
    unique_key = hash_object.hexdigest()

    return unique_key