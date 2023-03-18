#! /usr/bin/env python3
import pickle,sys,os,platform
import numpy as np

schedulePath = 'schedules/'
matrixPath = 'matrices/'
finalInputPath = 'misc/'
if platform.system() == 'Windows':
    finalOutputPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
else:
    finalOutputPath = 'variables/'

expIDs = [0,1]
incAction = 'unload'
fridgeAction = 'unload'

for expID in expIDs:

    if incAction == 'load':
        arr = np.loadtxt(finalOutputPath+'incubatorLoadUnload.txt',delimiter=',')
        arr[expID] = 1
        np.savetxt(finalOutputPath+'incubatorLoadUnload.txt',arr,delimiter=',')
    elif incAction == 'unload':
        arr = np.loadtxt(finalOutputPath+'incubatorLoadUnload.txt',delimiter=',')
        arr[expID] = 0
        np.savetxt(finalOutputPath+'incubatorLoadUnload.txt',arr,delimiter=',')

    if fridgeAction == 'load':
        arr = np.loadtxt(finalOutputPath+'fridgeLoadUnload.txt',delimiter=',')
        arr[expID] = 1
        np.savetxt(finalOutputPath+'fridgeLoadUnload.txt',arr,delimiter=',')
    elif fridgeAction == 'unload':
        arr = np.loadtxt(finalOutputPath+'incubatorLoadUnload.txt',delimiter=',')
        arr[expID] = 0
        np.savetxt(finalOutputPath+'fridgeLoadUnload.txt',arr,delimiter=',')
