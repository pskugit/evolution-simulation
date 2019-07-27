import math
import random
import pygame
import numpy as np
from collections import defaultdict
from dna import *
from util import *
pygame.font.init()
sys_font = pygame.font.SysFont('lucidasanstypewriterfett', 12)

### ============================================== BASE AGENT =======================================###
class Agent(object):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100,-100),dnaLength=1):
        # meta
        self.win_width = win_width
        self.win_height = win_height

        # attributes (external)
        self.dnaLength_pheno = 1
        self.spikes = 0
        self.spikeCount = 12
        self.aggression = 0
        self.altruism = 0
        self.color_red = 255
        self.color_green = 150
        self.color_blue = 255

        # atributes (internal)
        self.minSize = 7
        self.age = 1
        self.power = 3                #bitesize multiplier
        #self.maxAge = 7000           #age is shown divided by 10 -> de facto maxAge is maxAge*0.75
        self.asexual_reproduction_rate = 0.002
        self.sexual_reproduction_rate = 0.006
        self.metabolism = 1           #metabolism of <0.25 means certain death
        self.reproduction_cost = 0    #self.max_health / 4

        # attributes (sensors)
        self.senseRange = 0
        self.proximityList = []
        self.collisionList = []
        self.collission = 0

        # DNA and NAME
        self.dnaLength = dnaLength
        self.generateDna(parents, archTypes)
        self.name = name(archTypes[self.dna.archTypeRef].name)

        # movement
        self.position = position
        if self.position.x == -100:
            self.position = Position(random.random()*win_width-1, random.random()*win_height-1)
        self.torque = 0
        self.max_torque = math.pi/4
        self.turning = random.random()* math.pi *2
        self.acceleration = 0
        self.velocity = 0

        if not parents:
            print("Agent %s is created by God!   DNA: %s \n"%(self.name.toString(), self.dna.readable()))
        elif parents[0] == parents[1]:
            print("Agent %s has split off of his parent %s.  DNA: %s \n"%(self.name.toString(), parents[0].name.toString(), self.dna.readable()))
        else:
            print("Agent %s is born!   Parents: %s & %s.   DNA: %s \n"%(self.name.toString(), parents[0].name.toString(), parents[1].name.toString(), self.dna.readable()))

    def setPheno(self):
        self.max_health = 50*self.size
        self.health = self.max_health / 1.5  # self.reproduction_cost * 2
        self.bitesize = self.size * 2
        self.energyefficiency = 400 / (self.size * self.size)
        self.max_velocity = 1000 / (self.size * self.size)
        self.max_acceleration = 200 / (self.size * self.size)

    def generateDna(self, parents, archTypes):
        self.dna = Dna(parents, archTypes, self.dnaLength)

    def postoInt(self, position):
        return (int(position[0]), int(position[1]))

    def getGridPos(self, terrain):
        return Position(math.floor(self.position.x / terrain.scale), math.floor(self.position.y / terrain.scale))

    def isAlive(self):
        return self.health > 0

    def proximity(self, foodMap, agentList):
        for otherAgent in agentList:
            if self.position.eucDistanceTo(otherAgent.position) < self.senseRange:
                self.proximityList.append(otherAgent)
            if self.position.eucDistanceTo(otherAgent.position) < otherAgent.senseRange:
                otherAgent.proximityList.append(self)
            #COLLISION
            if self.position.eucDistanceTo(otherAgent.position) < self.size + otherAgent.size:
                self.collisionList.append(otherAgent)
                otherAgent.collisionList.append(self)

    def die(self, foodMap):
        self.health = -100
        #foodMap.values[foodPos.x][foodPos.y] = min(foodMap.values[foodPos.x][foodPos.y]+self.size*5,foodMap.max_value)
        foodMap.setValueAtPosition(min(foodMap.getValueAtPosition(self.position)+ max(0,self.health),foodMap.max_value), self.position)
        print('Agent %s tragically died!' % (self.name.toString()))

    def sense(self, foodMap):
        return None

    def think(self):
        pass

    def reproduceSexually(self, archTypes):
        if self.collisionList:
            if (random.random() < (self.sexual_reproduction_rate)):
                partner = random.choice(self.collisionList)
                #prevent DNA mismatch
                if partner.dnaLength == self.dnaLength:
                    # birth cost
                    self.health -= self.reproduction_cost / self.energyefficiency
                    return self.__class__(self.win_width, self.win_height, [self, partner], archTypes)
        return None

    def reproduceAsexually(self, archTypes):
        #return random.random() < (self.health/self.max_health)*self.reproduction_rate              #health dependant reproduction -deprectaed
        if (random.random() < self.asexual_reproduction_rate * (self.health/self.max_health)):
            #birth cost
            self.health -= self.reproduction_cost/self.energyefficiency

            return self.__class__(self.win_width, self.win_height, [self,self], archTypes)
        return None

    def eat(self, foodMap):
        #self.metabolism = (2*(1- self.aggression) + (1- self.altruism))/3

        #gain life
        food = foodMap.getValueAtPosition(self.position)
        if food > self.bitesize:
            self.health += min(food, self.bitesize) * self.metabolism
            self.health = min(self.health, self.max_health)
            foodMap.setValueAtPosition(max(0,food-self.bitesize), self.position)

    def updateColor(self):
        health_perc = min(1,max(0,self.health / self.max_health))
        self.color = (health_perc * self.color_red/2, health_perc * self.color_green/2, health_perc * self.color_blue/2)

    def move(self):
        # acceleration cost
        self.health -= 20 * ((abs(self.acceleration)/self.max_acceleration) / self.energyefficiency)

        # torque cost
        self.health -= 10 * ((self.torque/self.max_torque) / self.energyefficiency)

        # ----# movement calculation
        self.velocity = max(0, self.velocity + self.acceleration)
        self.turning += self.torque
        self.velocity = min(self.velocity, self.max_velocity)

        # speed cost
        self.health -= 40 * ((self.velocity/self.max_velocity) / self.energyefficiency)

        #friction
        self.velocity *= 0.9

        # screen edge control
        # nextx = min(self.win_width-1,max(0,self.position.x + math.sin(self.turning) * self.velocity))          #hard borders
        # nexty = min(self.win_height-1,max(0,self.position.y + math.cos(self.turning) * self.velocity))
        nextx = (self.position.x + math.sin(self.turning) * self.velocity) % self.win_width   # wrap screen
        nexty = (self.position.y + math.cos(self.turning) * self.velocity) % self.win_height

        # position update
        self.position.x = nextx
        self.position.y = nexty

        # force normalizations
        self.acceleration *= 0
        self.torque *= 0
        self.turning = self.turning%(2*math.pi)

    def bite(self,otherAgent):
        damage = (self.spikes * self.power) * self.aggression
        otherAgent.health -= damage
        self.health += min(otherAgent.health,damage*0.75)
        self.health = min(self.max_health, self.health)

    def transfuse(self,otherAgent):
        transfusion = min(self.spikes, self.health) * self.altruism
        self.health -= transfusion  * self.power
        otherAgent.health = min(otherAgent.max_health, otherAgent.health + (transfusion * self.power))

    def collide(self):
        self.collission = 1 if self.collisionList else 0
        for otherAgent in self.collisionList:
            pass
            # collision alert
            # print("%s und %s sind kollidiert!"%(self.name.toString(), otherAgent.name.toString()))

            #plain damage
            #self.health -= 25

            #instant death
            #self.health = -100

            #bite
            #if self.velocity > otherAgent.velocity:
            #    self.bite(otherAgent)

            #transfuse and bite
            self.bite(otherAgent)
            self.transfuse(otherAgent)

            # instant kill if bigger
            #if self.size*0.9 > otherAgent.size:
            #    self.health += otherAgent.health
            #    otherAgent.health = -100

    def update(self, foodMap):
        # process collision list
        self.collide()
        # eating
        self.eat(foodMap)
        # sensing
        self.sense(foodMap)
        # thinking
        self.think()
        # moving
        self.move()
        # health decay
        self.health = min(self.health, self.max_health)
        self.health = max(0, self.health - (self.bitesize / self.energyefficiency))
        # aging
        self.age += 1
        #self.metabolism = 0.6 - min(0.5,self.age/self.maxAge)
        # death
        if not self.isAlive():
            self.die(foodMap)

        #empty proximity list
        self.proximityList = []
        self.collisionList = []

    def drawBrain(self, archTypes, window):
        dims = (600,500)
        surf = pygame.surface.Surface(dims)
        surf.fill((255, 255, 255))
        surf.blit(sys_font.render("%s has no brain...."%(self.name.toString()), 0, (0, 0, 0)), (dims[0] / 2 - 50,20))
        window.blit(surf, (self.win_width, self.win_height / 2 + 100))

    def draw(self, window):
        # color update
        self.updateColor()
        perc_health = min(1,max(0,self.health / self.max_health))

        #set up transparent surface
        scale = 5
        tranparent_surface = pygame.Surface((2*scale*self.size, 2*scale*self.size))
        tranparent_surface.set_colorkey((0, 0, 0))
        tranparent_surface.set_alpha((perc_health * 130) +125)
        center = (scale*self.size,scale*self.size)

        #plane indicator
        #pygame.draw.rect(tranparent_surface,(1,1,1), (0,0, tranparent_surface.get_width(), tranparent_surface.get_height() ), 1)

        #draw spikes
        self.spikeCount = 10
        for i in range(self.spikeCount):
            # draw small line to seperate body halfs
            spikeEnd = (
            scale * self.size + math.sin(self.turning + (2 * math.pi / self.spikeCount) * i) * (self.size-1 + self.spikes),
            scale * self.size + math.cos(self.turning + (2 * math.pi / self.spikeCount) * i) * (self.size-1 + self.spikes))
            pygame.draw.line(tranparent_surface, (1, 1, 1), center, spikeEnd, max(1, int((self.size * self.size) / 50)))

        #draw feelers
        if isinstance(self, FeelerAgent):
            leftfeeler = (scale*self.size + math.sin(self.feelerAngle + self.turning) * self.leftFeelerLength,
                          scale * self.size + math.cos(self.feelerAngle + self.turning) * self.leftFeelerLength)
            pygame.draw.line(tranparent_surface, self.color, center, leftfeeler, max(1, int((self.size * self.size) / 100)))
            pygame.draw.circle(tranparent_surface, self.color, (int(leftfeeler[0]),int(leftfeeler[1])), int(self.size//5))

            rightfeeler = (scale*self.size + math.sin(-self.feelerAngle + self.turning) * self.rightFeelerLength,
                           scale * self.size + math.cos(-self.feelerAngle + self.turning) * self.rightFeelerLength)
            pygame.draw.line(tranparent_surface, self.color, center, rightfeeler, max(1, int((self.size * self.size) / 100)))
            pygame.draw.circle(tranparent_surface, self.color, (int(rightfeeler[0]),int(rightfeeler[1])), int(self.size//5))

        #draw character blob
        pygame.draw.circle(tranparent_surface, self.color, center , int(self.size))
        window.blit(tranparent_surface, (self.position.minus(Position(center[0],center[1])).toTuple()))

        #draw small line to seperate body halfs
        lineEnd=(self.position.x + math.sin(self.turning) * (self.size-2),
                 self.position.y + math.cos(self.turning) * (self.size-2))
        pygame.draw.line(window, (255,255,255), self.position.toTuple(), lineEnd, max(1,int((self.size*self.size)/100)))

        #draw name
        rendered = sys_font.render(self.name.toString(), 0, (0, 0, 0))
        window.blit(rendered, (self.position.x-(len(self.name.toString())*3),self.position.y-self.size*2.8))

        #rendered = sys_font.render(str(self.dna.archTypeRef), 0, (0, 0, 0))
        #window.blit(rendered, (self.position.x - (5), self.position.y + self.size * 2))


#################################################### RANDOM AGENT ################################################
class RandomAgent(Agent):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100,-100), dnaLength=0):
        if dnaLength == 0:
            dnaLength=parents[0].dna.length() if parents else 1
        super().__init__(win_width, win_height, parents, archTypes, position,dnaLength)
        self.readDnaR()
        self.setPheno()
        self.color_red = 255
        self.color_green = 255
        self.color_blue = 0

    def readDnaR(self):
        #self.size= self.minSize +abs(self.dna.values[0])
        #my optimum
        self.size= 10

    def think(self):
        #full random movement
        #self.acceleration = (random.random() * self.max_acceleration) - self.max_acceleration / 2          #random accelaration
        self.acceleration = self.max_acceleration                                                           #runner
        self.torque = (random.random() * 2 * self.max_torque) - self.max_torque


#################################################### SENSING AGENT ################################################
class SensingAgent(Agent):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100,-100), dnaLength=0):
        if dnaLength == 0:
            dnaLength=parents[0].dna.length() if parents else 1
        super().__init__(win_width, win_height, parents, archTypes, position, dnaLength)
        #color
        self.color_red = 255
        self.color_green = 0
        self.color_blue = 0
        # sensors
        self.centerSensorValue = 0
        self.readDnaS()
        self.setPheno()

    def readDnaS(self):
        # self.size= self.minSize +abs(self.dna.values[0])
        # my optimum
        self.size = 10

    def sense(self, foodMap):
        self.centerSensorValue = foodMap.getValueAtPosition(self.position)/foodMap.max_value

    def think(self):
        # induce movement based on field
        #self.acceleration = ((foodMap.max_value / ((foodMap.max_value + foodMap.getValueAtPosition(self.position) * 5))) * self.max_acceleration) - self.max_acceleration / 2
        self.acceleration = (1- self.centerSensorValue) * self.max_acceleration - self.max_acceleration / 2
        self.torque = (random.random() - 0.5) * math.pi / 10

    def draw(self, window):
        super().draw(window)

