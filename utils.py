#utils.py - Contains helper functions like loading and saving settings.
import json
import os

SETTINGS_FILE = "settings.json"

import pandas as pd

def load_raw_data(file_path):
    # Read the CSV and automatically interpret the first column as wavelength and the second as reflectance
    data = pd.read_csv(file_path, header=None)
    if data.shape[1] < 2:
        raise ValueError("File must contain at least two columns for wavelength and reflectance.")
    
    data.columns = ['wavelength', 'reflectance']
    return data[['wavelength', 'reflectance']]


def load_settings():
    """Load settings from a JSON file, or create default settings if file doesn't exist."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "dbr_layers": [],
            "metal_layers": [],
            "dbr_period": 1,
            "substrate": "GaSb"
        }

def save_settings(settings):
    """Save current settings to a JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

