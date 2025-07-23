import os

import jsonlines

class PersonManagement:
    def __init__(self, main_path: str="persons"):
        self.main_path = main_path
        self.file_dict = self.init_file_dict()

    def init_file_dict(self):
        country_person_file = {}
        for file in os.listdir(self.main_path):
            if file.endswith(".jsonl"):
                country_qid = file.split("_")[1].split(".")[0]
                country_person_file[country_qid] = os.path.join(self.main_path, file)
        return country_person_file

    def get_persons(self, country_qid: str):
        if country_qid not in self.file_dict:
            return []

        with jsonlines.open(self.file_dict[country_qid], "r") as person_file:
            for person in person_file:
                yield person
