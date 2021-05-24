import numpy as np

import parameters
import device
import network

# --------------- FF curve ----------------
# Build one to one connections between 250 Poisson spike generators and 
# 250 neurons. Use different input rates and monitor the spikes of 
# the neurons with different input frequencies.

# open DYNAP-SE1 board to get Dynapse1Model
dynapse = device.DynapseDevice()
model = dynapse.model


# use 250 neurons
# 250 spikegens share the same chip id, core id and neuron ids nids with the 250 neurons
schip = 0
score = 0
chip = 0
core = 0
num_neurons = 250
nids = np.arange(1, num_neurons+1)
duration = 2

# set params
parameters.set_all_default_params(model)
# enable AMPA synapse
parameters.set_param(model, parameters.AMPA_WEIGHT, (6,100), chip, core)

# the input rate values
input_freqs = list(np.linspace(0, 200, num_neurons))
# number of connections (weight)
num_conns = np.arange(1, 10, 2)

# result frequency list
output_rates = np.zeros((len(num_conns), len(input_freqs)))

# init a network generator
net = network.DynapseNetworkGenerator()

poisson_gens = dynapse.get_poisson_spikegens(input_freqs, schip, score, nids)
dynapse.monitor_neurons(chip, core, nids)

for i in range(len(num_conns)):
    # remove the existing network in netgen
    net.clear_network()

    spikegens = net.get_spikegens(schip, score, nids)
    neurons = net.get_neurons(chip, core, nids)
    net.add_connections_one_to_one(spikegens, neurons, network.SYNAPSE_AMPA, num_conns[i])

    # make a dynapse1config using the network
    model.apply_configuration(net.get_config())

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

    # Add counter for every neuron spiked during recording
    counter = np.zeros(num_neurons)
    for evt in events:
        # Count the number of spikes per neuron
        counter[evt.id-1] += 1

    output_rates[i] = counter/duration

print(output_rates)
# np.save('./5_output_rates', output_rates)

# close Dynapse1
dynapse.close()