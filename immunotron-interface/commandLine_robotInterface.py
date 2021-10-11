import json,pickle,math,sys,os,string
from datetime import datetime
import datetime as dt
import numpy as np
from integrateExperiments import integrateExperiments

schedulePath = 'schedules/' 
matrixPath = 'matrices/'
finalPath = ''
#finalPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'

culturePlateLength = 12
culturePlateWidth = 8
timepointTemplates = {8:[3,7,15,23,35,47,59,72],12:[1,3,6,12,18,24,30,36,42,48,60,72],16:[1,3,5,7,11,15,19,23,29,35,41,47,53,59,65,72]}

experimentID = input('Enter a (short) name for this experiment: ')

plateOffset = int(input('Enter the plate position (from the bottom of the rack): ')) - 1

platePoseRestriction = input('Enter cooling plate positions to restrict this experiment to (1-4): ')
if platePoseRestriction == '':
    platePoseRestriction = [1,2,3,4]
else:
    platePoseRestriction = list(map(int,platePoseRestriction.split(',')))

numConditions = int(input('Enter number of conditions: '))
numConditionsPerCulturePlate = int(input('Enter number of conditions per culture plate: ')) 
blankColumnString = input('Enter blank columns separated by commas: ')
if blankColumnString != '':
    if ',' in blankColumnString:
        blankColumns = list(map(int,blankColumnString.split(',')))
    else:
        blankColumns = [int(blankColumnString)]
else:
    blankColumns = []
numTimepoints = int(input('Enter number of timepoints: '))
startTime = input('Enter the estimated start time of the experiment (HH:MM AM/PM): ')
daysAgo = input('Enter how many days ago the experiment started: ')
if daysAgo == '':
    daysAgo = 0
else:
    daysAgo = int(daysAgo)

enterTimepointsManually = input('Do you want to enter the timepoints manually (y/n)? ')
if enterTimepointsManually == 'y':
    timepointList = [0.0]
    for timepoint in range(numTimepoints):
        timepointList.append(float(input('Enter time of timepoint '+str(timepoint+1)+' in hours: ')))
else:
    if numTimepoints in timepointTemplates:
        timepointList = [0.0]+timepointTemplates[numTimepoints]
    else:
        timepointLength = float(input('Enter length of timeseries (in hours): '))
        timepointInterval = timepointLength/numTimepoints
        timepointList = [0.0]
        for i in range(numTimepoints):
            timepointList.append((i+1)*timepointInterval)

integratingExperiments = input('Enter the names of currently running experiments you want to integrate this one with, separated by commas (can leave blank if not needed): ')

numCulturePlatesForExperiment = math.ceil(numConditions / numConditionsPerCulturePlate)
numCultureColumnsPerPlate = math.ceil(numConditions / culturePlateWidth / numCulturePlatesForExperiment)

timepointIntervals = [t-s for s,t in zip(timepointList,timepointList[1:])]

totalNumSupPlates = len(platePoseRestriction) 

#Change to 384 by multiplying by culture plate length and width by 2
numSupPlates = math.ceil((numTimepoints*numConditions)/(culturePlateLength*2*culturePlateWidth*2))

#No need to change this; this is the culture plate shelf (should be the same in 384 format)
numActualTimepoints = numTimepoints
numTimepoints *= numCulturePlatesForExperiment
plateArray = np.tile(list(range(1+plateOffset,numCulturePlatesForExperiment+1+plateOffset)),numActualTimepoints)

#No need to change this, this is the culture columns to aspirate (should be the same in 384 format)
cultureColumnArray = np.zeros([numTimepoints,culturePlateLength])
numConditionColumns = numCultureColumnsPerPlate 
cultureList = []
counter = 0
for conditionColumn in range(1,culturePlateLength+1):
    if conditionColumn not in blankColumns and counter < numConditionColumns:
        cultureList.append(conditionColumn)
        counter+=1

cultureArray = np.asarray(cultureList)
#cultureArray = np.array(list(range(1+offset,numConditionColumns+1+offset)))

supernatantColumnArray = np.zeros([numTimepoints,culturePlateLength])
wellPoseArray = np.zeros([numTimepoints,culturePlateLength])
allColumns = np.tile(np.array(list(range(1,culturePlateLength+1))),numSupPlates*4)
splitColumns = np.split(allColumns,numTimepoints)
allColumns2 = np.tile(np.array(list(range(1,culturePlateLength*4+1))),numSupPlates)
splitColumns2 = np.split(allColumns2,numTimepoints)

