import argparse
import sys
import csv
import json
import time
from math import fabs
from os import scandir, stat, path, getcwd
from statistics import mean
from tkinter import Tk
from tkinter.filedialog import askdirectory

import numpy as np
import pyperclip
from PIL import Image

MAX_TEAM_SIZE = 6

# File endings to consider
IMG_ENDINGS = ["jpg", "jpeg", "png", "tif", "tiff", "gif"]

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

# TODO: Add image recognition for location (Numbani, Ilios, Volskaya Industries, etc. Thresholding may be needed.
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
    :param b_use_smaller_pic: Set to true to use smaller pictures for faster performance at the cost of accuracy.
    :return:
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
    """
    Converts a screenshot into a list of pixel data.
    :param image: The screenshot that was taken
    :param team: 0 if you wish to analyze the ENEMY team, 1 for allies.
    :param b_use_smaller_pic: Set to true to use smaller pictures for faster performance at the cost of accuracy.
    :return: A list of 6 lists of lists of lists, one for each hero observed on the team.
    """
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


def generate_example_hero_image_data(b_use_smaller_pic):
    """
    Open the images in heroes/ and stores the pixel data as lists of lists of lists.
    :param b_use_smaller_pic: Set to true to use smaller pictures for faster performance at the cost of accuracy.
    :return: Returns a dictionary containing the data.
    """
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

    return hero_iarls


def save_configuration(hero_data_filename, b_use_smaller_pic, screenshot_dir):
    """
    Saves configuration data for the next time the script runs.
    :param hero_data_filename: The filename to which the data will be saved.
    :param b_use_smaller_pic: Set to true to use smaller pictures for faster performance at the cost of accuracy.
    :param screenshot_dir: The directory in which Overwatch keeps its Screenshots
    :return: A dictionary containing at least the heroImageData and screenshotDirectory at the moment.
    """
    """
    This function makes the assumption that you have a directory named "heroes" that contains a bunch of .jpg
    screenshots of you showing the score screen (Typically TAB), playing a hero that shares the same name as the
    screenshot. That is, if heroes/tracer.jpg does not exist, or you didn't have Tracer selected in that pic, you're
    going to have issues. Assuming the assumptions are met, this function will store arrays of image data of each hero's
    portrait in a JSON structure, then store that JSON in herodata.txt.
    """
    hero_examples = open(hero_data_filename, "w+")
    hero_iarls = generate_example_hero_image_data(b_use_smaller_pic)

    save_data = {"heroImgData": hero_iarls,
                 "screenshotDirectory": screenshot_dir
                 }
    # Convert the dict into a JSON structure and write it to file.
    hero_examples.write(json.dumps(save_data))
    print("Saved heroes to " + hero_data_filename)
    # Uncomment the below line if you want to actually see the contents of the file for some reason but prefer a
    # readable format.
    # heroExamples.write(json.dumps(heroIarls, indent = 4, sort_keys = True))


def mean_array_diff(list_a, list_b):
    """
    This kind of perform's photoshop's "difference" blending mode between two pixels, list_a and list_b. Basically,
    the new pixel's RGB is determined by [fabs(a[0] - b[0]), fabs(a[1] - b[1]), fabs(a[2] - b[2])]. Then the RGB
    channels of that new pixel are all averaged together to produce a number between 0 and 255 (inclusive) that
    indicates how much difference there is between the two pixels.
    :param list_a: A list of three integers between 0 and 255, inclusive. No check is done on size.
    :param list_b: A list of three integers between 0 and 255, inclusive. No check is done on size.
    :return:
    """
    diff = [fabs(list_a[i] - list_b[i]) for i in range(0, len(list_a))]
    return mean(diff)


