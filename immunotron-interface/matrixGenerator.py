
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
    experimentID = kwargs['experimentID'] # experiment name
    plateOffset = kwargs['plateOffset']-1 # incubator plate position??
    platePoseRestriction = kwargs['platePoseRestriction'] # cooling plate position
    numConditions = kwargs['numConditions'] # how many conditions per plate
    blankColumns = kwargs['blankColumns'] # blank columns on plate
    numTimepoints = kwargs['numTimepoints'] # number of timepoints in experiment
    startTime = kwargs['startTime'] # time of experiment start
    experimentType = experimentTypeDict[kwargs['experimentType']] # which robot protocol to use
    # START: Could this just be replaced with 1) how many plates are used and 2) blank columns from GUI?
    if experimentType in [1,2,4]:
        # Make sure explicit zero timepoint does not cause issues
        timepointList = [0.0]+[x if x != 0 else 0.1 for x in kwargs['timepointlist']] # make a list of all timepoints in experiment + 0.0
        daysAgo = kwargs['daysAgo'] # if experiment has already started (how many days ago)
        # Decide how many conditions are on a given plate (if more than 1 plate, should be evenly divided between them)
        if numConditions < 96:
            numConditionsPerCulturePlate = numConditions
        else:
            if 96 < numConditions < 192:
                numConditionsPerCulturePlate = int(numConditions/2)
            else:
                numConditionsPerCulturePlate = 96 
        # Determine how many plates needed for number of conditions and how many columns are used on each plate
        if experimentType == 1:
            numCulturePlatesForExperiment = math.ceil(numConditions / numConditionsPerCulturePlate)
            numCultureColumnsPerPlate = math.ceil(numConditions / culturePlateWidth / numCulturePlatesForExperiment)
        elif experimentType in [2,4]:
            numCulturePlatesForExperiment = numTimepoints
            numCultureColumnsPerPlate = culturePlateLength - len(blankColumns)
        # END

        #Determine time between timepoints
        timepointIntervals = [t-s for s,t in zip(timepointList,timepointList[1:])]

        # How many cooling plate positions can be used by experiment
        totalNumSupPlates = len(platePoseRestriction) 

        # Determine total number of supernatant plates needed for experiment
        numSupPlates = math.ceil((numTimepoints*numConditions)/(culturePlateLength*2*culturePlateWidth*2))

        #Allows for experiments to take up incomplete 384-well plates
        numActualTimepoints = numTimepoints
        tempTimepoints = 0
        
        while numTimepoints*numCultureColumnsPerPlate % 48 != 0: #48 columns available per 384 (24 across * 2 rows), add padding timepoints to ensure "full" plate
            tempTimepoints += 1
            numTimepoints += 1
            timepointList.append(timepointList[-1]+1.0)
            timepointIntervals.append(1.0)

        # For a supernatant experiment (same plate(s) throughout), add a "timepoint" for each plate in the experiment (ex. 2 lines for 2 plates) and make list of incubator positions
        if experimentType == 1:
            numTimepoints *= numCulturePlatesForExperiment
            plateArray = np.tile(list(range(1+plateOffset,numCulturePlatesForExperiment+1+plateOffset)),numActualTimepoints)
        # For 1-plate-per-timepoint experiments, generate list of incubator positions (must be consecutive!)
        elif experimentType in [2,4]:
            plateArray = np.array(range(1+plateOffset,numTimepoints+1+plateOffset))

        # Culture columns to aspirate (should be the same in 384 format)
        cultureColumnArray = np.zeros([numTimepoints,culturePlateLength]) # create blank base of matrix for pipetting
        numConditionColumns = numCultureColumnsPerPlate 
        cultureList = []
        counter = 0
        for conditionColumn in range(1,culturePlateLength+1):
            # If column is not blank, add it to list to aspirate/dispense
            if conditionColumn not in blankColumns and counter < numConditionColumns:
                cultureList.append(conditionColumn)
                counter+=1

        cultureArray = np.asarray(cultureList)
        #cultureArray = np.array(list(range(1+offset,numConditionColumns+1+offset)))

        supernatantColumnArray = np.zeros([numTimepoints,culturePlateLength]) # create blank base of matrix for collection plate pipetting
        wellPoseArray = np.zeros([numTimepoints,culturePlateLength]) # create blank base of matrix for collection plate positions
        allColumns = np.tile(np.array(list(range(1,culturePlateLength+1))),numSupPlates*4) # make array of all 96-well culture plate columns across all timepoints based on total number of collection plates for experiment
        splitColumns = np.split(allColumns,numTimepoints) # split columns into timepoints
        allColumns2 = np.tile(np.array(list(range(1,culturePlateLength*4+1))),numSupPlates) # make array of all 384-well collection plate columns across all timepoints
        splitColumns2 = np.split(allColumns2,numTimepoints) # split collection columns into timepoints

        supernatantPlateArray = np.zeros([numTimepoints,culturePlateLength])
        plateArrays = []
        wellPoseArrays = []
        plateNumber = 0
        completeColumnCounter = 0
        wellPose = -1 
        for splitColumn in splitColumns2: # for each timepoint
            timepointPlateArray = np.zeros(splitColumn.shape)
            timepointWellPoseArray = np.zeros(splitColumn.shape)
            for i,column in enumerate(list(splitColumn)): # for non-blank column per timepoint
                if column == 1:
                    plateNumber+=1 # which plate we are analyzing (in case > 1 per timepoint)
                if completeColumnCounter % culturePlateLength == 0: # if we have reached end of position (where each position = 12 columns)
                    wellPose+=1 # move to next position
                timepointPlateArray[i] = platePoseRestriction[0 + ((plateNumber-1)%totalNumSupPlates)] # which cooling plate position to load into
                timepointWellPoseArray[i] = wellPose % 4 # which position this column goes into (0, 1, 2, or 3)
                completeColumnCounter+=1 
            plateArrays.append(timepointPlateArray)
            wellPoseArrays.append(timepointWellPoseArray)

        supernatantLidArray = np.zeros([numTimepoints,1])
        waitTimeArray = np.zeros([numTimepoints,1])

        timeoffset = 10 

        actualTimepoint = 0
        for timepoint in range(numTimepoints):
            cultureColumnArray[timepoint,:numConditionColumns] = cultureArray # Make list of culture plate columns to aspirate/pipette + 0s for blank columns
            supernatantColumnArray[timepoint,:numConditionColumns] = splitColumns[timepoint] # Make list of columns on collection plate to load + 0s for blank columns
            supernatantPlateArray[timepoint,:numConditionColumns] = plateArrays[timepoint] # Which position collection plate to load column into
            supernatantLidArray[timepoint,0] = int(''.join(list(map(str,list(map(int,list(np.unique(plateArrays[timepoint])))))))) # Which position collection plate to load column into
            wellPoseArray[timepoint,:numConditionColumns] = wellPoseArrays[timepoint] # Which 384-well position to load into
            if experimentType == 1: # If this is the last plate for this timepoint, add wait time until next
                if timepoint % numCulturePlatesForExperiment == 0:
                    waitTimeArray[timepoint,0] = int(timepointIntervals[actualTimepoint]*60-timeoffset*(numCulturePlatesForExperiment-1))
                    actualTimepoint+=1
                else: # If there is another plate, add a placeholder wait time based on time it takes to run script per plate
                    waitTimeArray[timepoint,0] = timeoffset
            elif experimentType in [2,4]:
                waitTimeArray[timepoint,0] = int(timepointIntervals[actualTimepoint]*60)
                actualTimepoint+=1
        
        experimentArray = np.full((plateArray.shape[0],1), experimentType) # make list of robot script to use

        plateArray = np.reshape(plateArray,(plateArray.shape[0],1)) # reshape to be able to stack

        fullMatrix = np.hstack([plateArray,supernatantLidArray,cultureColumnArray,supernatantPlateArray,supernatantColumnArray,wellPoseArray,waitTimeArray, experimentArray]) # combine all pieces of matrix
        '''
        COLUMNS (1-indexed for Evoware):
        1: Incubator position
        2: Cooling plate position lid to remove
        3-14: Culture plate columns to aspirate/pipette
        15-26: Cooling plate position to load
        27-38: Cooling plate columns to load
        39-50: Well positions to load
        51: Wait time before next timepoint/row
        52: Robot protocol
        '''
        # Remove padding timepoints
        if tempTimepoints > 0:
            fullMatrix = fullMatrix[:-1*tempTimepoints]
        for i in range(tempTimepoints):
            timepointList.pop()
            timepointIntervals.pop()
            numTimepoints -= 1

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

        if experimentType == 3:
            numCulturePlatesForExperiment = math.ceil(numConditions / 96)
            numCultureColumnsPerTimepoint = math.ceil(numConditions / culturePlateWidth / numTimepoints)

        # a list of which incubator plates to remove (REPLACES plateArray)
        incPlateList = []
        for timepointNum in range(numTimepoints):
            plateNum = math.ceil(numCultureColumnsPerTimepoint * (timepointNum + 1) / culturePlateLength)
            incPlateList.append(plateNum)
        incPlateArray = np.array(incPlateList)
        incPlateArray = np.reshape(incPlateArray, (incPlateArray.shape[0], 1))

        # cooling plate lids to remove - UNUSED
        coolingPlateLidArray = np.zeros([numTimepoints, 1], dtype=int)

        # media and coculture plates to pipette between (REPLACES cultureColumnArray)
        pipetteList = []
        for timepointNum in range(numTimepoints):
            for colNum in range(numCultureColumnsPerTimepoint):
                pipetteList.append((timepointNum * numCultureColumnsPerTimepoint + colNum) % culturePlateLength + 1)
            for blankCol in range(culturePlateLength - numCultureColumnsPerTimepoint):
                pipetteList.append(0)
        pipetteArray = np.array(pipetteList)
        pipetteArray = np.reshape(pipetteArray, [numTimepoints, culturePlateLength])

        # cooling plate positions to transfer supernatant to (UNUSED)
        coolingPlatePosArray = np.zeros([numTimepoints, culturePlateLength], dtype=int)

        # cooling plate columns to transfer supernatant to (UNUSED)
        coolingPlateColArray = np.zeros([numTimepoints, culturePlateLength], dtype=int)

        # cooling plate well pos to transfer supernatant to (UNUSED)
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