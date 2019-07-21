import numpy as np
from functools import reduce


class AccumulateRewards:
    def __init__(self, decay, rewardFunction):
        self.decay = decay
        self.rewardFunction = rewardFunction

    def __call__(self, trajectory):
        rewards = [self.rewardFunction(state, action) for state, action, actionDist in trajectory]
        accumulateReward = lambda accumulatedReward, reward: self.decay * accumulatedReward + reward
        accumulatedRewards = np.array([reduce(accumulateReward, reversed(rewards[TimeT:])) for TimeT in range(len(rewards))])

        return accumulatedRewards


class AddValuesToTrajectory:
    def __init__(self, trajectoryValueFunction):
        self.trajectoryValueFunction = trajectoryValueFunction

    def __call__(self, trajectory):
        values = self.trajectoryValueFunction(trajectory)
        trajWithValues = [(s, a, dist, np.array([v])) for (s, a, dist), v in zip(trajectory, values)]

        return trajWithValues


class RemoveTerminalTupleFromTrajectory:
    def __init__(self, getTerminalActionFromTrajectory):
        self.getTerminalActionFromTrajectory = getTerminalActionFromTrajectory

    def __call__(self, trajectory):
        terminalAction = self.getTerminalActionFromTrajectory(trajectory)
        if terminalAction is None:
            return trajectory[:-1]
        else:
            return trajectory


class ProcessTrajectoryForPolicyValueNet:
    def __init__(self, actionToOneHot, agentId):
        self.actionToOneHot = actionToOneHot
        self.agentId = agentId

    def __call__(self, trajectory):
        processTuple = lambda state, actions, actionDist, value: \
            (np.asarray(state).flatten(), self.actionToOneHot(actions[self.agentId]), value)
        processedTrajectory = [processTuple(*triple) for triple in trajectory]

        return processedTrajectory


class PreProcessTrajectories:
    def __init__(self, addValuesToTrajectory, removeTerminalTupleFromTrajectory, processTrajectoryForNN):
        self.addValuesToTrajectory = addValuesToTrajectory
        self.removeTerminalTupleFromTrajectory = removeTerminalTupleFromTrajectory
        self.processTrajectoryForNN = processTrajectoryForNN

    def __call__(self, trajectories):
        trajectoriesWithValues = [self.addValuesToTrajectory(trajectory) for trajectory in trajectories]
        filteredTrajectories = [self.removeTerminalTupleFromTrajectory(trajectory) for trajectory in trajectoriesWithValues]
        processedTrajectories = [self.processTrajectoryForNN(trajectory) for trajectory in filteredTrajectories]

        return processedTrajectories


class ActionToOneHot:
    def __init__(self, actionSpace):
        self.actionSpace = actionSpace

    def __call__(self, action):
        oneHotAction = np.asarray([1 if (np.array(action) == np.array(
            self.actionSpace[index])).all() else 0 for index in range(len(self.actionSpace))])
        return oneHotAction
