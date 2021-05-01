import samna
import samnagui
import samna.dynapse1 as dyn1
import socket
from Dynapse1Constants import *
import random
import time
import json
from multiprocessing import Process
import numpy as np

def free_port():
    """
    Get a free port number using sockets.
    """
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(('0.0.0.0', 0))
    free_socket.listen(5)
    port = free_socket.getsockname()[1]
    free_socket.close()
    return port

def open_device(device_name, sender_port, receiver_port):
    """
    Get unopened devices detected by samna.
    Attribute:
        device_name: string, name the device you want to open.
        sender_port: int, samnaNode's sending port.
        receiver_port: int, samnaNode's receiving port.
    """
    # ----------- connect Python to C++ ----------------
    sender_endpoint = "tcp://0.0.0.0:"+str(sender_port)
    receiver_endpoint = "tcp://0.0.0.0:"+str(receiver_port)
    node_id = 1
    interpreter_id = 2
    # note: has to assign to "samna_node",
    # otherwise "RuntimeError: Store with ID: 1 timed out on content request"
    try:
        global samna_node
        samna_node = samna.SamnaNode(sender_endpoint, receiver_endpoint, node_id)
    except Exception as e:
        print("ERROR: "+str(e)+", please re-run open_device()!")

    # setup the python interpreter node
    samna.setup_local_node(receiver_endpoint, sender_endpoint, interpreter_id)
    # open a connection to device_node, i.e. the store
    samna.open_remote_node(node_id, "device_node")
    # ----------- connect Python to C++ ----------------

    # retrieve unopened device
    devices = samna.device_node.DeviceController.get_unopened_devices()

    if len(devices) == 0:
        raise Exception("no device detected!")

    # let user select a device to open
    for i in range(len(devices)):
        print("["+str(i)+"]: ", devices[i], "serial_number", devices[i].serial_number)

    idx = input("Select the device you want to open by index: ")

    # open the device
    samna.device_node.DeviceController.open_device(devices[int(idx)], device_name)

    samna_info_dict = {
        "sender_port":sender_endpoint,
        "receiver_port":receiver_endpoint,
        "samna_node_id":node_id,
        "device_name":device_name,
        "python_node_id":interpreter_id
    }

    return samna.device_node, samna_info_dict

def open_dynapse1(device_name, gui=True, sender_port=33336, receiver_port=33335):
    """
    open DYNAP-SE1 board with or without GUI.

    Attribute:
        device_name: string, name the DYNAP-SE1 board you want to open.
        gui: if to open the gui or not
            True: will return store and gui_process
            False: only return store
    """
    # ports = random.sample(range(10**4, 10**5), k=2)

    if gui:
        # has to be these 2 numbers if you want to run the GUI
        sender_port=33336
        receiver_port=33335
    
    store, samna_info_dict = open_device(device_name, sender_port, receiver_port)
    
    if gui:
        visualizer_id = 3

        # open the gui
        gui_process, gui_receiving_port = open_gui(store, device_name, visualizer_id)

        samna_info_dict["gui_receiving_port"] = gui_receiving_port
        samna_info_dict["gui_node_id"] = visualizer_id
        print("GUI receiving port:", samna_info_dict["gui_receiving_port"])
        print("GUI node ID:", samna_info_dict["gui_node_id"])

    print("Sender port:", samna_info_dict["sender_port"])
    print("Receiver port:", samna_info_dict["receiver_port"])
    print("Opened device name:", samna_info_dict["device_name"])
    print("SamnaNode ID:", samna_info_dict["samna_node_id"])
    print("PythonNode ID:", samna_info_dict["python_node_id"])
    
    with open('samna_info.json', 'w') as json_file:
        json.dump(samna_info_dict, json_file, indent=4)

    if gui:
        return store, gui_process
    else:
        return store

