import math
import random
import pygame
import numpy as np
import pygame.gfxdraw

class Grid(object):
    def __init__(self, width, height, scale):
        self.width = width
        self.height = height
        self.scale = scale
        self.max_value = 0
        self.cols = math.ceil(width/scale)
        self.rows = math.ceil(height/scale)
        self.values = np.zeros(self.cols*self.rows)
        self.time = 0
        print('Grid layed out!')

    def getValueAtPosition(self,position):
        col = math.floor(position.x / self.scale)
        row = math.floor(position.y / self.scale)
        return self.values[row*self.cols + col]

    def getIndexForPosition(self,position):
        col = math.floor(position.x / self.scale)
        row = math.floor(position.y / self.scale)
        return row*self.cols + col

    def setValueAtPosition(self, value, position):
        col = math.floor(position.x / self.scale)
        row = math.floor(position.y / self.scale)
        self.values[row*self.cols + col] = value

    def update(self):
        self.time += 1


class Foodplane(Grid):
    def __init__(self, width, height, scale):
        super().__init__(width, height, scale)
        self.max_value = 300
        self.refill_rate = 1
        self.piles = []
        self.pileCount = 4
        self.pileTime = 250
        self.fill()
        self.changePiles()

    def update(self):
        super().update()
        self.refuling()
        if self.time%self.pileTime==0:
            self.changePiles()

    def changePiles(self):
        self.piles = []
        for i in range(self.pileCount):
            self.piles.append(math.floor(random.random()*(len(self.values)-1)))
        #print("PILES CHANGED TO:",self.piles)

    def refuling(self):
        # refuling the food map
        for i, value in enumerate(self.values):
            self.values[i] = min(value + self.refill_rate, self.max_value)
            if i in self.piles:
                self.values[i] = self.max_value

    def fill(self):
        ##fill gradient
        # tempOnset=self.max_value/(self.cols*self.rows)
        # temp = 0
        # for i,value in  enumerate(self.values):
        #     temp += tempOnset
        #     self.values[i] += temp
        ##fill max
        #self.values += self.max_value
        ##fill random
        self.values += random.random()*self.max_value/2

    def getColorForIndex(self, tile):
        value = self.values[tile]
        color = (110, 110, 130, ((value / self.max_value) * 255) / 3)
        if tile in self.piles:
            return (110, 110, 130, 190)
        return color

    def getTotalSupply(self):
        return int((sum(self.values) / (len(self.values) * self.max_value) * 100))

    def draw(self, window):
        for row in range(self.rows):
            for col in range(self.cols):
                color = self.getColorForIndex(row*self.cols +col)
                pygame.gfxdraw.box(window, pygame.Rect(col*self.scale, row*self.scale, self.scale, self.scale), color)


class DensityPlane(Grid):
    def __init__(self, width, height, scale):
        super().__init__(width, height, scale)
        self.values = [[] for k in range(self.cols * self.rows)]

    # def incrementValueAtPosition(self, position):
    #     #self.setValueAtPosition(self.getValueAtPosition(position)+1,position)
    #     col = math.floor(position.x / self.scale)
    #     row = math.floor(position.y / self.scale)
    #     self.values[row*self.cols + col] += 1

    def update(self, agentList):
        super().update()
        self.values = [[] for k in range(self.cols * self.rows)]
        for agent in agentList:
            self.values[self.getIndexForPosition(agent.position)].append(agent.position)

    def getColorForIndex(self, tile):
        value = len(self.values[tile])
        color = (200, 0, 0, min(value * 20,200))
        return color

    def draw(self, window):
        for row in range(self.rows):
            for col in range(self.cols):
                color = self.getColorForIndex(row*self.cols +col)
                pygame.gfxdraw.box(window, pygame.Rect(col*self.scale, row*self.scale, self.scale, self.scale), color)