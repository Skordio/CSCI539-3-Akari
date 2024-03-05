import tkinter as tk
from tkinter import simpledialog
from argparse import ArgumentParser

from maze import Cell, Maze

class MazeEditor:
    def __init__(self, master, load_from_file=None):
        self.master = master
        self.highlighted_cell = None
        self.cell_size = 40  # Visual size of cells in pixels
        self.solved = False
        
        self.maze = Maze(15, 12)
        
        self.create_widgets()
        self.reset_grid()
        self.resize_grid()

        if load_from_file:
            self.load_from_file(load_from_file)

    def create_widgets(self):
        self.frame = tk.Frame(self.master, bd=0, highlightbackground="black", highlightthickness=1)
        self.frame.pack(side=tk.TOP, fill='none', expand=False, padx=20, pady=20, ipadx=0, ipady=0)

        self.canvas = tk.Canvas(self.frame)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.CENTER)

        # First row of buttons
        self.button_frame1 = tk.Frame(self.master)
        self.button_frame1.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(10, 0))
        
        self.reset_button = tk.Button(self.button_frame1, text="Reset", command=self.reset_grid)
        self.reset_button.pack(side=tk.LEFT)

        self.size_button = tk.Button(self.button_frame1, text="Set Grid Size", command=self.prompt_grid_size)
        self.size_button.pack(side=tk.LEFT)
        
        self.start_button = tk.Button(self.button_frame1, text="Set Start", command=self.set_start_cell)
        self.start_button.pack(side=tk.LEFT)

        self.end_button = tk.Button(self.button_frame1, text="Set End", command=self.set_end_cell)
        self.end_button.pack(side=tk.LEFT)

        self.number_button = tk.Button(self.button_frame1, text="Place Number", command=self.place_number)
        self.number_button.pack(side=tk.LEFT)

        self.size_button = tk.Button(self.button_frame1, text="Set Cell Size", command=self.prompt_cell_size)
        self.size_button.pack(side=tk.RIGHT)

        # Second row of buttons
        self.button_frame2 = tk.Frame(self.master)
        self.button_frame2.pack(side=tk.TOP, fill=tk.X, padx=20)

        self.dfs_solve_button = tk.Button(self.button_frame2, text="Solve DFS", command=self.solve_dfs)
        self.dfs_solve_button.pack(side=tk.LEFT)

        self.bfs_solve_button = tk.Button(self.button_frame2, text="Solve BFS", command=self.solve_bfs)
        self.bfs_solve_button.pack(side=tk.LEFT)

        self.human_solve_button = tk.Button(self.button_frame2, text="Solve Human Search", command=self.solve_human_search)
        self.human_solve_button.pack(side=tk.LEFT)

        self.remove_solution_button = tk.Button(self.button_frame2, text="Remove Solution", command=self.remove_solution)
        self.remove_solution_button.pack(side=tk.LEFT)
        
        # Third row of buttons
        self.button_frame3 = tk.Frame(self.master)
        self.button_frame3.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(0, 10))
        
        self.new_random_maze_button = tk.Button(self.button_frame3, text="Generate From Random Walls", command=self.new_maze_random_walls)
        self.new_random_maze_button.pack(side=tk.LEFT)
        
        self.new_random_maze_button = tk.Button(self.button_frame3, text="Generate From Random Path", command=self.new_maze_random_path)
        self.new_random_maze_button.pack(side=tk.LEFT)
        
        self.save_to_file_button = tk.Button(self.button_frame3, text="Save to File", command=self.save_to_file_prompt)
        self.save_to_file_button.pack(side=tk.RIGHT)
        
        self.load_from_file_button = tk.Button(self.button_frame3, text="Load from File", command=self.load_from_file)
        self.load_from_file_button.pack(side=tk.RIGHT)
        
        self.canvas.bind("<Button-3>", self.toggle_highlight)  # Right-click to highlight a cell

    def reset_grid(self):
        self.maze.cells = {(x, y): Cell(x, y) for x in range(self.maze.grid_size_x) for y in range(self.maze.grid_size_y)}
        for cell in self.maze.cells.values():
            cell.highlight_rect = None
        self.redraw_all()
        
    def redraw_all(self):
        self.canvas.delete("all")
        self.draw_grid()

    def prompt_grid_size(self):
        sizeX = simpledialog.askinteger("Input", "Enter grid size x:", parent=self.master, minvalue=5, maxvalue=20)
        sizeY = simpledialog.askinteger("Input", "Enter grid size y:", parent=self.master, minvalue=5, maxvalue=20)
        if sizeX and sizeY:
            self.maze.grid_size_x = int(sizeX)
            self.maze.grid_size_y = int(sizeY)
            self.resize_grid()

    def save_to_file_prompt(self):
        filename = simpledialog.askstring("Input", "Enter file name:", parent=self.master)
        if filename:
            self.maze.save_to_file(filename)
            
    def load_from_file(self, filename=None):
        if not filename:
            filename = simpledialog.askstring("Input", "Enter file name:", parent=self.master)
        if filename:
            self.reset_grid()
            self.maze.load_from_file(filename)
            self.resize_master()

            for cell in self.maze.cells.values():
                cell.highlight_rect = None
            self.draw_grid()

    def resize_grid(self,):
        # self.maze.grid_size_x = int(sizeX)
        # self.maze.grid_size_y = int(sizeY)
        self.resize_master()
        self.reset_grid()

    def resize_master(self):
        canvas_width = self.cell_size * self.maze.grid_size_x
        canvas_height = self.cell_size * self.maze.grid_size_y
        self.canvas.config(width=canvas_width, height=canvas_height)
        if canvas_width+40 < 550:
            width = 550
        else:
            width = canvas_width+40
        self.master.geometry(f"{width}x{canvas_height+145}")

    def draw_grid(self):
        for i in range(self.maze.grid_size_x):
            for j in range(self.maze.grid_size_y):
                x1, y1 = i * self.cell_size, j * self.cell_size
                self.draw_cell(i, j, x1, y1)
                cell = self.maze.cells[(i, j)]
                if not hasattr(cell, 'highlight_rect'):
                    cell.highlight_rect = None
                if cell.highlight_rect:
                    self.canvas.tag_raise(cell.highlight_rect)

    def prompt_cell_size(self):
        size = simpledialog.askinteger("Input", "Enter cell size (default is 40, min is 20, max is 60):", parent=self.master, minvalue=20, maxvalue=60)
        if size:
            self.cell_size = size        
            for cell in self.maze.cells.values():
                cell.highlight_rect = None
            self.canvas.delete("all")
            self.resize_master()
            self.draw_grid()

    def draw_cell(self, i, j, x1, y1):
        x2, y2 = x1 + self.cell_size, y1 + self.cell_size
        cell_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="light grey", tags=("cell", f"{i},{j}"))
        self.maze.cells[(i, j)].id = cell_id
        cell = self.maze.cells[(i, j)]
        if cell.is_start:
            self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="S", fill="green", font=('Arial', self.cell_size//2), tags=(f"{cell.coords()}-start"))
        elif cell.is_end:
            self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="E", fill="red", font=('Arial', self.cell_size//2), tags=(f"{cell.coords()}-end"))
        elif cell.number is not None:
            self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text=str(cell.number), font=('Arial', self.cell_size//2), tags=(f"{cell.coords()}-number"))
        self.update_cell_walls(i, j)

    def update_cell_walls(self, i, j):
        cell = self.maze.cells[(i, j)]
        x1, y1 = i * self.cell_size, j * self.cell_size
        x2, y2 = x1 + self.cell_size, y1 + self.cell_size

        self.canvas.delete(f"wall-{i},{j}-top")
        self.canvas.delete(f"wall-{i},{j}-right")
        self.canvas.delete(f"wall-{i},{j}-bottom")
        self.canvas.delete(f"wall-{i},{j}-left")

        if cell.walls['top']:
            self.canvas.create_line(x1, y1, x2, y1, fill="black", tags=(f"wall-{i},{j}-top"))
        if cell.walls['right']:
            self.canvas.create_line(x2, y1, x2, y2, fill="black", tags=(f"wall-{i},{j}-right"))
        if cell.walls['bottom']:
            self.canvas.create_line(x1, y2, x2, y2, fill="black", tags=(f"wall-{i},{j}-bottom"))
        if cell.walls['left']:
            self.canvas.create_line(x1, y1, x1, y2, fill="black", tags=(f"wall-{i},{j}-left"))

        self.canvas.bind("<Button-1>", self.toggle_wall)

    def toggle_wall(self, event):
        i, j = (event.x // self.cell_size, event.y // self.cell_size)
        cell = self.maze.cells[(i, j)]

        alsoUpdate = {'i':i, 'j':j}

        # Determine which wall to toggle based on the click position within the cell
        x, y = event.x % self.cell_size, event.y % self.cell_size
        if x < self.cell_size / 4 and i > 0:
            cell.walls['left'] = not cell.walls['left']
            if i > 0:
                otherCell = self.maze.cells[(i-1, j)]
                otherCell.walls['right'] = not otherCell.walls['right']
                alsoUpdate['i'] = i-1
        elif x > 3 * self.cell_size / 4 and i < self.maze.grid_size_x - 1:
            cell.walls['right'] = not cell.walls['right']
            if i < self.maze.grid_size_x - 1:
                otherCell = self.maze.cells[(i+1, j)]
                otherCell.walls['left'] = not otherCell.walls['left']
                alsoUpdate['i'] = i+1
        elif y < self.cell_size / 4 and j > 0:
            cell.walls['top'] = not cell.walls['top']
            if j > 0:
                otherCell = self.maze.cells[(i, j-1)]
                otherCell.walls['bottom'] = not otherCell.walls['bottom']
                alsoUpdate['j'] = j-1
        elif y > 3 * self.cell_size / 4 and j < self.maze.grid_size_y - 1:
            cell.walls['bottom'] = not cell.walls['bottom']
            if j < self.maze.grid_size_y - 1:
                otherCell = self.maze.cells[(i, j+1)]
                otherCell.walls['top'] = not otherCell.walls['top']
                alsoUpdate['j'] = j+1

        self.update_cell_walls(i, j)
        if alsoUpdate['i'] != i or alsoUpdate['j'] != j:
            self.update_cell_walls(alsoUpdate['i'], alsoUpdate['j'])
            
    def toggle_highlight(self, event):
        # i and j are coords for cell that was clicked
        i, j = (event.x // self.cell_size, event.y // self.cell_size)
        
        # if we clicked the already highlighted cell
        if self.highlighted_cell and self.highlighted_cell == self.maze.cells[(i, j)]:
            self.canvas.delete(self.highlighted_cell.highlight_rect)
            self.highlighted_cell.highlight_rect = None
            self.highlighted_cell = None
        else:
            if self.highlighted_cell:
                self.canvas.delete(self.highlighted_cell.highlight_rect)
                self.highlighted_cell.highlight_rect = None

            self.highlighted_cell = self.maze.cells[(i, j)]

            x1, y1 = i * self.cell_size, j * self.cell_size
            x2, y2 = x1 + self.cell_size, y1 + self.cell_size
            self.highlighted_cell.highlight_rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=2)

    def set_start_cell(self):
        if self.highlighted_cell:
            if self.highlighted_cell.is_start:
                self.canvas.delete(f"{self.highlighted_cell.coords()}-start")
                self.highlighted_cell.is_start = False
                self.maze.start_cell = None
                self.redraw_all()
            else:
                for cell in self.maze.cells.values():
                    self.canvas.delete(f"{cell.coords()}-start")
                    cell.is_start = False
                self.highlighted_cell.is_start = True
                self.maze.start_cell = self.highlighted_cell
            self.draw_grid()

    def set_end_cell(self):
        if self.highlighted_cell:
            if self.highlighted_cell.is_end:
                self.canvas.delete(f"{self.highlighted_cell.coords()}-end")
                self.highlighted_cell.is_end = False
                self.maze.end_cell = None
                self.redraw_all()
            else:
                for cell in self.maze.cells.values():
                    self.canvas.delete(f"{cell.coords()}-end")
                    cell.is_end = False
                self.highlighted_cell.is_end = True
                self.maze.end_cell = self.highlighted_cell
            self.draw_grid()

    def place_number(self):
        if self.highlighted_cell:
            if self.highlighted_cell.number is not None:
                self.canvas.delete(f"{self.highlighted_cell.coords()}-number")
                self.maze.remove_number(self.highlighted_cell.number)
                self.highlighted_cell.number = None
                self.redraw_all()
            else:
                number = simpledialog.askinteger("Input", "Enter cell number:", parent=self.master, minvalue=1, maxvalue=100)
                if number is not None:
                    self.highlighted_cell.number = number
                    self.maze.add_number(number)
            self.draw_grid()
        
    def find_cell_coordinates(self, cell):
        for i in range(self.maze.grid_size_x):
            for j in range(self.maze.grid_size_y):
                if self.maze.cells[(i, j)] == cell:
                    return i, j
        return None, None 
    
    def solve_dfs(self):
        if self.solved:
            self.remove_solution()
        solution = self.maze.solve_dfs(one_solution=True)[0]
        
        if solution:
            self.draw_solution(solution.path_coords())
            self.solved = True
        else:
            print("No solution found")
    
    def solve_bfs(self):
        if self.solved:
            self.remove_solution()
        solution = self.maze.solve_bfs(one_solution=True)[0]
        
        if solution:
            self.draw_solution(solution.path_coords())
            self.solved = True 
        else:
            print("No solution found")

    def solve_human_search(self):
        if self.solved:
            self.remove_solution()
        solution = self.maze.solve_human_search(one_solution=True)[0]
        if solution:
            self.draw_solution(solution.path_coords())
            self.solved = True
        else:
            print("No solution found")

    def remove_solution(self):
        self.canvas.delete("solution_path")
        self.solved = False

    def draw_solution(self, path):
        # Check if the path is empty
        if not path:
            return

        # Convert grid cell coordinates to canvas coordinates (centers of cells)
        canvas_path = [(x * self.cell_size + self.cell_size / 2, y * self.cell_size + self.cell_size / 2) for x, y in path]
        
        # Draw the solution path slowly
        for i in range(len(canvas_path) - 1):
            self.canvas.create_line(canvas_path[i], canvas_path[i + 1], fill="blue", width=2, tags="solution_path")
            self.canvas.update()
            self.canvas.after(30)
            
    def new_maze_random_walls(self):
        self.maze.new_maze_random_walls()
        self.redraw_all()
        
    def new_maze_random_path(self):
        fun_score = simpledialog.askinteger("Input", "Enter fun score from 1 to 4 (note - higher fun scores will take longer to generate):", parent=self.master, minvalue=1, maxvalue=4)
        self.maze.new_maze_random_path(fun_score)
        self.redraw_all()

parser = ArgumentParser(
                prog='guiMazeCreator.py',
                description='Edits, saves, and solves mazes')
parser.add_argument('-f','--filename', required=False, help='The filename of the maze to load from') 
args = parser.parse_args()

def main():
    root = tk.Tk()
    root.title("Maze Editor")
    app = MazeEditor(root, args.filename if args.filename else None)
    root.mainloop()

if __name__ == "__main__":
    main()
