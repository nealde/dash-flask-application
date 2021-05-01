title: Publication - Data Science for Electrochemical Engineers
date: 2016-11-10
descr: Data Science for Electrochemcial Engineers
tags: [data-science, electrochemistry, ECS]

### What is Data Science?  An Introduction For and By Chemical Engineers
*By: Neal Dawson-Elli, Seong Beom Lee, Manan Pathak, Kishalay Mitra, and Venkat R. Subramanian*

The paper can be found [here](https://iopscience.iop.org/article/10.1149/2.1391714jes/meta)

This article refers to a recently published open access paper in the Journal of the Electrochemical Society, 
“Data Science Approaches for Electrochemical Engineers: An Introduction through Surrogate Model Development 
for Lithium-Ion Batteries”.  Data science is often hailed as the fourth paradigm of science.  As the computing power
 available to researchers increases, data science techniques become more and more relevant to a larger 
 group of scientists. A quick literature search for electrochemistry and data science will reveal a startling 
 lack of analysis done on the data science side.  This paper is an attempt to help introduce the topics of 
 data science to electrochemists, as well as to analyze the power of these methods when combined with physics based models.

 ![image_1](/img/paper1/paper1_img.png)

At the core of the paper is the idea that one cannot be successful treating every problem as a black box and 
applying liberal use of data science – in other words, despite its growing popularity, it is not a panacea.  The image 
shows the basic workflow for using data science techniques – the creation of a dataset, splitting into training-test 
pairs, training a model, and then evaluating the model on some task. In this case, the training data comes from many 
simulations of the pseudo two-dimensional lithium ion battery model.  However, in order to get the best results, one 
cannot simply pair the inputs and outputs and train a machine learning model on it.  The inputs, or features, must 
be engineered to better highlight changes in your output data, and sometimes the problem needs to be totally 
restructured in order to be successful.  In this paper, the most successful approach is the recurrent approach, 
which splits the simulated discharge curves into 5-minute chunks and allows the algorithm to estimate the 
voltage one minute from the current time using the previous few voltages, resulting in an average error below
0.5%.  However, in order to more accurately predict the state of charge, or amount of energy remaining in the 
battery, the problem must be restructured again.  The main take-away from the paper is that in order to get the
best result from a machine learning model, one must take some time to understand the system and think about
non-obvious formulations.
