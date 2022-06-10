#!/usr/bin/python3

# converts xyz file from angstrom to bohr or vice versa
# author: D.B. Magers

import argparse
from argparse import RawTextHelpFormatter
bohr_to_angstrom = 0.52917721067 # codata 2014 value

# argument parser
description = 'Converts xyz file units to angstrom or bohr.\n\n1 bohr = '+str(bohr_to_angstrom)+'\n\nxyz file is assumed to follow the the standard format.\nExample:\n 2\n comment line\n H  0.0000  0.0000  0.3705\n H  0.0000  0.0000 -0.3705\n ...'
parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
parser.add_argument('-u','--unit', choices=["angstrom","bohr"], help="Set unit to convert to", default='angstrom')
parser.add_argument('-i', '--input', help='Set the name of the input file. (Default: geo.xyz)', default='geo.xyz')
parser.add_argument('-o', '--output', help='Set the name of the output file. (Default: geo_[unit].xyz)')
parser.add_argument('-p', '--print', action='store_true', help='Print output to screen instead of file. Overrides -o flag.')
args = vars(parser.parse_args())

# read input file
f = open(args['input'], "r")
inputLines = f.readlines()
f.close()
inputLines = [x.strip() for x in inputLines]

# define variables
unit = args['unit']
file_length = len(inputLines)
output = args['output']
if output is None:
    output = 'geo_'+unit+'.xyz'

# check for consistency
    # does num atoms on first line match file

# add units to file comment line
inputLines[1] +=' ['+unit+']'

# determine number of digits to past decimal to print, look at z component of first atom for ref
digits = str(len(inputLines[2].split()[-1].split('.')[-1]))

# do conversion and replace
for i, line in enumerate(inputLines[2:]):
    split_line = line.split()
    for j,item in enumerate(split_line[1:]):
        if unit == 'angstrom':
            temp = str(('{0:.'+digits+'f}').format(float(item) * bohr_to_angstrom))
        elif unit == 'bohr':
            temp = str(('{0:.'+digits+'f}').format(float(item) / bohr_to_angstrom))
        # add space for positive numbers for padding
        if not temp.startswith('-'):
            temp = ' '+temp
        temp = ' '+temp
        split_line[j+1] = temp
    line = " ".join(split_line)
    inputLines[i+2] = line

# write file
if not args['print']:
    with open(output,'w') as f_out:
        for item in inputLines:
            f_out.write("%s\n" % item)
    f_out.close()
else:
    for item in inputLines:
        print(item)


