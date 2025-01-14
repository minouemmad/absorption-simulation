#plotting.py - Manages the reflectance calculation and plotting.
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
import Funcs as MF
from utils import *
from scipy.interpolate import make_interp_spline
from tkinter import messagebox


class PlotReflectance:
    def __init__(self, dbr_stack, metal_layers, substrate_layer):
        self.dbr_stack = dbr_stack
        self.metal_layers = metal_layers
        self.substrate_layer = substrate_layer

        self.include_absorption_var = tk.BooleanVar(value=True)
        # Add a checkbox to toggle absorption
        self.absorption_checkbox = tk.Checkbutton(
            text="Include Absorption", variable=self.include_absorption_var,
            command=self.update_plot)
        self.absorption_checkbox.grid(row=0, column=0, padx=5, pady=5)


    def plot_raw_data(self, raw_data):
        # Check if raw_data is a file path or DataFrame
        if isinstance(raw_data, str):  # Assuming raw_data is a file path
            try:
                raw_data = pd.read_csv(raw_data, header=None, names=["wavelength", "reflectance"], 
                                       delimiter=",", engine="python")
            except Exception as e:
                raise ValueError(f"Failed to load file: {e}")
        elif not isinstance(raw_data, pd.DataFrame):
            raise TypeError("raw_data should be a pandas DataFrame or a CSV file path.")
        
        # Convert wavelength from nm to µm if needed
        if raw_data['wavelength'].max() > 100:  # Assuming large values mean nm
            raw_data['wavelength'] = raw_data['wavelength'] / 1000.0  # Convert to µm

        # Filter the data to include only the range of interest (e.g., 2.5 to 12 µm)
        min_wavelength = max(2.5, raw_data['wavelength'].min())
        max_wavelength = min(12, raw_data['wavelength'].max())
        filtered_data = raw_data[(raw_data['wavelength'] >= min_wavelength) & 
                                 (raw_data['wavelength'] <= max_wavelength)]
        
        if filtered_data.empty:
            raise ValueError("No data points found in the specified wavelength range (2.5–12 µm).")

        # Handle duplicates: Group by wavelength and average reflectance
        filtered_data = filtered_data.groupby("wavelength", as_index=False).mean()

        # Smooth curve using dense interpolation
        smooth_wavelengths = np.linspace(filtered_data['wavelength'].min(),
                                          filtered_data['wavelength'].max(), 500)
        smooth_reflectance = make_interp_spline(
            filtered_data['wavelength'], filtered_data['reflectance'], k=3  # Cubic spline
        )(smooth_wavelengths)

        # Plot the data points and smooth curve
        plt.figure(figsize=(8, 6))
        plt.plot(
            smooth_wavelengths, smooth_reflectance, label="Smoothed Curve", color="blue", linewidth=2
        )
        plt.scatter(
            filtered_data['wavelength'], filtered_data['reflectance'],
            color="red", label="Data Points", zorder=5
        )
        plt.xlabel("Wavelength (µm)")
        plt.ylabel("Reflectance (%)")
        plt.legend()
        plt.grid()
        plt.title("Reflectance vs. Wavelength")
        plt.show()

    def update_plot(self):
        # Get the current state of the checkbox
        include_absorption = self.include_absorption_var.get()
        
        # Call plot_stack with the updated absorption flag
        self.plot_stack(incang=45, polarization="both", include_absorption=include_absorption)


    def plot_stack(self, angle, polarization, include_absorption=True):
        settings = load_settings()
        dbr_stack = self.dbr_stack  # Example: [[100.0, 'Constant', 'GaSb_ln'], [100.0, 'Constant', 'AlAsSb_ln']]
        metal_layers = self.metal_layers
        substrate_material = self.substrate_layer  # Example: [[nan, 'Constant', 'GaSb_ln']]
    
        nlamb = 3500
        x = np.linspace(2.5, 15, nlamb) * 1000  # array of wavelengths (in nanometers), consisting of nlamb = 3500 points
    
        # Fix substrate material by replacing it with its corresponding refractive index function
        if isinstance(substrate_material, list) and len(substrate_material) > 0:
            if substrate_material[0][2] == "GaSb_ln":
                substrate_material[0][2] = [3.816, 0.0]
            elif substrate_material[0][2] == "GaAs_ln":
                substrate_material[0][2] = [1, 0]  # unknown for now
            else:
                substrate_material[0][2] = [1.0, 0.0]
    
        # Combine all layers into the final structure
        Ls_structure = (
            [[np.nan, "Constant", [1.0, 0.0]]] +  # Initial spacer layer
            metal_layers +                        # Metal layers
            [[239., "Constant", [3.101, 0.0]]] +  # Example additional layer
            dbr_stack +                           # DBR stack layers
            substrate_material                    # Substrate layer
        )
    
        Ls_structure = Ls_structure[::-1]  # Reverse the structure as required
    
        # Print results for debugging
        print("Extracted substrate material: " + str(substrate_material))
        print("Extracted DBR materials: " + str(dbr_stack))
        print("Final structure: " + str(Ls_structure))
    
        # Calculate reflectance and transmittance
        incang = angle * np.pi / 180 * np.ones(x.size)  # Incident angle
    
        rs, rp, Ts, Tp = MF.calc_rsrpTsTp(incang, Ls_structure, x)
    
        # Initialize figure and axis
        fig, ax1 = plt.subplots(figsize=(10, 5))
    
        # Handle user-specified polarization
        if polarization == "s":
            R0 = (abs(rs))**2
            T0 = np.real(Ts)
            Abs1 = 1.0 - R0 - T0 if include_absorption else None
            ax1.plot(x / 1000, R0, label='Reflectance (s-pol)', color='blue')
        elif polarization == "p":
            R0 = (abs(rp))**2
            T0 = np.real(Tp)
            Abs1 = 1.0 - R0 - T0 if include_absorption else None
            ax1.plot(x / 1000, R0, label='Reflectance (p-pol)', color='red')
        elif polarization == "both":
            R0_s = (abs(rs))**2
            R0_p = (abs(rp))**2
            R0_avg = 0.5 * (R0_s + R0_p)  # Average reflectance for unpolarized light
            Abs1 = 1 - R0_avg - (0.5 * (Ts + Tp)) if include_absorption else None
            ax1.plot(x / 1000, R0_s, label='Reflectance (s-pol)', color='blue', linestyle='--')
            ax1.plot(x / 1000, R0_p, label='Reflectance (p-pol)', color='red', linestyle='--')
            ax1.plot(x / 1000, R0_avg, label='Reflectance (avg)', color='green')
        else:
            raise ValueError("Invalid polarization. Choose 's', 'p', or 'both'.")
    
        # Create a second y-axis for absorption if included
        if include_absorption and Abs1 is not None:
            ax2 = ax1.twinx()
            ax2.plot(x / 1000, Abs1, label='Absorption', color='purple')
            ax2.set_ylabel('Absorption', size=12)
            ax2.set_ylim([0, 1])  # Set the y-axis range for absorption from 0 to 1
            ax2.legend(loc='upper right')
    
        # Customize plot
        ax1.set_xlabel('Wavelength (μm)', size=12)
        ax1.set_ylabel('Reflectance', size=12)
        ax1.set_title('Reflectance and Absorption of Custom Layer Stack', size=16)
    
        # Adjust x-axis range and ticks
        ax1.set_xlim([2.5, 15])  # Limit x-axis from 2.5 to 15
        ax1.set_xticks(np.arange(3, 15, 1))  # Set ticks at every 1 unit, starting at 3
    
        # Adjust y-axis range to [0, 1]
        ax1.set_ylim([0, 1])  # Set the y-axis range from 0 to 1
    
        # Add grid
        ax1.grid(alpha=0.2)
    
        # Add legends
        ax1.legend(loc='upper left')
    
        # Tight layout
        plt.tight_layout()
    
        # Show the plot
        plt.show()
    
        # Save settings if needed
        save_settings(settings)
    
