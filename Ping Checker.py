# importowanie bibliotek
import wx
import wx.grid as grid
import threading
import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title='Ping Checker', size=(1600, 900))

        self.panel = wx.Panel(self)

        # Stworzenie zakładki notatek
        self.notebook = wx.Notebook(self.panel)
        
        # Stworzenie zakładki Ping Log
        self.ping_log_panel = wx.Panel(self.notebook)
        self.notebook.AddPage(self.ping_log_panel, "Ping Log")
        
        #Stworzenie zakładki ustawienia
        self.settings_panel = wx.Panel(self.notebook)
        self.notebook.AddPage(self.settings_panel, "Ustawienia")

        #Stworzenie tabeli z trzema zmiennymi i adresami ip
        self.mygrid = grid.Grid(self.ping_log_panel)
        with open('ip.txt') as f:
            count = sum(1 for _ in f)
        self.mygrid.CreateGrid(count, 3)
        
        #Dodanie do tabeli Host,Status i Czas
        self.mygrid.SetColLabelValue(0, "Host")
        self.mygrid.SetColLabelValue(1, "Status")
        self.mygrid.SetColLabelValue(2, "Czas")
        self.mygrid.SetColSize(2, 150)

        #Dodanie do tabeli Error Log Host,Status i Czas
        self.error_grid = grid.Grid(self.ping_log_panel)
        self.error_grid.CreateGrid(0, 2)
        self.error_grid.SetColLabelValue(0, "Host")
        self.error_grid.SetColLabelValue(1, "Czas")
        self.error_grid.SetColSize(1, 150)

        #Dodanie do sizerów wielkości
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        sliders_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        #Dodanie siatki do sizerów
        grid_sizer.Add(self.mygrid, 1, wx.EXPAND)
        grid_sizer.Add(wx.StaticText(self.ping_log_panel, label="Error Log"), 0, wx.EXPAND | wx.ALL, 5)
        grid_sizer.Add(self.error_grid, 1, wx.EXPAND)

        self.ping_log_panel.SetSizer(grid_sizer)

        #Stworzenie pól do opcji i wpisania wartości
        self.smtp_server = wx.TextCtrl(self.settings_panel, value="")
        self.email_sender = wx.TextCtrl(self.settings_panel, value="")
        self.email_password = wx.TextCtrl(self.settings_panel, value="", style=wx.TE_PASSWORD)
        self.email_recipient = wx.TextCtrl(self.settings_panel, value="")

        self.email_interval_slider = wx.Slider(self.settings_panel, value=15, minValue=1, maxValue=60, style=wx.SL_LABELS)
        self.email_interval_slider.SetTickFreq(15)

        self.log_clear_interval_slider = wx.Slider(self.settings_panel, value=15, minValue=1, maxValue=60, style=wx.SL_LABELS)
        self.log_clear_interval_slider.SetTickFreq(15)

        self.log_clear_checkbox = wx.CheckBox(self.settings_panel, label="Włącz czyszczenie Error Log")
        self.log_clear_checkbox.SetValue(True)

        self.ping_size_slider = wx.Slider(self.settings_panel, value=3, minValue=1, maxValue=254, style=wx.SL_LABELS)
        self.ping_size_slider.SetTickFreq(1)

        self.ping_frequency_slider = wx.Slider(self.settings_panel, value=10, minValue=1, maxValue=60, style=wx.SL_LABELS)
        self.ping_frequency_slider.SetTickFreq(1)

        #Dodanie Etykiet do sliders_sizer
        sliders_sizer.Add(wx.StaticText(self.settings_panel, label="Odstep czasy wysyłania maila (min): "), 0, wx.ALL, 5)
        sliders_sizer.Add(self.email_interval_slider, 1, wx.ALL, 5)
        sliders_sizer.Add(wx.StaticText(self.settings_panel, label="Czas do usunięcia Error Log (min): "), 0, wx.ALL, 5)
        sliders_sizer.Add(self.log_clear_interval_slider, 1, wx.ALL, 5)
        sliders_sizer.Add(wx.StaticText(self.settings_panel, label="Ilość adresów w jednej kolejce: "), 0, wx.ALL, 5)
        sliders_sizer.Add(self.ping_size_slider, 1, wx.ALL, 5)
        sliders_sizer.Add(wx.StaticText(self.settings_panel, label="Odstęp czasowy między pingami (min): "), 0, wx.ALL, 5)
        sliders_sizer.Add(self.ping_frequency_slider, 1, wx.ALL, 5)

        settings_sizer = wx.BoxSizer(wx.VERTICAL)

        settings_sizer.Add(wx.StaticText(self.settings_panel, label="Serwer SMTP: "), 0, wx.ALL, 5)
        settings_sizer.Add(self.smtp_server, 0, wx.ALL | wx.EXPAND, 5)
        settings_sizer.Add(wx.StaticText(self.settings_panel, label="Email Z którego ma wysłać wiadomość: "), 0, wx.ALL, 5)
        settings_sizer.Add(self.email_sender, 0, wx.ALL | wx.EXPAND, 5)
        settings_sizer.Add(wx.StaticText(self.settings_panel, label="Hasło do Maila: "), 0, wx.ALL, 5)
        settings_sizer.Add(self.email_password, 0, wx.ALL | wx.EXPAND, 5)
        settings_sizer.Add(wx.StaticText(self.settings_panel, label="Email na który ma wysłać wiadomość: "), 0, wx.ALL, 5)
        settings_sizer.Add(self.email_recipient, 0, wx.ALL | wx.EXPAND, 5)
        settings_sizer.Add(self.log_clear_checkbox, 0, wx.ALL, 5)
        settings_sizer.Add(sliders_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.settings_panel.SetSizer(settings_sizer)

        main_sizer.Add(self.notebook, 1, wx.EXPAND)
        self.panel.SetSizer(main_sizer)

        #Zainicjowanie Czasu
        self.ping_timer = wx.Timer(self)
        self.email_timer = wx.Timer(self)
        self.log_clear_timer = wx.Timer(self)

        self.Bind(wx.EVT_TIMER, self.OnPingTimer, self.ping_timer)
        self.Bind(wx.EVT_TIMER, self.OnEmailTimer, self.email_timer)
        self.Bind(wx.EVT_TIMER, self.OnLogClearTimer, self.log_clear_timer)

        self.ping_hosts = self.TxTReader()
        self.host_index = 0

        #Rozpoczęcie odliczania czasu
        self.ping_timer.Start(1000)
        self.email_timer.Start(self.email_interval_slider.GetValue() * 60000)
        self.log_clear_timer.Start(self.log_clear_interval_slider.GetValue() * 60000)

        #Przypisanie slidera do checkboxa
        self.email_interval_slider.Bind(wx.EVT_SLIDER, self.OnEmailIntervalChange)
        self.log_clear_interval_slider.Bind(wx.EVT_SLIDER, self.OnLogClearIntervalChange)
        self.ping_size_slider.Bind(wx.EVT_SLIDER, self.OnPingSettingsChange)
        self.ping_frequency_slider.Bind(wx.EVT_SLIDER, self.OnPingSettingsChange)
        self.log_clear_checkbox.Bind(wx.EVT_CHECKBOX, self.OnLogClearCheckboxChange)

#Funkcja odstepu pingu 
    def OnPingTimer(self, event):
        ping_size = self.ping_size_slider.GetValue()
        ping_frequency = self.ping_frequency_slider.GetValue() * 60000  # Przekonwertowanie minut na milisekundy
        end_index = min(self.host_index + ping_size, len(self.ping_hosts))

        threads = []
        for index in range(self.host_index, end_index):
            thread = threading.Thread(target=self.check_ping, args=(self.ping_hosts[index], index))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.host_index = end_index
        if self.host_index >= len(self.ping_hosts):
            self.host_index = 0

        self.ping_timer.Start(ping_frequency)

#Funkcja która pobiera wartości z wpisanych pól email
    def OnEmailTimer(self, event):
        smtp_server = self.smtp_server.GetValue() if self.smtp_server.GetValue() else "smtp.gmail.com"
        sender_email = self.email_sender.GetValue()
        sender_password = self.email_password.GetValue()
        recipient_email = self.email_recipient.GetValue()
        subject = self.create_error_subject()
        
        message = self.create_error_report()
        self.send_email(smtp_server, sender_email, sender_password, recipient_email, subject, message)

#Funkcja czyszcząca Error Log
    def OnLogClearTimer(self, event):
        if self.log_clear_checkbox.GetValue():
            self.error_grid.ClearGrid()
            print("Error log cleared.")

#Funkcja zmieniająca minuty na milisekundy na polu 
    def OnEmailIntervalChange(self, event):
        self.email_timer.Start(self.email_interval_slider.GetValue() * 60000)

#Funkcja zmieniająca minuty na milisekundy na polu     
    def OnLogClearIntervalChange(self, event):
        if self.log_clear_checkbox.GetValue():
            self.log_clear_timer.Start(self.log_clear_interval_slider.GetValue() * 60000)

#Funkcja od zmiany ustawień pingu
    def OnPingSettingsChange(self, event):
        pass

#Funkcja wyczyszczenia Error Log  
    def OnLogClearCheckboxChange(self, event):
        if self.log_clear_checkbox.GetValue():
            self.log_clear_timer.Start(self.log_clear_interval_slider.GetValue() * 60000)
        else:
            self.log_clear_timer.Stop()

#Funkcja wysyłająca ping 
    def check_ping(self, host, index):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = os.system(f"ping -n 1 {host}")
        status = "Active" if response == 0 else "Error"
        wx.CallAfter(self.update_grid, host, status, current_time, index)

#Funkcja która aktualnia dane w tabeli
    def update_grid(self, host, status, current_time, index):
        self.mygrid.SetCellValue(index, 0, host)
        self.mygrid.SetCellValue(index, 1, status)
        self.mygrid.SetCellValue(index, 2, current_time)

        if status == "Active":
            self.mygrid.SetCellBackgroundColour(index, 1, wx.Colour(0, 255, 0))
        else:
            self.mygrid.SetCellBackgroundColour(index, 1, wx.Colour(255, 0, 0))
            self.add_error_log(host, current_time)

        self.mygrid.ForceRefresh()
        self.error_grid.ForceRefresh()

#Funkcja Dodanie error Log
    def add_error_log(self, host, current_time):
        current_rows = self.error_grid.GetNumberRows()
        self.error_grid.AppendRows(1)
        self.error_grid.SetCellValue(current_rows, 0, host)
        self.error_grid.SetCellValue(current_rows, 1, current_time)

#Funkcja czytania z pliku 
    def TxTReader(self):
        with open('ip.txt', 'r') as f:
            lines = f.readlines()
        return [line.strip() for line in lines]

#Funkcja do podłączenia się pod serwer pocztowy
    def send_email(self, smtp_server, sender_email, sender_password, recipient_email, subject, message):
        smtp_port = 587

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            print(f"Email wysłany pomyślnie do {recipient_email}")
        except Exception as e:
            print(f"Wystąpił błąd: {e}")

#Fukcja Treść wiadomości maila
    def create_error_report(self):
        num_rows = self.error_grid.GetNumberRows()
        if num_rows == 0:
            return "No errors to report."
        
        report = "Raport Ping Error:\n\n"
        for row in range(num_rows):
            host = self.error_grid.GetCellValue(row, 0)
            time = self.error_grid.GetCellValue(row, 1)
            report += f"Host: {host}, Czas: {time}\n"
        return report
    
    def create_error_subject(self):
        return "Raport Ping Error"
    
#Klasa która uruchamia aplikacje
class MyApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None)
        self.frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
