import pygame
import sys
import os
from queue import PriorityQueue
from PIL import Image
import numpy as np
from skimage.filters import threshold_otsu
import tkinter as tk
from tkinter import filedialog
pygame.init()
pygame.font.init()
W = 800
WIN = pygame.display.set_mode((W, W))
pygame.display.set_caption("A* Path Finding Algorithm")
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128)
TURQUOISE = (64, 224, 208)
DARKGREY = (50, 50, 50)
FONT = pygame.font.SysFont("Arial", 18)
class Node:
    def __init__(self, row, col, gap, total):
        self.row = row
        self.col = col
        self.x = row * gap
        self.y = col * gap
        self.color = WHITE
        self.neighbors = []
        self.gap = gap
        self.total = total
    def pos(self):
        return self.row, self.col
    def is_barrier(self):
        return self.color == BLACK
    def is_start(self):
        return self.color == ORANGE
    def is_end(self):
        return self.color == TURQUOISE
    def reset(self):
        self.color = WHITE
    def make_start(self):
        self.color = ORANGE
    def make_closed(self):
        self.color = RED
    def make_open(self):
        self.color = GREEN
    def make_barrier(self):
        self.color = BLACK
    def make_end(self):
        self.color = TURQUOISE
    def make_path(self):
        self.color = PURPLE
    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x, self.y, self.gap, self.gap))
    def update_neighbors(self, grid):
        self.neighbors = []
        if self.row < self.total - 1 and not grid[self.row + 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row + 1][self.col])
        if self.row > 0 and not grid[self.row - 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row - 1][self.col])
        if self.col < self.total - 1 and not grid[self.row][self.col + 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col + 1])
        if self.col > 0 and not grid[self.row][self.col - 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col - 1])
    def __lt__(self, other):
        return False
def h(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
def reconstruct_path(came_from, current, draw_fn):
    while current in came_from:
        current = came_from[current]
        current.make_path()
        draw_fn()
def algo(draw_fn, grid, start, end):
    c = 0
    open_set = PriorityQueue()
    open_set.put((0, c, start))
    came_from = {}
    g = {n: float("inf") for row in grid for n in row}
    g[start] = 0
    f = {n: float("inf") for row in grid for n in row}
    f[start] = h(start.pos(), end.pos())
    open_hash = {start}
    while not open_set.empty():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        cur = open_set.get()[2]
        open_hash.remove(cur)
        if cur == end:
            reconstruct_path(came_from, end, draw_fn)
            end.make_end()
            return True
        for nb in cur.neighbors:
            tg = g[cur] + 1
            if tg < g[nb]:
                came_from[nb] = cur
                g[nb] = tg
                f[nb] = tg + h(nb.pos(), end.pos())
                if nb not in open_hash:
                    c += 1
                    open_set.put((f[nb], c, nb))
                    open_hash.add(nb)
                    nb.make_open()
        draw_fn()
        if cur != start:
            cur.make_closed()
    return False
def image_to_grid(path, rows):
    img = Image.open(path).convert("L")
    px = np.array(img)
    thresh = threshold_otsu(px)
    binary = px > thresh
    r_any = np.any(binary, axis=1)
    c_any = np.any(binary, axis=0)
    if r_any.any() and c_any.any():
        rmin, rmax = np.where(r_any)[0][[0, -1]]
        cmin, cmax = np.where(c_any)[0][[0, -1]]
        img = img.crop((cmin, rmin, cmax + 1, rmax + 1))
    img = img.resize((rows, rows), Image.LANCZOS)
    px = np.array(img)
    wall_map = px <= threshold_otsu(px)
    gap = W // rows
    grid = []
    for i in range(rows):
        grid.append([])
        for j in range(rows):
            n = Node(i, j, gap, rows)
            if wall_map[j][i]:
                n.make_barrier()
            grid[i].append(n)
    return grid, None, None
def make_grid(rows):
    gap = W // rows
    return [[Node(i, j, gap, rows) for j in range(rows)] for i in range(rows)]
def draw_grid_lines(win, rows):
    gap = W // rows
    for i in range(rows):
        pygame.draw.line(win, GREY, (0, i * gap), (W, i * gap))
        pygame.draw.line(win, GREY, (i * gap, 0), (i * gap, W))
def draw_scene(win, grid, rows, msg, msg_color):
    win.fill(WHITE)
    for row in grid:
        for n in row:
            n.draw(win)
    draw_grid_lines(win, rows)
    if msg:
        surf = FONT.render(msg, True, WHITE)
        bg = surf.get_rect(topleft=(8, 8))
        bg.inflate_ip(6, 4)
        pygame.draw.rect(win, DARKGREY, bg, border_radius=4)
        win.blit(surf, (11, 10))
    pygame.display.update()
def get_node(pos, rows):
    gap = W // rows
    y, x = pos
    return y // gap, x // gap
def open_file_dialog():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        title="Select maze image",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")]
    )
    root.destroy()
    return path
def main(win):
    rows = 50
    grid = make_grid(rows)
    start = None
    end = None
    run = True
    started = False
    while run:
        if start and end:
            msg, col = "SPACE=solve  R=reset  I=load image", GREY
        elif not start:
            msg, col = "Left click to place start", GREY
        elif not end:
            msg, col = "Left click to place end", GREY
        else:
            msg, col = "Left click=barrier  R=reset  I=load image", GREY
        draw_scene(win, grid, rows, msg, col)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if started:
                continue
            if pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()
                row, col = get_node(pos, rows)
                n = grid[row][col]
                if not start and n != end:
                    start = n
                    start.make_start()
                elif not end and n != start:
                    end = n
                    end.make_end()
                elif n != end and n != start:
                    n.make_barrier()
            elif pygame.mouse.get_pressed()[2]:
                pos = pygame.mouse.get_pos()
                row, col = get_node(pos, rows)
                n = grid[row][col]
                n.reset()
                if n == start:
                    start = None
                elif n == end:
                    end = None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    path = open_file_dialog()
                    if path:
                        grid, start, end = image_to_grid(path, rows)
                        pygame.display.set_caption(f"A* - {os.path.basename(path)}")
                if event.key == pygame.K_r:
                    grid = make_grid(rows)
                    start = None
                    end = None
                    started = False
                if event.key == pygame.K_SPACE and start and end:
                    for row in grid:
                        for n in row:
                            n.update_neighbors(grid)
                    started = True
                    if not algo(lambda: draw_scene(win, grid, rows, None, None), grid, start, end):
                        draw_scene(win, grid, rows, "No path found!", RED)
                        pygame.time.wait(1500)
                    started = False
main(WIN)