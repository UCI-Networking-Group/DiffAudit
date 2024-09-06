#!/usr/bin/python

'''
This script processes and prepares the network traffic for analysis. Basically, the scripts perform the following steps:
1) Merge PCAP and HAR files for each app/website into one file for encrypted traffic and one file for decrypted traffic.
2) Produce JSON files, each for encrypted and decrypted traffic PCAP and HAR files.
3) Produce a unified JSON file in NoMoAds/OVRseen-style.
4) Run the unified JSON file through the filter-list matching script.
5) Finally, produce a CSV file that contains the flow of traffic for further processing.
'''

import argparse
import os
import subprocess
import shutil
import pandas as pd
import pickle
from utils.utils import DIR_DELIMITER
from pandasql import sqldf
from filter_list_checker_mult_dirs import init_rule_checker, fl_matcher_controller
pysqldf = lambda q: sqldf(q, globals())

# Filter list result directory
FL_RESULT_DIR = "filters_matching_results"
INTER_DATA_DIR = 'inter_data_files'

# Filter lists per platform
WEBSITE_FL = [
    "spy.txt",
    "adaway_hosts.txt",
    "AdguardDNS.txt",
    "Admiral.txt",
    "adservers.txt",
    "bigdargon_hostsvn_hosts.txt",
    "disconnect_ads_simple_ad.txt",
    "Easylist.txt",
    "Easyprivacy.txt",
    "fademind_tracking_hosts.txt",
    "fademind_uncheckyads_hosts.txt",
    "firebog_advertising_tracking_abp.txt",
    "firstparty-trackers-hosts.txt",
    "moaab_abp.txt",
    "piholeblocklist_default_abp.txt",
    "Prigent-Ads.txt",
    "serverlist.txt"
]
MOBILE_FL = [
    "spy.txt",
    "adaway_hosts.txt",
    "AdguardDNS.txt",
    "Admiral.txt",
    "adservers.txt",
    "bigdargon_hostsvn_hosts.txt",
    "disconnect_ads_simple_ad.txt",
    "Easylist.txt",
    "Easyprivacy.txt",
    "fademind_tracking_hosts.txt",
    "fademind_uncheckyads_hosts.txt",
    "firebog_advertising_tracking_abp.txt",
    "firstparty-trackers-hosts.txt",
    "moaab_abp.txt",
    "piholeblocklist_default_abp.txt",
    "Prigent-Ads.txt",
    "serverlist.txt"
]
TEMP_OUTPUT_NAME = "temp_output"
CSV_TMP_NAME = "csv_files"
OUTPUTS_DIR_NAME = "outputs"
              


def prepare_filter_lists_dir(platform):
    ## Prepare filter lists to match against packets
    # We assume that all the filter lists are in the folder 'filter_lists' in the current directory
    fl_path = os.path.join(os.getcwd(), 'filter_lists')
    # Platform filter lists path, e.g., mobile_filter_lists
    plat_fl_dir = platform + '_filter_lists'
    plat_fl_path = os.path.join(os.getcwd(), plat_fl_dir)
    if not os.path.exists(plat_fl_path):
        os.makedirs(plat_fl_path)
        print(f"[+] {platform}: Creating a new filter lists directory...")
    else:
        print(f"[.] {platform}: Reusing existing filter lists directory...")
    # Copy all of the necessary filter lists for the platform
    if platform == 'mobile':
        plat_fl = MOBILE_FL
    else:
        plat_fl = WEBSITE_FL
    for fl in plat_fl:
        src_file_path = os.path.join(fl_path, fl)
        dest_file_path = os.path.join(plat_fl_path, fl)
        shutil.copy(src_file_path, dest_file_path)

    # Create filter list matching object for this platform we have prepared the lists for
    fl_save_data_path = INTER_DATA_DIR + os.sep + f"{plat_fl_dir}_save_data.pkl"
    if os.path.isfile(fl_save_data_path):
        print(f"[.] Reusing saved filter lists matching object: {fl_save_data_path}")
        # use this as the filter list fl_matchers instead of creating it again each time
        with open(fl_save_data_path, "rb") as infile:
            fl_matchers = pickle.load(infile)

    else:
        # Prepare a filter list matcher for each filter list
        # List will contain a tuple for each filter list, with the first element being the name and the second element the matcher object
        fl_matchers = []
        for fl_file in os.listdir(plat_fl_dir):
            if "DS_Store" in fl_file:
                continue
            fl_path_file = plat_fl_dir + "/" + fl_file
            ext_start = fl_file.rfind(".")
            if ext_start < 0:
                print("WARNING: skipping filter list file '" + fl_file +
                    "' as the filename does not contain a file extension.")
                continue
            # Name of filter list becomes filename minus file extension
            fl_name = fl_file[0:ext_start]
            if len(fl_file) > 0:
                try:
                    fl_matchers.append((fl_name, init_rule_checker(fl_path_file)))
                except Exception as e:
                    print("Could not parse rule file: %s" % fl_path_file)
                    print(e)

            ## save filter list matcher object to reuse
            with open(fl_save_data_path, "wb") as outfile:
                pickle.dump(fl_matchers, outfile)
    
    return plat_fl_dir, fl_matchers


