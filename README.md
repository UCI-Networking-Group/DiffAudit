# DiffAudit: Auditing Privacy Practices of Online Services for Children and Adolescents

This repository hosts the source code for the paper "DiffAudit: Auditing Privacy Practices of Online Services for Children and Adolescents", including:

- Network traffic and data flow post-processing
- GPT-4 data type classification 
- Data flow and data linkability analysis

**Abstract**
> Children's and adolescents' online data privacy are regulated by laws such as the Children's Online Privacy Protection Act (COPPA) and the California Consumer Privacy Act (CCPA). Online services that are directed towards general audiences (i.e., including children, adolescents, and adults) must comply with these laws. In this paper, first, we present DiffAudit, a platform-agnostic privacy auditing methodology for general audience services. DiffAudit performs differential analysis of network traffic data flows to compare data processing practices (i) between child, adolescent, and adult users and (ii) before and after consent is given and user age is disclosed. We also present a data type classification method that utilizes GPT-4 and our data type ontology based on COPPA and CCPA, allowing us to identify considerably more data types than prior work. Second, we apply DiffAudit to a set of popular general audience mobile and web services and observe a rich set of behaviors extracted from over 440K outgoing requests, containing 3,968 unique data types we extracted and classified. We reveal problematic data processing practices prior to consent and age disclosure, lack of differentiation between age-specific data flows, inconsistent privacy policy disclosures, and sharing of linkable data with third parties, including advertising and tracking services.

## Citation

If you create a publication (including web pages, papers published by a third party, and publicly available presentations) using DiffAudit and/or its dataset, please cite the corresponding paper as follows:

```bibtex
@inproceedings{figueira2024diffaudit,
    title     = {{DiffAudit: Auditing Privacy Practices of Online Services for Children and Adolescents}},
    author    = {Figueira, Olivia and Trimananda, Rahmadi and Markopoulou, Athina and Jordan, Scott},
    booktitle = {ACM Internet Measurement Conference (IMC)},
    year      = {2024}
}
```

We also encourage you to provide us (athinagroupreleases@gmail.com) with a link to your publication. We use this information in reports to our funding agencies.

## Using DiffAudit

### Environment Setup

DiffAudit is written in Python and depends on many Python packages. For Python dependencies, please use the following to create a new Python virtual environment before using DiffAudit:

```
$ git clone https://github.com/UCI-Networking-Group/DiffAudit.git
$ cd virtualenv
$ ./python3_venv.sh
$ source python3_venv/bin/activate
```

Invoke the `deactivate` command to deactivate the virtual environment when it is no longer needed.

### Basic Usage

You can use our network traffic and data flow post-processing pipeline to construct and analyze data flows from network traffic you collect on either web or mobile services. The primary pieces of the pipeline include:

1. Network traffic post-processing (`data_flows/process_pcaps.py`).
2. Construction of data flows from post-processed traffic (`data_flows/construct_data_flows.py`). Includes data type classification based on OpenAI's GPT-4 API (`data_flows/gpt_labeling.py`). If you wish to use our GPT-4 data type classification method on your input data, you will need an OpenAI API key. You will have to provide the API key and other details as explained at the top of `data_flows/gpt_labeling.py`.
3. Analysis of data flows observed (`analysis/analysis_pipeline.py`). If you have obtained our dataset (see next section, DiffAudit Dataset), you can use this script to output results as we discuss in the paper, as it is specific to the services we audited in this study.

Please see `data_flows/README.md` for specific details on how to run steps 1 and 2 above, and please see `analysis/README.md` for details on how to run step 3 above.

### DiffAudit Dataset

We released the dataset of observed data flows in our study for reproducibility and other research usages. Please visit the [dataset page](https://athinagroup.eng.uci.edu/projects/childrens-privacy/) to request access to the dataset.

If you have obtained our dataset, you can reproduce the main results from our paper, including the following:
- Data flows observed per service and age/trace group, organized based on the level-2 ontology data type categories (Section 4.1, Table 4 in the paper)
- Data linkability results (Section 4.2, used to create Figures 3, 4, and 5)
- Statistics about domains and data types observed across the entire dataset (discussed in Sections 3 and 4)

Please see `analysis/README.md` for details on both how to run our analysis scripts and the structure/contents of the dataset.

## License

DiffAudit is dual licensed under the [MIT License](https://opensource.org/licenses/MIT) and the [GNU General Public License version 3 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.en.html). You can find the MIT License in the file `LICENSE-MIT.txt` and a copy of the GPLv3 in the file `LICENSE-GPL3.txt`.

The following parts of DiffAudit are covered by GPLv3:

- `DiffAudit/data_flows/extract_from_tshark.py`
- `DiffAudit/data_flows/utils/utils.py`

If those parts get used, GPLv3 applies to all of DiffAudit. Otherwise, you may modify and/or redistribute DiffAudit under either the MIT License or GPLv3.

