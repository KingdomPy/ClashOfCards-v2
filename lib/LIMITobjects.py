import math, random
import json
from lib import filePath, contentLoader

#Hosts the classes that define how the entities work
#Lists the AI's of enemeies
#Controls the change of states of enemies

#Constants
FILERETRACTS = 2
ENTITIES = contentLoader.loadEntities() # A list in the order of enemies, projectiles
ABILITIES = contentLoader.loadAbilities()
for ability in ABILITIES:
    print(ability)

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
        if stats["directory"] == 0 or stats["directory"] == 1:
            image = ENTITIES[stats["directory"]][stats["type"]]
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
        if self.stats["directory"] == 0: # Enemy entity
            stats = ENTITIES[0][self.stats["type"]][3]
            self.maxHealth = stats[1]
            self.health = stats[1]
            self.movementSpeed = stats[0] # Metres per second
        elif self.stats["directory"] == 1: # Bullet entity
            self.movementSpeed = ENTITIES[1][self.stats["type"]][3] # Metres per second
        else: # Temporary data loading
            self.movementSpeed = 200
            self.maxHealth = 15
            self.health = 15
            self.maxEnergy = 10
            self.energy =10

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

    def visualRotate(self, delta, direction, rotation=None):
        if rotation == None:
            self.visualAngle += direction*math.pi*delta # Rotation speed of 180 per second
        else:
            self.visualAngle = rotation
        self.visualAngle %= 2*math.pi
            
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
        self.learntAbilities = [] # Moves that have been learnt/unlocked
        self.passives = [] # A list of equipped abilities or effects that trigger automatically (timePassed, name)
        self.cooldowns = [[0,0],[0,0],[0,0],[0,0],[0,0]] # List that tracks the cooldowns of abilities (timePassed, cooldown, name/tag/id), passives are appended on

        self.basic = 0 # Holds the data of the current basic attack set (name,scaling)
        self.abilities = [0,0,0,0] #Holds a list of the data of the equipped active abilities (name,scaling)

        self.setLoadout("B","Surge")
        self.setLoadout("A", "Missile", 1)
        self.setLoadout("A", "Missile", 2)
        self.setLoadout("A", "Missile", 3)
        self.setLoadout("A", "Missile", 4)

    def activateCommand(self, slot):
        if self.cooldowns[slot][0] >= self.cooldowns[slot][1]:
            if slot == 0:
                self.cooldowns[slot][0] = 0
                return ("projectile", (self.basic[0],)) # Instruction, data
        return 0 # Response to the engine that the move currently can not be used

    def setLoadout(self, type, name, slot=1):
        moveData = 0 # Assume the ability can not be found
        for ability in ABILITIES: # Search for the ability
            if ability[0] == type and ability[1] == name:
                moveData = ability
                break
        if not(moveData == 0): # Only run if the ability has now been found
            if type == "B": # Attack command slot
                self.basic = (name,(ability[3][0],ability[3][1]))
                self.cooldowns[0] = [ability[3][2]*1000, ability[3][2]*1000] # Reset the cooldown
            elif type == "A": # Active (Magic) slot 1
                self.abilities[slot-1] = (name,ability[3])
                self.cooldowns[slot] = [ability[3][2]*1000, ability[3][2]*1000] # Reset the cooldown

    def update(self, delta, clockSignal):

        self.visualAngle = self.angle

        for ability in self.cooldowns: # Increment the cooldown timers
            if ability[0] < ability[1]:
                ability[0] += clockSignal

class projectile(entity):

    def __init__(self, tag, stats, position=(0,0,0), size=30):
        super().__init__(tag, stats, position, size)
        self.duration = [0,4000] # Current time, Maximum time alive

    def update(self, delta, clockSignal):
        self.moveForward(delta)
        self.visualRotate(delta, 1)
        self.duration[0] += clockSignal
        if self.duration[0] >= self.duration[1]:
            return 0 # Instruction to the engine to delete the projectile
        

    

