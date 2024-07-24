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
        wx.Frame.__init__(self, parent, title='Ping Checker', size=(800, 600))

        self.panel = wx.Panel(self)

        # Create grid with rows based on the number of IPs in the file and 3 columns
        self.mygrid = grid.Grid(self.panel)
        with open('ip.txt') as f:
            count = sum(1 for _ in f)
        self.mygrid.CreateGrid(count, 3)
        
        # Set column labels
        self.mygrid.SetColLabelValue(0, "Host")
        self.mygrid.SetColLabelValue(1, "Status")
        self.mygrid.SetColLabelValue(2, "Czas")
        self.mygrid.SetColSize(2, 150)

        # Create second grid for errors
        self.error_grid = grid.Grid(self.panel)
        self.error_grid.CreateGrid(0, 2)
        self.error_grid.SetColLabelValue(0, "Host")
        self.error_grid.SetColLabelValue(1, "Czas")
        self.error_grid.SetColSize(1, 150)

        # Create sizers to manage the layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add grids to sizer
        grid_sizer.Add(self.mygrid, 1, wx.EXPAND)
        grid_sizer.Add(wx.StaticText(self.panel, label="Error Log"), 0, wx.EXPAND | wx.ALL, 5)
        grid_sizer.Add(self.error_grid, 1, wx.EXPAND)
        
        # Add control elements to sizer
        self.email_interval_slider = wx.Slider(self.panel, value=15, minValue=1, maxValue=60, style=wx.SL_LABELS)
        self.email_interval_slider.SetTickFreq(15)
        control_sizer.Add(wx.StaticText(self.panel, label="Email Interval (min): "), 0, wx.ALL, 5)
        control_sizer.Add(self.email_interval_slider, 1, wx.ALL, 5)

        self.log_clear_interval_slider = wx.Slider(self.panel, value=15, minValue=1, maxValue=60, style=wx.SL_LABELS)
        self.log_clear_interval_slider.SetTickFreq(15)
        control_sizer.Add(wx.StaticText(self.panel, label="Log Clear Interval (min): "), 0, wx.ALL, 5)
        control_sizer.Add(self.log_clear_interval_slider, 1, wx.ALL, 5)

        # Add text controls for email configuration
        self.email_sender = wx.TextCtrl(self.panel, value="xbewex@gmail.com")
        self.email_password = wx.TextCtrl(self.panel, value="password", style=wx.TE_PASSWORD)
        self.email_recipient = wx.TextCtrl(self.panel, value="dominikpagowski@gmail.com")
        
        control_sizer.Add(wx.StaticText(self.panel, label="Sender Email: "), 0, wx.ALL, 5)
        control_sizer.Add(self.email_sender, 1, wx.ALL, 5)
        control_sizer.Add(wx.StaticText(self.panel, label="Password: "), 0, wx.ALL, 5)
        control_sizer.Add(self.email_password, 1, wx.ALL, 5)
        control_sizer.Add(wx.StaticText(self.panel, label="Recipient Email: "), 0, wx.ALL, 5)
        control_sizer.Add(self.email_recipient, 1, wx.ALL, 5)
       

        main_sizer.Add(grid_sizer, 1, wx.EXPAND)
        main_sizer.Add(control_sizer, 0, wx.EXPAND)

        self.panel.SetSizer(main_sizer)

        # Initialize timers
        self.ping_timer = wx.Timer(self)
        self.email_timer = wx.Timer(self)
        self.log_clear_timer = wx.Timer(self)

        self.Bind(wx.EVT_TIMER, self.OnPingTimer, self.ping_timer)
        self.Bind(wx.EVT_TIMER, self.OnEmailTimer, self.email_timer)
        self.Bind(wx.EVT_TIMER, self.OnLogClearTimer, self.log_clear_timer)

        self.ping_hosts = self.TxTReader()
        self.host_index = 0

        # Start timers
        self.ping_timer.Start(1000)
        self.email_timer.Start(self.email_interval_slider.GetValue() * 60000)
        self.log_clear_timer.Start(self.log_clear_interval_slider.GetValue() * 60000)

        # Bind slider events
        self.email_interval_slider.Bind(wx.EVT_SLIDER, self.OnEmailIntervalChange)
        self.log_clear_interval_slider.Bind(wx.EVT_SLIDER, self.OnLogClearIntervalChange)

    def OnPingTimer(self, event):
        if self.host_index < len(self.ping_hosts):
            threading.Thread(target=self.check_ping, args=(self.ping_hosts[self.host_index], self.host_index)).start()
            self.host_index += 1
        else:
            self.host_index = 0

    def OnEmailTimer(self, event):
        sender_email = self.email_sender.GetValue()
        sender_password = self.email_password.GetValue()
        recipient_email = self.email_recipient.GetValue()
        subject = self.create_error_subject()
        
        message = self.create_error_report()
        self.send_email(sender_email, sender_password, recipient_email, subject, message)

    def OnLogClearTimer(self, event):
        self.error_grid.ClearGrid()
        print("Error log cleared.")

    def OnEmailIntervalChange(self, event):
        self.email_timer.Start(self.email_interval_slider.GetValue() * 60000)
    
    def OnLogClearIntervalChange(self, event):
        self.log_clear_timer.Start(self.log_clear_interval_slider.GetValue() * 60000)

    def check_ping(self, host, index):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = os.system(f"ping -n 1 {host}")
        status = "Active" if response == 0 else "Error"
        wx.CallAfter(self.update_grid, host, status, current_time, index)

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

    def add_error_log(self, host, current_time):
        current_rows = self.error_grid.GetNumberRows()
        self.error_grid.AppendRows(1)
        self.error_grid.SetCellValue(current_rows, 0, host)
        self.error_grid.SetCellValue(current_rows, 1, current_time)

    def TxTReader(self):
        with open('ip.txt', 'r') as f:
            lines = f.readlines()
        return [line.strip() for line in lines]

    def send_email(self, sender_email, sender_password, recipient_email, subject, message):
        smtp_server = "smtp.gmail.com"
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

    def create_error_report(self):
        # Generate a report from the error log
        num_rows = self.error_grid.GetNumberRows()
        if num_rows == 0:
            return "No errors to report."
        else:
            return "Raport Ping Error"
        
    
    def create_error_subject(self):
        # Generate a report from the error log
        num_rows = self.error_grid.GetNumberRows()
        if num_rows == 0:
            return "No errors to report."
        
        report = "Raport Ping Error:\n\n"
        for row in range(num_rows):
            host = self.error_grid.GetCellValue(row, 0)
            time = self.error_grid.GetCellValue(row, 1)
            report += f"Host: {host}, Czas: {time}\n"
        return report

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None)
        self.frame.Show()
        return True  # Ensure OnInit returns True

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
