#!/usr/bin/python

'''
GPT-based labeling pipeline:
- Prepares input data (keys from key-value pairs) for classification with prompt, splits into sublists based on model context
- Post-processes GPT's outputs
- Prepares data type labels to be incorporated into data flows in constrcut_data_flows.py

NOTE: You must enter your API key, and check other constants based on your task. See line 28 and onwards. 
NOTE: GPT sometimes outputs unexpected formatting/results. You should post-process your generated results as needed.
'''

import os
import json
import tiktoken
import argparse
import openai
import time
import numpy as np
import math
from collections import Counter
from utils import utils

GPT_OUTPUTS_DIR = "gpt_outputs" # gpt labeling outputs directory
GPT_PROMPT_FILE = "labeling_utils/gpt_prompt.txt"  # ontology-based prompt
from labeling_utils.ontology_L3_to_L1 import data_type_categories_ontology_direct
GPT_PROMPT_CATEGORIES = list(data_type_categories_ontology_direct.keys())

### NOTE: You need to enter your OpenAI API key here, either directly or passed from a file/env
API_KEY = ""

### NOTE: Enter your desired constants for model selection and string naming if different from the default
### The model_key relates to the model_dict entries in line 44. Enter your model specification there.
model_key = 'gpt4_8K'
model_name = 'gpt-4'
model_name_string = 'gpt_4'

### NOTE: Enter a limit for how many sublists to make so that you do not surpass the context length
### You may need a different limit depending on the size of your input text and chosen model context length
limit = 110 

# Model options and prices are from Fall 2023
model_dict = {
    "gpt3.5_4K": {
        "name": "gpt-3.5-turbo",
        "context": "4K",
        "length": 4096,
        "input_cost": 0.0015,  # per 1K tokens
        "output_cost": 0.002   # per 1K tokens
    },
    "gpt3.5_16K": {
        "name": "gpt-3.5-turbo",
        "context": "16K",
        "length": 16384,
        "input_cost": 0.003,   
        "output_cost": 0.004   
    },
    "gpt4_8K": {
        "name": "gpt-4",
        "context": "8K",
        "length": 8192,
        "input_cost": 0.03,   
        "output_cost": 0.06   
    }
}


def count_tokens_from_str(input_str, model):
    encoding = tiktoken.encoding_for_model(model['name'])
    tokens_count = len(encoding.encode(input_str))
    return tokens_count


