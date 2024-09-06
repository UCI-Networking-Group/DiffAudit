#!/usr/bin/python

'''
This script constructs data flows from the post-processed network traffic. The script performs the following steps:
1) Extracts unique keys from key-value pairs in the network traffic and post-processes to prepare for classification.
2) Conducts GPT-based classification using OpenAI GPT-4. (requires your API key)
3) Extracts destination information based on domains in traffic.
4) Finally, constructs and produces files with data flows from packets and classified keys
'''

import os
import csv
import sys 
import json
import pickle
import whois
import time
import subprocess
import shutil
from utils import utils

DATASET_ROOT_DIR = 'dataset_root_dir'
TRACKER_RADAR_DIR = 'tracker-radar-main'
INTER_DATA_DIR = 'inter_data_files'
GPT_OUTPUTS_DIR = "gpt_outputs"

JSON_FIELD_KVS = 'kv_pairs'
PLATFORM_NAMES = ['website', 'mobile']
DS_STORE = '.DS_Store'
HOST = 'hostname'  
ESLD = 'second_level_domain'
OUTPUTS_DIR_NAME = "outputs"
FULL_CSV_OUTPUT_NAME = "-with-esld-engine-privacy-developer-party.csv"
PARTY_LABEL = 'party_labels'
ATS_FLAG = "overall_block_decision" 

csv.field_size_limit(sys.maxsize)


def helper_extract(input_csv_file, input_json_file):
    ## Extracts key-value pairs for each trace data file (JSON structures were previously extracted from packet payloads in process_pcaps.py pipeline)
    in_csv_file = open(input_csv_file, 'r')
    csv_reader = csv.DictReader(in_csv_file, delimiter=',', quotechar='"')
    with open(input_json_file, "r") as infile:
        extracted_kv_data = json.load(infile)
    
    # output name for profile category
    out_name = input_csv_file[:-4].split('/')[-1]
    
    # process each row from the input CSV and add the key-value tuples to the new csv
    out_dict = []
    for in_row in csv_reader:
        # payload = in_row[json_keys.http_body]
        pkt_id = in_row[utils.id]
        row = {}
        if utils.all_extracted_kvs in extracted_kv_data[pkt_id].keys():
            row[pkt_id] = {
                HOST: in_row[HOST], 
                utils.dst_ip: in_row[utils.dst_ip],
                PARTY_LABEL: in_row[PARTY_LABEL],
                ESLD: in_row[ESLD],
                JSON_FIELD_KVS: extracted_kv_data[pkt_id][utils.all_extracted_kvs],
                ATS_FLAG: in_row[ATS_FLAG]
            }
            out_dict.append(row)

    in_csv_file.close()
    return out_name, out_dict



def clean_keys(kv_pairs_tuples):
    ## Cleans up punctuation from extracted keys to prepare for labeling
    clean_keys_set = set() 
    for tup in kv_pairs_tuples:
        for i in tup[0]:
            if isinstance(i, list):
                for j in i:
                    if (j != '[]') and (j != '~') and (len(j) > 1):
                        clean_keys_set.add(j)
            elif (i != '[]') and (i != '~') and (len(i) > 1):
                clean_keys_set.add(i)
    return list(clean_keys_set)


