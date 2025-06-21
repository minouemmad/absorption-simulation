# Funcs.py
# -*- coding: utf-8 -*-
NNN = []
from numpy import *
import LD   # import from "Lorentz_Drude_funcs.py"
import numpy as np
def calc_Nlayer(layers, x, num_lay):
    try:
        case = layers[num_lay][1]
        params = layers[num_lay][2]
        
        while len(params) < 7:
            params.append(0)

        materials, delta_n, delta_alpha, delta_omega_p, delta_f, delta_gamma, delta_omega =  params

        if case == 'Constant':
            v2p=[layers[num_lay][2][0],layers[num_lay][2][1]]
            nnn=v2p[0]; kap=abs(v2p[1])
            Nlay=(nnn-1j*kap)*ones(x.size)
        elif case == 'Cauchy':
            v5p=[layers[num_lay][2][0],layers[num_lay][2][1],layers[num_lay][2][2],
                layers[num_lay][2][3],layers[num_lay][2][4]]
            nnn=v5p[0]+v5p[1]/x**2+v5p[2]/x**4; kap=abs(v5p[3])*exp(v5p[4]/x)
            Nlay=nnn-1j*kap
        elif case == 'Sellmeier':
            v2p=[layers[num_lay][2][0],layers[num_lay][2][1], layers[num_lay][2][2]]
            nnn=sqrt(v2p[0]+v2p[1]*(x*(1e-9))**2/((x*(1e-9))**2-v2p[2]**2))
            lmbd = 7.8e-6
            #kap = ((x*(1e-9))/(4*pi))*(-168.5 + 90.45*(x*(1e-9)) - 3.59*(x*(1e-9)))
            kap = 0.
            Nlay=nnn-1j*kap
        elif case == 'Sellmeier-epi':
            v2p=[layers[num_lay][2][0],layers[num_lay][2][1], layers[num_lay][2][2]]
            nnn=sqrt(v2p[0]+v2p[1]*(x*(1e-9))**2/((x*(1e-9))**2-v2p[2]**2))
            lmbd = 7.8e-6
            kap = ((x*(1e-7))/(4*pi))*(-168.5 + 90.45*(x*(1e-3)) - 3.59*(x*(1e-3))**2)*((10.0e16)/(10.0e18))
            # kap = ((x*(1e-9))/(4*pi))*(22.0 + 12.6*(x*(1e-9)) - 2.59*(x*(1e-9))**2)
            #kap = 0
            Nlay=nnn-1j*kap

        elif case == 'Sellmeier-sub':
            v2p=[layers[num_lay][2][0],layers[num_lay][2][1], layers[num_lay][2][2]]
            nnn=sqrt(v2p[0]+v2p[1]*(x*(1e-9))**2/((x*(1e-9))**2-v2p[2]**2))
            lmbd = 7.8e-6
            kap = ((x*(1e-7))/(4*pi))*(22.0 + 12.6*(x*(1e-3)) - 2.59*(x*(1e-3))**2)*((10.0e17)/(10.0e18))

            #kap = ((x*(1e-9))/(4*pi))*(-168.5 + 90.45*(x*(1e-9)) - 3.59*(x*(1e-9))**2)
            #kap = 0
            Nlay=nnn-1j*kap
        
        elif case == 'Metal-Approx':
            v2p=[layers[num_lay][2][0],layers[num_lay][2][1]] # v2p[0] = Plasma Freq. ,  v2p[1] = Damp Const.
            omga = (2*pi)*(3e8)/x
            ep_1 = 1 - ((v2p[0])**2/(omga**2 + v2p[1]))
            ep_2 = (v2p[1]*v2p[0]**2)/(omga*(omga**2 + v2p[1]))
            nnn = sqrt((1/2)*(ep_1 + sqrt(ep_1**2 + ep_2**2)))
            kap = ep_2/(2*nnn)
            Nlay = nnn - 1j*kap

        elif case == 'Lorentz-Drude':
            v2p=[layers[num_lay][2][0]]
            v2p, delta_n, delta_alpha, delta_omega_p, delta_f, delta_gamma, delta_omega = params
            
            # Clamp optional delta parameters
            delta_n = delta_n if delta_n else 0.0
            delta_alpha = delta_alpha if delta_alpha else 0.0
            delta_omega_p = delta_omega_p if delta_omega_p else 0.0
            delta_f = delta_f if delta_f else 0.0
            delta_gamma = delta_gamma if delta_gamma else 0.0
            delta_omega = delta_omega if delta_omega else 0.0

            # Use DB model if material is in a specific format (e.g., 'Ag-DB')
            if isinstance(v2p[0], str) and v2p[0].endswith('-DB'):
                material = v2p[0][:-3]  # Remove '-DB' suffix
                Metal = LD.LD(x * 1e-9, material, delta_omega_p, delta_f, delta_gamma, delta_omega, model='DB')
            else:
                Metal = LD.LD(x * 1e-9, v2p, delta_omega_p, delta_f, delta_gamma, delta_omega, model='LD')
            
            # Adjust RI delta parameters
            nnn = Metal.n + delta_n
            kap = Metal.k + delta_alpha
            print(f"Updated n: {nnn}, Updated k: {kap}")
            Nlay = nnn - 1j*kap
                
        elif case == 'Drude':
            v2p=[layers[num_lay][2][0],layers[num_lay][2][1],layers[num_lay][2][2]]   # f_o, w_o, G       
            ehbar = 1.519250349719305e+15 # e/hbar where hbar=h/(2*pi) and e=1.6e-19
            twopic = 1.883651567308853e+09  # twopic=2*pi*c where c is speed of light
            omega_light = twopic / (x*1e-9);  # angular frequency of light (rad/s)        
            epsilon_D = zeros(len(omega_light), dtype=complex)
            for i, w in enumerate(omega_light):
                epsilon_D[i] = 1 - (v2p[0] * (v2p[1]*ehbar) ** 2 / (w ** 2 + 1j * (v2p[2]*ehbar) * w))
            epsilon = epsilon_D
            Nlay = sqrt(epsilon)
                
        elif case == 'File':
            aux=loadtxt(layers[num_lay][2][0]) # N,k data
            nnn=interp(x,aux[:,0],aux[:,1]) 
            kap=interp(x,aux[:,0],aux[:,2]) 
            Nlay=nnn-1j*abs(kap); 
        elif case == 'BK7':
            n2=1+(1.03961*x**2)/(x**2-6.0e3)+(0.23179*x**2)/ \
            (x**2-2.0e4)+(1.0146*x**2)/(x**2-1.0e8)
            nnn=sqrt(n2)
            Nlay=nnn-1j*0.0
            
        # Validate result
        if np.any(np.isnan(Nlay)) or np.any(np.isinf(Nlay)):
            return np.ones_like(x, dtype=complex)  # Default to air if invalid
        return Nlay
        
    except Exception as e:
        print(f"Error calculating Nlayer: {e}")
        return np.ones_like(x, dtype=complex)  # Default to air if error

 
