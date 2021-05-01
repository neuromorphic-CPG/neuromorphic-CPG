import samna.dynapse1 as dyn1
import Dynapse1Utils as ut
from Dynapse1Constants import *
import collections
from collections import Counter

class Neuron:
    """
    Attribute:
        chip_id, core_id, neuron_id: int
        is_spike_gen: bool, if this neuron is a spike generator on the FPGA or a physical neuron on chip.
        incoming_connections: a dictionarty which stores the incoming_connections.
            key: tuple, (pre.core_id,pre.neuron_id,synapse_type).
                Corresponds to cam. Divide the connections by its cam value for cam reuse.
            value: list, [(pre.chip_id, pre.is_spike_gen), (pre.chip_id, pre.is_spike_gen),...].
                To tell if the post neurons are the same neuron. get the connection weight.
    """
    def __init__(self, chip_id=0, core_id=0, neuron_id=0, is_spike_gen=False):
        if is_spike_gen:
            num_chips = 1
        else:
            num_chips = NUM_CHIPS
        if chip_id >= num_chips or chip_id < 0:
            raise Exception("chip id invalid!")
        if core_id >= CORES_PER_CHIP or core_id < 0:
            raise Exception("core id invalid!")
        if neuron_id >= NEURONS_PER_CORE or neuron_id < 0:
            raise Exception("neuron id invalid!")
        self.chip_id = chip_id
        self.core_id = core_id
        self.neuron_id = neuron_id
        self.is_spike_gen = is_spike_gen
        # (pre.core_id,pre.neuron_id,synapse_type): [(pre.chip_id, pre.is_spike_gen), (pre.chip_id, pre.is_spike_gen),...]
        self.incoming_connections = collections.defaultdict(list)

class Network:
    """
    Attribute:
        post_neuron_dict: a dictionary which stores all the post neurons (and their incoming connections).
            key: tuple, (post.chip_id, post.core_id).
                Divide the post neurons by its location (core) for aliasing check.
            value: list of neurons each of which has incoming connections.
    """
    def __init__(self):
        # only track onchip post neurons
        # all connection info already stored in post_neuron.incoming_connections
        self.post_neuron_dict = collections.defaultdict(list)

    def add_connection(self, pre, post, synapse_type):
        if post.is_spike_gen:
            raise Exception("post neuron cannot be a spike generator!")

        # onchip connections from left chips (i.e. 0,2) to right chips (i.e. 1,3) will make chips die
        if pre.is_spike_gen is False:
            left_chips = [0,2]
            right_chips = [1,3]
            if pre.chip_id in left_chips and post.chip_id in right_chips:
                raise Exception("connections from left chips [0,2] to right chips [1,3] are forbidden!")

        post_key = (post.chip_id, post.core_id)
        # check if post neuron already in the dict
        # if not, add a post neuron with the pre in its incoming_connections;
        # if yes, only append the pre in post's incoming_connections
        nid_in_list = find_neuron_in_dict(post, self.post_neuron_dict)
        if nid_in_list == None:
            # add a new post neuron with the pre in incoming_conns to the dict
            post.incoming_connections.clear()
            post.incoming_connections[(pre.core_id, pre.neuron_id,
                synapse_type)].append((pre.chip_id, pre.is_spike_gen))
            self.post_neuron_dict[post_key].append(post)
        else:
            # only update the incoming_connections of the post neuron, add the new pre
            self.post_neuron_dict[post_key][nid_in_list].\
                incoming_connections[(pre.core_id, pre.neuron_id,
                synapse_type)].append((pre.chip_id, pre.is_spike_gen))

    def remove_connection(self, pre, post, synapse_type):
        if post.is_spike_gen:
            raise Exception("post neuron cannot be a spike generator!")

        # check if post neuron already in the dict
        post_id_in_list = find_neuron_in_dict(post, self.post_neuron_dict)
        if post_id_in_list == None:
            raise Exception("connection does not exist in the network!")
        else:
            # post neuron in the dict, check if pre in this post's incoming_connections
            post_key = (post.chip_id, post.core_id)
            post_in_dict = self.post_neuron_dict[post_key][post_id_in_list]
            pre_id = find_pre_in_post_incoming(pre, post_in_dict, synapse_type)
            if pre_id == None:
                raise Exception("connection does not exist in the network!")
            else:
                # remove the first pre from the incoming_connections of the post in the dict
                post_incoming_connections_dict = post_in_dict.incoming_connections
                pre_tag = (pre.core_id, pre.neuron_id, synapse_type)
                post_pre_tag_list = post_incoming_connections_dict[pre_tag]

                # remove the pre from the pre_tag list
                post_pre_tag_list.pop(pre_id)
                # self.post_neuron_dict[(post.chip_id, post.core_id)][post_id_in_list].\
                #     incoming_connections[(pre.core_id, pre.neuron_id,
                #     synapse_type)].pop(pre_id)

                # check if incoming_connections.pre_tag becomes empty
                # if empty, remove this pre_tag key from the incoming_connections dict
                if len(post_pre_tag_list) == 0:
                    # self.post_neuron_dict[(post.chip_id, post.core_id)][post_id_in_list].\
                    #     incoming_connections.pop((pre.core_id, pre.neuron_id,
                    #     synapse_type))
                    post_incoming_connections_dict.pop(pre_tag)

                    # check if the entire incoming_connections dict becomes empty
                    # if empty, the post neuron is not a post anymore, remove it from the post_dict[post_key] list
                    if len(post_incoming_connections_dict.keys()) == 0:
                        self.post_neuron_dict[post_key].pop(post_id_in_list)

                        # check if the post_neuron_dict[post_key] list becomes empty
                        # if empty, don't need this post_key anymore, remove this key from post_neuron_dict
                        if len(self.post_neuron_dict[post_key]) == 0:
                            self.post_neuron_dict.pop(post_key)

                            # check if post_neuron_dict becomes empty, send out a message
                            if len(self.post_neuron_dict.keys()) == 0:
                                print("Network cleared!")

