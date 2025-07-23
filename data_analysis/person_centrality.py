from tqdm import tqdm
import os
import json, jsonlines
import gzip
import pickle
from pprint import pprint


from person_management import PersonManagement


person_management = PersonManagement("/storage/iswc_paper_persons")

with gzip.open(os.path.join("..", "data", "country_data.json.gz")) as f:
    country_data = json.loads(f.read())

with open("worldbank_country_classification_march2025.json") as f:
    country_income_class_dict = json.load(f)

with open(os.path.join("..", "data", "person_object_counts", "wikidata-20250127-person-object-counts-new.pkl"), 'rb') as pickle_file:
    person_objects_counter = pickle.load(pickle_file)


def get_country_income_class(country_id):
    for income_class in country_income_class_dict.keys():
        if country_id in country_income_class_dict[income_class]:
            return income_class
        else:
            continue
    return "undefined"


def get_num_incoming_claims(person_id):
    return person_objects_counter[person_id]


def get_values(claims):
    values = []
    for claim in claims:
        if "datavalue" not in claim["mainsnak"]:
            object_elem = claim["mainsnak"]["snaktype"]
        else:
            object_elem = claim["mainsnak"]["datavalue"]["value"]["id"]
        values.append(object_elem)
    return values


def get_finished_countries(path_to_sparql_results, dump_results):
    # check with countries were already finished
    list_of_finished_countries = []
    for income_class in os.listdir(path_to_sparql_results):
        for country_file in os.listdir(os.path.join(path_to_sparql_results, income_class)):
            if country_file.endswith(".jsonl"):
                print(country_file.split(".")[0])
                list_of_finished_countries += [country_file.split(".")[0]]
        for country_file in os.listdir(os.path.join(dump_results, income_class)):
            list_of_finished_countries += [country_file.split(".")[0]]
    print("Num finished countries:", len(list_of_finished_countries))
    return list_of_finished_countries


def get_degrees(out_dir):
    for country in tqdm(country_data["countries"]):
        print("PROCESSING COUNTRY {}".format(country["id"]))
        income_class = get_country_income_class(country["id"])
        if income_class == "undefined":
            continue
        class_dir = os.path.join(out_dir, income_class)
        os.makedirs(class_dir, exist_ok=True)

        with jsonlines.open(os.path.join(class_dir, f"{country['id']}.jsonl"), 'w') as jsonl_file:
            for person in tqdm(person_management.get_persons(country["id"])):
                person_degrees = {}
                person_degrees["person_id"] = person["id"]
                person_degrees["birth_date"] = None
                person_degrees["genders"] = []
                person_degrees["occupations"] = []
                person_degrees["num_outgoing_claims"] = 0
                person_degrees["num_incoming_claims"] = 0

                for claim_pid, claims in person["claims"].items():
                    if claim_pid == "P569":
                        for claim in claims:
                            birth_date = None
                            if "datavalue" not in claim["mainsnak"]:
                                continue
                            else:
                                object_elem = claim["mainsnak"]["datavalue"]["value"]["time"]
                                object_elem = int(object_elem[1:5])
                            if birth_date is not None:
                                if object_elem > birth_date:
                                    birth_date = object_elem
                            else:
                                birth_date = object_elem
                            person_degrees["birth_date"] = birth_date
                    if claim_pid == "P21":
                        person_degrees["genders"] = get_values(claims)
                    if claim_pid == "P106":
                        person_degrees["occupations"] = get_values(claims)

                    person_degrees["num_outgoing_claims"] += len(claims)

                person_degrees["num_incoming_claims"] = get_num_incoming_claims(person["id"])
                jsonl_file.write(person_degrees)


if __name__ == "__main__":
    out_dir = os.path.join("..", "data", "indegrees_by_country")
    os.makedirs(out_dir, exist_ok=True)
    get_degrees(out_dir)