def csv_processing(csv_platform_apk_dir, apk_dir_paths, apk_dir_tmp, platform, fl_dir, platform_csvs_abs_dir, age_cat_flag):           
    # CSV processing pipeline for web and mobile
    for path in apk_dir_paths:
        # apk_dir_paths_by_apk is list of paths to the age category directories for each apk
        fl_result_dir = os.path.join(path, FL_RESULT_DIR) # ... website > Roblox > 1 > filters_matching_results
        print(f"[+] {platform}: Generating the final CSV file in " + fl_result_dir + "...\n")

        if age_cat_flag == 1:
            age_cat = path.split('/')[-1] # get the age category from the end of the dir string that points to that age category dir
            csv_file_path = os.path.join(fl_result_dir, apk_dir_tmp + "_" + age_cat + ".csv") # ... website > Roblox > 1 > filters_matching_results > Roblox_1.csv
        else:
            csv_file_path = os.path.join(fl_result_dir, apk_dir_tmp + ".csv") # ... website > Roblox > filters_matching_results > Roblox_1.csv

        if platform == 'website':
            ret = subprocess.check_call([
                "python3",
                "compare_results.py", 
                fl_result_dir,
                fl_dir, 
                csv_file_path,
                "--include_http_body",
                "--website"
                ])
        elif platform == 'mobile':
            ret = subprocess.check_call([
                "python3",
                "compare_results.py", 
                fl_result_dir,
                fl_dir, 
                csv_file_path,
                "--include_http_body"
                ])
        print(f"[+] {platform}: Copying the final CSV file into " + csv_platform_apk_dir + "...\n\n")
        shutil.copy(csv_file_path, csv_platform_apk_dir)

        # Add esld (given a csv with hostnames, we get the second level domain and append the information)
        if age_cat_flag == 1:
            csv_with_esld_file = csv_platform_apk_dir + os.sep + apk_dir_tmp + "_" + age_cat + "-with-esld.csv" # i.e. website > Roblox > outputs > Roblox_1-with-esld.csv
        else:
            csv_with_esld_file = csv_platform_apk_dir + os.sep + apk_dir_tmp + "-with-esld.csv" # i.e. website > Roblox > outputs > Roblox-with-esld.csv
        ret = subprocess.check_call(["python3", "append_sld_to_csv.py", csv_file_path, csv_with_esld_file])

        # Read in other CSVs from other apks (i.e., each age profile)
        csv_with_esld_df = pd.read_csv(csv_with_esld_file)
        app_csv_df = pd.read_csv(os.path.join(platform_csvs_abs_dir, "app_metadata.csv"))

        # Add in app title, developer, and developer privacy policy
        csv_with_esld_engine_privacy_developer_df = csv_with_esld_df
        for i, app_csv_row in app_csv_df.iterrows():
            if app_csv_row['app_id'] == apk_dir_tmp: #match app_id to file app
                # add data to csv file for this app
                csv_with_esld_engine_privacy_developer_df['app_title'] = app_csv_row['app_title']
                csv_with_esld_engine_privacy_developer_df['developer_privacy_policy'] = app_csv_row['developer_privacy_policy']
                csv_with_esld_engine_privacy_developer_df['final_status'] = app_csv_row['final_status']
                csv_with_esld_engine_privacy_developer_df['developer'] = app_csv_row['developer']
                csv_with_esld_engine_privacy_developer_df['platform'] = platform
                break

        # Filtering for 'Working' final_status
        csv_with_esld_engine_privacy_developer_df = csv_with_esld_engine_privacy_developer_df[csv_with_esld_engine_privacy_developer_df["final_status"] == "Working"]
        if age_cat_flag == 1:
            csv_with_esld_engine_privacy_developer_file = os.path.join(csv_platform_apk_dir, apk_dir_tmp + "_" + age_cat + "-with-esld-engine-privacy-developer.csv")
        else:
            csv_with_esld_engine_privacy_developer_file = os.path.join(csv_platform_apk_dir, apk_dir_tmp + "-with-esld-engine-privacy-developer.csv")
        csv_with_esld_engine_privacy_developer_df.to_csv(csv_with_esld_engine_privacy_developer_file, index=False)

        # Add party label
        if age_cat_flag == 1:
            csv_with_esld_engine_privacy_developer_party_file = os.path.join(csv_platform_apk_dir,  apk_dir_tmp + "_" + age_cat + "-with-esld-engine-privacy-developer-party.csv")
        else:
            csv_with_esld_engine_privacy_developer_party_file = os.path.join(csv_platform_apk_dir,  apk_dir_tmp + "-with-esld-engine-privacy-developer-party.csv")
        ret = subprocess.check_call(["python3", "hostname_fp_tp_csv_generator.py", csv_with_esld_engine_privacy_developer_file, csv_with_esld_engine_privacy_developer_party_file])

    

