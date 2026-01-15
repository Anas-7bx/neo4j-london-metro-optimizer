import tkinter as tk
from tkinter import ttk, messagebox
import threading

from routes_basic import fastest_route
from routes_transfers import least_transfer_route
from routes_congestion import find_congestion_aware_route
from routes_avoid_line import route_avoiding_line
from routes_info import list_stations, list_lines, network_stats
from db import close_driver

class RouteOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("London Underground Route Optimizer")
        self.root.geometry("600x700")

        # Data
        self.stations = []
        self.lines = []
        
        # Load data in background
        self.load_data()

        # UI Components
        self.create_widgets()

    def load_data(self):
        def fetch():
            try:
                # Disable inputs while loading
                self.root.after(0, lambda: self.start_combo.config(state="disabled"))
                self.root.after(0, lambda: self.end_combo.config(state="disabled"))
                self.root.after(0, lambda: self.root.title("Loading data..."))

                # Fetch all stations
                station_data = list_stations(limit=1000)
                stations = sorted([s['station'] for s in station_data])
                lines = sorted(list_lines())
                stats = network_stats()
                
                # Update UI safely
                def on_loaded():
                    self.stations = stations
                    self.lines = lines
                    
                    self.start_combo['values'] = self.stations
                    self.end_combo['values'] = self.stations
                    self.avoid_combo['values'] = self.lines
                    
                    self.start_combo.config(state="readonly")
                    self.end_combo.config(state="readonly")
                    
                    if "Paddington" in self.stations: self.start_combo.set("Paddington")
                    if "Stratford" in self.stations: self.end_combo.set("Stratford")

                    self.root.title(f"London Underground Optimizer ({stats['stations']} stations)")
                
                self.root.after(0, on_loaded)

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Connection Error", f"Failed to load data: {e}"))
        
        threading.Thread(target=fetch, daemon=True).start()

    def create_widgets(self):
        # Frame for controls
        control_frame = ttk.LabelFrame(self.root, text="Route Settings", padding="10")
        control_frame.pack(fill="x", padx=10, pady=5)

        # Start Station
        ttk.Label(control_frame, text="Start Station:").grid(row=0, column=0, sticky="w", pady=5)
        self.start_combo = ttk.Combobox(control_frame, values=self.stations, width=30)
        self.start_combo.grid(row=0, column=1, sticky="e", pady=5)
        if "Paddington" in self.stations: self.start_combo.set("Paddington")

        # End Station
        ttk.Label(control_frame, text="Destination:").grid(row=1, column=0, sticky="w", pady=5)
        self.end_combo = ttk.Combobox(control_frame, values=self.stations, width=30)
        self.end_combo.grid(row=1, column=1, sticky="e", pady=5)
        if "Stratford" in self.stations: self.end_combo.set("Stratford")

        # Avoid Line
        ttk.Label(control_frame, text="Avoid Line (Optional):").grid(row=2, column=0, sticky="w", pady=5)
        self.avoid_combo = ttk.Combobox(control_frame, values=self.lines, width=30)
        self.avoid_combo.grid(row=2, column=1, sticky="e", pady=5)

        # Buttons
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="Fastest Route", command=self.run_fastest).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Least Transfers", command=self.run_least_transfers).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Congestion Aware", command=self.run_congestion).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Route Avoiding Line", command=self.run_avoid_line).pack(fill="x", pady=2)

        # Result Area
        result_frame = ttk.LabelFrame(self.root, text="Results", padding="10")
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_text = tk.Text(result_frame, wrap="word", height=20)
        self.result_text.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(result_frame, command=self.result_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.result_text['yscrollcommand'] = scrollbar.set

    def get_inputs(self):
        start = self.start_combo.get()
        end = self.end_combo.get()
        if not start or not end:
            messagebox.showwarning("Input Error", "Please select both start and end stations.")
            return None, None
        return start, end

    def display_result(self, title, data):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"=== {title} ===\n\n")
        
        if not data:
            self.result_text.insert(tk.END, "No route found.\n")
            return

        for k, v in data.items():
            self.result_text.insert(tk.END, f"{k}: {v}\n")
        
        self.result_text.insert(tk.END, "\n----------------\nDONE")

    def run_in_thread(self, task_func, title):
        def wrapper():
            # Disable buttons or show loading
            self.root.after(0, lambda: self.result_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.result_text.insert(tk.END, f"Computing {title}...\n"))
            
            try:
                res = task_func()
                self.root.after(0, lambda: self.display_result(title, res))
            except Exception as ex:
                self.root.after(0, lambda: self.display_result("Error", {"Message": str(ex)}))
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

    def run_fastest(self):
        s, e = self.get_inputs()
        if s:
            self.run_in_thread(lambda: fastest_route(s, e), "Fastest Route")

    def run_least_transfers(self):
        s, e = self.get_inputs()
        if s:
            self.run_in_thread(lambda: least_transfer_route(s, e), "Least Transfers")

    def run_congestion(self):
        s, e = self.get_inputs()
        if s:
            self.run_in_thread(lambda: find_congestion_aware_route(s, e), "Congestion Aware")

    def run_avoid_line(self):
        s, e = self.get_inputs()
        line = self.avoid_combo.get()
        if not line:
             messagebox.showwarning("Input Error", "Please select a line to avoid.")
             return
        
        if s:
             self.run_in_thread(lambda: route_avoiding_line(s, e, line), f"Avoid {line}")

def on_closing():
    close_driver()
    root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RouteOptimizerApp(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
