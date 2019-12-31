from PyQt5 import QtSvg, QtWidgets, QtGui, QtCore, uic
from pathlib import Path
import numpy

from . import analyze

CELL_SIZE = 32

SVG_GRASS = QtSvg.QSvgRenderer('graphics/grass.svg')
SVG_CASTLE = QtSvg.QSvgRenderer('graphics/castle.svg')
SVG_WALL_LEFT = QtSvg.QSvgRenderer('graphics/wall_vertical.svg')
SVG_WALL_TOP = QtSvg.QSvgRenderer('graphics/wall_horizontal.svg')
DUDES = [QtSvg.QSvgRenderer(f'graphics/dude{i}.svg') for i in range(1, 6)]
LINES = [QtSvg.QSvgRenderer(f'graphics/lines/{i}.svg') for i in range(1, 16)]
DOWN = QtSvg.QSvgRenderer(f'graphics/arrows/down.svg')
LEFT = QtSvg.QSvgRenderer(f'graphics/arrows/left.svg')
RIGHT = QtSvg.QSvgRenderer(f'graphics/arrows/right.svg')
UP = QtSvg.QSvgRenderer(f'graphics/arrows/up.svg')


IS_TARGET = 1
IS_WALL_LEFT = 2
IS_WALL_UP = 4


def pixels_to_logical(x, y):
    return y // CELL_SIZE, x // CELL_SIZE


def logical_to_pixels(row, column):
    return column * CELL_SIZE, row * CELL_SIZE


class GridWidget(QtWidgets.QWidget):
    def __init__(self, array):
        super().__init__()
        self.set_array(array)
    
    def set_array(self, array):
        self.array = array
        size = logical_to_pixels(*array.shape)
        self.setMinimumSize(*size)
        self.setMaximumSize(*size)
        self.resize(*size)
        self.analyze()
        self.update()

    def analyze(self):
        self.analysis = analyze(self.array)
        locs = []
        for row in range(self.array.shape[0]):
            for col in range(self.array.shape[1]):
                if (self.array[row, col] >> 3) > 0:
                    locs.append((row, col))
        self.paths = self.analysis.paths(locs)
                

    def paintEvent(self, event):
        rect = event.rect()

        row_min, col_min = pixels_to_logical(rect.left(), rect.top())
        row_min = max(row_min, 0)
        col_min = max(col_min, 0)
        row_max, col_max = pixels_to_logical(rect.right(), rect.bottom())
        row_max = min(row_max + 1, self.array.shape[0])
        col_max = min(col_max + 1, self.array.shape[1])

        painter = QtGui.QPainter(self)

        for row in range(row_min, row_max):
            for col in range(col_min, col_max):
                x, y = logical_to_pixels(row, col)
                rect = QtCore.QRectF(x, y, CELL_SIZE, CELL_SIZE)
                white = QtGui.QColor(255, 255, 255)
                painter.fillRect(rect, QtGui.QBrush(white))

                SVG_GRASS.render(painter, rect)

                if self.paths[row, col] > 0:
                    LINES[self.paths[row, col] - 1].render(painter, rect)

                    direction = self.analysis.directions[row, col]
                    if direction == b'<':
                        LEFT.render(painter, rect)
                    elif direction == b'>':
                        RIGHT.render(painter, rect)
                    elif direction == b'^':
                        UP.render(painter, rect)
                    elif direction == b'v':
                        DOWN.render(painter, rect)

                value = self.array[row, col]
                if value & 1:
                    SVG_CASTLE.render(painter, rect)
                if value & 2:
                    rect.translate(-CELL_SIZE/2, 0)
                    SVG_WALL_LEFT.render(painter, rect)
                    rect.translate(CELL_SIZE/2, 0)
                if value & 4:
                    rect.translate(0, -CELL_SIZE/2)
                    SVG_WALL_TOP.render(painter, rect)
                    rect.translate(0, CELL_SIZE/2)
                
                value >>= 3
                if 1 <= value <= 5:
                    DUDES[value - 1].render(painter, rect)

    def mousePressEvent(self, event):
        row, column = pixels_to_logical(event.x(), event.y())

        if 0 <= row < self.array.shape[0] and 0 <= column < self.array.shape[1]:
            if self.selected == 0:
                self.array[row, column] ^= 1
            elif self.selected == 1:
                x = event.x() - column * CELL_SIZE
                y = event.y() - row * CELL_SIZE
                is_topleft = x + y < CELL_SIZE
                is_topright = x > y

                if is_topleft:
                    if is_topright:
                        if row > 0:
                            self.array[row, column] ^= 4
                    else:
                        if column > 0:
                            self.array[row, column] ^= 2
                else:
                    if is_topright:
                        if column + 1 < self.array.shape[1]:
                            column += 1
                            self.array[row, column] ^= 2
                    else:
                        if row + 1 < self.array.shape[0]:
                            row += 1
                            self.array[row, column] ^= 4

            elif 2 <= self.selected <= 6:
                oldDude = ((self.array[row, column] >> 3) & 7) + 1
                self.array[row, column] &= 7
                if oldDude != self.selected:
                    self.array[row, column] |= (self.selected - 1) << 3

            # self.update(*logical_to_pixels(row, column), CELL_SIZE, CELL_SIZE)
            self.analyze()
            self.update()

    def put_wall(self, x, y):
        x + y // CELL_SIZE

