#!/usr/bin/python3

# script for writing submit scripts to torque queue

import fnmatch
import argparse
import os
import sys
from subprocess import call
from mako.template import Template
from programs import psi4,nwchem,gamess,cfour,psi4beta
import yaml
import socket

# get sys info, paths, nodes, queues
sjob_path = os.path.dirname(os.path.abspath(__file__))
hostname = socket.gethostname()
cluster_name = hostname

def dummy_footer(args,cluster):
    return ""

checks = {
           'gamess':   { 'check_input': gamess.check_input,   'footer': dummy_footer },
           'nwchem':   { 'check_input': nwchem.check_input,   'footer': nwchem.footer },
           'cfour':    { 'check_input': cfour.check_input,    'footer': cfour.footer },
           'cfour2':   { 'check_input': cfour.check_input,    'footer': cfour.footer },
           'cfour2p':  { 'check_input': cfour.check_input,    'footer': cfour.footer },
           'psi4beta': { 'check_input': psi4beta.check_input, 'footer': dummy_footer },
           'psi4':     { 'check_input': psi4.check_input,     'footer': dummy_footer } }

curdir = os.getcwd().split('/')[-1]
scriptname = '%s.sh' % curdir
commandline = ' '.join(sys.argv)
nodeInfo = yaml.safe_load(open(sjob_path + '/templates/info.yaml','r'))
queue_choices = nodeInfo[cluster_name]['queues'].keys()

# get available programs
template_path = sjob_path + '/templates/' + cluster_name + '/'
programs = []
for root, dirnames, filenames in os.walk(template_path):
  for filename in fnmatch.filter(filenames, '*.tmpl'):
      programs.append(os.path.join(root, filename))

program_choices = [elem[len(template_path):-5] for elem in programs]
program_choices.remove('header')

# argumet parser from command line
parser = argparse.ArgumentParser(description='Submit jobs to the torque queue.')
parser.add_argument('-d', '--debug', action='store_true',  help='Just create the script. Do not submit.')
parser.add_argument('-i', '--input', help='Set the name of the input file. (Default: input.dat)', default='input.dat')
parser.add_argument('-N', '--name', help='Set name of the job. (default: %s)' % curdir, default=curdir)
parser.add_argument('-o', '--output', help='Set the name of the output file. (Default: output.dat)', default='output.dat')
parser.add_argument('-p', '--program', choices=program_choices, required=True, help='Program to use.')
parser.add_argument('-q', '--queue', choices=queue_choices, help='Queue to submit to.', default="batch")
parser.add_argument('-n', '--nslot', help='Set the number of processors to use per node.', type=int, default=0)
parser.add_argument('--no-parse', action='store_false', dest='parseInput', default=True, help='Parse input file to detect common errors [default: parse]')

# global argument checks
args = vars(parser.parse_args())

if args['nslot'] % 2 != 0 and args['nslot'] != 1:
    parser.error("nslot must be even or 1.")
if args['nslot'] > nodeInfo[cluster_name]['queues'][args['queue']]['numProc'] / 2:
    parser.error("nslot exceeds max allowed of %s" % (nodeInfo[cluster_name]['queues'][args['queue']]['numProc'] / 2))
if args['nslot'] == 0:
    if args['program'] == 'psi4' or args['program'] == 'psi4beta':
	    args['nslot'] = 2
    else:
        args['nslot'] = 1

# check for ZMAT for cfour run
if (args['program'] == 'cfour' or args['program'] == 'cfour2' or args['program'] == 'cfour2p') and args['input'] != 'ZMAT':
#    print("For cfour ZMAT is required for input file.  Looking for ZMAT.")
    args['input'] = 'ZMAT'
if args['program'] == 'cfour' or args['program'] == 'cfour2' or args['program'] == 'cfour2p':
    args['nslot'] = 1

# Input Check
base_program_name = args['program'].split('/')[0]
checks[base_program_name]['check_input'](args, nodeInfo[cluster_name]['queues'])

# Load Mako template file
header_template = Template(filename=template_path+'header.tmpl')
script = None
try:
    script = open(scriptname, 'w')
    script.write(header_template.render(queue=args['queue'],
					name=args['name'],
					nslot=args['nslot'],
					mppwidth=args['nslot'],
					cmdline=commandline))
except IOError as e:
    print("Unable to create your script file.")
    sys.exit(1)

# Load in program specific file
program = None
try:
    program = Template(filename=(template_path+'%s.tmpl') % args['program'])
except IOError as e:
    print("Unable to open the program template file for the requested program.")
    sys.exit(1)

script.write(program.render(nslot=args['nslot'],
			    name=args['name'],
                            input=args['input'],
                            output=args['output'],
                            ncorepernode=nodeInfo[cluster_name]['queues'][args['queue']]['numProc'],
			    nmpipersocket=args['nslot']/4,
			    mppwidth=args['nslot'],
			    ))

script.write(checks[base_program_name]['footer'](args,cluster_name))

# write to queue_complete
script.write("/opt/miniconda3/envs/python2.7/bin/python /opt/scripts/sjob/qwrite $PBS_JOBID\n")

# make sure there are blank lines at the end
script.write("\n\n")

script.close()

# Ensure /tmp and /tmp1 have the proper permissions
if args['debug'] == False:
    call(['qsub', scriptname])

