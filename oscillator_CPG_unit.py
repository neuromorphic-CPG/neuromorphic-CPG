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

duration = 2

# set params
parameters.set_all_default_params(model)
parameters.set_param(model, parameters.NEURON_LEAKAGE_1, (4,80), chip, core_e)
parameters.set_param(model, parameters.NEURON_LEAKAGE_1, (4,5), chip, core_i)
parameters.set_param(model, parameters.AMPA_WEIGHT, (6,25), chip, core_e)
parameters.set_param(model, parameters.AMPA_WEIGHT, (6,10), chip, core_i)
parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,50), chip, core_e)
parameters.set_param(model, parameters.GABA_B_LEAKAGE, (4,20), chip, core_e)
parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,50), chip, core_i)

# init a network generator
net = network.DynapseNetworkGenerator()

spikegen = net.get_spikegen(schip, score, sid)
neurons_E1 = net.get_neurons(chip, core_e, np.arange(4))
neurons_I1 = net.get_neurons(chip, core_i, np.arange(4))
neurons_E2 = net.get_neurons(chip, core_e, np.arange(4,8))
neurons_I2 = net.get_neurons(chip, core_i, np.arange(4,8))

net.add_connections_one_to_all(spikegen, neurons_E1, network.SYNAPSE_AMPA)
net.add_connections_one_to_all(spikegen, neurons_E2, network.SYNAPSE_AMPA)
net.add_connections_all_to_all(neurons_E1, neurons_E1, network.SYNAPSE_AMPA)
net.add_connections_all_to_all(neurons_E2, neurons_E2, network.SYNAPSE_AMPA)
net.add_connections_all_to_all(neurons_E1, neurons_I1, network.SYNAPSE_AMPA)
net.add_connections_all_to_all(neurons_E2, neurons_I2, network.SYNAPSE_AMPA)
net.add_connections_all_to_all(neurons_I1, neurons_E1, network.SYNAPSE_GABA_B)
net.add_connections_all_to_all(neurons_I2, neurons_E2, network.SYNAPSE_GABA_B)
# coupling
net.add_connections_all_to_all(neurons_E1, neurons_E2, network.SYNAPSE_AMPA)
net.add_connections_all_to_all(neurons_E2, neurons_E1, network.SYNAPSE_AMPA)
net.add_connections_all_to_all(neurons_I1, neurons_I2, network.SYNAPSE_GABA_B)
net.add_connections_all_to_all(neurons_I2, neurons_I1, network.SYNAPSE_GABA_B)


dynapse.monitor_neuron_network(neurons_E1 + neurons_E2 + neurons_I1 + neurons_I2)

model.apply_configuration(net.get_config())

poisson_gen = dynapse.get_poisson_spikegen(10, schip, score, sid)

# pulse spikegen
poisson_gen.start()
# time.sleep(0.5)
# poisson_gen.stop()

# start monitor
dynapse.start_graph()

events = dynapse.run_simulation(duration)
if len(events) > 0:
    print(f'new event list: start - {events[0].timestamp//1000} ms, end - {events[-1].timestamp//1000} ms.')

# parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,100), chip, core_e)
# parameters.set_param(model, parameters.AMPA_WEIGHT, (6,5), chip, core_i)
# parameters.set_param(model, parameters.NEURON_LEAKAGE_1, (4,20), chip, core_i)
# parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,20), chip, core_i)
parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,100), chip, core_e)

new_events = dynapse.run_simulation(duration)
if len(new_events) > 0:
    print(f'new event list: start - {new_events[0].timestamp//1000} ms, end - {new_events[-1].timestamp//1000} ms.')
events += new_events

# parameters.set_param(model, parameters.GABA_B_WEIGHT, (0,0), chip, core_i)
parameters.set_param(model, parameters.GABA_B_WEIGHT, (4,200), chip, core_e)

new_events = dynapse.run_simulation(duration)
if len(new_events) > 0:
    print(f'new event list: start - {new_events[0].timestamp//1000} ms, end - {new_events[-1].timestamp//1000} ms.')
events += new_events

dynapse.stop_graph()
# close Dynapse1
dynapse.close()

# save the events
print(len(events),"events.")
with open(f'data/oscillator_CPG.txt', 'wb') as f:
    pickle.dump(events, f)
