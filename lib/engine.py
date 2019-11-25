import pygame
import math
from lib import LIMITobjects, LIMITinterface, filePath, network
import _thread, socket, json, zlib

# Handles every entity
# Connects entities to each other
# Controls what entities are rendered
# Controls what data is sent to the interface
# Controls the flow of the main game

# Constants
FILERETRACTS = 2

# Functions
def distancePointPoint(point1, point2):
    x1 = point1[0]
    y1 = point1[1]
    x2 = point2[0]
    y2 = point2[1]
    return x2 - x1, y2 - y1

class engine:
    def __init__(self, surface, dimensions, controls, config, debug=False):
        if debug:
            print("Game Engine initiating.")
            
        #Set attributes
        self.SERVER_IP = config["SERVER_IP"]
        self.SERVER_PORT = config["SERVER_PORT"]
        self.debug = debug
        self.surface = surface
        self.dimensions = dimensions
        self.entities = []
        self.projectiles = []
        self.party = []
        self.instance = "map"
        self.baracksAnimation = [0,0,0]
        self.pausedInstances = ("paused", "interaction", "baracks")
        self.controls = controls
        self.path = filePath.getRootFolder(FILERETRACTS)
        self.entityGroups = {"enemy":("square","triangle","entity"), "ally":("player",), "object":("location","npc")}
        self.FPS = config["FPS"]
        self.currentFPS = config["FPS"] # Assume it can initially run at the target FPS
        self.deltaMin = round(1000/self.FPS)

        self.frameCount = 0
        self.fpsTimer = 0
        self.newFPS = config["FPS"] # Assume it can initially run at the target FPS
        
        # Load assets
        self.mainFont = pygame.font.Font(filePath.setPath(self.path,["assets","fonts","Coda-Regular.ttf"]), 30)
        
        # Load required parts of the engine
        self.player = None
        self.selectedCommand = 0
        self.commandMenu = [0]
        self.focus = [0, 0]
        self.freeFocus = [0, 0] # The focus of the camera in free camera mode
        self.cameraSpeed = 500 # The speed of the free camera in metres per second
        self.cameraMode = 0 #0 = free camera
        self.camera = camera(surface, dimensions, debug)
        self.hud = LIMITinterface.display(surface, dimensions, debug)

        # Start the network socket
        if self.debug:
            self.networkType = "Host"
            self.currentImage = []
        else:
            self.networkType = "Peer"
            self.lastFrame = []
        self.networkSocket = None
        self.connectedAddresses = []
        self.activeAddresses = []
        self.peerInputs = []

        if self.networkType == "Host":
            self.networkSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.SERVER_IP = socket.gethostbyname(socket.gethostname())
            self.networkSocket.bind((self.SERVER_IP,self.SERVER_PORT))
            if self.debug:
                print("SERVER OPENED ON",self.SERVER_IP,":",self.SERVER_PORT)
            _thread.start_new_thread(self.peerGateway, ())
        else:
            self.currentFrame = []
            self.frameSkipped = []
            self.networkSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.networkSocket.connect((self.SERVER_IP,self.SERVER_PORT))
            _thread.start_new_thread(self.peerConnection, ())

    def setFocus(self, target):
        self.focus = target
        self.camera.setFocus(target)

    def setCameraMode(self, mode):
        self.cameraMode = mode
        self.camera.setMode(mode)

    def addEntity(self, tag, stats={}, position=(0,0,0), size=30):
        # stats["directory"] = 0/1 = enemies/projectiles
        if stats["type"] == "Player":
            entity = LIMITobjects.player(tag, stats, position, size)
            self.player = entity
        elif stats["type"] == "peerPlayer":
            entity = LIMITobjects.player(tag, stats, position, size)
            self.party.append(entity)
        else:
            entity = LIMITobjects.entity(tag, stats, position, size)
        self.entities.append(entity)

    def addProjectile(self, tag, stats={}, position=(0,0,0), size=30):
        projectile = LIMITobjects.projectile(tag, stats, position, size)
        self.projectiles.append(projectile)

    def peerGateway(self):
        while True:
            packet, address = self.networkSocket.recvfrom(4096)  # Wait for data
            try:
                if not(address in self.connectedAddresses): # Check if it is from a new connection
                    self.connectedAddresses.append(address)
                    self.activeAddresses.append(0) # Set inactive counter to 0
                    if self.debug:
                        print("NEW CONNECTION FROM",address)

                packet = packet.decode() # Decode the message (bytes to str)
                packet = json.loads(packet) # Convert the data from a string to a list

                if network.networkDict[packet[0]] == "GETIMAGE":

                    if len(str(packet[1])) == 1:
                        if network.networkDict[packet[1]] == "PLAYER": # Command to follow the player
                            for i in range(len(self.party)):  # See if a player exists
                                if self.party[i].stats["type"] == "peerPlayer":
                                    if self.party[i].stats["address"] == address:
                                        entityFound = i
                            packet[1] = self.party[entityFound].getDomain()[0]

                    cameraData, minimapData = self.camera.getImage(packet[1], self.currentImage) # Complete the instruction
                    packet = json.dumps((cameraData, minimapData)).encode()
                    packet = zlib.compress(packet)
                    self.networkSocket.sendto(packet, address) #Send the data

                elif network.networkDict[packet[0]] == "SETPLAYER":
                    entityFound = -1
                    for i in range(len(self.party)): # See if a player exists
                        if self.party[i].stats["type"] == "peerPlayer":
                            if self.party[i].stats["address"] == address:
                                entityFound = i
                    if entityFound == -1: # Add the player if it has not been found
                        print(address, "has joined as a new player.")
                        self.addEntity("ally",{"name":"Nathan","directory":10,"type":"peerPlayer","canBeHit":True,"address":address},(0,0,0))
                        entityFound = len(self.party) - 1

                    x,y = packet[1][0]
                    angle = packet[1][1]
                    self.peerInputs.append((entityFound, (x,y,angle)))

            except Exception as error:
                print(error)
                self.networkSocket.sendto("0".encode(), address)

    def peerConnection(self):
        self.framing = False
        while True:
            startTime = pygame.time.get_ticks()
            if not(self.player == None): # Send the coordinates of the player
                self.networkSocket.send(json.dumps([network.revNetworkDict["SETPLAYER"], [self.player.getDomain()[0], self.player.getVisualAngle()]]).encode())
            if self.cameraMode == 0:
                self.setFocus(self.freeFocus)
                self.networkSocket.send(json.dumps([network.revNetworkDict["GETIMAGE"], self.focus]).encode())  # Request an image
            else:
                if not (self.player == None):
                    self.networkSocket.send(json.dumps([network.revNetworkDict["GETIMAGE"], network.revNetworkDict["PLAYER"]]).encode())  # Request an image that follows the player
                else:
                    self.networkSocket.send(json.dumps([network.revNetworkDict["GETIMAGE"], self.focus]).encode())  # Request an image

            packet = self.networkSocket.recv(32768)
            packet = zlib.decompress(packet)
            packet = packet.decode()
            try: # Attempt to render the image, if it fails use the previous frame
                packet = json.loads(packet)
                cameraData, minimapData = packet[0], packet[1]  # Split the packet up
                while self.framing:
                    pass
                self.currentFrame = cameraData
                self.frameSkipped = cameraData
            except Exception as error:
                self.currentFrame = self.frameSkipped

            timeElapsed = pygame.time.get_ticks() - startTime
            pygame.time.delay(max(self.deltaMin-timeElapsed,0))            

    def getClock(self, startTime):
        delta = pygame.time.get_ticks() - startTime
        clockSignal = max(self.deltaMin, delta)
        delta = max(self.deltaMin, delta) / 1000
        return delta, clockSignal
            
    def update(self):
        # Start Clock
        startTime = pygame.time.get_ticks()
        
        # Check Input
        self.handleInput() # self.inputs store the player's inputs

        if self.instance == "map": # Check if the engine is in the combat instance
            delta = pygame.time.get_ticks() - startTime
            clockSignal = max(self.deltaMin, delta)
            delta = max(self.deltaMin, delta) / 1000

            while len(self.inputs) > 0:  # Update the player according their inputs
                command = self.inputs.pop()
                if command == "up":
                    self.freeFocus[1] -= self.cameraSpeed * delta
                elif command == "down":
                    self.freeFocus[1] += self.cameraSpeed * delta
                elif command == "left":
                    self.freeFocus[0] -= self.cameraSpeed * delta
                elif command == "right":
                    self.freeFocus[0] += self.cameraSpeed * delta
                elif command == "forward":
                    self.player.moveForward(delta)
                elif command == "turnLeft":
                    self.player.rotate(delta, -1)
                elif command == "turnRight":
                    self.player.rotate(delta, 1)
                elif command == "activateCommand":
                    response = self.player.activateCommand(self.selectedCommand)
                    if response != 0:
                        if response[0] == "projectile":  # Instruction from the player to shoot a projectile
                            data = response[1]
                            if self.networkType == "Host":
                                self.addProjectile("ally", {"name": data[0], "directory": 1, "type": data[0]}, (
                                self.player.getDomain()[0][0], self.player.getDomain()[0][1], self.player.getVisualAngle()))
                            else: # Send fire bullet command
                                pass

                        elif response[0] == "selectedMove":
                            self.commandMenu.append(self.selectedCommand)
                            self.selectedCommand = response[1]
                elif command == "returnCommand":
                    if len(self.commandMenu) > 1:
                        self.selectedCommand = self.commandMenu.pop()
                        self.player.setCommandOptions(("Attack","Magic","Items","Upgrade"))

            if self.networkType == "Host":
                self.detectBulletCollisions()
            
                # Update Entities
                self.imageData = []

                while len(self.peerInputs) > 0: # Handle input from connected users
                    command = self.peerInputs.pop()
                    slot = command[0]
                    x,y,angle = command[1]
                    self.party[slot].setLocation((x,y),angle)

                i = 0
                while i < len(self.entities): # Update every non-projectile entity
                    # signal = response from the entity to the engine
                    signal = self.entities[i].update(delta, clockSignal)
                    if signal == 0: # Delete the entity
                        self.entities.pop(i)
                    else:
                        self.imageData.append((self.entities[i].render(),self.entities[i].getDomain()))
                        i += 1

                i = 0
                while i < len(self.projectiles): # Update all projectile type entities
                    # signal = response from the entity to the engine
                    signal = self.projectiles[i].update(delta, clockSignal)
                    if signal == 0:  # Delete the entity
                        self.projectiles.pop(i)
                    else:
                        self.imageData.append((self.projectiles[i].render(), self.projectiles[i].getDomain()))
                        i += 1

                self.imageData = json.dumps(self.imageData) # Allows me to pass the attribute by value and not reference
                self.currentImage = self.imageData # Store a copy that is never erased but only replaced

                if self.cameraMode == 0:
                    self.setFocus(self.freeFocus)
                else:
                    if not (self.player == None):
                        self.setFocus(self.player.getDomain()[0])

                cameraData, minimapData = self.camera.getImage(self.focus, self.imageData)
                self.camera.update(cameraData) # Render Entities

            else:
                self.framing = True
                self.camera.update(self.currentFrame) # Render Entities
                self.framing = False

            # Update the hud
            if not(self.player == None):
                self.hud.update(self.player.getCommandOptions(),[(0,0),(0,0),(0,0),(0,0),(0,0)],self.selectedCommand)
        
            # Display The Fps
            fpsDisplay = self.mainFont.render("FPS:"+str(self.currentFPS), True, (20,20,20))
            location = fpsDisplay.get_rect()
            location.topleft = self.surface.get_rect().topleft
            self.surface.blit(fpsDisplay,location)

            fpsDisplay = self.mainFont.render("FPS:" + str(self.newFPS), True, (20, 20, 20))
            location = fpsDisplay.get_rect()
            location.topright = self.surface.get_rect().topright
            self.surface.blit(fpsDisplay, location)

            pygame.display.flip()
            
            # End The Clock
            timeElapsed = pygame.time.get_ticks() - startTime
            if timeElapsed > 0:
                self.currentFPS = min(self.FPS,round(1000/timeElapsed))
            else:
                self.currentFPS = self.FPS

            if self.networkType == "Peer":
                delta, clockSignal = self.getClock(startTime)
                self.player.update(delta, clockSignal)

            self.fpsTimer += timeElapsed
            if self.fpsTimer > 1000:
                self.newFPS = self.frameCount
                self.frameCount = 0
                self.fpsTimer = 0
            else:
                self.frameCount += 1

            # Pause The Engine
            pygame.time.delay(max(self.deltaMin-timeElapsed,0))
            # Clear The Screen
            self.surface.fill((255,255,255))

    def detectBulletCollisions(self):
        i = 0
        while i < len(self.entities):
            entityDomain = self.entities[i].getDomain()
            j = 0
            while j < len(self.projectiles):
                if self.entities[i].getTag() != self.projectiles[j].getTag(): # They can only collide if they are not the same type
                    bulletDomain = self.projectiles[j].getDomain()
                    distanceX, distanceY = distancePointPoint(entityDomain[0], bulletDomain[0])
                    distance = math.sqrt(distanceX**2 + distanceY**2)
                    if distance <= entityDomain[1]+bulletDomain[1]: # Only check for collisions if they are within the radius of each other
                        hasCollided = self.entities[i].getBulletCollision(((distanceX,distanceY),bulletDomain[1]), self.projectiles[j].getDamage())
                        if not(hasCollided == False):
                            if self.projectiles[j].hasHit() == 0: # Let the projectile know it has hit something
                                self.projectiles.pop(j)
                            if hasCollided[1] == True: # A condition checking if the enemy has died from the hit
                                self.entities.pop(i) # Remove the entity that had died
                                i -= 1 # Prevent an entity from being skipped
                                j = len(self.projectiles) # Break the loop
                        else:
                            j += 1
                    else:
                        j += 1
                else:
                   j += 1
            i += 1


    def handleInput(self):
        self.inputs = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.cameraMode == 1:
                        self.setCameraMode(0)
                    else:
                        self.setCameraMode(1)
                if event.key == pygame.K_q:
                    self.selectedCommand -= 1
                    self.selectedCommand %= 4
                if event.key == pygame.K_e:
                    self.selectedCommand += 1
                    self.selectedCommand %= 4
                if event.key == pygame.K_j:
                    self.inputs.append("activateCommand")
                if event.key == pygame.K_k:
                    self.inputs.append("returnCommand")
                        
        keys = pygame.key.get_pressed()

        if not(self.player == None):
            if keys[pygame.K_w]:
                self.inputs.append("forward")
            if keys[pygame.K_a]:
                self.inputs.append("turnLeft")
            if keys[pygame.K_d]:
                self.inputs.append("turnRight")

        if self.cameraMode == 0:
            if keys[pygame.K_UP]:
                self.inputs.append("up")
            if keys[pygame.K_DOWN]:
                self.inputs.append("down")
            if keys[pygame.K_RIGHT]:
                self.inputs.append("right")
            if keys[pygame.K_LEFT]:
                self.inputs.append("left")

