from PIL import Image
from statistics import mean
from math import fabs
from tkinter import Tk
from tkinter.filedialog import askdirectory
import matplotlib.pyplot as plt
import numpy as np
import pyperclip
import time
import csv
import json
import argparse
import os
import sys
import __main__ as main

# This is for 1280x720 resolution
portraitStartX = 304
portraitStartY = 192
# Horizontal separation is 10% of screenshot width. Vertical separation? It's some weird irrational decimal. Blizzard, pls fix
portraitHSeparation = 128
portraitVSeparation = 203
portraitCenterSize = 32

# This is for 1980 x 1080
portraitStartX = 456
portraitStartY = 288
portraitHSeparation = 192
portraitVSeparation = 305
portraitCenterSize = 48

args = {}

allHeroNames = [
    "ana",
    "bastion",
    "dva",
    "genji",
    "hanzo",
    "junkrat",
    "lucio",
    "mccree",
    "mei",
    "mercy",
    "pharah",
    "reaper",
    "reinhardt",
    "roadhog",
    "soldier76",
    "sombra",
    "symmetra",
    "torbjorn",
    "tracer",
    "widowmaker",
    "winston",
    "zarya",
    "zenyatta"
]

shortHeroNames = {
    "reinhardt": "rein",
    "soldier76": "soldier",
    "symmetra": "symm",
    "torbjorn": "torb",
    "widowmaker": "widow",
    "zenyatta": "zen"
}

def getCropFrame(useSmallerPic):
    '''
    We will be doing a lot of cropping on screenshots. We're focused on hero portraits, (which are luckily all the same size and evenly aligned), so we need a way to programmatically cut images.
    This function will return a tuple that can be used for PIL's cropping function, and offsets can be calculated as needed.
    '''
    left = portraitStartX
    top = portraitStartY
    right = left + portraitCenterSize
    bottom = top + portraitCenterSize
    margin = 20
    if useSmallerPic:
        left += margin
        top += margin
        right -= margin
        bottom -= margin
    
    return (left, top, right, bottom)
    
def getPortraits(path, useSmallerPic):
    # Get the screenshot referenced by path.
    screenshot = Image.open(path)
    heroPortraits = []
    # Get the frame we will use to crop the screenshot
    baseCropFrame = getCropFrame(useSmallerPic)
    # If enemiesOnly is true, only a list of enemy's portraits will be returned.
    enemiesOnly = False
    for i in range(0, (1 if enemiesOnly else 2)):
        for j in range(0, 6):
            # Create a new frame offset from the base frame for our crop location
            cropFrame = (
                baseCropFrame[0] + (portraitHSeparation * j),
                baseCropFrame[1] + (portraitVSeparation * i),
                baseCropFrame[2] + (portraitHSeparation * j),
                baseCropFrame[3] + (portraitVSeparation * i)
            )
            croppedPortrait = screenshot.crop(cropFrame)
            #croppedPortrait.save(str(i) + str(j) + ".png")
            iar = np.array(croppedPortrait)
            heroPortraits.append(iar.tolist())
            
    return heroPortraits

def bulkAddExamples(herodataFilename, useSmallerPic, screenshotDir):
    '''
    This function makes the assumption that you have a directory named "heroes" that contains a bunch of .jpg screenshots of you showing the score screen (Typically TAB), playing a hero that shares the same name as the screenshot.
    That is, if heroes/tracer.jpg does not exist, or you didn't have Tracer selected in that pic, you're going to have issues.
    Assuming the assumptions are met, this function will store arrays of image data of each hero's portrait in a JSON structure, then store that JSON in herodata.txt.
    '''
    heroExamples = open(herodataFilename, "w+")
    heroIarls = {}
    
    # Get the frame we will use to crop the upcoming screenshot
    baseCropFrame = getCropFrame(useSmallerPic)
    
    # I should probably use an array instead of a tuple, since arrays are mutable at least. Eh.
    cropFrame = (
        baseCropFrame[0],
        baseCropFrame[1] + portraitVSeparation,
        baseCropFrame[2],
        baseCropFrame[3] + portraitVSeparation
    )
    
    # Iterate through the list of hero names at the top of the file.
    for heroName in allHeroNames:
        # Get the name of screenshot that HOPEFULLY contains their portrait in the player's slot.
        sScreenshot = "heroes/" + heroName + ".jpg"
        screenshot = Image.open(sScreenshot)
        
        # Get just the portrait.
        croppedPortrait = screenshot.crop(cropFrame)
        iar = np.array(croppedPortrait)
        
        # Store the image data into a dict.
        heroIarls[heroName] = iar.tolist()
    
    saveData = {"heroImgData":heroIarls, "screenshotDirectory":screenshotDir}
    # Convert the dict into a JSON structure and write it to file.
    heroExamples.write(json.dumps(saveData))
    print ("Saved heroes to " + herodataFilename)
    # Uncomment the below line if you want to actually see the contents of the file for some reason but prefer a readable format.
    #heroExamples.write(json.dumps(heroIarls, indent = 4, sort_keys = True))

