import tkinter as tk
from tkinter import ttk, messagebox
import re
import datetime
from tkcalendar import DateEntry
from database.models import Implementation, Offer, User

class ProjectFormWindow:
    """Ulepszone okno dla dodawania/edycji wdrożeń i ofert"""
    
    def __init__(self, parent, project=None, project_type="implementation", on_save=None):
        """
        Inicjalizuje okno formularza projektu
        
        Args:
            parent (tk.Widget): Widget rodzica
            project (Implementation|Offer): Projekt do edycji (None dla nowego)
            project_type (str): Typ projektu ("implementation" lub "offer")
            on_save (callable): Callback wywoływany po zapisie
        """
        self.parent = parent
        self.project = project
        self.project_type = project_type
        self.on_save = on_save
        
        # Określ odpowiednie typy i etykiety
        if project_type == "implementation":
            self.title_prefix = "Wdrożenie"
            self.project_class = Implementation
            self.operations = Implementation.OPERATIONS
        else:
            self.title_prefix = "Oferta"
            self.project_class = Offer
            self.operations = Offer.OPERATIONS
        
        # Utwórz okno dialogowe
        self.dialog = tk.Toplevel(parent)
        
        if project:
            self.dialog.title(f"Edycja {self.title_prefix.lower()}a: {project.name}")
        else:
            self.dialog.title(f"Dodaj {self.title_prefix.lower()}")
            
        # Bardzo duże okno, aby pomieścić wszystkie elementy
        self.dialog.geometry("900x700")
        self.dialog.minsize(900, 700)
        
        # Ustaw modalne okno
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Zmienne do przechowywania wartości pól formularza
        self.name_var = tk.StringVar(value=project.name if project else "")
        self.status_var = tk.StringVar(value=project.status if project else "W trakcie")
        
        # Zmienne dla operacji
        self.operation_enabled = {}
        self.operation_min_days = {}
        
        # Debugowanie - drukuj dane projektu przed utworzeniem widgetów
        if project:
            print(f"Ładowanie projektu: {project.name}")
            print(f"Operacje: {project.operations}")
        
        # Stwórz widgety i wypełnij dane
        self._create_widgets()
    
    def _create_widgets(self):
        """Tworzy widgety formularza"""
        # Całkowicie przebudowany układ - używamy prostego układu pack
        
        # Główny kontener
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar i canvas do przewijania
        main_canvas = tk.Canvas(main_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=main_canvas.yview)
        
        # Kontener na zawartość
        content_frame = ttk.Frame(main_canvas)
        
        # Konfiguracja scrollowania
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pakowanie elementów przewijania
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Utwórz okno w canvasie
        content_window = main_canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Dostosowanie szerokości zawartości do canvasa
        def _configure_canvas(event):
            canvas_width = event.width
            main_canvas.itemconfig(content_window, width=canvas_width)
        
        main_canvas.bind('<Configure>', _configure_canvas)
        
        # Aktualizacja obszaru przewijania
        def _configure_content(event):
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        
        content_frame.bind('<Configure>', _configure_content)
        
        # Obsługa przewijania myszką
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Tytuł formularza
        title_label = ttk.Label(
            content_frame, 
            text=f"{'Edytuj' if self.project else 'Dodaj'} {self.title_prefix.lower()}",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Dane podstawowe
        basic_frame = ttk.LabelFrame(content_frame, text="Informacje podstawowe", padding=10)
        basic_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Nazwa - użyj układu grid w ramce basic_frame
        ttk.Label(basic_frame, text="Nazwa:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(basic_frame, width=50, textvariable=self.name_var)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Status
        ttk.Label(basic_frame, text="Status:").grid(row=1, column=0, sticky=tk.W, pady=5)
        status_combobox = ttk.Combobox(
            basic_frame,
            textvariable=self.status_var,
            values=self.project_class.STATUSES,
            state="readonly",
            width=20
        )
        status_combobox.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Daty z kalendarzem
        
        # Data rozpoczęcia
        ttk.Label(basic_frame, text="Data rozpoczęcia:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Pobierz istniejącą datę startu lub ustaw domyślną
        default_start = datetime.date.today()
        if self.project and "Wdrożenie" in self.project.operations:
            start_date_str = self.project.operations["Wdrożenie"].get("start_date")
            if start_date_str:
                try:
                    default_start = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass
        
        self.start_date_entry = DateEntry(
            basic_frame, 
            width=15,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            selectmode='day',
            year=default_start.year,
            month=default_start.month,
            day=default_start.day
        )
        self.start_date_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Data zakończenia
        ttk.Label(basic_frame, text="Data zakończenia:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        # Pobierz istniejącą datę końca lub ustaw domyślną (miesiąc po starcie)
        default_end = default_start + datetime.timedelta(days=30)
        if self.project and "Wdrożenie" in self.project.operations:
            end_date_str = self.project.operations["Wdrożenie"].get("end_date")
            if end_date_str:
                try:
                    default_end = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass
        
        self.end_date_entry = DateEntry(
            basic_frame, 
            width=15,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            selectmode='day',
            year=default_end.year,
            month=default_end.month,
            day=default_end.day
        )
        self.end_date_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Opis
        ttk.Label(basic_frame, text="Opis:").grid(row=4, column=0, sticky=tk.NW, pady=5)
        
        # Pole tekstowe opisu z przewijaniem
        self.description_text = tk.Text(basic_frame, width=50, height=5)
        self.description_text.grid(row=4, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        # Dodaj opis, jeśli istnieje
        if self.project and self.project.description:
            self.description_text.insert("1.0", self.project.description)
        
        # Skonfiguruj przewijanie dla opisu
        desc_scrollbar = ttk.Scrollbar(basic_frame, orient="vertical", command=self.description_text.yview)
        desc_scrollbar.grid(row=4, column=2, sticky=tk.NS, pady=5)
        self.description_text.configure(yscrollcommand=desc_scrollbar.set)
        
        # Konfiguracja operacji
        operations_frame = ttk.LabelFrame(content_frame, text="Operacje", padding=10)
        operations_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Tabela operacji
        operations_table = ttk.Frame(operations_frame)
        operations_table.pack(fill=tk.X, pady=5)
        
        # Nagłówki tabeli
        ttk.Label(operations_table, text="Operacja", width=20, font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(operations_table, text="Wymagana", width=15, font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(operations_table, text="Min. dni", width=10, font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Wypełnij tabelę operacjami
        for i, operation in enumerate(self.operations):
            # Dostosuj nazwę operacji dla ofert
            operation_label = operation
            if operation == "Wdrożenie" and self.project_type == "offer":
                operation_label = "Oferta"
            
            # Dodaj etykietę operacji
            ttk.Label(operations_table, text=operation_label, width=20).grid(row=i+1, column=0, padx=5, pady=5, sticky=tk.W)
            
            # Ustaw początkowe wartości
            is_required = True
            min_days = 1
            
            # Jeśli edytujemy projekt, pobierz zapisane wartości
            if self.project and operation in self.project.operations:
                op_data = self.project.operations[operation]
                is_required = op_data.get("required", True)
                min_days = op_data.get("min_days", 1)
                print(f"Operacja {operation}: required={is_required}, min_days={min_days}")
            
            # Dodaj checkbox "wymagana"
            enabled_var = tk.BooleanVar(value=is_required)
            self.operation_enabled[operation] = enabled_var
            
            ttk.Checkbutton(
                operations_table,
                variable=enabled_var
            ).grid(row=i+1, column=1, padx=5, pady=5, sticky=tk.W)
            
            # Dodaj spinbox "min dni"
            min_days_var = tk.StringVar(value=str(min_days))
            self.operation_min_days[operation] = min_days_var
            
            ttk.Spinbox(
                operations_table,
                from_=1,
                to=100,
                increment=1,
                textvariable=min_days_var,
                width=5
            ).grid(row=i+1, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Przyciski akcji
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=self._save_project,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=self.dialog.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
    
    def _save_project(self):
        """Zapisuje projekt i zamyka okno"""
        # Pobierz dane z formularza
        name = self.name_var.get().strip()
        status = self.status_var.get()
        description = self.description_text.get("1.0", "end-1c").strip()  # Pobieranie tekstu z widgetu Text
        
        # Pobierz daty z kontrolek kalendarza
        start_date = self.start_date_entry.get_date().strftime("%Y-%m-%d")
        end_date = self.end_date_entry.get_date().strftime("%Y-%m-%d")
        
        # Walidacja
        if not name:
            messagebox.showerror("Błąd", "Nazwa projektu nie może być pusta.")
            return
        
        # Sprawdź czy data rozpoczęcia jest wcześniejsza niż data zakończenia
        start_date_obj = self.start_date_entry.get_date()
        end_date_obj = self.end_date_entry.get_date()
        
        if start_date_obj > end_date_obj:
            messagebox.showerror("Błąd", "Data rozpoczęcia nie może być późniejsza niż data zakończenia.")
            return
        
        print(f"Zapisywanie projektu: {name}")
        print(f"Daty: {start_date} - {end_date}")
        
        # Utwórz nowy lub zaktualizuj istniejący projekt
        if not self.project:
            # Nowy projekt
            project = self.project_class(
                name=name,
                description=description,
                status=status
            )
            
            # Zapisz projekt, co utworzy domyślne operacje
            project.save()
            
            # Po utworzeniu nowego projektu, ustaw go jako aktualny projekt
            self.project = project
        else:
            # Edycja istniejącego projektu
            self.project.name = name
            self.project.description = description
            self.project.status = status
        
        # Aktualizuj dane operacji
        for operation_name in self.operations:
            # Pobierz ustawienia z formularza
            is_enabled = self.operation_enabled[operation_name].get()
            min_days = self.operation_min_days[operation_name].get()
            
            print(f"Zapisywanie operacji {operation_name}: required={is_enabled}, min_days={min_days}")
            
            # Zapewnij, że operacja jest zainicjalizowana
            if operation_name not in self.project.operations:
                self.project.operations[operation_name] = {}
                
            # Zachowaj istniejące dane użytkownika i daty
            op_data = self.project.operations[operation_name]
            user_id = op_data.get("user_id")
            op_start_date = op_data.get("start_date")
            op_end_date = op_data.get("end_date")
            
            # Zapisz dane o wymaganiu operacji
            self.project.operations[operation_name]["required"] = is_enabled
            
            # Zapisz minimalną liczbę dni
            try:
                min_days_int = int(min_days)
                if min_days_int < 1:
                    min_days_int = 1
            except ValueError:
                min_days_int = 1
                
            self.project.operations[operation_name]["min_days"] = min_days_int
            
            # Dla operacji Wdrożenie ustaw daty z formularza
            if operation_name == "Wdrożenie":
                self.project.operations[operation_name]["start_date"] = start_date
                self.project.operations[operation_name]["end_date"] = end_date
                self.project.operations[operation_name]["user_id"] = user_id
        
        # Zapisz projekt do bazy danych
        self.project.save()
        
        print(f"Projekt zapisany: {self.project.name}")
        print(f"Operacje po zapisie: {self.project.operations}")
        
        # Zamknij okno dialogowe
        self.dialog.destroy()
        
        # Wywołaj callback
        if self.on_save:
            self.on_save(self.project)