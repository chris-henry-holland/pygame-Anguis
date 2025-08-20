# library/src/anguis/utils.py

import math
import random

from sortedcontainers import SortedSet

from collections.abc import Iterable
from typing import Dict, List, Set, Tuple, Optional, Union, Hashable,\
        Generator, Any, Callable

class UnionFind:
    def __init__(self, n: int):
        self.n = n
        self.root = list(range(n))
        self.rank = [1] * n
        #self.group_sizes = {idx: 1 for idx in range(n)}
    
    def find(self, v: int) -> int:
        r = self.root[v]
        if r == v: return v
        res = self.find(r)
        self.root[v] = res
        return res
    
    def union(self, v1: int, v2: int) -> None:
        r1, r2 = list(map(self.find, (v1, v2)))
        if r1 == r2: return
        d = self.rank[r1] - self.rank[r2]
        if d < 0: r1, r2 = r2, r1
        elif not d: self.rank[r1] += 1
        self.root[r2] = r1
        #self.group_sizes[r1] += self.group_sizes.pop(r2)
        return

### Random k-tuples from first n natural numbers functions ###
### and generators                                         ###

def countFunctionNondecreasing(n: int, k: int) -> int:
    return math.comb(n + k - 1, k)
    
def countFunctionIncreasing(n: int, k: int) -> int:
    return math.comb(n, k)

def getIthNondecreasingKTuple(i: int, n: int, k: int,\
        allow_repeats: bool) -> Tuple[int]:
    
    count_func = countFunctionNondecreasing if allow_repeats else\
            countFunctionIncreasing
    
    if i < 0 or i >= count_func(n, k):
        raise ValueError("In the function "\
                "getIthNondecreasingKTuple(), the given value "\
                "of i was outside the valid range for the "\
                "given n and k.")
    
    res = []
    def recur(i: int, n: int, k: int, prev: int) -> None:
        if not k: return
        tot = count_func(n, k)
        target = tot - i
        lft, rgt = 0, n - 1
        while lft < rgt:
            mid = lft - ((lft - rgt) >> 1)
            #if tot - countFunction(n - mid, k) <= i:
            if count_func(n - mid, k) >= target:
                lft = mid
            else: rgt = mid - 1
        num = prev + lft
        res.append(num)
        lft2 = lft + (not allow_repeats)
        recur(count_func(n - lft, k) - target, n - lft2, k - 1,\
                num + (not allow_repeats))
        return
    
    recur(i, n, k, 0)
    return tuple(res)

def getIthSet(i: int, n: int, k: int) -> Set[int]:
    if k > n:
        raise ValueError("In the function getIthSet(), k must "\
                "be no larger than n")
    return set(getIthNondecreasingKTuple(i, n, k, allow_repeats=False))
    

def getIthMultiset(i: int, n: int, k: int) -> Dict[int, int]:
    res = {}
    for num in getIthNondecreasingKTuple(i, n, k, allow_repeats=True):
        res[num] = res.get(num, 0) + 1
    return res

def numberedNondecreasingKTupleGenerator(inds: Iterable, n: int,\
        k: int, allow_repeats: bool, inds_sorted: bool=False)\
        -> Generator[Tuple[int], None, None]:
    if not inds_sorted:
        inds = sorted(inds)
    m = len(inds)
    
    count_func = countFunctionNondecreasing if allow_repeats else\
            countFunctionIncreasing
    
    inds_iter = iter(inds)
    
    ind_pair = [-1, next(inds_iter, float("inf"))]
    if not isinstance(ind_pair[1], int): return
    curr = []
    def recur(delta: int, n: int, k: int, prev: int)\
            -> Generator[Tuple[int], None, None]:
        if not k:
            yield_next = True
            res = tuple(curr)
            while yield_next:
                yield res
                ind_pair[0], ind_pair[1] =\
                        ind_pair[1], next(inds_iter, float("inf"))
                yield_next = (ind_pair[0] == ind_pair[1])
            return
        tot = count_func(n, k)
        tot2 = tot + delta
        lft = 0
        curr.append(0)
        while ind_pair[1] < tot2:
            target = tot2 - ind_pair[1]
            rgt = n - 1
            while lft < rgt:
                mid = lft - ((lft - rgt) >> 1)
                if count_func(n - mid, k) >= target:
                    lft = mid
                else: rgt = mid - 1
            num = prev + lft
            curr[-1] = num
            lft2 = lft + (not allow_repeats)
            yield from recur(delta + tot - count_func(n - lft, k),\
                    n - lft2, k - 1, num + (not allow_repeats))
            lft += 1
        curr.pop()
        return
    
    yield from recur(0, n, k, 0)
    return

def countFunctionAll(n: int, k: int) -> int:
    return n ** k
    
