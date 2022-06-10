#!/usr/bin/python3

# 8.9.17
# parses psi4 & cfour2 output files for main info
# author: D.B. Magers

import sys
import re

# get file name from command line
if len(sys.argv) !=2:
    print("Please provide file name to parse as argument")
    sys.exit()

# read file
f = open(sys.argv[1], "r")
outputLines = f.readlines()
f.close()
outputLines = [x.strip() for x in outputLines]

# determine program
program = ''
for i, line in enumerate(outputLines):
    if '* CFOUR Coupled-Cluster techniques for Computational Chemistry *' in line:
        program = 'cfour'
        break
    elif 'Psi4: An Open-Source Ab Initio Electronic Structure Package' in line:
        program = 'psi4'
        break
    elif i > 50:
        print('Neither PSI4 or CFOUR output detected.  See output.')
        sys.exit()
    else: continue

# psi4 parse function
def parsePsi4(outputLines):
    # check for successful job
    if outputLines[-1] != "*** Psi4 exiting successfully. Buy a developer a beer!":
        print("Job did not exit successfully. Please see output.")
        sys.exit()
    
    # find job type
    job = ''
    jobCount = 0
    for line in outputLines:
        if jobCount > 1:
            print('More than 1 job call. Parse is not that fancy. See output.')
            sys.exit()
        elif line.startswith('energy') or line.startswith('optimize') or line.startswith('frequency') or line.startswith('frequencies'):
            job = line
            jobCount += 1
            continue
        elif "*** tstart()" in line:
            if jobCount == 0:
                print('job type not found')
                sys.exit()
            else: break
    
    # strip job line
    jobType = job.split('(')[0]
    jobTheory = re.split('\'|"',job)[1].upper()
    
    # find basis set
    jobBasis = ''
    for line in outputLines:
        if line.startswith('basis'):
            jobBasis = line.split()[-1]
            break
        elif '*** tstart()' in line:
            jobBasis = '?'
            break
    
    # find energy
    printLines = []
    def find_CCSDT():
        for line in reversed(outputLines):
            if '* CCSD(T) total energy' in line:
                pline = line.split()
                pline = (pline[0]+' '+pline[1]).ljust(fCol)+'='+pline[-1].rjust(tCol)
                printLines.insert(0,pline)
                break
            elif 'Psi4:' in line:
                print('CCSD(T) not found')
                break
        find_CCSD()
    
    def find_CCSD():
        for line in reversed(outputLines):
            if '* CCSD total energy' in line:
                pline = line.split()
                pline = (pline[0]+' '+pline[1]).ljust(fCol)+'='+pline[-1].rjust(tCol)
                printLines.insert(0,pline)
                break
            elif 'Psi4:' in line:
                print('CCSD not found')
                break
        find_MP2()
    
    def find_MP2():
        for line in reversed(outputLines):
    #        if '* MP2 total energy' in line or re.match('Total Energy',line) is not None:
            if '* MP2 total energy' in line or line.startswith('MP2 Total Energy'):
                pline = line.split()
                pline = '* MP2'.ljust(fCol)+'='+pline[-1].rjust(tCol)
                printLines.insert(0,pline)
                break
            elif line.startswith('Total Energy'):
                pline = line.split()
                pline = '* DF-MP2'.ljust(fCol)+'='+pline[-2].rjust(tCol)
                printLines.insert(0,pline)
                break
            elif 'Psi4:' in line:
                print('MP2 not found')
                break
        find_SCF()
    
    def find_SCF():
        for line in reversed(outputLines):
            if 'HF Final Energy:' in line or 'HF Final Energy:' in line:
                pline = line[1:].split()
                pline = ('* '+pline[0]).ljust(fCol)+'='+pline[-1].rjust(tCol)
                printLines.insert(0,pline)
                break
            elif 'Psi4:' in line:
                print('SCF not found')
                break
    
    def find_DFT():
        for line in reversed(outputLines):
            if 'KS Final Energy:' in line or 'KS Final Energy:' in line:
                pline = line[1:].split()
                pline[0] = jobTheory
                pline = ('* '+pline[0]).ljust(fCol)+'='+pline[-1].rjust(tCol)
                printLines.insert(0,pline)
                break
            elif 'Psi4:' in line:
                print(jobTheory+' energy not found')
                break
    
    def check_OPT():
        for line in reversed(outputLines):
            if '**** Optimization is complete!' in line:
                break
            elif 'Psi4:' in line:
                print('Optimized failed')
                sys.exit()
    
    def find_sym():
        for i, line in enumerate(outputLines):
            if 'Molecular point group:' in line:
                pline = line.split()
                printLines.insert(0,'Calculation point group: '+pline[-1])
                if 'Full point group:' in outputLines[i+1]:
                    pline = outputLines[i+1].split()
                    printLines.insert(0,'Molecule point group: '+pline[-1])
                break
            elif '*** Psi4 exiting successfully' in line:
                printLines.insert(0,'Starting Symmetry Not Found')
                break
    
    def find_opt_sym():
        for i, line in reversed(list(enumerate(outputLines))):
            if 'Molecular point group:' in line:
                pline = line.split()
                pline2 = outputLines[i+1].split()
                printLines.insert(0,'Optimized Calc point group: '+pline[-1])
                printLines.insert(0,'Optimized Molec point group: '+pline2[-1])
                break
    
    def find_freq():
        for i, line in reversed(list(enumerate(outputLines))):
            if 'Harmonic Frequency' in line:
                for line2 in outputLines[i+3:]:
                    if '-'*47 in line2:
                        break
                    printLines.append(' '+line2)
                break
    
    def find_energy():
        if jobTheory == 'CCSD(T)':
            find_CCSDT()
        elif jobTheory == 'CCSD':
            find_CCSD()
        elif jobTheory == 'MP2':
            find_MP2()
        elif jobTheory == 'SCF' or jobTheory == 'HF':
            find_SCF()
        else:
            find_DFT()
    
    def header(jobTitle):
        printLines.insert(0,jobTitle+' - '+jobTheory+'/'+jobBasis)
    
    def print_results():
        for item in printLines:
            print(item)
    
    fCol = 13
    sCol = 4
    tCol = 24
    
    if jobType == 'optimize':
        check_OPT()
        find_energy()
        find_opt_sym()
        find_sym()
        header('Optimization')
    elif jobType == 'energy':
        find_energy()
        find_sym()
        header('Single point energy')
    elif jobType == 'frequency' or jobType == 'frequencies':
        find_freq()
        find_energy()
        find_sym()
        header('Frequencies')
    
    print_results()

