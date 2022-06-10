#!/usr/bin/python3

# script to gather working directory from torque based off JobId
# must be paired with qcd() bash function located in .bashrc
# becase this is called from a bash script, the first thing printed is what gets sent to 'cd'
# author: D.B. Magers

import subprocess
import xml.etree.ElementTree as ET
import sys
import os

def qstat(path,jobId):
    if os.path.exists(path): return subprocess.getoutput(path+" -f -x "+jobId) 
    else: 
        print("qstat command not found...exiting.")
        sys.exit()

def find_job_data(qstatXml):
    jobDir = qstatXml.find("Job").find('Output_Path').text.split(":")[1]
    jobDir = jobDir[:jobDir.rfind("/")]
    return jobDir

jobId = sys.argv[1]

qstatReturn = qstat(subprocess.getoutput("which qstat"),jobId)
if "Unknown Job Id" in qstatReturn:
    print("Job_no_longer_listed_in_qstat")
    sys.exit()
else:
    qstatXml = ET.fromstring(qstatReturn)

path = find_job_data(qstatXml)

print(path)

