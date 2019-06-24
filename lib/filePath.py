import json

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

def loadConfig(filePath):
    try:
        config = open(filePath).readlines()
        config = [x.strip() for x in config]
        dicte = "{"
        for i in range(len(config)):
            if config[i][0] != "#": #Ignore comments
                dicte += config[i]+','
        dicte = dicte[:-1]
        dicte += "}"
        config = json.loads(dicte)
        return config
    except:
        return 0 #loading error
