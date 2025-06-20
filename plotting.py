#plotting.py
import numpy as np
import pandas as pd
import tkinter as tk
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from tkinter import messagebox
from utils import load_settings, save_settings
import Funcs as MF
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import BOTH
import ttkbootstrap as tb
from tkinter import ttk
import matplotlib.cm as cm

class PlotReflectance:
    def __init__(self, dbr_stack=None, metal_layers=None, substrate_layer=None, 
                 substrate_thickness=None, light_direction=None, right_frame=None, 
                 metal_thickness=None):
        
        self.dbr_stack = dbr_stack
        self.metal_layers = metal_layers
        self.substrate_layer = substrate_layer
        self.substrate_thickness = substrate_thickness
        self.light_direction = light_direction
        self.right_frame = right_frame
        self.metal_thickness = metal_thickness

        self.raw_data_line = None
        self.raw_data = None
        
        self.current_plot = None

        self.angle_curves = []  # To store angle dependence curves
        self.angle_colors = plt.cm.get_cmap('tab10', 10)  # Color cycle for curves
        self.current_color_index = 0
        
        # Unknown metal parameters
        self.unknown_metal_params = {
            'thickness': 50.0,  # Default thickness
            'f0': 1.0,
            'gamma0': 0.1,
            'wp': 9.0
        }
        
        # Current plot state
        self.current_plot = None
        
        # Initialize plots if right_frame is provided
        if right_frame:
            self.setup_plots(right_frame)

    def setup_plots(self, right_frame):
        """Initialize the matplotlib figures and canvas"""
        # Create a main container with scrollbar
        self.main_canvas = tk.Canvas(right_frame)
        self.scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all")
            )
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel for scrolling
        self.main_canvas.bind_all("<MouseWheel>", 
            lambda event: self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        # Create control buttons frame at the top
        control_frame = ttk.Frame(self.scrollable_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Add toggle buttons for different plots
        self.show_efield_var = tk.BooleanVar(value=False)
        efield_btn = tb.Checkbutton(
            control_frame,
            text="Show Electric Field",
            variable=self.show_efield_var,
            bootstyle="primary-round-toggle",
            command=self.toggle_electric_field
        )
        efield_btn.pack(side=tk.LEFT, padx=5)
        
        self.show_angle_var = tk.BooleanVar(value=False)
        angle_btn = tb.Checkbutton(
            control_frame,
            text="Show Angle Dependence",
            variable=self.show_angle_var,
            bootstyle="primary-round-toggle",
            command=self.toggle_angle_dependence
        )
        angle_btn.pack(side=tk.LEFT, padx=5)
        
        # Axis controls frame (only for main reflectance plot)
        self.axis_frame = ttk.Frame(self.scrollable_frame)
        self.axis_frame.pack(fill=tk.X, pady=5)
        
        tb.Label(self.axis_frame, text="X Range:").pack(side=tk.LEFT, padx=5)
        self.xmin_entry = tb.Entry(self.axis_frame, width=5)
        self.xmin_entry.insert(0, "2.5")
        self.xmin_entry.pack(side=tk.LEFT)
        
        tb.Label(self.axis_frame, text="to").pack(side=tk.LEFT)
        self.xmax_entry = tb.Entry(self.axis_frame, width=5)
        self.xmax_entry.insert(0, "12")
        self.xmax_entry.pack(side=tk.LEFT)
        
        tb.Label(self.axis_frame, text="Y Range:").pack(side=tk.LEFT, padx=5)
        self.ymin_entry = tb.Entry(self.axis_frame, width=5)
        self.ymin_entry.insert(0, "0")
        self.ymin_entry.pack(side=tk.LEFT)
        
        tb.Label(self.axis_frame, text="to").pack(side=tk.LEFT)
        self.ymax_entry = tb.Entry(self.axis_frame, width=5)
        self.ymax_entry.insert(0, "1")
        self.ymax_entry.pack(side=tk.LEFT)
        
        apply_btn = tb.Button(
            self.axis_frame,
            text="Apply Axis",
            command=self.apply_axis_ranges,
            bootstyle="info"
        )
        apply_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tb.Button(
            self.axis_frame,
            text="Reset Axis",
            command=self.reset_axis_ranges,
            bootstyle="secondary"
        )
        reset_btn.pack(side=tk.LEFT)
        
        # Absorption toggle
        self.show_absorption_var = tk.BooleanVar(value=True)
        absorption_btn = tb.Checkbutton(
            self.axis_frame,
            text="Show Absorption",
            variable=self.show_absorption_var,
            bootstyle="primary-round-toggle",
            command=self.toggle_absorption
        )
        absorption_btn.pack(side=tk.LEFT, padx=5)
        
        # Create the main reflectance figure (always visible)
        self.fig1 = plt.figure(figsize=(10, 5), dpi=100)
        self.ax1 = self.fig1.add_subplot(111)
        self.ax1.set_xticks(np.arange(2, 13, 1))
        self.ax1.set_yticks(np.linspace(0.0, 1.0, 11))
        self.ax1.set_xlim(2.5, 12)
        self.ax1.set_ylim(0.0, 1.0)
        self.ax1.set_xlabel("Wavelength (μm)")
        self.ax1.set_ylabel("Reflectance")
        self.ax1.set_title("Simulated Reflectance")
        self.ax1.grid(alpha=0.2)
        
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.scrollable_frame)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=15)
            
        # Create container for optional plots
        self.optional_plots_frame = ttk.Frame(self.scrollable_frame)
        
        # Electric field plot
        self.efield_frame = ttk.Frame(self.optional_plots_frame)
        self.fig2 = plt.figure(figsize=(10, 4), dpi=100)
        self.ax2 = self.fig2.add_subplot(111)
    
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_xticks(np.linspace(0, 7, 8))
        self.ax2.set_yscale("log")
        self.ax2.set_yticks(np.logspace(-5, 1, 7))
        self.ax2.set_xlim(0, 7)
        self.ax2.set_xlabel("Depth from the top (μm)")
        self.ax2.set_ylabel("Amplitude")
        self.ax2.set_title("Electric Field Decay")
        self.ax2.grid(alpha=0.2)
        
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.efield_frame)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=15)
        
        # Angle dependence plot 
        self.angle_frame = ttk.Frame(self.optional_plots_frame)
        self.fig3 = plt.figure(figsize=(10, 4), dpi=100)
        self.ax3 = self.fig3.add_subplot(111)
        self.ax3.set_xticks(np.arange(0, 91, 15))
        self.ax3.set_yticks(np.linspace(0.0, 1.0, 11))
        self.ax3.set_xlim(0, 90)
        self.ax3.set_ylim(0.0, 1.0)
        self.ax3.set_xlabel("Angle of Incidence (degrees)")
        self.ax3.set_ylabel("Reflectance")
        self.ax3.set_title("Angle-Dependent Reflectance")
        self.ax3.grid(alpha=0.2)
        
        self.canvas3 = FigureCanvasTkAgg(self.fig3, master=self.angle_frame)
        self.canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=15)
        
        # Angle plot axis controls
        self.angle_axis_frame = ttk.Frame(self.angle_frame)
        self.angle_axis_frame.pack(fill=tk.X, pady=5)

        tb.Label(self.angle_axis_frame, text="X Range:").pack(side=tk.LEFT, padx=5)
        self.angle_xmin_entry = tb.Entry(self.angle_axis_frame, width=5)
        self.angle_xmin_entry.insert(0, "0")
        self.angle_xmin_entry.pack(side=tk.LEFT)

        tb.Label(self.angle_axis_frame, text="to").pack(side=tk.LEFT)
        self.angle_xmax_entry = tb.Entry(self.angle_axis_frame, width=5)
        self.angle_xmax_entry.insert(0, "90")
        self.angle_xmax_entry.pack(side=tk.LEFT)

        tb.Label(self.angle_axis_frame, text="Y Range:").pack(side=tk.LEFT, padx=5)
        self.angle_ymin_entry = tb.Entry(self.angle_axis_frame, width=5)
        self.angle_ymin_entry.insert(0, "0")
        self.angle_ymin_entry.pack(side=tk.LEFT)

        tb.Label(self.angle_axis_frame, text="to").pack(side=tk.LEFT)
        self.angle_ymax_entry = tb.Entry(self.angle_axis_frame, width=5)
        self.angle_ymax_entry.insert(0, "1")
        self.angle_ymax_entry.pack(side=tk.LEFT)

        angle_apply_btn = tb.Button(
            self.angle_axis_frame,
            text="Apply Axis",
            command=self.apply_angle_axis_ranges,
            bootstyle="info"
        )
        angle_apply_btn.pack(side=tk.LEFT, padx=5)

        angle_reset_btn = tb.Button(
            self.angle_axis_frame,
            text="Reset Axis",
            command=self.reset_angle_axis_ranges,
            bootstyle="secondary"
        )
        angle_reset_btn.pack(side=tk.LEFT)
        
        # Button frame for optional plot actions
        self.efield_btn_frame = ttk.Frame(self.efield_frame)
        self.angle_btn_frame = ttk.Frame(self.angle_frame)
        
        # Add buttons for the optional plots
        self.plot_efield_btn = tb.Button(
            self.efield_btn_frame,
            text="Plot Electric Field",
            command=lambda: self.plot_electric_field_decay(self.ax2, self.canvas2),
            bootstyle="info"
        )
        self.plot_efield_btn.pack(side=tk.LEFT, padx=5)
        
        self.plot_angle_btn = tb.Button(
            self.angle_btn_frame,
            text="Plot Angle Dependence",
            command=self.plot_angle_dependence,
            bootstyle="info"
        )
        self.plot_angle_btn.pack(side=tk.LEFT, padx=5)
        
        # Add delete last curve button
        self.delete_last_angle_btn = tb.Button(
            self.angle_btn_frame,
            text="Delete Last Curve",
            command=self.clear_last_angle_curve,
            bootstyle="danger"
        )
        self.delete_last_angle_btn.pack(side=tk.LEFT, padx=5)
        
        self.fig1.tight_layout()
        self.fig2.tight_layout()
        self.fig3.tight_layout()
        
    def apply_angle_axis_ranges(self):
        """Apply custom axis ranges to angle plot"""
        try:
            xmin = float(self.angle_xmin_entry.get())
            xmax = float(self.angle_xmax_entry.get())
            ymin = float(self.angle_ymin_entry.get())
            ymax = float(self.angle_ymax_entry.get())
            
            if xmin >= xmax or ymin >= ymax:
                raise ValueError("Invalid range values")
                
            self.ax3.set_xlim(xmin, xmax)
            self.ax3.set_ylim(ymin, ymax)
            
            # Update ticks for better readability
            x_ticks = np.linspace(xmin, xmax, num=min(7, int(xmax-xmin)+1))
            y_ticks = np.linspace(ymin, ymax, num=11)
            
            self.ax3.set_xticks(x_ticks)
            self.ax3.set_yticks(y_ticks)
            
            self.canvas3.draw()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid axis range: {str(e)}")

    def reset_angle_axis_ranges(self):
        """Reset angle plot axis ranges to defaults"""
        self.angle_xmin_entry.delete(0, tk.END)
        self.angle_xmin_entry.insert(0, "0")
        self.angle_xmax_entry.delete(0, tk.END)
        self.angle_xmax_entry.insert(0, "90")
        self.angle_ymin_entry.delete(0, tk.END)
        self.angle_ymin_entry.insert(0, "0")
        self.angle_ymax_entry.delete(0, tk.END)
        self.angle_ymax_entry.insert(0, "1")
        
        self.ax3.set_xlim(0, 90)
        self.ax3.set_ylim(0.0, 1.0)
        self.ax3.set_xticks(np.arange(0, 91, 15))
        self.ax3.set_yticks(np.linspace(0.0, 1.0, 11))
        self.canvas3.draw()

    def toggle_electric_field(self):
        if self.show_efield_var.get():
            self.efield_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.efield_btn_frame.pack(fill=tk.X, pady=5)
            self.optional_plots_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.efield_frame.pack_forget()
            if not self.show_angle_var.get():
                self.optional_plots_frame.pack_forget()

    def toggle_angle_dependence(self):
        if self.show_angle_var.get():
            self.angle_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            self.angle_btn_frame.pack(fill=tk.X, pady=5)
            self.optional_plots_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.angle_frame.pack_forget()
            if not self.show_efield_var.get():
                self.optional_plots_frame.pack_forget()

    def toggle_absorption(self):
        """Toggle absorption curve visibility"""
        if hasattr(self, 'ax1'):
            for line in self.ax1.get_lines():
                if line.get_label() == 'Absorption':
                    line.set_visible(self.show_absorption_var.get())
            self.canvas.draw_idle()

    def clear_last_angle_curve(self):
        """Remove the last angle dependence curve from the plot"""
        if self.angle_curves:
            last_curve = self.angle_curves.pop()
            last_curve.remove()
            self.canvas3.draw()
            
    def get_layer_description(self):
        """Generate a descriptive label for the current layer stack"""
        layers = []
        
        # Check if we're in manual mode
        if hasattr(self.layer_config, 'manual_mode_active') and self.layer_config.manual_mode_active:
            # Process manual layers
            for layer in self.layer_config.manual_layers:
                try:
                    thickness = float(layer['thickness_entry'].get())
                    layer_type = layer['type_var'].get()
                    
                    # Get material name from the combobox if available
                    material = "Unknown"
                    for child in layer['material_inputs'].winfo_children():
                        if hasattr(child, 'material_var'):
                            material = child.material_var.get()
                            break
                    
                    layers.append(f"{thickness:.0f}nm {material}")
                except:
                    continue
            
            # Add metal layer if enabled
            if (hasattr(self.layer_config, 'include_metal_var') and self.layer_config.include_metal_var.get()):
                try:
                    thickness = float(self.layer_config.manual_metal_thickness.get())
                except:
                    pass
        else:
            # Process standard configuration layers
            dbr_stack, metal_layers, substrate_layer = self.layer_config.get_layers()
            
            # Process metal layers
            for layer in metal_layers:
                thickness = layer[0]
                if layer[1] == "Drude":
                    layers.append(f"{thickness:.0f}nm Drude")
                else:
                    material = layer[2][0] if isinstance(layer[2], (list, tuple)) and len(layer[2]) > 0 else "Unknown"
                    layers.append(f"{thickness:.0f}nm {material}")
            
            # Process DBR layers
            for layer in dbr_stack:
                thickness = layer[0]
                material = layer[2][0] if isinstance(layer[2], (list, tuple)) and len(layer[2]) > 0 else "Unknown"
                layers.append(f"{thickness:.0f}nm {material}")
        
        return "/".join(layers)
    
    def plot_angle_dependence(self):
        """Plot reflectance vs angle of incidence at a fixed wavelength"""
        try:
            # Get wavelength from appropriate entry based on mode
            if hasattr(self.layer_config, 'manual_mode_active') and self.layer_config.manual_mode_active:
                wavelength_entry = self.layer_config.wavelength_entry
            else:
                wavelength_entry = self.layer_config.wavelength_entry
                
            wavelength = float(wavelength_entry.get())
            if wavelength <= 0:
                raise ValueError("Wavelength must be positive")
                
            polarization = self.layer_config.polarization_var.get()
            
            # Get current layer configuration
            dbr_stack, metal_layers, substrate_layer = self.layer_config.get_layers()
            
            # Calculate reflectance at angles from 0 to 90 degrees in 1-degree steps
            angles = np.linspace(0, 90, 91)
            reflectances = []
            
            for angle in angles:
                # Build layer structure with proper material properties
                Ls_structure = []
                
                # Add incident medium (air)
                Ls_structure.append([np.nan, "Constant", [1.0, 0.0]])
                
                # Add metal layers
                for layer in metal_layers:
                    if layer[1] == "Drude":
                        # Use the current Drude parameters
                        f0 = self.layer_config.f0_var.get()
                        wp = self.layer_config.wp_var.get()
                        gamma0 = self.layer_config.gamma0_var.get()
                        Ls_structure.append([
                            layer[0],
                            "Drude",
                            [float(f0), float(wp), float(gamma0)]
                        ])
                    else:
                        Ls_structure.append(layer.copy())
                
                # Add DBR layers
                for layer in dbr_stack:
                    Ls_structure.append(layer.copy())
                
                # Add substrate
                if substrate_layer and len(substrate_layer) > 0:
                    sub = substrate_layer[0].copy()
                    if isinstance(sub[2], str):
                        if sub[2] == "GaSb_ln":
                            sub[2] = [3.816, 0.0]
                        elif sub[2] == "GaAs_ln":
                            sub[2] = [3.3, 0.0]
                        else:
                            sub[2] = [1.0, 0.0]
                    Ls_structure.append(sub)
                
                if not self.light_direction:
                    Ls_structure = Ls_structure[::-1]
                
                # Convert angle to radians
                incang = np.array([float(angle) * np.pi / 180], dtype=np.float64)
                wavelength_nm = np.array([wavelength * 1000], dtype=np.float64)
                
                # Calculate reflectance at this angle with complex number handling
                rs, rp, _, _ = MF.calc_rsrpTsTp(
                    incang,
                    Ls_structure,
                    wavelength_nm
                )
                
                # Handle polarization with proper complex number handling
                if polarization == "s":
                    R0 = float(np.abs(complex(rs[0])))**2
                elif polarization == "p":
                    R0 = float(np.abs(complex(rp[0])))**2
                else:  # "both"
                    R0 = 0.5 * (float(np.abs(complex(rs[0]))**2 + float(np.abs(complex(rp[0]))**2)))
                
                reflectances.append(R0)
            
            # Get layer description for legend
            layer_desc = self.get_layer_description()
            
            # Get next color in cycle
            color = self.angle_colors(self.current_color_index % 10)
            self.current_color_index += 1
            
            # Plot raw results
            line, = self.ax3.plot(angles, reflectances, color=color, 
                                label=f'{wavelength}μm: {layer_desc}')
            
            # Store the line reference
            self.angle_curves.append(line)
            
            # Update legend and axes
            self.ax3.legend()
            self.ax3.set_xlabel("Angle of Incidence (degrees)")
            self.ax3.set_ylabel("Reflectance")
            self.ax3.set_title(f"Angle-Dependent Reflectance at {wavelength} μm")
            self.ax3.grid(alpha=0.2)
            
            # Apply current axis ranges
            self.apply_angle_axis_ranges()
            
            # Adjust layout to prevent label cutoff
            self.fig3.tight_layout()
            self.canvas3.draw()
            
        except Exception as e:
            messagebox.showerror("Plot Error", f"Failed to plot angle dependence: {str(e)}")
        
    def apply_axis_ranges(self):
        """Apply custom axis ranges"""
        try:
            xmin = float(self.xmin_entry.get())
            xmax = float(self.xmax_entry.get())
            ymin = float(self.ymin_entry.get())
            ymax = float(self.ymax_entry.get())
            
            if xmin >= xmax or ymin >= ymax:
                raise ValueError("Invalid range values")
                
            self.ax1.set_xlim(xmin, xmax)
            self.ax1.set_ylim(ymin, ymax)
            
            # Update ticks for better readability
            x_ticks = np.linspace(xmin, xmax, num=min(11, int(xmax-xmin)+1))
            y_ticks = np.linspace(ymin, ymax, num=11)
            
            self.ax1.set_xticks(x_ticks)
            self.ax1.set_yticks(y_ticks)
            
            self.canvas1.draw_idle()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid axis range: {str(e)}")

    def reset_axis_ranges(self):
        """Reset axis ranges to defaults"""
        self.xmin_entry.delete(0, tk.END)
        self.xmin_entry.insert(0, "2.5")
        self.xmax_entry.delete(0, tk.END)
        self.xmax_entry.insert(0, "12")
        self.ymin_entry.delete(0, tk.END)
        self.ymin_entry.insert(0, "0")
        self.ymax_entry.delete(0, tk.END)
        self.ymax_entry.insert(0, "1")
        
        self.ax1.set_xlim(2.5, 12)
        self.ax1.set_ylim(0.0, 1.0)
        self.ax1.set_xticks(np.arange(2, 13, 1))
        self.ax1.set_yticks(np.linspace(0.0, 1.0, 11))
        self.canvas1.draw_idle()

    def update_unknown_metal_params(self, thickness, f0, gamma0, wp):
        """Update the unknown metal parameters and refresh plot"""
        self.unknown_metal_params = {
            'thickness': float(thickness),
            'f0': float(f0),
            'gamma0': float(gamma0),
            'wp': float(wp)
        }
        
        # Update the metal layers with the new parameters
        self.metal_layers = [[
            self.unknown_metal_params['thickness'],
            "Drude",
            [self.unknown_metal_params['f0'],
             self.unknown_metal_params['wp'],
             self.unknown_metal_params['gamma0']]
        ]]
        
        # Update plot if we have current plot state
        if self.current_plot:
            self.plot_unknown_metal_response(
                self.current_plot['angle'],
                self.current_plot['polarization'],
                self.current_plot['ax'],
                self.current_plot['canvas']
            )

    def plot_unknown_metal_response(self, angle, polarization, ax, canvas):
        """Plot reflectance for unknown metal with progressive rendering"""
        if not all(self.unknown_metal_params.values()):
            return
            
        # Clear only the reflectance lines, not the entire plot
        for line in ax.get_lines():
            if line.get_label() in ['Reflectance', 'Absorption']:
                line.remove()
        
        # Set up layer structure
        substrate_material = self.substrate_layer
        if isinstance(substrate_material, list) and len(substrate_material) > 0:
            if substrate_material[0][2] == "GaSb_ln":
                substrate_material[0][2] = [3.816, 0.0]
            elif substrate_material[0][2] == "GaAs_ln":
                substrate_material[0][2] = [1, 0]
            else:
                substrate_material[0][2] = [1.0, 0.0]
        
        Ls_structure = (
            [[np.nan, "Constant", [1.0, 0.0]]] +
            self.metal_layers +
            (self.dbr_stack if self.dbr_stack else []) +
            substrate_material
        )
        
        if not self.light_direction:
            Ls_structure = Ls_structure[::-1]
        
        # Initial coarse calculation (every 10th point)
        nlamb = 350
        x_coarse = np.linspace(2.5, 12, nlamb) * 1000
        wavelength_microns_coarse = x_coarse / 1000
        incang = angle * np.pi / 180 * np.ones(x_coarse.size)
        
        rs, rp, Ts, Tp = MF.calc_rsrpTsTp(incang, Ls_structure, x_coarse)
        
        # Handle polarization
        if polarization == "s":
            R0_coarse = (abs(rs))**2
            T0_coarse = np.real(Ts)
            Abs1_coarse = 1.0 - R0_coarse - T0_coarse
        elif polarization == "p":
            R0_coarse = (abs(rp))**2
            T0_coarse = np.real(Tp)
            Abs1_coarse = 1.0 - R0_coarse - T0_coarse
        else:  # "both"
            R0_coarse = 0.5 * ((abs(rs))**2 + (abs(rp))**2)
            Abs1_coarse = 1 - R0_coarse - (0.5 * (np.real(Ts) + np.real(Tp)))
        
        # Plot coarse results first
        line_r, = ax.plot(wavelength_microns_coarse, R0_coarse, 
                        label='Reflectance', color='blue', alpha=0.7)
        line_a, = ax.plot(wavelength_microns_coarse, Abs1_coarse, 
                        label='Absorption', color='red', alpha=0.7)
        ax.legend()
        canvas.draw_idle()
        
        # Then calculate full resolution in background
        self.root.after(100, lambda: self._finish_high_res_plot(
            angle, polarization, Ls_structure, ax, canvas
        ))
        
        # Store current plot state
        self.current_plot = {
            'angle': angle,
            'polarization': polarization,
            'ax': ax,
            'canvas': canvas
        }

    def _finish_high_res_plot(self, angle, polarization, Ls_structure, ax, canvas):
        """Complete the high resolution plot after initial coarse render"""
        nlamb = 3500
        x = np.linspace(2.5, 12, nlamb) * 1000
        wavelength_microns = x / 1000
        incang = angle * np.pi / 180 * np.ones(x.size)
        
        rs, rp, Ts, Tp = MF.calc_rsrpTsTp(incang, Ls_structure, x)
        
        # Handle polarization
        if polarization == "s":
            R0 = (abs(rs))**2
            T0 = np.real(Ts)
            Abs1 = 1.0 - R0 - T0
        elif polarization == "p":
            R0 = (abs(rp))**2
            T0 = np.real(Tp)
            Abs1 = 1.0 - R0 - T0
        else:  # "both"
            R0 = 0.5 * ((abs(rs))**2 + (abs(rp))**2)
            Abs1 = 1 - R0 - (0.5 * (np.real(Ts) + np.real(Tp)))
        
        # Update the plot with high resolution data
        for line in ax.get_lines():
            if line.get_label() == 'Reflectance':
                line.set_data(wavelength_microns, R0)
            elif line.get_label() == 'Absorption':
                line.set_data(wavelength_microns, Abs1)
        
        canvas.draw_idle()

    def plot_raw_data(self, raw_data, ax, canvas): 
        """Plot raw reflectance data with a different color"""
        # Clear any existing raw data plot
        if self.raw_data_line is not None:
            self.raw_data_line.remove()
            
        # Load data from a file or ensure it's a DataFrame
        if isinstance(raw_data, str):
            try:
                raw_data = pd.read_csv(raw_data, header=None, names=["wavelength", "reflectance"],
                                    delimiter=",", engine="python")
            except Exception as e:
                raise ValueError(f"Failed to load file: {e}")
        elif not isinstance(raw_data, pd.DataFrame):
            raise TypeError("raw_data should be a pandas DataFrame or a CSV file path.")

        # Process data
        raw_data['wavelength'] = pd.to_numeric(raw_data['wavelength'], errors='coerce')
        raw_data['reflectance'] = pd.to_numeric(raw_data['reflectance'], errors='coerce')
        raw_data = raw_data.dropna(subset=['wavelength', 'reflectance'])
        
        # Detect and convert wavelength units
        median_wavelength = raw_data['wavelength'].median()
        
        if median_wavelength > 10000:  # Values in nm (e.g. 10000nm = 10μm)
            raw_data['wavelength'] = raw_data['wavelength'] / 10000
            messagebox.showinfo("Unit Conversion", 
                            "Detected wavelength values in nanometers. Automatically converted to microns (divided by 10000).")
        elif median_wavelength > 100:  # Values in 0.1nm or some other unit (e.g. 400 = 4μm)
            raw_data['wavelength'] = raw_data['wavelength'] / 100
            messagebox.showinfo("Unit Conversion", 
                            "Detected wavelength values in 0.1nm units. Automatically converted to microns (divided by 100).")
        elif median_wavelength > 10:  # Values might already be in microns
            pass  # Assume already in microns
        else:
            messagebox.showinfo("Data Uploaded", 
                                "Successfully Uploaded data")
        
        # Filter to our range of interest (2.5-12 microns)
        min_wavelength = max(2.5, raw_data['wavelength'].min())
        max_wavelength = min(12, raw_data['wavelength'].max())
        filtered_data = raw_data[(raw_data['wavelength'] >= min_wavelength) &
                            (raw_data['wavelength'] <= max_wavelength)]

        if filtered_data.empty:
            raise ValueError(f"No data points found in the specified wavelength range (2.5–12 µm). Data range: {raw_data['wavelength'].min():.2f}-{raw_data['wavelength'].max():.2f} µm")

        # Handle duplicates and smooth
        filtered_data = filtered_data.groupby("wavelength", as_index=False)["reflectance"].mean()
        smooth_wavelengths = np.linspace(filtered_data['wavelength'].min(),
                                        filtered_data['wavelength'].max(), 500)
        smooth_reflectance = make_interp_spline(
            filtered_data['wavelength'], filtered_data['reflectance'], k=3
        )(smooth_wavelengths)

        # Plot with a distinct color (green in this case)
        self.raw_data_line, = ax.plot(
            smooth_wavelengths, smooth_reflectance, 
            label="Raw Data", 
            color="green",
            linewidth=1.5,
            linestyle="--"
        )
        
        # Update legend
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)
        
        canvas.draw()
        self.raw_data = raw_data  # Store the processed data
            
    def plot_stack(self, angle, polarization, ax, canvas):
        try:
            # Don't clear the entire axis - just remove the simulated plots
            for line in ax.get_lines():
                if line.get_label() in ['Reflectance', 
                                    'Absorption',
                                    'Reflectance',
                                    'Absorption']:
                    line.remove()
            
            # Validate and process layers
            if not self.metal_layers and not self.dbr_stack:
                raise ValueError("No layers configured for simulation")
                
            # Process substrate
            substrate_material = self.substrate_layer
            if isinstance(substrate_material, list) and len(substrate_material) > 0:
                if substrate_material[0][2] == "GaSb_ln":
                    substrate_material[0][2] = [3.816, 0.0]
                elif substrate_material[0][2] == "GaAs_ln":
                    substrate_material[0][2] = [1, 0]
                else:
                    substrate_material[0][2] = [1.0, 0.0]
            substrate_thickness = float(self.substrate_thickness)
            
            # Build layer structure
            Ls_structure = (
                [[np.nan, "Constant", [1.0, 0.0]]] +
                self.metal_layers +
                (self.dbr_stack if self.dbr_stack else []) +
                substrate_material
            )
            
            if not self.light_direction:
                Ls_structure = Ls_structure[::-1]
            
            # Calculate reflectance
            nlamb = 3500
            x = np.linspace(2.5, 12, nlamb) * 1000
            wavelength_microns = x / 1000
            incang = angle * np.pi / 180 * np.ones(x.size)
            
            rs, rp, Ts, Tp = MF.calc_rsrpTsTp(incang, Ls_structure, x)
            
            # Handle polarization
            if polarization == "s":
                R0 = (abs(rs))**2
                T0 = np.real(Ts)
                Abs1 = 1.0 - R0 - T0
            elif polarization == "p":
                R0 = (abs(rp))**2
                T0 = np.real(Tp)
                Abs1 = 1.0 - R0 - T0
            else:  # "both"
                R0 = 0.5 * ((abs(rs))**2 + (abs(rp))**2)
                Abs1 = 1 - R0 - (0.5 * (np.real(Ts) + np.real(Tp)))
            
            if not np.isnan(substrate_thickness) and substrate_thickness > 0:
                print("Finite substrate thickness in microns: " + str(substrate_thickness/1000))
                R_finite = np.zeros_like(R0)

                # in microns
                substrate_thickness = substrate_thickness/1000

                # Define valid wavelength range (2 µm to 12 µm)
                valid_range = (wavelength_microns >= 2) & (wavelength_microns <= 12)

                # Initialize alpha with zeros
                alpha = np.zeros_like(wavelength_microns)

                # Compute alpha(absorption coefficient for GaSb) only in valid range
                alpha[valid_range] = 7.6 * (4.4 ** (0.3 * wavelength_microns[valid_range] - 2.8)) + 1.2  

                print(alpha)
                # Precompute exp(-2 * alpha * substrate_thickness) once
                exp_factor = np.exp(-2 * alpha * substrate_thickness)

                for i in range(1, 11):  # Summation term
                    term = (0.33 ** (i - 1)) * (R0 ** i) * (exp_factor ** (substrate_thickness*i))
                    R_finite += term

                    print(f"Iteration {i}, term min: {term.min()}, max: {term.max()}")

                # Final update for reflectance
                R_finite = 0.33 + (0.67 ** 2) * R_finite
                Abs1 = 1.0 - R_finite - T0

                reflectance_line, = ax.plot(wavelength_microns, R_finite, 
                                        label='Reflectance', 
                                        color='blue')
                
                absorption_line, = ax.plot(wavelength_microns, Abs1, 
                                        label='Absorption', 
                                        color='red',
                                        visible=self.show_absorption_var.get())
            else:    
                reflectance_line, = ax.plot(wavelength_microns, R0, 
                                        label='Reflectance', 
                                        color='blue')
                
                absorption_line, = ax.plot(wavelength_microns, Abs1, 
                                        label='Absorption', 
                                        color='red',
                                        visible=self.show_absorption_var.get())
            
            # Update legend to include both raw and simulated data
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels)
            
            # Reset plot properties (preserving any existing raw data)
            ax.set_xticks(np.arange(2, 13, 1))
            ax.set_yticks(np.linspace(0.0, 1.0, 11))
            ax.set_xlim(float(self.xmin_entry.get()), float(self.xmax_entry.get()))
            ax.set_ylim(float(self.ymin_entry.get()), float(self.ymax_entry.get()))
            ax.set_xlabel("Wavelength (μm)")
            ax.set_ylabel("Reflectance")
            ax.set_title("Simulated and Raw Reflectance")
            ax.grid(alpha=0.2)
            
            canvas.draw()

            # Store current plot state
            self.current_plot = {
                'angle': angle,
                'polarization': polarization,
                'ax': ax,
                'canvas': canvas
            }
                
        except Exception as e:
            print(f"Error in plot_stack: {e}")
            messagebox.showerror("Plot Error", f"Failed to plot reflectance: {str(e)}")


    def store_plot_state(self, angle, polarization, ax, canvas):
        """Store the current plot parameters for updates"""
        self.current_plot = {
            'angle': angle,
            'polarization': polarization,
            'ax': ax,
            'canvas': canvas
        }
        
    def update_unknown_metal_plot(self):
        """Redraw the plot with current parameters"""
        if self.current_plot:
            self.plot_unknown_metal_response(
                self.current_plot['angle'],
                self.current_plot['polarization'],
                self.current_plot['ax'],
                self.current_plot['canvas']
            )


    def plot_electric_field_decay(self, ax, canvas):
        try:
            # Use the layers that were already set in the plotter instance
            total_layers = (self.metal_layers if self.metal_layers else []) + \
                        (self.dbr_stack if self.dbr_stack else []) + \
                        (self.substrate_layer if self.substrate_layer else [])
                
            if not total_layers:
                raise ValueError("No layers configured")
                
            # Rest of the function remains the same...
            # Calculate cumulative depth
            depths = [0]
            for layer in total_layers:
                depths.append(depths[-1] + (layer[0] if not np.isnan(layer[0]) else 0))
                
            total_thickness = depths[-1]
            
            # Create depth array with fine resolution
            z = np.linspace(0, total_thickness, 5000)  # nm
            z_microns = z / 1000  # convert to microns
            
            # Initialize field
            E = np.ones_like(z)
            
            # Simulate field decay with oscillations
            current_depth = 0
            for i, layer in enumerate(total_layers):
                thickness = layer[0] if not np.isnan(layer[0]) else 0
                if thickness == 0:
                    continue
                    
                # Get material properties (simplified)
                n = 3.8 if "GaSb" in str(layer[2]) else \
                    3.1 if "AlAsSb" in str(layer[2]) else \
                    0.5 + 10j if layer[1] == "Drude" else 1.0
                    
                # Calculate decay and oscillations
                start_idx = np.searchsorted(z, current_depth)
                end_idx = np.searchsorted(z, current_depth + thickness)
                
                k = 2 * np.pi / (4.0 * 1000)  # wavevector for ~4μm light
                attenuation = np.exp(-z[start_idx:end_idx] * 0.001)  # arbitrary decay
                oscillations = np.cos(2 * k * z[start_idx:end_idx])
                
                E[start_idx:end_idx] = attenuation * oscillations
                
                current_depth += thickness
                
            # Plot
            ax.clear()
            ax.plot(z_microns, np.abs(E), 'b-', label='|E(z)|')
            ax.plot(z_microns, np.real(E), 'r--', alpha=0.5, label='Re(E(z))')
            ax.set_xlabel('Depth from top (μm)')
            ax.set_ylabel('Electric Field')
            ax.set_title('Electric Field in Stack')
            ax.legend()
            ax.grid(True)
            
            # Mark layer boundaries
            for depth in depths[1:-1]:
                ax.axvline(depth/1000, color='k', linestyle=':', alpha=0.3)
            
            # Adjust layout to prevent label cutoff
            self.fig2.tight_layout()
            canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Plot Error", f"Failed to plot electric field: {str(e)}")