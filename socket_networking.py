import socket, _thread, pygame, os, math, json
from lib import LIMITobjects, contentLoader, filePath
import collision #experimental

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 8080
os.environ['SDL_VIDEO_CENTERED'] = '1'
config = filePath.loadConfig(filePath.setPath(filePath.getRootFolder(2),["config.txt"]))
RESOLUTION = config["RESOLUTION"]
DEBUG = config["DEBUG"]

networkPacker = {
    "moveForward":0,
    "turnLeft":1,
    "turnRight":2,
    "primaryFire":3,
}

networkUnPacker = {
    0:"moveForward",
    1:"turnLeft",
    2:"turnRight",
    3:"primaryFire",
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
        newEntity = LIMITobjects.player("ally", {"name":"Player","directory":0,"canBeHit": True,"type":"Player", "address":address},(0,0,0), 30)
        self.connectedClients.append(newEntity)
        self.gameState.append(newEntity)

    def rectCollision(self, rect1, rect2):
        corner1, corner2, corner3, corner4 = rect1
        #bottom left, bottom right, top right, top left
        theirCorner1, theirCorner2, theirCorner3, theirCorner4 = rect2
        width = abs(corner2[0] - corner1[0])
        theirWidth = abs(theirCorner2[0] - theirCorner1[0])
        xDistance = theirCorner2[0] - corner1[0]
        if xDistance <= width + theirWidth and xDistance >= 0:
            length = abs(corner3[1] - corner2[1])
            theirLength = abs(theirCorner3[1] - theirCorner2[1])
            yDistance = theirCorner3[1] - corner2[1]
            if yDistance <= length+ + theirLength and yDistance >= 0:
                return True
        return False

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
                if action == "primaryFire":
                    payload = networkUnPacker[payload]
                    self.gameState.append(LIMITobjects.projectile("ally", {"name": payload, "directory": 1, "type": payload}, client.getBulletSpawn()))
                    
            updateToSend = []
            #Update all the entities
            for entity in self.gameState:
                entity.update(self.ticksCalculation, self.ticksMS)
                myRect = entity.getRect()
                for otherEntity in self.gameState: #Check for collisions
                    if otherEntity != entity:
                        theirRect = otherEntity.getRect()
                        if self.rectCollision(myRect, theirRect): #Check rectangle collision first

                            #SAT collision
                            myPolygon = entity.getShape()
                            theirPolygon = otherEntity.getShape()
                            collided, pushValue = collision.polygonCollide(myPolygon, theirPolygon)
                            if collided:
                                if entity.getHasMoved(): #Only move if the entity moved into something
                                    entity.collisionShift(pushValue)
                                
                entityType, x, y, angle = entity.getRender()
                entityType = networkPacker[entityType]
                updateToSend.append((entityType, round(x), round(y), round(angle))) #Rounding shrinks the packets
            
            #Send data to clients
            self.gameSocket.postUpdate(updateToSend)
            
            deltaTime = pygame.time.get_ticks() - startTime
            pygame.time.delay(max(self.targetTicks-deltaTime, 0))

    def runClient(self):
        pygame.init()
        self.renderer = renderer()
        self.canvas = pygame.display.set_mode(RESOLUTION)
        self.gameState = json.dumps([])
        self.gameSocket = client(self)
        _thread.start_new_thread(self.gameSocket.runClient, ())
        while True:
            startTime = pygame.time.get_ticks()
            self.canvas.fill((255,255,255)) #Clear the screen
            myInputs = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        myInputs.append((networkPacker["primaryFire"], networkPacker["Surge"]))
                        
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                myInputs.append((networkPacker["moveForward"], self.ticksCalculation))
            if keys[pygame.K_a]:
                myInputs.append((networkPacker["turnLeft"], self.ticksCalculation))
            if keys[pygame.K_d]:
                myInputs.append((networkPacker["turnRight"], self.ticksCalculation))
            
            for myInput in myInputs:
                self.gameSocket.sendInput(myInput) #Send input

            #Render game state
            stateToRender = json.loads(self.gameState) #Json loads used here to prevent pass by reference
            self.renderer.draw(self.canvas, stateToRender)    
            pygame.display.flip() #Update the screen
            deltaTime = pygame.time.get_ticks() - startTime
            pygame.time.delay(max(self.ticksCalculation-deltaTime, 0))

class renderer:
    def __init__(self):
        pass

    def draw(self, canvas, gameState):
        #gameState is a list of (entityType, x, y, angle)
        for entity in gameState:
            name, x, y, angle = entity
            name = networkUnPacker[name]
            colour, shape, sizes, stats = entities[name]
            pointsToDraw = []
            sizeIndex = 0
            if DEBUG:
                rectX = [None, None]
                rectY = [None, None]
            for point in shape:
                direction = math.radians(point+angle)
                
                pointX = x+sizes[sizeIndex]*math.cos(direction)
                pointY = y+sizes[sizeIndex]*math.sin(direction)
                
                pointsToDraw.append((pointX, pointY))

                if DEBUG:
                    if rectX[0] == None or pointX < rectX[0]:
                        rectX[0] = pointX
                    if rectX[1] == None or pointX > rectX[1]:
                        rectX[1] = pointX
                        
                    if rectY[0] == None or pointY < rectY[0]: 
                        rectY[0] = pointY 
                    if rectY[1] == None or pointY > rectY[1]:
                        rectY[1] = pointY 
                    
                if sizeIndex < len(sizes)-1:
                    sizeIndex += 1
                    
            pygame.draw.polygon(canvas, colour, pointsToDraw)
            pygame.draw.aalines(canvas, colour, True, pointsToDraw)

            if DEBUG:
                triangleTest = collision.polygonToTriangles(pointsToDraw)
                for triangle in triangleTest:
                    pygame.draw.aalines(canvas, (0,255,0), True, triangle)
                rectangle = ((rectX[0], rectY[0]),(rectX[1], rectY[0]),(rectX[1], rectY[1]),(rectX[0], rectY[1]))
                pygame.draw.aalines(canvas, (255,0,0), True, rectangle)
            
entities  = contentLoader.loadEntities()
entities[0].update(entities[1]) #Combine dictionaries
entities = entities[0]
orderOfEntities = []
for key in entities:
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