supernatantPlateArray = np.zeros([numTimepoints,culturePlateLength])
plateArrays = []
wellPoseArrays = []
plateNumber = 0
completeColumnCounter = 0
wellPose = -1 
for splitColumn in splitColumns2:
    timepointPlateArray = np.zeros(splitColumn.shape)
    timepointWellPoseArray = np.zeros(splitColumn.shape)
    for i,column in enumerate(list(splitColumn)):
        if column == 1:
            plateNumber+=1
        if completeColumnCounter % culturePlateLength == 0:
            wellPose+=1
        timepointPlateArray[i] = ((plateNumber-1)%totalNumSupPlates)+min(platePoseRestriction)
        timepointWellPoseArray[i] = wellPose % 4 
        completeColumnCounter+=1
    plateArrays.append(timepointPlateArray)
    wellPoseArrays.append(timepointWellPoseArray)

supernatantLidArray = np.zeros([numTimepoints,1])
waitTimeArray = np.zeros([numTimepoints,1])

timeoffset = 10 

actualTimepoint = 0
for timepoint in range(numTimepoints):
    cultureColumnArray[timepoint,:numConditionColumns] = cultureArray
    supernatantColumnArray[timepoint,:numConditionColumns] = splitColumns[timepoint]
    supernatantPlateArray[timepoint,:numConditionColumns] = plateArrays[timepoint]
    supernatantLidArray[timepoint,0] = int(''.join(list(map(str,list(map(int,list(np.unique(plateArrays[timepoint]))))))))
    wellPoseArray[timepoint,:numConditionColumns] = wellPoseArrays[timepoint]
    if timepoint % numCulturePlatesForExperiment == 0:
        waitTimeArray[timepoint,0] = int(timepointIntervals[actualTimepoint]*60-timeoffset*(numCulturePlatesForExperiment-1))
        actualTimepoint+=1
    else:
        waitTimeArray[timepoint,0] = timeoffset

plateArray = np.reshape(plateArray,(plateArray.shape[0],1))

fullMatrix = np.hstack([plateArray,supernatantLidArray,cultureColumnArray,supernatantPlateArray,supernatantColumnArray,wellPoseArray,waitTimeArray])

name='matrix_'+experimentID+'.txt'
np.savetxt(matrixPath+name,fullMatrix,fmt='%d',delimiter=',')
#np.savetxt(name,fullMatrix,fmt='%d',delimiter=',')

#np.savetxt('numTimepoints.txt',np.array([fullMatrix.shape[0]]),fmt='%d',delimiter=',')

#Produces file that contains the times each time point are performed, with a >>> signifying that the collection/sup/cell plates will be full at the end of the timepoint
def createSchedule(timename):
    baseTimeArrayHours = timepointList[1:]
    now = datetime.today() - dt.timedelta(days=daysAgo)
    parsedStartTime = datetime.strptime(startTime,'%I:%M %p')
    fullStartTime = datetime(now.year,now.month,now.day,parsedStartTime.hour,parsedStartTime.minute)
    currentTimePointTime = fullStartTime
    with open(timename,'w') as output:
        print('USE TIMEPOINTS IN PARENTHESES TO SET TIMEPOINT ON ROBOT',file=output,sep="\r\n")
        print(fullStartTime.strftime('Start Time: %Y-%m-%d %a %I:%M %p'),file=output,sep="\r\n")
        for i in range(0,len(baseTimeArrayHours)):
            currentTimePointTime = fullStartTime + dt.timedelta(hours=baseTimeArrayHours[i])
            if((i+1)%3 == 0):
                print(currentTimePointTime.strftime('Timepoint '+str(i+1)+': >>>%Y-%m-%d %a %I:%M %p' + ' ('+str(i+1+i*(numCulturePlatesForExperiment-1))+ ')'),file=output,sep="\r\n")
            else:
                print(currentTimePointTime.strftime('Timepoint '+str(i+1)+': %Y-%m-%d %a %I:%M %p' + ' ('+str(i+1+i*(numCulturePlatesForExperiment-1))+ ')'),file=output,sep="\r\n")

timename = schedulePath+'schedule_'+experimentID+'.txt'
createSchedule(timename)

if integratingExperiments != '':
    experimentIDs = integratingExperiments.split(',')
    if experimentID not in experimentIDs:
        experimentIDs.append(experimentID)
    integrateExperiments(experimentIDs)
    oldNumTimepoints = np.loadtxt(finalPath+'numTimepoints.txt')
    np.savetxt(finalPath+'numTimepoints.txt',np.array([oldNumTimepoints+numTimepoints]),fmt='%d',delimiter=',')
    print('Experiment Added!')
else:
    np.savetxt(finalPath+'numTimepoints.txt',np.array([numTimepoints]),fmt='%d',delimiter=',')
    name='Full_Matrix_OnlySup.txt'
    np.savetxt(finalPath+name,fullMatrix,fmt='%d',delimiter=',')
    timename = 'masterSchedule.txt'
    createSchedule(timename)
    print('Experiment Created!')
