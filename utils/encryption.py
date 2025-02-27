import hashlib
import os
import base64

def hash_password(password):
    """
    Haszuje hasło z użyciem salt, aby zapewnić bezpieczeństwo
    
    Args:
        password (str): Hasło w czystej postaci
        
    Returns:
        str: Zahaszowane hasło w formacie salt:hash
    """
    # Generuj losowy salt
    salt = os.urandom(32)
    
    # Haszuj hasło z solą
    key = hashlib.pbkdf2_hmac(
        'sha256',                # Algorytm hashu
        password.encode('utf-8'), # Konwertuj hasło na bajty
        salt,                     # Sól do haszowania
        100000                    # Liczba iteracji
    )
    
    # Zwróć salt:hash w formie zaszyfrowanej (base64)
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    key_b64 = base64.b64encode(key).decode('utf-8')
    
    return f"{salt_b64}:{key_b64}"

def verify_password(stored_password, provided_password):
    """
    Weryfikuje hasło z zapisanym hashem
    
    Args:
        stored_password (str): Zapisane zahaszowane hasło w formacie salt:hash
        provided_password (str): Hasło podane do weryfikacji
        
    Returns:
        bool: True jeśli hasło jest poprawne, False w przeciwnym przypadku
    """
    # Rozdziel salt i hash
    salt_b64, key_b64 = stored_password.split(':')
    salt = base64.b64decode(salt_b64)
    
    # Haszuj podane hasło z tym samym saltem
    new_key = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode('utf-8'),
        salt,
        100000
    )
    
    # Konwertuj na base64 dla porównania
    new_key_b64 = base64.b64encode(new_key).decode('utf-8')
    
    # Porównaj klucze
    return key_b64 == new_key_b64