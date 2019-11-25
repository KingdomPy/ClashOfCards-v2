import pygame
import pygame.gfxdraw
import json, math
from twisted.internet import reactor
from lib.networking import client
from lib import gameObjects, filePath

FILERETRACTS = 2

class scene:
    def __init__(self, targetDeltaTime):
        self.targetDeltaTime = targetDeltaTime

    def open(self, surface, networkProtocol, debug=False): #Load assets
        self.surface = surface
        self.dimensions = self.surface.get_size()
        self.debug = debug

        self.dt = 16 #milliseconds per frame
        self.waitingTime = self.dt/self.targetDeltaTime

        self.stage = "connecting to server"
        self.clock = 0
        self.closing = False

        self.networkProtocol = networkProtocol
        self.joiningGame = False

        self.controls = {"up": [pygame.K_w], "left": [pygame.K_a], "right": [pygame.K_d], "down": [pygame.K_s],
                         "SQUARE": [pygame.K_j], "CIRCLE": [pygame.K_l, 1], "CROSS": [pygame.K_k, 0],
                         "TRIANGLE": [pygame.K_i, 3],
                         "start": [pygame.K_p, 7], "home": [pygame.K_ESCAPE, 6],
                         "L1": [pygame.K_q, 4], "R1": [pygame.K_e, 5]}
        self.entities = {}

        self.path = filePath.getRootFolder(FILERETRACTS)
        self.mainFont = pygame.font.Font(filePath.setPath(self.path,["assets","fonts","Coda-Regular.ttf"]), 30)

        self.open = True
        
    def update(self, events, dt, graphics): #Updated by the game
        if self.open:
            self.surface.fill((255, 255, 255))

            if self.networkProtocol.inGame:
                inputs = [client.opCodes["input"]]

                keysPressed = pygame.key.get_pressed()

                for key in self.controls["up"]:
                    if keysPressed[key]:
                        inputs.append("upKey")

                for key in self.controls["left"]:
                    if keysPressed[key]:
                        inputs.append("leftKey")

                for key in self.controls["right"]:
                    if keysPressed[key]:
                        inputs.append("rightKey")

                for key in self.controls["down"]:
                    if keysPressed[key]:
                        inputs.append("downKey")

                if len(inputs) > 1: #Remove any contradicting inputs
                    if ("upKey" in inputs) and ("downKey" in inputs):
                        inputs.remove("upKey")
                        inputs.remove("downKey")
                    elif ("rightKey" in inputs) and ("leftKey" in inputs):
                        inputs.remove("rightKey")
                        inputs.remove("leftKey")

                for i in range(len(inputs) - 1):
                    inputs[i + 1] = client.opCodes[inputs[i + 1]]

                if len(inputs) > 1:
                    self.networkProtocol.sendData(json.dumps(inputs))

                if graphics == "low":
                    for entityId in self.entities:
                        entity = self.entities[entityId]
                        entity.update(dt)
                        polygon, radius = entity.getShape()
                        x, y, angle = entity.getPosition()
                        pygame.draw.lines(self.surface, (0,0,0), True, polygon)
                        pygame.draw.circle(self.surface, (0,0,0), (x,y), radius, 1)
                else:
                    for entityId in self.entities:
                        entity = self.entities[entityId]
                        entity.update(dt)
                        polygon, radius = entity.getShape()
                        x, y, vAngle, angle = entity.getPositionAngle()
                        pygame.draw.aalines(self.surface, (0, 0, 0), True, polygon)
                        pygame.gfxdraw.aacircle(self.surface, round(x), round(y), radius, (0,0,0))
            else:
                if not self.joiningGame:
                    packet = (client.opCodes["join"],"Nathan","Player")
                    packet = json.dumps(packet)
                    self.networkProtocol.sendData(packet)
                    self.joiningGame = True

            fpsDisplay = str(round(1000/dt))
            fpsDisplay = self.mainFont.render("FPS:" + fpsDisplay, True, (20, 20, 20))
            location = fpsDisplay.get_rect()
            location.topleft = self.surface.get_rect().topleft
            self.surface.blit(fpsDisplay, location)

    def close(self):#Closed by the game
        self.open = False

    def addEntity(self, entityId, position, entityName, entityClass):
        newEntity = gameObjects.entity(entityId, entityName, entityClass)
        newEntity.setPositionAngle(position)
        self.entities[entityId] = newEntity
        print(entityName, "("+entityClass+") has joined.")

    def removeEntity(self, entityId):
        self.entities.pop(entityId, None)

    def updateState(self, entityId, state):
        if entityId in self.entities:
            self.entities[entityId].updateState(state)