import numpy as np
from datetime import datetime

import parameters 
import device 
import network
import pickle

save_events = []

# open DYNAP-SE1 board to get Dynapse1Model
dynapse = device.DynapseDevice()
model = dynapse.model

# use 8 neurons per excitatory population
schip = 0
score = 0
chip = 0
core = 0
# fixme num_neurons = 8
num_neurons = 8
nids1 = np.arange(1, num_neurons+1)
nids2 = np.arange(num_neurons+1, 2*num_neurons+1)
snid = 2*num_neurons+1
nids = np.arange(1, 2*num_neurons+2)

# nids = np.arange(1, num_neurons+1)
duration = 2

# set params
parameters.set_all_default_params(model)
# parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,80), chip, core)
parameters.set_param(model, parameters.NEURON_DC_INPUT, (2,80), chip, core)

# init a network generator
net = network.DynapseNetworkGenerator()

# input frequency
# fixme input freq 200
input_freq = 50 # 200 Hz
poisson_gens = dynapse.get_poisson_spikegen(input_freq, schip, score, snid)
dynapse.monitor_neurons(chip, core, nids)

# remove the existing network in netgen
net.clear_network()

spikegen = net.get_spikegen(schip, score, snid)
neurons_E1 = net.get_neurons(chip, core, nids1)
neurons_E2 = net.get_neurons(chip, core, nids2)


# net.add_connections_one_to_all(spikegen, neurons_E1, network.SYNAPSE_AMPA, 8, 0.5)

# # net.add_connections_one_to_one()
# # connections within neuron group 1 with 0.5 probability
# # fixme: weight 10-15
# net.add_connections_all_to_all(neurons_E1, neurons_E1, network.SYNAPSE_AMPA, 8, 0.5)
# # connections within neuron group 2 with 0.5 probability
# net.add_connections_all_to_all(neurons_E2, neurons_E2, network.SYNAPSE_AMPA, 8, 0.5)
# # inhibitory connections between excitatory neuron groups with probability 0.5 
# net.add_connections_all_to_all(neurons_E1, neurons_E2, network.SYNAPSE_GABA_B, 5, 0.5)

# In the mean time we just need to set connections with p=1 I guess...
net.add_connections_one_to_all(spikegen, neurons_E1, network.SYNAPSE_AMPA, 10, 1)
#net.add_connections_all_to_all(neurons_E1, neurons_E1, network.SYNAPSE_AMPA, 4, 1)
#net.add_connections_all_to_all(neurons_E2, neurons_E2, network.SYNAPSE_AMPA, 4, 1)
# fixme there might be a bug in all-to-all connections
net.add_connections_one_to_one(neurons_E1, neurons_E2, network.SYNAPSE_AMPA, 4)

 # make a dynapse1config using the network
model.apply_configuration(net.get_config())

# print the network so you can double check (optional)
net.print_network()
    
# start monitor
dynapse.start_graph()
# start the stimulus
poisson_gens.start()
# run experiment
events = dynapse.run_simulation(duration)
# stop the stimulus
poisson_gens.stop()
# stop graph
dynapse.stop_graph()
# close Dynapse1
dynapse.close()

# save the events
print(len(events),"events.")
with open(f'data/adaptive_CPG--{datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")}.txt', 'wb') as fp:
    pickle.dump(events, fp)
