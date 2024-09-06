#!/usr/bin/python

'''
This script provides functions for the data linkability analysis portion of analysis_pipeline.py
'''

import os
import json
import copy
import csv
from collections import Counter
import sys

sys.path.append(os.path.abspath('../'))
from data_flows.utils.utils import MANUAL_ORGS
from data_flows.labeling_utils.ontology_L1_to_L3 import data_type_categories_ontology_L3_to_L1
from utils import utils

def get_max_length_sublist(all_lists):
    max_len_list = max(all_lists, key=len)
    max_len = len(max_len_list)
    return max_len_list, max_len

def get_min_length_sublist(all_lists):
    min_len_list = min(all_lists, key=len)
    min_len = len(min_len_list)
    return min_len_list, min_len

def get_most_common_sublist(all_data_type_sets):
    most_common_list = Counter(tuple(sublist) for sublist in all_data_type_sets).most_common(1)
    return most_common_list, len(most_common_list[0][0])

def analyze_data_linkability(web_full_data, web_login_data, web_logout_data, mobile_full_data, mobile_login_data, mobile_logout_data):
    print("[+] Analyzing data linkability...")

    # prepare data dict by age and platform combinations
    ages = [utils.CHILD_NUM, utils.TEEN_NUM, utils.ADULT_NUM]  
    data_dict_per_app_dests = {}
    for i in utils.SERVICE_NAMES_MAIN:
        data_dict_per_app_dests[i] = {}
        for j in ages:
            data_dict_per_app_dests[i][i + j] = {}
        data_dict_per_app_dests[i][i + "_loggedout"] = {}

    # account creation and logged in
    for obj in [web_full_data, mobile_full_data, web_login_data, mobile_login_data]:
        for app_cat, data in obj.items():
            app = app_cat[:len(app_cat)-2]
            if app in data_dict_per_app_dests.keys():
                identifier_flag, pers_info_flag = 0, 0
                for data_flow in data:
                    tup_dest_sld = data_flow[0]
                    tup_data_type_L3 = data_flow[3]
                    tup_party = data_flow[2]
                    tup_ats = data_flow[4]

                    if tup_dest_sld in data_dict_per_app_dests[app][app_cat].keys():
                        # add info to existing dest
                        # check L1 data type category from L3 tuple data type
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['frequency'] += 1 # update frequency (for data flow)

                        if tup_data_type_L3 in data_type_categories_ontology_L3_to_L1['Identifiers']:
                            identifier_flag = 1
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['identifier_flag'] = identifier_flag
                        elif tup_data_type_L3 in data_type_categories_ontology_L3_to_L1['Personal Information']:
                            pers_info_flag = 1
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['pers_info_flag'] = pers_info_flag
                        else:
                            print(f"[x] *** should not get here - {tup_data_type_L3}")

                        if tup_data_type_L3 not in data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types']:
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types'].append(tup_data_type_L3)

                    else:
                        # add dest entry
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld] = {}
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types'] = []
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['identifier_flag'] = 0
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['pers_info_flag'] = 0
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['party'] = tup_party
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['ats'] = tup_ats
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['frequency'] = 1 # frequency (for data flow)

                        if tup_data_type_L3 in data_type_categories_ontology_L3_to_L1['Identifiers']:
                            identifier_flag = 1
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['identifier_flag'] = identifier_flag
                        elif tup_data_type_L3 in data_type_categories_ontology_L3_to_L1['Personal Information']:
                            pers_info_flag = 1
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['pers_info_flag'] = pers_info_flag
                        else:
                            print(f"Error: should not get here - {tup_data_type_L3}")

                        if tup_data_type_L3 not in data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types']:
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types'].append(tup_data_type_L3)
                    
            else:
                print("\nError: full/login shouldn't get here\n")
                print(app)

    # logged out
    for obj in [web_logout_data, mobile_logout_data]:
        for app, data in obj.items():            
            if app == 'YouTubeKids':
                app = "YouTube"
            app_cat = app + "_loggedout"
            
            if app in data_dict_per_app_dests.keys():
                identifier_flag, pers_info_flag = 0, 0

                for data_flow in data:
                    tup_dest_sld = data_flow[0]
                    tup_data_type_L3 = data_flow[3]
                    tup_party = data_flow[2]
                    tup_ats = data_flow[4]

                    if tup_dest_sld in data_dict_per_app_dests[app][app_cat].keys():
                        # add info to existing dest
                        # check L1 data type category from L3 tuple data type
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['frequency'] += 1 ## update frequency (for most contacted)

                        if tup_data_type_L3 in data_type_categories_ontology_L3_to_L1['Identifiers']:
                            identifier_flag = 1
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['identifier_flag'] = identifier_flag
                        elif tup_data_type_L3 in data_type_categories_ontology_L3_to_L1['Personal Information']:
                            pers_info_flag = 1
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['pers_info_flag'] = pers_info_flag
                        else:
                            print(f"Error: should not get here - {tup_data_type_L3}")
                        
                        if tup_data_type_L3 not in data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types']:
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types'].append(tup_data_type_L3)

                    else:
                        ## add dest entry
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld] = {}
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types'] = []
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['identifier_flag'] = 0
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['pers_info_flag'] = 0
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['party'] = tup_party
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['ats'] = tup_ats
                        data_dict_per_app_dests[app][app_cat][tup_dest_sld]['frequency'] = 1 # frequency (for most contacted)

                        if tup_data_type_L3 in data_type_categories_ontology_L3_to_L1['Identifiers']:
                            identifier_flag = 1
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['identifier_flag'] = identifier_flag
                        elif tup_data_type_L3 in data_type_categories_ontology_L3_to_L1['Personal Information']:
                            pers_info_flag = 1
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['pers_info_flag'] = pers_info_flag
                        else:
                            print(f"Error: should not get here - {tup_data_type_L3}")

                        if tup_data_type_L3 not in data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types']:
                            data_dict_per_app_dests[app][app_cat][tup_dest_sld]['L3_data_types'].append(tup_data_type_L3)
                    
            else:
                print("\nError: loggedout shouldn't get here\n")
                print(app)

    ## save to json
    with open(utils.ANALYSIS_OUT_DIR + os.sep + 'bothplatforms_data_bridging_destination_dict.json', 'w') as out:
        json.dump(data_dict_per_app_dests, out, indent=4) 
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/bothplatforms_data_bridging_destination_dict.json\n")

    # most common set of linkable data types that are sent to 3rd parties
    print(f"[+] Analyzing bundles/sets of linkable data types across services...")
    dest_counts_inner_dict = {
        'dests_1st_both': [], ## 1st parties that receive at least 1 data type from personal info + identifier (BOTH)
        'dests_1st_ats_both': [], 
        'dests_1st_ids': [], ## 1st parties that receive at least 1 identifier data type
        'dests_1st_ats_ids': [], 
        'dests_1st_pers': [], ## 1st parties that receive at least 1 personal information data type
        'dests_1st_ats_pers': [],
        'dests_3rd_both': [], ## same except 3rd parties
        'dests_3rd_ats_both': [], 
        'dests_3rd_ids': [], 
        'dests_3rd_ats_ids': [], 
        'dests_3rd_pers': [], 
        'dests_3rd_ats_pers': []
    } 
    data_bridging_counts = {}
    for i in utils.SERVICE_NAMES_MAIN:
        data_bridging_counts[i] = {}
        for j in ages:
            data_bridging_counts[i][i + j] = copy.deepcopy(dest_counts_inner_dict)
        data_bridging_counts[i][i + "_loggedout"] = copy.deepcopy(dest_counts_inner_dict)

    linkable_data_types_subsets = {}

    for app, per_dest_data in data_dict_per_app_dests.items():
        print(f"[+] {app}:")
        linkable_data_types_subsets[app] = {}
        
        child = app + utils.CHILD_NUM
        teen = app + utils.TEEN_NUM
        adult = app + utils.ADULT_NUM
        loggedout = app + "_loggedout"

        for category in [child, teen, adult, loggedout]:
            if utils.CHILD_NUM in category:
                age_cat_str = utils.CHILD
            elif utils.TEEN_NUM in category:
                age_cat_str = utils.TEEN
            elif utils.ADULT_NUM in category:
                age_cat_str = utils.ADULT
            else:
                age_cat_str = 'logged out'

            print(f"\n[.] category: {category}, {age_cat_str}")
            all_data_type_sets = []
            linkable_data_types_subsets[app][category] = {}
            for sld, data in per_dest_data[category].items():
                if data['party'] == utils.FIRST:
                    if data['ats'] == "1":
                        if data['identifier_flag'] == 1 and data['pers_info_flag'] == 1:
                            data_bridging_counts[app][category]['dests_1st_ats_both'].append(sld)
                        elif data['identifier_flag'] == 1:
                            data_bridging_counts[app][category]['dests_1st_ats_ids'].append(sld)
                        elif data['pers_info_flag'] == 1:
                            data_bridging_counts[app][category]['dests_1st_ats_pers'].append(sld)
                    
                    elif data['ats'] == "0":
                        if data['identifier_flag'] == 1 and data['pers_info_flag'] == 1:
                            data_bridging_counts[app][category]['dests_1st_both'].append(sld)
                        elif data['identifier_flag'] == 1:
                            data_bridging_counts[app][category]['dests_1st_ids'].append(sld)
                        elif data['pers_info_flag'] == 1:
                            data_bridging_counts[app][category]['dests_1st_pers'].append(sld)
                
                elif data['party'] == utils.THIRD:
                    all_data_type_sets.append(data['L3_data_types'])
                    if data['ats'] == "1":
                        if data['identifier_flag'] == 1 and data['pers_info_flag'] == 1:
                            data_bridging_counts[app][category]['dests_3rd_ats_both'].append(sld)
                        elif data['identifier_flag'] == 1:
                            data_bridging_counts[app][category]['dests_3rd_ats_ids'].append(sld)
                        elif data['pers_info_flag'] == 1:
                            data_bridging_counts[app][category]['dests_3rd_ats_pers'].append(sld)
                    
                    elif data['ats'] == "0":
                        if data['identifier_flag'] == 1 and data['pers_info_flag'] == 1:
                            data_bridging_counts[app][category]['dests_3rd_both'].append(sld)
                        elif data['identifier_flag'] == 1:
                            data_bridging_counts[app][category]['dests_3rd_ids'].append(sld)
                        elif data['pers_info_flag'] == 1:
                            data_bridging_counts[app][category]['dests_3rd_pers'].append(sld)

            if len(all_data_type_sets) > 0:
                # get most common data type set, min set, max set
                max_len_list, max_len = get_max_length_sublist(all_data_type_sets)
                print(f" - max len data type list: {max_len}")
                print(f" - max data type list: {max_len_list}")

                min_len_list, min_len = get_min_length_sublist(all_data_type_sets)
                print(f" - min len data type list: {min_len}")
                print(f" - min data type list: {min_len_list}")
                
                most_common_list, most_common_list_len = get_most_common_sublist(all_data_type_sets)
                print(f" - most common len data type list: {most_common_list_len}")
                print(f" - most common data type list: {most_common_list[0][0]}")

                linkable_data_types_subsets[app][category]["max_len_list"] = max_len_list
                linkable_data_types_subsets[app][category]["max_len"] = max_len
                linkable_data_types_subsets[app][category]["min_len_list"] = min_len_list
                linkable_data_types_subsets[app][category]["min_len"] = min_len
                linkable_data_types_subsets[app][category]["most_common_list"] = most_common_list[0][0]
                linkable_data_types_subsets[app][category]["most_common_list_len"] = most_common_list_len
            else:
                print(" - all_data_type_sets is length 0")
                linkable_data_types_subsets[app][category]["max_len_list"] = []
                linkable_data_types_subsets[app][category]["max_len"] = []
                linkable_data_types_subsets[app][category]["min_len_list"] = []
                linkable_data_types_subsets[app][category]["min_len"] = []
                linkable_data_types_subsets[app][category]["most_common_list"] = []
                linkable_data_types_subsets[app][category]["most_common_list_len"] = []
        print('')

    with open(utils.ANALYSIS_OUT_DIR + os.sep + "bothplatforms_data_bridging_data_types_subsets_data.json", "w") as out:
        json.dump(linkable_data_types_subsets, out, indent=4)
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/bothplatforms_data_bridging_data_types_subsets_data.json\n")

    # see if the max and common are similar across age categories/logged out
    print(f"[.] Max subset list length across all services: ")
    for platform, vals in linkable_data_types_subsets.items():
        for category, data in vals.items():
            print(f' - {platform}, {category}, max subset list length: {data["max_len"]}')
    print('')

    all_most_common = {}
    for platform, vals in linkable_data_types_subsets.items():
        for category, data in vals.items():
            all_most_common[category] = data['most_common_list']
    single_most_common = set()
    for i in all_most_common.values():
        if i != []:
            temp = sorted(list(i))
            single_most_common.add(tuple(temp))
    print(f"[.] Most common set of linkable data: {single_most_common}\n")

    # save to json
    with open(utils.ANALYSIS_OUT_DIR + os.sep + 'bothplatforms_data_bridging_destination_counts.json', 'w') as out:
        json.dump(data_bridging_counts, out, indent=4) 
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/bothplatforms_data_bridging_destination_counts.json\n")

    # process to generate alluvial of orgs for data linkage 3rd parties 
    def dest_helper_linkage(domain_mapping_data, platform, i):
        manual_sld_owners = MANUAL_ORGS
        org_value = domain_mapping_data[platform][i]['tracker_radar_owner_data'].get('name') or 'Unknown'
        if org_value == "Unknown":
            if i in manual_sld_owners.keys():
                # print(i)
                org_value = manual_sld_owners[i]
                # print(org_value)
            elif org_value == 'Unknown':
                whoisorg = domain_mapping_data[platform][i]['whois_response'].get('org') or 'Unknown'
                if whoisorg != None and not ("c/o whoisproxy.com" in whoisorg or "Identity Protection Service" in whoisorg or "DATA REDACTED" in whoisorg or  whoisorg == "" or  "Domains By Proxy" in whoisorg or "Privacy service provided by" in whoisorg or "Contact Privacy Inc. Customer" in whoisorg):
                    org_value = whoisorg
            else:
                org_value = "Unknown"
        return org_value
    
    def alluvial_data_helper(domains, platform_list, platform, trace_list, org, org_mapping, age_str, i, domain_mapping_data):
        domains.append(i)
        platform_list.append(platform)
        trace_list.append(age_str)
        org_val = dest_helper_linkage(domain_mapping_data, platform, i)
        org.append(org_val)
        org_mapping[i] = org_val
        return domains, platform_list, trace_list, org, org_mapping

    with open(utils.INTER_DATA_DIR + os.sep + f'data_flow_domain_mapping.json', 'r') as infile:
        domain_mapping_data = json.load(infile)

    platform_list, domains, trace_list, org = [], [], [], []
    frequency_of_domains_by_category = {}
    org_mapping = {}
    for platform, v1 in data_bridging_counts.items():        
        frequency_of_domains_by_category[platform] = {}
        for age_cat, data in v1.items():
            frequency_of_domains_by_category[platform][age_cat] = {}
            if utils.CHILD_NUM in age_cat:
                age_cat_str = 'child'
                for i in data['dests_3rd_ats_both']:
                    domains, platform_list, trace_list, org, org_mapping = alluvial_data_helper(domains, platform_list, platform, trace_list, org, org_mapping, age_cat_str, i, domain_mapping_data)
                    frequency_of_domains_by_category[platform][age_cat][i] = data_dict_per_app_dests[platform][age_cat][i]['frequency']
                for i in data['dests_3rd_both']:
                    domains, platform_list, trace_list, org, org_mapping = alluvial_data_helper(domains, platform_list, platform, trace_list, org, org_mapping, age_cat_str, i, domain_mapping_data)

            elif utils.TEEN_NUM in age_cat:
                age_cat_str = 'teen'
                for i in data['dests_3rd_ats_both']:
                    domains, platform_list, trace_list, org, org_mapping = alluvial_data_helper(domains, platform_list, platform, trace_list, org, org_mapping, age_cat_str, i, domain_mapping_data)
                    frequency_of_domains_by_category[platform][age_cat][i] = data_dict_per_app_dests[platform][age_cat][i]['frequency']
                for i in data['dests_3rd_both']:
                    domains, platform_list, trace_list, org, org_mapping = alluvial_data_helper(domains, platform_list, platform, trace_list, org, org_mapping, age_cat_str, i, domain_mapping_data)
                                                                                                
            elif utils.ADULT_NUM in age_cat:
                age_cat_str = 'adult'
                for i in data['dests_3rd_ats_both']:
                    domains, platform_list, trace_list, org, org_mapping = alluvial_data_helper(domains, platform_list, platform, trace_list, org, org_mapping, age_cat_str, i, domain_mapping_data)
                    frequency_of_domains_by_category[platform][age_cat][i] = data_dict_per_app_dests[platform][age_cat][i]['frequency']
                for i in data['dests_3rd_both']:
                    domains, platform_list, trace_list, org, org_mapping = alluvial_data_helper(domains, platform_list, platform, trace_list, org, org_mapping, age_cat_str, i, domain_mapping_data)
                    
            else:
                age_cat_str = 'logged out'
                for i in data['dests_3rd_ats_both']:
                    domains, platform_list, trace_list, org, org_mapping = alluvial_data_helper(domains, platform_list, platform, trace_list, org, org_mapping, age_cat_str, i, domain_mapping_data)
                    frequency_of_domains_by_category[platform][age_cat][i] = data_dict_per_app_dests[platform][age_cat][i]['frequency']
                for i in data['dests_3rd_both']:
                    domains, platform_list, trace_list, org, org_mapping = alluvial_data_helper(domains, platform_list, platform, trace_list, org, org_mapping, age_cat_str, i, domain_mapping_data)
                    
    # top frequent data linkage domains by app and age trace
    out_dict = {
        'Service': [],
        'Domains': [],
        'Category': [],
        'Organization': [],
        'Frequency': []
    }
    print('[+] Generating csv with top most common domains sent linkable data by age category...')
    for platform, data1 in frequency_of_domains_by_category.items():
        # print(f"[.] {platform}")
        for age_cat, data2 in data1.items():
            if utils.CHILD_NUM in age_cat:
                age_cat_str = 'Child'
            elif utils.TEEN_NUM in age_cat:
                age_cat_str = 'Adolescent'
            elif utils.ADULT_NUM in age_cat:
                age_cat_str = 'Adult'
            else:
                age_cat_str = 'Logged Out'
            # print(f"[.] {age_cat}")
            sorted_domains = sorted(data2.items(), key=lambda x: x[1], reverse=True)
            # print(f"[.] top 10 most common data linkage domains across dataset for {platform}, {age_cat}:")
            if len(sorted_domains) < 10:
                for i in range(len(sorted_domains)):
                    # print(sorted_domains[i], org_mapping[sorted_domains[i][0]])
                    out_dict['Service'].append(platform)
                    out_dict['Domains'].append(sorted_domains[i][0])
                    out_dict['Category'].append(age_cat_str)
                    out_dict['Organization'].append(org_mapping[sorted_domains[i][0]])
                    out_dict['Frequency'].append(sorted_domains[i][1])
            else:
                for i in range(10):
                    # print(sorted_domains[i], org_mapping[sorted_domains[i][0]])
                    out_dict['Service'].append(platform)
                    out_dict['Domains'].append(sorted_domains[i][0])
                    out_dict['Category'].append(age_cat_str)
                    out_dict['Organization'].append(org_mapping[sorted_domains[i][0]])
                    out_dict['Frequency'].append(sorted_domains[i][1])
            # print('')
    data_file = open(utils.ANALYSIS_OUT_DIR + os.sep + 'bothplatforms_data_bridging_destination_alluvial_data_top_most_contacted_domains_ATS_only.csv', 'w', newline='')
    csv_writer = csv.writer(data_file)
    count = 0
    for i in range(len(out_dict['Service'])):
        if count == 0:
            header = out_dict.keys()
            csv_writer.writerow(header)
            count += 1
        csv_writer.writerow([out_dict['Service'][i], out_dict['Domains'][i], out_dict['Category'][i], out_dict['Organization'][i], out_dict['Frequency'][i]])
    data_file.close()
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/bothplatforms_data_bridging_destination_alluvial_data_top_most_contacted_domains_ATS_only.csv")