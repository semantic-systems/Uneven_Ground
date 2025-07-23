import dataclasses
import datetime
import math

from SPARQLWrapper import SPARQLWrapper, JSON
from matplotlib import pyplot as plt
from tqdm import tqdm
import pandas as pd
from collections import defaultdict
import os
import gzip
import json

from ISWCBestPaper.data_analysis.visualize_utils import plot_heatmaps, plot_grouped_histograms
from person_management import PersonManagement


person_management = PersonManagement("/storage/iswc_paper_persons")

with gzip.open(os.path.join("..", "data", "country_data.json.gz")) as f:
    country_data = json.loads(f.read())

with open("worldbank_country_classification_march2025.json") as f:
    country_income_class_dict = json.load(f)

def get_country_income_class(country_id):
    for income_class in country_income_class_dict.keys():
        if country_id in country_income_class_dict[income_class]:
            return income_class
        else:
            continue
    return "undefined"


@dataclasses.dataclass
class StatsContainer:
    person_counter: int = 0
    pid_counter: dict = dataclasses.field(default_factory=lambda: defaultdict(int))
    claim_counter: dict = dataclasses.field(default_factory=lambda: defaultdict(int))
    num_references: dict = dataclasses.field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    num_reference_with_url: dict = dataclasses.field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    ref_counter: dict = dataclasses.field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    claim_with_ref_counter: dict = dataclasses.field(default_factory=lambda: defaultdict(int))


def update_stats(stats_container, num_references, num_reference_with_url, pid_counter, claim_counter, ref_counter, claim_with_ref_counter):
    stats_container.person_counter += 1
    for claim_pid, count in claim_counter.items():
        stats_container.claim_counter[claim_pid] += count
    for claim_pid, count in pid_counter.items():
        stats_container.pid_counter[claim_pid] += count
    for claim_pid, counts in num_references.items():
        for num_refs, count in counts.items():
            stats_container.num_references[claim_pid][num_refs] += count
    for claim_pid, counts in num_reference_with_url.items():
        for num_refs, count in counts.items():
            stats_container.num_reference_with_url[claim_pid][num_refs] += count
    for claim_pid, count in claim_with_ref_counter.items():
        stats_container.claim_with_ref_counter[claim_pid] += count
    for claim_pid, ref_stats in ref_counter.items():
        for ref_pid, count in ref_stats.items():
            stats_container.ref_counter[claim_pid][ref_pid] += count


def asdict(obj: StatsContainer):
    """
    Convert a StatsContainer object to a dictionary.
    :param obj: StatsContainer object.
    :return: Dictionary representation of the StatsContainer object.
    """
    return {
        "person_counter": obj.person_counter,
        "pid_counter": dict(obj.pid_counter),
        "claim_counter": dict(obj.claim_counter),
        "num_references": {k: dict(v) for k, v in obj.num_references.items()},
        "num_reference_with_url": {k: dict(v) for k, v in obj.num_reference_with_url.items()},
        "ref_counter": {k: dict(v) for k, v in obj.ref_counter.items()},
        "claim_with_ref_counter": dict(obj.claim_with_ref_counter)
    }


