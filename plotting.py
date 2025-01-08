#plotting.py - Manages the reflectance calculation and plotting.
import numpy as np
import matplotlib.pyplot as plt
import Funcs as MF
from materials import *
from utils import *
from scipy.interpolate import make_interp_spline


class PlotReflectance:
    def __init__(self, dbr_stack=None, metal_layers=None, substrate_layer=None):
        self.dbr_stack = dbr_stack
        self.metal_layers = metal_layers
        self.substrate_layer = substrate_layer

    def plot_raw_data(self, raw_data):
        # Check if raw_data is a DataFrame, if not, try reading from a CSV file
        if isinstance(raw_data, str):  # Assuming raw_data is a file path
            raw_data = pd.read_csv(raw_data, header=None, names=["wavelength", "reflectance"])
        elif not isinstance(raw_data, pd.DataFrame):  # Ensure it's a DataFrame
            raise TypeError("raw_data should be a pandas DataFrame or a CSV file path.")
        
        # Filter the data to include only wavelengths from 2.5 to 12
        filtered_data = raw_data[(raw_data['wavelength'] >= 2.5) & (raw_data['wavelength'] <= 12)]

        # Handle duplicates: Group by wavelength and average reflectance
        filtered_data = filtered_data.groupby("wavelength", as_index=False).mean()

        # Select desired wavelengths (2.5 to 12 in 0.5 increments)
        desired_wavelengths = np.arange(2.5, 12, 1)
        interpolated_points = []
        for wavelength in desired_wavelengths:
            # Find the nearest data point for each desired wavelength
            closest_row = filtered_data.iloc[(filtered_data['wavelength'] - wavelength).abs().argsort()[:1]]
            interpolated_points.append(closest_row)

        # Combine the nearest points into a DataFrame
        interpolated_points = pd.concat(interpolated_points)

        # Ensure unique wavelengths for interpolation
        interpolated_points = interpolated_points.drop_duplicates(subset="wavelength")

        # Smooth curve using interpolation
        smooth_wavelengths = np.linspace(desired_wavelengths.min(), desired_wavelengths.max(), 500)
        smooth_reflectance = make_interp_spline(
            interpolated_points['wavelength'], interpolated_points['reflectance']
        )(smooth_wavelengths)

        # Plot the points and smooth curve
        plt.figure(figsize=(8, 6))
        plt.plot(
            smooth_wavelengths, smooth_reflectance, label="Smoothed Curve", color="blue"
        )
        plt.scatter(
            interpolated_points['wavelength'], interpolated_points['reflectance'],
            color="red", label="Data Points", zorder=5
        )
        plt.xlabel("Wavelength (µm)")
        plt.ylabel("Reflectance (%)")
        plt.legend()
        plt.grid()
        plt.title("Reflectance vs. Wavelength")
        plt.show()

    def plot_stack(self, angle, polarization):
        settings = load_settings()
        dbr_material = self.dbr_stack  # Example: [[100.0, 'Constant', 'GaSb_ln'], [100.0, 'Constant', 'AlAsSb_ln']]
        metal_layers = self.metal_layers
        substrate_material = self.substrate_layer  # Example: [[nan, 'Constant', 'GaSb_ln']]
        nlamb = 3500
        x = np.linspace(2.5, 10, nlamb) * 1000  # array of wavelengths (in nanometers), consisting of nlamb = 3500 points

        # Fix substrate material by replacing it with its corresponding refractive index function
        if isinstance(substrate_material, list) and len(substrate_material) > 0:
            if substrate_material[0][2] == "GaSb_ln":
                substrate_material[0][2] = GaSb_ln(x)
            elif substrate_material[0][2] == "GaAs_ln":
                substrate_material[0][2] = GaAs_ln(x)
            else:
                substrate_material[0][2] = [1.0, 0.0]

        # Replace materials in DBR stack with their corresponding refractive index functions
        for layer in dbr_material:
            if layer[2] == "GaSb_ln":
                layer[2] = GaSb_ln(x)
            elif layer[2] == "AlAsSb_ln":
                layer[2] = AlAsSb_ln(x)
            else:
                layer[2] = [1.0, 0.0]

        # Combine all layers into the final structure
        Ls_structure = (
            [[np.nan, "Constant", [1.0, 0.0]]] +  # Initial spacer layer
            metal_layers +                        # Metal layers
            [[239.0, "Constant", AlAsSb_ln(x)]] +  # Example additional layer
            dbr_material +                        # DBR stack layers
            substrate_material                    # Substrate layer
        )
        Ls_structure = Ls_structure[::-1]  # Reverse the structure as required

        # Print results for debugging
        print("Extracted substrate material: " + str(substrate_material))
        print("Extracted DBR materials: " + str(dbr_material))
        print("Final structure: " + str(Ls_structure))

        # Calculate reflectance and transmittance
        incang = angle * np.pi / 180 * np.ones(x.size)  # Incident angle

        rs, rp, Ts, Tp = MF.calc_rsrpTsTp(incang, Ls_structure, x)
    
        # Initialize figure and axis
        fig, ax1 = plt.subplots(figsize=(8, 5))
    
        # Handle user-specified polarization
        if polarization == "s":
            R0 = (abs(rs))**2
            T0 = np.real(Ts)
            Abs1 = 1.0 - R0 - T0
            ax1.plot(x / 1000, R0, label='Reflectance (s-pol)', color='blue')
        elif polarization == "p":
            R0 = (abs(rp))**2
            T0 = np.real(Tp)
            Abs1 = 1.0 - R0 - T0
            ax1.plot(x / 1000, R0, label='Reflectance (p-pol)', color='red')
        elif polarization == "both":
            R0_s = (abs(rs))**2
            R0_p = (abs(rp))**2
            R0_avg = 0.5 * (R0_s + R0_p)  # Average reflectance for unpolarized light
            ax1.plot(x / 1000, R0_s, label='Reflectance (s-pol)', color='blue', linestyle='--')
            ax1.plot(x / 1000, R0_p, label='Reflectance (p-pol)', color='red', linestyle='--')
            ax1.plot(x / 1000, R0_avg, label='Reflectance (avg)', color='green')
        else:
            raise ValueError("Invalid polarization. Choose 's', 'p', or 'both'.")
    
        # Customize plot
        ax1.set_xlabel('Wavelength (μm)', size=12)
        ax1.set_ylabel('Reflectance', size=12)
        ax1.set_title('Reflectance of Custom Layer Stack', size=16)

        # Adjust x-axis range and ticks
        ax1.set_xlim([2.5, 10])  # Limit x-axis from 2.5 to 10
        ax1.set_xticks(np.arange(3, 11, 1))  # Set ticks at every 1 unit, starting at 3

        # Add grid
        ax1.grid(alpha=0.2)

        # Add legend
        ax1.legend()

        # Tight layout
        plt.tight_layout()

        # Show the plot
        plt.show()
    
        # Save settings if needed
        save_settings(settings)

    
