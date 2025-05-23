# main.py - Updated with better layout and callbacks
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
        
        # Initialize Layer Configuration
        self.layer_config = LayerConfig(self.root, self.settings)
        
        # Set up callbacks
        self.layer_config.on_upload_raw_data = self.upload_raw_data
        self.layer_config.on_plot_reflectance = self.plot_reflectance
        self.layer_config.on_plot_electric_field = self.plot_electric_field
        self.layer_config.on_refresh_reflectance = self.refresh_reflectance
        self.layer_config.on_refresh_electric_field = self.refresh_electric_field
        
        # Initialize plotter
        self.plotter = PlotReflectance(right_frame=self.layer_config.right_panel)
        
        # Link plotter to layer config for real-time updates
        self.layer_config.plotter = self.plotter

    def upload_raw_data(self):
        file_path = filedialog.askopenfilename(
            title="Select Raw Reflectance Data File",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*"))
        )
        if file_path:
            try:
                self.raw_data = load_raw_data(file_path)
                self.plotter.plot_raw_data(self.raw_data, self.plotter.ax1, self.plotter.canvas)
                messagebox.showinfo("Success", "Raw reflectance data loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def plot_reflectance(self):
        try:
            angle = float(self.layer_config.angle_entry.get())
            polarization = self.layer_config.polarization_var.get()
            dbr_stack, metal_layers, substrate_layer = self.layer_config.get_layers()
            substrate_thickness = self.layer_config.substrate_thickness.get()
            light_direction = self.layer_config.reverse_light_direction.get()
            
            # Update plotter with current parameters
            self.plotter.dbr_stack = dbr_stack
            self.plotter.metal_layers = metal_layers
            self.plotter.substrate_layer = substrate_layer
            self.plotter.substrate_thickness = substrate_thickness
            self.plotter.light_direction = light_direction
            
            # Plot reflectance and store state for future updates
            self.plotter.plot_stack(angle, polarization, self.plotter.ax1, self.plotter.canvas)
            self.plotter.store_plot_state(angle, polarization, self.plotter.ax1, self.plotter.canvas)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def plot_electric_field(self):
        try:
            dbr_stack, metal_layers, substrate_layer = self.layer_config.get_layers()
            light_direction = self.layer_config.reverse_light_direction.get()
            
            # Calculate total thickness
            metal_thickness = 0
            if metal_layers:
                metal_thickness = sum(layer[0] for layer in metal_layers)
                
            substrate_thickness = 0
            if self.layer_config.is_finite_substrate.get():
                try:
                    substrate_thickness = float(self.layer_config.substrate_thickness.get())
                except ValueError:
                    substrate_thickness = 0
            
            # Update plotter and plot
            self.plotter.dbr_stack = dbr_stack
            self.plotter.metal_layers = metal_layers
            self.plotter.substrate_layer = substrate_layer
            self.plotter.light_direction = light_direction
            self.plotter.metal_thickness = metal_thickness
            
            self.plotter.plot_electric_field_decay(self.plotter.ax2, self.plotter.canvas)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to plot electric field: {e}")

    def refresh_reflectance(self):
        self.plotter.ax1.clear()
        
        # Reset reflectance plot properties
        self.plotter.ax1.set_xticks(np.arange(2, 13, 1))
        self.plotter.ax1.set_yticks(np.linspace(0.0, 1.0, 11))
        self.plotter.ax1.set_xlim(2.5, 12)
        self.plotter.ax1.set_ylim(0.0, 1.0)
        self.plotter.ax1.set_xlabel("Wavelength (μm)")
        self.plotter.ax1.set_ylabel("Reflectance")
        self.plotter.ax1.set_title("Simulated Reflectance")
        self.plotter.ax1.grid(alpha=0.2)
        
        self.plotter.canvas.draw()

    def refresh_electric_field(self):
        self.plotter.ax2.clear()
        
        # Reset electric field plot properties
        self.plotter.ax2.set_xticks(np.linspace(0, 7, 8))
        self.plotter.ax2.set_yscale("log")
        self.plotter.ax2.set_yticks(np.logspace(-5, 1, 7))
        self.plotter.ax2.set_xlim(0, 7)
        self.plotter.ax2.set_xlabel("Depth from the top (μm)")
        self.plotter.ax2.set_ylabel("Amplitude")
        self.plotter.ax2.set_title("Electric Field Decay")
        self.plotter.ax2.grid(alpha=0.2)
        
        self.plotter.canvas.draw()

        
if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = LayerStackApp(root)
        root.mainloop()
    except Exception as e:
        print(f"An error occurred: {e}")
