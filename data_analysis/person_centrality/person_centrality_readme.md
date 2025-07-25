# Person centrality analysis

Scripts overview:
- `count_person_objects.py` counts all instances of a person entity appearing as a tail entity and stores the counts and respective person objects in a separate `.pkl` file.
- `summarize_in_and_outdegrees.py` summarizes the numbers for incoming and outgoing claims per person entity and stores them in `.jsonl` files in a income_class/country/person_entity folder structure.
- `analyze_avg_person_centrality.py` brings it all together and computes the distributional statistics for person-wise in- and outdegrees, grouped by income class. The results are stored as a dict in a `.json` file. 