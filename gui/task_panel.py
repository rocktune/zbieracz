import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
from database.db_manager import DBManager
from database.models import Task, User, Implementation, Offer
from utils.timer import TaskTimer
from utils.export import export_tasks_to_excel

class TaskPanel(ttk.Frame):
    """Panel zadań użytkownika"""
    
    def __init__(self, parent, current_user, is_admin=False):
        """
        Inicjalizuje panel zadań
        
        Args:
            parent (ttk.Frame): Ramka nadrzędna
            current_user (User): Aktualnie zalogowany użytkownik
            is_admin (bool): Czy użytkownik jest administratorem
        """
        super().__init__(parent, padding=10)
        self.parent = parent
        self.current_user = current_user
        
        # Sprawdź uprawnienia
        self.is_admin = is_admin
        self.can_view_all_tasks = is_admin or current_user.has_permission("view_all_tasks")
        self.can_export_data = is_admin or current_user.has_permission("export_data")
        
        # Inicjalizacja timera
        self.timer = TaskTimer(self._update_timer_display)
        
        # Zmienne do przechowywania danych formularza
        self.category_var = tk.StringVar()
        self.task_type_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.implementation_var = tk.StringVar()
        self.offer_var = tk.StringVar()
        self.time_label_var = tk.StringVar(value="00:00:00")
        self.user_filter_var = tk.StringVar()
        
        # Stan UI
        self.active_task = False
        self.selected_task_id = None
        
        # Słowniki do przechowywania danych
        self.implementations = {}
        self.offers = {}
        self.users = {}
        
        # Stwórz widgety
        self._create_widgets()
        
        # Załaduj dane
        self._load_data()
        
        # Zdarzenia
        self.task_type_var.trace_add("write", self._on_task_type_change)
    
    def _create_widgets(self):
        """Tworzy widgety panelu zadań"""
        # Główny układ - zmiana na układ pionowy
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, expand=False, pady=(0, 10))
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        # Górny panel (formularz zadania)
        form_frame = ttk.LabelFrame(top_frame, text="Nowe zadanie", padding=10)
        form_frame.pack(fill=tk.X, expand=True)
        
        # Podziel formularz na lewą i prawą część dla bardziej kompaktowego układu
        form_left = ttk.Frame(form_frame)
        form_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        form_right = ttk.Frame(form_frame)
        form_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Lewa część formularza
        # Kategoria
        ttk.Label(form_left, text="Kategoria:").grid(row=0, column=0, sticky=tk.W, pady=5)
        category_combobox = ttk.Combobox(
            form_left, 
            textvariable=self.category_var,
            values=Task.CATEGORIES,
            state="readonly",
            width=20
        )
        category_combobox.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Typ zadania
        ttk.Label(form_left, text="Typ zadania:").grid(row=1, column=0, sticky=tk.W, pady=5)
        task_type_combobox = ttk.Combobox(
            form_left, 
            textvariable=self.task_type_var,
            values=Task.TYPES,
            state="readonly",
            width=20
        )
        task_type_combobox.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Wdrożenie (początkowo ukryte)
        self.implementation_label = ttk.Label(form_left, text="Wdrożenie:")
        self.implementation_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.implementation_combobox = ttk.Combobox(
            form_left, 
            textvariable=self.implementation_var,
            state="readonly",
            width=20
        )
        self.implementation_combobox.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Ukryj początkowo
        self.implementation_label.grid_remove()
        self.implementation_combobox.grid_remove()
        
        # Oferta (początkowo ukryta)
        self.offer_label = ttk.Label(form_left, text="Oferta:")
        self.offer_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.offer_combobox = ttk.Combobox(
            form_left, 
            textvariable=self.offer_var,
            state="readonly",
            width=20
        )
        self.offer_combobox.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Ukryj początkowo
        self.offer_label.grid_remove()
        self.offer_combobox.grid_remove()
        
        # Opis
        self.description_label = ttk.Label(form_left, text="Opis:")
        self.description_label.grid(row=4, column=0, sticky=tk.W, pady=5)
        
        description_entry = ttk.Entry(
            form_left, 
            textvariable=self.description_var,
            width=30
        )
        description_entry.grid(row=4, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Prawa część formularza
        # Timer
        timer_frame = ttk.Frame(form_right)
        timer_frame.pack(fill=tk.BOTH, expand=True)
        
        timer_label = ttk.Label(
            timer_frame, 
            textvariable=self.time_label_var,
            font=("Courier", 24)
        )
        timer_label.pack(pady=5)
        
        # Przyciski
        buttons_frame = ttk.Frame(form_right)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(
            buttons_frame, 
            text="Start",
            command=self._start_task
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            buttons_frame, 
            text="Stop",
            command=self._stop_task,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.end_button = ttk.Button(
            buttons_frame, 
            text="Zakończ pracę",
            command=self._end_work,
            state=tk.DISABLED
        )
        self.end_button.pack(side=tk.LEFT, padx=5)
        
        # Dolny panel (tabela zadań) - teraz na całą szerokość
        tasks_frame = ttk.LabelFrame(bottom_frame, text="Historia zadań", padding=10)
        tasks_frame.pack(fill=tk.BOTH, expand=True)
        
        # Filtr użytkownika (tylko dla admina lub użytkownika z uprawnieniem view_all_tasks)
        if self.can_view_all_tasks:
            filter_frame = ttk.Frame(tasks_frame)
            filter_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(filter_frame, text="Filtruj po użytkowniku:").pack(side=tk.LEFT, padx=(0, 5))
            
            self.user_filter_combobox = ttk.Combobox(
                filter_frame, 
                textvariable=self.user_filter_var,
                state="readonly",
                width=30
            )
            self.user_filter_combobox.pack(side=tk.LEFT, padx=5)
            self.user_filter_combobox.bind("<<ComboboxSelected>>", self._on_filter_change)
        
        # Przycisk eksportu (tylko jeśli ma uprawnienie export_data)
        if self.can_export_data:
            export_frame = ttk.Frame(tasks_frame)
            if not hasattr(self, 'filter_frame'):
                export_frame.pack(fill=tk.X, pady=(0, 10))
            else:
                # Jeśli jest już filtr, dodaj przycisk eksportu do niego
                export_frame = filter_frame
            
            ttk.Button(
                export_frame, 
                text="Eksportuj do Excel",
                command=self._export_to_excel
            ).pack(side=tk.RIGHT, padx=5)

        # Tabela zadań - teraz na całą szerokość
        table_frame = ttk.Frame(tasks_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ["id", "start_time", "end_time", "duration", "category", "task_type", "description"]
        if self.can_view_all_tasks:
            columns.insert(1, "user")  # Dodaj kolumnę użytkownika dla admina lub użytkownika z uprawnieniami
            
        self.tasks_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Nagłówki
        self.tasks_tree.heading("id", text="ID")
        self.tasks_tree.heading("start_time", text="Rozpoczęcie")
        self.tasks_tree.heading("end_time", text="Zakończenie")
        self.tasks_tree.heading("duration", text="Czas trwania")
        self.tasks_tree.heading("category", text="Kategoria")
        self.tasks_tree.heading("task_type", text="Typ")
        self.tasks_tree.heading("description", text="Opis")

        if self.can_view_all_tasks:
            self.tasks_tree.heading("user", text="Użytkownik")

        # Szerokości kolumn
        self.tasks_tree.column("id", width=50, minwidth=50)
        self.tasks_tree.column("start_time", width=130, minwidth=130)
        self.tasks_tree.column("end_time", width=130, minwidth=130)
        self.tasks_tree.column("duration", width=80, minwidth=80)
        self.tasks_tree.column("category", width=100, minwidth=100)
        self.tasks_tree.column("task_type", width=100, minwidth=100)
        self.tasks_tree.column("description", width=200, minwidth=200)

        if self.can_view_all_tasks:
            self.tasks_tree.column("user", width=150, minwidth=150)

        # Paski przewijania - tylko pionowy
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=y_scrollbar.set)

        # Pakowanie komponentów z paskami przewijania
        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Podwójne kliknięcie do edycji
        self.tasks_tree.bind("<Double-1>", self._on_task_double_click)
    
    def _load_data(self):
        """Ładuje dane do UI"""
        # Kategorie i typy zadań są już załadowane jako wartości comboboxów
        
        # Załaduj wdrożenia dla bieżącego użytkownika
        if self.is_admin or self.current_user.has_permission("manage_implementations"):
            implementations = Implementation.get_all()
        else:
            implementations = Implementation.get_by_user_id(self.current_user.id)
        
        self.implementations = {f"{impl.id}: {impl.name}": impl for impl in implementations}
        self.implementation_combobox["values"] = list(self.implementations.keys())
        
        # Załaduj oferty dla bieżącego użytkownika
        if self.is_admin or self.current_user.has_permission("manage_offers"):
            offers = Offer.get_all()
        else:
            offers = Offer.get_by_user_id(self.current_user.id)
        
        self.offers = {f"{offer.id}: {offer.name}": offer for offer in offers}
        self.offer_combobox["values"] = list(self.offers.keys())
        
        # Załaduj użytkowników (dla admina lub użytkownika z uprawnieniem view_all_tasks)
        if self.can_view_all_tasks:
            users = User.get_all_users()
            self.users = {f"{user.id}: {user.first_name} {user.last_name}": user for user in users}
            
            # Dodaj opcję "Wszyscy użytkownicy"
            user_values = ["Wszyscy użytkownicy"] + list(self.users.keys())
            self.user_filter_combobox["values"] = user_values
            self.user_filter_var.set("Wszyscy użytkownicy")
        
        # Załaduj zadania
        self._load_tasks()
   
    def _load_tasks(self):
        """Ładuje zadania do tabeli"""
        # Wyczyść istniejące zadania
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # Pobierz zadania
        if self.is_admin and self.user_filter_var.get() != "Wszyscy użytkownicy":
            # Filtrowane zadania dla admina
            selected_user = None
            for user_label, user in self.users.items():
                if user_label == self.user_filter_var.get():
                    selected_user = user
                    break
            
            if selected_user:
                tasks = Task.get_by_user_id(selected_user.id)
            else:
                tasks = []
        elif self.is_admin:
            # Wszystkie zadania dla admina
            tasks = Task.get_all_tasks()
        else:
            # Zadania bieżącego użytkownika
            tasks = Task.get_by_user_id(self.current_user.id)
        
        # Dodaj zadania do tabeli
        for task in tasks:
            # Konwertuj czas trwania z sekund na format hh:mm:ss
            duration_formatted = self._format_duration(task.duration)
            
            values = [
                task.id,
                task.start_time,
                task.end_time or "",
                duration_formatted,
                task.category,
                task.task_type,
                task.description or ""
            ]
            
            if self.is_admin:
                # Dodaj kolumnę z użytkownikiem
                if hasattr(task, 'user_full_name'):
                    user_name = task.user_full_name
                else:
                    user = User.get_by_id(task.user_id)
                    user_name = f"{user.first_name} {user.last_name}" if user else "Nieznany"
                
                values.insert(1, user_name)
            
            self.tasks_tree.insert("", "end", values=values)
    
    def _format_duration(self, seconds):
        """Formatuje czas trwania w sekundach na format hh:mm:ss"""
        if seconds is None or seconds == "":
            return ""
            
        # Konwersja na int (dla bezpieczeństwa)
        try:
            seconds = int(seconds)
        except (ValueError, TypeError):
            return ""
            
        # Oblicz godziny, minuty, sekundy
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Formatuj jako hh:mm:ss
        return f"{hours:02}:{minutes:02}:{seconds:02}"
        
    def _seconds_to_hms(self, seconds):
        """Konwertuje sekundy na tuple (godziny, minuty, sekundy)"""
        if seconds is None:
            return (0, 0, 0)
            
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return (hours, minutes, seconds)
    
    def _start_task(self):
        """Rozpoczyna nowe zadanie"""
        # Uruchom timer bez dodatkowych sprawdzeń
        self.timer.start()
        
        # Ustaw UI jako aktywne zadanie
        self.active_task = True
        self.start_button["state"] = tk.DISABLED
        self.stop_button["state"] = tk.NORMAL
        self.end_button["state"] = tk.NORMAL
    
    def _stop_task(self):
        """Zatrzymuje bieżące zadanie i zapisuje je do bazy"""
        if not self.active_task:
            return False
        
        # Sprawdź czy kategoria i typ są wybrane
        if not self.category_var.get() or not self.task_type_var.get():
            messagebox.showerror("Błąd", "Wybierz kategorię i typ zadania przed zapisaniem.")
            return False
        
        # Sprawdź czy wdrożenie/oferta są wybrane jeśli potrzebne
        if self.task_type_var.get() == "Wdrożenie" and not self.implementation_var.get():
            messagebox.showerror("Błąd", "Wybierz wdrożenie.")
            return False
        
        if self.task_type_var.get() == "Oferta" and not self.offer_var.get():
            messagebox.showerror("Błąd", "Wybierz ofertę.")
            return False
        
        # Zatrzymaj timer
        start_time, end_time, duration_seconds = self.timer.stop()
        
        # Sprawdź czy mamy prawidłowe dane
        if not start_time or not end_time:
            return False
        
        # Pobierz dane z formularza
        category = self.category_var.get()
        task_type = self.task_type_var.get()
        description = self.description_var.get()
        
        # Dane o wdrożeniu/ofercie
        implementation_id = None
        offer_id = None
        
        # Dodaj nazwę wdrożenia/oferty do opisu
        if task_type == "Wdrożenie" and self.implementation_var.get():
            impl = self.implementations.get(self.implementation_var.get())
            if impl:
                implementation_id = impl.id
                # Dodaj nazwę wdrożenia do opisu, jeśli opis jest pusty lub użytkownik zgodzi się na zastąpienie
                if not description or messagebox.askyesno(
                    "Aktualizacja opisu", 
                    f"Czy chcesz dodać nazwę wdrożenia '{impl.name}' do opisu?"
                ):
                    description = f"Wdrożenie: {impl.name}" + (f" - {description}" if description else "")
        
        if task_type == "Oferta" and self.offer_var.get():
            offer = self.offers.get(self.offer_var.get())
            if offer:
                offer_id = offer.id
                # Dodaj nazwę oferty do opisu, jeśli opis jest pusty lub użytkownik zgodzi się na zastąpienie
                if not description or messagebox.askyesno(
                    "Aktualizacja opisu", 
                    f"Czy chcesz dodać nazwę oferty '{offer.name}' do opisu?"
                ):
                    description = f"Oferta: {offer.name}" + (f" - {description}" if description else "")
        
        # Aktualizuj opis w polu tekstowym
        self.description_var.set(description)
        
        # Utwórz nowe zadanie
        task = Task(
            user_id=self.current_user.id,
            category=category,
            task_type=task_type,
            description=description,
            start_time=start_time,
            end_time=end_time,
            duration=duration_seconds,
            implementation_id=implementation_id,
            offer_id=offer_id
        )
        
        # Zapisz zadanie
        task.save()
        
        # Załaduj ponownie zadania
        self._load_tasks()
        
        # Zresetuj timer i UI, ale pozostaw aktywne zadanie
        self.time_label_var.set("00:00:00")
        self.timer.start()  # Rozpocznij ponownie timer
        
        return True
    
    def _end_work(self):
        """Kończy pracę i pokazuje podsumowanie"""
        if not self.active_task:
            return
        
        # Zatrzymaj zadanie (zapisz bieżące)
        task_saved = self._stop_task()
        
        # Zatrzymaj timer i zresetuj UI
        self.timer.reset()
        self.active_task = False
        self.start_button["state"] = tk.NORMAL
        self.stop_button["state"] = tk.DISABLED
        self.end_button["state"] = tk.DISABLED
        self.time_label_var.set("00:00:00")
        
        # Pokaż podsumowanie dnia
        self._show_summary()
    
    def _show_summary(self):
        """Pokazuje podsumowanie dnia pracy"""
        try:
            # Pobierz dzisiejsze zadania
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            conn = DBManager().get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT task_type, SUM(duration) as total_duration
            FROM tasks
            WHERE user_id = ? AND date(start_time) = ?
            GROUP BY task_type
            ''', (self.current_user.id, today))
            
            task_summary = cursor.fetchall()
            
            # Całkowity czas
            cursor.execute('''
            SELECT SUM(duration) as total_duration
            FROM tasks
            WHERE user_id = ? AND date(start_time) = ?
            ''', (self.current_user.id, today))
            
            total_result = cursor.fetchone()
            total_seconds = total_result['total_duration'] if total_result and total_result['total_duration'] else 0
            
            # Formatuj podsumowanie
            summary_text = f"Podsumowanie dnia pracy ({today}):\n\n"
            
            if task_summary:
                for row in task_summary:
                    task_type = row['task_type']
                    seconds = row['total_duration'] if row['total_duration'] else 0
                    hours, minutes, seconds = self._seconds_to_hms(seconds)
                    summary_text += f"{task_type}: {hours:02}:{minutes:02}:{seconds:02}\n"
            else:
                summary_text += "Brak zadań na dzisiaj.\n"
            
            # Dodaj całkowity czas
            if total_seconds:
                hours, minutes, seconds = self._seconds_to_hms(total_seconds)
                summary_text += f"\nCałkowity czas pracy: {hours:02}:{minutes:02}:{seconds:02}"
            
            # Pokaż podsumowanie
            messagebox.showinfo("Podsumowanie dnia", summary_text)
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas generowania podsumowania: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _update_timer_display(self, time_str):
        """Aktualizuje wyświetlacz timera"""
        self.time_label_var.set(time_str)
    
    def _on_task_type_change(self, *args):
        """Obsługuje zmianę typu zadania"""
        task_type = self.task_type_var.get()
        
        # Ukryj oba pola
        self.implementation_label.grid_remove()
        self.implementation_combobox.grid_remove()
        
        self.offer_label.grid_remove()
        self.offer_combobox.grid_remove()
        
        # Pokaż odpowiednie pole
        if task_type == "Wdrożenie":
            self.implementation_label.grid()
            self.implementation_combobox.grid()
            
            # Wyczyść wybór oferty
            self.offer_var.set("")
        
        elif task_type == "Oferta":
            self.offer_label.grid()
            self.offer_combobox.grid()
            
            # Wyczyść wybór wdrożenia
            self.implementation_var.set("")
    
    def _on_filter_change(self, event):
        """Obsługuje zmianę filtru użytkownika (tylko dla admina)"""
        self._load_tasks()
    
    def _on_task_double_click(self, event):
        """Obsługuje podwójne kliknięcie na zadanie"""
        # Pobierz wybrane zadanie
        selection = self.tasks_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tasks_tree.item(item, "values")
        
        # Pobierz ID zadania
        task_id = values[0]
        
        # Pobierz zadanie z bazy
        task = Task.get_by_id(task_id)
        
        if task:
            # Sprawdź czy użytkownik ma uprawnienia do edycji
            if not self.is_admin and not self.current_user.has_permission("view_all_tasks") and task.user_id != self.current_user.id:
                messagebox.showerror("Brak uprawnień", "Nie możesz edytować tego zadania.")
                return
            
            # Pokaż okno edycji
            self._show_edit_dialog(task)

    def _show_edit_dialog(self, task):
        """Pokazuje okno edycji zadania"""
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title(f"Edycja zadania #{task.id}")
        dialog.geometry("400x350")  # Zwiększona wysokość
        dialog.transient(self)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Zmienne
        category_var = tk.StringVar(value=task.category)
        task_type_var = tk.StringVar(value=task.task_type)
        description_var = tk.StringVar(value=task.description or "")
        
        # Formularz
        ttk.Label(main_frame, text="Kategoria:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(
            main_frame, 
            textvariable=category_var,
            values=Task.CATEGORIES,
            state="readonly",
            width=25
        ).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(main_frame, text="Typ zadania:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(
            main_frame, 
            textvariable=task_type_var,
            values=Task.TYPES,
            state="readonly",
            width=25
        ).grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(main_frame, text="Opis:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(
            main_frame, 
            textvariable=description_var,
            width=30
        ).grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Informacje o czasie (tylko do odczytu)
        ttk.Label(main_frame, text="Czas rozpoczęcia:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=task.start_time).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Czas zakończenia:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=task.end_time or "").grid(row=4, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Czas trwania:").grid(row=5, column=0, sticky=tk.W, pady=5)
        duration_formatted = self._format_duration(task.duration)
        ttk.Label(main_frame, text=duration_formatted).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=2, pady=15)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=lambda: self._save_edited_task(
                dialog, task, category_var.get(), task_type_var.get(), description_var.get()
            )
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def _save_edited_task(self, dialog, task, category, task_type, description):
        """Zapisuje edytowane zadanie"""
        # Aktualizuj zadanie
        task.category = category
        task.task_type = task_type
        task.description = description
        
        # Zapisz zaktualizowane zadanie
        task.save()
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę zadań
        self._load_tasks()
    
    def _export_to_excel(self):
        """Eksportuje zadania do pliku Excel"""
        # Pobierz zadania
        if self.is_admin and self.user_filter_var.get() != "Wszyscy użytkownicy":
            # Filtrowane zadania dla admina
            selected_user = None
            for user_label, user in self.users.items():
                if user_label == self.user_filter_var.get():
                    selected_user = user
                    break
            
            if selected_user:
                tasks = Task.get_by_user_id(selected_user.id)
                file_prefix = f"zadania_{selected_user.username}"
            else:
                tasks = []
                file_prefix = "zadania"
        elif self.is_admin:
            # Wszystkie zadania dla admina
            tasks = Task.get_all_tasks()
            file_prefix = "zadania_wszystkie"
        else:
            # Zadania bieżącego użytkownika
            tasks = Task.get_by_user_id(self.current_user.id)
            file_prefix = f"zadania_{self.current_user.username}"
        
        # Domyślna nazwa pliku
        default_filename = f"{file_prefix}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Zapytaj o lokalizację pliku
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Pliki Excel", "*.xlsx")],
            initialfile=default_filename
        )
        
        if not file_path:
            return
        
        # Eksportuj do pliku Excel
        if export_tasks_to_excel(tasks, file_path):
            messagebox.showinfo("Eksport", f"Zadania zostały wyeksportowane do pliku:\n{file_path}")
        else:
            messagebox.showerror("Błąd eksportu", "Nie udało się wyeksportować zadań.")