from enum import Enum
import time
from typing import Literal, List, Dict, Tuple
from collections import deque
import os
import random, copy

class Cell:
    x: int
    y: int
    is_black: bool
    number: int | None
    
    # these are for use with the GUI
    highlight_rect: int | str | None
    id: int | str | None
    
    def __init__(self, x, y, is_black=False, number=None):
        self.x = x
        self.y = y
        self.is_black = is_black
        self.number = number
        self.highlight_rect = None
        self.id = None

    def __str__(self):
        return str(self.coords())
    
    def __repr__(self):
        return self.__str__()

    def get_key(self):
        return self.coords()
    
    def distance_to_cell(self, cell):
        return ((self.x - cell.x)**2 + (self.y - cell.y)**2)**0.5
    
    def adjacent_cells(self, akari, white_only=False):
        count = 0
        neighbors = [(self.x+1, self.y), (self.x-1, self.y), (self.x, self.y+1), (self.x, self.y-1)]
        final_neighbors = []
        
        for neighbor in neighbors:
            if neighbor in akari.cells and (not white_only or white_only and not akari.cells[neighbor].is_black):
                final_neighbors.append(neighbor)
                
        return final_neighbors
    
    def coords(self):
        return (self.x, self.y)


class Akari:
    grid_size_x: int
    grid_size_y: int
    cells: dict[tuple[int, int], Cell]
    
    def __init__(self, grid_size_x=7, grid_size_y=7):
        self.set_grid_size(grid_size_x, grid_size_y)
        self.reset_cells()
        
    def set_grid_size(self, x, y):
        self.grid_size_x = x
        self.grid_size_y = y
        
    def reset_cells(self):
        self.cells = {(x, y): Cell(x, y) for x in range(self.grid_size_x) for y in range(self.grid_size_y)}
        
    def numbered_cells(self):
        return [cell for cell in self.cells.values() if cell.number is not None]
        
    def white_cells_adjacent_to_numbered_cells(self):
        cells = set()
        for cell in self.numbered_cells():
            if cell.number is not None and cell.number > 0:
                cells.update(cell.adjacent_cells(self, white_only=True))
        return list(cells)

    def load_from_file(self, filename):
        filename = os.path.normpath(filename)
        if not filename.startswith('puzzles\\'):
            filename = os.path.join('puzzles', filename)
        if not os.path.exists('puzzles'):
            os.makedirs('puzzles')
        with open(filename, 'rb') as maze_file:
            grid_size_x_byte = maze_file.read(1)
            grid_size_y_byte = maze_file.read(1)
            
            grid_size_x = int.from_bytes(grid_size_x_byte, "big")
            grid_size_y = int.from_bytes(grid_size_y_byte, "big")
            
            self.__init__(grid_size_x, grid_size_y)
            
            self.set_grid_size(grid_size_x, grid_size_y)
            self.reset_cells()
            
            x = 0
            y = 0
            while (byte := maze_file.read(1)) and y < grid_size_y:
                    
                byte_str = bin(int.from_bytes(byte, 'big'))[2:].rjust(8, '0')
                
                firstFour = byte_str[:4]
                
                if firstFour == '0000':
                    self.cells[(x, y)].is_black = False
                else:
                    self.cells[(x, y)].is_black = True
                    
                    lastFour = byte_str[4:]
                    cell_number = int(lastFour, base=2)
                    
                    self.cells[(x, y)].number = cell_number if cell_number != 0 else None
                    
                x += 1
                if x == grid_size_x:
                    x = 0
                if x == 0:
                    y += 1

    def save_to_file(self, filename):
        if not os.path.exists('puzzles'):
            os.makedirs('puzzles')
        with open(os.path.join('puzzles', filename), 'wb') as akari_file:
            akari_file.write(int(self.grid_size_x).to_bytes(1, 'big'))
            akari_file.write(int(self.grid_size_y).to_bytes(1, 'big'))
            
            for y in range(self.grid_size_y):
                for x in range(self.grid_size_x):
                    cell = self.cells[(x, y)]
                    byte = ''
                    
                    if not cell.is_black:
                        byte = '00000000'
                    else:
                        byte = '1000'
                    
                        if cell.number is not None:
                            byte += bin(cell.number)[2:].rjust(4, '0')
                        else:
                            byte += '0000'
                        
                    
                    akari_file.write(int(byte, base=2).to_bytes(1, 'big'))


