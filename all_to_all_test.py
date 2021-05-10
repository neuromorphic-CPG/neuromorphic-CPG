import samna.dynapse1 as dyn1
import NetworkGenerator as n
from NetworkGenerator import Neuron

net_gen = n.NetworkGenerator()

neuron1 = Neuron(0, 0, 0)
neuron2 = Neuron(0, 0, 1)
neuron3 = Neuron(0, 0, 2)

net_gen.add_connection(neuron1, neuron3, dyn1.Dynapse1SynType.AMPA)
net_gen.add_connection(neuron2, neuron3, dyn1.Dynapse1SynType.AMPA)

net_gen.print_network()

# outputs
# C0c0n2: [('C0c0n1', 'AMPA')]
# seems to just be a bug in the code for printing the network
# move `incoming_connections_list = []` and `incoming_connections_str_list = []`
# outside the `for pre_tag in incoming_connections_dict:` loop in NetworkGenerator.py:convert_incoming_conns_dict2list()
# then it correctly outputs
# C0c0n2: [('C0c0n0', 'AMPA'), ('C0c0n1', 'AMPA')]