def who_is_this(iarl, json_hero_data):
    """
    Takes an educated guess at which hero is described in the image data contained by iarl.
    FYI, this is fairly slow because it checks every pixel in every image supplied.
    :param iarl: The image data (list of list of pixels (list) to analyze
    :param json_hero_data: The stored data to compare it to.
    :return: Returns a string containing the name of the hero possibly shown in the picture.
    """
    unknown_hero_iarl = iarl
    hero_possibilities = []
    height = len(unknown_hero_iarl)
    width = len(unknown_hero_iarl[0])
    area = height * width
    for heroName in allHeroNames:
        possible_hero_iarl = json_hero_data[heroName]
        sum_mean_diff = 0
        redness = 0
        for i in range(0, len(possible_hero_iarl)):
            row_possible = possible_hero_iarl[i]
            row_unknown = unknown_hero_iarl[i]
            for j in range(0, len(row_possible)):
                pixel_possible = row_possible[j]
                pixel_unknown = row_unknown[j]
                if pixel_unknown[0] > (pixel_unknown[1] + pixel_unknown[2]) * 2:
                    redness += 1
                sum_mean_diff += mean_array_diff(pixel_possible, pixel_unknown)
        sum_mean_diff /= area
        redness /= area
        entry = [heroName, sum_mean_diff, redness]
        hero_possibilities.append(entry)

    # Sort possible heroes by amount of difference between the pictures, lowest difference being first.
    hero_possibilities = sorted(hero_possibilities, key=lambda a: a[1])
    # Uncomment this line to print the 6 most likely heroes for the given iarl.
    # print([i[0] for i in hero_possibilities][:6])
    best_guess = hero_possibilities[0]

    # Normalize the best guess for ease of readability and further calculation
    best_guess[1] = 1 - (best_guess[1] / 255)
    return best_guess


def get_mr_screenshot(directory):
    """
    Get the path of the most recent screenshot saved in directory.
    :param directory: A directory where screenshots are kept.
    :return: The path to the latest screenshot in directory.
    """
    dir_info = [i for i in scandir(directory)]
    entries = [(i.path, stat(i.path).st_ctime) for i in dir_info if any([e in i.path for e in IMG_ENDINGS])]
    entries = sorted(entries, key=lambda a: a[1], reverse=True)
    mr_screenshot = entries[0][0]
    return mr_screenshot


def shorten_name(name):
    """
    Shorthand for names is useful for saving space in the in-game chat.
    This function shortens whatever name it is supplied.
    :param name: The name of the hero to be shortened.
    :return: Returns "rein" for "reinhardt", "torb" for "torbjorn", etc.
    """
    return shortHeroNames[name] if name in shortHeroNames.keys() else name


def get_matchup_data_from_csv(csv_filename, b_print=False):
    """
    Typically you store matchup data in a table, with the same list of characters on both axes and every cell contains
    some number describing how favorable it is for the character on the y-axis.
    This converts that data to a Dictionary to make it easier to access.
    :return:
    """
    matchup_dict = {}
    try:
        with open(csv_filename) as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [row for row in reader]
            for row in rows:
                matchups = {}
                for key in row.keys():
                    if key != "name":
                        matchups[key] = float(row[key])

                matchup_dict[row["name"]] = {"vs": matchups}
                # Uncomment this to print the counterpickdata as JSON instead of CSV.
                if b_print:
                    print(json.dumps(matchup_dict, indent=4, sort_keys=True))
    except FileNotFoundError:
        print("Somehow, someway, you're missing {}. You may want to redownload this thing".format(csv_filename))
        exit(1)
    return matchup_dict