class NetworkGenerator:
    """
    Whenever you want to change your network, you need to add/remove connections
    using the previous NeuronNeuronConnector from which you took the configuration
    and applied it using the model during your last modification of the network.
    Otherwise, you just create a new NeuronNeuronConnector and configuration
    from the scratch and apply it.
    """
    def __init__(self):
        self.config = dyn1.Dynapse1Configuration()
        self.network = Network()

    def add_connection(self, pre, post, synapse_type):
        self.network.add_connection(pre, post, synapse_type)

    def remove_connection(self, pre, post, synapse_type):
        self.network.remove_connection(pre, post, synapse_type)

    def clear_network(self):
        self.network.post_neuron_dict.clear()

    def print_network(self):
        print_post_neuron_dict(self.network.post_neuron_dict)

    def make_dynapse1_configuration(self):
        '''
        check if the self.network is valid or not.
        If valid: convert it to a configuration
        If not: raise exception
        '''
        print("Checking if the given network is valid to be deployed on DYNAP-SE1 chips...")
        is_valid, large_conn_weight_dict = validate(self.network, MAX_NUM_CAMS)

        self.config = convert_validated_network2dynapse1_configuration(self.network, large_conn_weight_dict)
        print("Converted the validated network to a Dynapse1 configuration!")

        return self.config

    def make_dynapse1_configuration_in_chip(self, chip_id):
        # first check if the neurons in the network are all in the chip
        post_neuron_dict = self.network.post_neuron_dict
        for post_chip_core in post_neuron_dict:
            # check chip id of the post neuron
            if post_chip_core[0] != chip_id:
                raise Exception("ERROR: network has neuron(s) outside chip "+str(chip_id)+"!")

            # check the chip ids of all the pre neurons of the post neurons
            post_neurons = post_neuron_dict[post_chip_core]
            for post_neuron in post_neurons:
                for pre_tag in post_neuron.incoming_connections:
                    pre_chip_spikegens = post_neuron.incoming_connections[pre_tag]
                    for pre_chip_spikegen in pre_chip_spikegens:
                        if pre_chip_spikegen[1] == False and pre_chip_spikegen[0] != chip_id:
                            raise Exception("ERROR: network has neuron(s) outside chip "+str(chip_id)+"!")

        print("Neurons in the network are all located in chip "+str(chip_id)+".")

        config = self.make_dynapse1_configuration()
        return config

    def make_dynapse1_configuration_in_core(self, chip_id, core_id):
        # first check if the neurons in the network are all in the core
        post_neuron_dict = self.network.post_neuron_dict
        for post_chip_core in post_neuron_dict:
            # check core and chip id of the post neuron
            if post_chip_core[0] != chip_id or post_chip_core[1] != core_id:
                raise Exception("ERROR: network has neuron(s) outside chip "
                                +str(chip_id)+", core "+str(core_id)+"!")

            # check the core and chip ids of all the pre neurons of the post neurons
            post_neurons = post_neuron_dict[post_chip_core]
            for post_neuron in post_neurons:
                for pre_tag in post_neuron.incoming_connections:
                    pre_chip_spikegens = post_neuron.incoming_connections[pre_tag]
                    for pre_chip_spikegen in pre_chip_spikegens:
                        if pre_chip_spikegen[1] == False:
                            # for all the physical neurons, check their core and chip ids.
                            chip = pre_chip_spikegen[0]
                            core = pre_tag[0]
                            if chip != chip_id or core != core_id:
                                raise Exception("ERROR: network has neuron(s) outside chip "
                                                +str(chip_id)+", core "+str(core_id)+"!")

        print("Neurons in the network are all located in chip "+str(chip_id)+", core "+str(core_id)+".")

        config = self.make_dynapse1_configuration()
        return config

