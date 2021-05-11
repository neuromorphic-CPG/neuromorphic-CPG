import parameters 
import device 
import network
import pickle
import time
import numpy as np

# open DYNAP-SE1 board to get Dynapse1Model
dynapse = device.DynapseDevice(sender_port=12321, receiver_port=12322)
model = dynapse.model

schip = score = sid = 0
chip = core_e = 0
core_i = 1
ids_e = np.arange(4)
ids_i = np.arange(4,8)

duration = 2

# set params
parameters.set_all_default_params(model)
parameters.set_param(model, parameters.AMPA_WEIGHT, (6,50), chip, core_e)
parameters.set_param(model, parameters.AMPA_WEIGHT, (6,100), chip, core_i)
parameters.set_param(model, parameters.GABA_A_WEIGHT, (6,100), chip, core_e)
parameters.set_param(model, parameters.GABA_A_TIME_CONSTANT, (5,100), chip, core_e)

# init a network generator
net = network.DynapseNetworkGenerator()

dynapse.monitor_neurons(chip, [core_e]*4+[core_i]*4, ids_e+ids_i)

spikegen = net.get_spikegen(schip, score, sid)
neurons_E1 = net.get_neurons(chip, core_e, ids_e)
neurons_I1 = net.get_neurons(chip, core_i, ids_i)

net.add_connections_all_to_all(neurons_E1, neurons_E1, network.SYNAPSE_AMPA)
net.add_connections_all_to_all(neurons_E1, neurons_I1, network.SYNAPSE_AMPA)
net.add_connections_all_to_all(neurons_I1, neurons_E1, network.SYNAPSE_GABA_A)

model.apply_configuration(net.get_config())

net.print_network()

poisson_gen = dynapse.get_poisson_spikegen(20, schip, score, sid)

poisson_gen.start()
time.sleep(0.5)
poisson_gen.stop()
    
# start monitor
dynapse.start_graph()
# run experiment
events = dynapse.run_simulation(duration)
# stop graph
dynapse.stop_graph()
poisson_gen.start()
dynapse.start_graph()
events += dynapse.run_simulation(duration)
dynapse.stop_graph()
# close Dynapse1
dynapse.close()

# save the events
print(len(events),"events.")
with open(f'data/oscillator_CPG.txt', 'wb') as f:
    pickle.dump(events, f)
