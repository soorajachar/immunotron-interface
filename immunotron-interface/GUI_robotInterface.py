#! /usr/bin/env python3
import pickle,os,subprocess,math
from datetime import datetime
import datetime as dt
import tkinter as tk
import pandas as pd
import numpy as np
from functools import partial
from tkinter import messagebox
from matrixGenerator import generateExperimentMatrix,combineExperiments
from utils import calculateIncubatorPositions,calculateFridgePositions,checkContainerStatus,editContainerStatus
import tkinter.ttk as ttk
import platform
from string import ascii_uppercase

schedulePath = 'schedules/' 
matrixPath = 'matrices/'
finalInputPath = 'misc/'
if platform.system() == 'Windows':
    finalOutputPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
else:
    finalOutputPath = 'variables/'

incubatorPath = finalOutputPath+'incubatorStatus.txt'
fridgePath = finalOutputPath+'fridgeStatus.txt'

#Root class; handles frame switching in gui
class MainApp(tk.Tk):
    def __init__(self):
        self.root = tk.Tk.__init__(self)

        self._frame = None
        #TEMPORARY; REMOVE WHEN UPLOADED TO PYPI
        self.homedirectory = os.getcwd()
        if self.homedirectory[-1] != '/':
            self.homedirectory+='/'
        #print('current location: '+self.homedirectory)
        self.switch_frame(ExperimentHomePage)

    def switch_frame(self, frame_class,*args):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self,*args)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack()

