import device
import plotting

import numpy as np
from typing import List

def mean_group_spike_times(spikes: List[device.Spike], ids: List[int]):
	spikes_array = plotting.extract_spikes_group(plotting.convert_spikes_to_array(spikes), ids)
	spikes_array = spikes_array[np.argsort(spikes_array[:,0]),:]
	start = np.argmin([np.std(spikes_array[i:i+len(ids),0]) for i in range(len(ids))])
	return np.mean(np.reshape(spikes_array[start:start+((spikes_array.shape[0]-start)//len(ids))*len(ids),0], (-1,len(ids))), axis=1)

def get_oscillator_frequency(spikes: List[device.Spike], ids: List[int]):
	try:
		spike_times = mean_group_spike_times(spikes, ids)
		return 1000 / np.mean(np.diff(spike_times))
	except:
		return np.nan

def get_coupled_oscillator_frequency_phase(spikes: List[device.Spike], ids1: List[int], ids2: List[int]):
	try:
		spike_times_1 = mean_group_spike_times(spikes, ids1)
		spike_times_2 = mean_group_spike_times(spikes, ids2)

		T1 = np.mean(np.diff(spike_times_1))
		T2 = np.mean(np.diff(spike_times_2))

		min_spikes = min(spike_times_1.shape[0],spike_times_2.shape[0])
		phase = 360 * np.mod(np.mean(spike_times_1[:min_spikes]-spike_times_2[:min_spikes]) / ((T1+T2)/2), 1)

		return 1000/T1, 1000/T2, phase
	except:
		return np.nan, np.nan, np.nan