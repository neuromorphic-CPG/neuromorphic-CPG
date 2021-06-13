import device
import network
import parameters
import utils
import Dynapse1Constants
import numpy as np
from typing import List,Union,Tuple

def get_random_oscillator(dynapse: device.DynapseDevice, size_exc_pop: int, chips: Union[int,List[int]], cores: Union[int,List[int]]):
	neuron_ids = get_oscillator_neuron_ids(size_exc_pop)
	return Oscillator(dynapse, chips, cores, neuron_ids)

def get_random_coupled_oscillator(dynapse: device.DynapseDevice, size_exc_pop: int, chips: Union[int,List[int]], cores: Union[int,List[int]]):
	neuron_ids = get_coupled_oscillator_neuron_ids(size_exc_pop)
	return CoupledOscillator(dynapse, chips, cores, neuron_ids)

def get_oscillator_neuron_ids(size_exc_pop: int) -> Tuple[List[int],List[int]]:
		size_inh_pop = size_exc_pop // 4
		neuron_id_pool = np.random.choice(np.arange(1,Dynapse1Constants.NEURONS_PER_CORE), size_exc_pop+size_inh_pop, False)

		neuron_ids_E = neuron_id_pool[:size_exc_pop]
		neuron_ids_I = neuron_id_pool[-size_inh_pop:]

		return neuron_ids_E, neuron_ids_I

def get_coupled_oscillator_neuron_ids(size_exc_pop: int) -> Tuple[List[int],List[int],List[int],List[int]]:
		size_inh_pop = size_exc_pop // 4
		neuron_id_pool = np.random.choice(np.arange(1,Dynapse1Constants.NEURONS_PER_CORE), 2*(size_exc_pop+size_inh_pop), False)

		neuron_ids_E1 = neuron_id_pool[:size_exc_pop]
		neuron_ids_E2 = neuron_id_pool[size_exc_pop:2*size_exc_pop]
		neuron_ids_I1 = neuron_id_pool[-2*size_inh_pop:-size_inh_pop]
		neuron_ids_I2 = neuron_id_pool[-size_inh_pop:]

		return neuron_ids_E1, neuron_ids_E2, neuron_ids_I1, neuron_ids_I2

class Oscillator:
	def __init__(self, dynapse: device.DynapseDevice, chips: Union[int,List[int]], cores: Union[int,List[int]], ids: Tuple[List[int],List[int]], net_to_append: network.DynapseNetworkGenerator=None) -> None:
		self.neuron_ids_E, self.neuron_ids_I = ids
		((self.chip_E,self.core_E),(self.chip_I,self.core_I)) = utils.zip_lists_or_ints(chips, cores)
		self.dynapse = dynapse
		self.model = dynapse.model

		if net_to_append is None:
			self.net = network.DynapseNetworkGenerator()
		else:
			self.net = net_to_append
		
		self.make_oscillator_network()

	def start(self):
		self.model.apply_configuration(self.net.get_config())
		self.dynapse.monitor_neuron_network(self.neurons_E, self.neurons_I)

	def make_oscillator_network(self):
		self.neurons_E = self.net.get_neurons(self.chip_E, self.core_E, self.neuron_ids_E)
		self.neurons_I = self.net.get_neurons(self.chip_I, self.core_I, self.neuron_ids_I)

		self.net.add_connections_all_to_all(self.neurons_E, self.neurons_E, network.SYNAPSE_AMPA)
		self.net.add_connections_all_to_all(self.neurons_E, self.neurons_I, network.SYNAPSE_AMPA)
		self.net.add_connections_all_to_all(self.neurons_I, self.neurons_E, network.SYNAPSE_GABA_B, weight=4)
	
	def set_default_params(self):
		parameters.set_param(self.model, parameters.AMPA_WEIGHT, (6,40), self.chip_E, self.core_E)
		parameters.set_param(self.model, parameters.GABA_B_WEIGHT, (7,255), self.chip_E, self.core_E)
		parameters.set_param(self.model, parameters.GABA_B_GAIN, (7,255), self.chip_E, self.core_E)

	def set_E_DC_input(self, fine_value: int, coarse_value: int):
		parameters.set_param(self.model, parameters.NEURON_DC_INPUT, (fine_value,coarse_value), self.chip_E, self.core_E)
		
	def set_I_AMPA(self, fine_value: int, coarse_value: int):
		parameters.set_param(self.model, parameters.AMPA_WEIGHT, (fine_value,coarse_value), self.chip_I, self.core_I)

class CoupledOscillator:
	def __init__(self, dynapse: device.DynapseDevice, chips: Union[int,List[int]], cores: Union[int,List[int]], ids: Tuple[List[int],List[int],List[int],List[int]], net_to_append: network.DynapseNetworkGenerator=None) -> None:
		self.neuron_ids_E1, self.neuron_ids_E2, self.neuron_ids_I1, self.neuron_ids_I2 = ids
		((self.chip_E1,self.core_E1),(self.chip_E2,self.core_E2),(self.chip_I,self.core_I)) = utils.zip_lists_or_ints(chips, cores)
		self.dynapse = dynapse
		self.model = dynapse.model

		if net_to_append is None:
			self.net = network.DynapseNetworkGenerator()
		else:
			self.net = net_to_append

		self.oscillator1 = Oscillator(dynapse, [self.chip_E1,self.chip_I], [self.core_E1, self.core_I], (self.neuron_ids_E1,self.neuron_ids_I1), self.net)
		self.oscillator2 = Oscillator(dynapse, [self.chip_E2,self.chip_I], [self.core_E2, self.core_I], (self.neuron_ids_E2,self.neuron_ids_I2), self.net)

	def start(self):
		self.model.apply_configuration(self.net.get_config())
		self.dynapse.monitor_neuron_network(self.oscillator1.neurons_E, self.oscillator2.neurons_E, self.oscillator1.neurons_I, self.oscillator2.neurons_I)

	def set_default_params(self):
		self.oscillator1.set_default_params()
		self.oscillator2.set_default_params()

		parameters.set_param(self.model, parameters.GABA_B_WEIGHT, (7,255), self.chip_I, self.core_I)
		parameters.set_param(self.model, parameters.GABA_B_LEAKAGE, (2,80), self.chip_I, self.core_I)
		parameters.set_param(self.model, parameters.GABA_B_GAIN, (7,255), self.chip_I, self.core_I)

	def set_E1_DC_input(self, fine_value: int, coarse_value: int):
		parameters.set_param(self.model, parameters.NEURON_DC_INPUT, (fine_value,coarse_value), self.chip_E1, self.core_E1)

	def set_E2_DC_input(self, fine_value: int, coarse_value: int):
		parameters.set_param(self.model, parameters.NEURON_DC_INPUT, (fine_value,coarse_value), self.chip_E2, self.core_E2)

	def set_I_AMPA(self, fine_value: int, coarse_value: int):
		parameters.set_param(self.model, parameters.AMPA_WEIGHT, (fine_value,coarse_value), self.chip_I, self.core_I)