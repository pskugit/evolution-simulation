import sys
import math
import string
import random
import numpy as np

def sigmoid(x):
    return 1/ (1+ math.exp(-x))

def tanh(x):
    return 2 * sigmoid(2*x) -1

def generate_word(length):
    VOWELS = "aeiou"
    CONSONANTS = "".join(set(string.ascii_lowercase) - set(VOWELS))
    word = ""
    for i in range(length):
        if i % 2 == 0:
            word += random.choice(CONSONANTS)
        else:
            word += random.choice(VOWELS)
    return word

class name:
    def __init__(self, archTypeName):
        self.firstname = generate_word(2)
        self.lastname = archTypeName
    def toString(self):
        return self.firstname+"_"+self.lastname

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def toTuple(self):
        return (int(self.x),int(self.y))

    def minus(self, position):
        return Position(self.x -position.x, self.y - position.y)

    def wrapEdge(self, win_width, win_height):
        wrappedx = (self.x % win_width) - 1
        wrappedy = (self.y % win_height) - 1
        return Position(wrappedx,wrappedy)

    def eucDistanceTo(self, position):
        return math.sqrt(abs(self.x - position.x)**2 +abs(self.y - position.y)**2)

def dictPrint(dictionary):
    strlist =[]
    for key, value in dictionary.items():
        strlist.append("%d - %s, %s, %d"%(key, value.id, value.name, value.count))

    print("\n------Dict-------")
    for line in strlist:
        print(line)

def listPrint(list):
    strlist =[]
    for agent in list:
        strlist.append("%s - %d, %d"%(agent.name.toString(), agent.age, agent.dna.archTypeRef))

    print("\n------List-------")
    for line in strlist:
        print(line)





