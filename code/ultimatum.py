from abc import ABC, abstractmethod
from typing import *
import random
import numpy as np
from matplotlib import pyplot as plt


class Agent(ABC):
    def __init__(self):
        self.money = 0

    @abstractmethod
    def make_offer(self, recipient: 'Agent') -> float:
        pass

    def increment_money(self, amount):
        self.money += amount

    def play(self, offerer: 'Agent', amount: float) -> bool:
        accept = self.accept(offerer, amount)
        if accept:
            self.increment_money(amount)
            offerer.increment_money(1 - amount)
        return accept

    def reset(self):
        self.money = 0

    @abstractmethod
    def accept(self, offerer: 'Agent', amount: float) -> bool:
        pass

    @abstractmethod
    def copy(self):
        pass


class ConstantAgent(Agent):
    def __init__(self, offer: float, acceptance: float = None):
        """
        :param offer: What this agent will offer
        :param acceptance: The minimum amount this agent will accept
        """
        super().__init__()
        self.offer = offer
        self.acceptance = offer if acceptance is None else acceptance

    def make_offer(self, recipient: 'Agent') -> float:
        return self.offer

    def accept(self, offerer: 'Agent', amount: float) -> bool:
        return amount >= self.acceptance

    def copy(self):
        offer_mutate = np.random.choice([-0.01, 0, 0.01])
        accept_mutate = np.random.choice([-0.01, 0, 0.01])
        return ConstantAgent(self.offer + offer_mutate, self.acceptance + accept_mutate)

class AdaptingAgent(Agent):

    keys = [(None, None),
            (None, True),
            (None, False),
            (True, True),
            (True, False),
            (False, True),
            (False, False)]

    def __init__(self, offer_vals: List[float] = None, accept_vals: List[float] = None):
        """
        :param offer: What this agent will offer
        :param acceptance: The minimum amount this agent will accept
        """
        super().__init__()
        self.offer = 0
        self.acceptance = 0
        self.offer_vals = offer_vals
        self.accept_vals = accept_vals
        self.genotype = {'A': dict(zip(self.keys, self.accept_vals)), 'O': dict(zip(self.keys, self.offer_vals))}
        self.hist = (None, None)

    def make_offer(self, recipient: 'Agent'):
        self.offer += self.genotype['O'][self.hist]
        return self.offer

    def play(self, offerer: 'Agent', amount: float) -> bool:
        accept = self.accept(offerer, amount)
        if accept:
            self.increment_money(amount)
            offerer.increment_money(1 - amount)
        self.hist = self.hist[1], accept
        offerer.hist = offerer.hist[1], accept
        return accept

    def reset(self):
        super().reset()
        self.hist = None, None

    def accept(self, offerer: 'Agent', amount: float) -> bool:
        self.accept += self.genotype['A'][self.hist]
        return self.accept

    def copy(self):
        offer_mutate = self.mutate_vals(self.offer_vals)
        accept_mutate = self.mutate_vals(self.accept_vals)
        return AdaptingAgent(self, offer_mutate, accept_mutate)

    def mutate_vals(self, vals: List[float], prob=0.67) -> List[float]:
        if np.random.random() < prob_mutate:
            rand_idx = np.random.random(len(vals))
            vals[rand_idx] += np.random.choice([-0.01, 0.01])
        return vals


class Tournament:
    def __init__(self, n: int, agent_maker: Callable[[], Agent], iterations: int = 1, games_per_round: int = 10):
        """
        :param n: Number of agents to make
        :param agent_maker: Contructor to make an agent
        """
        self.agents = [agent_maker() for _ in range(n + (n % 2))]
        self.iterations = iterations
        self.games_per_round = games_per_round
        self.offer_list: List[float] = []
        self.num_accepts = 0
        self.instruments: List[Instrument] = []

    def reset_metrics(self):
        self.offer_list.clear()
        self.num_accepts = 0

    def plot_metrics(self):
        for instrument in self.instruments:
            instrument.plot()

    def step(self, randomize: bool = True):
        n = len(self.agents)
        pairs = np.arange(n)
        if randomize:
            np.random.shuffle(pairs)
        pairs = pairs.reshape((n // 2, 2))
        for offerer_index, recipient_index in pairs:
            offerer, recipient = self.agents[offerer_index], self.agents[recipient_index]
            for _ in range(self.iterations):
                offer = offerer.make_offer(recipient)
                self.num_accepts += 1 if recipient.play(offerer, offer) else 0
                self.offer_list.append(offer)

    def loop(self, rounds: int = 1):
        for i in range(rounds):
            for _ in range(self.games_per_round):
                self.step()
            self.update_instruments()
            self.reset_metrics()
            lowest = min(range(len(self.agents)), key=lambda i: self.agents[i].money)
            highest = max(range(len(self.agents)), key=lambda i: self.agents[i].money)
            self.agents[lowest] = self.agents[highest].copy()
            for a in self.agents:
                a.reset()
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
        return 'Opening'


class NicenessInstrument(Instrument):
    def measure(self, tour: Tournament):
        return tour.num_accepts / (len(tour.agents) * tour.iterations * tour.games_per_round)

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


def main():
    t = Tournament(1000, lambda: ConstantAgent(random.random()), games_per_round=1)
    t.instruments.append(OpeningInstrument())
    t.instruments.append(NicenessInstrument())
    t.instruments.append(FitnessInstrument())
    t.instruments.append(AcceptanceInstrument())
    t.loop(100000 // t.games_per_round)
    t.plot_metrics()


if __name__ == '__main__':
    main()
