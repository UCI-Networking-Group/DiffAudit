#!/usr/bin/python

'''
Script used to extract only the needed information from HAR files and outputs a unified JSON file. 
'''

import json
from urllib.parse import urlparse
import os
import argparse
import uuid
from tqdm import tqdm
import extract_key_val_pairs
from utils import utils

OUTPUTS_DIR_NAME = "outputs"
age_dict = {
	"1": "child (<13)",
	"2": "adult (>=16)",
	"3": "teen (13-15)"
} 

def extract_kv_pairs(payload):        
	json_kvs = tuple()
	ampersand_kvs = tuple()
	semicolon_kvs = tuple()
	# Check if this is JSON or ampersand/semicolon-separated structure
	if payload.startswith('[') or payload.startswith('{'):
		for k, v in extract_key_val_pairs.recursive_find_json_items(payload):
			json_kvs += ((k, v),)
			if isinstance(v, str) and ("&" in v or ";" in v):
				## value may also contain ampersand or semicolon separated structure, so process v as well
				for subk, subv, v_dict in extract_key_val_pairs.process_ampersand_separated_text(v):
					if v_dict == '':
						ampersand_kvs += ((subk, subv),)
					else:
						ampersand_kvs += ((subk, subv),)
						for tup in v_dict:
							ampersand_kvs += ((tup[0], tup[1]), )  #add the kvs from the sub json structure of the amp separated text
				for subk, subv, v_dict in extract_key_val_pairs.process_semicolon_separated_text(v):
					if v_dict == '':
						semicolon_kvs += ((subk, subv),)
					else:
						semicolon_kvs += ((subk, subv),)
						for tup in v_dict:
							semicolon_kvs += ((tup[0], tup[1]), )  #add the kvs from the sub json structure of the amp separated text
	## otherwise, the overall structure is not json, so process ampersand or semicolon strucutre
	else:
		for k, v, v_dict in extract_key_val_pairs.process_ampersand_separated_text(payload):
			if v_dict == '':
				ampersand_kvs += ((k, v),)
			else:
				ampersand_kvs += ((k, v),)
				for tup in v_dict:
					ampersand_kvs += ((tup[0], tup[1]), )  #add the kvs from the sub json structure of the amp separated text
		for k, v, v_dict in extract_key_val_pairs.process_semicolon_separated_text(payload):
			if v_dict == '':
				semicolon_kvs += ((k, v),)
			else:
				semicolon_kvs += ((k, v),)
				for tup in v_dict:
					semicolon_kvs += ((tup[0], tup[1]), )  #add the kvs from the sub json structure of the amp separated text

	# Merge all kv pairs found
	kv_pairs = []
	for t in json_kvs:
		kv_pairs.append((t[0], t[1]))
	for t in ampersand_kvs:
		kv_pairs.append((t[0], t[1]))
	for t in semicolon_kvs:
		kv_pairs.append((t[0], t[1]))
	
	return kv_pairs



