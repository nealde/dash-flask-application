title: SPM Model Teardown
date: 2018-11-10
descr: An explanation of the Single Particle physics-based battery model
tags: [spm, single-particle-model, battery, model]

An interactive form of the model is available [here](/dashapp/single-particle)

The Single Particle Model (SPM) is a relatively sophisticated physics-based lithium ion battery model.  It incorporates Fick's law of diffusion and Butler-Volmer kinetics, but does not include any electrolyte effects.

Below is a representation of a typical cell - it has a cathode, a separator, and an anode. The cathode and anode regions are the ones relevant to this model, which
are where lithium is accrued during discharge and charge, respectively.

![typical_cell](/img/spm/typical_cell.png)

In practical terms, during charge, a lithium ion deintercalates from the cathode and, upon leaving the surface of the positive electrode particle, is instantly teleported to the surface of the negative electrode particle, where it intercalates and is stored internally.  The concentrations in both the positive and negative electrodes are tracked and the surface area is calculated based upon the assumed particle radius, electrode thickness, and active area per unit volume.  The particles are all assumed to be perfect spheres of uniform size.

![spm](/img/spm/spm_3d.png#center)

The model can be split into a few different mechanisms:

#### Mass Transport - Fick's 2nd Law of Diffusion

$$\frac{\partial c_{s}}{\partial t} = \frac{D_s}{r^2}\frac{\partial}{\partial r}(r^2 \frac{\partial c_s}{\partial r})$$  

$$concentration: c_s \; [\frac{mol}{m^2}]$$   

$$Solid-phase \; diffusion \;  rate: D_s \; [\frac{m^2}{s}]$$

This equation describes the way that lithium ions diffuse once inside the particles.  This is a partial differential equation - the left hand side is the derivative with respect to time, and the right hand side is the derivative with respect to space.  This particular formulation captures the spherical nature of the particles.

The For this set of equations, which exist in both the positive and negative particle, we need one initial condition for time and two boundary conditions for space.  The initial condition is the initial concentration at all r:  
$$c_s[0,r] = c_{s, initial}$$

The boundary conditions are Radial Symmetry at the center and the ions either enter or leave the surface based on the current:

$$\frac{\partial c_s}{\partial r} = 0 @ [t, r=0]$$  

$$\frac{\partial c_s}{\partial r} = \frac{-J}{D_s} @ [t, r=R]$$  

where J is the ionic current, or the rate at which Li ions are entering or leaving the particle.

The current is dictated by Butler-Volmer kinetics, which relate the potential to the current.  This can be thought of as one element of a battery's 'resistance' - in order to move electrons, there has to be a voltage drop.  This really describes how the amount of current that flows relates to the difference between the circuit voltage and the battery's open circuit potential (U).  This is what gives a battery discharge curve its shape and really dictates the voltage window of the battery.

$$j = kc_{s,max}c^{0.5}_{e}(1-x_{surf})^{0.5}x_{surf}^{0.5}[exp(\frac{0.5 F}{RT}\eta)-exp(-\frac{0.5 F}{RT}\eta)]$$

$$\eta = \phi(x_{surf})-U$$

For the model (as implemented in [Ampere](http://github.com/nealde/ampere)), the following parameters are available:  

| name   | description                                 | default value | Units   |
|--------|---------------------------------------------|---------------|---------|
| Dn     | Li+ Diffusivity in negative particle        | 3.9e-14       | m^2/s  |
| Dp     | Li+ Diffusivity in positive particle        | 1e-14         | m^2/s  |
| Rn     | Negative particle radius                    | 2e-6          | m       |
| Rp     | Positive particle radius                    | 2e-6          | m       |
| T      | Ambient Temperature                         | 303.15        | K       |
| an     | Surface area per unit volume of negative electrode          | 723600        |   m^2/m^3      |
| ap     | Surface area per unit volume of positive electrode          | 885000        |    m^2/m^3     |
| ce     | Starting electrolyte Li+ concentration      | 1000          | mol/m^3 |
| csnmax | Maximum Li+ concentration of negative solid | 30555         | mol/m^3 |
| cspmax | Maximum Li+ concentration of positive solid | 51555         | mol/m^3 |
| kn     | Negative electrode reaction rate            | 5.0307e-9     | m^4/mol s        |
| kp     | Positive electrode reaction rate            | 2.334e-9      |   m^4/mol s      |
| ln     | Negative electrode thickness                | 88e-6         | m       |
| lp     | Positive electrode thickness                | 80e-6         | m       |
