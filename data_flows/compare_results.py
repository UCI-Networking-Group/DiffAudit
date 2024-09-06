#!/usr/bin/python

'''
Consolidates block decisions for packets in multiple JSON files in a single csv file.
'''

import argparse
import sys
import os
import json
import unicodedata
import unicodecsv as csv
import glob
from utils import utils

json_key_protocol = "protocol"
json_key_src_ip = "src_ip"   #not in har
json_key_dst_ip = "dst_ip"
json_key_dst_port = "dst_port"
json_key_tcp_stream = "tcp.stream" 
json_key_pii_found = "pii_types"
json_key_package_name = "package_name"   #not in har
json_key_http_body = "http.file_data"
overall_block_decision = "overall_block_decision" # 1 if at least one block decision is 1


DIFFAUDIT = "diffaudit"
ACCEPTED_FILE_NAMING_FORMATS = [DIFFAUDIT]


def write_block_decisions_to_csv(app_id, filter_list_names, full_path, csv_writer, include_http_body=False, website=False):
    with open(full_path, "r") as jf:
        data = json.load(jf)
        for key, value in data.items():
            if website:
                pkt = value
                protocol = pkt.get(json_key_protocol, "")
                dst_ip = pkt[json_key_dst_ip]
                dst_port = pkt[json_key_dst_port]
                host = pkt.get(utils.json_key_host, "")
                path = pkt.get(utils.json_key_uri, "")
                piis_found = pkt.get(json_key_pii_found, "[]")
                package_name = pkt.get(json_key_package_name, "")
                headers = json.dumps(pkt[utils.json_key_headers]) if utils.json_key_headers in pkt else ""
                src_ip = ""
                tcp_stream = pkt[json_key_tcp_stream]

            else:
                pkt = value
                protocol = pkt.get(json_key_protocol, "")
                src_ip = pkt[json_key_src_ip]
                dst_ip = pkt[json_key_dst_ip]
                dst_port = pkt[json_key_dst_port]
                tcp_stream = pkt[json_key_tcp_stream]
                host = pkt.get(utils.json_key_host, "")
                path = pkt.get(utils.json_key_uri, "")
                piis_found = pkt.get(json_key_pii_found, "[]")
                package_name = pkt.get(json_key_package_name, "")
                headers = json.dumps(pkt[utils.json_key_headers]) if utils.json_key_headers in pkt else ""

            row = [app_id,
                key,
                protocol,
                src_ip,
                dst_ip,
                dst_port,
                tcp_stream,
                host,
                path,
                headers,
                piis_found,
                package_name]

            if include_http_body:
                data = pkt.get(json_key_http_body, "").split()
                temp = [i.replace('\x00','') for i in data]
                data = "".join(temp)
                cleaned_data = unicodedata.normalize('NFKD', data).encode('ascii', 'ignore').decode('ascii')
                row.append(cleaned_data)

            overall_block_flag = 0
            for fl in filter_list_names:
                row.append(pkt[fl])
                if pkt[fl] == 1:
                    overall_block_flag = 1
            # add overall block decision based on all the block lists (if any are 1, ats block)
            row.append(overall_block_flag)  # 0 if all the block lists gave 0, otherwise 1

            csv_writer.writerow(row)


def file_naming_format(format):
    if format not in ACCEPTED_FILE_NAMING_FORMATS:
        raise argparse.ArgumentTypeError('Please pick a value from: ' +
                                         ACCEPTED_FILE_NAMING_FORMATS)
    return format


if __name__ == '__main__':
    default_file_naming_format = DIFFAUDIT
    ap = argparse.ArgumentParser(
        description="Consolidates block decisions for packets in multiple NoMoAds json files in a single csv file.")
    ap.add_argument('dir', 
                    type=utils.readable_dir, 
                    help='Directory containing JSON files in NoMoAds format, annotated with block decisions.')
    ap.add_argument('filter_list_dir', 
                    type=utils.readable_dir, 
                    help='''Directory with the filter lists present in the annotated NoMoAds JSON. 
                    This directory is traversed to determine the JSON keys used for the filter lists 
                    in the NoMoAds JSON (file extensions are not part of the JSON key).''')
    ap.add_argument('csv_file', 
                    help='CSV file where the consolidated results are to be written.')
    ap.add_argument('--format', 
                    type=file_naming_format, 
                    default=default_file_naming_format, 
                    help=f'File naming format, from the following list: {str(ACCEPTED_FILE_NAMING_FORMATS)}. Default is {default_file_naming_format}.')
    ap.add_argument('--include_http_body', 
                    action="store_true",
                    help='Whether to include http body')
    ap.add_argument('--website', 
                    action="store_true", 
                    help="Whether you are passing in data collected from the website platform")
    args = ap.parse_args()

    # Determine the json keys used for each filter list.
    fl_names = []
    for fl_file in os.listdir(args.filter_list_dir):
        if "DS_Store" in fl_file:
            continue
        ext_start = fl_file.rfind(".")
        if ext_start < 0:
            print("WARNING: skipping filter list file '" + fl_file +
                  "' as the filename does not contain a file extension.")
            continue
        # Name of filter list becomes filename minus file extension
        fl_name = fl_file[0:ext_start]
        if len(fl_file) > 0 and len(fl_name) > 0:
            fl_names.append(fl_name)
        else:
            print("WARNING: skipping filter list file '" + fl_file +
                  "' as the filename is empty before the file extension")

    with open(args.csv_file, "wb") as f:
        blk = "_block_decision"
        header_row = ["app_id",
                    "pkt_id",
                    json_key_protocol,
                    json_key_src_ip,
                    json_key_dst_ip,
                    json_key_dst_port,
                    "tcp_stream",
                    "hostname",
                    "path",
                    "headers",
                    json_key_pii_found,
                    json_key_package_name]
        if args.include_http_body:
            header_row.append(json_key_http_body)

        for fln in fl_names:
            header_row.append(fln + blk)
        header_row.append(overall_block_decision)

        csv_writer = csv.writer(f)
        csv_writer.writerow(header_row)

        FILE_SUFFIX = "-out-nomoads.json"

        for fn in glob.iglob(args.dir + os.sep + "*" + FILE_SUFFIX):
            if fn == ".DS_Store":
                continue
            if args.format == DIFFAUDIT:
                # Assume filename format like "app.json"
                app_id = os.path.basename(fn)
                app_id = app_id.replace(FILE_SUFFIX,"").replace("_", ".")
            else:
                # This shouldn't happen
                print("Error: format does not match")
                sys.exit(-1)
            full_path = fn
            write_block_decisions_to_csv(app_id, fl_names, full_path, csv_writer,include_http_body=args.include_http_body, website=args.website)
