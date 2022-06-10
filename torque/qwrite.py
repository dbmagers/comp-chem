#!/usr/bin/python3

# write completed job info to ~/.queue_complete
# to be run by .sh torque submit script at end of job
# author: D.B. Magers

import yaml
import os
import subprocess
import time
import xml.etree.ElementTree as ET
import sys

def qstat(path,jobid):
   if os.path.exists(path): return subprocess.getoutput(path+" -f -x "+jobid) 
   else: 
      print("qstat command not found...exiting.")
      sys.exit()

def check_up_state(state):
   downState = ["au", "adu", "d", "E", "auE"]
   if state is not None:
      if state.text in downState: return False
   return True

def find_job_data(job):
#   jobUser = job.find('Job_Owner').text.split("@")[0]
#   jobID = job.find('Job_Id').text.split(".")[0]
   jobVariableList = job.find('Variable_List').text
   jobVariableDict = dict(item.split("=",1) for item in jobVariableList.split(','))
   jobDir = jobVariableDict['PBS_O_WORKDIR']
   jobStart = job.find('start_time').text
   jobPPN = job.find('Resource_List').find('nodes').text.split('=')[1]
   jobWalltime = job.find('resources_used')
   if jobWalltime == None:
      jobWalltime = '00:00:00'
   else:
      jobWalltime = jobWalltime.find('walltime').text
   return {'jobDir': jobDir, 'jobStart': jobStart, 'jobPPN': jobPPN, 'jobWalltime':jobWalltime}

def get_qinfo_data(jobid):
   # Parse qstat output
   qstatXml = ET.fromstring(qstat(subprocess.getoutput("which qstat"),jobid))
    
   # Data structures
   queueInfo = {} # queue: [slots, used]
   jobInfo = {} # queue: [[user, name, state, id]]
   queueInfo['batch'] = [16,0]

   for job in qstatXml.iter("Job"):
      data = find_job_data(job)
      if 'batch' in jobInfo: jobInfo['batch'].append(data)
      else: jobInfo["batch"] = [data]

   return queueInfo, jobInfo

# main

# get job id from command line
jobid = sys.argv[1].split('.')[0]

#get job info from qstat
queueInfo, jobInfo = get_qinfo_data(jobid)

# pull certain data for writing
walltime = jobInfo['batch'][0]['jobWalltime']
timePattern = "%a %b %d %H:%M:%S %Z %Y"
startTime = time.strftime(timePattern, time.localtime(float(jobInfo['batch'][0]['jobStart'])))
stopTime = time.strftime(timePattern, time.localtime())
#jobTime = str(round((stopTime - startTime) / 3600.0, 1)) + " hrs" 

queueCompleteFile = "/home/"+os.environ["LOGNAME"]+"/.queue_complete"
qcfile = open(queueCompleteFile, 'a')
data = {int(jobid): {'Dir': jobInfo['batch'][0]['jobDir'], 'Start': startTime, 'Stop': stopTime, 'Elapsed Time': walltime, 'Number Processors': int(jobInfo['batch'][0]['jobPPN'])}}
print(yaml.dump(data,default_flow_style=False))
yaml.dump(data,qcfile,default_flow_style=False)
qcfile.close()