def new_dialog(window, grid):
    # Vytvoříme nový dialog.
    # V dokumentaci mají dialogy jako argument `this`;
    # jde o "nadřazené" okno.
    dialog = QtWidgets.QDialog(window)

    # Načteme layout z Qt Designeru.
    with open('edgemaze/newmaze.ui') as f:
        uic.loadUi(f, dialog)

    # Zobrazíme dialog.
    # Funkce exec zajistí modalitu (tzn. nejde ovládat zbytek aplikace,
    # dokud je dialog zobrazen) a vrátí se až potom, co uživatel dialog zavře.
    result = dialog.exec()

    # Výsledná hodnota odpovídá tlačítku/způsobu, kterým uživatel dialog zavřel.
    if result == QtWidgets.QDialog.Rejected:
        # Dialog uživatel zavřel nebo klikl na Cancel.
        return

    # Načtení hodnot ze SpinBoxů
    cols = dialog.findChild(QtWidgets.QSpinBox, 'widthSpinBox').value()
    rows = dialog.findChild(QtWidgets.QSpinBox, 'heightSpinBox').value()

    grid.set_array(numpy.zeros((rows, cols), dtype=numpy.int8))

    grid.update()

VALUE_ROLE = QtCore.Qt.UserRole

class MapCreatorGUI:
    def __init__(self):
        self.app = QtWidgets.QApplication([])

        self.window = QtWidgets.QMainWindow()

        with open('edgemaze/mainwindow.ui') as f:
            uic.loadUi(f, self.window)

        # mapa zatím nadefinovaná rovnou v kódu
        array = numpy.zeros((10, 10), dtype=numpy.int8)

        # získáme oblast s posuvníky z Qt Designeru
        scroll_area = self.window.findChild(QtWidgets.QScrollArea, 'scrollArea')

        # dáme do ní náš grid
        self.grid = GridWidget(array)
        scroll_area.setWidget(self.grid)

        # získáme paletu vytvořenou v Qt Designeru
        palette = self.window.findChild(QtWidgets.QListWidget, 'palette')
        self.init_palette(palette)

        action = self.window.findChild(QtWidgets.QAction, 'actionNew')
        action.triggered.connect(lambda: new_dialog(self.window, self.grid))

        action = self.window.findChild(QtWidgets.QAction, 'actionSave')
        action.triggered.connect(lambda: self.save_dialog())

        action = self.window.findChild(QtWidgets.QAction, 'actionLoad')
        action.triggered.connect(lambda: self.load_dialog())

        action = self.window.findChild(QtWidgets.QAction, 'actionAbout')
        action.triggered.connect(lambda: self.about_window())

    def init_palette(self, palette):
        add_item_to_palette(palette, 'Target', 'graphics/castle.svg', 0)
        add_item_to_palette(palette, 'Wall', 'graphics/wall_vertical.svg', 1)
        for index, dude in enumerate(DUDES):
            add_item_to_palette(palette, f'Dude {index + 1}', f'graphics/dude{index + 1}.svg', index + 2)

        def item_activated():
            for item in palette.selectedItems():
                self.grid.selected = item.data(VALUE_ROLE)

        palette.itemSelectionChanged.connect(item_activated)
        palette.setCurrentRow(1)
    
    def run(self):
        self.window.show()

        return self.app.exec()

    def load_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self.window, 'Load Map ...')
        if path:
            try:
                self.grid.set_array(numpy.loadtxt(path, dtype=numpy.int8))
            except Exception as ex:
                self.error_window("Failed to open specified file")
    
    def save_dialog(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self.window, 'Save Map ...')
        if path:
            try:
                numpy.savetxt(path, self.grid.array)
            except Exception as ex:
                self.error_window("Failed to save map into specified path")

    def about_window(self):
        QtWidgets.QMessageBox.about(self.window, 'About', '''\
Edgemaze map creator and solver

A tool to create mazes and automatically find paths through them.

Vojtěch Balík, Miro Hrončok, Marek Suchánek.

https://github.com/vojtechbalik/edgemaze-1

License: GNU GPL

All graphics taken from OpenGameArt.org\
''')

    def error_window(self, message):
        QtWidgets.QMessageBox.critical(self.window, 'Error!', message)

def add_item_to_palette(palette, label, icon_path, value):
    item = QtWidgets.QListWidgetItem(label)  # vytvoříme položku
    icon = QtGui.QIcon(icon_path)  # ikonu
    item.setIcon(icon)  # přiřadíme ikonu položce
    palette.addItem(item)  # přidáme položku do palety
    item.setData(VALUE_ROLE, value)

def gui():
    mapCreator = MapCreatorGUI()
    mapCreator.run()