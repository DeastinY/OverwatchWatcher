Overview:

I'm not sure about you, but I have enough trouble memorizing all interactions
among the 18 types of Pokemon, let alone all of Overwatch's heroes. So I
made this script, intended to suggest counterpicks for me. The script is
completely client-side with no modification to the binary or manipulation
of network communications.

The way this script works:
    1. The script monitors the directory Overwatch saves its screenshots to, and opens the latest screenshot taken.
    2. An image recognition algorithm is used to guess what heroes are on the enemy team.
    3. Using player-sourced data, it suggests heroes that have the biggest advantage against the enemy team.
    4. Findings are recorded to the clipboard so the user can quickly paste them in in-game chat.

The last version of Overwatch this script was tested on is 1.7.0.2.34484

Installation instructions:

1. Install Python 3.5 and pip
2. pip install -r requirements.txt should install all the necessary requirements. You may want to use a virtual environment for them.
3.Linux
    python ./app.py
3.Windows
    python.exe ./app.py
4. The first time it will look in "heroes/" for screenshots to build image data for individual heroes, needed for image recognition. You will be prompted for the screenshots folder the app will use.
    
**At the moment, some modification of the code is needed to alter resolution of screenshots*
