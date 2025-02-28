from database.db_manager import DBManager
import time
import datetime

class User:
    """Model użytkownika"""
    
    def __init__(self, username, first_name, last_name, password_hash, is_admin=False, password_reset_required=False, reset_requested=False, id=None):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.password_reset_required = password_reset_required  # Czy użytkownik musi zmienić hasło przy logowaniu
        self.reset_requested = reset_requested  # Czy użytkownik poprosił o reset hasła
    
    @staticmethod
    def create_tables():
        """Tworzy tabelę użytkowników w bazie danych i aktualizuje schemat jeśli potrzeba"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        # Najpierw tworzymy tabelę użytkowników, jeśli nie istnieje
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0
        )
        ''')
        
        # Sprawdź, czy istnieją nowe kolumny i dodaj je, jeśli nie
        # SQLite nie ma bezpośredniej metody na sprawdzenie istnienia kolumny,
        # więc musimy użyć PRAGMA table_info
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Dodaj kolumny reset, jeśli ich nie ma
        if 'password_reset_required' not in column_names:
            cursor.execute('ALTER TABLE users ADD COLUMN password_reset_required BOOLEAN NOT NULL DEFAULT 0')
        
        if 'reset_requested' not in column_names:
            cursor.execute('ALTER TABLE users ADD COLUMN reset_requested BOOLEAN NOT NULL DEFAULT 0')
        
        conn.commit()
    
    @staticmethod
    def get_by_id(user_id):
        """Pobiera użytkownika na podstawie ID"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            # Bezpieczne pobieranie pól, które mogą nie istnieć w starszych wersjach bazy
            password_reset_required = False
            reset_requested = False
            
            try:
                password_reset_required = bool(user_data['password_reset_required'])
            except (IndexError, KeyError):
                pass
                
            try:
                reset_requested = bool(user_data['reset_requested'])
            except (IndexError, KeyError):
                pass
                
            return User(
                id=user_data['id'],
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password_hash=user_data['password_hash'],
                is_admin=bool(user_data['is_admin']),
                password_reset_required=password_reset_required,
                reset_requested=reset_requested
            )
        return None
    
    @staticmethod
    def get_by_username(username):
        """Pobiera użytkownika na podstawie nazwy użytkownika"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        
        if user_data:
            # Bezpieczne pobieranie pól, które mogą nie istnieć w starszych wersjach bazy
            password_reset_required = False
            reset_requested = False
            
            try:
                password_reset_required = bool(user_data['password_reset_required'])
            except (IndexError, KeyError):
                pass
                
            try:
                reset_requested = bool(user_data['reset_requested'])
            except (IndexError, KeyError):
                pass
                
            return User(
                id=user_data['id'],
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password_hash=user_data['password_hash'],
                is_admin=bool(user_data['is_admin']),
                password_reset_required=password_reset_required,
                reset_requested=reset_requested
            )
        return None
    
    @staticmethod
    def get_all_users():
        """Pobiera wszystkich użytkowników"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users ORDER BY last_name, first_name")
        users_data = cursor.fetchall()
        
        users = []
        for user_data in users_data:
            # Bezpieczne pobieranie pól, które mogą nie istnieć w starszych wersjach bazy
            password_reset_required = False
            reset_requested = False
            
            try:
                password_reset_required = bool(user_data['password_reset_required'])
            except (IndexError, KeyError):
                pass
                
            try:
                reset_requested = bool(user_data['reset_requested'])
            except (IndexError, KeyError):
                pass
                
            users.append(User(
                id=user_data['id'],
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password_hash=user_data['password_hash'],
                is_admin=bool(user_data['is_admin']),
                password_reset_required=password_reset_required,
                reset_requested=reset_requested
            ))
        
        return users
    
    def save(self):
        """Zapisuje użytkownika do bazy danych"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        if self.id is None:
            # Nowy użytkownik
            cursor.execute('''
            INSERT INTO users (username, first_name, last_name, password_hash, is_admin, 
                              password_reset_required, reset_requested)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.username, self.first_name, self.last_name, self.password_hash, 
                self.is_admin, self.password_reset_required, self.reset_requested))
            self.id = cursor.lastrowid
        else:
            # Aktualizacja istniejącego użytkownika
            cursor.execute('''
            UPDATE users
            SET username = ?, first_name = ?, last_name = ?, password_hash = ?, 
                is_admin = ?, password_reset_required = ?, reset_requested = ?
            WHERE id = ?
            ''', (self.username, self.first_name, self.last_name, self.password_hash, 
                self.is_admin, self.password_reset_required, self.reset_requested, self.id))
        
        conn.commit()
        return self.id
    
    def delete(self):
        """Usuwa użytkownika z bazy danych"""
        if self.id is None:
            return False
            
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM users WHERE id = ?", (self.id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    @staticmethod
    def count():
        """Zwraca liczbę użytkowników w bazie"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        
        return result['count'] if result else 0
        
    @staticmethod
    def get_users_with_reset_requests():
        """Pobiera użytkowników, którzy poprosili o reset hasła"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        # Najpierw sprawdźmy, czy kolumna istnieje
        try:
            cursor.execute("SELECT * FROM users WHERE reset_requested = 1")
            users_data = cursor.fetchall()
            
            users = []
            for user_data in users_data:
                # Bezpieczne pobieranie pól, które mogą nie istnieć w starszych wersjach bazy
                password_reset_required = False
                reset_requested = False
                
                try:
                    password_reset_required = bool(user_data['password_reset_required'])
                except (IndexError, KeyError):
                    pass
                    
                try:
                    reset_requested = bool(user_data['reset_requested'])
                except (IndexError, KeyError):
                    pass
                    
                users.append(User(
                    id=user_data['id'],
                    username=user_data['username'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    password_hash=user_data['password_hash'],
                    is_admin=bool(user_data['is_admin']),
                    password_reset_required=password_reset_required,
                    reset_requested=reset_requested
                ))
            
            return users
        except:
            # Kolumna prawdopodobnie nie istnieje lub jest inny błąd
            return []


class Task:
    """Model zadania"""
    
    CATEGORIES = ["Produkcja", "Technologia", "Kontrola", "Marketing", "Zakupy", "Planowanie"]
    TYPES = ["Wdrożenie", "Oferta", "Zadania dodatkowe", "Rewizja", "Bieżące", "Spotkanie", "Zgłoszenia"]
    
    def __init__(self, user_id, category, task_type, description, start_time, end_time=None, duration=None, id=None, implementation_id=None, offer_id=None):
        self.id = id
        self.user_id = user_id
        self.category = category
        self.task_type = task_type
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.implementation_id = implementation_id
        self.offer_id = offer_id
    

    @staticmethod
    def create_tables():
        """Tworzy tabelę zadań w bazie danych"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            task_type TEXT NOT NULL,
            description TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration INTEGER,
            implementation_id INTEGER,
            offer_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (implementation_id) REFERENCES implementations (id) ON DELETE SET NULL,
            FOREIGN KEY (offer_id) REFERENCES offers (id) ON DELETE SET NULL
        )
        ''')
     
            
        conn.commit()
    
    @staticmethod
    def get_by_id(task_id):
        """Pobiera zadanie na podstawie ID"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task_data = cursor.fetchone()
        
        if task_data:
            return Task(
                id=task_data['id'],
                user_id=task_data['user_id'],
                category=task_data['category'],
                task_type=task_data['task_type'],
                description=task_data['description'],
                start_time=task_data['start_time'],
                end_time=task_data['end_time'],
                duration=task_data['duration'],
                implementation_id=task_data['implementation_id'],
                offer_id=task_data['offer_id']
            )
        return None
    
    @staticmethod
    def get_by_user_id(user_id):
        """Pobiera zadania dla konkretnego użytkownika"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY start_time DESC", (user_id,))
        tasks_data = cursor.fetchall()
        
        return [Task(
            id=task_data['id'],
            user_id=task_data['user_id'],
            category=task_data['category'],
            task_type=task_data['task_type'],
            description=task_data['description'],
            start_time=task_data['start_time'],
            end_time=task_data['end_time'],
            duration=task_data['duration'],
            implementation_id=task_data['implementation_id'],
            offer_id=task_data['offer_id']
        ) for task_data in tasks_data]
    
    @staticmethod
    def get_all_tasks():
        """Pobiera wszystkie zadania"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT t.*, u.username as username, u.first_name, u.last_name 
        FROM tasks t 
        JOIN users u ON t.user_id = u.id 
        ORDER BY t.start_time DESC
        ''')
        tasks_data = cursor.fetchall()
        
        result = []
        for task_data in tasks_data:
            task = Task(
                id=task_data['id'],
                user_id=task_data['user_id'],
                category=task_data['category'],
                task_type=task_data['task_type'],
                description=task_data['description'],
                start_time=task_data['start_time'],
                end_time=task_data['end_time'],
                duration=task_data['duration'],
                implementation_id=task_data['implementation_id'],
                offer_id=task_data['offer_id']
            )
            # Dodajemy informacje o użytkowniku
            task.username = task_data['username']
            task.user_full_name = f"{task_data['first_name']} {task_data['last_name']}"
            result.append(task)
            
        return result
    
    def save(self):
        """Zapisuje zadanie do bazy danych"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        if self.id is None:
            # Nowe zadanie
            cursor.execute('''
            INSERT INTO tasks (user_id, category, task_type, description, start_time, end_time, duration, implementation_id, offer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.user_id, self.category, self.task_type, self.description, self.start_time, 
                  self.end_time, self.duration, self.implementation_id, self.offer_id))
            self.id = cursor.lastrowid
        else:
            # Aktualizacja istniejącego zadania
            cursor.execute('''
            UPDATE tasks
            SET user_id = ?, category = ?, task_type = ?, description = ?, start_time = ?, end_time = ?, duration = ?, implementation_id = ?, offer_id = ?
            WHERE id = ?
            ''', (self.user_id, self.category, self.task_type, self.description, self.start_time, 
                  self.end_time, self.duration, self.implementation_id, self.offer_id, self.id))
        
        conn.commit()
        return self.id
    
    def delete(self):
        """Usuwa zadanie z bazy danych"""
        if self.id is None:
            return False
            
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tasks WHERE id = ?", (self.id,))
        conn.commit()
        
        return cursor.rowcount > 0


class Implementation:
    """Model wdrożenia"""
    
    OPERATIONS = ["Wdrożenie", "Spawanie", "Malowanie", "Klejenie"]
    STATUSES = ["W trakcie", "Zakończone"]
    
    def __init__(self, name, description, status="W trakcie", id=None):
        self.id = id
        self.name = name
        self.description = description
        self.status = status
        self.operations = {}  # Słownik operacji: nazwa_operacji -> {user_id, start_date, end_date}
    
    @staticmethod
    def create_tables():
        """Tworzy tabele wdrożeń i operacji w bazie danych"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS implementations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT "W trakcie"
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS implementation_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            implementation_id INTEGER NOT NULL,
            operation_name TEXT NOT NULL,
            user_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            FOREIGN KEY (implementation_id) REFERENCES implementations (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
        ''')
        
        conn.commit()
    
    @staticmethod
    def get_by_id(implementation_id):
        """Pobiera wdrożenie na podstawie ID"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM implementations WHERE id = ?", (implementation_id,))
        impl_data = cursor.fetchone()
        
        if not impl_data:
            return None
        
        implementation = Implementation(
            id=impl_data['id'],
            name=impl_data['name'],
            description=impl_data['description'],
            status=impl_data['status']
        )
        
        # Pobierz operacje wdrożenia
        cursor.execute('''
        SELECT * FROM implementation_operations 
        WHERE implementation_id = ?
        ''', (implementation_id,))
        
        operations_data = cursor.fetchall()
        
        for op_data in operations_data:
            implementation.operations[op_data['operation_name']] = {
                'user_id': op_data['user_id'],
                'start_date': op_data['start_date'],
                'end_date': op_data['end_date']
            }
        
        return implementation
    
    @staticmethod
    def get_all():
        """Pobiera wszystkie wdrożenia z operacjami"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM implementations 
        ORDER BY id DESC
        ''')
        
        implementations_data = cursor.fetchall()
        implementations = []
        
        for impl_data in implementations_data:
            implementation = Implementation(
                id=impl_data['id'],
                name=impl_data['name'],
                description=impl_data['description'],
                status=impl_data['status']
            )
            
            # Pobierz operacje wdrożenia
            cursor.execute('''
            SELECT * FROM implementation_operations 
            WHERE implementation_id = ?
            ''', (implementation.id,))
            
            operations_data = cursor.fetchall()
            
            for op_data in operations_data:
                implementation.operations[op_data['operation_name']] = {
                    'user_id': op_data['user_id'],
                    'start_date': op_data['start_date'],
                    'end_date': op_data['end_date']
                }
            
            implementations.append(implementation)
        
        return implementations
    
    @staticmethod
    def get_by_user_id(user_id):
        """Pobiera wdrożenia przypisane do konkretnego użytkownika"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT DISTINCT i.* 
        FROM implementations i
        JOIN implementation_operations io ON i.id = io.implementation_id
        WHERE io.user_id = ?
        ORDER BY i.id DESC
        ''', (user_id,))
        
        implementations_data = cursor.fetchall()
        implementations = []
        
        for impl_data in implementations_data:
            implementation = Implementation(
                id=impl_data['id'],
                name=impl_data['name'],
                description=impl_data['description'],
                status=impl_data['status']
            )
            
            # Pobierz operacje wdrożenia
            cursor.execute('''
            SELECT * FROM implementation_operations 
            WHERE implementation_id = ?
            ''', (implementation.id,))
            
            operations_data = cursor.fetchall()
            
            for op_data in operations_data:
                implementation.operations[op_data['operation_name']] = {
                    'user_id': op_data['user_id'],
                    'start_date': op_data['start_date'],
                    'end_date': op_data['end_date']
                }
            
            implementations.append(implementation)
        
        return implementations
    
    def save(self):
        """Zapisuje wdrożenie do bazy danych"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        if self.id is None:
            # Nowe wdrożenie
            cursor.execute('''
            INSERT INTO implementations (name, description, status)
            VALUES (?, ?, ?)
            ''', (self.name, self.description, self.status))
            self.id = cursor.lastrowid
            
            # Dodaj domyślne operacje
            for operation in self.OPERATIONS:
                cursor.execute('''
                INSERT INTO implementation_operations 
                (implementation_id, operation_name, user_id, start_date, end_date)
                VALUES (?, ?, NULL, NULL, NULL)
                ''', (self.id, operation))
        else:
            # Aktualizacja istniejącego wdrożenia
            cursor.execute('''
            UPDATE implementations
            SET name = ?, description = ?, status = ?
            WHERE id = ?
            ''', (self.name, self.description, self.status, self.id))
            
            # Aktualizuj operacje
            for operation_name, operation_data in self.operations.items():
                cursor.execute('''
                UPDATE implementation_operations
                SET user_id = ?, start_date = ?, end_date = ?
                WHERE implementation_id = ? AND operation_name = ?
                ''', (
                    operation_data.get('user_id'), 
                    operation_data.get('start_date'), 
                    operation_data.get('end_date'),
                    self.id, 
                    operation_name
                ))
        
        conn.commit()
        return self.id
    
    def delete(self):
        """Usuwa wdrożenie z bazy danych"""
        if self.id is None:
            return False
            
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        # Usuń najpierw operacje (choć kaskadowe usuwanie powinno działać)
        cursor.execute("DELETE FROM implementation_operations WHERE implementation_id = ?", (self.id,))
        
        # Usuń wdrożenie
        cursor.execute("DELETE FROM implementations WHERE id = ?", (self.id,))
        conn.commit()
        
        return cursor.rowcount > 0


