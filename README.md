# Uneven Ground: Analyzing Representational and Referencing Biases in Wikidata by Country Income Level

## 📁 Project Structure and Data Description

This project includes extracted Wikidata data, graph analysis, and fact-checking results. Below is an overview of the key directories and files:

### 📂 Directory Structure

- `data/`  
  Raw data extracted from Wikidata.

- `data_analysis/`  
  Graph-based analysis of the extracted data.

---

### 📄 Triple Files

Each file contains tuples in the format:  
`[subject, predicate, object, time]`

- `data/triples_values.tsv`  
  Human-readable values using Wikidata labels.

- `data/triples.tsv`  
  Machine-readable format using Wikidata QIDs (e.g., `Q42`) and PIDs (e.g., `P31`).

- `data/triples_urls.tsv`  
  Machine-readable format using Wikidata QIDs (e.g., `Q42`) and PIDs (e.g., `P31`), and URL as refernce.

- `data/triples_values_urls.tsv`  
  Human-readable values using Wikidata labels and URL as refernce.

These files were generated using `sample_triples.py`. Includes outgoing claims for all countries, excluding `"P1549"` (demonym).

Run following command to sample data with human-readable values using Wikidata labels and URLs provided as references.
```python
python sample_triples.py --use_values True --urls True
```


---
### URL validity

URLs provided as reference in Wkidata are checked for validity in `web_scraping.py` and `data/triples_values_urls_verified.csv` generated. The file contains human-readable values using Wikidata labels, URL as refernce and URL web scarping status (e.g., `Valid`, `Redirected`, `Not found`).

---

### ⚠️ Notes

- If no time information is available, the field contains `"NaN"`.
- For non-English object values, the `object` field is a dictionary with:
  ```json
  {
    "text": "Beispiel",
    "language": "de"
  }
