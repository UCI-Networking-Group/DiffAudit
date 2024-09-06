#!/usr/bin/python

'''
This script outputs analysis results from the data flows observed, as seen in the paper, including:
- unique data flows per service/age and trace group, organized with L2 level of ontology as in the paper
- data linkage results
- statistics about domains contacted across dataset and data types observed in dataset

This script also calls extract_unique.py, which does the following:
- reorganizes the data flow files ("labeled_data_dict_...json" generated from construct_data_flows.py) into 
  JSON files per service/trace category, and only with unique data flows
- separates the data linkability results into per-service/trace category JSON files
The resulting files generated from extract_unique.py are provided with the dataset release (note that the unique JSON keys will be different
each time that script is run).
'''

import os
import json
import sys
import subprocess

sys.path.append(os.path.abspath('../'))
from data_linkability import analyze_data_linkability
from destinations import destination_only_analysis
from data_flow_analysis import compare_mobile_web, compute_data_type_coverage
from utils import utils

def main():
    # Check directories
    if not os.path.isdir(utils.INTER_DATA_DIR):
        print(f"### ERROR: You need to have {utils.INTER_DATA_DIR} directory with the labeled data flow JSON files provided in our dataset release. Exiting.")
        return
    
    # Create analysis_outputs directory if does not exist
    if not os.path.isdir(utils.ANALYSIS_OUT_DIR):
        os.makedirs(utils.ANALYSIS_OUT_DIR)
    
    # Using labeled data flow JSON files generated from construct_data_flows.py
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

    # [1] Analyze data linkability 
    print(f"\n######################################## Data Linkability Analysis ########################################\n")
    analyze_data_linkability(web_full_data, web_login_data, web_logout_data, mobile_full_data, mobile_login_data, mobile_logout_data)
    
    # [2] Analyze destinations contacted across dataset
    print(f"\n######################################## Destination Only Analysis ########################################\n")
    destination_only_analysis(web_full_data, web_login_data, web_logout_data, mobile_full_data, mobile_login_data, mobile_logout_data)

    # [3] Count data types observed in all of dataset
    print(f"\n######################################## Count Data Types Observed in Dataset ########################################\n")
    compute_data_type_coverage(web_full_data, web_login_data, web_logout_data, mobile_full_data, mobile_login_data, mobile_logout_data)

    # [4] Prepare data flow dataset and generate latex data flow table for auditing and analysis
    print(f"\n######################################## Generate Latex Data Flow Table for Auditing ########################################\n")
    compare_mobile_web(web_login_data, mobile_login_data, web_full_data, mobile_full_data, web_logout_data, mobile_logout_data)

    # [5] Extract unique data flows from overall labeled_data_dict JSON files, and separate into per-service/trace JSON files
    print(f"\n######################################## Reorganize Data Flow and Data Linkability JSONs ########################################\n")
    ret = subprocess.check_call(["python3", "extract_unique.py"])


if __name__ == "__main__":
    main()