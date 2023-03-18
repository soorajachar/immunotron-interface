import pickle,platform
import unittest
from utils import calculateIncubatorPositions, calculateFridgePositions


class TestUtils_EmptyUnit(unittest.TestCase):
    ''' Test that incubator, fridge position calculations work across experiment protocols for an empty unit'''
    finalInputPath = 'misc/'
    if platform.system() == 'Windows':
        finalOutputPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
    else:
        finalOutputPath = 'variables/'
    @classmethod
    def setUpClass(self):
        self.incubator = dict(zip(range(1,23), [None]*22))
        self.fridge = dict(zip(range(1,45), [None]*44))
        self.experimentProtocols = pickle.load(open(finalInputPath+'experimentProtocols.pkl', 'rb'))

    def test_incubator_supOnly_1Plate_12timepoints(self):
        incubatorPositions = calculateIncubatorPositions(self.incubator, self.experimentProtocols['Supernatant (Sooraj)'], 1, 12)
        self.assertEqual(len(incubatorPositions), 1, 'Incorrect number of positions returned')
        self.assertEqual(incubatorPositions, [1], 'Incorrected positions returned (should have been [1])')
    
    def test_fridge_supOnly_1Plate_12timepoints(self):
        fridgePositions = calculateFridgePositions(self.fridge, self.experimentProtocols['Supernatant (Sooraj)'], 1, [], 12)
        self.assertEqual(len(fridgePositions), 3, 'Incorrect number of positions returned')
        self.assertEqual(fridgePositions, [1,2,3], 'Incorrected positions returned (should have been [1,2,3])')
    
    def test_incubator_supOnly_2Plates_12timepoints(self):
        incubatorPositions = calculateIncubatorPositions(self.incubator, self.experimentProtocols['Supernatant (Sooraj)'], 2, 12)
        self.assertEqual(len(incubatorPositions), 2, 'Incorrect number of positions returned')
        self.assertEqual(incubatorPositions, [1,2], 'Incorrected positions returned (should have been [1,2])')
    
    def test_fridge_supOnly_2Plates_12timepoints(self):
        fridgePositions = calculateFridgePositions(self.fridge, self.experimentProtocols['Supernatant (Sooraj)'], 2, [], 12)
        self.assertEqual(len(fridgePositions), 6, 'Incorrect number of positions returned')
        self.assertEqual(fridgePositions, [1,2,3,4,5,6], 'Incorrected positions returned (should have been [1,2,3,4,5,6])')
        
    def test_incubator_supOnly_2Plates_13timepoints(self):
        incubatorPositions = calculateIncubatorPositions(self.incubator, self.experimentProtocols['Supernatant (Sooraj)'], 2, 13)
        self.assertEqual(len(incubatorPositions), 2, 'Incorrect number of positions returned')
        self.assertEqual(incubatorPositions, [1,2], 'Incorrected positions returned (should have been [1,2])')
    
    def test_fridge_supOnly_2Plates_13timepoints(self):
        fridgePositions = calculateFridgePositions(self.fridge, self.experimentProtocols['Supernatant (Sooraj)'], 2, [], 13)
        self.assertEqual(len(fridgePositions), 7, 'Incorrect number of positions returned')
        self.assertEqual(fridgePositions, [1,2,3,4,5,6,7], 'Incorrected positions returned (should have been [1,2,3,4,5,6,7])')
    
    def test_incubator_supFixPerm_1Plate_12timepoints(self):
        incubatorPositions = calculateIncubatorPositions(self.incubator, self.experimentProtocols['Supernatant+Fix/Perm (Madison)'], 1, 12)
        self.assertEqual(len(incubatorPositions), 12, 'Incorrect number of positions returned')
        self.assertEqual(incubatorPositions, list(range(1,13)), 'Incorrected positions returned (should have been [1])')
    
    def test_fridge_supFixPerm_1Plate_12timepoints(self):
        fridgePositions = calculateFridgePositions(self.fridge, self.experimentProtocols['Supernatant+Fix/Perm (Madison)'], 1, [5,6,7,8,9,10,11,12], 12)
        self.assertEqual(len(fridgePositions), 13, 'Incorrect number of positions returned')
        self.assertEqual(fridgePositions, list(range(1,14)), 'Incorrected positions returned (should have been [1,2,3,4,5,6,7,8,9,10,11,12,13])')

