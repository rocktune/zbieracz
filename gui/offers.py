import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import re
from database.models import Implementation, Offer, User
from database.db_manager import DBManager
from utils.export import export_offers_to_excel
from database.models import WorkloadLimits

class OfferPanel(ttk.Frame):
    """Panel ofert (dla admina)"""
    
    def __init__(self, parent, current_user):
        """
        Inicjalizuje panel ofert
        
        Args:
            parent (ttk.Frame): Ramka nadrzędna
            current_user (User): Aktualnie zalogowany użytkownik (admin)
        """
        super().__init__(parent, padding=10)
        self.parent = parent
        self.current_user = current_user
        
        # Zmienne
        self.selected_offer_id = None
        self.status_filter_var = tk.StringVar(value="Wszystkie")
        
        # Stwórz widgety
        self._create_widgets()
        
        # Załaduj dane
        self._load_offers()
    
    def _create_widgets(self):
        """Tworzy widgety panelu ofert"""
        # Główny układ - zmiana na układ pionowy
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, expand=False, pady=(0, 10))
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Górny panel (formularz oferty)
        form_frame = ttk.LabelFrame(top_frame, text="Nowa oferta", padding=10)
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
            text="Dodaj ofertę",
            command=self._add_offer
        ).pack(pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Edytuj ofertę",
            command=self._edit_offer
        ).pack(pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Usuń ofertę",
            command=self._delete_offer
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
        

        # Dolny panel (tabela ofert) - na całą szerokość
        offers_frame = ttk.LabelFrame(bottom_frame, text="Lista ofert", padding=10)
        offers_frame.pack(fill=tk.BOTH, expand=True)

        # Filtr i eksport
        filter_frame = ttk.Frame(offers_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Filtruj po statusie:").pack(side=tk.LEFT, padx=(0, 5))

        status_combobox = ttk.Combobox(
            filter_frame, 
            textvariable=self.status_filter_var,
            values=["Wszystkie"] + Offer.STATUSES,
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

        # Tabela ofert z paskiem przewijania
        table_frame = ttk.Frame(offers_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Tabela ofert z osobnymi kolumnami dla operacji
        columns = ["id", "name", "status"]
        # Dodaj kolumny dla każdej operacji
        for operation in Offer.OPERATIONS:
            columns.append(operation)

        self.offers_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Nagłówki
        self.offers_tree.heading("id", text="ID")
        self.offers_tree.heading("name", text="Nazwa")
        self.offers_tree.heading("status", text="Status")

        # Nagłówki operacji
        for operation in Offer.OPERATIONS:
            self.offers_tree.heading(operation, text=operation)

        # Szerokości kolumn
        self.offers_tree.column("id", width=50, minwidth=50)
        self.offers_tree.column("name", width=200, minwidth=150)
        self.offers_tree.column("status", width=100, minwidth=100)

        # Szerokości kolumn operacji
        for operation in Offer.OPERATIONS:
            self.offers_tree.column(operation, width=150, minwidth=120)

        # Paski przewijania - tylko pionowy
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.offers_tree.yview)
        self.offers_tree.configure(yscrollcommand=y_scrollbar.set)

        self.offers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Podwójne kliknięcie do przypisania użytkowników
        self.offers_tree.bind("<Double-1>", self._on_offer_double_click)

        # Pojedyncze kliknięcie do wyboru
        self.offers_tree.bind("<<TreeviewSelect>>", self._on_offer_select)
    
    def _load_offers(self):
        """Ładuje oferty do tabeli"""
        # Wyczyść istniejące oferty
        for item in self.offers_tree.get_children():
            self.offers_tree.delete(item)
        
        # Pobierz oferty
        offers = Offer.get_all()
        
        # Filtrowanie po statusie
        if self.status_filter_var.get() != "Wszystkie":
            offers = [offer for offer in offers if offer.status == self.status_filter_var.get()]
        
        # Sortowanie po dacie końcowej operacji wdrożenia
        offers.sort(key=self._sort_by_end_date)
        
        # Dodaj oferty do tabeli
        for offer in offers:
            # Przygotuj tekst z operacjami
            operations_text = self._format_operations(offer)
            
            values = [
                offer.id,
                offer.name,
                offer.status,
                operations_text
            ]
            
            self.offers_tree.insert("", "end", values=values)
    
    def _sort_by_end_date(self, offer):
        """Funkcja sortująca oferty po planowanej dacie zakończenia"""
        if not offer.operations.get("Wdrożenie", {}).get("end_date"):
            return "9999-99-99"  # Oferty bez daty na końcu
        
        return offer.operations.get("Wdrożenie", {}).get("end_date", "9999-99-99")
    
    def _format_operations(self, offer):
        """Formatuje tekst operacji do wyświetlenia w tabeli"""
        operations_text = ""
        
        for operation_name in Offer.OPERATIONS:
            op_data = offer.operations.get(operation_name, {})
            
            # Pobierz dane użytkownika
            user_id = op_data.get("user_id")
            user = User.get_by_id(user_id) if user_id else None
            user_name = f"{user.first_name} {user.last_name}" if user else "-"
            
            # Dodaj do tekstu - tylko nazwa użytkownika
            if operations_text:
                operations_text += " | "
            
            operations_text += f"{operation_name}: {user_name}"
        
        return operations_text
    
    def _on_offer_select(self, event):
        """Obsługuje wybór oferty z tabeli"""
        selection = self.offers_tree.selection()
        if selection:
            item = selection[0]
            values = self.offers_tree.item(item, "values")
            self.selected_offer_id = int(values[0])
    
    def _on_offer_double_click(self, event):
        """Obsługuje podwójne kliknięcie na ofertę"""
        selection = self.offers_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.offers_tree.item(item, "values")
        
        # Pobierz ID oferty
        offer_id = int(values[0])
        
        # Pobierz ofertę z bazy
        offer = Offer.get_by_id(offer_id)
        
        if offer:
            # Pokaż okno przypisania użytkowników
            self._show_assign_users_dialog(offer)
    
    def _on_filter_change(self, event):
        """Obsługuje zmianę filtru statusu"""
        self._load_offers()
    


    def _add_offer(self):
        """Dodaje nową ofertę"""
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title("Dodaj ofertę")
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
            values=Offer.STATUSES,
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
            command=lambda: self._save_new_offer(
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

    def _save_new_offer(self, dialog, name, description, status, planned_start, planned_end):
        """Zapisuje nową ofertę"""
        # Sprawdź czy nazwa jest wprowadzona
        if not name:
            messagebox.showerror("Błąd", "Nazwa oferty nie może być pusta.")
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
        
        # Utwórz nową ofertę
        offer = Offer(
            name=name,
            description=description,
            status=status
        )
        
        # Zapisz ofertę (to utworzy domyślne operacje)
        offer.save()
        
        # Aktualizuj daty w operacji "Wdrożenie"
        if "Wdrożenie" in offer.operations:
            offer.operations["Wdrożenie"]["start_date"] = planned_start
            offer.operations["Wdrożenie"]["end_date"] = planned_end
            
            # Zapisz ponownie ofertę, aby zaktualizować daty operacji
            offer.save()
        
        # Wyczyść formularz
        # Usunięte, ponieważ zamykamy dialog
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę ofert
        self._load_offers()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            f"Oferta '{name}' została dodana."
        )
        
    def _edit_offer(self):
        """Edytuje istniejącą ofertę"""
        if not self.selected_offer_id:
            messagebox.showinfo("Informacja", "Wybierz ofertę do edycji.")
            return
        
        # Pobierz ofertę
        offer = Offer.get_by_id(self.selected_offer_id)
        
        if not offer:
            messagebox.showerror("Błąd", "Nie znaleziono oferty.")
            return
        
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title(f"Edycja oferty: {offer.name}")
        dialog.geometry("500x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formularz
        ttk.Label(main_frame, text="Nazwa:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(main_frame, width=30)
        name_entry.insert(0, offer.name)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(main_frame, text="Opis:").grid(row=1, column=0, sticky=tk.W, pady=5)
        description_entry = ttk.Entry(main_frame, width=30)
        description_entry.insert(0, offer.description or "")
        description_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Status
        ttk.Label(main_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, pady=5)
        status_combobox = ttk.Combobox(
            main_frame,
            values=Offer.STATUSES,
            state="readonly",
            width=20
        )
        status_combobox.set(offer.status)
        status_combobox.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Planowana data rozpoczęcia
        ttk.Label(main_frame, text="Planowany start (RRRR-MM-DD):").grid(row=3, column=0, sticky=tk.W, pady=5)
        planned_start_entry = ttk.Entry(main_frame, width=15)
        
        # Pobierz datę rozpoczęcia z operacji "Wdrożenie" jeśli istnieje
        if "Wdrożenie" in offer.operations:
            start_date = offer.operations["Wdrożenie"].get("start_date", "")
            if start_date:
                planned_start_entry.insert(0, start_date)
        
        planned_start_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Planowana data zakończenia
        ttk.Label(main_frame, text="Planowane zakończenie (RRRR-MM-DD):").grid(row=4, column=0, sticky=tk.W, pady=5)
        planned_end_entry = ttk.Entry(main_frame, width=15)
        
        # Pobierz datę zakończenia z operacji "Wdrożenie" jeśli istnieje
        if "Wdrożenie" in offer.operations:
            end_date = offer.operations["Wdrożenie"].get("end_date", "")
            if end_date:
                planned_end_entry.insert(0, end_date)
        
        planned_end_entry.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=15)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=lambda: self._save_edited_offer(
                dialog,
                offer,
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

    def _save_edited_offer(self, dialog, offer, name, description, status, planned_start, planned_end):
        """Zapisuje edytowaną ofertę"""
        # Sprawdź czy nazwa jest wprowadzona
        if not name:
            messagebox.showerror("Błąd", "Nazwa oferty nie może być pusta.")
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
        
        # Aktualizuj ofertę
        offer.name = name
        offer.description = description
        offer.status = status
        
        # Aktualizuj daty w operacji "Wdrożenie"
        if "Wdrożenie" not in offer.operations:
            offer.operations["Wdrożenie"] = {}
        
        # Zachowaj istniejące dane użytkownika dla operacji Wdrożenie
        user_id = offer.operations["Wdrożenie"].get("user_id")
        
        # Ustaw daty
        offer.operations["Wdrożenie"]["start_date"] = planned_start
        offer.operations["Wdrożenie"]["end_date"] = planned_end
        offer.operations["Wdrożenie"]["user_id"] = user_id
        
        # Zapisz ofertę
        offer.save()
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę ofert
        self._load_offers()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            f"Oferta '{name}' została zaktualizowana."
        )
    
    def _delete_offer(self):
        """Usuwa ofertę"""
        if not self.selected_offer_id:
            messagebox.showinfo("Informacja", "Wybierz ofertę do usunięcia.")
            return
        
        # Pobierz ofertę
        offer = Offer.get_by_id(self.selected_offer_id)
        
        if not offer:
            messagebox.showerror("Błąd", "Nie znaleziono oferty.")
            return
        
        # Potwierdź usunięcie
        if not messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć ofertę '{offer.name}'?"
        ):
            return
        
        # Usuń ofertę
        if offer.delete():
            # Odśwież listę ofert
            self._load_offers()
            
            # Wyczyść wybór
            self.selected_offer_id = None
            
            # Wyświetl komunikat
            messagebox.showinfo(
                "Sukces", 
                f"Oferta '{offer.name}' została usunięta."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                "Nie udało się usunąć oferty."
            )
    
    def _show_assign_users_dialog(self, offer):
        """Pokazuje okno przypisania użytkowników do operacji"""
        # Pobierz wszystkich użytkowników
        users = User.get_all_users()
        
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title(f"Przypisanie użytkowników do oferty: {offer.name}")
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
            text=f"Oferta: {offer.name}",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Status oferty:").pack(side=tk.LEFT, padx=(0, 5))
        
        status_combobox = ttk.Combobox(
            status_frame,
            values=Offer.STATUSES,
            state="readonly",
            width=15
        )
        status_combobox.set(offer.status)
        status_combobox.pack(side=tk.LEFT)
        
        # Operacje
        operations_frame = ttk.LabelFrame(main_frame, text="Operacje", padding=10)
        operations_frame.pack(fill=tk.BOTH, expand=True)
        
        # Słownik przechowujący UI dla operacji
        operation_ui = {}
        
        # Stwórz UI dla każdej operacji
        for i, operation_name in enumerate(Offer.OPERATIONS):
            op_frame = ttk.Frame(operations_frame)
            op_frame.pack(fill=tk.X, pady=5)
            
            # Dane operacji
            op_data = offer.operations.get(operation_name, {})
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
                offer,
                status_combobox.get(),
                operation_ui
            )
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _save_assigned_users(self, dialog, offer, status, operation_ui):
        """Zapisuje przypisanie użytkowników do operacji"""
        # Aktualizuj status
        offer.status = status
        
        # Aktualizuj operacje
        for operation_name, ui in operation_ui.items():
            user_option = ui["user_var"].get()
            user_id = None
            
            if user_option:
                try:
                    user_id = int(user_option.split(":")[0])
                except:
                    pass
            
            start_date = ui["start_date_entry"].get_date().strftime("%Y-%m-%d")
            end_date = ui["end_date_entry"].get_date().strftime("%Y-%m-%d")
            
            # Sprawdź daty
            if start_date > end_date:
                messagebox.showerror(
                    "Błąd", 
                    f"Dla operacji '{operation_name}' data rozpoczęcia jest późniejsza niż data zakończenia."
                )
                return
            
            # Aktualizuj operację
            offer.operations[operation_name] = {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date
            }
        
        # Sprawdź czy operacje mieszczą się w zakresie głównego wdrożenia
        main_start = offer.operations.get("Wdrożenie", {}).get("start_date")
        main_end = offer.operations.get("Wdrożenie", {}).get("end_date")
        
        if main_start and main_end:
            for operation_name, op_data in offer.operations.items():
                if operation_name == "Wdrożenie":
                    continue
                
                op_start = op_data.get("start_date")
                op_end = op_data.get("end_date")
                
                if op_start and op_end and (op_start < main_start or op_end > main_end):
                    messagebox.showerror(
                        "Błąd", 
                        f"Operacja '{operation_name}' wykracza poza zakres głównej oferty."
                    )
                    return
        
        # Zapisz ofertę
        offer.save()
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę ofert
        self._load_offers()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            f"Przypisania użytkowników do oferty '{offer.name}' zostały zaktualizowane."
        )
    
    def _auto_assign_users(self):
        """Automatycznie przydziela użytkowników do ofert"""
        # Pobierz wszystkich użytkowników
        users = User.get_all_users()
        
        if not users:
            messagebox.showinfo("Informacja", "Brak użytkowników do przypisania.")
            return
        
        # Pobierz wszystkie oferty o statusie "W trakcie"
        offers = [offer for offer in Offer.get_all() if offer.status == "W trakcie"]
        
        if not offers:
            messagebox.showinfo("Informacja", "Brak ofert w trakcie do przypisania.")
            return
        
        # Potwierdź operację
        if not messagebox.askyesno(
            "Potwierdzenie",
            "Czy na pewno chcesz automatycznie przydzielić użytkowników do ofert? "
            "Istniejące przypisania zostaną nadpisane."
        ):
            return
        
        # Inicjalizuj obciążenie użytkowników
        # słownik user_id -> słownik data -> liczba zadań
        user_load = {user.id: {} for user in users}
        
        # Pobierz istniejące wdrożenia, żeby uwzględnić ich obciążenie
        from database.models import Implementation
        implementations = [impl for impl in Implementation.get_all() if impl.status == "W trakcie"]
        
        # Dodaj obciążenie z wdrożeń
        for impl in implementations:
            for operation_name, op_data in impl.operations.items():
                user_id = op_data.get("user_id")
                start_date = op_data.get("start_date")
                end_date = op_data.get("end_date")
                
                if user_id and start_date and end_date:
                    self._add_user_load(user_load, user_id, start_date, end_date)
        
        # Przygotuj dane o użytkownikach
        user_dict = {user.id: user for user in users}
        
        # Posortuj oferty według daty rozpoczęcia
        offers.sort(key=lambda offer: offer.operations.get("Wdrożenie", {}).get("start_date", "9999-99-99"))
        
        # Przypisz użytkowników do ofert
        for offer in offers:
            # Pobierz zakres dat głównej oferty
            main_op = offer.operations.get("Wdrożenie", {})
            main_start = main_op.get("start_date")
            main_end = main_op.get("end_date")
            
            if not main_start or not main_end:
                continue  # Pomijamy oferty bez dat
            
            # Przypisz użytkownika do głównej operacji
            self._assign_user_to_operation(
                offer, "Wdrożenie", main_start, main_end, user_load, user_dict
            )
            
            # Przypisz użytkowników do pozostałych operacji
            for operation_name in ["Spawanie", "Malowanie", "Klejenie"]:
                # Pobierz daty z operacji lub użyj głównych dat
                op_data = offer.operations.get(operation_name, {})
                op_start = op_data.get("start_date", main_start)
                op_end = op_data.get("end_date", main_end)
                
                # Upewnij się, że daty mieszczą się w zakresie głównej oferty
                op_start = max(op_start, main_start)
                op_end = min(op_end, main_end)
                
                # Przypisz użytkownika
                self._assign_user_to_operation(
                    offer, operation_name, op_start, op_end, user_load, user_dict
                )
        
        # Zapisz wszystkie oferty
        for offer in offers:
            offer.save()
        
        # Odśwież listę ofert
        self._load_offers()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            "Automatyczne przydzielanie użytkowników do ofert zostało zakończone."
        )
    
    def _add_user_load(self, user_load, user_id, start_date, end_date):
        """Dodaje obciążenie użytkownika w danym okresie"""
        # Przygotuj daty do iteracji
        current_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Dodaj obciążenie dla każdego dnia
        date_obj = current_date
        while date_obj <= end_date_obj:
            date_str = date_obj.strftime("%Y-%m-%d")
            
            if date_str not in user_load[user_id]:
                user_load[user_id][date_str] = 0
            
            user_load[user_id][date_str] += 1
            date_obj += datetime.timedelta(days=1)
    
    def _assign_user_to_operation(self, offer, operation_name, start_date, end_date, user_load, user_dict):
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
            offer.operations[operation_name] = {
                "user_id": best_user_id,
                "start_date": start_date,
                "end_date": end_date
            }
            
            # Zaktualizuj obciążenie użytkownika
            self._add_user_load(user_load, best_user_id, start_date, end_date)
    
    def _export_to_excel(self):
        """Eksportuje oferty do pliku Excel"""
        # Pobierz filtrowane oferty
        offers = Offer.get_all()
        
        if self.status_filter_var.get() != "Wszystkie":
            offers = [offer for offer in offers if offer.status == self.status_filter_var.get()]
        
        # Sortowanie po dacie końcowej operacji oferty
        offers.sort(key=self._sort_by_end_date)
        
        if not offers:
            messagebox.showinfo("Informacja", "Brak ofert do eksportu.")
            return
        
        # Wybierz plik docelowy
        file_path = filedialog.asksaveasfilename(
            title="Eksportuj oferty do Excel",
            filetypes=[("Pliki Excel", "*.xlsx")],
            defaultextension=".xlsx",
            initialfile=f"oferty_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        
        if not file_path:
            return
        
        # Eksportuj do Excel
        if export_offers_to_excel(offers, file_path):
            messagebox.showinfo(
                "Sukces", 
                f"Oferty zostały wyeksportowane do pliku {file_path}."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                "Nie udało się wyeksportować ofert."
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

    # Zaktualizuj metodę auto_assign_users
    def _auto_assign_users(self):
        """Automatycznie przydziela użytkowników do ofert"""
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
            "Czy na pewno chcesz automatycznie przydzielić użytkowników do ofert i wdrożeń? "
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
        
        # Pobierz aktualne obciążenie z istniejących wdrożeń i ofert
        self._calculate_current_workload(implementations, offers, user_load)
        
        # Posortuj oferty według daty rozpoczęcia
        offers.sort(key=lambda offer: offer.operations.get("Wdrożenie", {}).get("start_date", "9999-99-99"))
        
        # Najpierw przydziel główne operacje ofert
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
        
        # Zapisz wszystkie oferty
        for offer in offers:
            offer.save()
        
        # Odśwież listę ofert
        self._load_offers()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            "Automatyczne przydzielanie użytkowników do projektów zostało zakończone."
        )