# Uneven Ground: Analyzing Representational and Referencing Biases in Wikidata by Country Income Level

## Abstract
Although Wikidata has been playing a significant role in semantic web and AI technologies, it is not exempt from limitations regarding its inherent biases. Our work expands upon existing critiques and evaluates differences in centrality, characterization, and evidence-groundedness between countries considered high-, upper-middle-, lower-middle-, and low-income. Our findings indicate that higher-income countries and individuals with respective citizenship are generally more centrally represented in Wikidata. Furthermore, the types of relations used differ, and references are more commonly used for statements for higher-income countries.
Additionally, there are prominent differences in the types of references utilized  across countries with different income levels. Our findings illuminate a previously underexplored facet of bias in Wikidata, adding to concerns regarding its current fitness as a backbone to semantic web and AI technologies meant to serve users across continents and countries. We hope to contribute to a better understanding of Wikidata's limitations to foster awareness and improved representational fairness in the long run.

## Project Structure and Data Description

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
### ✅ URL validity

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
