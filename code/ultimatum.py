from abc import ABC, abstractmethod
from typing import *
import random
import numpy as np


class Agent(ABC):
    def __init__(self):
        self.money = 0

    @abstractmethod
    def offer(self, recipient: 'Agent') -> float:
        pass

    def increment_money(self, amount):
        self.money += amount

    def play(self, offerer: 'Agent', amount: float) -> bool:
        accept = self.accept(offerer, amount)
        if accept:
            self.increment_money(amount)
            offerer.increment_money(1 - amount)
        return accept

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

    def offer(self, recipient: 'Agent') -> float:
        return self.offer

    def accept(self, offerer: 'Agent', amount: float) -> bool:
        return amount >= self.acceptance

    def copy(self):
        return ConstantAgent(self.offer, self.acceptance)


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

    def step(self, randomize: bool = True):
        n = len(self.agents)
        pairs = np.arange(n)
        if randomize:
            np.random.shuffle(pairs)
        pairs = pairs.reshape((n // 2, 2))
        for offerer, recipient in pairs:
            for _ in range(self.iterations):
                offer = offerer.offer(recipient)
                self.num_accepts += 1 if recipient.play(offerer, offer) else 0
                self.offer_list.append(offer)

    def loop(self, rounds: int = 1):
        for _ in range(rounds):
            for _ in range(self.games_per_round):
                self.step()
                self.update_instruments()
                self.reset_metrics()
            lowest = min(range(len(self.agents)), key=lambda i: self.agents[i].money)
            highest = max(range(len(self.agents)), key=lambda i: self.agents[i].money)
            self.agents[lowest] = self.agents[highest].copy()
            for a in self.agents:
                a.money = 0

    def update_instruments(self):
        for instrument in self.instruments:
            instrument.update(self)


class Instrument(ABC):
    def __init__(self):
        self.metrics = []

    @abstractmethod
    def measure(self, tour: Tournament):
        pass

    def update(self, tour: Tournament):
        self.metrics.append(self.measure(tour))


class OpeningInstrument(Instrument):
    def measure(self, tour: Tournament):
        return np.mean(tour.offer_list)


class NicenessInstrument(Instrument):
    def measure(self, tour: Tournament):
        return tour.num_accepts


def main():
    t = Tournament(50, lambda: ConstantAgent(random.random()))
