#!/bin/bash

set -e
pip3 install virtualenv

# Create a new virtual environment if it hasn't been created or use the existing one
if [[ ! -d python3_venv ]]; then
	echo ""
	echo "[+] Creating a new python3_venv virtual environment..."
	echo ""
	virtualenv -p python3 python3_venv
	# Alternative command below
	#python3 -m venv python3_venv
	source python3_venv/bin/activate
	pip3 install unicodecsv==0.14.1
	pip3 install tldextract==3.1.2
	pip3 install utils==1.0.1
	pip3 install pandas==1.5.3
	pip3 install pandasql==0.7.3
	pip3 install adblockparser==0.7
	pip3 install urllib3==1.26.7
	pip3 install tqdm==4.62.3
	pip3 install openai
	pip3 install tiktoken
	pip3 install python-whois
else
	echo "[+] Found an existing python3_venv virtual environment... Reusing it!"
	echo "[!] Please remove the existing python3_venv and rerun this script if the existing one is broken!"
	echo ""
	source python3_venv/bin/activate
fi
