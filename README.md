# Overwatch Watcher

I'm not sure about you, but I have enough trouble memorizing all interactions
among the 18 types of Pokemon, let alone all of Overwatch's heroes. So I
made this script, intended to suggest counterpicks for me. The script is
completely client-side with no modification to the binary or manipulation
of network communications.

## How do I get set up?

1. Install Python 3.5 (and pip, but it should come with python anyway)
2. Create a virtual environment

    python -m venv ./venv

3. Install requirements

    pip install -r requirements.txt

4. Run app.py
    * There are two major configurations: Normal, and tiny.
    * Normal configuration analyzes full portraits. It's slow, but accurate and less subject to erroneous suggestions.

        python ./app.py

    * Tiny configuration currently analyzes 1/9th of the full image. Fast, but prone to misinterpretation.

        python ./app.py -t

## How do I use it?

* The first time it starts, it will look in "heroes/" for screenshots to build image data for individual heroes, needed for image recognition. 
* You will be prompted for the screenshots folder the app will use.

## Can you summarize how it works?
    1. The script monitors the directory Overwatch saves its screenshots to, and opens the latest screenshot taken.
    2. An image recognition algorithm is used to guess what heroes are on the enemy team.
        * Note: Image recognition only gives reliable results outside of the hero selection screen.
    3. Using player-sourced data, it suggests heroes that have the biggest advantage against the enemy team.
    4. Once finished, it sounds a system alarm when done. Findings are recorded to the clipboard so you can paste them into in-game chat.

The last version of Overwatch this script was tested on is 1.8.0.2.34874

**At the moment, some modification of the code is needed to alter resolution of screenshots*
