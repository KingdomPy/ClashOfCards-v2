import pygame, os, math, json
import socket, _thread
from lib import LIMITobjects, contentLoader, filePath
import collision #experimental

SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 8080
os.environ['SDL_VIDEO_CENTERED'] = '1'
config = filePath.loadConfig(filePath.setPath(filePath.getRootFolder(2),["config.txt"]))
RESOLUTION = config["RESOLUTION"]
DEBUG = config["DEBUG"]
WIDTHSCALE, LENGTHSCALE = RESOLUTION[0]/1280, RESOLUTION[1]/720 #Scale game according to default 1280x720 dimensions

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
        #update = json.dumps(update).encode()
        clientIndex = 0
        for client in self.connectedClients:
            x, y = self.engine.connectedClients[clientIndex].getPosition()
            uniqueUpdate = json.dumps(((x,y), update)).encode()
            self.socket.sendto(uniqueUpdate, client)
            clientIndex += 1

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
            self.engine.setGameState(packet.decode())
            #Apply json loads after to prevent variable from being passed by reference

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

    def loadImages(self):
        #PRE-CALCULATIONS
        self.hudMap = ((33*WIDTHSCALE,603*LENGTHSCALE), (1065*WIDTHSCALE, 10*LENGTHSCALE)) #Calculated positions of where the hud images are place
        rootFolder = filePath.getRootFolder(2)
        
        #LOAD HUD TEMPLATE
        self.hud = filePath.setPath(rootFolder,["assets","player","hud.png"])
        self.hud = pygame.image.load(self.hud).convert_alpha()

        #LOAD ABILITY BOX
        self.abilityBox = ((206,233,245), (20*WIDTHSCALE, 595*LENGTHSCALE, round(320*WIDTHSCALE), round(110*LENGTHSCALE))) #Colour, rect

        #LOAD ABILITY ICONS
        self.abilityIcons = (
            ((52,106,129), (33*WIDTHSCALE, 630*LENGTHSCALE, round(64*WIDTHSCALE), round(64*LENGTHSCALE))),
            ((52,106,129), (110*WIDTHSCALE, 630*LENGTHSCALE, round(64*WIDTHSCALE), round(64*LENGTHSCALE))),
            ((52,106,129), (187*WIDTHSCALE, 630*LENGTHSCALE, round(64*WIDTHSCALE), round(64*LENGTHSCALE))),
            ((52,106,129), (264*WIDTHSCALE, 630*LENGTHSCALE, round(64*WIDTHSCALE), round(64*LENGTHSCALE)))
        )#(Colour, rect), (Colour, rect), ...

        #LOAD HP BAR
        self.hpBar = (
            ((30,58,93), (1112*WIDTHSCALE, 673*LENGTHSCALE, round(163*WIDTHSCALE), round(12*LENGTHSCALE)), round(2*WIDTHSCALE)),
            ((77,161,24), (1112*WIDTHSCALE, 673*LENGTHSCALE, round(163*WIDTHSCALE), round(12*LENGTHSCALE)))
        ) #Border (Colour, rect), Fill (Colour, rect)

        #LOAD MP BAR
        self.mpBar = (
            ((30,58,93), (1154*WIDTHSCALE, 688*LENGTHSCALE, round(120*WIDTHSCALE), round(12*LENGTHSCALE)), round(2*WIDTHSCALE)),
            ((47,105,203), (1154*WIDTHSCALE, 688*LENGTHSCALE, round(120*WIDTHSCALE), round(12*LENGTHSCALE)))
        ) #Border (Colour, rect), Fill (Colour, rect)
        
        #LOAD LEVEL BAR ANIMATION
        self.levelBar = []
        levelBarImage = filePath.setPath(rootFolder,["assets","player","level bars.png"])
        levelBarImage = pygame.image.load(levelBarImage).convert()
        for i in range(9):
            levelBar = pygame.Surface((1180, 88))
            levelBar.blit(levelBarImage, (0, 0), (0, i*88, 1180,  88))
            levelBar = pygame.transform.smoothscale(levelBar, (round(295*WIDTHSCALE), round(22*LENGTHSCALE)))
            self.levelBar.append(levelBar)
        
        #LOAD ATTACK STYLE ICON    
        self.basicAttacks = [
            filePath.setPath(rootFolder,["assets","player","basic surge.png"]),
            filePath.setPath(rootFolder,["assets","player","basic spray.png"]),
            filePath.setPath(rootFolder,["assets","player","basic hyper.png"])
        ]
        
        for i in range(3):
            image = pygame.image.load(self.basicAttacks[i]).convert_alpha()
            width, length = image.get_rect()[2], image.get_rect()[3]
            targetLength = round(41 * LENGTHSCALE)
            targetWidth = round(width*41*WIDTHSCALE/length)
            image = pygame.transform.smoothscale(image, (targetWidth, targetLength))
            position = (1240*WIDTHSCALE-targetWidth, 620*LENGTHSCALE)
            self.basicAttacks[i] = (image, position)

        #LOAD MINIMAP
        self.minimap = filePath.setPath(rootFolder,["assets","player","minimap.png"])
        self.minimap = pygame.image.load(self.minimap).convert_alpha()
        self.minimap = pygame.transform.smoothscale(self.minimap, (round(205*WIDTHSCALE), round(187*LENGTHSCALE)))

        #SET ANIMATION SETTINGS
        self.animations = [[0,8,0,50]] #Current frame, Max frame, time elapsed, duration

    def renderHud(self):
        #self.hudMap containts pre calculated positions: level bar, minimap
        
        #BLIT HUD TEMPLATE
        self.canvas.blit(self.hud, (0,0))
        #DRAW ABILITY BOX
        pygame.draw.rect(self.canvas, *self.abilityBox)
        #DRAW ABILITY ICONS
        for icon in self.abilityIcons: pygame.draw.rect(self.canvas, *icon)
        #DRAW HP BAR
        pygame.draw.rect(self.canvas, *self.hpBar[1])
        pygame.draw.rect(self.canvas, *self.hpBar[0])
        #DRAW MP BAR
        pygame.draw.rect(self.canvas, *self.mpBar[1])
        pygame.draw.rect(self.canvas, *self.mpBar[0])
        #BLIT LEVEL BAR
        self.canvas.blit(self.levelBar[self.animations[0][0]], self.hudMap[0])
        #BLIT ATTACK STYLE
        if self.playerStats["basic attack"] == "Surge":
            imageIndex = 0
        elif self.playerStats["basic attack"] == "Spray":
            imageIndex = 1
        else:
            imageIndex = 2
        image, position = self.basicAttacks[imageIndex] 
        self.canvas.blit(image, position)
        #BLIT MINIMAP
        self.canvas.blit(self.minimap, self.hudMap[1])

    def runServer(self):
        self.gameState = []

        for i in range(9):
            self.gameState.append(LIMITobjects.entity("enemy", {"name": "Unrepentant Bandit", "directory": 0, "type": "Bandit"}, (300+50*i,300+30*i,0)))
        
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
                    if payload == "Spray":
                        *position, angle = client.getBulletSpawn()
                        coneAngle = math.pi/12 #30 degree cone
                        angle -= coneAngle
                        for i in range(3):
                            self.gameState.append(LIMITobjects.projectile("ally", {"name": payload, "directory": 1, "type": payload}, (*position,angle)))
                            angle += coneAngle
                    else:
                        self.gameState.append(LIMITobjects.projectile("ally", {"name": payload, "directory": 1, "type": payload}, client.getBulletSpawn()))
                        
            updateToSend = []
            entityIndex = 0
            #Update all the entities
            while entityIndex < len(self.gameState):
                entity = self.gameState[entityIndex]
                isAlive = entity.update(self.ticksCalculation, self.ticksMS, self.connectedClients)
                if isAlive == 0: #It is dead
                    self.gameState.pop(entityIndex)
                else:
                    myRect = entity.getRect()
                    otherEntityIndex = 0
                    while otherEntityIndex < len(self.gameState): #Check for collisions
                        otherEntity = self.gameState[otherEntityIndex]
                        
                        if (entity != otherEntity) and not(entity.entityCategory == 1 and otherEntity.entityCategory == 1) and (not(entity.tag == otherEntity.tag and (entity.entityCategory == 1 or otherEntity.entityCategory == 1))): #If projectiles are not colliding with eachother
                            theirRect = otherEntity.getRect()
                            if self.rectCollision(myRect, theirRect): #Check rectangle collision first

                                #SAT collision
                                myPolygon = entity.getShape()
                                theirPolygon = otherEntity.getShape()
                                collided, pushValue = collision.polygonCollide(myPolygon, theirPolygon)
                                if collided:
                                    entityExists = True
                                    if entity.entityCategory == 1:
                                        shouldDestroy = entity.hasHit()
                                        if shouldDestroy:
                                            self.gameState.pop(entityIndex)
                                            entityIndex -= 1
                                            entityExists = False
                                            
                                    if otherEntity.entityCategory == 1:
                                        shouldDestroy = otherEntity.hasHit()
                                        if shouldDestroy:
                                            self.gameState.pop(otherEntityIndex)
                                            otherEntityIndex -= 1

                                    if entityExists: #Prevents errors from tiggering
                                        if entity.getHasMoved(): #Only move if the entity moved into something
                                            entity.collisionShift(pushValue)
                                        
                        otherEntityIndex += 1
                                    
                entityType, x, y, angle = entity.getRender()
                entityType = networkPacker[entityType]
                updateToSend.append((entityType, round(x, 2), round(y, 2), round(angle, 2))) #Rounding shrinks the packets

                entityIndex += 1
            
            #Send data to clients
            self.gameSocket.postUpdate(updateToSend)
            
            deltaTime = pygame.time.get_ticks() - startTime

            if deltaTime > self.ticksMS:
                print("too slow", deltaTime)
                
            pygame.time.delay(max(self.ticksMS-deltaTime, 0))

    def runClient(self):
        global DEBUG
        pygame.init()
        self.renderer = renderer()
        self.canvas = pygame.display.set_mode(RESOLUTION)
        self.gameState = json.dumps((((),()),())) #cam, gamestate

        self.playerStats = {"basic attack":"Surge"}

        #Load images
        self.loadImages()
        
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
                    if event.key == pygame.K_q:
                        if self.playerStats["basic attack"] == "Surge":
                            self.playerStats["basic attack"] = "Spray"
                        elif self.playerStats["basic attack"] == "Spray":
                            self.playerStats["basic attack"] = "Hyper"
                        else:
                            self.playerStats["basic attack"] = "Surge"

                    if event.key == pygame.K_e:
                        if self.playerStats["basic attack"] == "Surge":
                            self.playerStats["basic attack"] = "Hyper"
                        elif self.playerStats["basic attack"] == "Hyper":
                            self.playerStats["basic attack"] = "Spray"
                        else:
                            self.playerStats["basic attack"] = "Surge"
                        
                    if event.key == pygame.K_SPACE:
                        myInputs.append((networkPacker["primaryFire"], networkPacker[self.playerStats["basic attack"]]))

                    if event.key == pygame.K_F7:
                        if DEBUG:
                            DEBUG = 0
                        else:
                            DEBUG = 1
                            
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
            self.renderHud()
            pygame.display.flip() #Update the screen
            deltaTime = pygame.time.get_ticks() - startTime
            print(deltaTime)
            
            for i in range(len(self.animations)):
                self.animations[i][2] += max(self.ticksCalculation, deltaTime)
                if self.animations[i][2] >= self.animations[i][3]:
                    self.animations[i][2] = self.animations[i][2] - self.animations[i][3]
                    self.animations[i][0] += 1
                    if self.animations[i][0] > self.animations[i][1]:
                        self.animations[i][0] = 0
            pygame.time.delay(max(self.ticksCalculation-deltaTime, 0))

class renderer:
    def __init__(self):
        self.centerX, self.centerY = RESOLUTION[0]/2, RESOLUTION[1]/2

    def draw(self, canvas, gameState):
        #gameState is a list of (entityType, x, y, angle)
        cameraPosition, gameState = gameState
        camX, camY = cameraPosition
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
                
                pointX = (x+sizes[sizeIndex]*math.cos(direction) - camX)*WIDTHSCALE + self.centerX
                pointY = (y+sizes[sizeIndex]*math.sin(direction) - camY)*LENGTHSCALE + self.centerY
                
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
