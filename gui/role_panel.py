import tkinter as tk
from tkinter import ttk, messagebox
from database.models import Role, User

class RolePanel(ttk.Frame):
    """Panel zarządzania rolami"""
    
    # Lista dostępnych uprawnień
    PERMISSIONS = [
        ("admin_panel", "Dostęp do panelu administracyjnego"),
        ("manage_users", "Zarządzanie użytkownikami"),
        ("manage_roles", "Zarządzanie rolami"),
        ("manage_implementations", "Zarządzanie wdrożeniami"),
        ("manage_offers", "Zarządzanie ofertami"),
        ("view_all_tasks", "Podgląd wszystkich zadań"),
        ("export_data", "Eksport danych"),
    ]
    
    def __init__(self, parent, current_user):
        """
        Inicjalizuje panel zarządzania rolami
        
        Args:
            parent (ttk.Frame): Ramka nadrzędna
            current_user (User): Aktualnie zalogowany użytkownik (admin)
        """
        super().__init__(parent, padding=10)
        self.parent = parent
        self.current_user = current_user
        
        # Zmienne
        self.selected_role_id = None
        
        # Stwórz widgety
        self._create_widgets()
        
        # Załaduj dane
        self._load_roles()
        self._load_users()  # Dodanie ładowania użytkowników przy inicjalizacji
    
    def _create_widgets(self):
        """Tworzy widgety panelu zarządzania rolami"""
        # Główny układ
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Lewy panel (lista ról)
        roles_frame = ttk.LabelFrame(left_frame, text="Dostępne role", padding=10)
        roles_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tabela ról
        columns = ["id", "name", "description"]
        self.roles_tree = ttk.Treeview(
            roles_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Nagłówki
        self.roles_tree.heading("id", text="ID")
        self.roles_tree.heading("name", text="Nazwa roli")
        self.roles_tree.heading("description", text="Opis")
        
        # Szerokości kolumn
        self.roles_tree.column("id", width=50, minwidth=50)
        self.roles_tree.column("name", width=150, minwidth=100)
        self.roles_tree.column("description", width=300, minwidth=200)
        
        # Pasek przewijania
        scrollbar = ttk.Scrollbar(roles_frame, orient=tk.VERTICAL, command=self.roles_tree.yview)
        self.roles_tree.configure(yscrollcommand=scrollbar.set)
        
        self.roles_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Przyciski zarządzania rolami - pionowo
        buttons_frame = ttk.Frame(roles_frame)
        buttons_frame.pack(fill=tk.Y, pady=10)

        ttk.Button(
            buttons_frame, 
            text="Dodaj rolę",
            command=self._add_role,
            width=20
        ).pack(pady=5)

        ttk.Button(
            buttons_frame, 
            text="Edytuj rolę",
            command=self._edit_role,
            width=20
        ).pack(pady=5)

        ttk.Button(
            buttons_frame, 
            text="Usuń rolę",
            command=self._delete_role,
            width=20
        ).pack(pady=5)
        
        # Prawy panel (przypisanie ról użytkownikom)
        user_roles_frame = ttk.LabelFrame(right_frame, text="Przypisanie ról użytkownikom", padding=10)
        user_roles_frame.pack(fill=tk.BOTH, expand=True)
        
        # Lista użytkowników
        users_frame = ttk.Frame(user_roles_frame)
        users_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(users_frame, text="Wybierz użytkownika:").pack(anchor=tk.W, pady=(0, 5))
        
        # Lista użytkowników z paskiem przewijania
        users_list_frame = ttk.Frame(users_frame)
        users_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tabela użytkowników
        columns = ["id", "username", "full_name"]
        self.users_tree = ttk.Treeview(
            users_list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Nagłówki
        self.users_tree.heading("id", text="ID")
        self.users_tree.heading("username", text="Nazwa użytkownika")
        self.users_tree.heading("full_name", text="Imię i nazwisko")
        
        # Szerokości kolumn
        self.users_tree.column("id", width=50, minwidth=50)
        self.users_tree.column("username", width=150, minwidth=100)
        self.users_tree.column("full_name", width=200, minwidth=150)
        
        # Pasek przewijania
        user_scrollbar = ttk.Scrollbar(users_list_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=user_scrollbar.set)
        
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        user_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Role użytkownika
        roles_selection_frame = ttk.LabelFrame(user_roles_frame, text="Role użytkownika", padding=10)
        roles_selection_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Kontener na checkboxy ról
        self.roles_checkboxes_frame = ttk.Frame(roles_selection_frame)
        self.roles_checkboxes_frame.pack(fill=tk.BOTH, expand=True)
        
        # Przyciski zapisywania
        save_frame = ttk.Frame(user_roles_frame)
        save_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            save_frame, 
            text="Zapisz role użytkownika",
            command=self._save_user_roles,
            width=20
        ).pack(side=tk.RIGHT, padx=5)
        
        # Zdarzenia
        self.roles_tree.bind("<<TreeviewSelect>>", self._on_role_select)
        self.users_tree.bind("<<TreeviewSelect>>", self._on_user_select)
        
        # Zmienne dla checkboxów ról
        self.roles_vars = {}
        self.selected_user_id = None
    
    def _load_roles(self):
        """Ładuje role do tabeli"""
        # Wyczyść istniejące role
        for item in self.roles_tree.get_children():
            self.roles_tree.delete(item)
        
        # Pobierz role
        roles = Role.get_all_roles()
        
        # Dodaj role do tabeli
        for role in roles:
            values = [
                role.id,
                role.name,
                role.description
            ]
            
            self.roles_tree.insert("", "end", values=values)
    
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
                f"{user.first_name} {user.last_name}"
            ]
            
            self.users_tree.insert("", "end", values=values)
    
    def _update_role_checkboxes(self):
        """Aktualizuje checkboxy ról dla wybranego użytkownika"""
        # Wyczyść istniejące checkboxy
        for widget in self.roles_checkboxes_frame.winfo_children():
            widget.destroy()
        
        # Jeśli nie wybrano użytkownika, nie rób nic
        if not self.selected_user_id:
            return
        
        # Pobierz role użytkownika
        user = User.get_by_id(self.selected_user_id)
        if not user:
            return
            
        user_roles = user.get_roles()
        user_role_ids = [role.id for role in user_roles]
        
        # Pobierz wszystkie dostępne role
        all_roles = Role.get_all_roles()
        
        # Resetuj zmienne
        self.roles_vars = {}
        
        # Dodaj checkbox dla każdej roli
        for i, role in enumerate(all_roles):
            var = tk.BooleanVar(value=(role.id in user_role_ids))
            self.roles_vars[role.id] = var
            
            ttk.Checkbutton(
                self.roles_checkboxes_frame,
                text=f"{role.name} - {role.description}",
                variable=var
            ).grid(row=i, column=0, sticky=tk.W, pady=2)
    
    def _on_role_select(self, event):
        """Obsługuje wybór roli z tabeli"""
        selection = self.roles_tree.selection()
        if selection:
            item = selection[0]
            values = self.roles_tree.item(item, "values")
            self.selected_role_id = int(values[0])
    
    def _on_user_select(self, event):
        """Obsługuje wybór użytkownika z tabeli"""
        selection = self.users_tree.selection()
        if selection:
            item = selection[0]
            values = self.users_tree.item(item, "values")
            self.selected_user_id = int(values[0])
            self._update_role_checkboxes()
    
    def _add_role(self):
        """Dodaje nową rolę"""
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title("Dodaj rolę")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formularz
        ttk.Label(main_frame, text="Nazwa roli:").pack(anchor=tk.W, pady=(10, 2))
        name_entry = ttk.Entry(main_frame, width=30)
        name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Opis:").pack(anchor=tk.W, pady=(5, 2))
        description_entry = ttk.Entry(main_frame, width=30)
        description_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Uprawnienia
        permissions_frame = ttk.LabelFrame(main_frame, text="Uprawnienia", padding=10)
        permissions_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Zmienne dla uprawnień
        permission_vars = {}
        
        # Dodaj checkbox dla każdego uprawnienia
        for i, (perm_name, perm_label) in enumerate(self.PERMISSIONS):
            var = tk.BooleanVar(value=False)
            permission_vars[perm_name] = var
            
            ttk.Checkbutton(
                permissions_frame,
                text=perm_label,
                variable=var
            ).pack(anchor=tk.W, pady=2)
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=lambda: self._save_new_role(
                dialog,
                name_entry.get().strip(),
                description_entry.get().strip(),
                permission_vars
            )
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _save_new_role(self, dialog, name, description, permission_vars):
        """Zapisuje nową rolę"""
        # Sprawdź czy nazwa jest wprowadzona
        if not name:
            messagebox.showerror("Błąd", "Nazwa roli nie może być pusta.")
            return
        
        # Sprawdź czy rola o takiej nazwie już istnieje
        existing_role = Role.get_by_name(name)
        if existing_role:
            messagebox.showerror("Błąd", f"Rola o nazwie '{name}' już istnieje.")
            return
        
        # Zbierz uprawnienia
        permissions = {
            perm_name: var.get() for perm_name, var in permission_vars.items()
        }
        
        # Utwórz nową rolę
        role = Role(
            name=name,
            description=description,
            permissions=permissions
        )
        
        # Zapisz rolę
        role.save()
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę ról
        self._load_roles()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            f"Rola '{name}' została dodana."
        )
    
    def _edit_role(self):
        """Edytuje istniejącą rolę"""
        if not self.selected_role_id:
            messagebox.showinfo("Informacja", "Wybierz rolę do edycji.")
            return
        
        # Pobierz rolę
        role = Role.get_by_id(self.selected_role_id)
        
        if not role:
            messagebox.showerror("Błąd", "Nie znaleziono roli.")
            return
        
        # Utwórz okno dialogowe
        dialog = tk.Toplevel(self)
        dialog.title(f"Edycja roli: {role.name}")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Ramka
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Formularz
        ttk.Label(main_frame, text="Nazwa roli:").pack(anchor=tk.W, pady=(10, 2))
        name_entry = ttk.Entry(main_frame, width=30)
        name_entry.insert(0, role.name)
        name_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(main_frame, text="Opis:").pack(anchor=tk.W, pady=(5, 2))
        description_entry = ttk.Entry(main_frame, width=30)
        description_entry.insert(0, role.description or "")
        description_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Uprawnienia
        permissions_frame = ttk.LabelFrame(main_frame, text="Uprawnienia", padding=10)
        permissions_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Zmienne dla uprawnień
        permission_vars = {}
        
        # Dodaj checkbox dla każdego uprawnienia
        for i, (perm_name, perm_label) in enumerate(self.PERMISSIONS):
            var = tk.BooleanVar(value=role.permissions.get(perm_name, False))
            permission_vars[perm_name] = var
            
            ttk.Checkbutton(
                permissions_frame,
                text=perm_label,
                variable=var
            ).pack(anchor=tk.W, pady=2)
        
        # Przyciski
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Zapisz",
            command=lambda: self._save_edited_role(
                dialog,
                role,
                name_entry.get().strip(),
                description_entry.get().strip(),
                permission_vars
            )
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Anuluj",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _save_edited_role(self, dialog, role, name, description, permission_vars):
        """Zapisuje edytowaną rolę"""
        # Sprawdź czy nazwa jest wprowadzona
        if not name:
            messagebox.showerror("Błąd", "Nazwa roli nie może być pusta.")
            return
        
        # Sprawdź czy rola o takiej nazwie już istnieje (ale nie jest to ta sama rola)
        existing_role = Role.get_by_name(name)
        if existing_role and existing_role.id != role.id:
            messagebox.showerror("Błąd", f"Rola o nazwie '{name}' już istnieje.")
            return
        
        # Zbierz uprawnienia
        permissions = {
            perm_name: var.get() for perm_name, var in permission_vars.items()
        }
        
        # Aktualizuj rolę
        role.name = name
        role.description = description
        role.permissions = permissions
        
        # Zapisz rolę
        role.save()
        
        # Zamknij okno dialogowe
        dialog.destroy()
        
        # Odśwież listę ról
        self._load_roles()
        
        # Zaktualizuj checkboxy ról jeśli potrzeba
        if self.selected_user_id:
            self._update_role_checkboxes()
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            f"Rola '{name}' została zaktualizowana."
        )
    
    def _delete_role(self):
        """Usuwa rolę"""
        if not self.selected_role_id:
            messagebox.showinfo("Informacja", "Wybierz rolę do usunięcia.")
            return
        
        # Pobierz rolę
        role = Role.get_by_id(self.selected_role_id)
        
        if not role:
            messagebox.showerror("Błąd", "Nie znaleziono roli.")
            return
        
        # Potwierdź usunięcie
        if not messagebox.askyesno(
            "Potwierdzenie",
            f"Czy na pewno chcesz usunąć rolę '{role.name}'?\n\n"
            f"UWAGA: Ta operacja usunie tę rolę od wszystkich użytkowników."
        ):
            return
        
        # Usuń rolę
        if role.delete():
            # Odśwież listę ról
            self._load_roles()
            
            # Zaktualizuj checkboxy ról jeśli potrzeba
            if self.selected_user_id:
                self._update_role_checkboxes()
            
            # Wyczyść wybór
            self.selected_role_id = None
            
            # Wyświetl komunikat
            messagebox.showinfo(
                "Sukces", 
                f"Rola '{role.name}' została usunięta."
            )
        else:
            messagebox.showerror(
                "Błąd", 
                "Nie udało się usunąć roli."
            )
    
    def _save_user_roles(self):
        """Zapisuje role przypisane do użytkownika"""
        if not self.selected_user_id:
            messagebox.showinfo("Informacja", "Wybierz użytkownika, któremu chcesz przypisać role.")
            return
        
        # Pobierz użytkownika
        user = User.get_by_id(self.selected_user_id)
        
        if not user:
            messagebox.showerror("Błąd", "Nie znaleziono użytkownika.")
            return
        
        # Zbierz zaznaczone role
        selected_role_ids = [
            role_id for role_id, var in self.roles_vars.items() if var.get()
        ]
        
        # Zapisz przypisanie ról
        user.set_roles(selected_role_ids)
        
        # Wyświetl komunikat
        messagebox.showinfo(
            "Sukces", 
            f"Role użytkownika {user.username} zostały zaktualizowane."
        )