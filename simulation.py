import pygame
from agent import *
from grid import *
import operator
from collections import defaultdict
import pprint
from util import *
from interaction import *
from dna import *


pygame.init()
pygame.font.init()
sys_font = pygame.font.SysFont('lucidasanstypewriterfett', 12)


#initialization
win_width=1600
win_height=900
bg_color = (240,240,240)
window = pygame.display.set_mode((win_width,win_height))
pygame.display.set_caption("Lifes simulation")
window.fill(bg_color)

right_metrics = 600
bottom_metrics = 300

sim_area_width=win_width-right_metrics
sim_area_height=win_height-bottom_metrics

#screen elements
speed = Slider("Speed", 30, 5, 150, sim_area_width - 145, sim_area_height + 100)
slides = [speed]


clock = pygame.time.Clock()
run = True



#Metavariablen

#Agents
agentCreator = dict()
agentCreator['RandomAgent'] = 0
agentCreator['SensingAgent'] = 0
agentCreator['FeelerAgent'] = 0
agentCreator['HearingAgent'] = 0

agentCreator['BrainAgent1'] = 0
agentCreator['BrainAgent2'] = 0
agentCreator['BrainAgent3'] = 0
agentCreator['BrainAgent4'] = 0
agentCreator['BrainAgent5'] = 0

spawn = "BrainAgent5"
min_population = 8

#Archtypes
archTypes = dict()

#Agent List
fullAgentList=[]
for agentType, number in agentCreator.items():
    for i in range(number):
        fullAgentList.append(eval(agentType)(sim_area_width,sim_area_height,[], archTypes))

population_size = len(fullAgentList)
archTypeCount = population_size
dummyList = []

#Grids
food_grid_scale = 30
foodPlane = Foodplane(sim_area_width, sim_area_height, food_grid_scale)
density_grid_scale = 200
agentDensityPlane = DensityPlane(sim_area_width, sim_area_height, density_grid_scale)


#Metrics
population_size_history = [(0, population_size)]
food_supply_history = [(0, foodPlane.getTotalSupply())]
evo_progress_history = [(0, 0)]

displayNameList = []
displayNameList_At = []
at_representative = fullAgentList[0] if fullAgentList else None

max_history = 65
time = 0
avg_deathAge=0
deathCount=0
dnaLength = 0