def process_packet(entry):

	if entry['request'] == {}:
		return {}, {} #only process outgoing requests

	else: ## Process all outgoing requests
		# Pass a single entry to this function at a time (since extract_from_har will perform this in parallel)
		entry_dict, kv_dict = {}, {}

		# Get url to parse (and uri)
		url_raw = entry.get('request', {}).get('url', '')
		url = urlparse(url_raw, scheme='Unknown', allow_fragments=False)

		# Destination IP and port
		entry_dict[utils.dst_ip] = entry.get('serverIPAddress', '')
		if url.port:
			entry_dict[utils.dst_port] = url.port
		else:
			entry_dict[utils.dst_port] = ""

		entry_dict[utils.tcpstream] = entry.get('connection', '') ##tcp stream number

		# Process headers
		request_headers = entry.get('request', {}).get('headers', [])   
		processed_headers = {}
		for pair in request_headers:
			key = str(pair["name"])
			value = str(pair["value"])
			processed_headers[key] = value
		entry_dict[utils.headers] = processed_headers
		entry_dict[utils.host] = url.hostname   

		all_kvs = []

		# Get http.file_data
		request_postData = entry.get('request', {}).get('postData', {})
		request_postData_text = request_postData.get('text', '')
		if "Content-Type" in entry_dict[utils.headers].keys(): #if this is part of the header
			if ("image" not in entry_dict[utils.headers]["Content-Type"]) and ("video" not in entry_dict[utils.headers]["Content-Type"]):  
				# don't add http file data for images/videos (not useful content)
				if request_postData_text != "": #and if it's not empty, add the http file data content
					entry_dict[utils.http_body] = request_postData_text
					kv_dict[utils.extracted_kvs_payload] = extract_kv_pairs(str(entry_dict[utils.http_body])) # Extract key-values pairs data from payload data
					all_kvs += kv_dict[utils.extracted_kvs_payload]

		# For everything else, (may not have content-type in header) add nonempty http data
		elif request_postData_text != "":
			entry_dict[utils.http_body] = request_postData_text
			kv_dict[utils.extracted_kvs_payload] = extract_kv_pairs(str(entry_dict[utils.http_body])) # Extract key-values pairs data from payload data
			all_kvs += kv_dict[utils.extracted_kvs_payload]

		entry_dict[utils.method] = entry.get('request', {}).get('method', '') 
		entry_dict[utils.protocol] = url.scheme 
		entry_dict[utils.uri] = url.path

		# Extract key-values pairs data from header and url data
		kv_dict[utils.extracted_kvs_header] = extract_kv_pairs(json.dumps(entry_dict[utils.headers]))
		url_to_search = url_raw.replace(url.scheme + '://', "")
		url_to_search = url_to_search.replace(url.netloc, "")
		kv_dict[utils.extracted_kvs_url] = extract_kv_pairs(str(url_to_search)) ## raw string url without domain part
		
		# Merge all three kvs pairs sources together
		all_kvs += kv_dict[utils.extracted_kvs_header]
		all_kvs += kv_dict[utils.extracted_kvs_url]
		kv_dict[utils.all_extracted_kvs] = all_kvs

		return entry_dict, kv_dict


def extract_from_har(har_path, show_progress=False, har_parsed_dict={}, extraced_kvs_parsed_dict={}):
	# Extracts only the needed information from provided HAR file and outputs a JSON dictionary

	# Read and open HAR file
	with open (har_path, 'r', encoding='utf-8-sig') as har_file:
		har_raw = json.load(har_file)

	if 'log' not in har_raw.keys():
		# if no "log" in the har file keys, then it is malformed somehow
		# continue parsing the rest of the files and just skip malformed ones
		print("### ERROR: malformed HAR file. Skipped {har_path}.")
		return har_parsed_dict 

	num_entries = len(har_raw['log']['entries'])		
	with tqdm(total=num_entries, disable=(not show_progress)) as pbar:
		for entry in har_raw['log']['entries']:
			processed_packet, extracted_kvs_dict = process_packet(entry)
			if processed_packet != {}: # don't save the non-post messages (which are returned as empty dictionary from process_packet)
				# Make unique ID for each entry and store in dictionary format
				uid = str(uuid.uuid1())
				har_parsed_dict[uid] = processed_packet
				extraced_kvs_parsed_dict[uid] = extracted_kvs_dict
			pbar.update(1)

	return har_parsed_dict, extraced_kvs_parsed_dict


def write_data(data, file_out, permission):
    # Write the new data
    with open(file_out, permission) as jsonfile:
        jsonfile.seek(0)
        jsonfile.write(json.dumps(data, sort_keys=True, indent=4))
        jsonfile.truncate()


