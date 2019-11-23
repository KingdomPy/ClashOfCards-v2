import math
from lib import filePath, contentLoader

ENTITIES = contentLoader.loadEntities() #Enemies, Projectiles
orderOfEntities = {}
for key in ENTITIES[0]: #Add Enemies
    orderOfEntities[key] = ENTITIES[0][key]
for key in ENTITIES[1]: #Add Projectiles
    orderOfEntities[key] = ENTITIES[1][key]
ENTITIES = orderOfEntities
del orderOfEntities

class entity:

    def __init__(self, entityId, position=(0,0,0)):
        self.entityId = entityId
        #Server updates every 30 seconds
        self.tweenTime = 1000/30
        self.x, self.y, self.angle = position
        self.tweenStartX, self.tweenToX, self.tweenStartY = position
        self.tweenToY, self.tweenStartAngle, self.tweenToAngle = position
        self.animation = None
        self.updated = False

        self.movementSpeed = 40

    def getPosition(self):
        return self.x, self.y, self.angle

    def getUpdate(self): #Only called by the server
        if self.updated:
            self.updated = False
            return (self.x, self.y, self.angle)
        else:
            return 0

    def setType(self, name, entityClass):
        self.name = name
        self.entityClass = entityClass
        self.shape = ENTITIES[entityClass][1]
        self.sizes = ENTITIES[entityClass][2]
        self.sizeScale = 1

    def updatePosition(self, position): #Only called by the server
        x, y, angle = position
        self.x += x
        self.y += y
        self.angle += angle
        self.updated = True

    def getShape(self):
        self.visualAngle = self.angle
        pointsToDraw = []
        sizeIndex = 0
        self.radius = 0
        for point in self.shape:
            direction = math.radians(point) + self.visualAngle
            x = self.x+self.sizes[sizeIndex]*math.cos(direction)
            y = self.y+self.sizes[sizeIndex]*math.sin(direction)
            pointsToDraw.append((x,y))
            if self.sizes[sizeIndex] > self.radius:
                self.radius = self.sizes[sizeIndex]
            if sizeIndex < len(self.sizes)-1:
                sizeIndex += 1
        return pointsToDraw, self.radius

    def moveForward(self, delta, distance=None):
        if distance == None:
            self.x += self.movementSpeed * math.cos(self.angle) * delta
            self.y += self.movementSpeed * math.sin(self.angle) * delta
        else:
            self.x += distance * math.cos(self.angle)
            self.y += distance * math.sin(self.angle)
        self.updated = True

    def rotate(self, delta, direction, rotation=None):
        if rotation == None:
            self.angle += direction*math.pi*delta # Rotation speed of 180 per second
        else:
            self.angle = rotation
        self.angle %= 2*math.pi
        self.updated = True
    
    def tweenUpdate(self, update):
        x, y, angle = update
        
        self.tweenStartX = self.tweenToX
        self.tweenStartY = self.tweenToY
        self.tweenStartAngle = self.tweenToAngle

        self.x, self.y, self.angle = self.tweenStartX, self.tweenStartY, self.tweenStartAngle
        
        self.tweenToX = x
        self.tweenToY = y
        self.tweenToAngle = angle

    def update(self, dt):
        tweening = dt/self.tweenTime
        
        tweenX = (self.tweenToX - self.tweenStartX) * tweening
        tweenY = (self.tweenToY - self.tweenStartY) * tweening
        tweenAngle = (self.tweenToAngle - self.tweenStartAngle) * tweening

        if abs(self.tweenToX - self.x) < abs(tweenX):
            self.x += tweenX
        else:
            self.x = self.tweenToX
            self.tweenStartX = self.x
            
        if abs(self.tweenToY - self.y) < abs(tweenY):
            self.y += tweenY
        else:
            self.y = self.tweenToY
            self.tweenStartY = self.y

        if abs(self.tweenToAngle - self.angle) < abs(tweenAngle):
            self.angle += tweenAngle
        else:
            self.angle = self.tweenToAngle
            self.tweenStartAngle = self.angle