class camera:
    def __init__(self, surface, dimensions, debug):
        self.debug = debug
        self.surface = surface
        self.width = dimensions[0]
        self.length = dimensions[1]
        self.boundary = [self.width/2, self.length/2]
        self.focus = (0,0)
        self.mode = 0 #Free camera
        self.colour = (0,0,0)
        self.path = filePath.getRootFolder(FILERETRACTS)
        self.locationFont = pygame.font.Font(filePath.setPath(self.path,["assets","fonts","Kingdom_Hearts_Font.ttf"]), 50)
        self.mainFont = pygame.font.Font(filePath.setPath(self.path,["assets","fonts","Coda-Regular.ttf"]), 30)

    def setFocus(self, focus):
        self.focus = focus

    def setMode(self, mode):
        self.mode = mode

    def getImage(self, focus, entities): #Returns objectsToDraw and minimapData
        entities = json.loads(entities)
        objectsToDraw = []
        minimapData = []
        #Set the camera's shift
        camShiftX = self.width/2
        camShiftY = self.length/2
        #See if monsters are close enough to be rendered
        #data format:
        for entity in entities:
            image = entity[0] #Image, colour and tag
            domain = entity[1] #Coordinates and size
            xDistance,yDistance = distancePointPoint(focus,domain[0]) #Distance from the focus
            if abs(xDistance) < self.boundary[0]*4 + domain[1] and abs(yDistance) < self.boundary[1]*4 + domain[1]: #If close enough to be on the minimap
                minimapData.append((image[2], (xDistance, yDistance), domain[1])) #Tag, distance from focus, size
                if abs(xDistance) < self.boundary[0] + domain[1] and abs(yDistance) < self.boundary[1] + domain[1]: #If on screen
                    for point in image[0]:
                        point[0] += xDistance+camShiftX #Translate x coordinates to the screen
                        point[1] += yDistance+camShiftY #Translate y coordinates to the screen
                    objectsToDraw.append((image[0], image[1])) #Points, Colour
                    
        return objectsToDraw, minimapData

    def update(self, cameraData):
        for entity in cameraData:
            pygame.draw.aalines(self.surface, entity[1], True, entity[0])

        if self.mode == 0: #free camera
            #Draw the camera's cursor
            pygame.draw.line(self.surface, (20,20,20), (0, self.boundary[1]), (self.width, self.boundary[1]))
            pygame.draw.line(self.surface, (20,20,20), (self.boundary[0], 0), (self.boundary[0], self.length))
            coordinates = self.mainFont.render(str(self.focus), True, (20,20,20))
            location = coordinates.get_rect()
            location.bottomright = self.surface.get_rect().bottomright
            self.surface.blit(coordinates,location)
