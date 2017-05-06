import pyscreenshot
import keyboard
import logging
import argparse
import configparser
import csv
import json
import sys
import time
from os import scandir, stat, getcwd, path, mkdir
from tkinter import Tk
from tkinter.filedialog import askdirectory
import cv2
import numpy as np
import pyperclip
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

MAX_TEAM_SIZE = 6

# File endings to consider
IMG_ENDINGS = ["jpg", "jpeg", "png", "tif", "tiff", "gif"]

# Horizontal separation is 10% of screenshot width. Vertical separation? It's some weird irrational decimal.
# Blizzard, pls fix

USE_720P = False
# This is for 1280 x 720
if USE_720P:
    PORTRAIT_START_X = 304
    PORTRAIT_START_Y = 192
    
    PORTRAIT_H_SEPARATION = 128
    PORTRAIT_V_SEPARATION = 204
    PORTRAIT_SIZE_X = 32
    PORTRAIT_SIZE_Y = 32

USE_1080P = False
# This is for 1980 x 1080
if USE_1080P:
    PORTRAIT_START_X = 405
    PORTRAIT_START_Y = 540
    PORTRAIT_H_SEPARATION = 192
    PORTRAIT_V_SEPARATION = -320
    PORTRAIT_SIZE_X = 150
    PORTRAIT_SIZE_Y = 160

USE_1440P = True
# This is for 2560 x 1440
if USE_1440P:
    # https://github.com/ponty/pyscreenshot/issues/25
    from ctypes import windll
    user32 = windll.user32
    user32.SetProcessDPIAware()

    PORTRAIT_START_X = 530
    PORTRAIT_START_Y = 715
    PORTRAIT_H_SEPARATION = 256
    PORTRAIT_V_SEPARATION = -410
    PORTRAIT_SIZE_X = 220
    PORTRAIT_SIZE_Y = 220

args = {}

