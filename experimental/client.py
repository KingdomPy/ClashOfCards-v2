import pygame, os
import main_menu, main_game
from lib import filePath

from twisted.internet import reactor
from lib.networking import client

MAIN_MENU = main_menu.scene
MAIN_GAME = main_game.scene

class gameClient:

    def __init__(self, resolution, graphics="low", debug=False):
        self.targetDeltaTime = 16 #Time between each frame in milliseconds (just over 60 FPS)

        pygame.init()
        self.surface = pygame.display.set_mode(resolution)
        self.graphics = graphics.lower()
        self.debug = debug

        self.connectedToNetwork = False
        self.networkProtocol = client.startConnection(self)

        self.setState(MAIN_MENU, "Main_Menu")
        self.dt = self.targetDeltaTime
        self.runClient()
        reactor.run()

    def runClient(self):
        startTime = pygame.time.get_ticks()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()

        #keys = pygame.key.get_pressed()
        isOpen = self.gameState.open #Boolean
        if isOpen:
            self.gameState.update(events, self.dt, self.graphics)
            pygame.display.flip() #Update the screen
        elif self.stateName == "Main_Menu": #Switch state
            self.setState(MAIN_GAME, "Main_Game", self.networkProtocol)

        timeElapsed = pygame.time.get_ticks() - startTime

        wait = max(self.targetDeltaTime - timeElapsed, 0)/1000
        self.dt = max(self.targetDeltaTime, timeElapsed)

        reactor.callLater(wait, self.runClient)

    def setState(self, state, stateName, params=None):
        self.gameState = state(self.targetDeltaTime)
        self.stateName = stateName
        if params != None:
            self.gameState.open(self.surface, params, debug=self.debug)
        else:
            self.gameState.open(self.surface, debug=self.debug)

FILERETRACTS = 2
config = filePath.loadConfig(filePath.setPath(filePath.getRootFolder(FILERETRACTS),["config.txt"]))
SERVER_IP = config["SERVER_IP"]
SERVER_PORT = config["SERVER_PORT"]
RESOLUTION = config["RESOLUTION"]
FPS = config["FPS"]
GRAPHICS = config["GRAPHICS"]
os.environ['SDL_VIDEO_CENTERED'] = '1'
debug = True
gameClient(RESOLUTION, GRAPHICS, debug)
