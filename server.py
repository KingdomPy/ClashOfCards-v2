from twisted.internet import reactor, protocol, task
from socket import gethostbyname, gethostname
from lib import filePath
from lib import LIMITobjects as game_objects
import pygame, os, sys, json

SERVER_IP = gethostbyname(gethostname())
SERVER_PORT = 5005
config = filePath.loadConfig(filePath.setPath(filePath.getRootFolder(2),["config.txt"]))
RESOLUTION = config["RESOLUTION"]
FPS = config["FPS"]
os.environ['SDL_VIDEO_CENTERED'] = '1'
debug = True

#Send 30 updates per second
#Client will smooth transition

class UdpServer(protocol.DatagramProtocol):
    def __init__(self, gameEngine):
        self.gameEngine = gameEngine #Connection to the engine
        self.clients = []
        
    def datagramReceived(self, data, address):
        self.clients.append(address)
        #print ("received {} from {}:%{}".format(data, host, port))
        #self.transport.write(data, address)
        data = json.loads(data.decode())
        delta, instruction = data
        friend = self.gameEngine.gameObjects[1]
        if instruction == 0:
            friend.moveForward(delta)
        elif instruction == 1:
            friend.rotate(delta, -1)
        elif instruction == 2:
            friend.rotate(delta, 1)

    def updateClients(self, update):
        for client in self.clients:
            self.transport.write(update, client)

class gameEngine:

    def __init__(self):
        player = game_objects.player("ally", {"name":"Nathan","directory":10,"canBeHit": True,"type":"Player", "address":1},(0,0,0), 30)
        friend = game_objects.player("ally", {"name":"Friend","directory":10,"canBeHit": True,"type":"Player", "address":1},(0,0,0), 30)
        self.timeElapsed = 0
        self.gameObjects = [player, friend]
        pygame.init()
        self.canvas = pygame.display.set_mode(RESOLUTION, pygame.SCALED)

    def beginHosting(self):
        gameLoop = task.LoopingCall(self.update)
        gameLoop.start(1/60)
        self.connection = UdpServer(self)
        reactor.listenUDP(SERVER_PORT, self.connection, interface=SERVER_IP)
        print("Server started on {}:{}".format(SERVER_IP, SERVER_PORT))
        reactor.run()
        
    def update(self):
        self.canvas.fill((255,255,255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        keys = pygame.key.get_pressed()
        player, friend = self.gameObjects
        delta = 16/1000
        if keys[pygame.K_w]:
            player.moveForward(delta)
        if keys[pygame.K_a]:
            player.rotate(delta, -1)
        if keys[pygame.K_d]:
            player.rotate(delta, 1)
        pygame.draw.rect(self.canvas, (0,0,0), (player.x, player.y, 10, 10))
        pygame.draw.rect(self.canvas, (0,0,0), (friend.x, friend.y, 10, 10))                                    
        pygame.display.flip()
        self.timeElapsed += 16
        if self.timeElapsed > 33: #Send 30 updates per second
            self.timeElapsed %= 33
            update = []
            for entity in self.gameObjects:
                data = [0, entity.x, entity.y]
                update.append(data)
            update = json.dumps(update)
            self.connection.updateClients(update.encode())
            
        
engine = gameEngine()
engine.beginHosting()
