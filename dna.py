import sys
import math
import string
import random
import numpy as np
from util import *

class archType:
    def __init__(self, id, name, values):
        self.id = id
        self.name = name
        self.values = values
        self.count = 1
        print("NEW ARCHTYPE! Let us introduce the %s clan!"%(self.name))

    def update(self,values):
        self.values = (self.values*0.95 + values*0.05)

class Dna:
    def __init__(self, parents, archTypes, dnaLength):
        self.mutationRate = 0.05                  #chance for a gene to mutate
        self.mutationSeverity = 0.8               #1: 100% random mutation    0: 100% parental gene expression
        self.archTypeThreshold = 0.1              #how mach MAE is tolerated to still classify as that archtype
        self.values = np.zeros(dnaLength, dtype=float)
        self.archTypeRef = 0

        if not parents:
            #make random DNA
            for i in range(dnaLength):
                self.values[i] = random.random()*20 -10
            #make archtype
            id = len(archTypes.keys()) if len(archTypes.keys()) == 0 else max(archTypes.keys())+1
            archTypes[id] = archType(id,generate_word(2),self.values)
            self.archTypeRef = id
        else:                                   #there are parents
            if parents[0] == parents[1]:
                print("SELF REPRODUCTION %s  ---  %s" % (parents[0].name.toString(), parents[0].dna.readable()))
                self.values = np.copy(parents[0].dna.values)
            ###Crossover
            else:
                print("CROSSOVER %s : %s  ---  %s : %s"%(parents[0].name.toString(), parents[1].name.toString(),parents[0].dna.readable(), parents[1].dna.readable()))
                self.values = self.crossOver(parents[0].dna,parents[1].dna)
            ###MUTAITION
            mutations = 0
            for i in range(dnaLength):
                #if mutation occurs
                if random.random() < self.mutationRate:
                    mutations += 1
                    #self.values[i] =  self.values[i]*(1-self.mutationSeverity) + (random.random()*2 -1)*self.mutationSeverity                  #clipped weights
                    mutation = (random.random() * 20 - 10) * self.mutationSeverity
                    self.values[i] += mutation                                                       #free weights
                    print("MUTATTION of gene %d, with %f to %f"%(i, mutation, self.values[i]))
            if mutations > 0:
                print("%d Mutations in new genome of size %d."%(mutations, len(self.values)))
            #check if new dna creation is an archtype
            #parentDifference1 = self.mae(archTypes[parents[0].dna.archTypeRef].values)             #Compare with archtype
            #parentDifference2 = self.mae(archTypes[parents[1].dna.archTypeRef].values)
            parentDifference1 = self.mpe(parents[0].dna.values)             #Compare with archtype
            parentDifference2 = self.mpe(parents[1].dna.values)
            min_diff_parent = parents[1] if parentDifference1 > parentDifference2 else parents[0]
            print("parentDifference %f , %f for  %s and %s at threshold of %f" % (parentDifference1, parentDifference2,
                    parents[0].name.toString(), parents[1].name.toString(),  self.archTypeThreshold ))

            if parentDifference1 < self.archTypeThreshold or parentDifference2 < self.archTypeThreshold :
                self.archTypeRef = min_diff_parent.dna.archTypeRef
                archTypes[self.archTypeRef].update(self.values)
                archTypes[self.archTypeRef].count += 1
            else:
                #setup new archtype
                #appened to archTypes
                archType_name = parents[0].name.firstname + parents[1].name.firstname
                # make archtype
                id = len(archTypes.keys()) if len(archTypes.keys()) == 0 else max(archTypes.keys())+1
                archTypes[id] = archType(id, archType_name, self.values)
                self.archTypeRef = id

    def mae(self, values):
        return np.average(np.absolute(self.values - values))

    def mpe(self, values):
        absdifference =  np.absolute(self.values - values)
        return np.average(absdifference/np.absolute(values))

    def crossOver(self, dna1, dna2):
        if dna1.length() == dna2.length():
            values = []
            for i in range(dna1.length()):
                if random.random() < 0.5:
                    values.append(dna1.values[i])
                else:
                    values.append(dna2.values[i])
        return np.array(values)

    def readable(self):
        return str(["{0:.2f}".format(a) for a in self.values])

    def length(self):
        return len(self.values)

    def iter(self):
        return (value for value in self.values)