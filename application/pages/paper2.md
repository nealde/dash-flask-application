title: Publication - What Can Electrochemistry Learn from Chess?
date: 2018-11-10
descr: Building a Problem-Specific Optimizer using Deep Learning
tags: [data-science, deep-learning, optimization]

### What Can Electrochemistry Learn from Chess? On The Creation of A Problem-Specific Optimizer
*By: Neal Dawson-Elli, Suryanarayana Kolluri, Kishalay Mitra, and Venkat R. Subramanian*

The paper is published and can be found [here](https://iopscience.iop.org/article/10.1149/2.1261904jes/meta)

**This work focuses on the idea that there is more information contained in the error between two time series than
there is in a single-value abstraction of that data (like MSE), and leverages neural networks to take advantage of this 
additional information to make per-parameter adjustments during optimization.**

## Inspiration

The problem formulation in this work was inspired by a paper which created a neural network-based 
[chess algorithm](https://link.springer.com/chapter/10.1007%2F978-3-319-44781-0_11), which was able to increase
the effective size of the training data set by cleverly using a neural network as a board-state-comparator.


![deepchess](/img/paper2/deepchess.png)

Towards that end, I devised a similar formulation for the problem of Battery Model Calibration, where an unknown
modeled state's parameters can be inferred by a voltage vs time graph and a known battery modeled state, as illustrated
using [Anscombe's Quartet](https://en.wikipedia.org/wiki/Anscombe%27s_quartet) and a series of discharge curves, below:

![inspiration_error](/img/paper2/inspiration_error.png)

Just like with Anscombe's Quartet, abstracting to the descriptive statistic Mean Squared Error lost a ton of information,
which should be useful in the task of fitting a complicated model!

## Problem Formulation

![problem_formulation](/img/paper2/problem_formulation.png)

By training the neural network on the nuances associated with the changes in the discharge curve shape, it was able
to make an extremely accurate guess about what the parameters should look like when two curves are dissimilar.

## Toy Problem

To better internalize why Battery Model Calibration is a difficult problem, let's focus on a toy problem - 
we will select 2 parameters, \( l_p \) and \( l_n \), which represent the positive electrode thickness and the negative
electrode thickness, respectively. The model is very sensitive to these parameters.  The 2D plot on the left shows the
optimization pathway, along with the error topology, associated with a grid search of these two parameters from a
target point located at roughly \( 7.5 e^{-5} \) and \( 7.5 e^{-5} \) for \( l_p \) and \( l_n \), respectively.

![optimization](/img/paper2/optimization.png)

Just looking at this, we can see an axis of symmetry running from lower-left to upper-right, which successfully
fools the optimization attempt from the initial guess in the upper left.

However, by using the Neural Network to refine this guess, we can cut across that axis of symmetry, as in the right graph,
and polish that result with an optimizer to leverage the strength of each - the Neural Network nagivates the high-
dimensional space, getting us close to the true value. The optimizer takes the rest of the error out of the guess.

## Full problem

the full problem was changing the following 9 parameters within these bounds using Sobol Sampling:

|     name    |                           description                          | Lower Bound |   Upper Bound   | Units              |
| ----------- | -----------------------------------------------                |             | --------------- | ------------------ |
| D1          | Li+ Diffusivity in electrolyte                                 | 7.5e-11     | 7.5e-9          | m^2/s              |
| Dp          | Li+ Diffusivity in positive particle                           | 3.9e-15     | 3.9e-13         | m^2/s              |
| Dn          | Li+ Diffusivity in negative particle                           | 1.0e-15     | 1.0e-13         | m^2/s              |
| cspmax      | Maximum Li concentration of positive solid                     | 46400       | 56700           | mol/m^3            |
| csnmax      | Maximum Li concentration of negative solid                     | 27500       | 33600           | mol/m^3            |
| ep          | Positive electrode volume fraction of pores                    | 0.4365      | 0.5335          | m^3/m^3            |
| en          | Negative electrode volume fraction of pores                    | 0.3465      | 0.4235          | m^3/m^3            |
| lp          | Positive electrode thickness                                   | 8.8e-6      | 8.8e-5          | m                  |
| ln          | Negative electrode thickness                                   | 8e-6        | 8e-5            | m                  |

To approximate performance in higher dimensions, some variants of the Neural Network were more data-starved than others,
as indicated by the following sampling table, which maps Test Set Error back onto the performance we care about - 
the accurate prediction of unknown model parameters.

| Method             | Mean Relative Absolute Error of Parameters (%) | NN Test Set Error |
|--------------------|------------------------------------------------|-------------------|
| Static Initial Set | 2958                                           |                   |
| 200k Samples       | 56                                             | 0.0324            |
| 50k Sampless       | 58                                             | 0.0391            |
| 20k Samples        | 79                                             | 0.0393            |
| 5k Samples         | 143                                            | 0.0634            |
| 2k Samples         | 343                                            | 0.0707            |

### So, How Does The Neural Network Do?

The neural network does well. Extremely well. In fact, for any given set of data, over a sample of 100 optimization
pairs (starting from some parameter-space-location A and trying to get to parameter-space-location B only using the model outputs),
the worst neural network (trained on only 2,000 data points) outperforms the optimized result from the closest piece of
data generated by over 200,000 iterations!

![full_problem](/img/paper2/full_problem.png)

Additionally, it blows the genetic algorithm out of the water when it comes to the less sensitive parameters, and is
more parallelizable to boot!

![relative_errors](/img/paper2/relative_errors.png)

One of the most interesting points was the non-relationship between Initial Error and Converged (post-optimization) 
Error. One would think that, all else being equal, an initial error of 100mv would result in an equally good or bad
converged solution. However, that is not the case at all - looking at the vertical dotted line in the above graph,
any point on that line indicates an identical Initial Error. However, the converged error is significantly better
for the suggestions the neural network makes! This was really exciting and demonstrates the power of this
problem formulation.