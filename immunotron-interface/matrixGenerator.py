
import json,pickle,math,sys,os,string
from datetime import datetime
import datetime as dt
import time
import numpy as np
from integrateExperiments import integrateExperiments
import platform

<<<<<<< HEAD
def generateExperimentMatrix(singleExperiment=True,**kwargs):
    schedulePath = 'schedules/' 
    matrixPath = 'matrices/'
    finalInputPath = 'misc/'
    if platform.system() == 'Windows':
        finalOutputPath = 'C:/ProgramData/Tecan/EVOware/database/variables/'
    else:
        finalOutputPath = 'variables/'

    culturePlateLength = 12
    culturePlateWidth = 8

    experimentID = kwargs['experimentID'] # experiment name (str)
    protocol = kwargs['protocolParameters'] # protocol parameters (dict)
    plateArray = np.array(kwargs['incubatorPositions']) # incubator plate positions (list)
    fridgePlateArray = kwargs['fridgePositions'] # collection plate positions in fridge (list)
    numCulturePlatesPerTimepoint = kwargs['numPlates'] # how many conditions per plate (int)
    blankColumns = kwargs['blankColumns'] # blank columns on plate (list)
    numTimepoints = kwargs['numTimepoints'] # number of timepoints in experiment (int)
    startTime = kwargs['startTime'] # time of experiment start (str)
    daysAgo = kwargs['daysAgo'] # if experiment has already started (how many days ago)
    robotProtocol = protocol['protocolID'] # which robot protocol to use (int)
    samePlatesAcrossExperiment = protocol['samePlatesAcrossExperiment'] # if the same cultures are pulled out/replaced w/ incubator (bool)
    differentLinesPerPlate = protocol['differentLinesPerPlate'] # whether to treat multiple plates per timepoint as individual timepoints or as one line to be run all at once (bool)
    refrigerateCulturePlate = protocol['refrigerateCulturePlate'] # if the culture plate used per timepoint in the experiment is saved in the fridge rather than the incubator (bool) ** samePlatesAcrossExperiment MUST be False
    transferToCollection = protocol['transferToCollection'] # if samples are to be transferred to a 384-well plate for storage in fridge (bool)
    timeoffset = protocol['protocolLength'] # estimated amount of time (minutes) the protocol takes to run for a single culture plate (int)

    # Make sure explicit zero timepoint does not cause issues
    timepointList = [0.0]+[x if x != 0 else 0.1 for x in kwargs['timepointlist']] # make a list of all timepoints in experiment + 0.0
    #Determine time between timepoints
    timepointIntervals = [t-s for s,t in zip(timepointList,timepointList[1:])]
    

    if samePlatesAcrossExperiment:
        numCulturePlatesForExperiment = numCulturePlatesPerTimepoint
    else:
        numCulturePlatesForExperiment = numTimepoints * numCulturePlatesPerTimepoint

    # Determine total number of collection plates needed for experiment
    numCultureColumnsPerPlate = culturePlateLength - len(blankColumns)
    numCultureColumnsPerTimepoint = numCulturePlatesPerTimepoint * numCultureColumnsPerPlate
    numCollectionPlates = math.ceil((numTimepoints*numCultureColumnsPerTimepoint)/(culturePlateLength*4)) # 4 possible positions on 384-well plate per column on 96-well plate
    if not transferToCollection:
        numCollectionPlates = 0

    #Allows for experiments to take up incomplete 384-well plates
    numActualTimepoints = numTimepoints

    # For a same plate(s) throughout experiment, add a "timepoint" for each plate (ex. 2 lines for 2 plates) if not all run within same script and make list of incubator positions
    # If not same plate(s), len(incubator positions) should already equal number of timepoints
    extraIncubatorArray = np.zeros([numTimepoints, 2], dtype=int)
    if samePlatesAcrossExperiment and differentLinesPerPlate:
        numTimepoints *= numCulturePlatesPerTimepoint
        plateArray = np.tile(plateArray,numActualTimepoints)
        extraIncubatorArray = np.zeros([numTimepoints, 2], dtype=int)
    elif samePlatesAcrossExperiment:
        assert numCulturePlatesPerTimepoint <= 3, 'Only up to 3 plates can be used in a single timepoint without breaking into different lines. If you need this, you will need to expand the matrix!'
        for i, extraPlate in enumerate(plateArray[1:]):
            extraIncubatorArray[:,i] = extraPlate
        plateArray = np.tile(plateArray[0],numActualTimepoints)

    # Culture columns to aspirate (should be the same in 384 format)
    cultureList = []
    for conditionColumn in range(1,culturePlateLength+1):
        # If column is not blank, add it to list to aspirate/dispense (else add 0)
        if conditionColumn not in blankColumns:
            cultureList.append(conditionColumn)
