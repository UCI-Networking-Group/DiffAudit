# DiffAudit Network Traffic Post-Processing and Data Flow Construction

You can use our network traffic and data flow post-processing pipeline to construct and analyze data flows from network traffic you collect on either web or mobile services. The primary pieces include:

1. Network traffic post-processing (`data_flows/process_pcaps.py`).
2. Construction of data flows (`<data type, destination>`) from post-processed traffic (`data_flows/construct_data_flows.py`). Includes data type classification based on OpenAI's GPT-4 API (`data_flows/gpt_labeling.py`). If you wish to use our GPT-4 data type classification method on your input data, you will need an OpenAI API key. You will have to provide the API key and other details as explained at the top of `data_flows/gpt_labeling.py`.

If you wish to apply steps 1 and 2 of the pipeline to your own network traffic dataset, these scripts expect the following directory structure and contents:

- `data_flows/dataset_root_dir`: This folder should hold your network traffic in the following way to reflect the various age groups and data collection trace types we analyze in this study (note that "full_trace" in the code refers to the account creation trace). Also note that the numbering scheme in the code and directory structure uses 1 for child traces, 2 for adult traces, and 3 for teen traces. Please see the paper for details on our processes for network traffic collection and decryption, including using PCAPdroid, Wireshark, and Chrome Developer Tools.

    ```
    dataset_root_dir
    ├── mobile
    │   ├── full_trace
    │   │    ├── Appname1
    │   │    │   ├── 1           
    │   │    │   │   └── ...    // Put child account creation trace PCAP files for Appname1 here
    │   │    │   ├── 2           
    │   │    │   │   └── ...    // Put adult account creation trace PCAP files for Appname1 here
    │   │    │   └── 3           
    │   │    │       └── ...    // Put teen account creation trace PCAP files for Appname1 here
    │   │    └── Appname2
    │   │        └── ...        // same as above, account creation trace PCAP files for Appname2 for each age group
    │   ├── logged_in_trace
    │   │   ├── Appname1
    │   │   │   └── ...         // same as above, logged-in trace PCAP files for Appname1 for each age group
    │   │   └── Appname2
    │   │       └── ...         // same as above, logged-in trace PCAP files for Appname2 for each age group
    │   └── logged_out_trace
    │       ├── Appname1        // logged-out trace PCAP files for Appname1 (no age sub-folders)
    │       │   └── ...
    │       └── Appname2        // same as above, logged-out trace PCAP files for Appname2 (no age sub-folders)
    │           └── ...
    └── website
        ├── full_trace          // the same structure as the mobile folder above, HAR instead of PCAP
        │   └── ...
        ├── logged_in_trace
        │   └── ...
        └── logged_out_trace
            └── ...
    ```

    
    The folders within each app should contain the HAR and PCAP files for the website and mobile platforms, respectively, and for each trace (account creation, logged-in, and logged-out). The filenames should follow the below format for PCAP and HAR files. For the mobile platform, there should be both the encrypted (from PCAPdroid) and decrypted (post-processed with Wireshark) files.

    Mobile:
    - `DECRYPTED_<appname>_<agenum>_<trace>_PCAPdroid_<datetime>.pcapng`
        - e.g., `DECRYPTED_Duolingo_child1_full_PCAPdroid_01-01-2024-01-01-01.pcapng`
    - `ENCRYPTED_<appname>_<agenum>_<trace>_PCAPdroid_<datetime>.pcap`
        - e.g., `ENCRYPTED_Duolingo_adult2_full_PCAPdroid_01-01-2024-01-01-01.pcap`

    Website:
    - `<appname>_<agenum>_<trace>_<datetime>.har`
        - e.g., `Duolingo_child1_full_01-01-2024-01-01-01.har`, `Duolingo_loggedout_01-01-2024-01-01-01.har`, `Duolingo_teen3_loggedin_01-01-2024-01-01-01.har`, `Duolingo_adult2_loggedin_01-01-2024-01-01-01.har`

    If you have more than one trace file, simply add a number to the trace string to differentiate easily (i.e., full1, full2, loggedin1, loggedin2, etc.). The "datetime" string should contain dashes instead of underscores (e.g., MM-DD-YYYY-HH-MM-SS, MM-DD-YYYY, etc., depending on your tool's output). The "agenum" string should match the age number (i.e., child1, adult2, teen3).

- `data_flows/tracker-radar-main`: To analyze domain owners, we use the [DuckDuckGo Tracker Radar](https://github.com/duckduckgo/tracker-radar) dataset in this paper. You should obtain their latest dataset (e.g., tracker-radar-main/domains/US/) and save it in the folder `data_flows/tracker-radar-main/domains/US/`.

- `data_flows/filter_lists`: To label advertising and tracking services (ATS), we use filter lists from [Firebog](https://firebog.net/). We used lists from their "Advertising" and "Tracking & Telemetry Lists" sections in this work for labeling. The latest filter lists you wish to use should be downloaded and saved in `data_flows/filter_lists` and updated in `data_flows/process_pcaps.py`. Please see `data_flows/process_pcaps.py` for the filter lists used in the paper.

- Update `data_flows/platform_csvs_dir/app_metadata.csv` with the information of the apps and websites you are analyzing. Currently, it has information about the services analyzed in the paper.

- Note that our pipeline has components that are specific to our paper, which focused on six online services (Duolingo, Roblox, Minecraft, TikTok, YouTube, and Quizlet). Specifically, the destination mapping details should be updated if you want to use this pipeline for other websites and apps (see `construct_data_flows.py` and `hostname_fp_tp_csv_generator.py`).

Once you have prepared your directory as instructed above, you can run the scripts as follows for steps 1 and 2 for network traffic post-processing and data flow construction:

1. Run the network traffic post-processing pipeline (`data_flows/process_pcaps.py`) using the following command. Pass the arguments as follows to post-process all trace types and both the web and mobile platforms if you have collected all these traces of network traffic. Otherwise, pass different arguments for your desired trace/platform (e.g., just logged-out trace for websites), as detailed in `data_flows/process_pcaps.py`.

    ```
    $ cd data_flows 
    $ python3 process_pcaps.py dataset_root_dir platform_csvs_dir --process_har --process_pcap --select_trace_type all --select_platform both
    ```

2. Run the data flow construction pipeline (`data_flows/construct_data_flows.py`) using the following command. This script assumes you are processing both web and mobile platforms for all traces. Recall that this script also includes the GPT-4 data type labeling pipeline, so you will need to enter your OpenAI API key if you wish to run it. See `data_flows/gpt_labeling.py` for details.

    ```
    $ python3 construct_data_flows.py
    ```

Once you've run `data_flows/construct_data_flows.py`, you will have JSON files containing all the data flows observed in your network traffic dataset saved in `data_flows/inter_data_files` for each trace type and platform (e.g., ``labeled_data_dict_slds_with_owner_tuple-website_logged_out_trace.json``).

Please note that the scripts in the `analysis` folder are tailored for the data collected and analyzed in our paper. If you wish to run these scripts on your dataset generated after running the above steps, you'll have to adapt those scripts for your use case. These scripts are best suited for reproducing our results using our dataset (see `DiffAudit/README.md` for details on obtaining the dataset).

