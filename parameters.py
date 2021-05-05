import samna.dynapse1

import Dynapse1Constants

NEURON_GAIN = "IF_THR_N"
NEURON_REFRACTORY_PERIOD = "IF_RFR_N"
NEURON_TIME_CONSTANT_1 = "IF_TAU1_N"
NEURON_TIME_CONSTANT_2 = "IF_TAU2_N"
NEURON_DC_INPUT = "IF_DC_P"

AMPA_TIME_CONSTANT = "NPDPIE_TAU_F_P"
AMPA_GAIN = "NPDPIE_THR_F_P"
AMPA_WEIGHT = "PS_WEIGHT_EXC_F_N"

NMDA_TIME_CONSTANT = "NPDPIE_TAU_S_P"
NMDA_GAIN = "NPDPIE_THR_S_P"
NMDA_WEIGHT = "PS_WEIGHT_EXC_S_N"
NMDA_GATING_THRESHOLD = "IF_NMDA_N"

GABA_A_TIME_CONSTANT = "NPDPII_TAU_F_P"
GABA_A_GAIN = "NPDPII_THR_F_P"
GABA_A_WEIGHT = "PS_WEIGHT_INH_F_N"

GABA_B_TIME_CONSTANT = "NPDPII_TAU_S_P"
GABA_B_GAIN = "NPDPII_THR_S_P"
GABA_B_WEIGHT = "PS_WEIGHT_INH_S_N"

ADAPTATION_TIME_CONSTANT = "IF_AHTAU_N"
ADAPTATION_GAIN = "IF_AHTHR_N"
ADAPTATION_WEIGHT = "IF_AHW_P"
ADAPTATION_SOMETHING = "IF_CASC_N"

SYNAPSE_PULSE_WIDTH = "PULSE_PWLK_P"

VOLTAGE_READOUT_R2R = "R2R_P"
VOLTAGE_READOUT_BUFFER = "IF_BUF_P"

def get_default_params():
	paramGroup = samna.dynapse1.Dynapse1ParameterGroup()
	# THR, gain factor of neurons
	paramGroup.param_map[NEURON_GAIN].coarse_value = 5
	paramGroup.param_map[NEURON_GAIN].fine_value = 80

	# refactory period of neurons
	paramGroup.param_map[NEURON_REFRACTORY_PERIOD].coarse_value = 4
	paramGroup.param_map[NEURON_REFRACTORY_PERIOD].fine_value = 128

	# leakage of neurons
	paramGroup.param_map[NEURON_TIME_CONSTANT_1].coarse_value = 4
	paramGroup.param_map[NEURON_TIME_CONSTANT_1].fine_value = 80

	# turn off tau2
	paramGroup.param_map[NEURON_TIME_CONSTANT_2].coarse_value = 7
	paramGroup.param_map[NEURON_TIME_CONSTANT_2].fine_value = 255

	# turn off DC
	paramGroup.param_map[NEURON_DC_INPUT].coarse_value = 0
	paramGroup.param_map[NEURON_DC_INPUT].fine_value = 0

	# leakage of AMPA
	paramGroup.param_map[AMPA_TIME_CONSTANT].coarse_value = 4
	paramGroup.param_map[AMPA_TIME_CONSTANT].fine_value = 80

	# gain of AMPA
	paramGroup.param_map[AMPA_GAIN].coarse_value = 4
	paramGroup.param_map[AMPA_GAIN].fine_value = 80

	# weight of AMPA
	paramGroup.param_map[AMPA_WEIGHT].coarse_value = 0
	paramGroup.param_map[AMPA_WEIGHT].fine_value = 0

	# leakage of NMDA
	paramGroup.param_map[NMDA_TIME_CONSTANT].coarse_value = 4
	paramGroup.param_map[NMDA_TIME_CONSTANT].fine_value = 80

	# gain of NMDA
	paramGroup.param_map[NMDA_GAIN].coarse_value = 4
	paramGroup.param_map[NMDA_GAIN].fine_value = 80

	# weight of NMDA
	paramGroup.param_map[NMDA_WEIGHT].coarse_value = 0
	paramGroup.param_map[NMDA_WEIGHT].fine_value = 0

	# leakage of GABA_A (shunting)
	paramGroup.param_map[GABA_A_TIME_CONSTANT].coarse_value = 4
	paramGroup.param_map[GABA_A_TIME_CONSTANT].fine_value = 80

	# gain of GABA_A (shunting)
	paramGroup.param_map[GABA_A_GAIN].coarse_value = 4
	paramGroup.param_map[GABA_A_GAIN].fine_value = 80

	# weight of GABA_A (shunting)
	paramGroup.param_map[GABA_A_WEIGHT].coarse_value = 0
	paramGroup.param_map[GABA_A_WEIGHT].fine_value = 0

	# leakage of GABA_B
	paramGroup.param_map[GABA_B_TIME_CONSTANT].coarse_value = 4
	paramGroup.param_map[GABA_B_TIME_CONSTANT].fine_value = 80

	# gain of GABA_B
	paramGroup.param_map[GABA_B_GAIN].coarse_value = 4
	paramGroup.param_map[GABA_B_GAIN].fine_value = 80

	# weight of GABA_B
	paramGroup.param_map[GABA_B_WEIGHT].coarse_value = 0
	paramGroup.param_map[GABA_B_WEIGHT].fine_value = 0

	# other advanced parameters
	paramGroup.param_map[NMDA_GATING_THRESHOLD].coarse_value = 0
	paramGroup.param_map[NMDA_GATING_THRESHOLD].fine_value = 0

	paramGroup.param_map[ADAPTATION_TIME_CONSTANT].coarse_value = 4
	paramGroup.param_map[ADAPTATION_TIME_CONSTANT].fine_value = 80

	paramGroup.param_map[ADAPTATION_GAIN].coarse_value = 0
	paramGroup.param_map[ADAPTATION_GAIN].fine_value = 0

	paramGroup.param_map[ADAPTATION_WEIGHT].coarse_value = 0
	paramGroup.param_map[ADAPTATION_WEIGHT].fine_value = 0

	paramGroup.param_map[ADAPTATION_SOMETHING].coarse_value = 0
	paramGroup.param_map[ADAPTATION_SOMETHING].fine_value = 0

	paramGroup.param_map[SYNAPSE_PULSE_WIDTH].coarse_value = 4
	paramGroup.param_map[SYNAPSE_PULSE_WIDTH].fine_value = 106

	paramGroup.param_map[VOLTAGE_READOUT_R2R].coarse_value = 3
	paramGroup.param_map[VOLTAGE_READOUT_R2R].fine_value = 85

	paramGroup.param_map[VOLTAGE_READOUT_BUFFER].coarse_value = 3
	paramGroup.param_map[VOLTAGE_READOUT_BUFFER].fine_value = 80

	return paramGroup

def set_all_default_params(model):
	param_group = get_default_params()
	for chip in range(Dynapse1Constants.NUM_CHIPS):
		for core in range(Dynapse1Constants.CORES_PER_CHIP):
			model.update_parameter_group(param_group, chip, core)

def set_param(model, param: str, value: tuple, chip: int, core: int) -> int:
	model.update_single_parameter(samna.dynapse1.Dynapse1Parameter(param, value[0], value[1]), chip, core)
	config = model.get_configuration()
	return config.chips[chip].cores[core].parameter_group.get_linear_parameter(param)