import tkinter as tk
from tkinter import ttk
import sys

class ColorSudoku:
    def __init__(self, root, initial_clues=None):
        self.root = root
        root.title("Color Sudoku")

        self.scale_factor = 3
        self.cell_size = 50
        self.scaled_cell_size = self.cell_size * self.scale_factor
        self.scaled_candidate_cell_size = self.scaled_cell_size / 3
        self.key_row_height = self.scaled_cell_size  # Height for the key row

        self.mode = tk.StringVar(value='clues')
        self.board_clues = [[0] * 9 for _ in range(9)]
        self.board_guesses = [[0] * 9 for _ in range(9)]
        self.board_candidates = [[[False] * 9 for _ in range(9)] for _ in range(9)] # 9x9x9, [row][col][candidate_index] (0-8 for 1-9)
        self.current_cell = [0, 0] # [row, col]
        self.invalid_cells = set()
        self.display_numbers = tk.BooleanVar(value=True) # Checkbox state, default True

        self.colors = ["red", "orange", "yellow", "yellow green", "spring green", "cyan", "dodger blue", "purple1", "violet"]

        self.clues_radio = ttk.Radiobutton(root, text="Clues", variable=self.mode, value='clues', command=self.set_mode_clues)
        self.clues_radio.grid(row=0, column=0, padx=5, pady=5)
        self.candidate_radio = ttk.Radiobutton(root, text="Candidate", variable=self.mode, value='candidate', command=self.set_mode_candidate)
        self.candidate_radio.grid(row=0, column=1, padx=5, pady=5)
        self.guess_radio = ttk.Radiobutton(root, text="Guess", variable=self.mode, value='guess', command=self.set_mode_guess)
        self.guess_radio.grid(row=0, column=2, padx=5, pady=5)

        self.auto_candidate_button = ttk.Button(root, text="Auto-fill Candidates", command=self.auto_fill_candidates)
        self.auto_candidate_button.grid(row=0, column=3, padx=5, pady=5)
        self.remove_candidate_button = ttk.Button(root, text="Auto-remove Candidates", command=self.auto_remove_candidates)
        self.remove_candidate_button.grid(row=0, column=4, padx=5, pady=5)
        self.export_button = ttk.Button(root, text="Export Clues", command=self.export_clues)
        self.export_button.grid(row=0, column=5, padx=5, pady=5) # move export button

        self.display_numbers_check = tk.Checkbutton(root, text="Show Numbers", variable=self.display_numbers, command=self.draw_board)
        self.display_numbers_check.grid(row=0, column=6, padx=5, pady=5) # New checkbox

        self.canvas = tk.Canvas(root, width=450 * self.scale_factor, height=(450 + 50) * self.scale_factor, bg="white") # Increased height for key row
        self.canvas.grid(row=1, column=0, columnspan=7, padx=10, pady=10) # span 7 columns now
        self.canvas.focus_set() # Ensure canvas has focus for key events

        if initial_clues:
            self.load_clues(initial_clues)

        self.draw_board() # Draw board content (numbers, colors) first
        self.draw_grid() # Draw grid lines on top
        self.draw_cursor() # Initial cursor draw
        self.canvas.bind("<Button-1>", self.on_cell_click)
        root.bind("<Key>", self.on_key_press)
        root.bind("g", lambda event: self.set_mode_guess())
        root.bind("c", lambda event: self.set_mode_candidate())
        root.bind("r", lambda event: self.auto_remove_candidates()) # 'r' key binding for remove candidates
        root.bind("n", self.toggle_numbers_display) # 'n' key binding for toggle numbers
        root.bind("<Up>", lambda event: self.move_cursor('up'))
        root.bind("<Down>", lambda event: self.move_cursor('down'))
        root.bind("<Left>", lambda event: self.move_cursor('left'))
        root.bind("<Right>", lambda event: self.move_cursor('right'))


    def set_mode_clues(self):
        self.mode.set('clues')
        self.draw_board() # Redraw board when mode changes
    def set_mode_candidate(self):
        self.mode.set('candidate')
        self.draw_board() # Redraw board when mode changes
    def set_mode_guess(self):
        self.mode.set('guess')
        self.draw_board() # Redraw board when mode changes

    def toggle_mode(self, event=None): # 't' key mode toggle function
        current_mode = self.mode.get()
        if current_mode == 'candidate':
            self.mode.set('guess')
        elif current_mode == 'guess':
            self.mode.set('candidate')
        elif current_mode == 'clues': # If in clues mode, switch to guess as requested
            self.mode.set('guess')
        else: # if somehow in another state, toggle to candidate as default
            self.mode.set('candidate')
        self.draw_board()

    def toggle_numbers_display(self, event=None): # 'n' key toggle numbers display
        current_value = self.display_numbers.get()
        self.display_numbers.set(not current_value) # Toggle the boolean value
        self.draw_board() # Redraw to reflect change

    def draw_grid(self):
        self.canvas.delete("grid_lines") # To redraw if needed
        for i in range(10):
            line_thickness = (2 if i % 3 != 0 else 6) * self.scale_factor / 2 # Scaled line thickness, doubled
            x = i * self.scaled_cell_size
            # Vertical lines for main grid
            self.canvas.create_line(x, 0, x, 450 * self.scale_factor, width=line_thickness, fill="black", tags="grid_lines")
        for i in range(10): # Horizontal lines for main grid and key row
            line_thickness = (2 if i % 3 != 0 else 6) * self.scale_factor / 2 # Scaled line thickness, doubled
            y = i * self.scaled_cell_size
            self.canvas.create_line(0, y, 450 * self.scale_factor, y, width=line_thickness, fill="black", tags="grid_lines")
        # Horizontal line below the main grid, separating it from the key row
        self.canvas.create_line(0, 450 * self.scale_factor, 450 * self.scale_factor, 450 * self.scale_factor, width= 6 * self.scale_factor / 2, fill="black", tags="grid_lines")


    def draw_cursor(self):
        self.canvas.delete("cursor")
        row, col = self.current_cell
        x1 = col * self.scaled_cell_size
        y1 = row * self.scaled_cell_size
        x2 = x1 + self.scaled_cell_size
        y2 = y1 + self.scaled_cell_size
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="magenta", width=4 * self.scale_factor / 2, tags="cursor") # Scaled cursor width, doubled


    def draw_board(self):
        self.canvas.delete("numbers")
        self.canvas.delete("invalid_outline") # Clear previous invalid outlines

        for row in range(9):
            for col in range(9):
                x1 = col * self.scaled_cell_size
                y1 = row * self.scaled_cell_size
                x2 = x1 + self.scaled_cell_size
                y2 = y1 + self.scaled_cell_size

                if (row, col) in self.invalid_cells:
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2 * self.scale_factor / 2, tags="invalid_outline") # Scaled invalid outline width

                clue_val = self.board_clues[row][col]
                guess_val = self.board_guesses[row][col]

                if clue_val != 0:
                    color_index = clue_val - 1
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.colors[color_index], tags="numbers", outline="") # No outline for filled cell
                    if self.display_numbers.get(): # Conditionally draw numbers
                        self.canvas.create_text(x1 + self.scaled_cell_size / 2, y1 + self.scaled_cell_size / 2, text=str(clue_val), font=("Arial", int(24 * self.scale_factor / 2)), fill="black", tags="numbers") # Scaled font size
                elif guess_val != 0:
                    color_index = guess_val - 1
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.colors[color_index], tags="numbers", outline="") # No outline for filled cell
                    if self.display_numbers.get(): # Conditionally draw numbers
                        self.canvas.create_text(x1 + self.scaled_cell_size / 2, y1 + self.scaled_cell_size / 2, text=str(guess_val), font=("Arial", int(24 * self.scale_factor / 2)), fill="black", tags="numbers") # Scaled font size
                else: # Always draw candidates if they exist, regardless of mode
                    for cand_row in range(3):
                        for cand_col in range(3):
                            candidate_index = cand_row * 3 + cand_col
                            if self.board_candidates[row][col][candidate_index]:
                                cand_x1 = x1 + cand_col * self.scaled_candidate_cell_size
                                cand_y1 = y1 + cand_row * self.scaled_candidate_cell_size
                                cand_x2 = cand_x1 + self.scaled_candidate_cell_size
                                cand_y2 = cand_y1 + self.scaled_candidate_cell_size
                                color_index = candidate_index
                                self.canvas.create_rectangle(cand_x1, cand_y1, cand_x2, cand_y2, fill=self.colors[color_index], tags="numbers", outline="") # No outline for candidate cell
                                if self.display_numbers.get(): # Conditionally draw numbers
                                    self.canvas.create_text(cand_x1 + self.scaled_candidate_cell_size / 2, cand_y1 + self.scaled_candidate_cell_size / 2, text=str(candidate_index + 1), font=("Arial", int(8 * self.scale_factor / 2)), fill="black", tags="numbers") # Scaled font size
        self.draw_key_row() # Draw the key row at the bottom
        self.draw_grid() # Draw grid on top


    def draw_key_row(self):
        start_y = 450 * self.scale_factor # Y position for the key row
        for i in range(9):
            x1 = i * self.scaled_cell_size
            y1 = start_y
            x2 = x1 + self.scaled_cell_size
            y2 = y1 + self.key_row_height
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.colors[i], tags="numbers", outline="") # Color cell
            self.canvas.create_text(x1 + self.scaled_cell_size / 2, y1 + self.key_row_height / 2, text=str(i + 1), font=("Arial", int(24 * self.scale_factor / 2)), fill="black", tags="numbers") # Number


    def on_cell_click(self, event):
        col = event.x // self.scaled_cell_size
        row = event.y // self.scaled_cell_size
        if 0 <= row < 9 and 0 <= col < 9: # Only process clicks on the 9x9 grid
            self.current_cell = [row, col]
            self.draw_cursor()

    def on_key_press(self, event):
        mode = self.mode.get()
        key = event.char
        row, col = self.current_cell

        if mode == 'clues':
            if key in '123456789':
                value = int(key)
                self.board_clues[row][col] = value
                self.board_guesses[row][col] = 0 # clear guess when setting clue
                self.board_candidates[row][col] = [False] * 9 # clear candidates when setting clue
                self.next_cell()
            elif key == '0':
                self.board_clues[row][col] = 0
                self.next_cell()
        elif mode == 'candidate':
            if key in '123456789':
                candidate_index = int(key) - 1
                self.board_candidates[row][col][candidate_index] = not self.board_candidates[row][col][candidate_index]
        elif mode == 'guess':
            if key in '123456789':
                value = int(key)
                self.board_guesses[row][col] = value
                self.board_clues[row][col] = 0 # clear clue if setting guess
                self.board_candidates[row][col] = [False] * 9 # clear candidates when setting guess
            elif key == '0':
                self.board_guesses[row][col] = 0

        self.validate_board()
        self.draw_board()
        self.draw_cursor() # Redraw cursor after board update


    def next_cell(self):
        row, col = self.current_cell
        col += 1
        if col > 8:
            col = 0
            row += 1
            if row > 8:
                row = 0
        self.current_cell = [row, col]
        self.draw_cursor() # Update cursor position visually immediately


    def move_cursor(self, direction):
        row, col = self.current_cell
        if direction == 'up':
            row = max(0, row - 1)
        elif direction == 'down':
            row = min(8, row + 1)
        elif direction == 'left':
            col = max(0, col - 1)
        elif direction == 'right':
            col = min(8, col + 1)
        self.current_cell = [row, col]
        self.draw_cursor() # Update cursor position visually immediately


    def validate_board(self):
        self.invalid_cells = set()
        board = [[0] * 9 for _ in range(9)]
        for r in range(9):
            for c in range(9):
                if self.board_clues[r][c] != 0:
                    board[r][c] = self.board_clues[r][c]
                elif self.board_guesses[r][c] != 0:
                    board[r][c] = self.board_guesses[r][c]

        for r in range(9):
            if not self._is_valid_row(board, r): # Use _is_valid_row for validation
                for c in range(9):
                    if board[r][c] != 0:
                        self.invalid_cells.add((r,c))
        for c in range(9):
            if not self._is_valid_col(board, c): # Use _is_valid_col for validation
                for r in range(9):
                    if board[r][c] != 0:
                        self.invalid_cells.add((r,c))
        for block_r in range(3):
            for block_c in range(3):
                if not self._is_valid_block(board, block_r, block_c): # Use _is_valid_block for validation
                    for r_offset in range(3):
                        for c_offset in range(3):
                            r = block_r * 3 + r_offset
                            c = block_c * 3 + c_offset
                            if board[r][c] != 0:
                                self.invalid_cells.add((r,c))


    def _is_valid_row(self, board, row): # Internal row validation for board check
        nums = [n for n in board[row] if n != 0]
        return len(nums) == len(set(nums))

    def _is_valid_col(self, board, col): # Internal col validation for board check
        nums = [board[r][col] for r in range(9) if board[r][col] != 0]
        return len(nums) == len(set(nums))

    def _is_valid_block(self, board, block_r, block_c): # Internal block validation for board check
        nums = []
        for r_offset in range(3):
            for c_offset in range(3):
                num = board[block_r * 3 + r_offset][block_c * 3 + c_offset]
                if num != 0:
                    nums.append(num)
        return len(nums) == len(set(nums))


    def is_valid_row(self, board, row, num): # Check if num is valid in row (for candidate/auto-fill)
        for x in range(9):
            if board[row][x] == num:
                return False
        return True

    def is_valid_col(self, board, col, num): # Check if num is valid in col (for candidate/auto-fill)
        for x in range(9):
            if board[x][col] == num:
                return False
        return True

    def is_valid_block(self, board, block_r, block_c, num): # Check if num is valid in block (for candidate/auto-fill)
        for r_offset in range(3):
            for c_offset in range(3):
                if board[block_r * 3 + r_offset][block_c * 3 + c_offset] == num:
                    return False
        return True

    def is_valid_candidate(self, board, row, col, candidate_value): # Check if candidate is valid for cell
        block_r = row // 3
        block_c = col // 3
        return (self.is_valid_row(board, row, candidate_value) and
                self.is_valid_col(board, col, candidate_value) and
                self.is_valid_block(board, block_r, block_c, candidate_value))


    def auto_fill_candidates(self):
        for r in range(9): # Clear all existing candidates first
            for c in range(9):
                self.board_candidates[r][c] = [False] * 9

        current_board = [[0] * 9 for _ in range(9)] # Create working board
        for r in range(9): # Initialize working board with clues and guesses
            for c in range(9):
                if self.board_clues[r][c] != 0:
                    current_board[r][c] = self.board_clues[r][c]
                elif self.board_guesses[r][c] != 0: # Include guesses in current board
                    current_board[r][c] = self.board_guesses[r][c]

        for row in range(9):
            for col in range(9):
                if current_board[row][col] == 0: # Only consider empty cells
                    for candidate_value in range(1, 10):
                        if self.is_valid_candidate(current_board, row, col, candidate_value):
                            self.board_candidates[row][col][candidate_value-1] = True # Set candidate if valid
        self.draw_board() # Redraw board to show candidates

    def auto_remove_candidates(self):
        current_board = [[0] * 9 for _ in range(9)] # Create working board
        for r in range(9): # Initialize working board with clues and guesses
            for c in range(9):
                if self.board_clues[r][c] != 0:
                    current_board[r][c] = self.board_clues[r][c]
                elif self.board_guesses[r][c] != 0: # Include guesses in current board
                    current_board[r][c] = self.board_guesses[r][c]

        for row in range(9):
            for col in range(9):
                if current_board[row][col] == 0: # Only consider empty cells
                    for candidate_value in range(1, 10):
                        if not self.is_valid_candidate(current_board, row, col, candidate_value): # Check if *invalid*
                            self.board_candidates[row][col][candidate_value-1] = False # Remove candidate if invalid
        self.draw_board() # Redraw board to show candidates


    def load_clues(self, clues_str):
        if len(clues_str) != 81:
            print("Error: Clue string must be 81 digits long.")
            return
        for i in range(81):
            row = i // 9
            col = i % 9
            digit = int(clues_str[i])
            if 0 <= digit <= 9:
                self.board_clues[row][col] = digit
            else:
                print(f"Error: Invalid digit '{digit}' in clue string.")
                return
        self.draw_board()

    def export_clues(self):
        clues_str = ""
        for row in range(9):
            for col in range(9):
                clues_str += str(self.board_clues[row][col])
        print(clues_str)


if __name__ == "__main__":
    initial_clues = None
    if len(sys.argv) > 1:
        initial_clues = sys.argv[1]

    root = tk.Tk()
    game = ColorSudoku(root, initial_clues)
    root.mainloop()