###------------------------------------------------    GAME LOOP   ---------------------------------------------------------------
while(run):
    # Event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            #run = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0]< sim_area_width and mouse_pos[1] < sim_area_height:
                dummy = eval(spawn)(sim_area_width, sim_area_height, [], archTypes, position=Position(mouse_pos[0],mouse_pos[1]))
                dummyList.append(dummy)
                fullAgentList.append(dummy)

            else:
                # slider
                for s in slides:
                    if s.button_rect.collidepoint(mouse_pos):
                        s.hit = True

        elif event.type == pygame.MOUSEBUTTONUP:
            for s in slides:
                s.hit = False



        #keys
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                fullAgentList.append(RandomAgent(sim_area_width, sim_area_height, [], archTypes))
            elif event.key == pygame.K_s:
                fullAgentList.append(SensingAgent(sim_area_width, sim_area_height, [], archTypes))
            elif event.key == pygame.K_f:
                fullAgentList.append(FeelerAgent(sim_area_width, sim_area_height, [], archTypes))
            elif event.key == pygame.K_h:
                fullAgentList.append(HearingAgent(sim_area_width, sim_area_height, [], archTypes))
            elif event.key == pygame.K_1:
                fullAgentList.append(BrainAgent1(sim_area_width, sim_area_height, [], archTypes))

            elif event.key == pygame.K_2:
                fullAgentList.append(BrainAgent2(sim_area_width, sim_area_height, [], archTypes))
            elif event.key == pygame.K_3:
                fullAgentList.append(BrainAgent3(sim_area_width, sim_area_height, [], archTypes))
            elif event.key == pygame.K_4:
                fullAgentList.append(BrainAgent4(sim_area_width, sim_area_height, [], archTypes))
            elif event.key == pygame.K_5:
                fullAgentList.append(BrainAgent5(sim_area_width, sim_area_height, [], archTypes))

            #kill dummys
            elif event.key == pygame.K_k:
                for dummy in dummyList:
                    dummy.health=-100

    # Move slides
    for s in slides:
        if s.hit:
            s.move()


    #pygame.time.delay(90)
    window.fill(bg_color)



    #============================================================ calculate and read out metrics
    time +=1
    #population_size = sum([len(agentList) for agentType, agentList in agentContainer.items()])
    population_size = len(fullAgentList)
    food_supply = foodPlane.getTotalSupply()
    archTypeCount = len(archTypes.items())

    #for key in archTypes.keys():
    #    archTypes[key].count = 0
    alive = []


    if(time%10==0):                                                                                 #things to do every xxx seconds
        population_size_history.append((int(time),population_size))
        food_supply_history.append((int(time), food_supply))
        evo_progress_history.append((int(time), int((avg_deathAge*10) / (time/10))))

    if len(population_size_history)>max_history:
        population_size_history.pop(0)
        food_supply_history.pop(0)
        evo_progress_history.pop(0)


    #============================================================ manage terrain
    foodPlane.update()
    foodPlane.draw(window)

    #agentDensityPlane.update(fullAgentList)
    #agentDensityPlane.draw(window)

    #============================================================ manage agent
    #spawn new agents when population low
    if population_size < min_population:
        #fullAgentList.append(BrainAgent1(sim_area_width, sim_area_height, [], archTypes))
        fullAgentList.append(eval(spawn)(sim_area_width, sim_area_height, [], archTypes))


    for i, agent in enumerate(fullAgentList):
        agent.proximity(foodPlane, fullAgentList[i+1:])

    children = []
    for agent in fullAgentList:

        if displayNameList_At and (at_representative ==None or not at_representative.isAlive()):
            rep_found = False
            if agent.dna.archTypeRef == most_member_archtype_id and not rep_found:
                at_representative = agent
                rep_found = True

        agent.update(foodPlane)
        agent.draw(window)

        # give birth
        if population_size < 200:
            child = agent.reproduceAsexually(archTypes)
            if not child == None:
                children.append(child)

        if population_size < 150:
            child = agent.reproduceSexually(archTypes)
            if not child == None:
                children.append(child)


        #agent.proximityList = []
        #agent.collisionList = []

        ##die
        if agent.isAlive():
            alive.append(agent)

        else:
             deathCount += 1
             avg_deathAge = (avg_deathAge*(deathCount-1) + agent.age)/deathCount
             #print("Agent %s - %d died"%(agent.name.toString(), agent.dna.archTypeRef))
             archTypes[agent.dna.archTypeRef].count -= 1

    fullAgentList = alive.copy()
    fullAgentList.extend(children)


    # Prints the nicely formatted dictionary
    #listPrint(fullAgentList)
    #dictPrint(archTypes)

    for key in list(archTypes):
         if archTypes[key].count == 0:
             #print("ARCHTYPE EXTINCT: The last %s has perished.\n"%(archTypes[key].name))
             archTypes.pop(key)


    #============================================================ Render Metrcis White background

    pygame.draw.rect(window, (255, 255, 255), (0,sim_area_height, sim_area_width, win_height-sim_area_height))
    pygame.draw.rect(window, (255, 255, 255), (sim_area_width,0, win_width-sim_area_width, win_height))



    #========================================== Agent count and names list

    dims = (600, 400)
    surf = pygame.surface.Surface(dims)
    surf.fill((255, 255, 255))
    pygame.draw.rect(surf, (0, 0, 0), (10, 10, dims[0] -20, dims[1]-20), 1)

    ypos = 20
    rendered = sys_font.render("Total agents alive: %d" % (population_size), 0, (0, 0, 0))
    surf.blit(rendered, (30, ypos))
    ypos += 30

    #generate namelist
    if fullAgentList:
        displayNameList = [(agent.name.toString(), int(agent.age)) for agent in fullAgentList]
        oldest = fullAgentList[0]


    displayNameList.sort(key=operator.itemgetter(1), reverse=True)
    for entry in displayNameList[:15]:
        rendered = sys_font.render("%s       age %d"%(entry[0], entry[1]/12), 0, (0, 0, 0))
        surf.blit(rendered, (30, ypos))
        ypos += 20  # moves the following line down 30 pixels


    # ========================================== Archtype counts
    ypos = 20
    rendered = sys_font.render("Number of clans: %d" % (archTypeCount), 0, (0, 0, 0))
    surf.blit(rendered, (220, ypos))
    ypos += 30

    # generate namelist
    displayNameList_At = [(archType.name, archType.count, archType.id) for k,archType in archTypes.items()]

    displayNameList_At.sort(key=operator.itemgetter(1), reverse=True)
    if displayNameList_At:
        most_member_archtype_id = displayNameList_At[0][2]



    for entry in displayNameList_At[:15]:
        rendered = sys_font.render("%s: %d" % (entry[0], entry[1]), 0, (0, 0, 0))
        surf.blit(rendered, (220 , ypos))
        ypos += 20  # moves the following line down 30 pixels


    window.blit(surf, (sim_area_width,0))


    #========================================== graph
    right_border = sim_area_width-180
    bottom_border = win_height -10
    pygame.draw.rect(window, (0, 0, 0), (10, sim_area_height + 10, sim_area_width-180, win_height - sim_area_height - 20), 1)

    if len(population_size_history)>1:
        pop_points = [(right_border-time+point[0], bottom_border-(point[1]*2)) for point in population_size_history]
        food_points = [(right_border-time+point[0], bottom_border-(point[1]*2)-1) for point in food_supply_history]
        death_points = [(right_border - time + point[0], bottom_border - (point[1] * 2) + 1) for point in evo_progress_history]

        #draw circles
        for point in zip(pop_points, food_points, death_points):
            pygame.draw.circle(window, (0, 0, 200), point[0], 3, 1)
            pygame.draw.circle(window, (255,140,0), point[1], 3, 1)
            pygame.draw.circle(window, (200, 170, 0), point[2], 3, 1)

        #pygame.draw.aalines(window, (0, 0, 200), False, pop_points)            #aalines as alternative
        #pygame.draw.aalines(window, (255,140,0), False, food_points)
        #pygame.draw.aalines(window, (200, 170, 0), False, death_points)

    #Labels/Oveerlay
    window.blit(sys_font.render("Population size history", 0, (0, 0, 200)), (15, sim_area_height+15))
    window.blit(sys_font.render("Food supply history", 0, (255,140,0)), (right_border - 140, sim_area_height + 15))
    window.blit(sys_font.render("Evolutionary progess (avg death age/time)", 0, (200, 170, 0)), (270, sim_area_height + 15))


    for i in range(12):
        pygame.gfxdraw.hline(window, 10, right_border, win_height-30 - i*10*2, (0,0,0,100))
        window.blit(sys_font.render(str((i + 1) * 10), 0, (0, 0, 0)), (15, win_height - 30 - i * 10 * 2))
        #window.blit(sys_font.render(str((i + 1) * 10)+"%", 0, (0, 0, 0)), (sim_area_width - 32, win_height - 30 - i * 10 * 2))  #rechte achsenbezeichnugen


        # ========================================== Statistics
    window.blit(sys_font.render("Avg death age: %d" % (int(avg_deathAge / 10)), 0, (0, 0, 0)),(right_border + 35, sim_area_height + 15))
    window.blit(sys_font.render("Deaths so far: %d" % (deathCount), 0, (0, 0, 0)), (right_border + 35, sim_area_height + 35))
    window.blit(sys_font.render("Time: %d" % (time / 12), 0, (0, 0, 0)), (right_border + 35, sim_area_height + 70))


        # ========================================== Brain
    #oldest.drawBrain(window)
    if at_representative and at_representative.dna.archTypeRef in archTypes:
        at_representative.drawBrain(archTypes,window)

        #to show some metrics of the agent
        if isinstance(at_representative, HearingAgent):
            window.blit(sys_font.render("Right: %f" % (round(at_representative.rightEye_prox,3)), 0, (0, 0, 0)),(right_border + 35, sim_area_height + 160))
            window.blit(sys_font.render("Left: %f" % (round(at_representative.leftEye_prox, 3)), 0, (0, 0, 0)),(right_border + 35, sim_area_height + 175))
        #    window.blit(sys_font.render("Front: %f" % (round(at_representative.frontEarValue, 3)), 0, (0, 0, 0)), (right_border + 35, sim_area_height + 190))
        #    window.blit(sys_font.render("Back: %f" % (round(at_representative.backEarValue, 3)), 0, (0, 0, 0)), (right_border + 35, sim_area_height + 205))

        pygame.draw.circle(window, (255, 0, 0), at_representative.position.toTuple(), int(at_representative.size) + 2, 2)


    for s in slides:
        s.draw(window)

    #================================= UPDATE
    pygame.display.update()
    clock.tick(speed.val)

    #clock.tick(120)

pygame.quit()
quit()