def website_har_processor(platform, apk_dir_path, apk_dir, trace_dir, trace_dir_path, reprocess_har_flag):
    # Website-specific pipeline:
    # 1) Convert HAR files for each website to NoMoAds/OVRseen-style JSON and produce a unified JSON file

    apk_dir_path_tuples_to_append = []
    if reprocess_har_flag:
        print(f"[+] {platform}: Converting HAR files and creating a unified JSON file...\n")
        ret = subprocess.check_call(["python3", "convert_har.py",
            "--har_dir", os.path.join(apk_dir_path),
            "--data_out_file_name", os.path.join(apk_dir + "-out-nomoads.json"), #i.e., roblox-out-nomoads.json
            "--trace_select", trace_dir,   ## trace type select dir name, since they have different structures for processing
            "--show_progress",  #uncomment to show the prints/progress bars for convert_har.py
            ]) 

    if trace_dir != "logged_out_trace":
        apk_dir_age_cat_paths = [(apk_dir_path + os.sep + i) for i in os.listdir(apk_dir_path) if i != '.DS_Store' and i != FL_RESULT_DIR and i != CSV_TMP_NAME and i != OUTPUTS_DIR_NAME]
        apk_dir_path_tuples_to_append.append((apk_dir_age_cat_paths, apk_dir))
    else: ##logged out
        apk_dir_trace_path = trace_dir_path + os.sep + apk_dir
        apk_dir_path_tuples_to_append.append(([apk_dir_trace_path], apk_dir))

    return apk_dir_path_tuples_to_append



