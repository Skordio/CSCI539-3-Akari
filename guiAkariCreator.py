import tkinter as tk
import random, copy, time, enum
from tkinter import simpledialog
from argparse import ArgumentParser

from akari import Cell, Akari, SolutionState, solve, AkariGenerator


class GuiMode(enum.Enum):
    SOLVE = 1
    CREATE = 2


class AkariEditor:
    solution_state: SolutionState | None
    akari: Akari
    mode: GuiMode
    
    def __init__(self, master, load_from_file=None, cell_size=40):
        self.master = master
        self.highlighted_cell = None
        self.cell_size = cell_size  # Visual size of cells in pixels
        self.mode = GuiMode.CREATE if not load_from_file else GuiMode.SOLVE
        
        self.akari = Akari(7, 7)
        
        self.solution_state = SolutionState(self.akari, auto_find_cells_that_must_have_lamps=False)
        
        self.create_widgets()
        self.reset_grid()
        self.resize_grid()

        if load_from_file:
            self.load_from_file(load_from_file)

    def mode_button_text(self):
        return "Current Mode: Create Mode" if self.mode == GuiMode.CREATE else "Current Mode: Solve Mode"

    def create_widgets(self):
        self.message = tk.Label(self.master, text="Welcome to Akari Editor!", font=('Arial', 20))
        self.message.pack(side=tk.TOP, fill='none', expand=False, padx=20, pady=20, ipadx=0, ipady=0)

        self.frame = tk.Frame(self.master, bd=0, highlightbackground="black", highlightthickness=1)
        self.frame.pack(side=tk.TOP, fill='none', expand=False, padx=20, pady=20, ipadx=0, ipady=0)

        self.canvas = tk.Canvas(self.frame)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.CENTER)
        
        self.canvas.bind("<Button-1>", self.mouse_click)

        # First row of buttons
        self.button_frame1 = tk.Frame(self.master)
        self.button_frame1.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(10, 0))
        
        self.reset_button = tk.Button(self.button_frame1, text="Reset", command=self.reset_grid)
        self.reset_button.pack(side=tk.LEFT)

        if self.mode == GuiMode.CREATE:
            self.creation_mode_buttons()
        else:
            self.solve_mode_buttons()
            

        self.cell_size_button = tk.Button(self.button_frame1, text="Set Cell Size", command=self.cell_size_change_push)
        self.cell_size_button.pack(side=tk.RIGHT)
        
        # Third row of buttons
        self.button_frame2 = tk.Frame(self.master)
        self.button_frame2.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(0, 10))
        
        self.new_random_akari_button = tk.Button(self.button_frame2, text="Generate", command=self.new_akari)
        self.new_random_akari_button.pack(side=tk.LEFT)
        
        self.check_unique_button = tk.Button(self.button_frame2, text="Check Unique", command=self.check_unique_push)
        self.check_unique_button.pack(side=tk.LEFT)
        
        self.toggle_gui_button = tk.Button(self.button_frame2, text=self.mode_button_text(), command=self.toggle_gui_mode)
        self.toggle_gui_button.pack(side=tk.LEFT)
        
        self.save_to_file_button = tk.Button(self.button_frame2, text="Save to File", command=self.save_to_file_prompt)
        self.save_to_file_button.pack(side=tk.RIGHT)
        
        self.load_from_file_button = tk.Button(self.button_frame2, text="Load from File", command=self.load_from_file)
        self.load_from_file_button.pack(side=tk.RIGHT)
        
        self.canvas.bind("<Button-3>", self.toggle_highlight)  # Right-click to highlight a cell
        
        self.master.bind('<space>', self.place_number_keypad)
        
        for key in ('0', '1', '2', '3', '4'):
            self.master.bind(key, self.place_number_keypad)

    def creation_mode_buttons(self):
        if hasattr(self, 'solve_button'):
            self.solve_button.destroy()
        if hasattr(self, 'remove_solution_button'):
            self.remove_solution_button.destroy()
        if hasattr(self, 'check_solution_button'):
            self.check_solution_button.destroy()

        self.grid_size_button = tk.Button(self.button_frame1, text="Set Grid Size", command=self.prompt_grid_size)
        self.grid_size_button.pack(side=tk.LEFT)

        self.toggle_number_button = tk.Button(self.button_frame1, text="Toggle Number", command=self.toggle_number)
        self.toggle_number_button.pack(side=tk.LEFT)

    def solve_mode_buttons(self):
        if hasattr(self, 'grid_size_button'):
            self.grid_size_button.destroy()
        if hasattr(self, 'toggle_number_button'):
            self.toggle_number_button.destroy()

        self.solve_button = tk.Button(self.button_frame1, text="Solve", command=self.solve_push)
        self.solve_button.pack(side=tk.LEFT)

        self.remove_solution_button = tk.Button(self.button_frame1, text="Remove Solution", command=self.remove_solution)
        self.remove_solution_button.pack(side=tk.LEFT)

        self.check_solution_button = tk.Button(self.button_frame1, text="Check Solution", command=self.check_if_solution_is_correct)
        self.check_solution_button.pack(side=tk.LEFT)

    def reset_grid(self):
        self.message.config(text="Welcome to Akari Editor!")
        self.solution_state = None
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
        self.master.geometry(f"{width}x{canvas_height+200}")

    def draw_grid(self):
        for i in range(self.akari.grid_size_x):
            for j in range(self.akari.grid_size_y):
                x1, y1 = i * self.cell_size, j * self.cell_size
                self.draw_cell(i, j, x1, y1)
                cell = self.akari.cells[(i, j)]
        self.draw_solution()
                    
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

    def mouse_click(self, event):
        # i and j are coords for cell that was clicked
        i, j = (event.x // self.cell_size, event.y // self.cell_size)

        if self.mode == GuiMode.CREATE:
            self.toggle_cell_color(i, j)
        else:
            self.toggle_lamp_for_cell(i, j)
            
    def toggle_cell_color(self, x, y):
        cell = self.akari.cells[(x, y)]
        cell.is_black = not cell.is_black

        if not cell.is_black:
            cell.number = None
            self.canvas.delete(f"{cell.coords()}-number")

        self.solution_state = None
        
        self.redraw_all()

    def toggle_lamp_for_cell(self, x, y):
        if not self.solution_state:
            self.solution_state = SolutionState(self.akari, auto_find_cells_that_must_have_lamps=False)

        cell = self.akari.cells[(x, y)]

        if cell.is_black:
            return
        
        if cell.coords() in self.solution_state.lamps.keys():
            self.solution_state.assign_lamp_value(*cell.coords(), not self.solution_state.lamps[cell.coords()])
            if not self.solution_state.is_valid():
                self.solution_state.assign_lamp_value(*cell.coords(), not self.solution_state.lamps[cell.coords()])
                self.message.config(text="Invalid move! Try again.")
            else:
                self.message.config(text="")
                if self.solution_state.is_solved():
                    self.message.config(text="Solution is correct!")

        self.redraw_all()

    def check_if_solution_is_correct(self):
        if self.solution_state:
            if self.solution_state.is_solved():
                self.message.config(text="Solution is correct!")
            else:
                self.message.config(text="Solution is incorrect. Try again.")
        else:
            self.message.config(text="No solution to check!")

    def toggle_gui_mode(self):
        if self.mode == GuiMode.CREATE:
            self.mode = GuiMode.SOLVE
            self.solve_mode_buttons()
        else:
            self.mode = GuiMode.CREATE
            self.creation_mode_buttons()
        self.toggle_gui_button.config(text=self.mode_button_text())
            
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
            
    def toggle_number(self):
        if self.highlighted_cell:
            if self.highlighted_cell.number is None:
                number = simpledialog.askinteger("Input", "Enter number to place in highlighted cell:", parent=self.master, minvalue=0, maxvalue=4)
                if number or number == 0:
                    self.akari.cells[self.highlighted_cell.coords()].number = number
            else:
                self.canvas.delete(f"{self.highlighted_cell.coords()}-number")
                self.akari.cells[self.highlighted_cell.coords()].number = None
        else:
            self.message.config(text="No cell highlighted.")
        self.redraw_all()
    
    def solve_push(self):
        if self.solution_state:
            self.remove_solution()
        solution, depth, total_prop_iters, total_check_iters, backtracks, decision_points = solve(self.akari)
        if solution:
            self.message.config(text=f'Solved.')
            # print(f'solved: in {depth} steps with {total_prop_iters} propogation iterations and {total_check_iters} forward check iterations and {backtracks} backtracks and {decision_points} decision points')
            print(f"""
    solved:
        inital_prop_iters: {solution.initial_propogation_iterations}
        depth: {depth}
        total_prop_iters: {total_prop_iters}
        total_check_iters: {total_check_iters}
        backtracks: {backtracks}
        decision_points: {decision_points}
            """)
            self.solution_state = solution
            self.redraw_all()
        else:
            self.message.config(text="No solution found.")
            
    def check_unique_push(self):
        if self.solution_state and self.solution_state.is_solved():
            unique, solution = AkariGenerator().check_unique_solution(self.akari, find_solution_different_than=self.solution_state)
            if solution:
                self.solution_state = solution
                self.redraw_all()
        else:
            unique, solution = AkariGenerator().check_unique_solution(self.akari)
        if solution:
            if unique:
                self.message.config(text="This puzzle has a unique solution!")
            else:
                self.message.config(text="This puzzle does not have a unique solution.")
        else:
            self.message.config(text="No solution found.")
        
    def new_akari(self):
        self.akari = Akari(self.akari.grid_size_x, self.akari.grid_size_y)
        self.remove_solution()
        self.redraw_all()
        self.message.config(text="Generating...")
        difficulty = simpledialog.askinteger("Input", "Enter difficulty (1-3):", parent=self.master, minvalue=1, maxvalue=3)
        if difficulty:
            akari = AkariGenerator().generate_akari_puzzle(self.akari.grid_size_x, self.akari.grid_size_y, difficulty)
            if akari:
                self.akari = akari
                self.message.config(text="Generated.")
                self.solution_state = SolutionState(self.akari, auto_find_cells_that_must_have_lamps=False)
                if self.mode == GuiMode.CREATE:
                    self.toggle_gui_mode()
            else:
                self.message.config(text="Failed to generate.")
            self.redraw_all()
        else:
            self.message.config(text="")
            
    def draw_solution(self):
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
        self.message.config(text="")
        self.redraw_all()
    

parser = ArgumentParser(
                prog='guiAkariCreator.py',
                description='Edits, saves, and solves Akari puzzles')
parser.add_argument('-f','--filename', required=False, help='The filename of the puzzle to load from') 
parser.add_argument('-s','--size', required=False, help='The cell size to use (default is 40, range is 20-60)') 
args = parser.parse_args()


def main():
    root = tk.Tk()
    root.title("Akari Editor")
    file = args.filename if args.filename else None
    cell_size = int(args.size) if args.size else 40
    app = AkariEditor(root, load_from_file=file, cell_size=cell_size)
    root.mainloop()


if __name__ == "__main__":
    main()
