from abc import ABC, abstractmethod
import random
import numpy as np
from typing import *


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
        # print(amount, accept)
        return accept

    def reset(self):
        return

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
        self.offer = 0.5
        self.acceptance = 0.5
        self.offer_vals = offer_vals
        self.accept_vals = accept_vals
        self.genotype = {'A': dict(zip(self.keys, self.accept_vals)), 'O': dict(zip(self.keys, self.offer_vals))}
        self.hist = (None, None)

    def make_offer(self, recipient: 'Agent'):
        self.offer += self.genotype['O'][self.hist]
        self.offer = min(max(self.offer, 0), 1)
        return self.offer

    def play(self, offerer: 'Agent', amount: float) -> bool:
        accept = super().play(offerer, amount)
        self.hist = self.hist[1], accept
        offerer.hist = offerer.hist[1], accept
        return accept

    def reset(self):
        super().reset()
        self.hist = None, None
        self.offer, self.acceptance = 0.5, 0.5

    def accept(self, offerer: 'Agent', amount: float) -> bool:
        self.acceptance += self.genotype['A'][self.hist]
        self.acceptance = min(max(self.acceptance, 0), 1)
        return self.acceptance <= amount

    def copy(self):
        offer_mutate = self.mutate_vals(self.offer_vals)
        accept_mutate = self.mutate_vals(self.accept_vals)
        return AdaptingAgent(offer_mutate, accept_mutate)

    def mutate_vals(self, vals: List[float], prob=0.2) -> List[float]:
        for i in range(len(vals)):
            if np.random.random() < prob:
                vals[i] += (np.random.random() - 0.5) / 20
        return vals


class AlwaysAccept(ConstantAgent):
    def __init__(self):
        super().__init__(random.random(), 0)

    def copy(self):
        return AlwaysAccept()


class Alternate(Agent):
    def __init__(self):
        super().__init__()
        self.will_accept = True
        self.offer = random.random()

    @property
    def acceptance(self):
        return 0 if self.will_accept else 1

    def accept(self, offerer: 'Agent', amount: float) -> bool:
        self.will_accept = not self.will_accept
        return self.will_accept

    def make_offer(self, recipient: 'Agent') -> float:
        return self.offer

    def copy(self):
        a = Alternate()
        a.offer = self.offer
        return a


class Random(Agent):
    def __init__(self, prob_accept=0.5):
        super().__init__()
        self.prob_accept = prob_accept

    @property
    def acceptance(self):
        return 0

    def accept(self, offerer: 'Agent', amount: float) -> bool:
        return random.random() < self.prob_accept

    def make_offer(self, recipient: 'Agent') -> float:
        return random.random()

    def copy(self):
        return Random(self.prob_accept)
