# DiffAudit Analysis and Dataset

## Analysis

This folder contains scripts to analyze data flows observed in our network traffic dataset. If you have obtained our dataset (see `DiffAudit/README.md`), you can use this script to output results as we discuss in the paper, as it is specific to the services we audited in this study.

Once you have obtained our dataset, you only need to copy all seven of the JSON files contained in `all_data_flows.zip` into `data_flows/inter_data_files` (be sure not to override any previous "labeled_data_dict..." files if you ran the network traffic/data flow post-processing pipeline on your own dataset). Then, run the following script:

```
$ cd analysis
$ python3 analysis_pipeline.py
```

The script `analysis_pipeline.py` will output the following results, through both generated files and in the terminal output:
- Unique data flows observed per service and age/trace group, organized based on the level-2 ontology data type categories (Section 4.1, Table 4 in the paper)
- Data linkability results (Section 4.2, used to create Figures 3, 4, and 5)
- Statistics about domains and data types observed across the entire dataset (discussed in Sections 3 and 4)
- JSON files with all the unique data flows per service and per trace category (already provided in the dataset release)
- JSON files with the data linkability results separated per service and per trace category (already provided in the dataset release)

## Dataset Details

We released the dataset of observed data flows in our study for reproducibility and other research usages. Please visit the [dataset page](https://athinagroup.eng.uci.edu/childrens-privacy/) to request access to the dataset. See details regarding the dataset contents below.

### Data Flows

**File:** `all_data_flows.zip`

The paper analyzed data flows observed from network traffic across popular mobile apps and websites for children and adolescents. This zip file contains six JSON files with network trace data flows across the mobile and website platforms studied, and one JSON file with domain mapping data used to analyze destinations. For example, `labeled_data_dict_slds_with_owner_tuple-website_logged_in_trace.json` contains all the data flows across all the websites studied for the logged-in trace only. 

Within each file beginning with "labeled_data_dict", you will find the data flow tuples per service/age category for the account creation and logged-in trace files and per service only for the logged-out trace files. The data flows contain the following information in this order: SLD, organization that owns the domain, first/third party labeling, the data type category corresponding to our ontology, ATS flag (1 means it is an ATS, 0 otherwise), the post-processed key from the key-value pairs in the traffic, and the FQDN. The data flows per service and trace category (next section) provide a more readable version of these data. 

Additionally, the file `data_flow_domain_mapping.json` contains the domain mapping information extracted from the DuckDuckGo Tracker Radar Dataset and whois at the time this study was conducted, as described in the paper.

### Data Flows per Service and Trace Category

**File:** `data_flows_per_service_and_trace.zip`

This zip file contains JSON files with the unique data flows observed separated by service and trace category. For example, `Duolingo_child-unique_data_flows_dict.json` contains the unique data flows observed for the child-specific traces for the service Duolingo. Each JSON file contains the unique data flows, with random unique strings as keys to differentiate them, with the data flow information labeled in the key-value pairs.

### Data Linkability per Service and Trace Category

**File:** `data_linkability_per_service_and_trace.zip`

The paper analyzed data linkability among the data flows observed. This zip file contains JSON files with the data linkability results separated by service and trace category. For example, `Duolingo_child-data_linkability_destinations_dict.json` contains the data linkability information about the child-specific traces for the Duolingo service. Each JSON file contains data linkability information by SLDs. For each SLD, you'll find the data type categories corresponding from our ontology that were shared with that domain, flags to indicate whether data types from the identifier and personal information categories were observed among those data types shared, first/third party information, ATS flag (1 if an ATS, 0 otherwise), and the count of data flows sent to that domain.


