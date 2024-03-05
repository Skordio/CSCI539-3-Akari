from enum import Enum
import time
from typing import Literal, List, Dict, Tuple
from collections import deque
import os
import random, copy

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = {'top': False, 'right': False, 'bottom': False, 'left': False}        
        self.is_start = False
        self.is_end = False
        self.number = None


    def __str__(self):
        return str(self.coords())
    
    
    def __repr__(self):
        return self.__str__()


    def get_key(self):
        return (self.x, self.y)
    
    
    def distance_to_cell(self, cell):
        return ((self.x - cell.x)**2 + (self.y - cell.y)**2)**0.5
    
    
    def legal_neighbors(self, maze, traversed_path=[], last_seen_number=None):
        neighbors = []
        if not self.walls['top'] and self.y > 0:
            neighbors.append(maze.cells[(self.x, self.y - 1)])
        if not self.walls['right'] and self.x < maze.grid_size_x - 1:
            neighbors.append(maze.cells[(self.x + 1, self.y)])
        if not self.walls['bottom'] and self.y < maze.grid_size_y - 1:
            neighbors.append(maze.cells[(self.x, self.y + 1)])
        if not self.walls['left'] and self.x > 0:
            neighbors.append(maze.cells[(self.x - 1, self.y)])

        i = len(neighbors) - 1
        while i >= 0:
            remove = False
            if neighbors[i] in traversed_path:
                remove = True

            if last_seen_number is not None and maze.numbers:
                if neighbors[i].number is not None and neighbors[i].number != last_seen_number+1:
                    remove = True
                if neighbors[i].is_end and last_seen_number != maze.numbers[-1]:
                    remove = True
            
            if remove:
                neighbors.pop(i)

            i -= 1

        return neighbors
    
    
    def coords(self):
        return (self.x, self.y)


class Path:
    path: list[Cell]
    last_seen_number: int

    def __init__(self, path=[], last_seen_number=0):
        self.path = path
        self.last_seen_number = last_seen_number


    def __str__(self):
        return str(self.path_coords())
    
    
    def __repr__(self):
        return self.__str__()


    def path_coords(self):
        return [cell.coords() for cell in self.path]