=======
culturePlateLength = 12
culturePlateWidth = 8
timepointTemplates = {6:[4,10,24,32,48,72],12:[1,3,6,12,18,24,30,36,42,48,60,72],8:[3,7,15,23,35,47,59,72],12:[1,3,6,12,18,24,30,36,42,48,60,72],16:[1,3,5,7,11,15,19,23,29,35,41,47,53,59,65,72]}

experimentTypeDict = {
        'Supernatant (Sooraj)':1,
        'Supernatant+Fix/Perm (Madison)':2,
        'Reverse Plating (Anagha)':3,
        'Supernatant+LD/Ab/Fix/Perm (Anagha)':4,
        'Supernatant+Fix/Perm+SupTransfer (Madison)':5,
        'Reverse Kinetics (Dongya)':6,
        'SupTransfer_Only (Madison)':7
        }
schedulePath = 'schedules/' 
matrixPath = 'matrices/'
if platform.system() == 'Windows':
    finalPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
else:
    finalPath = ''

def generateExperimentMatrix(singleExperiment=True,**kwargs):
    experimentID = kwargs['experimentID'] # experiment name
    plateOffset = kwargs['plateOffset']-1 # incubator plate position??
    platePoseRestriction = kwargs['platePoseRestriction'] # cooling plate position
    numConditions = kwargs['numConditions'] # how many conditions per plate
    blankColumns = kwargs['blankColumns'] # blank columns on plate
    numTimepoints = kwargs['numTimepoints'] # number of timepoints in experiment
    startTime = kwargs['startTime'] # time of experiment start
    experimentType = experimentTypeDict[kwargs['experimentType']] # which robot protocol to use
    # START: Could this just be replaced with 1) how many plates are used and 2) blank columns from GUI?
    if experimentType in [1,2,4,5,6,7]:
        # Make sure explicit zero timepoint does not cause issues
        timepointList = [0.0]+[x if x != 0 else 0.1 for x in kwargs['timepointlist']] # make a list of all timepoints in experiment + 0.0
        daysAgo = kwargs['daysAgo'] # if experiment has already started (how many days ago)
        # Decide how many conditions are on a given plate (if more than 1 plate, should be evenly divided between them)
        if numConditions < 96:
            numConditionsPerCulturePlate = numConditions
