#!/usr/bin/env python3

'''
Helper functions to extract key value pairs from network traffic packets.
'''

from copy import deepcopy
import json
import re

CSV_FIELD_KEY = 'keys'
CSV_FIELD_PAYLOAD = 'http.file_data'
CSV_FIELD_VALUE = 'values'
CSV_FIELD_SRC = 'source'
CSV_FIELD_DEST = 'dest'
CSV_FIELD_KEY_STR = "key_strings"

def check_all_kv_pairs(root_obj, init_level=()):
    def handle_namespace(d):
        if isinstance(d.get("header"), dict):
            d = d["header"]

        if "namespace" in d:
            return f"<{d.pop('namespace')}>"
        else:
            return None

    def go(obj, level):
        if isinstance(obj, list):
            for item in obj:
                yield from go(item, level + ("[]",))
        elif isinstance(obj, dict):
            if (addtional_label := handle_namespace(obj)) is not None:
                level = (addtional_label,)  # restart path from the namespace

            for k, v in obj.items():
                yield from go(v, level + (k,))
        else:
            yield level, obj

    yield from go(deepcopy(root_obj), init_level)


def find_json(text):
    """
    Find JSON-like structures in the text
    Two patterns: 1) {...} or [...]; 2) "...": ...
    """
    json_decoder = json.JSONDecoder()
    last_ending = 0

    for m in re.finditer(r'(?:"[^"]+":|[{\[])', text):
        if m.start() < last_ending:
            continue

        if m[0] in '{[':
            key = None
            startpos = m.start()
        else:
            key = m[0][1:-2]
            startpos = m.end()

        part = text[startpos:]

        try:
            obj, endoffset = json_decoder.raw_decode(part)
        except json.decoder.JSONDecodeError:
            continue

        yield {key: obj} if key is not None else obj
        last_ending = startpos + endoffset


def process_ampersand_separated_text(payload):
    """
    Search for ampersand-separated strings in the payload. Yield key-value pairs.
    """
    split_text = payload.split("&")
    json_kvs = tuple()
    # We don't care about overwriting the value as long as we obtain the key.
    for subtext in split_text:
        # Usually it comes in the form of <key>=<value>.
        kv_pair = subtext.split("=")
        if len(kv_pair) > 1:
            # Key and value.
            if kv_pair[1].startswith('[') or kv_pair[1].startswith('{'):
                # value mught be a json structure as well
                for k, v in recursive_find_json_items(kv_pair[1]):
                    json_kvs += ((k, v),)
                yield kv_pair[0], kv_pair[1], json_kvs
            else:    
                yield kv_pair[0], kv_pair[1], '' # check if kv_pair[1] is a json structure
        elif len(kv_pair) == 1:
            # Only key but no value.
            yield kv_pair[0], '', ''


def process_semicolon_separated_text(payload):
    """
    Search for semicolon-separated strings in the payload. Yield key-value pairs.
    """
    split_text = payload.split(";")
    json_kvs = tuple()
    # We don't care about overwriting the value as long as we obtain the key.
    for subtext in split_text:
        # Usually it comes in the form of <key>=<value>.
        kv_pair = subtext.split("=")
        if len(kv_pair) > 1:
            # Key and value.
            if kv_pair[1].startswith('[') or kv_pair[1].startswith('{'):
                # value mught be a json structure as well
                for k, v in recursive_find_json_items(kv_pair[1]):
                    json_kvs += ((k, v),)
                yield kv_pair[0], kv_pair[1], json_kvs
            else:    
                yield kv_pair[0], kv_pair[1], '' ## check if kv_pair[1] is a json structure
        elif len(kv_pair) == 1:
            # Only key but no value.
            yield kv_pair[0], '', ''


def recursive_find_json_items(payload, init_level=()):
    """
    Search for JSON strings in the payload. Yield key-value pairs.
    """
    for item in find_json(payload):
        for k, v in check_all_kv_pairs(item, init_level):
            yield k, v

            # Recursively search for JSON strings in all nest string values.
            if isinstance(v, str):
                yield from recursive_find_json_items(v, init_level + k + ("~",))

