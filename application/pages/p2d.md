title: P2D Model Teardown
date: 2021-03-15
descr: An explanation of the Pseudo Two-Dimensional physics-based battery model
tags: [p2d, p2d-model, battery, model]


As an introductory statement, if the [Single Particle Model](/articles/spm) can be thought of as two single particles, illustrated below:

![spm](/img/spm/spm_3d.png)

Then the Pseudo Two-Dimensional model can be thought of as a bunch of these particles, at different depths in the electrode, surrounded by electrolyte.  

![p2d](/img/p2d/p2d_3d.png)

What this means is that the additional complexity compared to the Single Particle Model nets you the following things:

* Increased accuracy related to depth effects (lithium is preferentially selected from the closer electrode material)
* Increased accuracy related to electolyte effects (lithium diffusion through electrolyte can be slow)
* Increased accuracy related to overpotentials at the electrode surface (more accurately captures Solid-Electrolyte Interface growth or Lithium Plating)

### What is Lithium Plating?

![plating_1](/img/p2d/plating_1.jpg)

Lithium plating is the act of Lithium precipitating out of solution (electrolyte) rather than moving nicely into the electrode material (intercalation).  It generally happens when the overpotential, or electrochemical driving force, goes negative at the grapitic electrode.  This can happen during charge, especially during fast charge, right at the CC-CV (constant-current, constant-voltage) knee during the charge cycle.

![plating_2](/img/p2d/plating_2.png)

This reaction is irreversible and is one of the main modes of degradation of lithium cells (with the others being related to material stresses caused by swelling during charge / discharge).

### How Can A Battery Model Help?

By restricting the overpotential during a charge cycle, a properly-fitted battery model can restrict the charging conditions such that the overpotential at the negative electrode never goes negative, which can greatly extend the lifetime of the battery.

## The Model

The pseudo-two-dimensional model can be split into a few different mechanisms:

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

The current is dictated by Butler-Volmer kinetics, which relate the potential to the current.  This can be thought of as one element of a battery's 'resistance' - in order to move electrons, there has to be a voltage drop.  This really describes how the amount of current that flows relates to the difference between the circuit voltage and the battery's open circuit potential (U).  This is what gives a battery discharge curve its shape and dictates the voltage window of the battery.

$$j = kc_{s,max}c^{0.5}_{e}(1-x_{surf})^{0.5}x_{surf}^{0.5}[exp(\frac{0.5 F}{RT}\eta)-exp(-\frac{0.5 F}{RT}\eta)]$$

$$\eta = \phi(x_{surf})-U$$

This set of equations is replicated for each simulated particle, which are treated mathematically as discrete entities whose only interaction is through the varying concentration / potential gradients present in the electrolyte.

#### Electonic Conduction

$$\sigma _{eff, p} \frac{\partial ^2 \Phi_1}{\partial x^2} = a_pFj_p$$ $\Phi_1$ is the solid-phase potential

#### Charge Balance

$$-\sigma _{eff, p} \frac{\partial  \Phi_1}{\partial x} -\kappa_{eff, p} \frac{\partial \Phi_2}{\partial x} + \frac{2 \kappa_{eff, p}RT}{F}(1-t_+)\frac{\partial \ln c}{\partial x} = I$$

$\Phi_2$ is the liquid phase potential

#### Material Balance (back to Fick's Law)

$$-\epsilon _{p} \frac{\partial  c}{\partial x} = -D_{eff, p} \frac{\partial ^2 c}{\partial x^2} + a_p(1-t_+)j_p$$

$c$ is the electrolyte concentration

#### Other expressions

##### Effective (read: Experimentally Fitted) Reaction Rate

$$\kappa _{eff,p} = \epsilon_p^{brugg}\kappa = 0.01775(4.1253 E^{-2}+5.007 E^{-1}c-4.7212 E^{-1}c^2 +1.5094 E^{-1}c^3-1.6018 E^{-2}c^4)$$

$\kappa$ is the given reaction rate

$brugg$ is the bruggman coefficient - it captures the tortuosity associated with the pores in the electrode

$\epsilon$ is the volume fraction of the electrode that is porous

##### Butler-Volmer Kinetics at Each Electrode

$$j_p = 2\kappa_p(c_{s, max,p}-c^s_p)^{0.5}c^{s0.5}_pc^{0.5}sinh(\frac{0.5F}{RT}(\Phi_1-\Phi_2-U_p))$$

