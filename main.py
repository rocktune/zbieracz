import tkinter as tk
from tkinter import messagebox
import os
import sys

# Dodaj katalog główny projektu do ścieżek Pythona
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from database.models import User
from gui.login import LoginWindow
from gui.main_window import MainWindow

def start_application():
    """Uruchamia aplikację od ekranu logowania"""
    root = tk.Tk()
    
    # Zarejestruj zmienną globalną do śledzenia wszystkich okien
    global all_windows
    all_windows = [root]
    
    # Utwórz okno logowania
    login_window = LoginWindow(root, on_login_success=on_login_success)
    
    # Obsługa zamykania całej aplikacji
    root.protocol("WM_DELETE_WINDOW", lambda: close_application())
    
    # Uruchom pętlę główną
    root.mainloop()

def on_login_success(user):
    """
    Callback wywoływany po udanym logowaniu
    
    Args:
        user (User): Zalogowany użytkownik
    """
    global all_windows
    
    # Zamknij okno logowania
    all_windows[0].withdraw()
    
    # Utwórz nowe główne okno
    main_window = tk.Toplevel(all_windows[0])
    
    # Wyczyść poprzednie okna, poza root i nowym głównym oknem
    for window in all_windows[1:]:
        try:
            window.destroy()
        except:
            pass
    
    # Zresetuj listę okien
    all_windows = [all_windows[0], main_window]
    
    # Obsługa zamykania
    main_window.protocol("WM_DELETE_WINDOW", lambda: close_application())
    
    # Inicjalizuj główne okno
    app = MainWindow(main_window, user)

def close_application():
    """Zamyka wszystkie okna i kończy aplikację"""
    if messagebox.askyesno("Zamykanie aplikacji", "Czy na pewno chcesz zamknąć aplikację?"):
        global all_windows
        
        # Zamknij wszystkie okna
        for window in all_windows:
            try:
                window.destroy()
            except:
                pass
        
        # Zakończ proces
        import sys
        sys.exit(0)

if __name__ == "__main__":
    # Inicjalizuj tabele w bazie danych i dokonaj migracji jeśli potrzeba
    User.create_tables()
    Task = getattr(__import__('database.models', fromlist=['Task']), 'Task')
    Implementation = getattr(__import__('database.models', fromlist=['Implementation']), 'Implementation')
    Offer = getattr(__import__('database.models', fromlist=['Offer']), 'Offer')
    
    Task.create_tables()
    Implementation.create_tables()
    Offer.create_tables()
    
    # Uruchom aplikację
    start_application()