#################################################### FEELER AGENT ################################################

class FeelerAgent(SensingAgent):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100, -100), dnaLength=0):
        if dnaLength == 0:
            dnaLength=parents[0].dna.length() if parents else 4
        super().__init__(win_width, win_height, parents, archTypes, position, dnaLength)
        # color
        self.color_red = 0
        self.color_green = 255
        self.color_blue = 0

        #more sensor initialization
        self.rightFeelerValue = 0
        self.leftFeelerValue = 0
        self.rightFeelerPos = Position(0, 0)
        self.leftFeelerPos = Position(0, 0)

        # more sensor characteristics
        self.rightFeelerLength = 60
        self.leftFeelerLength = 60
        self.feelerAngle = math.pi / 2

        # DNA
        self.readDnaV()
        self.setPheno()
        #print("V-Agent %s with Sensor Length: %d Sensor Angle: %f"%(self.name, self.sensorLength, self.sensorAngle)

    def readDnaV(self):
        #self.rightFeelerLength = self.dna.values[0] * self.rightFeelerLength
        #self.leftFeelerLength = self.dna.values[1] * self.leftFeelerLength
        #self.feelerAngle = self.dna.values[2] * self.feelerAngle
        #self.senseRange = self.dna.values[3] * self.senseRange
        #self.size = self.minSize + abs(self.dna.values[0])

        # my optimum
        self.rightFeelerLength = 35
        self.leftFeelerLength = 35
        self.feelerAngle = math.pi / 4
        self.size = 10



    def sense(self, foodMap):
        super().sense(foodMap)
        self.leftFeelerPos = Position(self.position.x + math.sin(self.feelerAngle + self.turning) * self.leftFeelerLength,
                                      self.position.y + math.cos(self.feelerAngle + self.turning) * self.leftFeelerLength)
        self.rightFeelerPos = Position(self.position.x + math.sin(-self.feelerAngle + self.turning) * self.rightFeelerLength,
                                       self.position.y + math.cos(-self.feelerAngle + self.turning) * self.rightFeelerLength)
        self.leftFeelerValue = foodMap.getValueAtPosition(self.leftFeelerPos.wrapEdge(self.win_width, self.win_height)) \
                               / foodMap.max_value
        self.rightFeelerValue = foodMap.getValueAtPosition(self.rightFeelerPos.wrapEdge(self.win_width, self.win_height)) \
                                / foodMap.max_value

    def think(self):
        # induce acceleration based on center sensor
        self.acceleration = (1 - self.centerSensorValue) * self.max_acceleration - self.max_acceleration / 3
        # indoce torque based on side
        self.torque = (self.leftFeelerValue - self.rightFeelerValue) * self.max_torque

    def draw(self, window):
        super().draw(window)
        #draw sensors (inkl. hotfix for grafic jumps)       #deprecated
        #if self.leftFeelerPos.eucDistanceTo(self.position) < 250 and self.rightFeelerPos.eucDistanceTo(
        #        self.position) < 250:
        #    pygame.draw.line(window, self.color, self.position.toTuple(), self.leftFeelerPos.toTuple(), max(1, int((self.size * self.size) / 100)))
        #    pygame.draw.line(window, self.color, self.position.toTuple(), self.rightFeelerPos.toTuple(), max(1, int((self.size * self.size) / 100)))


