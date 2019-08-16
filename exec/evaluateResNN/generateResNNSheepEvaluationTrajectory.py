import sys
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
dirName = os.path.dirname(__file__)
sys.path.append(os.path.join(dirName, '..', '..'))

import json
from collections import OrderedDict
import pickle
import pandas as pd
import time
import mujoco_py as mujoco
from matplotlib import pyplot as plt
import numpy as np

from src.constrainedChasingEscapingEnv.envMujoco import ResetUniform, IsTerminal, TransitionFunction
from src.algorithms.mcts import ScoreChild, SelectChild, InitializeChildren, Expand, MCTS, backup, \
    establishPlainActionDist, RollOut
from src.episode import SampleTrajectory, chooseGreedyAction
from src.constrainedChasingEscapingEnv.policies import stationaryAgentPolicy, HeatSeekingDiscreteDeterministicPolicy, \
    HeatSeekingContinuesDeterministicPolicy
from exec.trajectoriesSaveLoad import GetSavePath, LoadTrajectories, readParametersFromDf, loadFromPickle, GenerateAllSampleIndexSavePaths, SaveAllTrajectories, saveToPickle
from exec.evaluationFunctions import ComputeStatistics, GenerateInitQPosUniform

from src.neuralNetwork.policyValueResNet import GenerateModel, restoreVariables, ApproximatePolicy
from src.constrainedChasingEscapingEnv.measure import DistanceBetweenActualAndOptimalNextPosition, \
    ComputeOptimalNextPos, GetAgentPosFromTrajectory, GetStateFromTrajectory
from src.constrainedChasingEscapingEnv.state import GetAgentPosFromState
from src.constrainedChasingEscapingEnv.analyticGeometryFunctions import computeAngleBetweenVectors
from exec.trainMCTSNNIteratively.valueFromNode import EstimateValueFromNode
from src.constrainedChasingEscapingEnv.reward import RewardFunctionCompete, HeuristicDistanceToTarget
from exec.preProcessing import AccumulateRewards