def estimate_cost(unique_keys, key, mult_temp_value=1):
    print("\n[+] Estimating cost of using GPT API on input data...")
    print("Number of cleaned keys: " , len(unique_keys))

    num_of_lists = math.ceil(len(unique_keys) / limit)
    print(f'Using default length of sublists model to split input data for prompt limit (can change in gpt_labeling.py): {limit}')
    
    spaced_keys = []
    for i in range(num_of_lists):
        if limit*(i+1) > len(unique_keys):
            sublist = unique_keys[ (limit*i) :]
        else:
            sublist = unique_keys[ (limit*i) : (limit*(i+1))]
        spaced_keys.append(sublist)
    
    len_sublists = 0
    for list in spaced_keys:
        len_sublists += (len(list))
    assert len_sublists == len(unique_keys)

    total_cost = 0
    print(f"Using {model_dict[key]['name']} {model_dict[key]['context']} context.")
    print(f"Using {GPT_PROMPT_FILE}.\n")
    with open(GPT_PROMPT_FILE, "r") as infile:
        prompt = infile.readlines()
    prompt_str = "".join(prompt)
    
    alert = 0 # if any exceed the length limit, flag that
    for key_list in spaced_keys:
        len_keys_list = len(key_list)

        print(f"total input keys: {len_keys_list}")
        full_prompt_tokens = count_tokens_from_str(prompt_str, model_dict[key])
        format_tokens = count_tokens_from_str(utils.ESIMATE_FORMAT_STR, model_dict[key])
        input_keys_tokens = count_tokens_from_str(str(key_list), model_dict[key])

        print(f"total input tokens: {full_prompt_tokens + input_keys_tokens}")
        if (full_prompt_tokens + input_keys_tokens) >= model_dict[key]["length"]:
            print(f"######### WARNING: length of tokens exceeds model's maximum length of {model_dict[key]['length']}")
            alert = 1

        total_input_prompt_tokens = (full_prompt_tokens + input_keys_tokens)/1000
        total_outputs_tokens = (format_tokens * len_keys_list)/1000

        print(f"number of input tokens div 1K ({full_prompt_tokens} prompt tokens + {input_keys_tokens} key tokens / 1K): {total_input_prompt_tokens}")
        print(f"number of output tokens div 1K ({format_tokens} format tokens * {len_keys_list} keys / 1K): {total_outputs_tokens}")

        input_cost_p_token = model_dict[key]['input_cost']
        output_cost_p_token = model_dict[key]['output_cost']
        input_cost = input_cost_p_token * total_input_prompt_tokens
        output_cost = output_cost_p_token * total_outputs_tokens
        
        print(f"total input + estimated output tokens: {(total_outputs_tokens + total_input_prompt_tokens)*1000}")
        if ((total_outputs_tokens + total_input_prompt_tokens)*1000) >= model_dict[key]['length']:
            print(f"######### WARNING: length of input+estimated output tokens exceeds model's maximum length of {model_dict[key]['length']}")
            alert = 1

        print(f"input cost (${input_cost_p_token} per 1K tokens * {total_input_prompt_tokens}K tokens): ${round(input_cost, 3)}")
        print(f"output cost (${output_cost_p_token} per 1K tokens * {total_outputs_tokens}K tokens): ${round(output_cost, 3)}")
        print(f"TOTAL COST: ${round(input_cost + output_cost, 3)}\n")

        spaced_total_cost = input_cost + output_cost
        total_cost += spaced_total_cost

    print(f"Number of iterations required for spaced key classification: {len(spaced_keys)}")
    print(f"Total cost for entire list of keys: ${round(total_cost, 4)}")
    if mult_temp_value > 1:
        print(f"Total cost if run for multiple temperatures: ${round(mult_temp_value * total_cost, 4)}")
    if alert == 1:
        print("ALERT! one of the iterations passed the context length")
    print('')

    return spaced_keys, alert



def classify_sublist(spaced_keys, temp_num, temp_str, model_name, model_key, model_name_string):
    openai.api_key = API_KEY
    
    print(f"Using GPT prompt file: {GPT_PROMPT_FILE}.")
    with open(GPT_PROMPT_FILE, "r") as infile:
        prompt = infile.readlines()
    prompt_str = "".join(prompt)

    filenames = []
    counter = 0
    for unique_keys in spaced_keys:
        start = time.time()
        print(f"\nClassifying set {counter} of spaced keys with temperature {temp_num} ({len(unique_keys)} keys)...")

        full_prompt = prompt_str + str(unique_keys)

        print(f"PROMPT TOKEN LEN: { count_tokens_from_str(full_prompt, model_dict[model_key]) }")
        print(f"PROMPT COST: { (count_tokens_from_str(full_prompt, model_dict[model_key])/1000) * model_dict[model_key]['input_cost'] }")
        format_tokens = count_tokens_from_str(utils.ESIMATE_FORMAT_STR, model_dict[model_key])
        total_outputs_tokens = (format_tokens * len(unique_keys))/1000
        out_cost = total_outputs_tokens * model_dict[model_key]['output_cost']
        in_cost = (count_tokens_from_str(full_prompt, model_dict[model_key])/1000) * model_dict[model_key]['input_cost']
        print(f"ESTIMATED OUTPUT COST: { total_outputs_tokens * model_dict[model_key]['output_cost'] }")
        print(f"ESTIMATED TOTAL COST: {out_cost + in_cost}")

        print(f"Using GPT model {model_name} for classification...\n")
        MODEL = model_name
        
        openai_error = 0
        try:
            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=[
                    {"role": "user", "content": full_prompt}],
                temperature = temp_num
            )
        except openai.error.APIError as e:
            print(f"OpenAI API returned an API Error: {e}")
            openai_error = 1
            return openai_error, e
        except openai.error.APIConnectionError as e:
            print(f"Failed to connect to OpenAI API: {e}")
            openai_error = 1
            return openai_error, e
        except openai.error.RateLimitError as e:
            print(f"OpenAI API request exceeded rate limit: {e}")
            openai_error = 1
            return openai_error, e
        except openai.error.Timeout as e:
            print(f"OpenAI API request timed out: {e}")
            openai_error = 1
            return openai_error, e
        except openai.error.InvalidRequestError as e:
            print(f"Invalid request to OpenAI API: {e}")
            openai_error = 1
            return openai_error, e
        except openai.error.AuthenticationError as e:
            print(f"Authentication error with OpenAI API: {e}")
            openai_error = 1
            return openai_error, e
        except openai.error.ServiceUnavailableError as e:
            print(f"OpenAI API service unavailable: {e}")
            openai_error = 1
            return openai_error, e

        print(f"RESPONSE CONTENT:\n{response['choices'][0]['message']['content']}")

        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename = f'{model_name_string}_classify_results_sublist_{counter}_temp{temp_str}-{timestr}'
        with open(GPT_OUTPUTS_DIR + os.sep + f"{filename}.json", "w") as outfile:
            json.dump(response, outfile, indent=4)
        filenames.append(filename)
        print(f"\nWrote results to {filename}.json.")        
        end = time.time()
        print(f"Time to complete classification for set {counter} = {round(end - start, 3)} sec\n")
        counter += 1
    
    return openai_error, filenames

