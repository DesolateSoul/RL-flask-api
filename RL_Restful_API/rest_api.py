import pickle
from flask import Flask, jsonify, abort, make_response, request
import random
import numpy as np
import torch
import torch.optim as optim
import torch.nn.functional as F
import logging

from model import ReplayMemory, Network, learning_rate, replay_buffer_size, minibatch_size, discount_factor, \
    interpolation_parameter,save_video_of_model

logging.basicConfig(filename='logs/logs.log',level=logging.DEBUG)

app = Flask(__name__)


class Agent:

    def __init__(self, state_size, action_size):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.state_size = state_size
        self.action_size = action_size
        self.local_qnetwork = Network(state_size, action_size).to(self.device)
        self.target_qnetwork = Network(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.local_qnetwork.parameters(), lr=learning_rate)
        self.memory = ReplayMemory(replay_buffer_size)
        self.t_step = 0

    def step(self, state, action, reward, next_state, done):
        self.memory.push((state, action, reward, next_state, done))
        self.t_step = (self.t_step + 1) % 4
        if self.t_step == 0:
            if len(self.memory.memory) > minibatch_size:
                experiences = self.memory.sample(100)
                self.learn(experiences, discount_factor)

    def act(self, state, epsilon=0.):
        state = torch.from_numpy(state).float().unsqueeze(0).to(self.device)
        self.local_qnetwork.eval()
        with torch.no_grad():
            action_values = self.local_qnetwork(state)
        self.local_qnetwork.train()
        if random.random() > epsilon:
            return np.argmax(action_values.cpu().data.numpy())
        else:
            return random.choice(np.arange(self.action_size))

    def learn(self, experiences, discount_factor):
        states, next_states, actions, rewards, dones = experiences
        next_q_targets = self.target_qnetwork(next_states).detach().max(1)[0].unsqueeze(1)
        q_targets = rewards + discount_factor * next_q_targets * (1 - dones)
        q_expected = self.local_qnetwork(states).gather(1, actions)
        loss = F.mse_loss(q_expected, q_targets)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        self.soft_update(self.local_qnetwork, self.target_qnetwork, interpolation_parameter)

    def soft_update(self, local_model, target_model, interpolation_parameter):
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(
                interpolation_parameter * local_param.data + (1.0 - interpolation_parameter) * target_param.data)


def launch_task(gravity, enable_wind, wind_power, turbulence_power, api):
    logging.info(f"Recieved task with gravity={gravity} enable_wind={enable_wind} wind_power={wind_power} "
                 f"turbulence_power={turbulence_power} api={api}")
    if api == 'v1.0':
        with open(f"models/base_agent.pkl", "rb") as fp:
            agent = pickle.load(fp)
        id = save_video_of_model(agent, enable_wind=bool(enable_wind), wind_power=float(wind_power),
                                 turbulence_power=float(turbulence_power))
        res_dict = {'Status': f'Video saved', 'ID': id}
        return res_dict
    else:
        res_dict = {'error': 'API doesnt exist'}
        return res_dict


@app.route('/lunar_lander/api/v1.0/getvideo', methods=['GET'])
def get_task():
    result = launch_task(request.args.get('gravity'), request.args.get('enable_wind'),
                         request.args.get('wind_power'), request.args.get('turbulence_power'), 'v1.0')

    return make_response(jsonify(result), 200)


@app.errorhandler(404)
def not_found(error):
    logging.warning('No such page')
    return make_response(jsonify({'code': 'PAGE_NOT_FOUND'}), 404)


@app.errorhandler(500)
def server_error(error):
    logging.debug('Error')
    return make_response(jsonify({'code': 'INTERNAL_SERVER_ERROR'}), 500)


if __name__ == '__main__':
    app.run(port=5001, debug=True)
