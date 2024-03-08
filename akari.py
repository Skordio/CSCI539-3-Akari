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
        self.is_black = False
        self.number = None
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
    
    def num_adjacent_white_squares(self, akari):
        count = 0
        neighbors = [(self.x+1, self.y), (self.x-1, self.y), (self.x, self.y+1), (self.x, self.y-1)]
        
        for neighbor in neighbors:
            if neighbor in akari.cells and not akari.cells[neighbor].is_black:
                count += 1
                
        return count
    
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

            