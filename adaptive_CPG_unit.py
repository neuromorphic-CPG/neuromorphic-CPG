import numpy as np
from datetime import datetime

import parameters 
import device 
import network
import pickle
from contextlib import redirect_stdout

# open DYNAP-SE1 board to get Dynapse1Model
dynapse = device.DynapseDevice()
model = dynapse.model

# use 8 neurons per excitatory population
schip = 0
score = 0
chip = 0
core = 0
# fixme num_neurons = 8
num_neurons = 15
# snids = np.arange(1, num_neurons+1)
nids1 = np.arange(num_neurons+1, 2*num_neurons+1)
nids2 = np.arange(2*num_neurons+1, 3*num_neurons+1)
# all_nids = np.concatenate((nids1, nids2, snids), axis = 0)
all_nids = np.concatenate((nids1, nids2), axis = 0)

# nids = np.arange(1, num_neurons+1)
duration = 10

# set params
parameters.set_all_default_params(model)
parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,255), chip, core)
# parameters.set_param(model, parameters.NEURON_DC_INPUT, (2,40), chip, core)
parameters.set_param(model, parameters.NEURON_DC_INPUT, (2,20), chip, core)
parameters.set_param(model, parameters.ADAPTATION_GAIN, (7,80), chip, core)
parameters.set_param(model, parameters.ADAPTATION_TIME_CONSTANT, (1,80), chip, core)
parameters.set_param(model, parameters.ADAPTATION_WEIGHT, (7,80), chip, core)
# parameters.set_param(model, parameters.ADAPTATION_SOMETHING (3,80), chip, core)

# init a network generator
net = network.DynapseNetworkGenerator()

# input frequency
# fixme input freq 200
# input_freq = 200 # 200 Hz
# poisson_gens = dynapse.get_poisson_spikegens(input_freq, schip, score, snids)
# poisson_gens = dynapse.get_poisson_spikegens(input_freq, schip, score, snids)
dynapse.monitor_neurons(chip, core, all_nids)

# remove the existing network in netgen
net.clear_network()

# spikegens = net.get_spikegens(schip, score, snids)
neurons_E1 = net.get_neurons(chip, core, nids1)
neurons_E2 = net.get_neurons(chip, core, nids2)
# neuron 14 keeps spiking for some reason while the others aren't


# net.add_connections_all_to_all(spikegen, neurons_E1, network.SYNAPSE_AMPA, 8, 0.5)

# # net.add_connections_one_to_one()
# # connections within neuron group 1 with 0.5 probability
# # fixme: weight 10-15
# net.add_connections_all_to_all(neurons_E1, neurons_E1, network.SYNAPSE_AMPA, 8, 0.5)
# # connections within neuron group 2 with 0.5 probability
# net.add_connections_all_to_all(neurons_E2, neurons_E2, network.SYNAPSE_AMPA, 8, 0.5)
# # inhibitory connections between excitatory neuron groups with probability 0.5 
# net.add_connections_all_to_all(neurons_E1, neurons_E2, network.SYNAPSE_GABA_B, 5, 0.5)

# In the mean time we just need to set connections with p=1 I guess...
# net.add_connections_all_to_all(spikegens, neurons_E1, network.SYNAPSE_AMPA, 2, 1)
net.add_connections_all_to_all(neurons_E1, neurons_E1, network.SYNAPSE_AMPA, 1, 1)
net.add_connections_all_to_all(neurons_E2, neurons_E2, network.SYNAPSE_AMPA, 1, 1)
net.add_connections_all_to_all(neurons_E1, neurons_E2, network.SYNAPSE_GABA_B, 2, 1)
net.add_connections_all_to_all(neurons_E2, neurons_E1, network.SYNAPSE_GABA_B, 2, 1)

 # make a dynapse1config using the network
model.apply_configuration(net.get_config())

# print the network so you can double check (optional)
# with open(f'data/network_adaptive_CPG--{datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")}.txt', 'w') as f:
#     with redirect_stdout(f):
#         print(net.print_network())

# net.print_network()
    
# start monitor
dynapse.start_graph()
# start the stimulus
#poisson_gens.start()
# run experiment
events = dynapse.run_simulation(duration)
# stop the stimulus
#poisson_gens.stop()
# stop graph
dynapse.stop_graph()
# close Dynapse1
dynapse.close()

# save the events
print(len(events),"events.")
with open(f'data/adaptive_CPG--{datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")}.txt', 'wb') as fp:
    pickle.dump(events, fp)
