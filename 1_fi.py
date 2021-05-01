import samna
import samna.dynapse1 as dyn1
import time

from Dynapse1Constants import *
import Dynapse1Utils as ut
import NetworkGenerator as n
from NetworkGenerator import Neuron

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
    paramGroup.param_map["PS_WEIGHT_EXC_F_N"].coarse_value = 0
    paramGroup.param_map["PS_WEIGHT_EXC_F_N"].fine_value = 0

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

def get_fi_curve(DC_values):
    # open DYNAP-SE1 board to get Dynapse1Model
    device_name = "my_dynapse1"
    # change the port numbers to not have conflicts with other groups
    store = ut.open_dynapse1(device_name, gui=False, sender_port=12321, receiver_port=12322)
    model = getattr(store, device_name)

    # --------------- FI curve ----------------
    # Monitor the spikes of a single neuron with different DC input

    # set initial (proper) parameters
    paramGroup = gen_param_group_1core()
    for chip in range(4):
        for core in range(4):
            model.update_parameter_group(paramGroup, chip, core)

    # prepare the DC values
    # Note: don't not use too large coarse values (>3). Too many spikes will kill the board..
    
    # linear DC values, float instead of tuple
    linear_DC_values = []
    # result frequency list
    freqs = []

    # get events of a selected neuron
    # choose a neuron to monitor.
    chip = 0
    core = 1
    nid = 16
    # get the global neuron ID of the neuron
    monitored_global_nid = ut.get_global_id(chip, core, nid)
    # duration per DC value
    duration = 1

    # create a graph to monitor the spikes of this neuron
    graph, filter_node, sink_node = ut.create_neuron_select_graph(model, [monitored_global_nid])
    graph.start()

    for dc in DC_values:
        # set new DC
        param = dyn1.Dynapse1Parameter("IF_DC_P", dc[0], dc[1])
        model.update_single_parameter(param, chip, core)

        # get events
        # clear the output buffer
        sink_node.get_buf()
        # sleep for duration
        time.sleep(duration)
        # get the events accumulated during the past 1 sec
        events = sink_node.get_buf()

        # append the frequency to the list
        freq = len(events)/duration
        freqs.append(freq)

        # get the linear DC value for plotting
        config = model.get_configuration()
        linear_dc_value = config.chips[chip].cores[core].parameter_group.get_linear_parameter("IF_DC_P")
        linear_DC_values.append(linear_dc_value)

    graph.stop()

    # close Dynapse1
    ut.close_dynapse1(store, device_name)

    return linear_DC_values, freqs

if __name__ == "__main__":
    DC_values = [(0, 0), (0, 50), (0, 100), (0, 200), (1, 50), (1, 100), \
                (1, 200), (2, 50), (2, 100), (2, 200), (3, 50), (3, 100)]

    linear_DC_values, freqs = get_fi_curve(DC_values)

    print(linear_DC_values)
    print(freqs)
    