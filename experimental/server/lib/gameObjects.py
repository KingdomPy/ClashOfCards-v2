import math

class entity:

    def __init__(self, entityId, entityName, entityType):
        self.entityId = entityId
        self.entityName = entityName
        self.entityType = entityType
        self.x = 0
        self.y = 0
        self.vAngle = 0
        self.angle = 0
        self.movementSpeed = 45
        self.clientInputs = []
        self.abilities = []

    def addInput(self, clientInput):
        self.clientInputs.append(clientInput)

    def setPosition(self, position):
        self.x, self.y = position

    def setAngles(self, visualAngle, angle):
        self.vAngle = visualAngle
        self.angle = angle

    def getPositionAngle(self):
        return self.x, self.y, self.vAngle, self.angle

    def rotate(self, direction, dt): #-1 or 1 for direction
        self.angle += direction * math.pi * dt

    def moveForward(self, direction, dt): #-1 or 1 for direction
        self.x += direction * self.movementSpeed * math.cos(self.angle) * dt
        self.y += direction * self.movementSpeed * math.sin(self.angle) * dt

    def update(self, dt):
        previousState = (self.x,self.y,self.vAngle,self.angle)
        for clientInput in self.clientInputs:
            if clientInput == "upKey":
                self.moveForward(1, dt)
            elif clientInput == "downKey":
                self.moveForward(-1, dt)
            elif clientInput == "leftKey":
                self.rotate(-1, dt)
            elif clientInput == "rightKey":
                self.rotate(1, dt)
        self.clientInputs = []
        if previousState != (self.x,self.y,self.vAngle,self.angle):
            return round(self.x, 1), round(self.y, 1), round(self.vAngle,2), round(self.angle,2) #Has been changed
        else:
            return 0 #Has not changed