#Top level actions for experiments
class ExperimentHomePage(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self, master)
        mainWindow = tk.Frame(self)
        mainWindow.pack(side=tk.TOP,padx=10)
        
        EMPTYTEXT = '-'
        NUMEXP = 8
        allLabels = ['Experiment:','Type (Author):','Name:','Incubator racks:','Fridge racks:','# plates:','Blank columns:','# timepoints:','Start Time:','Timepoints:','End Time:','Incubator Loaded?','Fridge Loaded?','Added to matrix:']
        
        #Load experiment parameters (experiments currently running on robot)
        if 'experimentParameters.pkl' not in os.listdir(finalInputPath):
            self.allExperimentParameters = {k:{} for k in range(NUMEXP)}
            with open(finalInputPath+'experimentParameters.pkl','wb') as f:
                pickle.dump(self.allExperimentParameters,f)
        else:
            self.allExperimentParameters = pickle.load(open(finalInputPath+'experimentParameters.pkl','rb'))
        #Load all saved experiment protocols
        if 'experimentProtocols.pkl' not in os.listdir(finalInputPath):
            self.experimentProtocols = {}
            with open(finalInputPath+'experimentProtocols.pkl','wb') as f:
                pickle.dump(self.experimentProtocols,f)
        else:
            self.experimentProtocols = pickle.load(open(finalInputPath+'experimentProtocols.pkl','rb'))
            allProtocols = list(self.experimentProtocols.keys())
            allIDs = [self.experimentProtocols[x]['protocolID'] for x in allProtocols]
            IDdict = {x:y for x,y in zip(allIDs,allProtocols)}

        expFrame = tk.Frame(self,borderwidth=0.8,relief=tk.SOLID)
        expFrame.pack()
        labelFrame = tk.Frame(expFrame)
        labelFrame.grid(row=0,column=0)
        
        def updateExperimentLabels():
            maxPlateChangeLen = 0
            validExps = []
            for exp in range(NUMEXP):
                if len(self.allExperimentParameters[exp]) != 0:
                    validExps.append(exp)
                    for i,expParameter in enumerate(['protocolParameters','experimentID','incubatorPositions','fridgePositions','numPlates','blankColumns','numTimepoints','startTime','timepointlist','addedToMatrix','incubatorStatus','fridgeStatus','addedToMatrix']):
                        if expParameter == 'protocolParameters':
                            rawValue = IDdict[self.allExperimentParameters[exp][expParameter]['protocolID']]
                        elif expParameter in ['incubatorStatus','fridgeStatus']:
                            rawValue = ''
                        else:
                            rawValue = self.allExperimentParameters[exp][expParameter]
                        if isinstance(rawValue,list):
                            if len(rawValue) == 0:
                                parsedValue = EMPTYTEXT
                            else:
                                if isinstance(rawValue[0],float):
                                    values = [int(x) if x.is_integer() else x for x in rawValue]
                                    values = list(map(str,values))
                                else:
                                    values = list(map(str,rawValue))
                                parsedValue = ', '.join(values)
                        else:
                            if str(rawValue) == '':
                                parsedValue = EMPTYTEXT
                            else:
                                if expParameter == 'startTime':
                                    parsedValue = self.allExperimentParameters[exp]['fullStart']
                                else:
                                    parsedValue = str(rawValue)
                        self.allExpInfoLabels[exp][i].configure(text=parsedValue,fg='black')
                    
                    endTime = datetime.strptime(self.allExperimentParameters[exp]['fullStart'],'%Y-%m-%d %a %I:%M %p')+dt.timedelta(hours=self.allExperimentParameters[exp]['timepointlist'][-1])
                    self.allExpInfoLabels[exp][-4].configure(text=endTime.strftime('%Y-%m-%d %a %I:%M %p'))
                    numPassedTimepoints = 0
                    start = datetime.strptime(self.allExperimentParameters[exp]['fullStart'],'%Y-%m-%d %a %I:%M %p')
                    for timepoint in self.allExperimentParameters[exp]['timepointlist']:
                        if datetime.now() > start+dt.timedelta(hours=timepoint):
                            numPassedTimepoints+=1
                    numTimepoints = self.allExperimentParameters[exp]['numTimepoints']
                    percentage = int(100*numPassedTimepoints/numTimepoints)
                    allProgressBars[exp]['value'] = percentage 
                    if percentage == 100:
                        progressString = 'Complete'
                    else:
                        progressString = str(percentage) + '% ('+str(numPassedTimepoints)+'/'+str(numTimepoints)+')'
                    style.configure('text.Horizontal.TProgressbar'+str(exp+1), text=progressString)
                    plateSize = 384
                    #Update added to matrix warnings check if all labels are either yes or - in both removeExp and generate matrix
                    if self.allExperimentParameters[exp]['addedToMatrix']:
                        self.allExpInfoLabels[exp][-1].configure(text='Yes',fg='green')
                    else:
                        self.allExpInfoLabels[exp][-1].configure(text='No',fg='red')                    
                    #Update fridge and incubator status to reflect whether they are loaded or unloaded
                    incubatorLoadUnload = np.loadtxt(finalOutputPath+'incubatorLoadUnload.txt',delimiter=',')[exp]
                    fridgeLoadUnload = np.loadtxt(finalOutputPath+'fridgeLoadUnload.txt',delimiter=',')[exp]
                    if incubatorLoadUnload == 1:
                        self.allExpInfoLabels[exp][-3].configure(text='Yes',fg='green')
                    else:
                        self.allExpInfoLabels[exp][-3].configure(text='No',fg='red')
                    if fridgeLoadUnload == 1:
                        self.allExpInfoLabels[exp][-2].configure(text='Yes',fg='green')
                    else:
                        self.allExpInfoLabels[exp][-2].configure(text='No',fg='red')
                else:
                    for k in range(len(allLabels)-1):
                        self.allExpInfoLabels[exp][k].configure(text=EMPTYTEXT,fg='black')
            
            #Update diti warning label
            if "masterSchedule.txt" in os.listdir(finalInputPath):
                with open(finalInputPath+"masterSchedule.txt", "r") as schedule:
                    lines = schedule.readlines()
                startLine = 0
                numExperiments = 0
                for i,line in enumerate(lines):
                    if 'Experiment ' in line:
                        numExperiments+=1
                singleExperiment = numExperiments == 1

                currentRow = 0
                currentLine = 0
                allRows = []
                finalTimepoint = ''
                totalnumTimepoints = 0
                nextTimepointExists = False
                for i,line in enumerate(lines):
                    if 'Timepoint ' in line:
                        totalnumTimepoints+=1
                        usefulPortion = line.split(': ')[1]
                        time,row = usefulPortion.split(' (')
                        timeObject = datetime.strptime(time,'%Y-%m-%d %a %I:%M %p')
                        row = int(row[:-2])
                        allRows.append(row)
                        #If current time is ahead of timepoint
                        if datetime.now() > timeObject:
                            currentRow = row
                            currentLine = i
                        else:
                            nextTimepointExists = True
                nextTimepointLine = 0
                if nextTimepointExists:
                    for i,line in enumerate(lines):
                        if 'Timepoint ' in line:
                            totalnumTimepoints+=1
                            usefulPortion = line.split(': ')[1]
                            time,row = usefulPortion.split(' (')
                            timeObject = datetime.strptime(time,'%Y-%m-%d %a %I:%M %p')
                            row = int(row[:-2])
                            allRows.append(row)
                            #If current time is behind timepoint
                            if datetime.now() <= timeObject:
                                nextTimepointLine = i
                                break
                #Update next timepoint window
                if len(validExps) > 0:
                    if nextTimepointExists:
                        nextUsefulPortion = lines[nextTimepointLine].split(': ')[1]
                        nextTime,nextRow = nextUsefulPortion.split(' (')
                        nextRow = nextRow[:-2]
                        nextTimeObject = datetime.strptime(nextTime,'%Y-%m-%d %a %I:%M %p')
                        if singleExperiment:
                            expID = self.allExperimentParameters[validExps[0]]['experimentID']
                            tp = lines[nextTimepointLine].split(': ')[0].split(' ')[1]
                        else:
                            expID = lines[nextTimepointLine].split(': ')[0].split('-')[1]
                            tp = lines[nextTimepointLine].split(': ')[0].split('-')[0].split(' ')[1]
                        timeDifference = nextTimeObject - datetime.now()
                        minutesRemaining = timeDifference.seconds//60
                        nextTimepointString = 'Timepoint '+str(tp)+' of experiment '+expID+' is next: row number is ('+str(nextRow)+'), wait time is (' +str(minutesRemaining)+') minutes'
                        nextTimepointLabel.configure(text=nextTimepointString)
                    else:
                        nextTimepointLabel.configure(text='')
            #Enable/disable generate matrix and quit buttons
            allIncubatorStrings = [self.allExpInfoLabels[exp][-3]['text'] for exp in range(NUMEXP)]
            allFridgeStrings = [self.allExpInfoLabels[exp][-2]['text'] for exp in range(NUMEXP)]
            allAddedStrings = [self.allExpInfoLabels[exp][-1]['text'] for exp in range(NUMEXP)]
            fullCount = 0
            emptyCount = 0
            noCount = 0
            incubatorCount = 0
            fridgeCount = 0
            for addedString,incubatorString,fridgeString in zip(allAddedStrings,allIncubatorStrings,allFridgeStrings):
                if addedString == EMPTYTEXT:
                    emptyCount+=1
                else:
                    fullCount+=1
                    if addedString == 'No':
                        noCount+=1
                    if incubatorString == 'Yes':
                        incubatorCount+=1
                    if fridgeString == 'Yes':
                        fridgeCount+=1
            #If there are no added experiments
            if emptyCount == NUMEXP:
                generateButton.config(state=tk.DISABLED)
                nextTimepointLabel.configure(text='')
            else:
                #Only enable matrix generation if all incubator and fridge positions are loaded 
                if fullCount == incubatorCount and fullCount == fridgeCount:
                    generateButton.config(state=tk.NORMAL)
                else:
                    generateButton.config(state=tk.DISABLED)
                if noCount > 0:
                    quitButton.config(state=tk.DISABLED)
                else:
                    quitButton.config(state=tk.NORMAL)
            #Only enable experiment removal button if incubator and fridge are unloaded:
            for exp in range(NUMEXP):
                if self.allExpInfoLabels[exp][-3]['text'] != EMPTYTEXT:
                    if self.allExpInfoLabels[exp][-3]['text'] == 'No' and self.allExpInfoLabels[exp][-3]['text'] == 'No':
                        allRemoveButtons[exp].config(state=tk.NORMAL)
                    else:
                        allRemoveButtons[exp].config(state=tk.DISABLED)
            #ttk.Separator(expFrame, orient='horizontal').place(relx=0,rely=0+separatorOffset*(len(allLabels)-1+maxPlateChangeLen),relwidth=1)
            self.after(5000, updateExperimentLabels)

        def editExp(expNum):
            master.switch_frame(ExperimentInfoPage,expNum)

        def removeExp(expNum):
            if messagebox.askokcancel(title='Warning',message='Are you sure you want to delete Experiment '+str(expNum+1)+'?'):
                if 'matrix_'+self.allExperimentParameters[expNum]['experimentID']+'.txt' in os.listdir(matrixPath):
                    os.remove(matrixPath+'matrix_'+self.allExperimentParameters[expNum]['experimentID']+'.txt')
                self.allExperimentParameters[expNum] = {}
                with open(finalInputPath+'experimentParameters.pkl','wb') as f:
                    pickle.dump(self.allExperimentParameters,f)
                updateExperimentLabels()
                allProgressBars[expNum]['value'] = 0
                editContainerStatus(incubatorPath, expNum+1, [0]*22)
                editContainerStatus(fridgePath, expNum+1, [0]*44)
                style.configure('text.Horizontal.TProgressbar'+str(expNum+1), text='0 %')
        
        self.headerLabels = []
        for i,label in enumerate(allLabels):
            if i == 0:
                headerLabel = tk.Label(labelFrame,text=label,font='-weight bold')
            else:
                headerLabel = tk.Label(labelFrame,text=label)
            headerLabel.grid(row=i,column=0,sticky=tk.W)
            self.headerLabels.append(headerLabel)
        tk.Label(labelFrame,text='Progress:').grid(row=len(allLabels),column=0,pady=(0,10),sticky=tk.W)
        tk.Label(labelFrame,text='').grid(row=len(allLabels)+1,column=0)
        self.allExpInfoLabels = []
        allEditButtons,allRemoveButtons,allProgressBars = [],[],[]
        style = ttk.Style()
        pbarStyleArguments = [('Horizontal.Progressbar.trough',{'children': [('Horizontal.Progressbar.pbar',{'side': 'left', 'sticky': 'ns'})],'sticky': 'nswe'}),('Horizontal.Progressbar.label', {'sticky': ''})]
        for expNum in range(NUMEXP):
            specificExpFrame = tk.Frame(expFrame, borderwidth = 1,relief=tk.RIDGE)
            specificExpFrame.grid(row=0,column=expNum+1,sticky=tk.EW)
            tk.Label(specificExpFrame,text=ascii_uppercase[expNum],font='-weight bold').grid(row=0,column=expNum*2,columnspan=2)
            specificExpInfoLabels = []
            separatorOffset = 0.06
            for j in range(len(allLabels)-1):
                expInfoLabel = tk.Label(specificExpFrame,text=EMPTYTEXT)
                expInfoLabel.grid(row=1+j,column=expNum*2,columnspan=2)
                specificExpInfoLabels.append(expInfoLabel)
            self.allExpInfoLabels.append(specificExpInfoLabels)
            style.layout('text.Horizontal.TProgressbar'+str(expNum+1), pbarStyleArguments)
            style.configure('text.Horizontal.TProgressbar'+str(expNum+1), text='0 %')
            pb = ttk.Progressbar(specificExpFrame, style='text.Horizontal.TProgressbar'+str(expNum+1), mode='determinate',length=150)
            pb.grid(row=len(allLabels),column=expNum*2,columnspan=2,pady=(0,10))
            editButton = ttk.Button(specificExpFrame,text='Edit',command=partial(editExp,expNum),width=10)
            editButton.grid(row=len(allLabels)+1,column=expNum*2,sticky=tk.E)
            removeButton = ttk.Button(specificExpFrame,text='Remove',command=partial(removeExp,expNum),width=10)
            removeButton.grid(row=len(allLabels)+1,column=expNum*2+1,sticky=tk.W)
            allEditButtons.append(editButton)
            allRemoveButtons.append(removeButton)
            allProgressBars.append(pb)

        def generateFullMatrix():
            experimentIDsToIntegrate,experimentProtocolsToIntegrate,experimentsToIntegrate = [],[],[]
            for i,l in enumerate(self.allExpInfoLabels):
                expName = l[1]['text']
                if expName != EMPTYTEXT:
                    protocolParameters = self.allExperimentParameters[i]['protocolParameters']
                    experimentIDsToIntegrate.append(expName)
                    experimentsToIntegrate.append(i)
                    experimentProtocolsToIntegrate.append(protocolParameters)
            if len(experimentsToIntegrate) == 0:
                messagebox.showwarning(title='Error',message='At least one experiment must be created before a matrix can be generated. Please try again.')
            else:
                if len(experimentsToIntegrate) == 1:
                    _ = generateExperimentMatrix(singleExperiment=True,**self.allExperimentParameters[experimentsToIntegrate[0]])
                else:
                    for exp in experimentsToIntegrate:
                        startTime = self.allExperimentParameters[exp]['fullStart']
                        trueStartTime = datetime.strptime(startTime,'%Y-%m-%d %a %I:%M %p')
                        nowTime = datetime.now()
                        difference = datetime(nowTime.year,nowTime.month,nowTime.day) - datetime(trueStartTime.year,trueStartTime.month,trueStartTime.day)
                        trueDaysAgo = max(0,difference.days)
                        self.allExperimentParameters[exp]['daysAgo'] = trueDaysAgo
                        
                        tempNumRows = generateExperimentMatrix(singleExperiment=False,**self.allExperimentParameters[exp])
                    combineExperiments(experimentIDsToIntegrate,experimentProtocolsToIntegrate)
                messagebox.showinfo(title='Success',message='Experiment matrix generated!')
                for exp in experimentsToIntegrate:
                    self.allExperimentParameters[exp]['addedToMatrix'] = True
                with open(finalInputPath+'experimentParameters.pkl','wb') as f:
                    pickle.dump(self.allExperimentParameters,f)
            updateExperimentLabels()

        nextTimepointWindow = tk.Frame(self)
        nextTimepointWindow.pack(side=tk.TOP,padx=10,pady=(10,0))
        nextTimepointLabel = tk.Label(nextTimepointWindow,text='')
        nextTimepointLabel.pack()
        
        ditiWarningWindow = tk.Frame(self)
        ditiWarningWindow.pack(side=tk.TOP,padx=10,pady=(10,10))
        ditiWarningLabel = tk.Label(ditiWarningWindow,text='')
        ditiWarningLabel.pack()

        buttonWindow = tk.Frame(self)
        buttonWindow.pack(side=tk.TOP,padx=10,pady=(10,10))
        style.configure("Bold.TButton", font = ('Sans-Serif','12','bold'))
        generateButton = ttk.Button(buttonWindow, text="Generate Matrix", style = "Bold.TButton",command=lambda: generateFullMatrix())
        generateButton.pack(side=tk.LEFT)
        quitButton = ttk.Button(buttonWindow, text="Quit",command=lambda: quit())
        quitButton.pack(side=tk.LEFT)

        updateExperimentLabels()