class SolutionState:
    lamps: dict[tuple[int, int], bool | None]
    solved = bool
    illuminated_cells: dict[tuple[int, int], bool]
    akari: Akari
    
    def __init__(self, akari: Akari):
        self.lamps = {(x, y): None for x in range(akari.grid_size_x) for y in range(akari.grid_size_y)}
        self.illuminated_cells = {(x, y): False for x in range(akari.grid_size_x) for y in range(akari.grid_size_y)}
        self.akari = akari
        for cell in akari.cells.values():
            if cell.is_black:
                self.lamps[(cell.x, cell.y)] = False
        self.solved = False
        
    def __str__(self):
        return str(self.lamps)
        
    def unassigned_lamps(self) -> List[Tuple[int, int]]:
        white_cells_adjacent_to_numbered_cells = [cell for cell in self.akari.white_cells_adjacent_to_numbered_cells()]
        unassigned_high_priority = []
        the_rest = []
        for key in self.lamps:
            if self.lamps[key] is None and self.illuminated_cells[key] is False:
                if key in white_cells_adjacent_to_numbered_cells:
                    unassigned_high_priority.append(key)
                else:
                    the_rest.append(key)
        return unassigned_high_priority + the_rest
    
    def assigned_lamps(self):
        return [key for key in self.lamps if self.lamps[key] is not None and self.lamps[key] is True]
    
    def assign_lamp_value(self, x, y, value):
        self.lamps[(x, y)] = value
        self.update_illuminated_cells_for_new_lamp(x, y)
        
    def update_illuminated_cells_for_new_lamp(self, x, y):
        if self.lamps[(x, y)] is False:
            return
        for i in range(x+1, self.akari.grid_size_x):
            if self.akari.cells[(i, y)].is_black:
                break
            self.illuminated_cells[(i, y)] = True
        for i in range(x-1, -1, -1):
            if self.akari.cells[(i, y)].is_black:
                break
            self.illuminated_cells[(i, y)] = True
        for i in range(y+1, self.akari.grid_size_y):
            if self.akari.cells[(x, i)].is_black:
                break
            self.illuminated_cells[(x, i)] = True
        for i in range(y-1, -1, -1):
            if self.akari.cells[(x, i)].is_black:
                break
            self.illuminated_cells[(x, i)] = True
    
    def all_numbered_squares_satisfied(self):
        for cell in self.akari.numbered_cells():
            lamp_count = 0
            for neighbor in cell.adjacent_cells(self.akari, white_only=True):
                if self.lamps[neighbor] is True:
                    lamp_count += 1
            if lamp_count != cell.number:
                return False
        return True
    
    def all_numbered_squares_valid(self):
        for cell in self.akari.numbered_cells():
            lamp_count = 0
            for neighbor in cell.adjacent_cells(self.akari, white_only=True):
                if self.lamps[neighbor] is True:
                    lamp_count += 1
            if cell.number and lamp_count > cell.number:
                return False
        return True
                
    def all_cells_illuminated(self):
        for cell in self.akari.cells.values():
            if not cell.is_black and not self.lamps[cell.coords()] and not self.illuminated_cells[cell.coords()]:
                return False
        return True
    
    def is_valid(self):
        for lamp in self.assigned_lamps():
            if self.illuminated_cells[lamp]:
                return False
        return True if self.all_numbered_squares_valid() else False
    
    def is_solved(self):
        if self.all_numbered_squares_satisfied() and self.all_cells_illuminated():
            self.solved = True
            return True
        return False
    
    