def calc_rsrpTsTp(incang, layers, x):
    # Input validation
    x = np.asarray(x)
    if np.any(x <= 0):
        raise ValueError("Wavelength values must be positive")
    
    # Initialize all return arrays
    rs = np.zeros(x.size, dtype=complex)
    rp = np.zeros(x.size, dtype=complex)
    Ts = np.zeros(x.size, dtype=complex)
    Tp = np.zeros(x.size, dtype=complex)
    
    Ms = np.zeros([x.size, 2, 2], dtype=complex)
    Mp = np.zeros([x.size, 2, 2], dtype=complex)
    S = np.zeros([x.size, 2, 2], dtype=complex)
    P = np.zeros([x.size, 2, 2], dtype=complex)
    
    # Initialize with identity matrices
    Ms[:, 0, 0] = 1
    Ms[:, 1, 1] = 1
    Mp[:, 0, 0] = 1
    Mp[:, 1, 1] = 1
    
    # Calculate N0 with validation
    im = 0
    try:
        N0 = calc_Nlayer(layers, x, im)
        if np.any(np.isnan(N0)) or np.any(np.isinf(N0)):
            return rs, rp, Ts, Tp  # Return zeros if invalid
        
        N0s = N0 * np.cos(incang)
        N0p = N0 / np.cos(incang)
        
        for im in range(1, len(layers)-1):
            Nlay = calc_Nlayer(layers, x, im)
            if np.any(np.isnan(Nlay)) or np.any(np.isinf(Nlay)):
                continue  # Skip invalid layers
                
            ARR = np.sqrt(Nlay**2 - N0**2 * (np.sin(incang)**2))
            Ns = np.abs(np.real(ARR)) - 1j * np.abs(np.imag(ARR))
            d = layers[im][0]
            
            if np.isnan(d) or d <= 0:
                continue
                
            Dr = 2 * np.pi * d / x * Ns
            Np = Nlay**2 / Ns
            
            # Handle division by zero in Np
            Np = np.where(np.abs(Ns) > 1e-10, Nlay**2 / Ns, 0)
            
            for ix in range(x.size):
                cosDr = np.cos(Dr[ix])
                sinDr = np.sin(Dr[ix])
                
                # Build S and P matrices with validation
                S[ix, :, :] = [
                    [cosDr, (1j/Ns[ix])*sinDr if np.abs(Ns[ix]) > 1e-10 else 0],
                    [1j*Ns[ix]*sinDr if np.abs(Ns[ix]) > 1e-10 else 0, cosDr]
                ]
                
                P[ix, :, :] = [
                    [cosDr, (1j/Np[ix])*sinDr if np.abs(Np[ix]) > 1e-10 else 0],
                    [1j*Np[ix]*sinDr if np.abs(Np[ix]) > 1e-10 else 0, cosDr]
                ]
                
                # Safe matrix multiplication
                try:
                    Ms[ix, :, :] = Ms[ix, :, :] @ S[ix, :, :]
                    Mp[ix, :, :] = Mp[ix, :, :] @ P[ix, :, :]
                except:
                    Ms[ix, :, :] = np.eye(2, dtype=complex)
                    Mp[ix, :, :] = np.eye(2, dtype=complex)
        
        # Final medium calculation
        im = len(layers)-1
        Nm = calc_Nlayer(layers, x, im)
        if np.any(np.isnan(Nm)) or np.any(np.isinf(Nm)):
            Nm = np.ones_like(Nm)  # Default to air if invalid
            
        ARR = np.sqrt(Nm**2 - N0**2 * (np.sin(incang)**2))
        Nms = np.abs(np.real(ARR)) - 1j * np.abs(np.imag(ARR))
        Nmp = Nm**2 / Nms
        
        for ix in range(x.size):
            # Calculate reflection coefficients with validation
            try:
                V_s = Ms[ix, :, :] @ [[1.], [Nms[ix]]]
                Bs = V_s[0]
                Cs = V_s[1]
                rs[ix] = (N0s[ix]*Bs - Cs) / (N0s[ix]*Bs + Cs) if np.abs(N0s[ix]*Bs + Cs) > 1e-10 else 0
                
                V_p = Mp[ix, :, :] @ [[1.], [Nmp[ix]]]
                Bp = V_p[0]
                Cp = V_p[1]
                rp[ix] = (N0p[ix]*Bp - Cp) / (N0p[ix]*Bp + Cp) if np.abs(N0p[ix]*Bp + Cp) > 1e-10 else 0
                
                # Calculate transmission coefficients
                Ts[ix] = 2 / (N0s[ix]*Bs + Cs) if np.abs(N0s[ix]*Bs + Cs) > 1e-10 else 0
                Tp[ix] = 2 / (N0p[ix]*Bp + Cp) if np.abs(N0p[ix]*Bp + Cp) > 1e-10 else 0
            except:
                rs[ix] = 0
                rp[ix] = 0
                Ts[ix] = 0
                Tp[ix] = 0
                
    except Exception as e:
        print(f"Error in calc_rsrpTsTp: {e}")
    
    return rs, rp, Ts, Tp

def compute_electric_field_profile(angle_rad, layer_structure, wavelengths):
    """
    Calculate electric field intensity |E(z)|^2 profile across a multilayer stack.
    angle_rad: scalar float angle in radians.
    layer_structure: list of layers.
    wavelengths: array of wavelengths in nm.

    Returns:
        z_positions: depth values in microns
        E2_profile: corresponding electric field intensity |E(z)|^2
    """
    # (Dummy template - you must replace this with actual EM field calculations.)
    z_positions = np.linspace(0, 10, 1000)  # e.g., 0 to 10 µm depth
    E2_profile = np.abs(np.sin(2 * np.pi * z_positions / 1.5))**2  # dummy sinusoidal profile
    return z_positions, E2_profile
