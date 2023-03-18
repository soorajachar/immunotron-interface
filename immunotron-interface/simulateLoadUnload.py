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
#tower2s = [True,True]
tower2s = [False,False]
incAction = 'unload'
fridgeAction = 'unload'

for tower2,expID in zip(tower2s,expIDs):
    if incAction == 'load':
        arr = np.loadtxt(finalOutputPath+'incubatorLoadUnload.txt',delimiter=',')
        arr[expID] = 1
        np.savetxt(finalOutputPath+'incubatorLoadUnload.txt',arr,delimiter=',')
        if tower2:
            arr = np.loadtxt(finalOutputPath+'incubatorLoadUnload2.txt',delimiter=',')
            arr[expID] = 1
            np.savetxt(finalOutputPath+'incubatorLoadUnload2.txt',arr,delimiter=',')
    elif incAction == 'unload':
        arr = np.loadtxt(finalOutputPath+'incubatorLoadUnload.txt',delimiter=',')
        arr[expID] = 0
        np.savetxt(finalOutputPath+'incubatorLoadUnload.txt',arr,delimiter=',')
        if tower2:
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
