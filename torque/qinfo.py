#!/usr/bin/python3

## J. Agarwal
## Rev 1: 5/24/13
## Rev 2: 6/17/13 
## Rev 2.1: 7/11/13
## Rev 2.2 7/26/13
## Rev 2.3 12/27/16 D. Brandon Magers
## Rev 3 __/__ /20 Rayley Farnam

### Import required modules ###
import subprocess
import xml.etree.ElementTree as ET
from optparse import OptionParser as OP
import time
import sys
import os
import yaml

### Functions ###


def qstat(path):
   if os.path.exists(path): return subprocess.getoutput(path+" -f -x") 
   else: 
      print("qstat command not found...exiting.")
      sys.exit()

def check_up_state(state):
   downState = ["au", "adu", "d", "E", "auE"]
   if state is not None:
      if state.text in downState: return False
   return True

def find_job_data(job):
   jobName = job.findtext('Job_Name')
   jobUser = job.find('Job_Owner').text.split("@")[0]
   jobState = job.find('job_state').text 
   jobID = job.find('Job_Id').text.split(".")[0]
   jobPPN = job.findtext('Resource_List/nodes')
   if jobPPN != None and '=' in jobPPN:
      jobPPN = jobPPN.split('=')[1]
   else:
      jobPPN = "0"
   jobWalltime = job.find('resources_used')
   if jobWalltime == None:
      jobWalltime = '00:00:00'
   else:
      jobWalltime = jobWalltime.find('walltime').text
   return [jobUser, jobName, jobState, jobID, jobPPN, jobWalltime]

#functions to color code the output
def red(phrase): return("\033[91m"+phrase+"\033[0m") 
def grey(phrase): return("\033[90m"+phrase+"\033[0m")
def green(phrase): return("\033[92m"+phrase+"\033[0m")
def purple(phrase): return("\033[95m"+phrase+"\033[0m")
def blue(phrase): return("\033[94m"+phrase+"\033[0m")
def bold(phrase): return("\033[1m"+phrase+"\033[0m")

def get_qinfo_data(options):
   queueInfo = {} # queue: [slots, used]
   jobInfo = {} # queue: [[user, name, state, id]]
   queueInfo['batch'] = [15,0]
   # Parse qstat output
   qstatOutput = qstat(subprocess.getoutput("which qstat"))
   if qstatOutput == "":
      return queueInfo, jobInfo
   qstatXml = ET.fromstring(qstatOutput)

   # Data structures
   for job in qstatXml.iter("Job"):
      data = find_job_data(job)
      if jobInfo.__contains__('batch'): jobInfo['batch'].append(data)
      else: jobInfo["batch"] = [data]
   return queueInfo, jobInfo

