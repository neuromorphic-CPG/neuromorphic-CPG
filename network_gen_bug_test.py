import samna.dynapse1 as dyn1
import NetworkGenerator as n
from NetworkGenerator import Neuron

net_gen = n.NetworkGenerator()

neuron1 = Neuron(0, 0, 1)
neuron2 = Neuron(0, 0, 2)
neuron3 = Neuron(0, 0, 3)

net_gen.add_connection(neuron1, neuron2, dyn1.Dynapse1SynType.AMPA)
net_gen.add_connection(neuron1, neuron3, dyn1.Dynapse1SynType.AMPA)
net_gen.add_connection(neuron1, neuron3, dyn1.Dynapse1SynType.AMPA)

net_gen.print_network()

new_config = net_gen.make_dynapse1_configuration()
# throws ERROR: 
# aliasing pre neurons exist! Post neurons C0c0n1 and C0c0n2 have different 
# pre neurons in different chips but with same (core_id, neuron_id, synapse_type) (0, 0, Dynapse1SynType.AMPA).