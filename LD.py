"""
LD.py
 This module calculates the real and imaginary part of the dielectric function,
 real and imaginary part of the refractive index for different metals using either
 Drude model (D) and Lorentz-Drude model (LD). The parameters are obtained from
 Rakic et al. This module is inspired by LD.m
 http://www.mathworks.com/matlabcentral/fileexchange/18040-drude-lorentz-and-debye-lorentz-models-for-the-dielectric-constant-of-metals-and-water

    Example:
    To use in other python files

    from LD import LD # Make sure the file is accessible to PYTHONPATH or in the same directory of file which is trying to import
    import numpy as np
    lamda = np.linspace(300E-9,1000E-9,100) # Creates a wavelength vector from 300 nm to 1000 nm of length 100
    gold = LD(lamda, material = 'Au',model = 'LD') # Creates gold object with dielectric function of LD model
    print gold.epsilon_real
    print gold.epsilon_imag
    print gold.n
    print gold.k
    gold.plot_epsilon()
    gold.plot_n_k()

%   INPUT PARAMETERS:
%
%       lambda   ==> wavelength (meters) of light excitation on material. Numpy array
%
%       material ==>    'Ag'  = silver
%                       'Al'  = aluminum
%                       'Au'  = gold
%                       'Cu'  = copper
%                       'Cr'  = chromium
%                       'Ni'  = nickel
%                       'W'   = tungsten
%                       'Ti'  = titanium
%                       'Be'  = beryllium
%                       'Pd'  = palladium
%                       'Pt'  = platinum
%
%       model    ==> Choose 'LD' or 'D' for Lorentz-Drude or Drude model.
%
%       Reference:
%       Rakic et al., Optical properties of metallic films for vertical-
%       cavity optoelectronic devices, Applied Optics (1998)

"""

import numpy as np
from refractivesqlite import dboperations as DB
import os
import warnings

