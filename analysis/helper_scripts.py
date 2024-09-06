#!/usr/bin/python

'''
This script provides helper functions for various parts of analysis_pipeline.py
'''

import os
import json
import copy
import sys

sys.path.append(os.path.abspath('../'))
from data_flows.labeling_utils.ontology_3_levels import data_type_categories_ontology
from utils import utils

def merge_data(data_dict, app_dict): 
    ## Helper function to merge data flow data per age group across traces
    for k, v in data_dict.items():
        if "_" in k:
            if utils.CHILD_NUM in k:
                app_name = k.replace(utils.CHILD_NUM, "")
                for i in v:
                    new_tup = (i[0], i[2], i[3], i[4], i[6]) ## sld, party, data type, ats label, host
                    app_dict[app_name][utils.CHILD].add(new_tup)
            
            elif utils.TEEN_NUM in k:
                app_name = k.replace(utils.TEEN_NUM, "")
                for i in v:
                    new_tup = (i[0], i[2], i[3], i[4], i[6]) 
                    app_dict[app_name][utils.TEEN].add(new_tup)
            
            elif utils.ADULT_NUM in k:
                app_name = k.replace(utils.ADULT_NUM, "")
                for i in v:
                    new_tup = (i[0], i[2], i[3], i[4], i[6]) 
                    app_dict[app_name][utils.ADULT].add(new_tup)
        
        else:
            app_name = k
            for i in v:
                new_tup = (i[0], i[2], i[3], i[4], i[6]) 
                app_dict[app_name].add(new_tup)
    return app_dict



