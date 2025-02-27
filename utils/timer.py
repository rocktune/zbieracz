import time
from datetime import datetime
import threading

class TaskTimer:
    """Klasa obsługująca timer do śledzenia czasu zadań"""
    
    def __init__(self, update_callback=None):
        """
        Inicjalizuje timer
        
        Args:
            update_callback (callable, optional): Callback wywoływany po każdej aktualizacji timera
        """
        self.start_time = None
        self.elapsed_seconds = 0
        self.running = False
        self.update_callback = update_callback
        self.timer_thread = None
        self.stop_thread = False
    
    def start(self):
        """Rozpoczyna odliczanie timera"""
        if not self.running:
            self.start_time = datetime.now()
            self.running = True
            self.stop_thread = False
            
            # Uruchom wątek aktualizujący timer
            self.timer_thread = threading.Thread(target=self._update_timer)
            self.timer_thread.daemon = True
            self.timer_thread.start()
    
    def stop(self):
        """Zatrzymuje timer i zwraca czas rozpoczęcia, zakończenia i czas trwania"""
        if not self.running:
            return None, None, 0
        
        # Zatrzymaj wątek i timer
        self.stop_thread = True
        # Poczekaj chwilę, aby wątek się zakończył
        time.sleep(0.1)
        
        # Sprawdź czy start_time istnieje
        if self.start_time is None:
            self.running = False
            self.elapsed_seconds = 0
            return None, None, 0
            
        end_time = datetime.now()
        duration_seconds = int((end_time - self.start_time).total_seconds())
        
        # Zapisz dane
        start_time_str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Resetuj timer
        self.running = False
        self.elapsed_seconds = 0
        start_time_backup = self.start_time
        self.start_time = None
        
        # Zwróć dane o zadaniu
        return start_time_str, end_time_str, duration_seconds
    
    def get_elapsed_time(self):
        """Zwraca aktualny czas timera w formacie HH:MM:SS"""
        if not self.running:
            hours, remainder = divmod(self.elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
    def reset(self):
        """Resetuje timer"""
        if self.running:
            self.stop()
        
        self.elapsed_seconds = 0
        self.start_time = None
        self.running = False
    
    def _update_timer(self):
        """Wątek aktualizujący timer co sekundę"""
        while self.running and not self.stop_thread:
            if self.update_callback:
                self.update_callback(self.get_elapsed_time())
            time.sleep(1)