# Overwatch Watcher

I'm not sure about you, but I have enough trouble memorizing all interactions
among the 18 types of Pokemon, let alone all of Overwatch's heroes. So I
made this script, intended to suggest counterpicks for me. The script is
completely client-side with no modification to the binary or manipulation
of network communications.

## How do I get set up?

1. Install Python 3.5 and pip
2. pip install -r requirements.txt should install all the necessary requirements. You may want to use a virtual environment for them.

## How do I use it?
Running:
    Linux:
        ./app.py
    Windows
        python.exe ./app.py

The first time it starts, it will look in "heroes/" for screenshots to build image data for individual heroes, needed for image recognition. 
You will be prompted for the screenshots folder the app will use.
Once it's running, get into a match on Overwatch.

## Can you summarize how it works?
    1. The script monitors the directory Overwatch saves its screenshots to, and opens the latest screenshot taken.
    2. An image recognition algorithm is used to guess what heroes are on the enemy team.
        * Note: Image recognition only gives reliable results outside of the hero selection screen.
    3. Using player-sourced data, it suggests heroes that have the biggest advantage against the enemy team.
    4. Once finished, it sounds a system alarm when done. Findings are recorded to the clipboard so you can paste them into in-game chat.

The last version of Overwatch this script was tested on is 1.8.0.2.34874


    
**At the moment, some modification of the code is needed to alter resolution of screenshots*
