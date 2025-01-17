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
        self.root.geometry("700x820")
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

        # Mystery Metal toggle
        tk.Label(self.root, text="Use Mystery Metal:").grid(row=9, column=0, padx=5, pady=5, sticky="w")
        self.mystery_metal_var = tk.BooleanVar(value=False)
        self.mystery_metal_checkbox = tk.Checkbutton(self.root, variable=self.mystery_metal_var, command=self.toggle_mystery_metal)
        self.mystery_metal_checkbox.grid(row=9, column=1, padx=5, pady=5, sticky="w")

        # Mystery Metal Frame
        self.mystery_metal_frame = ttk.Frame(self.root)
        self.mystery_metal_frame.grid(row=10, column=0, columnspan=4, pady=5, sticky="w")

        tk.Label(self.mystery_metal_frame, text="Thickness (nm):").grid(row=0, column=0, padx=5, pady=5)
        self.mystery_thickness_entry = tk.Entry(self.mystery_metal_frame, width=10)
        self.mystery_thickness_entry.grid(row=0, column=1, padx=5, pady=5)

        # Drude parameters
        self.f0_var = tk.StringVar(value="0")
        self.gamma0_var = tk.StringVar(value="0")
        self.wp_var = tk.StringVar(value="0")

        # f₀ parameter
        tk.Label(self.mystery_metal_frame, text="f₀:").grid(row=1, column=0, padx=5, pady=5)
        self.mystery_f0_entry = tk.Entry(self.mystery_metal_frame, textvariable=self.f0_var, width=10)
        self.mystery_f0_entry.grid(row=1, column=1, padx=5, pady=5)
        f0_slider = tk.Scale(self.mystery_metal_frame, from_=0, to=20, resolution=0.1, orient="horizontal", 
                             variable=self.f0_var)
        f0_slider.grid(row=1, column=2, padx=5, pady=5)

        # Γ₀ parameter
        tk.Label(self.mystery_metal_frame, text="Γ₀:").grid(row=2, column=0, padx=5, pady=5)
        self.mystery_gamma0_entry = tk.Entry(self.mystery_metal_frame, textvariable=self.gamma0_var, width=10)
        self.mystery_gamma0_entry.grid(row=2, column=1, padx=5, pady=5)
        gamma0_slider = tk.Scale(self.mystery_metal_frame, from_=0, to=20, resolution=0.1, orient="horizontal", 
                                 variable=self.gamma0_var)
        gamma0_slider.grid(row=2, column=2, padx=5, pady=5)

        # ωₚ parameter
        tk.Label(self.mystery_metal_frame, text="ωₚ:").grid(row=3, column=0, padx=5, pady=5)
        self.mystery_wp_entry = tk.Entry(self.mystery_metal_frame, textvariable=self.wp_var, width=10)
        self.mystery_wp_entry.grid(row=3, column=1, padx=5, pady=5)
        wp_slider = tk.Scale(self.mystery_metal_frame, from_=0, to=20, resolution=0.1, orient="horizontal", 
                             variable=self.wp_var)
        wp_slider.grid(row=3, column=2, padx=5, pady=5)

        tk.Button(self.mystery_metal_frame, text="Update Configuration", command=self.update_mystery_metal_params).grid(row=9, column=3, padx=5, pady=5, sticky="w")


        # Standard Metal Frame
        self.standard_metal_frame = ttk.Frame(self.root)
        self.standard_metal_frame.grid(row=11, column=0, columnspan=4, pady=5, sticky="w")

        tk.Label(
            self.standard_metal_frame,
            text="Standard Metal Configuration:",
            font=("Helvetica Neue", 12, "bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w")

        tk.Label(self.standard_metal_frame, text="Material:").grid(row=1, column=0, padx=5, pady=5)
        self.metal_material_var = tk.StringVar(value="Au")
        ttk.Combobox(
            self.standard_metal_frame,
            textvariable=self.metal_material_var,
            values=["Ag", "Al", "Au", "Cu", "Cr", "Ni", "W", "Ti", "Be", "Pd", "Pt"],
            width=10,
        ).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.standard_metal_frame, text="Thickness (nm):").grid(row=2, column=0, padx=5, pady=5)
        self.metal_thickness_entry = tk.Entry(self.standard_metal_frame, width=10)
        self.metal_thickness_entry.grid(row=2, column=1, padx=5, pady=5)

        # Delta parameters

        tk.Label(self.standard_metal_frame, text="Delta n:").grid(row=3, column=0, padx=5, pady=5)
        self.delta_n_entry = tk.Entry(self.standard_metal_frame, width=10)
        self.delta_n_entry.grid(row=3, column=1, padx=5, pady=5)
        self.delta_n_entry.insert(0, "0.0")

        tk.Label(self.standard_metal_frame, text="Delta Alpha:").grid(row=3, column=2, padx=5, pady=5)
        self.delta_alpha_entry = tk.Entry(self.standard_metal_frame, width=10)
        self.delta_alpha_entry.grid(row=3, column=3, padx=5, pady=5)
        self.delta_alpha_entry.insert(0, "0.0")

        tk.Label(self.standard_metal_frame, text="Delta ωp (Plasma Frequency):").grid(row=4, column=0, padx=5, pady=5)
        self.delta_omega_p_entry = tk.Entry(self.standard_metal_frame, width=10)
        self.delta_omega_p_entry.grid(row=4, column=1, padx=5, pady=5)
        self.delta_omega_p_entry.insert(0, "0.0")

        tk.Label(self.standard_metal_frame, text="Delta f (Oscillator Strength):").grid(row=4, column=2, padx=5, pady=5)
        self.delta_f_entry = tk.Entry(self.standard_metal_frame, width=10)
        self.delta_f_entry.grid(row=4, column=3, padx=5, pady=5)
        self.delta_f_entry.insert(0, "0.0")

        tk.Label(self.standard_metal_frame, text="Delta Γ (Damping Frequency):").grid(row=5, column=0, padx=5, pady=5)
        self.delta_gamma_entry = tk.Entry(self.standard_metal_frame, width=10)
        self.delta_gamma_entry.grid(row=5, column=1, padx=5, pady=5)
        self.delta_gamma_entry.insert(0, "0.0")

        tk.Label(self.standard_metal_frame, text="Delta ω (Resonant Frequency):").grid(row=5, column=2, padx=5, pady=5)
        self.delta_omega_entry = tk.Entry(self.standard_metal_frame, width=10)
        self.delta_omega_entry.grid(row=5, column=3, padx=5, pady=5)
        self.delta_omega_entry.insert(0, "0.0")

        # Buttons
        tk.Button(self.standard_metal_frame, text="Add Metal Layer", command=self.add_metal_layer).grid(row=8, column=0, padx=5, pady=5)
        tk.Button(self.standard_metal_frame, text="Edit Selected Layer", command=self.edit_metal_layer).grid(row=8, column=1, padx=5, pady=5)
        tk.Button(self.standard_metal_frame, text="Delete Selected Layer", command=self.delete_metal_layer).grid(row=8, column=2, padx=5, pady=5)
        tk.Button(self.standard_metal_frame, text="Clear Layers", command=self.delete_metal_layer).grid(row=8, column=3, padx=5, pady=5)

        self.metal_layer_list = tk.Listbox(self.standard_metal_frame, height=5, width=60)
        self.metal_layer_list.grid(row=9, column=0, columnspan=4, pady=5)

    def toggle_mystery_metal(self):
        if self.mystery_metal_var.get():
            print("Mystery Metal selected.")
            # Hide or disable standard metal configurations
            self.standard_metal_frame.grid_forget()
            self.mystery_metal_frame.grid(row=14, column=0, columnspan=4, padx=5, pady=5, sticky="w")
            
            thickness = float(self.mystery_thickness_entry.get())
            f0 = float(self.mystery_f0_entry.get())
            gamma0 = float(self.mystery_gamma0_entry.get())
            wp = float(self.mystery_wp_entry.get())

            layer = [thickness, "Drude", [f0, wp, gamma0]]
            print(f"layer: {layer}")
            self.metal_layers.append(layer)


        else:
            # Show standard options and hide mystery metal options
            
            self.mystery_metal_frame.grid_forget()
            self.standard_metal_frame.grid(row=10, column=0, columnspan=4, pady=5)

    def update_mystery_metal_params(self):
        """Update mystery metal parameters from GUI inputs."""
        try:
            # Retrieve values from GUI
            thickness = float(self.mystery_thickness_entry.get())
            f0 = float(self.f0_var.get())
            gamma0 = float(self.gamma0_var.get())
            wp = float(self.wp_var.get())

            # Update settings
            self.settings["metal_layers"] = [
                {"thickness": thickness, "f0": f0, "gamma0": gamma0, "wp": wp}
            ]
            layer = [thickness, "Drude", [f0, wp, gamma0]]
            self.metal_layers.append(layer)
            print(f"layer: {layer}")
            # Optionally, you can display confirmation or logging
            print("Updated Drude Parameters:", self.settings["metal_layers"])

        except ValueError:
            # Handle invalid inputs gracefully
            messagebox.showerror("Invalid Input", "Please enter valid numerical values for Drude parameters.")

    def add_metal_layer(self):

        thickness = float(self.metal_thickness_entry.get())
        metal = self.metal_material_var.get()
        delta_n = float(self.delta_n_entry.get())
        delta_alpha = float(self.delta_alpha_entry.get())

        delta_omega_p = float(self.delta_omega_p_entry.get())
        delta_f = float(self.delta_f_entry.get())
        delta_gamma = float(self.delta_gamma_entry.get())
        delta_omega = float(self.delta_omega_entry.get())

        #layer = [thickness, "Lorentz-Drude", [metal]]
        layer = [thickness, "Lorentz-Drude", [metal, delta_n, delta_alpha, delta_omega_p, delta_f, delta_gamma, delta_omega]]

        self.metal_layers.append(layer)

        self.metal_layer_list.insert(tk.END, (
            f"{metal} - {thickness} nm, "
            f"Δn={delta_n}, Δα={delta_alpha}, "
            f"Δωp={delta_omega_p}, Δf={delta_f}, "
            f"ΔΓ={delta_gamma}, Δω={delta_omega}"
        ))

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
            layer[2][3] = float(self.delta_omega_p_entry.get())
            layer[2][4] = float(self.delta_f_entry.get())
            layer[2][5] = float(self.delta_gamma_entry.get())
            layer[2][6] = float(self.delta_omega_entry.get())

            # Update the list display
            self.metal_layer_list.delete(index)
            self.metal_layer_list.insert(tk.END, (
            f"{layer[2][0]} - {layer[0]} nm, "
            f"Δn={layer[2][1]}, Δα={layer[2][2]}, "
            f"Δωp={layer[2][3]}, Δf={layer[2][4]}, "
            f"ΔΓ={layer[2][5]}, Δω={layer[2][6]}"
        ))
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
        return dbr_stack, self.metal_layers, substrate_layer