def read_from_csvs(platform, trace_select=""):
    ## Reads data from CSV files for specified platform (generated prior from process_pcapspy script)
    traces_dict = {
        "logged_in_trace": DATASET_ROOT_DIR + os.sep + platform + os.sep + "logged_in_trace",
        "logged_out_trace": DATASET_ROOT_DIR + os.sep + platform + os.sep + "logged_out_trace",
        "full_trace": DATASET_ROOT_DIR + os.sep + platform + os.sep + "full_trace",
    }

    all_unique_keys_cross_plat = set()
    all_unique_keys_per_plt = {}
    overall_data_dict = {}
    overall_data_dict_sld = {}

    # process each trace directory
    trace_dir_path = traces_dict[trace_select]
    for app_name in os.listdir(trace_dir_path):      
        if app_name != OUTPUTS_DIR_NAME and app_name != DS_STORE and '.json' not in app_name:
            if not os.path.isdir(trace_dir_path + os.sep + app_name + os.sep + OUTPUTS_DIR_NAME):
                print(f"### ERROR: outputs directory is missing for {app_name}")
            else:
                all_unique_keys_per_plt[app_name] = set()
                print(f"\n[+] Processing {app_name} data...")
                # extract key-value pairs from the http file data in the csv file
                output_file_dir = trace_dir_path + os.sep + app_name + os.sep + OUTPUTS_DIR_NAME
                out_file_dicts = {}
                csv_files_to_extract = [i for i in os.listdir(output_file_dir) if FULL_CSV_OUTPUT_NAME in i]
                for csv_file in csv_files_to_extract:
                    csv_file_path = trace_dir_path + os.sep + app_name + os.sep + OUTPUTS_DIR_NAME + os.sep + csv_file
                    # get the corresponding json file for kv-pairs
                    csv_file_temp = csv_file.split('-')[0]
                    if '_' in csv_file_temp:
                        csv_file_temp = csv_file_temp.replace('_', '-')
                    json_file_name = csv_file_temp + "-extracted_kv_pairs.json"
                    json_file_path = trace_dir_path + os.sep + app_name + os.sep + OUTPUTS_DIR_NAME + os.sep + json_file_name  #ex: Duolingo-1-extracted_kv_pairs.json
                    print(f"[.] Extracting packet data from {csv_file} and {json_file_name}...")
                    out_name, out_dict = helper_extract(csv_file_path, json_file_path)
                    out_file_dicts[out_name] = out_dict

                # process the keys 
                for filename, data in out_file_dicts.items():
                    overall_data_dict[filename] = []
                    overall_data_dict_sld[filename] = []
                    for pkt_id_obj in data:    
                        for k, v in pkt_id_obj.items():  # v has host, dst_ip, party_label, and kv_pairs
                            host = v[HOST]
                            party = v[PARTY_LABEL]
                            kvs = v[JSON_FIELD_KVS]
                            sld = v[ESLD]
                            ats_flag = v[ATS_FLAG]
                            cleaned_keys_list = clean_keys(kvs)
                            new_list = set()
                            for i in cleaned_keys_list:
                                # remove puncutation
                                new_text = i.replace("_", " ")
                                new_text = new_text.replace("-", " ")
                                new_text = new_text.replace("/", " ")
                                new_text = (new_text.strip(" ")).lower()
                                if '.min.js' in new_text or '.css' in new_text or '.png' in new_text or '.jpg' in new_text or '.js' in new_text or '.svg' in new_text or '.com' in new_text or '.net' in new_text:
                                    continue
                                if (not new_text.isnumeric()) and (len(new_text) > 1) and (new_text != '[]'):
                                    all_unique_keys_cross_plat.add(new_text)
                                    all_unique_keys_per_plt[app_name].add(new_text)
                                    new_list.add(new_text)
                            overall_data_dict[filename].append((host, party, list(new_list)))
                            overall_data_dict_sld[filename].append((sld, party, list(new_list), ats_flag, host)) # format: <sld, party, list of keys, ats_flag, HOST>
    return overall_data_dict, all_unique_keys_cross_plat, all_unique_keys_per_plt, overall_data_dict_sld


def count_matches_per_plat_gpt(all_unique_keys_per_plat, GPT_LABELS_FILE):
    ## Count how many data types were classified by GPT per platform using passed in labeled data file 
    ## (with corresponding schema - i.e., merged-avg, merged-max at certain confidence threshold)
    all_unique = set()
    for plat, keys in all_unique_keys_per_plat.items():
        for k in list(keys):
            all_unique.add(k)
    
    with open(INTER_DATA_DIR + os.sep + GPT_LABELS_FILE, "r") as infile:
        data_labels = json.load(infile)
    
    print('')
    total_match_count = 0
    actual_total = 0
    for plat, keys in all_unique_keys_per_plat.items():
        match_count, nomatch_count, total = 0, 0, len(list(keys))
        for k in list(keys):
            if k in data_labels.keys():
                if data_labels[k] != 'Unclear':  
                    match_count += 1
                else:
                    nomatch_count += 1
            else:
                nomatch_count += 1
        if total > 0:
            print(f"{plat} counts matched with ChatGPT: {match_count} / {total} = {match_count/total} ({nomatch_count} no label)")
            total_match_count += match_count
            actual_total += total
    print(f"[.] Total match count with this scheme and confidence threshold (how many were matched in total above 0.8): {total_match_count} / {actual_total}")
    print('')
    