def mobile_pcap_processor(trace_dir, apk_dir_path, apk_dir, platform, trace_dir_path, reprocess_pcap_flag):
    # The pipeline for all other platforms
    # 1) Merge PCAP files for each app into one PCAP file for encrypted traffic and
    #    one PCAP file for decrypted traffic.
    # 2) Produce tshark JSON files, each for encrypted and decrypted traffic PCAP files
    
    apk_dir_path_tuples_to_append = []
    if trace_dir == "logged_out_trace":
        items = [i for i in os.listdir(apk_dir_path) if i != '.DS_Store' and i != CSV_TMP_NAME and i != OUTPUTS_DIR_NAME]  # apk_dir_path is the directory that holds the pcap files
        apk_dir_trace_path = trace_dir_path + os.sep + apk_dir
        if len(items) != 0:
            if reprocess_pcap_flag:
                print(f"[+] {platform}: Merging decrypted PCAP files and creating a JSON file using tshark...")
                ret = subprocess.check_call(["python3", "merge_cap.py", "-dec", apk_dir_path])

                print(f"\n[+] {platform}: Merging encrypted PCAP files and creating a JSON file using tshark...")
                ret = subprocess.check_call(["python3", "merge_cap.py", "-enc", apk_dir_path])

                # 3) Produce a unified JSON file 
                print(f"[+] {platform}: Creating a unified JSON file...\n")
                outputs_dir_path = os.path.join(apk_dir_path, OUTPUTS_DIR_NAME)
                if not os.path.isdir(outputs_dir_path):
                    print(f"\nMaking new directory: {outputs_dir_path}\n")
                    os.makedirs(outputs_dir_path, exist_ok=True)
                ret = subprocess.check_call(["python3", "extract_from_tshark.py",
                    "--enc_file", os.path.join(apk_dir_path, apk_dir + "-ENC-out.json"),
                    "--dec_file", os.path.join(apk_dir_path, apk_dir + "-DEC-out.json"),
                    "--nomoads_out_file", os.path.join(apk_dir_path, apk_dir + "-out-nomoads.json"),
                    "--kvs_out_file", os.path.join(outputs_dir_path, apk_dir + '-extracted_kv_pairs.json'), ##write the extracted json to the outputs dir
                    "--include_http_body"
                    ])
            apk_dir_path_tuples_to_append.append(([apk_dir_trace_path], apk_dir))
    else:
        ## logged in / full trace - go one dir further to account for age directories
        flag = 0
        age_category_dirs = [i for i in os.listdir(apk_dir_path) if i != '.DS_Store' and i != CSV_TMP_NAME and i != OUTPUTS_DIR_NAME]
        for age_category_dir in age_category_dirs:
            pcap_file_paths = [ (apk_dir_path + os.sep + age_category_dir + os.sep + i) for i in (os.listdir(apk_dir_path + os.sep + age_category_dir)) if ('CRYPTED' in i)]
            pcap_file_dir_path = apk_dir_path + os.sep + age_category_dir
            app_name = pcap_file_dir_path.split('/')[-2]

            print(app_name)

            ## Verify that age profile pcap files match the enclosing directory
            for pcap_path in pcap_file_paths:
                age_cat_slash = pcap_path.split("/")  
                age_cat = age_cat_slash[-1].split("_")[2][-1]
                if age_cat != age_category_dir:
                    print("### ERROR: pcap file age category in file name does not match the enclosing directory age category.")
                    return False
                
            if (len(pcap_file_paths) > 0):  ##may not have files for some yet
                flag = 1 #found something
                if reprocess_pcap_flag: 
                    print(f"[+] {platform}: Merging decrypted PCAP files and creating a JSON file using tshark for {pcap_file_dir_path}...")
                    ret = subprocess.check_call(["python3", "merge_cap.py", "-dec", pcap_file_dir_path])

                    print(f"\n[+] {platform}: Merging encrypted PCAP files and creating a JSON file using tshark for {pcap_file_dir_path}...")
                    ret = subprocess.check_call(["python3", "merge_cap.py", "-enc", pcap_file_dir_path])

                    # 3) Produce a unified JSON file 
                    print(f"[+] {platform}: Creating a unified JSON file...\n")
                    outputs_dir_path = os.path.join(apk_dir_path, OUTPUTS_DIR_NAME)
                    if not os.path.isdir(outputs_dir_path):
                        print(f"\nMaking new directory: {outputs_dir_path}\n")
                        os.makedirs(outputs_dir_path, exist_ok=True)
                    ret = subprocess.check_call(["python3", "extract_from_tshark.py",
                        "--enc_file", os.path.join(pcap_file_dir_path, age_category_dir + "-ENC-out.json"),
                        "--dec_file", os.path.join(pcap_file_dir_path, age_category_dir + '-DEC-out.json'),
                        "--nomoads_out_file", os.path.join(pcap_file_dir_path, app_name + '-' + age_category_dir + "-out-nomoads.json"),
                        "--kvs_out_file", os.path.join(outputs_dir_path, app_name + '-' + age_category_dir + '-extracted_kv_pairs.json'), ##write the extracted json to the outputs dir
                        "--include_http_body"
                        ])
        if flag == 1:
            apk_dir_age_cat_paths = [(apk_dir_path + os.sep + i) for i in os.listdir(apk_dir_path) if i != '.DS_Store' and i != FL_RESULT_DIR and i != CSV_TMP_NAME and i != OUTPUTS_DIR_NAME]
            apk_dir_path_tuples_to_append.append((apk_dir_age_cat_paths, app_name))

    return apk_dir_path_tuples_to_append


