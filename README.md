# Evolution Simulation
> a simulation of artificial evolution

This program simulates agents that are equipped with several sensors and actions that conected through an
artificial neural network which is unique for every single angent. The weights of the feed forward net are updates through an evolutionary algorithm with the age of the agent as an implicit fitness function.

## Prerequisites

To run simulation.py, pygame and numpy need to be installed.

```
$ pip install pygame
$ pip install numpy 
```

## Explanation

![](/screenshots/ls1.gif?raw=true "Optional Title")

The agents live on a grid of food, which partly gets consumed on the position where an agent is passing over it. 
When doing so, the agent replenishes health which he loses constantly or through special interactions. 
Once an agent's health reaced 0, it dies.
In evenry frame, every agent has a chance to reproduce.
Reproduction can happen sexually (only possible when agents collide) or asexually. The offspring shares the dna of its parent or a mix of the dna of its parents in the former case (cross-over). The offspring's dna also has a chance to mutate individual genes. 
Agent with similar dna belong to a certain clan, which also defines their names. New clans can emerge when the distance between parent and child dna exceeds are certain threshold. 

Aside from the main simulation arem the program has the informative sections:
- the population graph (bottom): shows the amount of food in the world and the numer of agents over time 
- the agent ranking (top right): lists the oldest agents and a ranking of the most successful clans
- the agent's brain (right): shows the neural network weights of a representative agent from the dominant clan

### The Agents

![](/screenshots/ls4.jpg?raw=true "Optional Title")

Agent are equipped with 13 sensors that form the input variable for the neural network:

1. _health_: the current health percentage (also mirrored in the agents color intensity)
2. _speed_: the current speed (relative to max_speed)
3. _center_food_: the amount of food on the tile just below the agent
4. _feel_right_food_: the amount of food on the tile below the agents right feeler
5. _feel_left_food_: -analogous-
6. _proximity_right_: inverse of the distance to the closest other agent on the right side (normlized by the sensing range)
7. _red_right_: the amount of red shown by the agent that is closest on the right side
8. _green_right_: the amount of green shown by the agent that is closest on the right side
9. _proximity_left_: -analogous-
10. _red_left_: -analogous-
11. _green_left_: -analogous-
12. _ear_back_: the sum of inverse distances of other agents behind the agent. Capped on a set maximum value.
13. _collision_: binary signal of weather or not the agent collides with another

According to the sensory input and it's brain, an agent will show certain output values:

1. _torque_: the angle of further movement 
2. _acceleration_: the movement speed for the next frame
3. _spike_: the spike length - defines the agents strength, but increases it's ressource costs
4. _aggressivness_: defines what happens when the agent collides. Makes the agent more red.
5. _altruisticness_: defines what happens when the agent collides. Makes the agent more green.

Allowing agents to "choose" between being aggressive and altruistic, aims to have different survival strategies emerging. 
Aggressive agents bite on collision, while altruistic agents transfuse health to the one they collide with. The amout of bitten or tranfused health depends on an agents spike size/power.

## Parameters to explore

Several agent agnostic parameters may be changed within the agents '__init__()' and 'setPheno()' methods to further generate interesting evolution.
```python
def __init__(...):
  [...]
  self.power = 3  
  self.max_age = 7000           
  self.asexual_reproduction_rate = 0.002
  self.sexual_reproduction_rate = 0.006
  self.metabolism = 1                       
  self.reproduction_cost = 0
  [...]

def setPheno(self):
    self.max_health = 50*self.size
    self.health = self.max_health / 1.5  # self.reproduction_cost * 2
    self.bitesize = self.size * 2
    self.energyefficiency = 400 / (self.size * self.size)
    self.max_velocity = 1000 / (self.size * self.size)
    self.max_acceleration = 200 / (self.size * self.size)
```

One might also change what exactly happens when two agents collide within the agents 'collide()' method, to observe how this in turn affects the agents behavioral evolution.
```python
def collide(self):
      self.collission = 1 if self.collisionList else 0
      for otherAgent in self.collisionList:
          ## plain damage
          #self.health -= 25

          ## instant death
          #self.health = -100

          ## only the faster one bites
          #if self.velocity > otherAgent.velocity:
          #    self.bite(otherAgent)

          #both transfuse and bite
          self.bite(otherAgent)
          self.transfuse(otherAgent)
```
## Meta

Philipp Skudlik 

[https://github.com/pskugit](https://github.com/pskugit/)

