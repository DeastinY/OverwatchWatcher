import time
import csv
import json
import argparse
from os import scandir, stat, path
import sys

from PIL import Image
from statistics import mean
from math import fabs
from tkinter import Tk
from tkinter.filedialog import askdirectory
import numpy as np
import pyperclip

# This is for 1280x720 resolution
PORTRAIT_START_X = 304
PORTRAIT_START_Y = 192
# Horizontal separation is 10% of screenshot width. Vertical separation? It's some weird irrational decimal.
# Blizzard, pls fix
PORTRAIT_H_SEPARATION = 128
PORTRAIT_V_SEPARATION = 204
PORTRAIT_SIZE = 32

USE_1080P = True
# This is for 1980 x 1080
if USE_1080P:
    PORTRAIT_START_X = 456
    PORTRAIT_START_Y = 288
    PORTRAIT_H_SEPARATION = 192
    PORTRAIT_V_SEPARATION = 306
    PORTRAIT_SIZE = 48

# TODO: Add image recognition for location. Thresholding may be needed.
locationStartY = 64
locationFrameH = 16

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


def get_crop_frame(b_use_smaller_pic):
    """
    We will be doing a lot of cropping on screenshots. We're focused on hero portraits, (which are luckily all the same
    size and evenly aligned), so we need a way to pragmatically cut images.
    This function will return a tuple that can be used for PIL's cropping function, and offsets can be calculated as
    needed.
    """
    left = PORTRAIT_START_X
    top = PORTRAIT_START_Y
    right = left + PORTRAIT_SIZE
    bottom = top + PORTRAIT_SIZE
    margin = 16
    if b_use_smaller_pic:
        left += margin
        top += margin
        right -= margin
        bottom -= margin

    return left, top, right, bottom


def get_portraits_from_image(image, team, b_use_smaller_pic):
    hero_portraits = []
    # Get the frame we will use to crop the last_analyzed_screenshot
    base_crop_frame = get_crop_frame(b_use_smaller_pic)
    # If enemiesOnly is true, only a list of enemy's portraits will be returned.
    # If team is 0, we're analyzing the ENEMY team. Otherwise, we're analyzing ALLIES and need to add vertical
    # separation.
    # TODO: Replace this with a proper enum or something
    vertical_separation_multiplier = team
    for j in range(0, 6):
        # Create a new frame offset from the base frame for our crop location
        crop_frame = (
            base_crop_frame[0] + (PORTRAIT_H_SEPARATION * j),
            base_crop_frame[1] + (PORTRAIT_V_SEPARATION * vertical_separation_multiplier),
            base_crop_frame[2] + (PORTRAIT_H_SEPARATION * j),
            base_crop_frame[3] + (PORTRAIT_V_SEPARATION * vertical_separation_multiplier)
        )
        cropped_portrait = image.crop(crop_frame)
        # croppedPortrait.save(str(i) + str(j) + ".png")
        iar = np.array(cropped_portrait)
        hero_portraits.append(iar.tolist())

    return hero_portraits


def bulk_add_examples(hero_data_filename, b_use_smaller_pic, screenshot_dir):
    """
    This function makes the assumption that you have a directory named "heroes" that contains a bunch of .jpg
    screenshots of you showing the score screen (Typically TAB), playing a hero that shares the same name as the
    screenshot. That is, if heroes/tracer.jpg does not exist, or you didn't have Tracer selected in that pic, you're
    going to have issues. Assuming the assumptions are met, this function will store arrays of image data of each hero's
    portrait in a JSON structure, then store that JSON in herodata.txt.
    """
    hero_examples = open(hero_data_filename, "w+")
    hero_iarls = {}

    # Get the frame we will use to crop the upcoming screenshot
    base_crop_frame = get_crop_frame(b_use_smaller_pic)

    # I should probably use an array instead of a tuple, since arrays are mutable at least. Eh.
    crop_frame = (
        base_crop_frame[0],
        base_crop_frame[1] + PORTRAIT_V_SEPARATION,
        base_crop_frame[2],
        base_crop_frame[3] + PORTRAIT_V_SEPARATION
    )

    # Iterate through the list of hero names at the top of the file.
    for heroName in allHeroNames:
        # Get the name of screenshot that HOPEFULLY contains their portrait in the player's slot.
        example_data_path = path.join("heroes", heroName) + ".jpg"
        example_screenshot = Image.open(example_data_path)

        # Get just the portrait.
        cropped_portrait = example_screenshot.crop(crop_frame)
        iar = np.array(cropped_portrait)

        # Store the image data into a dict.
        hero_iarls[heroName] = iar.tolist()

    save_data = {"heroImgData": hero_iarls, "screenshotDirectory": screenshot_dir}
    # Convert the dict into a JSON structure and write it to file.
    hero_examples.write(json.dumps(save_data))
    print("Saved heroes to " + hero_data_filename)
    # Uncomment the below line if you want to actually see the contents of the file for some reason but prefer a
    # readable format.
    # heroExamples.write(json.dumps(heroIarls, indent = 4, sort_keys = True))