def validate(network, max_num_cams=MAX_NUM_CAMS):
    '''
    Validation rules:
    First check cams: check the number of incoming connections of each neuron (after reusing cam):
        for each neuron, check its pre neurons:
            if there's pre with same (core_id, neuron_id, synapse_type):
                calculate the number of cams (num_cams) needed by these pre neurons
                num_cams is the maximum weight of between a certain pre and this post
                other pre neurons will also get this max weight cause they are sharing the same cam
                send a warning to the user about 1) the weight sharing 2) different pres sharing same cam
            if the number of incoming connections > 64:
                raise exception

    Then check aliasing: for neurons in the same core, check their pre neurons.
        if two different post neurons have two different pres with
        same (core_id, neuron_id, synapse_type) but not in same chip:
            raise exception

    No need to check srams
    '''
    valid = False
    # dictionary to save weights > 1, e.g. (pre_tag, post_neuron): num_cams
    large_conn_weight_dict = {}
    post_neuron_dict = network.post_neuron_dict

    for core in post_neuron_dict:
        # get onchip neurons in each core
        post_neurons = post_neuron_dict[core]

        # ----------------------- check cams of all post neurons -----------------------
        for post in post_neurons:
            num_cams = 0
            # pre neurons with different (core_id, neuron_id, synapse_type)
            for pre_tag in post.incoming_connections:
                pre_chip_virtual_list = post.incoming_connections[pre_tag]

                # pre_weight_dict: a dictionary describe the weights between each pre and the post
                # e.g. {(pre1_chip,pre1_is_spike_gen): 1, (pre2_chip,pre2_is_spike_gen): 2}
                # means 1 connection (pre1, post), 2 connections (pre2, post) needed
                # this is an aliasing error:
                # num_cams=1, WRONG for pre2; num_cams=2, WRONG for pre1; num_cams=1, WRONG for both pre1 and pre2
                # If all pre neurons share the same weight, then it's fine
                pre_weight_dict = dict(Counter(pre_chip_virtual_list))
                weight_list = list(pre_weight_dict.values())
                # if all pre neurons have the same weight to the post
                all_pre_same_weight = all(elem == weight_list[0] for elem in weight_list)

                if not all_pre_same_weight:
                    raise Exception("ERROR: aliasing pre neurons exist! Post neuron "+gen_neuron_string(post)+ \
                                    " has pre neurons with same (core_id, neuron_id, synapse_type) " \
                                    +str(pre_tag)+" in different chips. The (pre, post) connections have different weights, which cannot be implemented on chip!")
                weight = weight_list[0]
                # pre neurons with same (core_id, neuron_id, synapse_type) will reuse the same cam of the post neuron
                if len(pre_weight_dict.keys()) > 1:
                    print("WARNING: post neuron "+gen_neuron_string(post)+ \
                        " may have aliasing pre neurons or spike generators with same (core_id, neuron_id, synapse_type) " \
                        +str(pre_tag)+" but in different chips! The (pre, post) connections share weight = "+str(weight)+".")

                # the number of cams needed for this pre tag
                num_cams += weight

                if weight > 1:
                    large_conn_weight_dict[(pre_tag, post)] = weight

            if num_cams > max_num_cams:
                raise Exception("ERROR: post neuron "+gen_neuron_string(post)+" has too many pre neurons or spike generators!")
        # ----------------------- check cams of all post neurons -----------------------

        # ----------------------- check aliasing -----------------------
        # number of post neurons in the same core
        num_post = len(post_neurons)

        # only if there are multiple post neurons in one core, check their pre neurons
        if num_post > 1:
            # compare each neuron with other neurons in the same chip
            # check if they have different pres with same (core_id, neuron_id, synapse_type) but not in same chip
            for nid_1 in range(num_post-1):
                for nid_2 in range(nid_1+1, num_post):
                    pre_dict_1 = post_neurons[nid_1].incoming_connections
                    pre_dict_2 = post_neurons[nid_2].incoming_connections
                    # compare pre neurons with same tag (core_id, neuron_id, synapse_type) cam
                    # of post nid1 and post nid2
                    for pre_tag_1 in pre_dict_1:
                        if pre_tag_1 in pre_dict_2:
                            # pre neuron info (chip_id, spike_gen) list with the same cam should be exact the same
                            # neurons in the same chip, should same neurons/spikegens! otherwise aliasing!
                            pre_chips_1 = sorted(pre_dict_1[pre_tag_1])
                            pre_chips_2 = sorted(pre_dict_2[pre_tag_1])
                            if pre_chips_1 != pre_chips_2:
                                raise Exception("ERROR: aliasing pre neurons exist! Post neurons " \
                                                +gen_neuron_string(post_neurons[nid_1])+" and " \
                                                +gen_neuron_string(post_neurons[nid_2]) \
                                                +" have different pre neurons in different chips but with same (core_id, neuron_id, synapse_type) " \
                                                +str(pre_tag_1)+".")
        # ----------------------- check aliasing -----------------------

    print("Validation complete: the network is good to go!")
    valid = True
    return valid, large_conn_weight_dict

