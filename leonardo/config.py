#function that get the config.json file and set the parameters in a dictionary and return it
import json

def get_config(experiment_name: str):
    with open('config.json') as json_file:
        data = json.load(json_file)
        return data[experiment_name]

def get_experiment_names():
    with open('config.json') as json_file:
        data = json.load(json_file)
        return list(data.keys())

#function to load a json and return a dictionary
def load_json(file):
    with open(file) as json_file:
        data = json.load(json_file)
        return data