def process_labels_gpt_tuple(overall_data_dict, gpt_labels_file):
    ## Connect the GPT-classified labels back to the data dictionary with destination and party label and create data flow tuple
    # read in labeled data list 
    with open(INTER_DATA_DIR + os.sep + gpt_labels_file, "r") as infile:
        data_labels = json.load(infile)
    labeled_data_dict = {}
    for plt_profile, packets in overall_data_dict.items():
        # k is the age profile for each platform, v is the list of packets for this age profile
        clean_plt_profile_name = plt_profile.replace(FULL_CSV_OUTPUT_NAME.replace('.csv', ''), '')
        labeled_data_dict[clean_plt_profile_name] = []
        for pkt in packets:
            # pkt is tuple of form (host, party, new_list), where new list is the cleaned keys to match to labels
            for key in pkt[2]:
                if key in data_labels.keys(): #not all keys were string matched (only kept >= 0.8)
                    if data_labels[key] != "Unclear":
                        labeled_tuple = (pkt[0], pkt[1], data_labels[key], pkt[3]) # <sld, party, label, ats flag>
                        labeled_data_dict[clean_plt_profile_name].append(labeled_tuple)
    return labeled_data_dict



def process_labels_gpt_tuple_with_owner(overall_data_dict, gpt_labels_file, tracker_radar_file_path, whois_file_path): 
    ## Connect the GPT-classified labels back to the data dictionary with destination, domain owner, and party label and create data flow tuple
    # read in labeled data list 
    with open(INTER_DATA_DIR + os.sep + gpt_labels_file, "r") as infile:
        data_labels = json.load(infile)
    with open(tracker_radar_file_path, "r") as infile:
        tracker_rader_data = json.load(infile)
    with open(whois_file_path, "r") as infile:
        whois_data = json.load(infile)

    # manual matching from crunchbase if unknown org owner in tracker-radar/whois or based on domain name
    manual_sld_owners = utils.MANUAL_ORGS 
    labeled_data_dict = {}
    for plt_profile, packets in overall_data_dict.items():
        # k is the age profile for each platform, v is the list of packets for this age profile
        clean_plt_profile_name = plt_profile.replace(FULL_CSV_OUTPUT_NAME.replace('.csv', ''), '')  # ex: Duolingo_1 or Duolingo (logged out)
        labeled_data_dict[clean_plt_profile_name] = []
        for pkt in packets:             
            if "_" in clean_plt_profile_name:
                app_name = clean_plt_profile_name.split("_")[0]
            else:
                app_name = clean_plt_profile_name

            # pkt is tuple of form (host, party, new_list), where new list is the cleaned keys to match to labels
            sld = pkt[0]
            party = pkt[1]
            ats_flag = pkt[3]
            host = pkt[4]
            if party == "platform_party":
                print(f"{sld}: {party}")
            for key in pkt[2]:
                if key in data_labels.keys(): # not all keys were string matched (only kept >= 0.8)
                    # get organization owner for sld
                    if sld in tracker_rader_data[app_name].keys() or sld in whois_data[app_name].keys():
                        tr_org = tracker_rader_data[app_name][sld]["tracker_radar_owner_data"]
                        whois_org = whois_data[app_name][sld]["whois_response"]
                        # check tracker-radar first
                        if tr_org != {}:  
                            owner = tr_org["name"]
                        # check the manual dictionary for owner
                        elif sld in manual_sld_owners.keys():
                            owner = manual_sld_owners[sld]
                        # check whois if tracker-radar owner value is empty
                        elif "org" in whois_org.keys():
                            whoisorg = whois_org["org"]
                            if whoisorg != None and not ("c/o whoisproxy.com" in whoisorg or "Identity Protection Service" in whoisorg or "DATA REDACTED" in whoisorg or  whoisorg == "" or  "Domains By Proxy" in whoisorg or "Privacy service provided by" in whoisorg or "Contact Privacy Inc. Customer" in whoisorg):
                                owner = whois_org["org"]
                            else:
                                owner = "Unknown"
                        else:
                            print(f"### Warning: No organization owner found for {sld}")
                            owner = "Unknown"
                        # fix some party labeling
                        if (app_name == "Minecraft") and (owner == "Microsoft Corporation") and (party != "first_party"):
                            party = "first_party"
                        if (app_name == "YouTube") and (owner == "Google LLC") and (party != "first_party"):
                            party = "first_party"
                        if (app_name == "YouTubeKids") and (owner == "Google LLC") and (party != "first_party"):
                            party = "first_party"
                        if (app_name == "TikTok") and (owner == "ByteDance Ltd.") and (party != "first_party"):
                            party = "first_party"
                        if (app_name == "Duolingo") and (owner == "Duolingo, Inc.") and (party != "first_party"):
                            party = "first_party"
                        if (app_name == "Quizlet") and (owner == "Quizlet, Inc.") and (party != "first_party"):
                            party = "first_party"
                        if (app_name == "Roblox") and (owner == "Roblox Corporation") and (party != "first_party"):
                            party = "first_party"

                    # construct packet tuple
                    # <sld, owner, party, label, ats flag, cleaned up key from traffic, hostname>
                    labeled_tuple = (sld, owner, party, data_labels[key], ats_flag, key, host) 
                    labeled_data_dict[clean_plt_profile_name].append(labeled_tuple)
    return labeled_data_dict



