from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import binascii

key = b'3oup16byoeaefiex'  # 16-байтный ключ для AES-128
cipher = AES.new(key, AES.MODE_ECB)

def encrypt_user_id(user_id):
    # Преобразуем user_id в строку, если это число
    mapping = {
        '0': 'A', '1': 'B', '2': 'C', '3': 'D', '4': 'E',
        '5': 'F', '6': 'G', '7': 'H', '8': 'I', '9': 'J'
    }
    
    # Преобразуем каждую цифру в букву
    return ''.join(mapping[digit] for digit in str(user_id))

def decrypt_user_id(encrypted_user_id):
    # Расшифровываем строку обратно в цифры
    reverse_mapping = {
        'A': '0', 'B': '1', 'C': '2', 'D': '3', 'E': '4',
        'F': '5', 'G': '6', 'H': '7', 'I': '8', 'J': '9'
    }
    
    # Преобразуем каждую букву обратно в цифру
    return ''.join(reverse_mapping[letter] for letter in encrypted_user_id)

# Пример использования
user_id = 530866064
encrypted_user_id = encrypt_user_id(user_id)
print(f"Зашифрованный user_id: {encrypted_user_id}")

decrypted_user_id = decrypt_user_id(encrypted_user_id)
print(f"Расшифрованный user_id: {decrypted_user_id}")
