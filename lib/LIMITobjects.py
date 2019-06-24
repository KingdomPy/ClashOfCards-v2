import math, random
import json
from lib import filePath, contentLoader

#Hosts the classes that define how the entities work
#Lists the AI's of enemeies
#Controls the change of states of enemies

#Constants
FILERETRACTS = 2
ENTITIES = contentLoader.loadEntities()

class entity:
    def __init__(self, tag, stats, position=(0,0,0), size=30):
        self.tag = tag
        self.stats = stats
        self.x = position[0]
        self.y = position[1]
        self.angle = position[2]
        self.visualAngle = self.angle
        self.size = size
        self.clock = 0
        self.currentAnimation = [""]
        self.iFrame = False # immunity frame
        self.dodgeFrame = False # ignore collision frame
        # How extensive bullet collision is
        self.complexity = 10

        #Load Image
        if tag == "enemy":
            image = ENTITIES[0][stats["type"]]
            self.colour = image[0]
            shape = image[1]
            self.size = image[2]
            self.outline = []
            for angle in shape:
                self.outline.append(math.pi*(angle)/180) # Convert to radians
        else: # Temporary player image
            self.colour = (0,0,0)
            shape = (0,140,220)
            self.size = 35
            self.outline = []
            for angle in shape:
                self.outline.append(math.pi * (angle) / 180)  # Convert to radians

        # Conditions (e.g. hp, mana, cooldowns, if it can be damage)
        self.loadStats()

    def loadStats(self):
        if self.tag == "enemy":
            stats = ENTITIES[0][self.stats["type"]][3]
            self.maxHealth = stats[1]
            self.health = stats[1]
            self.movementSpeed = stats[0] # Metres per second
        else: # Temporary data loading
            self.movementSpeed = 200
            self.maxHealth = 15
            self.health = 15

    def moveForward(self, delta, distance=None):
        if distance == None:
            self.x += self.movementSpeed*math.cos(self.angle)*delta
            self.y += self.movementSpeed*math.sin(self.angle)*delta
        else:
            self.x += distance*math.cos(self.angle)
            self.y += distance*math.sin(self.angle)

    def rotate(self, delta, direction, rotation=None):
        if rotation == None:
            self.angle += direction*math.pi*delta # Rotation speed of 180 per second
        else:
            self.angle = rotation
        self.angle %= 2*math.pi
            
    def update(self, delta, clockSignal):
        # Delta is the amount of time in seconds that has passed
        # since frame has refreshed, clockSignal is the time in milliseconds
        
        self.moveForward(delta)
        self.moveForward(delta)
        self.rotate(delta, 1)
        self.visualAngle = self.angle
        
        self.clock += clockSignal
        self.clock %= 10000 #Reset every 10 seconds

    def render(self):
        display = []
        for point in self.outline:
            newPoint = point+self.visualAngle #Rotate the points to the current direction
            imageX,imageY = math.cos(newPoint),math.sin(newPoint) #Convert points to coordinates
            display.append([self.size*imageX,self.size*imageY]) #Stretch the image
        return display,self.colour,self.tag #Return the drawn entity, its colour and its tag

    def setLocation(self, position, angle):
        self.x,self.y = position
        self.angle = angle

    def getDomain(self): #Area the entity is contained
        return (self.x,self.y),self.size

    def getVisualAngle(self):
        return self.visualAngle

class player(entity):

    def __init__(self, tag, stats, position=(0,0,0), size=30):
        super().__init__(tag, stats, position, size)
        self.items = [] # Weapons e.t.c
        self.abilities = [] # Moves that have been learnt/unlocked
        self.passives = [] # Abilities or effects that trigger automatically (timePassed, name)
        self.cooldowns = [] # List that tracks the cooldowns of abilities (timePassed, cooldown, name/tag/id)

    def update(self, delta, clockSignal):

        self.visualAngle = self.angle

        for ability in self.cooldowns: # Increment the cooldown timers
            if ability[0] < ability[1]:
                ability[0] += clockSignal
    