class Maze:
    grid_size_x: int
    grid_size_y: int
    cells: dict[tuple[int, int], Cell]
    start_cell: Cell
    end_cell: Cell
    numbers: list[int]
    
    def __init__(self, grid_size_x=15, grid_size_y=12):
        self.set_grid_size(grid_size_x, grid_size_y)
        self.reset_cells()
        self.numbers = []
        
        
    def set_grid_size(self, x, y):
        self.grid_size_x = x
        self.grid_size_y = y
        
        
    def add_number(self, number):
        self.numbers.append(number)
        self.numbers.sort()
        
        
    def remove_number(self, number):
        self.numbers.remove(number)
        self.numbers.sort()
        
        
    def reset_cells(self):
        self.cells = {(x, y): Cell(x, y) for x in range(self.grid_size_x) for y in range(self.grid_size_y)}
        self.start_cell = None
        self.end_cell = None


    def set_start(self, x, y):
        if self.start_cell is not None:
            self.start_cell.is_start = False
        self.start_cell = self.cells[(x, y)]
        self.start_cell.is_start = True


    def set_end(self, x, y):
        if self.end_cell is not None:
            self.end_cell.is_end = False
        self.end_cell = self.cells[(x, y)]
        self.end_cell.is_end = True


    def load_from_file(self, filename):
        with open(os.path.join('mazes', filename), 'rb') as maze_file:
            grid_size_x_byte = maze_file.read(1)
            grid_size_y_byte = maze_file.read(1)
            
            grid_size_x = int.from_bytes(grid_size_x_byte, "big")
            grid_size_y = int.from_bytes(grid_size_y_byte, "big")
            
            self.__init__(grid_size_x, grid_size_y)
            
            self.set_grid_size(grid_size_x, grid_size_y)
            self.reset_cells()
            
            start_cell_x_byte = maze_file.read(1)
            start_cell_y_byte = maze_file.read(1)
            
            start_cell_x = int.from_bytes(start_cell_x_byte, "big")
            start_cell_y = int.from_bytes(start_cell_y_byte, "big")
            
            
            end_cell_x_byte = maze_file.read(1)
            end_cell_y_byte = maze_file.read(1)
            
            end_cell_x = int.from_bytes(end_cell_x_byte, "big")
            end_cell_y = int.from_bytes(end_cell_y_byte, "big")
            
            x = 0
            y = 0
            while (byte := maze_file.read(1)) and y < grid_size_y:
                    
                byte_str = bin(int.from_bytes(byte, 'big'))[2:].rjust(8, '0')
                
                firstFour = byte_str[:4]
                
                self.cells[(x, y)].walls['top'] = firstFour[0] == '1'
                self.cells[(x, y)].walls['right'] = firstFour[1] == '1'
                self.cells[(x, y)].walls['bottom'] = firstFour[2] == '1'
                self.cells[(x, y)].walls['left'] = firstFour[3] == '1'
                
                lastFour = byte_str[4:]
                cell_number = int(lastFour, base=2)
                
                self.cells[(x, y)].number = cell_number if cell_number != 0 else None
                
                x += 1
                if x == grid_size_x:
                    x = 0
                if x == 0:
                    y += 1
                
            self.set_start(start_cell_x, start_cell_y)
            self.set_end(end_cell_x, end_cell_y)

            for cell in self.cells.values():
                if cell.number is not None:
                    self.numbers.append(cell.number)
            self.numbers.sort()


    def save_to_file(self, filename):
        with open(os.path.join('mazes', filename), 'wb') as maze_file:
            maze_file.write(int(self.grid_size_x).to_bytes(1, 'big'))
            maze_file.write(int(self.grid_size_y).to_bytes(1, 'big'))
                    
            start_cell = next((cell for cell in self.cells.values() if cell.is_start), None)
            end_cell = next((cell for cell in self.cells.values() if cell.is_end), None)
            
            maze_file.write(int(start_cell.x).to_bytes(1, 'big'))
            maze_file.write(int(start_cell.y).to_bytes(1, 'big'))
            
            maze_file.write(int(end_cell.x).to_bytes(1, 'big'))
            maze_file.write(int(end_cell.y).to_bytes(1, 'big'))
            
            for y in range(self.grid_size_y):
                for x in range(self.grid_size_x):
                    cell = self.cells[(x, y)]
                    byte = ''
                    
                    if cell.walls['top']:
                        byte += '1'
                    else:
                        byte += '0'
                    if cell.walls['right']:
                        byte += '1'
                    else:
                        byte += '0'
                    if cell.walls['bottom']:
                        byte += '1'
                    else:
                        byte += '0'
                    if cell.walls['left']:
                        byte += '1'
                    else:
                        byte += '0'
                    
                    if cell.number is not None:
                        byte += bin(cell.number)[2:].rjust(4, '0')
                    else:
                        byte += '0000'
                    
                    maze_file.write(int(byte, base=2).to_bytes(1, 'big'))


    def solve_dfs(self, one_solution=False) -> List[Path]:
        with open('solver_output_dfs.txt', 'w') as f:
            traversed = Path(path=[], last_seen_number=0)
            last_seen_number = 0
            solutions = []
            stack = [(None, self.start_cell)]
            iterations = 0
            while stack:
                iterations += 1
                current_cell = stack.pop()[1]
                traversed.path.append(current_cell)
                last_seen_number = current_cell.number if current_cell.number is not None else last_seen_number
                # if we are at the end, we have the solution
                if current_cell.is_end == True:
                    if one_solution:
                        f.write(f'iterations: {iterations}\n')
                        return [traversed]
                    else:
                        solutions.append(copy.deepcopy(traversed))
                        legal_neighbors = []
                else:
                    # check for legal neighbors
                    legal_neighbors = current_cell.legal_neighbors(self, traversed.path, last_seen_number)
                # if there are legal neighbors, add them to the stack
                if legal_neighbors:
                    for neighbor in legal_neighbors:
                        stack.append((current_cell, neighbor))
                # if there aren't any legal neighbors, we need to correct the traversed path to match the next cell on the stack
                elif stack:
                    while traversed.path and stack[-1][0] != traversed.path[-1]:
                        removing_cell = traversed.path.pop()
                        if removing_cell.number is not None:
                            last_seen_number = removing_cell.number - 1
                
            f.write(f'iterations: {iterations}\n')
            return solutions
    

    def solve_bfs(self, one_solution=False) -> List[Path]:
        with open('solver_output_bfs.txt', 'w') as f:
            solutions = []
            possible_solutions = [Path([self.start_cell])]
            new_solutions = []
            iterations = 0

            while possible_solutions:
                # for each path in the list
                for solution in possible_solutions:
                    iterations += 1
                    # get the last cell in the path
                    current = solution.path[-1]
                    # if the last cell is the end, we have the solution
                    if current.is_end:
                        if one_solution:
                            f.write(f'iterations: {iterations}\n')
                            return [solution]
                        else:
                            solutions.append(solution)
                            break
                    # for each legal neighbor of the last cell, create a new path and create a new list of possible solutions for the next iteration
                    for neighbor in current.legal_neighbors(self, solution.path, solution.last_seen_number):
                        new_path = Path(solution.path + [neighbor], neighbor.number if neighbor.number is not None else solution.last_seen_number)
                        new_solutions.append(new_path)
                # set the list of possible solutions to the list of new solutions
                possible_solutions = new_solutions
                new_solutions = []
                # repeat until we find the solution

            f.write(f'iterations: {iterations}\n')
            return solutions
    

    def rate_legal_neighbors(self, legal_neighbors, last_seen_number):
        rated_neighbors = []
        next_cell = None
        if self.numbers and last_seen_number < self.numbers[-1]:
            next_cell_num = last_seen_number + 1
            for cell in self.cells.values():
                if cell.number == next_cell_num:
                    next_cell = cell
                    break
        elif (self.numbers and last_seen_number == self.numbers[-1]) or not self.numbers:
            next_cell = self.end_cell

        if next_cell is not None:
            for neighbor in legal_neighbors:
                rated_neighbors.append((neighbor, neighbor.distance_to_cell(next_cell)))
            rated_neighbors.sort(key=lambda x: x[1], reverse=True)
            return [x[0] for x in rated_neighbors]
        else:
            rated_neighbors = legal_neighbors
            
    
    def solve_human_search(self, one_solution=False) -> List[Path]:
        with open('solver_output_human.txt', 'w') as f:
            traversed = Path(path=[], last_seen_number=0)
            solutions = []
            last_seen_number = 0
            stack = [(None, self.start_cell)]
            iterations = 0
            while stack:
                iterations += 1
                current_cell = stack.pop()[1]
                traversed.path.append(current_cell)
                last_seen_number = current_cell.number if current_cell.number is not None else last_seen_number
                # if we are at the end, we have the solution
                if current_cell.is_end:
                    if one_solution:
                        f.write(f'iterations: {iterations}\n')
                        return [traversed]
                    else:
                        solutions.append(copy.deepcopy(traversed))
                        legal_neighbors = []
                else:
                    # check for legal neighbors
                    legal_neighbors = current_cell.legal_neighbors(self, traversed.path, last_seen_number)
                    legal_neighbors = self.rate_legal_neighbors(legal_neighbors, last_seen_number)
                # if there are legal neighbors, add them to the stack
                if legal_neighbors:
                    for neighbor in legal_neighbors:
                        stack.append((current_cell, neighbor))
                # if there aren't any legal neighbors, we need to correct the traversed path to match the next cell on the stack
                elif stack:
                    while traversed.path and stack[-1][0] != traversed.path[-1]:
                        removing_cell = traversed.path.pop()
                        if removing_cell.number is not None:
                            last_seen_number = removing_cell.number - 1
                
            
            f.write(f'iterations: {iterations}\n')
            return solutions
   
        
    def new_maze_random_walls(self):
        solutions = []
        iterations = 0
        while len(solutions) == 0:
            iterations += 1
            self.set_grid_size(self.grid_size_x, self.grid_size_y)
            self.__init__(self.grid_size_x, self.grid_size_y)
            self.reset_cells()
            self.set_start(0, 0)
            self.set_end(self.grid_size_x-1, self.grid_size_y-1)
            cell_horizontal_pairs = []
            cell_vertical_pairs = []
            for x in range(self.grid_size_x):
                for y in range(self.grid_size_y):
                    if x < self.grid_size_x - 1:
                        cell_horizontal_pairs.append(((x, y), (x+1, y)))
                    if y < self.grid_size_y - 1:
                        cell_vertical_pairs.append(((x, y), (x, y+1))
                    )
            for cell in cell_horizontal_pairs:
                rand = random.randint(0, 1)
                if rand == 1:
                    self.cells[cell[0]].walls['right'] = True
                    self.cells[cell[1]].walls['left'] = True
                else:
                    self.cells[cell[0]].walls['right'] = False
                    self.cells[cell[1]].walls['left'] = False
            for cell in cell_vertical_pairs:
                rand = random.randint(0, 1)
                if rand == 1:
                    self.cells[cell[0]].walls['bottom'] = True
                    self.cells[cell[1]].walls['top'] = True
                else:
                    self.cells[cell[0]].walls['bottom'] = False
                    self.cells[cell[1]].walls['top'] = False
            self.numbers = []
            solutions = self.solve_dfs()
        self.remove_cutoff_sections()
        
        
    # this method takes a completely empty maze with no walls, and walks through a random path to take the first step in creating a maze
    # fun_score goes from 1 to 4, with 4 being the most fun and 1 being the least fun
    def new_maze_random_path(self, fun_score=3, print_checks=False):
        if fun_score not in [1, 2, 3, 4]:
            raise ValueError('fun_score must be 1, 2, 3, or 4')
        
        iterations = 0
        num_cells = self.grid_size_x * self.grid_size_y
        
        max_length_for_size = {
            5: 0.9,
            8: 0.8,
            11: 0.65,
            14: 0.5
        }
        
        max_length_percentage = 0.9
        average_size = (self.grid_size_x + self.grid_size_y) // 2
        
        for entry in max_length_for_size:
            if average_size >= entry:
                max_length_percentage = max_length_for_size[entry]
                
        if fun_score == 1:
            max_length_percentage = 0.5*max_length_percentage
        if fun_score == 2:
            max_length_percentage = 0.65*max_length_percentage
        if fun_score == 3:
            max_length_percentage = 0.8*max_length_percentage
            
        if print_checks:
            print(f'max_length: {max_length_percentage}')
        
        while True:
            try:
                path, path_iterations = self.generate_random_path(max_length_percentage)
                iterations += path_iterations
                
                if print_checks:
                    print('\nsuccessfully made path')
                
                self.draw_walls_around_path(path)
                self.place_numbers_in_path(path)
                
                self.remove_outer_walls()
                
                self.randomize_walls_for_path(path)
                self.remove_cutoff_sections()
                
                if fun_score > 2:
                    if not self.number_higher_than_one_reachable_before_one():
                        if print_checks:
                            print('failed number test')
                        continue
                    else:
                        if print_checks:
                            print('passed number test')
                    
                if fun_score > 3:
                    end_test = self.does_path_pass_end(path)
                    consecutive_test = self.are_two_non_consecutive_nums_next_to_each_other()
                    if not end_test and not consecutive_test:
                        if print_checks:
                            print('failed fun score == 4 test')
                        continue
                    else:
                        if print_checks:
                            print(f'passed fun score == 4 test with end_test: {end_test} and consecutive_test: {consecutive_test}')
                    
                new_solution = self.solve_bfs(one_solution=True)[0]
                if len(new_solution.path) < num_cells*(max_length_percentage-0.1):
                    if print_checks:
                        print('failed length test')
                    continue
                else:
                    if print_checks:
                        print('passed length test')
                break
            except:
                continue
        
        if print_checks:
            print(f'iterations: {iterations}')
        
    
    def generate_random_path(self, percent_traversed) -> Tuple[List[Cell], int]:
        traversed = []
        iterations = 0
        num_cells = self.grid_size_x * self.grid_size_y
        
        while True:
            iterations += 1
            # reset maze
            self.__init__(self.grid_size_x, self.grid_size_y)
            self.reset_cells()
            self.set_start(0, 0)
            end_x = random.randint(self.grid_size_x//4, self.grid_size_x-1)
            end_y = random.randint(self.grid_size_y//4, self.grid_size_y-1)
            self.set_end(end_x, end_y)
            # start at start cell
            current_cell = self.start_cell
            # traverse a path so we can use the legal_neighbors function
            traversed = [current_cell]
            while current_cell != self.end_cell:
                # call legal_neighbors
                legal_neighbors = current_cell.legal_neighbors(self, traversed)
                if self.end_cell in legal_neighbors and len(traversed) < num_cells*percent_traversed:
                    legal_neighbors.remove(self.end_cell)
                # if we have them, make a random choice and move to that cell
                if legal_neighbors:
                    next_cell = random.choice(legal_neighbors) 
                    traversed.append(next_cell)
                    current_cell = next_cell
                else:
                    # if we have no legal neighbors, we have likely hit a dead end,
                    # so we go back a few steps (based on size of maze) and try again
                    for i in range(self.grid_size_x + self.grid_size_y):
                        traversed.pop()
                        if traversed:
                            current_cell = traversed[-1]
                        else:
                            break
                        continue
                    break
            if current_cell == self.end_cell and len(traversed) > num_cells*percent_traversed:
                return traversed, iterations
        
        
    # this method takes a randomly generated path and places numbers throughout that path
    def place_numbers_in_path(self, path):
        step = int((self.grid_size_x + self.grid_size_y) // 2) + 5
        up_to = int(len(path) // step)
        place_nums_at = [0]
        for i in range(up_to):
            if i == 1:
                step_with_diff = step + 4
            else:
                step_with_diff = step + random.randint(-3, 3)
            place_nums_at.append(place_nums_at[i] + step_with_diff)
        for i in range(1, up_to):
            if place_nums_at[i] < len(path):
                self.add_number(i)
                path[place_nums_at[i]].number = i
            
            
    def draw_walls_around_path(self, path):
        previous_cell = None
        current_cell = None
        next_cell = None
        for i in range(len(path)):
            current_cell = path[i]
            if i != len(path)-1:
                next_cell = path[i+1]
            else:
                next_cell = None
            
            if next_cell and current_cell.x < next_cell.x:
                current_cell.walls['top'] = True
                if (current_cell.x, current_cell.y-1) in self.cells.keys():
                    self.cells[(current_cell.x, current_cell.y-1)].walls['bottom'] = True
                current_cell.walls['left'] = True
                if (current_cell.x-1, current_cell.y) in self.cells.keys():
                    self.cells[(current_cell.x-1, current_cell.y)].walls['right'] = True
                current_cell.walls['bottom'] = True
                if (current_cell.x, current_cell.y+1) in self.cells.keys():
                    self.cells[(current_cell.x, current_cell.y+1)].walls['top'] = True
                next_cell.walls['top'] = True
                if (next_cell.x, next_cell.y-1) in self.cells.keys():
                    self.cells[(next_cell.x, next_cell.y-1)].walls['bottom'] = True
                next_cell.walls['right'] = True
                if (next_cell.x+1, next_cell.y) in self.cells.keys():
                    self.cells[(next_cell.x+1, next_cell.y)].walls['left'] = True
                next_cell.walls['bottom'] = True
                if (next_cell.x, next_cell.y+1) in self.cells.keys():
                    self.cells[(next_cell.x, next_cell.y+1)].walls['top'] = True
            elif next_cell and current_cell.x > next_cell.x:
                current_cell.walls['top'] = True
                if (current_cell.x, current_cell.y-1) in self.cells.keys():
                    self.cells[(current_cell.x, current_cell.y-1)].walls['bottom'] = True
                current_cell.walls['right'] = True
                if (current_cell.x+1, current_cell.y) in self.cells.keys():
                    self.cells[(current_cell.x+1, current_cell.y)].walls['left'] = True
                current_cell.walls['bottom'] = True
                if (current_cell.x, current_cell.y+1) in self.cells.keys():
                    self.cells[(current_cell.x, current_cell.y+1)].walls['top'] = True
                next_cell.walls['top'] = True
                if (next_cell.x, next_cell.y-1) in self.cells.keys():
                    self.cells[(next_cell.x, next_cell.y-1)].walls['bottom'] = True
                next_cell.walls['left'] = True
                if (next_cell.x-1, next_cell.y) in self.cells.keys():
                    self.cells[(next_cell.x-1, next_cell.y)].walls['right'] = True
                next_cell.walls['bottom'] = True
                if (next_cell.x, next_cell.y+1) in self.cells.keys():
                    self.cells[(next_cell.x, next_cell.y+1)].walls['top'] = True
            elif next_cell and current_cell.y < next_cell.y:
                current_cell.walls['top'] = True
                if (current_cell.x, current_cell.y-1) in self.cells.keys():
                    self.cells[(current_cell.x, current_cell.y-1)].walls['bottom'] = True
                current_cell.walls['right'] = True
                if (current_cell.x+1, current_cell.y) in self.cells.keys():
                    self.cells[(current_cell.x+1, current_cell.y)].walls['left'] = True
                current_cell.walls['left'] = True
                if (current_cell.x-1, current_cell.y) in self.cells.keys():
                    self.cells[(current_cell.x-1, current_cell.y)].walls['right'] = True
                next_cell.walls['left'] = True
                if (next_cell.x-1, next_cell.y) in self.cells.keys():
                    self.cells[(next_cell.x-1, next_cell.y)].walls['right'] = True
                next_cell.walls['right'] = True
                if (next_cell.x+1, next_cell.y) in self.cells.keys():
                    self.cells[(next_cell.x+1, next_cell.y)].walls['left'] = True
                next_cell.walls['bottom'] = True
                if (next_cell.x, next_cell.y+1) in self.cells.keys():
                    self.cells[(next_cell.x, next_cell.y+1)].walls['top'] = True
            elif next_cell and current_cell.y > next_cell.y:
                current_cell.walls['left'] = True
                if (current_cell.x-1, current_cell.y) in self.cells.keys():
                    self.cells[(current_cell.x-1, current_cell.y)].walls['right'] = True
                current_cell.walls['right'] = True
                if (current_cell.x+1, current_cell.y) in self.cells.keys():
                    self.cells[(current_cell.x+1, current_cell.y)].walls['left'] = True
                current_cell.walls['bottom'] = True
                if (current_cell.x, current_cell.y+1) in self.cells.keys():
                    self.cells[(current_cell.x, current_cell.y+1)].walls['top'] = True
                next_cell.walls['left'] = True
                if (next_cell.x-1, next_cell.y) in self.cells.keys():
                    self.cells[(next_cell.x-1, next_cell.y)].walls['right'] = True
                next_cell.walls['right'] = True
                if (next_cell.x+1, next_cell.y) in self.cells.keys():
                    self.cells[(next_cell.x+1, next_cell.y)].walls['left'] = True
                next_cell.walls['top'] = True
                if (next_cell.x, next_cell.y-1) in self.cells.keys():
                    self.cells[(next_cell.x, next_cell.y-1)].walls['bottom'] = True
            if previous_cell and previous_cell.x < current_cell.x:
                current_cell.walls['left'] = False
                previous_cell.walls['right'] = False
            elif previous_cell and previous_cell.x > current_cell.x:
                current_cell.walls['right'] = False
                previous_cell.walls['left'] = False
            elif previous_cell and previous_cell.y < current_cell.y:
                current_cell.walls['top'] = False
                previous_cell.walls['bottom'] = False
            elif previous_cell and previous_cell.y > current_cell.y:
                current_cell.walls['bottom'] = False
                previous_cell.walls['top'] = False
            
            
            previous_cell = current_cell
            
            
    def randomize_walls_for_path(self, path):
        cell_horizontal_pairs = []
        cell_vertical_pairs = []
        for x in range(self.grid_size_x):
            for y in range(self.grid_size_y):
                if x < self.grid_size_x - 1:
                    cell_horizontal_pairs.append(((x, y), (x+1, y)))
                if y < self.grid_size_y - 1:
                    cell_vertical_pairs.append(((x, y), (x, y+1)))
        for cell_pair in cell_horizontal_pairs:
            if self.cells_consecutive_in_path(self.cells[cell_pair[0]], self.cells[cell_pair[1]], path):
                change_wall = False
            elif self.cells[cell_pair[0]] in path and self.cells[cell_pair[1]] in path:
                change_wall = random.choice([True, False, False, False, False, ])
            elif self.only_one_cell_in_path(self.cells[cell_pair[0]], self.cells[cell_pair[1]], path):
                change_wall = random.choice([True, False, False, False, False, ])
            else:
                change_wall = random.choice([True, False])
            if change_wall:
                self.cells[cell_pair[0]].walls['right'] = not self.cells[cell_pair[0]].walls['right']
                self.cells[cell_pair[1]].walls['left'] = not self.cells[cell_pair[1]].walls['left']
        for cell_pair in cell_vertical_pairs:
            if self.cells_consecutive_in_path(self.cells[cell_pair[0]], self.cells[cell_pair[1]], path):
                change_wall = False
            elif self.cells[cell_pair[0]] in path and self.cells[cell_pair[1]] in path:
                change_wall = random.choice([True, False, False, False, False, ])
            elif self.only_one_cell_in_path(self.cells[cell_pair[0]], self.cells[cell_pair[1]], path):
                change_wall = random.choice([True, False, False, False, False, ])
            else:
                change_wall = random.choice([True, False])
            if change_wall:
                self.cells[cell_pair[0]].walls['bottom'] = not self.cells[cell_pair[0]].walls['bottom']
                self.cells[cell_pair[1]].walls['top'] = not self.cells[cell_pair[1]].walls['top']
    
    
    def cells_consecutive_in_path(self, cell1, cell2, path:list):
        try:
            cell1_index = path.index(cell1)
            cell2_index = path.index(cell2)
        except ValueError:
            return False
        return abs(cell1_index - cell2_index) == 1
    
    
    def only_one_cell_in_path(self, cell1, cell2, path:list):
        return cell1 in path and not cell2 in path or not cell1 in path and cell2 in path
    
    
    def cell_is_square(self, cell:Cell):
        if cell.walls['top'] and cell.walls['right'] and cell.walls['bottom'] and cell.walls['left']:
            return True
        if cell.x == 0 and cell.walls['top'] and cell.walls['right'] and cell.walls['bottom']:
            return True
        if cell.x == self.grid_size_x - 1 and cell.walls['top'] and cell.walls['left'] and cell.walls['bottom']:
            return True
        if cell.y == 0 and cell.walls['right'] and cell.walls['bottom'] and cell.walls['left']:
            return True
        if cell.y == self.grid_size_y - 1 and cell.walls['top'] and cell.walls['left'] and cell.walls['right']:
            return True
                    
                    
    def remove_outer_walls(self):
        for cell in self.cells.values():
            if cell.x == 0:
                cell.walls['left'] = False
            if cell.x == self.grid_size_x - 1:
                cell.walls['right'] = False
            if cell.y == 0:
                cell.walls['top'] = False
            if cell.y == self.grid_size_y - 1:
                cell.walls['bottom'] = False
               
                
    def solution_similarity(self, solution1, solution2):
        # Convert both solutions to sets
        set1 = set(solution1)
        set2 = set(solution2)
        
        # Calculate intersection and union
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        # Compute the raw similarity based on common cells
        raw_similarity = len(intersection) / len(union) if union else 1  # Avoid division by zero
        
        # Adjust the similarity score to account for path length differences
        # This step considers the similarity in path lengths to slightly adjust the score
        length_similarity = 1 - abs(len(solution1) - len(solution2)) / (len(solution1) + len(solution2) + 1)  # +1 to avoid division by zero
        
        # Combine both similarity measures, weighting can be adjusted as needed
        # Here, we simply average them, but different weighting could be applied
        similarity_score = (raw_similarity + length_similarity) / 2
        
        # Convert to percentage
        similarity_percentage = similarity_score * 100
        
        return similarity_percentage
    

    def find_cells_in_cutoff_sections(self):
        traversed = set([])
        current = set([self.start_cell])
        next_iter = set([])
        while current:
            for cell in current:
                neighbors = cell.legal_neighbors(self)
                for neighbor in neighbors:
                    if not neighbor in traversed:
                        next_iter.add(neighbor)
                traversed.add(cell)
            current = next_iter
            next_iter = set([])
        traversed_set = set(traversed)
        cells_set = set(self.cells.values())
        cutoff_cells = cells_set - traversed_set
        cutoff_cells = list(cutoff_cells)
        cutoff_cells.sort(key=lambda x: x.coords())
        return cutoff_cells
    
    
    def remove_cutoff_sections(self):
        cutoff_cells = self.find_cells_in_cutoff_sections()
        while cutoff_cells:
            cell = cutoff_cells[0]
            # find which walls this cell has
            walls = []
            if cell.walls['top']:
                walls.append('top')
            if cell.walls['right']:
                walls.append('right')
            if cell.walls['bottom']:
                walls.append('bottom')
            if cell.walls['left']:
                walls.append('left')
            # remove one of the walls
            wall_to_remove = random.choice(walls)
            cell.walls[wall_to_remove] = False
            if wall_to_remove == 'top':
                self.cells[(cell.x, cell.y-1)].walls['bottom'] = False
            elif wall_to_remove == 'right':
                self.cells[(cell.x+1, cell.y)].walls['left'] = False
            elif wall_to_remove == 'bottom':
                self.cells[(cell.x, cell.y+1)].walls['top'] = False
            elif wall_to_remove == 'left':
                self.cells[(cell.x-1, cell.y)].walls['right'] = False
            cutoff_cells = self.find_cells_in_cutoff_sections()
       
            
    def number_higher_than_one_reachable_before_one(self):
        possible_paths = [Path([self.start_cell])]
        new_paths = []
        iterations = 0

        while possible_paths:
            for solution in possible_paths:
                iterations += 1
                current = solution.path[-1]
                if current.number != None:
                    if current.number > 1:
                        return True
                    else:
                        continue
                for neighbor in current.legal_neighbors(self, solution.path):
                    new_path = Path(solution.path + [neighbor], neighbor.number if neighbor.number is not None else solution.last_seen_number)
                    new_paths.append(new_path)
            possible_paths = new_paths
            new_paths = []
        
        return False
    
    
    def does_path_pass_end(self, path:list[Cell], fraction=2/3):
        for i in range(0, int(len(path)*fraction)):
            cell = path[i]
            # check four cells around the current cell
            if cell.x > 0 and self.cells[(cell.x-1, cell.y)].is_end:
                return True
            if cell.x < self.grid_size_x-1 and self.cells[(cell.x+1, cell.y)].is_end:
                return True
            if cell.y > 0 and self.cells[(cell.x, cell.y-1)].is_end:
                return True
            if cell.y < self.grid_size_y-1 and self.cells[(cell.x, cell.y+1)].is_end:
                return True
        return False
            
            
    def are_two_non_consecutive_nums_next_to_each_other(self):
        cells_with_numbers = [cell for cell in self.cells.values() if cell.number is not None]
        for i in range(len(cells_with_numbers)):
            cell = cells_with_numbers[i]
            # check four cells around the current cell
            if cell.x > 0 and self.cells[(cell.x-1, cell.y)].number is not None and abs(cell.number - self.cells[(cell.x-1, cell.y)].number) > 1:
                return True
            if cell.x < self.grid_size_x-1 and self.cells[(cell.x+1, cell.y)].number is not None and abs(cell.number - self.cells[(cell.x+1, cell.y)].number) > 1:
                return True
            if cell.y > 0 and self.cells[(cell.x, cell.y-1)].number is not None and abs(cell.number - self.cells[(cell.x, cell.y-1)].number) > 1:
                return True
            if cell.y < self.grid_size_y-1 and self.cells[(cell.x, cell.y+1)].number is not None and abs(cell.number - self.cells[(cell.x, cell.y+1)].number) > 1:
                return True
        return False
            