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

    def __init__(self, entityId, entityName, entityType):
        self.entityId = entityId
        self.entityName = entityName
        self.entityType = entityType
        self.x = 0
        self.y = 0
        self.angle = 0
        self.vAngle = 0 #Visual angle
        self.previousState = [self.x, self.y, self.vAngle, self.angle]
        self.currentState = [self.x, self.y, self.vAngle, self.angle]

        self.shape = ENTITIES[entityType][1]
        self.sizes = ENTITIES[entityType][2]
        self.sizeScale = 1

        self.serverTicks = 30 #30 ticks per second of server updates

    def getPositionAngle(self):
        return self.x, self.y, self.vAngle, self.angle

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

    def setPositionAngle(self, positionAngle):
        self.x, self.y, self.vAngle, self.angle = positionAngle

    def updateState(self, state):
        self.previousState = self.currentState
        self.currentState = state

    def update(self, dt):
        tweenScale = dt/self.serverTicks
        
        xTween = (self.currentState[0] - self.previousState[0])*tweenScale
        yTween = (self.currentState[1] - self.previousState[1])*tweenScale
        vaTween = (self.currentState[2] - self.previousState[2])*tweenScale #Visual Angle
        aTween = (self.currentState[3] - self.previousState[3])*tweenScale #Angle

        if abs(self.currentState[0] - self.x) > abs(xTween):
            self.x += xTween
        else:
            self.x = self.currentState[0]
            self.previousState[0] = self.x
            
        if abs(self.currentState[1] - self.y) > abs(yTween):
            self.y += yTween
        else:
            self.y = self.currentState[1]
            self.previousState[1] = self.y
            
        if abs(self.currentState[2] - self.vAngle) > abs(vaTween):
            self.vAngle += vaTween
        else:
            self.vAngle = self.currentState[2]
            self.previousState[2] = self.vAngle
            
        if abs(self.currentState[3] - self.angle)%2*math.pi > abs(aTween)%2*math.pi:
            self.angle += aTween
        else:
            self.angle = self.currentState[3]
            self.previousState[3] = self.angle

        