def process(filename):
    # process the latest gpt results
    with open(GPT_OUTPUTS_DIR + os.sep + filename + '.json', "r") as outfile:
        gpt_response_object = json.load(outfile)

    response = gpt_response_object['choices'][0]['message']['content']

    list_responses = [i for i in response.split('\n') if i != '']
    print(f"len of list repsonses: {len(list_responses)}")

    print(f"Processing file {filename}.json...")

    resp_dict = {}
    for resp_str in list_responses:
        if " // " not in resp_str:
            print(f"#### WARNING: Ignoring \"{resp_str}\" because it is probably another statement, not a result.")
        else:
            values = resp_str.split('//')
            values = [i.strip() for i in values]
            # values[0] - input text
            # values[1] - category
            # values[2] - score
            # values[3] - explanation
            if values[0].startswith("'") and values[0].endswith("'"):
                input_text_temp = values[0].strip("'")
            
            elif values[0].startswith("'") and values[0].endswith("',"):
                input_text_temp = values[0].replace("',", "")
                input_text_temp = input_text_temp.replace("'", "")
            
            elif values[0].startswith("['") and values[0].endswith("',"):
                input_text_temp = values[0].replace("['", "")
                input_text_temp = input_text_temp.replace("',", "")

            elif values[0].startswith("['") and values[0].endswith("']"):
                input_text_temp = values[0].replace("['", "")
                input_text_temp = input_text_temp.replace("']", "")

            elif values[0].startswith('"') and values[0].endswith('"'):
                input_text_temp = values[0].strip('"')

            else:
                input_text_temp = values[0]
            input_text = input_text_temp
            
            category = values[1]
            score = values[2]
            explanation = values[3]

            ## add to response dictionary
            resp_dict[input_text] = {
                "category": category,
                "score": score,
                "explanation": explanation
            }

    with open(GPT_OUTPUTS_DIR + os.sep + f"{filename}_processed.json", "w") as outfile:
        json.dump(resp_dict, outfile, indent=4)

    num_classified = len(resp_dict)

    print(f"Number of data types classified as something: {num_classified} out of {len(list_responses)}")
    if num_classified != len(list_responses):
        print("### ERROR: Missing some inputs keys...\n")
    print('')

    return resp_dict


