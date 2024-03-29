#! /usr/bin/env python3
import pickle,os,subprocess,math
from datetime import datetime
import datetime as dt
import tkinter as tk
import pandas as pd
import numpy as np
from functools import partial
from tkinter import messagebox
import seaborn as sns
from matrixGenerator import generateExperimentMatrix,combineExperiments
from utils import calculateIncubatorPositions,calculateFridgePositions,checkContainerStatus,editContainerStatus
from simulateLoadUnload import simulateLoadUnload
import tkinter.ttk as ttk
import platform
from string import ascii_uppercase

schedulePath = 'schedules/' 
matrixPath = 'matrices/'
finalInputPath = 'misc/'
if platform.system() == 'Windows':
    finalOutputPath = 'C:/ProgramData/Tecan/EVOware/database/variables/'
else:
    finalOutputPath = 'variables/'

incubatorPath = finalOutputPath+'incubatorStatus.txt'
fridgePath = finalOutputPath+'fridgeStatus.txt'

<<<<<<< HEAD
=======
experimentTypeDict = {
        'Supernatant (Sooraj)':1,
        'Supernatant+Fix/Perm (Madison)':2,
        'Reverse Plating (Anagha)':3,
        'Supernatant+LD/Ab/Fix/Perm (Anagha)':4,
        'Supernatant+Fix/Perm+SupTransfer (Madison)':5,
        'Reverse Kinetics (Dongya)':6,
        'SupTransfer_Only (Madison)':7
        }
>>>>>>> 8978657151be80dca5b0418633cbd90d2ad17419
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
        '''Destroys current frame and replaces it with a new one.'''
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
        allLabels = ['Experiment:','Type (Author):','Name:','Incubator racks:','Fridge racks:','# plates per timepoint:','Blank columns:','# timepoints:','Start Time:','Timepoints:','End Time:','Incubator Loaded?','Fridge Loaded?','Added to matrix:']
        
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
            if 'masterSchedule.txt' in os.listdir(finalInputPath):
                with open(finalInputPath+'masterSchedule.txt', 'r') as schedule:
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
                quitButton.config(state=tk.NORMAL)
            #Only enable experiment removal button if incubator and fridge are unloaded:
            for exp in range(NUMEXP):
                if self.allExpInfoLabels[exp][-3]['text'] != EMPTYTEXT:
                    if self.allExpInfoLabels[exp][-3]['text'] == 'No' and self.allExpInfoLabels[exp][-3]['text'] == 'No':
                        allRemoveButtons[exp].config(state=tk.NORMAL)
                    else:
                        allRemoveButtons[exp].config(state=tk.DISABLED)
                else:
                    allRemoveButtons[exp].config(state=tk.DISABLED)
            #ttk.Separator(expFrame, orient='horizontal').place(relx=0,rely=0+separatorOffset*(len(allLabels)-1+maxPlateChangeLen),relwidth=1)
            self.after(2000, updateExperimentLabels)

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
        
        def addProtocol():
            master.switch_frame(AddProtocolPage)
        
        def flipPage_simulateLoadUnload():
            master.switch_frame(SimulateLoadUnloadPage)
        
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
            slotColor = sns.color_palette(sns.color_palette(),10).as_hex()[expNum]
            tk.Label(specificExpFrame,text=str(expNum+1),font='-weight bold -size 20',fg=slotColor).grid(row=0,column=expNum*2,columnspan=2)
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
            editButton = ttk.Button(specificExpFrame,text='Edit',command=partial(editExp,expNum),width=6)
            editButton.grid(row=len(allLabels)+1,column=expNum*2,sticky=tk.E)
            removeButton = ttk.Button(specificExpFrame,text='Remove',command=partial(removeExp,expNum),width=6)
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

        buttonWindow = tk.Frame(self)
        buttonWindow.pack(side=tk.TOP,padx=10,pady=(10,10))
        style.configure('Bold.TButton', font = ('Sans-Serif','12','bold'))
        addButton = ttk.Button(buttonWindow, text='Add New Protocol', style = 'Bold.TButton',command=lambda: addProtocol())
        addButton.pack(side=tk.LEFT)
        
        generateButton = ttk.Button(buttonWindow, text='Generate Matrix', style = 'Bold.TButton',command=lambda: generateFullMatrix())
        generateButton.pack(side=tk.LEFT)
        
        simButton = ttk.Button(buttonWindow, text='Simulate Unload/Load', style = 'Bold.TButton', command=lambda: flipPage_simulateLoadUnload())
        simButton.pack(side=tk.LEFT)
        
        quitButton = ttk.Button(buttonWindow, text='Quit',command=lambda: quit())
        quitButton.pack(side=tk.LEFT)

        updateExperimentLabels()

