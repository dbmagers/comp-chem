#!/usr/bin/python3

# Converts cfour output into gaussian log file 
# in order to be read by avogadro
# author: J. Agarwal, D.B. Magers

import sys

if len(sys.argv) != 2:
    print("Please provide file name as an argument")
    sys.exit()

def bohr2ang(value): return value*0.52917721092

startingBlock = """ Entering Gaussian System, Link 0=g03
 trademark of Gaussian, Inc.
 
 -----------------------------
 #p XXXX/GEN Freq
 -----------------------------"""

orientationBlock = """
 ---------------------------------------------------------------------
 Center     Atomic     Atomic              Coordinates (Angstroms)
 Number     Number      Type              X           Y           Z
 ---------------------------------------------------------------------
"""

inputLines = open(sys.argv[1], "r").readlines()

# Functions to parse job arguments for cfour
def clean_job_line(line):
   if "*CFOUR(" in line: line = line.split("*CFOUR(")[1]
   if ")" in line: line = line.split(")")[0]
   line = line.lstrip(" ").rstrip("\n").rstrip(" ")
   return line.upper()
def parse_job_line(line, keywords):
   items = line.split(",")
   for item in items: keywords.update({item.split("=")[0]: item.split("=")[1]})
def find_job_item(keywords, item_names, throw_error):
   for name in item_names:
      if name in keywords: return keywords[name]
   if throw_error:
      parser.error(" or ".join(item_names)+" not found in keyword list")
   else:
      return False

# Check to make sure output is from a frequency job
keywords = {}
for i in range(0, 2000):
   if "IVIB" in inputLines[i]:
        if inputLines[i].split()[2] == "NO":
            print("Not a Frequency Job, No Conversion Necessary.")
        else: break

# Find coordinates
coordinates = []
for i in range(0, len(inputLines)):
    if "Coordinates (in bohr)" in inputLines[i]:
        for j in range(i+3, len(inputLines)):
            if "-"*10 in inputLines[j]: break
            elif j - i > 100: break
            elif int(inputLines[j].split()[1]) == 0: continue
            else: coordinates.append(inputLines[j])

# Find Infrared Intensities
irIntens = []
for i in range(j, len(inputLines)):
    if "Normal Coordinate Analysis" in inputLines[i]:
        for k in range(i+7, len(inputLines)):
            if "-"*10 in inputLines[k]: break
            elif "-"*4 in inputLines[k].split()[0]: continue
            elif k-i > 100: break
            else: irIntens.append(inputLines[k])

outputFile = open("AVOGADROplot.log","w")

# Write requisite header
outputFile.write(startingBlock+"\n\n")

# Write coordinates
for title in ["Input orientation:", "Standard orientation:"]:
    outputFile.write(title.center(70))
    outputFile.write(orientationBlock)
    for i in range(0, len(coordinates)):
        xyz = ["{0:06f}".format(round(bohr2ang(float(x)), 6)) for x in coordinates[i].split()[2:]]
        printLine = str(i+1).rjust(5)+coordinates[i].split()[1].rjust(11)+"0".rjust(14)
        printLine += xyz[0].rjust(16)+xyz[1].rjust(12)+xyz[2].rjust(12)
        outputFile.write(printLine+"\n")
    outputFile.write(orientationBlock.split("\n")[4]+"\n")

# Write frequencies
k += 4 # To move down to the next block
itemNum = 1 # To write label and get irIntes
while k < len(inputLines):
    print(k)
    if len(inputLines[k].split()) == 3:
        symm = inputLines[k].split()
        #vib = [str('%.4f'%float(x)) for x in inputLines[k+1].split()]
        vib = []
        for x in inputLines[k+1].split():                                                                                       
            if "i" in x: vib.append(str('%.4f'%float(x[:-1]))+"i")
            else: vib.append(str('%.4f'%float(x)))
        vectors = []
        for j in range(k+3, k+3+len(coordinates)):
            temp = inputLines[j][7:].split() # To hold original data
            tempCorr = [] # To hold corrected data
            # Silly routine because CFour formatting is screwed up
            for entry in temp: 
                if len(entry) > 7:
                    # Example: -0.100-0.0349
                    tempCorr.append(float(entry[:entry[1:].find("-")+1]))
                    tempCorr.append(float(entry[entry[1:].find("-")+1:]))
                else: tempCorr.append(float(entry))
            #vectors.append(["{0:02f}".format(round(x, 2)) for x in tempCorr])
            vectors.append(tempCorr)
        # Write data after storing
        outputFile.write("".rjust(19)+str(itemNum).center(5)+"".rjust(18)+str(itemNum+1).center(5)+"".rjust(18)+str(itemNum+2).center(5)+"\n")
        outputFile.write("".rjust(19)+symm[0].center(5)+"".rjust(18)+symm[1].center(5)+"".rjust(18)+symm[2].center(5)+"\n")
        outputFile.write(" Frequencies".ljust(13)+"--"+vib[0].rjust(11)+vib[1].rjust(23)+vib[2].rjust(23)+"\n")
        outputFile.write(" Red. masses".ljust(13)+"--"+"0.0000".rjust(11)+"0.0000".rjust(23)+"0.0000".rjust(23)+"\n")
        outputFile.write(" Frc consts".ljust(13)+"--"+"0.0000".rjust(11)+"0.0000".rjust(23)+"0.0000".rjust(23)+"\n")
        inten = [irIntens[itemNum-1].split()[2], irIntens[itemNum].split()[2], irIntens[itemNum+1].split()[2]]
        outputFile.write(" IR Inten".ljust(13)+"--"+inten[0].rjust(11)+inten[1].rjust(23)+inten[2].rjust(23)+"\n")
        labelLine = "Atom".rjust(5)+"AN".rjust(3)+"".rjust(4)
        for l in range(0, 3): 
            labelLine += "X".center(5)+"".rjust(2)+"Y".center(5)+"".rjust(2)+"Z".center(5)+"".rjust(4)
        outputFile.write(labelLine+"\n")
        for l, line in enumerate(vectors):
            printLine = str(l+1).rjust(4)+coordinates[l].split()[1].rjust(4)+"".rjust(4)
            for m in [0,3,6]: 
                for n in [0, 1, 2]: printLine += ('%.2f' % line[m+n]).rjust(5)+"".rjust(2)
                printLine += "".rjust(2)
            outputFile.write(printLine+"\n")
        k = j
        itemNum += 3
    elif "-"*10 in inputLines[k]: break 
    else: k += 1

outputFile.close()
