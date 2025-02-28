import tkinter as tk
from tkinter import ttk, messagebox
from database.models import WorkloadLimits

class WorkloadSettingsPanel(ttk.Frame):
    """Panel ustawień limitów obciążenia pracą"""
    
    def __init__(self, parent, current_user):
        """
        Inicjalizuje panel ustawień limitów obciążenia
        
        Args:
            parent (ttk.Frame): Ramka nadrzędna
            current_user (User): Aktualnie zalogowany użytkownik
        """
        super().__init__(parent, padding=10)
        self.parent = parent
        self.current_user = current_user
        
        # Stwórz widgety
        self._create_widgets()
        
        # Załaduj dane
        self._load_limits()
    
    def _create_widgets(self):
        """Tworzy widgety panelu ustawień limitów obciążenia"""
        # Główny układ
        main_frame = ttk.LabelFrame(self, text="Ustawienia limitów obciążenia pracą", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Opis
        ttk.Label(
            main_frame, 
            text="Poniższe ustawienia określają maksymalną liczbę jednoczesnych zadań,\n"
                "które mogą być przypisane do jednego pracownika podczas automatycznego przydziału.",
            justify=tk.CENTER
        ).pack(pady=(0, 20))
        
        # Formularz ustawień
        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Maksymalna liczba wdrożeń
        ttk.Label(settings_frame, text="Maksymalna liczba równoległych wdrożeń:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.max_implementations_var = tk.IntVar(value=1)
        ttk.Spinbox(
            settings_frame,
            from_=0,
            to=10,
            increment=1,
            textvariable=self.max_implementations_var,
            width=5
        ).grid(row=0, column=1, padx=10)
        
        # Maksymalna liczba ofert
        ttk.Label(settings_frame, text="Maksymalna liczba równoległych ofert:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.max_offers_var = tk.IntVar(value=2)
        ttk.Spinbox(
            settings_frame,
            from_=0,
            to=10,
            increment=1,
            textvariable=self.max_offers_var,
            width=5
        ).grid(row=1, column=1, padx=10)
        
        # Maksymalna liczba projektów łącznie
        ttk.Label(settings_frame, text="Maksymalna liczba projektów łącznie:").grid(row=2, column=0, sticky=tk.W, pady=10)
        self.max_total_projects_var = tk.IntVar(value=2)
        ttk.Spinbox(
            settings_frame,
            from_=1,
            to=10,
            increment=1,
            textvariable=self.max_total_projects_var,
            width=5
        ).grid(row=2, column=1, padx=10)
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz ustawienia",
            command=self._save_settings,
            width=20
        ).pack(side=tk.RIGHT)
    
    def _load_limits(self):
        """Ładuje aktualne limity obciążenia"""
        limits = WorkloadLimits.get_limits()
        
        self.max_implementations_var.set(limits.max_implementations)
        self.max_offers_var.set(limits.max_offers)
        self.max_total_projects_var.set(limits.max_total_projects)
    
    def _save_settings(self):
        """Zapisuje ustawienia limitów obciążenia"""
        try:
            max_implementations = int(self.max_implementations_var.get())
            max_offers = int(self.max_offers_var.get())
            max_total_projects = int(self.max_total_projects_var.get())
            
            # Walidacja
            if max_implementations < 0 or max_offers < 0 or max_total_projects < 1:
                messagebox.showerror("Błąd", "Wszystkie wartości muszą być nieujemne, a łączna liczba projektów musi być większa od 0.")
                return
            
            if max_implementations + max_offers > max_total_projects:
                if not messagebox.askyesno(
                    "Niezgodność limitów", 
                    "Suma maksymalnej liczby wdrożeń i ofert przekracza łączny limit projektów. "
                    "Łączny limit będzie ograniczeniem nadrzędnym. Kontynuować?"
                ):
                    return
            
            # Zapisz limity
            limits = WorkloadLimits.get_limits()
            limits.max_implementations = max_implementations
            limits.max_offers = max_offers
            limits.max_total_projects = max_total_projects
            limits.save()
            
            messagebox.showinfo("Sukces", "Ustawienia limitów obciążenia zostały zapisane.")
            
        except ValueError:
            messagebox.showerror("Błąd", "Wprowadź poprawne wartości liczbowe.")