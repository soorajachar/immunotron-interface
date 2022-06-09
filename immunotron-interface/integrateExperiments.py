import enum
import json,pickle,math,sys,os,string
from datetime import datetime, timedelta
import datetime as dt
import numpy as np
import platform

schedulePath = 'schedules/' 
matrixPath = 'matrices/'
if platform.system() == 'Windows':
    finalPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
else:
    finalPath = ''

def integrateExperiments(experimentIDs, experimentTypes):
    print(experimentIDs)
    print(experimentTypes)
    timeFormat = '%Y-%m-%d %a %I:%M %p'
    #CHANGE THIS WHEN CHANGING PROTOCOL
    timepointDuration = {1:14, 2:45, 3:6, 4:45}
    
    #Sort experiment start times:
    startTimeDict = {}
    for scheduleIndex,experimentName in enumerate(experimentIDs):
        schedule = open(schedulePath+"schedule_"+experimentName+".txt","r")
        startTimeLine = schedule.readlines()[1]
        timeObject = datetime.strptime(startTimeLine.split('Start Time: ')[1][:-1], timeFormat)
        startTimeDict[experimentName] = timeObject
    experimentIDs = sorted(startTimeDict, key=startTimeDict.get)
    #print(experimentIDs)

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
            timeKey = str(scheduleIndex)+'-'+str(timepointIndex)
            timeDict[timeKey] = timeObject
            timeStartList.append(int(parsedTimeIndex[1:-1]))
        timeDiffDict[scheduleIndex] = timeStartList[1] - timeStartList[0]
        
    timeObjects = list(timeDict.values())
    sortedDateTimes = sorted(timeObjects)
    uniqueSortedDateTimes = sorted(set(sortedDateTimes))

    sortedTimeKeys = []
    for time in uniqueSortedDateTimes:
        timeKey = [k for k,v in timeDict.items() if v == time]
        timeKey.sort(key=lambda x: timepointDuration[experimentTypes[int(x.split('-')[0])]])
        sortedTimeKeys.append(timeKey[0])
        if len(timeKey) > 1:
            prevExperimentType = experimentTypes[int(timeKey[0].split('-')[0])]
            for i in range(1, len(timeKey)):
                timeDict[timeKey[i]] += timedelta(minutes=i*timepointDuration[prevExperimentType])
                sortedTimeKeys.append(timeKey[i])
                prevExperimentType = experimentTypes[int(timeKey[i].split('-')[0])]

    #timeKeys = list(timeDict.keys())
    #sortedTimeKeys = [timeKeys[timeObjects.index(x)] for x in sortedDateTimes]

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
    timename = 'masterSchedule.txt'
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
    firstExperimentType = experimentTypes[int(sortedTimeKeys[0].split('-')[0])]
    initialTimeDiff = timeDict[sortedTimeKeys[0]] - startTimes[0] 
    minutes = int(initialTimeDiff.total_seconds() / 60)
    timeDiffs = [minutes-timepointDuration[firstExperimentType]*(timeDiffDict[0]-1)]

    for row in range(1,len(sortedTimeKeys)):
        currentTimeKey = sortedTimeKeys[row]
        prevTimeKey = sortedTimeKeys[row-1]
        
        currentScheduleIndex = int(currentTimeKey.split('-')[0])
        currentTimepointIndex = int(currentTimeKey.split('-')[1])
        prevScheduleIndex = int(prevTimeKey.split('-')[0])
        prevTimepointIndex = int(prevTimeKey.split('-')[1])
        currentExperimentType = experimentTypes[currentScheduleIndex]
        prevExperimentType = experimentTypes[prevScheduleIndex]

        timeObject1 = timeDict[prevTimeKey]    
        timeObject2 = timeDict[currentTimeKey] 
        timeDiff = timeObject2 - timeObject1
        minutes = int(timeDiff.total_seconds() / 60)
        scheduleRowsPerTimepoint = timeDiffDict[prevScheduleIndex]
        timeDiffs+=[timepointDuration[prevExperimentType]]*(scheduleRowsPerTimepoint-1)
        minutes-=timepointDuration[prevExperimentType]*(scheduleRowsPerTimepoint-1)
        timeDiffs+=[minutes]

    #Add in subtimepoints for last timepoint, if needed
    scheduleRowsPerTimepoint = timeDiffDict[currentScheduleIndex]
    timeDiffs+=[timepointDuration[currentExperimentType]]*(scheduleRowsPerTimepoint-1)

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
    fullMatrix[:,-2] = timeDiffs
    
    name = 'Full_Matrix_OnlySup.txt'
    np.savetxt(finalPath+name,fullMatrix,fmt='%d',delimiter=',')
