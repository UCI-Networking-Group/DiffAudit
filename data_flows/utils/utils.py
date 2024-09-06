#!/usr/bin/python

# This file is a part of DiffAudit <https://athinagroup.eng.uci.edu/projects/childrens-privacy/>.
# Copyright (c) 2024 UCI Networking Group.
#
# This file incorporates content from OVRseen <https://athinagroup.eng.uci.edu/projects/ovrseen/>.
# Copyright (c) 2021 UCI Networking Group.
#
# DiffAudit is dual licensed under the MIT License and the GNU General Public
# License version 3 (GPLv3). This file is covered by the GPLv3. If this file
# get used, GPLv3 applies to all of DiffAudit.
#
# See the LICENSE.md file along with DiffAudit for more details.

import os

# Global variables used by other scripts
GENERAL_FILE_NAME = 'general.json'

# Classification labels
LABEL_POSITIVE = 1
LABEL_NEGATIVE = 0

# JSON keys
json_key_type = "type"
json_key_rule = 'rule'
json_key_tk_flag = 'tk_flag' # whether the packet is ad-related or not
json_key_ad_label = 'ad' # whether the packet is ad-related or not
json_key_ad_pkg = "package_responsible" # which app is responsible for the ad
json_key_package_name = 'package_name' # which app generated the packet
json_key_version = "package_version"
json_key_pii_types = 'pii_types'    # a list
json_key_predicted_types = 'predict_piiTypes'
json_key_domain = 'domain'
json_key_host = 'host'
json_key_uri = 'uri'
json_key_headers = 'headers'
json_key_dst_port = "dst_port"
json_key_dst_ip = 'dst_ip'

# Headers for CSV files
hAdLibs = 'ad_libraries'
hPkgName = 'package'

# when reading in a list of directories, use this delimiter
DIR_DELIMITER = ";;"

package_name = "package_name"
version = "package_version"
type = "type"
ats_pkg = "ats_pkg"
id = "pkt_id"
pii_label = "pii_types"
predicted = "predicted"
list_label = "list_labels"

source = "_source"
layers = "layers"
protocol = "protocol"

dst_ip = "dst_ip"
src_ip = "src_ip"
ip = "ip"
tcp = "tcp"
tcpstream = tcp + ".stream"
tcp_payload = tcp + ".payload"

http = "http"
http2 = "http2"
method = "method"
uri = "uri"
headers = "headers"
referer = "referer"
domain = "domain"
host = "host"
dst_port = "dst_port"

http_req = http + ".request."
http_req_method = http_req + method
http_req_uri = http_req + uri
http_req_line = http_req + "line"
http_body = http + ".file_data"

http2_stream = http2 + ".stream"
http2_req = http2 + ".request."
http2_req_method = http2_req + method
http2_req_uri = http2_req + "full_uri"
http2_req_line = http2_req + "line"
http2_body = http2 + ".file_data"
http2_header_first = http2 + '.header' 
http2_header_num = http2 + ".header_" 
http2_header_count = http2 + ".header.count" 
http2_header_name = http2_header_first + ".name"  
http2_header_value = http2_header_first + ".value"   
http2_auth_host = "authority"

extracted_kvs_payload = "extracted_kvs_payload"
extracted_kvs_header = "extracted_kvs_header"
extracted_kvs_url = "extracted_kvs_url"
all_extracted_kvs = "all_extracted_kvs"

ssl = "tls"

pkt_comment = "pkt_comment"

frame = "frame"
frame_num = frame + ".number"
frame_comment = frame + ".comment"
frame_ts = frame + ".time_epoch"

irc = "irc"
websocket = "websocket"
websocketdata = "data-text-lines"

PCAPDROID_SRC_IP = "10.215.173.1" # https://emanuele-f.github.io/PCAPdroid/faq.html

ESIMATE_FORMAT_STR = "Inputxxxxxxxxx // Categoryxxxxxxxxx // xxx // xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx xxxxxxxxxxxx \n"

MANUAL_ORGS = {
    "stape.io": "Stape Inc.",
    "stape.ai": "Stape Inc.",
    "snplow.net": "Snowplow Analytics, Ltd",
    "duolingo.com": "Duolingo, Inc.",
    "roblox.com": "Roblox Corporation",
    "googleapis.com": "Google LLC",
    "merchant-center-analytics.goog": "Google LLC",
    "youtubekids.com": "Google LLC",
    "quizlet.com": "Quizlet, Inc.",
    "minecraft-services.net": "Microsoft Corporation",
    "minecraftservices.com": "Microsoft Corporation",
    "merchant-center-analytics.goog": "Google LLC",
    "akamaihd.net": "Akamai Technologies, Inc.",
    "buttercms.com": "Tiugo Technologies",
    "akamaized.net": "Akamai Technologies, Inc.",
    "ad-lib.io": "Smartly.io",
    "cloudfront.net": "Amazon Technologies, Inc.",
    "doceree.com": "Doceree Inc",
    "profitwell.com": "ProfitWell",
    "realestate.com.au": "REA Group",
    "eu-1-id5-sync.com": "ID5 Technology Ltd",
    "gammaplatform.com": "Gamma Group",
    "nextmillmedia.com": "Next Millennium Media",
    "amazonaws.com": "Amazon Technologies, Inc.",
    "wunderkind.co": "Wunderkind Corporation",
    "optimix.cn": "Optimix",
    "apptimize.com": "Apptimize, Inc.",
    "appsflyersdk.com": "AppsFlyer Inc.",
    "minecraft.net": "Microsoft Corporation",
    "azureedge.net": "Microsoft Corporation",
    "rbxcdn.com": "Roblox Corporation",
    "rbx.com": "Roblox Corporation",
    "tiktokv.us": "ByteDance Ltd.",
    "tiktokcdn-us.com": "ByteDance Ltd.",
}


def readable_dir(prospective_dir):
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if os.access(prospective_dir, os.R_OK):
        return prospective_dir
    else:
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))


def readable_dirs(prospective_dirs):
    existing_dirs = []
    split_dirs = prospective_dirs.split(DIR_DELIMITER)
    for dir in split_dirs:
        if not os.path.isdir(dir):
            print("WARNING: readable_dirs:{0} is not a valid path".format(dir))
        else:
            existing_dirs.append(dir)

    if len(existing_dirs) == 0:
        raise Exception("No valid directories found in %s", prospective_dirs)

    return existing_dirs
