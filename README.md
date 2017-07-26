# Tetris in PyGame

Crappy sample Tetris implementation that I wrote because I didn't see
anything that had the features I wanted. Fairly basic, can be run on
Linux using a Docker container.

## Usage

To run the game from a Docker container in Linux, from the directory
you would like to store the game,

    curl https://raw.githubusercontent.com/ChadACrawford/ctetris/master/bin/ctetris -o ctetris
    chmod +x ctetris

Note that this method gives the Docker container access to your X
window display, so make sure you trust me before running it. :smile:

Otherwise, you can run it directly with Python 3 with

    pip install numpy pygame
    python3 app/tetris.py
