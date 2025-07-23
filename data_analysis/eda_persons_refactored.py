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

from ISWCBestPaper.data_analysis.person_management import PersonManagement
from ISWCBestPaper.data_analysis.visualize_utils import plot_heatmaps, plot_grouped_histograms


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
    container = defaultdict(StatsContainer)
    counter = 0
    for country in tqdm(country_data["countries"]):
        income_class = get_country_income_class(country["id"])
        if income_class == "undefined":
            continue
        for person in person_management.get_persons(country["id"]):
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
            gender = "non-binary"
            if not genders:
                continue
            if len(genders) > 1:
                gender = "non-binary"
            elif genders[0] == "Q6581072":
                gender = "female"
            elif genders[0] == "Q6581097":
                gender = "male"
            decade = year_to_decade(birth_date)
            update_stats(container[(income_class, gender, decade)], num_references, num_reference_with_url, pid_counter, claim_counter, ref_counter, claim_with_ref_counter)
            counter += 1

    container = {key: asdict(value) for key, value in container.items()}

    pid_counter = []
    claim_counter = []
    claim_with_ref_counter = []
    count_refs = []
    num_refs = []
    num_refs_with_url = []
    ref_counter  = []

    for (income, gender, decade), stats in container.items():
        default_dict = {"person_counter": stats["person_counter"],
                            "income_class": income,
                            "decade": decade,
                            "gender": gender}
        pid_counter.append({**default_dict, **stats["pid_counter"]})
        claim_counter.append({**default_dict, **stats["claim_counter"]})
        claim_with_ref_counter.append({**default_dict, **stats["claim_with_ref_counter"]})
        ref_stats = defaultdict(int)

        flattened_num_refs = defaultdict(int)
        for pid, counter in stats["num_references"].items():
            for num_ref, count in counter.items():
                if num_ref > 0:
                    ref_stats[pid] += count
                flattened_num_refs[(pid, num_ref)] = count
        flattened_num_refs.update({
            (key, None): value for key, value in default_dict.items()
        })
        num_refs.append(flattened_num_refs)

        flattened_num_refs_with_urls = defaultdict(int)
        for pid, counter in stats["num_reference_with_url"].items():
            for num_ref, count in counter.items():
                flattened_num_refs_with_urls[(pid, num_ref)] = count
        flattened_num_refs_with_urls.update({
            (key, None): value for key, value in default_dict.items()
        })
        num_refs_with_url.append(flattened_num_refs_with_urls)

        count_refs.append({**default_dict, **ref_stats})
        flattened_ref_counter = {}
        for pid, counter in stats["ref_counter"].items():
            for ref_pid, count in counter.items():
                flattened_ref_counter[(pid, ref_pid)] = count
        flattened_ref_counter.update({
            (key, None): value for key, value in default_dict.items()
        })

        ref_counter.append(flattened_ref_counter)

    df_pid_counter = pd.DataFrame(pid_counter)
    df_claim_counter = pd.DataFrame(claim_counter)
    df_claim_with_ref_counter = pd.DataFrame(claim_with_ref_counter)
    df_count_refs = pd.DataFrame(count_refs)
    df_ref_counter = pd.DataFrame(ref_counter)
    df_ref_counter.columns = pd.MultiIndex.from_tuples(df_ref_counter.columns)
    df_num_refs = pd.DataFrame(num_refs)
    df_num_refs.columns = pd.MultiIndex.from_tuples(df_num_refs.columns)
    df_num_refs_with_url = pd.DataFrame(num_refs_with_url)
    df_num_refs_with_url.columns = pd.MultiIndex.from_tuples(df_num_refs_with_url.columns)
    # Repalce nan with 0
    df_num_refs = df_num_refs.fillna(0)
    df_ref_counter = df_ref_counter.fillna(0)
    df_count_refs = df_count_refs.fillna(0)
    df_pid_counter = df_pid_counter.fillna(0)
    df_claim_counter = df_claim_counter.fillna(0)
    df_claim_with_ref_counter = df_claim_with_ref_counter.fillna(0)

    df_num_refs.to_pickle(os.path.join("..", "data", "num_refs_detailed.pkl"))
    df_num_refs_with_url.to_pickle(os.path.join("..", "data", "num_refs_with_url_detailed.pkl"))
    df_count_refs.to_pickle(os.path.join("..", "data", "num_refs.pkl"))
    df_ref_counter.to_pickle(os.path.join("..", "data", "num_refs_per_pid.pkl"))
    df_pid_counter.to_pickle(os.path.join("..", "data", "pid_counter.pkl"))
    df_claim_counter.to_pickle(os.path.join("..", "data", "claim_counter.pkl"))
    df_claim_with_ref_counter.to_pickle(os.path.join("..", "data", "claim_with_ref_counter.pkl"))



