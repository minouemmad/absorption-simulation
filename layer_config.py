import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from utils import *

class LayerConfig:
    
    def __init__(self, root, settings):
        self.root = root
        self.root.title("Layer Configuration")
        
        # Set window size to fit the screen (webpage-like size)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()  # Adjust for taskbar/UI elements
        root.geometry(f"{screen_width}x{screen_height}")  # Position at top-left corner
        root.resizable(True, True)
        
        self.settings = settings
        self.dbr_layers = settings["dbr_layers"]
        self.metal_layers = settings["metal_layers"]
        
        # Create a Canvas and Scrollbar
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure the Canvas to scroll
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=(0, 0, self.scrollable_frame.winfo_width(), self.scrollable_frame.winfo_height())
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Use grid for Canvas and Scrollbar
        self.scrollbar.grid(row=0, column=0, sticky="ns")  # Scrollbar on the left
        self.canvas.grid(row=0, column=1, sticky="nsew")   # Canvas on the right

        # Configure root grid to expand
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)  # Canvas expands
        self.root.grid_columnconfigure(0, weight=0)  # Scrollbar does not expand

        # Ensure the scrollable_frame expands within the canvas
        self.scrollable_frame.grid_rowconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Prevent scrolling above row 0
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.setup_gui()
        self.setup_manual_layer_entry()
        self.setup_substrate_selection()
        self.setup_dbr_layers()
        self.setup_metal_layers()
        self.setup_light_direction_toggle()

    def _on_mousewheel(self, event):
        """Prevent scrolling above row 0."""
        if self.canvas.yview()[0] <= 0 and event.delta > 0:
            return  # Disable scrolling up when at the top
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def setup_gui(self):
        # Initialize the ttkbootstrap style
        self.style = tb.Style("flatly")

        # Main Frame
        self.main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        self.main_frame.grid(sticky=("N", "S", "E", "W"))

    def setup_manual_layer_entry(self):
        # Checkbox for manual layer entry
        self.manual_layer_var = tk.BooleanVar(value=False)
        self.manual_layer_checkbox = tk.Checkbutton(
            self.scrollable_frame,
            text="Manually Enter Each Layer",
            variable=self.manual_layer_var,
            font=("Helvetica Neue", 12),
            fg="#4A90E2",
            command=self.toggle_manual_layer_entry
        )
        self.manual_layer_checkbox.grid(row=0, column=0, columnspan=3, sticky="w", pady=10)

        # Frame for manual layer input (big white box)
        self.manual_layer_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text="Manual Layer Configuration",
            padding=10,
            style="info.TLabelframe"  # Use a ttkbootstrap style for a modern look
        )
        self.manual_layer_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        self.manual_layer_frame.grid_remove()  # Initially hidden

        # Add Layer button
        self.add_layer_button = tk.Button(
            self.manual_layer_frame,
            text="Add Layer",
            command=self.add_manual_layer,
            bg="#4A90E2",  # Modern blue color
            fg="white",
            font=("Helvetica Neue", 10, "bold")
        )
        self.add_layer_button.grid(row=0, column=0, columnspan=3, pady=10)

        # List to store manual layers
        self.manual_layers = []

    def add_manual_layer(self):
        # Create a new frame for this layer
        layer_frame = ttk.Frame(self.manual_layer_frame)
        layer_frame.grid(row=len(self.manual_layers) + 1, column=0, columnspan=3, sticky="ew", pady=5)

        # Label for the layer
        layer_label = tk.Label(layer_frame, text=f"Layer {len(self.manual_layers) + 1}:", font=("Helvetica Neue", 10))
        layer_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Thickness entry
        thickness_label = tk.Label(layer_frame, text="Thickness (nm):", font=("Helvetica Neue", 10))
        thickness_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        thickness_entry = tk.Entry(layer_frame, width=15, font=("Helvetica Neue", 10))
        thickness_entry.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Frame for material and composition inputs
        material_frame = ttk.Frame(layer_frame)
        material_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)

        # Add the first material input (default to 100%)
        self.add_material_input(material_frame)

        # Button to add another material
        add_material_button = tk.Button(
            material_frame,
            text="Add Material",
            command=lambda: self.add_material_input(material_frame),
            bg="#4A90E2",  # Modern blue color
            fg="white",
            font=("Helvetica Neue", 10, "bold")
        )
        add_material_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

        # Store the layer frame and its components
        self.manual_layers.append((layer_frame, thickness_entry, material_frame))

    def add_material_input(self, material_frame):
        # Determine the row for the new material input
        row = len(material_frame.winfo_children()) // 3  # Each material input takes 3 columns

        # Material selection
        material_var = tk.StringVar()
        material_combobox = ttk.Combobox(
            material_frame,
            textvariable=material_var,
            values=["Ag", "Al", "Au", "Cu", "Cr", "Ni", "W", "Ti", "Be", "Pd", "Pt", "GaSb", "GaAs", "AlAsSb"],
            width=15,
            font=("Helvetica Neue", 10)
        )
        material_combobox.grid(row=row, column=0, padx=5, pady=5, sticky="w")

        # Composition entry
        composition_label = tk.Label(material_frame, text="Composition (%):", font=("Helvetica Neue", 10))
        composition_label.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        composition_entry = tk.Entry(material_frame, width=15, font=("Helvetica Neue", 10))
        composition_entry.grid(row=row, column=2, padx=5, pady=5, sticky="w")

        # Set default composition to 100% for the first material
        if row == 0:
            composition_entry.insert(0, "100")

    def toggle_manual_layer_entry(self):
        if self.manual_layer_var.get():
            # Hide existing sections
            self.substrate_frame.grid_remove()
            self.dbr_frame.grid_remove()
            self.metal_frame.grid_remove()
            # Show manual layer input section
            self.manual_layer_frame.grid()
        else:
            # Show existing sections
            self.substrate_frame.grid()
            self.dbr_frame.grid()
            self.metal_frame.grid()
            # Hide manual layer input section
            self.manual_layer_frame.grid_remove()

    def setup_substrate_selection(self):
        # Substrate selection section
        self.substrate_frame = ttk.Frame(self.scrollable_frame)
        self.substrate_frame.grid(row=1, column=0, columnspan=3, sticky="w")

        tk.Label(self.substrate_frame, 
            text="Select Substrate", 
            font=("Helvetica Neue", 14, "bold"), 
            fg="#4A90E2",  # Modern blue color
            pady=10).grid(row=0, column=0, columnspan=3, sticky="w")        
        self.substrate_var = tk.StringVar(value=self.settings["substrate"])
        ttk.Combobox(
            self.substrate_frame, textvariable=self.substrate_var, values=["GaSb", "GaAs", "Air"], width=20
        ).grid(row=1, column=0, columnspan=3, pady=5)

        # Add option to choose between semi-infinite and finite substrate
        self.is_finite_substrate = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.substrate_frame,
            text="Finite Substrate",
            variable=self.is_finite_substrate,
            font=("Helvetica Neue", 12),
            fg="#4A90E2",
            command=self.toggle_finite_substrate
        ).grid(row=0, column=3, columnspan=3, sticky="w")

        # Add input for substrate thickness (visible only if finite is selected)
        tk.Label(
            self.substrate_frame,
            text="Substrate Thickness (nm):",
            font=("Helvetica Neue", 12),
            fg="#4A90E2"
        ).grid(row=1, column=3, sticky="w")

        self.substrate_thickness = tk.StringVar(value="0")  # Use StringVar for easier tracing
        self.thickness_entry = ttk.Entry(
            self.substrate_frame,
            textvariable=self.substrate_thickness,
            width=10
        )
        self.thickness_entry.grid(row=1, column=4, sticky="w")

        # Trace changes to the thickness entry
        self.substrate_thickness.trace_add("write", self.update_substrate_thickness)

    def update_substrate_thickness(self, *args):
        """Automatically update and print the substrate thickness when the entry is modified."""
        try:
            # Get the value from the entry and update the substrate thickness
            thickness = float(self.substrate_thickness.get())
            print(f"Substrate thickness updated to: {thickness} nm")
        except ValueError:
            # Handle invalid input (e.g., non-numeric values)
            print("Invalid thickness value. Please enter a number.")

    def toggle_finite_substrate(self):
        """Enable or disable substrate thickness entry based on finite substrate selection."""
        if self.is_finite_substrate.get():
            self.thickness_entry.configure(state="normal")
            print("Finite substrate selected. Thickness:", self.substrate_thickness.get())
        else:
            self.thickness_entry.configure(state="disabled")

    def get_is_finite_substrate(self):
        return self.is_finite_substrate.get()

    def setup_light_direction_toggle(self):
        """
        Add a button to toggle the direction of light (forward or reverse).
        """
        # Initialize the BooleanVar for toggling light direction
        self.reverse_light_direction = tk.BooleanVar(value=False)
        # Light direction toggle button
        self.light_direction_button = tk.Checkbutton(
            self.scrollable_frame,
            text="Reverse Light Direction(Metal->DBR->Substrate)",
            variable=self.reverse_light_direction,
            font=("Helvetica Neue", 12),
            fg="#4A90E2",
            command=self.toggle_light_direction
        )
        self.light_direction_button.grid(row=0, column=3, columnspan=2, sticky="w", pady=5)

    def toggle_light_direction(self):
        """
        Toggle the direction of light and update the configuration.
        """
        if self.reverse_light_direction.get():
            print("Light direction: Reverse")
        else:
            print("Light direction: Forward")

    def setup_dbr_layers(self):
        # DBR layers section
        self.dbr_frame = ttk.Frame(self.scrollable_frame)
        self.dbr_frame.grid(row=3, column=0, columnspan=3, sticky="w")

        tk.Label(self.dbr_frame, text="Select DBR", 
            font=("Helvetica Neue", 14, "bold"), 
            fg="#4A90E2"
            , pady=10).grid(row=0, column=0, columnspan=3, sticky="w")

        tk.Label(self.dbr_frame, text="Material:").grid(row=1, column=0, padx=5, pady=5)
        self.dbr_material_var = tk.StringVar(value="GaSb")
        ttk.Combobox(
            self.dbr_frame, textvariable=self.dbr_material_var, values=["GaSb", "AlAsSb"], width=10
        ).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.dbr_frame, text="Thickness (nm):").grid(row=1, column=2, padx=5, pady=5)
        self.dbr_thickness_entry = tk.Entry(self.dbr_frame, width=10)
        self.dbr_thickness_entry.grid(row=1, column=3, padx=5, pady=5)

        tk.Button(self.dbr_frame, text="Add DBR Layer", command=self.add_dbr_layer).grid(row=2, column=0, columnspan=4, pady=5)

        tk.Label(self.dbr_frame, text="Number of Periods:").grid(row=3, column=0, padx=5, pady=5)
        self.dbr_period_entry = tk.Entry(self.dbr_frame, width=10)
        self.dbr_period_entry.insert(0, self.settings["dbr_period"])
        self.dbr_period_entry.grid(row=3, column=1, padx=5, pady=5)

        tk.Button(self.dbr_frame, text="Set DBR Period", command=self.set_dbr_period).grid(row=3, column=2, columnspan=2, pady=5)

        self.dbr_layer_list = tk.Listbox(self.dbr_frame, height=5, width=40)
        self.dbr_layer_list.grid(row=4, column=0, columnspan=4, pady=10)

        tk.Button(self.dbr_frame, text="Clear DBR Layers", command=self.clear_dbr_layers).grid(row=5, column=0, columnspan=4, pady=5)

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
            self.dbr_message_label = tk.Label(self.dbr_frame, 
                                          text=f"DBR Stack set with {len(dbr_stack)} layers.", 
                                          font=("Arial", 10, "italic"), 
                                          fg="#FF6347")
            # Position the label to the right of the Set Period button
            self.dbr_message_label.grid(row=3, column=4, padx=0, sticky="w")

    def clear_dbr_layers(self):
        self.dbr_layers.clear()
        self.dbr_layer_list.delete(0, tk.END)
        #save_settings(self.settings)

    def setup_metal_layers(self):
        # Metal layers section
        self.metal_frame = ttk.Frame(self.scrollable_frame)
        self.metal_frame.grid(row=4, column=0, columnspan=3, sticky="w")

        tk.Label(self.metal_frame, text="Define Metal Layers", 
            font=("Helvetica Neue", 14, "bold"), 
            fg="#4A90E2", pady=10).grid(row=0, column=0, columnspan=3, sticky="w")

        # Mystery Metal toggle
        tk.Label(self.metal_frame, text="Use Mystery Metal:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.mystery_metal_var = tk.BooleanVar(value=False)
        self.mystery_metal_checkbox = tk.Checkbutton(self.metal_frame, variable=self.mystery_metal_var, command=self.toggle_mystery_metal)
        self.mystery_metal_checkbox.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Mystery Metal Frame
        self.mystery_metal_frame = ttk.Frame(self.metal_frame)
        self.mystery_metal_frame.grid(row=2, column=0, columnspan=4, pady=5, sticky="w")

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

        self.f0_var.trace_add("write", self.update_mystery_metal_params)
        self.gamma0_var.trace_add("write", self.update_mystery_metal_params)
        self.wp_var.trace_add("write", self.update_mystery_metal_params)

        # Standard Metal Frame
        self.standard_metal_frame = ttk.Frame(self.metal_frame)
        self.standard_metal_frame.grid(row=3, column=0, columnspan=4, pady=5, sticky="w")

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
        self.toggle_mystery_metal()

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

    def update_mystery_metal_params(self, *args):
        """Update mystery metal parameters from GUI inputs."""
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
        
    def setup_incidence_inputs(self):
        tk.Label(self.scrollable_frame, text="Incidence Angle (degrees):").grid(row=18, column=0)
        self.angle_entry = tk.Entry(self.scrollable_frame)
        self.angle_entry.grid(row=18, column=1, columnspan=2)
        self.angle_entry.insert(0, "0")
        
        tk.Label(self.scrollable_frame, text="Polarization:").grid(row=19, column=0)
        self.polarization_var = tk.StringVar(value="s")
        ttk.Combobox(self.scrollable_frame, textvariable=self.polarization_var, values=["s", "p"]).grid(row=19, column=1, columnspan=2)

    def get_layers(self):
        # Generate the substrate layer dynamically
        substrate_material = (
            "GaSb_ln" if self.substrate_var.get() == "GaSb"
            else "GaAs_ln" if self.substrate_var.get() == "GaAs"
            else [1.0, 0.0] if self.substrate_var.get() == "Air"
            else float('nan')  # Fallback if none of the conditions match
        )

        # Check if the substrate is finite
        substrate_thickness = self.substrate_thickness.get() if self.is_finite_substrate.get() else float('nan')

        # Create the substrate layer with the correct thickness
        substrate_layer = [[substrate_thickness, "Constant", substrate_material]]

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