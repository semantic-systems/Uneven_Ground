import os
import json
import pandas as pd
from itertools import chain
from tqdm import tqdm
from SPARQLWrapper import SPARQLWrapper, JSON


def get_triples_all_persons(persons_df):
    triples_all_persons = {}

    for i in range(len(persons_df)):
        person = persons_df.iloc[i]
        qid = person["id"]
        triples_per_person = get_triples_per_person(qid, person)
        triples_all_persons[qid] = triples_per_person
    return triples_all_persons


def get_triples_per_person(qid, person):
    triples_per_person = []
    #try:
    for pid, values in person["claims"].items():
        triples = []
        value_types = []

        for snaks in values:
            value = None
            try:
                a = snaks["mainsnak"]["datavalue"]
            except KeyError:
                print(snaks["mainsnak"])
            if snaks["mainsnak"]["snaktype"] in ["novalue", "somevalue"]:
                continue
            else:
                value_type = snaks["mainsnak"]["datavalue"]["type"]
            if value_type not in value_types:
                value_types.append(value_type)
            if value_type == "string":
                value = snaks["mainsnak"]["datavalue"]["value"]
            if value_type == "time":
                value = snaks["mainsnak"]["datavalue"]["value"]["time"]
            if value_type == "wikibase-entityid":
                value = snaks["mainsnak"]["datavalue"]["value"]["id"]
            if value_type == "quantity":
                value = snaks["mainsnak"]["datavalue"]["value"]["amount"]
            if value is not None:
                triples.append((qid, pid, value))
        triples_per_person.append(triples)
    #except AttributeError:
    #    print(qid)

    return list(chain(*triples_per_person))


def get_all_predicates(all_triples):
    return {triple[1] for triples in all_triples.values() for triple in triples}


def get_value_from_pid(pid, pid_to_label_map={}):
    if pid not in pid_to_label_map.keys():
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="bench-gap")
        sparql.setQuery(f""" 
                        SELECT  *
                        WHERE
        {{
                        wd:{pid} rdfs:label ?label .
        }} 
        """)
        sparql.setReturnFormat(JSON)
        query_result = sparql.query().convert()
        query_result = get_query_result_in_en(query_result)
        try:
            value = query_result["label"]["value"]
            pid_to_label_map[pid] = value
        except:
            print(pid, query_result)
            return None, pid_to_label_map

        return value, pid_to_label_map
    else:
        return pid_to_label_map[pid], pid_to_label_map


def get_query_result_in_en(query_result):
    is_english = False
    for result in query_result["results"]["bindings"]:
        if result["label"]["xml:lang"] == "en":
            is_english = True
        if is_english:
            return result
    if not is_english:
        raise ValueError("Non-english property")


if __name__ == "__main__":
    pid_to_label_map = {}
    os.chdir("/storage/iswc_paper_persons")
    triples_by_country = {}
    predicates_by_country = {}
    for path in tqdm(os.listdir("./")):
        if path.endswith(".jsonl"):
            person_qid = path.split("/")[-1].split("persons_")[-1].split(".jsonl")[0]
            persons = pd.read_json(path, lines=True)
            all_triples = get_triples_all_persons(persons)
            all_predicates = {triple[1] for triples in all_triples.values() for triple in triples}
            triples_by_country[person_qid] = all_triples
            predicates_by_country[person_qid] = all_predicates
            for pid in tqdm(all_predicates):
                _, pid_to_label_map = get_value_from_pid(pid, pid_to_label_map)

            with open(f'/storage/huang/ISWCBestPaper/data_analysis/characters/pid2label_map_{person_qid}.json', 'w') as fp:
                json.dump(pid_to_label_map, fp)

    with open(f'/storage/huang/ISWCBestPaper/data_analysis/characters/triples_by_country.json', 'w') as fp:
        json.dump(triples_by_country, fp)

    with open(f'/storage/huang/ISWCBestPaper/data_analysis/characters/predicates_by_country.json', 'w') as fp:
        json.dump(predicates_by_country, fp)