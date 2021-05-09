import numpy as np

import parameters 
import device 
import network

# open DYNAP-SE1 board to get Dynapse1Model
dynapse = device.DynapseDevice()
model = dynapse.model

chip = 0
core = 0
duration = 2

# set params
parameters.set_all_default_params(model)
parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,80), chip, core)

# init a network generator
net = network.DynapseNetworkGenerator()

neurons = net.get_neurons(chip, core, np.arange(3))

net.add_connection(neurons[0],neurons[1], network.SYNAPSE_AMPA, 1)
net.add_connection(neurons[0],neurons[2], network.SYNAPSE_AMPA, 2)

 # make a dynapse1config using the network
model.apply_configuration(net.get_config())

# start monitor
dynapse.start_graph()
# run experiment
events = dynapse.run_simulation(duration)
# stop graph
dynapse.stop_graph()


# close Dynapse1
dynapse.close()
