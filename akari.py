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
    
    def cells_that_must_have_lamps(self) -> list[tuple[int, int]]:
        numbered_cells = [cell for cell in self.cells.values() if cell.number is not None]
        cells_that_must_have_lamps:list[tuple[int, int]] = []
        
        for cell in numbered_cells:
            white_neighbors = cell.adjacent_cells(white_only=True)
            if len(white_neighbors) == cell.number:
                cells_that_must_have_lamps.extend(white_neighbors)
        
        return cells_that_must_have_lamps

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
    
    def __init__(self, akari: Akari, print_debug=False, auto_find_cells_that_must_have_lamps=True):
        self.lamps = {(x, y): None for x in range(akari.grid_size_x) for y in range(akari.grid_size_y)}
        self.illuminated_cells = {(x, y): False for x in range(akari.grid_size_x) for y in range(akari.grid_size_y)}
        self.akari = akari
        for cell in akari.cells.values():
            if cell.is_black:
                self.lamps[(cell.x, cell.y)] = False
                
        if auto_find_cells_that_must_have_lamps:
            cells_that_must_have_lamps = self.cells_that_must_have_lamps()
            if print_debug:
                print(f'{len(cells_that_must_have_lamps)} cells must have lamps')
            for cell in cells_that_must_have_lamps:
                self.assign_lamp_value(*cell, True)
            self.propagate_constraints()
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
        
    def cells_that_must_have_lamps(self) -> list[tuple[int, int]]:
        cells = self.akari.cells_that_must_have_lamps()
        for cell in cells:
            if self.lamps[cell]:
                cells.remove(cell)
        return cells
            
    def assigned_lamps(self, only_true=True):
        return  [key for key in self.lamps if self.lamps[key] is not None and self.lamps[key] is True] if only_true \
                else [key for key in self.lamps if self.lamps[key] is not None]
    
    def forward_check(self):
        # check if all unilluminated cells still could possibly be illuminated
        
        iterations = 0
        
        for cell in self.unilluminated_cells():
            iterations += 1
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
                return False, iterations
            
        return True, iterations
            
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
                if self.lamps[other_cell] is not None or self.illuminated_cells[other_cell] is True:
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
        iterations = 0
        while changes_made:
            iterations += 1
            changes_made = False
            for cell in self.akari.cells.values():
                if cell.is_black or self.lamps[cell.coords()] is not None:
                    continue
                
                must_have_lamp, cannot_have_lamp = self.check_cell_constraints(cell)
                if must_have_lamp:
                    self.assign_lamp_value(cell.x, cell.y, True)
                    if self.is_valid():
                        changes_made = True
                        break
                    else:
                        self.assign_lamp_value(cell.x, cell.y, None)
                elif cannot_have_lamp:
                    self.assign_lamp_value(*cell.coords(), False)
                    if self.is_valid():
                        changes_made = True
                        break
                    else:
                        self.assign_lamp_value(cell.x, cell.y, None)
        return iterations

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
        if not self.all_numbered_squares_valid():
            return False
        for lamp in self.assigned_lamps():
            if self.illuminated_cells[lamp]:
                return False
        return True if self.all_numbered_squares_valid() else False
    
    def is_solved(self):
        if self.all_numbered_squares_satisfied() and self.all_cells_illuminated():
            self.solved = True
            return True
        return False
    
    
def solve(
    
            akari: Akari, \
            state: SolutionState | None = None, \
            depth:int = 0, max_depth:int|None = None, \
            total_prop_iters = 0, \
            total_check_iters = 0, \
            backtracks = 0, \
            decision_points = 0 \
    
    ) -> tuple[SolutionState | None, int, int, int, int, int]:
    depth += 1
    
    if not state:
        state = SolutionState(akari)
        
    unassigned_lamps = state.unassigned_lamps()
    if len(unassigned_lamps) > 1:  # More than one choice counts as a decision point
        decision_points += 1
    
    if max_depth and depth > max_depth:
        return None, depth, total_prop_iters, total_check_iters, backtracks, decision_points
    
    if len(unassigned_lamps) == 0 or state.solved:
        return state, depth, total_prop_iters, total_check_iters, backtracks, decision_points
    else:
        for val in [True, False]:
            new_state = copy.deepcopy(state)
            new_state.assign_lamp_value(*unassigned_lamps[0], val)
            new_state.is_solved()
            if new_state.is_valid():
                ok, check_iters = new_state.forward_check()
                if ok:
                    prop_iters = new_state.propagate_constraints()
                    result, new_depth, new_prop_iters, new_check_iters, new_backtracks, new_decision_points = solve(
                            akari, new_state, depth, max_depth, \
                            total_prop_iters=total_prop_iters + prop_iters, \
                            total_check_iters=total_check_iters + check_iters, \
                            backtracks=backtracks, \
                            decision_points=decision_points \
                        )
                    if result and result.solved:
                        return result, new_depth, new_prop_iters, new_check_iters, new_backtracks, new_decision_points
                    else:
                        backtracks = new_backtracks + 1
                        decision_points = new_decision_points
                        total_check_iters = new_check_iters
                        total_prop_iters = new_prop_iters
                else:
                    backtracks += 1
            else: 
                backtracks += 1
    return None, depth, total_prop_iters, total_check_iters, backtracks, decision_points
    
