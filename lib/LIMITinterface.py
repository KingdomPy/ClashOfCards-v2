import pygame, pygame.gfxdraw, math

#Gui and Hud of the player
#Displays the hp and mp bar
#Displays the command menu
#Displays the minimap

def getRootFolder(retracts=1):
    #retracts is how many times it goes up the file path branch
    path = __file__
    if "\\" in path: #Checks if device uses '\' or '/' to navigate folders
        key = "\\"
    else:
        key = "/"
    path = path.split(key)
    for i in range(retracts):
        path.pop()
    path = key.join(path)
    return path

def setPath(path, pathList):
    if "\\" in path: #Checks if device uses '\' or '/' to navigate folders
        key = "\\"
    else:
        key = "/"
    path = path.split(key)
    for i in range(len(pathList)):
        path.append(pathList[i])
    path = key.join(path)
    return path


class display:
    def __init__(self, surface, dimensions, debug=False):
        self.debug = debug
        self.surface = surface
        self.width = dimensions[0]
        self.length = dimensions[1]
        path = getRootFolder(2)
        self.font = pygame.font.Font(setPath(path,["assets","fonts","ability_Font.ttf"]), 18)
        self.font2 = pygame.font.Font(setPath(path,["assets","fonts","Kh2_Menu_Font.ttf"]), 12)
        self.frame = pygame.image.load(setPath(path,["assets","player","command_menu","unselected.png"]))
        self.frame_selected = pygame.image.load(setPath(path,["assets","player","command_menu","selected.png"]))
        self.frame_reaction = pygame.image.load(setPath(path,["assets","player","command_menu","frame_reaction.png"]))
        self.toolTipAnimation = [""]
        if self.debug == True:
            self.colour = (0,0,0)
        else:
            self.colour = (0,0,0)

    def renderCMenu(self, commands=[], cooldowns=[], selected=0):
        x = 0
        y = self.length - 150
        
        #Load sprites
        "Command title"
        text = self.font2.render("COMMAND", True, (220,80,130))
        sprite = pygame.Rect(x+14, y-24, 119, 29)
        location = text.get_rect()
        location.topleft = sprite.topleft
        self.surface.blit(text, location)
        for i in range (0, 4):
            if i != selected:
                self.surface.blit(self.frame, (x, y+34*i))
        image = self.frame_selected
        self.surface.blit(image, (x, y+34*selected))
        
        #Load text and cooldowns
        for i in range(len(commands)):
            if i < 4:
                if i != selected:
                    sprite = pygame.Rect(x+25, y+34*i+13, 119, 29)
                    colour = (170,170,170)
                    cooldownSprite = pygame.Rect(x, y+34*i, 144, 42)
                else:
                    sprite = pygame.Rect(x+37, y+34*i+13, 119, 29)
                    colour = (255,255,255)
                    cooldownSprite = pygame.Rect(x+12, y+34*i, 144, 42)
                text = self.font.render(commands[i], True, colour)
                location = text.get_rect()
                location.topleft = sprite.topleft
                self.surface.blit(text, location)
                
    def renderHud(self, miniMapData, hudData):
        #Interact box
        toolTip = hudData[2]
        if toolTip != self.toolTipAnimation[0]:
            self.toolTipAnimation = [toolTip,5]
        if toolTip != "":
            x = self.toolTipAnimation[1]
            self.surface.blit(self.frame_reaction, (x,self.length-220))
            if x == 15:
                toolTip = self.font.render(toolTip, True, (250,250,250))
                toolTipRect = toolTip.get_rect()
                toolTipRect.topleft = (x+19, self.length-205)
                self.surface.blit(toolTip, toolTipRect)
            if self.toolTipAnimation[1] < 15:
                self.toolTipAnimation[1] += 2
                if self.toolTipAnimation[1] >= 15:
                    self.toolTipAnimation[1] = 15
                    
        #Mana bar
        points,colour = self.calculateManaBar(hudData[1])
        pygame.draw.polygon(self.surface, (21,56,81), points[1]) #Background 
        pygame.draw.polygon(self.surface, colour, points[0]) #Mana
        if self.debug == True:
            pygame.draw.lines(self.surface,  self.colour, True, points[1], 2) #Frame
                             
        #Health bar
        points,colour = self.calculateHealthBar(hudData[0])
        pygame.draw.polygon(self.surface, colour, points[0]) #Hp
        pygame.draw.lines(self.surface,  self.colour, True, points[1], 2) #Frame

        #Mini Map
        miniMapRect = (self.width-174,30,144,144)
        borderWidth = 3
        clipRect = (miniMapRect[0]+borderWidth, miniMapRect[1]+borderWidth, miniMapRect[2]-borderWidth*2, miniMapRect[3]-borderWidth*2)
        xConstant = (miniMapRect[0]*2 + miniMapRect[2])/2
        yConstant = (miniMapRect[1]*2 + miniMapRect[3])/2
        pygame.draw.rect(self.surface,  self.colour, miniMapRect, borderWidth)
        self.surface.set_clip(clipRect)
        #Dimensions of the map
        mapScale = 72/1500
        #Size of icons on the map
        sizeScale = 72/600
        enemies = ("triangle", "square")
        allies = ("npc", "location", "player")
        for i in range(len(miniMapData)):
            size = miniMapData[i][2]*sizeScale
            x = (-1*miniMapData[i][1][0]) * mapScale + xConstant - size/2
            y = (-1*miniMapData[i][1][1]) * mapScale + yConstant - size/2
            if miniMapData[i][0] in enemies:
                colour = (250,50,50)
                pygame.draw.rect(self.surface, colour, (x, y, size, size))
                
            elif miniMapData[i][0] in allies:          
                if miniMapData[i][0] == "location":
                    colour = miniMapData[i][3]
                    pygame.draw.rect(self.surface, colour, (x, y, size, size), 2)
                    x += size/2
                    y += size/2
                    radius = round(miniMapData[i][2] * 5 * mapScale)
                    pygame.gfxdraw.aacircle(self.surface, round(x), round(y), radius-1, colour) #Draw zone range
                    pygame.gfxdraw.aacircle(self.surface, round(x), round(y), radius, colour) #Make zone thicker

                else:
                    colour = (50,250,50)
                    if miniMapData[i][0] == "player":
                        pygame.draw.rect(self.surface, (0,0,0), (x-2, y-2, size+4, size+4))
                    if miniMapData[i][0] == "npc":
                        colour = (50,250,50)
                    pygame.draw.rect(self.surface, colour, (x, y, size, size))
            else: #Temporary online player
                colour = (50,250,50)
                #pygame.draw.rect(self.surface, (0,0,0), (x-2, y-2, size+4, size+4))
                #pygame.draw.rect(self.surface, colour, (x, y, size, size))
                
        #The player
        pygame.draw.rect(self.surface,  self.colour, (xConstant-2.5, yConstant-2.5, 5,5))
        self.surface.set_clip()

    def calculateHealthBar(self, hpStats):
        percentage = hpStats[0]/hpStats[1]
        colour = (63,237,47)
        #HP bar, Frame
        points = [((self.width-20-170*percentage,self.length-68), (self.width-20,self.length-68), (self.width-20,self.length-38), (self.width-20-200*percentage,self.length-38)),
                  ((self.width-190,self.length-68), (self.width-20,self.length-68), (self.width-20,self.length-38), (self.width-220,self.length-38))]
        return points, colour

    def calculateManaBar(self, mpStats):
        percentage = mpStats[0]/mpStats[1]
        if percentage > 0:
            colour =(66,167,244)
        else:
            percentage = abs(percentage)
            colour = (242,87,162)
        points = [((self.width-20-180*percentage,self.length-83), (self.width-20,self.length-83), (self.width-20,self.length-74), (self.width-20-170*percentage,self.length-74)),
                  ((self.width-220,self.length-43), (self.width-200,self.length-83),
                  (self.width-20,self.length-83), (self.width-20,self.length-73), (self.width-190,self.length-73))]
        return points, colour
        
    def update(self, commands=[], cooldowns=[], selected=0, miniMapData=[], hudData=(100,100)): #hudData = hp and mp
        self.renderCMenu(commands, cooldowns, selected)
        #self.renderHud(miniMapData, hudData)
        
