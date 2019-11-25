import math
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
    pass
    #print(ability)

def pointToPoint(xDif, yDif, angle):
    if yDif < 0:
        return  math.pi/2 - math.atan(xDif/yDif) 
    else:
        if yDif != 0:
            return - math.pi/2 - math.atan(xDif/yDif)
        else:
            return angle #returned when angle can not be calculated

        #(-1*yDif/abs(yDif)) = math.atan(xDif/yDif) One line equation

class entity:
    def __init__(self, tag, stats, position=(0,0,0), size=30):
        # Position & Rendering
        self.tag = tag
        self.stats = stats
        self.x = position[0]
        self.y = position[1]
        self.angle = position[2]
        self.visualAngle = self.angle

        # Physics & Rendering
        self.type = self.stats["type"]
        self.entityCategory = stats["directory"]
        self.shape = ENTITIES[self.entityCategory][self.type][1]
        self.sizes = ENTITIES[self.entityCategory][self.type][2]
        self.sizeScale = 1
        self.hasMoved = 0 # 0 = false, 1 = stopping, 2 = true

        # Animations
        self.clock = 0
        self.currentAnimation = [""]
        self.iFrame = False # immunity frame
        self.canCollide = False # ignore collision

        # (hp, mana, cooldowns, if it can be damage, e.t.c)
        self.loadStats()
        self.detectionRange = 300

    def loadStats(self):
        if self.entityCategory == 0: # Enemy entity
            #self.canBeHit = self.stats["canBeHit"]
            stats = ENTITIES[0][self.stats["type"]][3]
            self.maxHealth = stats[1]
            self.health = stats[1]
            self.movementSpeed = stats[0] # Metres per second

        elif self.entityCategory == 1: # Bullet entity
            self.movementSpeed = ENTITIES[1][self.stats["type"]][3] # Metres per second

        else: # Temporary data loading
            self.canBeHit = self.stats["canBeHit"]
            self.movementSpeed = 200
            self.maxHealth = 15
            self.health = 15
            self.maxEnergy = 10
            self.energy =10

    def hitProcedure(self, damage):
        self.health -= damage

    def moveForward(self, delta, distance=None):
        if distance == None:
            self.x += self.movementSpeed*math.cos(self.angle)*delta
            self.y += self.movementSpeed*math.sin(self.angle)*delta
        else:
            self.x += distance*math.cos(self.angle)
            self.y += distance*math.sin(self.angle)
            
        self.hasMoved = 2

    def rotate(self, delta, direction, rotation=None):
        if rotation == None:
            self.angle += direction*math.pi*delta # Rotation speed of 180 per second
        else:
            self.angle = rotation
        self.angle %= 2*math.pi

        self.hasMoved = 2

    def visualRotate(self, delta, direction, rotation=None):
        if rotation == None:
            self.visualAngle += direction*math.pi*delta # Rotation speed of 180 per second
        else:
            self.visualAngle = rotation
        self.visualAngle %= 2*math.pi

        self.hasMoved = 2
            
    def update(self, delta, clockSignal, playerObjects=[]):
        # Delta is the amount of time in seconds that has passed
        # since frame has refreshed, clockSignal is the time in milliseconds

        nearest_playerObject = (self.detectionRange+1, 0) #Distance, Center
        myRect = self.getRect() #Bottom Left, Bottom Right, Top Right, Top Left
        playerRect = 0 #Reserve for use later
        for playerObject in playerObjects: #Player objects are players and their allies
            #Me to Them
            playerRect = playerObject.getRect()
            xDistance = max(playerRect[0][0] - myRect[1][0], myRect[0][0] - playerRect[1][0])
            yDistance = max(playerRect[1][1] - myRect[2][1], myRect[1][1] - playerRect[2][1])
            distance = math.sqrt(xDistance**2 + yDistance**2)
            if distance < nearest_playerObject[0]:
                nearest_playerObject = (distance, playerObject.getPosition())

        if nearest_playerObject[0] <= self.detectionRange:
            center1 = self.getPosition()
            center2 = nearest_playerObject[1]
            self.visualRotate(0, 0, pointToPoint(center1[0] - center2[0], center1[1] - center2[1], self.visualAngle))
        else:
            self.moveForward(delta)
            self.moveForward(delta)
            self.rotate(delta, 1)
            self.visualAngle = self.angle
        
        self.clock += clockSignal
        self.clock %= 10000 #Reset every 10 seconds

        if self.hasMoved > 0:
            self.hasMoved -= 1

    def setLocation(self, position, angle):
        self.x,self.y = position
        self.angle = angle

    def getVisualAngle(self):
        return self.visualAngle

    def getTag(self):
        return self.tag

    def getPosition(self):
        return self.x, self.y

    def getRender(self):
        return self.type, self.x, self.y, math.degrees(self.visualAngle)

    def getRect(self):
        sizeIndex = 0
        rectX = [None, None]
        rectY = [None, None]
        for point in self.shape:
            direction = math.radians(point) + self.visualAngle
            x = self.x+self.sizes[sizeIndex]*math.cos(direction)
            y = self.y+self.sizes[sizeIndex]*math.sin(direction)
            if rectX[0] == None or x < rectX[0]:
                rectX[0] = x
            if rectX[1] == None or x > rectX[1]:
                rectX[1] = x
                
            if rectY[0] == None or y < rectY[0]: 
                rectY[0] = y
            if rectY[1] == None or y > rectY[1]:
                rectY[1] = y
                
            if sizeIndex < len(self.sizes)-1:
                sizeIndex += 1
        #Create the rectangle
        rectangle = ((rectX[0], rectY[0]),(rectX[1], rectY[0]),(rectX[1], rectY[1]),(rectX[0], rectY[1]))
        return rectangle

    def getShape(self):
        pointsToDraw = []
        sizeIndex = 0
        for point in self.shape:
            direction = math.radians(point) + self.visualAngle
            x = self.x+self.sizes[sizeIndex]*math.cos(direction)
            y = self.y+self.sizes[sizeIndex]*math.sin(direction)
            pointsToDraw.append((x,y))
            if sizeIndex < len(self.sizes)-1:
                sizeIndex += 1
        return pointsToDraw

    def collisionShift(self, pushValue):
        self.x += pushValue[0]
        self.y += pushValue[1]

    def getHasMoved(self):
        if self.hasMoved > 0:
            return True
        return False
    
    def getBulletSpawn(self):
        return self.x, self.y, self.angle
    
