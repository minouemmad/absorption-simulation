#layer_config.py
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from utils import *
import time  
import Funcs as MF
from tkinter import ttk, messagebox
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import threading  # Add this if not already present
import pandas as pd  # Add this if not already present

global_wavelength_array = np.linspace(2000, 16000, 3500)  # shape (3500,)


class LayerConfig:
    
    def __init__(self, root, settings, plotter=None):
        self.root = root
        # Modern window styling
        self.root.configure(bg='#f0f0f0')
        self.root.title("Optical Layer Configuration")
        self.plotter = plotter
        self.settings = settings
        self.dbr_layers = settings["dbr_layers"]
        self.metal_layers = settings["metal_layers"]
        
        self.cancel_fitting_flag = False  # For tracking cancellation
        self.fit_progress_value = 0  # For progress tracking
        self.fit_status_message = ""  # For status updates
        self.substrate_thickness = tk.StringVar(value="0")  # Add this line

        self.manual_layer_var = tk.BooleanVar(value=False)
        self.manual_mode_active = False  # Additional flag to track manual mode
        
        # Modern styling with better colors
        self.style = tb.Style("minty")
        self.style.configure("TLabel", font=('Helvetica', 10))
        self.style.configure("TButton", font=('Helvetica', 10), padding=5)
        self.style.configure("TEntry", font=('Helvetica', 10), padding=5)
        self.style.configure("TCombobox", padding=5)
        
        # Configure root window to fill screen
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry(f"{int(screen_width*0.95)}x{int(screen_height*0.9)}+20+20")
        root.resizable(True, True)
        
        # Customize theme colors
        self.style.configure(".", font=('Segoe UI', 10))
        self.style.configure("TButton", padding=6, relief="flat")
        self.style.configure("TEntry", padding=5, relief="flat")
        self.style.configure("TCombobox", padding=5)
        
        # Add a modern header
        header = tb.Frame(root, bootstyle="primary", height=60)
        header.pack(fill=X)
        tb.Label(header, 
                text="Optical Layer Simulator", 
                font=('Segoe UI', 16, 'bold'), 
                bootstyle="inverse-primary").pack(side=LEFT, padx=20)

        # Main container with improved scrolling
        self.main_container = tb.Frame(root)
        self.main_container.pack(fill=BOTH, expand=True)
        
        # Create paned window for left/right split with equal initial sizes
        self.paned = tb.PanedWindow(self.main_container, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=True)
        
        # Left panel (controls) with scrollbar - now with fixed minimum width
        self.left_container = tb.Frame(self.paned, width=400)  # Set initial width
        self.left_canvas = tk.Canvas(self.left_container)
        self.left_scroll = tb.Scrollbar(self.left_container, orient=VERTICAL, command=self.left_canvas.yview)
        self.left_canvas.configure(yscrollcommand=self.left_scroll.set)
        
        self.left_scroll.pack(side=RIGHT, fill=Y)
        self.left_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        self.left_frame = tb.Frame(self.left_canvas)
        self.left_canvas.create_window((0, 0), window=self.left_frame, anchor="nw")
        
        self.left_frame.bind("<Configure>", lambda e: self.left_canvas.configure(
            scrollregion=self.left_canvas.bbox("all")))
        
        # Right panel (plots) - same initial size as left panel
        self.right_frame = tb.Frame(self.paned, width=400)
        
        # Add frames to paned window with equal weights
        self.paned.add(self.left_container, weight=1)
        self.paned.add(self.right_frame, weight=1)
        
        # Bind mousewheel for scrolling
        self.left_canvas.bind_all("<MouseWheel>", lambda e: self.left_canvas.yview_scroll(-1*(e.delta//120), "units"))
        
        # Remove native window decorations for modern look
        self.root.overrideredirect(False)

        # Initialize UI sections
        self.setup_gui()
        self.setup_manual_layer_entry()
        self.setup_substrate_selection()
        self.setup_dbr_layers()
        self.setup_metal_layers()
        self.setup_light_direction_toggle()
        self.setup_incidence_inputs()
        self.setup_action_buttons()

        # Make unknown metal the default option
        self.unknown_metal_var.set(True)
        self.toggle_unknown_metal()
        
        # Select standard configuration by default
        self.notebook.select(self.config_tab)

    def setup_gui(self):
        # Main notebook for tabbed interface with better styling
        self.notebook = tb.Notebook(self.left_frame)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid weights
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

    def setup_action_buttons(self):
        # Button frame
        btn_frame = ttk.Frame(self.left_frame)
        btn_frame.pack(fill=X, pady=10)
        
        # Upload Button
        upload_btn = tb.Button(
            btn_frame, 
            text="Upload Raw Reflectance Data", 
            command=self.upload_raw_data, 
            bootstyle="primary"
        )
        upload_btn.pack(side=TOP, fill=X, pady=5)
        
        # Plot Buttons
        plot_btn = tb.Button(
            btn_frame,
            text="Plot Simulated Reflectance",
            command=self.plot_reflectance,
            bootstyle="primary"
        )
        plot_btn.pack(side=TOP, fill=X, pady=5)
        
        plot_efield_btn = tb.Button(
            btn_frame,
            text="Plot Electric Field",
            command=self.plot_electric_field,
            bootstyle="primary"
        )
        plot_efield_btn.pack(side=TOP, fill=X, pady=5)
        
        # Delete buttons
        del_frame = ttk.Frame(btn_frame)
        del_frame.pack(fill=X, pady=5)
        
        self.refresh_reflectance_btn = tb.Button(
            del_frame,
            text="Delete Reflectance",
            command=self.refresh_reflectance,
            bootstyle="danger",
            width=15
        )
        self.refresh_reflectance_btn.pack(side=LEFT, expand=True, padx=2)
        
        self.refresh_efield_btn = tb.Button(
            del_frame,
            text="Delete E-Field",
            command=self.refresh_electric_field,
            bootstyle="danger",
            width=15
        )
        self.refresh_efield_btn.pack(side=LEFT, expand=True, padx=2)

    def upload_raw_data(self):
        if hasattr(self, 'on_upload_raw_data'):
            self.on_upload_raw_data()
            
    def plot_reflectance(self):
        if hasattr(self, 'on_plot_reflectance'):
            self.on_plot_reflectance()

    def plot_electric_field(self):
        if hasattr(self, 'on_plot_electric_field'):
            self.on_plot_electric_field()
            
    def refresh_reflectance(self):
        if hasattr(self, 'on_refresh_reflectance'):
            self.on_refresh_reflectance()
            
    def refresh_electric_field(self):
        if hasattr(self, 'on_refresh_electric_field'):
            self.on_refresh_electric_field()

    def setup_manual_layer_entry(self):
        # Tab for manual layer entry
        self.manual_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.manual_tab, text="Manual Layer Entry")
        
        # Enable checkbox
        self.manual_layer_var = tk.BooleanVar(value=False)
        manual_check = tb.Checkbutton(
            self.manual_tab,
            text="Enable Manual Layer Entry",
            variable=self.manual_layer_var,
            bootstyle="primary-round-toggle",
            command=self.toggle_manual_layer_entry
        )
        manual_check.pack(pady=10, padx=10, anchor="w")

        # Frame for manual layer configuration
        self.manual_layer_frame = tb.LabelFrame(
            self.manual_tab,
            text="Layer Stack Configuration",
            bootstyle="info"
        )
        self.manual_layer_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Substrate section (always first layer)
        self.substrate_frame = tb.LabelFrame(
            self.manual_layer_frame,
            text="Substrate (Layer 1)",
            bootstyle="primary"
        )
        self.substrate_frame.pack(fill=X, padx=5, pady=5)
        
        # Substrate material selection
        tb.Label(self.substrate_frame, text="Material:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.substrate_var = tk.StringVar(value="GaSb")
        substrate_combo = ttk.Combobox(
            self.substrate_frame,
            textvariable=self.substrate_var,
            values=["GaSb", "GaAs", "Air"],
            width=15
        )
        substrate_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Finite substrate toggle for manual entry
        self.manual_is_finite_substrate = tk.BooleanVar(value=False)
        finite_check = tb.Checkbutton(
            self.substrate_frame,
            text="Finite Substrate",
            variable=self.manual_is_finite_substrate,
            bootstyle="primary-round-toggle",
            command=self.toggle_manual_finite_substrate
        )
        finite_check.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Thickness entry for substrate
        self.manual_substrate_thickness = tk.StringVar(value="0")
        tb.Label(self.substrate_frame, text="Thickness (μm):").grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.substrate_thickness_entry = tb.Entry(
            self.substrate_frame, 
            textvariable=self.manual_substrate_thickness, 
            width=10,
            state="disabled"  # Start disabled for semi-infinite
        )
        self.substrate_thickness_entry.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        # Frame for additional layers
        self.additional_layers_frame = tb.Frame(self.manual_layer_frame)
        self.additional_layers_frame.pack(fill=BOTH, expand=True, pady=5)
        
        # Scrollable area for layers
        self.layers_canvas = tk.Canvas(self.additional_layers_frame)
        self.layers_scroll = tb.Scrollbar(self.additional_layers_frame, orient=VERTICAL, command=self.layers_canvas.yview)
        self.layers_canvas.configure(yscrollcommand=self.layers_scroll.set)
        
        self.layers_scroll.pack(side=RIGHT, fill=Y)
        self.layers_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        self.layers_container = tb.Frame(self.layers_canvas)
        self.layers_canvas.create_window((0, 0), window=self.layers_container, anchor="nw")
        
        self.layers_container.bind("<Configure>", lambda e: self.layers_canvas.configure(
            scrollregion=self.layers_canvas.bbox("all")))
        
        # Bind mousewheel for scrolling
        self.layers_canvas.bind_all("<MouseWheel>", lambda e: self.layers_canvas.yview_scroll(-1*(e.delta//120), "units"))
        
        # Add Layer button
        self.add_layer_button = tb.Button(
            self.manual_layer_frame,
            text="+ Add New Layer",
            command=self.add_manual_layer,
            bootstyle="success"
        )
        self.add_layer_button.pack(pady=10)
        
        # Add Repeat Layers controls
        repeat_frame = tb.Frame(self.manual_layer_frame)
        repeat_frame.pack(fill=X, pady=10)
        
        tb.Label(repeat_frame, text="Repeat Selected Layers:").pack(side=LEFT, padx=5)
        
        self.repeat_times_entry = tb.Entry(repeat_frame, width=5)
        self.repeat_times_entry.pack(side=LEFT, padx=5)
        self.repeat_times_entry.insert(0, "1")
        
        repeat_btn = tb.Button(
            repeat_frame,
            text="Apply Repeat",
            command=self.apply_layer_repeat,
            bootstyle="info"
        )
        repeat_btn.pack(side=LEFT, padx=5)
        
        # List to store manual layers
        self.manual_layers = []
        
        # Add Drude fitting controls for manual layers
        self.setup_manual_drude_fitting()

    def apply_layer_repeat(self):
        """Repeat the selected layers the specified number of times"""
        try:
            repeat_times = int(self.repeat_times_entry.get())
            if repeat_times < 1:
                raise ValueError("Repeat times must be at least 1")
                
            # Get selected layers (working with a copy to avoid modification during iteration)
            selected_layers = [layer for layer in self.manual_layers if layer['select_var'].get()]
            
            if not selected_layers:
                messagebox.showwarning("No Selection", "No layers selected for repeating")
                return
                
            # Store the original layer count
            original_count = len(self.manual_layers)
            
            # For each repeat iteration
            for _ in range(repeat_times):
                # For each selected layer, create a copy
                for original_idx, original_layer in enumerate(selected_layers):
                    # Create a new layer (this will automatically add it to manual_layers)
                    new_layer = self.add_manual_layer(skip_pack=True)
                    
                    # Copy basic properties
                    new_layer['type_var'].set(original_layer['type_var'].get())
                    new_layer['thickness_entry'].delete(0, tk.END)
                    new_layer['thickness_entry'].insert(0, original_layer['thickness_entry'].get())
                    
                    # Copy all material properties
                    self._copy_material_properties(original_layer, new_layer)
                    
                    # Pack the new layer frame (we skipped this in add_manual_layer)
                    new_layer['frame'].pack(fill=X, pady=5, padx=5)
                    
                    # Unselect the new layer
                    new_layer['select_var'].set(False)
            
            # Update the display
            self.update_layer_numbers()
            self.layers_canvas.configure(scrollregion=self.layers_canvas.bbox("all"))
            self.layers_canvas.yview_moveto(1)  # Scroll to bottom to show new layers
            
            messagebox.showinfo("Success", f"Repeated selected layers {repeat_times} times")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid repeat value: {str(e)}")

    def _copy_material_properties(self, source_layer, dest_layer):
        """Copy all material properties from source to destination layer"""
        # First get current values from source
        source_material = None
        source_composition = None
        
        for child in source_layer['material_inputs'].winfo_children():
            if hasattr(child, 'material_var'):
                source_material = child.material_var.get()
            if hasattr(child, 'comp_entry') and child.comp_entry.winfo_ismapped():
                source_composition = child.comp_entry.get()
        
        # Clear existing inputs
        for widget in dest_layer['material_inputs'].winfo_children():
            widget.destroy()
        
        # Recreate inputs with source values
        self.add_material_input(
            dest_layer['material_inputs'], 
            source_layer['type_var'].get(),
            initial_material=source_material,
            initial_composition=source_composition
        )
        
        # Copy other properties (n/k values, etc.)
        source_widgets = self._get_material_widgets_recursive(source_layer['material_inputs'])
        dest_widgets = self._get_material_widgets_recursive(dest_layer['material_inputs'])
        
        for key in source_widgets:
            if key in dest_widgets:
                src_widget = source_widgets[key]
                dest_widget = dest_widgets[key]
                
                if isinstance(src_widget, tk.Entry):
                    current_value = src_widget.get()
                    dest_widget.delete(0, tk.END)
                    dest_widget.insert(0, current_value)
                elif isinstance(src_widget, tk.StringVar):
                    dest_widget.set(src_widget.get())
                elif isinstance(src_widget, tk.BooleanVar):
                    dest_widget.set(src_widget.get())

    def _get_material_widgets_recursive(self, frame):
        """Recursively get all material input widgets from a frame with their types"""
        widgets = {}
        
        for child in frame.winfo_children():
            if isinstance(child, (ttk.Combobox, tk.Entry, tk.Checkbutton)):
                # Use the label text or widget type as key
                if hasattr(child, 'winfo_children') and child.winfo_children():
                    # For compound widgets, check their children
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Label):
                            key = subchild.cget('text').replace(':', '').strip()
                            widgets[key] = child
                elif isinstance(child, ttk.Combobox):
                    widgets['material'] = child
                elif isinstance(child, tk.Entry):
                    # Try to find a label for this entry
                    prev_widget = None
                    for sibling in frame.winfo_children():
                        if sibling == child:
                            if isinstance(prev_widget, tk.Label):
                                key = prev_widget.cget('text').replace(':', '').strip()
                                widgets[key] = child
                            break
                        prev_widget = sibling
            elif isinstance(child, tk.Frame):
                # Recursively check nested frames
                widgets.update(self._get_material_widgets_recursive(child))
        
        return widgets


    def _update_layer_display(self):
        """Update the layer display after changes"""
        # Update layer numbers
        self.update_layer_numbers()
        
        # Update canvas scroll region
        self.layers_canvas.configure(scrollregion=self.layers_canvas.bbox("all"))

    def _create_layer_frame(self, index):
        """Helper to create a new layer frame"""
        layer_frame = tb.LabelFrame(
            self.layers_container,
            text=f"Layer {index + 2}",  # +1 for substrate, +1 for 0-based index
            bootstyle="info"
        )
        layer_frame.pack(fill=X, pady=5, padx=5)
        return layer_frame
    
    def _copy_layer_properties(self, source_layer, dest_layer):
        """Copy properties from source layer to destination layer"""
        # Copy layer type
        dest_layer['type_var'].set(source_layer['type_var'].get())
        
        # Copy thickness
        dest_layer['thickness_entry'].delete(0, tk.END)
        dest_layer['thickness_entry'].insert(0, source_layer['thickness_entry'].get())
        
        # Copy material inputs (this is more complex and might need additional handling)
        # You'll need to implement this based on your specific material input structure
        self._copy_material_inputs(source_layer, dest_layer)
        
        # Copy selection state
        dest_layer['select_var'].set(source_layer['select_var'].get())    

    def toggle_manual_finite_substrate(self):
        if self.manual_is_finite_substrate.get():
            self.substrate_thickness_entry.configure(state="normal")
        else:
            self.substrate_thickness_entry.configure(state="disabled")

    def toggle_manual_layer_entry(self):
        """Toggle between manual and standard configuration"""
        self.manual_mode_active = self.manual_layer_var.get()
        
        if self.manual_mode_active:
            self.notebook.select(self.manual_tab)
            # Enable manual layer frame
            self.manual_layer_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        else:
            self.notebook.select(0)  # Select first tab (standard configuration)
            # Disable manual layer frame
            self.manual_layer_frame.pack_forget()
        
        # Force update the manual mode state
        self.update_manual_mode_state()

    def update_manual_mode_state(self):
        """Ensure manual mode state is consistent with UI elements"""
        # Check if manual tab is currently selected
        current_tab = self.notebook.index(self.notebook.select())
        is_manual_tab = (current_tab == self.notebook.index(self.manual_tab))
        
        # Update the state based on both the checkbox and the active tab
        self.manual_mode_active = self.manual_layer_var.get() and is_manual_tab


    def get_cached_reflectance(self, f0, gamma0, wp, wavelength):
        """Get reflectance from cache or compute if not available"""
        # Round parameters to nearest 0.1 for caching
        f0_rounded = round(f0, 1)
        gamma0_rounded = round(gamma0, 1)
        wp_rounded = round(wp, 1)
        
        # Check cache
        key = (f0_rounded, gamma0_rounded, wp_rounded, tuple(wavelength))
        if key not in self.drude_cache:
            # Compute and cache if not available
            self.drude_cache[key] = self.compute_reflectance_for_params(
                f0, gamma0, wp, wavelength
            )
        return self.drude_cache[key]

    def compute_reflectance_for_params(self, f0, gamma0, wp, wavelength):
        """Compute reflectance for specific parameters using your existing calculation"""
        # This should contain your actual reflectance calculation logic
        # Here's a template - replace with your actual calculation:
        
        # Create metal layer with current parameters
        thickness = float(self.unknown_thickness_entry.get())
        metal_layers = [[thickness, "Drude", [f0, wp, gamma0]]]
        
        # Get other layers
        dbr_stack, _, substrate_layer = self.get_layers()
        
        # Build layer structure
        Ls_structure = (
            [[np.nan, "Constant", [1.0, 0.0]]] +
            metal_layers +
            (dbr_stack if dbr_stack else []) +
            substrate_layer
        )
        
        if not self.light_direction_frame:
            Ls_structure = Ls_structure[::-1]
        
        # Convert wavelength to nm if needed
        x = np.array(wavelength) * 1000
        angle = float(self.angle_entry.get())
        incang = angle * np.pi / 180 * np.ones(x.size)
        
        # Calculate reflection coefficients
        rs, rp, _, _ = MF.calc_rsrpTsTp(incang, Ls_structure, x)
        
        # Calculate reflectance based on polarization
        polarization = self.polarization_var.get()
        if polarization == "s":
            R0 = np.abs(rs)**2
        elif polarization == "p":
            R0 = np.abs(rp)**2
        else:
            R0 = 0.5 * (np.abs(rs)**2 + np.abs(rp)**2)
        
        return R0

    def setup_manual_drude_fitting(self):
        """Add Drude parameter controls to manual layer tab"""
        drude_frame = tb.LabelFrame(
            self.manual_layer_frame,
            text="Metal Layer (Drude Model)",
            bootstyle="warning"
        )
        drude_frame.pack(fill=X, pady=10)
        
        # Add checkbox to enable/disable metal layer
        self.include_metal_var = tk.BooleanVar(value=True)
        include_metal_check = tb.Checkbutton(
            drude_frame,
            text="Include Metal Layer",
            variable=self.include_metal_var,
            bootstyle="warning-round-toggle",
            command=self.toggle_metal_layer_inclusion
        )
        include_metal_check.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Thickness
        tb.Label(drude_frame, text="Metal Thickness (nm):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.manual_metal_thickness = tb.Entry(drude_frame, width=10)
        self.manual_metal_thickness.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.manual_metal_thickness.insert(0, "50")
        
        # Drude parameters
        self.manual_f0_var = tk.DoubleVar(value=1.0)
        self.manual_gamma0_var = tk.DoubleVar(value=0.1)
        self.manual_wp_var = tk.DoubleVar(value=9.0)
        
        # f₀ parameter
        tb.Label(drude_frame, text="f₀ (Oscillator Strength):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        f0_entry = tb.Entry(drude_frame, textvariable=self.manual_f0_var, width=8)
        f0_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Γ₀ parameter
        tb.Label(drude_frame, text="Γ₀ (Damping Frequency):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        gamma0_entry = tb.Entry(drude_frame, textvariable=self.manual_gamma0_var, width=8)
        gamma0_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # ωₚ parameter
        tb.Label(drude_frame, text="ωₚ (Plasma Frequency):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        wp_entry = tb.Entry(drude_frame, textvariable=self.manual_wp_var, width=8)
        wp_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # Fit button
        fit_btn = tb.Button(
            drude_frame,
            text="Fit to Raw Data",
            command=self.fit_drude_to_data,
            bootstyle="success"
        )
        fit_btn.grid(row=5, column=0, columnspan=2, pady=5)

    def toggle_metal_layer_inclusion(self):
        """Enable/disable metal layer controls based on checkbox"""
        state = "normal" if self.include_metal_var.get() else "disabled"
        
        # Disable all metal-related controls
        self.manual_metal_thickness.configure(state=state)
        
        # Find and disable all Drude parameter entries
        for child in self.manual_layer_frame.winfo_children():
            if isinstance(child, tb.LabelFrame) and "Metal Layer" in child.cget("text"):
                for widget in child.winfo_children():
                    if isinstance(widget, tb.Entry):
                        widget.configure(state=state)
                    elif isinstance(widget, tb.Button):
                        widget.configure(state=state)

    def add_manual_layer(self, skip_pack=False):
        """Add a new manual layer to the stack, with option to skip packing the frame"""
        layer_num = len(self.manual_layers) + 2  # +1 for substrate, +1 for 0-based index
        
        # Create a new frame for this layer
        layer_frame = tb.LabelFrame(
            self.layers_container,
            text=f"Layer {layer_num}",
            bootstyle="info"
        )
        if not skip_pack:
            layer_frame.pack(fill=X, pady=5, padx=5)
        
        # Checkbox for selecting this layer for repeating
        select_var = tk.BooleanVar(value=False)
        select_check = tb.Checkbutton(
            layer_frame,
            text="Select for Repeating",
            variable=select_var,
            bootstyle="primary-round-toggle"
        )
        select_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Material type selection
        tb.Label(layer_frame, text="Layer Type:").grid(row=0, column=1, padx=5, pady=5, sticky="w")
        material_type_var = tk.StringVar(value="Semiconductor")
        material_type_menu = ttk.Combobox(
            layer_frame,
            textvariable=material_type_var,
            values=["Semiconductor", "Dielectric", "Metal"],
            width=15,
            state="readonly"
        )
        material_type_menu.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        material_type_menu.bind("<<ComboboxSelected>>", lambda e, f=layer_frame: self.update_material_inputs(f))
        
        # Thickness entry
        tb.Label(layer_frame, text="Thickness (nm):").grid(row=0, column=3, padx=5, pady=5, sticky="w")
        thickness_entry = tb.Entry(layer_frame, width=10)
        thickness_entry.grid(row=0, column=4, padx=5, pady=5, sticky="w")
        thickness_entry.insert(0, "100")  # Default thickness
        
        # Frame for material inputs
        material_input_frame = tb.Frame(layer_frame)
        material_input_frame.grid(row=1, column=0, columnspan=5, sticky="ew", padx=5, pady=5)
        
        # Add initial material input based on type
        self.add_material_input(material_input_frame, material_type_var.get(), first=True)
        
        # Delete button
        delete_btn = tb.Button(
            layer_frame,
            text="Delete Layer",
            command=lambda: self.delete_manual_layer(layer_frame),
            bootstyle="danger-outline"
        )
        delete_btn.grid(row=0, column=5, padx=5, pady=5)
        
        # Store the layer components
        layer_data = {
            'frame': layer_frame,
            'type_var': material_type_var,
            'thickness_entry': thickness_entry,
            'material_inputs': material_input_frame,
            'select_var': select_var
        }
        
        self.manual_layers.append(layer_data)
        return layer_data


    def update_material_inputs(self, layer_frame):
        """Update the material inputs when layer type changes"""
        # Find which layer this is
        for layer in self.manual_layers:
            if layer['frame'] == layer_frame:
                # Clear existing inputs
                for widget in layer['material_inputs'].winfo_children():
                    widget.destroy()
                
                # Add new inputs based on type
                self.add_material_input(layer['material_inputs'], layer['type_var'].get(), first=True)
                break

    def add_semiconductor_input(self, parent_frame, first=False):
        """Add inputs for semiconductor materials with optional composition"""
        frame = tb.Frame(parent_frame)
        frame.pack(fill=X, pady=2)
        
        # Material selection
        tb.Label(frame, text="Material:").pack(side=LEFT, padx=5)
        material_var = tk.StringVar()
        material_combo = ttk.Combobox(
            frame,
            textvariable=material_var,
            values=["GaAs", "AlGaAs", "GaSb", "AlAsSb", "AlGaSb", "InSb", "AlSb", "InAs", "InAsSb"],
            width=12,
            state="readonly"
        )
        material_combo.pack(side=LEFT, padx=5)
        material_combo.set("GaAs")  # Default value
        
        # Composition frame
        comp_frame = tb.Frame(frame)
        comp_frame.pack(side=LEFT, padx=5)
        
        # Composition checkbox
        self.use_composition = tk.BooleanVar(value=False)
        comp_check = tb.Checkbutton(
            comp_frame,
            text="Specify Composition",
            variable=self.use_composition,
            bootstyle="primary-round-toggle",
            command=lambda: self.toggle_composition_entry(comp_entry)
        )
        comp_check.pack(side=LEFT)
        
        # Composition entry (initially disabled)
        comp_entry = tb.Entry(comp_frame, width=8, state="disabled")
        comp_entry.pack(side=LEFT, padx=5)
        
        # Function to update composition field based on material
        def update_composition_field(*args):
            material = material_var.get()
            if material in ["AlGaAs", "AlAsSb", "AlGaSb", "InAsSb"]:
                comp_check.config(state="normal")
                if self.use_composition.get():
                    comp_entry.config(state="normal")
                    if material == "AlGaAs":
                        comp_entry.delete(0, tk.END)
                        comp_entry.insert(0, "30")  # Default Al composition
                    elif material == "AlAsSb":
                        comp_entry.delete(0, tk.END)
                        comp_entry.insert(0, "30")  # Default AlAsSb composition
                    elif material == "AlGaSb":
                        comp_entry.delete(0, tk.END)
                        comp_entry.insert(0, "30") # Default to x=0.3 (Al₀.₃Ga₀.₇Sb)
                    elif material == "InAsSb":
                        comp_entry.delete(0, tk.END)
                        comp_entry.insert(0, "30")  # Default InAs composition
            else:
                comp_check.config(state="disabled")
                comp_entry.config(state="disabled")
                self.use_composition.set(False)
        
        # Initial setup
        update_composition_field()
        material_var.trace_add("write", update_composition_field)
        
        # Delete button (always shown except for first input)
        if not first:
            del_btn = tb.Button(
                frame,
                text="−",
                command=lambda: frame.destroy(),
                bootstyle="danger-outline",
                width=2
            )
            del_btn.pack(side=RIGHT, padx=5)


    def toggle_composition_entry(self, entry):
        """Toggle composition entry based on checkbox"""
        if self.use_composition.get():
            entry.config(state="normal")
        else:
            entry.config(state="disabled")

    def delete_manual_layer(self, frame):
        """Remove a manual layer from the stack"""
        for i, layer in enumerate(self.manual_layers):
            if layer['frame'] == frame:
                self.manual_layers.pop(i)
                frame.destroy()
                self.update_layer_numbers()
                break

    def update_layer_numbers(self):
        """Update layer numbering after deletions"""
        # Substrate is always layer 1
        for i, layer in enumerate(self.manual_layers, start=2):
            layer['frame'].config(text=f"Layer {i}")

    def update_manual_layer_numbers(self):
        for i, (layer_frame, _, _) in enumerate(self.manual_layers):
            for widget in layer_frame.winfo_children():
                if isinstance(widget, tb.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tb.Label) and "Layer" in child.cget("text"):
                            child.config(text=f"Layer {i+1}")

    def add_material_input(self, parent_frame, material_type, first=False, initial_material=None, initial_composition=None):
        """Add appropriate material inputs based on layer type"""
        frame = tb.Frame(parent_frame)
        frame.pack(fill=X, pady=2)
        
        if material_type == "Semiconductor":
            # Material selection
            tb.Label(frame, text="Material:").pack(side=LEFT, padx=5)
            material_var = tk.StringVar(value=initial_material if initial_material else "GaAs")
            material_combo = ttk.Combobox(
                frame,
                textvariable=material_var,
                values=["GaAs", "AlGaAs", "AlGaSb", "GaSb", "AlAsSb", "InAs", "InSb"],
                width=12,
                state="readonly"
            )
            material_combo.pack(side=LEFT, padx=5)
            frame.material_var = material_var
            
            # Composition entry for alloys
            comp_label = tb.Label(frame, text="Composition (%):")
            comp_entry = tb.Entry(frame, width=8)
            frame.comp_entry = comp_entry  # Store reference to composition entry
            
            def update_composition_state(*args):
                current_material = material_var.get()
                if current_material in ["AlGaAs", "AlAsSb", "AlGaSb"]:
                    comp_label.pack(side=LEFT, padx=5)
                    comp_entry.pack(side=LEFT)
                    if initial_composition is not None:  # Use provided composition if available
                        comp_entry.delete(0, tk.END)
                        comp_entry.insert(0, initial_composition)
                    elif not comp_entry.get():  # Otherwise use default if empty
                        comp_entry.delete(0, tk.END)
                        comp_entry.insert(0, "30" if current_material == "AlGaAs" else "50")
                else:
                    comp_label.pack_forget()
                    comp_entry.pack_forget()
            
            material_var.trace_add("write", update_composition_state)
            update_composition_state()  # Initial update
            
        elif material_type == "Metal":
            # Metal selection (unchanged)
            tb.Label(frame, text="Metal:").pack(side=LEFT, padx=5)
            material_var = tk.StringVar(value=initial_material if initial_material else "Ag")
            material_combo = ttk.Combobox(
                frame,
                textvariable=material_var,
                values=["Ag", "Al", "Au", "Cu", "Cr", "Ni", "W", "Ti", "Be", "Pd", "Pt"],
                width=12,
                state="readonly"
            )
            material_combo.pack(side=LEFT, padx=5)
            frame.material_var = material_var
            
        else:  # Dielectric (unchanged)
            # Refractive index entries
            tb.Label(frame, text="n:").pack(side=LEFT, padx=5)
            n_entry = tb.Entry(frame, width=8)
            n_entry.pack(side=LEFT)
            n_entry.insert(0, "1.0")
            
            tb.Label(frame, text="k:").pack(side=LEFT, padx=5)
            k_entry = tb.Entry(frame, width=8)
            k_entry.pack(side=LEFT)
            k_entry.insert(0, "0.0")

    def setup_substrate_selection(self):
        # Main configuration tab
        self.config_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="Standard Configuration")
        
        # Substrate selection section
        self.substrate_frame = tb.LabelFrame(
            self.config_tab,
            text="Substrate Configuration",
            bootstyle="primary"
        )
        self.substrate_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10, columnspan=2)
        
        # Substrate material
        tb.Label(self.substrate_frame, text="Substrate Material:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.substrate_var = tk.StringVar(value=self.settings["substrate"])
        substrate_combo = ttk.Combobox(
            self.substrate_frame,
            textvariable=self.substrate_var,
            values=["GaSb", "GaAs", "Air"],
            width=15
        )
        substrate_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Finite substrate toggle
        self.is_finite_substrate = tk.BooleanVar(value=False)
        finite_check = tb.Checkbutton(
            self.substrate_frame,
            text="Finite Substrate",
            variable=self.is_finite_substrate,
            bootstyle="primary-round-toggle",
            command=self.toggle_finite_substrate
        )
        finite_check.grid(row=1, column=0, padx=5, pady=5, sticky="w", columnspan=2)
        
        # Substrate thickness
        self.substrate_thickness = tk.StringVar(value="0")
        thickness_frame = tb.Frame(self.substrate_frame)
        thickness_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        tb.Label(thickness_frame, text="Thickness (nm):").pack(side=LEFT)
        self.thickness_entry = tb.Entry(thickness_frame, textvariable=self.substrate_thickness, width=10)
        self.thickness_entry.pack(side=LEFT, padx=5)
        self.thickness_entry.configure(state="disabled") 
               
        # Trace changes to thickness
        if hasattr(self, 'substrate_thickness'):
            self.substrate_thickness.trace_add("write", self.update_substrate_thickness)

    def enable_finite_substrate(self):
        """Show thickness controls when user clicks the button"""
        self.is_finite_substrate.set(True)
        self.toggle_finite_substrate()
        self.make_thickness_btn.grid_forget()

    def toggle_finite_substrate(self):
        """Show/hide substrate thickness controls"""
        if self.is_finite_substrate.get():
            # Create thickness controls if they don't exist
            if not hasattr(self, 'substrate_thickness'):
                self.substrate_thickness = tk.StringVar(value="100")  # Default thick substrate
                
                tb.Label(self.thickness_frame, text="Thickness (nm):").pack(side=LEFT)
                self.thickness_entry = tb.Entry(self.thickness_frame, textvariable=self.substrate_thickness, width=10)
                self.thickness_entry.pack(side=LEFT, padx=5)
            
            self.thickness_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        else:
            self.thickness_frame.grid_forget()
            self.substrate_thickness = float('nan')  # Default to semi-infinite

    def update_substrate_thickness(self, *args):
        try:
            thickness = float(self.substrate_thickness.get())
        except ValueError:
            print("Invalid thickness value")

    def toggle_finite_substrate(self):
        if self.is_finite_substrate.get():
            self.thickness_entry.configure(state="normal")
        else:
            self.thickness_entry.configure(state="disabled")

    def setup_light_direction_toggle(self):
        """Light direction toggle in the main tab"""
        self.light_direction_frame = tb.Frame(self.config_tab)
        self.light_direction_frame.grid(row=1, column=0, sticky="w", padx=10, pady=5, columnspan=2)
        
        self.reverse_light_direction = tk.BooleanVar(value=False)
        light_dir_btn = tb.Checkbutton(
            self.light_direction_frame,
            text="Reverse Light Direction (Metal→DBR→Substrate)",
            variable=self.reverse_light_direction,
            bootstyle="primary-round-toggle",
            command=self.toggle_light_direction
        )
        light_dir_btn.pack()

    def toggle_light_direction(self):
        if self.reverse_light_direction.get():
            print("Light direction: Reverse")
        else:
            print("Light direction: Forward")

    def setup_dbr_layers(self):
        # DBR layers section
        self.dbr_frame = tb.LabelFrame(
            self.config_tab,
            text="DBR Configuration",
            bootstyle="info"
        )
        self.dbr_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        # Material selection
        tb.Label(self.dbr_frame, text="Material:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.dbr_material_var = tk.StringVar(value="GaSb")
        material_combo = ttk.Combobox(
            self.dbr_frame,
            textvariable=self.dbr_material_var,
            values=["GaSb", "AlAsSb"],
            width=15
        )
        material_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Thickness entry
        tb.Label(self.dbr_frame, text="Thickness (nm):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.dbr_thickness_entry = tb.Entry(self.dbr_frame, width=10)
        self.dbr_thickness_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Add DBR layer button
        add_btn = tb.Button(
            self.dbr_frame,
            text="Add DBR Layer",
            command=self.add_dbr_layer,
            bootstyle="success"
        )
        add_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Number of periods for selected layers
        tb.Label(self.dbr_frame, text="Periods for Selection:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.dbr_period_entry = tb.Entry(self.dbr_frame, width=10)
        self.dbr_period_entry.insert(0, "1")
        self.dbr_period_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Set period for selected layers button
        period_btn = tb.Button(
            self.dbr_frame,
            text="Set Period for Selection",
            command=self.set_dbr_period,
            bootstyle="info"
        )
        period_btn.grid(row=4, column=0, columnspan=2, pady=5)
        
        # DBR layer list with multiple selection enabled
        self.dbr_layer_list = tk.Listbox(
            self.dbr_frame,
            height=5,
            width=40,
            bg="white",
            fg="black",
            selectbackground="#4A90E2",
            selectmode=tk.MULTIPLE  # Allow multiple selection
        )
        self.dbr_layer_list.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Button frame for delete and clear
        button_frame = tb.Frame(self.dbr_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=5)
        
        # Delete selected button
        delete_btn = tb.Button(
            button_frame,
            text="Delete Selected",
            command=self.delete_selected_dbr_layers,
            bootstyle="danger"
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear all button
        clear_btn = tb.Button(
            button_frame,
            text="Clear All",
            command=self.clear_dbr_layers,
            bootstyle="danger"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Initialize layer groups storage
        self.dbr_layer_groups = []
        self.current_group_id = 0

    def add_dbr_layer(self):
        try:
            thickness = float(self.dbr_thickness_entry.get())
            material = self.dbr_material_var.get()
            layer = {
                'id': self.current_group_id,
                'thickness': thickness,
                'material': material,
                'type': "Constant",
                'refractive_index': "GaSb_ln" if material == "GaSb" else "AlAsSb_ln"
            }
            self.current_group_id += 1
            self.dbr_layers.append(layer)
            self.dbr_layer_list.insert(tk.END, f"{material} - {thickness} nm")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid thickness")

    def set_dbr_period(self):
        try:
            selected_indices = self.dbr_layer_list.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Please select layers to repeat")
                return
                
            period = int(self.dbr_period_entry.get())
            if period < 1:
                messagebox.showerror("Error", "Period must be at least 1")
                return
                
            # Get the selected layers
            selected_layers = [self.dbr_layers[i] for i in selected_indices]
            
            # Create a new group with these layers and the period
            group = {
                'layers': selected_layers,
                'period': period
            }
            self.dbr_layer_groups.append(group)
            
            # Rebuild the DBR stack
            self.rebuild_dbr_stack()
            
            # Update status message
            self.update_dbr_status_message()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of periods")

    def rebuild_dbr_stack(self):
        self.dbr_stack = []
        
        for group in self.dbr_layer_groups:
            for _ in range(group['period']):
                for layer in group['layers']:
                    if layer['refractive_index'] == "GaSb_ln":
                        self.dbr_stack.append([layer['thickness'], layer['type'], [3.816, 0.0]])
                    elif layer['refractive_index'] == "AlAsSb_ln":
                        self.dbr_stack.append([layer['thickness'], layer['type'], [3.101, 0.0]])
                    else:
                        self.dbr_stack.append([layer['thickness'], layer['type'], [1.0, 0.0]])

    def update_dbr_status_message(self):
        total_layers = len(self.dbr_stack)
        group_info = ", ".join([f"{len(g['layers'])}×{g['period']}" for g in self.dbr_layer_groups])
        
        if hasattr(self, "dbr_message_label"):
            self.dbr_message_label.config(text=f"DBR Stack: {total_layers} layers ({group_info})")
        else:
            self.dbr_message_label = tb.Label(
                self.dbr_frame,
                text=f"DBR Stack: {total_layers} layers ({group_info})",
                bootstyle="success"
            )
            self.dbr_message_label.grid(row=7, column=0, columnspan=2, pady=5)

    def delete_selected_dbr_layers(self):
        selected_indices = self.dbr_layer_list.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select layers to delete")
            return
            
        # Delete from the list (starting from the end to avoid index shifting)
        for i in sorted(selected_indices, reverse=True):
            deleted_layer = self.dbr_layers.pop(i)
            self.dbr_layer_list.delete(i)
            
            # Remove this layer from any groups
            for group in self.dbr_layer_groups[:]:
                group['layers'] = [l for l in group['layers'] if l['id'] != deleted_layer['id']]
                if not group['layers']:
                    self.dbr_layer_groups.remove(group)
        
        # Rebuild the stack if we deleted something
        if selected_indices:
            self.rebuild_dbr_stack()
            self.update_dbr_status_message()

    def clear_dbr_layers(self):
        self.dbr_layers.clear()
        self.dbr_layer_list.delete(0, tk.END)
        self.dbr_layer_groups.clear()
        self.dbr_stack = []
        
        if hasattr(self, "dbr_message_label"):
            self.dbr_message_label.config(text="DBR Stack: 0 layers")

    def setup_metal_layers(self):
        # Metal layers section
        self.metal_frame = tb.LabelFrame(
            self.config_tab,
            text="Metal Layer Configuration",
            bootstyle="warning"
        )
        self.metal_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        
        # Unknown Metal toggle - default to True
        self.unknown_metal_var = tk.BooleanVar(value=True)
        unknown_check = tb.Checkbutton(
            self.metal_frame,
            text="Use Unknown Metal (Drude Model)",
            variable=self.unknown_metal_var,
            bootstyle="warning-round-toggle",
            command=self.toggle_unknown_metal
        )
        unknown_check.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        # Unknown Metal Frame
        self.unknown_metal_frame = tb.Frame(self.metal_frame)
        self.unknown_metal_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky="nsew")
        
        # Thickness
        tb.Label(self.unknown_metal_frame, text="Thickness (nm):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.unknown_thickness_entry = tb.Entry(self.unknown_metal_frame, width=10)
        self.unknown_thickness_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.unknown_thickness_entry.insert(0, "50")  # Default thickness
        
        # Drude parameters with modern sliders
        self.f0_var = tk.DoubleVar(value=1.0)
        self.gamma0_var = tk.DoubleVar(value=0.1)
        self.wp_var = tk.DoubleVar(value=9.0)
        
        # f₀ parameter
        tb.Label(self.unknown_metal_frame, text="f₀ (Oscillator Strength):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        f0_frame = tb.Frame(self.unknown_metal_frame)
        f0_frame.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.unknown_f0_entry = tb.Entry(f0_frame, textvariable=self.f0_var, width=8)
        self.unknown_f0_entry.pack(side=LEFT, padx=5)
        
        # Add increment/decrement buttons for f0
        f0_btn_frame = tb.Frame(f0_frame)
        f0_btn_frame.pack(side=LEFT, padx=2)
        
        def increment_f0():
            self.f0_var.set(round(self.f0_var.get() + 0.1, 1))
        
        def decrement_f0():
            self.f0_var.set(round(max(0, self.f0_var.get() - 0.1), 1))
        
        tb.Button(
            f0_btn_frame, 
            text="▲", 
            command=increment_f0,
            bootstyle="light",
            width=2
        ).pack(side=TOP)
        
        tb.Button(
            f0_btn_frame, 
            text="▼", 
            command=decrement_f0,
            bootstyle="light",
            width=2
        ).pack(side=BOTTOM)
        
        f0_slider = tb.Scale(
            f0_frame,
            from_=0,
            to=20,
            value=1.0,
            orient=HORIZONTAL,
            variable=self.f0_var,
            command=lambda val: self.update_unknown_metal_params(),
            bootstyle="warning"
        )
        f0_slider.pack(side=LEFT, fill=X, expand=True)
        
        # Γ₀ parameter
        tb.Label(self.unknown_metal_frame, text="Γ₀ (Damping Frequency):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        gamma0_frame = tb.Frame(self.unknown_metal_frame)
        gamma0_frame.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.unknown_gamma0_entry = tb.Entry(gamma0_frame, textvariable=self.gamma0_var, width=8)
        self.unknown_gamma0_entry.pack(side=LEFT, padx=5)
        
        # Add increment/decrement buttons for gamma0
        gamma0_btn_frame = tb.Frame(gamma0_frame)
        gamma0_btn_frame.pack(side=LEFT, padx=2)
        
        def increment_gamma0():
            self.gamma0_var.set(round(self.gamma0_var.get() + 0.1, 1))
        
        def decrement_gamma0():
            self.gamma0_var.set(round(max(0, self.gamma0_var.get() - 0.1), 1))
        
        tb.Button(
            gamma0_btn_frame, 
            text="▲", 
            command=increment_gamma0,
            bootstyle="light",
            width=2
        ).pack(side=TOP)
        
        tb.Button(
            gamma0_btn_frame, 
            text="▼", 
            command=decrement_gamma0,
            bootstyle="light",
            width=2
        ).pack(side=BOTTOM)
        
        gamma0_slider = tb.Scale(
            gamma0_frame,
            from_=0,
            to=5,
            value=0.1,
            orient=HORIZONTAL,
            variable=self.gamma0_var,
            command=lambda val: self.update_unknown_metal_params(),
            bootstyle="warning"
        )
        gamma0_slider.pack(side=LEFT, fill=X, expand=True)
        
        # ωₚ parameter
        tb.Label(self.unknown_metal_frame, text="ωₚ (Plasma Frequency):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        wp_frame = tb.Frame(self.unknown_metal_frame)
        wp_frame.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.unknown_wp_entry = tb.Entry(wp_frame, textvariable=self.wp_var, width=8)
        self.unknown_wp_entry.pack(side=LEFT, padx=5)
        
        # Add increment/decrement buttons for wp
        wp_btn_frame = tb.Frame(wp_frame)
        wp_btn_frame.pack(side=LEFT, padx=2)
        
        def increment_wp():
            self.wp_var.set(round(self.wp_var.get() + 0.1, 1))
        
        def decrement_wp():
            self.wp_var.set(round(max(0, self.wp_var.get() - 0.1), 1))
        
        tb.Button(
            wp_btn_frame, 
            text="▲", 
            command=increment_wp,
            bootstyle="light",
            width=2
        ).pack(side=TOP)
        
        tb.Button(
            wp_btn_frame, 
            text="▼", 
            command=decrement_wp,
            bootstyle="light",
            width=2
        ).pack(side=BOTTOM)
        
        wp_slider = tb.Scale(
            wp_frame,
            from_=0,
            to=20,
            value=9.0,
            orient=HORIZONTAL,
            variable=self.wp_var,
            command=lambda val: self.update_unknown_metal_params(),
            bootstyle="warning"
        )
        wp_slider.pack(side=LEFT, fill=X, expand=True)
        
        # Real-time updates
        self.f0_var.trace_add("write", lambda *args: self.update_unknown_metal_params())
        self.gamma0_var.trace_add("write", lambda *args: self.update_unknown_metal_params())
        self.wp_var.trace_add("write", lambda *args: self.update_unknown_metal_params())
        self.unknown_thickness_entry.bind("<KeyRelease>", lambda e: self.update_unknown_metal_params())
        
        # Standard Metal Frame (hidden by default)
        self.standard_metal_frame = tb.Frame(self.metal_frame)
        
        # Add "Match to Raw Data" button
        self.match_btn = tb.Button(
            self.unknown_metal_frame,
            text="Match to Raw Data",
            command=self.fit_drude_to_data,
            bootstyle="success"
        )
        self.match_btn.grid(row=4, column=0, columnspan=3, pady=10)
        
        # Add progress bar for fitting process
        self.fit_progress = tb.Progressbar(
            self.unknown_metal_frame,
            orient="horizontal",
            mode="determinate",
            bootstyle="success-striped"
        )
        self.fit_progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.fit_progress.grid_remove()

        # Configure grid weights
        self.metal_frame.grid_rowconfigure(1, weight=1)
        self.metal_frame.grid_columnconfigure(0, weight=1)

    def toggle_unknown_metal(self):
        if self.unknown_metal_var.get():
            # Show unknown metal options
            self.unknown_metal_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")
            self.standard_metal_frame.grid_forget()
            
            # Initialize with current values
            thickness = float(self.unknown_thickness_entry.get())
            f0 = float(self.f0_var.get())
            gamma0 = float(self.gamma0_var.get())
            wp = float(self.wp_var.get())
            
            layer = [thickness, "Drude", [f0, wp, gamma0]]
            self.metal_layers = [layer]
            
            # Update plot immediately
            self.update_unknown_metal_params()
        else:
            # Show standard metal options
            self.unknown_metal_frame.grid_forget()
            self.standard_metal_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")

    def update_unknown_metal_params(self, *args):
        """Update unknown metal parameters from GUI inputs."""
        # Retrieve values from GUI
        thickness = float(self.unknown_thickness_entry.get())
        f0 = float(self.f0_var.get())
        gamma0 = float(self.gamma0_var.get())
        wp = float(self.wp_var.get())
        
        # Update settings
        self.settings["metal_layers"] = [
            {"thickness": thickness, "f0": f0, "gamma0": gamma0, "wp": wp}
        ]
        layer = [thickness, "Drude", [f0, wp, gamma0]]
        self.metal_layers = [layer]  # Replace any existing layers
        

    def fit_drude_to_data(self):
        """Fit Drude parameters to match the raw reflectance data"""
        if not hasattr(self.plotter, 'raw_data') or self.plotter.raw_data is None:
            messagebox.showerror("Error", "No raw data uploaded to match against")
            return
            
        try:
            # Disable button during fitting
            self.match_btn.configure(state="disabled")
            
            # Create loading window
            self.loading_window = tb.Toplevel(self.root)
            self.loading_window.title("Fitting Drude Parameters")
            self.loading_window.geometry("400x200")
            self.loading_window.resizable(False, False)
            
            # Add progress bar and status
            tb.Label(self.loading_window, 
                    text="Fitting Drude parameters to raw data...",
                    font=('Helvetica', 10)).pack(pady=10)
            
            self.progress_bar = tb.Progressbar(
                self.loading_window,
                orient="horizontal",
                length=300,
                mode="determinate",
                bootstyle="success-striped"
            )
            self.progress_bar.pack(pady=10)
            
            self.status_label = tb.Label(
                self.loading_window,
                text="Initializing optimization...",
                wraplength=380
            )
            self.status_label.pack(pady=10)
            
            # Cancel button
            tb.Button(
                self.loading_window,
                text="Cancel",
                command=self.cancel_fitting,
                bootstyle="danger"
            ).pack(pady=10)
            
            # Get current configuration
            angle = float(self.angle_entry.get())
            polarization = self.polarization_var.get()
            dbr_stack, _, substrate_layer = self.get_layers()
            thickness = float(self.unknown_thickness_entry.get())
            
            # Run fitting in background thread
            self.cancel_fitting_flag = False
            self.fit_progress_value = 0
            self.fit_status_message = "Starting optimization..."
            
            self.fit_thread = threading.Thread(
                target=self._perform_drude_fitting,
                args=(angle, polarization, thickness, dbr_stack, substrate_layer),
                daemon=True
            )
            self.fit_thread.start()
            
            # Start progress updater
            self.update_progress()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid parameters: {str(e)}")
            if hasattr(self, 'loading_window'):
                self.loading_window.destroy()
            self.match_btn.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            if hasattr(self, 'loading_window'):
                self.loading_window.destroy()
            self.match_btn.configure(state="normal")

    def cancel_fitting(self):
        """Cancel the fitting process"""
        self.cancel_fitting_flag = True
        if hasattr(self, 'loading_window'):
            self.loading_window.destroy()
        self.match_btn.configure(state="normal")

    def update_progress(self):
        """Update the progress bar during fitting"""
        if hasattr(self, 'loading_window') and self.loading_window.winfo_exists():
            try:
                # Update progress bar and status
                self.progress_bar["value"] = self.fit_progress_value
                self.status_label.config(text=self.fit_status_message)
                
                if self.fit_progress_value < 100 and not self.cancel_fitting_flag:
                    self.root.after(200, self.update_progress)
                else:
                    self.loading_window.destroy()
                    self.match_btn.configure(state="normal")
            except:
                pass

    def _perform_drude_fitting(self, angle, polarization, thickness, dbr_stack, substrate_layer):
        """Perform the actual Drude parameter fitting"""
        try:
            from scipy.optimize import minimize
            
            # Get raw data
            raw_wavelength = pd.to_numeric(self.plotter.raw_data['wavelength'].values, errors='coerce')
            raw_reflectance = pd.to_numeric(self.plotter.raw_data['reflectance'].values, errors='coerce')
            
            # Remove any NaN values
            valid_mask = ~(np.isnan(raw_wavelength)) | ~(np.isnan(raw_reflectance))
            raw_wavelength = raw_wavelength[valid_mask]
            raw_reflectance = raw_reflectance[valid_mask]
            
            if len(raw_wavelength) == 0:
                raise ValueError("No valid data points in raw data")
                
            # Initial guess
            x0 = np.array([
                float(self.f0_var.get()), 
                float(self.wp_var.get()), 
                float(self.gamma0_var.get())
            ])
        
            # Bounds for parameters (f0, wp, gamma0)
            bounds = [(0.1, 20), (1, 20), (0.01, 5)]
            
            # Progress callback
            def progress_callback(xk, state=None):
                self.fit_progress_value = (state.nit / state.maxiter) * 100
                self.fit_status_message = (
                    f"Iteration {state.nit}/{state.maxiter}\n"
                    f"Current error: {state.fun:.4f}\n"
                    f"Parameters: f₀={xk[0]:.2f}, ωₚ={xk[1]:.2f}, Γ₀={xk[2]:.2f}"
                )
            
            # Optimized objective function with caching
            def objective(params):
                if self.cancel_fitting_flag:
                    raise RuntimeError("Fitting cancelled by user")
                    
                try:
                    # Get reflectance from cache or compute
                    f0, wp, gamma0 = params
                    R0 = self.get_cached_reflectance(f0, wp, gamma0, raw_wavelength)
                    
                    # Calculate mean squared error
                    error = np.mean((R0 - raw_reflectance)**2)
                    return error
                    
                except Exception as e:
                    print(f"Error in objective function: {str(e)}")
                    return np.inf

            # Run optimization
            result = minimize(
                objective,
                x0,
                bounds=bounds,
                method='L-BFGS-B',
                callback=progress_callback,
                options={
                    'maxiter': 50,
                    'disp': True,
                    'ftol': 1e-4,
                    'eps': 0.1
                }
            )
            
            # Update UI with results
            if not self.cancel_fitting_flag:
                self.root.after(0, lambda: self._update_fitted_params(result.x))
                    
        except Exception as err:
            self.root.after(0, lambda err=err: messagebox.showerror("Fitting Error", str(err)))
        finally:
            self.fit_progress_value = 100
            self.root.after(0, lambda: self.match_btn.configure(state="normal"))
            if hasattr(self, 'loading_window'):
                self.root.after(0, lambda: self.loading_window.destroy())
                
    def _update_fitted_params(self, params):
        """Update the UI with fitted parameters"""
        f0, wp, gamma0 = params
        
        # Update variables and sliders
        self.f0_var.set(round(f0, 3))
        self.wp_var.set(round(wp, 3))
        self.gamma0_var.set(round(gamma0, 3))
        
        # Update plot
        if self.plotter and hasattr(self.plotter, 'current_plot'):
            angle = float(self.angle_entry.get())
            polarization = self.polarization_var.get()
            self.plot_reflectance()
        
        # Show success message
        success_msg = (
            f"Fitted Drude Parameters:\n"
            f"f₀ = {round(f0, 3)}\n"
            f"ωₚ = {round(wp, 3)}\n"
            f"Γ₀ = {round(gamma0, 3)}\n\n"
            f"These values have been automatically applied."
        )
        messagebox.showinfo("Success", success_msg)


    def add_metal_layer(self):
        try:
            thickness = float(self.metal_thickness_entry.get())
            metal = self.metal_material_var.get()
            delta_n = float(self.delta_n_entry.get())
            delta_alpha = float(self.delta_alpha_entry.get())

            delta_omega_p = float(self.delta_omega_p_entry.get())
            delta_f = float(self.delta_f_entry.get())
            delta_gamma = float(self.delta_gamma_entry.get())
            delta_omega = float(self.delta_omega_entry.get())

            layer = [thickness, "Lorentz-Drude", [metal, delta_n, delta_alpha, delta_omega_p, delta_f, delta_gamma, delta_omega]]

            self.metal_layers.append(layer)

            self.metal_layer_list.insert(tk.END, (
                f"{metal} - {thickness} nm, "
                f"Δn={delta_n}, Δα={delta_alpha}, "
                f"Δωp={delta_omega_p}, Δf={delta_f}, "
                f"ΔΓ={delta_gamma}, Δω={delta_omega}"
            ))

            messagebox.showinfo("Success", "Metal layer added successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for all parameters.")

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
            self.metal_layer_list.insert(index, (
                f"{layer[2][0]} - {layer[0]} nm, "
                f"Δn={layer[2][1]}, Δα={layer[2][2]}, "
                f"Δωp={layer[2][3]}, Δf={layer[2][4]}, "
                f"ΔΓ={layer[2][5]}, Δω={layer[2][6]}"
            ))
            
            messagebox.showinfo("Success", "Metal layer updated successfully!")
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
        messagebox.showinfo("Success", "Metal layer deleted successfully!")

    def clear_metal_layers(self):
        self.metal_layers.clear()
        self.metal_layer_list.delete(0, tk.END)
        messagebox.showinfo("Success", "All metal layers cleared!")
        
    def setup_incidence_inputs(self):
        # Create a frame for incidence angle and polarization
        incidence_frame = tb.LabelFrame(
            self.config_tab,
            text="Incidence Parameters",
            bootstyle="primary"
        )
        incidence_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10, columnspan=2)
        
        # Incidence Angle (for main reflectance plot)
        tb.Label(incidence_frame, text="Incidence Angle (degrees):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.angle_entry = tb.Entry(incidence_frame, width=10)
        self.angle_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.angle_entry.insert(0, "0")
        
        # Wavelength for angle dependence plot (initially hidden)
        self.wavelength_frame = tb.Frame(incidence_frame)
        self.wavelength_label = tb.Label(self.wavelength_frame, text="Wavelength (μm) for Angle Plot:")
        self.wavelength_entry = tb.Entry(incidence_frame, width=10, validate="key")
        self.wavelength_entry['validatecommand'] = (self.wavelength_entry.register(self.validate_numeric_input), '%P')
        self.wavelength_entry.insert(0, "4.0")
        
        # Polarization
        polarization_frame = tb.Frame(incidence_frame)
        polarization_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        tb.Label(polarization_frame, text="Polarization:").pack(side=tk.LEFT, padx=5)
        
        self.polarization_var = tk.StringVar(value="s")
        s_radio = tb.Radiobutton(
            polarization_frame,
            text="s-polarization",
            variable=self.polarization_var,
            value="s",
            bootstyle="primary-toolbutton"
        )
        s_radio.pack(side=tk.LEFT, padx=5)
        
        p_radio = tb.Radiobutton(
            polarization_frame,
            text="p-polarization",
            variable=self.polarization_var,
            value="p",
            bootstyle="primary-toolbutton"
        )
        p_radio.pack(side=tk.LEFT, padx=5)

    def validate_numeric_input(self, text):
        if text == "":
            return True
        try:
            float(text)
            return True
        except ValueError:
            return False

    def toggle_angle_dependence_inputs(self, show):
        """Show/hide wavelength input based on angle dependence plot visibility"""
        if show:
            self.wavelength_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.wavelength_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            self.wavelength_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        else:
            self.wavelength_frame.grid_forget()

    def get_layers(self): 
        self.update_manual_mode_state()
        if self.manual_mode_active:
            # Process manual layers
            manual_layers = []
            for layer in self.manual_layers:
                try:
                    thickness = float(layer['thickness_entry'].get())
                except ValueError:
                    print(f"Warning: Invalid thickness entry. Skipping this layer.")
                    continue
                # Get material properties from the layer's input frame
                material_properties = self._get_material_properties(layer)
                
                # Add each material component based on composition percentage
                for mat_type, n, k, percent in material_properties:
                    if percent > 0:  # Only add if composition percentage > 0
                        sublayer_thickness = thickness * (percent / 100)
                        manual_layers.append([sublayer_thickness, "Constant", [n, k]])

            # Add metal layer from manual Drude parameters if specified and enabled
            if self.include_metal_var.get():
                try:
                    metal_thickness = float(self.manual_metal_thickness.get())
                    f0 = float(self.manual_f0_var.get())
                    gamma0 = float(self.manual_gamma0_var.get())
                    wp = float(self.manual_wp_var.get())
                    
                    metal_layer = [metal_thickness, "Drude", [f0, wp, gamma0]]
                    manual_layers.insert(0, metal_layer)  # Add metal layer at the beginning
                except ValueError:
                    print("Warning: Invalid metal layer parameters - skipping")
                    
            # Substrate handling for manual mode
            substrate_material = (
                "GaSb_ln" if self.substrate_var.get() == "GaSb"
                else "GaAs_ln" if self.substrate_var.get() == "GaAs"
                else [1.0, 0.0] if self.substrate_var.get() == "Air"
                else float('nan')
            )            
            # Get substrate thickness - this was the missing part
            substrate_thickness = float('nan')  # Default to semi-infinite
            if self.manual_is_finite_substrate.get():
                try:
                    substrate_thickness = float(self.manual_substrate_thickness.get())
                except ValueError:
                    print(f"Warning: Invalid substrate thickness entry. Using NaN.")
                    substrate_thickness = float('nan')
                    
            substrate_layer = [[substrate_thickness, "Constant", substrate_material]]

            return [], manual_layers, substrate_layer     

        else:
            # Predefined DBR layer setup
            substrate_material = (
                "GaSb_ln" if self.substrate_var.get() == "GaSb"
                else "GaAs_ln" if self.substrate_var.get() == "GaAs"
                else [1.0, 0.0] if self.substrate_var.get() == "Air"
                else float('nan')
            )
            try:
                substrate_thickness = float(self.substrate_thickness.get()) if self.is_finite_substrate.get() else float('nan')
            except ValueError:
                print(f"Warning: Invalid substrate thickness entry: '{self.substrate_thickness.get()}'. Using NaN.")
                substrate_thickness = float('nan')
            substrate_layer = [[substrate_thickness, "Constant", substrate_material]]

            try:
                dbr_period = int(self.dbr_period_entry.get())
            except ValueError:
                print(f"Warning: Invalid DBR period entry: '{self.dbr_period_entry.get()}'. Using 0.")
                dbr_period = 0

            dbr_stack = []
            for layer in self.dbr_layers:
                if isinstance(layer, dict):  # Check if layer is a dictionary
                    material = layer.get('material', '')
                    thickness = layer.get('thickness', 0)
                    layer_type = layer.get('type', 'Constant')
                    
                    if material == "GaSb":
                        dbr_stack.append([thickness, layer_type, [3.816, 0.0]])
                    elif material == "AlAsSb":
                        dbr_stack.append([thickness, layer_type, [3.101, 0.0]])
                    elif material == "AlGaSb":
                        # Default to x=0.3 (Al₀.₃Ga₀.₇Sb) if composition is not specified
                        dbr_stack.append([thickness, layer_type, [4.106, 0.0]])  # Approximate n at 1.5 eV
                    else:
                        dbr_stack.append([thickness, layer_type, [1.0, 0.0]])
                else:  # Handle legacy list format
                    if len(layer) >= 3 and layer[2] == "GaSb_ln":
                        dbr_stack.append([layer[0], layer[1], [3.816, 0.0]])
                    elif len(layer) >= 3 and layer[2] == "AlAsSb_ln":
                        dbr_stack.append([layer[0], layer[1], [3.101, 0.0]])
                    elif len(layer) >= 3 and layer[2] == "AlGaSb_ln":
                        dbr_stack.append([layer[0], layer[1], [4.106, 0.0]])  # Default x=0.3
                    else:
                        dbr_stack.append([layer[0], layer[1], [1.0, 0.0]])

            # Repeat the DBR stack for the specified number of periods
            dbr_stack = dbr_stack * dbr_period if dbr_period > 0 else []

            # Metal layers handling
            metal_layers = []
            if self.unknown_metal_var.get():
                try:
                    thickness = float(self.unknown_thickness_entry.get())
                    f0 = float(self.f0_var.get())
                    wp = float(self.wp_var.get())
                    gamma0 = float(self.gamma0_var.get())
                    metal_layers = [[thickness, "Drude", [f0, wp, gamma0]]]
                except ValueError:
                    print("Warning: Invalid metal layer parameters - skipping")

            return dbr_stack, metal_layers, substrate_layer


    def _get_material_properties(self, layer):
        """Extract material properties from a layer's input frame"""
        properties = []
        
        for child in layer['material_inputs'].winfo_children():
            if isinstance(child, tb.Frame):
                material_type = layer['type_var'].get()
                
                if material_type == "Semiconductor":
                    # Get semiconductor properties
                    for widget in child.winfo_children():
                        if isinstance(widget, ttk.Combobox):
                            material = widget.get()
                        elif isinstance(widget, tb.Entry) and widget.cget("state") != "disabled":
                            try:
                                composition = float(widget.get())
                            except ValueError:
                                composition = 0
                    
                    # Get refractive indices based on material and composition
                    n, k = self._get_semiconductor_refractive_index(material, composition, wavelength_nm=global_wavelength_array)
                    properties.append(("Semiconductor", n, k, composition))
                    
                elif material_type == "Metal":
                    # Get metal properties
                    for widget in child.winfo_children():
                        if isinstance(widget, ttk.Combobox):
                            metal = widget.get()
                        elif isinstance(widget, tb.Entry):
                            try:
                                composition = float(widget.get())
                            except ValueError:
                                composition = 100  # Default to pure metal
                    
                    # Get metal optical constants
                    n, k = self._get_metal_refractive_index(metal)
                    properties.append(("Metal", n, k, composition))
                    
                elif material_type == "Dielectric":
                    # Get dielectric properties
                    n_entry = None
                    k_entry = None
                    for widget in child.winfo_children():
                        if isinstance(widget, tb.Entry):
                            if "Dielectric Constant" in str(widget.master.winfo_children()[0].cget("text")):
                                n_entry = widget
                            elif "Extinction Coefficient" in str(widget.master.winfo_children()[0].cget("text")):
                                k_entry = widget
                    
                    try:
                        n = float(n_entry.get()) if n_entry else 1.0
                        k = float(k_entry.get()) if k_entry else 0.0
                        properties.append(("Dielectric", n, k, 100))  # 100% composition
                    except ValueError:
                        print("Warning: Invalid dielectric constants - using n=1.0, k=0.0")
                        properties.append(("Dielectric", 1.0, 0.0, 100))
        
        return properties

    def _get_semiconductor_refractive_index(self, material, composition, wavelength_nm):
      
        """Return refractive index (n,k) for semiconductor materials with composition dependence"""
        # Convert composition percentage to fraction (0-1)
        x = composition / 100.0
        
        if material == "GaAs":
            # Pure GaAs from Adachi 1989
            return (3.3, 0.0)  # n=3.3, k=0 at ~2.0 eV
            
        elif material == "AlGaAs":
            # Calculate Al(x)Ga(1-x)As refractive index 
            # Using data from batop.de (https://batop.de/information/n_AlGaAs.html#), with linear interpolation between points
            # Create wavelength array (from 2 µm to 16 µm, 10 nm step)
            if x < 0 or x > 1:
                raise ValueError("Aluminum fraction x must be between 0 and 1.")

            wl = np.array(wavelength_nm) 
            energy_eV = 1239.84 / wl  # Convert wavelength to energy

            # Calculate energy gap
            if x > 0.45:
                energy_gap = 1.9 + 0.125 * x + 0.143 * x**2
            else:
                energy_gap = 1.422 + 1.2475 * x

            # Identify where absorption occurs
            absorbing = energy_eV >= energy_gap

            # Intermediate chi terms
            chi = energy_eV / (1.425 + 1.155 * x + 0.37 * x**2)
            chio = energy_eV / (1.765 + 1.115 * x + 0.37 * x**2)

            # Avoid invalid sqrt of (1 - chi), clip inside [-1, 1] range
            chi = np.clip(chi, -0.999, 0.999)
            chio = np.clip(chio, -0.999, 0.999)

            # f and fo terms
            f = (2 - np.sqrt(1 + chi) - np.sqrt(1 - chi)) / (chi**2)
            fo = (2 - np.sqrt(1 + chio) - np.sqrt(1 - chio)) / (chio**2)

            # Bruch coefficient
            bruch = 0.5 * np.sqrt(
                ((1.425 + 1.155 * x + 0.37 * x**2) /
                (1.765 + 1.115 * x + 0.37 * x**2)) ** 3
            )

            # Final refractive index
            n_squared_term = (6.3 + 19.0 * x) * (f + bruch * fo) + (9.4 - 10.2 * x)
            n = np.sqrt(n_squared_term)

            # Set k = 0 for non-absorbing regions, or NaN if absorbing
            k = np.zeros_like(n)
            n[absorbing] = np.nan  # or optionally keep as-is
            k[absorbing] = np.nan  # if you want to mark absorbing wavelengths

            return (n, k)

        elif material == "GaSb":
            # Pure GaSb from Adachi 1989
            return (3.8, 0.0)  # n=3.8 at ~1.5 eV
            
        elif material == "AlAsSb":
            # AlAs(x)Sb(1-x) refractive index with wavelength dependence
            # Using multiple empirical relations from Gupta, Moss, Herve, Ravindra, and Reddy
            
            wl = np.array(wavelength_nm) 
            
            # Calculate energy in eV
            energy_eV = 1239.84 / wl  # hc/E conversion
            
            # Bandgap calculation for AlAsSb (from https://www.sciencedirect.com/science/article/pii/S0749603613000931)
            Eg = 1.615 * x + 0.73 * (1-x) - 0.5 * x * (1-x)  # Vegard's law with bowing
            
            # Initialize arrays
            n_vals = np.zeros_like(wl)
            k_vals = np.zeros_like(wl)
            
            # Apply all empirical relations
            for i, (wl_i, E_i) in enumerate(zip(wl, energy_eV)):
                # Gupta and Ravindra relation
                n_gupta = 4.084 - 0.62 * Eg
                
                # Moss formula (n^4 Eg = k, where k ≈ 95 is typical)
                n_moss = (95 / Eg)**0.25 if Eg > 0 else n_gupta
                
                # Herve and Vandamme
                n_herve = np.sqrt(1 + (13.6/(Eg + 3.4))**2)
                
                # Ravindra relation
                n_ravindra = 4.16 - 0.85 * Eg
                
                # Reddy and Ahammed
                n_reddy = ((154/(Eg - 0.365)))**0.25 if Eg > 0.365 else n_gupta
                
                # Take average of all valid relations
                valid_estimates = [n for n in [n_gupta, n_moss, n_herve, n_ravindra, n_reddy] if not np.isnan(n)]
                n_vals[i] = np.mean(valid_estimates) if valid_estimates else 3.5  # fallback
                
                # Calculate k if above bandgap
                if E_i >= Eg:
                    # Simple approximation for absorption coefficient
                    alpha = 1e4 * np.sqrt(E_i - Eg)  # cm^-1
                    k_vals[i] = (alpha * wl_i * 1e-7) / (4 * np.pi)
                else:
                    k_vals[i] = 0.0
            
            # Return as tuple (n, k)
            if len(n_vals) == 1:
                return (float(n_vals[0]), float(k_vals[0]))
            return (n_vals, k_vals)

        elif material == "InSb":
            # From the first dataset you provided (Mikhail Polyanskiy)
            # At ~1.5 eV (827 nm)
            n, k = 3.8, 0.0
            return(n,k)
           
        elif material == "AlSb":
            # From the second dataset you provided (Mikhail Polyanskiy)
            # At ~2.0 eV (620 nm)
            n, k = 3.1, 0.0
            return(n,k)

        elif material == "InAs":
            # From the third dataset you provided (Mikhail Polyanskiy)
            # At ~1.5 eV (827 nm)
            n, k = 3.5, 0.0
            return(n,k)
        elif material == "InAsSb":
            # For InAs(x)Sb(1-x), interpolate between InAs and InSb

                x = composition / 100.0
                # InSb (x=0) parameters
                n_InSb = 3.8
                k_InSb = 0.0
                
                # InAs (x=1) parameters
                n_InAs = 3.5
                k_InAs = 0.0
                
                # Linear interpolation
                n = n_InSb + (n_InAs - n_InSb) * x
                k = k_InSb + (k_InAs - k_InSb) * x
                return (n, k)
        elif material == "AlGaSb":
            # data from R. Ferrini et al., Optical functions from 0.02 to 6 eV of AlxGa1-xSb/GaSb epitaxial layers
            # Al(x)Ga(1-x)Sb implementation based on provided data
            # We'll implement two approaches:
            # 1. For energies below E0 (fundamental gap): Use Sellmeier equation
            # 2. For energies above E0: Use interpolation of tabulated data

            wavelength_um_array = wavelength_nm / 1000.0

            energy_eV_array = 1.2398 / wavelength_um_array

            # Output arrays
            n_array = np.zeros_like(energy_eV_array)
            k_array = np.zeros_like(energy_eV_array)

            data_points = [
                    # x=0.0 (GaSb)
                    [0.0, 0.5, 3.846, 0.0],
                    [0.0, 0.6, 3.878, 0.0],
                    [0.0, 0.7, 3.959, 0.023],
                    [0.0, 0.8, 4.010, 0.125],
                    [0.0, 0.9, 4.026, 0.145],
                    [0.0, 1.0, 4.050, 0.173],
                    [0.0, 1.1, 4.096, 0.201],
                    [0.0, 1.2, 4.140, 0.225],
                    [0.0, 1.3, 4.200, 0.268],
                    [0.0, 1.4, 4.270, 0.299],
                    [0.0, 1.5, 4.370, 0.338],
                    [0.0, 1.6, 4.500, 0.407],
                    [0.0, 1.7, 4.644, 0.514],
                    [0.0, 1.8, 4.822, 0.647],
                    [0.0, 1.9, 5.037, 0.881],
                    [0.0, 2.0, 5.197, 1.465],
                    [0.0, 2.1, 4.630, 1.843],
                    [0.0, 2.2, 4.470, 1.770],
                    [0.0, 2.3, 4.455, 1.812],
                    [0.0, 2.4, 4.464, 2.000],
                    [0.0, 2.5, 4.235, 2.289],
                    [0.0, 2.6, 3.946, 2.268],
                    [0.0, 2.7, 3.816, 2.190],
                    [0.0, 2.8, 3.755, 2.148],
                    [0.0, 2.9, 3.740, 2.116],
                    [0.0, 3.0, 3.751, 2.119],
                    # x=0.1
                    [0.1, 0.5, 3.765, 0.0],
                    [0.1, 0.6, 3.781, 0.0],
                    [0.1, 0.7, 3.807, 0.0],
                    [0.1, 0.8, 3.861, 0.014],
                    [0.1, 0.9, 3.942, 0.094],
                    [0.1, 1.0, 3.952, 0.125],
                    [0.1, 1.1, 3.983, 0.148],
                    [0.1, 1.2, 4.031, 0.162],
                    [0.1, 1.3, 4.110, 0.184],
                    [0.1, 1.4, 4.183, 0.217],
                    [0.1, 1.5, 4.262, 0.268],
                    [0.1, 1.6, 4.393, 0.309],
                    [0.1, 1.7, 4.529, 0.372],
                    [0.1, 1.8, 4.697, 0.487],
                    [0.1, 1.9, 4.917, 0.675],
                    [0.1, 2.0, 5.154, 1.025],
                    [0.1, 2.1, 5.087, 1.729],
                    [0.1, 2.2, 4.568, 1.804],
                    [0.1, 2.3, 4.483, 1.792],
                    [0.1, 2.4, 4.461, 1.897],
                    [0.1, 2.5, 4.425, 2.142],
                    [0.1, 2.6, 4.100, 2.327],
                    [0.1, 2.7, 3.893, 2.247],
                    [0.1, 2.8, 3.804, 2.200],
                    [0.1, 2.9, 3.768, 2.181],
                    [0.1, 3.0, 3.758, 2.164],
                    # x=0.3
                    [0.3, 0.5, 3.637, 0.0],
                    [0.3, 0.6, 3.645, 0.0],
                    [0.3, 0.7, 3.657, 0.0],
                    [0.3, 0.8, 3.674, 0.0],
                    [0.3, 0.9, 3.702, 0.0],
                    [0.3, 1.0, 3.751, 0.0],
                    [0.3, 1.1, 3.863, 0.033],
                    [0.3, 1.2, 3.906, 0.075],
                    [0.3, 1.3, 3.946, 0.109],
                    [0.3, 1.4, 4.015, 0.125],
                    [0.3, 1.5, 4.106, 0.133],
                    [0.3, 1.6, 4.249, 0.174],
                    [0.3, 1.7, 4.373, 0.240],
                    [0.3, 1.8, 4.515, 0.361],
                    [0.3, 1.9, 4.679, 0.497],
                    [0.3, 2.0, 4.853, 0.674],
                    [0.3, 2.1, 5.053, 0.974],
                    [0.3, 2.2, 5.127, 1.539],
                    [0.3, 2.3, 4.636, 1.845],
                    [0.3, 2.4, 4.489, 1.833],
                    [0.3, 2.5, 4.453, 1.909],
                    [0.3, 2.6, 4.419, 2.101],
                    [0.3, 2.7, 4.180, 2.318],
                    [0.3, 2.8, 3.959, 2.286],
                    [0.3, 2.9, 3.870, 2.259],
                    [0.3, 3.0, 3.829, 2.249],
                    # x=0.5
                    [0.5, 0.5, 3.508, 0.0],
                    [0.5, 0.6, 3.514, 0.0],
                    [0.5, 0.7, 3.523, 0.0],
                    [0.5, 0.8, 3.535, 0.0],
                    [0.5, 0.9, 3.551, 0.0],
                    [0.5, 1.0, 3.575, 0.0],
                    [0.5, 1.1, 3.610, 0.0],
                    [0.5, 1.2, 3.667, 0.0],
                    [0.5, 1.3, 3.778, 0.0],
                    [0.5, 1.4, 3.895, 0.004],
                    [0.5, 1.5, 3.970, 0.017],
                    [0.5, 1.6, 4.063, 0.033],
                    [0.5, 1.7, 4.176, 0.067],
                    [0.5, 1.8, 4.289, 0.098],
                    [0.5, 1.9, 4.475, 0.155],
                    [0.5, 2.0, 4.720, 0.265],
                    [0.5, 2.1, 4.989, 0.525],
                    [0.5, 2.2, 5.112, 0.970],
                    [0.5, 2.3, 5.031, 1.426],
                    [0.5, 2.4, 4.632, 1.702],
                    [0.5, 2.5, 4.483, 1.605],
                    [0.5, 2.6, 4.552, 1.716],
                    [0.5, 2.7, 4.491, 1.943],
                    [0.5, 2.8, 4.302, 2.147],
                    [0.5, 2.9, 4.105, 2.146],
                    [0.5, 3.0, 4.030, 2.149]
                ]
 
            x_values = sorted(list(set(pt[0] for pt in data_points)))

            # Preprocess data by x
            data_by_x = {xv: [] for xv in x_values}
            for pt in data_points:
                data_by_x[pt[0]].append(pt)


            # First calculate E0 (fundamental gap) for this composition
            E0 = 0.738 + 1.247 * x  # From linear relation in paper

            for i, energy_eV in enumerate(energy_eV_array):

                if energy_eV < E0:
                    # Use Sellmeier equation
                    A = 14.07 - 4.80*x - 0.66*x*x
                    B = 0.458 - 0.099*x + 1.258*x*x
                    C = 1.486 - 2.308*x + 1.973*x*x  # in microns
                    λ = wavelength_um_array[i]
                    n_squared = A + B * λ**2 / (λ**2 - C**2)
                    n_array[i] = np.sqrt(n_squared)
                    k_array[i] = 0.0
                
                else:
                    # Bilinear interpolation in x and energy
                    lower_x = max([xv for xv in x_values if xv <= x])
                    upper_x = min([xv for xv in x_values if xv >= x])

                    def interpolate_energy(x_data, energy):
                        energies = [pt[1] for pt in x_data]
                        n_vals = [pt[2] for pt in x_data]
                        k_vals = [pt[3] for pt in x_data]

                        lower_e = max([e for e in energies if e <= energy])
                        upper_e = min([e for e in energies if e >= energy])

                        if lower_e == upper_e:
                            idx = energies.index(lower_e)
                            return n_vals[idx], k_vals[idx]
                        else:
                            idx_l = energies.index(lower_e)
                            idx_u = energies.index(upper_e)
                            t = (energy - lower_e) / (upper_e - lower_e)
                            n = n_vals[idx_l] + t * (n_vals[idx_u] - n_vals[idx_l])
                            k = k_vals[idx_l] + t * (k_vals[idx_u] - k_vals[idx_l])
                            return n, k

                    if lower_x == upper_x:
                        n, k = interpolate_energy(data_by_x[lower_x], energy_eV)
                    else:
                        n_lower, k_lower = interpolate_energy(data_by_x[lower_x], energy_eV)
                        n_upper, k_upper = interpolate_energy(data_by_x[upper_x], energy_eV)
                        t_x = (x - lower_x) / (upper_x - lower_x)
                        n = n_lower + t_x * (n_upper - n_lower)
                        k = k_lower + t_x * (k_upper - k_lower)

                    n_array[i] = n
                    k_array[i] = k

            return n_array, k_array
        else:
            return (1.0, 0.0)  # Default for unknown materials

    def _get_metal_refractive_index(self, metal):
        """Return refractive index (n,k) for common metals"""
        # These are example values at specific wavelengths - you should replace with proper data
        metal_indices = {
            "Ag": (0.15, 3.5),   # Silver at 600nm
            "Al": (1.5, 7.0),    # Aluminum at 600nm
            "Au": (0.2, 3.0),    # Gold at 600nm
            "Cu": (0.6, 2.5),    # Copper at 600nm
            # Add more metals as needed
        }
        return metal_indices.get(metal, (1.0, 0.0))  # Default if metal not found

    def _get_substrate_properties(self):
        """Return substrate optical properties"""
        substrate = self.substrate_var.get()
        if substrate == "GaSb":
            return [3.816, 0.0]
        elif substrate == "GaAs":
            return [3.3, 0.0]
        elif substrate == "Air":
            return [1.0, 0.0]
        else:
            return float('nan')
