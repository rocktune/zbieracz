import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import re
from database.models import Implementation, Offer, User, WorkloadLimits
from utils.export import export_implementations_to_excel, export_offers_to_excel
from gui.project_form import ProjectFormWindow

class ProjectsPanel(ttk.Frame):
    """Panel zarządzania projektami (wdrożenia i oferty)"""
    
    def __init__(self, parent, current_user):
        """
        Inicjalizuje panel zarządzania projektami
        
        Args:
            parent (ttk.Frame): Ramka nadrzędna
            current_user (User): Aktualnie zalogowany użytkownik (admin)
        """
        super().__init__(parent, padding=10)
        self.parent = parent
        self.current_user = current_user
        
        # Zmienne
        self.selected_project_id = None
        self.selected_project_type = None  # "implementation" lub "offer"
        self.status_filter_var = tk.StringVar(value="Wszystkie")
        self.project_type_filter_var = tk.StringVar(value="Wszystkie")
        self.sort_by_var = tk.StringVar(value="Termin rosnąco")
        
        # Stwórz widgety
        self._create_widgets()
        
        # Załaduj dane
        self._load_projects()
    
    def _create_widgets(self):
        """Tworzy widgety panelu zarządzania projektami"""
        # Główny układ
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, expand=False, pady=(0, 10))
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Górny panel z przyciskami
        buttons_frame = ttk.LabelFrame(top_frame, text="Zarządzanie projektami", padding=10)
        buttons_frame.pack(fill=tk.X, expand=True)
        
        # Przyciski - pionowo
        ttk.Button(
            buttons_frame, 
            text="Dodaj wdrożenie",
            command=lambda: self._add_project("implementation"),
            width=20
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Dodaj ofertę",
            command=lambda: self._add_project("offer"),
            width=20
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Edytuj projekt",
            command=self._edit_project,
            width=20
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Usuń projekt",
            command=self._delete_project,
            width=20
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Panel automatycznego przydzielania
        auto_frame = ttk.LabelFrame(top_frame, text="Automatyczne przydzielanie użytkowników", padding=10)
        auto_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            auto_frame, 
            text="Przydziel użytkowników automatycznie",
            command=self._auto_assign_users,
            width=30
        ).pack(pady=10)
        
        ttk.Label(
            auto_frame, 
            text="Automatyczne przydzielanie uwzględnia role użytkowników, ich obciążenie pracą\n"
                 "oraz skonfigurowane limity równoczesnych projektów.",
            justify=tk.CENTER,
            wraplength=500
        ).pack(pady=5)
        
        # Dolny panel (tabela projektów)
        projects_frame = ttk.LabelFrame(bottom_frame, text="Lista projektów", padding=10)
        projects_frame.pack(fill=tk.BOTH, expand=True)
        
        # Filtr i eksport
        filter_frame = ttk.Frame(projects_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Typ projektu
        ttk.Label(filter_frame, text="Typ projektu:").pack(side=tk.LEFT, padx=(0, 5))
        project_type_combobox = ttk.Combobox(
            filter_frame, 
            textvariable=self.project_type_filter_var,
            values=["Wszystkie", "Wdrożenie", "Oferta"],
            state="readonly",
            width=15
        )
        project_type_combobox.pack(side=tk.LEFT, padx=5)
        
        # Status
        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT, padx=(15, 5))
        status_combobox = ttk.Combobox(
            filter_frame, 
            textvariable=self.status_filter_var,
            values=["Wszystkie", "W trakcie", "Zakończone"],
            state="readonly",
            width=15
        )
        status_combobox.pack(side=tk.LEFT, padx=5)
        
        # Sortowanie
        ttk.Label(filter_frame, text="Sortuj po:").pack(side=tk.LEFT, padx=(15, 5))
        sort_combobox = ttk.Combobox(
            filter_frame, 
            textvariable=self.sort_by_var,
            values=["Termin rosnąco", "Termin malejąco", "Nazwa A-Z", "Nazwa Z-A"],
            state="readonly",
            width=15
        )
        sort_combobox.pack(side=tk.LEFT, padx=5)
        
        # Zmiana filtru
        project_type_combobox.bind("<<ComboboxSelected>>", self._on_filter_change)
        status_combobox.bind("<<ComboboxSelected>>", self._on_filter_change)
        sort_combobox.bind("<<ComboboxSelected>>", self._on_filter_change)
        
        # Przycisk eksportu
        ttk.Button(
            filter_frame, 
            text="Eksportuj do Excel",
            command=self._export_to_excel
        ).pack(side=tk.RIGHT, padx=5)
        
        # Tabela projektów
        table_frame = ttk.Frame(projects_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Kolumny tabeli
        columns = ["id", "type", "name", "status", "deadline", "operations"]
        
        self.projects_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Nagłówki
        self.projects_tree.heading("id", text="ID")
        self.projects_tree.heading("type", text="Typ")
        self.projects_tree.heading("name", text="Nazwa")
        self.projects_tree.heading("status", text="Status")
        self.projects_tree.heading("deadline", text="Termin")
        self.projects_tree.heading("operations", text="Operacje")
        
        # Szerokości kolumn
        self.projects_tree.column("id", width=50, minwidth=50)
        self.projects_tree.column("type", width=80, minwidth=80)
        self.projects_tree.column("name", width=200, minwidth=150)
        self.projects_tree.column("status", width=100, minwidth=80)
        self.projects_tree.column("deadline", width=100, minwidth=100)
        self.projects_tree.column("operations", width=400, minwidth=300)
        
        # Paski przewijania - tylko pionowy
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=y_scrollbar.set)
        
        self.projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Podwójne kliknięcie do przypisania użytkowników
        self.projects_tree.bind("<Double-1>", self._on_project_double_click)
        
        # Pojedyncze kliknięcie do wyboru
        self.projects_tree.bind("<<TreeviewSelect>>", self._on_project_select)
    
    def _load_projects(self):
        """Ładuje projekty do tabeli"""
        # Wyczyść istniejące projekty
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)
        
        # Pobierz projekty
        all_projects = []
        
        # Czy pokazywać wdrożenia
        if self.project_type_filter_var.get() in ["Wszystkie", "Wdrożenie"]:
            implementations = Implementation.get_all()
            
            # Filtrowanie po statusie
            if self.status_filter_var.get() != "Wszystkie":
                implementations = [impl for impl in implementations if impl.status == self.status_filter_var.get()]
            
            # Dodaj typ projektu do każdego wdrożenia
            for impl in implementations:
                impl.project_type = "Wdrożenie"
                all_projects.append(impl)
        
        # Czy pokazywać oferty
        if self.project_type_filter_var.get() in ["Wszystkie", "Oferta"]:
            offers = Offer.get_all()
            
            # Filtrowanie po statusie
            if self.status_filter_var.get() != "Wszystkie":
                offers = [offer for offer in offers if offer.status == self.status_filter_var.get()]
            
            # Dodaj typ projektu do każdej oferty
            for offer in offers:
                offer.project_type = "Oferta"
                all_projects.append(offer)
        
        # Sortowanie projektów
        sort_option = self.sort_by_var.get()
        if sort_option == "Termin rosnąco":
            all_projects.sort(key=self._get_project_deadline)
        elif sort_option == "Termin malejąco":
            all_projects.sort(key=self._get_project_deadline, reverse=True)
        elif sort_option == "Nazwa A-Z":
            all_projects.sort(key=lambda p: p.name)
        elif sort_option == "Nazwa Z-A":
            all_projects.sort(key=lambda p: p.name, reverse=True)
        
        # Dodaj projekty do tabeli
        for project in all_projects:
            # Pobierz termin (data zakończenia)
            deadline = self._get_project_deadline_str(project)
            
            # Przygotuj informacje o operacjach
            operations_text = self._format_operations(project)
            
            values = [
                project.id,
                project.project_type,
                project.name,
                project.status,
                deadline,
                operations_text
            ]
            
            item = self.projects_tree.insert("", "end", values=values)
            
            # Dodaj tagi dla rozróżnienia typów projektów
            if project.project_type == "Wdrożenie":
                self.projects_tree.item(item, tags=("implementation",))
            else:
                self.projects_tree.item(item, tags=("offer",))
        
        # Kolorowe tła dla wdrożeń i ofert
        self.projects_tree.tag_configure("implementation", background="#E8F5E9")  # Jasny zielony
        self.projects_tree.tag_configure("offer", background="#E3F2FD")  # Jasny niebieski
    
    def _get_project_deadline(self, project):
        """Zwraca datę zakończenia projektu do sortowania"""
        # Pobierz datę zakończenia z operacji "Wdrożenie"
        end_date = None
        if "Wdrożenie" in project.operations:
            end_date = project.operations["Wdrożenie"].get("end_date")
        
        # Jeśli nie ma daty zakończenia, zwróć "9999-99-99" (na końcu)
        if not end_date:
            return "9999-99-99"
        
        return end_date
    
    def _get_project_deadline_str(self, project):
        """Zwraca sformatowaną datę zakończenia projektu"""
        deadline = self._get_project_deadline(project)
        
        if deadline == "9999-99-99":
            return "Brak terminu"
        
        # Sformatuj datę jako DD.MM.YYYY
        try:
            date_obj = datetime.datetime.strptime(deadline, "%Y-%m-%d").date()
            return date_obj.strftime("%d.%m.%Y")
        except ValueError:
            return deadline
    
    def _format_operations(self, project):
        """Formatuje tekst operacji do wyświetlenia w tabeli"""
        operations_text = ""
        
        for operation_name in ["Wdrożenie", "Spawanie", "Malowanie", "Klejenie"]:
            op_data = project.operations.get(operation_name, {})
            
            # Jeśli operacja nie jest wymagana, pomijamy ją
            if not op_data.get("required", True):
                continue
            
            # Pobierz dane użytkownika
            user_id = op_data.get("user_id")
            user = User.get_by_id(user_id) if user_id else None
            user_name = f"{user.first_name} {user.last_name}" if user else "-"
            
            # Dostosuj etykietę dla operacji Wdrożenie w przypadku oferty
            display_name = operation_name
            if operation_name == "Wdrożenie" and project.project_type == "Oferta":
                display_name = "Oferta"
            
            # Dodaj do tekstu - tylko nazwa użytkownika
            if operations_text:
                operations_text += " | "
            
            operations_text += f"{display_name}: {user_name}"
        
        return operations_text
    
    def _on_project_select(self, event):
        """Obsługuje wybór projektu z tabeli"""
        selection = self.projects_tree.selection()
        if selection:
            item = selection[0]
            values = self.projects_tree.item(item, "values")
            tags = self.projects_tree.item(item, "tags")
            
            self.selected_project_id = int(values[0])
            
            # Określ typ wybranego projektu
            if "implementation" in tags:
                self.selected_project_type = "implementation"
            elif "offer" in tags:
                self.selected_project_type = "offer"
            else:
                self.selected_project_type = values[1].lower()  # "Wdrożenie" -> "wdrożenie", "Oferta" -> "oferta"
    
    def _on_project_double_click(self, event):
        """Obsługuje podwójne kliknięcie na projekt"""
        selection = self.projects_tree.selection()
        if not selection:
            return
        
        self._on_project_select(event)
        
        if self.selected_project_type == "implementation":
            # Pobierz wdrożenie z bazy
            implementation = Implementation.get_by_id(self.selected_project_id)
            
            if implementation:
                # Pokaż okno przypisania użytkowników
                self._show_assign_users_dialog(implementation, "implementation")
        else:
            # Pobierz ofertę z bazy
            offer = Offer.get_by_id(self.selected_project_id)
            
            if offer:
                # Pokaż okno przypisania użytkowników
                self._show_assign_users_dialog(offer, "offer")
    
    def _on_filter_change(self, event):
        """Obsługuje zmianę filtru"""
        self._load_projects()
        
    def _add_project(self, project_type):
        """
        Dodaje nowy projekt z użyciem ulepszonego okna formularza
        
        Args:
            project_type (str): Typ projektu ("implementation" lub "offer")
        """
        # Utwórz nowe okno formularza projektu
        ProjectFormWindow(
            self, 
            project=None,
            project_type=project_type,
            on_save=lambda project: self._on_project_saved()
        )

    def _edit_project(self):
        """Edytuje istniejący projekt z użyciem ulepszonego okna formularza"""
        if not self.selected_project_id or not self.selected_project_type:
            messagebox.showinfo("Informacja", "Wybierz projekt do edycji.")
            return
        
        # Pobierz projekt odpowiedniego typu
        project = None
        if self.selected_project_type == "implementation":
            project = Implementation.get_by_id(self.selected_project_id)
        else:
            project = Offer.get_by_id(self.selected_project_id)
        
        if not project:
            messagebox.showerror("Błąd", "Nie znaleziono projektu.")
            return
        
        # Utwórz okno formularza projektu do edycji
        ProjectFormWindow(
            self, 
            project=project,
            project_type=self.selected_project_type,
            on_save=lambda project: self._on_project_saved()
        )

    def _on_project_saved(self):
        """Obsługuje zdarzenie zapisania projektu"""
        # Odśwież listę projektów
        self._load_projects()

    def _delete_project(self):
        """Usuwa projekt"""
        if not self.selected_project_id or not self.selected_project_type:
            messagebox.showinfo("Informacja", "Wybierz projekt do usunięcia.")
            return
        
        # Pobierz projekt odpowiedniego typu
        project = None
        if self.selected_project_type == "implementation":
            project = Implementation.get_by_id(self.selected_project_id)
            project_type_name = "wdrożenie"
        else:
            project = Offer.get_by_id(self.selected_project_id)
            project_type_name = "ofertę"
        
        if not project:
            messagebox.showerror("Błąd", "Nie znaleziono projektu.")
            return
        
        # Potwierdź usunięcie
        if not messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć {project_type_name} '{project.name}'?"
        ):
            return
        
        # Usuń projekt
        if project.delete():
            # Odśwież listę projektów
            self._load_projects()
            
            # Wyczyść wybór
            self.selected_project_id = None
            self.selected_project_type = None
            
            # Wyświetl komunikat
            messagebox.showinfo(
                "Sukces", 
                f"{project_type_name.capitalize()} '{project.name}' została usunięta."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                f"Nie udało się usunąć {project_type_name}."
            )

    def _show_assign_users_dialog(self, project, project_type):
        """
        Pokazuje okno przypisania użytkowników do operacji
        
        Args:
            project (Implementation|Offer): Projekt
            project_type (str): Typ projektu ("implementation" lub "offer")
        """
        # Pobierz wszystkich użytkowników
        users = User.get_all_users()
        
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        project_type_name = "wdrożenia" if project_type == "implementation" else "oferty"
        dialog.title(f"Przypisanie użytkowników do {project_type_name}: {project.name}")
        dialog.geometry("800x700")  # Zwiększony rozmiar okna
        dialog.minsize(800, 700)    # Minimalny rozmiar okna
        dialog.transient(self)
        dialog.grab_set()
        
        # Główny kontener z przewijaniem
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas do przewijania
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Konfiguracja przewijania
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Ramka formularza
        form_frame = ttk.Frame(scrollable_frame, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nagłówek
        ttk.Label(
            form_frame, 
            text=f"Projekt: {project.name}",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Panel informacji podstawowych
        basic_frame = ttk.LabelFrame(form_frame, text="Informacje podstawowe", padding=10)
        basic_frame.pack(fill=tk.X, pady=10)
        
        # Status
        status_frame = ttk.Frame(basic_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Status projektu:").pack(side=tk.LEFT, padx=(0, 5))
        
        status_combobox = ttk.Combobox(
            status_frame,
            values=Implementation.STATUSES if project_type == "implementation" else Offer.STATUSES,
            state="readonly",
            width=15
        )
        status_combobox.set(project.status)
        status_combobox.pack(side=tk.LEFT)
        
        # Daty główne projektu
        dates_frame = ttk.Frame(basic_frame)
        dates_frame.pack(fill=tk.X, pady=5)
        
        # Pobierz daty z operacji "Wdrożenie" jeśli istnieją
        start_date = ""
        end_date = ""
        if "Wdrożenie" in project.operations:
            start_date = project.operations["Wdrożenie"].get("start_date", "")
            end_date = project.operations["Wdrożenie"].get("end_date", "")
        
        ttk.Label(dates_frame, text="Data rozpoczęcia (RRRR-MM-DD):").pack(side=tk.LEFT, padx=(0, 5))
        main_start_entry = ttk.Entry(dates_frame, width=15)
        if start_date:
            main_start_entry.insert(0, start_date)
        main_start_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(dates_frame, text="Data zakończenia (RRRR-MM-DD):").pack(side=tk.LEFT, padx=(0, 5))
        main_end_entry = ttk.Entry(dates_frame, width=15)
        if end_date:
            main_end_entry.insert(0, end_date)
        main_end_entry.pack(side=tk.LEFT)
        
        # Operacje
        operations_frame = ttk.LabelFrame(form_frame, text="Operacje", padding=10)
        operations_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Nagłówki
        headers_frame = ttk.Frame(operations_frame)
        headers_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(headers_frame, text="Operacja", width=15).grid(row=0, column=0, padx=5)
        ttk.Label(headers_frame, text="Użytkownik", width=30).grid(row=0, column=1, padx=5)
        ttk.Label(headers_frame, text="Od (RRRR-MM-DD)", width=15).grid(row=0, column=2, padx=5)
        ttk.Label(headers_frame, text="Do (RRRR-MM-DD)", width=15).grid(row=0, column=3, padx=5)
        ttk.Label(headers_frame, text="Wymagana", width=10).grid(row=0, column=4, padx=5)
        ttk.Label(headers_frame, text="Min. dni", width=10).grid(row=0, column=5, padx=5)
        
        # Słownik przechowujący UI dla operacji
        operation_ui = {}
        
        # Stwórz UI dla każdej operacji
        for i, operation_name in enumerate(["Wdrożenie", "Spawanie", "Malowanie", "Klejenie"]):
            op_frame = ttk.Frame(operations_frame)
            op_frame.pack(fill=tk.X, pady=5)
            
            # Dostosuj etykietę dla pierwszej operacji w zależności od typu projektu
            operation_label = operation_name
            if operation_name == "Wdrożenie" and project_type == "offer":
                operation_label = "Oferta"
            
            # Dane operacji
            op_data = project.operations.get(operation_name, {})
            user_id = op_data.get("user_id")
            op_start_date = op_data.get("start_date", "")
            op_end_date = op_data.get("end_date", "")
            
            # Domyślnie wszystkie operacje są wymagane
            is_required = op_data.get("required", True)
            min_days = op_data.get("min_days", 1)
            
            # Elementy UI
            ttk.Label(op_frame, text=operation_label, width=15).grid(row=0, column=0, pady=5, padx=5)
            
            # Combobox użytkowników z filtrowaniem po odpowiedniej roli
            user_var = tk.StringVar()
            user_combobox = ttk.Combobox(
                op_frame,
                textvariable=user_var,
                state="readonly",
                width=30
            )
            
            # Przygotuj listę użytkowników z odpowiednimi rolami
            filtered_users = []
            for user in users:
                user_roles = user.get_roles()
                has_required_role = False
                
                # Sprawdź czy użytkownik ma odpowiednią rolę dla operacji
                for role in user_roles:
                    # Wdrożenie - wymaga roli "Wdrożenia" dla głównej operacji wdrożenia
                    # lub roli "Oferty" dla głównej operacji oferty
                    if operation_name == "Wdrożenie":
                        if (project_type == "implementation" and role.permissions.get("task_implementation", False)) or \
                        (project_type == "offer" and role.permissions.get("task_offer", False)):
                            has_required_role = True
                            break
                    # Spawanie - wymaga roli "Spawanie"
                    elif operation_name == "Spawanie" and role.permissions.get("task_welding", False):
                        has_required_role = True
                        break
                    # Malowanie - wymaga roli "Malowanie"
                    elif operation_name == "Malowanie" and role.permissions.get("task_painting", False):
                        has_required_role = True
                        break
                    # Klejenie - wymaga roli "Klejenie"
                    elif operation_name == "Klejenie" and role.permissions.get("task_gluing", False):
                        has_required_role = True
                        break
                
                if has_required_role:
                    filtered_users.append(user)
            
            # Przygotuj listę użytkowników
            user_options = [""] + [f"{user.id}: {user.first_name} {user.last_name}" for user in filtered_users]
            user_combobox["values"] = user_options
            
            # Ustaw wybranego użytkownika
            if user_id:
                for option in user_options:
                    if option.startswith(f"{user_id}:"):
                        user_var.set(option)
                        break
            
            user_combobox.grid(row=0, column=1, pady=5, padx=5)
            
            # Daty - jako pola tekstowe
            start_entry = ttk.Entry(op_frame, width=15)
            if op_start_date:
                start_entry.insert(0, op_start_date)
            start_entry.grid(row=0, column=2, pady=5, padx=5)
            
            end_entry = ttk.Entry(op_frame, width=15)
            if op_end_date:
                end_entry.insert(0, op_end_date)
            end_entry.grid(row=0, column=3, pady=5, padx=5)
            
            # Checkbox czy operacja jest wymagana
            required_var = tk.BooleanVar(value=is_required)
            ttk.Checkbutton(
                op_frame, 
                variable=required_var
            ).grid(row=0, column=4, pady=5, padx=5)
            
            # Pole dla minimalnej liczby dni
            min_days_var = tk.StringVar(value=str(min_days))
            ttk.Spinbox(
                op_frame,
                from_=1,
                to=100,
                increment=1,
                textvariable=min_days_var,
                width=5
            ).grid(row=0, column=5, pady=5, padx=5)
            
            # Zapisz UI dla operacji
            operation_ui[operation_name] = {
                "user_var": user_var,
                "start_entry": start_entry,
                "end_entry": end_entry,
                "required_var": required_var,
                "min_days_var": min_days_var
            }
    
        # Przyciski
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        save_command = lambda: self._save_assigned_users(
            dialog,
            project,
            project_type,
            status_combobox.get(),
            main_start_entry.get().strip(),
            main_end_entry.get().strip(),
            operation_ui
        )
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=save_command
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _save_assigned_users(self, dialog, project, project_type, status, main_start, main_end, operation_ui):
        """
        Zapisuje przypisanie użytkowników do operacji
        
        Args:
            dialog (tk.Toplevel): Okno dialogowe
            project (Implementation|Offer): Projekt
            project_type (str): Typ projektu ("implementation" lub "offer")
            status (str): Nowy status projektu
            main_start (str): Główna data rozpoczęcia
            main_end (str): Główna data zakończenia
            operation_ui (dict): Słownik z UI dla operacji
        """
        # Sprawdź format głównych dat
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        
        if main_start and not date_pattern.match(main_start):
            messagebox.showerror("Błąd", "Nieprawidłowy format głównej daty rozpoczęcia. Użyj formatu RRRR-MM-DD.")
            return
            
        if main_end and not date_pattern.match(main_end):
            messagebox.showerror("Błąd", "Nieprawidłowy format głównej daty zakończenia. Użyj formatu RRRR-MM-DD.")
            return
        
        # Sprawdź czy główna data rozpoczęcia jest wcześniejsza niż data zakończenia
        if main_start and main_end and main_start > main_end:
            messagebox.showerror("Błąd", "Główna data rozpoczęcia nie może być późniejsza niż data zakończenia.")
            return
        
        # Aktualizuj status
        project.status = status
        
        # Aktualizuj operacje
        for operation_name, ui in operation_ui.items():
            user_option = ui["user_var"].get()
            user_id = None
            
            if user_option:
                try:
                    user_id = int(user_option.split(":")[0])
                except:
                    pass
            
            start_date = ui["start_entry"].get().strip()
            end_date = ui["end_entry"].get().strip()
            is_required = ui["required_var"].get()
            min_days = ui["min_days_var"].get()
            
            # Sprawdź format dat
            if start_date and not date_pattern.match(start_date):
                messagebox.showerror(
                    "Błąd", 
                    f"Dla operacji '{operation_name}' nieprawidłowy format daty rozpoczęcia. Użyj formatu RRRR-MM-DD."
                )
                return
                
            if end_date and not date_pattern.match(end_date):
                messagebox.showerror(
                    "Błąd", 
                    f"Dla operacji '{operation_name}' nieprawidłowy format daty zakończenia. Użyj formatu RRRR-MM-DD."
                )
                return

            # Sprawdź czy data rozpoczęcia jest wcześniejsza niż data zakończenia
            if start_date and end_date and start_date > end_date:
                messagebox.showerror(
                    "Błąd", 
                    f"Dla operacji '{operation_name}' data rozpoczęcia jest późniejsza niż data zakończenia."
                )
                return
                        
            # Sprawdź czy minimalna liczba dni jest liczbą
            try:
                min_days_int = int(min_days)
                if min_days_int < 1:
                    min_days_int = 1
            except ValueError:
                messagebox.showerror(
                    "Błąd", 
                    f"Dla operacji '{operation_name}' nieprawidłowa minimalna liczba dni. Podaj liczbę całkowitą >= 1."
                )
                return
            
            # Aktualizuj operację
            if operation_name not in project.operations:
                project.operations[operation_name] = {}
                
            # Użyj głównych dat dla operacji "Wdrożenie"
            if operation_name == "Wdrożenie":
                project.operations[operation_name] = {
                    "user_id": user_id,
                    "start_date": main_start,
                    "end_date": main_end,
                    "required": is_required,
                    "min_days": min_days_int
                }
            else:
                # Dla pozostałych operacji użyj dat z formularza
                project.operations[operation_name] = {
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "required": is_required,
                    "min_days": min_days_int
                }
        
        # Sprawdź czy operacje mieszczą się w zakresie głównego projektu
        if main_start and main_end:
            for operation_name, op_data in project.operations.items():
                if operation_name == "Wdrożenie":
                    continue
                
                op_start = op_data.get("start_date")
                op_end = op_data.get("end_date")
                
                if op_data.get("required", True) and op_start and op_end and (op_start < main_start or op_end > main_end):
                    messagebox.showerror(
                        "Błąd", 
                        f"Operacja '{operation_name}' wykracza poza zakres głównego projektu."
                    )
                    return
        
        # Zapisz projekt
        project.save()
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę projektów
        self._load_projects()
        
        # Wyświetl komunikat
        project_type_name = "wdrożenia" if project_type == "implementation" else "oferty"
        messagebox.showinfo(
            "Sukces", 
            f"Przypisania użytkowników do {project_type_name} '{project.name}' zostały zaktualizowane."
        )
        print(f"Zapisuję projekt: {project.name}")
        print(f"Status: {status}")
        for op_name, op_data in project.operations.items():
            print(f"Operacja: {op_name}")
            print(f"  required: {op_data.get('required')}")
            print(f"  min_days: {op_data.get('min_days')}")
            print(f"  user_id: {op_data.get('user_id')}")
            print(f"  start_date: {op_data.get('start_date')}")
            print(f"  end_date: {op_data.get('end_date')}")
            print()    
            
    def _auto_assign_users(self):
        """Automatycznie przydziela użytkowników do projektów z uwzględnieniem wymaganych operacji i minimalnej liczby dni"""
        # Pobierz wszystkich użytkowników
        users = User.get_all_users()
        
        if not users:
            messagebox.showinfo("Informacja", "Brak użytkowników do przypisania.")
            return
        
        # Pobierz wszystkie wdrożenia o statusie "W trakcie"
        implementations = [impl for impl in Implementation.get_all() if impl.status == "W trakcie"]
        
        # Pobierz wszystkie oferty o statusie "W trakcie"
        offers = [offer for offer in Offer.get_all() if offer.status == "W trakcie"]
        
        if not implementations and not offers:
            messagebox.showinfo("Informacja", "Brak projektów w trakcie do przypisania.")
            return
        
        # Potwierdź operację
        if not messagebox.askyesno(
            "Potwierdzenie",
            "Czy na pewno chcesz automatycznie przydzielić użytkowników do projektów? "
            "Istniejące przypisania zostaną nadpisane.\n\n"
            "Uwzględnione zostaną tylko zaznaczone jako wymagane operacje, "
            "a długość operacji wyniknie z ustawionej minimalnej liczby dni."
        ):
            return
        
        # Pobierz limity obciążenia
        workload_limits = WorkloadLimits.get_limits()
        
        # Inicjalizuj obciążenie użytkowników
        # słownik user_id -> słownik z licznikami wdrożeń, ofert i całkowitych projektów oraz datami zajętymi
        user_load = {}
        user_skills = {}
        
        for user in users:
            user_load[user.id] = {
                "implementations_count": 0,
                "offers_count": 0,
                "total_projects": 0,
                "dates": {}  # data -> liczba zadań
            }
            
            # Określ umiejętności użytkownika na podstawie ról
            user_roles = user.get_roles()
            user_skills[user.id] = {
                "can_implementation": False,
                "can_offer": False,
                "can_welding": False,
                "can_painting": False,
                "can_gluing": False
            }
            
            for role in user_roles:
                # Sprawdź uprawnienia roli
                if role.permissions.get("task_implementation", False):
                    user_skills[user.id]["can_implementation"] = True
                if role.permissions.get("task_offer", False):
                    user_skills[user.id]["can_offer"] = True
                if role.permissions.get("task_welding", False):
                    user_skills[user.id]["can_welding"] = True
                if role.permissions.get("task_painting", False):
                    user_skills[user.id]["can_painting"] = True
                if role.permissions.get("task_gluing", False):
                    user_skills[user.id]["can_gluing"] = True
        
        # Przygotuj dane o użytkownikach
        user_dict = {user.id: user for user in users}
        
        # Pobierz aktualne obciążenie z istniejących wdrożeń i ofert
        self._calculate_current_workload(implementations, offers, user_load)
        
        # Posortuj wdrożenia według daty rozpoczęcia
        implementations.sort(key=lambda impl: impl.operations.get("Wdrożenie", {}).get("start_date", "9999-99-99"))
        
        # Posortuj oferty według daty rozpoczęcia
        offers.sort(key=lambda offer: offer.operations.get("Wdrożenie", {}).get("start_date", "9999-99-99"))
        
        # Najpierw przydziel główne operacje wdrożeń
        for impl in implementations:
            # Pobierz zakres dat głównego wdrożenia
            main_op = impl.operations.get("Wdrożenie", {})
            main_start = main_op.get("start_date")
            main_end = main_op.get("end_date")
            
            # Sprawdź czy operacja Wdrożenie jest wymagana
            is_implementation_required = main_op.get("required", True)
            
            if not main_start or not main_end or not is_implementation_required:
                continue  # Pomijamy wdrożenia bez dat lub bez wymagania głównej operacji
            
            # Znajdź najlepszego użytkownika do głównej operacji wdrożenia
            best_user_id = self._find_best_user(
                "implementation", main_start, main_end, user_load, user_skills, workload_limits
            )
            
            if best_user_id:
                impl.operations["Wdrożenie"]["user_id"] = best_user_id
                self._update_user_workload(user_load, best_user_id, "implementation", main_start, main_end)
        
        # Następnie przydziel główne operacje ofert
        for offer in offers:
            # Pobierz zakres dat głównej oferty
            main_op = offer.operations.get("Wdrożenie", {})
            main_start = main_op.get("start_date")
            main_end = main_op.get("end_date")
            
            # Sprawdź czy operacja Wdrożenie jest wymagana
            is_implementation_required = main_op.get("required", True)
            
            if not main_start or not main_end or not is_implementation_required:
                continue  # Pomijamy oferty bez dat lub bez wymagania głównej operacji
            
            # Znajdź najlepszego użytkownika do głównej operacji oferty
            best_user_id = self._find_best_user(
                "offer", main_start, main_end, user_load, user_skills, workload_limits
            )
            
            if best_user_id:
                offer.operations["Wdrożenie"]["user_id"] = best_user_id
                self._update_user_workload(user_load, best_user_id, "offer", main_start, main_end)
        
        # Przydziel pozostałe operacje dla wdrożeń
        for impl in implementations:
            # Pobierz zakres dat głównego wdrożenia
            main_op = impl.operations.get("Wdrożenie", {})
            main_start = main_op.get("start_date")
            main_end = main_op.get("end_date")
            
            if not main_start or not main_end:
                continue  # Pomijamy wdrożenia bez dat
            
            # Przydziel użytkowników do pozostałych operacji
            for operation_name in ["Spawanie", "Malowanie", "Klejenie"]:
                # Sprawdź czy operacja jest wymagana
                op_data = impl.operations.get(operation_name, {})
                is_required = op_data.get("required", True)
                
                if not is_required:
                    # Jeśli operacja nie jest wymagana, wyczyść przypisanie użytkownika
                    op_data["user_id"] = None
                    op_data["start_date"] = None
                    op_data["end_date"] = None
                    continue
                
                # Określ typ umiejętności potrzebnej do operacji
                skill_type = ""
                if operation_name == "Spawanie":
                    skill_type = "welding"
                elif operation_name == "Malowanie":
                    skill_type = "painting"
                elif operation_name == "Klejenie":
                    skill_type = "gluing"
                
                # Pobierz minimalną liczbę dni dla operacji
                min_days = op_data.get("min_days", 1)
                
                # Wyznacz daty dla operacji
                # Start po głownym starcie, zakończenie przed głównym końcem
                # Uwzględnij minimalną liczbę dni
                
                # Zacznij od dat głównej operacji
                op_start = main_start
                
                # Oblicz datę końcową dodając minimalną liczbę dni
                try:
                    start_date_obj = datetime.datetime.strptime(op_start, "%Y-%m-%d").date()
                    end_date_obj = start_date_obj + datetime.timedelta(days=min_days-1)
                    op_end = end_date_obj.strftime("%Y-%m-%d")
                    
                    # Upewnij się, że data końcowa nie przekracza głównej daty końcowej
                    if op_end > main_end:
                        op_end = main_end
                except ValueError:
                    # Jeśli coś pójdzie nie tak z datami, użyj głównych dat
                    op_start = main_start
                    op_end = main_end
                
                # Przypisz użytkownika
                best_user_id = self._find_best_user(
                    skill_type, op_start, op_end, user_load, user_skills, workload_limits
                )
                
                if best_user_id:
                    impl.operations[operation_name]["user_id"] = best_user_id
                    impl.operations[operation_name]["start_date"] = op_start
                    impl.operations[operation_name]["end_date"] = op_end
                    # Operacje specjalistyczne nie zwiększają licznika projektów, tylko obciążenie dzienne
                    self._update_user_workload(user_load, best_user_id, "specialist", op_start, op_end)
        
        # Przydziel pozostałe operacje dla ofert
        for offer in offers:
            # Pobierz zakres dat głównej oferty
            main_op = offer.operations.get("Wdrożenie", {})
            main_start = main_op.get("start_date")
            main_end = main_op.get("end_date")
            
            if not main_start or not main_end:
                continue  # Pomijamy oferty bez dat
            
            # Przydziel użytkowników do pozostałych operacji
            for operation_name in ["Spawanie", "Malowanie", "Klejenie"]:
                # Sprawdź czy operacja jest wymagana
                op_data = offer.operations.get(operation_name, {})
                is_required = op_data.get("required", True)
                
                if not is_required:
                    # Jeśli operacja nie jest wymagana, wyczyść przypisanie użytkownika
                    op_data["user_id"] = None
                    op_data["start_date"] = None
                    op_data["end_date"] = None
                    continue
                
                # Określ typ umiejętności potrzebnej do operacji
                skill_type = ""
                if operation_name == "Spawanie":
                    skill_type = "welding"
                elif operation_name == "Malowanie":
                    skill_type = "painting"
                elif operation_name == "Klejenie":
                    skill_type = "gluing"
                
                # Pobierz minimalną liczbę dni dla operacji
                min_days = op_data.get("min_days", 1)
                
                # Wyznacz daty dla operacji
                # Start po głownym starcie, zakończenie przed głównym końcem
                # Uwzględnij minimalną liczbę dni
                
                # Zacznij od dat głównej operacji
                op_start = main_start
                
                # Oblicz datę końcową dodając minimalną liczbę dni
                try:
                    start_date_obj = datetime.datetime.strptime(op_start, "%Y-%m-%d").date()
                    end_date_obj = start_date_obj + datetime.timedelta(days=min_days-1)
                    op_end = end_date_obj.strftime("%Y-%m-%d")
                    
                    # Upewnij się, że data końcowa nie przekracza głównej daty końcowej
                    if op_end > main_end:
                        op_end = main_end
                except ValueError:
                    # Jeśli coś pójdzie nie tak z datami, użyj głównych dat
                    op_start = main_start
                    op_end = main_end
                
                # Przypisz użytkownika
                best_user_id = self._find_best_user(
                    skill_type, op_start, op_end, user_load, user_skills, workload_limits
                )
                
                if best_user_id:
                    offer.operations[operation_name]["user_id"] = best_user_id
                    offer.operations[operation_name]["start_date"] = op_start
                    offer.operations[operation_name]["end_date"] = op_end
                    # Operacje specjalistyczne nie zwiększają licznika projektów, tylko obciążenie dzienne
                    self._update_user_workload(user_load, best_user_id, "specialist", op_start, op_end)
        
        # Zapisz wszystkie wdrożenia
        for impl in implementations:
            impl.save()
        
        # Zapisz wszystkie oferty
        for offer in offers:
            offer.save()
        
        # Odśwież listę projektów
        self._load_projects()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            "Automatyczne przydzielanie użytkowników do projektów zostało zakończone.\n"
            "Przydzielono tylko wymagane operacje z uwzględnieniem minimalnej liczby dni."
        )
        
    def _calculate_current_workload(self, implementations, offers, user_load):
        """Oblicza aktualne obciążenie użytkowników na podstawie istniejących przypisań"""
        # Przetwarzaj wdrożenia
        for impl in implementations:
            for operation_name, op_data in impl.operations.items():
                user_id = op_data.get("user_id")
                start_date = op_data.get("start_date")
                end_date = op_data.get("end_date")
                
                if user_id and start_date and end_date:
                    if operation_name == "Wdrożenie":
                        # Zwiększ licznik wdrożeń i projektów
                        if user_id in user_load:
                            user_load[user_id]["implementations_count"] += 1
                            user_load[user_id]["total_projects"] += 1
                    
                    # Dodaj obciążenie dzienne
                    self._add_daily_workload(user_load, user_id, start_date, end_date)
        
        # Przetwarzaj oferty
        for offer in offers:
            for operation_name, op_data in offer.operations.items():
                user_id = op_data.get("user_id")
                start_date = op_data.get("start_date")
                end_date = op_data.get("end_date")
                
                if user_id and start_date and end_date:
                    if operation_name == "Wdrożenie":
                        # Zwiększ licznik ofert i projektów
                        if user_id in user_load:
                            user_load[user_id]["offers_count"] += 1
                            user_load[user_id]["total_projects"] += 1
                    
                    # Dodaj obciążenie dzienne
                    self._add_daily_workload(user_load, user_id, start_date, end_date)

    def _add_daily_workload(self, user_load, user_id, start_date, end_date):
        """Dodaje obciążenie dzienne dla użytkownika w podanym okresie"""
        if user_id not in user_load:
            return
        
        try:
            # Przygotuj daty do iteracji
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Dodaj obciążenie dla każdego dnia
            date_obj = start_date_obj
            while date_obj <= end_date_obj:
                date_str = date_obj.strftime("%Y-%m-%d")
                
                if date_str not in user_load[user_id]["dates"]:
                    user_load[user_id]["dates"][date_str] = 0
                
                user_load[user_id]["dates"][date_str] += 1
                date_obj += datetime.timedelta(days=1)
        except ValueError:
            # Ignoruj nieprawidłowe daty
            pass

    def _find_best_user(self, task_type, start_date, end_date, user_load, user_skills, workload_limits):
        """
        Znajduje najlepszego użytkownika do przypisania zadania
        
        Args:
            task_type (str): Typ zadania lub umiejętności ("implementation", "offer", "welding", itp.)
            start_date (str): Data rozpoczęcia w formacie YYYY-MM-DD
            end_date (str): Data zakończenia w formacie YYYY-MM-DD
            user_load (dict): Słownik z obciążeniem użytkowników
            user_skills (dict): Słownik z umiejętnościami użytkowników
            workload_limits (WorkloadLimits): Limity obciążenia
            
        Returns:
            int: ID najlepszego użytkownika lub None jeśli nie znaleziono
        """
        best_user_id = None
        best_load = float("inf")
        
        try:
            # Przygotuj daty do iteracji
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            # Jeśli daty są nieprawidłowe, zwróć None
            return None
        
        # Dla każdego użytkownika
        for user_id, load_data in user_load.items():
            # Sprawdź czy użytkownik ma odpowiednie umiejętności
            if task_type == "implementation" and not user_skills[user_id]["can_implementation"]:
                continue
            elif task_type == "offer" and not user_skills[user_id]["can_offer"]:
                continue
            elif task_type == "welding" and not user_skills[user_id]["can_welding"]:
                continue
            elif task_type == "painting" and not user_skills[user_id]["can_painting"]:
                continue
            elif task_type == "gluing" and not user_skills[user_id]["can_gluing"]:
                continue
            
            # Sprawdź limity projektów
            if task_type == "implementation":
                if load_data["implementations_count"] >= workload_limits.max_implementations:
                    continue
                if load_data["total_projects"] >= workload_limits.max_total_projects:
                    continue
            elif task_type == "offer":
                if load_data["offers_count"] >= workload_limits.max_offers:
                    continue
                if load_data["total_projects"] >= workload_limits.max_total_projects:
                    continue
            
            # Oblicz obciążenie użytkownika w okresie zadania
            user_period_load = 0
            date_obj = start_date_obj
            
            while date_obj <= end_date_obj:
                date_str = date_obj.strftime("%Y-%m-%d")
                daily_load = load_data["dates"].get(date_str, 0)
                
                # Jeśli użytkownik ma już więcej niż 2 zadania w danym dniu, unikaj przydzielania kolejnych
                if daily_load >= 2:
                    user_period_load += 100  # Duża kara za przekroczenie dziennego limitu
                else:
                    user_period_load += daily_load
                
                date_obj += datetime.timedelta(days=1)
            
            # Sprawdź czy lepszy niż dotychczasowy
            if user_period_load < best_load:
                best_load = user_period_load
                best_user_id = user_id
        
        return best_user_id

    def _update_user_workload(self, user_load, user_id, task_type, start_date, end_date):
        """
        Aktualizuje obciążenie użytkownika po przypisaniu zadania
        
        Args:
            user_load (dict): Słownik z obciążeniem użytkowników
            user_id (int): ID użytkownika
            task_type (str): Typ zadania ("implementation", "offer", "specialist")
            start_date (str): Data rozpoczęcia w formacie YYYY-MM-DD
            end_date (str): Data zakończenia w formacie YYYY-MM-DD
        """
        if user_id not in user_load:
            return
        
        # Aktualizuj liczniki projektów
        if task_type == "implementation":
            user_load[user_id]["implementations_count"] += 1
            user_load[user_id]["total_projects"] += 1
        elif task_type == "offer":
            user_load[user_id]["offers_count"] += 1
            user_load[user_id]["total_projects"] += 1
        
        # Dodaj obciążenie dzienne
        self._add_daily_workload(user_load, user_id, start_date, end_date)

    def _export_to_excel(self):
        """Eksportuje projekty do pliku Excel"""
        # Pobierz filtrowane projekty
        all_projects = []
        
        # Pobierz wdrożenia jeśli wybrane
        if self.project_type_filter_var.get() in ["Wszystkie", "Wdrożenie"]:
            implementations = Implementation.get_all()
            
            # Filtrowanie po statusie
            if self.status_filter_var.get() != "Wszystkie":
                implementations = [impl for impl in implementations if impl.status == self.status_filter_var.get()]
            
            all_projects.extend([(impl, "implementation") for impl in implementations])
        
        # Pobierz oferty jeśli wybrane
        if self.project_type_filter_var.get() in ["Wszystkie", "Oferta"]:
            offers = Offer.get_all()
            
            # Filtrowanie po statusie
            if self.status_filter_var.get() != "Wszystkie":
                offers = [offer for offer in offers if offer.status == self.status_filter_var.get()]
            
            all_projects.extend([(offer, "offer") for offer in offers])
        
        if not all_projects:
            messagebox.showinfo("Informacja", "Brak projektów do eksportu.")
            return
        # Wybierz plik docelowy
        file_path = filedialog.asksaveasfilename(
            title="Eksportuj projekty do Excel",
            filetypes=[("Pliki Excel", "*.xlsx")],
            defaultextension=".xlsx",
            initialfile=f"projekty_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        
        if not file_path:
            return
        
        # Podziel projekty na wdrożenia i oferty
        implementations = [p[0] for p in all_projects if p[1] == "implementation"]
        offers = [p[0] for p in all_projects if p[1] == "offer"]
        
        # Zapisz dwie zakładki: wdrożenia i oferty
        try:
            # Najpierw eksportuj wdrożenia
            if implementations:
                if not export_implementations_to_excel(implementations, file_path):
                    messagebox.showerror("Błąd", "Nie udało się wyeksportować wdrożeń.")
                    return
            
            # Następnie eksportuj oferty (do istniejącego pliku)
            if offers:
                if not export_offers_to_excel(offers, file_path, append=True):
                    messagebox.showerror("Błąd", "Nie udało się wyeksportować ofert.")
                    return
            
            messagebox.showinfo(
                "Sukces", 
                f"Projekty zostały wyeksportowane do pliku {file_path}."
            )
        except Exception as e:
            messagebox.showerror(
                "Błąd", 
                f"Wystąpił błąd podczas eksportu: {str(e)}"
            )