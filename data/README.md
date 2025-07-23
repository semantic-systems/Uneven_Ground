# Structure of country_data.json

The file `country_data.json` contains information about all countries in Wikidata.

```
{
  "countries": ... ,
  "pid_labels" : ...,
  "qid_labels" : ... 
}
```

`pid_labels` is a dictionary assigning to each PID occurring inside `countries` its English label.

`qid_labels` is a dictionary assigning to each QID occurring inside `countries` its English label.

`countries` is a list of all entities in Wikidata which are of type `Q6256`. 
Each element in the list is a dictionary with the following keys:

```
{
  "id": <QID of the country>,
  "label": <English label of the country>,
  "outgoing_claims": ...,
  "incoming_claims": <Dictionary with keys being the PIDs of the incoming claims and values number of claims>,
  "modified": <Date of last modification>
}
```

`outgoing_claims` is a dictionary with keys being the PIDs of the outgoing claims and values being all claims having the PID as the main relation. 
It follows the format of the Wikidata JSON dump. Each claim contains a main claim under `mainsnak`.
Additionally, `qualifiers` might be available as well as `references`.

Example where only a single claim is present for the PID `P38`:
```
"P38": [
          {
            "mainsnak": {
              "snaktype": "value",
              "property": "P38",
              "datavalue": {
                "value": {
                  "entity-type": "item",
                  "numeric-id": 4916,
                  "id": "Q4916"
                },
                "type": "wikibase-entityid"
              },
              "datatype": "wikibase-item"
            },
            "type": "statement",
            "qualifiers": {
              "P580": [
                {
                  "snaktype": "value",
                  "property": "P580",
                  "hash": "95b5f8757e8297bbca8f42b215a79ac44f5bac0a",
                  "datavalue": {
                    "value": {
                      "time": "+1999-01-01T00:00:00Z",
                      "timezone": 0,
                      "before": 0,
                      "after": 0,
                      "precision": 11,
                      "calendarmodel": "http://www.wikidata.org/entity/Q1985727"
                    },
                    "type": "time"
                  },
                  "datatype": "time"
                }
              ]
            },
            "qualifiers-order": [
              "P580"
            ],
            "id": "q31$2AD587B8-A440-438E-A7E0-3F992600D36D",
            "rank": "preferred",
            "references": [
              {
                "hash": "732ec1c90a6f0694c7db9a71bf09fe7f2b674172",
                "snaks": {
                  "P143": [
                    {
                      "snaktype": "value",
                      "property": "P143",
                      "datavalue": {
                        "value": {
                          "entity-type": "item",
                          "numeric-id": 10000,
                          "id": "Q10000"
                        },
                        "type": "wikibase-entityid"
                      },
                      "datatype": "wikibase-item"
                    }
                  ]
                },
                "snaks-order": [
                  "P143"
                ]
              }
            ]
          }
        ],
```

The included claims were filtered in the following way:
- Only claims with a `rank` of `normal or preferred` were included.
- If a claim with a `preferred` rank was present, no `normal`-ranked claim was included.
- All main claims of type `external-id`, `commonsMedia` or `url` were excluded.

All raw data can be found in the folder `data/raw`.
