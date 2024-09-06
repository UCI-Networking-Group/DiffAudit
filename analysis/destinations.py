#!/usr/bin/python

'''
This script provides functions for the destination analysis portion of analysis_pipeline.py
'''

import os
import pandas as pd
import json
import copy
from collections import Counter

from analysis.helper_scripts import merge_data
from utils import utils

def create_tup_list(tup, trace_category, counter, unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict):
    # Helper function for destination analysis processing
    sld = tup[0]
    company = tup[1]
    party = tup[2]
    data_type = tup[3]
    ats = tup[4]
    original_key = tup[5]
    host = tup[6]
    new_tup = (trace_category, sld, company, party, ats, host)
    data_flow_pair = (data_type, host)
    unique_data_flow_list.add(data_flow_pair)
    aggregate_data_flows.append(new_tup)
    if new_tup not in unique_tups_list:
        unique_tups_list.add(new_tup)
        alluvial_dict['id'].append(counter)
        counter += 1
        alluvial_dict["Age"].append(trace_category)
        alluvial_dict['SLD'].append(sld)
        alluvial_dict['Company'].append(company)
        if ats == '1' and party == "third_party":
            alluvial_dict['Party & ATS'].append("ATS Third Party")
        elif ats == '1' and party == "first_party":
            alluvial_dict['Party & ATS'].append("ATS First Party")
        elif ats == '0' and party == "third_party":
            alluvial_dict['Party & ATS'].append("Third Party")
        elif ats == '0' and party == "first_party":
            alluvial_dict['Party & ATS'].append("First Party")

    return unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict, counter

def dest_helper(data_dict, alluvial_dict, unique_tups_list, unique_data_flow_list, aggregate_data_flows):
    counter = 1
    for app, data in data_dict.items():
        if utils.CHILD_NUM in app:
            for tup in data: #  (sld, owner, party, data_labels[key], ats_flag, key, host) 
                unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict, counter = create_tup_list(tup, utils.CHILD, counter, unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict)
        elif utils.TEEN_NUM in app:
            for tup in data:
                unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict, counter = create_tup_list(tup, utils.TEEN, counter, unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict)
        elif utils.ADULT_NUM in app:
            for tup in data:
                unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict, counter = create_tup_list(tup, utils.ADULT, counter, unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict)
        elif "_" not in app:
            ## logged out
            for tup in data:
                unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict, counter = create_tup_list(tup, utils.LOGGED_OUT, counter, unique_data_flow_list, aggregate_data_flows, unique_tups_list, alluvial_dict)

    return alluvial_dict, unique_tups_list, aggregate_data_flows, unique_data_flow_list

def tup_helper(i):
    sld = i[0]
    owner = i[1]
    party = i[2]
    ats = i[4]
    host = i[6]
    new_tup = (sld, owner, party, ats, host) 
    return new_tup, sld, owner, party, ats, host
    
def dest_metadata_helper(dest_metadata, sld, host, owner, party, ats):
    dest_metadata["all_slds"].add(sld)
    dest_metadata["all_hosts"].add(host)
    dest_metadata["companies"].add(owner)
    if party == utils.FIRST and ats == '1':
        dest_metadata["1st_ats"].add(host)
    elif party == utils.FIRST and ats == '0':
        dest_metadata["1st"].add(host)
    elif party == utils.THIRD and ats == '1':
        dest_metadata["3rd_ats"].add(host)
    elif party == utils.THIRD and ats == '0':
        dest_metadata["3rd"].add(host)
    return dest_metadata

