import sys
import os
import mujoco_py as mujoco
import numpy as np

DIRNAME = os.path.dirname(__file__)
sys.path.append(os.path.join(DIRNAME, '..','..'))

from src.constrainedChasingEscapingEnv.envMujoco import IsTerminal, TransitionFunction
from src.constrainedChasingEscapingEnv.state import GetAgentPosFromState

def main():
    dirName = os.path.dirname(__file__)
    physicsDynamicsPath = os.path.join(dirName, 'twoAgentsTwoObstacles3.xml')
    physicsModel = mujoco.load_model_from_path(physicsDynamicsPath)
    physicsSimulation = mujoco.MjSim(physicsModel)

    # physicsSimulation.model.body_mass[8] = 30

    physicsSimulation.model.geom_friction[:,0] = 0.15

    physicsSimulation.set_constants()
    physicsSimulation.forward()

    # physicsSimulation.data.qpos[:] = np.array(init).flatten()


    qPos=np.array([-5.5, -5, 5, 0]).flatten()
    physicsSimulation.data.qpos[:] = qPos
    physicsSimulation.step()


    physicsViewer = mujoco.MjViewer(physicsSimulation)
    numSimulationFrames = 1500
    totalMaxVel = 0
    print(physicsSimulation.data.qvel, '!!!')
    print(physicsSimulation.data.qpos, '~~~')
    print(physicsSimulation.data.body_xpos, '...')
    for frameIndex in range(numSimulationFrames):
        if frameIndex == 550 or frameIndex == 600:
            print(physicsSimulation.data.ctrl[:], '###')
            print(physicsSimulation.data.qvel, '!!!')
            print(physicsSimulation.data.qpos, '~~~')
            print(physicsSimulation.data.body_xpos, '...')
        if frameIndex % 20 ==   0 and frameIndex > 200:
            action = np.array([7,7, -10, 0])
            physicsSimulation.data.ctrl[:] = action
        if frameIndex % 1 == 0 and frameIndex > 500:
            action = np.array([7, 7, -10,0])
            physicsSimulation.data.ctrl[:] = action

            physicsSimulation.data.ctrl[:] = action
        vels = physicsSimulation.data.qvel
        #maxVelInAllAgents = vels[2]
        # maxVelInAllAgents = max([np.linalg.norm(vels[i:i+3]) for i in range(3)])
        # if maxVelInAllAgents > totalMaxVel:
        #     totalMaxVel = maxVelInAllAgents
        physicsSimulation.step()
        physicsSimulation.forward()
        physicsViewer.render()

    print(totalMaxVel)


    # baselinePhysicsViewer = mujoco.MjViewer(baselinePhysicsSimulation)
    # numSimulationFrames = 0
    # for frameIndex in range(numSimulationFrames):
    #     #action = np.array([0] * 24)
    #     #baselinePhysicsSimulation.data.ctrl[:] = action
    #     baselinePhysicsSimulation.step()
    #     baselinePhysicsSimulation.forward()
    #     baselinePhysicsViewer.render()

if __name__ == '__main__':
    main()
