title: Ampere - A Framework for High-Performance Battery Models
date: 2019-09-01
descr: A battery modeling framework
tags: [p2d, spm, battery, model]


### The Sci-Kit Learn of Battery Simulation

Battery simulation is hard. The equations are typically very stiff, and often take a large number of nodes to become self-convergent, in particular at high discharge rates.  The goal of [Ampere](http://github.com/nealde/ampere) is to make this a little easier, to let experimentalists worry about what experiments they want to run and let the models take care of themselves.

The syntax for using the models is very simple, and features a sci-kit learn-like interface:
```python
import matplotlib.pyplot as plt
%matplotlib inline
from ampere import SingleParticleFD, PseudoTwoDimFD
spm = SingleParticleFD()
p2d = PseudoTwoDimFD()
```

The model is then interacted with as a model, with available methods:

#### Charge

```python
trial = p2d.charge(current=3.0)
```

![charge](/img/battery/p2d_charge.png)

#### Discharge

```python
trial = p2d.discharge(current=3.0)
```

![discharge](/img/battery/p2d_discharge.png)

#### Piecewise Charge / Discharge

Notice that each charge / discharge cycle begins from the battery state present at the end of the previous cycle. This
is great for doing e.g. Drive Cycle analysis, capturing regenerative braking and accelerations.

```python
times = [500, 400, 600, 200, 50, 700,300, 2000]  # times in seconds
currents = [1.0, -0.5, 1.2, -0.75, 2.0, 0.5, -1.0, 1.5]  # currents in amps, where negative is charge current
trial = p2d.piecewise_current(times, currents)
```

![discharge](/img/battery/piecewise.png)

#### Model Calibration

To help with model calibration, the *fit* method is available and work with *charge*, *discharge*, and *piecewise_current*.

```python
spm.fit([t_exp], [v_exp], currents=[0.5], maxiter=1000, tol=1e-7)
```

##### Starting Values

| Label   | Parameter | Description                      | Starting Value |
|---------|-----------|----------------------------------|----------------|
| Initial | Rp        | Positive particle radius (m)     | 1.5e-6         |
| Initial | lp        | Positive electrode thickness (m) | 85e-6          |
| Target  | Rp        | Positive particle radius (m)     | 2e-06          |
| Target  | lp        | Positive electrode thickness (m) | 80e-5          |

![initial](/img/battery/initial.png)

##### Converged Values

| Label     | Parameter | Description                      | Final Value |
|-----------|-----------|----------------------------------|-------------|
| Converged | Rp        | Positive particle radius (m)     | 1.977e-6    |
| Converged | lp        | Positive electrode thickness (m) | 80.8e-6     |
| Target    | Rp        | Positive particle radius (m)     | 2e-06       |
| Target    | lp        | Positive electrode thickness (m) | 80e-5       |

![converged](/img/battery/converged.png)

##### Piecewise Fitting

The piecewise function can also be used for fitting directly:

```python
spm2.fit(times, v_exp, currents=currents, currents_type='piecewise', tol=1e-8, maxiter=1000)
```

![piecewise_opt](/img/battery/piecewise_opt.png)

### Performance

Because this python package wraps a high-performance C solver, the models are extremely fast:

| Model                                        | Applicability     | Number of Equations | Solve Time  |
|----------------------------------------------|-------------------|---------------------|-------------|
| Single Particle Model (N1=30, N2=30)         | Low Currents      | 68                  | 15.9 ms     | 
| Single Particle model (N1=60, N2=60)         | Moderate Currents | 128                 | 41.1 ms     | 
| P2D Model (N1=7, N2=3, N3=7, Nr1=3, Nr2=3)   | Moderate Currents | 132                 | 48.2 ms     | 
| P2D Model (N1=11, N2=3, N3=11, Nr1=9, Nr2=9) | High Currents     | 328                 | 196.1 ms    | 