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

        self.current_plot = None

        
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
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6), gridspec_kw={'height_ratios': [2, 1]})
        self.fig.tight_layout(pad=3.0)
        
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
        self.ax2.set_title("Electric Field Decay")
        self.ax2.grid(alpha=0.2)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True)

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
        """Plot reflectance for unknown metal with real-time updates"""
        if not all(self.unknown_metal_params.values()):
            return
            
        ax.clear()
        
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
        
        # Plot results
        ax.plot(wavelength_microns, R0, label='Reflectance', color='blue')
        ax.plot(wavelength_microns, Abs1, label='Absorption', color='red')
        ax.legend()
        
        # Reset plot limits and labels
        ax.set_xticks(np.arange(2, 13, 1))
        ax.set_yticks(np.linspace(0.0, 1.0, 11))
        ax.set_xlim(2.5, 12)
        ax.set_ylim(0.0, 1.0)
        ax.set_xlabel("Wavelength (μm)")
        ax.set_ylabel("Reflectance")
        ax.set_title("Simulated Reflectance")
        ax.grid(alpha=0.2)
        
        canvas.draw()
        
        # Store current plot state
        self.current_plot = {
            'angle': angle,
            'polarization': polarization,
            'ax': ax,
            'canvas': canvas
        }

    def plot_raw_data(self, raw_data, ax, canvas): 
        """Plot raw reflectance data with a different color"""
        # Clear any existing raw data plot
        if self.raw_data_line:
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
        
        # Filter to our range of interest
        min_wavelength = max(2.5, raw_data['wavelength'].min())
        max_wavelength = min(12, raw_data['wavelength'].max())
        filtered_data = raw_data[(raw_data['wavelength'] >= min_wavelength) &
                               (raw_data['wavelength'] <= max_wavelength)]
    
        if filtered_data.empty:
            raise ValueError("No data points found in the specified wavelength range (2.5–12 µm).")
    
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
            color="green",  # Changed from blue to green
            linewidth=1.5,
            linestyle="--"  # Added dashed line for better distinction
        )
        
        # Update legend
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels)
        
        canvas.draw()

    def plot_stack(self, angle, polarization, ax, canvas):
        try:
            ax.clear()
            
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
            else:
                R0 = 0.5 * ((abs(rs))**2 + (abs(rp))**2)
                Abs1 = 1 - R0 - (0.5 * (np.real(Ts) + np.real(Tp)))
            
            # Plot results
            ax.plot(wavelength_microns, R0, label='Reflectance', color='blue')
            ax.plot(wavelength_microns, Abs1, label='Absorption', color='red')
            ax.legend()
            
            # Reset plot properties
            ax.set_xticks(np.arange(2, 13, 1))
            ax.set_yticks(np.linspace(0.0, 1.0, 11))
            ax.set_xlim(2.5, 12)
            ax.set_ylim(0.0, 1.0)
            ax.set_xlabel("Wavelength (μm)")
            ax.set_ylabel("Reflectance")
            ax.set_title("Simulated Reflectance")
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
        """
        Plot the electric field amplitude decay vs. depth in the substrate.
        Uses the provided Matplotlib Axes object and FigureCanvas to render on a separate canvas.
        """
        # Validate substrate thickness
        if self.substrate_thickness is None or self.substrate_thickness == 0:
            raise ValueError("Substrate thickness must be a positive value.")

        try:
            total_thickness = float(self.substrate_thickness)
        except ValueError:
            raise ValueError("Substrate thickness must be a numeric value.")

        # Add metal thickness if present
        if self.metal_thickness is not None:
            try:
                total_thickness += float(self.metal_thickness)
            except ValueError:
                raise ValueError("Metal thickness must be a numeric value if provided.")

        # Define depth in microns
        depth_microns = np.linspace(0, total_thickness / 1000, 500)

        # Compute electric field amplitude decay
        absorption_coefficient = 7.6 * (4.4 ** (0.3 * 3 - 2.8)) + 1.2  # Empirical formula at ~3 µm
        electric_field_amplitude = np.exp(-absorption_coefficient * depth_microns)

        # Clear the existing plot and draw new one
        ax.clear()
        ax.plot(depth_microns, electric_field_amplitude, label='Electric Field Amplitude', color='purple')
        ax.set_xlabel('Depth in GaSb (µm)')
        ax.set_ylabel('Electric Field Amplitude')
        ax.set_title('Electric Field Decay in Substrate')
        ax.grid(True)
        ax.legend()

        # Redraw canvas
        canvas.draw()