import json
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
                offer = offerer.make_offer(recipient)
                accept = recipient.play(offerer, offer)
                if logging:
                    print(offer, recipient.acceptance)
                self.num_accepts += 1 if accept else 0
                self.num_games += 1
                self.offer_list.append(offer)
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
            lowest = sort[:10]
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
                   games_per_round=10, iterations=10)
    t.loop(10000000 // t.games_per_round // t.iterations)
    agents = []
    for a in t.agents:
        geno = {'A': {str(k): v for k, v in a.genotype['A'].items()},
                'O': {str(k): v for k, v in a.genotype['O'].items()}}
        agents.append(geno)
    dct = {'final_agents': geno}
    for instr in t.instruments:
        dct[instr.title().lower()] = tuple(instr.metrics)
    with open('data/adaptiveagents.json', 'w') as file:
        file.write(json.dumps(dct))
    # t.step()
    t.plot_metrics()


def plot_data():
    with open('data/adaptiveagents.json', 'r') as file:
        data = json.loads(file.readline())
    for name, vals in data.items():
        if name == 'final_agents':
            continue
        plt.plot(vals)
        plt.title(name)
        plt.show()
    fit = np.array(data['fitness'])
    nice = np.array(data['niceness'])
    print(np.sum(np.abs(fit / 100 - nice)))


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


if __name__ == '__main__':
    main()