def main():
    dirName = os.path.dirname(__file__)
    trajectoryDirectory = os.path.join(dirName, '..', '..', 'data', 'evaluateSupervisedLearning',
                                       'evaluateTrajectories')
    if not os.path.exists(trajectoryDirectory):
        os.makedirs(trajectoryDirectory)

    trajectoryExtension = '.pickle'
    trainMaxRunningSteps = 25
    trainNumSimulations = 100
    killzoneRadius = 2
    sheepId = 0
    trajectoryFixedParameters = {'agentId': sheepId, 'maxRunningSteps': trainMaxRunningSteps, 'numSimulations': trainNumSimulations}

    getTrajectorySavePath = GetSavePath(trajectoryDirectory, trajectoryExtension, trajectoryFixedParameters)

    parametersForTrajectoryPath = json.loads(sys.argv[1])
    startSampleIndex = int(sys.argv[2])
    endSampleIndex = int(sys.argv[3])
    parametersForTrajectoryPath['sampleIndex'] = (startSampleIndex, endSampleIndex)
    trajectorySavePath = getTrajectorySavePath(parametersForTrajectoryPath)

    if not os.path.isfile(trajectorySavePath):

        # Mujoco environment
        physicsDynamicsPath = os.path.join(dirName, '..', '..', 'env', 'xmls', 'twoAgents.xml')
        physicsModel = mujoco.load_model_from_path(physicsDynamicsPath)
        physicsSimulation = mujoco.MjSim(physicsModel)
        numAgents = 2
        agentIds = list(range(numAgents))

        sheepId = 0
        wolfId = 1
        xPosIndex = [2, 3]
        getSheepXPos = GetAgentPosFromState(sheepId, xPosIndex)
        getWolfXPos = GetAgentPosFromState(wolfId, xPosIndex)

        isTerminal = IsTerminal(killzoneRadius, getSheepXPos, getWolfXPos)

        numSimulationFrames = 20
        transit = TransitionFunction(physicsSimulation, isTerminal, numSimulationFrames)

        actionSpace = [(10, 0), (7, 7), (0, 10), (-7, 7), (-10, 0), (-7, -7), (0, -10), (7, -7)]
        numActionSpace = len(actionSpace)

        alivePenalty = 0.05
        deathBonus = -1
        rewardFunction = RewardFunctionCompete(alivePenalty, deathBonus, isTerminal)

        # neural network init and save path
        numStateSpace = 12
        regularizationFactor = 1e-4
        sharedWidths = [128]
        actionLayerWidths = [128]
        valueLayerWidths = [128]
        generateModel = GenerateModel(numStateSpace, numActionSpace, regularizationFactor)

        NNFixedParameters = {'agentId': sheepId, 'maxRunningSteps': trainMaxRunningSteps, 'numSimulations': trainNumSimulations}
        dirName = os.path.dirname(__file__)
        NNModelSaveDirectory = os.path.join(dirName, '..', '..', 'data', 'evaluateSupervisedLearning',
                                            'trainedResSheepModels','res4')
        NNModelSaveExtension = ''
        getNNModelSavePath = GetSavePath(NNModelSaveDirectory, NNModelSaveExtension, NNFixedParameters)

        depth = int(parametersForTrajectoryPath['depth'])
        resBlockSheep = 4
        sheepNNModel = generateModel(sharedWidths * depth, actionLayerWidths, valueLayerWidths, resBlockSheep)

        # generate a set of starting conditions to maintain consistency across all the conditions
        evalQPosInitNoise = 0
        evalQVelInitNoise = 0
        qVelInit = [0, 0, 0, 0]

        getResetFromQPosInitDummy = lambda qPosInit: ResetUniform(physicsSimulation, qPosInit, qVelInit, numAgents, evalQPosInitNoise, evalQVelInitNoise)

        evalNumTrials = 300
        generateInitQPos = GenerateInitQPosUniform(-9.7, 9.7, isTerminal, getResetFromQPosInitDummy)
        evalAllQPosInit = [generateInitQPos() for _ in range(evalNumTrials)]
        evalAllQVelInit = np.random.uniform(-8, 8, (evalNumTrials, 4))
        getResetFromTrial = lambda trial: ResetUniform(physicsSimulation, evalAllQPosInit[trial], evalAllQVelInit[trial],
                                                       numAgents, evalQPosInitNoise, evalQVelInitNoise)
        evalMaxRunningSteps = 25
        getSampleTrajectory = lambda trial: SampleTrajectory(evalMaxRunningSteps, transit, isTerminal,
                                                             getResetFromTrial(trial), chooseGreedyAction)
        allSampleTrajectories = [getSampleTrajectory(trial) for trial in range(evalNumTrials)]

        # save evaluation trajectories
        manipulatedVariables = json.loads(sys.argv[1])

        modelPath = getNNModelSavePath(manipulatedVariables)
        restoredSheepModel = restoreVariables(sheepNNModel, modelPath)
        sheepPolicy = ApproximatePolicy(restoredSheepModel, actionSpace)
        resBlockWolf = 0
        initWolfNNModel = generateModel(sharedWidths, actionLayerWidths, valueLayerWidths, resBlockWolf)
        wolfNNModelPath= os.path.join(dirName, '..', '..', 'data', 'evaluateSupervisedLearning',
                                            'wolfModel','killzoneRadius=0.5_maxRunningSteps=10_numSimulations=100_qPosInitNoise=9.7_qVelInitNoise=5_rolloutHeuristicWeight=0.1_trainSteps=99999')
        restoredWolfModel = restoreVariables(initWolfNNModel, wolfNNModelPath)

        wolfPolicy = ApproximatePolicy(restoredWolfModel, actionSpace)
        policy = lambda state: [sheepPolicy(state), wolfPolicy(state)]

        beginTime = time.time()
        trajectories = [sampleTrajectory(policy) for sampleTrajectory in allSampleTrajectories[startSampleIndex:endSampleIndex]]
        processTime = time.time() - beginTime
        saveToPickle(trajectories, trajectorySavePath)
        restoredSheepModel.close()
        restoredWolfModel.close()


if __name__ == '__main__':
    main()
