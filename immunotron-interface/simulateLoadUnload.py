#! /usr/bin/env python3
import pickle,sys,os,platform
import numpy as np

schedulePath = 'schedules/'
matrixPath = 'matrices/'
finalInputPath = 'misc/'
if platform.system() == 'Windows':
    finalOutputPath = 'C:/ProgramData/Tecan/EVOware/database/variables/'
else:
    finalOutputPath = 'variables/'

def main():
    simulateLoadUnload(0,0,3)

def simulateLoadUnload(incubatorFridge, UnloadLoad, CurrentExperimentSlot):
    container = 'incubator'
    if incubatorFridge == 1:
        container = 'fridge'
    arr = np.loadtxt(finalOutputPath+'{}LoadUnload.txt'.format(container),delimiter=',')
    if UnloadLoad == 1:
        arr[CurrentExperimentSlot-1] = 1
    else:
        arr[CurrentExperimentSlot-1] = 0
    np.savetxt(finalOutputPath+'{}LoadUnload.txt'.format(container),arr.reshape(1, arr.shape[0]),delimiter=',',fmt='%d')

main()

""" expIDs = [0,1]
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
        np.savetxt(finalOutputPath+'fridgeLoadUnload.txt',arr,delimiter=',') """