def open_gui(store, device_name, visualizer_id=3):
    model = getattr(store, device_name)

    # add a node in filter gui_graph
    global gui_graph
    gui_graph = samna.graph.EventFilterGraph()
    # Add a converter node that translate the raw DVS events
    dynapse1_to_visualizer_converter_id = gui_graph.add_filter_node("Dynapse1EventToRawConverter")
    # Add a streamer node that streams visualization events to our graph
    streamer_id = gui_graph.add_filter_node("VizEventStreamer")

    # connect nodes in graph
    gui_graph.connect(dynapse1_to_visualizer_converter_id, streamer_id)

    # connect a node from outside a gui_graph to a node inside the gui_graph
    # We need to explicitly select the input channel
    model.get_source_node().add_destination(gui_graph.get_node_input(dynapse1_to_visualizer_converter_id))

    gui_graph.start()

    # create gui process
    gui_process = Process(target=samnagui.runVisualizer)
    gui_process.start()
    time.sleep(1)

    port = random.randint(10**4, 10**5)
    viz_name = "visualizer"+str(port)
    # open a connection to the GUI node
    samna.open_remote_node(visualizer_id, viz_name)
    visualizer = getattr(samna, viz_name)

    try:
        # The GUI node contains a ZMQ receiver endpoint by default, we can set the address it should listen on
        gui_receiving_port = "tcp://0.0.0.0:"+str(port)
        visualizer.receiver.set_receiver_endpoint(gui_receiving_port) # local connection on port 40000
    except Exception as e:
        print("ERROR: "+str(e)+", please re-run open_gui()!")

    # get streamer node
    streamer_node = gui_graph.get_node(streamer_id)
    # stream on the same endpoint as the receiver is listening to
    streamer_node.set_streamer_endpoint(gui_receiving_port)

    # Connect the receiver output to the visualizer plots input
    visualizer.receiver.add_destination(visualizer.splitter.get_input_channel())

    # Add plots to the GUI
    activity_plot_id = visualizer.plots.add_activity_plot(64, 64, "DYNAP-SE1")
    visualizer.splitter.add_destination("passthrough", visualizer.plots.get_plot_input(activity_plot_id))

    # List currently displayed plots
    visualizer.plots.report()

    return gui_process, gui_receiving_port

def close_dynapse1(store, device_name, gui_process=''):
    '''
    Close DYNAP-SE1 board with or without the GUI.
    '''
    if gui_process != '':
        gui_process.join()
    store.DeviceController.close_device(device_name)

def get_neuron_from_config(config, global_neuron_id):
    """
    Get a neuron by its global_neuron_id from a configuration
    Attributes:
        config: Dynapse1Configuration
        global_neuron_id: int, global neuron id
    """
    chip = int(global_neuron_id / NEURONS_PER_CHIP)
    core = int(global_neuron_id%NEURONS_PER_CHIP / NEURONS_PER_CORE)
    neuron = global_neuron_id%NEURONS_PER_CORE

    return config.chips[chip].cores[core].neurons[neuron]

def gen_synapse_string(synapse):
    syn_type = synapse.syn_type
    if syn_type == dyn1.Dynapse1SynType.NMDA:
        syn_str = "NMDA"
    elif syn_type == dyn1.Dynapse1SynType.AMPA:
        syn_str = "AMPA"
    elif syn_type == dyn1.Dynapse1SynType.GABA_B:
        syn_str = "GABA_B"
    elif syn_type == dyn1.Dynapse1SynType.GABA_A:
        syn_str = "GABA_A"

    return "c"+str(synapse.listen_core_id)+\
            "n"+str(synapse.listen_neuron_id)+\
            syn_str

def print_neuron_synapses(neuron, synapse_id_list=range(MAX_NUM_CAMS)):
    synapses = neuron.synapses
    for i in synapse_id_list:
        if i == len(synapse_id_list)-1:
            end = '\n'
        else:
            end = ','
        print(gen_synapse_string(synapses[i]), end = end)

def gen_destination_string(destination):
    return "C"+str(destination.target_chip_id)+\
            "c"+str(destination.core_mask)+\
            str(destination.in_use)

def print_neuron_destinations(neuron, destination_id_list=range(4)):
    destinations = neuron.destinations
    for i in destination_id_list:
        if i == len(destination_id_list)-1:
            end = '\n'
        else:
            end = ','
        print(gen_destination_string(destinations[i]), end = end)

def get_global_id(chip, core, neuron):
    return neuron+core*NEURONS_PER_CORE+chip*NEURONS_PER_CHIP

def get_global_id_list(tuple_list):
    return [tuple_list[2]+tuple_list[1]*NEURONS_PER_CORE+tuple_list[0]*NEURONS_PER_CHIP\
                for tuple_list in tuple_list]

def get_parameters(config, chip, core):
    return config.chips[chip].cores[core].parameter_group.param_map.values()

