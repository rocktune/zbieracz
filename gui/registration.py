import tkinter as tk
from tkinter import ttk, messagebox
from utils.auth import AuthManager

class RegistrationWindow:
    """Klasa okna rejestracji"""
    
    def __init__(self, root, on_registration_success=None, admin_registration=False):
        """
        Inicjalizuje okno rejestracji
        
        Args:
            root (tk.Toplevel): Okno rejestracji
            on_registration_success (callable): Callback wywoływany po udanej rejestracji
            admin_registration (bool): Czy rejestracja administratora
        """
        self.root = root
        self.on_registration_success = on_registration_success
        self.admin_registration = admin_registration
        self.auth_manager = AuthManager()
        
        # Konfiguracja okna
        self.root.title("Rejestracja użytkownika")
        self.root.geometry("400x400")  # Zwiększona wysokość
        self.root.minsize(400, 400)
        self.root.configure(bg="#f0f0f0")
        
        # Centruj okno na ekranie
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 400) // 2
        self.root.geometry(f"400x400+{x}+{y}")
        
        # Tworzenie widgetów
        self._create_widgets()
    
    def _create_widgets(self):
        """Tworzy widgety okna rejestracji"""
        # Ramka
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Tytuł
        if self.admin_registration:
            title_text = "Utwórz konto administratora"
        else:
            title_text = "Utwórz nowe konto"
            
        ttk.Label(
            main_frame, 
            text=title_text,
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Formularz rejestracji
        ttk.Label(main_frame, text="Nazwa użytkownika:").pack(anchor="w", pady=(10, 2))
        self.username_entry = ttk.Entry(main_frame, width=30)
        self.username_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Imię:").pack(anchor="w", pady=(5, 2))
        self.first_name_entry = ttk.Entry(main_frame, width=30)
        self.first_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Nazwisko:").pack(anchor="w", pady=(5, 2))
        self.last_name_entry = ttk.Entry(main_frame, width=30)
        self.last_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Hasło:").pack(anchor="w", pady=(5, 2))
        self.password_entry = ttk.Entry(main_frame, width=30, show="*")
        self.password_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Powtórz hasło:").pack(anchor="w", pady=(5, 2))
        self.confirm_password_entry = ttk.Entry(main_frame, width=30, show="*")
        self.confirm_password_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Utwórz konto",
            command=self._register
        ).pack(side=tk.RIGHT, padx=5)
        
        if not self.admin_registration:
            ttk.Button(
                buttons_frame, 
                text="Anuluj",
                command=self._cancel
            ).pack(side=tk.RIGHT, padx=5)
    
    def _register(self):
        """Obsługuje rejestrację użytkownika"""
        username = self.username_entry.get().strip()
        first_name = self.first_name_entry.get().strip()
        last_name = self.last_name_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        # Sprawdź czy wszystkie pola są wypełnione
        if not (username and first_name and last_name and password and confirm_password):
            messagebox.showerror("Błąd", "Wszystkie pola muszą być wypełnione.")
            return
        
        # Sprawdź czy hasła są identyczne
        if password != confirm_password:
            messagebox.showerror("Błąd", "Hasła nie są identyczne.")
            return
        
        # Sprawdź minimalną długość hasła
        if len(password) < 6:
            messagebox.showerror("Błąd", "Hasło musi mieć co najmniej 6 znaków.")
            return
        
        # Próba rejestracji
        user = self.auth_manager.register_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_admin=self.admin_registration
        )
        
        if user:
            if self.on_registration_success:
                self.on_registration_success(user)
            self.root.destroy()
        else:
            messagebox.showerror(
                "Błąd rejestracji", 
                "Użytkownik o podanej nazwie już istnieje."
            )
    
    def _cancel(self):
        """Zamyka okno rejestracji"""
        self.root.destroy()