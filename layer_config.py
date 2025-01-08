#layer_config.py - Handles DBR and metal layer configurations.
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from utils import *

class LayerConfig:
    def __init__(self, root, settings):
        self.root = root
        self.root.title("Layer Configuration")
        self.root.geometry("600x800")
        self.root.resizable(True, True)
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
        # Initialize the ttkbootstrap style
        self.style = tb.Style("flatly")

        # Main Frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(sticky=("N", "S", "E", "W"))

    def setup_substrate_selection(self):
        # Substrate selection section
        tk.Label(self.root, 
            text="Select Substrate", 
            font=("Helvetica Neue", 14, "bold"), 
            fg="#4A90E2",  # Modern blue color
            pady=10).grid(row=0, column=0, columnspan=3, sticky="w")        
        self.substrate_var = tk.StringVar(value=self.settings["substrate"])
        ttk.Combobox(
            self.root, textvariable=self.substrate_var, values=["GaSb", "GaAs", "Air"], width=20
        ).grid(row=1, column=0, columnspan=3, pady=5)

    def setup_dbr_layers(self):
        # DBR layers section
        tk.Label(self.root, text="Select DBR", 
            font=("Helvetica Neue", 14, "bold"), 
            fg="#4A90E2"
            , pady=10).grid(row=2, column=0, columnspan=3, sticky="w")

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
        #save_settings(self.settings)

    def set_dbr_period(self):
        self.settings["dbr_period"] = int(self.dbr_period_entry.get())
        dbr_period = int(self.dbr_period_entry.get())
        dbr_stack = []
    
        for _ in range(dbr_period):
            for layer in self.dbr_layers:
                print(layer[2])
                if layer[2] == "GaSb_ln":
                    dbr_stack.append([layer[0], layer[1], [3.816, 0.0]])
                elif layer[2] == "AlAsSb_ln":
                    dbr_stack.append([layer[0], layer[1], [3.101, 0.0]])
                else:
                    dbr_stack.append([layer[0], layer[1], [1.0, 0.0]])
    
        self.dbr_stack = dbr_stack

        # Create or update a label for displaying the message
        if hasattr(self, "dbr_message_label"):
            # Update the text of the existing label
            self.dbr_message_label.config(text=f"DBR Stack set with {len(dbr_stack)} layers.", fg="red")
        else:
            # Create the label if it doesn't already exist
            self.dbr_message_label = tk.Label(self.root, 
                                          text=f"DBR Stack set with {len(dbr_stack)} layers.", 
                                          font=("Arial", 10, "italic"), 
                                          fg="#FF6347")
            # Position the label to the right of the Set Period button
            self.dbr_message_label.grid(row=5, column=4, padx=0, sticky="w")

    def clear_dbr_layers(self):
        self.dbr_layers.clear()
        self.dbr_layer_list.delete(0, tk.END)
        #save_settings(self.settings)

    def setup_metal_layers(self):
        # Metal layers section
        tk.Label(self.root, text="Define Metal Layers", 
            font=("Helvetica Neue", 14, "bold"), 
            fg="#4A90E2", pady=10).grid(row=8, column=0, columnspan=3, sticky="w")

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

        self.metal_layer_list = tk.Listbox(self.root, height=5, width=60)
        self.metal_layer_list.grid(row=11, column=0, columnspan=4, pady=10)

        tk.Button(self.root, text="Edit Selected Layer", command=self.edit_metal_layer).grid(row=13, column=0, columnspan=2, pady=5)
        tk.Button(self.root, text="Clear Metal Layers", command=self.clear_metal_layers).grid(row=13, column=0, columnspan=4, pady=5)
        tk.Button(self.root, text="Delete Selected Layer", command=self.delete_metal_layer).grid(row=13, column=2, columnspan=2, pady=5)

    def add_metal_layer(self):
        thickness = float(self.metal_thickness_entry.get())
        metal = self.metal_material_var.get()
        delta_n = float(self.delta_n_entry.get())
        delta_alpha = float(self.delta_alpha_entry.get())

        #layer = [thickness, "Lorentz-Drude", [metal]]
        layer = [thickness, "Lorentz-Drude", [metal, delta_n, delta_alpha]]

        self.metal_layers.append(layer)

        self.metal_layer_list.insert(tk.END, f"{metal} - {thickness} nm, Δn={delta_n}, Δα={delta_alpha}")
        #save_settings(self.settings)

    def edit_metal_layer(self):
        selected_index = self.metal_layer_list.curselection()
        if not selected_index:
            messagebox.showwarning("Edit Layer", "No layer selected to edit.")
            return

        index = selected_index[0]
        layer = self.metal_layers[index]

        try:
            # Update the selected layer
            layer[0] = float(self.metal_thickness_entry.get())
            layer[2][0] = self.metal_material_var.get()
            layer[2][1] = float(self.delta_n_entry.get())
            layer[2][2] = float(self.delta_alpha_entry.get())

            # Update the list display
            self.metal_layer_list.delete(index)
            self.metal_layer_list.insert(index, f"{layer[2][0]} - {layer[0]} nm, Δn={layer[2][1]}, Δα={layer[2][2]}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid values for all parameters.")

    def delete_metal_layer(self):
        selected_index = self.metal_layer_list.curselection()
        if not selected_index:
            messagebox.showwarning("Delete Layer", "No layer selected to delete.")
            return

        index = selected_index[0]
        self.metal_layers.pop(index)
        self.metal_layer_list.delete(index)

    def clear_metal_layers(self):
        self.metal_layers.clear()
        self.metal_layer_list.delete(0, tk.END)
        # save_settings(self.settings)

    def get_layers(self):
        # Generate the substrate layer dynamically
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

        # Dynamically generate the dbr_stack
        dbr_period = self.settings["dbr_period"]
        dbr_stack = []

        for _ in range(dbr_period):
            for layer in self.dbr_layers:
                if layer[2] == "GaSb_ln":
                    dbr_stack.append([layer[0], layer[1], [3.816, 0.0]])
                elif layer[2] == "AlAsSb_ln":
                    dbr_stack.append([layer[0], layer[1], [3.101, 0.0]])
                else:
                    dbr_stack.append([layer[0], layer[1], [1.0, 0.0]])
        print(f"DBR Stack: {dbr_stack}")
        return dbr_stack, self.metal_layers, substrate_layer