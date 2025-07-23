import json
import os
from collections import Counter
from dataclasses import dataclass
from pprint import pprint
import pickle

from gzip import GzipFile
from tqdm import tqdm
import hydra
from hydra.core.config_store import ConfigStore

def write_person_objects_to_txt(wikidata_path, path_to_person_objects_txt):
    with GzipFile(wikidata_path) as gf:
        with open(path_to_person_objects_txt, 'a') as txt_file:
            for ln in tqdm(gf):
                if ln == b'[\n' or ln == b']\n':
                    continue
                if ln.endswith(b',\n'):  # all but the last element
                    obj = json.loads(ln[:-2])
                else:
                    obj = json.loads(ln)

                # try:
                #     instance_of = obj["claims"]["P31"][0]["mainsnak"]["datavalue"]["value"]["id"]
                #     if instance_of != "Q5":  # check if human
                #         continue
                # except:
                #     continue

                # right now actually writing all objects to txt file
                for claims in obj["claims"].values():
                    for claim in claims:
                        if "datavalue" in claim["mainsnak"]:
                            try:
                                person_obj = claim["mainsnak"]["datavalue"]["value"]["id"]
                                txt_file.write(person_obj + "\n")
                            except:
                                continue


def read_person_objects_from_txt(path_to_person_objects_txt):
    with open(path_to_person_objects_txt, 'r') as txt_file:
        person_objects_list = txt_file.read().split("\n")
    return person_objects_list


def count_person_objects(person_objects_list, path_to_person_object_counts):
    obj_counter = Counter(person_objects_list)
    with open(path_to_person_object_counts, 'wb') as pickle_file:
        pickle.dump(obj_counter, pickle_file)


@dataclass
class MyConfig:
    wikidata_path: str = "/storage/wikidata-20250127-all.json.gz"
    output_dir: str = "../data/person_object_counts"
    path_to_person_objects_txt: str = os.path.join(output_dir, "wikidata-20250127-person-objects-new.txt")
    path_to_person_object_counts: str = os.path.join(output_dir, "wikidata-20250127-person-object-counts-new.pkl")
    extract_person_objects: bool = False


cs = ConfigStore.instance()
cs.store(name="conf", node=MyConfig())


@hydra.main(version_base=None, config_name="conf")
def main(cfg: MyConfig) -> None:
    os.makedirs(cfg.output_dir, exist_ok=True)
    if cfg.extract_person_objects:
        print("Extracting all person objects")
        write_person_objects_to_txt(cfg.wikidata_path, cfg.path_to_person_objects_txt)
    print("Counting person objects")
    person_objects = read_person_objects_from_txt(cfg.path_to_person_objects_txt)
    count_person_objects(person_objects, cfg.path_to_person_object_counts)
    print("Complete")


if __name__ == '__main__':
    main()