def check_sublist_completion(filenames_list, unique_keys, original_keys_file):  
    with open(GPT_OUTPUTS_DIR + os.sep + original_keys_file, "r") as infile:
        original_keys = (json.load(infile))['spaced_keys']   

    full_merged_list_from_spaced = []
    for i in original_keys:
        for j in i:
            full_merged_list_from_spaced.append(j)
    assert(set(unique_keys) == set(full_merged_list_from_spaced))

    missing_keys = {}
    flag = 0
    for file in filenames_list:
        with open(GPT_OUTPUTS_DIR + os.sep + file, "r") as infile:
            jsondata = json.load(infile)
        all_keys_list = []
        for sublist, data in jsondata.items():
            sublist_num = int(sublist.split("_")[5])
            temp = (((file.split('-'))[0]).split('_'))[-2] # update if files names change format
            print(f"sublist: {sublist_num}, temp: {temp}")
            labeled_keys = set(data.keys())
            for i in labeled_keys:
                all_keys_list.append(i)
            
            dict_name = f"{temp}_sublist{sublist_num}"
            missing_keys_list = []
            if labeled_keys != set(original_keys[sublist_num]):
                if len(set(original_keys[sublist_num]) - labeled_keys) == 1:                    
                    print(f"\ntemp: {temp}")
                    print(f"sublist num: {sublist_num}")
                    print(f"number of keys missing in labeled data: {len(set(original_keys[sublist_num]) - labeled_keys)}")
                    missing = set(original_keys[sublist_num]) - labeled_keys
                    print(f"keys missing in labeled data: ")
                    
                    for i in missing:
                        print(i)
                        missing_keys_list.append(i)
                        flag = 1
                else:
                    print(f"\ntemp: {temp}")
                    print(f"sublist num: {sublist_num}")
                    print(f"number of keys missing in labeled data: {len(set(original_keys[sublist_num]) - labeled_keys)}")
                    print(f"things new in the labeled keys that shouldn't be there: {labeled_keys - set(original_keys[sublist_num])}")
                    missing = set(original_keys[sublist_num]) - labeled_keys
                    print(f"keys missing in labeled data: ")
                    
                    for i in missing:
                        print(i)
                        missing_keys_list.append(i)
                    flag = 1

            if len(missing_keys_list) > 0:
                missing_keys[dict_name] = missing_keys_list
                flag = 1
        if(set(all_keys_list) != set(full_merged_list_from_spaced)):
            print("ERROR: mismatch in keys labeled and input")
            flag = 1
     
    if flag == 1:
        print("\n#### RESULT: There are mismatches between the original inputs and the labeled keys. Check missing keys file generated.\n")
        timestr = time.strftime("%Y%m%d-%H%M%S")
        with open(GPT_OUTPUTS_DIR + os.sep + f"missing_keys-{timestr}.json", "w") as outfile:
            json.dump(missing_keys, outfile, indent=4)
    else:
        print("\n#### RESULT: Original inputs and labeled keys match.\n")

    return flag


def merge_sublists_into_json(filenames_list):
    data_dict = {
            "temp0": {},
            "temp025": {},
            "temp05": {}, 
            "temp075": {}, 
            "temp1": {}
        }
    
    # merge the results into single jsons, not separated by sublists
    merged_filenames = []
    for file in filenames_list:
        print(file)
        temp = (file.split('-')[0]).split('_')[-2]
        print(f"counting data types categorized using {temp}...")
        with open(GPT_OUTPUTS_DIR + os.sep + file, "r") as fp:
            data = json.load(fp)
        for k, v in data.items():
            print(k)
            print(len(v))
            print('')
            for i, j in v.items():
                data_dict[temp][i] = j
        print(len(data_dict[temp]))
        print('\n')

        merged_filenames.append(file.strip('.json') + "_merged.json")
        with open(GPT_OUTPUTS_DIR + os.sep + file.strip('.json') + "_merged.json", "w") as outfile:
            json.dump(data_dict[temp], outfile, indent=4)

    set0 = set(list(data_dict["temp0"].keys()))
    set25 = set(list(data_dict["temp025"].keys()))
    set5 = set(list(data_dict["temp05"].keys()))
    set75 = set(list(data_dict["temp075"].keys()))
    set1 = set(list(data_dict["temp1"].keys()))

    assert(set0 == set25 == set5 == set75 == set1)
    print(len(set0))
    return merged_filenames



