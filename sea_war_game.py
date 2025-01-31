import pygame
import random
import sys
from pygame import mixer


pygame.init()
mixer.init()


NAVY_BLUE = (28, 51, 71)
MILITARY_GREEN = (75, 83, 32)
KHAKI = (189, 183, 107)
STEEL_GRAY = (119, 136, 153)
DESERT_TAN = (210, 180, 140)
BLOOD_RED = (138, 3, 3)
OCEAN_BLUE = (0, 119, 190)
WHITE = (255, 255, 255)

class Ship:
    def __init__(self, length):
        self.length = length
        self.positions = []
        self.is_vertical = False
        self.hits = set()

    def is_sunk(self):
        return len(self.hits) == len(self.positions)

class BattleshipGame:
    def __init__(self):
        self.size = 10
        self.cell_size = 60
        self.margin = 70
        self.board_size = self.size * self.cell_size
        self.width = self.board_size * 2 + self.margin * 3
        self.height = self.board_size + self.margin * 2
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Морской Бой")
        
        self.font = pygame.font.Font(None, 36)
        self.ship_sizes = {4: 1, 3: 2, 2: 3, 1: 4}
        self.reset_game()
        
        
        self.hit_sound = mixer.Sound('hit.wav')
        self.miss_sound = mixer.Sound('miss.wav')
        self.win_sound = mixer.Sound('win.wav')
    
        
    def reset_game(self):
        self.board1 = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.board2 = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.ships1 = []
        self.ships2 = []
        self.player1_name = ""
        self.player2_name = ""
        self.menu_state = "MAIN_MENU"
        self.game_mode = None
        self.current_player = 1
        self.winner = None
        self.manual_placement = False
        self.selected_ship_size = 4
        self.selected_ship_rotation = False
        self.ships_to_place = self.ship_sizes.copy()
        self.message = ""
        self.message_timer = 0

    def draw_menu(self):
        self.screen.fill(NAVY_BLUE)
        title = self.font.render("МОРСКОЙ БОЙ", True, WHITE)
        pvp_button = self.font.render("Игра против друга", True, WHITE)
        pve_button = self.font.render("Игра против компьютера", True, WHITE)
        
        self.screen.blit(title, (self.width//2 - title.get_width()//2, 100))
        self.screen.blit(pvp_button, (self.width//2 - pvp_button.get_width()//2, 300))
        self.screen.blit(pve_button, (self.width//2 - pve_button.get_width()//2, 400))

    def get_player_names(self):
        input_rect = pygame.Rect(self.width//2 - 100, 300, 200, 32)
        active = True
        text = ""
        asking_first_player = True

        while active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and text:
                        if asking_first_player:
                            self.player1_name = text
                            if self.game_mode == "PVE":
                                self.player2_name = "                                                                  Компьютер"
                                active = False
                            else:
                                asking_first_player = False
                                text = ""
                        else:
                            self.player2_name = text
                            active = False
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

            self.screen.fill(NAVY_BLUE)
            prompt = f"Введите имя {'первого' if asking_first_player else 'второго'} игрока:"
            prompt_surface = self.font.render(prompt, True, WHITE)
            self.screen.blit(prompt_surface, (self.width//2 - prompt_surface.get_width()//2, 250))

            txt_surface = self.font.render(text, True, WHITE)
            pygame.draw.rect(self.screen, WHITE, input_rect, 2)
            self.screen.blit(txt_surface, (input_rect.x + 5, input_rect.y + 5))
            pygame.display.flip()

    def handle_setup(self):
        if not self.player1_name:
            self.get_player_names()
            return

        if self.game_mode == "PVP" and not self.player2_name and self.current_player == 2:
            input_rect = pygame.Rect(self.width//2 - 100, 300, 200, 32)
            active = True
            text = ""
        
            while active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN and text:
                            self.player2_name = text
                            active = False
                        elif event.key == pygame.K_BACKSPACE:
                            text = text[:-1]
                        else:
                            text += event.unicode
            
                self.screen.fill(NAVY_BLUE)
                prompt = "Введите имя второго игрока:"
                prompt_surface = self.font.render(prompt, True, WHITE)
                self.screen.blit(prompt_surface, (self.width//2 - prompt_surface.get_width()//2, 250))
            
                txt_surface = self.font.render(text, True, WHITE)
                pygame.draw.rect(self.screen, WHITE, input_rect, 2)
                self.screen.blit(txt_surface, (input_rect.x + 5, input_rect.y + 5))
                pygame.display.flip()
            return

        if self.manual_placement:
            
            self.screen.fill(NAVY_BLUE)

           
            if self.current_player == 1:
                self.draw_board(self.margin, self.board1)
            else:
                self.draw_board(self.margin * 2 + self.board_size, self.board2)

            self.handle_manual_placement()

            
            if self.selected_ship_size:
                ship_info = f"Размещение корабля размером {self.selected_ship_size} для {self.player1_name if self.current_player == 1 else self.player2_name}"
                ship_info_surface = self.font.render(ship_info, True, WHITE)
                self.screen.blit(ship_info_surface, (10, 10))

                rotation_info = "Нажмите R для поворота корабля"
                rotation_surface = self.font.render(rotation_info, True, WHITE)
                self.screen.blit(rotation_surface, (10, self.height - 30))

    def draw_ship_preview(self, row, col, board):
        ship_cells = self.get_ship_cells(row, col, self.selected_ship_size, 
                                       self.selected_ship_rotation)
        can_place = self.can_place_ship(row, col, self.selected_ship_size, 
                                      self.selected_ship_rotation, board)
        color = MILITARY_GREEN if can_place else BLOOD_RED
        
        for cell_row, cell_col in ship_cells:
            if 0 <= cell_row < self.size and 0 <= cell_col < self.size:
                x = (self.margin if self.current_player == 1 else self.margin * 2 + self.board_size) + cell_col * self.cell_size
                y = self.margin + cell_row * self.cell_size
                pygame.draw.rect(self.screen, color, 
                               (x + 5, y + 5, self.cell_size - 10, self.cell_size - 10), 2)

    def get_ship_cells(self, row, col, size, is_vertical):
        return [(row + i, col) if is_vertical else (row, col + i) for i in range(size)]

    def can_place_ship(self, row, col, size, is_vertical, board):
        ship_cells = self.get_ship_cells(row, col, size, is_vertical)
        
        for cell_row, cell_col in ship_cells:
            if not (0 <= cell_row < self.size and 0 <= cell_col < self.size):
                return False
            
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    r, c = cell_row + dr, cell_col + dc
                    if (0 <= r < self.size and 0 <= c < self.size and 
                        board[r][c] != 0):
                        return False
        return True

    def handle_manual_placement(self):
        mouse_pos = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_r]:
            self.selected_ship_rotation = not self.selected_ship_rotation

        
        y_offset = 50
        for size, count in self.ships_to_place.items():
            ship_info = f"Корабли {size} палуб(ы): {count}"
            info_surface = self.font.render(ship_info, True, WHITE)
            self.screen.blit(info_surface, (10, y_offset))
            y_offset += 30

        cell = self.get_cell_coordinates(mouse_pos)
        if cell:
            row, col, board = cell
            current_board = self.board1 if self.current_player == 1 else self.board2

            if ((board == 0 and self.current_player == 1) or 
                (board == 1 and self.current_player == 2)):
                self.draw_ship_preview(row, col, current_board)

                if pygame.mouse.get_pressed()[0]:
                    if self.can_place_ship(row, col, self.selected_ship_size, 
                                         self.selected_ship_rotation, current_board):
                        self.place_ship(row, col, current_board)
                        self.selected_ship_size = self.get_next_ship_size()
                        if self.selected_ship_size is None:
                            if self.current_player == 1 and self.game_mode == "PVP":
                                self.current_player = 2
                                self.selected_ship_size = 4
                                self.ships_to_place = self.ship_sizes.copy()
                            else:
                                self.menu_state = "GAME"
        

    def place_ship(self, row, col, board):
        ship = Ship(self.selected_ship_size)
        ship.is_vertical = self.selected_ship_rotation
        
        for cell_row, cell_col in self.get_ship_cells(row, col, self.selected_ship_size, 
                                                     self.selected_ship_rotation):
            board[cell_row][cell_col] = 1
            ship.positions.append((cell_row, cell_col))
        
        if self.current_player == 1:
            self.ships1.append(ship)
        else:
            self.ships2.append(ship)

    def get_next_ship_size(self):
        if self.ships_to_place[self.selected_ship_size] > 0:
            self.ships_to_place[self.selected_ship_size] -= 1
        
        
            if self.ships_to_place[self.selected_ship_size] == 0:
                for size in [4, 3, 2, 1]:
                    if self.ships_to_place[size] > 0:
                        return size
                return None
            return self.selected_ship_size
    
    
        for size in [4, 3, 2, 1]:
            if self.ships_to_place[size] > 0:
                return size
        return None


    def auto_place_ships(self, board):
        ships = []
        for size, count in self.ship_sizes.items():
            for _ in range(count):
                while True:
                    ship = Ship(size)
                    ship.is_vertical = random.choice([True, False])
                    row = random.randint(0, self.size - (size if ship.is_vertical else 1))
                    col = random.randint(0, self.size - (1 if ship.is_vertical else size))
                    
                    if self.can_place_ship(row, col, size, ship.is_vertical, board):
                        for cell_row, cell_col in self.get_ship_cells(row, col, size, 
                                                                     ship.is_vertical):
                            board[cell_row][cell_col] = 1
                            ship.positions.append((cell_row, cell_col))
                        ships.append(ship)
                        break
        return ships

    def handle_shot(self, row, col):
        target_board = self.board2 if self.current_player == 1 else self.board1
        target_ships = self.ships2 if self.current_player == 1 else self.ships1

        if target_board[row][col] == 1:  
            target_board[row][col] = 2
            self.hit_sound.play()

            
            for ship in target_ships:
                if (row, col) in ship.positions:
                    ship.hits.add((row, col))
                    if ship.is_sunk():
                        self.message = "Корабль потоплен!"
                    else:
                        self.message = "Попадание!"
                    self.message_timer = 250
                    break
                    
            
            if all(ship.is_sunk() for ship in target_ships):
                self.winner = self.current_player
                self.win_sound.play()
            return True
        else:
            target_board[row][col] = 3  
            self.miss_sound.play()
            self.message = "Промах!"
            self.message_timer = 100
            self.current_player = 3 - self.current_player
            return False

    def computer_turn(self):
        pygame.time.wait(1000)  

        while True:
            row = random.randint(0, self.size - 1)
            col = random.randint(0, self.size - 1)

            if self.board1[row][col] not in [2, 3]:
                hit = self.handle_shot(row, col)
                if hit and not self.winner:
                    pygame.time.wait(500)  
                    continue  
                break  
                
        return hit


    def get_cell_coordinates(self, pos):
        x, y = pos
        board = 0 if x < self.width//2 else 1
        
        board_x = self.margin if board == 0 else self.margin * 2 + self.board_size
        
        if (board_x <= x <= board_x + self.board_size and 
            self.margin <= y <= self.margin + self.board_size):
            row = (y - self.margin) // self.cell_size
            col = (x - board_x) // self.cell_size
            return row, col, board
        return None

    def draw_board(self, x_offset, board, hide_ships=False):
        for i in range(self.size):
            for j in range(self.size):
                x = x_offset + j * self.cell_size
                y = self.margin + i * self.cell_size
                cell = pygame.Rect(x, y, self.cell_size, self.cell_size)
                
                pygame.draw.rect(self.screen, STEEL_GRAY, cell)
                pygame.draw.rect(self.screen, NAVY_BLUE, cell, 2)
                
                if board[i][j] == 1 and not hide_ships:
                    pygame.draw.rect(self.screen, MILITARY_GREEN, 
                                   (x + 5, y + 5, self.cell_size - 10, self.cell_size - 10))
                elif board[i][j] == 2:  
                    pygame.draw.circle(self.screen, BLOOD_RED, 
                                     (x + self.cell_size//2, y + self.cell_size//2), 20)
                elif board[i][j] == 3:  
                    pygame.draw.circle(self.screen, OCEAN_BLUE, 
                                     (x + self.cell_size//2, y + self.cell_size//2), 10)

        
        for i in range(self.size):
            text = self.font.render(chr(65 + i), True, WHITE)
            self.screen.blit(text, (x_offset - 30, self.margin + i * self.cell_size + 20))
            text = self.font.render(str(i + 1), True, WHITE)
            self.screen.blit(text, (x_offset + i * self.cell_size + 20, self.margin - 30))

    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            self.screen.fill(NAVY_BLUE)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if self.menu_state == "MAIN_MENU":
                        if 300 <= mouse_pos[1] <= 330:
                            self.game_mode = "PVP"
                            self.menu_state = "SETUP"
                        elif 400 <= mouse_pos[1] <= 430:
                            self.game_mode = "PVE"
                            self.menu_state = "SETUP"
                    
                    elif self.menu_state == "GAME" and not self.winner:
                        cell = self.get_cell_coordinates(mouse_pos)
                        if cell:
                            row, col, board = cell
                            if ((self.current_player == 1 and board == 1) or 
                                (self.current_player == 2 and board == 0 and self.game_mode == "PVP")):
                                target_board = self.board2 if board == 1 else self.board1
                                if target_board[row][col] not in [2, 3]:
                                    self.handle_shot(row, col)
                                    if self.game_mode == "PVE" and not self.winner and self.current_player == 2:
                                        pygame.time.wait(500)  # Пауза перед ходом компьютера
                                        self.computer_turn()

            if self.menu_state == "MAIN_MENU":
                self.draw_menu()
            
            elif self.menu_state == "SETUP":
                if not self.player1_name:
                    self.get_player_names()
                elif self.manual_placement:
                    self.draw_board(self.margin, self.board1)
                    self.draw_board(self.margin * 2 + self.board_size, self.board2)
                    self.handle_manual_placement()
                    
                    
                    if self.selected_ship_size:
                        ship_info = f"Размещение корабля размером {self.selected_ship_size} для {self.player1_name if self.current_player == 1 else self.player2_name}"
                        ship_info_surface = self.font.render(ship_info, True, WHITE)
                        self.screen.blit(ship_info_surface, (10, 10))
                        
                        rotation_info = "Нажмите R для поворота корабля"
                        rotation_surface = self.font.render(rotation_info, True, WHITE)
                        self.screen.blit(rotation_surface, (10, self.height - 30))
                else:
                    buttons = [
                        ("Авторасстановка", 300),
                        ("Ручная расстановка", 400),
                    ]
                    
                    for text, y in buttons:
                        button_text = self.font.render(text, True, WHITE)
                        button_rect = button_text.get_rect(center=(self.width//2, y))
                        self.screen.blit(button_text, button_rect)
                        
                        if pygame.mouse.get_pressed()[0]:
                            mouse_pos = pygame.mouse.get_pos()
                            if button_rect.collidepoint(mouse_pos):
                                if text == "Авторасстановка":
                                    if self.current_player == 1:
                                        self.ships1 = self.auto_place_ships(self.board1)
                                        if self.game_mode == "PVE":
                                            self.ships2 = self.auto_place_ships(self.board2)
                                            self.menu_state = "GAME"
                                        else:
                                            self.current_player = 2
                                    else:
                                        self.ships2 = self.auto_place_ships(self.board2)
                                        self.menu_state = "GAME"
                                else:
                                    self.manual_placement = True
                                    self.selected_ship_size = 4
                                    self.ships_to_place = self.ship_sizes.copy()
            
            elif self.menu_state == "GAME":
                self.draw_board(self.margin, self.board1)
                self.draw_board(self.margin * 2 + self.board_size, self.board2, 
                              hide_ships=self.game_mode == "PVP" or self.current_player == 1)
                
                
                player1_text = self.font.render(f"{self.player1_name}", True, WHITE)
                player2_text = self.font.render(f"{self.player2_name}", True, WHITE)
                self.screen.blit(player1_text, (self.margin, 10))
                self.screen.blit(player2_text, (self.margin * 2 + self.board_size, 10))
                
                current_player_name = self.player1_name if self.current_player == 1 else self.player2_name
                turn_text = self.font.render(f"   Ход: {current_player_name}  "    " ", True, WHITE)
                self.screen.blit(turn_text, (self.width//2 - turn_text.get_width()//2, 10))
                
                
                if self.message_timer > 0:
                    message_surface = self.font.render(self.message, True, WHITE)
                    self.screen.blit(message_surface, 
                                   (self.width//2 - message_surface.get_width()//2, 
                                    self.height - 40))
                    self.message_timer -= 1
                
                
                if self.winner:
                    winner_name = self.player1_name if self.winner == 1 else self.player2_name
                    winner_text = self.font.render(f"Победитель: {winner_name}!", True, WHITE)
                    self.screen.blit(winner_text, 
                                   (self.width//2 - winner_text.get_width()//2, 
                                    self.height//2))
            
            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    game = BattleshipGame()
    game.run()
