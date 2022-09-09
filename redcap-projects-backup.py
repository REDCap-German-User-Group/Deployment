## create backup of REDCap-Projects via API

REDCAP_API = "https://redcap.medizin.uni-leipzig.de/redcap/api/"

## in BACKUP_DIR, subfolders YEAR/MONTH are created, with backup files
## named YYYY-MM-DD_<REDCAP-PID>.xml.gz
BACKUP_DIR = "/mnt/workgroup/KIK-MF/FDM/REDCap/backup"

## TOKEN_FILE should be a csv file (semicolon-separated) with pid,token
## - may contain additional columns like project title etc
## pid and token column are selected by the column title
TOKEN_FILE = "/mnt/workgroup/KIK-MF/FDM/REDCap/backup/tokens.csv"

## Path to the LOG file produced by this script.
## Based on the content of this log file, the script determines whether
## a project was changed (based on a hash value of the whole exported XML)
## it writes log entries like this:
##  - 2022-09-08T23:42:25.184451 : 312 : KNOWN : 80f261bdee029776a8c6b603ed4e0fb07f1ee496 already saved
##  - 2022-09-08T23:42:28.412167 : 317 : SUCCESS : /mnt/workgroup/KIK-MF/FDM/REDCap/backup/2022/09/2022-09-08_317.xml.gz : 10762 : 2e23df70c2e5352d2f894e272653cc42e1badf98
##  - 2022-09-08T23:30:03.161540 : 13 : ERROR : 500 Server Error: Internal Server Error for url: https://redcap.medizin.uni-leipzig.de/redcap/api/
##  First column is a timestamp, then the PID, a status and additional info - in case of SUCCEDD the file size and hash code
LOG_FILE = "/mnt/workgroup/KIK-MF/FDM/REDCap/backup/log.txt"

import json
import requests
import csv
import gzip
from datetime import datetime
import os
import re
import hashlib

## redcap-server verwendet einrichtungsinternes zerfifikat, dem python nicht vertraut 
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

known_hashes = []

with open(LOG_FILE) as log:
    for line in log:
        candidate = line.strip().split(' : ')[-1]
        if len(candidate) == 40:
            known_hashes.append(candidate)

log = open(LOG_FILE, "a")

with open(TOKEN_FILE, encoding="ISO-8859-1") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=";")
    for row in reader:
        try:
            response = requests.post(REDCAP_API,
                                     data={'token': row['token'].strip(),
                                           'content': 'project_xml',
                                           'format': 'json',
                                           'exportFiles': False,
                                           'exportSurveyFields': True,
                                           'exportDataAccessGroups': False,
                                           'returnFormat': json},
                                     verify=False)
            response.raise_for_status()
            ## we remove the creation date from the xml to make sure that
            ## the hash of the backup is the same if no content is changed
            xml = response.content.decode('utf8')
            xml = re.sub(r'AsOfDateTime="[0-9T:-]+" CreationDateTime="[0-9T:-]+"',
                         r'AsOfDateTime="1970-01-01T00:00:00" CreationDateTime="1970-01-01T00:00:00"',
                         xml)
            xml = re.sub(r'MetaDataVersion( *)OID="([^"]+)\d{4}-\d{2}-\d{2}_(\d+)"',
                         r'MetaDataVersion\1OID="\2"',
                         xml)
            sha = hashlib.sha1()
            sha.update(xml.encode('utf8'))

            hexhash = sha.hexdigest()
    
            today = datetime.today()
            filename = '_'.join([today.strftime("%Y-%m-%d"), row['pid']]) + ".xml.gz"
            path = os.path.join(BACKUP_DIR, today.strftime("%Y"), today.strftime("%m"))
            os.makedirs(path, exist_ok=True)
            if hexhash in known_hashes:
                log.write(f"{datetime.now().isoformat()} : {row['pid']} : KNOWN : {hexhash} already saved\n")
            else:
                with gzip.open(os.path.join(path, filename), "wb", compresslevel=8) as fd:
                    fd.write(xml.encode('utf8'))
                log.write(f"{datetime.now().isoformat()} : {row['pid']} : SUCCESS : {path}/{filename} : {os.path.getsize(os.path.join(path, filename))} : {hexhash}\n")
        except Exception as e:
            log.write(f"{datetime.now().isoformat()} : {row['pid']} : ERROR : {e}\n")
        log.flush()
