"""
training pipeline
"""
import os
import torch
import math
import torch.nn as nn
from model.network import RLNetwork, eval_step, train_step
from car_game.src.core.game import CarGame
from collections import deque
from model.config import *
import random
import pygame
import car_game.src.config.game as GAME_SETTING
from car_game.src.core.car import CarControlAction
from car_game.src.config.game import MAX_OBSERVATION
def main():
    '''
    if os.path.exists('model.pt'):
        print('load exist model')
        main_model = torch.load('model.pt')
        target_model = torch.load('model.pt')
    else:
    '''
    main_model = RLNetwork(LAYERS)
    target_model = RLNetwork(LAYERS)
    lr = LR
    optimizer = torch.optim.Adam(main_model.parameters(), lr=lr)
    loss_func = nn.MSELoss()
    game = CarGame()
    frame = 0
    D = deque()

    observation, reward, terminal = game.step(0, training=True)
    epsilon = RANDOM_EPSILON
    while True:
        game.render()
        pygame.time.delay(GAME_SETTING.GAME_STEP_INTERVAL)
        #observation, reward, terminal = game.step(0, training=True)
        if frame % STEP_FRAME == 0:
            #print('[train] step on frame {}'.format(frame))
            if random.random() < epsilon:
                action = random.randrange(ACTION_NUMBER)
                print('[train] random action {}'.format(ACTIONS[action]))
            else:
                action = torch.argmax(eval_step(main_model,observation)).item()
                #print('[train] action {}'.format(ACTIONS[action]))
        else:
            #pass
            action = 0
            #print('[train] pass frame {}'.format(frame))

        observation_old = observation
        reward_old = reward
        terminal_old = terminal
        car_action = CarControlAction.ACTION_IDLE
        if action == 0:
            car_action = CarControlAction.ACTION_IDLE
        if action == 1:
            car_action = CarControlAction.ACTION_TURN_LEFT
        if action == 2:
            car_action = CarControlAction.ACTION_TURN_RIGHT
        observation, reward, terminal = game.step(car_action, training=True)
        if terminal.value != 0:
            #print('[train] game end')
            game.reset()

        distance1 = max(observation[1], observation[3]) / (observation[1]+observation[3])
        distance2 = max(observation[0], observation[4]) / (observation[0]+observation[4])
        if reward >= 0:
            reward = 0
        if distance2 > 0.75:
            reward = -0.5
        #if distance2 > 0.7:
        #    reward = -1

        print(reward)
        D.append((observation_old, action, reward, observation, terminal))
        if len(D) > MEMORY:
            D.popleft()
        if frame >= OBSERVE:
            minibatch = random.sample(D, BATCH)

            s1_batch = []
            a_batch = []
            for i in range(len(minibatch)):
                s1_batch.append(minibatch[i][3])
                a_batch.append([minibatch[i][1]])

            y, _ = torch.max(eval_step(target_model, s1_batch), dim=1)
            y_batch = []
            s_batch = []
            for i in range(len(minibatch)):
                terminal = minibatch[i][-1]
                s_batch.append(minibatch[i][0])
                if terminal.value != 0:
                    y_batch.append([minibatch[i][2]])
                else:
                    y_batch.append([minibatch[i][2] + GAMMA * y[i].item()])
            loss = train_step(main_model, s_batch, a_batch, y_batch, optimizer, loss_func)
            print('[train] loss: {}'.format(loss.item()))
            if frame % SAVE_STEP == 0:
                if epsilon > RANDOM_EPSILON_MIN:
                    epsilon *= RANDOM_EPSILON_DECAY
                    print('[train] epsilon {}'.format(epsilon))
                state_dict = main_model.state_dict()
                target_model.load_state_dict(state_dict)
                torch.save(main_model, 'model.pt')
            if frame % DECAY_STEP == 0 and frame != 0:
                if lr > LR_MIN:
                    lr = lr * LR_GAMMA
                    for param_group in optimizer.param_groups:
                        param_group["lr"] = lr

        frame += 1


if __name__ == '__main__':
    main()








    pass

if __name__ == '__main__':
    print('training game AI')