def helper_create_ontology_lists(data_flows_per_app, platform, trace_select):
    ## Helper function to extract unique data flows and organize based on which ontology categories they 
    ## belong to, which is used to create data flow latex tables for analysis

    collect_share_by_data_category_inner_dict = {
        "child_collect": 0,     ## first party, NO ATS
        "child_collect_ats": 0, ## first party, ATS 
        "child_share_third": 0, ## third party, NO ATS
        "child_share_ats": 0,   ## third party, ATS

        "teen_collect": 0,
        "teen_collect_ats": 0, 
        "teen_share_third": 0,
        "teen_share_ats": 0,

        "adult_collect": 0,
        "adult_collect_ats": 0, 
        "adult_share_third": 0,
        "adult_share_ats": 0,
    }

    collect_share_by_data_category_overall_dict_L1 = {}
    collect_share_by_data_category_overall_dict_L2 = {}
    collect_share_by_data_category_overall_dict_L3 = {}

    for app, flow_data in data_flows_per_app.items():
        collect_share_by_data_category_overall_dict_L1[app] = {}
        collect_share_by_data_category_overall_dict_L2[app] = {}
        collect_share_by_data_category_overall_dict_L3[app] = {}

        ## check the flows for the L3 categories, then add the corresponding L1 and L2 categories to the dictionary                    
        for age, flows in flow_data.items():
            for tup in flows:
                party = tup[1] ## sld, party, data type, ats label, host
                data_label = tup[2]
                ats_flag = tup[3]

                for L1, L2_list in data_type_categories_ontology.items():
                    ## L1 based dictionary
                    if L1 not in collect_share_by_data_category_overall_dict_L1[app].keys():
                        collect_share_by_data_category_overall_dict_L1[app][L1] = copy.deepcopy(collect_share_by_data_category_inner_dict)

                    ## L2 based dictionary
                    for L2, L3_categories in L2_list.items():
                        if L2 not in collect_share_by_data_category_overall_dict_L2[app].keys():
                            collect_share_by_data_category_overall_dict_L2[app][L2] = copy.deepcopy(collect_share_by_data_category_inner_dict)

                        ## if label is in the L3 categories list, then update the corresponding L1 and L2 dictionaries with the flag that this data flow appeared
                        if data_label in L3_categories:
                            if data_label not in collect_share_by_data_category_overall_dict_L3[app].keys():
                                collect_share_by_data_category_overall_dict_L3[app][data_label] = copy.deepcopy(collect_share_by_data_category_inner_dict)

                            ## first party collection, NON ATS domain
                            if party == utils.FIRST and ats_flag == '0':
                                # print(f"{tup} --> {L1}, {L2}, {age}_collect")
                                collect_share_by_data_category_overall_dict_L1[app][L1][f"{age}_collect"] = 1
                                collect_share_by_data_category_overall_dict_L2[app][L2][f"{age}_collect"] = 1
                                collect_share_by_data_category_overall_dict_L3[app][data_label][f"{age}_collect"] = 1

                            ## first party collection with ATS domain
                            elif party == utils.FIRST and ats_flag == '1':
                                # print(f"{tup} --> {L1}, {L2}, {age}_collect_ats")
                                collect_share_by_data_category_overall_dict_L1[app][L1][f"{age}_collect_ats"] = 1
                                collect_share_by_data_category_overall_dict_L2[app][L2][f"{age}_collect_ats"] = 1
                                collect_share_by_data_category_overall_dict_L3[app][data_label][f"{age}_collect_ats"] = 1
                                
                            ## third party sharing to NON ATS domain
                            elif party == utils.THIRD and ats_flag == '0':   
                                # print(f"{tup} --> {L1}, {L2}, {age}_share_third")
                                collect_share_by_data_category_overall_dict_L1[app][L1][f"{age}_share_third"] = 1
                                collect_share_by_data_category_overall_dict_L2[app][L2][f"{age}_share_third"] = 1
                                collect_share_by_data_category_overall_dict_L3[app][data_label][f"{age}_share_third"] = 1
                                
                            ## third party sharing to ATS domain
                            elif party == utils.THIRD and ats_flag == '1':
                                # print(f"{tup} --> {L1}, {L2}, {age}_share_ats")
                                collect_share_by_data_category_overall_dict_L1[app][L1][f"{age}_share_ats"] = 1
                                collect_share_by_data_category_overall_dict_L2[app][L2][f"{age}_share_ats"] = 1  
                                collect_share_by_data_category_overall_dict_L3[app][data_label][f"{age}_share_ats"] = 1 

    l1_filename = f"{platform}_collect_share_by_data_category_overall_dict_L1_{trace_select}.json"
    l2_filename = f"{platform}_collect_share_by_data_category_overall_dict_L2_{trace_select}.json"
    l3_filename = f"{platform}_collect_share_by_data_category_overall_dict_L3_{trace_select}.json"
    
    with open(utils.ANALYSIS_OUT_DIR + os.sep + l1_filename, "w") as f:
        json.dump(collect_share_by_data_category_overall_dict_L1, f, indent=4)

    with open(utils.ANALYSIS_OUT_DIR + os.sep + l2_filename, "w") as f:
        json.dump(collect_share_by_data_category_overall_dict_L2, f, indent=4)

    with open(utils.ANALYSIS_OUT_DIR + os.sep + l3_filename, "w") as f:
        json.dump(collect_share_by_data_category_overall_dict_L3, f, indent=4)
    
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/{l1_filename}")
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/{l2_filename}")
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/{l3_filename}")

    return l1_filename, l2_filename, l3_filename


