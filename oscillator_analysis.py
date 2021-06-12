import device
import plotting

import numpy as np
from typing import List

def get_coupled_oscillator_frequency_phase(spikes: List[device.Spike], ids1: List[int], ids2: List[int]):
	try:
		spikes_array = plotting.convert_spikes_to_array(spikes)
		spikes_array_1 = plotting.extract_spikes_group(spikes_array, ids1)
		spikes_array_1 = spikes_array_1[np.argsort(spikes_array_1[:,0]),:]
		start_1 = np.argmin([np.std(spikes_array_1[i:i+len(ids1),0]) for i in range(len(ids1))])
		spike_times_1 = np.mean(np.reshape(spikes_array_1[start_1:start_1+((spikes_array_1.shape[0]-start_1)//len(ids1))*len(ids1),0], (-1,len(ids1))), axis=1)
		
		spikes_array_2 = plotting.extract_spikes_group(spikes_array, ids2)
		spikes_array_2 = spikes_array_2[np.argsort(spikes_array_2[:,0]),:]
		start_2 = np.argmin([np.std(spikes_array_2[i:i+len(ids2),0]) for i in range(len(ids2))])
		spike_times_2 = np.mean(np.reshape(spikes_array_2[start_2:start_2+((spikes_array_2.shape[0]-start_1)//len(ids2))*len(ids2),0], (-1,len(ids2))), axis=1)

		T1 = np.mean(np.diff(spike_times_1))
		T2 = np.mean(np.diff(spike_times_2))

		min_spikes = min(spike_times_1.shape[0],spike_times_2.shape[0])
		phase = 360 * np.mod(np.mean(spike_times_1[:min_spikes]-spike_times_2[:min_spikes]) / ((T1+T2)/2), 1)

		return 1000/T1, 1000/T2, phase
	except:
		return np.nan, np.nan, np.nan