import time
import Dynapse1Utils as ut
import utils
from typing import List, Union
import pickle
class DynapseDevice():
	def __init__(self, device_name="my_dynapse1", gui=False, sender_port=12345, receiver_port=12346) -> None:
		self.device_name = device_name
		self.store = ut.open_dynapse1(device_name, gui, sender_port, receiver_port)
		self.model = getattr(self.store, device_name)
	
	def close(self):
		ut.close_dynapse1(self.store, self.device_name)

	def monitor_neurons(self, chips: Union[int,List[int]], cores: Union[int,List[int]], ids: List[int]):
		monitored_global_neuron_ids = [ut.get_global_id(chip, core, id) for chip,core,id in utils.zip_lists_or_ints(chips,cores,ids)]
		graph, filter_node, sink_node = ut.create_neuron_select_graph(self.model, monitored_global_neuron_ids)
		self.graph = graph
		self.filter_node = filter_node
		self.sink_node = sink_node

	def monitor_neuron(self, chip: int, core: int, id: int) -> None:
		monitored_global_neuron_id = ut.get_global_id(chip, core, id)
		graph, filter_node, sink_node = ut.create_neuron_select_graph(self.model, [monitored_global_neuron_id])
		self.graph = graph
		self.filter_node = filter_node
		self.sink_node = sink_node

	def get_poisson_spikegen(self, rate: int, chip: int, core: int, id: int):
		return PoissonGenerator(self.model, rate, chip, core, id)

	def get_poisson_spikegens(self, rates: Union[int,List[int]], chips: Union[int,List[int]], cores: Union[int,List[int]], ids: List[int]):
		return PoissonGeneratorGroup(self.model, rates, chips, cores, ids)

	def start_graph(self) -> None:
		self.graph.start()

	def stop_graph(self) -> None:
		self.graph.stop()

	def run_simulation(self, duration: float):
		# clear the output buffer
		self.sink_node.get_buf()
		# sleep for duration
		time.sleep(duration)
		# get the events accumulated during the experiment
		events = self.sink_node.get_buf()
		return [Spike(ut.get_global_id(event.chip_id, event.core_id, event.neuron_id), event.timestamp) for event in events]

class PoissonGenerator():
	def __init__(self, model, rate: int, chip: int, core: int, id: int) -> None:
		self.id = ut.get_global_id(chip, core, id)
		self.poisson_gen = model.get_poisson_gen()
		self.poisson_gen.set_chip_id(chip)
		self.poisson_gen.write_poisson_rate_hz(self.id, int(rate))

	def set_rate(self, rate: int) -> None:
		self.poisson_gen.write_poisson_rate_hz(self.id, rate)

	def start(self) -> None:
		self.poisson_gen.start()

	def stop(self) -> None:
		self.poisson_gen.stop()

class PoissonGeneratorGroup():
	def __init__(self, model, rates: Union[int,List[int]], chips: Union[int,List[int]], cores: Union[int,List[int]], ids: List[int]) -> None:
		self.poisson_gens = [PoissonGenerator(model,rate,chip,core,id) for chip,core,id,rate in utils.zip_lists_or_ints(chips,cores,ids,rates)]

	def set_rates(self, rates: List[int]) -> None:
		for poisson_gen, rate in zip(self.poisson_gens, rates):
			poisson_gen.set_rate(rate)

	def start(self) -> None:
		self.poisson_gens[0].start()

	def stop(self) -> None:
		self.poisson_gens[0].stop()

class Spike():
	def __init__(self, id: int, timestamp: int) -> None:
		self.id = id
		self.timestamp = timestamp

	def __str__(self) -> str:
		return f'[{self.timestamp},{self.id}]'