def convert_validated_network2dynapse1_configuration(network, large_conn_weight_dict):
    """
    Convert a validated "network" to a Dynapse1Configuration which can be applied using Dynapse1Model.
    """
    # check if the network is empty
    if len(network.post_neuron_dict.keys()) == 0:
        print("WARNING: the network is empty!")

    config = dyn1.Dynapse1Configuration()

    for loc in network.post_neuron_dict:
        # get the chip and core ids of this core
        # for write sram of the pre neurons
        post_chip_id = loc[0]
        post_core_id = loc[1]

        # get onchip neurons in each core
        post_neurons = network.post_neuron_dict[loc]
        for post_neuron in post_neurons:
            post_in_config = ut.get_neuron_from_config(config,
                                        post_neuron.neuron_id+
                                        post_core_id*NEURONS_PER_CORE+
                                        post_chip_id*NEURONS_PER_CHIP)

            for pre_tag in post_neuron.incoming_connections:
                # pre_tag = (pre_neuron.core_id, pre_neuron.neuron_id, synapse_type)
                # for write cam of the post
                pre_core_id = pre_tag[0]
                pre_neuron_id = pre_tag[1]
                synapse_type = pre_tag[2]

                # write cam of this post neuron in configuration
                # this cam serves all the pre neurons under this pre_tag
                # only write cams once for all the pres with the same pre_tag
                # cam reuse is implemented already this way!

                # write how many pre_tags into the cams of post_neuron?
                # num_cams = weights of (pre_tag, post) connection
                # all the pre neurons should have the same weight (validated already) !
                if (pre_tag, post_neuron) in large_conn_weight_dict:
                    weight = large_conn_weight_dict[(pre_tag, post_neuron)]
                else:
                    weight = 1

                check_and_write_post_cam(post_in_config, pre_core_id,
                                        pre_neuron_id, synapse_type,
                                        weight)

                # write the srams of all pre neurons in configuration
                for pre_chip_virtual in post_neuron.incoming_connections[pre_tag]:
                    # pre_chip_virtual = (neuron.chip_id, neuron.is_spike_gen)
                    # if pre is spikeGen, no need to write the sram of the pre.
                    if pre_chip_virtual[1]:
                        continue
                    else:
                        # get the real pre neuron in the configuration
                        pre_in_config = ut.get_neuron_from_config(config,
                                            pre_neuron_id+
                                            pre_core_id*NEURONS_PER_CORE+
                                            pre_chip_virtual[0]*NEURONS_PER_CHIP)
                        # write the sram of the pre
                        check_and_write_pre_sram(pre_in_config, post_chip_id, post_core_id)

    return config

