
import math
import random

class Neuron:
    """Represents a single neuron."""

    def __init__(self, num_inputs):
        """Initializes the neuron with random weights and bias."""
        self.weights = [random.uniform(-1, 1) for _ in range(num_inputs)]
        self.bias = random.uniform(-1, 1)
        self.output = 0
        self.delta = 0

    def activate(self, inputs):
        """Activate neuron with inputs."""
        if len(inputs) != len(self.weights):
            raise ValueError("Number of inputs must match number of weights.")
        weighted_sum = sum(w * x for w, x in zip(self.weights, inputs)) + self.bias
        self.output = self._sigmoid(weighted_sum)
        return self.output

    def _sigmoid(self, x):
        """Sigmoid activation function."""
        return 1 / (1 + math.exp(-x))

    @staticmethod
    def _sigmoid_derivative(x):
        """Derivative of sigmoid function."""
        s = Neuron._sigmoid(x)
        return s * (1 - s)


class Layer:
    """Represents a layer of neurons."""

    def __init__(self, num_neurons, num_inputs):
        """Initializes the layer with neurons."""
        self.neurons = [Neuron(num_inputs) for _ in range(num_neurons)]

    def forward(self, inputs):
        """Forward propagation through the layer."""
        outputs = [neuron.activate(inputs) for neuron in self.neurons]
        return outputs

    def get_outputs(self):
        """Get outputs of all neurons."""
        return [neuron.output for neuron in self.neurons]


class NeuralNetwork:
    """Multi-layer neural network."""

    def __init__(self, layer_sizes):
        """Initializes the network with layers."""
        if len(layer_sizes) < 2:
            self.layers = []
        else:
            self.layers = []
            for i in range(1, len(layer_sizes)):
                self.layers.append(Layer(layer_sizes[i], layer_sizes[i - 1]))

    def forward(self, inputs):
        """Forward propagation through entire network."""
        current_inputs = inputs
        for layer in self.layers:
            current_inputs = layer.forward(current_inputs)
        return current_inputs

    def backward(self, inputs, targets, learning_rate=0.1):
        """Backward propagation and weight update."""
        outputs = self.forward(inputs)
        for i, neuron in enumerate(self.layers[-1].neurons):
            error = targets[i] - outputs[i]
            neuron.delta = error * Neuron._sigmoid_derivative(neuron.output)

        for layer_idx in range(len(self.layers) - 2, -1, -1):
            layer = self.layers[layer_idx]
            next_layer = self.layers[layer_idx + 1]
            for i, neuron in enumerate(layer.neurons):
                error = sum(n.delta * n.weights[i] for n in next_layer.neurons)
                neuron.delta = error * Neuron._sigmoid_derivative(neuron.output)

        prev_outputs = inputs
        for layer in self.layers:
            for neuron in layer.neurons:
                for i in range(len(neuron.weights)):
                    neuron.weights[i] += learning_rate * neuron.delta * prev_outputs[i]
                neuron.bias += learning_rate * neuron.delta
            prev_outputs = layer.get_outputs()

    def train(self, training_data, epochs=1000, learning_rate=0.1):
        """Train the network."""
        for epoch in range(epochs):
            total_error = 0
            for inputs, targets in training_data:
                outputs = self.forward(inputs)
                error = sum((t - o) ** 2 for t, o in zip(targets, outputs))
                total_error += error
                self.backward(inputs, targets, learning_rate)

            if epoch % 100 == 0:
                print(f'Epoch {epoch}, Error: {total_error:.4f}')

    def predict(self, inputs):
        """Make a prediction."""
        return self.forward(inputs)


if __name__ == '__main__':
    network = NeuralNetwork([2, 4, 1])
    training_data = [([0, 0], [0]), ([0, 1], [1]), ([1, 0], [1]), ([1, 1], [0])]
    network.train(training_data, epochs=1000, learning_rate=0.5)

    print('\nPredictions:')
    for inputs, _ in training_data:
        prediction = network.predict(inputs)
        print(f'Input: {inputs}, Output: {prediction[0]:.4f}')
