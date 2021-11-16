# Evolution of Iterative Ultimatum Game

### Neel Dhulipala, Ben Morris

## Abstract

In this project, we plan on exploring an iterative version of the Ultimatum Game. The Ultimatum Game is a game between two players where there is a certain amount of money that needs to be split between two players, and the first proposes a way to split the money. If the second accepts, the players split the money according to the offer. Otherwise, neither player gets any money. Here, we explore an iterative version of this game, where players have some rudimentary memory and can change how they play based on previous interactions with players.

## Annotated Bibliography

[Altruism may arise from individual selection](https://arxiv.org/pdf/q-bio/0403023.pdf)

Added By Hazel Smith 

Sánchez, A., & Cuesta, J. A. (2005). Altruism may arise from individual selection. Journal of theoretical biology, 235(2), 233-240. 

The authors of this paper suggest a model to explain altruism using the ultimatum game. The Ultimatum Game goes as follows: two players need to decide how to split M dollars. One of them is assigned to make an offer of how to split the money and the other chooses whether to accept that offer. If they refuse the offer, then neither player receives anything. In this paper the authors suggest a selection model with N players. Each player will have a threshold value of how much money they need to be offered to accept the offer / how much money they will offer. In each time step players are randomly partnered off and play the ultimatum game. In some of the timesteps players with the least amount of money die and those with the most duplicate themselves. Mutation can also occur. The authors found that players tended to evolve towards being more cooperative.

## Replication

Create an agent-based model where each agent has two values: an acceptance threshold and an offer value. In a game between two agents, the first agent will offer an amount of money that corresponds with their offer value. If it is higher than the receiver’s acceptance threshold, the receiver accepts; otherwise it rejects, and neither gets any money. The fitness of each agent is represented by the amount of money each player has after a certain number of games. Each loop, after a certain number of games are played, the agent with the lowest fitness is discarded, and replaced by a clone of the agent of highest fitness with some variability in their two parameters. The agents have no memory of previous games or information about the players they are playing against.

## Extension

We hope to extend this model by creating genotypes based on memory; agents will play multiple rounds against each other and can use information from previous rounds to influence their decisions.

## Results

We expect fitness over time to increase, along with cooperation, which can be represented by overall larger offers. This is because learning more about the other players in the group should lead to cooperation faster.

## Concerns

We need to figure out a clean way to represent the genotype; this was possible with the Prisoner’s Dilemma since it was a binary system, and possible with the non-iterative Ultimatum since there was no need for memory (i.e. nothing changed), but having both memory and a continuous range of values means the genotype must be more complicated.

## Next Steps

Over the next week, we will be working on implementing the original experiment and learning about the different parameters that can affect agents and the game overall. 
