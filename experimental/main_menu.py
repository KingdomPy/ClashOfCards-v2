import pygame
import json, math
from lib import filePath
FILERETRACTS = 2
class scene:
    def __init__(self, targetDeltaTime):
        self.targetDeltaTime = targetDeltaTime

    def open(self, surface, debug=False): #Load assets
        self.surface = surface
        self.dimensions = self.surface.get_size()
        self.debug = debug

        self.dt = 16 #milliseconds per frame
        self.waitingTime = self.dt/self.targetDeltaTime
        
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.mouse.set_visible(False)

        self.path = filePath.getRootFolder(FILERETRACTS)

        self.fontMain = pygame.font.Font(filePath.setPath(self.path,["assets","fonts","Coda-Regular.ttf"]), 24)
        self.fontSub = pygame.font.Font(filePath.setPath(self.path,["assets","fonts","Coda-Regular.ttf"]), 20)

        self.menuSounds = [
            pygame.mixer.Sound(filePath.setPath(self.path,["assets","sounds","system sound effects","error.wav"])),
            pygame.mixer.Sound(filePath.setPath(self.path,["assets","sounds","system sound effects","menu back.wav"])),
            pygame.mixer.Sound(filePath.setPath(self.path,["assets","sounds","system sound effects","menu open.wav"])),
            pygame.mixer.Sound(filePath.setPath(self.path,["assets","sounds","system sound effects","menu scroll.wav"])),
            pygame.mixer.Sound(filePath.setPath(self.path,["assets","sounds","system sound effects","select.wav"])),
        ]

        menuMusic = pygame.mixer.music.load(filePath.setPath(self.path,["assets","sounds","music","kh3-Dearly Beloved.mp3"]))

        self.musicStarted = False

        self.emblems = [
            pygame.image.load(filePath.setPath(self.path,["assets","player","emblems","vanguard.png"])).convert_alpha(),
            pygame.image.load(filePath.setPath(self.path,["assets","player","emblems","engineer.png"])).convert_alpha(),
            pygame.image.load(filePath.setPath(self.path,["assets","player","emblems","stealth.png"])).convert_alpha(),
        ]

        for i in range(len(self.emblems)): #Scale images
            self.emblems[i] = pygame.transform.scale(self.emblems[i], self.dimensions)
        
        self.controls = {"up":[pygame.K_w], "left":[pygame.K_a], "right":[pygame.K_d], "down":[pygame.K_s],
                         "SQUARE":[pygame.K_j], "CIRCLE":[pygame.K_l,1], "CROSS":[pygame.K_k,0], "TRIANGLE":[pygame.K_i,3],
                         "start":[pygame.K_p,7], "home":[pygame.K_ESCAPE,6],
                         "L1":[pygame.K_q,4], "R1":[pygame.K_e,5]}

        self.playSounds = 1
        self.playMusic = 1
        self.customCursor = 1

        #Start up animation
        self.startupImage = pygame.image.load(filePath.setPath(self.path,["assets","title screen","logo.png"])).convert_alpha()
        self.startupImage = pygame.transform.scale(self.startupImage, self.dimensions)
        self.startupRect = self.startupImage.get_rect()
        self.startupRect.center = (round(self.dimensions[0]/2), round(self.dimensions[1]/2))

        #Title screen
        self.background = pygame.image.load(filePath.setPath(self.path,["assets","title screen","overlay.png"])).convert_alpha()
        self.background = pygame.transform.scale(self.background, self.dimensions)
        
        self.cursor = pygame.image.load(filePath.setPath(self.path,["assets","background","cursor.png"]))
        self.cursor = pygame.transform.scale(self.cursor, (40,40))

        self.cursorTouching = [None]

        self.instance = "main screen" #Controls which UI is loaded

        self.savedData = self.loadSaves()

        #Calculations needed for graph coordinates
        boxSpace = self.dimensions[1]/3 - 110
        boxShift = (boxSpace - 3*35)/2 +self.dimensions[1]/3 +70
        boxShift2 = (boxSpace - 2*35)/2 +self.dimensions[1]/3 +70
        #i*45+boxShift  #Box Widths = 168, 242, 119

        self.graph = {
            "NEW GAME":{"up":"CONFIG","down":"LOAD","value":(self.dimensions[0]-200, self.dimensions[1]-4.6*self.dimensions[1]/20 +5),"next":"Normal","previous":""}, #Controls where the controller should take the cursor
            "LOAD":{"up":"NEW GAME","down":"CONFIG","value":(self.dimensions[0]-200, self.dimensions[1]-3.2*self.dimensions[1]/20 +5),"next":"save1","previous":""},
            "CONFIG":{"up":"LOAD","down":"NEW GAME","value":(self.dimensions[0]-200, self.dimensions[1]-1.8*self.dimensions[1]/20 +5),"next":"Sound","previous":""},
            
            "Normal":{"up":"Extreme","down":"Hard","value":(self.dimensions[0]*0.25+75, boxShift),"next":"save1","previous":"NEW GAME"},
            "Hard":{"up":"Normal","down":"Extreme","value":(self.dimensions[0]*0.25+75, 45+boxShift),"next":"save1","previous":"NEW GAME"},
            "Extreme":{"up":"Hard","down":"Normal","value":(self.dimensions[0]*0.25+75, 90+boxShift),"next":"save1","previous":"NEW GAME"},

            "save1":{"up":"save6","down":"save2","value":(self.dimensions[0]*0.12, self.dimensions[1]*0.25),"next":"Yes","previous":""},
            "save2":{"up":"save1","down":"save3","value":(self.dimensions[0]*0.12, self.dimensions[1]*0.35),"next":"Yes","previous":""},
            "save3":{"up":"save2","down":"save4","value":(self.dimensions[0]*0.12, self.dimensions[1]*0.45),"next":"Yes","previous":""},
            "save4":{"up":"save3","down":"save5","value":(self.dimensions[0]*0.12, self.dimensions[1]*0.55),"next":"Yes","previous":""},
            "save5":{"up":"save4","down":"save6","value":(self.dimensions[0]*0.12, self.dimensions[1]*0.65),"next":"Yes","previous":""},
            "save6":{"up":"save5","down":"save1","value":(self.dimensions[0]*0.12, self.dimensions[1]*0.75),"next":"Yes","previous":""},

            "Sound":{"up":"Custom Cursor","down":"Music","value":(self.dimensions[0]*0.25+112, boxShift),"next":"Sound","previous":"CONFIG"},
            "Music":{"up":"Sound","down":"Custom Cursor","value":(self.dimensions[0]*0.25+112, 45+boxShift),"next":"Music","previous":"CONFIG"},
            "Custom Cursor":{"up":"Music","down":"Sound","value":(self.dimensions[0]*0.25+112, 90+boxShift),"next":"Custom Cursor","previous":"CONFIG"},

            "Yes":{"up":"No","down":"No","value":(self.dimensions[0]*0.25+56.5, boxShift2),"next":"","previous":""},
            "No":{"up":"Yes","down":"Yes","value":(self.dimensions[0]*0.25+56.5, 45+boxShift2),"next":"","previous":""},
        }
        self.currentNode = "NEW GAME"

        #Gradients
        self.gradient = pygame.Surface(self.dimensions, pygame.SRCALPHA)
        optionsRect = (self.dimensions[0]*0.4, self.dimensions[1]/20) #Constant for ui sizes 
        self.rectangleSurface = pygame.Surface(optionsRect, pygame.SRCALPHA)
        self.squareSurface = pygame.Surface((optionsRect[1], optionsRect[1]), pygame.SRCALPHA)
        self.highlightSurface = pygame.Surface((optionsRect[1]*0.6, optionsRect[1]*0.6), pygame.SRCALPHA)
        self.lineSurface = pygame.Surface((self.dimensions[0]-30, 3), pygame.SRCALPHA)
        self.uiBox = pygame.Surface((self.dimensions[0], self.dimensions[1]/3), pygame.SRCALPHA)
        self.uiBox.fill((0,0,0,170))
        self.saveImage = pygame.Surface((self.dimensions[0]*0.8, self.dimensions[1]*0.1), pygame.SRCALPHA)
        self.saveImageLine = pygame.Surface((self.dimensions[0]*0.8, 3), pygame.SRCALPHA)

        #draw main option pre-calculations
        self.yCalculations = [self.dimensions[1] - 1.8*optionsRect[1], self.dimensions[1] - 3.2*optionsRect[1], self.dimensions[1] - 4.6*optionsRect[1]]
        self.mainOptionCalculations = [
            ((self.dimensions[0]+1-optionsRect[0], self.yCalculations[0]), (30, self.yCalculations[0]), (30+optionsRect[1]*0.2, self.yCalculations[0]+optionsRect[1]*0.2), (30, self.yCalculations[0]+optionsRect[1]-3)),
            ((self.dimensions[0]+1-optionsRect[0], self.yCalculations[1]), (30, self.yCalculations[1]), (30+optionsRect[1]*0.2, self.yCalculations[1]+optionsRect[1]*0.2), (30, self.yCalculations[1]+optionsRect[1]-3)),
            ((self.dimensions[0]+1-optionsRect[0], self.yCalculations[2]), (30, self.yCalculations[2]), (30+optionsRect[1]*0.2, self.yCalculations[2]+optionsRect[1]*0.2), (30, self.yCalculations[2]+optionsRect[1]-3))
        ]

        #draw ui box pre-calculations
        self.uiBoxCalculations = [
            (0,self.dimensions[1]/3),
            ((0, self.dimensions[1]/3-5), (self.dimensions[0], self.dimensions[1]/3 -5)),
            ((0, 2*self.dimensions[1]/3), (self.dimensions[0], 2*self.dimensions[1]/3)),
            (self.dimensions[0]/2, 2*self.dimensions[1]/3 - 25),
            (self.dimensions[0]/2, self.dimensions[1]/3 + 30),
            self.dimensions[1]/3 - 110,
            self.dimensions[1]/3 +70,
            self.dimensions[0]*0.25,
        ]

        #load menu pre-calculations
        self.loadMenuCalculations = [
            pygame.Rect(self.dimensions[0]*0.1, self.dimensions[1]*0.2, self.dimensions[0]*0.8, self.dimensions[1]*0.6),
            self.dimensions[1]*0.1,
            pygame.Rect(self.dimensions[0]*0.1, self.dimensions[1]*0.2, self.dimensions[0]*0.8, self.dimensions[1]*0.1),
            pygame.Rect(self.dimensions[0]*0.1, self.dimensions[1]*0.2 +self.dimensions[1]*0.1, self.dimensions[0]*0.8, self.dimensions[1]*0.1),
            pygame.Rect(self.dimensions[0]*0.1, self.dimensions[1]*0.2 +self.dimensions[1]*0.2, self.dimensions[0]*0.8, self.dimensions[1]*0.1),
            pygame.Rect(self.dimensions[0]*0.1, self.dimensions[1]*0.2 +self.dimensions[1]*0.3, self.dimensions[0]*0.8, self.dimensions[1]*0.1),
            pygame.Rect(self.dimensions[0]*0.1, self.dimensions[1]*0.2 +self.dimensions[1]*0.4, self.dimensions[0]*0.8, self.dimensions[1]*0.1),
            pygame.Rect(self.dimensions[0]*0.1, self.dimensions[1]*0.2 +self.dimensions[1]*0.5, self.dimensions[0]*0.8, self.dimensions[1]*0.1),
        ]

        self.loadMenuYCalculations = [
            self.dimensions[1]*0.2,
            self.dimensions[1]*0.2+self.dimensions[1]*0.1,
            self.dimensions[1]*0.2+self.dimensions[1]*0.2,
            self.dimensions[1]*0.2+self.dimensions[1]*0.3,
            self.dimensions[1]*0.2+self.dimensions[1]*0.4,
            self.dimensions[1]*0.2+self.dimensions[1]*0.5,
        ]
        
        self.stage = "startUp1"
        self.clock = 0
        self.closing = False
        self.open = True
        
    def update(self, events, dt, graphics): #Updated by the game
        if self.open:
            if not self.musicStarted:
                pygame.mixer.music.play(-1)
                self.musicStarted = True

            if self.stage == "startUp1":
                if self.clock < 280*16*self.waitingTime: #Emulate for loop
                    i = self.clock//(16*self.waitingTime)
                    if i < 75: #Up till 1.5 seconds
                        self.startupImage.set_alpha(i*4+1)
                        self.surface.blit(self.startupImage, self.startupRect)
                    
                else:
                    self.stage = "startUp2"
                    self.clock = 0 #Reset the clock

            elif self.stage == "startUp2":
                if self.clock < 60*16*self.waitingTime: #Emulate for loop
                    i = self.clock//(16*self.waitingTime)
                    self.gradient = pygame.Surface(self.dimensions, pygame.SRCALPHA)
                    self.gradient.fill((0,0,0,i*4+1))
                    self.surface.blit(self.gradient, (0,0))

                else:
                    self.stage = "titleScreen transition"
                    self.clock = 0 #Reset the clock

            elif self.stage == "titleScreen transition":
                if self.clock < 63*16*self.waitingTime: #Emulate for loop
                    i = self.clock//(16*self.waitingTime)
                    self.drawMainOption(4.6, (0,0), "NEW GAME")
                    self.drawMainOption(3.2, (0,0), "LOAD")
                    self.drawMainOption(1.8, (0,0), "CONFIG")

                    self.surface.blit(self.background, (0,0))

                    self.gradient.fill((255,255,255,249-i*3))
                    self.surface.blit(self.gradient, (0,0))
                else:
                    if self.customCursor == 1:
                        pygame.mouse.set_visible(False)
                    else:
                        pygame.mouse.set_visible(True)
                        
                    #Test the gamepad
                    self.gamePads = []
                    for i in range(0, pygame.joystick.get_count()): 
                        self.gamePads.append(pygame.joystick.Joystick(i))
                        self.gamePads[-1].init()
                        if self.debug:
                            print("Detected gamepad '",self.gamePads[-1].get_name(),"'")

                    self.stage = "titleScreen"
                    clock = 0 #Reset the clock

            elif self.stage == "titleScreen":
                for event in events:
                    #Test the gamepad
                    if event.type == pygame.JOYBUTTONDOWN:
                        if self.debug:
                            print("button:",event.button)
                        if event.button == 0: #Advance button
                            destination = self.graph[self.currentNode]["next"]
                            if destination != "":
                                previousNode = self.currentNode
                                if previousNode != destination: #Prevents loops
                                    self.currentNode = destination
                                    self.graph[self.currentNode]["previous"] = previousNode
                                    startNode = self.graph[self.currentNode]["down"]
                                    while startNode != self.currentNode: #Set all the options previous settings
                                        self.graph[startNode]["previous"] = previousNode
                                        startNode = self.graph[startNode]["down"]
                                    if previousNode == "LOAD":
                                        for i in range(6):
                                            self.graph["save"+str(i+1)]["next"] = ""
                                    elif self.graph[previousNode]["previous"] == "NEW GAME":
                                        for i in range(6):
                                            self.graph["save"+str(i+1)]["next"] = "Yes"
                            elif self.currentNode == "No":
                                self.currentNode = self.graph[self.currentNode]["previous"]
                            self.handleInput()
                            if self.debug:
                                print("option:",self.currentNode)
                            
                        if event.button == 1:
                            if self.graph[self.currentNode]["previous"] != "":
                                x,y = 0,0
                                self.currentNode = self.graph[self.currentNode]["previous"]
                                if self.currentNode == "NEW GAME" or self.currentNode == "LOAD" or self.currentNode == "CONFIG":
                                    self.cursorTouching[0] = "0"
                                elif self.graph[self.currentNode]["next"][:2] == "sa":
                                    self.cursorTouching[0] = "1"
                                elif self.currentNode[:2] == "sa":
                                    self.cursorTouching = ["CREATEFILE", "No"]
                                else:
                                    self.cursorTouching[0] = "0"
                                self.handleInput()
                            else:
                                pygame.mixer.Sound.play(self.menuSounds[1]) #back
                                
                            if self.debug:
                                print("option:",self.currentNode)

                    if event.type == pygame.JOYHATMOTION:
                        dpad = self.gamePads[0].get_hat(0)
                        if self.debug:
                            print("dpad:",dpad)
                        if dpad[1] == 1:
                            self.currentNode = self.graph[self.currentNode]["up"]
                        elif dpad[1] == -1:
                            self.currentNode = self.graph[self.currentNode]["down"]
                            
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if len(self.gamePads) == 0:
                            self.handleInput()
                            
                if self.instance == "startGame":
                    if not self.closing:
                        pygame.mixer.music.fadeout(3000)
                        self.closing = True
                    if self.clock < 30*16*self.waitingTime: #Emulate for loop
                        i = self.clock//(16*self.waitingTime)
                        self.gradient.fill((0,0,0,i*8+1))
                        self.surface.blit(self.gradient, (0,0))
                        self.drawnLoadingText = False
                    else:
                        if not self.drawnLoadingText:
                            text = self.fontMain.render("LOADING", True, (240,240,240))
                            textRect = text.get_rect()
                            textRect.bottomright = (self.dimensions[0]*0.95, self.dimensions[1]-8)
                            self.surface.blit(text, textRect)
                            self.drawnLoadingText = True
                            self.close() #Exit the scene
                            
                if not self.closing:
                    self.surface.fill((255,255,255)) #Make screen blank (white)
                    self.surface.blit(self.background, (0,0)) #Title

                    if len(self.gamePads) > 0:
                        x,y = self.graph[self.currentNode]["value"]
                        y +=4 # move y down slightlty
                    else:
                        x,y = pygame.mouse.get_pos() #Get mouse coordinates

                    if self.instance == "main screen":
                        self.drawMainOption(4.6, (x,y), "NEW GAME")
                        self.drawMainOption(3.2, (x,y), "LOAD")
                        self.drawMainOption(1.8, (x,y), "CONFIG")
                        
                    else: #Render the gui but prevent selection and collision
                        self.drawMainOption(4.6, (0,0), "NEW GAME")
                        self.drawMainOption(3.2, (0,0), "LOAD")
                        self.drawMainOption(1.8, (0,0), "CONFIG")

                    #Instances
                    if self.instance == "newGame":
                        self.drawUIBOX((x,y), "Select a game difficulty level.", "(The difficulty can not be changed.)",
                            [
                            ("Normal","Standard difficulty, recommended for new players."),
                            ("Hard","Enemy stats are increased to x1.3."),
                            ("Extreme","Enemy stats are increased to x1.5, damage increased to x1.25, EXP gain decreased to x0.8.")
                        ])
                        
                    elif self.instance == "createFile":
                        self.loadMenu((x,y), 1)
                        
                    elif self.instance == "load":
                        self.loadMenu((x,y))

                    elif self.instance == "confirm":
                        self.drawUIBOX((x,y), "CREATE A NEW SAVE", self.createTextOption,
                            [
                            ("Yes","Begin your new save with "+self.fileType.upper()+" difficulty."),
                            ("No","Return to save menu."),
                        ])
                        
                    elif self.instance == "config":
                        self.drawUIBOX((x,y), "Configure your options.", "(These can be changed in-game.)",
                            [
                            ("Sound","Toggle if sound effects are played."),
                            ("Music","Toggle if music is played."),
                            ("Custom Cursor","Toggle between custom cursor and your device's cursor.")
                        ],
                            [
                            ("TOGGLE", self.playSounds, "playSounds"),
                            ("TOGGLE", self.playMusic, "playMusic"),
                            ("TOGGLE", self.customCursor, "customCursor"),
                        ])

                    if self.customCursor: #Render custom mouse if the option is on
                        cursorRect = self.cursor.get_rect()
                        cursorRect.center = (x,y)
                        self.surface.blit(self.cursor, cursorRect) 
                    
            self.clock += dt

    def close(self):#Closed by the game
        self.open = False

    def drawMainOption(self, y, mouse_coordinates, text="TEST"):
        optionsRect = (self.dimensions[0]*0.4, self.dimensions[1]/20) #Constant for ui sizes 

        if y == 1.8:
            y = self.yCalculations[0]
            index = 0
        elif y == 3.2:
            y = self.yCalculations[1]
            index = 1
        elif y == 4.6:
            y = self.yCalculations[2]
            index = 2

        if mouse_coordinates[0] >= 30 and mouse_coordinates[1] > y and mouse_coordinates[1] < (y+optionsRect[1]): #Calculate if touching the mouse pointer
            colours = ((113,169,247,140), (0,0,0,255), (113,169,247,255)) #Rectangle, Square & Line, Hightlight #230,250,252 | 113,169,247 Colour Codes
            textColour = (0,0,0)
            if self.cursorTouching[0] != text:
                if self.playSounds:
                    pygame.mixer.Sound.play(self.menuSounds[3]) #menu scroll
            self.cursorTouching = [text]
        else:
            colours = ((160,160,160,190), (160,160,160,190), (0,0,0,0)) #Rectangle, Square & Line, Highlight
            textColour = (175,175,175)
            if self.cursorTouching[0] == text: #clear touching if no longer touching
                self.cursorTouching = [None]
            
        self.rectangleSurface.fill(colours[0])
        self.squareSurface.fill(colours[1])
        self.highlightSurface.fill(colours[2])
        self.lineSurface.fill(colours[1])

        self.surface.blit(self.rectangleSurface, self.mainOptionCalculations[index][0])
        self.surface.blit(self.squareSurface, (30, y))
        self.surface.blit(self.highlightSurface, self.mainOptionCalculations[index][2])
        self.surface.blit(self.lineSurface, self.mainOptionCalculations[index][3])

        text = self.fontMain.render(text, True, textColour)
        text_rect = text.get_rect()
        text_rect.topleft = (30+optionsRect[1]+10, y)
        self.surface.blit(text, text_rect)
        
    def drawUIBOX(self, mouse_coordinates, title="Select a game difficulty.", text="(Select an option.)", options=[("Test1","Hover on me."), ("Test2","Hover on me.")], buttonScripts=[]):
        iterations = len(options)-len(buttonScripts) #Load button scripts
        for i in range(iterations):
            buttonScripts.append("")

        #Draw the ui box
        self.gradient = pygame.Surface(self.dimensions, pygame.SRCALPHA)
        self.gradient.fill((0,0,0,200))
        self.surface.blit(self.gradient, (0,0))
        self.surface.blit(self.uiBox, self.uiBoxCalculations[0])
        pygame.draw.line(self.surface, (168,149,229), self.uiBoxCalculations[1][0], self.uiBoxCalculations[1][1], 7) #Top border
        pygame.draw.line(self.surface, (168,149,229), self.uiBoxCalculations[2][0], self.uiBoxCalculations[2][1], 7) #Bottom border

        #Check if touching outside the menu
        if mouse_coordinates[1] < self.dimensions[1]/3 -7 or mouse_coordinates[1] > 2*self.dimensions[1]/3 + 7:
            self.cursorTouching = ["0"] #close the ui
        
        text = self.fontMain.render(text, True, (236,239,26)) #Information text
        title = self.fontMain.render(title, True, (240,240,240)) #Tile text
        
        textRect = text.get_rect()  #Information text box
        textRect.center = self.uiBoxCalculations[3]
        self.surface.blit(text, textRect) #Information text render
        titleRect = title.get_rect()
        titleRect.center = self.uiBoxCalculations[4]
        self.surface.blit(title, titleRect) #Information text render

        longestText = 0
        renderedText = []
        for i in range (len(options)): #Find the option with the longest text length
            renderedText.append(self.fontMain.render(options[i][0], True, (240,240,240)))
            length = renderedText[i].get_rect()[2] #2 = width of the text
            if length > longestText:
                longestText = length
        #Set width of the button using the longest length so that all buttons are the same width
        width = longestText + 80 #40 on each side
        boxSpace = self.uiBoxCalculations[5] #The vertical length of space the buttons will be placed in
        numOfOptions = len(options)
        boxShift = (boxSpace - numOfOptions*35)/2 + self.uiBoxCalculations[6] # Creates equal gap between title and the text
        for i in range(numOfOptions):
            colours = ((10,5,25), (120,120,120)) #Box, Text colours
            
            optionBox = pygame.Rect(0,0,width,35) #x,y,width,length
            optionBox.center = (self.uiBoxCalculations[6], i*45+boxShift)

            if optionBox.collidepoint(mouse_coordinates): #change colours if collinding with mouse
                
                if buttonScripts[i] == "": #Check if it is an ordinary button
                    colours = ((56,9,5), (240,240,240)) #Box, Text colours
                    pygame.draw.rect(self.surface, (168,24,11), (optionBox[0]-3,optionBox[1]-3,optionBox[2]+6,optionBox[3]+6)) #Highlighted border
                    if self.cursorTouching != ["CREATEFILE",options[i][0]]:
                        if self.playSounds:
                            pygame.mixer.Sound.play(self.menuSounds[3]) #menu scroll
                    self.cursorTouching = ["CREATEFILE",options[i][0]]
                    
                else: #Run the button's script
                    script = buttonScripts[i]
                    if script[0] == "TOGGLE":
                        if script[1] == 1:
                            colours = ((72,10,5), (240,240,240)) #Box, Text colours
                            pygame.draw.rect(self.surface, (234,79,18), (optionBox[0]-3,optionBox[1]-3,optionBox[2]+6,optionBox[3]+6))
                        else:
                            if self.cursorTouching != ["TOGGLE", script[2]]:
                                colours = ((10,5,25), (120,120,120)) #Box, Text colours
                        if self.cursorTouching != ["TOGGLE", script[2]]:
                            if self.playSounds:
                                pygame.mixer.Sound.play(self.menuSounds[3]) #menu scroll
                        self.cursorTouching = ["TOGGLE", script[2]]
                    
            else:
                if buttonScripts[i] == "": #Check if it is an ordinary button
                    if self.cursorTouching == ["CREATEFILE",options[i][0]]: #clear touching if no longer touching
                        self.cursorTouching = [None]
                else: #Run the button's script
                    script = buttonScripts[i]
                    if script[0] == "TOGGLE":
                        if script[1] == 1:
                            colours = colours = ((72,10,5), (240,240,240)) #Box, Text colours
                            pygame.draw.rect(self.surface, (234,79,18), (optionBox[0]-3,optionBox[1]-3,optionBox[2]+6,optionBox[3]+6))
                        if self.cursorTouching == ["TOGGLE", script[2]]: #clear touching if no longer touching
                            self.cursorTouching = [None]
            
            pygame.draw.rect(self.surface, colours[0], optionBox)

            text = self.fontMain.render(options[i][0], True, colours[1]) #Re-render the text with correct colours depending on mouse collision
            textRect = renderedText[i].get_rect()
            textRect.center = optionBox.center
            self.surface.blit(text, textRect)
            
            subText = self.fontSub.render(": "+options[i][1], True, (240,240,240))
            subRect = subText.get_rect()
            subRect.topleft = (self.dimensions[0]*0.25 +width/2 +6, optionBox.topleft[1]) #x = buton width + 6, y = button y coordinate
            self.surface.blit(subText, subRect)

    def loadSaves(self):
        saves = []
        for i in range(6): #6 = maximum number of saves
            try: #Load save files
                #File formate = [difficulty, level, money, shipType, emblems, items, current chapter]
                saveFile = open(filePath.setPath(self.path,["data","saves","save"+str((i+1))+".txt"]), "r").readlines()
                try: #Check if the save is interperatble
                    save = 0
                    savedData = json.loads(saveFile[0])
                    if 0 <= savedData[0] and savedData[0] <= 2: #difficulty
                        if 0 <= savedData[1] and savedData[1] <= 260770: #exp
                            if 0 <= savedData[2] and savedData[2] <= 99999: #money
                                if -1 <= savedData[3] and savedData[3] <= 2: #shipType
                                    if -1 <= savedData[4][0] and savedData[4][0] <= 2 and -1 <= savedData[4][1] and savedData[4][1] <= 2: #emblems
                                        if 0 <= savedData[6] and savedData[6] <= 21: #current chapter
                                            saves.append(savedData)
                                            save = 1
                    if save == 0:
                        saves.append("corrupted")
                        
                except: #Returned save corrupted
                    saves.append("corrupted")
                    
            except: #Skip if save not found
                saves.append(0)
        if self.debug:
            for i in range(len(saves)): print(saves[i])
            print("")
        return saves

    def loadMenu(self, mouse_coordinates, access = 0):
        #access = 0 loading file mode
        #access = 1 creating new file mode
        self.gradient = pygame.Surface(self.dimensions, pygame.SRCALPHA)
        self.gradient.fill((6,38,5,220))
        self.surface.blit(self.gradient,(0,0))
        uiCollisionRect = self.loadMenuCalculations[0]
        if not(uiCollisionRect.collidepoint(mouse_coordinates)):
            self.cursorTouching = [str(access)] #close the ui
            
        length = self.loadMenuCalculations[1] #6 = max number of saves
        
        for i in range(6):
            saveUI = self.loadMenuCalculations[i+2]
            
            if saveUI.collidepoint(mouse_coordinates):
                colours = ((13,76,12,200), (220,220,220,140)) #box, line
                if self.cursorTouching != ["SAVE", i]:
                    if self.playSounds:
                        pygame.mixer.Sound.play(self.menuSounds[3]) #menu scroll
                self.cursorTouching = ["SAVE",i]
            else:
                colours = ((6,38,5,140), (220,220,220,80)) #box, line
                if self.cursorTouching == ["SAVE", i]:
                    self.cursorTouching = [None]
                    
            self.saveImage.fill(colours[0])
            self.saveImageLine.fill(colours[1])
            y = self.loadMenuYCalculations[i]
            self.surface.blit(self.saveImage, (self.dimensions[0]*0.1, y))
            self.surface.blit(self.saveImageLine, (self.dimensions[0]*0.1, y+length-3))

            #RENDER SAVE TEXT
            savedData = self.savedData[i]

            #Slot number
            text = self.fontSub.render(str(i+1), True, (240,240,240))
            textRect = text.get_rect()
            textRect.topleft = (self.dimensions[0]*0.15, y+length/3)
            self.surface.blit(text, textRect)
            
            if savedData != "corrupted" and savedData != 0:
                #Difficulty
                if savedData[0] == 0: 
                    text = "Normal" #Valour
                elif savedData[0] == 1:
                    text = "Hard" #Wisdom
                else:
                    text = "Extreme" #Balance/Vanguard
                text = self.fontSub.render(text, True, (240,240,240))
                textRect = text.get_rect()
                textRect.topleft = (self.dimensions[0]*0.3, y+length/3)
                self.surface.blit(text, textRect)
                
                #Level
                level = 0  #Convert exp to level
                if savedData[1] >= 300:
                    level = math.floor(math.sqrt((savedData[1]-300)/70)-1)
                    if level < 0:
                        level = 0
                text = self.fontSub.render("Level "+str(level), True, (240,240,240))
                textRect = text.get_rect()
                textRect.topleft = (self.dimensions[0]*0.2, y+length/3)
                self.surface.blit(text, textRect)

                #Money
                text = self.fontSub.render("Money "+str(savedData[2]), True, (240,240,240))
                textRect = text.get_rect()
                textRect.topleft = (self.dimensions[0]*0.4, y+length/3)
                self.surface.blit(text, textRect)

                #Ship Type
                if savedData[3] == 0: 
                    text = "Vanguard" #Valour
                elif savedData[3] == 1:
                    text = "Engineer" #Wisdom
                elif savedData[3] == 2:
                    text = "Stealth" #Balance/Vanguard
                else:
                    text = "Recruit" #New save
                text = self.fontSub.render(text, True, (240,240,240))
                textRect = text.get_rect()
                textRect.topright = (self.dimensions[0]*0.89, y+length*(10/72))
                self.surface.blit(text, textRect)

                #Emblems
                if savedData[4][0] != -1:
                    emblem1 = self.emblems[savedData[4][0]]
                    emblem1Rect = emblem1.get_rect()
                    emblem1Rect.topleft = (self.dimensions[0]*0.7, y+length/7)
                    self.surface.blit(emblem1, emblem1Rect)
                    
                if savedData[4][1] != -1:
                    emblem2 = self.emblems[savedData[4][1]]
                    emblem2Rect = emblem2.get_rect()
                    emblem2Rect.topleft = (self.dimensions[0]*0.75, y+length/7)
                    self.surface.blit(emblem2, emblem2Rect)

                #Current Chapter
                text = self.fontSub.render("Ch "+str(savedData[6]), True, (240,240,240))
                textRect = text.get_rect()
                textRect.bottomright = (self.dimensions[0]*0.89, y+length*(62/72))
                self.surface.blit(text, textRect)
                
            else:
                if savedData == 0:
                    savedData = "NO DATA"
                text = self.fontSub.render(savedData.upper(), True, (240,240,240))
                textRect = text.get_rect()
                textRect.topleft = (self.dimensions[0]*0.3, y+length/3)
                self.surface.blit(text, textRect)

    def handleInput(self):
        if self.cursorTouching[0] == "0": #close the ui
            self.instance = "main screen"
            if self.playSounds:
                pygame.mixer.Sound.play(self.menuSounds[1]) #back
                                
        elif self.cursorTouching[0] == "1": #go to self.instance new game
            self.instance = "newGame"
            if self.playSounds:
                pygame.mixer.Sound.play(self.menuSounds[1]) #back

        elif self.cursorTouching[0] == "NEW GAME":
            self.instance = "newGame"
            if self.playSounds:
                pygame.mixer.Sound.play(self.menuSounds[2]) #open

        elif self.cursorTouching[0] == "CREATEFILE":
            if self.instance != "confirm":
                self.instance = "createFile"
                self.fileType = self.cursorTouching[1]

                if self.playSounds:
                        pygame.mixer.Sound.play(self.menuSounds[4]) #select
                        
            elif self.instance == "confirm":
                if self.cursorTouching[1] == "Yes":
                    newSave = open(filePath.setPath(self.path,["data","saves","save"+str((self.saveSlot+1))+".txt"]), "w+") #Create new save or overwrite file
                    if self.fileType == "Normal":
                        difficulty = "0"
                    elif self.fileType == "Hard":
                        difficulty = "1"
                    else:
                        difficulty = "2"
                    self.playerData = [int(difficulty), 0, 0, -1, [-1,-1], [], 0, {"commands":["Surge"]}] #Store the player's save data to be used on launch
                    newSave.write(json.dumps(self.playerData))
                    newSave.close()
                    #difficulty, level, money, shipType, emblems, items, current chapter
                    self.instance = "startGame"
                    self.clock = 0 #Reset the clock

                    if self.playSounds:
                        pygame.mixer.Sound.play(self.menuSounds[4]) #select
                                
                elif self.cursorTouching[1] == "No":
                    self.instance = "createFile"

                    if self.playSounds:
                        pygame.mixer.Sound.play(self.menuSounds[1]) #back

        elif self.cursorTouching[0] == "LOAD":
            self.instance = "load"
            if self.playSounds:
                pygame.mixer.Sound.play(self.menuSounds[2]) #open
                                
        elif self.cursorTouching[0] == "SAVE":
            if self.instance == "createFile":
                if self.savedData[self.cursorTouching[1]] == 0: #If an empty save
                    self.createTextOption = "(Start a new save and begin your adventure.)"
                else:
                    self.createTextOption = "(Are you sure you want to overwrite your save file?)"
                self.instance = "confirm"
                self.saveSlot = self.cursorTouching[1]
                if self.playSounds:
                    pygame.mixer.Sound.play(self.menuSounds[4]) #select
                                
            elif self.instance == "load":
                self.playerData = self.savedData[self.cursorTouching[1]]
                if not(self.playerData == 0 or self.playerData == "corrupted"):#check if the save is loadable
                    self.instance = "startGame"
                    self.clock = 0 #Reset the clock
                    if self.playSounds:
                        pygame.mixer.Sound.play(self.menuSounds[4]) #select
                else:
                    if self.playSounds:
                        pygame.mixer.Sound.play(self.menuSounds[0]) #error
                                
        elif self.cursorTouching[0] == "CONFIG":
            self.instance = "config"
            if self.playSounds:
                pygame.mixer.Sound.play(self.menuSounds[2]) #open

        elif self.cursorTouching[0] == "TOGGLE":
            if self.cursorTouching[1] == "playSounds":
                if self.playSounds == 1:
                    self.playSounds = 0
                else:
                    self.playSounds = 1
                if self.playSounds:
                    pygame.mixer.Sound.play(self.menuSounds[4]) #select
                                
            elif self.cursorTouching[1] == "playMusic":
                if self.playMusic == 1:
                    self.playMusic = 0
                    pygame.mixer.music.pause()
                else:
                    self.playMusic = 1
                    pygame.mixer.music.unpause()
                if self.playSounds:
                    pygame.mixer.Sound.play(self.menuSounds[4]) #select
                            
            elif self.cursorTouching[1] == "customCursor":
                if len(self.gamePads) == 0:
                    if self.customCursor == 1:
                        self.customCursor = 0
                        pygame.mouse.set_visible(True)
                    else:
                        self.customCursor = 1
                        pygame.mouse.set_visible(False)
                    if self.playSounds:
                        pygame.mixer.Sound.play(self.menuSounds[4]) #select
                else:
                    pygame.mixer.Sound.play(self.menuSounds[0]) #error