def threshold(imageArray):
    '''
    A simple, but unused image data manipulation function. This one performs a variant of Photoshop's "threshold" operation on imageArray.
    Returns an array contining the pixel data of the processed image.
    '''
    balanceAr = []
    newAr = imageArray
    from statistics import mean
    for eachRow in imageArray:
        for eachPix in eachRow:
            avgNum = mean(eachPix[:3])
            balanceAr.append(avgNum)

    balance = mean(balanceAr)
    for eachRow in newAr:
        for eachPix in eachRow:
            avgPix = mean(eachPix[:3])
            if avgPix > balance:
                eachPix[0] = 255
                eachPix[1] = 255
                eachPix[2] = 255
                if len(eachPix) > 3:
                    eachPix[3] = 255
            else:
                eachPix[0] = 0
                eachPix[1] = 0
                eachPix[2] = 0
                if len(eachPix) > 3:
                    eachPix[3] = 255
    return newAr

def meanArrDiff(listA, listB):
    ''' This kind of perform's photoshop's "difference" blending mode between two pixels, listA and listB. Basically, the new pixel's RGB is determined by [fabs(a[0] - b[0]), fabs(a[1] - b[1]), fabs(a[2] - b[2])].
    Then the RGB channels of that new pixel are all averaged together to produce a number between 0 and 255 (inclusive) that indicates how much difference there is between the two pixels.'''
    ret = [fabs(listA[i] - listB[i]) for i in range(0, len(listA))]
    return mean(ret)

def whoisthispic(pic):
    img = Image.open(pic)
    iar = threshold(np.array(img))
    iarl = iar.tolist()
    whoisthis(iarl)

def whoisthis(iarl, heroData):
    listHeroQ = iarl
    heroPossibilities = []
    for heroName in allHeroNames:
        listHeroEx = heroData[heroName]
        sumMeanDifferences = 0;
        for i in range(0, len(listHeroEx)):
            rowEx = listHeroEx[i]
            rowQ = listHeroQ[i]
            for j in range(0, len(rowEx)):
                pixelEx = rowEx[j]
                pixelQ = rowQ[j]
                sumMeanDifferences += meanArrDiff(pixelEx, pixelQ)
        sumMeanDifferences /= (i * j)
        entry = (heroName, sumMeanDifferences)
        heroPossibilities.append(entry)
    
    heroPossibilities = sorted(heroPossibilities, key = lambda a : a[1])
    certainty = round((1 - (heroPossibilities[0][1] / 255)) * 100)
    print ("Possible hero identified: " + str(heroPossibilities[0][0]) + " Certainty: " + str(certainty))
    return heroPossibilities[0]
        
def getMRscreenshotIn(directoryName):
    '''
    Get the most recent screenshot taken in directory directoryName.
    '''
    dirInfo = [i for i in os.scandir(directoryName)]
    entries = [(i.path, os.stat(i.path).st_ctime) for i in dirInfo]
    entries = sorted(entries, key = lambda a : a[1], reverse = True)
    mrscreenshot = entries[0][0]
    return mrscreenshot

