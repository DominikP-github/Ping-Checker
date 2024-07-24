import wx
import wx.grid as grid
import threading
import os
from datetime import datetime

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

        # Set the column width for "Czas" to 150 pixels
        self.mygrid.SetColSize(2, 150)

        # Create second grid for errors
        self.error_grid = grid.Grid(self.panel)
        self.error_grid.CreateGrid(0, 2)
        self.error_grid.SetColLabelValue(0, "Host")
        self.error_grid.SetColLabelValue(1, "Czas")
        self.error_grid.SetColSize(1, 150)

        # Create sizer to manage the layout horizontally
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add grids to sizer
        sizer.Add(self.mygrid, 1, wx.EXPAND)
        sizer.Add(wx.StaticText(self.panel, label="Error Log"), 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.error_grid, 1, wx.EXPAND)
        
        self.panel.SetSizer(sizer)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        self.ping_hosts = self.TxTReader()
        self.host_index = 0

        self.timer.Start(3000)

    def OnTimer(self, event):
        if self.host_index < len(self.ping_hosts):
            threading.Thread(target=self.check_ping, args=(self.ping_hosts[self.host_index], self.host_index)).start()
            self.host_index += 1
        else:
            self.host_index = 0

    def check_ping(self, host, index):
        # Get current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        response = os.system(f"ping -n 1 {host}")
        status = "Active" if response == 0 else "Error"
        wx.CallAfter(self.update_grid, host, status, current_time, index)

    def update_grid(self, host, status, current_time, index):
        self.mygrid.SetCellValue(index, 0, host)
        self.mygrid.SetCellValue(index, 1, status)
        self.mygrid.SetCellValue(index, 2, current_time)

        # Set the background color based on the status
        if status == "Active":
            self.mygrid.SetCellBackgroundColour(index, 1, wx.Colour(0, 255, 0))  # Green for "Active"
        else:
            self.mygrid.SetCellBackgroundColour(index, 1, wx.Colour(255, 0, 0))  # Red for "Error"
            # Add a new row to the error log grid and update it
            self.add_error_log(host, current_time)

        # Refresh the grids to show the updated color
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

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None)
        self.frame.Show()
        return True

# Entry point of the application
if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
