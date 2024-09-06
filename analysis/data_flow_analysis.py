#!/usr/bin/python

'''
This script provides functions for the data flow analysis portion of analysis_pipeline.py
'''

import os
import json
import copy
import sys

sys.path.append(os.path.abspath('../'))
from data_flows.labeling_utils.ontology_L3_to_L1 import data_type_categories_ontology_direct
from analysis.helper_scripts import merge_data, helper_create_ontology_lists, helper_create_ontology_sets_loggedout
from utils import utils

def compute_data_type_coverage(web_full_data, web_login_data, web_logout_data, mobile_full_data, mobile_login_data, mobile_logout_data):
    ## Compute how many data type categories are found in the dataset
    print("[+] Computing number of data type categories observed across dataset...")
    category_labels = sorted(list(data_type_categories_ontology_direct.keys()))
    category_coverage_flags = {} 
    for i in category_labels:
        category_coverage_flags[i] = 0

    to_process = [web_full_data, web_login_data, mobile_full_data, mobile_login_data, web_logout_data, mobile_logout_data]
    for data_dict in to_process:
        for app, data_flows in data_dict.items():
            for tup in data_flows:
                data_label = tup[3]
                category_coverage_flags[data_label] = 1

    obs = 0
    obs_list = set()
    for k, v in category_coverage_flags.items():
        # print(k, v)
        if v == 1:
            obs += 1
            obs_list.add(k)
    print("[.] Num data type categories observed: ", obs)
    print("[.] Num data type categories not observed: ", len(category_labels) - obs)


def compare_mobile_web_helper(input_data, platform, trace):
    ## Script to merge mobile and web data together for each trace group
    if trace == "loggedout":
        ## logged out only
        logout_app_dict, logout_app_dict_tosave = {}, {}
        for i in utils.SERVICE_NAMES_ALL:
            logout_app_dict[i] = set()
            logout_app_dict_tosave[i] = []
        logout_app_dict = merge_data(input_data, logout_app_dict)

        for k, v in logout_app_dict.items():
            logout_app_dict_tosave[k] = list(v)
        with open(utils.ANALYSIS_OUT_DIR + os.sep + f"{platform}_unique_dataflows_{trace}.json", "w") as out:
            json.dump(logout_app_dict_tosave, out, indent=4)
        print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/{platform}_unique_dataflows_{trace}.json")
        
        return logout_app_dict_tosave

    else:
        ## logged in and full merged together per platform
        app_dict_inner = {utils.CHILD: set(), utils.TEEN: set(), utils.ADULT: set()}    
        app_dict_inner_lists = {utils.CHILD: [], utils.TEEN: [], utils.ADULT: []} 

        app_dict, app_dict_to_save = {}, {}
        for i in utils.SERVICE_NAMES_MAIN:
            app_dict[i] = copy.deepcopy(app_dict_inner)
            app_dict_to_save[i] = copy.deepcopy(app_dict_inner_lists)

        for data_dict in input_data:
            app_dict = merge_data(data_dict, app_dict)

        for app, age_data in app_dict.items():
            for age, data in age_data.items():
                app_dict_to_save[app][age] = list(data)
        
        with open(utils.ANALYSIS_OUT_DIR + os.sep + f"{platform}_unique_dataflows_{trace}.json", "w") as out:
            json.dump(app_dict_to_save, out, indent=4)
        print(f"[.] Generated: {utils.ANALYSIS_OUT_DIR}/{platform}_unique_dataflows_{trace}.json")
        
        return app_dict_to_save



