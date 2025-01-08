#layer_config.py - Handles DBR and metal layer configurations.
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter as tk
from tkinter import ttk, messagebox

class LayerConfig:
    def __init__(self, root, settings):
        self.root = root
        self.settings = settings
        self.dbr_layers = settings["dbr_layers"]
        self.metal_layers = settings["metal_layers"]

        self.setup_gui()
        self.setup_substrate_selection()
        self.setup_dbr_layers()
        self.setup_metal_layers()

    def setup_gui(self):
        # Setting up a visually appealing theme
        style = ttk.Style()
        style.theme_use('clam')

    def setup_substrate_selection(self):
        # Substrate selection section
        tk.Label(self.root, text="Select Substrate", font=("Arial", 12, "bold"), pady=10).grid(row=0, column=0, columnspan=3, sticky="w")
        
        self.substrate_var = tk.StringVar(value=self.settings["substrate"])
        ttk.Combobox(
            self.root, textvariable=self.substrate_var, values=["GaSb", "GaAs", "Air"], width=20
        ).grid(row=1, column=0, columnspan=3, pady=5)

    def setup_dbr_layers(self):
        # DBR layers section
        tk.Label(self.root, text="Define DBR Layers", font=("Arial", 12, "bold"), pady=10).grid(row=2, column=0, columnspan=3, sticky="w")

        tk.Label(self.root, text="Material:").grid(row=3, column=0, padx=5, pady=5)
        self.dbr_material_var = tk.StringVar(value="GaSb")
        ttk.Combobox(
            self.root, textvariable=self.dbr_material_var, values=["GaSb", "AlAsSb"], width=10
        ).grid(row=3, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Thickness (nm):").grid(row=3, column=2, padx=5, pady=5)
        self.dbr_thickness_entry = tk.Entry(self.root, width=10)
        self.dbr_thickness_entry.grid(row=3, column=3, padx=5, pady=5)

        tk.Button(self.root, text="Add DBR Layer", command=self.add_dbr_layer).grid(row=4, column=0, columnspan=4, pady=5)

        tk.Label(self.root, text="Number of Periods:").grid(row=5, column=0, padx=5, pady=5)
        self.dbr_period_entry = tk.Entry(self.root, width=10)
        self.dbr_period_entry.insert(0, self.settings["dbr_period"])
        self.dbr_period_entry.grid(row=5, column=1, padx=5, pady=5)

        tk.Button(self.root, text="Set DBR Period", command=self.set_dbr_period).grid(row=5, column=2, columnspan=2, pady=5)

        self.dbr_layer_list = tk.Listbox(self.root, height=5, width=40)
        self.dbr_layer_list.grid(row=6, column=0, columnspan=4, pady=10)

        tk.Button(self.root, text="Clear DBR Layers", command=self.clear_dbr_layers).grid(row=7, column=0, columnspan=4, pady=5)

    def add_dbr_layer(self):
        thickness = float(self.dbr_thickness_entry.get())
        material = self.dbr_material_var.get()
        layer = [thickness, "Constant", "GaSb_ln" if material == "GaSb" else "AlAsSb_ln"]
        self.dbr_layers.append(layer)
        self.dbr_layer_list.insert(tk.END, f"{material} - {thickness} nm")
        # save_settings(self.settings)

    def set_dbr_period(self):
        self.settings["dbr_period"] = int(self.dbr_period_entry.get())
        messagebox.showinfo("DBR Stack", f"DBR Stack set with {self.settings['dbr_period']} periods.")
        # save_settings(self.settings)

    def clear_dbr_layers(self):
        self.dbr_layers.clear()
        self.dbr_layer_list.delete(0, tk.END)
        # save_settings(self.settings)

    def setup_metal_layers(self):
        # Metal layers section
        tk.Label(self.root, text="Define Metal Layers", font=("Arial", 12, "bold"), pady=10).grid(row=8, column=0, columnspan=3, sticky="w")

        tk.Label(self.root, text="Material:").grid(row=9, column=0, padx=5, pady=5)
        self.metal_material_var = tk.StringVar(value="Au")
        ttk.Combobox(
            self.root, textvariable=self.metal_material_var, values=["Ag", "Al", "Au", "Cu", "Cr", "Ni", "W", "Ti", "Be", "Pd", "Pt"], width=10
        ).grid(row=9, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Thickness (nm):").grid(row=9, column=2, padx=5, pady=5)
        self.metal_thickness_entry = tk.Entry(self.root, width=10)
        self.metal_thickness_entry.grid(row=9, column=3, padx=5, pady=5)

        tk.Label(self.root, text="Delta n:").grid(row=10, column=0, padx=5, pady=5)
        self.delta_n_entry = tk.Entry(self.root, width=10)
        self.delta_n_entry.insert(0, "0.0")
        self.delta_n_entry.grid(row=10, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Delta Alpha:").grid(row=10, column=2, padx=5, pady=5)
        self.delta_alpha_entry = tk.Entry(self.root, width=10)
        self.delta_alpha_entry.insert(0, "0.0")
        self.delta_alpha_entry.grid(row=10, column=3, padx=5, pady=5)

        tk.Button(self.root, text="Add Metal Layer", command=self.add_metal_layer).grid(row=12, column=0, columnspan=4, pady=5)

        self.metal_layer_list = tk.Listbox(self.root, height=5, width=40)
        self.metal_layer_list.grid(row=11, column=0, columnspan=4, pady=10)

        tk.Button(self.root, text="Clear Metal Layers", command=self.clear_metal_layers).grid(row=13, column=0, columnspan=4, pady=5)

    def add_metal_layer(self):
        thickness = float(self.metal_thickness_entry.get())
        metal = self.metal_material_var.get()

        delta_n = float(self.delta_n_entry.get())
        delta_alpha = float(self.delta_alpha_entry.get())

        layer = [thickness, "Lorentz-Drude", [metal]]
        self.metal_layers.append(layer)

        self.metal_layer_list.insert(tk.END, f"{metal} - {thickness} nm, Δn={delta_n}, Δα={delta_alpha}")
        # save_settings(self.settings)

    def clear_metal_layers(self):
        self.metal_layers.clear()
        self.metal_layer_list.delete(0, tk.END)
        # save_settings(self.settings)

    def get_layers(self):
        substrate_layer = [[float('nan'), "Constant", "GaSb_ln" if self.substrate_var.get() == "GaSb" else "GaAs_ln"]]
        substrate_layer = [
        [
        float('nan'), 
        "Constant", 
        "GaSb_ln" if self.substrate_var.get() == "GaSb" 
        else "GaAs_ln" if self.substrate_var.get() == "GaAs" 
        else [1.0, 0.0] if self.substrate_var.get() == "Air" 
        else float('nan')  # Fallback if none of the conditions match
        ]
    ]
        dbr_stack = self.settings["dbr_period"] * self.dbr_layers
        return dbr_stack, self.metal_layers, substrate_layer
