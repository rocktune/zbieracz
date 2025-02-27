import os
import sqlite3
import json
from pathlib import Path

class DBManager:
    """Klasa zarządzająca połączeniem z bazą danych"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Ścieżka do pliku konfiguracyjnego
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
        
        # Domyślna ścieżka do bazy danych
        default_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'work_tracker.db')
        
        # Sprawdź czy istnieje plik konfiguracyjny
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.db_path = config.get('db_path', default_db_path)
        else:
            # Jeśli nie ma pliku konfiguracyjnego, stwórz go
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            self.db_path = default_db_path
            with open(self.config_path, 'w') as f:
                json.dump({'db_path': self.db_path}, f)
        
        # Upewnij się, że katalog bazy danych istnieje
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = None
        self._initialized = True
    
    def get_connection(self):
        """Zwraca połączenie z bazą danych"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close_connection(self):
        """Zamyka połączenie z bazą danych"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def update_db_path(self, new_path):
        """Aktualizuje ścieżkę do bazy danych"""
        # Zamknij istniejące połączenie
        self.close_connection()
        
        # Aktualizuj ścieżkę
        self.db_path = new_path
        
        # Zaktualizuj plik konfiguracyjny
        with open(self.config_path, 'w') as f:
            json.dump({'db_path': self.db_path}, f)
        
        # Upewnij się, że katalog istnieje
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Ponownie nawiąż połączenie
        return self.get_connection()