from lib import filePath

#Loads contents and mods
#Order of priority
#0 base game files
#1-10 Mods
#Any clashes will result in the lower numbered file overwritting the other file
#Clashes between files of the same priority will favour the latter file
#e.g. two mods add in an enemy with the same name, only the enemy from the mod
#with the higher priority will be added in.

#Constants
FILERETRACTS = 2

fileRootPath = filePath.getRootFolder(FILERETRACTS)

#Load enemy data
def loadEnemyData():
    contentFolder = filePath.setPath(fileRootPath ,["data","content","enemies.txt"])
    contentData = filePath.loadConfig(contentFolder)
    return contentData

def loadProjectileData():
    contentFolder = filePath.setPath(fileRootPath ,["data","content","projectiles.txt"])
    contentData = filePath.loadConfig(contentFolder)
    return contentData

def loadEntities():
    entities = [loadEnemyData(),loadProjectileData()]
    return entities

def loadAbilities():
    contentFolder = filePath.setPath(fileRootPath, ["data", "content", "abilities.txt"])
    contentData = filePath.loadList(contentFolder)
    return contentData