def create_web_mobile_comp_latex_table(website_L2_data_dict_fulllogin, mobile_L2_data_dict_fulllogin, website_L2_data_dict_logout, mobile_L2_data_dict_logout, level, l3_data_types_obs=""):
    # Generate web/mobile data flow comparison latex table from previously generated files
    per_app_strs = ""
    latex_flag = {
        '00': '\\NO', ## neither
        '01': '\\mobile',
        '10': '\\website',
        '11': '\\both', ## both
    }
    ages = [utils.CHILD, utils.TEEN, utils.ADULT]
    apps = sorted(website_L2_data_dict_fulllogin.keys())

    if level == '2':
        data_categories = website_L2_data_dict_fulllogin['Duolingo'].keys()
    elif level == "3":
        data_categories = sorted(l3_data_types_obs)

    #### L2 account trace+loggedin vs logged out, for both web and mobile
    for app in apps:
        # print(app.upper())
        for data_category in data_categories:
            str_vals = []
            for age in ages:

                ### data category is in web -- ? + __
                if data_category in website_L2_data_dict_fulllogin[app].keys():
                    collect_code = str(website_L2_data_dict_fulllogin[app][data_category][f"{age}_collect"])
                    # print(f"collect_code: {collect_code}")

                    collect_ats_code = str(website_L2_data_dict_fulllogin[app][data_category][f"{age}_collect_ats"])
                    # print(f"collect_ats_code: {collect_ats_code}")

                    share_third_code = str(website_L2_data_dict_fulllogin[app][data_category][f"{age}_share_third"])
                    # print(f"share_third_code: {share_third_code}")

                    share_ats_code = str(website_L2_data_dict_fulllogin[app][data_category][f"{age}_share_ats"])
                    # print(f"share_ats_code: {share_ats_code}")
                    
                    ### data category is in web and mobile -- ? + ?
                    if data_category in mobile_L2_data_dict_fulllogin[app].keys():
                        collect_code += str(mobile_L2_data_dict_fulllogin[app][data_category][f"{age}_collect"])
                        str_vals.append(latex_flag[collect_code])

                        collect_ats_code += str(mobile_L2_data_dict_fulllogin[app][data_category][f"{age}_collect_ats"])
                        str_vals.append(latex_flag[collect_ats_code])

                        share_third_code += str(mobile_L2_data_dict_fulllogin[app][data_category][f"{age}_share_third"])
                        str_vals.append(latex_flag[share_third_code])

                        share_ats_code += str(mobile_L2_data_dict_fulllogin[app][data_category][f"{age}_share_ats"])
                        str_vals.append(latex_flag[share_ats_code])

                    ### data category is in web and NOT mobile -- ? + 0
                    elif data_category not in mobile_L2_data_dict_fulllogin[app].keys():
                        collect_code += '0'
                        str_vals.append(latex_flag[collect_code])

                        collect_ats_code += '0'
                        str_vals.append(latex_flag[collect_ats_code])

                        share_third_code += '0'
                        str_vals.append(latex_flag[share_third_code])

                        share_ats_code += '0'
                        str_vals.append(latex_flag[share_ats_code])
                
                ### not in web, but in the mobile -- 0 + ?
                elif data_category not in website_L2_data_dict_fulllogin[app].keys() and data_category in mobile_L2_data_dict_fulllogin[app].keys():
                    collect_code = '0' + str(mobile_L2_data_dict_fulllogin[app][data_category][f"{age}_collect"])
                    # print(f"collect_code: {collect_code}")
                    str_vals.append(latex_flag[collect_code])

                    collect_ats_code = '0' + str(mobile_L2_data_dict_fulllogin[app][data_category][f"{age}_collect_ats"])
                    # print(f"collect_ats_code: {collect_ats_code}")
                    str_vals.append(latex_flag[collect_ats_code])

                    share_third_code = '0' + str(mobile_L2_data_dict_fulllogin[app][data_category][f"{age}_share_third"])
                    # print(f"share_third_code: {share_third_code}")
                    str_vals.append(latex_flag[share_third_code])

                    share_ats_code = '0' + str(mobile_L2_data_dict_fulllogin[app][data_category][f"{age}_share_ats"])
                    # print(f"share_ats_code: {share_ats_code}")
                    str_vals.append(latex_flag[share_ats_code])

                ## data_category not observed at all in web nor mobile -- 0 + 0
                elif data_category not in website_L2_data_dict_fulllogin[app].keys() and data_category not in mobile_L2_data_dict_fulllogin[app].keys():
                    collect_code = '00'
                    str_vals.append(latex_flag[collect_code])
                    collect_ats_code = '00'
                    str_vals.append(latex_flag[collect_ats_code])
                    share_third_code = '00'
                    str_vals.append(latex_flag[share_third_code])
                    share_ats_code = '00'
                    str_vals.append(latex_flag[share_ats_code])
                    

            #### LOGGED OUT DATASET
            if mobile_L2_data_dict_logout[app] != {}: ## if there is mobile data for this app

                ## data category in web but not mobile -- ? + 0
                if data_category in website_L2_data_dict_logout[app].keys() and data_category not in mobile_L2_data_dict_logout[app].keys():
                    logout_collect_code = str(website_L2_data_dict_logout[app][data_category][f"loggedout_collect"]) + '0'
                    str_vals.append(latex_flag[logout_collect_code])

                    loggedout_collect_ats = str(website_L2_data_dict_logout[app][data_category][f"loggedout_collect_ats"])  + '0'
                    str_vals.append(latex_flag[loggedout_collect_ats])

                    loggedout_share_third = str(website_L2_data_dict_logout[app][data_category][f"loggedout_share_third"])  + '0'
                    str_vals.append(latex_flag[loggedout_share_third])

                    loggedout_share_ats = str(website_L2_data_dict_logout[app][data_category][f"loggedout_share_ats"])  + '0'
                    str_vals.append(latex_flag[loggedout_share_ats])
            
                ### data category in web and mobile -- ? + ?
                elif data_category in website_L2_data_dict_logout[app].keys() and data_category in mobile_L2_data_dict_logout[app].keys():
                    logout_collect_code = str(website_L2_data_dict_logout[app][data_category][f"loggedout_collect"]) + str(mobile_L2_data_dict_logout[app][data_category][f"loggedout_collect"])
                    str_vals.append(latex_flag[logout_collect_code])

                    loggedout_collect_ats = str(website_L2_data_dict_logout[app][data_category][f"loggedout_collect_ats"]) + str(mobile_L2_data_dict_logout[app][data_category][f"loggedout_collect_ats"])
                    str_vals.append(latex_flag[loggedout_collect_ats])

                    loggedout_share_third = str(website_L2_data_dict_logout[app][data_category][f"loggedout_share_third"]) + str(mobile_L2_data_dict_logout[app][data_category][f"loggedout_share_third"])
                    str_vals.append(latex_flag[loggedout_share_third])

                    loggedout_share_ats = str(website_L2_data_dict_logout[app][data_category][f"loggedout_share_ats"]) + str(mobile_L2_data_dict_logout[app][data_category][f"loggedout_share_ats"])
                    str_vals.append(latex_flag[loggedout_share_ats])

                ### data category not in web but in mobile -- 0 + ?
                elif data_category in website_L2_data_dict_logout[app].keys() and data_category in mobile_L2_data_dict_logout[app].keys():
                    logout_collect_code = '0' + str(mobile_L2_data_dict_logout[app][data_category][f"loggedout_collect"])
                    str_vals.append(latex_flag[logout_collect_code])

                    loggedout_collect_ats = '0' + str(mobile_L2_data_dict_logout[app][data_category][f"loggedout_collect_ats"])
                    str_vals.append(latex_flag[loggedout_collect_ats])

                    loggedout_share_third = '0' + str(mobile_L2_data_dict_logout[app][data_category][f"loggedout_share_third"])
                    str_vals.append(latex_flag[loggedout_share_third])

                    loggedout_share_ats = '0' + str(mobile_L2_data_dict_logout[app][data_category][f"loggedout_share_ats"])
                    str_vals.append(latex_flag[loggedout_share_ats])
                
                ## not in web nor mobile -- 0 + 0
                elif data_category not in website_L2_data_dict_logout[app].keys():
                    logout_collect_code = '00'
                    str_vals.append(latex_flag[logout_collect_code])
                    
                    loggedout_collect_ats = '00'
                    str_vals.append(latex_flag[loggedout_collect_ats])
                    
                    loggedout_share_third = '00'
                    str_vals.append(latex_flag[loggedout_share_third])
                    
                    loggedout_share_ats = '00'
                    str_vals.append(latex_flag[loggedout_share_ats])
                    
            else: ## there is no mobile data -- ? + 0
                ## ? + 0
                if data_category in website_L2_data_dict_logout[app].keys():
                    logout_collect_code = str(website_L2_data_dict_logout[app][data_category][f"loggedout_collect"]) + '0'
                    str_vals.append(latex_flag[logout_collect_code])

                    loggedout_collect_ats = str(website_L2_data_dict_logout[app][data_category][f"loggedout_collect_ats"]) + '0'
                    str_vals.append(latex_flag[loggedout_collect_ats])

                    loggedout_share_third = str(website_L2_data_dict_logout[app][data_category][f"loggedout_share_third"]) + '0'
                    str_vals.append(latex_flag[loggedout_share_third])

                    loggedout_share_ats = str(website_L2_data_dict_logout[app][data_category][f"loggedout_share_ats"]) + '0'
                    str_vals.append(latex_flag[loggedout_share_ats])
                
                ## 0 + 0
                elif data_category not in website_L2_data_dict_logout[app].keys():
                    logout_collect_code = '00'
                    str_vals.append(latex_flag[logout_collect_code])
                    
                    loggedout_collect_ats = '00'
                    str_vals.append(latex_flag[loggedout_collect_ats])
                    
                    loggedout_share_third = '00'
                    str_vals.append(latex_flag[loggedout_share_third])
                    
                    loggedout_share_ats = '00'
                    str_vals.append(latex_flag[loggedout_share_ats])
            
            if str_vals == [latex_flag["00"]]*16:
                print(f" - {data_category} category not present in {app} data")
            
            else: ## still include the all 0 rows to see what is going on
                row_str = "  &   {category} & {child_collect} & {child_collect_ats} & {child_share_3}  & {child_share_ats}  & {teen_collect} & {teen_collect_ats} & {teen_share_3}  & {teen_share_ats}  & {adult_collect} & {adult_collect_ats}  & {adult_share_3}  &  {adult_share_ats}  & {logged_out_collect} & {logged_out_collect_ats} & {logged_out_share_3} & {logged_out_share_ats} \\".format(
                    category = data_category, 
                    child_collect = "\multicolumn{1}{|c}{" + str_vals[0] + "}",
                    child_collect_ats = str_vals[1],
                    child_share_3 = str_vals[2],
                    child_share_ats = "\multicolumn{1}{c|}{" + str_vals[3] + "}",
                    
                    teen_collect = str_vals[4],
                    teen_collect_ats = str_vals[5],
                    teen_share_3 = str_vals[6],
                    teen_share_ats = "\multicolumn{1}{c|}{" + str_vals[7] + "}",
                    
                    adult_collect = str_vals[8],
                    adult_collect_ats = str_vals[9],
                    adult_share_3 = str_vals[10],
                    adult_share_ats = "\multicolumn{1}{c|}{" + str_vals[11] + "}",

                    logged_out_collect = str_vals[12],
                    logged_out_collect_ats = str_vals[13],
                    logged_out_share_3 = str_vals[14],
                    logged_out_share_ats = str_vals[15]
                )

                if level == '2':
                    if data_category == "Personal Characteristics":
                        per_app_strs += ('\multicolumn{1}{c|}{' + f'{app}' + '}' + row_str + '\\' + '\n')
                    elif data_category == "User Interests and Behaviors":
                        per_app_strs += ('\multicolumn{1}{c|}{}' + row_str + '\\' + '\hline' + '\n\n')
                    else:
                        per_app_strs += ('\multicolumn{1}{c|}{}' + row_str + '\\' + '\n')
                elif level == '3':
                    if data_category == "Account Settings":
                        per_app_strs += ('\multicolumn{1}{c|}{' + f'{app}' + '}' + row_str + '\\' + '\n')
                    elif data_category == "Service Information":
                        per_app_strs += ('\multicolumn{1}{c|}{}' + row_str + '\\' + '\hline' + '\n\n')
                    else:
                        per_app_strs += ('\multicolumn{1}{c|}{}' + row_str + '\\' + '\n')
        per_app_strs += '\n'

    with open(utils.ANALYSIS_OUT_DIR + os.sep + f"web_vs_mobile_latex_data_L{level}_fullloggedin_logout.txt", "w") as f:
        f.write(per_app_strs)

    print(f"[.] Generated {utils.ANALYSIS_OUT_DIR}/web_vs_mobile_latex_data_L{level}_fullloggedin_logout.txt")



