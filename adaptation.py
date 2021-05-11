import numpy as np
from datetime import datetime

import parameters 
import Dynapse1Utils as ut
import device 
import network
import pickle
from contextlib import redirect_stdout

# open DYNAP-SE1 board to get Dynapse1Model
dynapse = device.DynapseDevice()
model = dynapse.model

num_neurons = 5
snids = np.arange(1, num_neurons+1)
nids = np.arange(num_neurons+1, 2*num_neurons+1)
duration = 2
chip = 0
core = 0
schip = 0
score = 0

# set params
parameters.set_all_default_params(model)
parameters.set_param(model, parameters.NEURON_DC_INPUT, (3,80), chip, core)
parameters.set_param(model, parameters.ADAPTATION_GAIN, (7,80), chip, core)
parameters.set_param(model, parameters.ADAPTATION_TIME_CONSTANT, (4,80), chip, core)
parameters.set_param(model, parameters.ADAPTATION_WEIGHT, (7,80), chip, core)

# init a network generator
net = network.DynapseNetworkGenerator()

# # only use 1 spikegen No.15, [0,1024)
# spikegen_id = 15
# # 400 spikes in 2 second
# spike_times = np.linspace(0, 2, 400)
# # spikegen id list corresponding to spike_times
# indices = [spikegen_id]*len(spike_times)

# set spike generator
input_freq = 200 # 200 Hz
poisson_gens = dynapse.get_poisson_spikegens(input_freq, schip, score, snids)

# the chip where the post neurons are
# post_chip = 0
# target_chips = [post_chip]*len(indices)
# isi_base = 900
# repeat_mode=False

# get the fpga spike gen from Dynapse1Model
# fpga_spike_gen = model.get_fpga_spike_gen()


# set up neuron population
spikegens = net.get_spikegens(schip, score, snids)
neurons = net.get_neurons(chip, core, nids)

# # set up the fpga_spike_gen
# ut.set_fpga_spike_gen(fpga_spike_gen, spike_times, indices, neurons, isi_base, repeat_mode)

# # add connections
# net.add_connections_one_to_all(fpga_spike_gen, neurons, network.SYNAPSE_AMPA, 1, 1)
net.add_connections_one_to_one(spikegens, neurons, network.SYNAPSE_AMPA, 1)

# monitor network
all_nids = np.concatenate((snids, nids), axis= 0)
dynapse.monitor_neurons(chip, core, all_nids)

# remove the existing network in netgen
net.clear_network()

# make a dynapse1config using the network
model.apply_configuration(net.get_config())

# check connections of network 
net.print_network()
    
# start monitor
dynapse.start_graph()
# start the stimulus
# fpga_spike_gen.start()
poisson_gens.start()
# run experiment
events = dynapse.run_simulation(duration)
# stop the stimulus
# fpga_spike_gen.stop()
poisson_gens.start()
# stop graph
dynapse.stop_graph()
# close Dynapse1
dynapse.close()

# save the events
print(len(events),"events.")
with open(f'data/adaptive_CPG--{datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")}.txt', 'wb') as fp:
    pickle.dump(events, fp)
