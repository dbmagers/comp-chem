#!/usr/bin/python3

# extracts xyz file from cfour2.0 output file
# author: D.B. Magers

import sys
import argparse

# argument parser
description = 'Extracts xyz data from cfour2.0 output file'
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-i', '--input', help='Set the name of the input file. (Default: output.dat)', default='output.dat')
parser.add_argument('-o', '--output', default='geo_bohr.xyz', help='Set the name of the output file. (Default: geo_bohr.xyz)')
parser.add_argument('-f', '--first', action='store_true', help='Pull first xyz instead of last')
args = vars(parser.parse_args())

# read file
f = open(args['input'], "r")
outputLines = f.readlines()
f.close()
outputLines = [x.strip() for x in outputLines]

# initialize print lines
printLines = []

# find first xyz
if args['first']:
    for i, line in enumerate(outputLines):
        if 'Coordinates (in bohr)' in line:
            for line2 in outputLines[i+3:]:
                if '----' in line2:
                    break
                printLines.append(line2)
            break

# find last xyz
else:
    for i, line in reversed(list(enumerate(outputLines))):
        if 'Coordinates (in bohr' in line:
            for line2 in outputLines[i+3:]:
                if '----' in line2:
                    break
                printLines.append(line2)
            break

# clean up extracted xyz
for i,line in enumerate(printLines):
    split_line = line.split()
    split_line.pop(1)
    for j,item in enumerate(split_line[1:]):
        if not item.startswith('-'):
            item = ' '+item
        split_line[j+1] = item
    line = ' '.join(split_line)
    printLines[i] = line

# determine number of atoms
num_atoms = str(len(printLines))

# add header
printLines.insert(0,'[bohr]')
printLines.insert(0,num_atoms)

# print
for item in printLines:
    print(item)
 
# write file
with open('geo_bohr.xyz','w') as f_out:
    for item in printLines:
        f_out.write('%s\n' % item)
    f_out.close()

