import samna
import samna.dynapse1 as dyn1
import time

import sys
# change the path to '/home/class_NI2021/ctxctl_contrib' on zemo
sys.path.insert(1, '/home/class_NI2021/ctxctl_contrib')
from Dynapse1Constants import *
import Dynapse1Utils as ut
import NetworkGenerator as n
from NetworkGenerator import Neuron
import numpy as np

def gen_param_group_1core():
    paramGroup = dyn1.Dynapse1ParameterGroup()
    # THR, gain factor of neurons
    paramGroup.param_map["IF_THR_N"].coarse_value = 5
    paramGroup.param_map["IF_THR_N"].fine_value = 80

    # refactory period of neurons
    paramGroup.param_map["IF_RFR_N"].coarse_value = 4
    paramGroup.param_map["IF_RFR_N"].fine_value = 128

    # leakage of neurons
    paramGroup.param_map["IF_TAU1_N"].coarse_value = 4
    paramGroup.param_map["IF_TAU1_N"].fine_value = 80

    # turn off tau2
    paramGroup.param_map["IF_TAU2_N"].coarse_value = 7
    paramGroup.param_map["IF_TAU2_N"].fine_value = 255

    # turn off DC
    paramGroup.param_map["IF_DC_P"].coarse_value = 0
    paramGroup.param_map["IF_DC_P"].fine_value = 0

    # leakage of AMPA
    paramGroup.param_map["NPDPIE_TAU_F_P"].coarse_value = 4
    paramGroup.param_map["NPDPIE_TAU_F_P"].fine_value = 80

    # gain of AMPA
    paramGroup.param_map["NPDPIE_THR_F_P"].coarse_value = 4
    paramGroup.param_map["NPDPIE_THR_F_P"].fine_value = 80

    # weight of AMPA
    paramGroup.param_map["PS_WEIGHT_EXC_F_N"].coarse_value = 7
    paramGroup.param_map["PS_WEIGHT_EXC_F_N"].fine_value = 100

    # leakage of NMDA
    paramGroup.param_map["NPDPIE_TAU_S_P"].coarse_value = 4
    paramGroup.param_map["NPDPIE_TAU_S_P"].fine_value = 80

    # gain of NMDA
    paramGroup.param_map["NPDPIE_THR_S_P"].coarse_value = 4
    paramGroup.param_map["NPDPIE_THR_S_P"].fine_value = 80

    # weight of NMDA
    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_EXC_S_N"].fine_value = 0

    # leakage of GABA_A (shunting)
    paramGroup.param_map["NPDPII_TAU_F_P"].coarse_value = 4
    paramGroup.param_map["NPDPII_TAU_F_P"].fine_value = 80

    # gain of GABA_A (shunting)
    paramGroup.param_map["NPDPII_THR_F_P"].coarse_value = 4
    paramGroup.param_map["NPDPII_THR_F_P"].fine_value = 80

    # weight of GABA_A (shunting)
    paramGroup.param_map["PS_WEIGHT_INH_F_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_INH_F_N"].fine_value = 0

    # leakage of GABA_B
    paramGroup.param_map["NPDPII_TAU_S_P"].coarse_value = 4
    paramGroup.param_map["NPDPII_TAU_S_P"].fine_value = 80

    # gain of GABA_B
    paramGroup.param_map["NPDPII_THR_S_P"].coarse_value = 4
    paramGroup.param_map["NPDPII_THR_S_P"].fine_value = 80

    # weight of GABA_B
    paramGroup.param_map["PS_WEIGHT_INH_S_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_INH_S_N"].fine_value = 0

    # other advanced parameters
    paramGroup.param_map["IF_NMDA_N"].coarse_value = 0
    paramGroup.param_map["IF_NMDA_N"].fine_value = 0

    paramGroup.param_map["IF_AHTAU_N"].coarse_value = 4
    paramGroup.param_map["IF_AHTAU_N"].fine_value = 80

    paramGroup.param_map["IF_AHTHR_N"].coarse_value = 0
    paramGroup.param_map["IF_AHTHR_N"].fine_value = 0

    paramGroup.param_map["IF_AHW_P"].coarse_value = 0
    paramGroup.param_map["IF_AHW_P"].fine_value = 0

    paramGroup.param_map["IF_CASC_N"].coarse_value = 0
    paramGroup.param_map["IF_CASC_N"].fine_value = 0

    paramGroup.param_map["PULSE_PWLK_P"].coarse_value = 4
    paramGroup.param_map["PULSE_PWLK_P"].fine_value = 106

    paramGroup.param_map["R2R_P"].coarse_value = 3
    paramGroup.param_map["R2R_P"].fine_value = 85

    paramGroup.param_map["IF_BUF_P"].coarse_value = 3
    paramGroup.param_map["IF_BUF_P"].fine_value = 80

    return paramGroup

device_name = "my_dynapse1"
store = ut.open_dynapse1(device_name, gui=False, sender_port=12345, receiver_port=12346)
model = getattr(store, device_name)

paramGroup = gen_param_group_1core()
for chip in range(4):
    for core in range(4):
        model.update_parameter_group(paramGroup, chip, core)

duration = 1

# ------------------- build network -------------------
net_gen = n.NetworkGenerator()

# select a neuron
chip = 0
core = 0
nid = 1
neuron = Neuron(chip, core, nid)

new_config = net_gen.make_dynapse1_configuration()
model.apply_configuration(new_config)

param = dyn1.Dynapse1Parameter("IF_DC_P", 1, 200)
model.update_single_parameter(param, chip, core)

monitored_global_nid = ut.get_global_id(chip, core, nid)
graph, filter_node, sink_node = ut.create_neuron_select_graph(model, [monitored_global_nid])

#############################
# Run test
#############################

# 1.
# let some spikes accumulate in the buffer
time.sleep(2)
# immediately clear buffer, sleep, check buffer
graph.start()
sink_node.get_buf()
time.sleep(duration)
events1 = sink_node.get_buf()
graph.stop()

# 2.
# let some spikes accumulate in the buffer
time.sleep(2)
# sleep after starting graph, clear buffer, sleep, check buffer
graph.start()
time.sleep(0.01)
sink_node.get_buf()
time.sleep(duration)
events2 = sink_node.get_buf()
graph.stop()

# 3.
# start the graph first, clear buffer, sleep, check buffer
graph.start()
# let some spikes accumulate in the buffer
time.sleep(2)
sink_node.get_buf()
time.sleep(duration)
events3 = sink_node.get_buf()
graph.stop()

print(f'Test 1: spikes over {(events1[-1].timestamp - events1[0].timestamp) / 1e6} s.')
print(f'Test 2: spikes over {(events2[-1].timestamp - events2[0].timestamp) / 1e6} s.')
print(f'Test 3: spikes over {(events3[-1].timestamp - events3[0].timestamp) / 1e6} s.')

ut.close_dynapse1(store, device_name)