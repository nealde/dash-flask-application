title: Making Small Neural Networks Faster with Numpy
date: 2019-11-01
descr: Using Numpy to speed up small neural networks for deployment
tags: [deeplearning, cython, neuralnetworks]

### Motivation

Neural networks are super powerful learners, but the libraries can be too large for edge devices or too slow for
iterative calls in Python.  To address this issue, we will just have to solve the math ourselves!

To start with, we will create a small nonsense data set using numpy.

```python
import numpy as np

# make training data
_x = np.random.randn(5000, 25)
_y = np.random.randn(5000, 1)
print(_x.shape, _y.shape)
```

Then, we will scale these results to what the neural network expects - inputs and outputs between [0, 1].

```python
from sklearn.preprocessing import MinMaxScaler

mmsx = MinMaxScaler(feature_range=(0, 1), copy=True)
mmsy = MinMaxScaler(feature_range=(0, 1), copy=True)
x = mmsx.fit_transform(_x)
y = mmsy.fit_transform(_y)
```

#### Train the neural network

Next, we will make and train our neural network.

```python
import keras
from keras.models import Sequential
from keras.layers import Dense

input_shape = (x.shape[1],)
batch_size=256

model = Sequential()
model.add(Dense(30, input_shape = input_shape, activation='elu', trainable=True))
model.add(Dense(30, activation='elu', trainable=True))
model.add(Dense(y.shape[1],activation='linear'))
print(model.summary())
model.compile(loss='mse',
              optimizer='adam',
              metrics=['mse'])
model.fit(x, y, epochs=500, verbose=2, validation_split=0.8, batch_size=batch_size)
```

Now that the network is trained, we can look at performance.  Using Jupyter's *%timeit* notebook magic,
we can get reliable performance metrics on any function we call.

```python
to_predict = x[:1, :]

%timeit pred = model.predict(to_predict)

# 266 µs ± 3.48 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
```

That's not bad! But what if we needed to call this model 1000 times sequentially to make a prediction? Or if this
was just one small part of a model, and we had to call a handful of these?  That may not be fast enough.

#### Implementing neural networks in Numpy

First, we need to extract the weights and biases. Luckily, keras makes this really easy. Since our
activation function was *elu*, we will need to implement that too.

```python
def extract_weights(sequential_model):
    weights=[]
    for layer in sequential_model.layers:
        weights.append(layer.get_weights())
    # weights is a list of (weights: np.array, biases: np.array)
    return weights


def np_elu(x):
    mask = np.where(x<0)
    x[mask] = np.exp(x[mask])-1
    return x


def model_np(input1, weights):
    temp = input1.copy()
    for weight, bias in weights:
        temp = np.dot(temp, weight)+bias
        temp = np_elu(temp)
    return temp

```

Now that we have a function, we can easily time it again using the Jupyter magic:

```python
weights = extract_weights(m1)
%timeit pred = model_np(to_predict, weights)

# 41.7 µs ± 500 ns per loop (mean ± std. dev. of 7 runs, 10000 loops each)
```

So for low price of a list of arrays and a simple function, we net ourselves a 5x speedup!

Looking at the scaling for this method, we can see that it's really only viable for neural networks with
less than ~1M parameters. But, if you have have a package conflict, or want to avoid needing Tensorflow
in a deployment scenario, and need Numpy anyway, this is an occasionally-useful tool to have in your tool belt.

| NN Shape            | Num Params  | Keras Time (1 predictions) | Numpy Time (1 prediction) | Numpy Speedup | Keras Time (100 concurrent predictions) | Numpy Time (100 concurrent predictions) | Numpy Speedup |
|---------------------|-------------|----------------------------|---------------------------|---------------|-----------------------------------------|-----------------------------------------|---------------|
| (30,30,30)          | 2,671       | 0.286 ms                   | 0.0565 ms                 | 5.06x         | 0.907 ms                                | 0.273 ms                                | 3.32x         |
| (100,100,100)       | 22,901      | 0.292 ms                   | 0.0757 ms                 | 3.85x         | 1.12 ms                                 | 0.816 ms                                | 1.37x         |
| (1000,1000,1000)    | 2,029,001   | 0.833 ms                   | 5.19 ms                   | 0.16x         | 9.1 ms                                  | 15.5 ms                                 | 0.59x         |
| (10000,10000,10000) | 200,290,001 | 28.1 ms                    | 513 ms                    | 0.05x         | 186 ms                                  | 900 ms                                  | 0.21x         |