#################################################### HEARING AGENT ################################################
class HearingAgent(FeelerAgent):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100, -100), dnaLength=0):
        if dnaLength == 0:
            dnaLength=parents[0].dna.length() if parents else 4
        super().__init__(win_width, win_height, parents, archTypes, position,dnaLength)
        # color
        self.color_red = 255
        self.color_green = 128
        self.color_blue = 0

        # more sensors
        self.senseRange = 100
        self.leftEarValue = 0
        self.rightEarValue = 0
        self.backEarValue = 0
        self.frontEarValue = 0
        self.maxEarValue = self.senseRange          #Ear value is sum of euclidic distances to sensable agents   divided by maxEarValue
        #right eye
        self.rightEye_prox = 0
        self.rightEye_red = 0
        self.rightEye_green = 0
        self.rightEye_blue = 0
        # left eye
        self.leftEye_prox = 0
        self.leftEye_red = 0
        self.leftEye_green = 0
        self.leftEye_blue = 0

        self.readDnaH()
        self.setPheno()

    def readDnaH(self):
        # self.size = self.minSize + abs(self.dna.values[0])
        # self.senseRange = self.dna.values[3] * self.senseRange
        #my optimum
        self.size = 10
        self.senseRange = 100

    def sense(self, foodMap):
        super().sense(foodMap)
        #reset sensors before checking proximity
        self.rightEarValue = 0
        self.leftEarValue = 0
        self.rightEye_prox = 0
        self.rightEye_red = 0
        self.rightEye_green = 0
        self.rightEye_blue = 0
        self.leftEye_prox = 0
        self.leftEye_red = 0
        self.leftEye_green = 0
        self.leftEye_blue = 0

        #find the closest agent for each eye
        closestLeft = None
        closestLeft_dist = 2*self.senseRange
        closestRight = None
        closestRight_dist = 2*self.senseRange

        #for vision
        frontLeft_vector = np.array([math.sin(self.turning+(math.pi/3)) * (self.senseRange),math.cos(self.turning+(math.pi/3)) * (self.senseRange)])
        frontLeftPerp_vector =  np.array([math.sin(self.turning+(math.pi/3) - (math.pi/2.25)) * (self.senseRange),math.cos(self.turning+(math.pi/3) - (math.pi/2.25)) * (self.senseRange)])
        frontRight_vector = np.array([math.sin(self.turning - (math.pi / 3)) * (self.senseRange), math.cos(self.turning - (math.pi / 3)) * (self.senseRange)])
        frontRightPerp_vector = np.array([math.sin(self.turning - (math.pi / 3) + (math.pi / 2.25)) * (self.senseRange), math.cos(self.turning - (math.pi / 3) + (math.pi / 2.25)) * (self.senseRange)])

        #for hearing
        perpendicularVector = np.array([math.sin(self.turning + (math.pi / 2)) * (self.senseRange), math.cos(self.turning + (math.pi / 2)) * (self.senseRange)])
        ownPosVector = np.array([math.sin(self.turning) * (self.senseRange), math.cos(self.turning) * (self.senseRange)])

        for otherAgent in self.proximityList:
            otherAgentPosVector = np.array([otherAgent.position.x - self.position.x, otherAgent.position.y - self.position.y])

            # proximity (closest other agent) front left
            frontLeft_dot_product = np.dot(frontLeft_vector, otherAgentPosVector)
            frontLeftPerp_dot_product = np.dot(frontLeftPerp_vector, otherAgentPosVector)
            frontRight_dot_product = np.dot(frontRight_vector, otherAgentPosVector)
            frontRightPerp_dot_product = np.dot(frontRightPerp_vector, otherAgentPosVector)

            #if other agent is in sight of left eye
            if frontLeft_dot_product > 0 and frontLeftPerp_dot_product > 0:
                #check if he is the closest
                distance = self.position.eucDistanceTo(otherAgent.position)
                if distance < closestLeft_dist:
                    closestLeft = otherAgent
                    closestLeft_dist = distance

            # if other agent is in sight of right eye
            if frontRight_dot_product > 0 and frontRightPerp_dot_product > 0:
                # check if he is the closest
                distance = self.position.eucDistanceTo(otherAgent.position)
                if distance < closestRight_dist:
                    closestRight = otherAgent
                    closestRight_dist = distance

            #HEARING!!
            # hear left and right
            perp_dot_product = np.dot(perpendicularVector, otherAgentPosVector)  # value is between -10000 and 10000
            if perp_dot_product < 0:
                self.rightEarValue += max(0, self.senseRange - self.position.eucDistanceTo(otherAgent.position)) * (
                math.sqrt(abs(perp_dot_product)) / self.senseRange)  # with dot product
                # self.rightEarValue += self.senseRange - self.position.eucDistanceTo(otherAgent.position)                                                                #without dot product
            if perp_dot_product > 0:
                self.leftEarValue += max(0, self.senseRange - self.position.eucDistanceTo(otherAgent.position)) * (
                math.sqrt(abs(perp_dot_product)) / self.senseRange)
            # hear front and back
            straight_dot_product = np.dot(ownPosVector, otherAgentPosVector)
            t = self.senseRange - self.position.eucDistanceTo(otherAgent.position)
            if straight_dot_product < 0:
                self.backEarValue += max(0, self.senseRange - self.position.eucDistanceTo(otherAgent.position)) * (
                math.sqrt(abs(straight_dot_product)) / self.senseRange)
                # self.backEarValue += self.senseRange- (self.position.eucDistanceTo(otherAgent.position)/2 + math.sqrt(abs(straight_dot_product))/2)
            if straight_dot_product > 0:
                self.frontEarValue += max(0, self.senseRange - self.position.eucDistanceTo(otherAgent.position)) * (
                math.sqrt(abs(straight_dot_product)) / self.senseRange)
                # self.frontEarValue += self.senseRange- (self.position.eucDistanceTo(otherAgent.position)/2 + math.sqrt(abs(straight_dot_product))/2)

        # normalization of hearing
        self.rightEarValue = min(1, self.rightEarValue / self.maxEarValue)
        self.leftEarValue = min(1, self.leftEarValue / self.maxEarValue)
        self.backEarValue = min(1, self.backEarValue / self.maxEarValue)
        self.frontEarValue = min(1, self.frontEarValue / self.maxEarValue)

        #fill eye sensors
        if closestRight is not None:
            #fill sensors with values
            self.rightEye_prox = max(0,(self.senseRange - closestRight_dist)/self.senseRange)
            self.rightEye_red = closestRight.color_red /255
            self.rightEye_green = closestRight.color_green /255
            self.rightEye_blue = closestRight.color_blue /255

        if closestLeft is not None:
            self.leftEye_prox = max(0,(self.senseRange - closestLeft_dist)/self.senseRange)
            self.leftEye_red = closestLeft.color_red /255
            self.leftEye_green = closestLeft.color_green /255
            self.leftEye_blue = closestLeft.color_blue /255

        #eye positions for drawing
        #self.leftEye_vector_Pos =  Position(self.position.x + frontLeft_vector[0], self.position.y + frontLeft_vector[1])
        #self.leftEyePerp_vector_Pos = Position(self.position.x + frontLeftPerp_vector[0], self.position.y + frontLeftPerp_vector[1])
        #self.rightEye_vector_Pos = Position(self.position.x + frontRight_vector[0], self.position.y + frontRight_vector[1])
        #self.rightEyePerp_vector_Pos = Position(self.position.x + frontRightPerp_vector[0], self.position.y + frontRightPerp_vector[1])

    def think(self):
        # induce acceleration based on center sensor
        self.acceleration = (1 - self.centerSensorValue) * self.max_acceleration - self.max_acceleration / 3

        # indoce torque based on Feelers
        self.torque = (self.leftFeelerValue - self.rightFeelerValue) * self.max_torque

        # induce torque based on side EARS
        self.torque = (self.rightEarValue - self.leftEarValue) * self.max_torque         #avoiding others
        #self.torque = (self.leftEarValue - self.rightEarValue) * self.max_torque         #being attracted to others

        # induce acceleration based on hearing
        noise = (self.leftEarValue+self.rightEarValue)/2
        #if noise > 0.25:
        #    self.acceleration =  min(self.acceleration*2, self.max_acceleration)

        #elif noise > 0.8:
            # self.torque += (random.random() * 2 * self.max_torque) - self.max_torque
            # self.torque = (self.rightEarValue - self.leftEarValue) * self.max_torque / 2
        #else:
        #    self.torque += (self.leftEarValue - self.rightEarValue) * self.max_torque / 2

        #acceleration based on front and back
        self.acceleration += self.frontEarValue * -self.max_acceleration/2

        #print("\nAgent %s hears %f left and %f right. Noise is %f. "%(self.name.toString(), round(self.leftEarValue,3), round(self.rightEarValue,3), round(noise,3)))
        #print("Decides for %f acceleration and %f torque."%(round(self.acceleration,3), round(self.torque/(2*math.pi),3)))

    def draw(self, window):
        super().draw(window)
        #sensing circle
        #pygame.draw.circle(window, (255,255,255), self.position.toTuple(), int(self.senseRange), 1)
        # draw eyes (inkl. hotfix for grafic jumps)
        #if self.leftFeelerPos.eucDistanceTo(self.position) < 250 and self.rightFeelerPos.eucDistanceTo(self.position) < 250:
        #    pygame.draw.line(window, (200,200,200), self.position.toTuple(), self.leftEye_vector_Pos.toTuple(), 1)
        #    pygame.draw.line(window, (200,200,200), self.position.toTuple(), self.leftEyePerp_vector_Pos.toTuple(), 1)
        #    pygame.draw.line(window, (200,200,200), self.position.toTuple(), self.rightEye_vector_Pos.toTuple(), 1)
        #    pygame.draw.line(window, (200,200,200), self.position.toTuple(), self.rightEyePerp_vector_Pos.toTuple(), 1)


