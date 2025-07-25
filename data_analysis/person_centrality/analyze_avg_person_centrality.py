import os
import json
import numpy as np
from collections import defaultdict
from pprint import pprint
import pickle

"""This script is used to compute the distribution statistics for person-level in- and out-degrees by income class.
Note that you need to firstly retrieve the person-level degree values from Wikidata first. This is done with the script 'person_centrality.py'.
The values should be stored in country-wise folders within the folder 'data/indegrees_by_country'."""

def get_country_data(country_path):
    indegrees = []
    outdegrees = []
    num_people = 0
    if os.stat(country_path).st_size == 0:
        print(country_path, 'is empty')
        return [], [], 0
    with open(country_path) as f:
        try:
            for line in f:
                entry = json.loads(line)
                indegrees.append(entry['num_incoming_claims'])
                outdegrees.append(entry['num_outgoing_claims'])
                num_people += 1
        except:
            print("Failed for", country_path)
            return [], [], 0
    return indegrees, outdegrees, num_people


def compute_country_statistics(country_path):
    indegrees = []
    outdegrees = []
    num_people = 0
    if os.stat(country_path).st_size == 0:
        print(country_path, 'is empty')
        return None
    with open(country_path) as f:
        try:
            for line in f:
                entry = json.loads(line)
                indegrees.append(entry['num_incoming_claims'])
                outdegrees.append(entry['num_outgoing_claims'])
                num_people += 1
        except:
            print("Failed for", country_path)
            return None
    min_in = min(indegrees)
    max_in = max(indegrees)
    min_out = min(outdegrees)
    max_out = max(outdegrees)
    mean_in = np.mean(indegrees)
    std_in = np.std(indegrees)
    mean_out = np.mean(outdegrees)
    std_out = np.std(outdegrees)
    country_stats = {"indegrees": {"mean": mean_in, "std": std_in, "min": min_in, "max": max_in},
                        "outdegrees": {"mean": mean_out, "std": std_out, "min": min_out, "max": max_out},
                        "num_people": num_people}
    return country_stats


def compute_income_class_statistics(data_dir, out_dir):
    income_class_statistics = defaultdict(dict)
    for income_class in os.listdir(data_dir):
        #indegree_statistics = defaultdict(list)
        #outdegree_statistics = defaultdict(list)
        indegrees_for_income_class = []
        outdegrees_for_income_class = []
        #income_statistics = defaultdict(dict)
        num_countries_for_income_class = 0
        num_people_for_income_class = 0
        for country_json in os.listdir(os.path.join(data_dir, income_class)):
            # country_statistics = compute_country_statistics(os.path.join(data_dir, income_class, country_json))
            indegrees, outdegrees, num_people = get_country_data(os.path.join(data_dir, income_class, country_json))
            indegrees_for_income_class += indegrees
            outdegrees_for_income_class += outdegrees
            num_countries_for_income_class += 1 if num_people > 0 else 0
            num_people_for_income_class += num_people

        income_class_statistics[income_class] = {"indegrees": {"mean": np.mean(indegrees_for_income_class),
                                                               "std": np.std(indegrees_for_income_class),
                                                               "min": min(indegrees_for_income_class),
                                                               "max": max(indegrees_for_income_class)},
                                                 "outdegrees": {"mean": np.mean(outdegrees_for_income_class),
                                                                "std": np.std(outdegrees_for_income_class),
                                                                "min": min(outdegrees_for_income_class),
                                                                "max": max(outdegrees_for_income_class)},
                                                 "num_of_countries": num_countries_for_income_class,
                                                 "num_people": num_people_for_income_class}
        dest_folder = os.path.join(out_dir, "raw_degrees")
        os.makedirs(dest_folder, exist_ok=True)
        with open(os.path.join(dest_folder, f"{income_class}_indegrees.pkl"), 'wb') as pickle_file:
            pickle.dump(indegrees_for_income_class, pickle_file)
        with open(os.path.join(dest_folder, f"{income_class}_outdegrees.pkl"), 'wb') as pickle_file:
            pickle.dump(outdegrees_for_income_class, pickle_file)

    pprint(income_class_statistics)
    with open(os.path.join(out_dir, "income_wise_degrees.json"), "w") as f:
        f.write(json.dumps(income_class_statistics))


if __name__ == "__main__":
    data_dir = os.path.join("..", "..", "data", "indegrees_by_country")
    out_dir = os.path.join("..", "..", "data", "person_level_degrees")
    os.makedirs(out_dir, exist_ok=True)
    compute_income_class_statistics(data_dir, out_dir)