def print_post_neuron_dict(post_neuron_dict):
    if len(post_neuron_dict.keys()) == 0:
        print("The network is empty!")
    else:
        print("Post neuron (ChipId,coreId,neuronId): incoming connections [(preNeuron,synapseType), ...]")
        dictionary_items = post_neuron_dict.items()
        sorted_items = sorted(dictionary_items)
        for item in sorted_items:
            post_neurons = item[1]
            for post in post_neurons:
                incoming_connections_list, incoming_connections_str_list = \
                    convert_incoming_conns_dict2list(post.incoming_connections)
                print(gen_neuron_string(post)+":", incoming_connections_str_list)

def convert_incoming_conns_dict2list(incoming_connections_dict):
    """
    Convert (pre.core_id,pre.neuron_id,synapse_type): [(pre.chip_id, pre.is_spike_gen), (pre.chip_id, pre.is_spike_gen),...]
    to
    [(preNeuron1,synapseType1), (preNeuron1,synapseType2), (preNeuron1,synapseType2), (preNeuron2,synapseType1),...]
    """
    for pre_tag in incoming_connections_dict:
        core = pre_tag[0]
        neuron = pre_tag[1]
        syn_type = pre_tag[2]
        if syn_type == dyn1.Dynapse1SynType.NMDA:
            syn_str = "NMDA"
        elif syn_type == dyn1.Dynapse1SynType.AMPA:
            syn_str = "AMPA"
        elif syn_type == dyn1.Dynapse1SynType.GABA_B:
            syn_str = "GABA_B"
        elif syn_type == dyn1.Dynapse1SynType.GABA_A:
            syn_str = "GABA_A"

        pre_neurons = incoming_connections_dict[pre_tag]
        incoming_connections_list = []
        incoming_connections_str_list = []
        for pre_neuron in pre_neurons:
            chip = pre_neuron[0]
            is_spike_gen = pre_neuron[1]
            pre_neuron = Neuron(chip,core,neuron,is_spike_gen)
            incoming_connections_list.append((pre_neuron,syn_type))
            incoming_connections_str_list.append((gen_neuron_string(pre_neuron),syn_str))

    return incoming_connections_list, incoming_connections_str_list

def gen_neuron_string(neuron):
    if neuron.is_spike_gen:
        return ("C"+str(neuron.chip_id)
            +"c"+str(neuron.core_id)
            +"s"+str(neuron.neuron_id))
    else:
        return ("C"+str(neuron.chip_id)
                +"c"+str(neuron.core_id)
                +"n"+str(neuron.neuron_id))

def is_same_neuron(neuron1, neuron2):
    if neuron1.chip_id == neuron2.chip_id and\
        neuron1.core_id == neuron2.core_id and\
        neuron1.neuron_id == neuron2.neuron_id and\
        neuron1.is_spike_gen == neuron2.is_spike_gen:
        return True
    else:
        return False

def find_neuron_in_dict(neuron, post_neuron_dict):
    # if the key exist
    if (neuron.chip_id, neuron.core_id) in post_neuron_dict.keys():
        # if the neuron exists in the corresponding key
        neuron_list = post_neuron_dict[(neuron.chip_id, neuron.core_id)]
        for i in range(len(neuron_list)):
            neuron_in_dict = neuron_list[i]
            if is_same_neuron(neuron, neuron_in_dict):
                return i

        return None

def find_pre_in_post_incoming(pre_neuron, post_neuron_in_dict, synapse_type):
    pre_dict = post_neuron_in_dict.incoming_connections
    # if the key exist
    if (pre_neuron.core_id, pre_neuron.neuron_id, synapse_type) in pre_dict.keys():
        # if the pre neuron exists in the corresponding key
        pre_neuron_list = pre_dict[(pre_neuron.core_id, pre_neuron.neuron_id, synapse_type)]
        for i in range(len(pre_neuron_list)):
            chip_spikegen_tuple = pre_neuron_list[i]
            # if same neuron, return the first pre_id in the list
            if pre_neuron.chip_id == chip_spikegen_tuple[0] and \
                pre_neuron.is_spike_gen == chip_spikegen_tuple[1]:
                return i
    return None