def print_qinfo_data(queueInfo, jobInfo, options): 
   allbox = u''.join(chr(9472 + x) for x in range(200))
   box = [ allbox[i] for i in (2, 0, 12, 16, 20, 24, 44, 52, 28, 36, 60) ]
   (vbar, hbar, ul, ur, ll, lr, nt, st, wt, et, plus) = box
   # Print title card

   # Column widths and misc information
   nCol = 5 # Job Number column
   fCol = 12 # First column width
   sCol = 18 # Second column width
   tCol = 7 # Third column width
   frCol = 5 # Fourth column width
   ffCol = 11 # Fifth column width
   colSum = fCol + sCol + tCol + nCol + frCol + ffCol
   endLine = bold(red("|"))
   dashLine = bold(red(hbar*((colSum+1)*len(queueInfo))))
   label = bold("ID".center(nCol))+bold("  User".ljust(fCol))+bold("Job Name".ljust(sCol))+bold("Proc.".ljust(tCol))+bold("St.".ljust(frCol))+bold("Elap. Time".ljust(ffCol))+endLine
   blank = " ".center(colSum)+endLine
   
   # Find queue headers
   headers = ""
   for queue in sorted(queueInfo):
      used = str(queueInfo[queue][1])
      avail = str(queueInfo[queue][0] - queueInfo[queue][1])

      headers += (queue.split(".")[0]+" ("+avail+" avail)").center(colSum+1)
   print(headers+"\n"+dashLine)
   print((label*len(queueInfo))+"\n"+dashLine)
   
   completedLines = []
   queue = 'batch'
   logname = options.logname
   if jobInfo:
      if len(jobInfo[queue]) > 0:
         for i in range(0, len(jobInfo[queue])):
            printLine = ""
            printLine += jobInfo[queue][i][3].center(nCol) # Job ID
            if logname == jobInfo[queue][i][0]:
               printLine += bold((" "+jobInfo[queue][i][0][:fCol-2]).ljust(fCol)) # User
            else: printLine += (" "+jobInfo[queue][i][0][:fCol-2]).ljust(fCol)
            printLine += jobInfo[queue][i][1][:sCol-1].ljust(sCol) # Job Name
            printLine += ("  "+jobInfo[queue][i][4]).ljust(tCol) # PPN
            state = jobInfo[queue][i][2] 
            if state == "r": state = bold(green((" "+state).ljust(frCol)))
            else: state = bold(blue((" "+state).ljust(frCol)))
            printLine += state # State
            printLine += (" "+jobInfo[queue][i][5]).ljust(ffCol) # Elapsed Time - Walltime
            printLine += endLine
            if jobInfo[queue][i][2] != "C":
               print(printLine)
            elif logname == jobInfo[queue][i][0]:
               completedLines.append(printLine)
      else: print(blank)
   else:
      print(" No current jobs".ljust(colSum)+endLine)

   # Summary of additional jobs or blank line
   printLine = ""
   for queue in sorted(queueInfo):
      if jobInfo.__contains__(queue):
         if len(jobInfo[queue]) > options.numJobs:
            printLine += grey((" +"+str(len(jobInfo[queue])-options.numJobs)+" more jobs").center(colSum))+endLine
         else: printLine += blank
      else: printLine += blank
   print(dashLine)
   completeFile = "/home/"+logname+"/.queue_complete"
   if os.path.exists(completeFile):
      fullWidth = (colSum+1) * len(queueInfo)
      recentJobs = yaml.safe_load(subprocess.getoutput("tail -"+str(6*options.completed)+" "+completeFile))
      if len(recentJobs) != 0: 
         print((" Recently Completed Jobs for "+options.logname+":").ljust(58)+endLine)
         print(bold("ID".center(nCol))+bold("  Job Name".ljust(fCol+sCol))+bold("Stop Time".ljust(tCol+frCol))+bold("Elap. Time".ljust(ffCol))+endLine)
         for job in recentJobs: 
            stop = ' '.join(recentJobs[job]["Stop"].split()[1:4])
            printLine = str(job).rjust(4)+"  "+recentJobs[job]["Dir"].split("/")[-1].ljust(24)+" "+stop+"  "+recentJobs[job]["Elapsed Time"]
            print(printLine.ljust(fullWidth-1)+endLine)
         print(dashLine)

### Main ###


# Parse arguments
_version = "3"
_description = "qinfo"
parser = OP(add_help_option=True, version=_version, description=_description)
parser.add_option("--watch", default=False, action="store_true", dest="watch",
      help="Continuously update qinfo (every 30 seconds) [default: %default]")
parser.add_option("-n", "--num-jobs", default=26, action="store", dest="numJobs", type="int",
      help="Defines number of jobs to print in qinfo output [default: %default]")
parser.add_option("-c", "--num-complete", default=5, action='store', dest='numComplete', type='int',
      help="Defines number of completed jobs to print in qinfo output [default: %default]")
parser.add_option("-u", "--user", default=os.environ["LOGNAME"], action="store", dest='logname', type='str',
      help="Specifies which user to display completed jobs [default: current user]")
parser.add_option("-r", "--recently-complete", default=2, action="store", dest="completed", type="int",
      help="Defines number of recently completed jobs to display [default: %default]")
(options, args) = parser.parse_args()

if options.numJobs < 1:
   print("We must at least print 1 job!")
   sys.exit()
if options.numJobs > 150:
   print("Over 150 jobs!? That's crazy.")
   sys.exit()

if options.watch:
   for x in range(0, 240): # 2 hrs
      os.system("clear")
      queueInfo, jobInfo = get_qinfo_data(options)
      print_qinfo_data(queueInfo, jobInfo, options)
      print(time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()))
      time.sleep(30)
   print("Are you there? Please re-run command")     
else: 
   queueInfo, jobInfo = get_qinfo_data(options)
   print_qinfo_data(queueInfo, jobInfo, options)

#main()
        
