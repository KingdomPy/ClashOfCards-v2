from twisted.internet import reactor, protocol
from twisted.protocols import basic

from lib import contentLoader
import pygame, json
from socket import gethostname, gethostbyname

SERVER_IP = gethostbyname(gethostname())
SERVER_PORT = 5005

opCodes = {
    "addEntity":0,
    "removeEntity":1,
    "updateEntity":2,
    "input":3,
    "upKey":4,
    "downKey":5,
    "leftKey":6,
    "rightKey":7,
    "login":8,
    "loginSuccess":9,
    "join":10,
    "joinSuccess":11,
}

reverseOpCodes = {  
}

for key in opCodes:
    reverse = opCodes[key]
    reverseOpCodes[reverse] = key

entityCodes = {
}

reverseEntityCodes = {
}

entities  = contentLoader.loadEntities()
orderOfEntities = []
for key in entities[0]: #Add Enemies
    length = len(entityCodes)
    entityCodes[key] = length
    reverseEntityCodes[length] = key
for key in entities[1]: #Add Projectiles
    length = len(entityCodes)
    entityCodes[key] = length
    reverseEntityCodes[length] = key

def packetUnpacker(packet):
    packet = json.loads(packet)
    packet[0] = reverseOpCodes[packet[0]]
    instruction = packet[0]
    if instruction == "addEntity":
        #addEntity, Id, Position, Name, Class
        packet[4] = reverseEntityCodes[packet[4]]
    elif instruction == "input":
        packet[1] = reverseOpCodes[packet[1]]
    return packet

class entityList:
    def __init__(self):
        self.entities = []

    def addEntity(self, entity):
        pass

    def removeEntity(self, entityId):
        pass
    
    def updateEntity(self, entityId, update):
        pass

class MyClient(basic.LineReceiver):
    def __init__(self, factory, gameClient):
        self.factory = factory
        self.gameClient = gameClient
        self.connected = False
    
    def connectionMade(self):
        self.connected = True
        print("Successfully connected to the server")
        #packet = (opCodes["login"],"Nathan","Player") #Name, Class
        self.loggedIn = False
        self.inGame = False
        packet = (opCodes["login"],)
        packet = json.dumps(packet)
        self.sendLine(packet.encode())

    def lineReceived(self, data):
        data = packetUnpacker(data.decode())
        opCode = data.pop(0)
        if opCode == "loginSuccess":
            self.loggedIn = True
        elif opCode == "joinSuccess":
            self.inGame = True
        elif opCode == "addEntity":
            self.gameClient.gameState.addEntity(*data)
        elif opCode == "removeEntity":
            self.gameClient.gameState.removeEntity(data[0])
        elif opCode == "updateEntity":
            data = data[0]
            for update in data:
                entityId, state = update
                self.gameClient.gameState.updateState(entityId, state)

    def sendData(self, data):
        if self.connected:
            self.sendLine(data.encode())
    
class MyClientFactory(protocol.ClientFactory):
    def __init__(self, gameClient):
        self.protocol = MyClient(self, gameClient)

    def startedConnecting(self, connector):
        print("Connecting to server...")

    def buildProtocol(self, addr):
        return self.protocol

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed")

    def clientConnectionLost(self, connector, reason):
        print("Connection lost")

def startConnection(gameClient):
    factory = MyClientFactory(gameClient)
    reactor.connectTCP(SERVER_IP, SERVER_PORT, factory)
    return factory.protocol