def gpt_processing_pipeline(platform, schema, trace_select, gpt_version, overall_data_dict_sld, gpt_labels_file):
    ## Main controller for GPT processing
    # use the gpt key labels generated from gpt_labeling.py
    print(f"[.] Platform: {platform}")
    print(f"[.] Schema: {schema}")
    print(f"[.] Trace type: {trace_select}")

    # connect labeled keys back to the packets with destinations, each key needs tuple with its destination
    print(f"[.] Processing labeled data types (labeled with ChatGPT) for {trace_select}...")
    tracker_radar_file_path = INTER_DATA_DIR + os.sep + f"{platform}_all_traces_destinations-tracker_radar-{gpt_version}.json"
    whois_file_path = INTER_DATA_DIR + os.sep + f"{platform}_all_traces_destinations-whois-{gpt_version}.json"
    labeled_data_dict_slds_tuple = process_labels_gpt_tuple(overall_data_dict_sld, gpt_labels_file)
    # outputs: <esld, party, data label, ats flag>
    labeled_data_dict_slds_with_owner_tuple = process_labels_gpt_tuple_with_owner(overall_data_dict_sld, gpt_labels_file, tracker_radar_file_path, whois_file_path) 
    # outputs: <esld, owner, party, data label, ats flag>

    with open(INTER_DATA_DIR + os.sep + f"labeled_data_dict_slds_with_owner_tuple-{platform}_{trace_select}.json", "w") as outfile:
        json.dump(labeled_data_dict_slds_with_owner_tuple, outfile, indent=4)

    return labeled_data_dict_slds_with_owner_tuple, labeled_data_dict_slds_tuple, tracker_radar_file_path, whois_file_path


def logged_out_processing_pipeline(platform, schema, trace_select, gpt_version, overall_data_dict_sld, gpt_labels_file):
    ## Process the logged out trace data with gpt processing pipeline
    gpt_processing_pipeline(platform, schema, trace_select, gpt_version, overall_data_dict_sld, gpt_labels_file)


def logged_in_full_processing_pipeline(platform, schema, trace_select, gpt_version, overall_data_dict_sld, gpt_labels_file):
    ## Process the logged in / full trace with gpt processing pipelin
    gpt_processing_pipeline(platform, schema, trace_select, gpt_version, overall_data_dict_sld, gpt_labels_file) 