class ExperimentInfoPage(tk.Frame):
    def __init__(self,master,expNum):
        tk.Frame.__init__(self, master)
        mainWindow = tk.Frame(self)
        mainWindow.pack(side=tk.TOP,padx=10)
        
        allExpParameters = pickle.load(open(finalInputPath+'experimentParameters.pkl','rb'))
        experimentProtocols = pickle.load(open(finalInputPath+'experimentProtocols.pkl','rb'))
        protocolIDToName = {experimentProtocols[x]['protocolID']:x for x in experimentProtocols}
        #Set defaults to saved values if entry already exists; does not quite work for multiplates
        tempExpParameters = allExpParameters[expNum]
        expParameterList = ['experimentProtocol','experimentID','numPlates','blankColumns','numTimepoints','startTime','timepointList','daysAgo']
        defaultValueDict = {k:v for k,v in zip(expParameterList,[list(experimentProtocols.keys())[0],'','',[False]*12,'',['  ','  ','  '],[],0])}
        for expParameter in expParameterList:
            if expParameter in tempExpParameters or expParameter == 'experimentProtocol':
                if expParameter == 'experimentProtocol' and 'protocolParameters' in tempExpParameters:
                    defaultValueDict[expParameter] = protocolIDToName[tempExpParameters['protocolParameters']['protocolID']]
                elif expParameter in ['experimentID','numTimepoints','numPlates']:
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
            #Also check for re-enabling 'enter timepoints' button
            try:
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
        experimentNameEntry.bind('<Key>',enableFinish)

        startPos = 4
        
<<<<<<< HEAD
        tk.Label(mainWindow,text='Number of plates:').grid(row=2,column=0,sticky=tk.W)
        plateNumberEntry = tk.Entry(mainWindow,width=10)
        plateNumberEntry.insert(tk.END,str(defaultValueDict['numPlates']))
        plateNumberEntry.grid(row=2,column=1,sticky=tk.W)
=======
        tk.Label(mainWindow,text='Incubator plate position:').grid(row=startPos,column=0,sticky=tk.W)
        incubatorPlatePosList = list(range(1,23)) 
        incubatorPlatePosVar = tk.IntVar()
        incubatorPlatePosDropdown = ttk.OptionMenu(mainWindow,incubatorPlatePosVar,defaultValueDict['plateOffset'],*incubatorPlatePosList,command=lambda _: enableFinish())
        incubatorPlatePosDropdown.grid(row=startPos,column=1,sticky=tk.W)
        
        tk.Label(mainWindow,text='Cooling plate positions:').grid(row=3,column=0,sticky=tk.W)
        coolingPlatePosList = list(range(1,5))
        coolingPlatePosCBList,coolingPlatePosVarList = [],[]
        coolingCBFrame = tk.Frame(mainWindow)
        coolingCBFrame.grid(row=3,column=1,sticky=tk.W)
        for pos in coolingPlatePosList:
            coolingPlatePosVar = tk.BooleanVar(value=defaultValueDict['platePoseRestriction'][pos-1])
            coolingPlatePosCB = ttk.Checkbutton(coolingCBFrame,variable=coolingPlatePosVar)
            l = tk.Label(coolingCBFrame,text=str(pos))
            l.grid(row=1,column=pos-1,sticky=tk.W)
            if pos in reservedCooling:
                coolingPlatePosVar.set(False)
                coolingPlatePosCB['state'] = tk.DISABLED
                l.config(fg='grey')
            coolingPlatePosCB.grid(row=0,column=pos-1,sticky=tk.W)
            coolingPlatePosCBList.append(coolingPlatePosCB)
            coolingPlatePosVarList.append(coolingPlatePosVar)

        def disableIncubatorEntries():
            conditionNumber = conditionNumberVar.get()
            numPlates = math.ceil(conditionNumber/96)
            plateDisablingRadius = numPlates-1
            #First re-enable any disabled option menu at previous condition number
            for i in range(len(incubatorPlatePosList)):
                incubatorPlatePosDropdown['menu'].entryconfigure(i, state = "normal")
            for reservedRack in reservedRacks:
                for i in range(max(reservedRack-plateDisablingRadius,1),reservedRack+1):
                    incubatorPlatePosDropdown['menu'].entryconfigure(i-1, state = "disabled")
            #disableTimepointEntries()

        timepointNumberList = list(range(1,25))
        def disableTimepointEntries():
            conditionNumber = conditionNumberVar.get()
            invalidTimepoints = [x for x in timepointNumberList if (x*conditionNumber)%384 != 0]
            #First re-enable any disabled option menu at previous condition number
            for i in range(len(timepointNumberList)):
                timepointNumberDropdown['menu'].entryconfigure(i, state = "normal")
            for invalidTimepoint in invalidTimepoints:
                timepointNumberDropdown['menu'].entryconfigure(invalidTimepoint-1, state = "disabled")

        tk.Label(mainWindow,text='Number of conditions:').grid(row=2,column=0,sticky=tk.W)
        conditionNumberList =[8,16,24,32,48,56,64,72,80,88,96,128,192,256,288,384]
        conditionNumberVar = tk.IntVar()
        conditionNumberDropdown = ttk.OptionMenu(mainWindow,conditionNumberVar,defaultValueDict['numConditions'],*conditionNumberList,command=lambda _: disableIncubatorEntries())
        conditionNumberDropdown.grid(row=2,column=1,sticky=tk.W)
        
        #Disable racks that are already occupied
        plateDisablingRadius = math.ceil(defaultValueDict['numConditions']/96)-1
        for reservedRack in reservedRacks:
            for i in range(max(reservedRack-plateDisablingRadius,1),reservedRack+1):
                incubatorPlatePosDropdown['menu'].entryconfigure(i-1, state = "disabled")
