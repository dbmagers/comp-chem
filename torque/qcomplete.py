#!/usr/bin/python3

# prints completed jobs stored in ~/.queue_complete
# author: J. Argawal, D.B. Magers

import yaml
import os
import subprocess
import time
from optparse import OptionParser as OP
import sys

class colors:
    RED = '\033[91m'
    GREY = '\033[90m'
    GREEN = '\033[92m'
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

# parse arguements
_description = 'qcomplete'
parser = OP(add_help_option=True, description=_description)
parser.add_option("-u", "--user", default=os.environ["LOGNAME"], action="store", dest="logname", type="str",
      help="Specifies which user to display completed jobs [default: current user]")
(options, args) = parser.parse_args()

# Check for queue complete file
homeDirectory = "/home/"+options.logname+"/" 
queueCompleteFile = homeDirectory+".queue_complete"

if not os.path.exists(queueCompleteFile):
   print("No completed jobs file exists ("+queueCompleteFile+")")
   sys.exit()

# Load queue complete YAML
numPrintJobs = 5
queueComplete = yaml.safe_load(subprocess.getoutput("tail -"+str(6*numPrintJobs)+" "+queueCompleteFile))

# Print job information
#print(("-"*28)+"\n# queuecomplete//ja//ver1  #\n"+("-"*28)+"\n")

for x in queueComplete:
   jobDir = queueComplete[x]["Dir"].replace("/home/"+options.logname,"~")
   jobNum = "Job #"+str(x)+": "
   timePattern = "%a %b %m %H:%M:%S %Z %Y"
   startTime = queueComplete[x]["Start"]
   stopTime = queueComplete[x]["Stop"]
   jobTime = queueComplete[x]["Elapsed Time"] 

   print(colors.BOLD+jobNum.rjust(12)+jobDir+colors.END)
   print("".rjust(12)+" RunTime: "+jobTime)