def dest_helper(platform, gpt_version, regenerate_flag):
    ## Helper function for destination processing
    traces = ['logged_in_trace', 'logged_out_trace', 'full_trace']
    destinations_dict = {}
    if regenerate_flag:
        destinations = {}
        for trace in traces:
            overall_data_dict, all_unique_keys_cross_plat, all_unique_keys_per_plat, overall_data_dict_sld = read_from_csvs(platform, trace_select=trace)
            for source, data_arr in overall_data_dict_sld.items():
                # clean up name for dictionary key
                if "_" in source:
                    appname = source.split('_')[0]
                else:
                    appname = source.split('-')[0]
                # create empty set for newly encountered app 
                if appname not in destinations.keys():
                    destinations[appname] = set()
                # add each tuple of sld and party label to the set for each app
                for i in data_arr:
                    destinations[appname].add((i[0], i[1], i[3])) #append destination, party label, and ats flag to set
                    
        for k, v in destinations.items():
            destinations_dict[k] = list(v)

        gpt_version_timestr = gpt_version ##matches the labels file that this corresponds to
        with open(INTER_DATA_DIR + os.sep + f"{platform}_all_traces_destinations-{gpt_version_timestr}.json", "w") as outfile:
            json.dump(destinations_dict, outfile, indent=4)

        # using whois
        whois_dest_dict = {}
        for app, dest_arr in destinations_dict.items():
            whois_dest_dict[app] = {}
            for dest_tuple in dest_arr:
                dest = dest_tuple[0]
                party = dest_tuple[1]
                ats_flag = dest_tuple[2]
                if dest != "" and dest != '.':
                    # print(dest)
                    w = whois.whois(dest)
                    whois_dest_dict[app][dest] = {}
                    whois_dest_dict[app][dest]["party"] = party
                    whois_dest_dict[app][dest]["ats_flag"] = ats_flag
                    whois_dest_dict[app][dest]["whois_response"] = w
        
        with open(INTER_DATA_DIR + os.sep + f"{platform}_all_traces_destinations-whois-{gpt_version_timestr}.json", "w") as outfile:
            json.dump(whois_dest_dict, outfile, indent=4, default=str)

        # using tracker radar dataset
        tracker_radar_dest_dict = {}
        tracker_radar_us_domains_path = TRACKER_RADAR_DIR + os.sep + "domains" + os.sep + "US"
        tracker_radar_domain_files = os.listdir(tracker_radar_us_domains_path)
        for app, dest_arr in destinations_dict.items():
            for dest_tuple in dest_arr:
                dest = dest_tuple[0]
                party = dest_tuple[1]
                ats_flag = dest_tuple[2]
                dest_json_name = dest + ".json"
                if dest != "" and dest != '.':
                    if app not in tracker_radar_dest_dict.keys():
                        tracker_radar_dest_dict[app] = {}
                    if dest_json_name in tracker_radar_domain_files:
                        # print(dest_json_name)
                        with open(tracker_radar_us_domains_path + os.sep + dest_json_name, "r") as infile:
                            tr_data = json.load(infile)
                        tracker_radar_dest_dict[app][dest] = {}
                        tracker_radar_dest_dict[app][dest]["party_label"] = party
                        tracker_radar_dest_dict[app][dest]["ats_flag_label"] = ats_flag
                        tracker_radar_dest_dict[app][dest]["tracker_radar_owner_data"] = tr_data["owner"]
                        tracker_radar_dest_dict[app][dest]["tracker_radar_full_data"] = tr_data
                    else:
                        tracker_radar_dest_dict[app][dest] = {
                            "party_label": party,
                            "ats_flag_label": ats_flag,
                            "tracker_radar_owner_data": {}
                        } ## make an empty entry
                        print(f"### {app}: did not find domain <{dest}> in tracker radar dataset -- we labeled as {party}")
                        if dest in whois_dest_dict[app].keys():
                            print(f"Found <{dest}> in whois data. Organization name: {whois_dest_dict[app][dest]['whois_response']}")
                        print('')

        for k in tracker_radar_dest_dict.keys():
            print('#############################################################################################')
            print(k)
            for i in tracker_radar_dest_dict[k].keys():
                print(i)
                print(tracker_radar_dest_dict[k][i]["party_label"])
                print(tracker_radar_dest_dict[k][i]["ats_flag_label"])
                print(f'tracker radar info: {tracker_radar_dest_dict[k][i]["tracker_radar_owner_data"]}')
                if tracker_radar_dest_dict[k][i]["tracker_radar_owner_data"] == {}:
                    if "whois_response" in whois_dest_dict[k][i].keys():
                        print(f'whois info: {whois_dest_dict[k][i]["whois_response"]}')
                    else:
                        print('whois info: {}') #none
                print('')

        with open(INTER_DATA_DIR + os.sep + f"{platform}_all_traces_destinations-tracker_radar-{gpt_version_timestr}.json", "w") as outfile:
            json.dump(tracker_radar_dest_dict, outfile, indent=4, default=str)

    else:
        # read the one that was already generated previously 
        gpt_version_timestr = gpt_version # matches the labels file that this corresponds to

        with open(INTER_DATA_DIR + os.sep + f"{platform}_all_traces_destinations-whois-{gpt_version_timestr}.json", "r") as infile:
            whois_dest_dict = json.load(infile)

        with open(INTER_DATA_DIR + os.sep + f"{platform}_all_traces_destinations-tracker_radar-{gpt_version_timestr}.json", "r") as infile:
            tracker_radar_dest_dict = json.load(infile)

    return tracker_radar_dest_dict, whois_dest_dict



