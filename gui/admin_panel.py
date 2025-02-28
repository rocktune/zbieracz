import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database.models import Role, User
from database.db_manager import DBManager
from utils.auth import AuthManager

class AdminPanel(ttk.Frame):
    """Panel administracyjny"""
    
    def __init__(self, parent, current_user):
        """
        Inicjalizuje panel administracyjny
        
        Args:
            parent (ttk.Frame): Ramka nadrzędna
            current_user (User): Aktualnie zalogowany użytkownik (admin)
        """
        super().__init__(parent, padding=10)
        self.parent = parent
        self.current_user = current_user
        self.auth_manager = AuthManager()
        self.db_manager = DBManager()
        
        # Zmienne
        self.selected_user_id = None
        
        # Stwórz widgety
        self._create_widgets()
        
        # Załaduj dane
        self._load_users()
    
    def _create_widgets(self):
        """Tworzy widgety panelu administracyjnego"""
        # Główny układ
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Powiadomienia o resetowaniu haseł
        reset_requests = User.get_users_with_reset_requests()
        if reset_requests:
            notifications_frame = ttk.LabelFrame(left_frame, text="Powiadomienia", padding=10)
            notifications_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(
                notifications_frame, 
                text=f"Prośby o reset hasła: {len(reset_requests)}",
                font=("Arial", 10, "bold"),
                foreground="red"
            ).pack(anchor="w", pady=(0, 5))
            
            for i, user in enumerate(reset_requests[:3]):  # Pokaż max 3 prośby
                user_frame = ttk.Frame(notifications_frame)
                user_frame.pack(fill=tk.X, pady=2)
                
                ttk.Label(
                    user_frame, 
                    text=f"{user.first_name} {user.last_name} ({user.username})"
                ).pack(side=tk.LEFT)
                
                ttk.Button(
                    user_frame, 
                    text="Resetuj hasło",
                    command=lambda u=user: self._reset_user_password(u.id)
                ).pack(side=tk.RIGHT)
            
            if len(reset_requests) > 3:
                ttk.Label(
                    notifications_frame, 
                    text=f"...i {len(reset_requests) - 3} więcej"
                ).pack(anchor="w", pady=(5, 0))
        
        # Lewy panel (lista użytkowników)
        users_frame = ttk.LabelFrame(left_frame, text="Użytkownicy", padding=10)
        users_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tabela użytkowników
        columns = ["id", "username", "full_name", "is_admin"]
        self.users_tree = ttk.Treeview(
            users_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Nagłówki
        self.users_tree.heading("id", text="ID")
        self.users_tree.heading("username", text="Nazwa użytkownika")
        self.users_tree.heading("full_name", text="Imię i nazwisko")
        self.users_tree.heading("is_admin", text="Administrator")
        
        # Szerokości kolumn
        self.users_tree.column("id", width=50, minwidth=50)
        self.users_tree.column("username", width=150, minwidth=100)
        self.users_tree.column("full_name", width=200, minwidth=150)
        self.users_tree.column("is_admin", width=100, minwidth=100)
        
        # Pasek przewijania
        scrollbar = ttk.Scrollbar(users_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Przyciski zarządzania użytkownikami - pionowo
        buttons_frame = ttk.Frame(users_frame)
        buttons_frame.pack(fill=tk.Y, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Dodaj użytkownika",
            command=self._add_user,
            width=20
        ).pack(pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Edytuj użytkownika",
            command=self._edit_user,
            width=20
        ).pack(pady=5)
        
        ttk.Button(
            buttons_frame, 
            text="Usuń użytkownika",
            command=self._delete_user,
            width=20
        ).pack(pady=5)
        
        # Prawy panel (ustawienia)
        settings_frame = ttk.LabelFrame(right_frame, text="Ustawienia", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Ścieżka do bazy danych
        ttk.Label(settings_frame, text="Ścieżka do bazy danych:").pack(anchor=tk.W, pady=(10, 5))
        
        db_path_frame = ttk.Frame(settings_frame)
        db_path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.db_path_entry = ttk.Entry(db_path_frame, width=40)
        self.db_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.db_path_entry.insert(0, self.db_manager.db_path)
        
        ttk.Button(
            db_path_frame, 
            text="Zmień...",
            command=self._change_db_path
        ).pack(side=tk.RIGHT)
        
        # Resetowanie hasła
        password_frame = ttk.LabelFrame(settings_frame, text="Resetowanie hasła", padding=10)
        password_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(password_frame, text="Nowe hasło:").pack(anchor=tk.W, pady=(0, 5))
        
        self.new_password_entry = ttk.Entry(password_frame, show="*", width=30)
        self.new_password_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(password_frame, text="Powtórz hasło:").pack(anchor=tk.W, pady=(0, 5))
        
        self.confirm_password_entry = ttk.Entry(password_frame, show="*", width=30)
        self.confirm_password_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(
            password_frame, 
            text="Resetuj hasło użytkownika",
            command=self._reset_password
        ).pack(pady=10)
        
        # Zdarzenia
        self.users_tree.bind("<<TreeviewSelect>>", self._on_user_select)
    
    def _load_users(self):
        """Ładuje użytkowników do tabeli"""
        # Wyczyść istniejących użytkowników
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Pobierz użytkowników
        users = User.get_all_users()
        
        # Dodaj użytkowników do tabeli
        for user in users:
            values = [
                user.id,
                user.username,
                f"{user.first_name} {user.last_name}",
                "Tak" if user.is_admin else "Nie"
            ]
            
            item = self.users_tree.insert("", "end", values=values)
            
            # Zaznacz użytkowników z prośbą o reset hasła na czerwono
            if user.reset_requested:
                self.users_tree.item(item, tags=("reset_requested",))
        
        # Utwórz tag dla zaznaczenia
        self.users_tree.tag_configure("reset_requested", background="#FFCCCC")
    
    def _on_user_select(self, event):
        """Obsługuje wybór użytkownika z tabeli"""
        selection = self.users_tree.selection()
        if selection:
            item = selection[0]
            values = self.users_tree.item(item, "values")
            self.selected_user_id = int(values[0])
    
    def _add_user(self):
        """Dodaje nowego użytkownika"""
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title("Dodaj użytkownika")
        dialog.geometry("500x450")  # Zwiększona wysokość na role
        dialog.transient(self)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formularz
        ttk.Label(main_frame, text="Nazwa użytkownika:").pack(anchor=tk.W, pady=(10, 2))
        username_entry = ttk.Entry(main_frame, width=30)
        username_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Imię:").pack(anchor=tk.W, pady=(5, 2))
        first_name_entry = ttk.Entry(main_frame, width=30)
        first_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Nazwisko:").pack(anchor=tk.W, pady=(5, 2))
        last_name_entry = ttk.Entry(main_frame, width=30)
        last_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Hasło:").pack(anchor=tk.W, pady=(5, 2))
        password_entry = ttk.Entry(main_frame, width=30, show="*")
        password_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Powtórz hasło:").pack(anchor=tk.W, pady=(5, 2))
        confirm_password_entry = ttk.Entry(main_frame, width=30, show="*")
        confirm_password_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Administrator
        is_admin_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame,
            text="Administrator",
            variable=is_admin_var
        ).pack(anchor=tk.W, pady=(5, 10))
        
        # Role użytkownika
        roles_frame = ttk.LabelFrame(main_frame, text="Role użytkownika", padding=10)
        roles_frame.pack(fill=tk.X, pady=(5, 10))
        
        # Pobierz wszystkie role
        roles = Role.get_all_roles()
        
        # Zmienne dla checkboxów ról
        role_vars = {}
        
        # Dodaj checkbox dla każdej roli
        for i, role in enumerate(roles):
            var = tk.BooleanVar(value=False)
            role_vars[role.id] = var
            
            ttk.Checkbutton(
                roles_frame,
                text=f"{role.name}",
                variable=var
            ).pack(anchor=tk.W, pady=2)
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=lambda: self._save_new_user(
                dialog,
                username_entry.get().strip(),
                first_name_entry.get().strip(),
                last_name_entry.get().strip(),
                password_entry.get(),
                confirm_password_entry.get(),
                is_admin_var.get(),
                role_vars
            )
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _save_new_user(self, dialog, username, first_name, last_name, password, confirm_password, is_admin, role_vars):
        """Zapisuje nowego użytkownika"""
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
        
        # Pobierz wybrane role
        selected_role_ids = [
            role_id for role_id, var in role_vars.items() if var.get()
        ]
        
        # Próba rejestracji
        user = self.auth_manager.register_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_admin=is_admin
        )
        
        if user:
            # Przypisz role do użytkownika
            if selected_role_ids:
                user.set_roles(selected_role_ids)
            
            # Zamknij okno dialogowe
            dialog.destroy()
            
            # Odśwież listę użytkowników
            self._load_users()
            
            # Wyświetl komunikat
            messagebox.showinfo(
                "Sukces", 
                f"Użytkownik {username} został dodany."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                "Użytkownik o podanej nazwie już istnieje."
            )

    def _edit_user(self):
        """Edytuje istniejącego użytkownika"""
        if not self.selected_user_id:
            messagebox.showinfo("Informacja", "Wybierz użytkownika do edycji.")
            return
        
        # Pobierz użytkownika
        user = User.get_by_id(self.selected_user_id)
        
        if not user:
            messagebox.showerror("Błąd", "Nie znaleziono użytkownika.")
            return
        
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title(f"Edycja użytkownika: {user.username}")
        dialog.geometry("500x400")  # Zwiększona wysokość na role
        dialog.transient(self)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formularz
        ttk.Label(main_frame, text="Nazwa użytkownika:").pack(anchor=tk.W, pady=(10, 2))
        username_entry = ttk.Entry(main_frame, width=30)
        username_entry.insert(0, user.username)
        username_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Imię:").pack(anchor=tk.W, pady=(5, 2))
        first_name_entry = ttk.Entry(main_frame, width=30)
        first_name_entry.insert(0, user.first_name)
        first_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Nazwisko:").pack(anchor=tk.W, pady=(5, 2))
        last_name_entry = ttk.Entry(main_frame, width=30)
        last_name_entry.insert(0, user.last_name)
        last_name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Administrator
        is_admin_var = tk.BooleanVar(value=user.is_admin)
        admin_check = ttk.Checkbutton(
            main_frame,
            text="Administrator",
            variable=is_admin_var
        )
        admin_check.pack(anchor=tk.W, pady=(5, 10))
        
        # Zablokuj zmianę uprawnień dla samego siebie
        if user.id == self.current_user.id:
            admin_check.configure(state=tk.DISABLED)
        
        # Role użytkownika
        roles_frame = ttk.LabelFrame(main_frame, text="Role użytkownika", padding=10)
        roles_frame.pack(fill=tk.X, pady=(5, 10))
        
        # Pobierz wszystkie role
        all_roles = Role.get_all_roles()
        
        # Pobierz role użytkownika
        user_roles = user.get_roles()
        user_role_ids = [role.id for role in user_roles]
        
        # Zmienne dla checkboxów ról
        role_vars = {}
        
        # Dodaj checkbox dla każdej roli
        for i, role in enumerate(all_roles):
            var = tk.BooleanVar(value=(role.id in user_role_ids))
            role_vars[role.id] = var
            
            ttk.Checkbutton(
                roles_frame,
                text=f"{role.name}",
                variable=var
            ).pack(anchor=tk.W, pady=2)
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=lambda: self._save_edited_user(
                dialog,
                user,
                username_entry.get().strip(),
                first_name_entry.get().strip(),
                last_name_entry.get().strip(),
                is_admin_var.get(),
                role_vars
            )
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _save_edited_user(self, dialog, user, username, first_name, last_name, is_admin, role_vars):
        """Zapisuje edytowanego użytkownika"""
        # Sprawdź czy wszystkie pola są wypełnione
        if not (username and first_name and last_name):
            messagebox.showerror("Błąd", "Wszystkie pola muszą być wypełnione.")
            return
        
        # Aktualizuj użytkownika
        original_username = user.username
        
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        
        # Nie pozwól odebrać sobie uprawnień administratora
        if user.id == self.current_user.id:
            user.is_admin = True
        else:
            user.is_admin = is_admin
        
        # Pobierz wybrane role
        selected_role_ids = [
            role_id for role_id, var in role_vars.items() if var.get()
        ]
        
        try:
            # Zapisz użytkownika
            user.save()
            
            # Przypisz role do użytkownika
            user.set_roles(selected_role_ids)
            
            # Zamknij okno dialogowe
            dialog.destroy()
            
            # Odśwież listę użytkowników
            self._load_users()
            
            # Wyświetl komunikat
            messagebox.showinfo(
                "Sukces", 
                f"Użytkownik {original_username} został zaktualizowany."
            )
        except Exception as e:
            messagebox.showerror(
                "Błąd", 
                f"Nie udało się zaktualizować użytkownika: {str(e)}"
            )
        
    def _delete_user(self):
        """Usuwa użytkownika"""
        if not self.selected_user_id:
            messagebox.showinfo("Informacja", "Wybierz użytkownika do usunięcia.")
            return
        
        # Pobierz użytkownika
        user = User.get_by_id(self.selected_user_id)
        
        if not user:
            messagebox.showerror("Błąd", "Nie znaleziono użytkownika.")
            return
        
        # Nie pozwól usunąć samego siebie
        if user.id == self.current_user.id:
            messagebox.showerror("Błąd", "Nie możesz usunąć swojego konta.")
            return
        
        # Potwierdź usunięcie
        if not messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć użytkownika {user.username}?"
        ):
            return
        
        # Usuń użytkownika
        if user.delete():
            # Odśwież listę użytkowników
            self._load_users()
            
            # Wyczyść wybór
            self.selected_user_id = None
            
            # Wyświetl komunikat
            messagebox.showinfo(
                "Sukces", 
                f"Użytkownik {user.username} został usunięty."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                "Nie udało się usunąć użytkownika."
            )
    
    def _reset_password(self):
        """Resetuje hasło użytkownika"""
        if not self.selected_user_id:
            messagebox.showinfo("Informacja", "Wybierz użytkownika, którego hasło chcesz zresetować.")
            return
        
        # Pobierz użytkownika
        user = User.get_by_id(self.selected_user_id)
        
        if not user:
            messagebox.showerror("Błąd", "Nie znaleziono użytkownika.")
            return
        
        # Pobierz hasła
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
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
        
        # Resetuj hasło
        result = self.auth_manager.reset_password(user.id, new_password)
        if result:
            # Wyczyść pola
            self.new_password_entry.delete(0, tk.END)
            self.confirm_password_entry.delete(0, tk.END)
            
            # Odśwież listę użytkowników
            self._load_users()
            
            # Wyświetl komunikat
            messagebox.showinfo(
                "Sukces", 
                f"Hasło użytkownika {user.username} zostało zresetowane. "
                f"Przy następnym logowaniu użytkownik będzie musiał zmienić hasło."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                "Nie udało się zresetować hasła."
            )
            
    def _reset_user_password(self, user_id):
        """Resetuje hasło użytkownika z prośbą o reset"""
        # Pobierz użytkownika
        user = User.get_by_id(user_id)
        
        if not user:
            messagebox.showerror("Błąd", "Nie znaleziono użytkownika.")
            return
        
        # Potwierdź reset
        if not messagebox.askyesno(
            "Potwierdzenie", 
            f"Czy na pewno chcesz zresetować hasło użytkownika {user.first_name} {user.last_name}?"
        ):
            return
        
        # Resetuj hasło (generuj tymczasowe)
        result = self.auth_manager.reset_password(user.id)
        
        if isinstance(result, tuple) and result[0]:
            # Odśwież listę użytkowników
            self._load_users()
            
            # Pokaż tymczasowe hasło
            temp_password = result[1]
            messagebox.showinfo(
                "Hasło zresetowane", 
                f"Hasło użytkownika {user.username} zostało zresetowane.\n\n"
                f"Tymczasowe hasło: {temp_password}\n\n"
                f"Przy następnym logowaniu użytkownik będzie musiał zmienić hasło."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                "Nie udało się zresetować hasła."
            )
    
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
            # Aktualizuj ścieżkę
            self.db_manager.update_db_path(file_path)
            
            # Aktualizuj pole tekstowe
            self.db_path_entry.delete(0, tk.END)
            self.db_path_entry.insert(0, file_path)
            
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