#!/usr/bin/python

'''
This script does the following:
1) extracts unique data flows from the data flow files generated from construct_data_flows.py and separates them 
   into different JSON files per service and per age/trace category for ease of viewing.
2) separates the data linkability results into separate JSON files per service and per age/trace category for ease of viewing.
The files generated as a result of running this script are provided in the dataset release (the only difference is the unique JSON keys
generated for the data flow files everytime this script is run.)
'''

import json
import os
import uuid
from utils import utils


def name_readability(input_str):
    if utils.CHILD_NUM in input_str:
        new_str = input_str.strip(utils.CHILD_NUM)
        new_str += '_' + utils.CHILD
    elif utils.TEEN_NUM in input_str:
        new_str = input_str.strip(utils.TEEN_NUM)
        new_str += '_' + utils.TEEN
    elif utils.ADULT_NUM in input_str:
        new_str = input_str.strip(utils.ADULT_NUM)
        new_str += '_' + utils.ADULT
    else:
        new_str = input_str
    return new_str

def main():
    ## data linkability per service and age
    with open(utils.ANALYSIS_OUT_DIR + os.sep + 'bothplatforms_data_bridging_destination_dict.json', 'r') as fp:
        data_linkability_dict = json.load(fp) 

    for service, data in data_linkability_dict.items():
        for age_cat, dest_data in data.items():
            file_name_str = name_readability(age_cat)
            data_link_out_path = utils.ANALYSIS_OUT_DIR + os.sep + 'data_linkability_per_service_and_age'
            if not os.path.isdir(data_link_out_path):
                os.makedirs(data_link_out_path)
            with open(data_link_out_path + os.sep + f'{file_name_str}-data_linkability_destinations_dict.json', 'w') as fp:
                json.dump(dest_data, fp, indent=4)
            print(f"Generated {data_link_out_path}/{file_name_str}-data_linkability_destinations_dict.json")


    ## data flows per service and age
    with open(utils.INTER_DATA_DIR + os.sep + 'labeled_data_dict_slds_with_owner_tuple-website_full_trace.json', "r") as infile:
        web_full_data = json.load(infile)
    with open(utils.INTER_DATA_DIR + os.sep + 'labeled_data_dict_slds_with_owner_tuple-mobile_full_trace.json', "r") as infile:
        mobile_full_data = json.load(infile)

    with open(utils.INTER_DATA_DIR + os.sep + 'labeled_data_dict_slds_with_owner_tuple-website_logged_in_trace.json', "r") as infile:
        web_login_data = json.load(infile)
    with open(utils.INTER_DATA_DIR + os.sep + 'labeled_data_dict_slds_with_owner_tuple-mobile_logged_in_trace.json', "r") as infile:
        mobile_login_data = json.load(infile)

    with open(utils.INTER_DATA_DIR + os.sep + 'labeled_data_dict_slds_with_owner_tuple-website_logged_out_trace.json', "r") as infile:
        web_logout_data = json.load(infile)
    with open(utils.INTER_DATA_DIR + os.sep + 'labeled_data_dict_slds_with_owner_tuple-mobile_logged_out_trace.json', "r") as infile:
        mobile_logout_data = json.load(infile)


    ## merge each trace together, then create per-service and per-age group separated files
    data_flow_dict = {} 
    ages = [utils.CHILD_NUM, utils.TEEN_NUM, utils.ADULT_NUM] 
    age_cat_list = []
    for app in utils.SERVICE_NAMES_MAIN:
        for age in ages:
            age_cat = app +  age
            age_cat_list.append(age_cat)
    # print(age_cat_list)

    all_unique_data_dict = {}
    for age_cat in age_cat_list:
        print(f'{age_cat}')
        data_flow_dict = {} ## per app+age category -- merging across web/mobile for each app+age category
        for obj in [web_full_data, mobile_full_data, web_login_data, mobile_login_data]:
            if age_cat in obj.keys():
                for flow in obj[age_cat]:
                    new_tuple = {
                        "fqdn": flow[6],
                        "sld": flow[0],
                        "organization": flow[1],
                        "key": flow[5],
                        "data_type_label": flow[3],
                        "party": flow[2],
                        "ats": flow[4]
                    }
                    if new_tuple not in data_flow_dict.values():
                        data_flow_dict[str(uuid.uuid1())] = new_tuple

        all_unique_data_dict[age_cat] = data_flow_dict
        file_name_str = name_readability(age_cat)
        if "YouTube_child" in file_name_str :
            file_name_str = "YouTubeKids_child"
        data_flows_out_path = utils.ANALYSIS_OUT_DIR + os.sep + 'data_flows_per_service_and_age'
        if not os.path.isdir(data_flows_out_path):
                os.makedirs(data_flows_out_path)
        with open(data_flows_out_path + os.sep + f'{file_name_str}-unique_data_flows_dict.json', 'w') as fp:
            json.dump(data_flow_dict, fp, indent=4)
        print(f"Generated {data_flows_out_path}/{file_name_str}-unique_data_flows_dict.json")
        
    for app in utils.SERVICE_NAMES_ALL:
        print(f'{app} logged out')
        data_flow_dict = {} ## per app+age category -- merging across web/mobile for each app+age category
        for obj in [web_logout_data, mobile_logout_data]:
            if app in obj.keys():
                for flow in obj[app]:
                    new_tuple = {
                        "fqdn": flow[6],
                        "sld": flow[0],
                        "organization": flow[1],
                        "key": flow[5],
                        "data_type_label": flow[3],
                        "party": flow[2],
                        "ats": flow[4]
                    }
                    if new_tuple not in data_flow_dict.values():
                        data_flow_dict[str(uuid.uuid1())] = new_tuple
                
        all_unique_data_dict[app] = data_flow_dict
        data_flows_out_path = utils.ANALYSIS_OUT_DIR + os.sep + 'data_flows_per_service_and_age'
        if not os.path.isdir(data_flows_out_path):
                os.makedirs(data_flows_out_path)
        with open(data_flows_out_path + os.sep + f'{app}_loggedout-unique_data_flows_dict.json', 'w') as fp:
            json.dump(data_flow_dict, fp, indent=4) 
        print(f"Generated {data_flows_out_path}/{app}_loggedout-unique_data_flows_dict.json")



if __name__ == "__main__":
    main()