This is a fork over https://github.com/CarvellScott/OverwatchWatcher which does not seem to be developed anymore.

# Overwatch Watcher

    I'm not sure about you, but I have enough trouble memorizing all interactions
    among the 18 types of Pokemon, let alone all of Overwatch's heroes. So I
    made this script, intended to suggest counterpicks for me. The script is
    completely client-side with no modification to the binary or manipulation
    of network communications.
    - CarvellScott

## How do I get set up?

1. Install Python 3.5 (and pip, but it should come with python anyway)
2. Create a virtual environment

    python -m venv ./venv

3. Install requirements

    pip install -r requirements.txt

4. Set up OpenCV for Python 3. This might be more complicated, so look it up on Google :)

## How do I use it?

Either create screenshots ingame and tell the program their location, or use tab + a ingame to have the program take one.

## Can you summarize how it works?
1. The script monitors the directory Overwatch saves its screenshots to, and opens the latest screenshot taken or takes a screenshot on it's own.
2. An image recognition algorithm is used to guess what heroes are on the enemy team.
  * Note: Image recognition only gives reliable results under certain restrictions. On Fire/Death and changing locations currently give uncertain results
3. Using player-sourced data, it suggests heroes that have the biggest advantage against the enemy team.
4. Once finished, it sounds a system alarm when done. Findings are recorded to the clipboard so you can paste them into in-game chat.

This was last tested on 07 Mei 2017.

**At the moment, some modification of the code is needed to alter resolution of screenshots. Only works for 1440p right now**