class ExperimentInfoPage(tk.Frame):
    def __init__(self,master,expNum):
        tk.Frame.__init__(self, master)
        mainWindow = tk.Frame(self)
        mainWindow.pack(side=tk.TOP,padx=10)
        
        allExpParameters = pickle.load(open(finalInputPath+'experimentParameters.pkl','rb'))
        experimentProtocols = pickle.load(open(finalInputPath+'experimentProtocols.pkl','rb'))
        #Set defaults to saved values if entry already exists; does not quite work for multiplates
        tempExpParameters = allExpParameters[expNum]
        expParameterList = ['experimentProtocol','experimentID','numPlates','blankColumns','numTimepoints','startTime','timepointList','daysAgo']
        defaultValueDict = {k:v for k,v in zip(expParameterList,[list(experimentProtocols.keys())[0],'','',[False]*12,'',['  ','  ','  '],[],0])}
        for expParameter in expParameterList:
            if expParameter in tempExpParameters:
                if expParameter in ['experimentProtocol','experimentID','numTimepoints','numPlates']:
                    defaultValueDict[expParameter] = tempExpParameters[expParameter]
                elif expParameter == 'daysAgo':
                    timeDifference = datetime.today() - datetime.strptime(tempExpParameters['fullStart'],'%Y-%m-%d %a %I:%M %p') 
                    roundupDay = 0
                    if timeDifference.seconds > 0:
                        roundupDay = 1
                    defaultValueDict[expParameter] = timeDifference.days+roundupDay 
                elif expParameter == 'blankColumns':
                    bools = defaultValueDict[expParameter].copy() 
                    trueBools = []
                    for i,x in enumerate(defaultValueDict[expParameter]):
                        negation = bools[int(x)-1]
                        if i+1 not in tempExpParameters[expParameter]:
                            trueBools.append(negation)
                        else:
                            trueBools.append(not negation)
                    defaultValueDict[expParameter] = trueBools 
                elif expParameter == 'startTime':
                    full = tempExpParameters[expParameter]
                    firstBreak = full.index(':')
                    secondBreak = full.index(' ')
                    defaultValueDict[expParameter] = [full[:firstBreak],full[firstBreak+1:secondBreak],full[secondBreak+1:]]

        def enableFinish(event=None):
            #Also check for re-enabling "enter timepoints" button
            try:
                # TODO: Remove incubator position??
                allWidgetChecks = [experimentProtocolVar.get(),meridianVar.get(),minuteVar.get()]
                allWidgetBools = [experimentNameEntry.get() != '']+[x != '  ' for x in allWidgetChecks]
                if all(allWidgetBools):
                    enterTpButton.config(state=tk.NORMAL)
                else:
                    enterTpButton.config(state=tk.DISABLED)
            except:
                enterTpButton.config(state=tk.DISABLED)
                
        tk.Label(mainWindow,text='Experiment type:').grid(row=0,column=0,sticky=tk.W)
        experimentProtocolList = list(experimentProtocols.keys()) 
        experimentProtocolVar = tk.StringVar()
        experimentProtocolDropdown = ttk.OptionMenu(mainWindow,experimentProtocolVar,defaultValueDict['experimentProtocol'],*experimentProtocolList,command=lambda _: enableFinish())
        experimentProtocolDropdown.grid(row=0,column=1,sticky=tk.W)
        
        tk.Label(mainWindow,text='Experiment name:').grid(row=1,column=0,sticky=tk.W)
        experimentNameEntry = ttk.Entry(mainWindow,width=20)
        experimentNameEntry.insert(tk.END, str(defaultValueDict['experimentID']))
        experimentNameEntry.grid(row=1,column=1,sticky=tk.W)
        experimentNameEntry.bind("<Key>",enableFinish)

        startPos = 4
        
        tk.Label(mainWindow,text='Number of plates:').grid(row=2,column=0,sticky=tk.W)
        plateNumberEntry = tk.Entry(mainWindow,width=10)
        plateNumberEntry.insert(tk.END,str(defaultValueDict['numPlates']))
        plateNumberEntry.grid(row=2,column=1,sticky=tk.W)
        
        tk.Label(mainWindow,text='Blank columns:').grid(row=startPos+1,column=0,sticky=tk.W)
        blankList = list(range(1,13))
        blankCBList,blankVarList = [],[]
        blankCBFrame = tk.Frame(mainWindow)
        blankCBFrame.grid(row=startPos+1,column=1)
        for pos in blankList:
            blankVar = tk.BooleanVar(value=defaultValueDict['blankColumns'][pos-1])
            blankCB = ttk.Checkbutton(blankCBFrame,variable=blankVar)
            blankCB.grid(row=0,column=pos-1,sticky=tk.W)
            tk.Label(blankCBFrame,text=str(pos)).grid(row=1,column=pos-1,sticky=tk.W)
            blankCBList.append(blankCB)
            blankVarList.append(blankVar)
        
        startPos2 = 6

        tk.Label(mainWindow,text='Number of timepoints:').grid(row=startPos2,column=0,sticky=tk.W)
        timepointNumberEntry = tk.Entry(mainWindow,width=10)
        timepointNumberEntry.insert(tk.END,str(defaultValueDict['numTimepoints']))
        timepointNumberEntry.grid(row=startPos2,column=1,sticky=tk.W)

        tk.Label(mainWindow,text='Experiment start time:').grid(row=startPos2+1,column=0,sticky=tk.W)
        startTimeFrame = tk.Frame(mainWindow)
        startTimeFrame.grid(row=startPos2+1,column=1,sticky=tk.W)
        hourList = [str(x).zfill(2) for x in range(1,13)]
        hourVar = tk.StringVar()
        hourDropdown = ttk.OptionMenu(startTimeFrame,hourVar,str(defaultValueDict['startTime'][0]),*hourList,command=lambda _: enableFinish())
        hourDropdown.grid(row=0,column=0,sticky=tk.W)
        minuteList = [str(x).zfill(2) for x in range(0,60,5)]
        minuteVar = tk.StringVar()
        minuteDropdown = ttk.OptionMenu(startTimeFrame,minuteVar,str(defaultValueDict['startTime'][1]),*minuteList,command=lambda _: enableFinish())
        minuteDropdown.grid(row=0,column=1,sticky=tk.W)
        meridianList = ['AM','PM']
        meridianVar = tk.StringVar()
        meridianDropdown = ttk.OptionMenu(startTimeFrame,meridianVar,str(defaultValueDict['startTime'][2]),*meridianList,command=lambda _: enableFinish())
        meridianDropdown.grid(row=0,column=2,sticky=tk.W)
        
        tk.Label(mainWindow,text='Days since experiment start:').grid(row=startPos2+2,column=0,sticky=tk.W)
        daysAgoEntry = ttk.Entry(mainWindow,width=5)
        daysAgoEntry.grid(row=startPos2+2,column=1,sticky=tk.W)
        daysAgoEntry.insert(tk.END,str(defaultValueDict['daysAgo']))
        
        def collectInputs():
            experimentParameters = {}
            experimentParameters['experimentID'] = experimentNameEntry.get()
            experimentParameters['protocolParameters'] = experimentProtocols[experimentProtocolVar.get()]
            experimentParameters['incubatorPositions'] = calculateIncubatorPositions(incubatorPath, experimentProtocols[experimentProtocolVar.get()], int(plateNumberEntry.get()), int(timepointNumberEntry.get()))
            experimentParameters['fridgePositions'] = calculateFridgePositions(fridgePath, experimentProtocols[experimentProtocolVar.get()], int(plateNumberEntry.get()), [x+1 for x in range(12) if blankVarList[x].get()], int(timepointNumberEntry.get()))
            experimentParameters['numPlates'] = int(plateNumberEntry.get())
            experimentParameters['blankColumns'] = [x+1 for x in range(12) if blankVarList[x].get()]
            experimentParameters['numTimepoints'] = int(timepointNumberEntry.get())
            experimentParameters['timepointlist'] = []
            experimentParameters['startTime'] = hourVar.get()+':'+minuteVar.get()+' '+meridianVar.get()
            experimentParameters['daysAgo'] = int(daysAgoEntry.get())    
            now = datetime.today() - dt.timedelta(days=experimentParameters['daysAgo'])
            parsedStartTime = datetime.strptime(experimentParameters['startTime'],'%I:%M %p')
            fullStartTime = datetime(now.year,now.month,now.day,parsedStartTime.hour,parsedStartTime.minute)
            experimentParameters['fullStart'] = fullStartTime.strftime('%Y-%m-%d %a %I:%M %p')
            experimentParameters['addedToMatrix'] = False

            master.switch_frame(TimepointEntryPage,expNum,experimentParameters)
        
        buttonWindow = tk.Frame(self)
        buttonWindow.pack(side=tk.TOP,pady=20)
        enterTpButton = ttk.Button(buttonWindow, text="Enter timepoints",command=lambda: collectInputs())
        enterTpButton.pack(side=tk.LEFT)
        enableFinish()
        ttk.Button(buttonWindow, text="Back",command=lambda: master.switch_frame(ExperimentHomePage)).pack(side=tk.LEFT)
        ttk.Button(buttonWindow, text="Quit",command=lambda: quit()).pack(side=tk.LEFT)
    