def write_pre_destination(pre_destinations, pre_dest_id, virtual_core_id, target_chip_id,\
    sx, sy, dx, dy, core_mask, in_use):
    pre_destinations[pre_dest_id].virtual_core_id = virtual_core_id
    pre_destinations[pre_dest_id].target_chip_id = target_chip_id
    pre_destinations[pre_dest_id].sx = sx
    pre_destinations[pre_dest_id].sy = sy
    pre_destinations[pre_dest_id].dx = dx
    pre_destinations[pre_dest_id].dy = dy
    pre_destinations[pre_dest_id].core_mask = core_mask
    pre_destinations[pre_dest_id].in_use = in_use

def write_post_synapse(post_synapses, post_synapse_id, listen_core_id, listen_neuron_id, synapse_type):
    post_synapses[post_synapse_id].listen_core_id = listen_core_id
    post_synapses[post_synapse_id].listen_neuron_id = listen_neuron_id
    post_synapses[post_synapse_id].syn_type = synapse_type

def get_usable_pre_destination_id(pre_destinations, target_chip_id):
    """
    check if the pre neuron can send a connection to the target chip.
    Attributes:
        pre_destinations: destinations of the pre neuron, sram
        target_chip_id: int
    """
    # check if the pre can send a connection to the target chip
    pre_available = False
    reuse_destination = False

    # if pre already has sram targeting target_chip, no need to write new sram
    pre_dest_id = 0
    for i in range(len(pre_destinations)):
        if pre_destinations[i].target_chip_id == target_chip_id:
            pre_available = True
            pre_dest_id = i
            break

    # if pre does not have sram targeting target_chip, write the first unoccupied sram
    if not pre_available:
        for i in range(len(pre_destinations)):
            if not pre_destinations[i].in_use:
                pre_available = True
                pre_dest_id = i
                break

    if pre_available and pre_destinations[pre_dest_id].in_use:
        reuse_destination = True

    return pre_available, pre_dest_id, reuse_destination

def get_usable_post_synapse_id(post_synapses, listen_core_id, listen_neuron_id, synapse_type, weight):
    """
    check if the post neuron can receive a connection.
    Attributes:
        post_synapses: synapses of the post neuron, cam
        listen_core_id: int, [0,4)
        listen_neuron_id: int, [0,256)
        synapse_type: samna.dynapse1.Dynapse1SynType.NMDA, AMPA, GABA_B, GABA_A
        weight: number of cams needed to be written
    """
    # check if the post can receive a connection
    post_available = False
    post_synapse_id = 0

    # no need to check the reuse because when converting network to configuration
    # we take a "global" view: the pre_tag is brand new to the post everytime this function is called
    # and this function will be called only once which adds the cams for all the pre neurons
    total_cams = len(post_synapses)
    for i in range(total_cams):
        # if there is space left on post_synapses
        # find the first available cams, num_available_cams should = weight
        if (post_synapses[i].listen_neuron_id+\
            post_synapses[i].listen_core_id) == 0 and\
            post_synapses[i].syn_type == dyn1.Dynapse1SynType.NMDA and\
            (total_cams - i) >= weight:
            post_available = True
            post_synapse_id = i
            break

    return post_available, post_synapse_id

def check_and_write_pre_sram(pre, post_chip_id, post_core_id):
    pre_destinations = pre.destinations
    pre_chip_id = pre.chip_id

    pre_available, pre_dest_id, reuse_destination = \
        get_usable_pre_destination_id(pre_destinations, post_chip_id)

    if not pre_available:
        raise Exception("pre neuron has no available outputs!")

    # prepare the coremask: add the new post core into the coremask
    # 1 << post_core_id: shift 1 to left by post_core_id bits
    # 1<<0, 1<<1, 1<<2, 1<<3 = (1, 2, 4, 8) = 0001, 0010, 0100, 1000
    core_mask = pre_destinations[pre_dest_id].core_mask | (1 << post_core_id)

    if reuse_destination:
        # reuse the existing sram, sram already targets the post chip, only need to update the coremask
        pre_destinations[pre_dest_id].core_mask = core_mask

    else:
        # create a new sram for this connection
        virtual_core_id = pre.core_id

        # Routing: calculate the sign and distance between post and pre
        # take the lowest bit as 1 or 0
        # 0&1, 1&1, 2&1, 3&1 = 0000&1, 0001&1, 0010&1, 0011&1 = (0, 1, 0, 1)
        d = (post_chip_id & 1) - (pre_chip_id & 1)
        if d < 0:
            sx = True
        else:
            sx = False
        dx = abs(d)

        # Routing: calculate the sign and distance between post and pre
        # take the second lowest bit as 1 or 0
        # (0&2)>>1, (1&2)>>1, (2&2)>>1, (3&2)>>1 = (0, 0, 1, 1)
        d = ((post_chip_id & 2)>>1) - ((pre_chip_id & 2)>>1)
        if d < 0:
            sy = False
        else:
            sy = True
        dy = abs(d)

        write_pre_destination(pre_destinations, pre_dest_id, virtual_core_id, post_chip_id,\
            sx, sy, dx, dy, core_mask, True)

