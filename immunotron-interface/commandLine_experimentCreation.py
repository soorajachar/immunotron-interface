import pandas as pd
import pickle
from matrixGenerator import generateExperimentMatrix, combineExperiments
from utils import calculateIncubatorPositions, calculateFridgePositions

experimentProtocols = pickle.load(open('/Users/acharsr/Documents/immunotron-interface/immunotron-interface/experimentProtocols.pkl', 'rb'))
incubatorStatus = pickle.load(open('/Users/acharsr/Documents/immunotron-interface/immunotron-interface/incubatorStatus.pkl', 'rb'))
fridgeStatus = pickle.load(open('/Users/acharsr/Documents/immunotron-interface/immunotron-interface/fridgeStatus.pkl', 'rb'))

kwargs = {
    'experimentID':'test',
    'protocolParameters':experimentProtocols['Supernatant (Sooraj)'],
    'incubatorPositions':calculateIncubatorPositions(incubatorStatus, experimentProtocols['Supernatant (Sooraj)'], 2, 12),
    'fridgePositions':calculateFridgePositions(fridgeStatus, experimentProtocols['Supernatant (Sooraj)'], 2, [], 12),
    'numPlates':2,
    'blankColumns':[],
    'numTimepoints':12,
    'startTime':'1:00 PM',
    'daysAgo':0,
    'timepointlist':[1,3,6,12,18,24,30,36,42,48,60,72],
    'fullStart':'2022-06-06 Tue 01:35 PM',
    'addedToMatrix':False
}

kwargs2 = {
    'experimentID':'test2',
    'protocolParameters':experimentProtocols['Supernatant+Fix/Perm+SupTransfer (Madison)'],
    'incubatorPositions':calculateIncubatorPositions(incubatorStatus, experimentProtocols['Supernatant+Fix/Perm+SupTransfer (Madison)'], 1, 8),
    'fridgePositions':calculateFridgePositions(fridgeStatus, experimentProtocols['Supernatant+Fix/Perm+SupTransfer (Madison)'], 1, [9,10,11,12], 8),
    'numPlates':1,
    'blankColumns':[9,10,11,12],
    'numTimepoints':8,
    'startTime':'1:00 PM',
    'daysAgo':0,
    'timepointlist':[6,12,18,24,36,48,60,72],
    'fullStart':'2022-06-07 Tue 02:30 PM',
    'addedToMatrix':False
}
generateExperimentMatrix(True, **kwargs)
generateExperimentMatrix(True, **kwargs2)
with open('experimentParameters.pkl','wb') as f:
    pickle.dump({0:kwargs,1:kwargs2,2:{},3:{}},f)
combineExperiments(['test', 'test2'], [experimentProtocols['Supernatant (Sooraj)'], experimentProtocols['Supernatant+Fix/Perm+SupTransfer (Madison)']])