#################################################### BRAIN AGENT 1 ################################################
class BrainAgent1(HearingAgent):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100, -100), brain=(5,5,2)):
        self.dnaLength_pheno = 1

        # specific brain parameters
        self.inputNames = ["health","velocity", "center", "left feeler", "right feeler"]
        self.outputNames = ["torque", "acceleration"]
        self.inputSize = brain[0]
        self.hiddenSize = brain[1]
        self.outputSize = brain[2]

        #calculate dna length
        if self.hiddenSize > 0:
            dnaLength= self.inputSize*self.hiddenSize + self.hiddenSize  + self.hiddenSize*self.outputSize  + self.outputSize
        else:
            dnaLength = self.inputSize * self.outputSize + self.outputSize
        dnaLength += self.dnaLength_pheno

        #create agent with given dna
        super().__init__(win_width, win_height, parents, archTypes, position,dnaLength)

        # color
        self.color_red = 80
        self.color_green = 60
        self.color_blue = 255

        #initialize the Brain
        self.hiddenLayer = np.zeros(self.hiddenSize)
        self.outputLayer = np.zeros(self.outputSize)
        self.hiddenWeights, self.hiddenBias, self.outputWeights, self.outputBias = self.readDnaB(self.dna.values[self.dnaLength_pheno:])

        # set phenotype
        self.rightFeelerLength = 35
        self.leftFeelerLength = 35
        self.feelerAngle = math.pi / 4
        self.senseRange = 100
        self.size = 10
        self.setPheno()

    def readDnaB(self, dna_values):
        hiddenWeights = np.array([])
        hiddenBias = np.array([])
        if self.hiddenSize > 0:
            #Brain mit
            hW = self.inputSize * self.hiddenSize
            hiddenWeights = np.reshape(dna_values[:hW], (self.hiddenSize, self.inputSize))
            hiddenBias = dna_values[hW : hW+self.hiddenSize]
            oW = hW+self.hiddenSize
            outputWeights = np.reshape(dna_values[oW: oW+self.hiddenSize*self.outputSize], (self.outputSize, self.hiddenSize))
            outputBias = dna_values[oW + self.hiddenSize * self.outputSize:]
        else:
            #Brain mit
            outputWeights = np.reshape(dna_values[:self.inputSize * self.outputSize], (self.outputSize, self.inputSize))
            outputBias = dna_values[-self.outputSize:]
        return hiddenWeights, hiddenBias, outputWeights, outputBias


    def think(self):
        #build input vector
        in1 = self.health/self.max_health
        in2 = self.velocity/self.max_velocity
        in3 = self.centerSensorValue
        in4 = self.leftFeelerValue
        in5 = self.rightFeelerValue
        self.inputVector = np.array([in1, in2, in3, in4, in5])

        for i in range(self.hiddenSize):
            self.hiddenLayer[i] = tanh(np.dot(self.hiddenWeights[i], self.inputVector) + self.hiddenBias[i])
        for i in range(self.outputSize):
            self.outputLayer[i] = sigmoid(np.dot(self.outputWeights[i], self.hiddenLayer) + self.outputBias[i])
        self.torque = (self.outputLayer[0] * self.max_torque * 2) - self.max_torque
        self.acceleration = (self.outputLayer[1] * self.max_acceleration * 2) - self.max_acceleration

    def draw(self, window):
        super().draw(window)

    def drawBrain(self, archTypes, window, inputNames = [], outputNames=[]):
        ## use archtype DNA/weights
        at_hiddenWeights, at_hiddenBias, at_outputWeights, at_outputBias = self.readDnaB(archTypes[self.dna.archTypeRef].values[self.dnaLength_pheno:])
        dims = (600,500)
        surf = pygame.surface.Surface(dims)
        surf.fill((255, 255, 255))
        surf.blit(sys_font.render("Brain of %s"%(self.name.toString()), 0, (0, 0, 0)), (dims[0]/2-50,20))

        #Neuron circle positiond
        hiddenScale = int(dims[1] / (self.hiddenSize+1))
        outScale = int(dims[1] / (self.outputSize+1))
        inScale = int(dims[1] / (self.inputSize+1))
        inPositions =       [(int(dims[0]/8),           inScale * (i+1)) for i in range(self.inputSize)]
        hiddenPositions =   [(int(dims[0]/2),           hiddenScale * (i+1)) for i in range(self.hiddenSize)]
        outPositions =      [(int(dims[0]-dims[0]/8),   outScale * (i+1)) for i in range(self.outputSize)]
        if self.hiddenSize == 0:
            hiddenPositions = inPositions

        #Values
        inputValues = [round(v,2) for v in self.inputVector]
        hiddenValues = [round(v,2) for v in self.hiddenLayer]
        outputValues = [round(v,2) for v in self.outputLayer]

        #print neurons
        for i, inPosition in enumerate(inPositions):
            #name
            surf.blit(sys_font.render(self.inputNames[i], 0, (0, 0, 0)), (inPosition[0]-60,inPosition[1] - 12))
            #value
            surf.blit(sys_font.render(str(inputValues[i]), 0, (0, 0, 0)), (inPosition[0] - 60, inPosition[1]+2))
            #circle
            pygame.draw.circle(surf, (0,0,0), inPosition, 10, 2)
        if self.hiddenSize > 0:
            for i,hiddenPosition in enumerate(hiddenPositions):
                # value
                surf.blit(sys_font.render(str(hiddenValues[i]), 0, (0, 0, 0)), (hiddenPosition[0] - 15, hiddenPosition[1] + 20))
                #circle
                if at_hiddenBias[i] > 0:
                    pygame.draw.circle(surf, (0,0,0), hiddenPosition, 10, 2)
                else:
                    pygame.draw.circle(surf, (255,0,0), hiddenPosition, 10, 2)
        for i, outPosition in enumerate(outPositions):
            #name
            surf.blit(sys_font.render(self.outputNames[i], 0, (0, 0, 0)), (outPosition[0]+15, outPosition[1] - 12))
            #value
            surf.blit(sys_font.render(str(outputValues[i]), 0, (0, 0, 0)), (outPosition[0]+15, outPosition[1] + 2))
            #circle
            if at_outputBias[i] > 0:
                pygame.draw.circle(surf, (0,0,0), outPosition, 10, 2)
            else:
                pygame.draw.circle(surf, (255, 0, 0), outPosition, 10, 2)

        # lines of weigths
        #hidden weights
        if self.hiddenSize > 0:
            max_hiddenWeight = max(abs(at_hiddenWeights.max()), abs(at_hiddenWeights.min()))
            for i,neuron in enumerate(self.hiddenWeights):
                for j, weight in enumerate(neuron):
                    if weight < 0:
                        #surf.blit(sys_font.render(str(round(weight, 3)), 0, (155, 0, 0)), (((inPositions[j][0] + hiddenPositions[i][0]) / 2) - 20,((inPositions[j][1] + hiddenPositions[i][1]) / 2) - 20)) #show weights
                        pygame.draw.line(surf, (155, 0, 0), inPositions[j], hiddenPositions[i],  int(abs((weight/max_hiddenWeight)*6+1)))
            for i,neuron in enumerate(self.hiddenWeights):
                for j, weight in enumerate(neuron):
                    if weight > 0:
                        #surf.blit(sys_font.render(str(round(weight, 3)), 0, (0, 0, 0)), (((inPositions[j][0] + hiddenPositions[i][0]) / 2) - 20, ((inPositions[j][1] + hiddenPositions[i][1]) / 2) - 20)) #show weights
                        pygame.draw.line(surf, (0, 0, 0), inPositions[j], hiddenPositions[i],  int(abs((weight/max_hiddenWeight)*6+1)))

        #output weights
        max_outWeight = max(abs(at_outputWeights.max()), abs(at_outputWeights.min()))
        for i,neuron in enumerate(self.outputWeights):
            for j, weight in enumerate(neuron):
                if weight < 0:
                    #surf.blit(sys_font.render(str(round(weight, 3)), 0, (155, 0, 0)), (((hiddenPositions[j][0] + outPositions[i][0]) / 2) - 20, ((hiddenPositions[j][1] + outPositions[i][1]) / 2) - 20)) # show weights
                    pygame.draw.line(surf, (155, 0, 0),hiddenPositions[j], outPositions[i],  int(abs((weight/max_outWeight)*6+1)))
        for i, neuron in enumerate(self.outputWeights):
            for j, weight in enumerate(neuron):
                if weight > 0:
                    #surf.blit(sys_font.render(str(round(weight, 3)), 0, (0, 0, 0)), (((hiddenPositions[j][0] + outPositions[i][0]) / 2) - 20, ((hiddenPositions[j][1] + outPositions[i][1]) / 2) - 20))    # show weights
                    pygame.draw.line(surf, (0, 0, 0), hiddenPositions[j], outPositions[i],  int(abs((weight/max_outWeight)*6+1)))

        #surf.blit(sys_font.render(str(self.dna.readable()), 0, (0, 0, 0)), (10, dims[1]-30))
        window.blit(surf, (self.win_width, self.win_height/2+100))