# cfour parse function
def parseCFOUR(outputLines):
    # check for successful job
    for line in reversed(outputLines):
        if '--executable' in line:
            match = re.match("--executable \w* finished with status *0", line)
            if match: break
            else:
                print("Job did not exit successfully. Please see output.")
                sys.exit()
        else: continue
    
    # find job variables
    jobVars = {}
    for i, line in enumerate(outputLines):
        if 'CFOUR Control Parameters' in line:
            for line2 in outputLines[i+5:]:
                if '-'*67 in line2: break
                lineSplit = line2.split()
                key = lineSplit[0]
                value = lineSplit[2]
                if line2.split()[2] == '10D-':
                    value += lineSplit[3]
                jobVars[key] = value
            break
    
    # pitfalls checks
    # zmatrix check, frozen core with bassis set, cc_prog, fcgradnew, etc.
    def sanity_check():
        warnings = []
        if 'CC' in jobVars['CALCLEVEL']:
            if jobVars['ABCDTYPE'] != 'AOBASIS':
                warnings.append('NOTE: ABCDTYPE variable not set to AOBASIS for CC job')
            if jobVars['REFERENCE'] == 'RHF' or jobVars['REFERENCE'] == 'UHF':
                if jobVars['CC_PROGRAM'] != 'ECC':
                    warnings.append('NOTE: CC_PROGRAM variable not set to ECC for RHF or UHF REFERENCE')
            elif jobVars['REFERENCE'] == 'ROHF' and jobType != 'Single point energy':
                if jobVars['CC_PROGRAM'] != 'VCC':
                    warnings.append('WARNING: CC_PROGRAM variable note set to VCC for ROHF REFERENCE and OPT/FREQ job type')
        return warnings
    
    # determine job type
    def find_jobType():
        if jobVars['VIBRATION'] != 'NO':
            return 'Frequencies'
        else:
            for line in outputLines:
                if '-'*80 in line:
                    print('Something went wrong.  No jobType found.')
                    sys.exit()
                if 'will be optimized.' in line:
                    num_opt_coords = line.split()[2]
                    if num_opt_coords == '0':
                        return 'Single point energy'
                    else:
                        return 'Optimization'
                    break
    
    # find symmetry
    def find_sym():
        sym = []
        for i, line in enumerate(outputLines):
            if 'Full symmetry point group:' in line:
                sym.append(outputLines[i].split()[-1])
                sym.append(outputLines[i+1].split()[-1])
                return sym
    
    def find_opt_sym():
        opt_sym = []
        for i, line in reversed(list(enumerate(outputLines))):
            if 'Full symmetry point group:' in line:
                opt_sym.append(outputLines[i].split()[-1])
                opt_sym.append(outputLines[i+1].split()[-1])
                return opt_sym
    
    # find frequencies
    def find_zpve():
        for line in reversed(outputLines):
            if 'Zero-point energy:' in line:
                return line.split()[2]+' kcal/mol'
    
    def find_freq():
        freq = []
        for i, line in reversed(list(enumerate(outputLines))):
            if 'Vibrational frequencies after' in line:
                for line2 in outputLines[i+2:]:
                    if 'Zero-point energy:' in line2:
                        break
                    freq.append(line2)
                return freq
    
    # find energy
    # energy CCSD (Total MP2 energy, E(SCF) or E(SCF)= or HF-SCF energy, Total CCSD energy)
    # freq CCSD(T) (Hf-SCF energy, MP2 energy, CCSD energy, CCSD(T) energy)
    def find_energy():
        if 'The final electronic energy is' in outputLines[-2]:
            return outputLines[-2].split()[-2]
            pline = jobVars['CALCLEVEL'].ljust(fCol)+'='+outputLines[-2].split()[-2].rjust(tCol)
            printLines.insert(0,pline)
    
    # print
    def print_results(jobType, sym, energy, opt_sym, zpve, freq, warnings):
        printLines.append(jobType+' - '+jobVars['CALCLEVEL']+'/'+jobVars['BASIS'])
        printLines.append('Molecule point group: '+sym[0])
        printLines.append('Calculation point group: '+sym[1])
        printLines.append(jobVars['CALCLEVEL'].ljust(fCol)+'='+energy.rjust(tCol))
        if jobType == 'Optimization':
            printLines.append('Optimized Molec point group: '+opt_sym[0])
            printLines.append('Optimized Calc point group: '+opt_sym[1])
        if zpve != None:
            for item in freq:
                printLines.append(item)
            printLines.append('ZPVE'.ljust(fCol)+'='+zpve.rjust(tCol))
        for item in printLines:
            print(item)
        if warnings != None:
            for item in warnings:
                print(item)
    
    fCol = 13
    tCol = 24
    printLines = []
    
    jobType = find_jobType()
    sym = find_sym()
    energy = find_energy()
    if jobType == 'Optimization':
        opt_sym = find_opt_sym()
    else: opt_sym = None
    if jobType == 'Frequencies':
        zpve = find_zpve()
        freq = find_freq()
    else:
        zpve = None
        freq = None
    warnings = sanity_check()
    
    print_results(jobType, sym, energy, opt_sym, zpve, freq, warnings)


# main
if program == 'psi4': parsePsi4(outputLines)
elif program == 'cfour': parseCFOUR(outputLines)
else:
    print('Something went wrong. See output.')
    sys.exit()