def helper_create_ontology_sets_loggedout(data_flows_per_app, platform):
    ## Helper function to extract unique data flows for the logged out traces only and organize based on
    ## which ontology categories they belong to, which is used to create data flow latex tables for analysis

    collect_share_by_data_category_inner_dict = {
        "loggedout_collect": 0,
        "loggedout_collect_ats": 0,
        "loggedout_share_third": 0,
        "loggedout_share_ats": 0,
    }

    collect_share_by_data_category_overall_dict_L1 = {}
    collect_share_by_data_category_overall_dict_L2 = {}
    collect_share_by_data_category_overall_dict_L3 = {}

    for app, logged_out_flows in data_flows_per_app.items():
        # print(app, "loggedouttrace")
        collect_share_by_data_category_overall_dict_L1[app] = {}
        collect_share_by_data_category_overall_dict_L2[app] = {}
        collect_share_by_data_category_overall_dict_L3[app] = {}

        for tup in logged_out_flows:
            party = tup[1]  ## sld, party, data type, ats label, host
            data_label = tup[2]
            ats_flag = tup[3]

            for L1, L2_list in data_type_categories_ontology.items():
                ## L1 based dictionary
                if L1 not in collect_share_by_data_category_overall_dict_L1[app].keys():
                    collect_share_by_data_category_overall_dict_L1[app][L1] = copy.deepcopy(collect_share_by_data_category_inner_dict)

                ## L2 based dictionary
                for L2, L3_categories in L2_list.items():
                    if L2 not in collect_share_by_data_category_overall_dict_L2[app].keys():
                        collect_share_by_data_category_overall_dict_L2[app][L2] = copy.deepcopy(collect_share_by_data_category_inner_dict)

                    ## check the flows for the L3 categories, then add the corresponding L1 and L2 categories to the dictionary                    
                    ## if label is in the L3 categories list, then update the corresponding L1 and L2 dictionaries with the flag that this data flow appeared
                    if data_label in L3_categories:
                        if data_label not in collect_share_by_data_category_overall_dict_L3[app].keys():
                            collect_share_by_data_category_overall_dict_L3[app][data_label] = copy.deepcopy(collect_share_by_data_category_inner_dict)

                        ## first party collection
                        if party == utils.FIRST and ats_flag == '0':
                            # print(f"{tup} --> {L1}, {L2}, loggedout_collect")
                            collect_share_by_data_category_overall_dict_L1[app][L1][f"loggedout_collect"] = 1
                            collect_share_by_data_category_overall_dict_L2[app][L2][f"loggedout_collect"] = 1
                            collect_share_by_data_category_overall_dict_L3[app][data_label][f"loggedout_collect"] = 1

                        ## first party collection and it is ATS domain
                        elif party == utils.FIRST and ats_flag == '1':
                            # print(f"{tup} --> {L1}, {L2}, loggedout_collect_ats")
                            collect_share_by_data_category_overall_dict_L1[app][L1][f"loggedout_collect_ats"] = 1
                            collect_share_by_data_category_overall_dict_L2[app][L2][f"loggedout_collect_ats"] = 1
                            collect_share_by_data_category_overall_dict_L3[app][data_label][f"loggedout_collect_ats"] = 1
                        
                        ## third party sharing and NOT ATS domain
                        elif party == utils.THIRD and ats_flag == '0':
                            # print(f"{tup} --> {L1}, {L2}, loggedout_share_third")
                            collect_share_by_data_category_overall_dict_L1[app][L1][f"loggedout_share_third"] = 1
                            collect_share_by_data_category_overall_dict_L2[app][L2][f"loggedout_share_third"] = 1
                            collect_share_by_data_category_overall_dict_L3[app][data_label][f"loggedout_share_third"] = 1
                            
                        ## third party sharing to ATS domain
                        elif party == utils.THIRD and ats_flag == '1':
                            # print(f"{tup} --> {L1}, {L2}, loggedout_share_ats")
                            collect_share_by_data_category_overall_dict_L1[app][L1][f"loggedout_share_ats"] = 1
                            collect_share_by_data_category_overall_dict_L2[app][L2][f"loggedout_share_ats"] = 1
                            collect_share_by_data_category_overall_dict_L3[app][data_label][f"loggedout_share_ats"] = 1
        # print('')

    l1_filename = f"{platform}_collect_share_by_data_category_overall_dict_L1_loggedout.json"
    l2_filename = f"{platform}_collect_share_by_data_category_overall_dict_L2_loggedout.json"
    l3_filename = f"{platform}_collect_share_by_data_category_overall_dict_L3_loggedout.json"
    with open(utils.ANALYSIS_OUT_DIR + os.sep + l1_filename, "w") as f:
        json.dump(collect_share_by_data_category_overall_dict_L1, f, indent=4)

    with open(utils.ANALYSIS_OUT_DIR + os.sep + l2_filename, "w") as f:
        json.dump(collect_share_by_data_category_overall_dict_L2, f, indent=4)
    
    with open(utils.ANALYSIS_OUT_DIR + os.sep + l3_filename, "w") as f:
        json.dump(collect_share_by_data_category_overall_dict_L3, f, indent=4)
    
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/{l1_filename}")
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/{l2_filename}")
    print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/{l3_filename}")

    return l1_filename, l2_filename, l3_filename

