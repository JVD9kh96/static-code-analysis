"""Tests for genCodes.code_19 (Neuron, Layer, NeuralNetwork)."""
import pytest
from genCodes import code_19


def test_neuron_activate():
    import random
    random.seed(42)
    neuron = code_19.Neuron(3)
    output = neuron.activate([1.0, 0.5, 0.0])
    assert 0 <= output <= 1


def test_neuron_wrong_input_length():
    import random
    random.seed(42)
    neuron = code_19.Neuron(2)
    with pytest.raises(ValueError, match="Number of inputs"):
        neuron.activate([1.0, 2.0, 3.0])


def test_layer_forward():
    import random
    random.seed(42)
    layer = code_19.Layer(4, 2)
    outputs = layer.forward([0.5, 0.5])
    assert len(outputs) == 4
    assert all(0 <= o <= 1 for o in outputs)


def test_neural_network_forward():
    import random
    random.seed(42)
    net = code_19.NeuralNetwork([2, 3, 1])
    out = net.forward([1.0, 0.0])
    assert len(out) == 1
    assert 0 <= out[0] <= 1


def test_neural_network_predict():
    import random
    random.seed(42)
    net = code_19.NeuralNetwork([2, 2, 1])
    pred = net.predict([0.0, 1.0])
    assert len(pred) == 1