>>>>>>> 8978657151be80dca5b0418633cbd90d2ad17419
        
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

            #Need special logic here to avoid re-calculating incubator positions that were already assigned
            oldIncubatorPositions = np.loadtxt(finalOutputPath+'incubatorStatus.txt',delimiter=',')[expNum]
            oldIncubatorPositions = list(oldIncubatorPositions[oldIncubatorPositions != 0].astype(int))
            editContainerStatus(incubatorPath, expNum+1, [0]*22)
            newIncubatorPositions = calculateIncubatorPositions(incubatorPath, experimentProtocols[experimentProtocolVar.get()], int(plateNumberEntry.get()), int(timepointNumberEntry.get()))
            if len(newIncubatorPositions) == len(oldIncubatorPositions):
                finalIncubatorPositions = oldIncubatorPositions
            else:
                finalIncubatorPositions = newIncubatorPositions
            editContainerStatus(incubatorPath, expNum+1, finalIncubatorPositions)
            experimentParameters['incubatorPositions'] = finalIncubatorPositions 
            
            #Need special logic here to avoid re-calculating fridge positions that were already assigned
            oldFridgePositions = np.loadtxt(finalOutputPath+'fridgeStatus.txt',delimiter=',')[expNum]
            oldFridgePositions = list(oldFridgePositions[oldFridgePositions != 0].astype(int))
            editContainerStatus(fridgePath, expNum+1, [0]*44)
            newFridgePositions = calculateFridgePositions(fridgePath, experimentProtocols[experimentProtocolVar.get()], int(plateNumberEntry.get()), [x+1 for x in range(12) if blankVarList[x].get()], int(timepointNumberEntry.get()))
            if len(newFridgePositions) == len(oldFridgePositions):
                finalFridgePositions = oldFridgePositions
            else:
                finalFridgePositions = newFridgePositions
            editContainerStatus(fridgePath, expNum+1, finalFridgePositions)
            experimentParameters['fridgePositions'] = finalFridgePositions 
            
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
        enterTpButton = ttk.Button(buttonWindow, text='Enter timepoints',command=lambda: collectInputs())
        enterTpButton.pack(side=tk.LEFT)
        enableFinish()
        ttk.Button(buttonWindow, text='Back',command=lambda: master.switch_frame(ExperimentHomePage)).pack(side=tk.LEFT)
        ttk.Button(buttonWindow, text='Quit',command=lambda: quit()).pack(side=tk.LEFT)
    
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
        ttk.Button(buttonWindow, text='Finish',command=lambda: collectInputs()).pack(side=tk.LEFT)
        ttk.Button(buttonWindow, text='Back',command=lambda: master.switch_frame(ExperimentInfoPage,expNum)).pack(side=tk.LEFT)
        ttk.Button(buttonWindow, text='Quit',command=lambda: quit()).pack(side=tk.LEFT)

class AddProtocolPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master

        self.experimentProtocols = pickle.load(open(finalInputPath + 'experimentProtocols.pkl', 'rb'))
        next_protocol_id = max([protocol['protocolID'] for protocol in self.experimentProtocols.values()], default=0) + 1
        
        def enableFinish(event=None):
            try:
                allWidgetChecks = [protocol_name_entry.get(), protocol_author_entry.get(), protocol_length_entry.get(), num_cols_tips_entry.get()]
                allWidgetBools = [x != '' for x in allWidgetChecks]
                if all(allWidgetBools):
                    saveButton.config(state=tk.NORMAL)
                else:
                    saveButton.config(state=tk.DISABLED)
            except:
                saveButton.config(state=tk.DISABLED)
        
        # Create the necessary widgets for the page
        # Protocol ID
        protocol_id_label = tk.Label(self, text='Protocol ID:')
        protocol_id_label.pack()
        
        protocol_id_entry = tk.Entry(self)
        protocol_id_entry.insert(0, str(next_protocol_id))
        protocol_id_entry.configure(state='readonly')
        protocol_id_entry.pack()
        
        # Protocol Name
        protocol_name_label = tk.Label(self, text='Protocol Name:')
        protocol_name_label.pack()
        
        protocol_name_entry = tk.Entry(self)
        protocol_name_entry.pack()
        protocol_name_entry.bind('<Key>',enableFinish)
        
        # Protocol Author
        protocol_author_label = tk.Label(self, text='Protocol Author:')
        protocol_author_label.pack()
        
        protocol_author_entry = tk.Entry(self)
        protocol_author_entry.pack()
        protocol_author_entry.bind('<Key>',enableFinish)
        
        # Protocol Length
        protocol_length_label = tk.Label(self, text='Estimated Protocol Length (min):')
        protocol_length_label.pack()
        
        protocol_length_entry = tk.Entry(self)
        protocol_length_entry.pack()
        protocol_length_entry.bind('<Key>',enableFinish)
        
        # Number of Columns/Tips
        num_cols_tips_label = tk.Label(self, text='Number of Columns of Tips used per Timepoint:')
        num_cols_tips_label.pack()
        
        num_cols_tips_entry = tk.Entry(self)
        num_cols_tips_entry.pack()
        num_cols_tips_entry.bind('<Key>',enableFinish)

        # Same Plates Across Experiment
        same_plates_label = ttk.Label(self, text='Same Plates Across Experiment:')
        same_plates_label.pack()
        self.same_plates_var = tk.StringVar(value='False')
        same_plates_combobox = ttk.Combobox(self, textvariable=self.same_plates_var, values=['True', 'False'])
        same_plates_combobox.set('False')
        same_plates_combobox.pack()
        same_plates_combobox.bind('<<ComboboxSelected>>', enableFinish)
        
        # Transfer to Collection
        transfer_to_collection_label = ttk.Label(self, text='Transfer to Collection:')
        transfer_to_collection_label.pack()
        self.transfer_to_collection_var = tk.StringVar(value='False')
        transfer_to_collection_combobox = ttk.Combobox(self, textvariable=self.transfer_to_collection_var, values=['True', 'False'])
        transfer_to_collection_combobox.set('False')
        transfer_to_collection_combobox.pack()
        transfer_to_collection_combobox.bind('<<ComboboxSelected>>', enableFinish)
        
        # Refrigerate Culture Plate
        refrigerate_culture_plate_label = ttk.Label(self, text='Refrigerate Culture Plate:')
        refrigerate_culture_plate_label.pack()
        self.refrigerate_culture_plate_var = tk.StringVar(value='False')
        refrigerate_culture_plate_combobox = ttk.Combobox(self, textvariable=self.refrigerate_culture_plate_var, values=['True', 'False'])
        refrigerate_culture_plate_combobox.set('False')
        refrigerate_culture_plate_combobox.pack()
        refrigerate_culture_plate_combobox.bind('<<ComboboxSelected>>', enableFinish)
        
        # Different Lines per Plate
        different_lines_per_plate_label = ttk.Label(self, text='Treat multiple plates as separate timepoints:')
        different_lines_per_plate_label.pack()
        self.different_lines_per_plate_var = tk.StringVar(value='False')
        different_lines_per_plate_combobox = ttk.Combobox(self, textvariable=self.different_lines_per_plate_var, values=['True', 'False'])
        different_lines_per_plate_combobox.set('False')
        different_lines_per_plate_combobox.pack()
        different_lines_per_plate_combobox.bind('<<ComboboxSelected>>', enableFinish)
    
        def collectInputs():
            protocol_id = int(protocol_id_entry.get())
            protocol_name = protocol_name_entry.get()
            protocol_author = protocol_author_entry.get()
            same_plates = True if self.same_plates_var.get() == 'True' else False
            transfer_to_collection = True if self.transfer_to_collection_var.get() == 'True' else False
            protocol_length = int(protocol_length_entry.get())
            num_cols_tips = int(num_cols_tips_entry.get())
            refrigerate_culture = True if self.refrigerate_culture_plate_var.get() == 'True' else False
            different_lines = True if self.different_lines_per_plate_var.get() == 'True' else False

            # Create a new dictionary with the protocol information
            protocol_info = {
                'protocolID': protocol_id,
                'samePlatesAcrossExperiment': same_plates,
                'transferToCollection': transfer_to_collection,
                'protocolLength':protocol_length,
                'numColsTips':num_cols_tips,
                'refrigerateCulturePlate':refrigerate_culture,
                'differentLinesPerPlate':different_lines
            }

            # Add the new protocol to the main dictionary
            self.experimentProtocols[f'{protocol_name} ({protocol_author})'] = protocol_info

            # Save the updated dictionary to the file
            pickle.dump(self.experimentProtocols, open(finalInputPath + 'experimentProtocols.pkl', 'wb'))
            
            # Inform the user that the protocol has been saved
            messagebox.showinfo('Protocol Saved', 'Protocol {} has been saved.'.format(protocol_name))

            # Switch back to the main page
            self.master.switch_frame(ExperimentHomePage)
    
        buttonWindow = tk.Frame(self)
        buttonWindow.pack(side=tk.TOP,pady=20)
        saveButton = ttk.Button(buttonWindow, text='Finish',command=lambda: collectInputs())
        saveButton.pack(side=tk.LEFT)
        enableFinish()
        ttk.Button(buttonWindow, text='Back',command=lambda: master.switch_frame(ExperimentHomePage)).pack(side=tk.LEFT)

class SimulateLoadUnloadPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master

        
        # Create the necessary widgets for the page
        
        # Experiment Slot
        slot_label = ttk.Label(self, text='Which experiment slot are you simulating?:')
        slot_label.pack()
        self.slot_var = tk.StringVar(value='1')
        slot_combobox = ttk.Combobox(self, textvariable=self.slot_var, values=[str(x) for x in range(1,9)])
        slot_combobox.set('1')
        slot_combobox.pack()

        # Incubator or Fridge
        container_label = ttk.Label(self, text='Would you like to simulate the incubator or fridge?:')
        container_label.pack()
        self.container_var = tk.StringVar(value='Incubator')
        container_combobox = ttk.Combobox(self, textvariable=self.container_var, values=['Incubator', 'Fridge'])
        container_combobox.set('Incubator')
        container_combobox.pack()
        
        # Unload Load
        action_label = ttk.Label(self, text='Do you need to load or unload?:')
        action_label.pack()
        self.action_var = tk.StringVar(value='Unload')
        action_combobox = ttk.Combobox(self, textvariable=self.action_var, values=['Unload', 'Load'])
        action_combobox.set('Unload')
        action_combobox.pack()
        
    
        def collectInputs():
            incubatorFridge = 0 if self.container_var.get() == 'Incubator' else 1
            unloadLoad = 0 if self.action_var.get() == 'Unload' else 1
            experimentSlot = int(self.slot_var.get())

            simulateLoadUnload(incubatorFridge, unloadLoad, experimentSlot)
            
            # Switch back to the main page
            self.master.switch_frame(ExperimentHomePage)
    
        buttonWindow = tk.Frame(self)
        buttonWindow.pack(side=tk.TOP,pady=20)
        saveButton = ttk.Button(buttonWindow, text='Finish',command=lambda: collectInputs())
        saveButton.pack(side=tk.LEFT)
        ttk.Button(buttonWindow, text='Back',command=lambda: master.switch_frame(ExperimentHomePage)).pack(side=tk.LEFT)

if __name__== '__main__':
    app = MainApp()
    app.mainloop()