#################################################### BRAIN AGENT 2################################################
class BrainAgent2(BrainAgent1):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100, -100), brain=(4, 4, 2)):
        super().__init__(win_width, win_height, parents, archTypes, position, brain)
        #specific brain parameters
        self.inputNames= ["velocity", "center", "left feeler", "right feeler"]
        self.outputNames = ["torque", "acceleration"]

    def think(self):
        #build input vector
        in1 = self.velocity/self.max_velocity
        in2 = self.centerSensorValue
        in3 = self.leftFeelerValue
        in4 = self.rightFeelerValue
        self.inputVector = np.array([in1, in2, in3, in4])

        for i in range(self.hiddenSize):
            self.hiddenLayer[i] = tanh(np.dot(self.hiddenWeights[i], self.inputVector) + self.hiddenBias[i])
        for i in range(self.outputSize):
            self.outputLayer[i] = sigmoid(np.dot(self.outputWeights[i], self.hiddenLayer) + self.outputBias[i])
        self.torque = (self.outputLayer[0] * self.max_torque * 2) - self.max_torque
        self.acceleration = (self.outputLayer[1] * self.max_acceleration * 2) - self.max_acceleration


#################################################### BRAIN AGENT 3   ################################################
class BrainAgent3(BrainAgent1):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100, -100), brain=(3,0,2)):
        super().__init__(win_width, win_height, parents, archTypes, position, brain)
        #my optimal dna:    [0,10,-10,-9,0,0,0,5]
        # specific brain parameters
        self.inputNames = ["center", "left feeler", "right feeler"]
        self.outputNames = ["torque", "acceleration"]

    def think(self):
        #build input vector
        in1 = self.centerSensorValue
        in2 = self.leftFeelerValue
        in3 = self.rightFeelerValue
        self.inputVector = np.array([in1, in2, in3])

        for i in range(self.outputSize):
            self.outputLayer[i] = sigmoid(np.dot(self.outputWeights[i], self.inputVector) + self.outputBias[i])
        self.torque = (self.outputLayer[0] * self.max_torque *2) - self.max_torque
        self.acceleration = (self.outputLayer[1] * self.max_acceleration * 2) - self.max_acceleration


