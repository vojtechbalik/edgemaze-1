import numpy

from . import speedup

LDIR = lambda l: (l[0], l[1] - 1)
RDIR = lambda l: (l[0], l[1] + 1)
UDIR = lambda l: (l[0] - 1, l[1])
DDIR = lambda l: (l[0] + 1, l[1])

DIRS = {
    b'<': LDIR,
    b'>': RDIR,
    b'^': UDIR,
    b'v': DDIR,
}

UNREACHABLE = b' '
TARGET = b'X'


def arrows_to_path(arrows, loc):
    if arrows[loc] == UNREACHABLE:
        raise ValueError('Cannot construct path for unreachable cell')
    path = [loc]

    nloc = loc
    while arrows[nloc] != TARGET:
        nloc = DIRS[arrows[nloc]](nloc)
        path.append(nloc)

    return path

def arrows_to_paths(arrows, locs):
    paths_array = numpy.zeros(arrows.shape, dtype=numpy.int8)

    paths = [arrows_to_path(arrows, loc) for loc in locs if arrows[loc] != UNREACHABLE]
    
    for path in paths:
        last_idx = 0
        for i in range(0, len(path) - 1):
            loc = path[i]
            value = arrows[loc]
            if value == b'<':
                summand = 2
            elif value == b'>':
                summand = 8
            elif value == b'^':
                summand = 1
            elif value == b'v':
                summand = 4

            if paths_array[loc] > 0:
                paths_array[loc] |= summand
                break
            else:
                paths_array[loc] = summand
                last_idx = i
        
        for rev_i in range(i + 1, 0, -1):
            value = arrows[path[rev_i - 1]]
            if value == b'<':
                summand = 8
            elif value == b'>':
                summand = 2
            elif value == b'^':
                summand = 4
            elif value == b'v':
                summand = 1
        
            paths_array[path[rev_i]] |= summand

    return paths_array

def flood(maze):
    if maze.ndim != 2 or not numpy.issubdtype(maze.dtype, numpy.integer):
        raise TypeError('maze must be a 2-dimensional array of integers')
    return speedup.flood(maze.astype(numpy.int8, copy=False))


def is_reachable(directions):
    return UNREACHABLE not in directions


class AnalyzedMaze:
    def __init__(self, maze):
        self.maze = maze
        self.distances, self.directions = flood(maze)
        self.is_reachable = is_reachable(self.directions)

    def path(self, column, row):
        return arrows_to_path(self.directions, (column, row))

    def paths(self, locs):
        return arrows_to_paths(self.directions, locs)


def analyze(maze):
    return AnalyzedMaze(maze)
