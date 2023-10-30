import enum
import json,pickle,math,sys,os,string
from datetime import datetime, timedelta
import datetime as dt
import numpy as np
import platform

def integrateExperiments(experimentIDs, experimentProtocols):
    schedulePath = 'schedules/' 
    matrixPath = 'matrices/'
    finalInputPath = 'misc/'
    if platform.system() == 'Windows':
        finalOutputPath = 'C:/ProgramData/Tecan/EVOware/database/variables/'
    else:
        finalOutputPath = 'variables/'

    timeFormat = '%Y-%m-%d %a %I:%M %p'
<<<<<<< HEAD
    #CHANGE THIS WHEN CHANGING PROTOCOL 
=======
    #CHANGE THIS WHEN CHANGING PROTOCOL
    timepointDuration = {1:14, 2:75, 3:60, 4:90, 5:85, 6:75, 7:20}    
>>>>>>> 8978657151be80dca5b0418633cbd90d2ad17419
    #Sort experiment start times:
    startTimeDict = {}
    for scheduleIndex,experimentName in enumerate(experimentIDs):
        schedule = open(schedulePath+"schedule_"+experimentName+".txt","r")
        startTimeLine = schedule.readlines()[1]
        timeObject = datetime.strptime(startTimeLine.split('Start Time: ')[1][:-1], timeFormat)
        startTimeDict[experimentName] = timeObject
    experimentIDs = sorted(startTimeDict, key=startTimeDict.get)

    timeDict = {}
    timeDiffDict = {}
    for scheduleIndex,experimentName in enumerate(experimentIDs):
        schedule = open(schedulePath+"schedule_"+experimentName+".txt","r")
        scheduleLines = schedule.readlines()[2:]
        rawTimeList = [x.split(': ')[1] for x in scheduleLines]
        timeStartList = [] 
        for timepointIndex,time in enumerate(rawTimeList):
            Mindex = time.rfind('M')
            parsedTime = time[:Mindex+1]
            parsedTimeIndex = time[Mindex+2:-1]
            if '>' in time:
                parsedTime = parsedTime[parsedTime.rfind('>')+1:]
            timeObject = datetime.strptime(parsedTime, timeFormat)
            timeKey = str(scheduleIndex)+'-'+str(timepointIndex) # EX: 0-5 (1st experiment, 6th timepoint)
            timeDict[timeKey] = timeObject
            timeStartList.append(int(parsedTimeIndex[1:-1]))
        timeDiffDict[scheduleIndex] = timeStartList[1] - timeStartList[0]
        
    timeObjects = list(timeDict.values())
    sortedDateTimes = sorted(timeObjects)
    uniqueSortedDateTimes = sorted(set(sortedDateTimes))

    sortedTimeKeys = []
    for time in uniqueSortedDateTimes:
        timeKey = [k for k,v in timeDict.items() if v == time]
        timeKey.sort(key=lambda x: experimentProtocols[int(x.split('-')[0])]['protocolLength'])
        sortedTimeKeys.append(timeKey[0])
        if len(timeKey) > 1:
            prevExperimentType = experimentProtocols[int(timeKey[0].split('-')[0])]
            for i in range(1, len(timeKey)):
                timeDict[timeKey[i]] += timedelta(minutes=i*prevExperimentType['protocolLength'])
                sortedTimeKeys.append(timeKey[i])
                prevExperimentType = experimentProtocols[int(timeKey[i].split('-')[0])]

    timename = schedulePath+'masterSchedule.txt'
    startTimes = []
    with open(timename,'w') as output:
        print('USE TIMEPOINTS IN PARENTHESES TO SET TIMEPOINT ON ROBOT',file=output,sep="\r\n")
        print(file=output,sep="\r\n")
        for scheduleIndex,experimentName in enumerate(experimentIDs):
            schedule = open(schedulePath+"schedule_"+experimentName+".txt","r")
            startTimeLine = schedule.readlines()[1]
            startTimes.append(datetime.strptime(startTimeLine.split('Start Time: ')[1][:-1], timeFormat))
            experimentID = experimentIDs[scheduleIndex]
            print('Experiment '+experimentID+' '+startTimeLine[:-1],file=output)
        print(file=output,sep="\r\n")
        timepointLine = 1
        for timeKey in sortedTimeKeys:
            scheduleIndex = int(timeKey.split('-')[0])
            timepointIndex = int(timeKey.split('-')[1])
            currentTimeObject = timeDict[timeKey]
            timepointLineString = '('+str(timepointLine)+')'
            timepointLine+=timeDiffDict[scheduleIndex]
            print(currentTimeObject.strftime('Timepoint '+str(timepointIndex+1)+'-'+experimentIDs[scheduleIndex]+': %Y-%m-%d %a %I:%M %p'+' '+timepointLineString),file=output,sep="\r\n")
    timename = finalInputPath+'masterSchedule.txt'
    startTimes = []
    with open(timename,'w') as output:
        print('USE TIMEPOINTS IN PARENTHESES TO SET TIMEPOINT ON ROBOT',file=output,sep="\r\n")
        print(file=output,sep="\r\n")
        for scheduleIndex,experimentName in enumerate(experimentIDs):
            schedule = open(schedulePath+"schedule_"+experimentName+".txt","r")
            startTimeLine = schedule.readlines()[1]
            startTimes.append(datetime.strptime(startTimeLine.split('Start Time: ')[1][:-1], timeFormat))
            experimentID = experimentIDs[scheduleIndex]
            print('Experiment '+experimentID+' '+startTimeLine[:-1],file=output)
        print(file=output,sep="\r\n")
        timepointLine = 1
        for timeKey in sortedTimeKeys:
            scheduleIndex = int(timeKey.split('-')[0])
            timepointIndex = int(timeKey.split('-')[1])
            currentTimeObject = timeDict[timeKey]
            timepointLineString = '('+str(timepointLine)+')'
            timepointLine+=timeDiffDict[scheduleIndex]
            print(currentTimeObject.strftime('Timepoint '+str(timepointIndex+1)+'-'+experimentIDs[scheduleIndex]+': %Y-%m-%d %a %I:%M %p'+' '+timepointLineString),file=output,sep="\r\n")

    #First time diff really doesn't matter
    firstTimeKey = sortedTimeKeys[0]
    firstExperimentType = experimentProtocols[int(sortedTimeKeys[0].split('-')[0])]
    initialTimeDiff = timeDict[sortedTimeKeys[0]] - startTimes[0] 
    minutes = int(initialTimeDiff.total_seconds() / 60)
    timeDiffs = [minutes-firstExperimentType['protocolLength']*(timeDiffDict[0]-1)]

    for row in range(1,len(sortedTimeKeys)):
        currentTimeKey = sortedTimeKeys[row]
        prevTimeKey = sortedTimeKeys[row-1]
        
        currentScheduleIndex = int(currentTimeKey.split('-')[0])
        currentTimepointIndex = int(currentTimeKey.split('-')[1])
        prevScheduleIndex = int(prevTimeKey.split('-')[0])
        prevTimepointIndex = int(prevTimeKey.split('-')[1])
        currentExperimentType = experimentProtocols[currentScheduleIndex]
        prevExperimentType = experimentProtocols[prevScheduleIndex]

        timeObject1 = timeDict[prevTimeKey]    
        timeObject2 = timeDict[currentTimeKey] 
        timeDiff = timeObject2 - timeObject1
        minutes = int(timeDiff.total_seconds() / 60)
        scheduleRowsPerTimepoint = timeDiffDict[prevScheduleIndex]
        timeDiffs+=[prevExperimentType['protocolLength']]*(scheduleRowsPerTimepoint-1)
        minutes-=prevExperimentType['protocolLength']*(scheduleRowsPerTimepoint-1)
        if minutes < prevExperimentType['protocolLength']*(scheduleRowsPerTimepoint-1):
            minutes = prevExperimentType['protocolLength']*(scheduleRowsPerTimepoint-1)
        timeDiffs+=[minutes]

    #Add in subtimepoints for last timepoint, if needed
    scheduleRowsPerTimepoint = timeDiffDict[currentScheduleIndex]
    timeDiffs+=[prevExperimentType['protocolLength']]*(scheduleRowsPerTimepoint-1)

    matrixAssemblyList = []
    for timeKey in sortedTimeKeys:
        scheduleIndex = int(timeKey.split('-')[0])
        experimentName = experimentIDs[scheduleIndex] 
        timepointIndex = int(timeKey.split('-')[1])
        scheduleRowsPerTimepoint = timeDiffDict[scheduleIndex]
        experimentMatrix = np.loadtxt(matrixPath+'matrix_'+experimentName+'.txt',delimiter=',')
        for plate in range(scheduleRowsPerTimepoint):
            lineToAdd = experimentMatrix[timepointIndex*scheduleRowsPerTimepoint+plate,:]
            matrixAssemblyList.append(lineToAdd)

    fullMatrix = np.vstack(matrixAssemblyList)
    fullMatrix[:,50] = timeDiffs
    
    name = 'Full_Matrix_OnlySup.txt'
<<<<<<< HEAD
    np.savetxt(finalOutputPath+name,fullMatrix,fmt='%d',delimiter=',')
    np.savetxt(finalOutputPath+'numTimepoints.txt',np.array([fullMatrix.shape[0]]),fmt='%d',delimiter=',')
=======
    np.savetxt(finalPath+name,fullMatrix,fmt='%d',delimiter=',')
    name = 'numTimepoints.txt'
    np.savetxt(finalPath+name,np.array([fullMatrix.shape[0]]),fmt='%d',delimiter=',')
>>>>>>> 8978657151be80dca5b0418633cbd90d2ad17419
