#main.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from layer_config import LayerConfig
from plotting import PlotReflectance
from utils import load_settings, save_settings, load_raw_data  # Import modified load_raw_data
import ttkbootstrap as ttkb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

class LayerStackApp:
    def __init__(self, root):
        self.root = root

        # Load settings
        self.settings = load_settings()
        
        # File upload button for raw data
        self.raw_data = None
        upload_btn = ttkb.Button(self.root, text="Upload Raw Reflectance Data", command=self.upload_raw_data, bootstyle="primary")
        upload_btn.grid(row=0, column=5, columnspan=3, pady=10, padx=10, sticky="e")

        # Set up DBR and Metal layers
        self.layer_config = LayerConfig(self.root, self.settings)
        
        # User-defined angle of incidence and polarization
        self.setup_incidence_inputs()
        
        # Plot button for simulated data
        plot_btn = ttkb.Button(self.root, text="Plot Simulated Reflectance", command=self.plot_reflectance, bootstyle="primary")
        plot_btn.grid(row=1, column=5, columnspan=3, pady=10, padx=10, sticky="ew")

        # Create a button to refresh the canvas
        self.refresh_button = tk.Button(root, text="Refresh Canvas", command=self.refresh_canvas)
        self.refresh_button.grid(row=10, column=10, columnspan=2, sticky="ew")

        # Initialize Matplotlib figure and canvas once
        self.right_frame = tk.Frame(self.root)
        self.right_frame.grid(row=0, column=11, rowspan=10, sticky="nsew")

        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)

        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Set initial plot structure (empty)
        self.setup_plot()

    def setup_plot(self):
        """Setup the axes with labels and limits before any plotting occurs."""
        self.ax.set_xticks(np.arange(2, 13, 1))
        self.ax.set_yticks(np.linspace(0.0, 1.0, 11))
        self.ax.set_xlim(2.5, 12)
        self.ax.set_ylim(0.0, 1.0)
        self.ax.set_xlabel("Wavelength (μm)")
        self.ax.set_ylabel("Reflectance")
        self.ax.set_title("Simulated Reflectance")
        self.ax.grid(alpha=0.2)

    def refresh_canvas(self):
        """Clears all existing plots and resets the figure."""
        self.ax.clear()
        self.setup_plot()  # Reset axes labels and limits
        self.canvas.draw()  # Redraw the canvas to reflect changess

    def setup_incidence_inputs(self):
        tk.Label(self.root, text="Incidence Angle (degrees):").grid(row=18, column=0)
        self.angle_entry = tk.Entry(self.root)
        self.angle_entry.grid(row=18, column=1, columnspan=2)
        self.angle_entry.insert(0, "0")  # Default is normal incidence
        
        tk.Label(self.root, text="Polarization:").grid(row=19, column=0)
        self.polarization_var = tk.StringVar(value="s")
        ttk.Combobox(self.root, textvariable=self.polarization_var, 
                     values=["s", "p"]).grid(row=19, column=1, columnspan=2)

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
            plot = PlotReflectance(right_frame=self.right_frame)
            plot.plot_raw_data(self.raw_data, self.ax, self.canvas)  # Ensure your function accepts ax
            self.canvas.draw()

    def plot_reflectance(self):
        angle = float(self.angle_entry.get())
        polarization = self.polarization_var.get()
        dbr_stack, metal_layers, substrate_layer = self.layer_config.get_layers()
        substrate_thickness = self.layer_config.substrate_thickness.get()
        light_direction = self.layer_config.reverse_light_direction.get()
        
        plot = PlotReflectance(dbr_stack, metal_layers, substrate_layer, substrate_thickness, light_direction, right_frame=self.right_frame)
        
        plot.plot_stack(angle, polarization, self.ax, self.canvas) 
        self.canvas.draw()
        

if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = LayerStackApp(root)
        root.mainloop()
    except Exception as e:
        print(f"An error occurred: {e}")