$U_p$ is a fitted relationship between the open-circuit potential and the degree of lithiation of each electrode - this is a material property that is generally measured experimentally.

### The Path of A Lithium Particle

During charge, the lithium begins in the anode.  An external voltage is applied, and this splits the electron off of the Lithium. The electron is removed from the system by way of electronic conduction through the graphite structure to the current collector, and the Li+ diffuses out of the porous electrode. These relationships are captured by the Fick's Law equation, the Electronic Conduction, the Charge Balance, and the Butler-Volmer Kinetic equations.

As the Li+ is generated at the anode and diffuses into the electrolyte, the charge balance of the system changes. These mechanics are captured in the Charge Balance equation, which relies on $c$, the concentration of lithium in the electrolyte, $\kappa_{eff}$, the effective rate of reaction, and $\sigma_{eff}$, the electronic conductivity of the material. Together, this equation couples the diffusion, reaction rate, and electronic conduction equations in order to accurately capture the driving force behind the charge at different points in the electrode.

Once the lithium ion leaves the anode particle, it diffuses through the separator in the electrolyte.

When it reaches the cathode, it is free to combine with another electron and this process happens in reverse - the varying potentials in the solid material and liquid electrolyte drive the local reactions, where Lithium intercalates into the cathodic crystal structure.

## Implementation

For the model (as implemented in [Ampere](http://github.com/nealde/ampere)) the following parameters are available:

|     name    |                           description                          |  default value  | Units              |
| ----------- | -----------------------------------------------                | --------------- | ------------------ |
| D1          | Li+ Diffusivity in electrolyte                                 | 0.15e-8         | cm^2/s             |
| Dp          | Li+ Diffusivity in positive particle                           | 7.2e-14         | cm^2/s             |
| Dn          | Li+ Diffusivity in negative particle                           | 7.5e-14         | cm^2/s             |
| cspmax      | Maximum Li concentration of positive solid                     | 45829           | mol/m^3            |
| csnmax      | Maximum Li concentration of negative solid                     | 30555           | mol/m^3            |
| ls          | Separator thickness                                            | 16e-6           | m                  |
| lp          | Positive electrode thickness                                   | 43e-6           | m                  |
| ln          | Negative electrode thickness                                   | 46.5e-6         | m                  |
| es          | Separator volume fraction of pores                             | 0.45            | m^3/m^3            |
| ep          | Positive electrode volume fraction of pores                    | 0.4             | m^3/m^3            |
| en          | Negative electrode volume fraction of pores                    | 0.38            | m^3/m^3            |
| efn         | Negative electrode filler fraction                             | 0.0326          | m^3/m^3            |
| efp         | Positive electrode filler fraction                             | 0.025           | m^3/m^3            |
| brugs       | Separator Bruggeman coefficient - pore tortuosity              | 1.5             |                    |
| brugn       | Negative electrode Bruggeman coefficient - pore tortuosity     | 1.5             |                    |
| brugp       | Positive electrode coefficient - pore tortuosity               | 1.5             |                    |
| sigma_n     | Negative electrode electrical conductivity                     | 100             | S/m                |
| sigma_p     | Positive electrode electrical conductivity                     | 10              | S/m                |
| t+          | Transference Number - fraction of ionic current carried by Li+ | 0.363           |                    |
| Rp          | Positive particle radius                                       | 10e-6           | m                  |
| Rn          | Negative particle radius                                       | 8e-6            | m                  |
| T           | Ambient Temperature                                            | 303.15          | K                  |
| ce          | Starting electrolyte Li+ concentration                         | 1200            | mol/m^3            |
| ap          | Surface area of positive electrode per volume                  | 885000          | m^2/m^3            |
| an          | Surface area of negative electrode per volume                  | 723600          | m^2/m^3            |
| kp          | Positive electrode reaction rate                               | 0.10307e-9      | m^2.5/(mol^0.5s)   |
| kn          | Negative electrode reaction rate                               | 0.1334e-9       | m^2.5/(mol^0.5s)   |
| N1          | Positive electrode number of FD Nodes                          | 7               |                    |
| N2          | Separator number of FD Nodes                                   | 3               |                    |
| N3          | Negative electrode number of FD Nodes                          | 7               |                    |
| Nr1         | Positive particle number of FD nodes (per particle)            | 3               |                    |
| Nr2         | Negative particle number of FD nodes (per particle)            | 3               |                    |

