import json,pickle,math,sys,os,string
from datetime import datetime
import datetime as dt
import time
import numpy as np
from integrateExperiments import integrateExperiments
import platform

culturePlateLength = 12
culturePlateWidth = 8
timepointTemplates = {6:[4,10,24,32,48,72],12:[1,3,6,12,18,24,30,36,42,48,60,72],8:[3,7,15,23,35,47,59,72],12:[1,3,6,12,18,24,30,36,42,48,60,72],16:[1,3,5,7,11,15,19,23,29,35,41,47,53,59,65,72]}

experimentTypeDict = {
        'Supernatant (Sooraj)':1,
        'Supernatant+Fix/Perm (Madison)':2,
        'Reverse Plating (Anagha)':3,
        'Supernatant+LD/Ab/Fix/Perm (Anagha)':4
        }
schedulePath = 'schedules/' 
matrixPath = 'matrices/'
if platform.system() == 'Windows':
    finalPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
else:
    finalPath = ''

def generateExperimentMatrix(singleExperiment=True,**kwargs):
    schedulePath = 'schedules/' 
    matrixPath = 'matrices/'
    if platform.system() == 'Windows':
        finalPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
    else:
        finalPath = ''
    experimentID = kwargs['experimentID']
    plateOffset = kwargs['plateOffset']-1
    platePoseRestriction = kwargs['platePoseRestriction']
    numConditions = kwargs['numConditions']
    blankColumns = kwargs['blankColumns']
    numTimepoints = kwargs['numTimepoints']
    startTime = kwargs['startTime']
    experimentType = experimentTypeDict[kwargs['experimentType']]
    if experimentType in [1,2, 4]:
        #Make sure explicit zero timepoint does not cause issues
        timepointList = [0.0]+[x if x != 0 else 0.1 for x in kwargs['timepointlist']]
        daysAgo = kwargs['daysAgo']
        
        if numConditions < 96:
            numConditionsPerCulturePlate = numConditions
        else:
            if 96 < numConditions < 192:
                numConditionsPerCulturePlate = int(numConditions/2)
            else:
                numConditionsPerCulturePlate = 96 
        
        if experimentType == 1:
            numCulturePlatesForExperiment = math.ceil(numConditions / numConditionsPerCulturePlate)
            numCultureColumnsPerPlate = math.ceil(numConditions / culturePlateWidth / numCulturePlatesForExperiment)
        elif experimentType in [2, 4]:
            numCulturePlatesForExperiment = numTimepoints
            numCultureColumnsPerPlate = culturePlateLength - len(blankColumns)

        timepointIntervals = [t-s for s,t in zip(timepointList,timepointList[1:])]

        totalNumSupPlates = len(platePoseRestriction) 

        #Change to 384 by multiplying by culture plate length and width by 2
        numSupPlates = math.ceil((numTimepoints*numConditions)/(culturePlateLength*2*culturePlateWidth*2))

        #No need to change this; this is the culture plate shelf (should be the same in 384 format)
        numActualTimepoints = numTimepoints

        #Allows for experiments to take up incomplete 384-well plates
        tempTimepoints = 0
        while numTimepoints*culturePlateLength % 48 != 0:
            tempTimepoints += 1
            numTimepoints += 1
            timepointList.append(timepointList[-1]+1.0)
            timepointIntervals.append(1.0)

        if experimentType == 1:
            numTimepoints *= numCulturePlatesForExperiment
            plateArray = np.tile(list(range(1+plateOffset,numCulturePlatesForExperiment+1+plateOffset)),numActualTimepoints)
        elif experimentType in [2, 4]:
            plateArray = np.array(range(1+plateOffset,numTimepoints+1+plateOffset))

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
        allColumns = np.tile(np.array(list(range(1,culturePlateLength+1))),numSupPlates*4) # all columns in 96
        splitColumns = np.split(allColumns,numTimepoints)
        allColumns2 = np.tile(np.array(list(range(1,culturePlateLength*4+1))),numSupPlates) # all columns in 384
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
                timepointPlateArray[i] = platePoseRestriction[0 + ((plateNumber-1)%totalNumSupPlates)]
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
            if experimentType == 1:
                if timepoint % numCulturePlatesForExperiment == 0:
                    waitTimeArray[timepoint,0] = int(timepointIntervals[actualTimepoint]*60-timeoffset*(numCulturePlatesForExperiment-1))
                    actualTimepoint+=1
                else:
                    waitTimeArray[timepoint,0] = timeoffset
            elif experimentType in [2, 4]:
                waitTimeArray[timepoint,0] = int(timepointIntervals[actualTimepoint]*60)
                actualTimepoint+=1
        
        experimentArray = np.full((plateArray.shape[0],1), experimentType)

        plateArray = np.reshape(plateArray,(plateArray.shape[0],1))

        fullMatrix = np.hstack([plateArray,supernatantLidArray,cultureColumnArray,supernatantPlateArray,supernatantColumnArray,wellPoseArray,waitTimeArray, experimentArray])
        if tempTimepoints > 0:
            fullMatrix = fullMatrix[:-1*tempTimepoints]
        for i in range(tempTimepoints):
            timepointList.pop()
            timepointIntervals.pop()
            numTimepoints -= 1

        name='matrix_'+experimentID+'.txt'
        np.savetxt(matrixPath+name,fullMatrix,fmt='%d',delimiter=',')
        #np.savetxt(name,fullMatrix,fmt='%d',delimiter=',')

        #np.savetxt('numTimepoints.txt',np.array([fullMatrix.shape[0]]),fmt='%d',delimiter=',')

        #Produces file that contains the times each time point are performed
        def createSchedule(timename,master=False):
            baseTimeArrayHours = timepointList[1:]
            now = datetime.today() - dt.timedelta(days=daysAgo)
            parsedStartTime = datetime.strptime(startTime,'%I:%M %p')
            fullStartTime = datetime(now.year,now.month,now.day,parsedStartTime.hour,parsedStartTime.minute)
            currentTimePointTime = fullStartTime
            with open(timename,'w') as output:
                print('USE TIMEPOINTS IN PARENTHESES TO SET TIMEPOINT ON ROBOT',file=output,sep="\r\n")
                if master:
                    print(file=output,sep="\r\n")
                    print('Experiment '+experimentID+' '+fullStartTime.strftime('Start Time: %Y-%m-%d %a %I:%M %p'),file=output)
                    print(file=output,sep="\r\n")
                else:
                    print(fullStartTime.strftime('Start Time: %Y-%m-%d %a %I:%M %p'),file=output,sep="\r\n")
                for i in range(0,len(baseTimeArrayHours)):
                    currentTimePointTime = fullStartTime + dt.timedelta(hours=baseTimeArrayHours[i])
                    robotTimepoint = i+1
                    if experimentType == 1:
                        robotTimepoint += +i*(numCulturePlatesForExperiment-1)
                    print(currentTimePointTime.strftime('Timepoint '+str(i+1)+': %Y-%m-%d %a %I:%M %p' + ' ('+str(robotTimepoint)+ ')'),file=output,sep="\r\n")

        timename = schedulePath+'schedule_'+experimentID+'.txt'
        createSchedule(timename)
        
        if singleExperiment:
            np.savetxt(finalPath+'numTimepoints.txt',np.array([numTimepoints]),fmt='%d',delimiter=',')
            name='Full_Matrix_OnlySup.txt'
            np.savetxt(finalPath+name,fullMatrix,fmt='%d',delimiter=',')
            timename = 'masterSchedule.txt'
            createSchedule(timename,master=True)
            timename = schedulePath+'masterSchedule.txt'
            createSchedule(timename,master=True)
        
        return numTimepoints
    else:
        # Make sure explicit zero timepoint does not cause issues
        timepointList = [0.0] + [x if x != 0 else 0.1 for x in kwargs['timepointlist']]
        daysAgo = kwargs['daysAgo']

        schedulePath = 'schedules/'
        matrixPath = 'matrices/'
        if platform.system() == 'Windows':
            finalPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
        else:
            finalPath = ''

        if experimentType == 3:
            numCulturePlatesForExperiment = math.ceil(numConditions / 96)
            numCultureColumnsPerTimepoint = math.ceil(numConditions / culturePlateWidth / numTimepoints)

        # a list of which incubator plates to remove
        incPlateList = []
        for timepointNum in range(numTimepoints):
            plateNum = math.ceil(numCultureColumnsPerTimepoint * (timepointNum + 1) / culturePlateLength)
            incPlateList.append(plateNum)
        incPlateArray = np.array(incPlateList)
        incPlateArray = np.reshape(incPlateArray, (incPlateArray.shape[0], 1))

        # cooling plate lids to remove
        coolingPlateLidArray = np.zeros([numTimepoints, 1], dtype=int)

        # media and coculture plates to pipette between
        pipetteList = []
        for timepointNum in range(numTimepoints):
            for colNum in range(numCultureColumnsPerTimepoint):
                pipetteList.append((timepointNum * numCultureColumnsPerTimepoint + colNum) % culturePlateLength + 1)
            for blankCol in range(culturePlateLength - numCultureColumnsPerTimepoint):
                pipetteList.append(0)
        pipetteArray = np.array(pipetteList)
        pipetteArray = np.reshape(pipetteArray, [numTimepoints, culturePlateLength])

        # cooling plate positions to transfer supernatant to
        coolingPlatePosArray = np.zeros([numTimepoints, culturePlateLength], dtype=int)

        # cooling plate columns to transfer supernatant to
        coolingPlateColArray = np.zeros([numTimepoints, culturePlateLength], dtype=int)

        # cooling plate well pos to transfer supernatant to
        coolingPlateWellPosArray = np.zeros([numTimepoints, culturePlateLength], dtype=int)

        # time to next timepoint
        timeOffset = 5.0
        timepointIntervals = [int((t - s) * 60 - timeOffset) for s, t in zip(timepointList, timepointList[1:])]
        timeArray = np.array(timepointIntervals)
        timeArray = np.reshape(timeArray, (timeArray.shape[0], 1))

        # experiment number
        expNoArray = np.tile(3, numTimepoints)
        expNoArray = np.reshape(expNoArray, (expNoArray.shape[0], 1))

        # join arrays together
        joinedArray = np.hstack(
            [incPlateArray, coolingPlateLidArray, pipetteArray, coolingPlatePosArray, coolingPlateColArray,
             coolingPlateWellPosArray, timeArray, expNoArray])

        # save matrix as a txt file
        name = 'matrix_' + experimentID + '.txt'
        np.savetxt(matrixPath + name, joinedArray, fmt='%d', delimiter=',')

        # Produces file that contains the times each time point are performed

        def createSchedule(timename, master=False):
            baseTimeArrayHours = timepointList[1:]
            now = datetime.today() - dt.timedelta(days=daysAgo)
            parsedStartTime = datetime.strptime(startTime, '%I:%M %p')
            fullStartTime = datetime(now.year, now.month, now.day, parsedStartTime.hour, parsedStartTime.minute)
            currentTimePointTime = fullStartTime
            with open(timename, 'w') as output:
                print('USE TIMEPOINTS IN PARENTHESES TO SET TIMEPOINT ON ROBOT', file=output, sep="\r\n")
                if master:
                    print(file=output, sep="\r\n")
                    print('Experiment ' + experimentID + ' ' + fullStartTime.strftime('Start Time: %Y-%m-%d %a %I:%M %p'),
                          file=output)
                    print(file=output, sep="\r\n")
                else:
                    print(fullStartTime.strftime('Start Time: %Y-%m-%d %a %I:%M %p'), file=output, sep="\r\n")
                for i in range(0, len(baseTimeArrayHours)):
                    currentTimePointTime = fullStartTime + dt.timedelta(hours=baseTimeArrayHours[i])
                    robotTimepoint = i + 1
                    if experimentType == 1:
                        robotTimepoint += +i * (numCulturePlatesForExperiment - 1)
                    print(currentTimePointTime.strftime(
                        'Timepoint ' + str(i + 1) + ': %Y-%m-%d %a %I:%M %p' + ' (' + str(robotTimepoint) + ')'),
                          file=output, sep="\r\n")

        timename = schedulePath + 'schedule_' + experimentID + '.txt'
        createSchedule(timename)

        if singleExperiment:
            np.savetxt(finalPath + 'numTimepoints.txt', np.array([numTimepoints]), fmt='%d', delimiter=',')
            name = 'Full_Matrix_OnlySup.txt'
            np.savetxt(finalPath + name, fullMatrix, fmt='%d', delimiter=',')
            timename = 'masterSchedule.txt'
            createSchedule(timename, master=True)
            timename = schedulePath + 'masterSchedule.txt'
            createSchedule(timename, master=True)
        return numTimepoints

def combineExperiments(experimentIDs,experimentTypes,numRows,fullMatrix=[]):
    integrateExperiments(experimentIDs,experimentTypes)
    np.savetxt(finalPath+'numTimepoints.txt',np.array([numRows]),fmt='%d',delimiter=',')
