import re
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from tkcalendar import DateEntry
import datetime
from database.models import Implementation, Offer, User, WorkloadLimits
from utils.export import export_implementations_to_excel

class ImplementationPanel(ttk.Frame):
    """Panel wdrożeń (dla admina)"""
    
    def __init__(self, parent, current_user):
        """
        Inicjalizuje panel wdrożeń
        
        Args:
            parent (ttk.Frame): Ramka nadrzędna
            current_user (User): Aktualnie zalogowany użytkownik (admin)
        """
        super().__init__(parent, padding=10)
        self.parent = parent
        self.current_user = current_user
        
        # Zmienne
        self.selected_implementation_id = None
        self.status_filter_var = tk.StringVar(value="Wszystkie")
        
        # Stwórz widgety
        self._create_widgets()
        
        # Załaduj dane
        self._load_implementations()
    
    def _create_widgets(self):
        """Tworzy widgety panelu wdrożeń"""
        # Główny układ - zmiana na układ pionowy
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, expand=False, pady=(0, 10))
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Górny panel (formularz wdrożenia)
        form_frame = ttk.LabelFrame(top_frame, text="Nowe wdrożenie", padding=10)
        form_frame.pack(fill=tk.X, expand=True)
        
        # Lewa strona formularza
        form_left = ttk.Frame(form_frame)
        form_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Nazwa
        ttk.Label(form_left, text="Nazwa:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(form_left, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Opis
        ttk.Label(form_left, text="Opis:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.description_entry = ttk.Entry(form_left, width=30)
        self.description_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Prawa strona formularza
        form_right = ttk.Frame(form_frame)
        form_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Przyciski - teraz pionowo
        buttons_frame = ttk.Frame(form_right)
        buttons_frame.pack(fill=tk.Y, expand=True, anchor=tk.CENTER)
        
        ttk.Button(
            buttons_frame, 
            text="Dodaj wdrożenie",
            command=self._add_implementation
        ).pack(pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Edytuj wdrożenie",
            command=self._edit_implementation
        ).pack(pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Usuń wdrożenie",
            command=self._delete_implementation
        ).pack(pady=5)
        
        # Druga sekcja - automatyczne przydzielanie
        auto_frame = ttk.LabelFrame(top_frame, text="Automatyczne przydzielanie użytkowników", padding=10)
        auto_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            auto_frame, 
            text="Przydziel użytkowników automatycznie",
            command=self._auto_assign_users
        ).pack(pady=10)
        
        ttk.Label(
            auto_frame, 
            text="Automatyczne przydzielanie uwzględnia obciążenie pracy użytkowników\n"
                 "i zapewnia optymalne wykorzystanie zasobów.",
            justify=tk.CENTER,
            wraplength=300
        ).pack(pady=5)
        
        # Dolny panel (tabela wdrożeń) - na całą szerokość
        implementations_frame = ttk.LabelFrame(bottom_frame, text="Lista wdrożeń", padding=10)
        implementations_frame.pack(fill=tk.BOTH, expand=True)

        # Filtr i eksport
        filter_frame = ttk.Frame(implementations_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Filtruj po statusie:").pack(side=tk.LEFT, padx=(0, 5))

        status_combobox = ttk.Combobox(
            filter_frame, 
            textvariable=self.status_filter_var,
            values=["Wszystkie"] + Implementation.STATUSES,
            state="readonly",
            width=15
        )
        status_combobox.pack(side=tk.LEFT, padx=5)

        # Zmiana filtru
        status_combobox.bind("<<ComboboxSelected>>", self._on_filter_change)

        # Przycisk eksportu
        ttk.Button(
            filter_frame, 
            text="Eksportuj do Excel",
            command=self._export_to_excel
        ).pack(side=tk.RIGHT, padx=5)

        # Tabela wdrożeń z paskiem przewijania
        table_frame = ttk.Frame(implementations_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Tabela wdrożeń z osobnymi kolumnami dla operacji
        columns = ["id", "name", "status"]
        # Dodaj kolumny dla każdej operacji
        for operation in Implementation.OPERATIONS:
            columns.append(operation)

        self.implementations_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Nagłówki
        self.implementations_tree.heading("id", text="ID")
        self.implementations_tree.heading("name", text="Nazwa")
        self.implementations_tree.heading("status", text="Status")

        # Nagłówki operacji
        for operation in Implementation.OPERATIONS:
            self.implementations_tree.heading(operation, text=operation)

        # Szerokości kolumn
        self.implementations_tree.column("id", width=50, minwidth=50)
        self.implementations_tree.column("name", width=200, minwidth=150)
        self.implementations_tree.column("status", width=100, minwidth=100)

        # Szerokości kolumn operacji
        for operation in Implementation.OPERATIONS:
            self.implementations_tree.column(operation, width=150, minwidth=120)

        # Paski przewijania - tylko pionowy
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.implementations_tree.yview)
        self.implementations_tree.configure(yscrollcommand=y_scrollbar.set)

        self.implementations_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Podwójne kliknięcie do przypisania użytkowników
        self.implementations_tree.bind("<Double-1>", self._on_implementation_double_click)

        # Pojedyncze kliknięcie do wyboru
        self.implementations_tree.bind("<<TreeviewSelect>>", self._on_implementation_select)
    
    def _load_implementations(self):
        """Ładuje wdrożenia do tabeli"""
        # Wyczyść istniejące wdrożenia
        for item in self.implementations_tree.get_children():
            self.implementations_tree.delete(item)
        
        # Pobierz wdrożenia
        implementations = Implementation.get_all()
        
        # Filtrowanie po statusie
        if self.status_filter_var.get() != "Wszystkie":
            implementations = [impl for impl in implementations if impl.status == self.status_filter_var.get()]
        
        # Sortowanie po dacie końcowej operacji wdrożenia
        implementations.sort(key=self._sort_by_end_date)
        
        # Dodaj wdrożenia do tabeli
        for impl in implementations:
            # Przygotuj wartości dla podstawowych kolumn
            values = [
                impl.id,
                impl.name,
                impl.status
            ]
            
            # Dodaj informacje o użytkownikach dla każdej operacji
            for operation_name in Implementation.OPERATIONS:
                op_data = impl.operations.get(operation_name, {})
                user_id = op_data.get("user_id")
                user = User.get_by_id(user_id) if user_id else None
                user_name = f"{user.first_name} {user.last_name}" if user else "-"
                values.append(user_name)
            
            self.implementations_tree.insert("", "end", values=values)
    
    def _sort_by_end_date(self, impl):
        """Funkcja sortująca wdrożenia po planowanej dacie zakończenia"""
        if not impl.operations.get("Wdrożenie", {}).get("end_date"):
            return "9999-99-99"  # Wdrożenia bez daty na końcu
        
        return impl.operations.get("Wdrożenie", {}).get("end_date", "9999-99-99")
    
    def _format_operations(self, impl):
        """Formatuje tekst operacji do wyświetlenia w tabeli"""
        operations_text = ""
        
        for operation_name in Implementation.OPERATIONS:
            op_data = impl.operations.get(operation_name, {})
            
            # Pobierz dane użytkownika
            user_id = op_data.get("user_id")
            user = User.get_by_id(user_id) if user_id else None
            user_name = f"{user.first_name} {user.last_name}" if user else "-"
            
            # Dodaj do tekstu - tylko nazwa użytkownika
            if operations_text:
                operations_text += " | "
            
            operations_text += f"{operation_name}: {user_name}"
        
        return operations_text
    
    def _on_implementation_select(self, event):
        """Obsługuje wybór wdrożenia z tabeli"""
        selection = self.implementations_tree.selection()
        if selection:
            item = selection[0]
            values = self.implementations_tree.item(item, "values")
            self.selected_implementation_id = int(values[0])
    
    def _on_implementation_double_click(self, event):
        """Obsługuje podwójne kliknięcie na wdrożenie"""
        selection = self.implementations_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.implementations_tree.item(item, "values")
        
        # Pobierz ID wdrożenia
        implementation_id = int(values[0])
        
        # Pobierz wdrożenie z bazy
        implementation = Implementation.get_by_id(implementation_id)
        
        if implementation:
            # Pokaż okno przypisania użytkowników
            self._show_assign_users_dialog(implementation)
    
    def _on_filter_change(self, event):
        """Obsługuje zmianę filtru statusu"""
        self._load_implementations()
    

    def _add_implementation(self):
        """Dodaje nowe wdrożenie"""
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title("Dodaj wdrożenie")
        dialog.geometry("500x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formularz
        ttk.Label(main_frame, text="Nazwa:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(main_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(main_frame, text="Opis:").grid(row=1, column=0, sticky=tk.W, pady=5)
        description_entry = ttk.Entry(main_frame, width=30)
        description_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Status
        ttk.Label(main_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, pady=5)
        status_combobox = ttk.Combobox(
            main_frame,
            values=Implementation.STATUSES,
            state="readonly",
            width=20
        )
        status_combobox.set("W trakcie")  # Domyślna wartość
        status_combobox.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Planowana data rozpoczęcia
        ttk.Label(main_frame, text="Planowany start (RRRR-MM-DD):").grid(row=3, column=0, sticky=tk.W, pady=5)
        planned_start_entry = ttk.Entry(main_frame, width=15)
        planned_start_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Planowana data zakończenia
        ttk.Label(main_frame, text="Planowane zakończenie (RRRR-MM-DD):").grid(row=4, column=0, sticky=tk.W, pady=5)
        planned_end_entry = ttk.Entry(main_frame, width=15)
        planned_end_entry.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=15)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=lambda: self._save_new_implementation(
                dialog,
                name_entry.get().strip(),
                description_entry.get().strip(),
                status_combobox.get(),
                planned_start_entry.get().strip(),
                planned_end_entry.get().strip()
            )
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)


    def _edit_implementation(self):
        """Edytuje istniejące wdrożenie"""
        if not self.selected_implementation_id:
            messagebox.showinfo("Informacja", "Wybierz wdrożenie do edycji.")
            return
        
        # Pobierz wdrożenie
        implementation = Implementation.get_by_id(self.selected_implementation_id)
        
        if not implementation:
            messagebox.showerror("Błąd", "Nie znaleziono wdrożenia.")
            return
        
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title(f"Edycja wdrożenia: {implementation.name}")
        dialog.geometry("500x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formularz
        ttk.Label(main_frame, text="Nazwa:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(main_frame, width=30)
        name_entry.insert(0, implementation.name)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(main_frame, text="Opis:").grid(row=1, column=0, sticky=tk.W, pady=5)
        description_entry = ttk.Entry(main_frame, width=30)
        description_entry.insert(0, implementation.description or "")
        description_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Status
        ttk.Label(main_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, pady=5)
        status_combobox = ttk.Combobox(
            main_frame,
            values=Implementation.STATUSES,
            state="readonly",
            width=20
        )
        status_combobox.set(implementation.status)
        status_combobox.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Planowana data rozpoczęcia
        ttk.Label(main_frame, text="Planowany start (RRRR-MM-DD):").grid(row=3, column=0, sticky=tk.W, pady=5)
        planned_start_entry = ttk.Entry(main_frame, width=15)
        
        # Pobierz datę rozpoczęcia z operacji "Wdrożenie" jeśli istnieje
        if "Wdrożenie" in implementation.operations:
            start_date = implementation.operations["Wdrożenie"].get("start_date", "")
            if start_date:
                planned_start_entry.insert(0, start_date)
        
        planned_start_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Planowana data zakończenia
        ttk.Label(main_frame, text="Planowane zakończenie (RRRR-MM-DD):").grid(row=4, column=0, sticky=tk.W, pady=5)
        planned_end_entry = ttk.Entry(main_frame, width=15)
        
        # Pobierz datę zakończenia z operacji "Wdrożenie" jeśli istnieje
        if "Wdrożenie" in implementation.operations:
            end_date = implementation.operations["Wdrożenie"].get("end_date", "")
            if end_date:
                planned_end_entry.insert(0, end_date)
        
        planned_end_entry.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=15)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=lambda: self._save_edited_implementation(
                dialog,
                implementation,
                name_entry.get().strip(),
                description_entry.get().strip(),
                status_combobox.get(),
                planned_start_entry.get().strip(),
                planned_end_entry.get().strip()
            )
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
            
    def _save_new_implementation(self, dialog, name, description, status, planned_start, planned_end):
        """Zapisuje nowe wdrożenie"""
        # Sprawdź czy nazwa jest wprowadzona
        if not name:
            messagebox.showerror("Błąd", "Nazwa wdrożenia nie może być pusta.")
            return
        
        # Sprawdź format dat
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        
        if planned_start and not date_pattern.match(planned_start):
            messagebox.showerror("Błąd", "Nieprawidłowy format daty rozpoczęcia. Użyj formatu RRRR-MM-DD.")
            return
            
        if planned_end and not date_pattern.match(planned_end):
            messagebox.showerror("Błąd", "Nieprawidłowy format daty zakończenia. Użyj formatu RRRR-MM-DD.")
            return
        
        # Sprawdź czy data rozpoczęcia jest wcześniejsza niż data zakończenia
        if planned_start and planned_end and planned_start > planned_end:
            messagebox.showerror("Błąd", "Data rozpoczęcia nie może być późniejsza niż data zakończenia.")
            return
        
        # Utwórz nowe wdrożenie
        implementation = Implementation(
            name=name,
            description=description,
            status=status
        )
        
        # Zapisz wdrożenie (to utworzy domyślne operacje)
        implementation.save()
        
        # Aktualizuj daty w operacji "Wdrożenie"
        if "Wdrożenie" in implementation.operations:
            implementation.operations["Wdrożenie"]["start_date"] = planned_start
            implementation.operations["Wdrożenie"]["end_date"] = planned_end
            
            # Zapisz ponownie wdrożenie, aby zaktualizować daty operacji
            implementation.save()
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę wdrożeń
        self._load_implementations()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            f"Wdrożenie '{name}' zostało dodane."
        )

    def _save_edited_implementation(self, dialog, implementation, name, description, status, planned_start, planned_end):
        """Zapisuje edytowane wdrożenie"""
        # Sprawdź czy nazwa jest wprowadzona
        if not name:
            messagebox.showerror("Błąd", "Nazwa wdrożenia nie może być pusta.")
            return
        
        # Sprawdź format dat
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        
        if planned_start and not date_pattern.match(planned_start):
            messagebox.showerror("Błąd", "Nieprawidłowy format daty rozpoczęcia. Użyj formatu RRRR-MM-DD.")
            return
            
        if planned_end and not date_pattern.match(planned_end):
            messagebox.showerror("Błąd", "Nieprawidłowy format daty zakończenia. Użyj formatu RRRR-MM-DD.")
            return
        
        # Sprawdź czy data rozpoczęcia jest wcześniejsza niż data zakończenia
        if planned_start and planned_end and planned_start > planned_end:
            messagebox.showerror("Błąd", "Data rozpoczęcia nie może być późniejsza niż data zakończenia.")
            return
        
        # Aktualizuj wdrożenie
        implementation.name = name
        implementation.description = description
        implementation.status = status
        
        # Aktualizuj daty w operacji "Wdrożenie"
        if "Wdrożenie" not in implementation.operations:
            implementation.operations["Wdrożenie"] = {}
        
        # Zachowaj istniejące dane użytkownika dla operacji Wdrożenie
        user_id = implementation.operations["Wdrożenie"].get("user_id")
        
        # Ustaw daty
        implementation.operations["Wdrożenie"]["start_date"] = planned_start
        implementation.operations["Wdrożenie"]["end_date"] = planned_end
        implementation.operations["Wdrożenie"]["user_id"] = user_id
        
        # Zapisz wdrożenie
        implementation.save()
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę wdrożeń
        self._load_implementations()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            f"Wdrożenie '{name}' zostało zaktualizowane."
        )
    
    def _delete_implementation(self):
        """Usuwa wdrożenie"""
        if not self.selected_implementation_id:
            messagebox.showinfo("Informacja", "Wybierz wdrożenie do usunięcia.")
            return
        
        # Pobierz wdrożenie
        implementation = Implementation.get_by_id(self.selected_implementation_id)
        
        if not implementation:
            messagebox.showerror("Błąd", "Nie znaleziono wdrożenia.")
            return
        
        # Potwierdź usunięcie
        if not messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć wdrożenie '{implementation.name}'?"
        ):
            return
        
        # Usuń wdrożenie
        if implementation.delete():
            # Odśwież listę wdrożeń
            self._load_implementations()
            
            # Wyczyść wybór
            self.selected_implementation_id = None
            
            # Wyświetl komunikat
            messagebox.showinfo(
                "Sukces", 
                f"Wdrożenie '{implementation.name}' zostało usunięte."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                "Nie udało się usunąć wdrożenia."
            )
    
    def _show_assign_users_dialog(self, implementation):
        """Pokazuje okno przypisania użytkowników do operacji"""
        # Pobierz wszystkich użytkowników
        users = User.get_all_users()
        
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title(f"Przypisanie użytkowników do wdrożenia: {implementation.name}")
        dialog.geometry("800x600")  # Zwiększony rozmiar okna
        dialog.minsize(800, 600)    # Minimalny rozmiar okna
        dialog.transient(self)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nagłówek
        ttk.Label(
            main_frame, 
            text=f"Wdrożenie: {implementation.name}",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Status wdrożenia:").pack(side=tk.LEFT, padx=(0, 5))
        
        status_combobox = ttk.Combobox(
            status_frame,
            values=Implementation.STATUSES,
            state="readonly",
            width=15
        )
        status_combobox.set(implementation.status)
        status_combobox.pack(side=tk.LEFT)
        
        # Operacje
        operations_frame = ttk.LabelFrame(main_frame, text="Operacje", padding=10)
        operations_frame.pack(fill=tk.BOTH, expand=True)
        
        # Słownik przechowujący UI dla operacji
        operation_ui = {}
        
        # Stwórz UI dla każdej operacji
        for i, operation_name in enumerate(Implementation.OPERATIONS):
            op_frame = ttk.Frame(operations_frame)
            op_frame.pack(fill=tk.X, pady=5)
            
            # Dane operacji
            op_data = implementation.operations.get(operation_name, {})
            user_id = op_data.get("user_id")
            start_date = op_data.get("start_date", "")
            end_date = op_data.get("end_date", "")
            
            # Elementy UI
            ttk.Label(op_frame, text=f"{operation_name}:", width=15).grid(row=0, column=0, pady=5, padx=5)
            
            # Combobox użytkowników
            user_var = tk.StringVar()
            user_combobox = ttk.Combobox(
                op_frame,
                textvariable=user_var,
                state="readonly",
                width=30
            )
            
            # Przygotuj listę użytkowników
            user_options = [""] + [f"{user.id}: {user.first_name} {user.last_name}" for user in users]
            user_combobox["values"] = user_options
            
            # Ustaw wybranego użytkownika
            if user_id:
                for option in user_options:
                    if option.startswith(f"{user_id}:"):
                        user_var.set(option)
                        break
            
            user_combobox.grid(row=0, column=1, pady=5, padx=5)
            
            # Daty - jako proste pola tekstowe zamiast DateEntry
            ttk.Label(op_frame, text="Od (RRRR-MM-DD):").grid(row=0, column=2, pady=5, padx=5)
            start_entry = ttk.Entry(op_frame, width=12)
            if start_date:
                start_entry.insert(0, start_date)
            start_entry.grid(row=0, column=3, pady=5, padx=5)
            
            ttk.Label(op_frame, text="Do (RRRR-MM-DD):").grid(row=0, column=4, pady=5, padx=5)
            end_entry = ttk.Entry(op_frame, width=12)
            if end_date:
                end_entry.insert(0, end_date)
            end_entry.grid(row=0, column=5, pady=5, padx=5)
            
            # Zapisz UI dla operacji
            operation_ui[operation_name] = {
                "user_var": user_var,
                "start_entry": start_entry,
                "end_entry": end_entry
            }
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=lambda: self._save_assigned_users(
                dialog,
                implementation,
                status_combobox.get(),
                operation_ui
            )
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _save_assigned_users(self, dialog, implementation, status, operation_ui):
        """Zapisuje przypisanie użytkowników do operacji"""
        # Aktualizuj status
        implementation.status = status
        
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
            
            # Sprawdź format daty
            date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
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
            
            # Sprawdź daty
            if start_date and end_date and start_date > end_date:
                messagebox.showerror(
                    "Błąd", 
                    f"Dla operacji '{operation_name}' data rozpoczęcia jest późniejsza niż data zakończenia."
                )
                return
            
            # Aktualizuj operację
            implementation.operations[operation_name] = {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date
            }
        
        # Sprawdź czy operacje mieszczą się w zakresie głównego wdrożenia
        main_start = implementation.operations.get("Wdrożenie", {}).get("start_date")
        main_end = implementation.operations.get("Wdrożenie", {}).get("end_date")
        
        if main_start and main_end:
            for operation_name, op_data in implementation.operations.items():
                if operation_name == "Wdrożenie":
                    continue
                
                op_start = op_data.get("start_date")
                op_end = op_data.get("end_date")
                
                if op_start and op_end and (op_start < main_start or op_end > main_end):
                    messagebox.showerror(
                        "Błąd", 
                        f"Operacja '{operation_name}' wykracza poza zakres głównego wdrożenia."
                    )
                    return
        
        # Zapisz wdrożenie
        implementation.save()
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę wdrożeń
        self._load_implementations()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            f"Przypisania użytkowników do wdrożenia '{implementation.name}' zostały zaktualizowane."
        )

    def _auto_assign_users(self):
        """Automatycznie przydziela użytkowników do wdrożeń"""
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
            "Czy na pewno chcesz automatycznie przydzielić użytkowników do wdrożeń i ofert? "
            "Istniejące przypisania zostaną nadpisane."
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
            
            if not main_start or not main_end:
                continue  # Pomijamy wdrożenia bez dat
            
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
            
            if not main_start or not main_end:
                continue  # Pomijamy oferty bez dat
            
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
                # Określ typ umiejętności potrzebnej do operacji
                skill_type = ""
                if operation_name == "Spawanie":
                    skill_type = "welding"
                elif operation_name == "Malowanie":
                    skill_type = "painting"
                elif operation_name == "Klejenie":
                    skill_type = "gluing"
                
                # Pobierz daty z operacji lub użyj głównych dat
                op_data = impl.operations.get(operation_name, {})
                op_start = op_data.get("start_date", main_start)
                op_end = op_data.get("end_date", main_end)
                
                # Upewnij się, że daty mieszczą się w zakresie głównego wdrożenia
                op_start = max(op_start, main_start)
                op_end = min(op_end, main_end)
                
                # Przypisz użytkownika
                best_user_id = self._find_best_user(
                    skill_type, op_start, op_end, user_load, user_skills, workload_limits
                )
                
                if best_user_id:
                    impl.operations[operation_name]["user_id"] = best_user_id
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
                # Określ typ umiejętności potrzebnej do operacji
                skill_type = ""
                if operation_name == "Spawanie":
                    skill_type = "welding"
                elif operation_name == "Malowanie":
                    skill_type = "painting"
                elif operation_name == "Klejenie":
                    skill_type = "gluing"
                
                # Pobierz daty z operacji lub użyj głównych dat
                op_data = offer.operations.get(operation_name, {})
                op_start = op_data.get("start_date", main_start)
                op_end = op_data.get("end_date", main_end)
                
                # Upewnij się, że daty mieszczą się w zakresie głównej oferty
                op_start = max(op_start, main_start)
                op_end = min(op_end, main_end)
                
                # Przypisz użytkownika
                best_user_id = self._find_best_user(
                    skill_type, op_start, op_end, user_load, user_skills, workload_limits
                )
                
                if best_user_id:
                    offer.operations[operation_name]["user_id"] = best_user_id
                    # Operacje specjalistyczne nie zwiększają licznika projektów, tylko obciążenie dzienne
                    self._update_user_workload(user_load, best_user_id, "specialist", op_start, op_end)
        
        # Zapisz wszystkie wdrożenia
        for impl in implementations:
            impl.save()
        
        # Zapisz wszystkie oferty
        for offer in offers:
            offer.save()
        
        # Odśwież listę wdrożeń
        self._load_implementations()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            "Automatyczne przydzielanie użytkowników do projektów zostało zakończone."
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
        
        def _assign_user_to_operation(self, implementation, operation_name, start_date, end_date, user_load, user_dict):
            """Przypisuje użytkownika do operacji na podstawie obciążenia"""
            # Przygotuj daty do iteracji
            current_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Znajdź użytkownika z najmniejszym obciążeniem w tym okresie
            best_user_id = None
            best_load = float("inf")
            
            for user_id in user_load:
                # Oblicz obciążenie użytkownika w okresie
                user_total_load = 0
                date_obj = current_date
                
                while date_obj <= end_date_obj:
                    date_str = date_obj.strftime("%Y-%m-%d")
                    user_total_load += user_load.get(user_id, {}).get(date_str, 0)
                    date_obj += datetime.timedelta(days=1)
                
                # Sprawdź czy lepszy niż dotychczasowy
                if user_total_load < best_load:
                    best_load = user_total_load
                    best_user_id = user_id
            
            # Przypisz użytkownika do operacji
            if best_user_id:
                implementation.operations[operation_name] = {
                    "user_id": best_user_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
                
                # Zaktualizuj obciążenie użytkownika
                date_obj = current_date
                while date_obj <= end_date_obj:
                    date_str = date_obj.strftime("%Y-%m-%d")
                    
                    if date_str not in user_load[best_user_id]:
                        user_load[best_user_id][date_str] = 0
                    
                    user_load[best_user_id][date_str] += 1
                    date_obj += datetime.timedelta(days=1)
    
    def _export_to_excel(self):
        """Eksportuje wdrożenia do pliku Excel"""
        # Pobierz filtrowane wdrożenia
        implementations = Implementation.get_all()
        
        if self.status_filter_var.get() != "Wszystkie":
            implementations = [impl for impl in implementations if impl.status == self.status_filter_var.get()]
        
        # Sortowanie po dacie końcowej operacji wdrożenia
        implementations.sort(key=self._sort_by_end_date)
        
        if not implementations:
            messagebox.showinfo("Informacja", "Brak wdrożeń do eksportu.")
            return
        
        # Wybierz plik docelowy
        file_path = filedialog.asksaveasfilename(
            title="Eksportuj wdrożenia do Excel",
            filetypes=[("Pliki Excel", "*.xlsx")],
            defaultextension=".xlsx",
            initialfile=f"wdrozenia_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        
        if not file_path:
            return
        
        # Eksportuj do Excel
        if export_implementations_to_excel(implementations, file_path):
            messagebox.showinfo(
                "Sukces", 
                f"Wdrożenia zostały wyeksportowane do pliku {file_path}."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                "Nie udało się wyeksportować wdrożeń."
            )