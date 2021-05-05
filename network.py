from Dynapse1Constants import *
import Dynapse1Utils as ut
import NetworkGenerator
from typing import List
import random

import samna.dynapse1

SYNAPSE_AMPA = samna.dynapse1.Dynapse1SynType.AMPA
SYNAPSE_NMDA = samna.dynapse1.Dynapse1SynType.NMDA
SYNAPSE_GABA_A = samna.dynapse1.Dynapse1SynType.GABA_A
SYNAPSE_GABA_B = samna.dynapse1.Dynapse1SynType.GABA_B

class DynapseNetworkGenerator(NetworkGenerator.NetworkGenerator):
	def __init__(self) -> None:
		super().__init__()

	def get_neuron(self, chip: int, core: int, id: int) -> NetworkGenerator.Neuron:
		return NetworkGenerator.Neuron(chip, core, id)

	def get_spikegen(self, chip: int, core: int, id: int) -> NetworkGenerator.Neuron:
		return NetworkGenerator.Neuron(chip, core, id, True)

	def get_neurons(self, chips: List[int], cores: List[int], ids: List[int]) -> List[NetworkGenerator.Neuron]:
		return [NetworkGenerator.Neuron(chip, core, id) for chip,core,id in zip(chips,cores,ids)]

	def get_spikegens(self, chips: List[int], cores: List[int], ids: List[int]) -> List[NetworkGenerator.Neuron]:
		return [NetworkGenerator.Neuron(chip, core, id, True) for chip,core,id in zip(chips,cores,ids)]

	def add_connection(self, pre: NetworkGenerator.Neuron, post: NetworkGenerator.Neuron, synapse_type, weight: int=1) -> None:
		for _ in range(weight):
			super().add_connection(pre, post, synapse_type)

	def add_connections_one_to_one(self, pres: List[NetworkGenerator.Neuron], posts: List[NetworkGenerator.Neuron], synapse_type, weight: int=1) -> None:
		for pre,post in zip(pres,posts):
			for _ in range(weight):
				self.add_connection(pre, post, synapse_type)

	def add_connections_all_to_all(self, pres: List[NetworkGenerator.Neuron], posts: List[NetworkGenerator.Neuron], synapse_type, weight: int=1, probability: float=1.0) -> None:
		for pre in pres:
			for post in posts:
				for _ in range(weight):
					if random.random() <= probability:
						super().add_connection(pre, post, synapse_type)

	def get_config(self):
		return super().make_dynapse1_configuration()