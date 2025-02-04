#plotting.py - Manages the reflectance calculation and plotting.
import numpy as np
import pandas as pd
import tkinter as tk
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from tkinter import messagebox
from utils import load_settings, save_settings
import Funcs as MF
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PlotReflectance:

    def __init__(self, dbr_stack=None, metal_layers=None, substrate_layer=None, substrate_thickness=None):

        self.dbr_stack = dbr_stack
        self.metal_layers = metal_layers
        self.substrate_layer = substrate_layer
        self.substrate_thickness = substrate_thickness


    def plot_raw_data(self, raw_data): 
        """Plot raw reflectance data from a CSV file or DataFrame."""
        # Load data from a file or ensure it's a DataFrame
        if isinstance(raw_data, str):  # Assuming raw_data is a file path
            try:
                raw_data = pd.read_csv(raw_data, header=None, names=["wavelength", "reflectance"],
                                       delimiter=",", engine="python")
            except Exception as e:
                raise ValueError(f"Failed to load file: {e}")
        elif not isinstance(raw_data, pd.DataFrame):
            raise TypeError("raw_data should be a pandas DataFrame or a CSV file path.")
    
        # Ensure 'wavelength' and 'reflectance' columns are numeric
        raw_data['wavelength'] = pd.to_numeric(raw_data['wavelength'], errors='coerce')
        raw_data['reflectance'] = pd.to_numeric(raw_data['reflectance'], errors='coerce')
    
        # Drop rows with NaN values
        raw_data = raw_data.dropna(subset=['wavelength', 'reflectance'])
    
        # Filter the data to include only the range of interest (e.g., 2.5 to 12 µm)
        min_wavelength = max(2.5, raw_data['wavelength'].min())
        max_wavelength = min(12, raw_data['wavelength'].max())
        filtered_data = raw_data[(raw_data['wavelength'] >= min_wavelength) &
                                 (raw_data['wavelength'] <= max_wavelength)]
    
        if filtered_data.empty:
            raise ValueError("No data points found in the specified wavelength range (2.5–12 µm).")
    
        # Handle duplicates: Group by wavelength and average reflectance
        filtered_data = filtered_data.groupby("wavelength", as_index=False)["reflectance"].mean()
    
        # Smooth curve using dense interpolation
        smooth_wavelengths = np.linspace(filtered_data['wavelength'].min(),
                                          filtered_data['wavelength'].max(), 500)
        smooth_reflectance = make_interp_spline(
            filtered_data['wavelength'], filtered_data['reflectance'], k=3  # Cubic spline
        )(smooth_wavelengths)
    
        # Plot the data points and smooth curve
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_alpha(0)  # Transparent figure background
        ax.set_facecolor("none")  # Transparent axes background
    
        plt.plot(
            smooth_wavelengths, smooth_reflectance, label="Smoothed Curve", color="blue", linewidth=1  # Thinner line
        )
        plt.scatter(
            filtered_data['wavelength'], filtered_data['reflectance'],
            color="red", label="Data Points", zorder=5, alpha=0.6, s=15  # Reduced size of points
        )
        plt.xlabel("Wavelength (µm)")
        plt.ylabel("Reflectance (%)")
                # Adjust x-axis range and ticks
        plt.xlim([2.5, 12])  # Limit x-axis from 2.5 to 12
        plt.xticks(np.arange(3, 12, 1))  # Set ticks at every 1 unit, starting at 3
        plt.legend()
        plt.grid(alpha=0.5)
        plt.title("Reflectance vs. Wavelength")
    
        # Adjust y-axis limits
        plt.ylim(0, 1)
                # Adjust y-axis range to [0, 1]
        plt.ylim([0, 1])  # Set the y-axis range from 0 to 1
        plt.yticks(np.arange(0, 1, 0.1))  
    
        plt.show()

       
    def plot_stack(self, angle, polarization):
        self.settings = load_settings()
        dbr_stack = self.dbr_stack  # Example: [[100.0, 'Constant', 'GaSb_ln'], [100.0, 'Constant', 'AlAsSb_ln']]
        metal_layers = self.metal_layers
        substrate_material = self.substrate_layer  # Example: [[nan, 'Constant', 'GaSb_ln']]
        substrate_thickness = self.substrate_thickness

        nlamb = 3500
        x = np.linspace(2.5, 12, nlamb) * 1000  # array of wavelengths (in nanometers), consisting of nlamb = 3500 points
        wavelength_microns = x / 1000  # Convert to microns



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
            dbr_stack +                           # DBR stack layers
            substrate_material                    # Substrate layer
        )
        # Print debugging information
        print(f"Substrate Thickness: {substrate_thickness}")
        print(f"Layer Stack: {Ls_structure}")
    
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
            Abs1 = 1.0 - R0 - T0
            # ax1.plot(x / 1000, R0, label='Reflectance (s-pol)', color='blue')
            # ax1.plot(x / 1000, Abs1, label='Absorption (s-pol)', color='green')
        elif polarization == "p":
            R0 = (abs(rp))**2
            T0 = np.real(Tp)
            Abs1 = 1.0 - R0 - T0
            # ax1.plot(x / 1000, R0, label='Reflectance (p-pol)', color='red')
            # ax1.plot(x / 1000, Abs1, label='Absorption (p-pol)', color='purple')
        elif polarization == "both":
            R0_s = (abs(rs))**2
            R0_p = (abs(rp))**2
            T0=(Ts+Tp)/2
            R0 = 0.5 * (R0_s + R0_p)  # Average reflectance for unpolarized light
            Abs1 = 1 - R0 - (0.5 * (Ts + Tp))
            # ax1.plot(x / 1000, R0_s, label='Reflectance (s-pol)', color='blue', linestyle='--')
            # ax1.plot(x / 1000, R0_p, label='Reflectance (p-pol)', color='red', linestyle='--')
            # ax1.plot(x / 1000, R0, label='Reflectance (avg)', color='green')
            # ax1.plot(x / 1000, Abs1, label='Absorption (avg)', color='purple')
        else:
            raise ValueError("Invalid polarization. Choose 's', 'p', or 'both'.")
        
        if substrate_thickness != 0.0:  # Check if finite substrate is selected
            print("Finite substrate thickness in microns: " + str(substrate_thickness/1000))
            R_finite = np.zeros_like(R0)

            # in microns
            substrate_thickness=substrate_thickness/1000

            # alpha=absorption coefficient for GaSb
            # Define valid wavelength range (2 µm to 12 µm)
            valid_range = (wavelength_microns >= 2) & (wavelength_microns <= 12)

            # Initialize alpha with zeros
            alpha = np.zeros_like(wavelength_microns)

            # Compute alpha only in valid range
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

            print(f"Reflectance finite percentage shape: {R_finite.shape}, min: {R_finite.min()}, max: {R_finite.max()}")

            # Plot reflectance as a function of wavelength
            ax1.plot(wavelength_microns, R_finite, label='Reflectance (Finite Substrate)', color='green')
            ax1.plot(wavelength_microns, Abs1, label='Absorption (Finite Substrate)', color='red')

        else:
            # Plot semi-infinite reflectance
            ax1.plot(x/1000, R0, label='Reflectance (Semi-Infinite Substrate)', color='blue')
            ax1.plot(x/1000, Abs1, label='Absorption (Semi-Infinite Substrate)', color='green')


        # Customize plot
        ax1.set_xlabel('Wavelength (μm)', size=12)
        ax1.set_ylabel('Reflectance', size=12)
        ax1.set_title('Reflectance and Absorption of Custom Layer Stack', size=16)


        # Adjust x-axis range and ticks
        ax1.set_xlim([2.5, 12])  # Limit x-axis from 2.5 to 12
        ax1.set_xticks(np.arange(3, 12, 1))  # Set ticks at every 1 unit, starting at 3

        # Adjust y-axis range to [0, 1]
        ax1.set_ylim([0, 1])  # Set the y-axis range from 0 to 1
        ax1.set_yticks(np.arange(0, 1, 0.1))  

        # Add grid
        ax1.grid(alpha=0.2)

        # Add legends
        ax1.legend(loc='upper right')

        # Tight layout
        plt.tight_layout()

        # Show the plot
        plt.show()


    def is_finite_substrate(self):
        if self.layer_config:
            return self.layer_config.get_is_finite_substrate()
        return False