def clean_up_categories(filenames_list):
    data_dict = {
            "temp0": {},
            "temp025": {},
            "temp05": {}, 
            "temp075": {}, 
            "temp1": {}
        }

    lower_cats = [i.lower() for i in GPT_PROMPT_CATEGORIES]
    cats_translator_dict = {}
    for i in GPT_PROMPT_CATEGORIES:
        cats_translator_dict[i.lower()] = i
    cats = set(lower_cats)
    
    outfiles = []
    for file in filenames_list:
        print(file)
        temp = (file.split('-')[0]).split('_')[-2] # update depending on file naming format
        print(f"counting data types categorized using {temp}...")
        with open(GPT_OUTPUTS_DIR + os.sep + file, "r") as fp:
            data = json.load(fp)
        
        # clean up category names from gpt
        translate = {
            "Unclear": ['uncategorizable', 'unclear', 'unclassified', 'miscellaneous', 'not applicable', 'n/a', 'not enough information to categorize', 
                        'unreadable/unknown', 'unclassifiable', 'unknown',  'unrecognized', 'custom numbers', "unidentified", 'unidentifiable', 
                        "uncertain", "not assigned", "not enough information", "online information", "app or service usage or products and advertising", 
                        "coarse geolocation or precise geolocation", "not able to classify",
                        "financial information",
                        "website information, app or service usage",
                        "inference about users, app or service usage",
                        "aliases, reasonably linked personal identifiers",
                        "login information, app or service usage",
                        "linked personal identifiers, aliases",
                        "name, linked personal identifiers",
                        "aliases, reasonably linked personal identifiers",
                        "user, language",
                        "network connection information, website information",
                        "user, linked personal identifiers"
            ],
            "Name": ["user, name", "user", "user, name, first name, last name, username"],
            "Products and Advertising": ['advertising or products',  'product and advertising'],
            "Location Time": ['time'],
            "Aliases": ["alias"],
            "Device Information": ["device performance", "devices information"],
            "App or Service Usage": ["user interactions"],
            "Device Hardware Identifiers": ["devices hardware identifiers"],
        }

        clean_data = {}
        for k, v in data.items():
            ## if not in existing category, check if it is in our known list of new categories and translate to known category
            cat_to_check = (v["category"].lower()).strip()
            if cat_to_check not in cats:
                flag = 0
                for correct_label, ex_labels in translate.items():
                    if cat_to_check in ex_labels:
                        # update to correct label
                        clean_data[k] = {
                            "category": correct_label,
                            "score": v["score"],
                            "explanation": v["explanation"]
                        }
                        flag = 1
                if flag == 0:
                    print(f"### {k}")
                    print(f"#### error: new category not accounted for - {v['category']}")
            elif v["category"] not in GPT_PROMPT_CATEGORIES:
                if v["category"].lower() in cats_translator_dict.keys():
                    correct_label = cats_translator_dict[v["category"].lower()]
                    clean_data[k] = {
                        "category": correct_label,
                        "score": v["score"],
                        "explanation": v["explanation"]
                    }
                else:
                    print(v["category"]) 
            else:
                clean_data[k] = {
                    "category": v["category"].strip(),
                    "score": v["score"],
                    "explanation": v["explanation"]
                }

        data_dict[temp] = clean_data

        outfiles.append(file.strip('.json') + "_cleaned_categories.json")
        with open(GPT_OUTPUTS_DIR + os.sep + file.strip('.json') + "_cleaned_categories.json", "w") as outfile:
            json.dump(clean_data, outfile, indent=4)
        
        print(len(data_dict[temp]))
        print('\n')

    set0 = set(list(data_dict["temp0"].keys()))
    set25 = set(list(data_dict["temp025"].keys()))
    set5 = set(list(data_dict["temp05"].keys()))
    set75 = set(list(data_dict["temp075"].keys()))
    set1 = set(list(data_dict["temp1"].keys()))
    assert(set0 == set25 == set5 == set75 == set1)

    return data_dict, outfiles