def mean_array_diff(list_a, list_b):
    """ This kind of perform's photoshop's "difference" blending mode between two pixels, list_a and list_b. Basically,
    the new pixel's RGB is determined by [fabs(a[0] - b[0]), fabs(a[1] - b[1]), fabs(a[2] - b[2])]. Then the RGB
    channels of that new pixel are all averaged together to produce a number between 0 and 255 (inclusive) that
    indicates how much difference there is between the two pixels."""
    diff = [fabs(list_a[i] - list_b[i]) for i in range(0, len(list_a))]
    return mean(diff)


def who_is_this(iarl, json_hero_data):
    unknown_hero_iarl = iarl
    hero_possibilities = []
    for heroName in allHeroNames:
        possible_hero_iarl = json_hero_data[heroName]
        sum_mean_diff = 0
        i = 0
        j = 0
        for i in range(0, len(possible_hero_iarl)):
            row_possible = possible_hero_iarl[i]
            row_unknown = unknown_hero_iarl[i]
            for j in range(0, len(row_possible)):
                pixel_possible = row_possible[j]
                pixel_unknown = row_unknown[j]
                sum_mean_diff += mean_array_diff(pixel_possible, pixel_unknown)
        sum_mean_diff /= (i * j)
        entry = (heroName, sum_mean_diff)
        hero_possibilities.append(entry)

    hero_possibilities = sorted(hero_possibilities, key=lambda a: a[1])
    return hero_possibilities[0]


def get_mr_screenshot(directory):
    """
    Get the path of the most recent screenshot saved in directory.
    """
    dir_info = [i for i in scandir(directory)]
    entries = [(i.path, stat(i.path).st_ctime) for i in dir_info]
    entries = sorted(entries, key=lambda a: a[1], reverse=True)
    mr_screenshot = entries[0][0]
    return mr_screenshot

def shortenedName(name):
    return shortHeroNames[name] if name in shortHeroNames.keys() else name


