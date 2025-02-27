import tkinter as tk
from tkinter import ttk, messagebox
from database.models import User
from utils.auth import AuthManager
from gui.registration import RegistrationWindow

class LoginWindow:
    """Klasa okna logowania"""
    
    def __init__(self, root, on_login_success=None):
        """
        Inicjalizuje okno logowania
        
        Args:
            root (tk.Tk): Główne okno aplikacji
            on_login_success (callable): Callback wywoływany po udanym logowaniu
        """
        self.root = root
        self.on_login_success = on_login_success
        self.auth_manager = AuthManager()
        
        # Konfiguracja głównego okna
        self.root.title("System śledzenia pracy - Logowanie")
        self.root.geometry("400x350")  # Zwiększona wysokość
        self.root.minsize(400, 350)
        self.root.configure(bg="#f0f0f0")
        
        # Centruj okno na ekranie
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 350) // 2
        self.root.geometry(f"400x350+{x}+{y}")
        
        # Ustawienie protokołu zamykania
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Tworzenie widgetów
        self._create_widgets()
        
        # Sprawdź czy musimy najpierw utworzyć konto administratora
        if User.count() == 0:
            messagebox.showinfo(
                "Pierwszy uruchomienie",
                "Witaj w aplikacji! Nie znaleziono żadnych użytkowników w bazie. "
                "Proszę najpierw utworzyć konto administratora."
            )
            self._show_registration(admin=True)
    
    def _create_widgets(self):
        """Tworzy widgety okna logowania"""
        # Ramka
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Tytuł
        ttk.Label(
            main_frame, 
            text="System śledzenia pracy",
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Formularz logowania
        ttk.Label(main_frame, text="Nazwa użytkownika:").pack(anchor="w", pady=(10, 2))
        self.username_entry = ttk.Entry(main_frame, width=30)
        self.username_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Hasło:").pack(anchor="w", pady=(5, 2))
        self.password_entry = ttk.Entry(main_frame, width=30, show="*")
        self.password_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Zaloguj się",
            command=self._login
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Zresetuj hasło",
            command=self._request_password_reset
        ).pack(side=tk.RIGHT, padx=5)
        
        # Powiąż Enter z logowaniem
        self.username_entry.bind("<Return>", lambda event: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda event: self._login())
    
    def _login(self):
        """Obsługuje logowanie użytkownika"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Błąd", "Wprowadź nazwę użytkownika i hasło.")
            return
        
        # Próba logowania
        result = self.auth_manager.login(username, password)
        
        if result == "reset_required":
            # Użytkownik musi zmienić hasło
            self._show_password_change_form()
        elif result:
            if self.on_login_success:
                self.on_login_success(result)
        else:
            messagebox.showerror("Błąd logowania", "Nieprawidłowa nazwa użytkownika lub hasło.")
    
    def _on_close(self):
        """Obsługuje zamykanie okna logowania"""
        # Zamknij wszystkie podrzędne okna
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()
        
        # Zamknij główne okno
        self.root.destroy()
        
        # Zakończ aplikację
        import sys
        sys.exit(0)
        
    def _request_password_reset(self):
        """Wysyła prośbę o reset hasła"""
        username = self.username_entry.get().strip()
        
        if not username:
            messagebox.showerror("Błąd", "Wprowadź nazwę użytkownika.")
            return
        
        # Próba wysłania prośby
        if self.auth_manager.request_password_reset(username):
            messagebox.showinfo(
                "Prośba wysłana", 
                "Prośba o reset hasła została wysłana do administratora. "
                "Po zresetowaniu hasła będziesz mógł się zalogować."
            )
        else:
            messagebox.showerror("Błąd", "Nie znaleziono użytkownika o podanej nazwie.")
    
    def _show_password_change_form(self):
        """Pokazuje formularz zmiany hasła"""
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self.root)
        dialog.title("Zmiana hasła")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Komunikat
        ttk.Label(
            main_frame, 
            text="Twoje hasło zostało zresetowane. Musisz ustawić nowe hasło.",
            wraplength=380
        ).pack(pady=(0, 10))
        
        # Formularz
        ttk.Label(main_frame, text="Nowe hasło:").pack(anchor="w", pady=(5, 2))
        new_password_entry = ttk.Entry(main_frame, width=30, show="*")
        new_password_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Powtórz nowe hasło:").pack(anchor="w", pady=(5, 2))
        confirm_password_entry = ttk.Entry(main_frame, width=30, show="*")
        confirm_password_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Przycisk
        ttk.Button(
            main_frame, 
            text="Zmień hasło",
            command=lambda: self._change_password(
                dialog,
                new_password_entry.get(),
                confirm_password_entry.get()
            )
        ).pack(pady=10)
        
        # Zabroń zamknięcia okna krzyżykiem
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def _change_password(self, dialog, new_password, confirm_password):
        """Obsługuje zmianę hasła"""
        # Sprawdź czy hasła są wprowadzone
        if not new_password or not confirm_password:
            messagebox.showerror("Błąd", "Wprowadź nowe hasło i jego potwierdzenie.")
            return
        
        # Sprawdź czy hasła są identyczne
        if new_password != confirm_password:
            messagebox.showerror("Błąd", "Hasła nie są identyczne.")
            return
        
        # Sprawdź minimalną długość hasła
        if len(new_password) < 6:
            messagebox.showerror("Błąd", "Hasło musi mieć co najmniej 6 znaków.")
            return
        
        # Zmień hasło
        if self.auth_manager.complete_password_reset(new_password):
            # Zamknij okno dialogowe
            dialog.destroy()
            
            # Zaloguj użytkownika
            if self.on_login_success:
                self.on_login_success(self.auth_manager.current_user)
        else:
            messagebox.showerror("Błąd", "Nie udało się zmienić hasła.")
    
    def _show_registration(self, admin=False):
        """Pokazuje okno rejestracji dla administratora (tylko przy pierwszym uruchomieniu)"""
        # Ukryj główne okno
        self.root.withdraw()
        
        # Pokaż okno rejestracji
        reg_window = tk.Toplevel(self.root)
        reg_app = RegistrationWindow(
            reg_window, 
            on_registration_success=self._on_registration_success,
            admin_registration=admin
        )
        
        # Zabroń zamknięcia okna krzyżykiem, jeśli jest to rejestracja administratora
        if admin:
            reg_window.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def _on_registration_success(self, user):
        """Callback wywoływany po udanej rejestracji"""
        # Pokaż główne okno
        self.root.deiconify()
        
        # Wypełnij pola logowania
        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(0, user.username)
        self.password_entry.delete(0, tk.END)
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Rejestracja udana", 
            f"Konto użytkownika {user.username} zostało utworzone."
        )