def countFunctionDistinct(n: int, k: int) -> int:
    return math.perm(n, k)

def findKthMissing(lst: SortedSet, k: int) -> int:
    # k starts at 0
    # Assumes lst contains only non-negative integers
    if not lst or k >= lst[-1]: return k + len(lst)
    
    def countLT(num: int) -> int:
        return num - lst.bisect_left(num)
    
    lft, rgt = k, k + len(lst)
    while lft < rgt:
        mid = lft - ((lft - rgt) >> 1)
        if countLT(mid) <= k: lft = mid
        else: rgt = mid - 1
    return lft

def getIthKTuple(i: int, n: int, k: int,\
        allow_repeats: bool) -> Tuple[int]:
    
    count_func = countFunctionAll if allow_repeats else\
            countFunctionDistinct
    
    if i < 0 or i >= count_func(n, k):
        raise ValueError("In the function "\
                "getIthKTuple(), the given value  of i was outside "\
                "the valid range for the given n and k.")
    
    count_func = countFunctionAll if allow_repeats else\
            countFunctionDistinct
    
    if allow_repeats:
        res = []
        for j in range(k):
            ans, i = divmod(i, count_func(n, k - j - 1))
            res.append(ans)
        return tuple(res)
    seen = SortedSet()
    res = []
    for j in range(k):
        ans, i = divmod(i, count_func(n - j - 1, k - j - 1))
        ans = findKthMissing(seen, ans)
        res.append(ans)
        seen.add(ans)
    return tuple(res)

def numberedKTupleGenerator(inds: Iterable, n: int,\
        k: int, allow_repeats: bool, inds_sorted: bool=False)\
        -> Generator[Tuple[int], None, None]:
    if not inds_sorted:
        inds = sorted(inds)
    m = len(inds)
    
    count_func = countFunctionAll if allow_repeats else\
            countFunctionDistinct
    
    def numProcessorAll(num: int) -> int:
        return num
    
    def numProcessorDistinct(num: int) -> int:
        num = findKthMissing(seen, num)
        seen.add(num)
        return num
    
    def seenProcessorAll(num: int) -> None:
        return
    
    def seenProcessorDistinct(num: int) -> None:
        seen.remove(num)
        return
    
    if allow_repeats:
        num_processor = numProcessorAll
        seen_processor = seenProcessorAll
    else:
        num_processor = numProcessorDistinct
        seen_processor = seenProcessorDistinct
        seen = SortedSet()
    
    inds_iter = iter(inds)
    
    ind_pair = [-1, next(inds_iter, float("inf"))]
    if not isinstance(ind_pair[1], int): return
    curr = []
    def recur(delta: int, n: int, k: int)\
            -> Generator[Tuple[int], None, None]:
        if not k:
            yield_next = True
            res = tuple(curr)
            while yield_next:
                yield res
                ind_pair[0], ind_pair[1] =\
                        ind_pair[1], next(inds_iter, float("inf"))
                yield_next = (ind_pair[0] == ind_pair[1])
            return
        n2 = n - (not allow_repeats)
        tot = count_func(n, k)
        tot2 = tot + delta
        lft = 0
        curr.append(0)
        div = count_func(n2, k - 1)
        while ind_pair[1] < tot2:
            
            q = (ind_pair[1] - delta) // div
            curr[-1] = num_processor(q)
            yield from recur(delta + q * div, n2, k - 1)
            seen_processor(curr[-1]) 
        curr.pop()
        return
    
    yield from recur(0, n, k)
    return

def randomSampleWithoutReplacement(n: int, k: int) -> List[int]:
    seen = SortedSet()
    res = []
    for i in range(k):
        num = findKthMissing(seen, random.randrange(0, n - i))
        res.append(num)
        seen.add(num)
    return res

def randomKTupleGenerator(n: int, k: int,\
        mx_n_samples: int, allow_index_repeats: bool,\
        allow_tuple_repeats: bool, nondecreasing: bool)\
        -> Generator[Tuple[int], None, None]:
    
    if nondecreasing:
        count_func = countFunctionNondecreasing if allow_index_repeats\
                else countFunctionIncreasing
        gen_func = numberedNondecreasingKTupleGenerator
    else:
        count_func = countFunctionAll if allow_index_repeats else\
                countFunctionDistinct
        gen_func = numberedKTupleGenerator
    
    tot = count_func(n, k)
    #print(mx_n_samples, tot)
    inds = [random.choice(range(tot)) for _ in range(mx_n_samples)]\
            if allow_tuple_repeats else\
            randomSampleWithoutReplacement(tot,\
            min(mx_n_samples, tot))
    yield from gen_func(inds, n,\
            k, allow_index_repeats, inds_sorted=False)

################