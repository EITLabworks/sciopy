from sciopy import (
    create_prep_directory,
    prepare_all_samples_for_16_el_single,
    extract_potentials_from_sample_n_el_16,
)
from sciopy.sciopy_dataclasses import PreperationConfig

lpath = "measurement_16/"

# Initialise the configuration class object
prep_cnf = PreperationConfig(lpath, "", 0)

# Create the save directory.
prep_cnf = create_prep_directory(prep_cnf)

# Convert all samples from load path to save path.
prepare_all_samples_for_16_el_single(prep_cnf)

# Use the following function if positional data is available:
# prepare_all_samples_for_16_el(prep_cnf)
