from maze import Maze



def run():
    newmaze = Maze()
    newmaze.load_from_file("maze00")
    solution = newmaze.solve_bfs()
    return solution