def merge_labels(main_trace_list, platform, second_trace_list_to_merge=[], merge_traces=False):
    ## read and open json files to get all labels per temperature
    data_per_temp = {
        "temp0": {},
        "temp025": {},
        "temp05": {},
        "temp075": {},
        "temp1": {}
    }
    ## merge the full trace and loggedin/out traces in the same dictionary if merge_traces is passed True
    for file in main_trace_list:
        temp = (file.split('_'))[9] ## change if file naming format changes
        with open(GPT_OUTPUTS_DIR + os.sep + file, "r") as infile:
            data = json.load(infile)
            print(len(data.keys()))
            for k, v in data.items():
                data_per_temp[temp][k] = v
    if merge_traces:
        for file in second_trace_list_to_merge:
            temp = (file.split('_'))[9] ## change if file naming format changes
            with open(GPT_OUTPUTS_DIR + os.sep + file, "r") as infile:
                data = json.load(infile)
                print(len(data.keys()))
                for k, v in data.items():
                    data_per_temp[temp][k] = v

    set0 = sorted(list(data_per_temp["temp0"].keys()))
    set25 = sorted(list(data_per_temp["temp025"].keys()))
    set5 = sorted(list(data_per_temp["temp05"].keys()))
    set75 = sorted(list(data_per_temp["temp075"].keys()))
    set1 = sorted(list(data_per_temp["temp1"].keys()))
    assert(set0 == set25 == set5 == set75 == set1)
    
    ## get most agreed upon label across temperatures for final labels
    all_keys = list(data_per_temp["temp0"].keys())
    labels_scores_per_key = {}

    for key in all_keys:
        # gather all categories
        all_labels = [data_per_temp["temp0"][key]["category"], 
                        data_per_temp["temp025"][key]["category"], 
                        data_per_temp["temp05"][key]["category"], 
                        data_per_temp["temp075"][key]["category"], 
                        data_per_temp["temp1"][key]["category"]]
        
        all_explanations = [data_per_temp["temp0"][key]["explanation"], 
                        data_per_temp["temp025"][key]["explanation"], 
                        data_per_temp["temp05"][key]["explanation"], 
                        data_per_temp["temp075"][key]["explanation"], 
                        data_per_temp["temp1"][key]["explanation"]]

        ## check if the labels are actually our categories for sanity check
        categories_list = GPT_PROMPT_CATEGORIES
        for i in all_labels:
            if i != "Unclear" and i not in categories_list:
                print(f"'{i}'")
                assert(i in categories_list)

        ## get winner label
        counter_labels = Counter(all_labels)
        winner_label = counter_labels.most_common(1)[0][0]

        ## gather all scores
        all_scores = [float(data_per_temp["temp0"][key]["score"]), 
                        float(data_per_temp["temp025"][key]["score"]), 
                        float(data_per_temp["temp05"][key]["score"]), 
                        float(data_per_temp["temp075"][key]["score"]), 
                        float(data_per_temp["temp1"][key]["score"])]
        
        ## get winner scores - first get all scores based on the indices of the winning label
        indices = np.where(np.array(all_labels) == winner_label)[0]
        winner_scores = []
        for i in indices:
            winner_scores.append(all_scores[i])
        
        ## calculate max and average of the corresponding label scores
        max_score = np.max(winner_scores)
        avg_score = np.mean(winner_scores)
        
        ## get an explanation corresponding with the winning label
        winner_explanation = all_explanations[indices[0]]

        labels_scores_per_key[key] = {
            "all_labels": all_labels,
            "all_scores": all_scores,
            "all_explanations": all_explanations,
            "winner_label": winner_label,
            "winner_explanation": winner_explanation,
            "max_score": max_score,
            "avg_score": avg_score
        }

    assert(len(labels_scores_per_key.keys()) == len(all_keys))

    ## save labels based on score 
    max_scores_dict = {}
    avg_scores_dict = {}
    max_count, avg_count = 0, 0
    conf = 0.8
    for key, data in labels_scores_per_key.items():
        if data["max_score"] >= conf:
            max_scores_dict[key] = data["winner_label"]
            max_count += 1
        if data["avg_score"] >= conf:
            avg_scores_dict[key] = data["winner_label"]
            avg_count += 1

    assert(len(max_scores_dict.keys()) == max_count)
    assert(len(avg_scores_dict.keys()) == avg_count)

    print(f"\nCount of labeled data based on MAX score >= {conf} = {max_count}")
    print(f"Count of labeled data based on AVG score >= {conf} = {avg_count}")
    print(f"Total number of input data keys = {len(all_keys)}")
    print(f"Proportion covered by MAX schema = {round(max_count / len(all_keys), 3)}")
    print(f"Proportion covered by AVG schema = {round(avg_count / len(all_keys), 3)}\n")

    timestr = time.strftime("%Y%m%d-%H%M%S")
    final_labels_per_key_filename = f"{platform}_final_labels_per_key-{timestr}.json"
    with open(GPT_OUTPUTS_DIR + os.sep + final_labels_per_key_filename, "w") as outfile:
        json.dump(labels_scores_per_key, outfile, indent=4)
    print(f"Saved final merged label results to {final_labels_per_key_filename}")

    ## max
    max_score_labeled_keys_filename = f"{platform}_labeled_json_keys_merged_max_score_08-{timestr}.json"
    with open(GPT_OUTPUTS_DIR + os.sep + max_score_labeled_keys_filename, "w") as outfile:
        json.dump(max_scores_dict, outfile, indent=4)
    print(f"Saved final label results using max score >= {conf} to {max_score_labeled_keys_filename}")
    
    ## avg
    avg_score_labeled_keys_filename = f"{platform}_labeled_json_keys_merged_avg_score_08-{timestr}.json"
    with open(GPT_OUTPUTS_DIR + os.sep + avg_score_labeled_keys_filename, "w") as outfile:
        json.dump(avg_scores_dict, outfile, indent=4)
    print(f"Saved final label results using avg score >= {conf} to {avg_score_labeled_keys_filename}\n")

    return [timestr, final_labels_per_key_filename, max_score_labeled_keys_filename, avg_score_labeled_keys_filename]