def analyze_screeshot(screenshot, useSmallerPic):
    """
    Analyzes a screeshot to find the probabilites for characters on each team.
    :return: Returns information about all Players and their probabilities.
    """
    openedScreenshot = None
    enemies = []
    allies = []
    try:
        openedScreenshot = Image.open(screenshot)
    except:
        print(sys.exc_info()[0])
        print("Sometimes a race condition happens between Overwatch writing a screenshot and the program " +
                "reading the screenshot and it results in an error of some sort. It's a known issue.")
        return

    allPlayers = []
    avg_certainties = []
    # TODO: Combine desired certainty with margin on portraits somehow. They kind of influence each other.
    desiredCertainty = 0.95
    for i in range(2):
        # Populate a list with all portraits on an enemy team
        team = get_portraits_from_image(openedScreenshot, i, useSmallerPic)
        # Convert those portraits to tuples containing the hero name, some level of certainty, and
        # if they're possibly dead
        team = [who_is_this(img, heroImgData) for img in team]
        for j in team:
            possiblyDead = j[2] > .5
            uncertainID = j[1] < desiredCertainty
            print("{} {} {} with certainty {:1.2f}. {}"
                    .format(
                    ("Ignoring" if possiblyDead or uncertainID else "Identified"),  # What we're doing
                    ("enemy" if i == 0 else "ally"),  # What team they're on
                    j[0],  # What character
                    j[1],  # How certain we are its that character (between 0 and 1, inclusive)
                    ("Possibly dead." if j[2] > .5 else "")))  # Notes.
        # Get the average certainty for the whole team.
        avg_certainty = mean([j[1] for j in team])
        avg_certainties.append(avg_certainty)
        # Finally, convert the tuples to just the names.
        team = [j[0] for j in team if j[2] < .5]
        allPlayers.append(team)
    return allPlayers


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
    argp.add_argument("-n", "--no-monitor",
                      dest="noMonitor",
                      help="Don't monitor the directory, just run once and quit",
                      nargs="?",
                      const=True,
                      default=False,
                      required=False)
    argp.add_argument("-r", "--resolution",
                      dest="resolution",
                      help="The resolution of the screenshots. Defaults to 720. Not actually implemented yet",
                      type=int,
                      default=720,
                      required=False)

    args = argp.parse_args()
    print(str(args))

    # TODO: Have a command-line option to regenerate herodata.json from csv.
    herodataFilename = "herodata.json"
    heroFile = ""
    heroData = None
    print("Working in " + getcwd())
    try:
        heroFile = open(herodataFilename, "r").read()
    except FileNotFoundError as e:
        print("No hero data for image recognition found. Creating.")
        print("Please choose the directory that your screenshots are kept in.")
        directoryName = ""
        # Kind of hackish way of prompting the user for a directory to monitor, BUT IT WORKS
        Tk().withdraw()
        directoryName = askdirectory()

        save_configuration(herodataFilename, args.useSmallerPic, directoryName)
        heroFile = open(herodataFilename, "r").read()
    heroData = json.loads(heroFile)

    if args.buildExamples:
        print("Please choose the directory that your screenshots are kept in.")
        directoryName = ""
        Tk().withdraw()
        directoryName = askdirectory()
        save_configuration(herodataFilename, args.useSmallerPic, directoryName)
        exit(0)

    csv_filename = "counterpickdata.csv"
    matchupDict = get_matchup_data_from_csv(csv_filename)

    print("Press Ctrl+C to exit the program.")

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
            # Set the last analyzed screenshot here
            last_analyzed_screenshot = mostrecentscreenshot
            print("New screenshot \"{}\" detected at time {:1.2f}".format(mostrecentscreenshot, tStart))
            allPlayers = analyze_screeshot(last_analyzed_screenshot, args.useSmallerPic)
            

            print(json.dumps(allPlayers, indent=4, sort_keys=True))
            # TODO: Turn everything below into a function that accepts enemies and allies as parameters.
            compToBeat = allPlayers[0]
            filteredMatchupLists = {}

            favorabilityRankings = []
            # Iterate all characters we have matchup data for.
            for name in matchupDict.keys():
                # favorability is a rough indicator of approximately how hard the character counters the enemy team.
                favorability = 0
                # Grab the individual favorabilities for the character across the whole enemy team...
                matchups = [matchupDict[name]["vs"][enemy] for enemy in allPlayers[0]]
                # and sum them.
                favorability = sum(matchups)
                # Sum them and shove them into a list for sorting later
                favorabilityRankings.append({"name": name, "favorability": sum(matchups)})

            # If this was SQL, this would be "ORDER BY favorability LIMIT MAX_TEAM_SIZE" or something
            favorabilityRankings = sorted(favorabilityRankings, key=lambda a: a["favorability"], reverse=True)
            favorabilityRankings = favorabilityRankings[:MAX_TEAM_SIZE]
            # TODO: Turn everything above into a function that returns favorabilityRankings.

            # Create a list just containing the names of the most favorable heroes.
            ret = [i["name"] for i in favorabilityRankings]

            # Merge name and favorability into one entry for each entry in favorabilityRankings...
            favorabilityRankings = ["{}: {}".format(i["name"], i["favorability"]) for i in favorabilityRankings]
            # ...so we can neatly print the details.
            print("Top {}:\n{}".format(MAX_TEAM_SIZE, json.dumps(favorabilityRankings, indent=4, sort_keys=True)))

            # Summarize the results into a format that can be easily copied to a clipboard.
            text = ", ".join([shorten_name(i) for i in ret])

            # Indicate that we're finished by sounding an alarm, specifically, printing the ASCII Bell character, '\a'
            print("\aFinished in " + str(time.time() - tStart) + " seconds")
            print("Suggestions: " + text)

            # Copy results to clipboard so you can paste them into in-game chat
            pyperclip.copy(str(text))

        sleepDuration = time.time() - tStart
        if args.noMonitor:
            # Sleep for a second or two so we can actually hear the alarm before terminating.
            time.sleep(2)
            exit(0)
        time.sleep(1 - (sleepDuration if sleepDuration < 1 else 0))
