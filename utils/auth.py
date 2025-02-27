from database.models import User
from utils.encryption import hash_password, verify_password

class AuthManager:
    """Klasa zarządzająca autoryzacją użytkowników"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.current_user = None
        self._initialized = True
    
    def register_user(self, username, first_name, last_name, password, is_admin=False):
        """
        Rejestruje nowego użytkownika
        
        Args:
            username (str): Nazwa użytkownika
            first_name (str): Imię
            last_name (str): Nazwisko
            password (str): Hasło
            is_admin (bool): Czy użytkownik ma być administratorem
            
        Returns:
            User: Utworzony użytkownik lub None jeśli rejestracja się nie powiodła
        """
        # Sprawdź czy użytkownik już istnieje
        if User.get_by_username(username):
            return None
        
        # Zahaszuj hasło
        password_hash = hash_password(password)
        
        # Utwórz nowego użytkownika
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
            is_admin=is_admin
        )
        
        # Zapisz użytkownika
        user.save()
        
        return user
    
    def login(self, username, password):
        """
        Loguje użytkownika
        
        Args:
            username (str): Nazwa użytkownika
            password (str): Hasło
            
        Returns:
            User: Zalogowany użytkownik lub None jeśli logowanie się nie powiodło
            str: "reset_required" jeśli użytkownik musi zresetować hasło
        """
        # Pobierz użytkownika
        user = User.get_by_username(username)
        
        if not user:
            return None
        
        # Sprawdź hasło
        if not verify_password(user.password_hash, password):
            return None
        
        # Sprawdź, czy użytkownik musi zmienić hasło
        if user.password_reset_required:
            # Ustaw bieżącego użytkownika (potrzebne do zmiany hasła)
            self.current_user = user
            return "reset_required"
        
        # Ustaw bieżącego użytkownika
        self.current_user = user
        
        return user
    
    def logout(self):
        """Wylogowuje aktualnego użytkownika"""
        self.current_user = None
    
    def change_password(self, user_id, old_password, new_password):
        """
        Zmienia hasło użytkownika
        
        Args:
            user_id (int): ID użytkownika
            old_password (str): Stare hasło
            new_password (str): Nowe hasło
            
        Returns:
            bool: True jeśli zmiana się powiodła, False w przeciwnym przypadku
        """
        # Pobierz użytkownika
        user = User.get_by_id(user_id)
        
        if not user:
            return False
        
        # Sprawdź stare hasło
        if not verify_password(user.password_hash, old_password):
            return False
        
        # Ustaw nowe hasło
        user.password_hash = hash_password(new_password)
        
        # Zapisz użytkownika
        user.save()
        
        return True
    
    def reset_password(self, user_id, new_password=None):
        """
        Resetuje hasło użytkownika (tylko dla administratorów)
        
        Args:
            user_id (int): ID użytkownika
            new_password (str, optional): Nowe hasło. Jeśli None, generuje tymczasowe hasło.
            
        Returns:
            bool: True jeśli reset się powiódł, False w przeciwnym przypadku
            str: Tymczasowe hasło, jeśli new_password było None
        """
        # Sprawdź czy bieżący użytkownik jest administratorem
        if not self.current_user or not self.current_user.is_admin:
            return False
        
        # Pobierz użytkownika
        user = User.get_by_id(user_id)
        
        if not user:
            return False
        
        # Jeśli nie podano hasła, wygeneruj tymczasowe
        temp_password = None
        if new_password is None:
            import random
            import string
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            new_password = temp_password
        
        # Ustaw nowe hasło
        user.password_hash = hash_password(new_password)
        
        # Ustaw flagę wymuszającą zmianę hasła przy następnym logowaniu
        user.password_reset_required = True
        
        # Wyczyść flagę żądania resetowania hasła
        user.reset_requested = False
        
        # Zapisz użytkownika
        user.save()
        
        if temp_password:
            return True, temp_password
        
        return True
        
    def request_password_reset(self, username):
        """
        Wysyła prośbę o reset hasła
        
        Args:
            username (str): Nazwa użytkownika
            
        Returns:
            bool: True jeśli prośba została wysłana, False w przeciwnym przypadku
        """
        # Pobierz użytkownika
        user = User.get_by_username(username)
        
        if not user:
            return False
        
        # Ustaw flagę żądania resetowania hasła
        user.reset_requested = True
        
        # Zapisz użytkownika
        user.save()
        
        return True
        
    def complete_password_reset(self, new_password):
        """
        Kończy proces resetowania hasła po zalogowaniu
        
        Args:
            new_password (str): Nowe hasło
            
        Returns:
            bool: True jeśli zmiana się powiodła, False w przeciwnym przypadku
        """
        # Sprawdź czy jest zalogowany użytkownik
        if not self.current_user:
            return False
        
        # Ustaw nowe hasło
        self.current_user.password_hash = hash_password(new_password)
        
        # Wyłącz flagę wymuszającą zmianę hasła
        self.current_user.password_reset_required = False
        
        # Zapisz użytkownika
        self.current_user.save()
        
        return True