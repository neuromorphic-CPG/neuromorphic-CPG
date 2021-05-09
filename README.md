# Neuromorphic Intelligence CPG project

## Hardware Notes

Onchip connections from left chips (i.e. 0,2) to right chips (i.e. 1,3) will make chips die. NetworkGenerator.py:53

Having a different number of connections from the same neuron to 2 different neurons will cause the network verification to fail. Eg. n0 -> n1 (2 times) and n0 -> n2 (3 times). Unclear if this is a limitation of the chip, or a bug with the network generator code. NetworkGenerator.py:303