import os
import json
from tqdm import tqdm
import gzip
import numpy as np
from collections import defaultdict
from pprint import pprint


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
        indegree_statistics = defaultdict(list)
        outdegree_statistics = defaultdict(list)
        income_statistics = defaultdict(dict)
        #list_of_avg_indegrees = []
        #list_of_avg_outdegrees = []
        num_countries = 0
        num_people = 0
        for country_json in os.listdir(os.path.join(data_dir, income_class)):
            country_statistics = compute_country_statistics(os.path.join(data_dir, income_class, country_json))
            if country_statistics is not None:
                income_statistics[country_json.split('.')[0]] = country_statistics
                indegree_statistics["means"].append(country_statistics["indegrees"]["mean"])
                indegree_statistics["mins"].append(country_statistics["indegrees"]["min"])
                indegree_statistics["maxs"].append(country_statistics["indegrees"]["max"])
                outdegree_statistics["means"].append(country_statistics["outdegrees"]["mean"])
                outdegree_statistics["mins"].append(country_statistics["outdegrees"]["min"])
                outdegree_statistics["maxs"].append(country_statistics["outdegrees"]["max"])
                num_countries += 1
                num_people += country_statistics["num_people"]

        income_class_statistics[income_class] = {"indegrees": {"mean": np.mean(indegree_statistics["means"]),
                                                               "std": np.std(indegree_statistics["means"]),
                                                               "min": min(indegree_statistics["means"]),
                                                               "max": max(indegree_statistics["means"]),},
                                                 "outdegrees": {"mean": np.mean(outdegree_statistics["means"]),
                                                                "std": np.std(outdegree_statistics["means"]),
                                                                "min": min(outdegree_statistics["means"]),
                                                                "max": max(outdegree_statistics["means"]),},
                                                 "num_of_countries": num_countries, "num_people": num_people}
        dest_folder = os.path.join(out_dir, "country_stats")
        os.makedirs(dest_folder, exist_ok=True)
        with open(os.path.join(dest_folder, f"{income_class}.json"), "w") as f:
            f.write(json.dumps(income_statistics))

    pprint(income_class_statistics)
    with open(os.path.join(out_dir, "income_wise_degrees.json"), "w") as f:
        f.write(json.dumps(income_class_statistics))


if __name__ == "__main__":
    data_dir = os.path.join("..", "data", "indegrees_by_country")
    out_dir = os.path.join("..", "data", "person_level_degrees")
    os.makedirs(out_dir, exist_ok=True)
    compute_income_class_statistics(data_dir, out_dir)
