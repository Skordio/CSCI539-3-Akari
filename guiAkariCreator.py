import tkinter as tk
import random, copy
from tkinter import simpledialog
from argparse import ArgumentParser

from akari import Cell, Akari, SolutionState, solve

class AkariEditor:
    illuminated_cells: dict[tuple[int, int], bool]
    
    def __init__(self, master, load_from_file=None):
        self.master = master
        self.highlighted_cell = None
        self.cell_size = 40  # Visual size of cells in pixels
        self.solved = False
        
        self.akari = Akari(7, 7)
        
        self.illuminated_cells = {(x, y): False for x in range(self.akari.grid_size_x) for y in range(self.akari.grid_size_y)}
        
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
        
        self.canvas.bind("<Button-1>", self.toggle_cell_color)

        # First row of buttons
        self.button_frame1 = tk.Frame(self.master)
        self.button_frame1.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(10, 0))
        
        self.reset_button = tk.Button(self.button_frame1, text="Reset", command=self.reset_grid)
        self.reset_button.pack(side=tk.LEFT)

        self.size_button = tk.Button(self.button_frame1, text="Set Grid Size", command=self.prompt_grid_size)
        self.size_button.pack(side=tk.LEFT)

        # Replace this with the ability to use number keys to set number for black squares
        # self.number_button = tk.Button(self.button_frame1, text="Place Number", command=self.place_number)
        # self.number_button.pack(side=tk.LEFT)

        self.size_button = tk.Button(self.button_frame1, text="Set Cell Size", command=self.prompt_cell_size)
        self.size_button.pack(side=tk.RIGHT)

        self.number_button = tk.Button(self.button_frame1, text="Place Number", command=self.place_number_prompt)
        self.number_button.pack(side=tk.LEFT)

        self.number_button = tk.Button(self.button_frame1, text="Remove Number", command=self.remove_number)
        self.number_button.pack(side=tk.LEFT)

        # Second row of buttons
        self.button_frame2 = tk.Frame(self.master)
        self.button_frame2.pack(side=tk.TOP, fill=tk.X, padx=20)

        self.solve_button = tk.Button(self.button_frame2, text="Solve", command=self.solve)
        self.solve_button.pack(side=tk.LEFT)

        self.remove_solution_button = tk.Button(self.button_frame2, text="Remove Solution", command=self.remove_solution)
        self.remove_solution_button.pack(side=tk.LEFT)
        
        # Third row of buttons
        self.button_frame3 = tk.Frame(self.master)
        self.button_frame3.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(0, 10))
        
        self.new_random_maze_button = tk.Button(self.button_frame3, text="Generate", command=self.new_akari)
        self.new_random_maze_button.pack(side=tk.LEFT)
        
        self.save_to_file_button = tk.Button(self.button_frame3, text="Save to File", command=self.save_to_file_prompt)
        self.save_to_file_button.pack(side=tk.RIGHT)
        
        self.load_from_file_button = tk.Button(self.button_frame3, text="Load from File", command=self.load_from_file)
        self.load_from_file_button.pack(side=tk.RIGHT)
        
        self.canvas.bind("<Button-3>", self.toggle_highlight)  # Right-click to highlight a cell
        
        self.master.bind('<space>', self.place_number)
        
        for key in ('0', '1', '2', '3', '4'):
            self.master.bind(key, self.place_number)

    def reset_grid(self):
        self.akari.reset_cells()
        for cell in self.akari.cells.values():
            cell.highlight_rect = None
        self.redraw_all()
        
    def redraw_all(self):
        self.canvas.delete("all")
        self.draw_grid()

    def prompt_grid_size(self):
        sizeX = simpledialog.askinteger("Input", "Enter grid size x:", parent=self.master, minvalue=5, maxvalue=20)
        sizeY = simpledialog.askinteger("Input", "Enter grid size y:", parent=self.master, minvalue=5, maxvalue=20)
        if sizeX and sizeY:
            self.akari.set_grid_size(int(sizeX), int(sizeY))
            self.resize_grid()

    def save_to_file_prompt(self):
        filename = simpledialog.askstring("Input", "Enter file name:", parent=self.master)
        if filename:
            self.akari.save_to_file(filename)
            
    def load_from_file(self, filename=None):
        if not filename:
            filename = simpledialog.askstring("Input", "Enter file name:", parent=self.master)
        if filename:
            self.reset_grid()
            self.akari.load_from_file(filename)
            self.resize_master()
            self.draw_grid()

    def resize_grid(self,):
        # self.akari.grid_size_x = int(sizeX)
        # self.akari.grid_size_y = int(sizeY)
        self.resize_master()
        self.reset_grid()

    def resize_master(self):
        canvas_width = self.cell_size * self.akari.grid_size_x
        canvas_height = self.cell_size * self.akari.grid_size_y
        self.canvas.config(width=canvas_width, height=canvas_height)
        if canvas_width+40 < 550:
            width = 550
        else:
            width = canvas_width+40
        self.master.geometry(f"{width}x{canvas_height+145}")

    def draw_grid(self):
        for i in range(self.akari.grid_size_x):
            for j in range(self.akari.grid_size_y):
                x1, y1 = i * self.cell_size, j * self.cell_size
                self.draw_cell(i, j, x1, y1)
                cell = self.akari.cells[(i, j)]
                    
        if self.highlighted_cell and self.highlighted_cell.highlight_rect:

            x1, y1 = self.highlighted_cell.coords()
            x1 = x1 * self.cell_size
            y1 = y1 * self.cell_size
            x2, y2 = x1 + self.cell_size, y1 + self.cell_size
            self.highlighted_cell.highlight_rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="cyan", width=2)

    def draw_cell(self, i, j, x1, y1):
        x2, y2 = x1 + self.cell_size, y1 + self.cell_size
        cell = self.akari.cells[(i, j)]
        fill = 'white'
        
        if cell.is_black:
            fill = 'black'
            
        if self.illuminated_cells[cell.coords()]:
            fill = 'yellow'
                
        cell_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="light grey", fill=fill, tags=("cell", f"{i},{j}"))
        
        if cell.number is not None:
            self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text=str(cell.number), font=('Arial', self.cell_size//2), fill='light grey', tags=(f"{cell.coords()}-number"))
            
        self.akari.cells[(i, j)].id = cell_id

    def prompt_cell_size(self):
        size = simpledialog.askinteger("Input", "Enter cell size (default is 40, min is 20, max is 60):", parent=self.master, minvalue=20, maxvalue=60)
        if size:
            self.cell_size = size        
            for cell in self.akari.cells.values():
                cell.highlight_rect = None
            self.canvas.delete("all")
            self.resize_master()
            self.draw_grid()
            
    def toggle_cell_color(self, event):
        # i and j are coords for cell that was clicked
        i, j = (event.x // self.cell_size, event.y // self.cell_size)
        cell = self.akari.cells[(i, j)]
        cell.is_black = not cell.is_black
        if not cell.is_black:
            cell.number = None
            self.canvas.delete(f"{cell.coords()}-number")
        self.redraw_all()
            
    def toggle_highlight(self, event):
        # i and j are coords for cell that was clicked
        i, j = (event.x // self.cell_size, event.y // self.cell_size)
        
        # if we clicked the already highlighted cell
        if self.highlighted_cell and self.highlighted_cell == self.akari.cells[(i, j)] and self.highlighted_cell.highlight_rect:
            self.canvas.delete(self.highlighted_cell.highlight_rect)
            self.highlighted_cell.highlight_rect = None
            self.highlighted_cell = None
        else:
            if self.highlighted_cell and self.highlighted_cell.highlight_rect:
                self.canvas.delete(self.highlighted_cell.highlight_rect)
                self.highlighted_cell.highlight_rect = None

            self.highlighted_cell = self.akari.cells[(i, j)]

            x1, y1 = i * self.cell_size, j * self.cell_size
            x2, y2 = x1 + self.cell_size, y1 + self.cell_size
            self.highlighted_cell.highlight_rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="cyan", width=2)

    def place_number(self, event):
        number = 0
        if(event.keysym == 'space'):
            number = -1
        else:
            number = int(event.char)
        
        if self.highlighted_cell:
            if number == -1:
                self.canvas.delete(f"{self.highlighted_cell.coords()}-number")
                self.akari.cells[self.highlighted_cell.coords()].number = None
            else:
                self.akari.cells[self.highlighted_cell.coords()].number = number
            self.redraw_all()
            
    def place_number_prompt(self):
        number = simpledialog.askinteger("Input", "Enter number to place in highlighted cell:", parent=self.master, minvalue=0, maxvalue=4)
        if number or number == 0:
            if self.highlighted_cell:
                self.akari.cells[self.highlighted_cell.coords()].number = number
                self.redraw_all()
                
    def remove_number(self):
        if self.highlighted_cell:
            self.canvas.delete(f"{self.highlighted_cell.coords()}-number")
            self.akari.cells[self.highlighted_cell.coords()].number = None
            self.redraw_all()
    
    def solve(self):
        if self.solved:
            self.remove_solution()
        solution = solve(self.akari, None)
        if solution:
            self.solved = True
            self.draw_solution(solution)
        # TODO implement this
    
    def solve_step(self, akari: Akari, state: SolutionState | None) -> SolutionState | None:
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
                self.illuminated_cells = new_state.illuminated_cells
                if new_state.is_valid(akari):
                    self.redraw_all()
                    self.draw_solution(new_state)
                    print(f'state.all_numbered_squares_satisfied: {new_state.all_numbered_squares_satisfied(akari)}')
                    print(f'state.all_cells_illuminated: {new_state.all_cells_illuminated(akari)}')
                    input(f'state.solved: {new_state.solved}')
                    new_state = self.solve_step(akari, new_state)
                    if new_state and new_state.solved:
                        return new_state
        return None
            
    def draw_solution(self, solution: SolutionState):
        for lamp in solution.lamps:
            if solution.lamps[lamp]:
                x, y = lamp
                x1, y1 = x * self.cell_size, y * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                self.canvas.create_oval(x1 + self.cell_size//4, y1 + self.cell_size//4, x2 - self.cell_size//4, y2 - self.cell_size//4, fill="yellow", tags="solution_path")

    def remove_solution(self):
        self.canvas.delete("solution_path")
        self.solved = False
        
    def new_akari(self):
        # TODO implement this
        # fun_score = simpledialog.askinteger("Input", "Enter fun score from 1 to 4 (note - higher fun scores will take longer to generate):", parent=self.master, minvalue=1, maxvalue=4)
        # self.akari.new_maze_random_path(fun_score)
        # self.redraw_all()
        pass

parser = ArgumentParser(
                prog='guiAkariCreator.py',
                description='Edits, saves, and solves Akari puzzles')
parser.add_argument('-f','--filename', required=False, help='The filename of the puzzle to load from') 
args = parser.parse_args()

def main():
    root = tk.Tk()
    root.title("Akari Editor")
    app = AkariEditor(root, args.filename if args.filename else None)
    root.mainloop()

if __name__ == "__main__":
    main()