def process():
    pid_labels = json.load(open("../data/pid_labels_persons.json"))
    reference_labels = json.load(open("../data/pid_labels.json"))
    pid_labels = {**pid_labels, **reference_labels}

    filter_list = {key for key, label in pid_labels.items() if "ID" in label or "ISNI" in label or "category" in label.lower()}

    df_pid_counter = pd.read_pickle(os.path.join("..", "data", "pid_counter.pkl"))
    df_claim_counter = pd.read_pickle(os.path.join("..", "data", "claim_counter.pkl"))
    df_claim_with_ref_counter = pd.read_pickle(os.path.join("..", "data", "claim_with_ref_counter.pkl"))
    df_count_refs = pd.read_pickle(os.path.join("..", "data", "count_refs.pkl"))
    df_ref_counter = pd.read_pickle(os.path.join("..", "data", "ref_counter.pkl"))

    p_cols = df_pid_counter.columns[df_pid_counter.columns.str.startswith('P')]
    most_popular_pids = df_pid_counter[p_cols].sum(axis=0).nlargest(50).index.tolist()
    most_popular_pids = [pid for pid in most_popular_pids if pid in pid_labels]
    most_popular_pids = [pid for pid in most_popular_pids if pid not in filter_list]


    # Accumulate over genders
    df_pid_counter = df_pid_counter.groupby(['income_class', "decade"]).sum()
    df_claim_counter = df_claim_counter.groupby(['income_class', "decade"]).sum()
    df_claim_with_ref_counter = df_claim_with_ref_counter.groupby(['income_class', "decade"]).sum()
    df_count_refs = df_count_refs.groupby(['income_class', "decade"]).sum()
    df_ref_counter = df_ref_counter.groupby([('income_class', None), ('decade', None)]).sum()

    most_popular_ref_pids = df_ref_counter.groupby(level=1, axis=1).sum()
    most_popular_ref_pids = most_popular_ref_pids.sum(axis=0).nlargest(50).index.tolist()

    # Normalize df_ref_counter by the pid_counts in df_claim_counter if PID is matching
    normalized_ref_counter = df_ref_counter.copy()
    ref_normalized_ref_counter = df_ref_counter.copy()
    for pid in df_ref_counter.columns:
        if not pid[0].startswith("P"):
            continue
        if pid[0] in df_claim_counter.columns:
            normalized_ref_counter[pid] = normalized_ref_counter[pid].div(df_claim_counter[pid[0]], axis=0)
        if pid[0] in df_claim_with_ref_counter.columns:
            ref_normalized_ref_counter[pid] = ref_normalized_ref_counter[pid].div(df_claim_with_ref_counter[pid[0]], axis=0)

    normalized_ref_counter = normalized_ref_counter.fillna(0)
    ref_normalized_ref_counter = ref_normalized_ref_counter.fillna(0)

    normalized_ref_counter = normalized_ref_counter.loc[:, normalized_ref_counter.columns.get_level_values(0).isin(most_popular_pids)]
    ref_normalized_ref_counter = ref_normalized_ref_counter.loc[:, ref_normalized_ref_counter.columns.get_level_values(0).isin(most_popular_pids)]

    normalized_ref_counter = normalized_ref_counter.groupby(level=1, axis=1).mean()
    normalized_ref_counter = normalized_ref_counter.loc[:, normalized_ref_counter.columns.isin(most_popular_ref_pids)]

    ref_normalized_ref_counter = ref_normalized_ref_counter.groupby(level=1, axis=1).mean()
    ref_normalized_ref_counter = ref_normalized_ref_counter.loc[:, ref_normalized_ref_counter.columns.isin(most_popular_ref_pids)]

    p_cols = df_pid_counter.columns[df_pid_counter.columns.str.startswith('P')]
    df_pid_counter[p_cols] = df_pid_counter[p_cols].div(df_pid_counter['person_counter'], axis=0)
    # Filter all PID columns out that are not in the most_popular_pids
    df_pid_counter = df_pid_counter.loc[:, df_pid_counter.columns.isin(most_popular_pids)]
    df_pid_counter.fillna(0)


    p_cols = df_count_refs.columns[df_count_refs.columns.str.startswith('P')]
    df_count_refs[p_cols] = df_count_refs[p_cols].div(df_count_refs['person_counter'], axis=0)







if __name__ == "__main__":

    preprocess_data()
    # process()