def save_parameters2txt_file(config, filename="./dynapse_parameters.txt"):
    save_file = open(filename, "w")
    for chip in range(NUM_CHIPS):
        for core in range(CORES_PER_CHIP):
            params = get_parameters(config, chip, core)
            for param in params:
                save_file.write(
                    'C{0}c{1}:({2},{3},{4})\n'.format(
                        chip,
                        core,
                        param.param_name,
                        param.coarse_value,
                        param.fine_value))

def set_parameters_in_txt_file(model, filename="./dynapse_parameters.txt"):
    # parse file and update parameters
    with open(filename) as f:
        lines = f.read().splitlines()

    non_empty_lines = [line for line in lines if line.strip() != ""]

    # Strips the newline character
    for line in non_empty_lines:
        chip = line.split('C')[1].split('c')[0].strip()
        core = line.split('c')[1].split(':')[0].strip()
        name = line.split('(')[1].split(',')[0].strip()
        coarse_value = line.split(',')[1].strip()
        fine_value = line.split(',')[2].split(')')[0].strip()

        param = dyn1.Dynapse1Parameter(name, int(coarse_value), int(fine_value))

        model.update_single_parameter(param, int(chip), int(core))

def save_parameters2json_file(config, filename="./dynapse_parameters.json"):
    data = {}
    data['parameters'] = []
    for chip in range(NUM_CHIPS):
        for core in range(CORES_PER_CHIP):
            params = get_parameters(config, chip, core)
            for param in params:
                param_dict = {
                    "chip":chip,
                    "core":core,
                    "parameter_name":param.param_name,
                    "coarse_value":param.coarse_value,
                    "fine_value":param.fine_value
                }
                data['parameters'].append(param_dict)

    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def set_parameters_in_json_file(model, filename="./dynapse_parameters.json"):
    with open(filename) as json_file:
        data = json.load(json_file)
    for p in data['parameters']:
        param = dyn1.Dynapse1Parameter(p['parameter_name'], int(p['coarse_value']), int(p['fine_value']))
        model.update_single_parameter(param, int(p['chip']), int(p['core']))

def get_serial_number(store, device_name):
    devices = store.DeviceController.get_opened_devices()
    for device in devices:
        if device.name == device_name:
            print(device.name)
            print(device.device_info)
            return device.device_info.serial_number
    raise Exception("wrong device name!")

def print_dynapse1_spike(event):
    print((event.timestamp, event.neuron_id+
            event.core_id*NEURONS_PER_CORE+
            event.chip_id*NEURONS_PER_CHIP), end=',')

def create_neuron_select_graph(model, global_neuron_ids):
    """
    Attribute:
        model: Dynapse1Model, returned by getattr(store, device_name)
        global_neuron_ids: list of int, global neuron ids of the neurons you want to monitor.
    Process and usage of the graph:
        Create a graph: source_node in model -> filter_node in graph -> sink_node to get events.
        Only filter_node is in the graph. Source and sink nodes are outside graph.
        To use the graph, first graph.start().
        To get events, sink_node.get_buf().
        If you graph.stop(), for now the graph actually won't stop, all events are still
        streamed into the buffer of sink_node. This is work in progess.
        Thus to get events for 1 second, you need to first clear the buffer of sink_node using get_buf().
        i.e.,
        sink_node.get_buf()
        sleep(1)
        events = sink_node.get_buf()
    """
    # create a graph. A graph is a thread.
    graph = samna.graph.EventFilterGraph()
    # Filtered sinkNode. Node 3. Initialized outside graph, not by add_filter_node.
    sink_node = samna.BufferSinkNode_dynapse1_dynapse1_event()

    # NeuronSelectFilterNode. Node 2. Initialized inside graph, by add_filter_node.
    filter_node_id = graph.add_filter_node("Dynapse1NeuronSelect")
    # Get this filterNode from the created graph and set selected global neuron IDs.
    filter_node = graph.get_node(filter_node_id)
    filter_node.set_neurons(global_neuron_ids)

    # dk.get_source_node() is Node 1. Initialized outside graph, not by add_filter_node.
    # Connect Node 1 to Node 2, using add_destination because Node 1 not inside graph.
    # Use graph.connect(node_id_1, node_id_2) only if both nodes inside graph.
    model.get_source_node().add_destination(graph.get_node_input(filter_node_id))

    # connect Node 2 to Node 3.
    graph.add_destination(filter_node_id, sink_node.get_input_channel())

    return graph, filter_node, sink_node

