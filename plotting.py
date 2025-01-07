#plotting.py - Manages the reflectance calculation and plotting.
import numpy as np
import matplotlib.pyplot as plt
import Funcs as MF
from materials import *
from utils import *

class PlotReflectance:
    def __init__(self, dbr_stack=None, metal_layers=None, substrate_layer=None):
        self.dbr_stack = dbr_stack
        self.metal_layers = metal_layers
        self.substrate_layer = substrate_layer

    def plot_raw_data(self, raw_data):
        wavelengths = raw_data['wavelength']
        reflectance = raw_data['reflectance']
        
        plt.plot(wavelengths, reflectance, label="Raw Data", linestyle='--', color='blue')
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Reflectance")
        plt.legend()
        plt.show()  # Show plot immediately after raw data is uploaded

    # def plot_stack(self, angle, polarization):
    #     # Simulated reflectance data plotting
    #     wavelengths, simulated_reflectance = self.calculate_reflectance(angle, polarization)
        
    #     plt.plot(wavelengths, simulated_reflectance, label="Simulated Reflectance", color='red')
    #     plt.xlabel("Wavelength (nm)")
    #     plt.ylabel("Reflectance")
    #     plt.legend()
    #     plt.show()
    

    def plot_stack(self, angle, polarization):
        settings = load_settings()
        dbr_material = self.dbr_stack  # Example: [[100.0, 'Constant', 'GaSb_ln'], [100.0, 'Constant', 'AlAsSb_ln']]
        metal_layers = self.metal_layers
        substrate_material = self.substrate_layer  # Example: [[nan, 'Constant', 'GaSb_ln']]
        nlamb = 3500
        x = np.linspace(2.5, 15, nlamb) * 1000  # array of wavelengths (in nanometers), consisting of nlamb = 3500 points

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
        fig, ax1 = plt.subplots(figsize=(10, 5))
    
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
    
        # Customize the plot
        ax1.set_xlabel('Wavelength (μm)', size=12)
        ax1.set_ylabel('Reflectance', size=12)
        ax1.set_title('Reflectance of Custom Layer Stack', size=16)
        ax1.legend()
        ax1.grid(alpha=0.2)
    
        plt.tight_layout()
        plt.show()
    
        # Save settings if needed
        save_settings(settings)

    