class TestUtils_FullUnit(unittest.TestCase):
    ''' Test that positions are assigned correctly when some slots are taken'''
    finalInputPath = 'misc/'
    if platform.system() == 'Windows':
        finalOutputPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
    else:
        finalOutputPath = 'variables/'
    @classmethod
    def setUpClass(self):
        self.incubator = dict(zip(range(1,23), [None]*22))
        self.fridge = dict(zip(range(1,45), [None]*44))
        for i in range(1,40):
            if i < 20:
                self.incubator[i] = 'Full'
            self.fridge[i] = 'Full'
        self.experimentProtocols = pickle.load(open(finalInputPath+'experimentProtocols.pkl', 'rb'))
    
    
    def test_incubator_supOnly_1Plate_12timepoints(self):
        incubatorPositions = calculateIncubatorPositions(self.incubator, self.experimentProtocols['Supernatant (Sooraj)'], 1, 12)
        self.assertEqual(len(incubatorPositions), 1, 'Incorrect number of positions returned')
        self.assertEqual(incubatorPositions, [20], 'Incorrected positions returned (should have been [20])')
    
    def test_fridge_supOnly_1Plate_12timepoints(self):
        fridgePositions = calculateFridgePositions(self.fridge, self.experimentProtocols['Supernatant (Sooraj)'], 1, [], 12)
        self.assertEqual(len(fridgePositions), 3, 'Incorrect number of positions returned')
        self.assertEqual(fridgePositions, [40,41,42], 'Incorrected positions returned (should have been [40,41,42])')
    
    def test_fridge_supOnly_2Plates_12timepoints(self):
        fridgePositions = calculateFridgePositions(self.fridge, self.experimentProtocols['Supernatant (Sooraj)'], 2, [], 12)
        self.assertFalse(fridgePositions, 'Incorrect (Should have returned False due to not enough slots)')
    
    def test_incubator_supOnly_4Plates_12timepoints(self):
        incubatorPositions = calculateIncubatorPositions(self.incubator, self.experimentProtocols['Supernatant (Sooraj)'], 4, 12)
        self.assertFalse(incubatorPositions, 'Incorrect (Should have returned False due to not enough slots)')
    
    def test_incubator_supOnly_3Plates_12timepoints(self):
        incubatorPositions = calculateIncubatorPositions(self.incubator, self.experimentProtocols['Supernatant (Sooraj)'], 3, 12)
        self.assertEqual(len(incubatorPositions), 3, 'Incorrect number of positions returned')
        self.assertEqual(incubatorPositions, [20,21,22], 'Incorrected positions returned (should have been [20,21,22])')

class TestUtils_ScatteredUnit(unittest.TestCase):
    ''' Test that positions are assigned correctly when some slots are taken'''
    finalInputPath = 'misc/'
    if platform.system() == 'Windows':
        finalOutputPath = 'C:/ProgramData/TECAN/EVOware/database/variables/'
    else:
        finalOutputPath = 'variables/'
    @classmethod
    def setUpClass(self):
        self.incubator = dict(zip(range(1,23), [None]*22))
        for i in range(1,10):
            self.incubator[i] = 'Full'
        for i in range(13,21):
            self.incubator[i] = 'Full'
        self.experimentProtocols = pickle.load(open(finalInputPath+'experimentProtocols.pkl', 'rb'))
    
    def test_incubator_supOnly_3Plates_12timepoints(self):
        incubatorPositions = calculateIncubatorPositions(self.incubator, self.experimentProtocols['Supernatant (Sooraj)'], 3, 12)
        self.assertEqual(len(incubatorPositions), 3, 'Incorrect number of positions returned')
        self.assertEqual(incubatorPositions, [10,11,12], 'Incorrected positions returned (should have been [10,11,12])')

    def test_incubator_supOnly_4Plates_12timepoints(self):
        incubatorPositions = calculateIncubatorPositions(self.incubator, self.experimentProtocols['Supernatant (Sooraj)'], 4, 12)
        self.assertEqual(len(incubatorPositions), 4, 'Incorrect number of positions returned')
        self.assertEqual(incubatorPositions, [10,11,12,21], 'Incorrected positions returned (should have been [10,11,12])')

if __name__ == '__main__':
    unittest.main()
