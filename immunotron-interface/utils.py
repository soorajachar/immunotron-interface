import numpy as np
import math

culturePlateLength = 12
culturePlateWidth = 8

def calculateIncubatorPositions(incubatorPath, experimentProtocol, numPlates, numTimepoints):
    '''
    Determines how many incubator positions are required for an experiment and which positions should be used based on the incubator's current status.
    NOTE: Must separately load the plates via Evoware to fill the incubator.
    Args:
        fridgePath: Path to matrix containing currently used positions for experiments (string)
        experimentProtocol: Protocol the experiment will run extracted from experimentProtocols (dict)
        numPlates: How many culture plates are taken out of the incubator at each timepoint (int)
        numTimepoints: Number of timepoints in the experiment (int)

    Returns:
        List of incubator positions to associate with this experiment (List of ints)
    '''
    
    incubator = checkContainerStatus(incubatorPath)
    
    positionsNeeded = numPlates
    if not experimentProtocol['samePlatesAcrossExperiment']:
        positionsNeeded *= numTimepoints
    
    # To prioritize putting plates in the incubator in a continuous block of positions for an experiment, find all blocks of free positions
    continuousFreeBlocks = {}
    allFreePositions = []
    currentlyFree = 0
    currentStart = 1
    totalFree = 0
    for pos, status in incubator.items():
        if status is None:
            currentlyFree += 1
            totalFree += 1
            allFreePositions.append(pos)
        else:
            continuousFreeBlocks[currentStart] = currentlyFree
            currentStart = pos + 1
            currentlyFree = 0
    if status is None:
        continuousFreeBlocks[currentStart] = currentlyFree
    # Check to ensure enough spots are available to load the experiment in the incubator
    if totalFree < positionsNeeded:
        print('Not enough positions available for this experiment in the incubator - please unload another experiment first.')
        return False
    # If possible, assign a continuous block of positions for the experiment that fits the experiment as tightly as possible
    possibleContinuousBlocks = [k for k,v in continuousFreeBlocks.items() if v >= positionsNeeded]
    incubatorPositions = []
    if len(possibleContinuousBlocks) > 0:
        possibleContinuousBlocks.sort(key=lambda x:continuousFreeBlocks[x])
        incubatorPositions = list(range(possibleContinuousBlocks[0], possibleContinuousBlocks[0] + positionsNeeded))
        assert(len(incubatorPositions) == positionsNeeded)
    # If there is not a large enough continuous block, assign the first positions available
    else:
        for i in range(positionsNeeded):
            incubatorPositions.append(allFreePositions[i])
        assert(len(incubatorPositions) == positionsNeeded)
    return incubatorPositions

def calculateFridgePositions(fridgePath, experimentProtocol, numPlates, blankColumns, numTimepoints):
    '''
    Determines how many fridge positions are required for an experiment and which positions should be used based on the fridge's current status.
    NOTE: Must separately load the plates via Evoware to fill the incubator.
    Args:
        fridgePath: Path to matrix containing currently used positions for experiments (string)
        experimentProtocol: Protocol the experiment will run extracted from experimentProtocols (dict)
        numPlates: How many culture plates are taken out of the incubator at each timepoint (int)
        blankColumns: Blank columns on plate (list)
        numTimepoints: Number of timepoints in the experiment (int)

    Returns:
        List of fridge positions to associate with this experiment (List of ints)
    '''
    
    fridge = checkContainerStatus(fridgePath)
    
    positionsNeeded = 0
    if experimentProtocol['transferToCollection']:
        numCultureColumnsPerPlate = culturePlateLength - len(blankColumns)
        numCultureColumnsPerTimepoint = numPlates * numCultureColumnsPerPlate
        numCollectionPlates = math.ceil((numTimepoints*numCultureColumnsPerTimepoint)/(culturePlateLength*4)) # 4 possible positions on 384-well plate per column on 96-well plate
        positionsNeeded += numCollectionPlates
    if experimentProtocol['refrigerateCulturePlate']:
        positionsNeeded += numTimepoints*numPlates
    
    # To prioritize putting plates in the incubator in a continuous block of positions for an experiment, find all blocks of free positions
    continuousFreeBlocks = {}
    allFreePositions = []
    currentlyFree = 0
    currentStart = 1
    totalFree = 0
    for pos, status in fridge.items():
        if status is None:
            currentlyFree += 1
            totalFree += 1
            allFreePositions.append(pos)
        else:
            continuousFreeBlocks[currentStart] = currentlyFree
            currentStart = pos + 1
            currentlyFree = 0
    if status is None:
        continuousFreeBlocks[currentStart] = currentlyFree
    # Check to ensure enough spots are available to load the experiment in the fridge
    if totalFree < positionsNeeded:
        print('Not enough positions available for this experiment in the fridge - please unload another experiment first.')
        return False
    # If possible, assign a continuous block of positions for the experiment that fits the experiment as tightly as possible
    possibleContinuousBlocks = [k for k,v in continuousFreeBlocks.items() if v >= positionsNeeded]
    fridgePositions = []
    if len(possibleContinuousBlocks) > 0:
        possibleContinuousBlocks.sort(key=lambda x:continuousFreeBlocks[x])
        fridgePositions = list(range(possibleContinuousBlocks[0], possibleContinuousBlocks[0] + positionsNeeded))
        assert(len(fridgePositions) == positionsNeeded)
    # If there is not a large enough continuous block, assign the first positions available
    else:
        for i in range(positionsNeeded):
            fridgePositions.append(allFreePositions[i])
        assert(len(fridgePositions) == positionsNeeded)
    return fridgePositions

def checkContainerStatus(path):
    '''
    Determines how many positions are in the container (incubator or fridge) and creates a dictionary to determine which positions are filled.
    Args:
        path: Path to matrix containing currently used positions for experiments (string)

    Returns:
        Dictionary of all positions and whether they are full (Dict)
    '''
    status = np.loadtxt(path, delimiter=',')
    positions = list(range(1,status.shape[1]+1))
    statuses = [None]*len(positions)
    container = dict(zip(positions, statuses))
    for pos in np.unique(status):
        if pos != 0:
            container[pos] = 'Occupied'
    return container

def editContainerStatus(path, experimentSlot, positions):
    '''
    Writes to incubator or fridge status file at the specified path when positions are assigned to an experiment
    Args:
        path: Path to matrix containing currently used positions for experiments (string)
        experimentSlot: Which experiment slot on the GUI is being edited (1-indexed) (int)
        positions: List of positions to use for this experiment (List of ints)

    Returns:
        None
    '''
    
    container = np.loadtxt(path, delimiter=',')
    numPositions = len(positions)
    container[experimentSlot-1, 0:numPositions] = positions
    container[experimentSlot-1, numPositions:] = 0
    np.savetxt(path, container, delimiter=',', fmt='%i')