def solve(akari: Akari, state: SolutionState | None) -> SolutionState | None:
    if not state:
        state = SolutionState(akari)
    unassigned_lamps = state.unassigned_lamps()
    if len(unassigned_lamps) == 0 or state.solved:
        return state
    else:
        for val in [True, False]:
            new_state = copy.deepcopy(state)
            new_state.assign_lamp_value(*unassigned_lamps[0], val)
            new_state.is_solved()
            if new_state.is_valid():
                new_state = solve(akari, new_state)
                if new_state and new_state.solved:
                    return new_state
    return None

def generate_solved_grid(akari: Akari):
    # Randomly place lamps in a way that they don't illuminate each other
    # and try to fully illuminate the grid.
    
    attempts = 0
    max_attempts = 100  # To prevent infinite loops
    solution = SolutionState(akari)

    while not solution.all_cells_illuminated() and attempts < max_attempts:
        x = random.randint(0, akari.grid_size_x - 1)
        y = random.randint(0, akari.grid_size_y - 1)
        cell = akari.cells[(x, y)]
        
        # Skip if the cell is black or already has a lamp
        if cell.is_black or solution.lamps[(x, y)]:
            continue
        
        # Temporarily assign a lamp to check if it violates any rule
        solution.assign_lamp_value(x, y, True)
        if not solution.is_valid():
            # If invalid, remove the lamp and try another cell
            solution.assign_lamp_value(x, y, None)
        else:
            # Update illuminated cells for the newly placed lamp
            solution.update_illuminated_cells_for_new_lamp(x, y)
        
        attempts += 1

    # This is a basic and naive approach and might not fully illuminate the grid
    # or ensure that all rules are satisfied. Further refinement and checks may be necessary.
    if not solution.all_cells_illuminated():
        return akari, solution
    else:
        return None, None
    
def add_black_cells_and_clues(akari: Akari, solution_state: SolutionState):
    # This function assumes that a solved grid has been generated and
    # aims to modify it to create an Akari puzzle.
    
    # A simple strategy: turn some cells black around lamps and add clues
    for x, y in solution_state.assigned_lamps():
        # For each lamp, consider making some of its neighbors black
        neighbors = akari.cells[(x, y)].adjacent_cells(akari)
        for nx, ny in neighbors:
            # Randomly decide to turn this cell black
            if random.choice([True, False]):
                akari.cells[(nx, ny)].is_black = True
                akari.cells[(nx, ny)].number = None  # Ensure no number is assigned yet
                
                # Possibly assign a number to this black cell based on its adjacent lamps
                adjacent_lamps = 0
                for nnx, nny in akari.cells[(nx, ny)].adjacent_cells(akari):
                    if (nnx, nny) in solution_state.assigned_lamps():
                        adjacent_lamps += 1
                        
                # Randomly decide whether to add a clue (a number) or not
                if adjacent_lamps > 0 and random.choice([True, False]):
                    akari.cells[(nx, ny)].number = adjacent_lamps
    
    # Ensure every numbered black cell is valid according to the original solution
    for cell in akari.numbered_cells():
        x, y = cell.coords()
        if cell.number is not None:
            adjacent_lamps = 0
            for nx, ny in cell.adjacent_cells(akari):
                if (nx, ny) in solution_state.assigned_lamps():
                    adjacent_lamps += 1
            # Adjust the number if it doesn't match the actual number of adjacent lamps
            cell.number = adjacent_lamps

    # Additional step: Ensure the puzzle is still solvable and unique
    # This might involve verifying the puzzle with the solver to ensure it has a unique solution
    # and adjusting black cells or clues if necessary. This step is crucial for puzzle quality.
    