def year_to_decade(year):
    """
    Convert a year to the corresponding decade like 1965 to 1960s
    :param year: Year as an integer.
    :return: Decade as an integer.
    """
    return str((year // 10) * 10) + "s"

def get_values(claims):
    values = []
    for claim in claims:
        if "datavalue" not in claim["mainsnak"]:
            object_elem = claim["mainsnak"]["snaktype"]
        else:
            object_elem = claim["mainsnak"]["datavalue"]["value"]["id"]
        values.append(object_elem)
    return values
def preprocess_data():
    cutoff_date = 1925
    by_occupation = defaultdict(StatsContainer)
    by_gender = defaultdict(StatsContainer)
    by_income_class = defaultdict(StatsContainer)
    by_birth_date = defaultdict(StatsContainer)

    for country in tqdm(country_data["countries"]):
        income_class = get_country_income_class(country["id"])
        if income_class == "undefined":
            continue
        for person in person_management.get_persons(country["id"]):
            occupations = []
            genders = []
            num_references = defaultdict(lambda: defaultdict(int))
            num_reference_with_url = defaultdict(lambda: defaultdict(int))
            pid_counter = defaultdict(int)
            claim_counter  = defaultdict(int)
            ref_counter = defaultdict(lambda: defaultdict(int))
            claim_with_ref_counter = defaultdict(int)
            birth_date = None
            for claim_pid, claims in person["claims"].items():
                if claim_pid == "P569":
                    for claim in claims:
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
                if claim_pid == "P21":
                    genders = get_values(claims)
                if claim_pid == "P106":
                    occupations = get_values(claims)
                pid_counter[claim_pid] += 1
                claim_counter[claim_pid] += len(claims)
                for claim in claims:
                    num_ref_with_url = 0
                    if claim.get("references", []):
                        claim_with_ref_counter[claim_pid] += 1
                        ref_pids = set()
                        num_references[claim_pid][len(claim["references"])] += 1
                        for reference in claim["references"]:
                            ref_pids.update(reference["snaks"].keys())
                            for  value in reference["snaks"].values():
                                if value[0].get("datatype") == "url":
                                    num_ref_with_url += 1
                                    break
                        for ref_pid in ref_pids:
                            ref_counter[claim_pid][ref_pid] += 1
                    else:
                        num_references[claim_pid][0] += 1
                    num_reference_with_url[claim_pid][num_ref_with_url] += 1
            if birth_date is None or birth_date < cutoff_date:
                continue
            for occupation in occupations:
                update_stats(by_occupation[occupation], num_references, num_reference_with_url, pid_counter, claim_counter, ref_counter, claim_with_ref_counter)
            for gender in genders:
                update_stats(by_gender[gender], num_references, num_reference_with_url, pid_counter, claim_counter, ref_counter, claim_with_ref_counter)
            update_stats(by_birth_date[year_to_decade(birth_date)], num_references, num_reference_with_url, pid_counter, claim_counter, ref_counter, claim_with_ref_counter)
            update_stats(by_income_class[income_class], num_references, num_reference_with_url, pid_counter, claim_counter, ref_counter, claim_with_ref_counter)

    by_income_class = {key: asdict(value) for key, value in by_income_class.items()}
    by_occupation = {key: asdict(value) for key, value in by_occupation.items()}
    by_gender = {key: asdict(value) for key, value in by_gender.items()}
    by_birth_date = {key: asdict(value) for key, value in by_birth_date.items()}

    json.dump(by_income_class, open("../data/by_income_class.json", "w"), indent=4)
    json.dump(by_occupation, open("../data/by_occupation.json", "w"), indent=4)
    json.dump(by_gender, open("../data/by_gender.json", "w"), indent=4)
    json.dump(by_birth_date, open("../data/by_birth_date.json", "w"), indent=4)

def get_labels(qids: list):
    sparql_wrapper = SPARQLWrapper("https://query.wikidata.org/sparql", agent="bench-gap")
    pid_labels = {}
    for i in tqdm(range(0, len(qids), 32)):
        batch = qids[i:i + 32]
        query = f"""
        SELECT ?pid ?pidLabel WHERE {{
            VALUES ?pid {{ {' '.join([f'wd:{qid}' for qid in batch])} }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
        }}
        """
        sparql_wrapper.setQuery(query)
        sparql_wrapper.setReturnFormat(JSON)
        results = sparql_wrapper.query().convert()

        for result in results["results"]["bindings"]:
            pid = result["pid"]["value"].split("/")[-1]
            label = result["pidLabel"]["value"]
            pid_labels[pid] = label
    return pid_labels
def process():
    pid_labels = json.load(open("../data/pid_labels_persons.json"))
    reference_labels = json.load(open("../data/pid_labels.json"))
    pid_labels = {**pid_labels, **reference_labels}

    filter_list = {key for key, label in pid_labels.items() if "ID" in label or "ISNI" in label or "category" in label.lower()}

    files = [
        "../data/by_income_class.json",
        "../data/by_occupation.json",
        "../data/by_gender.json",
        "../data/by_birth_date.json"
    ]
    output_directories = [
        "../data/by_income_class",
        "../data/by_occupation",
        "../data/by_gender",
        "../data/by_birth_date"
    ]

    for output_directory, file_path in zip(output_directories, files):
        os.makedirs(output_directory, exist_ok=True)

        with open(file_path, 'r') as f:
            stats = json.load(f)

        # Take only top 10 categories by person_counter
        top_stats = dict(sorted(stats.items(), key=lambda x: x[1]["person_counter"], reverse=True)[:10])

        # Relabel keys
        keys = list(top_stats.keys())
        key_labels = get_labels(keys)
        top_stats = {key_labels.get(key, key): value for key, value in top_stats.items()}

        # Plotting
        plot_heatmaps(top_stats, output_directory, pid_labels, filter_list=filter_list)
        plot_grouped_histograms(top_stats, "claim_counter", output_directory, pid_labels, filter_list=filter_list)
        plot_grouped_histograms(top_stats, "pid_counter", output_directory, pid_labels, filter_list=filter_list)


if __name__ == "__main__":
    if os.path.exists("../data/by_income_class.json"):
        print("Data already preprocessed. Skipping...")
    else:
        preprocess_data()
    process()