def controller(dataset_root_abs_dir, platform_csvs_abs_dir, trace_select, trace_types, select_platform, reprocess_har_flag, reprocess_pcap_flag):
    ## Iterate over APK subdirectories (i.e., website, mobile) that contain the PCAP/HAR files and call the necessary scripts
    for platform in os.listdir(dataset_root_abs_dir):
        
        if platform != select_platform and select_platform != 'all':
            continue

        # Ignore non-APK subdirectories
        if platform == ".DS_Store" or platform == TEMP_OUTPUT_NAME or platform == CSV_TMP_NAME or platform == OUTPUTS_DIR_NAME:
            continue

        apk_dir_path_tuple = []
        app_store_dir = os.path.join(dataset_root_abs_dir, platform)  # i.e., website, mobile
        
        print(f"\n[+] Processing data from: {platform}\n")
        trace_select_dir_name = trace_types[trace_select] ## run the selected trace

        if trace_select_dir_name == "all":
            ## do processing pipeline for all trace types
            for trace_dir in os.listdir(app_store_dir): ##trace_dir is the trace directory names directly under platform directory (full_trace, logged_in_trace, etc.)
                
                if trace_dir == ".DS_Store" or trace_dir == CSV_TMP_NAME or trace_dir == TEMP_OUTPUT_NAME or trace_dir == OUTPUTS_DIR_NAME:
                    continue

                # Get the absolute path
                trace_dir_path = os.path.join(app_store_dir, trace_dir) ## dataset_root_dir / website / full_trace 
                if trace_dir == '__MACOSX' or not os.path.isdir(trace_dir_path):
                    continue
                
                # Go one level down for the app directories within this trace directory
                for apk_dir in os.listdir(trace_dir_path):
                    
                    if apk_dir == ".DS_Store" or apk_dir == CSV_TMP_NAME or apk_dir == TEMP_OUTPUT_NAME or apk_dir == OUTPUTS_DIR_NAME:
                        continue

                    # Get the absolute path
                    apk_dir_path = os.path.join(trace_dir_path, apk_dir) ## dataset_root_dir / website / full_trace / Roblox
                    if apk_dir == '__MACOSX' or not os.path.isdir(apk_dir_path):
                        continue
                    
                    ## Website platform
                    if platform == 'website' and (select_platform == "website" or select_platform == 'all'):    
                        print(f"[+] {platform}: Begin the pipeline for app {apk_dir} and trace {trace_dir}...\n")
                        tuples_to_append = website_har_processor(platform, apk_dir_path, apk_dir, trace_dir, trace_dir_path, reprocess_har_flag)
                        for i in tuples_to_append:
                            apk_dir_path_tuple.append(i)

                    ## Mobile platform
                    elif platform == 'mobile' and (select_platform == 'mobile' or select_platform == 'all'):
                        print(f"[+] {platform}: Begin the pipeline for app {apk_dir} and trace {trace_dir}...\n")
                        tuples_to_append = mobile_pcap_processor(trace_dir, apk_dir_path, apk_dir, platform, trace_dir_path, reprocess_pcap_flag)
                        for i in tuples_to_append:
                            apk_dir_path_tuple.append(i)

                    else:
                        print("### Unexpected platform type. Please add to pipeline.\n")

        elif trace_select_dir_name == "full_trace" or trace_select_dir_name == "logged_in_trace" or trace_select_dir_name == "logged_out_trace":
            for trace_dir in os.listdir(app_store_dir): ##trace_dir is the trace directory names directly under platform directory (full_trace, logged_in_trace, etc.)
                # Get specific trace directory name based on selected trace
                if (trace_select_dir_name not in trace_dir) or trace_dir == ".DS_Store" or trace_dir == CSV_TMP_NAME or trace_dir == TEMP_OUTPUT_NAME or trace_dir == OUTPUTS_DIR_NAME:
                    continue ## skip the incorrect dir

                ## Only process for this specific trace type selected
                elif trace_select_dir_name in trace_dir:
                    # Get the absolute path for the trace
                    trace_dir_path = os.path.join(app_store_dir, trace_dir) ## dataset_root_dir / website / full_trace 
                    if trace_dir == '__MACOSX' or not os.path.isdir(trace_dir_path):
                        continue

                    # Go one level down for the app directories within this trace directory
                    for apk_dir in os.listdir(trace_dir_path):

                        if apk_dir == ".DS_Store" or apk_dir == CSV_TMP_NAME or apk_dir == TEMP_OUTPUT_NAME or apk_dir == OUTPUTS_DIR_NAME:
                            continue

                        # Get the absolute path
                        apk_dir_path = os.path.join(trace_dir_path, apk_dir) ## dataset_root_dir / website / full_trace / Roblox
                        if apk_dir == '__MACOSX' or not os.path.isdir(apk_dir_path):
                            continue
                        
                        ## Website platform
                        if platform == 'website' and (select_platform == 'website' or select_platform == 'all'):
                            print(f"[+] {platform}: Begin the pipeline for app {apk_dir} and trace {trace_dir}...\n")
                            tuples_to_append = website_har_processor(platform, apk_dir_path, apk_dir, trace_dir, trace_dir_path, reprocess_har_flag)
                            for i in tuples_to_append:
                                apk_dir_path_tuple.append(i)

                        ## Mobile platform
                        elif platform == 'mobile' and (select_platform == 'mobile' or select_platform == 'all'):
                            print(f"[+] {platform}: Begin the pipeline for app {apk_dir} and trace {trace_dir}...\n")
                            tuples_to_append = mobile_pcap_processor(trace_select_dir_name, apk_dir_path, apk_dir, platform, trace_dir_path, reprocess_pcap_flag)
                            for i in tuples_to_append:
                                apk_dir_path_tuple.append(i)

                        else:
                            print("### Unexpected platform type. Please add to pipeline.\n")

        # Gather the apk dir paths gathered in previous step into a list
        apk_dir_paths_only = [x for x, _ in apk_dir_path_tuple]

        # 4) Run the unified JSON files (for each age category if applicable) through the filter-list matching script
        print(f"[+] {platform}: Running the unified JSON files and matching the entries against filter lists...")
        fl_dir, fl_matchers = prepare_filter_lists_dir(platform) ## Gathers filter lists needed for this platform and checks if pkl obj has been created already with fl_matchers object
        for apk_dir_paths_by_apk in apk_dir_paths_only: # Apply filter lists to each input, don't open and reopen the object each time
            fl_matcher_controller(apk_dir_paths_by_apk, fl_matchers, FL_RESULT_DIR)
            ## Filter list matching results are saved to platform > apkdir > filters_matching_results > ...
            print(f"[+] {platform}: Filter lists matching results are saved in {FL_RESULT_DIR} for {DIR_DELIMITER.join(apk_dir_paths_by_apk)}...\n")


        # 5) Finally, produce a CSV file that contains the flow of traffic for further processing. This will be a CSV per apk_dir per age category in a platform stored in fl_result_dir. (e.g., ATS analyses, policy analyses, etc.) 
        if trace_select_dir_name == "all":
            ## Process all trace types
            for apk_dir_paths, apk_dir_tmp in apk_dir_path_tuple:
                # Make output directory to hold output for each platform (i.e., website > trace_type > Roblox > outputs)
                current_trace = [i for i in apk_dir_paths[0].split('/') if 'trace' in i][0] # get current trace string
                csv_platform_apk_dir = app_store_dir + os.sep + current_trace + os.sep + apk_dir_tmp + os.sep + OUTPUTS_DIR_NAME
                if not os.path.isdir(csv_platform_apk_dir):
                    print(f"\nMaking new directory: {csv_platform_apk_dir}\n")
                    os.makedirs(csv_platform_apk_dir, exist_ok=True)

                for path in apk_dir_paths:
                    if "logged_out" not in path:
                        csv_processing(csv_platform_apk_dir, apk_dir_paths, apk_dir_tmp, platform, fl_dir, platform_csvs_abs_dir, age_cat_flag=1)
                    else:
                        csv_processing(csv_platform_apk_dir, apk_dir_paths, apk_dir_tmp, platform, fl_dir, platform_csvs_abs_dir, age_cat_flag=0)

        else: ##logged_in, logged_out, full 
            ## Only process the specific selection for trace type
            for apk_dir_paths, apk_dir_tmp in apk_dir_path_tuple:
                current_trace = [i for i in apk_dir_paths[0].split('/') if 'trace' in i][0] # get current trace string
                # only do the selected trace type
                if trace_select_dir_name == current_trace:
                    # Make output directory to hold output for each platform (i.e., website > trace_type > Roblox > outputs)
                    csv_platform_apk_dir = app_store_dir + os.sep + current_trace + os.sep + apk_dir_tmp + os.sep + OUTPUTS_DIR_NAME
                    if not os.path.isdir(csv_platform_apk_dir):
                        print(f"\nMaking new directory: {csv_platform_apk_dir}\n")
                        os.makedirs(csv_platform_apk_dir, exist_ok=True)
                    
                    for path in apk_dir_paths:
                        if "logged_out" not in path:
                            csv_processing(csv_platform_apk_dir, apk_dir_paths, apk_dir_tmp, platform, fl_dir, platform_csvs_abs_dir, age_cat_flag=1)
                        else:
                            csv_processing(csv_platform_apk_dir, apk_dir_paths, apk_dir_tmp, platform, fl_dir, platform_csvs_abs_dir, age_cat_flag=0)



