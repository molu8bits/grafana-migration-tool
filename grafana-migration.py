#!/usr/bin/python3
# 2019.04.18 molu8bits@gmail.com
# Grafana Migration Tool
# Tool to export dashboards and folder hierarchy from Grafana and import it later keeping hierarchy.

import json
import requests
import time
import os, argparse, json, copy
from os import listdir
from os.path import isfile, join


'''
Script requires following variables to be set in the code:
OUTPUT_FOLDER="export_folder"   #local directory to export and import dashboards and folders

Export requires:
GF_URL_SRC="http://my-grafana.mydomain.com"     # source Grafana URL
GF_KEY_SRC="ABC123"                             # source Grafana API KEY

Import requires:
GF_URL_DST="http://new-grafana.mydomain.com"    # destination Grafana URL
GF_KEY_DST="789XYZ"                             # destination Grafana URL

'''

OUTPUT_FOLDER='exported_dashboards'


# SOURCE GRAFANA DETAILS
GF_URL_SRC="http://old-grafana.mydomain.net"
GF_KEY_SRC = "OLD_GRAFANA_API_KEY"

# DESTINATION GRAFANA DETAILS
GF_URL_DST = "http://new-grafana.mydomain.com"
GF_KEY_DST = "NEW_GRAFANA_API_KEY"

# GRAFANA API ENDPOINTS
GF_DASH="/api/dashboards/db"
GF_SEARCH="/api/search?query=&"
GF_DASH_GET="/api/dashboards/uid/"
GF_FLD="/api/folders"

headers_src = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GF_KEY_SRC}
headers_dst = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GF_KEY_DST}

# SET this value to SURE_STRING = 'Yes I want delete all the dashboards' if you want destroy content of destination Grafana
SURE_STRING = 'No'


argParser = argparse.ArgumentParser()
argParser.add_argument('--export', action='store_true', help='export grafana folders and dashboards into subdirectory "OUTPUT_FOLDER"')
argParser.add_argument('--import_folders', action='store_true', help='import grafana folder structure from "OUTPUT_FOLDER"/grafana-folders.json')
argParser.add_argument('--import_dashboards_from', type=str, help='import all grafana dashboards from specified subfolder inside "OUTSIDE_FOLDER"')
argParser.add_argument('--delete_folders', action='store_true', help='delete all existing folders and dashboards on destination Grafana')
passedArgs = vars(argParser.parse_args())

EXPORT = True if passedArgs['export'] is True else False
IMPORT_FOLDERS = True if passedArgs['import_folders'] is True else False
IMPORT_DASHBOARDS_FROM = passedArgs['import_dashboards_from']
DELETE_FOLDERS = True if passedArgs['delete_folders'] is True else False

# To set null value in JSON
null = None

# Error counter
ERROR_COUNTER = 0

print('*' * 50)
print('--- Environment settings ---')
print('url_src :', GF_URL_SRC + GF_DASH)
#print('headers_src :', headers_src)
print('url_dst :', GF_URL_DST + GF_DASH)
#print('headers_dst :', headers_dst)
print('*' * 50)


def dashboard_export():
    global ERROR_COUNTER
    try:
        r = requests.get(GF_URL_SRC + GF_SEARCH, headers=headers_src)
        rf = requests.get(GF_URL_SRC + GF_FLD, headers=headers_src)
        if rf.status_code != 200 and r.status_code != 200:
            raise Exception(r.status_code, r.text, ' ', rf.status_code, rf.text)
            pass
        dashboard_list_src = r.json()
        folder_list_src = rf.json()
        print('Number of folders :', len(folder_list_src))
        print('Number of dashboards :', len(dashboard_list_src))

        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
        filepath = OUTPUT_FOLDER + '/' + 'grafana-folders.json'
        file_json = open(filepath, "w")
        folder_list_src_export = copy.deepcopy(folder_list_src)
        for each in folder_list_src_export:
            each['id'] = null
        json.dump(folder_list_src_export, file_json, indent=4, sort_keys=False)
        print('*** directories exported :', filepath)

    except Exception as e:
        print('dashboard_exports(): Error found while getting information from source Grafana :', e)
        ERROR_COUNTER += 1
        exit(0)

    dirdict_title = {}
    dirdict_id = {}

    for key in folder_list_src:
        dirdict_title[key['uid']] = key['title'].replace(" ","_").replace("(","_").replace(")","_")
        dirdict_id[key['uid']] = key['id']

    for each in dashboard_list_src:
        if each['type'] in 'dash-db':
            new_title = each['title'].replace("/","_").replace(" ","_").replace(",","_")
            if 'folderUid' in each:
                folder_uid = each['folderUid']
                folder_name = dirdict_title[folder_uid]
                folder_id = dirdict_id[folder_uid]
            else:
                folder_name = 'General'
                folder_id = "0"
                folder_uid = "0"
            try:
                if not os.path.exists(OUTPUT_FOLDER + '/' + folder_name):
                    os.makedirs(OUTPUT_FOLDER + '/' + folder_name)
                filepath = OUTPUT_FOLDER + '/' + folder_name + '/' + new_title + '.json'
                file_json = open(filepath, "w")
                get_url = GF_URL_SRC + GF_DASH_GET + each['uid']
                r = requests.get(get_url, headers=headers_src)
                if r.status_code != 200:
                    print('r.status_code + r.reason :', r.status_code, r.reason)
                dashboard_content = r.json()
                del dashboard_content['meta']
                dashboard_content['dashboard']['id'] = null
                dashboard_content['folderId'] = folder_id
                dashboard_content['folderUid'] = folder_uid
                json.dump(dashboard_content, file_json, indent=4, sort_keys=False)
                print('*** dashboard exported :', filepath)
            except Exception as e:
                ERROR_COUNTER += 1
                print('Error :', e, '. Cannot save file :', filepath)
            #time.sleep(10)   # Delay for 10 sec
        else:
            #print('#' * 5, ' --- NOT DASHBOARD --- ', '#' * 5)
            pass