def compare_mobile_web(web_login_data, mobile_login_data, web_full_data, mobile_full_data, web_logout_data, mobile_logout_data):
    ## Prepares data and generate files to create latex tables to analyze data flows across
    ## platforms, services, and age/trace groups, as seen in the paper
    
    print("[+] Preparing data flow dataset to generate data flow latex table...")

    web_login_full_list = [web_login_data, web_full_data] 
    web_login_full_data_merged = compare_mobile_web_helper(web_login_full_list, 'website', 'full_and_loggedin')
    web_logout_data_merged = compare_mobile_web_helper(web_logout_data, 'website', 'loggedout')

    mobile_login_full_list = [mobile_login_data, mobile_full_data] 
    mobile_login_full_data_merged = compare_mobile_web_helper(mobile_login_full_list, 'mobile', 'full_and_loggedin')
    mobile_logout_data_merged = compare_mobile_web_helper(mobile_logout_data, 'mobile', 'loggedout')

    l1_filename_web_fl, l2_filename_web_fl, l3_filename_web_fl = helper_create_ontology_lists(web_login_full_data_merged, "website", "full_and_loggedin")
    l1_filename_mob_fl, l2_filename_mob_fl, l3_filename_mob_fl = helper_create_ontology_lists(mobile_login_full_data_merged, "mobile", "full_and_loggedin")

    l1_filename_web_lo, l2_filename_web_lo, l3_filename_web_lo = helper_create_ontology_sets_loggedout(web_logout_data_merged, "website")
    l1_filename_mob_lo, l2_filename_mob_lo, l3_filename_mob_lo = helper_create_ontology_sets_loggedout(mobile_logout_data_merged, "mobile")

    # Using L2 categories, create data flow table latex
    with open(utils.ANALYSIS_OUT_DIR + os.sep + l2_filename_web_fl, "r") as f:
        website_L2_data_dict_fulllogin = json.load(f)
    with open(utils.ANALYSIS_OUT_DIR + os.sep + l2_filename_mob_fl, "r") as f:
        mobile_L2_data_dict_fulllogin = json.load(f)

    with open(utils.ANALYSIS_OUT_DIR + os.sep + l2_filename_web_lo, "r") as f:
        website_L2_data_dict_logout = json.load(f)
    with open(utils.ANALYSIS_OUT_DIR + os.sep + l2_filename_mob_lo, "r") as f:
        mobile_L2_data_dict_logout = json.load(f)

    create_web_mobile_comp_latex_table(website_L2_data_dict_fulllogin, mobile_L2_data_dict_fulllogin, website_L2_data_dict_logout, mobile_L2_data_dict_logout, '2')


