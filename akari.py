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
    akari: 'Akari'
    
    # these are for use with the GUI
    highlight_rect: int | str | None
    id: int | str | None
    
    def __init__(self, akari:'Akari', x, y, is_black=False, number=None):
        self.akari = akari
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
    
    def adjacent_cells(self, white_only=False, numbered_only=False):
        count = 0
        neighbors = [(self.x+1, self.y), (self.x-1, self.y), (self.x, self.y+1), (self.x, self.y-1)]
        final_neighbors: list[tuple[int, int]] = []
        
        for neighbor in neighbors:
            if  neighbor in self.akari.cells.keys() and \
                ((not white_only) or (white_only and not self.akari.cells[neighbor].is_black)) and \
                ((not numbered_only) or (numbered_only and self.akari.cells[neighbor].number is not None)):
                final_neighbors.append(neighbor)
                
        return final_neighbors
    
    def adjacent_to_zero_cell(self):
        for neighbor in self.adjacent_cells():
            if self.akari.cells[neighbor].number == 0:
                return True
        return False
    
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
        self.cells = {(x, y): Cell(self, x, y) for x in range(self.grid_size_x) for y in range(self.grid_size_y)}
        
    def numbered_cells(self):
        return [cell for cell in self.cells.values() if cell.number is not None]
        
    def white_cells_adjacent_to_numbered_cells(self):
        cells = set()
        for cell in self.numbered_cells():
            if cell.number is not None and cell.number > 0:
                cells.update(cell.adjacent_cells(white_only=True))
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
                    
                    self.cells[(x, y)].number = cell_number if cell_number != 5 else None
                    
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
                            byte += bin(5)[2:].rjust(4, '0')
                        
                    
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
        
        # Prioritize cells by constraint strength
        cells_by_constraint = sorted(
            self.akari.cells.values(), 
            key=lambda cell: (-len(cell.adjacent_cells(white_only=True)), cell.x, cell.y)
        )
        
        high_priority = []
        for cell in cells_by_constraint:
            if self.lamps[cell.coords()] is None and not cell.is_black:
                adjacent_black_numbers = [self.akari.cells[coords].number for coords in cell.adjacent_cells() if self.akari.cells[coords].is_black and self.akari.cells[coords].number is not None]
                if adjacent_black_numbers:
                    high_priority.append(cell.coords())
                else:
                    break  # Stop after the most constrained cells
        
        return high_priority + [cell.coords() for cell in self.akari.cells.values() if self.lamps[cell.coords()] is None and not cell.is_black and cell.coords() not in high_priority]
    
    def assigned_lamps(self, only_true=True):
        return  [key for key in self.lamps if self.lamps[key] is not None and self.lamps[key] is True] if only_true \
                else [key for key in self.lamps if self.lamps[key] is not None]
    
    def forward_check(self):
        # check if all unilluminated cells still could possibly be illuminated
        
        for cell in self.unilluminated_cells():
            # if cell could contain a lamp, it could be valid
            if self.cell_can_contain_lamp(*cell.coords()):
                continue
            
            cell_can_be_illuminated = False
            # walk up, down, left, right from cell until we see a black cell or the edge of the grid
            # right
            for i in range(cell.x+1, self.akari.grid_size_x):
                if self.akari.cells[(i, cell.y)].is_black:
                    break
                if self.cell_can_contain_lamp(i, cell.y):
                    cell_can_be_illuminated = True
                    break
            # left
            if not cell_can_be_illuminated:
                for i in range(cell.x-1, -1, -1):
                    if self.akari.cells[(i, cell.y)].is_black:
                        break
                    if self.cell_can_contain_lamp(i, cell.y):
                        cell_can_be_illuminated = True
                        break
            # down
            if not cell_can_be_illuminated:
                for i in range(cell.y+1, self.akari.grid_size_y):
                    if self.akari.cells[(cell.x, i)].is_black:
                        break
                    if self.cell_can_contain_lamp(cell.x, i):
                        cell_can_be_illuminated = True
                        break
            # up
            if not cell_can_be_illuminated:
                for i in range(cell.y-1, -1, -1):
                    if self.akari.cells[(cell.x, i)].is_black:
                        break
                    if self.cell_can_contain_lamp(cell.x, i):
                        cell_can_be_illuminated = True
                        break
            if not cell_can_be_illuminated:
                return False
            
        return True
            
    def cell_can_contain_lamp(self, x:int, y:int):
        cell = self.akari.cells[(x, y)]
        
        if self.illuminated_cells[(x, y)]:
            return False
        if cell.is_black:
            return False
        
        adjacent_numbered_cells = cell.adjacent_cells(numbered_only=True)
        for adj in adjacent_numbered_cells:
            adj_cell = self.akari.cells[adj]
            if adj_cell.number is not None and self.numbered_cell_num_lamps(adj_cell) == adj_cell.number:
                return False
                
        return True
    
    def cell_must_contain_lamp(self, x:int, y:int):
        cell = self.akari.cells[(x, y)]
        must_have_lamp = False
        
        adjacent_numbered_cells = cell.adjacent_cells(numbered_only=True)
        for adj in adjacent_numbered_cells:
            adj_cell = self.akari.cells[adj]
            
            adj_cell_white_cells = adj_cell.adjacent_cells(white_only=True)
            for other_cell in adj_cell_white_cells:
                if self.lamps[other_cell] is not None:
                    adj_cell_white_cells.remove(other_cell)
                    
            if adj_cell.number is not None and self.numbered_cell_num_lamps(adj_cell) == adj_cell.number - 1 and len(adj_cell_white_cells) == 1:
                must_have_lamp = True
        
        return must_have_lamp
        
            
    def numbered_cell_num_lamps(self, cell:Cell):
        lamp_count = 0
        for neighbor in cell.adjacent_cells(white_only=True):
            if self.lamps[neighbor] is True:
                lamp_count += 1
        return lamp_count
    
    def assign_lamp_value(self, x, y, value):
        old_value = self.lamps[(x, y)]
        self.lamps[(x, y)] = value
        if value is True:
            self.update_illuminated_cells_for_lamp(x, y)
        elif value is False and old_value is True:
            self.update_illuminated_cells()
        
    def update_illuminated_cells(self):
        self.illuminated_cells = {(x, y): False for x in range(self.akari.grid_size_x) for y in range(self.akari.grid_size_y)}
        for lamp in [lamp for lamp in self.lamps.keys() if self.lamps[lamp]]:
            for i in range(lamp[0]+1, self.akari.grid_size_x):
                if self.akari.cells[(i, lamp[1])].is_black:
                    break
                self.illuminated_cells[(i, lamp[1])] = True
            for i in range(lamp[0]-1, -1, -1):
                if self.akari.cells[(i, lamp[1])].is_black:
                    break
                self.illuminated_cells[(i, lamp[1])] = True
            for i in range(lamp[1]+1, self.akari.grid_size_y):
                if self.akari.cells[(lamp[0], i)].is_black:
                    break
                self.illuminated_cells[(lamp[0], i)] = True
            for i in range(lamp[1]-1, -1, -1):
                if self.akari.cells[(lamp[0], i)].is_black:
                    break
                self.illuminated_cells[(lamp[0], i)] = True
        
    def update_illuminated_cells_for_lamp(self, x, y):
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
            for neighbor in cell.adjacent_cells(white_only=True):
                if self.lamps[neighbor] is True:
                    lamp_count += 1
            if lamp_count != cell.number:
                return False
        return True
    
    def propagate_constraints(self):
        changes_made = True
        while changes_made:
            changes_made = False
            for cell in self.akari.cells.values():
                if cell.is_black or self.lamps[cell.coords()] is not None:
                    continue
                
                must_have_lamp, cannot_have_lamp = self.check_cell_constraints(cell)
                if must_have_lamp:
                    self.assign_lamp_value(cell.x, cell.y, True)
                    if self.is_valid():
                        changes_made = True
                    else:
                        self.assign_lamp_value(cell.x, cell.y, None)
                elif cannot_have_lamp:
                    self.assign_lamp_value(*cell.coords(), False)
                    if self.is_valid():
                        changes_made = True
                    else:
                        self.assign_lamp_value(cell.x, cell.y, None)

    def check_cell_constraints(self, cell:Cell):
        cannot_have_lamp = not self.cell_can_contain_lamp(cell.x, cell.y)
        
        must_have_lamp = self.cell_must_contain_lamp(cell.x, cell.y)
                
        return must_have_lamp, cannot_have_lamp

    
    def all_numbered_squares_valid(self):
        for cell in self.akari.numbered_cells():
            lamp_count = 0
            for neighbor in cell.adjacent_cells(white_only=True):
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
    
    def unilluminated_cells(self):
        return [cell for cell in self.akari.cells.values() if not cell.is_black and not self.lamps[cell.coords()] and not self.illuminated_cells[cell.coords()]]
    
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
                ok = new_state.forward_check()
                if ok:
                    new_state.propagate_constraints()
                    new_state = solve(akari, new_state)
                    if new_state and new_state.solved:
                        return new_state
                else:
                    continue
    return None
   
    