ALL_HERO_NAMES = [
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
    "orisa",
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


def get_hero_portraits():
    """Uses spriters-resource to download the current hero portraits."""
    data = requests.get("https://www.spriters-resource.com/pc_computer/overwatch").text
    soup = BeautifulSoup(data, "lxml")
    if not path.exists('portraits'):
        mkdir('portraits')
    for img in soup.find_all('img'):
        if any([h in img.get('alt').lower() for h in ALL_HERO_NAMES]):
            r = requests.get('https://www.spriters-resource.com'+img.get('src'))
            with open(path.join('portraits', img.get('src').split('/')[-1]), 'wb') as fout:
                fout.write(r.content)


def generate_portrait_sifts():
    """Creates SIFT features for all portraits and stores them."""
    sift_data = {}
    for hero_name in ALL_HERO_NAMES:
        portrait_path = path.join('portraits', hero_name + '.png')
        portrait = cv2.imread(portrait_path, 0)
        # TODO: Could be serialized via pickle. Currently takes ~ 0.8 sec, so maybe not needed
        sift_data[hero_name] = (create_sift_data(portrait), portrait)
    return sift_data

surf = None


def create_sift_data(image):
    """
    Creates SIFT features for a passed image
    :param image: The image to process.
    :return: The SIFT features.
    """
    global surf
    if not surf:
        surf = cv2.xfeatures2d.SURF_create()
    return surf.detectAndCompute(image, None)


def get_portraits_from_image(image):
    """
    Converts a screenshot into a list of pixel data.
    :param image: The screenshot that was taken
    :return: 
    """
    portraits = {}
    # Get the frame we will use to crop the last_analyzed_screenshot
    for vertical_separation_multiplier in [0, 1]:
        hero_portraits = []
        for j in range(0, 6):
            # Create a new frame offset from the base frame for our crop location
            x = PORTRAIT_START_X + PORTRAIT_H_SEPARATION * j
            y = PORTRAIT_START_Y + PORTRAIT_V_SEPARATION * vertical_separation_multiplier
            w = PORTRAIT_SIZE_X
            h = PORTRAIT_SIZE_Y
            hero_portraits.append(image[y:y+h, x:x+w, ...])  # It is (y, x, rgb) in numpy
            cv2.waitKey()
        team = "enemy" if vertical_separation_multiplier else "ally"
        portraits[team] = hero_portraits
    return portraits


def who_is_this(image, hero_data, top_matches=20, debug=False):
    """
    Takes an educated guess at which hero is described in the image.
    Uses SIFT Features
    :return: Returns a string containing the name of the hero possibly shown in the picture.
    """
    hero_possibilities = []
    kp, des = create_sift_data(image)
    bf = cv2.BFMatcher(cv2.NORM_L1, crossCheck=False)
    for hero_name, data in hero_data.items():
        kpdes, img = data
        matches = bf.match(des, kpdes[1])
        matches = sorted(matches, key=lambda x: x.distance)
        avg_dist = np.mean([m.distance for m in matches[:top_matches]])
        if debug:
            i = None
            i = cv2.drawMatches(image, kp, img, kpdes[0], matches[:top_matches], i, flags=2)
            cv2.imshow("Matches", i)
            cv2.waitKey()
        hero_possibilities.append((hero_name, avg_dist))

    hero_possibilities = sorted(hero_possibilities, key=lambda a: a[1])

    return hero_possibilities[0]


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


def get_matchup_data_from_csv(csv_filename):
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
    except FileNotFoundError:
        print("Somehow, someway, you're missing {}. You may want to redownload this thing".format(csv_filename))
        exit(1)
    return matchup_dict


def load_screenshot(screenshot):
    try:
        return cv2.imread(screenshot, 0)
    except IOError:
        logging.error(sys.exc_info()[0])
        logging.error("Sometimes a race condition happens between Overwatch writing a screenshot and "
                      "the program reading the screenshot and it results in an error of some sort. It's a known issue.")



def analyze_screenshot(screenshot, hero_data):
    """
    Analyzes a screeshot to find the probabilites for characters on each team.
    :return: Returns information about all Players and their probabilities.
    """
    portraits = get_portraits_from_image(screenshot)
    # Convert those portraits to tuples containing the hero name, some level of certainty, and
    # if they're possibly dead
    players = {
        "ally": [],
        "enemy": []
    }
    for i in ["ally", "enemy"]:
        for portrait in portraits[i]:
            players[i].append(who_is_this(portrait, hero_data))
    return players


def get_config():
    """
    :return: A ConfigParser object containing our config. 
    """
    config_file = "config.ini"
    config = configparser.ConfigParser()

    if not path.exists(config_file):
        print("Please choose the directory that your screenshots are kept in.")
        # Kind of hackish way of prompting the user for a directory to monitor, BUT IT WORKS
        Tk().withdraw()
        config['DEFAULT'] = {'ScreenshotDirectory': askdirectory()}
        with open(config_file, 'w') as fout:
            config.write(fout)
    else:
        config.read(config_file)
    return config


def analyze_team(players, matchup_data):
    """Analyzes the given team."""
    filteredMatchupLists = {}

    favorabilityRankings = []
    teamheroes = " ".join([p[0] for p in players["ally"]])
    # Iterate all characters we have matchup data for.
    for name in matchup_data.keys():
        # favorability is a rough indicator of approximately how hard the character counters the enemy team.
        favorability = 0
        # Grab the individual favorabilities for the character across the whole enemy team...
        matchups = [matchup_data[name]["vs"][enemy[0]] for enemy in players["enemy"]]
        # and sum them.
        favorability = sum(matchups)
        # Sum them and shove them into a list for sorting later
        favorabilityRankings.append({"name": name, "favorability": sum(matchups)})

    # If this was SQL, this would be "ORDER BY favorability LIMIT MAX_TEAM_SIZE" or something
    favorabilityRankings = sorted(favorabilityRankings, key=lambda a: a["favorability"], reverse=True)
    favorabilityRankings = favorabilityRankings[:MAX_TEAM_SIZE]
    # TODO: Turn everything above into a function that returns favorabilityRankings.

    # Create a list just containing the names of the most favorable heroes.
    ret = [i["name"] for i in favorabilityRankings if not i["name"] in teamheroes]

    # Merge name and favorability into one entry for each entry in favorabilityRankings...
    favorabilityRankings = ["{}: {}".format(i["name"], i["favorability"]) for i in favorabilityRankings]
    # ...so we can neatly print the details.
    logging.info("Top {}:\n{}".format(MAX_TEAM_SIZE, json.dumps(favorabilityRankings, indent=4, sort_keys=True)))

    # Summarize the results into a format that can be easily copied to a clipboard.
    text = ", ".join([shorten_name(i) for i in ret])

    # Indicate that we're finished by sounding an alarm, specifically, printing the ASCII Bell character, '\a'
    logging.info("Finished in " + str(time.time() - tStart) + " seconds")
    logging.info("Suggestions: " + text)

    # Copy results to clipboard so you can paste them into in-game chat
    pyperclip.copy(str(text))


def hotkey_pressed(hero_data, matchup_data):
    logging.info("Hotkey pressed")
    image = pyscreenshot.grab()
    image = np.asarray(image)
    print(image.shape)
    cv2.imwrite("ttest.png", image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    players = analyze_screenshot(image, hero_data)
    logging.info(json.dumps(players, indent=2, sort_keys=True))
    analyze_team(players, matchup_data)


if __name__ == "__main__":
    argp = argparse.ArgumentParser()
    argp.add_argument("-g", "--getOnlinePortraits",
                      dest="getOnlinePortraits",
                      help="Load current portraits from the web. Clean and name them afterwards yourself !",
                      nargs="?",
                      const=True,
                      required=False)
    argp.add_argument("-r", "--resolution",
                      dest="resolution",
                      help="The resolution of the screenshots. Defaults to 720. Not actually implemented yet",
                      type=int,
                      default=720,
                      required=False)

    args = argp.parse_args()
    config = get_config()
    screenshot_directory = config['DEFAULT']['ScreenshotDirectory']
    logging.info(str(args))
    logging.debug("Working in " + getcwd())

    if args.getOnlinePortraits:
        logging.info("Crawling Portraits")
        get_hero_portraits()
        exit(0)

    logging.info("Building SIFT features for portraits")
    hero_data = generate_portrait_sifts()

    logging.info("Loading counterpickdata.csv")
    csv_filename = "counterpickdata.csv"
    matchup_data = get_matchup_data_from_csv(csv_filename)

    logging.info("Registering hotkey")
    keyboard.add_hotkey('tab+a', hotkey_pressed, args=[hero_data, matchup_data], timeout=1)

    logging.info("Press Ctrl+C to exit the program.")

    logging.info("Monitoring {} for screenshots".format(screenshot_directory))

    last_analyzed_screenshot = ""
    while True:
        tStart = time.time()
        mostrecentscreenshot = get_mr_screenshot(screenshot_directory)
        analysisInProgress = False
        if last_analyzed_screenshot != mostrecentscreenshot:
            # Set the last analyzed screenshot here
            last_analyzed_screenshot = mostrecentscreenshot
            logging.info("New screenshot \"{}\" detected at time {:1.2f}".format(mostrecentscreenshot, tStart))
            players = analyze_screenshot(load_screenshot(last_analyzed_screenshot), hero_data)
            logging.info(json.dumps(players, indent=2, sort_keys=True))
            analyze_team(players, matchup_data)

        sleepDuration = time.time() - tStart
        time.sleep(1 - (sleepDuration if sleepDuration < 1 else 0))
