import numpy as np
import math

culturePlateLength = 12
culturePlateWidth = 8

def calculateIncubatorPositions(incubator, experimentProtocol, numPlates, numTimepoints):
    '''
    Determines how many incubator positions are required for an experiment and which positions should be used based on the incubator's current status.
    NOTE: DOES NOT fill these incubator positions!! Must separately call loadPlates() to fill the incubator.
    Args:
        incubator: Current filled positions in incubator (dict)
        experimentProtocol: Protocol the experiment will run extracted from experimentProtocols (dict)
        numPlates: How many culture plates are taken out of the incubator at each timepoint (int)
        numTimepoints: Number of timepoints in the experiment (int)

    Returns:
        List of incubator positions to associate with this experiment (List of ints)
    '''
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

def calculateFridgePositions(fridge, experimentProtocol, numPlates, blankColumns, numTimepoints):
    '''
    Determines how many fridge positions are required for an experiment and which positions should be used based on the fridge's current status.
    NOTE: DOES NOT fill these fridge positions!! Must separately call loadPlates() to officially reserve these positions.
    Args:
        fridge: Current filled positions in fridge (dict)
        experimentProtocol: Protocol the experiment will run extracted from experimentProtocols (dict)
        numPlates: How many culture plates are taken out of the incubator at each timepoint (int)
        numTimepoints: Number of timepoints in the experiment (int)

    Returns:
        List of fridge positions to associate with this experiment (List of ints)
    '''
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

def loadPlates(container, experimentID, positions):
    '''
    Changes status of positions in the incubator or fridge to be filled with plates from an experiment
    Args:
        container: Current filled positions in incubator or fridge (dict)
        experimentID: Name of experiment to be loaded (str)
        positions: Which incubator positions to fill with this experiment (List of ints)

    Returns:
        True if plates loaded successfully, else returns False + prints which position is filled with another experiment
    '''
    for pos in positions:
        if container[pos] is not None:
            print('Container position {} is not available - please unload experiment {} first.'.format(pos, container[pos]))
            return False
        container[pos] = experimentID
    return True

def unloadPlates(container, experimentID):
    '''
    Changes status of positions in the incubator or fridge to be empty
    Args:
        container: Current filled positions in incubator or fridge (dict)
        experimentID: Name of experiment to be unloaded (str)

    Returns:
        Positions emptied (list of ints)
    '''
    positions = [k for k,v in container.items() if v == experimentID]
    for pos in positions:
        container[pos] = None
    return positions
