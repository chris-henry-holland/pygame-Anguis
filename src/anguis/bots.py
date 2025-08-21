# library/src/anguis/bots.py

from __future__ import annotations

from typing import Union, Tuple, List, Set, Dict, Optional, Callable, Any, Generator, TYPE_CHECKING

from collections import deque
import random



from anguis.utils import UnionFind

class TailChaserBot:
    def __init__(self, shape: Tuple[int], head_idx: int, head_direct: Tuple[int], fruits: Set[int], snake_qu: Optional[deque]=None):
        self.shape = shape
        self.length = shape[0] * shape[1]
        #self.head_idx = head_idx
        self.head_direct = head_direct
        if snake_qu is None:
            self.snake_qu = deque([head_idx])
            self.in_snake = {head_idx}
        else:
            self.snake_qu = deque(snake_qu)
            self.in_snake = set(snake_qu)
        
        self.fruit_dist_arrs = {}
        for fruit in fruits:
            self.addFruit(fruit)
        
    
    def possibleMoveGenerator(self, head_idx: int, direct: Optional[Tuple[int]]=None)\
            -> Generator[Tuple[Tuple[int], int], None, None]:
        direct_opp = (direct[0], -direct[1]) if direct else None
        step = 1
        inds = divmod(head_idx, self.shape[1])
        tail_end_idx = self.snake_qu[0] if self.snake_qu else None
        for i in reversed(range(2)):
            for mv, idx2, edge_func in (((i, -1), head_idx - step, (lambda x: x > 0)), ((i, 1), head_idx + step, (lambda x: x < self.shape[i] - 1))):
                if mv != direct_opp and edge_func(inds[i]) and (idx2 == tail_end_idx or idx2 not in self.in_snake):
                    yield (mv, idx2)
            step *= self.shape[i]
        return
    
    def possibleNextPositionGenerator(self, idx: int, in_snake: Optional[Set[int]]=None)\
            -> Generator[int, None, None]:
        if in_snake is None:
            in_snake = self.in_snake
        step = 1
        inds = divmod(idx, self.shape[1])
        for i in reversed(range(2)):
            for idx2, edge_func in ((idx - step, (lambda x: x > 0)), (idx + step, (lambda x: x < self.shape[i] - 1))):
                if edge_func(inds[i]) and idx2 not in in_snake:
                    yield idx2
            step *= self.shape[i]
        return
                
    
    def createFruitDistanceArray(self, fruit_idx: int) -> List[Union[int, float]]:
        arr = [float("inf")] * self.length
        qu = deque([fruit_idx])
        arr[fruit_idx] = 0
        for d in range(1, self.length):
            if not qu: break
            for _ in range(len(qu)):
                idx = qu.popleft()
                for idx2 in self.possibleNextPositionGenerator(idx):
                    if d >= arr[idx2]: continue
                    arr[idx2] = d
                    qu.append(idx2)
        return arr
    
    def updateFruitDistanceArray(self, arr: List[Union[int, float]], snake_add: int, snake_rm: Optional[int]) -> None:
        # Assumes self.in_snake has been updated already
        qu1 = deque([(snake_add, arr[snake_add])])
        arr[snake_add] = float("inf")
        qu2 = deque()
        while qu1:
            #print("qu1")
            #print(f"qu1 = {qu1}")
            idx, val = qu1.popleft()
            for idx2 in self.possibleNextPositionGenerator(idx):
                if isinstance(arr[idx2], float): continue
                if arr[idx2] == val + 1:
                    qu1.append((idx2, arr[idx2]))
                    arr[idx2] = float("inf")
                elif arr[idx2] <= val:
                    qu2.append(idx2)
        if snake_rm is not None:
            idx2_set = set(self.possibleNextPositionGenerator(snake_rm))
            val = min(arr[idx2] for idx2 in idx2_set) if idx2_set else float("inf")
            if isinstance(val, int):
                arr[snake_rm] = val + 1
                qu2.append(snake_rm)
        while qu2:
            #print("qu2")
            #print(f"qu2 = {qu2}")
            idx = qu2.popleft()
            val = arr[idx] + 1
            for idx2 in self.possibleNextPositionGenerator(idx):
                if arr[idx2] <= val: continue
                arr[idx2] = val
                qu2.append(idx2)
        return arr
    
    def addFruit(self, add_fruit: int) -> None:
        self.fruit_dist_arrs[add_fruit] = self.createFruitDistanceArray(add_fruit)
        return
        
    def removeFruit(self, rm_fruit: int) -> None:
        self.fruit_dist_arrs.pop(rm_fruit)
        return
    
    def update(self, head_idx: int, head_direct: Tuple[int], rm_fruit: Optional[int], rm_tail_end: bool=True) -> None:
        
        self.head_idx = head_idx
        self.head_direct = head_direct
        if rm_tail_end:
            rm_tail_idx = self.snake_qu.popleft()
            self.in_snake.remove(rm_tail_idx)
        else: rm_tail_idx = None
        self.in_snake.add(head_idx)
        self.snake_qu.append(head_idx)
        if rm_fruit is not None:
            self.removeFruit(rm_fruit)
        for arr in self.fruit_dist_arrs.values():
            self.updateFruitDistanceArray(arr, head_idx, rm_tail_idx)
        return
    
    def moveGroups(self) -> Tuple[Dict[int, int]]:
        idx_prev = self.snake_qu[-2] if len(self.snake_qu) >= 2 else None
        head_idx = self.snake_qu[-1]
        tail_idx = self.snake_qu.popleft()
        self.in_snake.remove(tail_idx)
        idx_lst = [idx for idx in self.possibleNextPositionGenerator(head_idx, in_snake=self.in_snake) if idx != idx_prev]
        uf = UnionFind(len(idx_lst))
        seen = {}
        tail_connected = set()
        qu = deque()
        group_sizes = []#[1] * len(idx_lst)
        for i, idx in enumerate(idx_lst):
            if idx == tail_idx:
                #print("hello")
                group_sizes.append(0)
                tail_connected.add(i)
                #print(i, idx)
                continue
            group_sizes.append(1)
            qu.append(idx)
            seen[idx] = i
        while qu:
            idx = qu.popleft()
            i = seen[idx]
            for idx2 in self.possibleNextPositionGenerator(idx, in_snake=self.in_snake):
                if idx2 == tail_idx:
                    tail_connected.add(i)
                elif idx2 in seen.keys():
                    uf.union(i, seen[idx2])
                    #if len(uf.group_sizes) == 1: break
                else:
                    seen[idx2] = i
                    group_sizes[i] += 1
                    qu.append(idx2)
            else: continue
            break
        self.snake_qu.appendleft(tail_idx)
        self.in_snake.add(tail_idx)
        group_size_dict = {}
        for i, sz in enumerate(group_sizes):
            i2 = uf.find(i)
            idx2 = idx_lst[i2]
            group_size_dict[idx2] = group_size_dict.get(idx2, 0) + sz
        tail_connected = {idx_lst[uf.find(i)] for i in tail_connected}
        
        res = ({idx: idx_lst[uf.find(i)] for i, idx in enumerate(idx_lst)}, group_size_dict, tail_connected, seen)
        #print(res)
        return res
    
    def findMove(self, search_depth: int=1) -> Tuple[int]:
        #print(f"search depth = {search_depth}")
        orig_mv = self.head_direct
        best = [-1, False, (-1, 0, -float("inf")), None]
        #mv, idx = None, None
        fruits_remain = set(self.fruit_dist_arrs.keys())
        n_fruits = len(fruits_remain)
        #print()
        def recur(prev_mv: Tuple[int], depth: int=1) -> bool:
            head_idx = self.snake_qu[-1]
            groups = [{}, {}]
            # Finding the appropriate order
            for mv, idx in self.possibleMoveGenerator(head_idx, prev_mv):
                if idx in fruits_remain:
                    is_fruit = True
                    fruits_remain.remove(idx)
                    if len(self.snake_qu) + len(self.fruit_dist_arrs) == self.length:
                        best[0] = float("inf")
                        if depth == 1:
                            best[3] = (mv, idx)
                        #print("endgame")
                        #print(f"depth = {depth}")
                        #print(best)
                        return True
                else:
                    is_fruit = False
                    tail_idx = self.snake_qu.popleft()
                    self.in_snake.remove(tail_idx)
                self.snake_qu.append(idx)
                self.in_snake.add(idx)
                group_rep_dict, group_size_dict, tail_connected_group_reps, seen = self.moveGroups()
                candidate_reps = tail_connected_group_reps if tail_connected_group_reps else group_size_dict.keys()
                tail_connected = bool(tail_connected_group_reps)
                mx = (0, -float("inf"))
                for idx2, idx3 in group_rep_dict.items():
                    if idx3 not in candidate_reps: continue
                    sz = group_size_dict[idx3]
                    if sz < mx[0]: continue
                    dist = min(self.fruit_dist_arrs[k][idx2] for k in fruits_remain) if fruits_remain else float("inf")
                    mx = max(mx, (sz, -dist))
                fruits_collected = n_fruits - len(fruits_remain)
                tup = (mx[0] + fruits_collected, fruits_collected, mx[1] + (search_depth - depth))
                # Note- by exiting early here, may miss larger available areas that open
                # up due to movement of the tail opening up a new connection between
                # areas.
                if best[0] != search_depth or not best[1] or (tail_connected and tup > best[2]):
                    #print(f"depth = {depth}")
                    #print(f"tup = {tup}")
                    #print(f"snake lengths = {len(self.in_snake)}, {len(self.snake_qu)}")
                    #print(f"snake = {self.snake_qu}")
                    #print(group_rep_dict, group_size_dict)
                    #print(f"number seen = {len(seen)}")
                    #extra = self.in_snake.intersection(seen.keys())
                    #print(f"extra: {extra}")
                    groups[tail_connected].setdefault(tup, [])
                    groups[tail_connected][tup].append((mv, idx))
                self.in_snake.remove(self.snake_qu.pop())
                if is_fruit:
                    fruits_remain.add(idx)
                else:
                    self.snake_qu.appendleft(tail_idx)
                    self.in_snake.add(tail_idx)
            if not groups[0] and not groups[1]: return False
            if depth == search_depth:
                #print(groups)
                tail_connected = bool(groups[1])
                tup = max(groups[tail_connected].keys())
                if (tail_connected, search_depth, tup) <= (best[1], best[0], best[2]):
                    return False
                best[0] = depth
                best[1] = tail_connected
                best[2] = tup
                if depth == 1:
                    best[3] = random.choice(groups[tail_connected][tup])
                return True
            groups2 = dict(groups[0])
            for k, v in groups[1].items():
                groups2.setdefault(k, [])
                groups2[k].extend(v)
            res = False
            for tup in reversed(sorted(groups2.keys())):
                if best[0] >= search_depth and best[1] and tup <= best[2]: break
                lst = groups2[tup]
                random.shuffle(lst)
                for (mv, idx) in lst:
                    if idx in fruits_remain:
                        is_fruit = True
                        fruits_remain.remove(idx)
                    else:
                        is_fruit = False
                        tail_idx = self.snake_qu.popleft()
                        self.in_snake.remove(tail_idx)
                    self.snake_qu.append(idx)
                    self.in_snake.add(idx)
                    ans = recur(mv, depth=depth + 1)
                    self.in_snake.remove(self.snake_qu.pop())
                    if is_fruit:
                        fruits_remain.add(idx)
                    else:
                        self.snake_qu.appendleft(tail_idx)
                        self.in_snake.add(tail_idx)
                    
                    if ans:
                        res = True
                        if depth == 1:
                            best[3] = (mv, idx)
                        if not isinstance(best[0], int):
                            return True
                        if best[1] and tup <= best[2]: break
                else: continue
                break
            
            if not res and depth >= best[0]:
                tail_connected = bool(groups[1])
                tup = max(groups[tail_connected].keys())
                if (tail_connected, depth, tup) <= (best[1], best[0], best[2]):
                    return False
                best[0] = depth
                best[1] = tail_connected
                best[2] = tup
                best[3] = random.choice(groups[tail_connected][tup])
            return True
        res = recur(self.head_direct, depth=1)
        #print(res, best)
        #print()
        if res:
            return best[3]
        mv = self.head_direct
        step = 1 if mv[0] == 0 else self.shape[1]
        return (mv, self.snake_qu[-1] + step * mv[1])
    
    def addFruitFindMoveAndUpdate(self, add_fruit: Optional[int]=None, search_depth: int=2) -> Tuple[int]:
        if add_fruit is not None:
            self.addFruit(add_fruit)
        n_space = self.length - len(self.fruit_dist_arrs) - len(self.snake_qu)
        if n_space < 10:
            search_depth = 16#4 * self.length if n_space <= 2 else 16
            
            #print(f"search depth increased to {search_depth}")
        mv, head_idx = self.findMove(search_depth=search_depth)
        rm_fruit, rm_tail_end = (head_idx, False) if head_idx in self.fruit_dist_arrs.keys() else (None, True)
        #print(f"rm_fruit = {rm_fruit}")
        if 0 <= head_idx < self.length:
            self.update(head_idx, mv, rm_fruit, rm_tail_end=rm_tail_end)
        return mv