>>>>>>> 8978657151be80dca5b0418633cbd90d2ad17419
        else:
            cultureList.append(0)
    cultureArray = np.asarray(cultureList)
    
    cultureColumnArray = np.tile(cultureArray, (numTimepoints, 1)) # Make list of culture plate columns to aspirate/pipette + 0s for blank columns for all timepoints

    completeColumnCounter = 0
    collectionColumnArray = []
    wellPoseArray = []
    collectionPlateArray = []
    collectionLidArray = np.ones([numTimepoints,1], dtype=int)
    fridgeArray = np.zeros([numTimepoints, 3], dtype=int)
    waitTimeArray = np.zeros([numTimepoints,1], dtype=int)
    actualTimepoint = 0

    # CALCULATE MATRIX DATA FOR EACH TIMEPOINT
    for j, timepoint in enumerate(cultureColumnArray): # for each timepoint
        timepointPlateArray = np.zeros(timepoint.shape, dtype=int)
        timepointWellPoseArray = np.zeros(timepoint.shape, dtype=int)
        timepointCollectionPlateArray = np.zeros(timepoint.shape, dtype=int)
        for i, col in enumerate(timepoint): # for each culture column in the timepoint
            if col != 0: # If the column is to be pipetted
                completeColumnCounter += 1
                timepointPlateArray[i] = completeColumnCounter % culturePlateLength # Column to transfer to on collection plate
                if timepointPlateArray[i] == 0: # If last column of position (factor of culturePlateLength)
                    timepointPlateArray[i] = culturePlateLength
                timepointCollectionPlateArray[i] = (completeColumnCounter - 1) / (culturePlateLength*4) + 1 # 4 possible positions on each collection plate -> plates fill up as factor of culturePlateLength*4 columns
                timepointWellPoseArray[i] = ((completeColumnCounter - 1) - ((culturePlateLength*4) * (timepointCollectionPlateArray[i] - 1))) / 12 # 4 positions = 0,1,2,3. After removing cols for previous plates, divide by culturePlateLength to determine which position to use
        collectionColumnArray.append(timepointPlateArray)
        wellPoseArray.append(timepointWellPoseArray)
        uniqueCollectionPlates = []
        if transferToCollection:
            # Decide which collection plates are needed for timepoint (up to 2 plates can be used)
            uniqueCollectionPlates = np.unique(timepointCollectionPlateArray)
            uniqueCollectionPlates = uniqueCollectionPlates[uniqueCollectionPlates != 0]
            timepointCollectionPlateArray = [1 if x == uniqueCollectionPlates[0] else x if x == 0 else 2 for x in timepointCollectionPlateArray] # Convert collection plate needed for col to position of plate (1 or 2, or 0 if col is not pipetted)
            uniqueCollectionPlates = [fridgePlateArray[x - 1] for x in uniqueCollectionPlates] # Convert collection plate number to fridge position
        if refrigerateCulturePlate and not samePlatesAcrossExperiment: 
            uniqueCollectionPlates.append(fridgePlateArray[j + numCollectionPlates]) # The first fridge position saved for culture plates will be AFTER any collection plates
        elif refrigerateCulturePlate and samePlatesAcrossExperiment and not differentLinesPerPlate:
            fridgePositions = [fridgePlateArray[x + numCollectionPlates] for x in range(numCulturePlatesPerTimepoint)] # If fridge positions are needed but the same plates are used across the experiment, add a fridge position for each plate in the timepoint
            for x in fridgePositions:
                uniqueCollectionPlates.append(x)

        if len(uniqueCollectionPlates) >= 2: # If a timepoint needs to be split across 2 timepoints, 2 lids will need to be removed after being pulled from the fridge
            collectionLidArray[j] = 12
        while len(uniqueCollectionPlates) < 3:
            uniqueCollectionPlates.append(0) # If the fridge positions are not needed, append a 0 placeholder
        
        collectionPlateArray.append(timepointCollectionPlateArray)
        fridgeArray[j,:] = uniqueCollectionPlates
        # If this is the last plate for this timepoint, add wait time until next
        if (j % numCulturePlatesPerTimepoint == 0) or not differentLinesPerPlate:
            intervalTime = int(timepointIntervals[actualTimepoint]*60-timeoffset*(numCulturePlatesPerTimepoint-1))
            waitTimeArray[j,0] = intervalTime if intervalTime > 0 else 1
            actualTimepoint+=1
        else: # If there is another plate, add a placeholder wait time based on time it takes to run script per plate
            waitTimeArray[j,0] = timeoffset

    
    collectionColumnArray = np.array(collectionColumnArray)
    wellPoseArray = np.array(wellPoseArray)
    collectionPlateArray = np.array(collectionPlateArray)

    experimentArray = np.full((plateArray.shape[0],1), robotProtocol) # make list of robot script to use

    plateArray = np.reshape(plateArray,(plateArray.shape[0],1)) # reshape to be able to stack

    fullMatrix = np.hstack([plateArray,collectionLidArray,cultureColumnArray,collectionPlateArray,collectionColumnArray,wellPoseArray,waitTimeArray, experimentArray, fridgeArray, extraIncubatorArray]) # combine all pieces of matrix
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
    53-55: Collection plates to remove from fridge (if needed)
    56-57: Extra incubator positions (if needed)
    '''

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
<<<<<<< HEAD
                print(fullStartTime.strftime('Start Time: %Y-%m-%d %a %I:%M %p'),file=output,sep="\r\n")
            for i in range(0,len(baseTimeArrayHours)):
                currentTimePointTime = fullStartTime + dt.timedelta(hours=baseTimeArrayHours[i])
                robotTimepoint = i+1
                if differentLinesPerPlate:
                    robotTimepoint += +i*(numCulturePlatesPerTimepoint-1)
                print(currentTimePointTime.strftime('Timepoint '+str(i+1)+': %Y-%m-%d %a %I:%M %p' + ' ('+str(robotTimepoint)+ ')'),file=output,sep="\r\n")
=======
                numConditionsPerCulturePlate = 96 
        # Determine how many plates needed for number of conditions and how many columns are used on each plate
        if experimentType in [1,6]:
            numCulturePlatesForExperiment = math.ceil(numConditions / numConditionsPerCulturePlate)
            numCultureColumnsPerPlate = math.ceil(numConditions / culturePlateWidth / numCulturePlatesForExperiment)
        elif experimentType in [2,4,5,7]:
            numCulturePlatesForExperiment = numTimepoints
            numCultureColumnsPerPlate = culturePlateLength - len(blankColumns)
        # END
>>>>>>> 8978657151be80dca5b0418633cbd90d2ad17419

    timename = schedulePath+'schedule_'+experimentID+'.txt'
    createSchedule(timename)
    
    if singleExperiment:
        np.savetxt(finalOutputPath+'numTimepoints.txt',np.array([numTimepoints]),fmt='%d',delimiter=',')
        name='Full_Matrix_OnlySup.txt'
        np.savetxt(finalOutputPath+name,fullMatrix,fmt='%d',delimiter=',')
        timename = finalInputPath+'masterSchedule.txt'
        createSchedule(timename,master=True)
        timename = schedulePath+'masterSchedule.txt'
        createSchedule(timename,master=True)
    
    return numTimepoints

<<<<<<< HEAD
def combineExperiments(experimentIDs,experimentProtocols):
    integrateExperiments(experimentIDs,experimentProtocols)
=======
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
        if experimentType in [1]:
            numTimepoints *= numCulturePlatesForExperiment
            plateArray = np.tile(list(range(1+plateOffset,numCulturePlatesForExperiment+1+plateOffset)),numActualTimepoints)
        # For 1-plate-per-timepoint experiments, generate list of incubator positions (must be consecutive!)
        elif experimentType in [2,4,5,7]:
            plateArray = np.array(range(1+plateOffset,numTimepoints+1+plateOffset))
        elif experimentType in [6]:
            numTimepoints *= numCulturePlatesForExperiment
            plateArray = np.tile(list(range(1+plateOffset,numCulturePlatesForExperiment+1+plateOffset)),numTimepoints)

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
        actualTimepointArray = np.zeros([numTimepoints,1])

        timeoffset = 10 

        actualTimepoint = 0
        for timepoint in range(numTimepoints):
            cultureColumnArray[timepoint,:numConditionColumns] = cultureArray # Make list of culture plate columns to aspirate/pipette + 0s for blank columns
            supernatantColumnArray[timepoint,:numConditionColumns] = splitColumns[timepoint] # Make list of columns on collection plate to load + 0s for blank columns
            supernatantPlateArray[timepoint,:numConditionColumns] = plateArrays[timepoint] # Which position collection plate to load column into
            supernatantLidArray[timepoint,0] = int(''.join(list(map(str,list(map(int,list(np.unique(plateArrays[timepoint])))))))) # Which position collection plate to load column into
            wellPoseArray[timepoint,:numConditionColumns] = wellPoseArrays[timepoint] # Which 384-well position to load into
            if experimentType in [1,6]: # If this is the last plate for this timepoint, add wait time until next
                if timepoint % numCulturePlatesForExperiment == 0:
                    waitTimeArray[timepoint,0] = int(timepointIntervals[actualTimepoint]*60-timeoffset*(numCulturePlatesForExperiment-1))
                    actualTimepoint+=1
                    actualTimepointArray[timepoint,0] = actualTimepoint
                else: # If there is another plate, add a placeholder wait time based on time it takes to run script per plate
                    waitTimeArray[timepoint,0] = timeoffset
                    actualTimepointArray[timepoint,0] = actualTimepoint
            elif experimentType in [2,4,5,7]:
                waitTimeArray[timepoint,0] = int(timepointIntervals[actualTimepoint]*60)
                actualTimepointArray[timepoint,0] = actualTimepoint+1
                actualTimepoint+=1
        
        experimentArray = np.full((plateArray.shape[0],1), experimentType) # make list of robot script to use

        plateArray = np.reshape(plateArray,(plateArray.shape[0],1)) # reshape to be able to stack

        fullMatrix = np.hstack([plateArray,supernatantLidArray,cultureColumnArray,supernatantPlateArray,supernatantColumnArray,wellPoseArray,waitTimeArray, experimentArray, actualTimepointArray]) # combine all pieces of matrix
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
        53: Timepoint number for this protocol
        '''
        # Remove padding timepoints
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
>>>>>>> 8978657151be80dca5b0418633cbd90d2ad17419