if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Runs the full pipeline for processing PCAP and HAR files, including for website and mobile.')
    ap.add_argument('dataset_root_dir', type=str, help='root directory of dataset')
    ap.add_argument('platform_csvs_dir', type=str, help='directory of csvs about apps and platforms')
    ap.add_argument('--process_har', required=False, action="store_true", help='select whether to reprocess the har files or not (yes or no)')
    ap.add_argument('--process_pcap', required=False, action="store_true", help='select whether to reprocess the pcap files or not (yes or no)')
    ap.add_argument('--select_trace_type', required=True, type=str, help='enter the specific website network trace type you want to process (all, full, logged_in, logged_out)')
    ap.add_argument('--select_platform', required=True, type=str, help='enter the specific platform you want to process (website, mobile, both)')

    args = ap.parse_args()

    # Get the absolute paths
    dataset_root_abs_dir = os.path.abspath(args.dataset_root_dir)
    platform_csvs_abs_dir = os.path.abspath(args.platform_csvs_dir)
    reprocess_har_flag = args.process_har
    reprocess_pcap_flag = args.process_pcap
    select_platform = args.select_platform
    trace_select = args.select_trace_type
    trace_types = {  ## arg string to dir name in website platform
        "all": "all", ##not a dir name
        "full": "full_trace",
        "logged_in": "logged_in_trace",
        "logged_out": "logged_out_trace"
    }

    if not os.path.isdir(INTER_DATA_DIR):
        os.makedirs(INTER_DATA_DIR)

    if select_platform == 'both':
        controller(dataset_root_abs_dir, platform_csvs_abs_dir, trace_select, trace_types, 'website', reprocess_har_flag, reprocess_pcap_flag)
        controller(dataset_root_abs_dir, platform_csvs_abs_dir, trace_select, trace_types, 'mobile', reprocess_har_flag, reprocess_pcap_flag)
    else:
        controller(dataset_root_abs_dir, platform_csvs_abs_dir, trace_select, trace_types, select_platform, reprocess_har_flag, reprocess_pcap_flag)