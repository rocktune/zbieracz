import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import calendar
from database.models import User, Implementation, Offer

class GanttPanel(ttk.Frame):
    """Panel wykresu Gantta dla wdrożeń i ofert"""
    
    MONTHS_PL = ["", "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", 
             "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
    DAYS_PL = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Ndz"]

    COLORS = {
        "Wdrożenie": "#4CAF50",  # Zielony
        "Spawanie": "#2196F3",    # Niebieski
        "Malowanie": "#FFC107",   # Żółty
        "Klejenie": "#F44336",    # Czerwony
        "Implementation": "#81C784",  # Jasnozielony
        "Offer": "#90CAF9"        # Jasnoniebieski
    }
    
    # Dodajemy stałe skali widoku
    SCALE_DAY = "Dzień"
    SCALE_WEEK = "Tydzień"
    SCALE_MONTH = "Miesiąc"
    
    def __init__(self, parent, current_user, is_admin=False):
        """
        Inicjalizuje panel wykresu Gantta
        
        Args:
            parent (ttk.Frame): Ramka nadrzędna
            current_user (User): Aktualnie zalogowany użytkownik
            is_admin (bool): Czy użytkownik jest administratorem
        """
        super().__init__(parent, padding=10)
        self.parent = parent
        self.current_user = current_user
        self.is_admin = is_admin
        
        # Daty - używamy first_day_of_month i last_day_of_month, aby uniknąć błędu
        self.start_date = self._first_day_of_month(datetime.date.today())
        # Ostatni dzień za 2 miesiące (bezpieczna metoda)
        self.end_date = self._last_day_of_month(self._add_months(self.start_date, 2))
        
        # Zmienne
        self.user_filter_var = tk.StringVar()
        self.scale_var = tk.StringVar(value=self.SCALE_MONTH)  # Domyślna skala to miesiąc
        self.canvas_width = 0
        self.canvas_height = 0
        self.day_width = 20  # Szerokość dnia w pikselach
        self.row_height = 30  # Wysokość wiersza w pikselach
        self.header_height = 50  # Wysokość nagłówka w pikselach
        self.margin_left = 150  # Margines lewy w pikselach
        
        # Stwórz widgety
        self._create_widgets()
        
        # Załaduj dane
        self._load_data()
        
    def _first_day_of_month(self, date):
        """Zwraca pierwszy dzień miesiąca dla podanej daty"""
        return date.replace(day=1)
        
    def _last_day_of_month(self, date):
        """Zwraca ostatni dzień miesiąca dla podanej daty"""
        # Przejdź do pierwszego dnia następnego miesiąca i cofnij o jeden dzień
        if date.month == 12:
            next_month = date.replace(year=date.year+1, month=1, day=1)
        else:
            next_month = date.replace(month=date.month+1, day=1)
        
        return next_month - datetime.timedelta(days=1)
        
    def _add_months(self, date, months):
        """Dodaje podaną liczbę miesięcy do daty w bezpieczny sposób"""
        month = date.month - 1 + months
        year = date.year + month // 12
        month = month % 12 + 1
        return date.replace(year=year, month=month, day=1)
    
    def _create_widgets(self):
        """Tworzy widgety panelu Gantta"""
        # Główny układ
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Panel filtrów
        filter_frame = ttk.LabelFrame(top_frame, text="Filtry", padding=10)
        filter_frame.pack(fill=tk.X)
        
        # Filtr użytkownika
        ttk.Label(filter_frame, text="Użytkownik:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.user_filter_combobox = ttk.Combobox(
            filter_frame,
            textvariable=self.user_filter_var,
            state="readonly",
            width=30
        )
        self.user_filter_combobox.pack(side=tk.LEFT, padx=5)
        
        # Dodajemy selektor skali wykresu
        ttk.Label(filter_frame, text="Skala:").pack(side=tk.LEFT, padx=(15, 5))
        
        scale_combobox = ttk.Combobox(
            filter_frame,
            textvariable=self.scale_var,
            values=[self.SCALE_DAY, self.SCALE_WEEK, self.SCALE_MONTH],
            state="readonly",
            width=10
        )
        scale_combobox.pack(side=tk.LEFT, padx=5)
        scale_combobox.bind("<<ComboboxSelected>>", self._on_scale_change)
        
        # Przyciski nawigacji
        ttk.Button(
            filter_frame, 
            text="<<",
            width=3,
            command=lambda: self._change_date_range(-2)
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            filter_frame, 
            text="<",
            width=3,
            command=lambda: self._change_date_range(-1)
        ).pack(side=tk.RIGHT, padx=5)
        
        self.date_label = ttk.Label(filter_frame, text="")
        self.date_label.pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(
            filter_frame, 
            text=">",
            width=3,
            command=lambda: self._change_date_range(1)
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            filter_frame, 
            text=">>",
            width=3,
            command=lambda: self._change_date_range(2)
        ).pack(side=tk.RIGHT, padx=5)
        
        # Przycisk "Dzisiaj"
        ttk.Button(
            filter_frame,
            text="Dzisiaj",
            width=8,
            command=self._go_to_today
        ).pack(side=tk.RIGHT, padx=5)
        
        # Aktualizacja daty
        self._update_date_label()
        
        # Canvas dla wykresu Gantta
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas z paskami przewijania
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        
        # Paski przewijania
        y_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        x_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        # Konfiguracja canvasa
        self.canvas.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Packowanie pasków przewijania i canvasa
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Obsługa zmiany rozmiaru
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Obsługa zmiany filtru
        self.user_filter_combobox.bind("<<ComboboxSelected>>", self._on_filter_change)
    
    def _load_data(self):
        """Ładuje dane do widoku Gantta"""
        # Załaduj użytkowników
        users = User.get_all_users()
        
        # Dodaj opcje filtrowania
        if self.is_admin:
            # Admin widzi wszystkich użytkowników
            user_options = ["Wszyscy użytkownicy"] + [f"{user.id}: {user.first_name} {user.last_name}" for user in users]
            self.user_filter_combobox["values"] = user_options
            self.user_filter_var.set("Wszyscy użytkownicy")
        else:
            # Zwykły użytkownik widzi tylko siebie
            self.user_filter_combobox["values"] = [f"{self.current_user.id}: {self.current_user.first_name} {self.current_user.last_name}"]
            self.user_filter_var.set(f"{self.current_user.id}: {self.current_user.first_name} {self.current_user.last_name}")
        
        # Pobierz i pokaż dane
        self._draw_gantt()
    
    def _on_canvas_configure(self, event):
        """Obsługuje zmianę rozmiaru canvasa"""
        self.canvas_width = event.width
        self.canvas_height = event.height
        
        # Ponownie narysuj wykres
        self._draw_gantt()
    
    def _on_filter_change(self, event):
        """Obsługuje zmianę filtru użytkownika"""
        self._draw_gantt()
    
    def _on_scale_change(self, event):
        """Obsługuje zmianę skali widoku"""
        # Dostosuj skalę
        scale = self.scale_var.get()
        
        # Dostosuj szerokość dnia w zależności od skali
        if scale == self.SCALE_DAY:
            self.day_width = 60  # Szerszy widok dla dni
            # Ustaw zakres na 7 dni
            today = datetime.date.today()
            self.start_date = today
            self.end_date = today + datetime.timedelta(days=6)
        elif scale == self.SCALE_WEEK:
            self.day_width = 30  # Średni widok dla tygodni
            # Ustaw zakres na 4 tygodnie
            today = datetime.date.today()
            # Znajdź początek tygodnia (poniedziałek)
            start_date = today - datetime.timedelta(days=today.weekday())
            self.start_date = start_date
            self.end_date = start_date + datetime.timedelta(days=27)  # 4 tygodnie
        else:  # Miesiąc
            self.day_width = 20  # Standardowy widok miesięczny
            # Ustaw zakres na 3 miesiące
            self.start_date = self._first_day_of_month(datetime.date.today())
            self.end_date = self._last_day_of_month(self._add_months(self.start_date, 2))
        
        # Aktualizuj etykietę
        self._update_date_label()
        
        # Ponownie narysuj wykres
        self._draw_gantt()
    
    def _update_date_label(self):
        """Aktualizuje etykietę z zakresem dat"""
        start_str = self.start_date.strftime("%d.%m.%Y")
        end_str = self.end_date.strftime("%d.%m.%Y")
        self.date_label.config(text=f"{start_str} - {end_str}")
    
    def _change_date_range(self, amount):
        """Zmienia zakres dat o podaną wartość"""
        scale = self.scale_var.get()
        
        if scale == self.SCALE_DAY:
            # Przesuwanie o dni
            self.start_date += datetime.timedelta(days=amount * 7)  # Przesuwamy o tygodnie
            self.end_date += datetime.timedelta(days=amount * 7)
        elif scale == self.SCALE_WEEK:
            # Przesuwanie o tygodnie
            self.start_date += datetime.timedelta(days=amount * 14)  # Przesuwamy o 2 tygodnie
            self.end_date += datetime.timedelta(days=amount * 14)
        else:  # Miesiąc
            # Przesuwanie o miesiące
            if amount > 0:
                # Przesuwanie w przód
                self.start_date = self._add_months(self.start_date, amount)
                self.end_date = self._last_day_of_month(self._add_months(self.start_date, 2))
            else:
                # Przesuwanie w tył
                self.start_date = self._add_months(self.start_date, amount)
                self.end_date = self._last_day_of_month(self._add_months(self.start_date, 2))
        
        # Aktualizuj etykietę
        self._update_date_label()
        
        # Ponownie narysuj wykres
        self._draw_gantt()
    
    def _go_to_today(self):
        """Przechodzi do dzisiejszej daty"""
        scale = self.scale_var.get()
        
        today = datetime.date.today()
        
        if scale == self.SCALE_DAY:
            self.start_date = today
            self.end_date = today + datetime.timedelta(days=6)
        elif scale == self.SCALE_WEEK:
            # Znajdź początek tygodnia (poniedziałek)
            start_date = today - datetime.timedelta(days=today.weekday())
            self.start_date = start_date
            self.end_date = start_date + datetime.timedelta(days=27)  # 4 tygodnie
        else:  # Miesiąc
            self.start_date = self._first_day_of_month(today)
            self.end_date = self._last_day_of_month(self._add_months(self.start_date, 2))
        
        # Aktualizuj etykietę
        self._update_date_label()
        
        # Ponownie narysuj wykres
        self._draw_gantt()
    
    def _draw_gantt(self):
        """Rysuje wykres Gantta"""
        # Wyczyść canvas
        self.canvas.delete("all")
        
        # Pobierz dane do wykresu
        gantt_data = self._get_gantt_data()
        
        if not gantt_data:
            # Brak danych do wyświetlenia
            self.canvas.create_text(
                self.canvas_width // 2, 
                self.canvas_height // 2,
                text="Brak danych do wyświetlenia",
                font=("Arial", 12)
            )
            return
        
        # Oblicz całkowitą liczbę dni
        total_days = (self.end_date - self.start_date).days + 1
        
        # Oblicz całkowitą szerokość wykresu
        chart_width = self.margin_left + (total_days * self.day_width)
        
        # Oblicz całkowitą wysokość wykresu
        chart_height = self.header_height + (len(gantt_data) * self.row_height)
        
        # Skonfiguruj obszar przewijania
        self.canvas.config(scrollregion=(0, 0, chart_width, chart_height))
        
        # Narysuj tło
        self._draw_background(total_days, len(gantt_data))
        
        # Narysuj nagłówek
        self._draw_header(total_days)
        
        # Narysuj dane
        self._draw_data(gantt_data, total_days)
    
    def _get_gantt_data(self):
        """Pobiera dane do wykresu Gantta"""
        # Dane wykresu: lista słowników {label, tasks}
        gantt_data = []
        
        # Pobierz wybranego użytkownika
        selected_user_id = None
        if self.user_filter_var.get() != "Wszyscy użytkownicy":
            try:
                selected_user_id = int(self.user_filter_var.get().split(":")[0])
            except:
                pass
        
        # Pobierz użytkowników
        if selected_user_id:
            users = [User.get_by_id(selected_user_id)]
        elif self.is_admin:
            users = User.get_all_users()
        else:
            users = [self.current_user]
        
        # Dla każdego użytkownika
        for user in users:
            if not user:
                continue
                
            user_label = f"{user.first_name} {user.last_name}"
            user_tasks = []
            
            # Pobierz wdrożenia
            implementations = Implementation.get_by_user_id(user.id)
            
            for impl in implementations:
                # Dla każdej operacji przypisanej do użytkownika
                for operation_name, op_data in impl.operations.items():
                    user_id = op_data.get("user_id")
                    start_date = op_data.get("start_date")
                    end_date = op_data.get("end_date")
                    
                    if user_id == user.id and start_date and end_date:
                        try:
                            # Bezpieczna konwersja dat z obsługą błędów
                            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                            
                            # Sprawdź czy zadanie mieści się w zakresie widocznym
                            if end_date_obj < self.start_date or start_date_obj > self.end_date:
                                continue
                            
                            # Dodaj zadanie
                            user_tasks.append({
                                "label": f"{impl.name} - {operation_name}",
                                "start_date": start_date_obj,
                                "end_date": end_date_obj,
                                "type": "Implementation",
                                "operation": operation_name
                            })
                        except ValueError:
                            # Ignoruj wpisy z nieprawidłowymi datami
                            continue
            
            # Pobierz oferty
            offers = Offer.get_by_user_id(user.id)
            
            for offer in offers:
                # Dla każdej operacji przypisanej do użytkownika
                for operation_name, op_data in offer.operations.items():
                    user_id = op_data.get("user_id")
                    start_date = op_data.get("start_date")
                    end_date = op_data.get("end_date")
                    
                    if user_id == user.id and start_date and end_date:
                        try:
                            # Bezpieczna konwersja dat z obsługą błędów
                            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
                            
                            # Sprawdź czy zadanie mieści się w zakresie widocznym
                            if end_date_obj < self.start_date or start_date_obj > self.end_date:
                                continue
                            
                            # Dodaj zadanie
                            user_tasks.append({
                                "label": f"{offer.name} - {operation_name}",
                                "start_date": start_date_obj,
                                "end_date": end_date_obj,
                                "type": "Offer",
                                "operation": operation_name
                            })
                        except ValueError:
                            # Ignoruj wpisy z nieprawidłowymi datami
                            continue
            
            # Dodaj dane użytkownika NAWET jeśli nie ma zadań
            gantt_data.append({
                "label": user_label,
                "tasks": user_tasks
            })
        
        return gantt_data

    
    def _draw_background(self, total_days, rows):
        """Rysuje tło wykresu"""
        scale = self.scale_var.get()
        
        # Wybierz odstęp linii siatki w zależności od skali
        if scale == self.SCALE_DAY:
            grid_spacing = 1  # Linia co dzień
        elif scale == self.SCALE_WEEK:
            grid_spacing = 7  # Linia co tydzień
        else:  # Miesiąc
            grid_spacing = 1  # Linia co dzień, ale zmieniamy jej styl dla różnych dni
        
        # Rysuj siatkę pionową
        for i in range(total_days + 1):
            x = self.margin_left + (i * self.day_width)
            
            # Wybierz styl linii w zależności od dnia
            if scale == self.SCALE_MONTH:
                current_date = self.start_date + datetime.timedelta(days=i)
                # Podświetl pierwszy dzień miesiąca i pierwszy dzień tygodnia (poniedziałek)
                if current_date.day == 1:
                    line_color = "#444444"  # Ciemny dla pierwszego dnia miesiąca
                    line_width = 2
                elif current_date.weekday() == 0:  # Poniedziałek
                    line_color = "#888888"  # Średni dla poniedziałku
                    line_width = 1
                else:
                    line_color = "#DDDDDD"  # Jasny dla normalnych dni
                    line_width = 1
            elif scale == self.SCALE_WEEK and i % 7 == 0:
                line_color = "#888888"
                line_width = 1
            elif scale == self.SCALE_DAY:
                line_color = "#DDDDDD"
                line_width = 1
            else:
                line_color = "#DDDDDD"
                line_width = 1
            
            # Linia pionowa
            self.canvas.create_line(
                x, 0, 
                x, self.header_height + (rows * self.row_height),
                fill=line_color,
                width=line_width
            )
        
        # Siatka pozioma (wiersze)
        for i in range(rows + 1):
            y = self.header_height + (i * self.row_height)
            
            # Linia pozioma
            self.canvas.create_line(
                0, y, 
                self.margin_left + (total_days * self.day_width), y,
                fill="#DDDDDD"
            )
        
        # Dodaj podświetlenie dzisiejszego dnia
        today = datetime.date.today()
        if self.start_date <= today <= self.end_date:
            # Oblicz pozycję dzisiejszego dnia
            today_offset = (today - self.start_date).days
            x = self.margin_left + (today_offset * self.day_width)
            
            # Narysuj podświetlenie
            self.canvas.create_rectangle(
                x, 0,
                x + self.day_width, self.header_height + (rows * self.row_height),
                fill="#FFFFDD",  # Jasny żółty
                outline="",
                tags="today_highlight"
            )
            
            # Przesuń podświetlenie za tło
            self.canvas.tag_lower("today_highlight")
    
    def _draw_header(self, total_days):
        """Rysuje nagłówek wykresu"""
        # Tytuł wykresu
        self.canvas.create_text(
            self.margin_left // 2, 
            self.header_height // 2,
            text="Użytkownik",
            font=("Arial", 10, "bold")
        )
        
        # Linia oddzielająca
        self.canvas.create_line(
            self.margin_left, 0, 
            self.margin_left, self.header_height,
            fill="black"
        )
        
        # Aktualna data
        current_date = self.start_date
        
        # Poprzedni miesiąc
        prev_month = None
        month_start_x = 0
        
        # Format nagłówka zależy od skali
        scale = self.scale_var.get()
        
        # Dla każdego dnia
        for i in range(total_days):
            x = self.margin_left + (i * self.day_width)
            
            # Dzień miesiąca
            day = current_date.day
            
            # Nazwa dnia tygodnia (po polsku)
            day_name = self.DAYS_PL[current_date.weekday()]
            
            # Format w zależności od skali
            if scale == self.SCALE_DAY:
                # Dla widoku dziennego pokazujemy pełną datę i dzień tygodnia
                self.canvas.create_text(
                    x + (self.day_width // 2), 
                    self.header_height - 15,
                    text=f"{day} {day_name}",
                    font=("Arial", 9)
                )
                # Dodaj też numer tygodnia
                week_num = current_date.isocalendar()[1]
                self.canvas.create_text(
                    x + (self.day_width // 2), 
                    self.header_height - 35,
                    text=f"Tydz. {week_num}",
                    font=("Arial", 8)
                )
            elif scale == self.SCALE_WEEK:
                # Dla widoku tygodniowego pokazujemy dzień i datę
                if current_date.weekday() == 0 or i == 0:  # Poniedziałek lub pierwszy dzień
                    self.canvas.create_text(
                        x + (self.day_width // 2), 
                        self.header_height - 15,
                        text=f"{day} {day_name}",
                        font=("Arial", 9)
                    )
                else:
                    self.canvas.create_text(
                        x + (self.day_width // 2), 
                        self.header_height - 15,
                        text=f"{day}",
                        font=("Arial", 9)
                    )
            else:  # Miesiąc - pionowe etykiety dla dni
                # Dla widoku miesięcznego pokazujemy pionowo
                self.canvas.create_text(
                    x + (self.day_width // 2), 
                    self.header_height - 10,
                    text=f"{day}",
                    font=("Arial", 8)
                )
                # Pionowa etykieta dnia tygodnia
                self.canvas.create_text(
                    x + (self.day_width // 2), 
                    self.header_height - 30,
                    text=f"{day_name}",
                    font=("Arial", 7),
                    angle=90  # Pionowy tekst
                )
            
            # Narysuj nazwę miesiąca jeśli się zmienił (po polsku)
            month = current_date.month
            
            if prev_month != month:
                # Zakończ poprzedni miesiąc
                if prev_month is not None:
                    month_width = x - month_start_x
                    month_name = self.MONTHS_PL[prev_month]  # Polska nazwa miesiąca
                    year = current_date.year if current_date.month > prev_month else current_date.year - 1
                    
                    self.canvas.create_text(
                        month_start_x + (month_width // 2), 
                        self.header_height // 2 - 25,  # Wyżej, aby uniknąć nakładania
                        text=f"{month_name} {year}",
                        font=("Arial", 9, "bold")
                    )
                
                # Rozpocznij nowy miesiąc
                prev_month = month
                month_start_x = x
            
            # Przejdź do następnego dnia
            current_date += datetime.timedelta(days=1)
        
        # Narysuj ostatni miesiąc
        if prev_month is not None:
            month_width = self.margin_left + (total_days * self.day_width) - month_start_x
            month_name = self.MONTHS_PL[prev_month]  # Polska nazwa miesiąca
            year = current_date.year if current_date.month <= prev_month else current_date.year - 1
            
            self.canvas.create_text(
                month_start_x + (month_width // 2), 
                self.header_height // 2 - 25,
                text=f"{month_name} {year}",
                font=("Arial", 9, "bold")
            )
    
    def _draw_data(self, gantt_data, total_days):
        """Rysuje dane na wykresie"""
        # Dla każdego użytkownika
        for i, user_data in enumerate(gantt_data):
            # Pozycja Y wiersza
            y = self.header_height + (i * self.row_height)
            
            # Etykieta wiersza
            self.canvas.create_text(
                self.margin_left // 2, 
                y + (self.row_height // 2),
                text=user_data["label"],
                font=("Arial", 9)
            )
            
            # Dla każdego zadania
            for task in user_data["tasks"]:
                # Oblicz pozycję X
                start_offset = max(0, (task["start_date"] - self.start_date).days)
                task_duration = (task["end_date"] - task["start_date"]).days + 1
                
                # Ogranicz do widocznego zakresu
                if start_offset < 0:
                    task_duration += start_offset
                    start_offset = 0
                
                if start_offset + task_duration > total_days:
                    task_duration = total_days - start_offset
                
                # Tylko rysuj zadanie, jeśli jest widoczne
                if task_duration > 0:
                    # Pozycja X i szerokość
                    x = self.margin_left + (start_offset * self.day_width)
                    width = task_duration * self.day_width
                    
                    # Wybierz kolor
                    if task["type"] == "Implementation":
                        color = self.COLORS["Implementation"]
                    else:
                        color = self.COLORS["Offer"]
                    
                    # Kolor operacji jeśli jest
                    if "operation" in task:
                        if task["operation"] in self.COLORS:
                            color = self.COLORS[task["operation"]]
                    
                    # Narysuj pasek zadania
                    bar_height = self.row_height - 6
                    self.canvas.create_rectangle(
                        x, y + 3,
                        x + width, y + bar_height + 3,
                        fill=color,
                        outline="white",
                        tags=("task",)
                    )
                    
                    # Dodaj etykietę zadania
                    # Wyświetlaj etykietę tylko jeśli jest wystarczająca szerokość
                    if width > 50:
                        self.canvas.create_text(
                            x + (width // 2), 
                            y + (bar_height // 2) + 3,
                            text=task["label"],
                            fill="black",
                            font=("Arial", 8),
                            width=width - 10,  # Limit szerokości tekstu
                            tags=("task_label",)
                        )