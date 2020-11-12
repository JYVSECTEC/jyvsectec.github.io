#!/usr/bin/env python3

import glob
import json
import os
import argparse
import sys
import re

META_JSON_NAME = '.meta.json'
MITRE_ATTACK_BY_TID = {}


parser = argparse.ArgumentParser()
parser.add_argument("phr_root")
parser.add_argument('-f', '--fill-html-template')
parser.add_argument('-t', '--html-template-file', default='graph_template.html')
parser.add_argument('-r', '--resolve-mitre-attack-names', action='store_true')
parser.add_argument('-o','--output', type=argparse.FileType('w'), default='-')

def get_meta(folder_path):
    meta_path = os.path.join(folder_path, META_JSON_NAME)
    if os.path.exists(meta_path):
        with open(meta_path) as in_f:
            return json.load(in_f)
    else:
        return {}


def get_name(folder_path, meta=None):
    meta = meta if meta else get_meta(folder_path)
    if 'name' in meta:
        return meta['name']
    else:
        return os.path.basename(folder_path)


def sort_children(children, meta):
    if 'child_order' in meta:
        child_order = meta['child_order']
        
        meta_ordered = [c for c in children if c['folder_name'] in child_order]
        rest = [c for c in children if c['folder_name'] not in child_order]

        ordered_w_meta = sorted(meta_ordered, key=lambda c: child_order.index(c['folder_name']))
        ordered_wo_meta = sorted(rest, key=lambda c: c['name'].lower())

        return ordered_w_meta + ordered_wo_meta
    else:
        return sorted(children, key=lambda c: c['name'].lower())


def import_folder(folder_path, options):
    children = []

    meta = get_meta(folder_path)
    name = get_name(folder_path)
    folder_name = os.path.basename(folder_path)
    if folder_name.startswith('_'):
        return None


    for sub_folder in glob.glob(os.path.join(folder_path, '*')):
        if not os.path.isdir(sub_folder):
            continue

        r = import_folder(sub_folder, options)
        if r:
            children.append(r)
    
    children = sort_children(children, meta)

    folder_type = 'topic'
    if not children:
        folder_type = 'tool'

    attack_object = None
    if options.resolve_mitre_attack_names and re.search('^T\d\d\d\d(.\d+)?$', name):
        attack_object = MITRE_ATTACK_BY_TID.get(name)
        if attack_object:
            name = '%s (%s)' % (attack_object['name'], name)

    return {
        'name': name,
        'folder_name': folder_name,
        'children': children,
        'type': folder_type,
        'url': attack_object['url'] if attack_object else None,
        'description': attack_object['description'] if attack_object else None,
    }

def preload_mitre_attack_enterprise():
    if not os.path.exists('enterprise-attack.json'):
        raise Exception('Download enterprise-attack.json first.')
    with open('enterprise-attack.json') as in_f:
        enterprise_attack = json.load(in_f)
        for obj in enterprise_attack['objects']:
            if not obj['type'] == 'attack-pattern':
                continue

            refs = [r for r in obj['external_references'] if r['source_name'] == 'mitre-attack']
            if not refs:
                continue
            ref = refs[0]
            MITRE_ATTACK_BY_TID[ref['external_id']] = {
                'name': obj.get('name', ''),
                'description': obj.get('description', ''),
                'url': ref.get('url', '')
            }

def run():
    options = parser.parse_args()
    phr_root = options.phr_root

    if options.resolve_mitre_attack_names:
        preload_mitre_attack_enterprise()

    result = import_folder(phr_root, options)

    if options.fill_html_template:
        with open(options.html_template_file) as in_f:
            template = in_f.read()
            template = template.replace('JSON_PLACEHOLDER', json.dumps(result))
            print(template, file=options.output)
    else:
        pass
    print(json.dumps(result, indent=4), file=options.output)



if __name__ == '__main__':
    run()