class LD():
    def __init__(self, lamda, material, delta_omega_p=0, delta_f=0, 
                 delta_gamma=0, delta_omega=0, model='LD'):
        """
        Initialize the material model
        
        Parameters:
        lamda : array_like
            Wavelength(s) in meters
        material : str or list
            Material name (for DB model) or parameters (for LD/D model)
        model : str
            'DB' for database, 'LD' for Lorentz-Drude, 'D' for Drude
        """
        self.lamda = np.asarray(lamda)
        self.material = material
        self.model = model
        self.db_path = "refractive.db"

        # Delta parameters for adjustments
        self.delta_omega_p = delta_omega_p
        self.delta_f = delta_f
        self.delta_gamma = delta_gamma
        self.delta_omega = delta_omega

        # Initialize database
        self._init_database()

        # Physical constants
        self.twopic = 1.883651567308853e+09  # 2*pi*c (c in nm/s)
        self.ehbar = 1.519250349719305e+15    # e/hbar
        
        # Calculate optical properties
        if model == 'DB':
            self.get_refractive_index_from_db()
        elif model in ['LD', 'D']:
            self.calculate_with_drude_lorentz()
        else:
            raise ValueError(f"Invalid model '{model}'. Use 'DB', 'LD', or 'D'")

        # Complex refractive index and dielectric function
        self.refractive_index = self.n + 1j*self.k
        self.epsilon = self.refractive_index**2
        self.epsilon_real = self.epsilon.real
        self.epsilon_imag = self.epsilon.imag

    def _init_database(self):
        """Initialize the refractiveindex.info database"""
        if not os.path.exists(self.db_path):
            warnings.warn("Downloading refractiveindex.info database (first-time setup)...")
            try:
                db = DB.Database(self.db_path)
                db.create_database_from_url()
                print("Database successfully downloaded.")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize database: {str(e)}")

    def get_refractive_index_from_db(self):
        """Get refractive index from refractiveindex.info database"""
        db = DB.Database(self.db_path)
        
        # Search for material in database
        results = db.search_pages(self.material, exact=True)
        
        if not results:
            available = db.search_pages("")[:5]  # Get first 5 materials as examples
            available_str = "\n".join([f"{r[1]}/{r[2]}/{r[3]}" for r in available])
            raise ValueError(
                f"No data found for material '{self.material}'. "
                f"Example available materials:\n{available_str}"
            )
            
        # For simplicity, use the first result (Rakic data when available)
        preferred = [r for r in results if 'Rakic' in r[3]] or results
        pageid = preferred[0][0]
        
        try:
            mat = db.get_material(pageid)
        except Exception as e:
            raise RuntimeError(f"Failed to load material data: {str(e)}")
        
        # Convert wavelength from meters to microns for database lookup
        wavelength_microns = self.lamda * 1e6
        
        # Get n and k at specified wavelengths
        self.n = np.zeros_like(wavelength_microns)
        self.k = np.zeros_like(wavelength_microns)
        
        for i, wl in enumerate(wavelength_microns):
            self.n[i] = mat.get_refractiveindex(wl)
            self.k[i] = mat.get_extinctioncoefficient(wl)

    def calculate_with_drude_lorentz(self):
        """Calculate using Drude-Lorentz model"""
        # Material parameters from Rakic papers
        if isinstance(self.material, str):
            material_params = self._get_material_params(self.material)
        else:
            material_params = self.material  # Assume parameters were passed directly
            
        omega_p = material_params['omega_p'] * self.ehbar
        f = material_params['f']
        Gamma = [g * self.ehbar for g in material_params['Gamma']]
        omega = [o * self.ehbar for o in material_params['omega']]
        
        # Apply delta adjustments
        omega_p += self.delta_omega_p * self.ehbar
        f = [fi + self.delta_f for fi in f]
        Gamma = [g + self.delta_gamma * self.ehbar for g in Gamma]
        omega = [o + self.delta_omega * self.ehbar for o in omega]
        
        # Angular frequency of light (rad/s)
        omega_light = self.twopic / self.lamda
        
        # Drude term
        epsilon_D = 1 - (f[0] * omega_p**2 / 
                        (omega_light**2 + 1j * Gamma[0] * omega_light))
        
        if self.model == 'D':
            epsilon = epsilon_D
        else:  # LD model
            # Lorentz terms
            epsilon_L = np.zeros_like(omega_light, dtype=complex)
            for k in range(1, len(omega)):
                epsilon_L += (f[k] * omega_p**2) / \
                           (omega[k]**2 - omega_light**2 - 1j * Gamma[k] * omega_light)
            epsilon = epsilon_D + epsilon_L
        
        # Complex refractive index (n + ik)
        self.refractive_index = np.sqrt(epsilon)
        self.n = self.refractive_index.real
        self.k = self.refractive_index.imag

    def _get_material_params(self, material):
        """Get Drude-Lorentz parameters for common materials"""
        params = {
            'Ag': {
                'omega_p': 9.01,
                'f': [0.845, 0.065, 0.124, 0.011, 0.840, 5.646],
                'Gamma': [0.048, 3.886, 0.452, 0.065, 0.916, 2.419],
                'omega': [0.000, 0.816, 4.481, 8.185, 9.083, 20.29]
            },
            'Au': {
                'omega_p': 9.03,
                'f': [0.760, 0.024, 0.010, 0.071, 0.601, 4.384],
                'Gamma': [0.053, 0.241, 0.345, 0.870, 2.494, 2.214],
                'omega': [0.000, 0.415, 0.830, 2.969, 4.304, 13.32]
            },
            # Add other materials as needed
        }
        
        if material not in params:
            raise ValueError(f"No Drude-Lorentz parameters for material '{material}'. "
                           f"Available: {list(params.keys())}")
        
        return params[material]

    def plot_epsilon(self):
        """Plot real and imaginary parts of dielectric function"""
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Convert wavelength to nm for plotting
        wavelength_nm = self.lamda * 1e9
        
        ax1.plot(wavelength_nm, self.epsilon_real, 'b-')
        ax1.set_xlabel('Wavelength (nm)')
        ax1.set_ylabel('Real(ε)')
        ax1.set_title('Real Part of Dielectric Function')
        ax1.grid(True)
        
        ax2.plot(wavelength_nm, self.epsilon_imag, 'r-')
        ax2.set_xlabel('Wavelength (nm)')
        ax2.set_ylabel('Imag(ε)')
        ax2.set_title('Imaginary Part of Dielectric Function')
        ax2.grid(True)
        
        plt.suptitle(f'{self.material} ({self.model} model)')
        plt.tight_layout()
        plt.show()

    def plot_n_k(self):
        """Plot refractive index (n) and extinction coefficient (k)"""
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Convert wavelength to nm for plotting
        wavelength_nm = self.lamda * 1e9
        
        ax1.plot(wavelength_nm, self.n, 'g-')
        ax1.set_xlabel('Wavelength (nm)')
        ax1.set_ylabel('n')
        ax1.set_title('Refractive Index (n)')
        ax1.grid(True)
        
        ax2.plot(wavelength_nm, self.k, 'm-')
        ax2.set_xlabel('Wavelength (nm)')
        ax2.set_ylabel('k')
        ax2.set_title('Extinction Coefficient (k)')
        ax2.grid(True)
        
        plt.suptitle(f'{self.material} ({self.model} model)')
        plt.tight_layout()
        plt.show()


if __name__ == '__main__':
    # Example usage
    wavelengths = np.linspace(200e-9, 2000e-9, 300)  # 200-2000 nm
    
    # Using database (experimental data)
    print("Using refractiveindex.info database:")
    gold_db = LD(wavelengths, 'Au', model='DB')
    gold_db.plot_n_k()
    
    # Using Lorentz-Drude model
    print("\nUsing Lorentz-Drude model:")
    gold_ld = LD(wavelengths, 'Au', model='LD')
    gold_ld.plot_n_k()
    
    # Compare n and k at 500 nm
    idx_500nm = np.argmin(np.abs(wavelengths - 500e-9))
    print(f"\nAt 500 nm:")
    print(f"Database: n = {gold_db.n[idx_500nm]:.3f}, k = {gold_db.k[idx_500nm]:.3f}")
    print(f"LD Model: n = {gold_ld.n[idx_500nm]:.3f}, k = {gold_ld.k[idx_500nm]:.3f}")