"""
Bot AI - A* pathfinding algoritması ile en kısa yolu bulur
"""
import heapq
from collections import deque

class MazeBot:
    def __init__(self, maze, start_pos, target_pos):
        """
        maze: 2D liste (harita)
        start_pos: (row, col) başlangıç pozisyonu
        target_pos: (row, col) hedef pozisyonu
        """
        self.maze = maze
        self.start = start_pos
        self.target = target_pos
        self.path = []
        self.current_step = 0
        
    def heuristic(self, pos):
        """Manhattan mesafesi - hedef tahmini"""
        return abs(pos[0] - self.target[0]) + abs(pos[1] - self.target[1])
    
    def get_neighbors(self, pos):
        """Komşu hücreleri döndür (yukarı, aşağı, sol, sağ)"""
        row, col = pos
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # yukarı, aşağı, sol, sağ
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            # Sınırları kontrol et
            if 0 <= new_row < len(self.maze) and 0 <= new_col < len(self.maze[0]):
                # Sadece yürünebilir alanlara git (0, 2=başlangıç, 3=hedef)
                cell_value = self.maze[new_row][new_col]
                if cell_value in [0, 2, 3]:
                    neighbors.append((new_row, new_col))
        
        return neighbors
    
    def find_path(self):
        """A* algoritması ile en kısa yolu bul"""
        # Priority queue: (f_score, counter, position, path)
        counter = 0
        start_node = (self.heuristic(self.start), counter, self.start, [self.start])
        open_set = [start_node]
        closed_set = set()
        
        g_scores = {self.start: 0}  # Başlangıçtan bu noktaya gerçek maliyet
        
        while open_set:
            # En düşük f_score'a sahip düğümü al
            current_f, _, current_pos, current_path = heapq.heappop(open_set)
            
            # Hedefe ulaştık mı?
            if current_pos == self.target:
                self.path = current_path
                print(f"[BOT] Yol bulundu! {len(self.path)} adım")
                return True
            
            # Bu düğümü zaten işledik mi?
            if current_pos in closed_set:
                continue
            
            closed_set.add(current_pos)
            current_g = g_scores[current_pos]
            
            # Komşuları incele
            for neighbor in self.get_neighbors(current_pos):
                if neighbor in closed_set:
                    continue
                
                # Yeni g_score hesapla
                tentative_g = current_g + 1
                
                # Bu komşuya daha iyi bir yol bulduk mu?
                if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor)
                    
                    counter += 1
                    new_path = current_path + [neighbor]
                    heapq.heappush(open_set, (f_score, counter, neighbor, new_path))
        
        print("[BOT] Yol bulunamadı!")
        return False
    
    def get_next_move(self):
        """Bir sonraki adımı döndür"""
        if self.current_step < len(self.path):
            next_pos = self.path[self.current_step]
            self.current_step += 1
            return next_pos
        return None
    
    def reset(self):
        """Botu sıfırla"""
        self.current_step = 0
    
    def get_path(self):
        """Tüm yolu döndür"""
        return self.path
    
    def is_finished(self):
        """Bot hedefe ulaştı mı?"""
        return self.current_step >= len(self.path)