class TimepointEntryPage(tk.Frame):
    def __init__(self,master,expNum,experimentParameters):
        tk.Frame.__init__(self, master)
        mainWindow = tk.Frame(self)
        mainWindow.pack(side=tk.TOP,padx=10)
        
        timepointTemplates = {
                6:[3,6,12,24,48,72],
                8:[3,6,12,18,24,36,48,72],
                12:[1,3,6,12,18,24,30,36,42,48,60,72],
                16:[1,3,5,7,11,15,19,23,29,35,41,47,53,59,65,72],
                24:[1,3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51,54,57,60,63,66,72]
                }
        numTimepoints = experimentParameters['numTimepoints']

        tk.Label(mainWindow,text='Timepoint').grid(row=0,column=0,sticky=tk.W)
        timepointEntryList = []
        for t in range(numTimepoints):
            tk.Label(mainWindow,text=str(t+1)+':').grid(row=t,column=1)
            timepointEntry = ttk.Entry(mainWindow,width=5)
            if len(experimentParameters['timepointlist']) == 0:
                if numTimepoints in timepointTemplates:
                    timepointEntry.insert(tk.END, str(timepointTemplates[numTimepoints][t]))
            else:
                timepointEntry.insert(tk.END, str(experimentParameters['timepointlist'][t]))
            timepointEntry.grid(row=t,column=2,sticky=tk.W)
            timepointEntryList.append(timepointEntry)

        def collectInputs():
            experimentParameters['timepointlist'] = [float(x.get()) for x in timepointEntryList]
            allExperimentParameters = pickle.load(open(finalInputPath+'experimentParameters.pkl','rb'))
            allExperimentParameters[expNum] = experimentParameters
            with open(finalInputPath+'experimentParameters.pkl','wb') as f:
                pickle.dump(allExperimentParameters,f)
            
            #Write to containers
            editContainerStatus(incubatorPath,expNum+1,experimentParameters['incubatorPositions'])
            editContainerStatus(fridgePath,expNum+1,experimentParameters['fridgePositions'])
            master.switch_frame(ExperimentHomePage)

        buttonWindow = tk.Frame(self)
        buttonWindow.pack(side=tk.TOP,pady=20)
        ttk.Button(buttonWindow, text="Finish",command=lambda: collectInputs()).pack(side=tk.LEFT)
        ttk.Button(buttonWindow, text="Back",command=lambda: master.switch_frame(ExperimentInfoPage,expNum)).pack(side=tk.LEFT)
        ttk.Button(buttonWindow, text="Quit",command=lambda: quit()).pack(side=tk.LEFT)

if __name__== "__main__":
    app = MainApp()
    app.mainloop()
