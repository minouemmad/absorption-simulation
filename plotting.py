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

    def __init__(self, dbr_stack=None, metal_layers=None, substrate_layer=None, substrate_thickness=None, light_direction=None, right_frame=None, metal_thickness=None):

        self.dbr_stack = dbr_stack
        self.metal_layers = metal_layers
        self.substrate_layer = substrate_layer
        self.substrate_thickness = substrate_thickness
        self.light_direction = light_direction
        self.right_frame = right_frame  # Store right_frame reference
        self.metal_thickness=metal_thickness

    def plot_raw_data(self, raw_data, ax, canvas): 
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
    
        ax.plot(
            smooth_wavelengths, smooth_reflectance, label="Smoothed Curve", color="blue", linewidth=1  # Thinner line
        )

        canvas.draw()

    def plot_stack(self, angle, polarization, ax, canvas):

        self.settings = load_settings()
        dbr_stack = self.dbr_stack  # Example: [[100.0, 'Constant', 'GaSb_ln'], [100.0, 'Constant', 'AlAsSb_ln']]
        metal_layers = self.metal_layers
        substrate_material = self.substrate_layer  # Example: [[nan, 'Constant', 'GaSb_ln']]
        substrate_thickness = float(self.substrate_thickness)

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
        print(f"Light Direction: {self.light_direction}")
        if self.light_direction:
            print("Reversing light direction")
            pass  # Leave the structure as is
        else:
            print("Normal light direction")
            Ls_structure = Ls_structure[::-1]  # Reverse the structure as required
    
        # Print results for debugging
        print("Extracted substrate material: " + str(substrate_material))
        print("Final structure: " + str(Ls_structure))
    
        # Calculate reflectance and transmittance
        incang = angle * np.pi / 180 * np.ones(x.size)  # Incident angle
    
        rs, rp, Ts, Tp = MF.calc_rsrpTsTp(incang, Ls_structure, x)
    
        # Handle user-specified polarization
        if polarization == "s":
            R0 = (abs(rs))**2
            T0 = np.real(Ts)
            Abs1 = 1.0 - R0 - T0
        elif polarization == "p":
            R0 = (abs(rp))**2
            T0 = np.real(Tp)
            Abs1 = 1.0 - R0 - T0
        elif polarization == "both":
            R0_s = (abs(rs))**2
            R0_p = (abs(rp))**2
            T0=(Ts+Tp)/2
            R0 = 0.5 * (R0_s + R0_p)  # Average reflectance for unpolarized light
            Abs1 = 1 - R0 - (0.5 * (Ts + Tp))
        else:
            raise ValueError("Invalid polarization. Choose 's', 'p', or 'both'.")
        
        if substrate_thickness != 0.0 or substrate_thickness != None:  # Check if finite substrate is selected
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

            print(f"Reflectance finite percentage shape: {R_finite.shape}, min: {R_finite.min()}, max: {R_finite.max()}")
            ax.plot(wavelength_microns, R_finite, label='Reflectance (Finite Substrate)', color='green')
            ax.plot(wavelength_microns, Abs1, label='Absorption (Finite Substrate)', color='red')

        else:
            # Plot semi-infinite reflectance
            ax.plot(wavelength_microns, R0, label='Reflectance (Semi-Infinite Substrate)', color='blue')
            ax.plot(wavelength_microns, Abs1, label='Absorption (Semi-Infinite Substrate)', color='green')

        canvas.draw()

    def plot_electric_field_decay(self, ax2, canvas):
        """
        Plot the electric field amplitude decay vs. depth in the substrate.
        Uses the predefined canvas and ax2 parameters.
        """
        # Ensure substrate thickness is valid
        if self.substrate_thickness is None or self.substrate_thickness == 0:
            raise ValueError("Substrate thickness must be a positive value.")
    
        # Convert thickness values to floats if needed
        try:
            total_thickness = float(self.substrate_thickness)  # Ensure it's a float
        except ValueError:
            raise ValueError("Substrate thickness must be a numeric value.")
    
        if self.metal_thickness is not None:
            try:
                total_thickness += float(self.metal_thickness)  # Convert and add metal thickness
            except ValueError:
                raise ValueError("Metal thickness must be a numeric value if provided.")
    
        # Define depth range (from surface to total thickness)
        depth_microns = np.linspace(0, total_thickness / 1000, 500)
        
        # Compute decay profile using an exponential function
        absorption_coefficient = 7.6 * (4.4 ** (0.3 * 3 - 2.8)) + 1.2  # Approximate value at 3 µm
        electric_field_amplitude = np.exp(-absorption_coefficient * depth_microns)
        ax2.plot(depth_microns, electric_field_amplitude, label='Electric Field Amplitude', color='purple')
        ax2.set_xlabel('Depth in GaSb (µm)')
        ax2.set_ylabel('Electric Field Amplitude')
        ax2.set_title('Electric Field Decay in Substrate')
        ax2.legend()

        canvas.draw()