def extract_destinations(platform, gpt_version, regenerate_flag):
    ## Extract destination information (owner) from domains
    if platform == "bothplatforms":
        overall_dest_dict = {}
        both_plats_dest = {
            'website': {},
            'mobile': {}
        }
        for plat in both_plats_dest.keys():
            both_plats_dest[plat]['tracker-radar'], both_plats_dest[plat]['whois'] = dest_helper(platform=plat, gpt_version=gpt_version, regenerate_flag=regenerate_flag)
        apps = both_plats_dest['website']['tracker-radar'].keys()
        for app in apps:
            overall_dest_dict[app] = {}
        for plat in both_plats_dest.keys():
            for app in overall_dest_dict.keys():
                if app in both_plats_dest[plat]['tracker-radar'].keys():
                    for k, v in both_plats_dest[plat]['tracker-radar'][app].items():
                        if k not in overall_dest_dict[app].keys():
                            overall_dest_dict[app][k] = {}
                            overall_dest_dict[app][k]["party_label"] = v['party_label']  
                            overall_dest_dict[app][k]["ats_flag_label"] = v['ats_flag_label']
                            overall_dest_dict[app][k]["tracker_radar_owner_data"] = v['tracker_radar_owner_data']
                            if "whois_response" in both_plats_dest[plat]["whois"][app][k].keys():
                                overall_dest_dict[app][k]["whois_response"] = both_plats_dest[plat]["whois"][app][k]["whois_response"]
                            else:
                                overall_dest_dict[app][k]["whois_response"] = {}
        
        for k, v in overall_dest_dict.items():
            print('#############################################################################################')
            print(k) ## app name
            for i in overall_dest_dict[k].keys():
                print(i)
                print(overall_dest_dict[k][i]["party_label"])
                print(overall_dest_dict[k][i]["ats_flag_label"])
                print(f'tracker radar info: {overall_dest_dict[k][i]["tracker_radar_owner_data"]}')
                print(f'whois info: {overall_dest_dict[k][i]["whois_response"]}')
                print('')
        
        with open(INTER_DATA_DIR + os.sep + f"{platform}_all_merged_unique_destinations_info_all_traces-{gpt_version}.json", "w") as outfile:
            json.dump(overall_dest_dict, outfile, indent=4, default=str)
    
    else:
        dest_helper(platform, gpt_version, regenerate_flag=regenerate_flag)



def create_label_json():
    ## Create JSON files with keys from packet key-value pairs to be used for GPT labeling
    plats = ['website', 'mobile']
    traces = ['logged_in_trace', 'logged_out_trace', 'full_trace']
    timestr = time.strftime("%Y%m%d-%H%M%S")
    all_keys_cross_plat_and_trace = set()
    for plat in plats:
        for trace in traces:
            print(f"[.] Extracting data from platform {plat} csv files to create {plat}_all_unique_keys_cross_plat JSON file based on {trace} trace(s)...")
            ## read csv files from process_pcaps outputs and generate the all_unique_keys_cross_plat.json for gpt_labeling.py
            overall_data_dict, all_unique_keys_cross_plat, all_unique_keys_per_plat, overall_data_dict_sld = read_from_csvs(plat, trace_select=trace)
            ## save all unique keys cross plat
            with open(INTER_DATA_DIR + os.sep + f"{plat}_all_unique_keys_cross_plat_{trace}-{timestr}.json", "w") as outfile:
                json.dump({"keys": list(all_unique_keys_cross_plat)}, outfile, indent=4)
            print(f"\n[.] {plat}: Number of unique keys across all apps for {trace}: {len(list(all_unique_keys_cross_plat))}\n")
            ## merge into overall list of keys 
            for i in all_unique_keys_cross_plat:
                all_keys_cross_plat_and_trace.add(i)

    ## write overall list of keys for both mobile and website platform for all traces to json file
    filepath = INTER_DATA_DIR + os.sep + f"all_unique_keys_all_plaforms_all_traces-{timestr}.json"
    with open(filepath, "w") as outfile:
        json.dump({"keys": list(all_keys_cross_plat_and_trace)}, outfile, indent=4)
    print(f"\n[.] Number of unique keys across all platforms (web and mobile) and all traces: {len(list(all_keys_cross_plat_and_trace))}\n")

    return filepath



