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
    
    def __init__(self, akari: Akari):
        self.lamps = {(x, y): None for x in range(akari.grid_size_x) for y in range(akari.grid_size_y)}
        self.illuminated_cells = {(x, y): False for x in range(akari.grid_size_x) for y in range(akari.grid_size_y)}
        for cell in akari.cells.values():
            if cell.is_black:
                self.lamps[(cell.x, cell.y)] = False
        self.solved = False
        
    def __str__(self):
        return str(self.lamps)
        
    def unassigned_lamps(self, akari: Akari) -> List[Tuple[int, int]]:
        white_cells_adjacent_to_numbered_cells = [cell for cell in akari.white_cells_adjacent_to_numbered_cells()]
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
    
    def assign_lamp_value(self, akari, x, y, value):
        self.lamps[(x, y)] = value
        self.update_illuminated_cells_for_new_lamp(akari, x, y)
        
    def update_illuminated_cells_for_new_lamp(self, akari: Akari, x, y):
        if self.lamps[(x, y)] is False:
            return
        for i in range(x+1, akari.grid_size_x):
            if akari.cells[(i, y)].is_black:
                break
            self.illuminated_cells[(i, y)] = True
        for i in range(x-1, -1, -1):
            if akari.cells[(i, y)].is_black:
                break
            self.illuminated_cells[(i, y)] = True
        for i in range(y+1, akari.grid_size_y):
            if akari.cells[(x, i)].is_black:
                break
            self.illuminated_cells[(x, i)] = True
        for i in range(y-1, -1, -1):
            if akari.cells[(x, i)].is_black:
                break
            self.illuminated_cells[(x, i)] = True
    
    def all_numbered_squares_satisfied(self, akari: Akari):
        for cell in akari.numbered_cells():
            lamp_count = 0
            for neighbor in cell.adjacent_cells(akari, white_only=True):
                if self.lamps[neighbor] is True:
                    lamp_count += 1
            if lamp_count != cell.number:
                return False
        return True
    
    def all_numbered_squares_valid(self, akari: Akari):
        for cell in akari.numbered_cells():
            lamp_count = 0
            for neighbor in cell.adjacent_cells(akari, white_only=True):
                if self.lamps[neighbor] is True:
                    lamp_count += 1
            if cell.number and lamp_count > cell.number:
                return False
        return True
                
    def all_cells_illuminated(self, akari: Akari):
        for cell in akari.cells.values():
            if not cell.is_black and not self.lamps[cell.coords()] and not self.illuminated_cells[cell.coords()]:
                return False
        return True
    
    def is_valid(self, akari):
        for lamp in self.assigned_lamps():
            if self.illuminated_cells[lamp]:
                return False
        return True if self.all_numbered_squares_valid(akari) else False
    
    def is_solved(self, akari):
        if self.all_numbered_squares_satisfied(akari) and self.all_cells_illuminated(akari):
            self.solved = True
            return True
        return False
    
    
def solve(akari: Akari, state: SolutionState | None) -> SolutionState | None:
    if not state:
        state = SolutionState(akari)
    unassigned_lamps = state.unassigned_lamps(akari)
    if len(unassigned_lamps) == 0 or state.solved:
        return state
    else:
        for val in [True, False]:
            new_state = copy.deepcopy(state)
            new_state.assign_lamp_value(akari, *unassigned_lamps[0], val)
            new_state.is_solved(akari)
            if new_state.is_valid(akari):
                new_state = solve(akari, new_state)
                if new_state and new_state.solved:
                    return new_state
    return None