def unique_dest_helper(input_dict, out_dict, dest_metadata={}): 
    for k, v in input_dict.items():
        if "_" in k:
            if utils.CHILD_NUM in k:
                for i in v:
                    new_tup, sld, owner, party, ats, host = tup_helper(i)
                    out_dict[utils.CHILD].add(new_tup)
                    if dest_metadata != {}:
                        dest_metadata_helper(dest_metadata, sld, host, owner, party, ats)
            elif utils.TEEN_NUM in k:
                for i in v:
                    new_tup, sld, owner, party, ats, host = tup_helper(i)
                    out_dict[utils.TEEN].add(new_tup)
                    if dest_metadata != {}:
                        dest_metadata_helper(dest_metadata, sld, host, owner, party, ats)
            elif utils.ADULT_NUM in k:
                for i in v:
                    new_tup, sld, owner, party, ats, host = tup_helper(i)
                    out_dict[utils.ADULT].add(new_tup)
                    if dest_metadata != {}:
                        dest_metadata_helper(dest_metadata, sld, host, owner, party, ats)
        else:
            for i in v:
                new_tup, sld, owner, party, ats, host = tup_helper(i)
                out_dict[utils.LOGGED_OUT].add(new_tup)
                if dest_metadata != {}:
                    dest_metadata_helper(dest_metadata, sld, host, owner, party, ats)
    
    return out_dict, dest_metadata


def count_domains_eslds(web_login_data, mobile_login_data, web_full_data, mobile_full_data, web_logout_data, mobile_logout_data):
    print("[+] Computing destination counts...")
    ## compute number of domains, eslds across services and age groups
    app_dict_inner = {utils.CHILD: set(), utils.TEEN: set(), utils.ADULT: set()}    
    app_dict_inner_lists = {utils.CHILD: [], utils.TEEN: [], utils.ADULT: []} 
    app_dict, app_dict_to_save = {}, {}
    for i in utils.SERVICE_NAMES_MAIN:
        app_dict[i] = copy.deepcopy(app_dict_inner)
        app_dict_to_save[i] = copy.deepcopy(app_dict_inner_lists)

    ## logged in
    loggedin_app_dict = copy.deepcopy(app_dict)
    loggedin_app_dict_tosave = copy.deepcopy(app_dict_to_save)
    loggedin_app_dict = merge_data(web_login_data, loggedin_app_dict)
    loggedin_app_dict = merge_data(mobile_login_data, loggedin_app_dict)
    
    for app, age_data in loggedin_app_dict.items():
        for age, data in age_data.items():
            loggedin_app_dict_tosave[app][age] = list(data)
    
    with open(utils.ANALYSIS_OUT_DIR + os.sep + "unique_merged_plat_dataflows_loggedinonly.json", "w") as out:
        json.dump(loggedin_app_dict_tosave, out, indent=4)
    
    ## account trace
    full_trace_app_dict = copy.deepcopy(app_dict)
    full_app_dict_tosave = copy.deepcopy(app_dict_to_save)
    full_trace_app_dict = merge_data(web_full_data, full_trace_app_dict)
    full_trace_app_dict = merge_data(mobile_full_data, full_trace_app_dict)
    
    for app, age_data in full_trace_app_dict.items():
        for age, data in age_data.items():
            full_app_dict_tosave[app][age] = list(data)
    
    with open(utils.ANALYSIS_OUT_DIR + os.sep + "unique_merged_plat_dataflows_fullonly.json", "w") as out:
        json.dump(full_app_dict_tosave, out, indent=4)

    ## logged out
    logout_app_dict, logout_app_dict_tosave = {}, {}
    for i in utils.SERVICE_NAMES_ALL:
        logout_app_dict[i] = set()
        logout_app_dict_tosave[i] = []

    logout_app_dict = merge_data(web_logout_data, logout_app_dict)
    logout_app_dict = merge_data(mobile_logout_data, logout_app_dict)

    for k, v in logout_app_dict.items():
        logout_app_dict_tosave[k] = list(v)
    with open(utils.ANALYSIS_OUT_DIR + os.sep + "unique_merged_plat_dataflows_logoutonly.json", "w") as out:
        json.dump(logout_app_dict_tosave, out, indent=4)

    total_domains, total_eslds = {}, {}
    for i in utils.SERVICE_NAMES_ALL:
        total_domains[i] = set()
        total_eslds[i] = set()

    for app,v in full_app_dict_tosave.items():
        for age, flows in v.items():
            for tup in flows:
                total_domains[app].add(tup[4]) #host
                total_eslds[app].add(tup[0]) #sld
    
    for app,v in loggedin_app_dict_tosave.items():
        for age, flows in v.items():
            for tup in flows:
                total_domains[app].add(tup[4]) #host
                total_eslds[app].add(tup[0]) #sld

    for app,flows in logout_app_dict_tosave.items():
        for tup in flows:
            total_domains[app].add(tup[4]) #host
            total_eslds[app].add(tup[0]) #sld

    unique_slds, unique_domains = set(), set()
    print("\n[.] Total FQDNs counts:")
    for k, v in total_domains.items():
        print(k, len(v))
        for i in v:
            unique_domains.add(i)
    
    print("\n[.] Total SLDs counts")
    for k, v in total_eslds.items():
        print(k, len(v))
        for i in v:
            unique_slds.add(i)

    print(f"\n[.] Total unique SLDs: {len(unique_slds)}")
    print(f"\n[.] Total unique FQDNs: {len(unique_domains)}")



