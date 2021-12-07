import json
from abc import ABC, abstractmethod
from typing import *
import random
import numpy as np
from matplotlib import pyplot as plt
from agents import *


class Tournament:
    def __init__(self, n: int, agent_maker: Callable[[], Agent], iterations: int = 1, games_per_round: int = 10,
                 kills_per_round=10):
        """
        :param n: Number of agents to make
        :param agent_maker: Contructor to make an agent
        """
        self.agents = [agent_maker() for _ in range(n + (n % 2))]
        self.iterations = iterations
        self.games_per_round = games_per_round
        self.kills_per_round = kills_per_round
        self.offer_list: List[float] = []
        self.num_accepts = 0
        self.num_games = 0
        self.opening = OpeningInstrument()
        self.niceness = NicenessInstrument()
        self.acceptance = AcceptanceInstrument()
        self.fitness = FitnessInstrument()
        self.responses = [ResponseInstrument(True, True), ResponseInstrument(True, False),
                          ResponseInstrument(False, True), ResponseInstrument(False, False)]
        self.instruments = [self.opening, self.niceness, self.fitness, self.acceptance] + self.responses

    def reset_metrics(self):
        self.offer_list.clear()
        self.num_accepts = 0
        self.num_games = 0

    def plot_metrics(self):
        for instrument in self.instruments:
            instrument.plot()

    def play_game(self, offerer: Agent, recipient: Agent, logging: bool = False):
        offer = offerer.make_offer(recipient)
        accept = recipient.play(offerer, offer)
        if logging:
            print(offer, recipient.acceptance)
        self.num_accepts += 1 if accept else 0
        self.num_games += 1
        self.offer_list.append(offer)

    def step(self, randomize: bool = True, logging: bool = False):
        n = len(self.agents)
        pairs = np.arange(n)
        if randomize:
            np.random.shuffle(pairs)
        pairs = pairs.reshape((n // 2, 2))
        for offerer_index, recipient_index in pairs:
            offerer, recipient = self.agents[offerer_index], self.agents[recipient_index]
            if logging:
                print(f'Offerer: {offerer.genotype["O"]}')
                print(f'Recipient: {recipient.genotype["A"]}')
            for _ in range(self.iterations):
                self.play_game(offerer, recipient, logging=logging)
                self.play_game(recipient, offerer, logging=logging)
        if logging:
            print()

    def loop(self, rounds: int = 1):
        for i in range(rounds):
            for _ in range(self.games_per_round):
                self.step()  # logging=i == rounds - 1)
                self.acceptance.update(self)
                for agent in self.agents:
                    agent.reset()
            self.opening.update(self)
            self.niceness.update(self)
            self.fitness.update(self)
            for r in self.responses:
                r.update(self)
            self.reset_metrics()
            sort = sorted(range(len(self.agents)), key=lambda i: self.agents[i].money)
            lowest = sort[:self.kills_per_round]
            highest = sort[-1]
            for low in lowest:
                self.agents[low] = self.agents[highest].copy()
            for a in self.agents:
                a.money = 0
            if i % (rounds / 100) == 0:
                print(i)

    def update_instruments(self):
        for instrument in self.instruments:
            instrument.update(self)


class Instrument(ABC):
    def __init__(self):
        self.metrics = []

    @abstractmethod
    def title(self):
        pass

    @abstractmethod
    def measure(self, tour: Tournament):
        pass

    def update(self, tour: Tournament):
        self.metrics.append(self.measure(tour))

    def plot(self):
        plt.plot(self.metrics)
        plt.title(self.title())
        plt.show()


class OpeningInstrument(Instrument):
    def measure(self, tour: Tournament):
        return np.mean(tour.offer_list)

    def title(self):
        return 'Offer'


class NicenessInstrument(Instrument):
    def measure(self, tour: Tournament):
        return (tour.num_accepts / tour.num_games + np.mean(tour.offer_list)) / 2

    def title(self):
        return 'Niceness'


class AcceptanceInstrument(Instrument):
    def measure(self, tour: Tournament):
        return np.mean([a.acceptance for a in tour.agents])

    def title(self):
        return 'Acceptance Threshold'


class FitnessInstrument(Instrument):
    def measure(self, tour: Tournament):
        return np.mean([agent.money for agent in tour.agents])

    def title(self):
        return 'Fitness'


class ResponseInstrument(Instrument):
    def __init__(self, offer, accept):
        super().__init__()
        self.measure_offer = 'O' if offer else 'A'
        self.accept = accept

    def measure(self, tour: Tournament):
        return np.mean([sum(a.genotype[self.measure_offer][k] for k in a.genotype[self.measure_offer]\
                            if k[1] is not None and k[1] == self.accept) / 3 for a in tour.agents])

    def title(self):
        return f'{"Offer" if self.measure_offer == "O" else "Acceptance"} Response to {"Acceptance" if self.accept else "Rejection"}'


def rand_list(length: int) -> List[float]:
    return [random.random() - 0.5 for _ in range(length)]


def rand_adapt_agent():
    offer = rand_list(len(AdaptingAgent.keys))
    accept = rand_list(len(AdaptingAgent.keys))
    # print(offer, accept)
    return AdaptingAgent(offer, accept)


def main():
    t = Tournament(1000, lambda: rand_adapt_agent(),
                   games_per_round=10, kills_per_round=10, iterations=10)
    t.loop(1000000 // t.games_per_round // t.iterations)
    agents = []
    for a in t.agents:
        geno = {'A': {str(k): v for k, v in a.genotype['A'].items()},
                'O': {str(k): v for k, v in a.genotype['O'].items()}}
        # geno = {'offer': a.offer, 'acceptance': a.acceptance}
        agents.append(geno)
    dct = {'final_agents': geno}
    for instr in t.instruments:
        dct[instr.title().lower()] = tuple(instr.metrics)
    with open('data/adaptiveagentsswap.json', 'w') as file:
        file.write(json.dumps(dct))
    # t.step()
    t.plot_metrics()


def plot_data():
    titles = {'offer': 'Constant Agent: Offers',
              'niceness': 'Constant Agent: Niceness',
              'fitness': 'Constant Agent: Average Money',
              'acceptance threshold': 'Constant Agent: Amount to Accept'}
    ylabels = {'offer': 'Offer Amount',
               'niceness': 'Niceness',
               'fitness': 'Dollars',
               'acceptance threshold': 'Acceptance Threshold'}
    with open('data/constantagents.json', 'r') as file:
        data = json.loads(file.readline())
    for name, vals in data.items():
        if name == 'final_agents':
            continue
        plt.plot(vals)
        plt.title(titles[name])
        plt.xlabel('Iteration')
        plt.ylabel(ylabels[name])
        plt.show()


if __name__ == '__main__':
    main()