def check_unique_solution(akari: Akari):
    # Attempt to solve the puzzle using the existing solve function
    initial_state = SolutionState(akari)
    solved_state = solve(akari, initial_state)
    
    if solved_state is None or not solved_state.solved:
        # If the puzzle cannot be solved, then it definitely does not have a unique solution
        return False
    
    # Assuming the solve function attempts all possibilities and backtracks,
    # we can further verify the uniqueness by ensuring that no cell that can hold a lamp
    # has been left untested for both having and not having a lamp in the final solution.
    
    # A way to check this (though computationally intensive) is to attempt to place a lamp
    # in any of the cells not having a lamp in the solved state, and see if the puzzle still has a valid solution.
    for x, y in initial_state.lamps.keys():
        if solved_state.lamps[(x, y)] is None:
            # Temporarily place a lamp and check if the puzzle is still solvable
            test_state = copy.deepcopy(solved_state)
            test_state.assign_lamp_value(x, y, True)
            if test_state.is_valid():
                # If placing a lamp here doesn't immediately break the rules,
                # attempt to solve the puzzle again from this state.
                test_state = solve(akari, test_state)
                if test_state and test_state.solved:
                    # If the puzzle can be solved with this change, it means there's at least a second solution
                    return False
    
    # If we've gone through all possibilities and found no alternative solutions,
    # we can be reasonably confident the puzzle has a unique solution.
    return True

def adjust_puzzle_for_single_solution(akari: Akari):
    # This function assumes that the puzzle currently does not have a unique solution
    # and attempts to adjust it to meet this criterion.

    attempts = 0
    max_attempts = 50  # Prevent infinite loops

    while not check_unique_solution(akari) and attempts < max_attempts:
        # Randomly choose a strategy to adjust the puzzle
        strategy = random.choice(['add_black', 'remove_black', 'add_number', 'remove_number'])
        
        if strategy == 'add_black':
            # Attempt to add a black cell in a position that does not currently have one
            x, y = random.choice(list(akari.cells.keys()))
            if not akari.cells[(x, y)].is_black and akari.cells[(x, y)].number is None:
                akari.cells[(x, y)].is_black = True
                akari.cells[(x, y)].number = None

        elif strategy == 'remove_black':
            # Attempt to remove a black cell (making it white)
            black_cells = [cell for cell in akari.cells.values() if cell.is_black and cell.number is None]
            if black_cells:
                cell = random.choice(black_cells)
                cell.is_black = False
                cell.number = None

        elif strategy == 'add_number':
            # Attempt to add a number to a black cell that does not have one
            black_cells = [cell for cell in akari.cells.values() if cell.is_black and cell.number is None]
            if black_cells:
                cell = random.choice(black_cells)
                # Calculate the number based on adjacent lamps in the solution state
                # This step is simplified and assumes there's a way to know the solution state's lamp positions
                cell.number = random.randint(1, 4)  # Simplification; should be based on actual adjacent lamps

        elif strategy == 'remove_number':
            # Attempt to remove a number from a black cell that has one
            numbered_cells = [cell for cell in akari.cells.values() if cell.is_black and cell.number is not None]
            if numbered_cells:
                cell = random.choice(numbered_cells)
                cell.number = None

        attempts += 1

    if attempts >= max_attempts:
        print("Failed to adjust the puzzle to have a unique solution after maximum attempts.")
    else:
        print("Puzzle adjusted successfully to have a unique solution.")

# Note: Before calling generate_solved_grid, ensure akari.solution_state is initialized properly.
def generate_akari_puzzle(grid_size_x, grid_size_y):
    # Start with a solved grid
    akari = None
    solution = None
    while akari is None or solution is None:
        akari = Akari(grid_size_x, grid_size_y)
        akari, solution = generate_solved_grid(akari)
    
    # Add black cells and clues
    add_black_cells_and_clues(akari, solution)
    
    # Ensure the puzzle has a single solution
    while not check_unique_solution(akari):
        adjust_puzzle_for_single_solution(akari)
    
    # Return the puzzle that now has exactly one solution
    return akari