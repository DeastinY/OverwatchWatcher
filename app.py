from PIL import Image
from statistics import mean
from math import fabs
from tkinter import Tk
from tkinter.filedialog import askdirectory
import matplotlib.pyplot as plt
import numpy as np
import pyperclip
import time
import json
import argparse
import os
import sys

portraitStartX = 304
portraitStartY = 192
portraitHSeparation = 128
portraitVSeparation = 203
portraitCenterSize = 32
argp = argparse.ArgumentParser()

allHeroNames = [
    "ana",
    "bastion",
    "dva",
    "genji",
    "hanzo",
    "junkrat",
    "lucio",
    "mcree",
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

def test():
    test_image = "C:/Users/Muhznit/Documents/Overwatch/ScreenShots/Overwatch/ScreenShot_17-02-06_21-51-48-000.jpg"
    original = Image.open(test_image)
    #original.show()

    width, height = original.size   # Get dimensions
    left = portraitStartX
    top = portraitStartY
    right = left + portraitCenterSize
    bottom = top + portraitCenterSize
    cropped_example = original.crop((left, top, right, bottom))

    #cropped_example.show()
    iar = np.array(cropped_example)
    plt.imshow(threshold(iar))
    plt.show()
    print (iar)
    cropped_example.save("bastion.jpg")

def getPortraits(path, useSmallerPic):
    screenshot = Image.open(path)
    left = portraitStartX
    top = portraitStartY
    right = left + portraitCenterSize
    bottom = top + portraitCenterSize
    if useSmallerPic:
        left += (portraitCenterSize // 4)
        top += (portraitCenterSize // 4)
        right -= (portraitCenterSize // 4)
        bottom -= (portraitCenterSize // 4)
    heroPortraits = []
    for i in range(0, (1 if False else 2)):
        for j in range(0, 6):
            left = portraitStartX + (portraitHSeparation * j)
            right = left + portraitCenterSize
            top = portraitStartY + (portraitVSeparation * i)
            bottom = top + portraitCenterSize
            print ("cropping at " + str((left, top, right, bottom)))
            croppedPortrait = screenshot.crop((left, top, right, bottom))
            #croppedPortrait.show()
            iar = np.array(croppedPortrait)
            heroPortraits.append(iar.tolist())
            
    return heroPortraits

def bulkAddExamples():
    heroExamples = open('herodata.txt', 'w')
    heroIarls = {}
    for heroName in allHeroNames:
        sScreenshot = "heroes/" + heroName + ".jpg"
        screenshot = Image.open(sScreenshot)
        left = portraitStartX
        top = portraitStartY + portraitVSeparation
        right = left + portraitCenterSize
        bottom = top + portraitCenterSize
        
        croppedPortrait = screenshot.crop((left, top, right, bottom))
        iar = np.array(croppedPortrait)
        
        heroIarls[heroName] = iar.tolist()
    
    heroExamples.write(json.dumps(heroIarls))
    #heroExamples.write(json.dumps(heroIarls, indent = 4, sort_keys = True))
    
    
def addTeamExamples(heroName):
    ''' Arrrggh. This was such a waste. I was using custom games to control whole team selections and ensure the AI chose only what I needed....
    ...but AI for all characters is not implemented! I can't get whole teams of Symmetra!
    '''
    heroExamples = open(heroName + '.txt', 'a')
    sScreenshot = heroName + ".jpg"
    screenshot = Image.open(sScreenshot)
    left = portraitStartX
    top = portraitStartY
    right = left + portraitCenterSize
    bottom = top + portraitCenterSize
    heroThresholds = []
    heroIarls = []
    imlist = []
    for i in range(0, 2):
        for j in range(0, 6):
            left = portraitStartX + (portraitHSeparation * j)
            right = left + portraitCenterSize
            top = portraitStartY + (portraitVSeparation * i)
            bottom = top + portraitCenterSize
            
            croppedThumbnail = screenshot.crop((left, top, right, bottom))
            imlist.append(croppedThumbnail)
            iar = np.array(croppedThumbnail)
            iarl = iar.tolist()
            heroIarls.append(iarl)
            #croppedThumbnail.save(heroName + "{0:0>2}".format((i * 6) + j) + ".png")

    # Code jacked from http://stackoverflow.com/questions/17291455/how-to-get-an-average-picture-from-100-pictures-using-pil
    N = len(imlist)

    # Create a numpy array of floats to store the average (assume RGB images)
    arr = np.zeros((portraitCenterSize, portraitCenterSize, 3), np.float)

    # Build up average pixel intensities, casting each image as an array of floats
    for im in imlist:
        imarr = np.array(im, dtype = np.float)
        arr = arr+imarr/N

    # Round values in array and cast as 8-bit integer
    arr = np.array(np.round(arr),dtype = np.uint8)
    plt.imshow(arr)
    plt.show()

    # Generate, save and preview final image
    # out = Image.fromarray(arr, mode = "RGB")
    # out.show
    
    avgHero = arr.tolist()
    print(str(avgHero))
    plt.imshow(np.array(avgHero))
    #plt.show()
    heroExamples.write(str(avgHero) + '\n')

def threshold(imageArray):

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
            if mean(eachPix[:3]) > balance:
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
    ret = [fabs(listA[i] - listB[i]) for i in range(0, len(listA))]
    return mean(ret)

def whatisthispic(pic):
    img = Image.open(pic)
    iar = np.array(img)
    iarl = iar.tolist()
    whoisthis(iarl)

def whoisthis(iarl, heroData):
    listHeroQ = iarl
    heroPossibilities = []
    for heroName in allHeroNames:
        listHeroEx = heroData[heroName]
        sumMeans = 0;
        for i in range(0, len(listHeroEx)):
            rowEx = listHeroEx[i]
            rowQ = listHeroQ[i]
            for j in range(0, len(rowEx)):
                pixelEx = rowEx[j]
                pixelQ = rowQ[j]
                sumMeans += meanArrDiff(pixelEx, pixelQ)
        sumMeans /= (i * j)
        entry = (heroName, sumMeans)
        heroPossibilities.append(entry)
    
    heroPossibilities = sorted(heroPossibilities, key = lambda a : a[1])
    print (heroPossibilities[0])
    return heroPossibilities[0][0]
        
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
    # Kind of hackish way of prompting the user for a directory to monitor.
    Tk().withdraw()
    directoryName = askdirectory()
    
    print ("Press Ctrl+C to exit the program (Note: Program will lose focus due to tkinter spawning a window)")
    screenshot = ""
    while True:
        tStart = time.time()
        mostrecentscreenshot = getMRscreenshotIn(directoryName)
        if screenshot != mostrecentscreenshot:
            print ("New screenshot detected at time " + str(tStart))
            screenshot = mostrecentscreenshot
            portraitList = getPortraits(screenshot, False)
            benchmarkStart = time.time()            
            heroFile = open('heroData.txt', 'r').read()
            heroData = json.loads(heroFile)
            heroList = [whoisthis(img, heroData) for img in portraitList]
            # Indicate that we're finished by sounding an alarm.
            print ("\aFinished in " + str(time.time() - benchmarkStart) + " seconds")
            strHeroesInBattle = str(heroList)
            print (str(heroList))
            pyperclip.copy(strHeroesInBattle)
        sleepDuration = time.time() - tStart
        time.sleep(1 - (sleepDuration if sleepDuration < 1 else 0))
    '''
    i = Image.open('images/numbers/0.1.png')
    iar = np.array(i)
    i2 = Image.open('images/numbers/y0.4.png')
    iar2 = np.array(i2)
    i3 = Image.open('images/numbers/y0.5.png')
    iar3 = np.array(i3)
    i4 = Image.open('images/sentdex.png')
    iar4 = np.array(i4)


    iar = threshold(iar)
    iar2 = threshold(iar2)
    iar3 = threshold(iar3)
    iar4 = threshold(iar4)

    fig = plt.figure()
    ax1 = plt.subplot2grid((8,6),(0,0), rowspan=4, colspan=3)
    ax2 = plt.subplot2grid((8,6),(4,0), rowspan=4, colspan=3)
    ax3 = plt.subplot2grid((8,6),(0,3), rowspan=4, colspan=3)
    ax4 = plt.subplot2grid((8,6),(4,3), rowspan=4, colspan=3)

    ax1.imshow(iar)
    ax2.imshow(iar2)
    ax3.imshow(iar3)
    ax4.imshow(iar4)


    plt.show()
    '''