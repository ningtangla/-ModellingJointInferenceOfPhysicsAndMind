import time
import sys
import os
DIRNAME = os.path.dirname(__file__)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
sys.path.append(os.path.join(DIRNAME, '..', '..'))
# import ipdb

import itertools as it
import numpy as np
from collections import OrderedDict, deque
import pandas as pd
from matplotlib import pyplot as plt
import mujoco_py as mujoco
import math

from src.constrainedChasingEscapingEnv.envMujoco import IsTerminal, TransitionFunction, ResetUniform
from src.constrainedChasingEscapingEnv.reward import RewardFunctionCompete
from exec.trajectoriesSaveLoad import GetSavePath, readParametersFromDf, LoadTrajectories, SaveAllTrajectories, \
    GenerateAllSampleIndexSavePaths, saveToPickle, loadFromPickle
from src.neuralNetwork.policyValueNet import GenerateModel, Train, saveVariables, sampleData, ApproximateValue, \
    ApproximatePolicy, restoreVariables
from src.constrainedChasingEscapingEnv.state import GetAgentPosFromState
from src.neuralNetwork.trainTools import CoefficientCotroller, TrainTerminalController, TrainReporter, LearningRateModifier
from src.replayBuffer import SampleBatchFromBuffer, SaveToBuffer
from exec.preProcessing import AccumulateMultiAgentRewards, AddValuesToTrajectory, RemoveTerminalTupleFromTrajectory, \
    ActionToOneHot, ProcessTrajectoryForPolicyValueNet
from src.algorithms.mcts import ScoreChild, SelectChild, InitializeChildren, Expand, MCTS, backup, establishPlainActionDist
from exec.trainMCTSNNIteratively.valueFromNode import EstimateValueFromNode
from src.constrainedChasingEscapingEnv.policies import stationaryAgentPolicy, HeatSeekingContinuesDeterministicPolicy
from src.episode import  SampleTrajectory, chooseGreedyAction
from exec.parallelComputing import GenerateTrajectoriesParallel,ExcuteCodeOnConditionsParallel



def main():
    dirName = os.path.dirname(__file__)

    numTrajectoriesToStartTrain = 1024
    sampleTrajectoryFileName = 'sampleMultiMCTSAgentResNetTrajCondtion.py'
    numCpuCores = os.cpu_count()
    numCpuToUse = int(0.8*numCpuCores)
    numCmdList = min(numTrajectoriesToStartTrain, numCpuToUse)
    generateTrajectoriesParallel = GenerateTrajectoriesParallel(sampleTrajectoryFileName, numTrajectoriesToStartTrain, numCmdList)
    trajectoryBeforeTrainPathParamters = {'iterationIndex': 0}
    # cmdList = generateTrajectoriesParallel(trajectoryBeforeTrainPathParamters)


    manipulatedVariables = OrderedDict()
    manipulatedVariables['numTrainStepEachIteration'] = [1,4,16]
    manipulatedVariables['numTrajectoriesPerIteration'] = [1,4,16]

    productedValues = it.product(*[[(key, value) for value in values] for key, values in manipulatedVariables.items()])
    parametersAllCondtion = [dict(list(specificValueParameter)) for specificValueParameter in productedValues]

    levelNames = list(manipulatedVariables.keys())
    levelValues = list(manipulatedVariables.values())
    modelIndex = pd.MultiIndex.from_product(levelValues, names=levelNames)
    toSplitFrame = pd.DataFrame(index=modelIndex)

    sampleTrajectoryFileName = 'multiAgentTrainResNetCondition.py'
    # sampleTrajectoryFileName = 'multiAgentTrainResNetConditionSerial.py'

    numCpuCores = os.cpu_count()
    numCpuToUse = len(parametersAllCondtion)
    numTrials = math.floor(numCpuToUse/len(parametersAllCondtion)) * 1
    trainResNNParallel = ExcuteCodeOnConditionsParallel(sampleTrajectoryFileName, numTrials, numCpuToUse)

    print("start")
    startTime = time.time()

    cmdList = trainResNNParallel(parametersAllCondtion)

    endTime = time.time()
    print("Time taken {} seconds".format((endTime - startTime)))



if __name__ == '__main__':
    main()
