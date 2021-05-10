import pickle
import matplotlib.pyplot as plt

with open('adaptive_CPG--2021_05_10-10:07:45_AM.txt','rb') as f:
	spikes = pickle.load(f)

plt.plot([spike.timestamp for spike in spikes], [spike.id for spike in spikes],'|')
plt.show()