def main():
    ap = argparse.ArgumentParser(description='label keys with gpt classification')
    ap.add_argument('--platform', required=True, type=str, help='select platform (mobile, website, or bothplatforms)')
    ap.add_argument('--unique_keys_file', required=True, type=str,  help='json file with unique keys from traffic to classify')
    ap.add_argument('--estimate', required=False, action="store_true", help='to estimate the cost of using chatgpt to classify keys')
    ap.add_argument('--classify', required=False, action="store_true", help='classify sublists with temperatures ranging from 0-1 for validation purposes')
    args = ap.parse_args()

    platform = args.platform
    unique_keys_file_path = args.unique_keys_file

    ### Check if API_KEY has been set
    if API_KEY == "":
        print("ERROR: API_KEY not set. Please enter your API key in gpt_labeling.py file for OpenAI for GPT classification.")
        return 0

    print(f'Using the following model for GPT classification: {model_key}')

    ### Read in unique keys file
    with open(unique_keys_file_path, "r") as infile:
        unique_keys = json.load(infile)["keys"]
    print(f"Number of keys to classify from f{unique_keys_file_path}: {len(unique_keys)}")

    ### Estimate how much it will cost to classify these input keys in unique_keys with multiple temperatures (before conducting classification)
    if args.estimate:
        print(f"\n[+] Estimating cost to classify input keys...")
        mult_temp_value = 5 # how many sets of parameters (i.e., temperature) you will experiment with
        alert = estimate_cost(unique_keys, key=model_key, mult_temp_value=mult_temp_value)

    ### GPT classification and post-processing pipeline
    elif args.classify: 
        print(f"\n[+] Classifying input keys...")
        ### Step 1: Classify the input unique_keys with multiple temps ranging from 0-1 in 0.25 increments
        mult_temp_value = 5
        spaced_keys, alert = estimate_cost(unique_keys, key=model_key, mult_temp_value=mult_temp_value)
        spaced_keys_dict = {
            "spaced_keys": spaced_keys
        }
        timestr = time.strftime("%Y%m%d-%H%M%S")
        spaced_keys_filename = f"{model_name_string}_spaced_keys-{timestr}.json"
        with open(GPT_OUTPUTS_DIR + os.sep + spaced_keys_filename, "w") as outfile:
            json.dump(spaced_keys_dict, outfile, indent=4)
        
        if alert == 1:
            print("Input exceeds model input length. Abort.")
            return
        
        temp_dict = {
            "0": 0.0,  
            "025": 0.25,
            "05": 0.5,  
            "075": 0.75,
            "1": 1.0  
        }
        step1_output_filenames = []
        for temp_str, temp_num in temp_dict.items():
            print(f"\n[+] Running classification loop with temperature {temp_num}...")
            openai_error, filenames = classify_sublist(spaced_keys, temp_num, temp_str, model_name, model_key, model_name_string)
            if openai_error == 1:
                print(f"Encountered open ai error: {filenames}")
            else:
                print(f"\n[+] Saving classification results with temperature {temp_num} to json file...")
                f_dict = {temp_str: filenames}
                timestr = time.strftime("%Y%m%d-%H%M%S")
                outfilename = f'{model_name_string}_classify_sublist_results_temp{temp_str}_filenames_list-{timestr}.json'
                with open(GPT_OUTPUTS_DIR + os.sep + outfilename, "w") as fp:
                    json.dump(f_dict, fp, indent=4)
                step1_output_filenames.append(outfilename)


        ### Step 2: Clean up the classification results from step 1 (i.e., GPT responses) and organize into single files
        print(f"\n[+] Post-processing classification results...")
        overall_files_dict = {}
        step2_output_filenames = []
        for list_file in step1_output_filenames:
            print(f"\nProcessing {list_file}...")
            with open(GPT_OUTPUTS_DIR + os.sep + list_file, "r") as fp:
                data = json.load(fp)
            for temp, files in data.items():
                overall_files_dict[temp] = files
                results = {}
                for file in files:
                    print(f"Processing {file}...")
                    results[file] = process(file)  
                timestr = time.strftime("%Y%m%d-%H%M%S")
                output_filename = f"{model_name_string}_classify_overall_results_from_sublists_temp{temp}-{timestr}.json"
                with open(GPT_OUTPUTS_DIR + os.sep + output_filename, "w") as fp:
                    json.dump(results, fp, indent=4)
                step2_output_filenames.append(output_filename)
        print(step2_output_filenames)


        ### Step 3: Check if there are any missing input labels in the labeled data. If none are missing, 
        # check and clean up the category names and merge the sublists within the json files.
        # check if the sublists contain all the original input labels
        print(f"\n[+] Checking whether all input keys were labeled and merging sublists...")
        flag = check_sublist_completion(step2_output_filenames, unique_keys, spaced_keys_filename)
        if flag == 0:
            # no mismatches, merge processed sublists files into a single json 
            merged_filenames = merge_sublists_into_json(step2_output_filenames, model_name_string) ## creates _merged files
            print("\nNo mismatches, and completed merge of sublists for each temperature round.\n")

            print("Checking categories now...")
            data_dict, step3_output_filenames = clean_up_categories(merged_filenames)  ## creates _merged_cleaned_categories files
            timestr = time.strftime("%Y%m%d-%H%M%S")
            with open(GPT_OUTPUTS_DIR + os.sep + f"{model_name_string}_merged_data_dict-{timestr}.json", "w") as outfile:
                json.dump(data_dict, outfile, indent=4)
            print(f"Wrote cleaned category data to:\n{step3_output_filenames}\n")


        ### Step 4: Get the majority vote labels across gpt temperatures to get the final labels and separate based on confidence score (max and avg methods)
        print(f"\n[+] Generating final labeled keys files with majority vote and confidence score threshold...")
        final_filenames = merge_labels(step3_output_filenames, platform)
        return final_filenames


    else:
        print("ERROR: incorrect/missing arguments.")
        return 0

        
    
if __name__ == "__main__":
    main()