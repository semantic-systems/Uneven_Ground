import os
import json
import gzip
import csv
import argparse
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
        
def parse_triples_from_person_data(person_data, out):
    counter = 0
    skipped_novalue_objects = 0
    qid_to_label_map = {}
    pid_to_label_map={}

    filename = out

    with open(os.path.join(filename), 'wt') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        last_tuple = ["", "", "", ""]
        for person in person_data:
            subject_id = person['id']
            income_class = person['income_class']
            for claim in person['claims']:
                predicate_id = claim['mainsnak']['property']
                if claim['mainsnak']['datatype'] == "wikibase-item" and "datavalue" in claim['mainsnak']:
                    object_id = claim['mainsnak']['datavalue']['value']['id']

                    for reference in claim['references']:
                        for pid in reference['snaks-order']:
                            if reference['snaks'][pid][0]['datatype'] == "url"  and "datavalue" in reference['snaks'][pid][0]:
                                evidence_url = reference['snaks'][pid][0]['datavalue']['value']

                                subject, qid_to_label_map = get_value_from_wikidata_id(subject_id, qid_to_label_map)
                                object, qid_to_label_map = get_value_from_wikidata_id(object_id, qid_to_label_map)
                                predicate, pid_to_label_map = get_predictae_value_from_wikidata_id(predicate_id, pid_to_label_map)

                                new_tuple = [subject, predicate, object, evidence_url, subject_id, predicate_id, object_id, income_class]
                                # print(new_tuple)
                                if new_tuple != last_tuple:
                                    # prevent duplicates
                                    tsv_writer.writerow([subject, predicate, object, evidence_url, subject_id, predicate_id, object_id, income_class])
                                    last_tuple = new_tuple
                                    counter += 1

    print("Written " + str(counter), "to", filename)


if __name__ == '__main__':
    wiki_lines = []
    with gzip.open(os.path.join("../data/person_statements/person_statements_part1.jsonl.gz")) as f:
            for line in f:
                    wiki_lines.append(json.loads(line))
            # wikidata_data = json.loads(f.read())

    parse_triples_from_person_data(wiki_lines, '../data/triples_values_urls.tsv')
