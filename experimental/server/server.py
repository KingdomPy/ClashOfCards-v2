from twisted.internet import reactor, protocol
from twisted.protocols import basic
from lib import gameObjects, contentLoader
import json
from socket import gethostname, gethostbyname

SERVER_IP = gethostbyname(gethostname())
SERVER_PORT = 5005
ticksPerSecond = 30
dt = 1/ticksPerSecond

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
    reverseEntityCodes[length - 1] = key
for key in entities[1]: #Add Projectiles
    length = len(entityCodes)
    entityCodes[key] = length
    reverseEntityCodes[length - 1] = key

def packetUnpacker(packet):
    try:
        packet = json.loads(packet)
    except Exception as e:
        print(packet)
        print(e)
    packet[0] = reverseOpCodes[packet[0]]
    instruction = packet[0]
    if instruction == "addEntity":
        packet[1] = reverseOpCodes[packet[1]]
    elif instruction == "input":
        for i in range(len(packet)-1):
            packet[i+1] = reverseOpCodes[packet[i+1]]
    return packet

class entityList:
    def __init__(self):
        self.entities = {}

    def getEntities(self):
        return self.entities

    def addEntity(self, entityName, entityClass, position=(0,0)):
        entityId = len(self.entities)
        newEntity = gameObjects.entity(entityId, entityName, entityClass)
        newEntity.setPosition(position)
        self.entities[entityId] = newEntity
        return entityId

    def removeEntity(self, entityId):
        del self.entities[entityId]

    def getEntity(self, entityId):
        return self.entities[entityId]

connectedUsers = {}
currentEntities = entityList()

class MyServer(basic.LineReceiver):
    def connectionMade(self):
        connectedUsers[self] = {}
        addr = self.transport.getPeer()
        print("({}:{}) has connected".format(addr.host, addr.port))
            
    def lineReceived(self, data):
        data = packetUnpacker(data.decode())
        opCode = data.pop(0)
        if opCode == "login":
            if connectedUsers[self] == {}:
                connectedUsers[self] = {"entityId":None, "playing":False, "hasInput":False}
                addr = self.transport.getPeer()
                print("({}:{}) has logged in".format(addr.host, addr.port))
                packet = json.dumps((opCodes["loginSuccess"],))
                self.sendLine(packet.encode())
        elif opCode == "join":
            entities = currentEntities.getEntities()
            for entityId in entities:
                entity = entities[entityId]
                entityName, entityType = entity.entityName, entity.entityType
                packet = (opCodes["addEntity"], entityId, entity.getPositionAngle(), entityName, entityCodes[entityType])
                packet = json.dumps(packet)
                packet = packet.encode()
                self.sendLine(packet)

            packet = json.dumps((opCodes["joinSuccess"],))
            self.sendLine(packet.encode())
                
            userName, userClass = data
            entityId = currentEntities.addEntity(userName, userClass)
            connectedUsers[self]["entityId"] = entityId
            connectedUsers[self]["playing"] = True
            packet = (opCodes["addEntity"], entityId, (0, 0, 0, 0), userName, entityCodes[userClass])
            packet = json.dumps(packet)
            packet = packet.encode()   
            for client in connectedUsers: #Send new player to all online players
                if connectedUsers[client]["playing"]:
                    client.sendLine(packet)
                  
        elif opCode == "input":
            hasInput = connectedUsers[self]["hasInput"]
            if not hasInput:
                userId = connectedUsers[self]["entityId"]            
                entity = currentEntities.getEntity(userId)
                for userInput in data:
                    entity.addInput(userInput)
                connectedUsers[self]["hasInput"] = True

    def sendData(self, data):
        self.sendLine(data)
    
    def connectionLost(self, reason):
        addr = self.transport.getPeer()
        if connectedUsers[self] != {}:
            entityId = connectedUsers[self]["entityId"]
            if entityId != None:
                currentEntities.removeEntity(entityId)
                del connectedUsers[self]
                packet = (opCodes["removeEntity"], entityId)
                packet = json.dumps(packet)
                packet = packet.encode()
                for client in connectedUsers: #Tell all players to delete the entity
                    if connectedUsers[client]["playing"]:
                        client.sendLine(packet)
            else:
                del connectedUsers[self]
        print("({}:{}) has disconnected".format(addr.host, addr.port))

class MyServerFactory(protocol.Factory):
    protocol = MyServer

def updateEntities():
    updatesToSend = []
    entities = currentEntities.getEntities()
    for entityId in entities:
        update = entities[entityId].update(dt)
        if update != 0:
            updatesToSend.append((entityId, update))
    if len(updatesToSend) > 0:
        packet = (opCodes["updateEntity"], updatesToSend)
        packet = json.dumps(packet)
        packet = packet.encode()
        for client in connectedUsers:
            if connectedUsers[client]["playing"]:
                client.sendLine(packet)
                connectedUsers[client]["hasInput"] = False
    reactor.callLater(1/ticksPerSecond, updateEntities)

factory = MyServerFactory()
reactor.listenTCP(SERVER_PORT, factory, interface=SERVER_IP)
updateEntities()
print("Server started on {}:{}".format(SERVER_IP, SERVER_PORT))
reactor.run()