def check_and_write_post_cam(post, pre_core_id, pre_neuron_id, synapse_type, weight):

    post_available, post_synapse_id = get_usable_post_synapse_id(post.synapses,
                                                pre_core_id,
                                                pre_neuron_id,
                                                synapse_type,
                                                weight)

    if not post_available:
        raise Exception("post neuron has no available inputs!")

    # write "weight" available cams
    for w in range(weight):
        write_post_synapse(post.synapses, post_synapse_id+w, pre_core_id, pre_neuron_id, synapse_type)

if __name__ == "__main__":
    # create a network
    net_gen = NetworkGenerator()

    # Test different abnormal cases
    is_spikegen = True
    try:
        print("--------------- WRONG post is spikegen ---------------")
        # post.is_spike_gen
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,20,is_spikegen), dyn1.Dynapse1SynType.AMPA)
        new_config = net_gen.make_dynapse1_configuration()
        print("WRONG post is spikegen pass")
    except Exception as e:
        print(e)

    try:
        print("--------------- WRONG remove nonexisting conn ---------------")
        # remove nonexisting conn
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,30), dyn1.Dynapse1SynType.AMPA)
        net_gen.remove_connection(Neuron(2,0,10), Neuron(0,0,30), dyn1.Dynapse1SynType.AMPA)
        print("WRONG remove nonexisting conn pass")
    except Exception as e:
        print(e)

    try:
        print("--------------- correct remove existing conn ---------------")
        net_gen.print_network()
        net_gen.remove_connection(Neuron(0,0,10), Neuron(0,0,30), dyn1.Dynapse1SynType.AMPA)
        net_gen.print_network()
        print("correct remove existing conn pass")
    except Exception as e:
        print(e)

    try:
        print("--------------- WRONG Aliasing 1.1: same post, pre in different (Dynapse1/spikeGen) chips with different weight ---------------")
        # Aliasing 1.1: same post, pre in different (Dynapse1/spikeGen) chips with different weight
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,20), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,20), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(0,0,10,is_spikegen), Neuron(0,0,20), dyn1.Dynapse1SynType.AMPA)
        new_config = net_gen.make_dynapse1_configuration()
        print("try 3 pass")
    except Exception as e:
        print(e)

    try:
        print("--------------- WRONG Aliasing 1.2: same post, pre in different Dynapse1 chips with different weight ---------------")
        # Aliasing 1.2: same post, pre in different Dynapse1 chips with different weight
        net_gen.clear_network()
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,20), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,20), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(1,0,10), Neuron(0,0,20), dyn1.Dynapse1SynType.AMPA)
        new_config = net_gen.make_dynapse1_configuration()
        print("try 4 pass")
    except Exception as e:
        print(e)

    try:
        print("--------------- WRONG Aliasing 2: different post neurons in the same core, receive different pre with same pre_tag ---------------")
        # Aliasing 2: different post neurons in the same core, receive different pre with same pre_tag
        net_gen.clear_network()
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,20), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(2,0,10), Neuron(0,0,30), dyn1.Dynapse1SynType.AMPA)
        new_config = net_gen.make_dynapse1_configuration()
        print("try 5 pass")

    except Exception as e:
        print(e)

    try:
        print("--------------- WRONG out of cams ---------------")
        # out of cams
        net_gen.clear_network()
        for i in range(MAX_NUM_CAMS + 1):
            net_gen.add_connection(Neuron(0,0,i+10), Neuron(0,0,20), dyn1.Dynapse1SynType.AMPA)
        new_config = net_gen.make_dynapse1_configuration()
        print("try 6 pass")

    except Exception as e:
        print(e)

    try:
        print("--------------- correct max cams ---------------")
        # max cams
        net_gen.clear_network()
        for i in range(MAX_NUM_CAMS):
            net_gen.add_connection(Neuron(0,0,i+10), Neuron(0,0,20), dyn1.Dynapse1SynType.AMPA)
        new_config = net_gen.make_dynapse1_configuration()
        print("Max cams try pass")
    except Exception as e:
        print("Max cams try", e)

    try:
        print("--------------- correct cam reuse ---------------")
        # Warning only: cam reuse
        net_gen.clear_network()
        net_gen.add_connection(Neuron(2,0,10), Neuron(0,0,30), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,30), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,50), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(2,0,10), Neuron(0,0,50), dyn1.Dynapse1SynType.AMPA)
        new_config = net_gen.make_dynapse1_configuration()
        print("cam reuse, weight>1 try pass")
    except Exception as e:
        print(e)

    try:
        print("--------------- WRONG cam reuse + aliasing ---------------")
        # ERROR
        net_gen.clear_network()
        net_gen.add_connection(Neuron(2,0,10), Neuron(0,0,30), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,30), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(3,0,10), Neuron(0,0,50), dyn1.Dynapse1SynType.AMPA)
        net_gen.add_connection(Neuron(2,0,10), Neuron(0,0,50), dyn1.Dynapse1SynType.AMPA)
        new_config = net_gen.make_dynapse1_configuration()
        print("cam reuse + aliasing try pass")
    except Exception as e:
        print(e)

    # build a network
    net_gen.clear_network()

    neuron_ids = [(0,0,10), (0,0,30), (0,2,60), (1,1,60), (3,1,107), (2,1,107), (2,3,152)]
    global_ids = ut.get_global_id_list(neuron_ids)
    # global_ids = [nid[2]+nid[1]*NEURONS_PER_CORE+nid[0]*NEURONS_PER_CHIP\
    #                 for nid in neuron_ids]

    net_gen.add_connection(Neuron(0,1,66,is_spikegen), Neuron(0,0,10), dyn1.Dynapse1SynType.AMPA)
    # check sram of Neuron(0,0,10)
    net_gen.add_connection(Neuron(0,0,10), Neuron(0,0,30), dyn1.Dynapse1SynType.AMPA)
    net_gen.add_connection(Neuron(0,0,10), Neuron(0,2,60), dyn1.Dynapse1SynType.NMDA)
    net_gen.add_connection(Neuron(0,0,10), Neuron(1,1,60), dyn1.Dynapse1SynType.GABA_A)
    # check cam of Neuron(2,3,152)
    net_gen.add_connection(Neuron(3,1,107), Neuron(2,3,152), dyn1.Dynapse1SynType.GABA_B)
    net_gen.add_connection(Neuron(2,1,107), Neuron(2,3,152), dyn1.Dynapse1SynType.GABA_B)
    net_gen.add_connection(Neuron(3,1,107), Neuron(2,3,152), dyn1.Dynapse1SynType.GABA_B)
    net_gen.add_connection(Neuron(2,1,107), Neuron(2,3,152), dyn1.Dynapse1SynType.GABA_B)

    # print the network
    net_gen.print_network()

    # make a dynapse1config using the network
    new_config = net_gen.make_dynapse1_configuration()

    # print cam and sram of the above neurons
    for i in range(len(global_ids)):
        nid = global_ids[i]
        neuron = ut.get_neuron_from_config(new_config, nid)
        print("------------Neuron", neuron_ids[i],"------------")
        print("Cams:")
        ut.print_neuron_synapses(neuron, range(4))
        print("Srams:")
        ut.print_neuron_destinations(neuron)

    device_name = "dynapse1"
    store, gui_process = ut.open_dynapse1(device_name)

    # get the handle of the device
    model = getattr(store, device_name)
    # model = store.dynapse1

    print("get dynapse1 model")
    # get the interface api
    api = model.get_dynapse1_api()
    print("get dynapse1 api")

    # apply the config
    model.apply_configuration(new_config)

    # check the config using get_config
    config = model.get_configuration()

    # print cam and sram of the above neurons
    for i in range(len(global_ids)):
        nid = global_ids[i]
        neuron = ut.get_neuron_from_config(config, nid)
        print("------------Neuron", neuron_ids[i],"------------")
        print("Cams:")
        ut.print_neuron_synapses(neuron, range(4))
        print("Srams:")
        ut.print_neuron_destinations(neuron)

    # net_gen.print_network()

    # samna.device_node.DeviceController.close_device(device_name)
    ut.close_dynapse1(store, device_name, gui_process)