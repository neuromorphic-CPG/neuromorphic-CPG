import numpy as np

import parameters
import device
import network

# --------------- FF curve ----------------
# Connect a Poisson spike generator to a neuron
# Monitor the spikes of this neuron with different input frequencies
# given different AMPA weight parameters

# open DYNAP-SE1 board to get Dynapse1Model
dynapse = device.DynapseDevice()
model = dynapse.model

# set params
parameters.set_all_default_params(model)

# weight fine value list, given coarse value = 7
fine_values = np.hstack((np.arange(0, 50, 10), np.arange(50, 300, 100)))
coarse_value = 7
# the input rate values
input_freqs = np.arange(0, 200, 20)
# result frequency list
freqs = np.zeros((len(fine_values), len(input_freqs)))
# duration per input rate per weight
duration = 1

# init a network generator
net = network.DynapseNetworkGenerator()
# select a spike generator
schip = 0
score = 0
sid = 1
spikegen = net.get_spikegen(schip, score, sid)
# select a neuron
chip = 0
core = 1
nid = 16
neuron = net.get_neuron(chip, core, nid)
# connect spikegen to neuron (only in the network topology not chips for now)
net.add_connection(spikegen, neuron, network.SYNAPSE_AMPA)

# print the network so you can double check (optional)
net.print_network()

# apply the configuration
model.apply_configuration(net.get_config())

poisson_gen = dynapse.get_poisson_spikegen(input_freqs[0], schip, score, sid)
dynapse.monitor_neuron(chip, core, nid)
dynapse.start_graph()

# ----------- get events with different input rates different weight -----------
for i in range(len(fine_values)):
	# set new weight
	ampa_weight = parameters.set_param(model, parameters.AMPA_WEIGHT, (coarse_value,fine_values[i]), chip, core)

	for j in range(len(input_freqs)):
		poisson_gen.set_rate(input_freqs[j])

		# start poisson_gen
		poisson_gen.start()

		# get events
		events = dynapse.run_simulation(duration)

		# stop poisson_gen
		poisson_gen.stop()
		####################### TODO #######################

		# append the frequency to the list
		freq = len(events)/duration
		freqs[i][j] = freq

	print(f'AMPA weight=({coarse_value},{fine_values[i]})={ampa_weight}\n{list(freqs[i])}')

dynapse.stop_graph()
dynapse.close()