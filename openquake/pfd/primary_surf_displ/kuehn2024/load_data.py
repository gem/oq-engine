# openquake/fdha/primary_surf_displ/kuehn2024/load_data.py
"""Load the Kuehn et al. (2024) regression coefficient tables from CSV.

On import this module populates the module-level ``DATA`` dictionary, keyed by
faulting style (``'normal'``, ``'reverse'``, ``'strike-slip'``), with the mean
and full (posterior) coefficient ``DataFrame`` objects shipped in the ``data``
subdirectory.
"""

import os
import warnings

import pandas as pd

# Determine the directory of this load_data.py file
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the 'data' subdirectory
# This assumes the 'data' folder is a direct subfolder of the kuehn2024 module
DATA_DIR = os.path.join(THIS_DIR, 'data')

coefficient_files = {
    'normal': {
        'mean': 'coefficients_mean_NM_powtr.csv',
        'full': 'coefficients_posterior_NM_powtr.csv'
    },
    'reverse': {
        'mean': 'coefficients_mean_REV_powtr.csv',
        'full': 'coefficients_posterior_REV_powtr.csv'
    },
    'strike-slip': {
        'mean': 'coefficients_mean_SS_powtr.csv',
        'full': 'coefficients_posterior_SS_powtr.csv'
    }
}

DATA = {}
for style, files in coefficient_files.items():
    try:
        # Construct full paths for mean and full coefficient files
        mean_filepath = os.path.join(DATA_DIR, files['mean'])
        full_filepath = os.path.join(DATA_DIR, files['full'])

        # Load 'mean' coefficients
        # Check if the 'mean' file exists and is not empty before attempting to read
        mean_coeffs_df = None
        if os.path.exists(mean_filepath) and os.path.getsize(mean_filepath) > 0:
            mean_coeffs_df = pd.read_csv(mean_filepath, index_col=0)
        else:
            warnings.warn(
                f"Mean coefficients file for {style} ({mean_filepath}) is "
                f"missing or empty. Skipping mean coefficients for this style."
            )

        # Load 'full' (posterior) coefficients
        # This file is critical, so we expect it to exist and not be empty
        full_coeffs_df = pd.read_csv(full_filepath, index_col=0)

        DATA[style] = {
            'mean': mean_coeffs_df, # Will be None if mean file was missing/empty
            'full': full_coeffs_df
        }
    except FileNotFoundError:
        # Missing coefficient data is critical; re-raise so the original
        # FileNotFoundError (which carries the offending path) propagates.
        raise
    except pd.errors.EmptyDataError:
        warnings.warn(
            f"The mean coefficients file {mean_filepath} for style {style} is "
            f"empty; loading full (posterior) coefficients only."
        )
        # Attempt to load full even if mean is empty, as full is critical
        full_filepath = os.path.join(DATA_DIR, files['full'])
        full_coeffs_df = pd.read_csv(full_filepath, index_col=0)
        DATA[style] = {
            'mean': None,  # Explicitly set to None if the mean file was empty
            'full': full_coeffs_df
        }