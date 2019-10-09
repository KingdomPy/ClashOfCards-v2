import socket, _thread
import json
import pygame, os
from lib import LIMITobjects, contentLoader, filePath

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5005
os.environ['SDL_VIDEO_CENTERED'] = '1'
config = filePath.loadConfig(filePath.setPath(filePath.getRootFolder(2),["config.txt"]))
RESOLUTION = config["RESOLUTION"]

networkPacker = {
    "moveForward":0,
    "turnLeft":1,
    "turnRight":2,
}

networkUnPacker = {
    0:"moveForward",
    1:"turnLeft",
    2:"turnRight"
}

class server:
    def __init__(self, engine):
        self.engine = engine
        self.clientInputs = []
        self.connectedClients = [] #List of connected addresses
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((SERVER_IP, SERVER_PORT))

    def runServer(self):
        while True: #Collects player input
            packet, address = self.socket.recvfrom(4096)
            self.addPlayer(address)
            self.clientInputs.append((json.loads(packet.decode()), address))

    def postUpdate(self, update):
        update = json.dumps(update).encode()
        for client in self.connectedClients:
            self.socket.sendto(update, client)

    def addPlayer(self, address):
        if not (address in self.connectedClients):
            self.connectedClients.append(address)
            self.engine.addPlayer(address)

    def getInputs(self):
        clientInputs = self.clientInputs
        self.clientInputs = []
        return clientInputs
            
class client:
    def __init__(self, engine):
        self.engine = engine
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((SERVER_IP, SERVER_PORT))

    def runClient(self):
        while True: #Collects game state from the server
            packet = self.socket.recv(4096)
            self.engine.setGameState(packet.decode()) #Apply json loads after to prevent variable
            #being passed by reference

    def sendInput(self, myInput):
        self.socket.send(json.dumps(myInput).encode())    

class engine:
    def __init__(self):
        #load data
        self.connectedClients = [] #Shortcut to player object
        self.targetFPS = 60 #60
        self.ticksCalculation = round(1000/self.targetFPS) #pre-calculated ticks per second
        '''pygame.init()
        self.canvas = pygame.display.set_mode((0,0), pygame.SCALED)'''

    def setGameState(self, gameState):
        self.gameState = gameState

    def addPlayer(self, address):
        newEntity = LIMITobjects.player("ally", {"name":"Player","directory":10,"canBeHit": True,"type":"Player", "address":address},(0,0,0), 30)
        self.connectedClients.append(newEntity)
        self.gameState.append(newEntity)

    def runServer(self):
        self.gameState = []
        self.targetTicks = 30
        self.ticksMS = round(1000/self.targetTicks) #ticks per update in milliseconds
        self.ticksCalculation = self.ticksMS/1000 #pre-calculated ticks per second
        self.gameSocket = server(self)
        _thread.start_new_thread(self.gameSocket.runServer, ())
        while True: #30 ticks per second, updates game state
            startTime = pygame.time.get_ticks()
                    
            clientInputs = self.gameSocket.getInputs() #Get multiplayer input
            for instruction in clientInputs: #Process the input
                action, payload = instruction[0]
                address = instruction[1]

                action = networkUnPacker[action]
                client = None
                for player in self.connectedClients:
                    if player.getAddress() == address:
                        client = player
                        break
            
                if action == "moveForward":
                    payload /= 1000
                    client.moveForward(payload)
                if action == "turnLeft":
                    payload /= 1000
                    client.rotate(payload, -1)
                if action == "turnRight":
                    payload /= 1000
                    client.rotate(payload, 1)
                    
            updateToSend = []
            #Update all the entities
            for entity in self.gameState:
                entity.update(self.ticksCalculation, self.ticksMS)
                
                entityType, x, y = entity.getRender()
                entityType = networkPacker[entityType]
                updateToSend.append((entityType, x, y))
            
            #Send data to clients
            self.gameSocket.postUpdate(updateToSend)
            
            deltaTime = pygame.time.get_ticks() - startTime
            pygame.time.delay(max(self.targetTicks-deltaTime, 0))

    def runClient(self):
        pygame.init()
        self.canvas = pygame.display.set_mode(RESOLUTION, pygame.SCALED)
        self.gameState = json.dumps([])
        self.gameSocket = client(self)
        _thread.start_new_thread(self.gameSocket.runClient, ())
        while True:
            startTime = pygame.time.get_ticks()
            self.canvas.fill((255,255,255)) #Clear the screen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit() 
            keys = pygame.key.get_pressed()
            myInputs = []
            if keys[pygame.K_w]:
                myInputs.append((networkPacker["moveForward"], self.ticksCalculation))
            if keys[pygame.K_a]:
                myInputs.append((networkPacker["turnLeft"], self.ticksCalculation))
            if keys[pygame.K_d]:
                myInputs.append((networkPacker["turnRight"], self.ticksCalculation))
            
            for myInput in myInputs:
                self.gameSocket.sendInput(myInput) #Send input

            #Render game state
            stateToRender = json.loads(self.gameState) #json loads used here to prevent pass by reference
            for entity in stateToRender:
                entityType, x, y = entity
                entityType = networkUnPacker[entityType]
                if entityType == "Player":
                    pygame.draw.rect(self.canvas, (0,0,0), (x-5, y-5, 10, 10))
            pygame.display.flip() #Update the screen
            deltaTime = pygame.time.get_ticks() - startTime
            pygame.time.delay(max(self.ticksCalculation-deltaTime, 0))
        

entities  = contentLoader.loadEntities()
orderOfEntities = []
for key in entities[0]: #Add Enemies
    orderOfEntities.append(key)
for key in entities[1]: #Add Projectiles
    orderOfEntities.append(key)

#Add entities to network packer and unpacker
for entity in orderOfEntities:
    value = len(networkPacker)
    networkPacker[entity] = value
    networkUnPacker[value] = entity

connectionType = input("Client or Server (C or S):")
game = engine()
if connectionType.lower() == "c":
    game.runClient()
else:
    game.runServer()