#################################################### BRAIN AGENT 4   ################################################
class BrainAgent4(BrainAgent1):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100, -100), brain=(13,8,6)):
        super().__init__(win_width, win_height, parents, archTypes, position, brain)
        # specific brain parameters
        self.inputNames = ["health","speed","center", "feel R", "feel L", "prox R", "red R", "green R", "blue R", "prox L", "red L", "green L", "blue L"]
        self.outputNames = ["torque", "acc", "spike", "red", "green", "blue"]

    def think(self):
        #build input vector
        in1 = self.health/self.max_health
        in2 = self.velocity/self.max_velocity
        in3 = self.centerSensorValue
        in4 = self.rightFeelerValue
        in5 = self.leftFeelerValue
        in6 = self.rightEye_prox
        in7 = self.rightEye_red
        in8 = self.rightEye_green
        in9 = self.rightEye_blue
        in10 = self.leftEye_prox
        in11 = self.leftEye_red
        in12 = self.leftEye_green
        in13 = self.leftEye_blue
        self.inputVector = np.array([in1, in2, in3, in4, in5, in6, in7, in8, in9, in10, in11, in12, in13])

        for i in range(self.hiddenSize):
            self.hiddenLayer[i] = tanh(np.dot(self.hiddenWeights[i], self.inputVector) + self.hiddenBias[i])
        for i in range(self.outputSize):
            self.outputLayer[i] = sigmoid(np.dot(self.outputWeights[i], self.hiddenLayer) + self.outputBias[i])
        self.torque = (self.outputLayer[0] * self.max_torque * 2) - self.max_torque
        self.acceleration = (self.outputLayer[1] * self.max_acceleration * 2) - self.max_acceleration
        self.spikes = (self.outputLayer[2] * self.size)
        self.color_red = self.outputLayer[3] * 254 +1
        self.color_green = self.outputLayer[4] * 254 +1
        self.color_blue = self.outputLayer[5] * 254 +1