if __name__ == "__main__":
    argp = argparse.ArgumentParser()
    argp.add_argument("-b", "--buildExamples",
                      dest="buildExamples",
                      help="Don\'t actually run the monitor, just build a list of examples from the heroes folder.",
                      nargs="?",
                      const=True,
                      required=False)
    argp.add_argument("-t", "--tiny",
                      dest="useSmallerPic",
                      help="Use smaller 16x16 images. Much faster than normal, but more room for misjudgements.",
                      nargs="?",
                      const=True,
                      default=False,
                      required=False)
    # TODO: Implement "run once and quit"
    argp.add_argument("-n", "--no-monitor",
                      dest="noMonitor",
                      help="Don\'t run the monitor, just report matching heroes and exit.",
                      nargs="?",
                      const=True,
                      default=False,
                      required=False)

    args = argp.parse_args()

    herodataFilename = "herodata.json"
    heroFile = ""
    heroData = None
    try:
        heroFile = open(herodataFilename, "r").read()
    except FileNotFoundError as e:
        print("No hero data for image recognition found. Creating.")
        print("Please choose the directory that your screenshots are kept in.")
        directoryName = ""
        Tk().withdraw()
        directoryName = askdirectory()

        bulk_add_examples(herodataFilename, args.useSmallerPic, directoryName)
        heroFile = open(herodataFilename, "r").read()
    heroData = json.loads(heroFile)

    if args.buildExamples:
        print("Please choose the directory that your screenshots are kept in.")
        directoryName = ""
        Tk().withdraw()
        directoryName = askdirectory()
        bulk_add_examples(herodataFilename, args.useSmallerPic, directoryName)
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
                    if key != "name":
                        matchups[key] = float(row[key])

                matchupDict[row["name"]] = {"matchups": matchups}
                # Uncomment this to print the counterpickdata as JSON instead of CSV.
                # print(json.dumps(matchupDict, indent = 4, sort_keys = True))
    except FileNotFoundError as e:
        print("Somehow, someway, you're missing counterpick data. You may want to redownload this thing")
        sys.exit(1)

    print("Press Ctrl+C to exit the program.")
    # Kind of hackish way of prompting the user for a directory to monitor, BUT IT WORKS

    heroImgData = heroData["heroImgData"]
    directoryName = heroData["screenshotDirectory"]
    print("Monitoring " + directoryName + " for screenshots")

    last_analyzed_screenshot = ""
    while True:
        # get the current time. We'll need to see how much time elapsed while we were working to calculate the time we
        # sleep for.
        tStart = time.time()
        mostrecentscreenshot = get_mr_screenshot(directoryName)
        analysisInProgress = False
        if last_analyzed_screenshot != mostrecentscreenshot:
            last_analyzed_screenshot = mostrecentscreenshot
            print("New screenshot detected at time " + str(tStart))
            openedScreenshot = None
            enemies = []
            allies = []
            try:
                openedScreenshot = Image.open(last_analyzed_screenshot)
            except:
                print("Sometimes a race condition happens between Overwatch writing a screenshot and the program " +
                      "reading the screenshot and it results in a PermissionError.")
                sleepDuration = time.time() - tStart
                continue
            # Set the last analyzed screenshot here if it was opened successfully
            enemies = get_portraits_from_image(openedScreenshot, 0, args.useSmallerPic)
            allies = get_portraits_from_image(openedScreenshot, 1, args.useSmallerPic)
            enemies = [who_is_this(img, heroImgData) for img in enemies]
            allies = [who_is_this(img, heroImgData) for img in allies]
            enemies = [[i[0], round((1 - (i[1] / 255)) * 100)] for i in enemies]
            allies = [[i[0], round((1 - (i[1] / 255)) * 100)] for i in allies]

            for i in enemies:
                print("Possible enemy identified: " + str(i[0]) + " Certainty: " + str(i[1]))
            for i in allies:
                print("Possible ally identified: " + str(i[0]) + " Certainty: " + str(i[1]))

            # TODO: Combine desired certainty with margin on portraits somehow. They kind of influence each other.
            desiredCertainty = 0.9
            enemies = [i[0] for i in enemies if i[1] > desiredCertainty]
            allies = [i[0] for i in allies if i[1] > desiredCertainty]

            summary = {"enemies": enemies, "allies": allies}
            print(json.dumps(summary, indent=4, sort_keys=True))
            # Iterate through matchup data, filter so all "vs" entries contain only the enemies currently being fought.
            compToBeat = enemies
            filteredMatchupLists = {}
            for name in matchupDict.keys():
                for key, value in matchupDict.items():
                    # Iterate through filtered matchup data and create a dict of name:sums of the weights for members
                    # of the enemy team.
                    matchups = [{"vs": key, "favor": val} for key, val in matchupDict[name]["matchups"].items() if
                                str(key) in compToBeat]
                    filteredMatchupDict = {}
                    favorSum = sum([i["favor"] for i in matchups])
                    filteredMatchupDict["favorSum"] = favorSum
                    filteredMatchupLists[name] = {"favorSum": favorSum}
            # Sort the filtered matchups
            ret = [{"name": key, "favorSum": val["favorSum"]} for key, val in filteredMatchupLists.items()]
            ret = sorted(ret, key=lambda a: a["favorSum"], reverse=True)
            ret = ret[:6]

            dictRet = {}
            for i in ret:
                dictRet[i["name"]] = "{:1.2f}".format(i["favorSum"])
            print(json.dumps(dictRet, indent=4, sort_keys=True))
            output = [shortenedName(i["name"]) for i in ret]
            text = ", ".join(output)

            # Indicate that we're finished by sounding an alarm, specifically, printing the ASCII Bell character, '\a'
            print("\aFinished in " + str(time.time() - tStart) + " seconds")
            print(json.dumps(output, indent=4, sort_keys=True))

            # Copy results to clipboard so you don't have to alt + tab to see them, just paste anywhere that has a text
            # box.
            pyperclip.copy(str(text))

        sleepDuration = time.time() - tStart
        time.sleep(1 - (sleepDuration if sleepDuration < 1 else 0))