def controller(input_dir, output_file_name, trace_select, show_progress=False):
	# Extracts only the needed information from provided HAR files and outputs one unified JSON file for each website.

	if not os.path.isdir(input_dir):
		print("### ERROR: input directory missing or incorrectly named")
		return False
	
	if trace_select == "logged_in_trace" or trace_select == "full_trace":
		if show_progress: print(f"\nInput Directory: {input_dir}")
		age_category_dirs = [i for i in os.listdir(input_dir) if i != '.DS_Store' and i != 'csv_files' and i != 'outputs']
		for age_category_dir in age_category_dirs:
			har_file_paths = [ (input_dir + os.sep + age_category_dir + os.sep + i) for i in (os.listdir(input_dir + os.sep + age_category_dir)) if i != ".DS_Store" and ".har" in i ]
			# Verify that age profile har files match the enclosing directory
			for path in har_file_paths:
				age_cat = path.split("_")[-3][-1]
				if age_cat != age_category_dir:
					print("### ERROR: har file age category in file name does not match the enclosing directory age category")
					return False

			# Iterate over each HAR file in input directory and convert data to one unified JSON 
			output_dict, extracted_kvs_dict = {}, {}
			for har_path in har_file_paths:
				# Extract from har and update the output_dict for each file in the directory
				age_category = har_path.split("_")[-3][-1]
				if show_progress: print(f"Extracting data from {har_path} (age category {age_category}: {age_dict[age_category]})...")
				output_dict, extracted_kvs_dict = extract_from_har(har_path, show_progress, output_dict, extracted_kvs_dict)

			#  Write dict to output JSON files, and save into the corresponding age category directory
			output_file_split = output_file_name.split("-") 
			output_file_split.insert(1, age_category_dir)
			output_file_join = '-'.join([str(i) for i in output_file_split]) 
			output_file = input_dir + os.sep + age_category_dir + os.sep + output_file_join 
			write_data(output_dict, output_file, 'w')

			if not os.path.exists(input_dir + os.sep + OUTPUTS_DIR_NAME):
				os.makedirs(input_dir + os.sep + OUTPUTS_DIR_NAME)
			output_kvs_file = input_dir + os.sep + OUTPUTS_DIR_NAME + os.sep + (output_file_join.replace('-out-nomoads.json', '-extracted_kv_pairs.json')) # i.e., website/Roblox/outputs/Roblox-1-extracted_kv_pairs.json
			write_data(extracted_kvs_dict, output_kvs_file, 'w')

			if show_progress: print(f"[Info] Length of output dictionary: {len(output_dict)}")
			if show_progress: print(f"[Info] Wrote JSON data to {output_file}")
			if show_progress: print(f"[Info] Wrote extracted key-value pairs data to {output_kvs_file}\n")
	
	elif trace_select == "logged_out_trace":
		if show_progress: print(f"\nInput Directory: {input_dir}")		
		har_file_paths = [ (input_dir + os.sep + i) for i in (os.listdir(input_dir)) if i != ".DS_Store" and ".har" in i ]

		# Iterate over each HAR file in input directory and convert data to one unified JSON
		output_dict, extracted_kvs_dict = {}, {}
		for har_path in har_file_paths:
			# Extract from har and update the output_dict for each file in the directory
			if show_progress: print(f"Extracting data from {har_path}...")
			output_dict, extracted_kvs_dict = extract_from_har(har_path, show_progress, output_dict, extracted_kvs_dict)

		#  Write dict to output JSON files, and save into the corresponding age category directory
		output_file = input_dir + os.sep + output_file_name 
		write_data(output_dict, output_file, 'w')

		if not os.path.exists(input_dir + os.sep + OUTPUTS_DIR_NAME):
			os.makedirs(input_dir + os.sep + OUTPUTS_DIR_NAME)
		output_kvs_file = input_dir + os.sep + OUTPUTS_DIR_NAME + os.sep + (output_file_name.replace('-out-nomoads.json', '-extracted_kv_pairs.json')) # i.e., website/Roblox/outputs/Roblox-extracted_kv_pairs.json
		write_data(extracted_kvs_dict, output_kvs_file, 'w')
		if show_progress: print(f"[Info] Length of output dictionary: {len(output_dict)}")
		if show_progress: print(f"[Info] Wrote JSON data to {output_file}")
		if show_progress: print(f"[Info] Wrote extracted key-value pairs data to {output_kvs_file}\n")

	else:
		print(f"### ERROR: invalid trace select {trace_select}\n")
		return False

	return True

if __name__ == '__main__':
	ap = argparse.ArgumentParser(description="Converts HAR files into JSON")
	ap.add_argument('--har_dir', required=True, help='Directory where the HAR files for one website are located')
	ap.add_argument('--data_out_file_name', required=True, help='Output file name for the resulting JSON file')
	ap.add_argument('--trace_select', required=True, type=str, help="String to select the traces to process, based on the directory name or all of them within a platform")
	ap.add_argument('--show_progress', action="store_true", help='Show progress bars and prints statements')
	args = ap.parse_args()

	controller(args.har_dir, args.data_out_file_name, args.trace_select, show_progress=args.show_progress)
