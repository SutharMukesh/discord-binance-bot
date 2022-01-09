import json
from os import getcwd, path
from jsmin import jsmin


def get_config_file(configfile):
    # Generate a direct file path to the configuration file.
    configfile = path.join(getcwd(), configfile)

    # Throw an error if the configuration file doesn't exist.
    if not path.exists(configfile):
        raise Exception(
            f'Configuration file can not be found at the following location: {configfile}, '
            f'duplicate config.example.yaml and rename it to config.yaml')

    # Open the config file in text-mode for reading.
    with open(configfile, 'r') as config_file_stream:
        # Read and parse the entire config file.
        config_raw_data = config_file_stream.read()
        config_data = json.loads(jsmin(config_raw_data))

    return config_data