def dashboard_folder_import():
    global ERROR_COUNTER
    try:
        print('*' * 50)
        print('Importing folder structure to GRAFANA :', GF_URL_DST)
        print('*' * 50)
        with open(OUTPUT_FOLDER + '/' + 'grafana-folders.json', "r") as f:
            folder_list = json.load(f)
            #print(folder_list)
        for each in folder_list:
            print('Importing folder :', each)
            r = requests.post(GF_URL_DST + GF_FLD, data=json.dumps(each), headers=headers_dst)
            if r.status_code != 200:
                print('r.status_cod + r.reason :', r.status_code, r.reason)
                ERROR_COUNTER += 1
    except Exception as e:
        ERROR_COUNTER += 1
        print('dashboard_folder_import() raised the following exception :', e)

def dashboard_folder_cleanup():
    global ERROR_COUNTER
    try:
        print('*' * 50)
        print('Removing all the dashboards from GRAFANA :', GF_URL_DST)
        print('*' * 50)
        if not SURE_STRING in 'Yes I want delete all the dashboards':
            raise Exception('I will not remove all dashboards if you are not sure')
        rd = requests.get(GF_URL_DST + GF_FLD, headers=headers_dst)
        if rd.status_code != 200:
            raise Exception(rd.status_code, rd.text)
        folder_list_dst = rd.json()
        #print('folder_list_dst :', folder_list_dst)
        for each in folder_list_dst:
            print('dashboard_folder_cleanup(): Removing folder :', each['title'])
            rdel = requests.delete(GF_URL_DST + GF_FLD + '/' + each['uid'], headers=headers_dst)
            if rdel.status_code != 200:
                print(rdel.status_code, rdel.text)
                raise Exception(rdel.status_code, rdel.text)

    except Exception as e:
        ERROR_COUNTER += 1
        print('dashboard_folder_cleanup(): error found :', e)

def dashboard_import(grafana_folder):
    global ERROR_COUNTER
    import_folder = os.path.join(OUTPUT_FOLDER, grafana_folder)
    print('*' * 50)
    print('Importing all the dashboard from folder "{0}" into grafana "{1}"'.format(grafana_folder, GF_URL_DST))
    print('*' * 50)
    try:
        rd = requests.get(GF_URL_DST + GF_FLD, headers=headers_dst)
        if rd.status_code != 200:
            raise Exception(rd.status_code, rd.text)
        folder_list_dst = rd.json()
        dirdict_id = {}
        for key in folder_list_dst:
            dirdict_id[key['uid']] = key['id']

    except Exception as e:
        print('dashboard_import() exception: ', e)
        exit(0)

    try:
        grafana_dashboard_files = [dsh_file for dsh_file in listdir(import_folder) if isfile(join(import_folder, dsh_file))]
    except Exception as e:
        ERROR_COUNTER += 1
        print('Error found when listing json files in folder {0}'.format(grafana_folder))
        exit(0)

    for eachfile in grafana_dashboard_files:
        try:
            filename = os.path.join(import_folder, eachfile)
            print('Importing file :', filename)
            with open(filename, "r") as f:
                dashboard_definition = json.load(f)
                folder_uid = dashboard_definition['folderUid']
                if folder_uid in dirdict_id.keys():
                    dashboard_definition['folderId'] = dirdict_id[folder_uid]
                else:
                    dashboard_definition['folderId'] = 0
                    print('Folder uid not found for the dashboard {0}'.format(eachfile))
                del dashboard_definition['folderUid']
                r = requests.post(GF_URL_DST + GF_DASH, data=json.dumps(dashboard_definition), headers=headers_dst)
                if r.status_code != 200:
                    print('r.status_cod + r.reason :', r.status_code, r.reason)
                    ERROR_COUNTER += 1

        except Exception as e:
            ERROR_COUNTER += 1
            print('error :', e)

if __name__ == '__main__':
    print("Grafana migration script is starting ...")
    if EXPORT:
        dashboard_export()
    elif IMPORT_FOLDERS:
        dashboard_folder_import()
    elif IMPORT_DASHBOARDS_FROM:
        dashboard_import(IMPORT_DASHBOARDS_FROM)
    elif DELETE_FOLDERS:
        dashboard_folder_cleanup()
    else:
        print('No parameter found to execute. Run with "-h" for help')
        print('*' * 50)
        print('Export all dashboards and folder as json files: python3 grafana-migration.py --export')
        print('Import folders from folder OUTPUT_FOLDER/grafana-folders.json: python3 grafana-migration.py --import-folders ')
        print('Import all dashboards from OUTPUT_FOLDER/mydirectory/*json: python3 grafana-migration.py --import-dashboards-from mydirectory')
        print('Folders must be imported separately before dashboards to preserve the hierarchy as in the source Grafana')
        print('*' * 50)
        print('Export operation requires values GF_URL_SRC (Grafana URL) and GF_KEY_SRC (Authorization Key) to be set')
        print('Import operations require values GF_URL_DST (Grafana URL) and GF_KEY_DST (Authorization Key) to be set')
        print('Both operation uses OUTPUT_FOLDER variable to save and read JSON files. ')

    if ERROR_COUNTER > 0:
        print('Number of errors found {0}. Please check script log to find details'.format(ERROR_COUNTER))