class player(entity):

    def __init__(self, tag, stats, position=(0,0,0), size=30):
        super().__init__(tag, stats, position, size)
        try:
            self.address = self.stats["address"]
        except:
            pass
        self.items = []  # Weapons, potions e.t.c
        self.learntAbilities = [] # Moves that have been learnt/unlocked
        self.passives = [] # A list of equipped abilities or effects that trigger automatically (timePassed, name)
        self.cooldowns = [[0,0],[0,0],[0,0],[0,0],[0,0]] # List that tracks the cooldowns of abilities (timePassed, cooldown, name/tag/id), passives are appended on

        self.basic = 0 # Holds the data of the current basic attack set (name, scaling)
        self.abilities = [0,0,0,0] # Holds a list of the data of the equipped active abilities (name, scaling)
        self.equippedItems = [("Potion",1),("Hi-Potion",1),("Restore",1),("Accelerator",1)] # Holds a list of the equipped items (name, amount)
        self.upgrades = ["Enhanced","Shift","Techno",""] #  Holds a list of equipped upgrades

        self.commandOptions = ("Attack","Magic","Items","Upgrade") # The options displayed in the command menu by the interface

        self.setLoadout("B","Surge")
        self.setLoadout("A", "Missile", 1)
        self.setLoadout("A", "Missile", 2)
        self.setLoadout("A", "Missile", 3)
        self.setLoadout("A", "Missile", 4)

    def activateCommand(self, slot):
        if self.commandOptions[slot] == "Attack":
            if self.cooldowns[slot][0] >= self.cooldowns[slot][1]:
                self.cooldowns[slot][0] = 0
                return ("projectile", (self.basic[0],)) # Instruction, data
        elif self.commandOptions[slot] == "Magic":
            self.commandOptions = (self.abilities[0][0], self.abilities[1][0], self.abilities[2][0], self.abilities[3][0])
            return("selectedMove", 0)
        elif self.commandOptions[slot] == "Items":
            self.commandOptions = (self.equippedItems[0][0]+" *"+str(self.equippedItems[0][1]), self.equippedItems[1][0]+" *"+str(self.equippedItems[1][1]),
                                   self.equippedItems[2][0]+" *"+str(self.equippedItems[2][1]), self.equippedItems[3][0]+" *"+str(self.equippedItems[3][1]))
            return("selectedMove", 0)
        elif self.commandOptions[slot] == "Upgrade":
            self.commandOptions = self.upgrades
            return("selectedMove", 0)
        return 0 # Response to the engine that the move currently can not be used

    def setLoadout(self, type, name, slot=1):
        moveData = 0 # Assume the ability can not be found
        for ability in ABILITIES: # Search for the ability
            if ability[0] == type and ability[1] == name:
                moveData = ability
                break
        if not(moveData == 0): # Only run if the ability has now been found
            if type == "B": # Attack command slot
                self.basic = (name,(ability[3][0],ability[3][1])) # Name, (ability scalings and cooldown)
                self.cooldowns[0] = [ability[3][2]*1000, ability[3][2]*1000] # Reset the cooldown
            elif type == "A": # Active (Magic) slot 1
                self.abilities[slot-1] = (name,ability[3]) # Name, (ability scalings and cooldown)
                self.cooldowns[slot] = [ability[3][2]*1000, ability[3][2]*1000] # Reset the cooldown

    def update(self, delta, clockSignal, playerObjects=[]):

        self.visualAngle = self.angle

        for ability in self.cooldowns: # Increment the cooldown timers
            if ability[0] < ability[1]:
                ability[0] += clockSignal

        if self.hasMoved > 0:
            self.hasMoved -= 1

    def setCommandOptions(self, options):
        self.commandOptions = options

    def getCommandOptions(self):
        return self.commandOptions

    def getAddress(self):
        return self.address
    
class projectile(entity):

    def __init__(self, tag, stats, position=(0,0,0), size=30):
        super().__init__(tag, stats, position, size)
        self.duration = [0,4000] # Current time, Maximum time alive
        self.damage = 10
        self.inMotion = True # Has not collided

    def hasHit(self):
        self.inMotion = False
        return 1 # Should be destroyed upon being hit

    def update(self, delta, clockSignal, playerObjects=[]):
        self.duration[0] += clockSignal
        if self.duration[0] >= self.duration[1] or not(self.inMotion):
            return 0 # Instruction to the engine to delete the projectile
        self.moveForward(delta)
        if self.type == "Surge":
            self.visualRotate(delta, 1)
        elif self.type == "Hyper":
            self.visualRotate(delta, 1)

    def getDamage(self):
        return self.damage

