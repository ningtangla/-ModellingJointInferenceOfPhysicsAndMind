import sys
sys.path.append('../src')
sys.path.append('../env/xmls')
import unittest
import numpy as np
from ddt import ddt, data, unpack

# Local import
from envMujoco import Reset, TransitionFunction, IsTerminal


@ddt
class TestEnvMujoco(unittest.TestCase):
    def setUp(self):
        self.modelName = 'twoAgents'
        self.numAgent = 2
        self.killzoneRadius = 0.5
        self.isTerminal = IsTerminal(self.killzoneRadius)
        self.numSimulationFrames = 20

    @data(([0, 0, 0, 0], [0, 0, 0, 0], [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]), ([1, 2, 3, 4], [0, 0, 0, 0], [[1, 2, 1, 2, 0, 0], [3, 4, 3, 4, 0, 0]]), ([1, 2, 3, 4], [5, 6, 7, 8], [[1, 2, 1, 2, 5, 6], [3, 4, 3, 4, 7, 8]]))
    @unpack
    def testReset(self, qPosInit, qVelInit, groundTruthReturnedInitialState):
        reset = Reset(self.modelName, qPosInit, qVelInit, self.numAgent)
        returnedInitialState = reset()
        truthValue = returnedInitialState == groundTruthReturnedInitialState
        self.assertTrue(truthValue.all())

    @data((np.asarray([[1, 2, 1, 2, 0, 0], [4, 5, 4, 5, 0, 0]]), np.asarray([[1, 1], [1, 1]])), (np.asarray([[4, 7, 4, 7, 0, 0], [-4, -7, -4, -7, 0, 0]]), np.asarray([[-1, -1], [-1, -1]])), (np.asarray([[-6, 8, -6, 8, 0, 0], [6, -8, 6, -8, 0, 0]]), np.asarray([[-1, 1], [1, -1]])))
    @unpack
    def testQPositionChangesInDirectionOfActionAfterTransition(self, oldState, allAgentsActions):
        transitionFunction = TransitionFunction(self.modelName, self.isTerminal, False, self.numSimulationFrames)
        newState = transitionFunction(oldState, allAgentsActions)
        differenceBetweenStates = newState - oldState
        differenceBetweenQPositions = differenceBetweenStates[:, :2].flatten()
        hadamardProductQPosAndAction = np.multiply(differenceBetweenQPositions, allAgentsActions.flatten())
        truthValue = all(i > 0 for i in hadamardProductQPosAndAction)
        self.assertTrue(truthValue)

    @data((np.asarray([[1, 2, 1, 2, 0, 0], [4, 5, 4, 5, 0, 0]]), np.asarray([[1, 1], [1, 1]])), (np.asarray([[4, 7, 4, 7, 0, 0], [-4, -7, -4, -7, 0, 0]]), np.asarray([[-1, -1], [-1, -1]])), (np.asarray([[-6, 8, -6, 8, 0, 0], [6, -8, 6, -8, 0, 0]]), np.asarray([[-1, 1], [1, -1]])))
    @unpack
    def testXPosEqualsQPosAfterTransition(self, state, allAgentsActions):
        transitionFunction = TransitionFunction(self.modelName, self.isTerminal, False, self.numSimulationFrames)
        newState = transitionFunction(state, allAgentsActions)
        newXPos = newState[:, 2:4]
        newQPos = newState[:, :2]
        truthValue = newQPos == newXPos
        self.assertTrue(truthValue.all())

    @data((0.2, np.asarray([[0, 0, 0, 0, 0, 0], [1, 1, 1, 1, 0, 0]]), False), (1, np.asarray([[-0.5, -0.5, -0.5, -0.5, 0, 0], [0, 0, 0, 0, 0, 0]]), True), (0.5, np.asarray([[10, -10, 10, -10, 0, 0], [-10, 10, -10, 10, 0, 0]]), False))
    @unpack
    def testIsTerminal(self, minXDis, state, groundTruthTerminal):
        isTerminal = IsTerminal(minXDis)
        terminal = isTerminal(state)
        self.assertEqual(terminal, groundTruthTerminal)