if __name__ == "__main__":
    argp = argparse.ArgumentParser()
    argp.add_argument("-b", "--buildExamples",
                      dest = "buildExamples",
                      help = "Don\'t actually run the monitor, just build a list of examples from the heroes folder.",
                      nargs = "?",
                      const = True,
                      required = False)
    argp.add_argument("-t", "--tiny",
                      dest = "useSmallerPic",
                      help = "Use smaller 16x16 images. Much faster than normal, but more room for misjudgements.",
                      nargs = "?",
                      const = True,
                      default = False,
                      required = False)
                      
    args = argp.parse_args()
    herodataFilename = "herodata.json"
    heroFile = ""
    
    try:
        heroFile = open(herodataFilename, "r").read()
    except FileNotFoundError as e:
        print("Please choose the directory that your screenshots are kept in.")
        directoryName = ""
        Tk().withdraw()
        directoryName = askdirectory()
        print ("No hero data for image recognition found. Creating.")
        bulkAddExamples(herodataFilename, args.useSmallerPic, directoryName)
        heroFile = open(herodataFilename, "r").read()
        
    if args.buildExamples:
        bulkAddExamples(herodataFilename, args.useSmallerPic)
        sys.exit(0)
    
    matchupDict = {}
    try:
        with open("counterpickdata.csv") as csvfile:
            reader = csv.DictReader(csvfile)
            title = reader.fieldnames
            rows = [row for row in reader]
            for row in rows:
                matchups = {}
                for key in row.keys():
                    if key != "Hero":
                        matchups[key] = float(row[key])
                
                matchupDict[row["Hero"]] = {"matchups": matchups}
        # Uncomment this to print the counterpickdata as JSON instead of CSV.
        #print(json.dumps(matchupDict, indent = 4, sort_keys = True))
    except FileNotFoundError as e:
        print ("Somehow, someway, you're missing counterpick data. You may want to redownload this thing")
        sys.exit(1)
    
    print ("Press Ctrl+C to exit the program.")
    # Kind of hackish way of prompting the user for a directory to monitor, BUT IT WORKS
    
    heroData = json.loads(heroFile)
    heroImgData = heroData["heroImgData"]
    directoryName = heroData["screenshotDirectory"]
    print("Monitoring " + directoryName + " for screenshots")
    
    screenshot = ""
    while True:
        # get the current time. We'll need to see how much time elapsed while we were working to calculate the time we sleep for.
        tStart = time.time()
        mostrecentscreenshot = getMRscreenshotIn(directoryName)
        analysisInProgress = False
        if screenshot != mostrecentscreenshot:
            print ("New screenshot detected at time " + str(tStart))
            screenshot = mostrecentscreenshot
            portraitList = getPortraits(screenshot, args.useSmallerPic)
            benchmarkStart = time.time()
            
            heroList = [whoisthis(img, heroImgData) for img in portraitList]
            #Uncomment this to print the raw list of heroes identified, along with certainty values.
            #print(json.dumps(heroList, indent = 4, sort_keys = True))
            desiredCertainty = 0.9
            certaintyThreshold = 255 * (1 - desiredCertainty)
            enemies = [enemy[0] for enemy in heroList[:6] if enemy[1] < certaintyThreshold]
            allies = [ally[0] for ally in heroList[6:] if ally[1] < certaintyThreshold]
            
            
            summary = {}
            summary["enemies"] = enemies
            summary["allies"] = allies
            
            compToBeat = allies
            print(json.dumps(summary, indent = 4, sort_keys = True))
            # Iterate through matchup data, filter so all "vs" entries contain only the enemies currently being fought.
            filteredMatchupLists = {}
            for name in matchupDict.keys():
                for key, value in matchupDict.items():
                    # Iterate through filtered matchup data and create a dict of name:sums of the weights for members of the enemy team.
                    matchups = [{"vs":key, "favor":val} for key, val in matchupDict[name]["matchups"].items() if str(key) in compToBeat]
                    filteredMatchupDict = {}
                    for i in matchups:
                        filteredMatchupDict[i["vs"]] = i["favor"]
                    favorSum = sum([i["favor"] for i in matchups])
                    filteredMatchupDict["favorSum"] = favorSum
                filteredMatchupLists[name] = filteredMatchupDict
            # Sort the filtered matchups
            ret = [{"name":key, "favorSum":val["favorSum"]} for key, val in filteredMatchupLists.items()]
            ret = sorted(ret, key = lambda a : a["favorSum"], reverse = True)
            ret = ret[:6]
            # Uncomment this line to print the list of heroes with favorability numbers.
            #print (json.dumps(ret, indent = 4, sort_keys = True))
            dictRet = {}
            for i in ret:
                dictRet[i["name"]] = i["favorSum"]
            print (json.dumps(dictRet, indent = 4, sort_keys = True))
            output = [i["name"] for i in ret]
            #output = [(shortHeroNames[i] if i in shortHeroNames.keys() else i) for i in output]
            text = ", ".join(output)
            
            # Indicate that we're finished by sounding an alarm, specifically, printing the ASCII Bell character, '\a'
            print ("\aFinished in " + str(time.time() - benchmarkStart) + " seconds")
            print (json.dumps(output, indent = 4, sort_keys = True))
            
            # Copy results to clipboard so you don't have to alt + tab to see them, just paste anywhere that has a text box.
            pyperclip.copy(str(text))
            # Uncomment this if you're a lazy butt who wants to ask friends about the accuracy of this script.
            # print ("How would this comp: \n" + ", ".join(output) + "\nfair against this one: \n" + ", ".join(compToBeat))
        sleepDuration = time.time() - tStart
        time.sleep(1 - (sleepDuration if sleepDuration < 1 else 0))