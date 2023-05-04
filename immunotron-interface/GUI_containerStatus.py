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
import seaborn as sns

schedulePath = 'schedules/' 
matrixPath = 'matrices/'
finalInputPath = 'misc/'
if platform.system() == 'Windows':
    finalOutputPath = 'C:/ProgramData/Tecan/EVOware/database/variables/'
else:
    finalOutputPath = 'variables/'

incubatorPath = finalOutputPath+'incubatorStatus.txt'
fridgePath = finalOutputPath+'fridgeStatus.txt'

NUMEXP = 8

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
        self.switch_frame(ContainerStatusPage)

    def switch_frame(self, frame_class,*args):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self,*args)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack()

#Top level actions for experiments
class ContainerStatusPage(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self, master)
        mainWindow = tk.Frame(self)
        mainWindow.pack(side=tk.TOP,padx=10)
        
        #mainWindow.configure(bg="white")
        defaultbg = mainWindow.cget('bg')

        #5 columns, 24 rows
        #tk.Label(mainWindow,text='Container',font='-weight bold').grid(row=0,column=0)
        tk.Label(mainWindow,text='Tower:',font='-weight bold').grid(row=1,column=0,sticky=tk.W)
        tk.Label(mainWindow,text='Rack:',font='-weight bold').grid(row=2,column=0,rowspan=22,sticky=tk.W)

        tk.Label(mainWindow,text='Incubator',font='-weight bold').grid(row=0,column=1,columnspan=2,sticky=tk.W)
        tk.Label(mainWindow,text='Fridge',font='-weight bold').grid(row=0,column=3,columnspan=2,sticky=tk.W)

        tk.Label(mainWindow,text='1',font='-weight bold').grid(row=1,column=1,sticky=tk.EW)
        tk.Label(mainWindow,text='2',font='-weight bold').grid(row=1,column=2,sticky=tk.EW)
        tk.Label(mainWindow,text='1',font='-weight bold').grid(row=1,column=3,sticky=tk.EW)
        tk.Label(mainWindow,text='2',font='-weight bold').grid(row=1,column=4,sticky=tk.EW)

        self.incubatorTower1Labels,self.incubatorTower2Labels = [],[]
        self.fridgeLabels = ['-']*44
        for row in range(22):
            label = 22-row-1
            incTower1Label = tk.Label(mainWindow,text=str(label+1))#+':-')
            incTower1Label.grid(row=2+row,column=1,sticky=tk.EW)
            self.incubatorTower1Labels.append(incTower1Label)
            incTower2Label = tk.Label(mainWindow,text=str(label+1))#+':-')
            incTower2Label.grid(row=2+row,column=2,sticky=tk.EW)
            self.incubatorTower2Labels.append(incTower2Label)
            fridgeLabel1 = tk.Label(mainWindow,text=str(label+1))#+':-')
            fridgeLabel1.grid(row=2+row,column=3,sticky=tk.EW)
            self.fridgeLabels[22-row-1] = fridgeLabel1
            fridgeLabel2 = tk.Label(mainWindow,text=str(label+23))#+':-')
            self.fridgeLabels[44-row-1] = fridgeLabel2
            fridgeLabel2.grid(row=2+row,column=4,sticky=tk.EW)
        
        def updateContainerLabels():
            palette = sns.color_palette(sns.color_palette(),10).as_hex()
            incubatorStatus = np.loadtxt(finalOutputPath+'incubatorStatus.txt',delimiter=',')
            fridgeStatus = np.loadtxt(finalOutputPath+'fridgeStatus.txt',delimiter=',')
            incubatorLoadUnload = np.loadtxt(finalOutputPath+'incubatorLoadUnload.txt',delimiter=',')
            fridgeLoadUnload = np.loadtxt(finalOutputPath+'fridgeLoadUnload.txt',delimiter=',')
            for expSlot in range(NUMEXP):
                for row in range(22):
                    label = 22-row-1
                    if incubatorLoadUnload[expSlot] == 1:
                        if row+1 in list(incubatorStatus[expSlot]):
                            self.incubatorTower1Labels[label].configure(text=str(row+1),fg='white',bg=palette[expSlot])
                        else:
                            self.incubatorTower1Labels[label].configure(text=str(row+1),fg='black',bg=defaultbg)
                    else:
                        if row+1 in list(incubatorStatus[expSlot]):
                            self.incubatorTower1Labels[label].configure(text=str(row+1),fg='black',bg=defaultbg)
                for row in range(44):
                    label = 44-row-1
                    if fridgeLoadUnload[expSlot] == 1:
                        if row+1 in list(fridgeStatus[expSlot]):
                            self.fridgeLabels[row].configure(text=str(row+1),fg='white',bg=palette[expSlot])
                        else:
                            self.fridgeLabels[row].configure(text=str(row+1),fg='black',bg=defaultbg)
                    else:
                        if row+1 in list(fridgeStatus[expSlot]):
                            self.fridgeLabels[row].configure(text=str(row+1),fg='black',bg=defaultbg)

            self.after(2000, updateContainerLabels)

        updateContainerLabels()
        ttk.Separator(mainWindow, orient='vertical').place(relx=0.29, rely=0, relwidth=0.001, relheight=1)
        ttk.Separator(mainWindow, orient='vertical').place(relx=0.70, rely=0, relwidth=0.001, relheight=1)
        ttk.Separator(mainWindow, orient='horizontal').place(relx=0, rely=0.08, relwidth=1, relheight=0.001)
        buttonWindow = tk.Frame(self)
        buttonWindow.pack(side=tk.TOP,padx=10,pady=(10,10))
        quitButton = ttk.Button(buttonWindow, text="Quit",command=lambda: quit())
        quitButton.pack(side=tk.LEFT)

if __name__== "__main__":
    app = MainApp()
    app.mainloop()