def add_black_cells_and_clues(akari: Akari):
    # This function assumes that a solved grid has been generated and
    # aims to modify it to create an Akari puzzle.
    num_black_cells = random.randint(akari.grid_size_x * akari.grid_size_y // 8, akari.grid_size_x * akari.grid_size_y // 3)
    
    # A simple strategy: turn some cells black around lamps and add clues
    for i in range(num_black_cells):
        x = random.randint(0, akari.grid_size_x - 1)
        y = random.randint(0, akari.grid_size_y - 1)
        
        cell_cannot_be_black = False
        
        # Skip if placing a black cell here would make another black cell's constrain to be impossible to satisfy
        adjacent_black_cells = [cell for cell in akari.cells[(x, y)].adjacent_cells() if akari.cells[cell].is_black]
        for cell in adjacent_black_cells:
            cell = akari.cells[cell]
            cell_neighbors = cell.adjacent_cells(white_only=True)
            if len(cell_neighbors) == cell.number:
                cell_cannot_be_black = True
                break
            
        # Skip if the cell is already black
        if (x, y) in akari.numbered_cells():
            cell_cannot_be_black = True
        
        if cell_cannot_be_black:
            i += 1
            continue
        
        akari.cells[(x, y)].is_black = True
        
        # Randomly decide whether to add a clue (a number) or not
        if random.choice([True, False]):
            while True:
                number = random.choice([0, 1, 1, 2, 2, 3, 3, 4])
                cell_neighbors = akari.cells[(x, y)].adjacent_cells(white_only=True)
                if len(cell_neighbors) < number:
                    continue
                else:
                    break
            akari.cells[(x, y)].number = number  


def generate_solved_grid(akari: Akari):
    # Randomly place lamps in a way that they don't illuminate each other
    # and try to fully illuminate the grid.
    
    attempts = 0
    max_attempts = 100  # To prevent infinite loops
    solution = SolutionState(akari)

    while not (solution.is_valid() and solution.all_cells_illuminated()) and attempts < max_attempts:
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
            solution.update_illuminated_cells()
        
        attempts += 1

    # This is a basic and naive approach and might not fully illuminate the grid
    # or ensure that all rules are satisfied. Further refinement and checks may be necessary.
    if not solution.all_cells_illuminated():
        return akari, solution
    else:
        return None, None
    
    
def check_unique_solution(akari: Akari):
    print('check unique solution called')
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
        return False
    else:
        print("Puzzle adjusted successfully to have a unique solution.")
        return True


# Note: Before calling generate_solved_grid, ensure akari.solution_state is initialized properly.
def generate_akari_puzzle(grid_size_x, grid_size_y):
    good_puzzle = False
    good_puzzle_attempts = 10
    
    # while not good_puzzle and good_puzzle_attempts > 0:
    #     print(f'outside loop iteration {11-good_puzzle_attempts}')
    #     good_puzzle_attempts -= 1
    
    #     akari = Akari(grid_size_x, grid_size_y)
        
    #     add_black_cells_and_clues(akari)
        
    #     good_puzzle = adjust_puzzle_for_single_solution(akari)
    
    akari = Akari(grid_size_x, grid_size_y)
    add_black_cells_and_clues(akari)

    return akari
    
    # while akari is None or solution is None:
    #     akari = Akari(grid_size_x, grid_size_y)
    #     akari, solution = generate_solved_grid(akari)
    
    # # Ensure the puzzle has a single solution
    # while not check_unique_solution(akari):
    #     adjust_puzzle_for_single_solution(akari)
    
    # # Return the puzzle that now has exactly one solution
    # return akari