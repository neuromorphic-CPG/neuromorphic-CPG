import numpy as np
from datetime import datetime

import parameters 
import device 
import network
import pickle

# open DYNAP-SE1 board to get Dynapse1Model
dynapse = device.DynapseDevice()
model = dynapse.model

chip = 0
core = 0
num_neurons = 4
nids = np.arange(1,num_neurons+1)

# set params
parameters.set_all_default_params(model)
# parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,255), chip, core)
parameters.set_param(model, parameters.NEURON_DC_INPUT, (0,0), chip, core)
# parameters.set_param(model, parameters.NEURON_DC_INPUT, (0,0), chip, core)
# parameters.set_param(model, parameters.ADAPTATION_GAIN, (7,80), chip, core)
# parameters.set_param(model, parameters.ADAPTATION_TIME_CONSTANT, (1,80), chip, core)
# parameters.set_param(model, parameters.ADAPTATION_WEIGHT, (7,80), chip, core)
# parameters.set_param(model, parameters.ADAPTATION_SOMETHING, (3,80), chip, core)
parameters.set_param(model, parameters.AMPA_WEIGHT, (7,100), chip, core)
# leakage of AMPA
#  parameters.set_param(model, parameters.AMPA_TIME_CONSTANT, (2,80), chip, core)

# init a network generator
net = network.DynapseNetworkGenerator()

# remove the existing network in netgen
net.clear_network()

# only use 1 spikegen No.15, [0,1024)
spikegen_id = 5
# snids = np.arange(1, 8)
# 400 spikes in 2 second 
duration = 2
rate = 800
# rates = np.repeat(rate, 8)
spike_times = np.linspace(0, duration, rate)
# spikegen id list corresponding to spike_times
indices = [spikegen_id]*len(spike_times)

# the chip where the post neurons are
post_chip = 0
target_chips = [post_chip]*len(indices)
isi_base = 900
repeat_mode=False

#spikegens = net.get_spikegens(0, 0, snids)
spikegen = net.get_spikegen(chip, core, spikegen_id)
# get the fpga spike gen from Dynapse1Model
# fpga_gen = dynapse.get_fpga_spikegens_rate(chip, core, snids, rate, duration, repeat_mode)
fpga_gen = dynapse.get_fpga_spikegen(chip, core, spikegen_id, spike_times, repeat_mode)
# # get the fpga spike gen from Dynapse1Model
# fpga_spike_gen = dynapse.get_fpga_spikegen_rate(spikegen, spike_times, indices, target_chips, isi_base, repeat_mode)
# # set up the fpga_spike_gen
# set_fpga_spikegen(fpga_spike_gen, spike_times, indices, target_chips, isi_base, repeat_mode)

neurons = net.get_neurons(chip, core, nids)

# add connections
net.add_connections_one_to_all(spikegen, neurons, network.SYNAPSE_AMPA, 16)

# make a dynapse1config using the network
model.apply_configuration(net.get_config())

# check connections of network 
net.print_network()

# monitor neurons
dynapse.monitor_neurons(chip, core, nids)

# start monitor
dynapse.start_graph()
# start the stimulus
fpga_gen.start()
# run experiment
events = dynapse.run_simulation(duration)
# stop the stimulus
fpga_gen.stop()
# stop graph
dynapse.stop_graph()
# close Dynapse1
dynapse.close()

# save the events
print(len(events),"events.")
with open(f'data/adaptation_property--{datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")}.txt', 'wb') as fp:
    pickle.dump(events, fp)