class Offer:
    """Model oferty"""
    
    OPERATIONS = ["Wdrożenie", "Spawanie", "Malowanie", "Klejenie"]
    STATUSES = ["W trakcie", "Zakończone"]
    
    def __init__(self, name, description, status="W trakcie", id=None):
        self.id = id
        self.name = name
        self.description = description
        self.status = status
        self.operations = {}  # Słownik operacji: nazwa_operacji -> {user_id, start_date, end_date}
    
    @staticmethod
    def create_tables():
        """Tworzy tabele ofert i operacji w bazie danych"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT "W trakcie"
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS offer_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER NOT NULL,
            operation_name TEXT NOT NULL,
            user_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            FOREIGN KEY (offer_id) REFERENCES offers (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
        ''')
        
        conn.commit()
    
    @staticmethod
    def get_by_id(offer_id):
        """Pobiera ofertę na podstawie ID"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM offers WHERE id = ?", (offer_id,))
        offer_data = cursor.fetchone()
        
        if not offer_data:
            return None
        
        offer = Offer(
            id=offer_data['id'],
            name=offer_data['name'],
            description=offer_data['description'],
            status=offer_data['status']
        )
        
        # Pobierz operacje oferty
        cursor.execute('''
        SELECT * FROM offer_operations 
        WHERE offer_id = ?
        ''', (offer_id,))
        
        operations_data = cursor.fetchall()
        
        for op_data in operations_data:
            offer.operations[op_data['operation_name']] = {
                'user_id': op_data['user_id'],
                'start_date': op_data['start_date'],
                'end_date': op_data['end_date']
            }
        
        return offer
    
    @staticmethod
    def get_all():
        """Pobiera wszystkie oferty z operacjami"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM offers 
        ORDER BY id DESC
        ''')
        
        offers_data = cursor.fetchall()
        offers = []
        
        for offer_data in offers_data:
            offer = Offer(
                id=offer_data['id'],
                name=offer_data['name'],
                description=offer_data['description'],
                status=offer_data['status']
            )
            
            # Pobierz operacje oferty
            cursor.execute('''
            SELECT * FROM offer_operations 
            WHERE offer_id = ?
            ''', (offer.id,))
            
            operations_data = cursor.fetchall()
            
            for op_data in operations_data:
                offer.operations[op_data['operation_name']] = {
                    'user_id': op_data['user_id'],
                    'start_date': op_data['start_date'],
                    'end_date': op_data['end_date']
                }
            
            offers.append(offer)
        
        return offers
    
    @staticmethod
    def get_by_user_id(user_id):
        """Pobiera oferty przypisane do konkretnego użytkownika"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT DISTINCT o.* 
        FROM offers o
        JOIN offer_operations oo ON o.id = oo.offer_id
        WHERE oo.user_id = ?
        ORDER BY o.id DESC
        ''', (user_id,))
        
        offers_data = cursor.fetchall()
        offers = []
        
        for offer_data in offers_data:
            offer = Offer(
                id=offer_data['id'],
                name=offer_data['name'],
                description=offer_data['description'],
                status=offer_data['status']
            )
            
            # Pobierz operacje oferty
            cursor.execute('''
            SELECT * FROM offer_operations 
            WHERE offer_id = ?
            ''', (offer.id,))
            
            operations_data = cursor.fetchall()
            
            for op_data in operations_data:
                offer.operations[op_data['operation_name']] = {
                    'user_id': op_data['user_id'],
                    'start_date': op_data['start_date'],
                    'end_date': op_data['end_date']
                }
            
            offers.append(offer)
        
        return offers
    
    def save(self):
        """Zapisuje ofertę do bazy danych"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        if self.id is None:
            # Nowa oferta
            cursor.execute('''
            INSERT INTO offers (name, description, status)
            VALUES (?, ?, ?)
            ''', (self.name, self.description, self.status))
            self.id = cursor.lastrowid
            
            # Dodaj domyślne operacje
            for operation in self.OPERATIONS:
                cursor.execute('''
                INSERT INTO offer_operations 
                (offer_id, operation_name, user_id, start_date, end_date)
                VALUES (?, ?, NULL, NULL, NULL)
                ''', (self.id, operation))
        else:
            # Aktualizacja istniejącej oferty
            cursor.execute('''
            UPDATE offers
            SET name = ?, description = ?, status = ?
            WHERE id = ?
            ''', (self.name, self.description, self.status, self.id))
            
            # Aktualizuj operacje
            for operation_name, operation_data in self.operations.items():
                cursor.execute('''
                UPDATE offer_operations
                SET user_id = ?, start_date = ?, end_date = ?
                WHERE offer_id = ? AND operation_name = ?
                ''', (
                    operation_data.get('user_id'), 
                    operation_data.get('start_date'), 
                    operation_data.get('end_date'),
                    self.id, 
                    operation_name
                ))
        
        conn.commit()
        return self.id
    
    def delete(self):
        """Usuwa ofertę z bazy danych"""
        if self.id is None:
            return False
            
        conn = DBManager().get_connection() 
        cursor = conn.cursor()
class Role:
    """Model roli użytkownika"""
    
    def __init__(self, name, description, permissions=None, id=None):
        self.id = id
        self.name = name
        self.description = description
        self.permissions = permissions or {}  # Słownik uprawnień: nazwa_uprawnienia -> True/False
    
    # Modyfikacja w database/models.py, klasa Role, metoda create_tables

    @staticmethod
    def create_tables():
        """Tworzy tabele ról w bazie danych"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        # Tabela ról
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
        ''')
        
        # Tabela uprawnień dla ról
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            permission_name TEXT NOT NULL,
            permission_value BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
            UNIQUE(role_id, permission_name)
        )
        ''')
        
        # Tabela przypisań ról do użytkowników
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
            UNIQUE(user_id, role_id)
        )
        ''')
        
        # Tabela konfiguracji ograniczeń równoległych zadań
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS workload_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            max_implementations INTEGER NOT NULL DEFAULT 1,
            max_offers INTEGER NOT NULL DEFAULT 2,
            max_total_projects INTEGER NOT NULL DEFAULT 2
        )
        ''')
        
        # Dodaj domyślne ograniczenia jeśli tabela jest pusta
        cursor.execute("SELECT COUNT(*) as count FROM workload_limits")
        count = cursor.fetchone()['count']
        
        if count == 0:
            cursor.execute('''
            INSERT INTO workload_limits (max_implementations, max_offers, max_total_projects)
            VALUES (1, 2, 2)
            ''')
        
        conn.commit()
        
        # Sprawdź, czy istnieją już jakieś role, jeśli nie, dodaj domyślne
        cursor.execute("SELECT COUNT(*) as count FROM roles")
        count = cursor.fetchone()['count']
        
        if count == 0:
            # Dodaj domyślne role
            admin_role = Role(name="Administrator", description="Pełne uprawnienia administracyjne")
            admin_role.permissions = {
                "admin_panel": True,
                "manage_users": True,
                "manage_roles": True,
                "manage_implementations": True,
                "manage_offers": True,
                "view_all_tasks": True,
                "export_data": True
            }
            admin_role.save()
            
            manager_role = Role(name="Kierownik", description="Zarządzanie projektami i podgląd danych")
            manager_role.permissions = {
                "admin_panel": False,
                "manage_users": False,
                "manage_roles": False,
                "manage_implementations": True,
                "manage_offers": True,
                "view_all_tasks": True,
                "export_data": True
            }
            manager_role.save()
            
            user_role = Role(name="Użytkownik", description="Podstawowe uprawnienia użytkownika")
            user_role.permissions = {
                "admin_panel": False,
                "manage_users": False,
                "manage_roles": False,
                "manage_implementations": False,
                "manage_offers": False,
                "view_all_tasks": False,
                "export_data": True
            }
            user_role.save()
            
            # Dodaj nowe role zadaniowe
            implementation_role = Role(name="Wdrożenia", description="Specjalista od wdrożeń")
            implementation_role.permissions = {
                "task_implementation": True
            }
            implementation_role.save()
            
            offer_role = Role(name="Oferty", description="Specjalista od ofert")
            offer_role.permissions = {
                "task_offer": True
            }
            offer_role.save()
            
            welding_role = Role(name="Spawanie", description="Specjalista od spawania")
            welding_role.permissions = {
                "task_welding": True
            }
            welding_role.save()
            
            gluing_role = Role(name="Klejenie", description="Specjalista od klejenia")
            gluing_role.permissions = {
                "task_gluing": True
            }
            gluing_role.save()
            
            painting_role = Role(name="Malowanie", description="Specjalista od malowania")
            painting_role.permissions = {
                "task_painting": True
            }
            painting_role.save()
            
            # Przypisz rolę administratora do wszystkich istniejących administratorów
            cursor.execute("SELECT id FROM users WHERE is_admin = 1")
            admin_users = cursor.fetchall()
            
            for user in admin_users:
                cursor.execute('''
                INSERT INTO user_roles (user_id, role_id)
                VALUES (?, ?)
                ''', (user['id'], admin_role.id))
            
            # Przypisz rolę użytkownika do wszystkich pozostałych
            cursor.execute("SELECT id FROM users WHERE is_admin = 0")
            regular_users = cursor.fetchall()
            
            for user in regular_users:
                cursor.execute('''
                INSERT INTO user_roles (user_id, role_id)
                VALUES (?, ?)
                ''', (user['id'], user_role.id))
            
            conn.commit()
    
    @staticmethod
    def get_by_id(role_id):
        """Pobiera rolę na podstawie ID"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM roles WHERE id = ?", (role_id,))
        role_data = cursor.fetchone()
        
        if not role_data:
            return None
        
        role = Role(
            id=role_data['id'],
            name=role_data['name'],
            description=role_data['description']
        )
        
        # Pobierz uprawnienia roli
        cursor.execute(
            "SELECT permission_name, permission_value FROM role_permissions WHERE role_id = ?", 
            (role_id,)
        )
        permissions_data = cursor.fetchall()
        
        role.permissions = {
            p['permission_name']: bool(p['permission_value']) for p in permissions_data
        }
        
        return role
    
    @staticmethod
    def get_by_name(name):
        """Pobiera rolę na podstawie nazwy"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM roles WHERE name = ?", (name,))
        role_data = cursor.fetchone()
        
        if not role_data:
            return None
        
        return Role.get_by_id(role_data['id'])
    
    @staticmethod
    def get_all_roles():
        """Pobiera wszystkie role"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM roles ORDER BY name")
        roles_data = cursor.fetchall()
        
        roles = []
        for role_data in roles_data:
            role = Role.get_by_id(role_data['id'])
            roles.append(role)
        
        return roles
    
    @staticmethod
    def get_user_roles(user_id):
        """Pobiera role przypisane do użytkownika"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT r.* FROM roles r
        JOIN user_roles ur ON r.id = ur.role_id
        WHERE ur.user_id = ?
        ORDER BY r.name
        ''', (user_id,))
        
        roles_data = cursor.fetchall()
        
        roles = []
        for role_data in roles_data:
            role = Role.get_by_id(role_data['id'])
            roles.append(role)
        
        return roles
    
    @staticmethod
    def set_user_roles(user_id, role_ids):
        """Ustawia role dla użytkownika"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        # Usuń obecne role użytkownika
        cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
        
        # Dodaj nowe role
        for role_id in role_ids:
            cursor.execute('''
            INSERT INTO user_roles (user_id, role_id)
            VALUES (?, ?)
            ''', (user_id, role_id))
        
        conn.commit()
        return True
    
    @staticmethod
    def check_user_permission(user_id, permission_name):
        """Sprawdza czy użytkownik ma dane uprawnienie"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        # Sprawdź, czy użytkownik jest adminem (mają wszystkie uprawnienia)
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if user_data and user_data['is_admin']:
            return True
        
        # Sprawdź uprawnienie w rolach użytkownika
        cursor.execute('''
        SELECT MAX(rp.permission_value) as has_permission
        FROM role_permissions rp
        JOIN user_roles ur ON rp.role_id = ur.role_id
        WHERE ur.user_id = ? AND rp.permission_name = ?
        ''', (user_id, permission_name))
        
        result = cursor.fetchone()
        
        return bool(result['has_permission']) if result and result['has_permission'] is not None else False
    
    def save(self):
        """Zapisuje rolę do bazy danych"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        if self.id is None:
            # Nowa rola
            cursor.execute('''
            INSERT INTO roles (name, description)
            VALUES (?, ?)
            ''', (self.name, self.description))
            
            self.id = cursor.lastrowid
        else:
            # Aktualizacja istniejącej roli
            cursor.execute('''
            UPDATE roles
            SET name = ?, description = ?
            WHERE id = ?
            ''', (self.name, self.description, self.id))
            
            # Usuń stare uprawnienia
            cursor.execute("DELETE FROM role_permissions WHERE role_id = ?", (self.id,))
        
        # Dodaj uprawnienia
        for permission_name, permission_value in self.permissions.items():
            cursor.execute('''
            INSERT INTO role_permissions (role_id, permission_name, permission_value)
            VALUES (?, ?, ?)
            ''', (self.id, permission_name, permission_value))
        
        conn.commit()
        return self.id
    
    def delete(self):
        """Usuwa rolę z bazy danych"""
        if self.id is None:
            return False
            
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        # Usuń rolę (kaskadowo usunie uprawnienia i przypisania)
        cursor.execute("DELETE FROM roles WHERE id = ?", (self.id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    # Dodaj do klasy User rozszerzenia związane z rolami
    @staticmethod
    def _extend_user_class():
        """Rozszerza klasę User o metody związane z rolami"""
        # Te metody zostaną dodane do klasy User w czasie wykonania
        
        def get_roles(self):
            """Pobiera role użytkownika"""
            return Role.get_user_roles(self.id)
        
        def has_permission(self, permission_name):
            """Sprawdza czy użytkownik ma dane uprawnienie"""
            # Administratorzy mają wszystkie uprawnienia
            if self.is_admin:
                return True
            return Role.check_user_permission(self.id, permission_name)
        
        def set_roles(self, role_ids):
            """Ustawia role dla użytkownika"""
            return Role.set_user_roles(self.id, role_ids)
        
        # Dodaj metody do klasy User
        User.get_roles = get_roles
        User.has_permission = has_permission
        User.set_roles = set_roles

# Wywołaj rozszerzenie klasy User
Role._extend_user_class()

class WorkloadLimits:
    """Model limitów obciążenia pracą"""
    
    def __init__(self, max_implementations=1, max_offers=2, max_total_projects=2, id=None):
        self.id = id
        self.max_implementations = max_implementations
        self.max_offers = max_offers
        self.max_total_projects = max_total_projects
    
    @staticmethod
    def get_limits():
        """Pobiera aktualne limity obciążenia pracą"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM workload_limits LIMIT 1")
        limits_data = cursor.fetchone()
        
        if not limits_data:
            # Jeśli brak rekordów, dodaj domyślny
            limits = WorkloadLimits()
            limits.save()
            return limits
        
        return WorkloadLimits(
            id=limits_data['id'],
            max_implementations=limits_data['max_implementations'],
            max_offers=limits_data['max_offers'],
            max_total_projects=limits_data['max_total_projects']
        )
    
    def save(self):
        """Zapisuje limity obciążenia pracą"""
        conn = DBManager().get_connection()
        cursor = conn.cursor()
        
        if self.id is None:
            # Nowy rekord
            cursor.execute('''
            INSERT INTO workload_limits (max_implementations, max_offers, max_total_projects)
            VALUES (?, ?, ?)
            ''', (self.max_implementations, self.max_offers, self.max_total_projects))
            
            self.id = cursor.lastrowid
        else:
            # Aktualizacja istniejącego rekordu
            cursor.execute('''
            UPDATE workload_limits
            SET max_implementations = ?, max_offers = ?, max_total_projects = ?
            WHERE id = ?
            ''', (self.max_implementations, self.max_offers, self.max_total_projects, self.id))
        
        conn.commit()
        return self.id