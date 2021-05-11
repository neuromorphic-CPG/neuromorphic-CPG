import numpy as np
from datetime import datetime

import parameters 
import device 
import network
import pickle

# open DYNAP-SE1 board to get Dynapse1Model
dynapse = device.DynapseDevice()
model = dynapse.model

duration = 2
chip = 0
core = 0
nids = np.arange(1,15)
all_nids = np.arange(1,16)

# set params
parameters.set_all_default_params(model)
parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,80), chip, core)
parameters.set_param(model, parameters.NEURON_DC_INPUT, (3,80), chip, core)
parameters.set_param(model, parameters.ADAPTATION_GAIN, (7,80), chip, core)
parameters.set_param(model, parameters.ADAPTATION_TIME_CONSTANT, (7,80), chip, core)
parameters.set_param(model, parameters.ADAPTATION_WEIGHT, (7,80), chip, core)

# init a network generator
net = network.DynapseNetworkGenerator()

# remove the existing network in netgen
net.clear_network()

# only use 1 spikegen No.15, [0,1024)
spikegen_id = 15

spikegen = net.get_spikegen(chip, core, spikegen_id)
neurons = net.get_neurons(chip, core, nids)

# add connections
net.add_connections_one_to_all(spikegen, neurons, network.SYNAPSE_AMPA, 2)

# make a dynapse1config using the network
model.apply_configuration(net.get_config())

# check connections of network 
net.print_network()

# get the fpga spike gen from Dynapse1Model
fpga_spike_gen = dynapse.get_fpga_spikegen_rate(chip, core, spikegen_id, 200, duration) # 400 spikes in 2 second

# monitor neurons
dynapse.monitor_neuron_network(neurons + [spikegen])

# start monitor
dynapse.start_graph()
# start the stimulus
fpga_spike_gen.start()
# run experiment
events = dynapse.run_simulation(duration)
# stop the stimulus
fpga_spike_gen.stop()
# stop graph
dynapse.stop_graph()
# close Dynapse1
dynapse.close()

# save the events
print(len(events),"events.")
with open(f'data/adaptation_property--{datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")}.txt', 'wb') as fp:
    pickle.dump(events, fp)
