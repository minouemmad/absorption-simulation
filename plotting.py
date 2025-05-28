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
                
            if not np.isnan(substrate_thickness) and substrate_thickness > 0:
                print("Finite substrate thickness in microns: " + str(substrate_thickness/1000))
                R_finite = np.zeros_like(R0)

                # in microns
                substrate_thickness=substrate_thickness/1000

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

                ax.plot(wavelength_microns, R_finite, label='Reflectance (Finite Substrate)', color='green')
                ax.plot(wavelength_microns, Abs1, label='Absorption (Finite Substrate)', color='red')


            else:    
                # Plot results
                ax.plot(wavelength_microns, R0, label='Reflectance (Semi-Infinite Substrate)', color='blue')
                ax.plot(wavelength_microns, Abs1, label='Absorption (Semi-Infinite Substrate)', color='red')
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
                
            canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Plot Error", f"Failed to plot electric field: {str(e)}")