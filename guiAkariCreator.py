import tkinter as tk
import random, copy, time
from tkinter import simpledialog
from argparse import ArgumentParser

from akari import Cell, Akari, SolutionState, solve, generate_akari_puzzle

class AkariEditor:
    solution_state: SolutionState | None
    akari: Akari
    
    def __init__(self, master, load_from_file=None):
        self.master = master
        self.highlighted_cell = None
        self.cell_size = 40  # Visual size of cells in pixels
        self.solved = False
        
        self.akari = Akari(7, 7)
        
        self.solution_state = SolutionState(self.akari)
        
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

        self.size_button = tk.Button(self.button_frame1, text="Set Cell Size", command=self.cell_size_change_push)
        self.size_button.pack(side=tk.RIGHT)

        self.number_button = tk.Button(self.button_frame1, text="Place Number", command=self.place_number_push)
        self.number_button.pack(side=tk.LEFT)

        self.number_button = tk.Button(self.button_frame1, text="Remove Number", command=self.remove_number_push)
        self.number_button.pack(side=tk.LEFT)

        # Second row of buttons
        self.button_frame2 = tk.Frame(self.master)
        self.button_frame2.pack(side=tk.TOP, fill=tk.X, padx=20)

        self.solve_button = tk.Button(self.button_frame2, text="Solve", command=self.solve_push)
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
        
        self.master.bind('<space>', self.place_number_keypad)
        
        for key in ('0', '1', '2', '3', '4'):
            self.master.bind(key, self.place_number_keypad)

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
            
        if self.solution_state and self.solution_state.illuminated_cells[cell.coords()]:
            fill = 'yellow'
                
        cell_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="light grey", fill=fill, tags=("cell", f"{i},{j}"))
        
        if cell.number is not None:
            self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text=str(cell.number), font=('Arial', self.cell_size//2), fill='light grey', tags=(f"{cell.coords()}-number"))
            
        self.akari.cells[(i, j)].id = cell_id

    def cell_size_change_push(self):
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

    def place_number_keypad(self, event):
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
            
    def place_number_push(self):
        number = simpledialog.askinteger("Input", "Enter number to place in highlighted cell:", parent=self.master, minvalue=0, maxvalue=4)
        if number or number == 0:
            if self.highlighted_cell:
                self.akari.cells[self.highlighted_cell.coords()].number = number
                self.redraw_all()
                
    def remove_number_push(self):
        if self.highlighted_cell:
            self.canvas.delete(f"{self.highlighted_cell.coords()}-number")
            self.akari.cells[self.highlighted_cell.coords()].number = None
            self.redraw_all()
    
    def solve_push(self):
        if self.solution_state:
            self.remove_solution()
        solution, depth = solve(self.akari)
        if solution:
            print(f'solved in {depth} steps')
            self.solution_state = solution
            self.draw_solution()
        else:
            print(f'failed after {depth} steps')
        
    def new_akari(self):
        akari = generate_akari_puzzle(self.akari.grid_size_x, self.akari.grid_size_y)
        self.akari = akari if akari else self.akari
        self.redraw_all()
        
    
    def solve_step(self, akari: Akari, state: SolutionState | None) -> SolutionState | None:
        if not state:
            state = SolutionState(akari)
        unassigned_lamps = state.unassigned_lamps()
        if len(unassigned_lamps) == 0 or state.solved:
            return state
        else:
            for val in [True, False]:
                new_state = copy.deepcopy(state)
                print('took next step')
                new_state.assign_lamp_value(*unassigned_lamps[0], val)
                new_state.is_solved()
                if new_state.is_valid():
                    self.solution_state = new_state
                    self.redraw_all()
                    self.draw_solution()
                    input()
                    ok = new_state.forward_check()
                    if ok:
                        self.do_propogate_constrains()
                        input()
                        new_state = self.solve_step(akari, new_state)
                        if new_state and new_state.solved:
                            return new_state
                    else:
                        continue
        return None
    
    def propagate_constraints(self,):
        if self.solution_state:
            changes_made = True
            while changes_made:
                print('propagating')
                changes_made = False
                change_made = ''
                for cell in self.akari.cells.values():
                    if cell.is_black or self.solution_state.lamps[cell.coords()] is not None:
                        continue
                    
                    must_have_lamp, cannot_have_lamp = self.solution_state.check_cell_constraints(cell)
                    if must_have_lamp:
                        self.solution_state.assign_lamp_value(cell.x, cell.y, True)
                        if self.solution_state.is_valid():
                            changes_made = True
                            change_made = f'assigned lamp to {cell.coords()}'
                            break
                        else:
                            self.solution_state.assign_lamp_value(cell.x, cell.y, None)
                    elif cannot_have_lamp:
                        self.solution_state.assign_lamp_value(*cell.coords(), False)
                        if self.solution_state.is_valid():
                            changes_made = True
                            change_made = f'assigned no lamp to {cell.coords()}'
                            break
                        else:
                            self.solution_state.assign_lamp_value(cell.x, cell.y, None)
                # print(change_made)
                # self.redraw_all()
                # self.draw_solution()
                # input()
        
    def do_propogate_constrains(self):
        self.propagate_constraints()
        self.redraw_all()
        self.draw_solution()
            
    def draw_solution(self):
        self.redraw_all()
        if not self.solution_state:
            return
        for lamp in self.solution_state.lamps:
            if self.solution_state.lamps[lamp]:
                x, y = lamp
                x1, y1 = x * self.cell_size, y * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                self.canvas.create_oval(x1 + self.cell_size//4, y1 + self.cell_size//4, x2 - self.cell_size//4, y2 - self.cell_size//4, fill="yellow", tags="solution_path")

    def remove_solution(self):
        self.canvas.delete("solution_path")
        self.solution_state = None
        self.redraw_all()
    

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
