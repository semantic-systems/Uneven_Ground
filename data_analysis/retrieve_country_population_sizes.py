import os
import json
import gzip
from collections import defaultdict


"""This script retrieves the population sizes of all countries.
These data are used for reference when analyzing centrality and coverage biases."""


def get_country_income_class(country_id):
    for income_class in country_income_class_dict.keys():
        if country_id in country_income_class_dict[income_class]:
            return income_class
        else:
            continue
    return "undefined"


def parse_triples_from_country_data(country_data, out_dir):
    population_pid = "P1082"
    skipped_novalue_objects = 0

    country_wise_filename = 'population_sizes.json'
    income_class_wise_filename = 'income_class_wise_population_sizes.json'
    population_sizes_by_country = defaultdict(int)
    income_class_wise_population = defaultdict(int)

    for country in country_data["countries"]:
        country_name = country["label"]
        try:
            population_size = int(country["outgoing_claims"][population_pid][0]["mainsnak"]["datavalue"]["value"]["amount"])
            population_sizes_by_country[country_name] = population_size
            income_class_wise_population[get_country_income_class(country["id"])] += population_size
            print(country_name, str(population_size))
        except:
            print("No population size for country", country_name)
            skipped_novalue_objects += 1
            continue

    with open(os.path.join(out_dir, country_wise_filename), 'w') as f:
        json.dump(population_sizes_by_country, f)

    with open(os.path.join(out_dir, income_class_wise_filename), 'w') as f:
        json.dump(income_class_wise_population, f)

    print("Written " + str(len(population_sizes_by_country)), "to", country_wise_filename)
    print("Skipped " + str(skipped_novalue_objects), "objects due to no specified value")


if __name__ == "__main__":
    with gzip.open(os.path.join("..", "data", "country_data.json.gz")) as f:
        country_data = json.loads(f.read())

    with open("worldbank_country_classification_march2025.json") as f:
        country_income_class_dict = json.load(f)

    out_dir = os.path.join("..", "data")
    parse_triples_from_country_data(country_data, out_dir)
