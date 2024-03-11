# Akari Solver/Creator

For this assignment I chose to create a solver and creator for the puzzle known as Akari. It is implemented in a similar fashion to my previous maze creator, with a gui portion and the main code section.

## Usage

To use this program, start up guiAkariCreator.py with python. You can pass in the path to a puzzle file to load up a puzzle on startup, like this:

```
python3 \.guiAkariCreator.py -f .\puzzles\steve_akari_hard
```

Once you are in the program, you can use the generate button to create a new puzzle, and use the solve button to solve one.

## Measuring difficulty

To measure the difficulty of any given Akari puzzle to solve, I recorded several metrics from the solver function: 

- Total times propogation of constraints was used
- Total times forward checking was used
- Total times backtracking was used

I used these metrics to gauge how difficult the puzzle might be for a human to solve. More backtracking means the puzzle is harder, less constraint propogation means the puzzle is harder, and more forward checking required means the puzzle is harder. 