def get_time_wrap_events(model):
    """
    Attribute:
        model: Dynapse1Model, returned by getattr(store, device_name)
    Purpose:
        DYNAP-SE1 sends out 2 types of events: spike and timeWrapEvent.
        timeWrapEvent occurs when the 32 bit timestamp wraps around.
        This happens every ~37 minutes.
        With the graph created here, you can monitor if any timeWrapEvent is generated.
    """
    graph = samna.graph.EventFilterGraph()
    # add a filter node to the graph
    filter_node_id = graph.add_filter_node("Dynapse1TimestampWrapEventFilter")
    filter_node = graph.get_node(filter_node_id)

    # connect sourceNode (outside the graph) to the filterNode
    model.get_source_node().add_destination(graph.get_node_input(filter_node_id))

    # connect the filterNode to a sinkNode (outside the graph)
    sink_node = samna.BufferSinkNode_dynapse1_dynapse1_event()
    graph.add_destination(filter_node_id, sink_node.get_input_channel())

    return graph, sink_node


def set_fpga_spike_gen(fpga_spike_gen, spike_times, indices, target_chips, isi_base, repeat_mode=False):
    """
    Author: Nicoletta Risi. Adapted by Jingyue Zhao.

    This sets the FpgaSpikeGen object.
    Args:
        spike_times    (list): list of input spike times, in sec
        indices     (list): list of FPGA spike generator ids sorted according to 
                            time of spike
        target_chip    (list): list of target chip to which each event will be
                            sent.
        isi_base        (int): 90 or 900 (See below)
        repeat_mode    (bool): If repeat is True, the spike generator will 
                            loop from the beginning when it reaches the end 
                            of the stimulus.                    
    This function sets the SpikeGenerator object given a list of spike times, 
    in sec, correspondent input neuron ids and the target chips, i.e. the
    chip destination of each input event. 
    
    About  **** isi_base ****:
    Given a list of spike times (in sec) a list of isi (Inter Stimulus Interval) 
    is generated. Given a list of isi, the resulting list of isi set from the 
    FPGA will be:
        isi*unit_fpga
    with             
        unit_fpga = isi_base/90 * us    
        
    Thus, given a list of spike_times in sec:
        - first the spike times are converted in us
        - then a list of isi (in us) is generated
        - then the list of isi is divided by the unit_fpga (so that the
            resulting list of isi set on FPGA will have the correct unit
            given the input isi_base)        
    E.g.: if isi_base=900 the list of generated isi will be multiplied on
    FPGA by 900/90 us = 10 us
    
    """
    assert all(np.sort(spike_times)==(spike_times)), 'Spike times must be sorted!'
    assert(len(indices)==len(spike_times)==len(target_chips)), 'Spike times '+\
        ' and neuron ids need to have the same length'
    
    unit_fpga = isi_base/90 #us
    spike_times_us = np.array(spike_times)*1e6
    spike_times_unit_fpga = (spike_times_us / unit_fpga).astype('int')
    
    fpga_isi = np.array([0]+list(np.diff(spike_times_unit_fpga)), dtype=int)
    fpga_nrn_ids = np.array(indices)
    fpga_target_chips = np.array(target_chips)
    
    fpga_events = []
    for idx_isi, isi in enumerate(fpga_isi):
        fpga_event = dyn1.FpgaSpikeEvent()
        fpga_event.core_mask = 15
        fpga_event.target_chip = fpga_target_chips[idx_isi]
        fpga_event.neuron_id = fpga_nrn_ids[idx_isi]
        fpga_event.isi = isi
        fpga_events.append(fpga_event)
        
    assert all(np.asarray(fpga_isi) < MAX_ISI), 'isi is too large for'+\
            'the specified isi_base!'
    assert len(fpga_isi) < MAX_FPGA_LEN , 'Input stimulus is too long!'
    
    # Set spikeGen:
    fpga_spike_gen.set_variable_isi_mode(True)
    fpga_spike_gen.preload_stimulus(fpga_events)
    fpga_spike_gen.set_isi_multiplier(isi_base)
    fpga_spike_gen.set_repeat_mode(repeat_mode)
