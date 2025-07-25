import os
import json
import gzip
import csv
import time
import argparse
import requests
from bs4 import BeautifulSoup
import fitz
from io import BytesIO
import pandas as pd
from tqdm import tqdm
from SPARQLWrapper import SPARQLWrapper, JSON


def get_value_from_wikidata_id(wikidata_id, qid_to_label_map={}):
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="bench-gap")
        if wikidata_id not in qid_to_label_map.keys():
            # Only call API if label has not been retrieved before
            sparql.setQuery(f""" 
                            SELECT  *
                            WHERE
            {{
                            wd:{wikidata_id} rdfs:label ?label .

            }} LIMIT 1
            """)
            sparql.setReturnFormat(JSON)
            query_result = sparql.query().convert()
            try:
                value = query_result["results"]["bindings"][0]["label"]["value"]
                language = query_result["results"]["bindings"][0]["label"]["xml:lang"]
                return_dict = {"text": value, "language": language}
            except:
                print(wikidata_id, query_result)
                return None, qid_to_label_map
            qid_to_label_map[wikidata_id] = return_dict
            return return_dict, qid_to_label_map
        else:
            return qid_to_label_map[wikidata_id], qid_to_label_map
        
def get_predictae_value_from_wikidata_id(wikidata_id, pid_to_label_map={}):
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="bench-gap")
        if wikidata_id not in pid_to_label_map.keys():
            # Only call API if label has not been retrieved before
            sparql.setQuery(f""" 
                            SELECT  ?label
                            WHERE
            {{
                            wd:{wikidata_id} rdfs:label ?label . FILTER (lang(?label) = 'en') 

            }} LIMIT 1
            """)
            sparql.setReturnFormat(JSON)
            query_result = sparql.query().convert()
            try:
                value = query_result["results"]["bindings"][0]["label"]["value"]
                language = query_result["results"]["bindings"][0]["label"]["xml:lang"]
                return_dict = {"text": value, "language": language}
            except:
                print(wikidata_id, query_result)
                return None, pid_to_label_map
            pid_to_label_map[wikidata_id] = return_dict
            return return_dict, pid_to_label_map
        else:
            return pid_to_label_map[wikidata_id], pid_to_label_map

def parse_triples_from_country_data(country_data, args, out_dir="data"):
    counter = 0
    skipped_novalue_objects = 0
    qid_to_label_map = {}

    filename = 'triples_values.tsv' if args.use_values else 'triples.tsv'

    with open(os.path.join(out_dir, filename), 'wt') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        last_tuple = ["", "", "", ""]
        for country in country_data["countries"]:
            subject = country["label"] if args.use_values else country["id"]
            for claim in country["outgoing_claims"].keys():
                # Skip demonym claims
                if claim == "P1549":
                    continue
                predicate = country_data["pid_labels"][claim] if args.use_values else claim
                for tail in country["outgoing_claims"][claim]:
                    if "datavalue" in tail["mainsnak"]:
                        # skip entries with "novalue" or "somevalue", i.e. not further specified info
                        tail_object = tail["mainsnak"]["datavalue"]["value"]
                    else:
                        skipped_novalue_objects += 1
                        continue
                    if "entity-type" in tail_object and tail_object["entity-type"] == "item":
                        tail_object = tail_object["id"]
                        if args.use_values:
                            if tail_object in country_data["qid_labels"]:
                                tail_object = country_data["qid_labels"][tail_object]
                            else:
                                tail_object, qid_to_label_map = get_value_from_wikidata_id(tail_object,
                                                                                           qid_to_label_map)
                                if tail_object is None:
                                    skipped_novalue_objects += 1
                                    continue
                    if "qualifiers" in tail:
                        for qualifier in tail["qualifiers"]:
                            if tail["qualifiers"][qualifier][0]["datatype"] == "time":
                                if "datavalue" in tail["qualifiers"][qualifier][0]:
                                    # skip entries with "novalue" or "somevalue", i.e. not further specified info
                                    time = tail["qualifiers"][qualifier][0]["datavalue"]["value"]["time"].split("-")[0][1:]
                                else:
                                    time = "NaN"
                            else:
                                time = "NaN"

                            new_tuple = [subject, predicate, tail_object, time]
                            if new_tuple != last_tuple:
                                # prevent duplicates
                                tsv_writer.writerow([subject, predicate, tail_object, time])
                                last_tuple = new_tuple
                                counter += 1
                    if args.urls and "references" in tail:
                        for reference in tail["references"][0]['snaks']:
                            if tail["references"][0]['snaks'][reference][0]['datatype'] == "url":
                                evidence_url = tail["references"][0]['snaks'][reference][0]['datavalue']['value']
                                evidence_rel = tail["references"][0]['snaks'][reference][0]['property']

                                new_tuple = [subject, predicate, tail_object, evidence_url, evidence_rel]
                                # print(new_tuple)
                                if new_tuple != last_tuple:
                                    # prevent duplicates
                                    tsv_writer.writerow([subject, predicate, tail_object, evidence_url, evidence_rel])
                                    last_tuple = new_tuple
                                    counter += 1

    print("Written " + str(counter), "to", filename)
    print("Skipped " + str(skipped_novalue_objects), "objects due to no specified value")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--use_values", action="store_true", default=False,
                        help="Use values instead of PIDs and QIDs.")
    parser.add_argument("-v", "--urls", action="store_true", default=False,
                        help="Scrape evidence URLS.")
    args = parser.parse_args()

    with gzip.open(os.path.join("../data", "country_data.json.gz")) as f:
        country_data = json.loads(f.read())
    parse_triples_from_country_data(country_data, args)
