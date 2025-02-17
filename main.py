import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from layer_config import LayerConfig
from plotting import PlotReflectance
from utils import load_settings, save_settings, load_raw_data
import ttkbootstrap as ttkb
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

class LayerStackApp:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.raw_data = None


        
        # Layer Configuration
        self.layer_config = LayerConfig(self.root, self.settings)
        
        # Incidence Inputs
        self.layer_config.setup_incidence_inputs()
        # Upload Button
        upload_btn = ttkb.Button(self.layer_config.scrollable_frame, text="Upload Raw Reflectance Data", command=self.upload_raw_data, bootstyle="primary")
        upload_btn.grid(row=0, column=5, columnspan=3, pady=10, padx=10, sticky="e")
        # Plot Buttons
        plot_btn = ttkb.Button(self.layer_config.scrollable_frame, text="Plot Simulated Reflectance", command=self.plot_reflectance, bootstyle="primary")
        plot_btn.grid(row=1, column=5, columnspan=3, pady=5, sticky="ew")
        
        plot_efield_btn = ttkb.Button(self.layer_config.scrollable_frame, text="Plot Simulated Electric Field", command=self.plot_electric_field, bootstyle="primary")
        plot_efield_btn.grid(row=2, column=5, columnspan=3, pady=5, sticky="ew")
        
        # Both buttons span 3 columns and are set to expand horizontally
        self.refresh_reflectance_btn = tk.Button(self.layer_config.scrollable_frame, text="Delete Reflectance Plot", command=self.refresh_reflectance)
        self.refresh_reflectance_btn.grid(row=3, column=5, columnspan=1, pady=5, sticky="sew")

        self.refresh_efield_btn = tk.Button(self.layer_config.scrollable_frame, text="Delete Electric Field Plot", command=self.refresh_electric_field)
        self.refresh_efield_btn.grid(row=4, column=5, columnspan=1, pady=5, sticky="sew")
        # Frames for Plots
        self.right_frame = tk.Frame(self.layer_config.scrollable_frame)
        self.right_frame.grid(row=1, column=11, rowspan=10, sticky="nsew")
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 8), gridspec_kw={'hspace': 0.5})

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.setup_plots()
    
    def setup_plots(self):
        """Setup the axes with labels and limits before any plotting occurs."""
        # Reflectance Plot
        self.ax1.set_xticks(np.arange(2, 13, 1))
        self.ax1.set_yticks(np.linspace(0.0, 1.0, 11))
        self.ax1.set_xlim(2.5, 12)
        self.ax1.set_ylim(0.0, 1.0)
        self.ax1.set_xlabel("Wavelength (μm)")
        self.ax1.set_ylabel("Reflectance")
        self.ax1.set_title("Simulated Reflectance")
        self.ax1.grid(alpha=0.2)
        
        # Electric Field Plot
        self.ax2.set_xticks(np.linspace(0, 7, 8))
        self.ax2.set_yscale("log")
        self.ax2.set_yticks(np.logspace(-5, 1, 7))
        self.ax2.set_xlim(0, 7)
        self.ax2.set_xlabel("Depth from the top (μm)")
        self.ax2.set_ylabel("Amplitude")
        self.ax2.set_title("Simulated Electric Field")
        self.ax2.grid(alpha=0.2)

    
    def refresh_reflectance(self):
        """Clears only the reflectance plot."""
        self.ax1.clear()
        self.setup_plots()  # Reset the properties
        self.canvas.draw()

    def refresh_electric_field(self):
        """Clears only the electric field plot."""
        self.ax2.clear()
        self.setup_plots()  # Reset the properties
        self.canvas.draw()

    
    def upload_raw_data(self):
        file_path = filedialog.askopenfilename(title="Select Raw Reflectance Data File", filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")))
        if file_path:
            try:
                self.raw_data = load_raw_data(file_path)
                messagebox.showinfo("Success", "Raw reflectance data loaded successfully.")
                self.plot_raw_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
    
    def plot_raw_data(self):
        if self.raw_data is not None:
            plot = PlotReflectance(right_frame=self.right_frame)
            plot.plot_raw_data(self.raw_data, self.ax1, self.canvas)
            self.canvas.draw()
    
    def plot_reflectance(self):
        angle = float(self.layer_config.angle_entry.get())
        polarization = self.layer_config.polarization_var.get()
        dbr_stack, metal_layers, substrate_layer = self.layer_config.get_layers()
        substrate_thickness = self.layer_config.substrate_thickness.get()
        light_direction = self.layer_config.reverse_light_direction.get()
        
        plot = PlotReflectance(dbr_stack, metal_layers, substrate_layer, substrate_thickness, light_direction, right_frame=self.right_frame)
        plot.plot_stack(angle, polarization, self.ax1, self.canvas)
        self.canvas.draw()
    
    def plot_electric_field(self):
        """Placeholder for electric field plotting logic."""
        dbr_stack, metal_layers, substrate_layer = self.layer_config.get_layers()
        light_direction = self.layer_config.reverse_light_direction.get()
    
        metal_thickness = 0
        dbr_thickness = 0
        substrate_thickness = 0
    
        # Check if substrate thickness should be included
        if self.layer_config.is_finite_substrate.get():
            substrate_thickness = self.layer_config.substrate_thickness.get()
    
        # Fix BooleanVar access by using .get()
        if self.layer_config.mystery_metal_var.get():
            metal_thickness = self.layer_config.mystery_thickness_entry.get()
        else:
            metal_thickness = self.layer_config.metal_thickness_entry.get()
    
        dbr_thickness = self.layer_config.dbr_thickness_entry.get() * self.layer_config.dbr_period_entry.get()
    
        # Ensure numeric conversion (to prevent string operations)
        try:
            metal_thickness = float(metal_thickness)
            substrate_thickness = float(substrate_thickness)
            dbr_thickness = float(dbr_thickness)
        except ValueError:
            raise ValueError("Thickness values must be numeric.")
    
        total_thickness = substrate_thickness + metal_thickness + dbr_thickness
    
        plot = PlotReflectance(dbr_stack, metal_layers, substrate_layer, substrate_thickness, 
                               light_direction, right_frame=self.right_frame, total_thickness=total_thickness)
        
        plot.plot_electric_field_decay(self.ax2, self.canvas)
        self.canvas.draw()

        
if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = LayerStackApp(root)
        root.mainloop()
    except Exception as e:
        print(f"An error occurred: {e}")