def solve_basic(akari: Akari, state: SolutionState | None = None, depth:int = 0, max_depth:int|None = None) -> tuple[SolutionState | None, int]:
    depth += 1
    
    if not state:
        state = SolutionState(akari)
        
    unassigned_lamps = state.unassigned_lamps()
    
    if max_depth and depth > max_depth:
        return None, depth
    
    if len(unassigned_lamps) == 0 or state.solved:
        return state, depth
    else:
        for val in [True, False]:
            new_state = copy.deepcopy(state)
            new_state.assign_lamp_value(*unassigned_lamps[0], val)
            new_state.is_solved()
            if new_state.is_valid():
                ok, check_iters = new_state.forward_check()
                if ok:
                    new_state.propagate_constraints()
                    result, new_depth = solve_basic(akari, new_state, depth, max_depth)
                    
                    if result and result.solved:
                        return result, new_depth, 
                    else:
                        depth = new_depth
    return None, depth
    
class AkariGenerator:
    def add_black_cells_and_clues(self, akari: Akari):
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

    def lamps_must_intersect(self, akari: Akari):
        solution = SolutionState(akari)
        cells_that_must_have_lamps = akari.cells_that_must_have_lamps()
                
        for cell in cells_that_must_have_lamps:
            solution.assign_lamp_value(*cell, True)
            if not solution.is_valid():
                return True
        
        return False

    def check_unique_solution(self, akari: Akari, find_solution_different_than:SolutionState|None=None) -> tuple[bool, SolutionState | None]:
        initial_state = SolutionState(akari)
        solution, solvable_depth = solve_basic(akari, max_depth=18)

        solution = find_solution_different_than if find_solution_different_than else solution
        
        if not solution:
            return False, None
        
        for x, y in initial_state.unassigned_lamps():
            if not solution.lamps[(x, y)]:
                test_state = copy.deepcopy(initial_state)
                test_state.assign_lamp_value(x, y, True)
                
                test_state, depth = solve_basic(akari, test_state, max_depth=solvable_depth+2)
                if test_state and test_state.solved:
                    # If the puzzle can be solved with this change, it means there's at least a second solution
                    return False, test_state

        return True, solution

    def adjust_puzzle_for_single_solution(self, akari: Akari):
        attempts = 0
        max_attempts = 50 

        # Function to revert changes
        def revert_changes(changes):
            for x, y, was_black, prev_number in changes:
                akari.cells[(x, y)].is_black = was_black
                akari.cells[(x, y)].number = prev_number

        while attempts < max_attempts:
            attempts += 1
            changes = []  # To track changes for potential reversion

            # Randomly choose a strategy for adjustment
            strategy = random.choice(['add_black', 'remove_black', 'add_number', 'remove_number'])

            if strategy == 'add_black':
                # Find all white cells that can be turned black
                white_cells = [(x, y) for (x, y), cell in akari.cells.items() if not cell.is_black and cell.number is None]
                if white_cells:
                    x, y = random.choice(white_cells)
                    changes.append((x, y, False, akari.cells[(x, y)].number))  # Store current state for reversion
                    akari.cells[(x, y)].is_black = True
                    akari.cells[(x, y)].number = None  # Ensure no number on newly blackened cell

            elif strategy == 'remove_black':
                # Find all black cells that can be turned white
                black_cells = [(x, y) for (x, y), cell in akari.cells.items() if cell.is_black and cell.number is None]
                if black_cells:
                    x, y = random.choice(black_cells)
                    changes.append((x, y, True, akari.cells[(x, y)].number))  # Store current state for reversion
                    akari.cells[(x, y)].is_black = False

            elif strategy == 'add_number':
                # Find black cells without numbers
                eligible_cells = [(x, y) for (x, y), cell in akari.cells.items() if cell.is_black and cell.number is None]
                if eligible_cells:
                    x, y = random.choice(eligible_cells)
                    number = random.randint(0, 4)  # Example: choose a random number, adjust logic as needed
                    changes.append((x, y, akari.cells[(x, y)].is_black, None))  # Store current state for reversion
                    akari.cells[(x, y)].number = number

            elif strategy == 'remove_number':
                # Find black cells with numbers
                numbered_cells = [(x, y) for (x, y), cell in akari.cells.items() if cell.is_black and cell.number is not None]
                if numbered_cells:
                    x, y = random.choice(numbered_cells)
                    changes.append((x, y, akari.cells[(x, y)].is_black, akari.cells[(x, y)].number))  # Store current state for reversion
                    akari.cells[(x, y)].number = None

            # Check if the current puzzle state has a unique solution
            unique, solution = self.check_unique_solution(akari)
            if unique:
                return True  # Puzzle successfully adjusted
            else:
                revert_changes(changes)  # Revert the puzzle to its previous state

        return False  # Indicate failure if max attempts are reached

    def generate_akari_puzzle(self, grid_size_x, grid_size_y, difficulty=1):
        # Difficulty is from 1 to 3
        attempts = 0
        
        while True:
            print(f'iteration {attempts}')
            attempts += 1
        
            akari = Akari(grid_size_x, grid_size_y)
            self.add_black_cells_and_clues(akari)
            
            while self.lamps_must_intersect(akari):
                akari = Akari(grid_size_x, grid_size_y)
                self.add_black_cells_and_clues(akari)
                
            solution, depth = solve_basic(akari, max_depth=18)
            
            if not solution:
                continue
            else:
                self.adjust_puzzle_for_single_solution(akari,)
            
            unique, solution = self.check_unique_solution(akari)
            
            if unique and solution:
                solution, depth, total_prop_iters, total_check_iters, backtracks, decision_points = solve(akari)
                if difficulty == 1 and ((backtracks <= 4) or (total_check_iters <= 30)):
                        print('puzzle generated successfully')
                        return akari
                elif difficulty == 2 and ((backtracks <= 8 and backtracks > 4) or (total_check_iters <= 60 and total_check_iters > 30)):
                        print('puzzle generated successfully')
                        return akari
                elif difficulty == 3 and ((backtracks > 8) or (total_check_iters > 60)):
                        print('puzzle generated successfully')
                        return akari
        