#################################################### BRAIN AGENT 5   ################################################
class BrainAgent5(BrainAgent1):
    def __init__(self, win_width, win_height, parents, archTypes, position=Position(-100, -100), brain=(13,8,5)):
        super().__init__(win_width, win_height, parents, archTypes, position, brain)
        # specific brain parameters
        self.inputNames = ["health","speed","center", "feel R", "feel L", "prox R", "red R", "green R", "prox L", "red L", "green L", "ear", "collision"]
        self.outputNames = ["torque", "acc", "spike", "aggro", "altru"]

    def think(self):
        #build input vector
        in1 = self.health/self.max_health
        in2 = self.velocity/self.max_velocity
        in3 = self.centerSensorValue
        in4 = self.rightFeelerValue
        in5 = self.leftFeelerValue
        in6 = self.rightEye_prox
        in7 = self.rightEye_red
        in8 = self.rightEye_green
        in9 = self.leftEye_prox
        in10 = self.leftEye_red
        in11 = self.leftEye_green
        in12 = self.backEarValue
        in13 = self.collission
        self.inputVector = np.array([in1, in2, in3, in4, in5, in6, in7, in8, in9, in10, in11, in12, in13])

        for i in range(self.hiddenSize):
            self.hiddenLayer[i] = tanh(np.dot(self.hiddenWeights[i], self.inputVector) + self.hiddenBias[i])
        for i in range(self.outputSize):
            self.outputLayer[i] = sigmoid(np.dot(self.outputWeights[i], self.hiddenLayer) + self.outputBias[i])
        self.torque = (self.outputLayer[0] * self.max_torque * 2) - self.max_torque
        self.acceleration = (self.outputLayer[1] * self.max_acceleration * 2) - self.max_acceleration
        self.spikes = (self.outputLayer[2] * self.size)
        self.aggression = self.outputLayer[3]
        self.altruism = self.outputLayer[4]
        self.color_red = self.aggression * 254 +1
        self.color_green = self.altruism * 254 +1
        self.color_blue = 50