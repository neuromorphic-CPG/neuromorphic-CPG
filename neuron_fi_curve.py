import parameters
import device

# Monitor Frequency-Input curve of a DYNAP-SE1 neuron 
def get_fi_curve(DC_values):
	# open DYNAP-SE1 board to get Dynapse1Model
	dynapse = device.DynapseDevice()
	model = dynapse.model

	# set params
	parameters.set_all_default_params(model)

	# prepare the DC values
	# Note: don't not use too large coarse values (>3). Too many spikes will kill the board..
	# linear DC values, float instead of tuple
	linear_DC_values = []
	# result frequency list
	freqs = []

	chip = 0
	core = 0
	id = 0
	dynapse.monitor_neuron(chip, core, id)

	# duration per DC value
	dynapse.start_graph()

	duration = 1

	for dc in DC_values:
		# set new DC
		linear_dc_value = parameters.set_param(model, parameters.NEURON_DC_INPUT, dc, chip, core)
		linear_DC_values.append(linear_dc_value)

		# get events
		events = dynapse.run_simulation(duration)

		freqs.append(len(events)/duration)
		
	# close Dynapse1
	dynapse.stop_graph()
	dynapse.close()

	return linear_DC_values, freqs

if __name__ == "__main__":
	DC_values = [(0, 0), (0, 50), (0, 100), (0, 200), (1, 50), (1, 100), (1, 200), (2, 50), (2, 100), (2, 200), (3, 50), (3, 100)]

	linear_DC_values, freqs = get_fi_curve(DC_values)

	print(linear_DC_values)
	print(freqs)
	