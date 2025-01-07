# Funcs.py
# -*- coding: utf-8 -*-
NNN = []
from numpy import *
import LD   # import from "Lorentz_Drude_funcs.py"

def calc_Nlayer(layers,x,num_lay):
    case = layers[num_lay][1]
    if case == 'Constant':
        v2p=[layers[num_lay][2][0],layers[num_lay][2][1]]
        #print(v2p)
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
        Metal = LD.LD(x*1e-9, material = v2p[0],model = 'LD') # Metal with dielectric function of LD model
        nnn = Metal.n
        kap = Metal.k
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
    return Nlay
 
def calc_rsrpTsTp(incang,layers,x):
    Ms=zeros([x.size,2,2],dtype=complex); Mp=zeros([x.size,2,2],dtype=complex)
    S=zeros([x.size,2,2],dtype=complex); P=zeros([x.size,2,2],dtype=complex)
    Ms[:,0,0]=1; Ms[:,1,1]=1; Mp[:,0,0]=1; Mp[:,1,1]=1
    rs=zeros((x.size),dtype=complex); rp=zeros((x.size),dtype=complex)
    Ts=zeros((x.size),dtype=complex); Tp=zeros((x.size),dtype=complex);
    im=0
    N0=calc_Nlayer(layers,x,im)
    N0s=N0*cos(incang); N0p=N0/cos(incang)
    for im in range(1,len(layers)-1):
        Nlay=calc_Nlayer(layers,x,im)
        ARR=sqrt(Nlay**2-N0**2*(sin(incang)**2))
        Ns=abs(real(ARR)) - 1j*abs(imag(ARR))
        d=layers[im][0] 
        Dr=2*pi*d/x*Ns 
        Np=Nlay**2/Ns
        for ix in range(x.size):
            S[ix,:,:]=[[cos(Dr[ix]), 1j/Ns[ix]*sin(Dr[ix])],
                [1j*Ns[ix]*sin(Dr[ix]), cos(Dr[ix])]]
            P[ix,:,:]=[[cos(Dr[ix]), 1j/Np[ix]*sin(Dr[ix])],
                [1j*Np[ix]*sin(Dr[ix]), cos(Dr[ix])]]
            Ms[ix,:,:]=Ms[ix,:,:]@S[ix,:,:]; Mp[ix,:,:]=Mp[ix,:,:]@P[ix,:,:]
    im=len(layers)-1
    Nm=calc_Nlayer(layers,x,im)
    ARR=sqrt(Nm**2-N0**2*(sin(incang)**2))
    Nms=abs(real(ARR)) - 1j*abs(imag(ARR))
    Nmp=Nm**2/Nms 
    for ix in range(x.size):
        V_s = Ms[ix,:,:]@[[1.],[Nms[ix]]]; Bs=V_s[0]; Cs=V_s[1]
        rs[ix]=(N0s[ix]*Bs-Cs)/(N0s[ix]*Bs+Cs)
        Ts[ix]=4*N0s[ix]*real(Nms[ix])/(abs(N0s[ix]*Bs+Cs))**2 
        V_p = Mp[ix,:,:]@[[1.],[Nmp[ix]]]; Bp=V_p[0]; Cp=V_p[1]
        rp[ix]=(N0p[ix]*Bp-Cp)/(N0p[ix]*Bp+Cp)
        Tp[ix]=4*N0p[ix]*real(Nmp[ix])/(abs(N0p[ix]*Bp+Cp))**2
    return [rs,rp,Ts,Tp]