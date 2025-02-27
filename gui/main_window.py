import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from database.db_manager import DBManager
from utils.auth import AuthManager
from database.models import User, Task, Implementation, Offer
from gui.task_panel import TaskPanel
from gui.admin_panel import AdminPanel
from gui.implementation import ImplementationPanel
from gui.offers import OfferPanel
from gui.gantt import GanttPanel

class MainWindow:
    """Klasa głównego okna aplikacji"""
    
    def __init__(self, root, current_user):
        """
        Inicjalizuje główne okno aplikacji
        
        Args:
            root (tk.Tk): Główne okno
            current_user (User): Aktualnie zalogowany użytkownik
        """
        self.root = root
        self.current_user = current_user
        self.auth_manager = AuthManager()
        
        # Konfiguracja głównego okna
        self.root.title(f"System śledzenia pracy - {current_user.first_name} {current_user.last_name}")
        self.root.geometry("1400x900")  # Zwiększony rozmiar
        self.root.minsize(1200, 800)    # Zwiększony minimalny rozmiar
        
        # Centruj okno na ekranie
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1400) // 2
        y = (screen_height - 900) // 2
        self.root.geometry(f"1400x900+{x}+{y}")
        
        # Utwórz tabele jeśli nie istnieją
        self._create_tables()
        
        # Stwórz widgety
        self._create_widgets()
        
        # Obsługa zamykania
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_tables(self):
        """Tworzy tabele w bazie danych"""
        User.create_tables()
        Task.create_tables()
        Implementation.create_tables()
        Offer.create_tables()
    
    def _create_widgets(self):
        """Tworzy widgety głównego okna"""
        # Pasek menu
        menubar = tk.Menu(self.root)
        
        # Menu Plik
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Zmień ścieżkę bazy danych", command=self._change_db_path)
        file_menu.add_separator()
        file_menu.add_command(label="Wyloguj", command=self._logout)
        file_menu.add_command(label="Zamknij", command=self._on_close)
        
        menubar.add_cascade(label="Plik", menu=file_menu)
        
        # Ustawienie paska menu
        self.root.config(menu=menubar)
        
        # Główny układ
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel zakładek
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Zakładka zadań (dostępna dla wszystkich)
        self.task_panel = TaskPanel(
            self.notebook, 
            self.current_user, 
            is_admin=self.current_user.is_admin
        )
        self.notebook.add(self.task_panel, text="Zadania")
        
        # Zakładki dla administratora
        if self.current_user.is_admin:
            # Panel administratora
            self.admin_panel = AdminPanel(self.notebook, self.current_user)
            self.notebook.add(self.admin_panel, text="Panel Administratora")
            
            # Panel wdrożeń
            self.implementation_panel = ImplementationPanel(self.notebook, self.current_user)
            self.notebook.add(self.implementation_panel, text="Wdrożenia")
            
            # Panel ofert
            self.offer_panel = OfferPanel(self.notebook, self.current_user)
            self.notebook.add(self.offer_panel, text="Oferty")
        
        # Wykres Gantta (dla wszystkich)
        self.gantt_panel = GanttPanel(
            self.notebook, 
            self.current_user, 
            is_admin=self.current_user.is_admin
        )
        self.notebook.add(self.gantt_panel, text="Wykres Gantta")
        
        # Panel dolny z informacjami i przyciskiem wylogowania
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Informacje o użytkowniku
        user_label = ttk.Label(
            bottom_frame, 
            text=f"Zalogowany jako: {self.current_user.username} ({self.current_user.first_name} {self.current_user.last_name})"
        )
        user_label.pack(side=tk.LEFT)
        
        # Przycisk wylogowania
        logout_button = ttk.Button(
            bottom_frame, 
            text="Wyloguj",
            command=self._logout
        )
        logout_button.pack(side=tk.RIGHT)
    
    def _logout(self):
        """Wylogowuje użytkownika"""
        # Potwierdź wylogowanie
        if not messagebox.askyesno(
            "Potwierdzenie", 
            "Czy na pewno chcesz się wylogować?"
        ):
            return
        
        # Wyloguj użytkownika
        self.auth_manager.logout()
        
        # Zamknij główne okno
        self.root.destroy()
        
        # Uruchom ponownie logowanie
        from main import start_application
        start_application()
        
    def _on_close(self):
        """Obsługuje zamykanie okna aplikacji"""
        # Potwierdź wyjście
        if messagebox.askyesno("Zamykanie aplikacji", "Czy na pewno chcesz zamknąć aplikację?"):
            # Zamknij wszystkie otwarte okna
            for window in self.root.winfo_children():
                if isinstance(window, tk.Toplevel):
                    window.destroy()
                    
            # Zamknij główne okno
            self.root.destroy()
    
    def _change_db_path(self):
        """Zmienia ścieżkę do bazy danych"""
        # Pobierz nową ścieżkę
        file_path = filedialog.asksaveasfilename(
            title="Wybierz lokalizację bazy danych",
            filetypes=[("Baza danych SQLite", "*.db")],
            defaultextension=".db",
            initialfile="work_tracker.db"
        )
        
        if not file_path:
            return
        
        # Potwierdź zmianę
        if not messagebox.askyesno(
            "Potwierdzenie",
            "Zmiana lokalizacji bazy danych będzie wymagała ponownego uruchomienia aplikacji. Kontynuować?"
        ):
            return
        
        try:
            # Inicjalizuj DBManager jeśli nie istnieje
            db_manager = DBManager()
            
            # Aktualizuj ścieżkę
            db_manager.update_db_path(file_path)
            
            # Wyświetl komunikat
            messagebox.showinfo(
                "Sukces", 
                "Ścieżka do bazy danych została zmieniona. "
                "Zmiany zostaną wprowadzone po ponownym uruchomieniu aplikacji."
            )
        except Exception as e:
            messagebox.showerror(
                "Błąd", 
                f"Nie udało się zmienić ścieżki do bazy danych: {str(e)}"
            )