import sys
import pandas as pd

sys.path.append('../src/constrainedChasingEscapingEnv')
sys.path.append('../visualize')
sys.path.append('../src')


from envDiscreteGrid import *
from state import *
from policies import *
from analyticGeometryFunctions import computeAngleBetweenVectors

from discreteGridVisualization import *

from episode import MultiAgentSampleTrajectory

pd.set_option('display.max_columns', 50)


def main():

    rationalityParam = 0.9
    # actionSpace = [(-1, 0), (1,0), (0, 1), (0, -1), (0, 0)]

    actionSpace = [(-1, 0), (1,0), (0, 1), (0, -1)]

    gridSize = (10,10)
    iterationNumber = 50
    agentNames = ["Wolf", "Sheep", "Master"]


    lowerBoundAngle = 0
    upperBoundAngle = np.pi / 2

    getWolfProperAction = ActHeatSeeking(actionSpace, computeAngleBetweenVectors, lowerBoundAngle, upperBoundAngle)
    getSheepProperAction = ActHeatSeeking(actionSpace, computeAngleBetweenVectors, lowerBoundAngle, upperBoundAngle)


    wolfID = 0
    sheepID = 1
    masterID = 2
    positionIndex = [0,1] # [2, 0, 1] state = [sheepState, masterState, wolfState]

    getWolfPos = GetAgentPosFromState(wolfID, positionIndex)
    getSheepPos = GetAgentPosFromState(sheepID, positionIndex)
    getMasterPos = GetAgentPosFromState(masterID, positionIndex)

    getWolfPolicy = HeatSeekingDiscreteStochasticPolicy(rationalityParam, getWolfProperAction, getWolfPos, getSheepPos)
    getSheepPolicy = HeatSeekingDiscreteStochasticPolicy(rationalityParam, getSheepProperAction, getWolfPos, getSheepPos)
    getMasterPolicy = RandomPolicy(actionSpace)

    unorderedPolicy = [getWolfPolicy, getSheepPolicy, getMasterPolicy]
    agentID = [wolfID, sheepID, masterID]

    rearrangeList = lambda unorderedList, order: list(np.array(unorderedList)[np.array(order).argsort()])
    allAgentPolicy = rearrangeList(unorderedPolicy, agentID) # sheepPolicy, masterPolicy, wolfPolicy

    policy = lambda state: [getAction(state) for getAction in allAgentPolicy] # result of policy function is [sheepAct, masterAct, wolfAct]

    pulledAgentID = 0
    noPullAgentID = 1
    pullingAgentID = 2

    getPulledAgentPos = GetAgentPosFromState(pulledAgentID, positionIndex)
    getNoPullAgentPos = GetAgentPosFromState(noPullAgentID, positionIndex)
    getPullingAgentPos = GetAgentPosFromState(pullingAgentID, positionIndex)

    lowerGridBound = 1
    agentCount = 3
    reset = Reset(gridSize, lowerGridBound, agentCount)
    stayWithinBoundary = StayWithinBoundary(gridSize, lowerGridBound)

    distanceForceRatio = 20
    getPullingForceValue = GetPullingForceValue(distanceForceRatio)
    samplePulledForceDirection = SamplePulledForceDirection(computeAngleBetweenVectors, actionSpace, lowerBoundAngle, upperBoundAngle)

    getPulledAgentForce = GetPulledAgentForce(getPullingAgentPos, getPulledAgentPos, samplePulledForceDirection, getPullingForceValue)
    getAgentsForce = GetAgentsForce(getPulledAgentForce, pulledAgentID, noPullAgentID, pullingAgentID)

    transition = Transition(stayWithinBoundary, getAgentsForce)


    isTerminal = IsTerminal(getWolfPos, getSheepPos)

    getMultiAgentSampleTrajectory = MultiAgentSampleTrajectory(agentNames, iterationNumber, isTerminal, reset)

    trajectory = getMultiAgentSampleTrajectory(policy, transition)


    print(trajectory)
    print(len(trajectory))

    BLACK = (  0,   0,   0)
    WHITE = (255, 255, 255)

    BLUE =  (  0,   0, 255)
    PINK = ( 250,   0, 255)
    GREEN = (0, 255, 0)

    screenWidth = 800
    screenHeight = 800
    gridNumberX, gridNumberY = gridSize
    gridPixelSize = min(screenHeight// gridNumberX, screenWidth// gridNumberY)


    pointExtendTime = 100
    FPS = 60
    colorList = [BLACK,BLACK,BLACK]
    # colorList = [BLUE, PINK, GREEN]

    pointWidth = 10
    modificationRatio = 3


    modifyOverlappingPoints = ModifyOverlappingPoints(gridPixelSize, modificationRatio, checkDuplicates)
    drawCircles = DrawCircles(pointExtendTime, FPS, colorList , pointWidth, modifyOverlappingPoints)

    caption= "Game"
    initializeGame = InitializeGame(screenWidth, screenHeight, caption)

    gridColor = BLACK
    gridLineWidth = 3
    backgroundColor= WHITE
    drawGrid = DrawGrid(gridSize, gridPixelSize, backgroundColor, gridColor, gridLineWidth)
    # trajectory = [[(6, 2), (9, 2), (5, 4)], [(7, 3), (10, 2), (6, 3)], [(6, 2), (10, 2), (7, 2)], [(8, 2), (10, 2), (6, 1)], [(8, 2), (10, 2), (7, 1)], [(8, 2), (10, 3), (7, 1)], [(9, 1), (10, 3), (8, 2)], [(8, 2), (10, 3), (8, 2)], [(8, 3), (10, 3), (7, 2)], [(8, 3), (10, 3), (8, 1)], [(9, 2), (10, 3), (7, 2)], [(8, 3), (10, 3), (8, 1)], [(9, 2), (10, 3), (8, 1)], [(10, 1), (10, 4), (7, 2)], [(9, 2), (10, 5), (9, 2)], [(9, 3), (9, 5), (9, 3)], [(9, 4), (9, 6), (10, 3)], [(10, 5), (9, 7), (10, 3)], [(9, 4), (10, 7), (10, 4)], [(10, 5), (10, 7), (10, 4)], [(10, 5), (10, 8), (9, 5)], [(9, 6), (10, 9), (10, 4)], [(10, 7), (10, 9), (8, 4)], [(9, 8), (10, 10), (9, 3)], [(10, 7), (10, 10), (10, 4)], [(10, 7), (10, 10), (9, 5)], [(10, 7), (10, 10), (8, 6)], [(9, 8), (10, 10), (10, 6)], [(9, 8), (10, 10), (10, 6)], [(10, 9), (10, 9), (9, 7)]]
    drawPointsFromLocationDfandSaveImage = DrawPointsFromLocationDfAndSaveImage(initializeGame, drawGrid, drawCircles, gridPixelSize)
    drawPointsFromLocationDfandSaveImage(trajectory, iterationNumber, saveImage = True)


if __name__ == '__main__':
    main()