def main():
    ## Prepare/check directories
    if not os.path.isdir(INTER_DATA_DIR):
        print(f"### Error: {INTER_DATA_DIR} should have been created by first running process_pcaps.py. Exiting.")
        return
    if not os.path.isdir(GPT_OUTPUTS_DIR):
        os.makedirs(GPT_OUTPUTS_DIR)
    if not os.path.isdir(TRACKER_RADAR_DIR):
        print(f"### Error: you need to download the Tracker Radar US dataset and save to {TRACKER_RADAR_DIR}. Exiting.")
        return

    ## Assume processing all traces and platforms
    platform = "bothplatforms"

    ## [1] create_label_json: Generate the unique keys file for gpt labeling script to use, and also generate destinations file for processing
    print(f"\n[+] Extracting unique keys from key-value pairs in network traffic...")
    all_unique_keys_file_path = create_label_json()


    ## [2] GPT classification pipeline
    print(f"\n[+] Running GPT classification pipeline (make sure you have entered you API key in gpt_labeling and selected your model parameters if different from default)...")
    ret = subprocess.check_call(["python3", "gpt_labeling.py", 
        "--platform", platform,
        "--unique_keys_file", all_unique_keys_file_path,
        "--classify"
    ])
    if ret == 0:
        print("### ERROR: error from GPT pipeline. Aborting.")
        return
    # get gpt files and gpt_version from timestr to match up with data flows output files
    gpt_version, final_labels_per_key_filename, max_score_labeled_keys_filename, avg_score_labeled_keys_filename = ret[0], ret[1], ret[2], ret[3]

    # copy from gpt_outputs to inter_data_file to preserve originaly
    shutil.copyfile(GPT_OUTPUTS_DIR + os.sep + final_labels_per_key_filename, INTER_DATA_DIR + os.sep + final_labels_per_key_filename)
    shutil.copyfile(GPT_OUTPUTS_DIR + os.sep + max_score_labeled_keys_filename, INTER_DATA_DIR + os.sep + max_score_labeled_keys_filename)
    shutil.copyfile(GPT_OUTPUTS_DIR + os.sep + avg_score_labeled_keys_filename, INTER_DATA_DIR + os.sep + avg_score_labeled_keys_filename)

    # assuming using merged-avg approach with 0.8 confidence from gpt_labeling output
    gpt_labels_file = avg_score_labeled_keys_filename
    schema = "merged_avg"
    with open(INTER_DATA_DIR + os.sep + "gpt_labeling_version_data.json", "w") as fp:    
        data = {'gpt_version': gpt_version, 'gpt_labels_file': gpt_labels_file, 'schema': schema}
        json.dump(data, fp, indent=4)


    ## [3] Extract destination information (entities)
    print(f"\n[+] Extracting destination information from contacted domains in traffic...")
    extract_destinations(platform, gpt_version, regenerate_flag=True)


    ## [4] Construct data flows pipeline
    print(f"\n[+] Constructing data flows for both platforms and all traces...")
    traces = ['logged_in_trace', 'logged_out_trace', 'full_trace']
    for plat in PLATFORM_NAMES:
        for trace in traces:
            print(f"\n[.] Extracting data flow data from service CSV files for {trace}...")
            overall_data_dict, all_unique_keys_cross_plat, all_unique_keys_per_plat, overall_data_dict_sld = read_from_csvs(plat, trace_select=trace)
            with open(INTER_DATA_DIR + os.sep + f"overall_data_dict-{plat}_{trace}.pkl", "wb") as outfile:
                pickle.dump(overall_data_dict, outfile) # save obj to pickle if want to be faster and reload instead
            with open(INTER_DATA_DIR + os.sep + f"overall_data_dict_sld-{plat}_{trace}.pkl", "wb") as outfile:
                pickle.dump(overall_data_dict_sld, outfile)  
            
            # output counts of matches and non matches
            count_matches_per_plat_gpt(all_unique_keys_per_plat, gpt_labels_file)
            
            # process for this trace
            print(f"[.] Processing {trace} data flows...")
            if trace == "full_trace" or trace == "logged_in_trace":
                logged_in_full_processing_pipeline(plat, schema, trace, gpt_version, overall_data_dict_sld, gpt_labels_file)
            elif trace == "logged_out_trace":
                logged_out_processing_pipeline(plat, schema, trace, gpt_version, overall_data_dict_sld, gpt_labels_file)
    
    print("[+] Done.")
    return


if __name__ == "__main__":
    main()