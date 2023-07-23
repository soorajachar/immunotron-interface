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
