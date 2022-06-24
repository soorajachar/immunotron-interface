#! /usr/bin/env python3
import pickle,os,subprocess,math
from datetime import datetime
import datetime as dt
import tkinter as tk
import pandas as pd
import numpy as np
from functools import partial
#from PIL import Image,ImageTk
from tkinter import messagebox
from matrixGenerator import generateExperimentMatrix,combineExperiments
import tkinter.ttk as ttk
import platform
from string import ascii_uppercase

schedulePath = 'schedules/' 
matrixPath = 'matrices/'
if platform.system() == 'Windows':
    finalPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
else:
    finalPath = ''


experimentTypeDict = {
        'Supernatant (Sooraj)':1,
        'Supernatant+Fix/Perm (Madison)':2,
        'Reverse Plating (Anagha)':3,
        'Supernatant+LD/Ab/Fix/Perm (Anagha)':4
        }
#Root class; handles frame switching in gui
class MainApp(tk.Tk):
    def __init__(self):
        self.root = tk.Tk.__init__(self)

        #self.title('plateypus '+version('plateypus'))
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
        NUMEXP = 4
        allLabels = ['Experiment:','Type (Author):','Name:','Incubator rack:','Cooling plate:','# conditions:','Blank columns:','# timepoints:','Start Time:','Timepoints:','End Time:','Change cooling plate:','Added to matrix:']
        
        if 'allExperimentParameters.pkl' not in os.listdir():
            self.allExperimentParameters = {k:{} for k in range(NUMEXP)}
            with open('allExperimentParameters.pkl','wb') as f:
                pickle.dump(self.allExperimentParameters,f)
        else:
            self.allExperimentParameters = pickle.load(open('allExperimentParameters.pkl','rb'))
            #Temporary backwards compatibility
            if 'experimentType' not in list(self.allExperimentParameters.keys()):
                for eID in self.allExperimentParameters:
                    if len(self.allExperimentParameters[eID].keys()) != 0:
                        newDict = {**{'experimentType':list(experimentTypeDict.keys())[0]},**self.allExperimentParameters[eID]}
                        self.allExperimentParameters[eID] = newDict
        
        expFrame = tk.Frame(self,borderwidth=0.8,relief=tk.SOLID)
        expFrame.pack()
        labelFrame = tk.Frame(expFrame)
        labelFrame.grid(row=0,column=0)
        
        def updateExperimentLabels():
            maxPlateChangeLen = 0
            finalPlateChangeDict = {}
            validExps = []
            for exp in range(NUMEXP):
                if len(self.allExperimentParameters[exp]) != 0:
                    validExps.append(exp)
                    for i,expParameter in enumerate(list(self.allExperimentParameters[exp].keys())[:-3]):
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
                                if expParameter == 'plateOffset':
                                    numPlates = int(math.ceil(self.allExperimentParameters[exp]['numConditions']/96))
                                    parsedValue = ', '.join([str(x) for x in range(rawValue,rawValue+numPlates)])
                                elif expParameter == 'startTime':
                                    parsedValue = self.allExperimentParameters[exp]['fullStart']
                                else:
                                    parsedValue = str(rawValue)
                        self.allExpInfoLabels[exp][i].configure(text=parsedValue,fg='black')
                    
                    endTime = datetime.strptime(self.allExperimentParameters[exp]['fullStart'],'%Y-%m-%d %a %I:%M %p')+dt.timedelta(hours=self.allExperimentParameters[exp]['timepointlist'][-1])
                    self.allExpInfoLabels[exp][-3].configure(text=endTime.strftime('%Y-%m-%d %a %I:%M %p'))
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
                    numConditions = self.allExperimentParameters[exp]['numConditions']
                    timepointsPerPlate = int(plateSize/numConditions)
                    platesRequired = int(numTimepoints/timepointsPerPlate)
                    platePoses = self.allExperimentParameters[exp]['platePoseRestriction']
                    plateChangeDict,plateChangeDict2 = {},{}
                    j = 1
                    for i in range(platesRequired):
                        plateChange = i%len(platePoses)
                        if plateChange not in plateChangeDict:
                            plateChangeDict2[plateChange] = []
                            plateChangeDict[plateChange] = []
                        else:
                            #Plate change dict 2 tracks the completion of a plate; this does not depend on the number of plate positions; only on the number of timepoints/plate
                            plateChangeDict2[plateChange]+=[j*timepointsPerPlate-1]
                            j+=1
                            plateChangeDict[plateChange]+=[i*timepointsPerPlate]
                    truePlateChangeDict = {}
                    truePlateChangeDict2 = {}
                    maxLen = 0
                    for i in plateChangeDict:
                        if len(plateChangeDict[i]) > 0:
                            plateChangeDeadlines,plateChangeDeadlines2 = [],[]
                            for x in plateChangeDict[i]:
                                plateChangeDeadline = start+dt.timedelta(hours=self.allExperimentParameters[exp]['timepointlist'][x])
                                plateChangeDeadlines.append(plateChangeDeadline.strftime('%Y-%m-%d %a %I:%M %p'))
                            for x in plateChangeDict2[i]:
                                plateChangeDeadline2 = start+dt.timedelta(hours=self.allExperimentParameters[exp]['timepointlist'][x])
                                plateChangeDeadlines2.append(plateChangeDeadline2.strftime('%Y-%m-%d %a %I:%M %p'))
                            if len(plateChangeDeadlines) > maxLen:
                                maxLen = len(plateChangeDeadlines)
                            truePlateChangeDict[platePoses[i]] = plateChangeDeadlines
                            truePlateChangeDict2[platePoses[i]] = plateChangeDeadlines2
                    finalPlateChangeStrings = []
                    for j in range(maxLen):
                        for i in truePlateChangeDict:
                            if j < len(truePlateChangeDict[i]):
                                #Remove any plate change deadlines that have passed
                                if datetime.now() < datetime.strptime(truePlateChangeDict[i][j],'%Y-%m-%d %a %I:%M %p'):
                                    finalPlateChangeStrings.append('['+str(i)+'] between '+truePlateChangeDict2[i][j]+'\n                     '+truePlateChangeDict[i][j])
                    if len(finalPlateChangeStrings) > maxPlateChangeLen:
                        maxPlateChangeLen = len(finalPlateChangeStrings)
                    if len(finalPlateChangeStrings) > 0:
                        finalPlateChangeDict[exp] = finalPlateChangeStrings
                    #Update added to matrix warnings check if all labels are either yes or - in both removeExp and generate matrix
                    if self.allExperimentParameters[exp]['addedToMatrix']:
                        self.allExpInfoLabels[exp][-1].configure(text='Yes',fg='green')
                    else:
                        self.allExpInfoLabels[exp][-1].configure(text='No',fg='red')
                else:
                    for k in range(len(allLabels)-1):
                        self.allExpInfoLabels[exp][k].configure(text=EMPTYTEXT,fg='black')
            
            #Update plate change deadlines
            for exp in range(NUMEXP):
                if exp in finalPlateChangeDict:
                    finalPlateChangeStrings = finalPlateChangeDict[exp]
                    for i in range(2*(maxPlateChangeLen-len(finalPlateChangeDict[exp]))):
                        finalPlateChangeStrings+=['']
                    finalPlateChangeString = '\n'.join(finalPlateChangeStrings)
                    self.allExpInfoLabels[exp][-2].configure(text=finalPlateChangeString)
                else: 
                    if maxPlateChangeLen > 0:
                        decrement = maxPlateChangeLen*2 - 1
                        finalPlateChangeString = '\n'.join([EMPTYTEXT]+['']*decrement)
                        self.allExpInfoLabels[exp][-2].configure(text=finalPlateChangeString)
            #Add in extra newlines to keep spacing consistent
            if maxPlateChangeLen > 0:
                decrement = maxPlateChangeLen*2 - 1
                self.headerLabels[-2].configure(text='\n'.join([allLabels[-2]]+['']*decrement))
            # REMOVE diti warning (calculations out of date)
            """             
            #Update diti warning label
            if "masterSchedule.txt" in os.listdir():
                with open("masterSchedule.txt", "r") as schedule:
                    lines = schedule.readlines()
                startLine = 0
                numExperiments = 0
                for i,line in enumerate(lines):
                    if 'Experiment ' in line:
                        numExperiments+=1
                singleExperiment = numExperiments == 1
                wafers = int(np.loadtxt(finalPath+'DiTisite.txt'))
                remainingRows = 15-wafers-1

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
                            cutoff = currentRow + remainingRows
                            if row > cutoff and (cutoff != 0):
                                #Determine whether previous timepoint could finish
                                difference = allRows[-1] - allRows[-2]
                                if allRows[-2]+difference-1 <= cutoff:
                                    finalTimepoint = lines[i]
                                else:
                                    finalTimepoint = lines[i-1]
                                break
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

                #Update diti warning label
                if finalTimepoint == '':
                    ditiWarningLabel.config(text='')
                else:
                    if len(validExps) > 0:
                        if singleExperiment:
                            expID = self.allExperimentParameters[validExps[0]]['experimentID']
                        else:
                            expID = finalTimepoint.split(': ')[0].split('-')[1]
                        tipChangeDeadline = finalTimepoint.split(': ')[1].split(' (')[0]
                        ditiWarningLabel.config(text='Change tips before '+tipChangeDeadline+' ('+expID+' timepoint)')
                
                for exp in range(NUMEXP):
                    allAddedStrings = [self.allExpInfoLabels[exp][-1]['text'] for exp in range(NUMEXP)]
                    emptyCount = 0
                    noCount = 0
                    for addedString in allAddedStrings:
                        if addedString == EMPTYTEXT:
                            emptyCount+=1
                        elif addedString == 'No':
                            noCount+=1
                    if emptyCount == NUMEXP:
                        generateButton.config(state=tk.DISABLED)
                    else:
                        generateButton.config(state=tk.NORMAL)
                        if noCount > 0:
                            quitButton.config(state=tk.DISABLED)
                        else:
                            quitButton.config(state=tk.NORMAL) """

            #ttk.Separator(expFrame, orient='horizontal').place(relx=0,rely=0+separatorOffset*(len(allLabels)-1+maxPlateChangeLen),relwidth=1)
            self.after(60000, updateExperimentLabels)

        def editExp(expNum):
            master.switch_frame(ExperimentInfoPage,expNum)

        def removeExp(expNum):
            if messagebox.askokcancel(title='Warning',message='Are you sure you want to delete Experiment '+str(expNum+1)+'?'):
                #if 'schedule_'+self.allExperimentParameters[expNum]['experimentID']+'.txt' in os.listdir(schedulePath):
                #    os.remove(schedulePath+'schedule_'+self.allExperimentParameters[expNum]['experimentID']+'.txt')
                if 'matrix_'+self.allExperimentParameters[expNum]['experimentID']+'.txt' in os.listdir(matrixPath):
                    os.remove(matrixPath+'matrix_'+self.allExperimentParameters[expNum]['experimentID']+'.txt')
                self.allExperimentParameters[expNum] = {}
                with open('allExperimentParameters.pkl','wb') as f:
                    pickle.dump(self.allExperimentParameters,f)
                updateExperimentLabels()
                allProgressBars[expNum]['value'] = 0 
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
                #ttk.Separator(expFrame, orient='horizontal').place(relx=0,rely=0+separatorOffset*j,relwidth=1)
                #expInfoLabel.grid(row=2+j*2,column=expNum*2,columnspan=2)
                expInfoLabel.grid(row=1+j,column=expNum*2,columnspan=2)
                specificExpInfoLabels.append(expInfoLabel)
            self.allExpInfoLabels.append(specificExpInfoLabels)
            style.layout('text.Horizontal.TProgressbar'+str(expNum+1), pbarStyleArguments)
            style.configure('text.Horizontal.TProgressbar'+str(expNum+1), text='0 %')
            pb = ttk.Progressbar(specificExpFrame, style='text.Horizontal.TProgressbar'+str(expNum+1), mode='determinate',length=150)
            #pb = ttk.Progressbar(specificExpFrame,orient='horizontal',mode='determinate',length=150)
            pb.grid(row=len(allLabels),column=expNum*2,columnspan=2,pady=(0,10))
            editButton = ttk.Button(specificExpFrame,text='Edit',command=partial(editExp,expNum),width=10)
            editButton.grid(row=len(allLabels)+1,column=expNum*2,sticky=tk.E)
            removeButton = ttk.Button(specificExpFrame,text='Remove',command=partial(removeExp,expNum),width=10)
            removeButton.grid(row=len(allLabels)+1,column=expNum*2+1,sticky=tk.W)
            allEditButtons.append(editButton)
            allRemoveButtons.append(removeButton)
            allProgressBars.append(pb)

        def generateFullMatrix():
            experimentIDsToIntegrate,experimentTypesToIntegrate,experimentsToIntegrate = [],[],[]
            for i,l in enumerate(self.allExpInfoLabels):
                expName = l[1]['text']
                if expName != EMPTYTEXT:
                    experimentType = self.allExperimentParameters[i]['experimentType']
                    experimentType = experimentTypeDict[experimentType]
                    experimentIDsToIntegrate.append(expName)
                    experimentsToIntegrate.append(i)
                    experimentTypesToIntegrate.append(experimentType)
            if len(experimentsToIntegrate) == 0:
                messagebox.showwarning(title='Error',message='At least one experiment must be created before a matrix can be generated. Please try again.')
            else:
                if len(experimentsToIntegrate) == 1:
                    _ = generateExperimentMatrix(singleExperiment=True,**self.allExperimentParameters[experimentsToIntegrate[0]])
                else:
                    numRows = 0
                    for exp in experimentsToIntegrate:
                        startTime = self.allExperimentParameters[exp]['fullStart']
                        trueStartTime = datetime.strptime(startTime,'%Y-%m-%d %a %I:%M %p')
                        nowTime = datetime.now()
                        difference = datetime(nowTime.year,nowTime.month,nowTime.day) - datetime(trueStartTime.year,trueStartTime.month,trueStartTime.day)
                        trueDaysAgo = max(0,difference.days)
                        self.allExperimentParameters[exp]['daysAgo'] = trueDaysAgo
                        
                        tempNumRows = generateExperimentMatrix(singleExperiment=False,**self.allExperimentParameters[exp])
                        numRows+=tempNumRows
                    combineExperiments(experimentIDsToIntegrate,experimentTypesToIntegrate,numRows)
                messagebox.showinfo(title='Success',message='Experiment matrix generated!')
                for exp in experimentsToIntegrate:
                    self.allExperimentParameters[exp]['addedToMatrix'] = True
                with open('allExperimentParameters.pkl','wb') as f:
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
        
        #Disallow selection of cooling positions and incubator positions that are currently in use
        allExpParameters = pickle.load(open('allExperimentParameters.pkl','rb'))
        reservedRacks,reservedCooling = [],[]
        for exp in allExpParameters:
            if exp != expNum:
                if 'numConditions' in allExpParameters[exp]:
                    plateOffset = allExpParameters[exp]['plateOffset']
                    numPlates = int(math.ceil(allExpParameters[exp]['numConditions']/96))
                    reservedRacks+=[x for x in range(plateOffset,plateOffset+numPlates)]
                    reservedCooling += allExpParameters[exp]['platePoseRestriction']
        #Set defaults to saved values if entry already exists; does not quite work for multiplates
        tempExpParameters = allExpParameters[expNum]
        expParameterList = ['experimentType','experimentID','plateOffset','platePoseRestriction','numConditions','blankColumns','numTimepoints','startTime','timepointList','daysAgo']
        defaultValueDict = {k:v for k,v in zip(expParameterList,[list(experimentTypeDict.keys())[0],'','  ',[True]*4,96,[False]*12,12,['  ','  ','  '],[],0])}
        for expParameter in expParameterList:
            if expParameter in tempExpParameters:
                if expParameter in ['experimentType','experimentID','numTimepoints','plateOffset','numConditions']:
                    defaultValueDict[expParameter] = tempExpParameters[expParameter]
                elif expParameter == 'daysAgo':
                    timeDifference = datetime.today() - datetime.strptime(tempExpParameters['fullStart'],'%Y-%m-%d %a %I:%M %p') 
                    roundupDay = 0
                    if timeDifference.seconds > 0:
                        roundupDay = 1
                    defaultValueDict[expParameter] = timeDifference.days+roundupDay 
                elif expParameter in ['platePoseRestriction','blankColumns']:
                    bools = defaultValueDict[expParameter].copy() 
                    trueBools = []
                    for i,x in enumerate(defaultValueDict[expParameter]):
                        if expParameter == 'platePoseRestriction':
                            negation = not bools[int(x)-1]
                        else:
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
                allWidgetChecks = [experimentTypeVar.get(),incubatorPlatePosVar.get(),meridianVar.get(),minuteVar.get()]
                checkButtonChecks = [x.get() for x in coolingPlatePosVarList]
                allWidgetBools = [experimentNameEntry.get() != '']+[x != '  ' for x in allWidgetChecks]+[any(checkButtonChecks)]
                if all(allWidgetBools):
                    enterTpButton.config(state=tk.NORMAL)
                else:
                    enterTpButton.config(state=tk.DISABLED)
            except:
                enterTpButton.config(state=tk.DISABLED)
                
        tk.Label(mainWindow,text='Experiment type:').grid(row=0,column=0,sticky=tk.W)
        experimentTypeList = list(experimentTypeDict.keys()) 
        experimentTypeVar = tk.StringVar()
        experimentTypeDropdown = ttk.OptionMenu(mainWindow,experimentTypeVar,defaultValueDict['experimentType'],*experimentTypeList,command=lambda _: enableFinish())
        experimentTypeDropdown.grid(row=0,column=1,sticky=tk.W)
        
        tk.Label(mainWindow,text='Experiment name:').grid(row=1,column=0,sticky=tk.W)
        experimentNameEntry = ttk.Entry(mainWindow,width=20)
        experimentNameEntry.insert(tk.END, str(defaultValueDict['experimentID']))
        experimentNameEntry.grid(row=1,column=1,sticky=tk.W)
        experimentNameEntry.bind("<Key>",enableFinish)

        startPos = 4
        
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
        conditionNumberList =[16,24,32,48,56,64,72,80,88,96,128,192,256,288,384]
        conditionNumberVar = tk.IntVar()
        conditionNumberDropdown = ttk.OptionMenu(mainWindow,conditionNumberVar,defaultValueDict['numConditions'],*conditionNumberList,command=lambda _: disableIncubatorEntries())
        conditionNumberDropdown.grid(row=2,column=1,sticky=tk.W)
        
        #Disable racks that are already occupied
        plateDisablingRadius = math.ceil(defaultValueDict['numConditions']/96)-1
        for reservedRack in reservedRacks:
            for i in range(max(reservedRack-plateDisablingRadius,1),reservedRack+1):
                incubatorPlatePosDropdown['menu'].entryconfigure(i-1, state = "disabled")
        
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

        #tk.Label(mainWindow,text='Number of timepoints:').grid(row=startPos2,column=0,sticky=tk.W)
        #timepointNumberEntry = ttk.Entry(mainWindow,width=5)
        #timepointNumberEntry.grid(row=startPos2,column=1,sticky=tk.W)
        #timepointNumberEntry.insert(tk.END, str(defaultValueDict['numTimepoints']))
        
        tk.Label(mainWindow,text='Number of timepoints:').grid(row=startPos2,column=0,sticky=tk.W)
        timepointNumberVar = tk.IntVar()
        timepointNumberDropdown = ttk.OptionMenu(mainWindow,timepointNumberVar,str(defaultValueDict['numTimepoints']),*timepointNumberList)
        timepointNumberDropdown.grid(row=startPos2,column=1,sticky=tk.W)

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
            experimentParameters['experimentType'] = experimentTypeVar.get()
            experimentParameters['experimentID'] = experimentNameEntry.get()
            experimentParameters['plateOffset'] = incubatorPlatePosVar.get()
            experimentParameters['platePoseRestriction'] = [x+1 for x in range(4) if coolingPlatePosVarList[x].get()]
            experimentParameters['numConditions'] = conditionNumberVar.get()
            experimentParameters['blankColumns'] = [x+1 for x in range(12) if blankVarList[x].get()]
            #experimentParameters['numTimepoints'] = int(timepointNumberEntry.get())
            experimentParameters['numTimepoints'] = timepointNumberVar.get()
            experimentParameters['startTime'] = hourVar.get()+':'+minuteVar.get()+' '+meridianVar.get()
            experimentParameters['timepointlist'] = []
            experimentParameters['daysAgo'] = int(daysAgoEntry.get())
    
            now = datetime.today() - dt.timedelta(days=experimentParameters['daysAgo'])
            parsedStartTime = datetime.strptime(experimentParameters['startTime'],'%I:%M %p')
            fullStartTime = datetime(now.year,now.month,now.day,parsedStartTime.hour,parsedStartTime.minute)
            experimentParameters['fullStart'] = fullStartTime.strftime('%Y-%m-%d %a %I:%M %p')
            experimentParameters['addedToMatrix'] = False 

            master.switch_frame(TimepointEntryPage,expNum,experimentParameters)
        
        #disableTimepointEntries()

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
                6: [4, 10, 24, 32, 48, 72],
                8:[3,7,15,23,35,47,59,72],
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
            allExperimentParameters = pickle.load(open('allExperimentParameters.pkl','rb'))
            allExperimentParameters[expNum] = experimentParameters
            with open('allExperimentParameters.pkl','wb') as f:
                pickle.dump(allExperimentParameters,f)
            master.switch_frame(ExperimentHomePage)

        buttonWindow = tk.Frame(self)
        buttonWindow.pack(side=tk.TOP,pady=20)
        ttk.Button(buttonWindow, text="Finish",command=lambda: collectInputs()).pack(side=tk.LEFT)
        ttk.Button(buttonWindow, text="Back",command=lambda: master.switch_frame(ExperimentInfoPage,expNum)).pack(side=tk.LEFT)
        ttk.Button(buttonWindow, text="Quit",command=lambda: quit()).pack(side=tk.LEFT)

if __name__== "__main__":
    app = MainApp()
    app.mainloop()