def destination_only_analysis(web_full_data, web_login_data, web_logout_data, mobile_full_data, mobile_login_data, mobile_logout_data):
    # Count numbers of FQDNs and SLDs
    count_domains_eslds(web_login_data, mobile_login_data, web_full_data, mobile_full_data, web_logout_data, mobile_logout_data)
    
    # prepare data for destination analysis - top domains, counts, etc.
    alluvial_dict = {
        'id': [],
        'Age': [],
        'SLD': [],
        'Company': [],
        'Party & ATS': []
    }

    # care about unique traces, so merge first then create the alluvial csv
    unique_tups_list = set()
    unique_data_flow_list = set()
    aggregate_data_flows = []
    alluvial_dict, unique_tups_list, aggregate_data_flows, unique_data_flow_list = dest_helper(web_full_data, alluvial_dict, unique_tups_list, unique_data_flow_list, aggregate_data_flows)
    alluvial_dict, unique_tups_list, aggregate_data_flows, unique_data_flow_list = dest_helper(mobile_full_data, alluvial_dict, unique_tups_list, unique_data_flow_list, aggregate_data_flows)
    alluvial_dict, unique_tups_list, aggregate_data_flows, unique_data_flow_list = dest_helper(web_login_data, alluvial_dict, unique_tups_list, unique_data_flow_list, aggregate_data_flows)
    alluvial_dict, unique_tups_list, aggregate_data_flows, unique_data_flow_list = dest_helper(mobile_login_data, alluvial_dict, unique_tups_list, unique_data_flow_list, aggregate_data_flows)
    alluvial_dict, unique_tups_list, aggregate_data_flows, unique_data_flow_list = dest_helper(web_logout_data, alluvial_dict, unique_tups_list, unique_data_flow_list, aggregate_data_flows)
    alluvial_dict, unique_tups_list, aggregate_data_flows, unique_data_flow_list = dest_helper(mobile_logout_data, alluvial_dict, unique_tups_list, unique_data_flow_list, aggregate_data_flows)

    df = pd.DataFrame(data=alluvial_dict)
    df.to_csv(utils.ANALYSIS_OUT_DIR + os.sep + "alluvial_child_and_teen_data_unique_alltraces.csv", index = True)
    print("\n[.] Generated alluvial_child_and_teen_data_unique_alltraces.csv")

    print(f"\n[+] Number of unique data flows (data type, destination) across entire dataset: {len(unique_data_flow_list)}")

    # output the frequencies of the destinations and get the top most contacted
    destination_frequency = {
        "slds": {
            utils.FIRST: [],
            utils.THIRD: [],
            utils.FIRST + "_ats": [],
            utils.THIRD + "_ats": [],
        },
        "hosts": {
            utils.FIRST: [],
            utils.THIRD: [],
            utils.FIRST + "_ats": [],
            utils.THIRD + "_ats": [],
        },
    }
    for tup in aggregate_data_flows: # (category, sld, company, party, ats, host)
        sld = tup[1]
        party = tup[3]
        ats = tup[4]
        host = tup[5]
        if party == utils.FIRST and ats == '0':
            destination_frequency["slds"][utils.FIRST].append(sld)
            destination_frequency["hosts"][utils.FIRST].append(host)
        elif party == utils.FIRST and ats == '1':
            destination_frequency["slds"][utils.FIRST+"_ats"].append(sld)
            destination_frequency["hosts"][utils.FIRST+"_ats"].append(host)
        elif party == utils.THIRD and ats == '0':
            destination_frequency["slds"][utils.THIRD].append(sld)
            destination_frequency["hosts"][utils.THIRD].append(host)
        elif party == utils.THIRD and ats == '1':
            destination_frequency["slds"][utils.THIRD+"_ats"].append(sld)
            destination_frequency["hosts"][utils.THIRD+"_ats"].append(host)

    print("\n[+] Most frequently contacted domains by category (party and ATS labeling):")
    for k, v in destination_frequency["slds"].items():
        counts = Counter(v).most_common(5)
        print(f"[.] {k}: {counts}")

    for k, v in destination_frequency["hosts"].items():
        print(f"[.] {k}: {counts}")

    # output the counts of 1st/3rd and ATS for each age category across traces
    unique_dest_dict = {
        utils.CHILD: set(),
        utils.TEEN: set(),
        utils.ADULT: set(),
        "child_adult": set(),
        "teen_adult": set(),
        "child_teen": set(),
        "all_three": set(),
    }
    unique_dest_dict, _ = unique_dest_helper(web_full_data, unique_dest_dict)
    unique_dest_dict, _ = unique_dest_helper(web_login_data, unique_dest_dict)
    unique_dest_dict, _ = unique_dest_helper(mobile_full_data, unique_dest_dict)
    unique_dest_dict, _ = unique_dest_helper(mobile_login_data, unique_dest_dict)

    unique_dest_dict["child_adult"] = unique_dest_dict[utils.CHILD] & unique_dest_dict[utils.ADULT]
    unique_dest_dict["teen_adult"] = unique_dest_dict[utils.TEEN] & unique_dest_dict[utils.ADULT]
    unique_dest_dict["child_teen"] = unique_dest_dict[utils.CHILD] & unique_dest_dict[utils.TEEN]
    unique_dest_dict["all_three"] = unique_dest_dict[utils.CHILD] & unique_dest_dict[utils.ADULT] & unique_dest_dict[utils.TEEN]

    # output counts of destinations
    unique_dest_dict = {
        utils.CHILD: set(),
        utils.TEEN: set(),
        utils.ADULT: set(),
        utils.LOGGED_OUT: set()
    }
    dest_metadata = {
        "all_slds": set(),
        "all_hosts": set(),
        "companies": set(),
        "1st_ats": set(),
        "1st": set(),
        "3rd": set(),
        "3rd_ats": set()
    }
    
    unique_dest_dict, dest_metadata = unique_dest_helper(web_full_data, unique_dest_dict, dest_metadata)
    unique_dest_dict, dest_metadata = unique_dest_helper(web_login_data, unique_dest_dict, dest_metadata)
    unique_dest_dict, dest_metadata = unique_dest_helper(mobile_full_data, unique_dest_dict, dest_metadata)
    unique_dest_dict, dest_metadata = unique_dest_helper(mobile_login_data, unique_dest_dict, dest_metadata)
    unique_dest_dict, dest_metadata = unique_dest_helper(web_logout_data, unique_dest_dict, dest_metadata)
    unique_dest_dict, dest_metadata = unique_dest_helper(mobile_logout_data, unique_dest_dict, dest_metadata)

    print("\n[+] Destination stats across entire dataset:")
    for k, v in dest_metadata.items():
        print(k, len(v))