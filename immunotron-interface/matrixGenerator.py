
import json,pickle,math,sys,os,string
from datetime import datetime
import datetime as dt
import time
import numpy as np
from integrateExperiments import integrateExperiments
import platform

culturePlateLength = 12
culturePlateWidth = 8

def generateExperimentMatrix(singleExperiment=True,**kwargs):
    schedulePath = '/Users/wahlstenml/Documents/immunotron-interface/immunotron-interface/schedules/' 
    matrixPath = '/Users/wahlstenml/Documents/immunotron-interface/immunotron-interface/matrices/'
    if platform.system() == 'Windows':
        finalPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
    else:
        finalPath = ''
    experimentID = kwargs['experimentID'] # experiment name (str)
    protocol = kwargs['protocolParameters'] # protocol parameters (dict) TODO: Change in GUI to pass values from experimentProtocols[protocolName]
    plateArray = np.array(kwargs['incubatorPositions']) # incubator plate positions (list) TODO: Change in GUI to function that calculates positions
    fridgePlateArray = kwargs['fridgePositions'] # collection plate positions in fridge (list) TODO: Change in GUI to function that calculates positions
    #platePoseRestriction = kwargs['platePoseRestriction'] # cooling plate position (list) TODO: Remove in GUI
    numCulturePlatesPerTimepoint = kwargs['numPlates'] # how many conditions per plate (int) TODO: Change in GUI (originally numConditions)
    blankColumns = kwargs['blankColumns'] # blank columns on plate (list)
    numTimepoints = kwargs['numTimepoints'] # number of timepoints in experiment (int)
    startTime = kwargs['startTime'] # time of experiment start (str)
    daysAgo = kwargs['daysAgo'] # if experiment has already started (how many days ago)
    robotProtocol = protocol['protocolID'] # which robot protocol to use (int)
    samePlatesAcrossExperiment = protocol['samePlatesAcrossExperiment'] # if the same cultures are pulled out/replaced w/ incubator (bool)
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

    #Allows for experiments to take up incomplete 384-well plates
    numActualTimepoints = numTimepoints

    # For a same plate(s) throughout experiment, add a "timepoint" for each plate (ex. 2 lines for 2 plates) and make list of incubator positions
    # If not same plate(s), len(incubator positions) should already equal number of timepoints
    if samePlatesAcrossExperiment:
        numTimepoints *= numCulturePlatesPerTimepoint
        plateArray = np.tile(plateArray,numActualTimepoints)

    # Culture columns to aspirate (should be the same in 384 format)
    cultureList = []
    for conditionColumn in range(1,culturePlateLength+1):
        # If column is not blank, add it to list to aspirate/dispense (else add 0)
        if conditionColumn not in blankColumns:
            cultureList.append(conditionColumn)
        else:
            cultureList.append(0)
    cultureArray = np.asarray(cultureList)
    
    cultureColumnArray = np.tile(cultureArray, (numTimepoints, 1)) # Make list of culture plate columns to aspirate/pipette + 0s for blank columns for all timepoints

    completeColumnCounter = 0
    collectionColumnArray = []
    wellPoseArray = []
    collectionPlateArray = []
    collectionLidArray = np.ones([numTimepoints,1], dtype=int)
    fridgeArray = np.zeros([numTimepoints, 2], dtype=int)
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
        if refrigerateCulturePlate: 
            uniqueCollectionPlates.append(fridgePlateArray[j + numCollectionPlates]) # The first fridge position saved for culture plates will be AFTER any collection plates
        if len(uniqueCollectionPlates) == 0:
            uniqueCollectionPlates.append(0) # If the fridge is not used, append a 0 placeholder
        
        if len(uniqueCollectionPlates) == 2: # If a timepoint needs to be split across 2 timepoints, 2 lids will need to be removed after being pulled from the fridge
            collectionLidArray[j] = 12
        else: # If only one plate is needed for the timepoint, add a 0 placeholder for position 2
            uniqueCollectionPlates.append(0)
        collectionPlateArray.append(timepointCollectionPlateArray)
        fridgeArray[j,:] = uniqueCollectionPlates
        # If this is the last plate for this timepoint, add wait time until next
        if j % numCulturePlatesPerTimepoint == 0:
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

    fullMatrix = np.hstack([plateArray,collectionLidArray,cultureColumnArray,collectionPlateArray,collectionColumnArray,wellPoseArray,waitTimeArray, experimentArray, fridgeArray]) # combine all pieces of matrix
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
    53-54: Collection plates to remove from fridge and load onto positions 1 (and 2 if needed) of cooling plate
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
                print(fullStartTime.strftime('Start Time: %Y-%m-%d %a %I:%M %p'),file=output,sep="\r\n")
            for i in range(0,len(baseTimeArrayHours)):
                currentTimePointTime = fullStartTime + dt.timedelta(hours=baseTimeArrayHours[i])
                robotTimepoint = i+1
                robotTimepoint += +i*(numCulturePlatesPerTimepoint-1)
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

def combineExperiments(experimentIDs,experimentProtocols):
    integrateExperiments(experimentIDs,experimentProtocols)