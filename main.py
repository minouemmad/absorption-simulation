import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from layer_config import LayerConfig
from plotting import PlotReflectance
from utils import load_settings, save_settings, load_raw_data  # Import modified load_raw_data
import ttkbootstrap as ttkb

class LayerStackApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Layer Stack Configuration")
        
        # Load settings
        self.settings = load_settings()
        
        # File upload button for raw data
        self.raw_data = None
        upload_btn = ttkb.Button(self.root, text="Upload Raw Reflectance Data", command=self.upload_raw_data, bootstyle="primary").grid(row=0, column=3, columnspan=3, pady=10, padx=10, sticky="e")
        # Set up DBR and Metal layers
        self.layer_config = LayerConfig(self.root, self.settings)
        
        # User-defined angle of incidence and polarization
        self.setup_incidence_inputs()
        

        # Plot button for simulated data
        plot_btn = ttkb.Button(self.root, text="Plot Simulated Reflectance", command=self.plot_reflectance, bootstyle="primary").grid(row=17, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

    def setup_incidence_inputs(self):
        tk.Label(self.root, text="Incidence Angle (degrees):").grid(row=14, column=0)
        self.angle_entry = tk.Entry(self.root)
        self.angle_entry.grid(row=14, column=1, columnspan=2)
        self.angle_entry.insert(0, "0")  # Default is normal incidence
        
        tk.Label(self.root, text="Polarization:").grid(row=16, column=0)
        self.polarization_var = tk.StringVar(value="both")
        ttk.Combobox(self.root, textvariable=self.polarization_var, 
                     values=["s", "p", "both"]).grid(row=16, column=1, columnspan=2)

    def upload_raw_data(self):
        # Open file dialog for user to select the raw data file
        file_path = filedialog.askopenfilename(title="Select Raw Reflectance Data File", 
                                               filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")))
        if file_path:
            try:
                self.raw_data = load_raw_data(file_path)
                messagebox.showinfo("Success", "Raw reflectance data loaded successfully.")
                self.plot_raw_data()  # Immediately plot the raw data after loading
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def plot_raw_data(self):
        if self.raw_data is not None:
            plot = PlotReflectance()
            plot.plot_raw_data(self.raw_data)

    def plot_reflectance(self):
        angle = float(self.angle_entry.get())
        polarization = self.polarization_var.get()
        dbr_stack, metal_layers, substrate_layer = self.layer_config.get_layers()
        
        plot = PlotReflectance(dbr_stack, metal_layers, substrate_layer)
        
        # Plot simulated reflectance overlay
        plot.plot_stack(angle, polarization)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = LayerStackApp(root)
        root.mainloop()
    except Exception as e:
        print(f"An error occurred: {e}")
