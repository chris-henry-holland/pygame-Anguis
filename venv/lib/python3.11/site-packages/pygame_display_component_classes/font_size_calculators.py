#!/usr/bin/env python

from typing import Optional, List, Tuple, Union

from pygame_display_component_classes.config import lower_char
from pygame_display_component_classes.utils import Real

# from font_size_calculators import getCharAscent, getCharDescent, getTextAscentDescent, findLargestAscentAndDescentCharacters, findMaxAscentDescentGivenMaxCharacters, findMaxFontSizeGivenHeightAndAscDescChars, findMaxFontSizeGivenHeight, findWidestText, findMaxFontSizeGivenWidth, findMaxFontSizeGivenDimensions

def getCharAscent(font: "pg.freetype", c: str,\
        font_size: Real) -> int:
    #print(font, c, font_size)
    return font.get_metrics(c, size=font_size)[0][3]

def getCharDescent(font: "pg.freetype", c: str,\
        font_size: Real) -> int:
    tup = font.get_metrics(c, size=font_size)[0]
    return (0 if tup[2] < tup[3] else (1 << 32)) - tup[2]

def getTextAscentAndDescent(font: "pg.freetype", text: str,\
        font_size: Real):
    
    ascent = -float("inf")
    descent = -float("inf")
    for l, tup in zip(text, font.get_metrics(text, size=font_size)):
        y1, y2 = tup[2], tup[3]
        if y1 > y2: y1 = y1 - (1 << 32)
        #print(l, y1, y2)
        ascent = max(ascent, y2)
        descent = max(descent, -y1)
    return ascent, descent

def findLargestAscentAndDescentCharacters(font: "pg.freetype",\
        text_list: str, font_size: Optional[Real]=None, min_lowercase: bool=False) -> Optional[Tuple[int]]:
    if font_size is None: font_size = 100
    if min_lowercase:
        text_list.append(lower_char)
        text = "".join(text_list)
        text_list.pop()
    else: text = "".join(text_list)
    max_ascent = -float("inf")
    max_descent = -float("inf")
    for l, tup in zip(text, font.get_metrics(text, size=font_size)):
        y1, y2 = tup[2], tup[3]
        if y1 > y2: y1 = y1 - (1 << 32)
        #print(l, y1, y2)
        if y2 > max_ascent:
            max_ascent = y2
            l_asc = l
        if -y1 > max_descent:
            max_descent = -y1
            l_desc = l
    return l_asc, l_desc if l_asc else None

def findMaxAscentDescentGivenMaxCharacters(font: "pg.freetype",\
        font_size: float, l_asc: str, l_desc: str) -> Tuple[int]:
    
    ascent = font.get_metrics(l_asc, size=font_size)[0][3]
    tup = font.get_metrics(l_desc, size=font_size)[0]
    descent = -tup[2] if tup[2] <= tup[3] else (1 << 32) - tup[2]
    return (ascent, descent)

def findHeightGivenAscDescChars(font: "pg.freetype", font_size: Real, l_asc: str, l_desc: str) -> int:
    return sum(findMaxAscentDescentGivenMaxCharacters(font,\
            font_size, l_asc, l_desc))

def findMaxFontSizeGivenHeightAndAscDescChars(font: "pg.freetype", l_asc: str, l_desc: str, height: Optional[int]=None, max_size: Optional[Real]=None) -> Tuple[Union[Real, bool]]:
    #print(f"l_asc = {l_asc}, l_desc = {l_desc}, height = {height}")
    if height is None:
        return max_size, False
    def getHeight(font_size: Real) -> int:
        return findHeightGivenAscDescChars(font, font_size, l_asc, l_desc)
        #print(font,\
        #        font_size, l_asc, l_desc)
        #return sum(findMaxAscentDescentGivenMaxCharacters(font,\
        #        font_size, l_asc, l_desc))
    #print("hi1")
    if max_size is None:
        max_size = float("inf")
    elif getHeight(max_size) <= height:
        return max_size, False
    #print("hi2")
    size = min(height, max_size)
    size *= height / getHeight(size)
    h = getHeight(size)
    #print(height, h)
    if h <= height:
        while h <= height:
            lb = size
            size *= 2
            h = getHeight(size)
        ub = min(size, max_size)
    else:
        while h > height:
            ub = size
            size /= 2
            h = getHeight(size)
            #print(f"\n\nsize = {size}, h = {h}")
            if size < 10 ** -5:
                return 0, True
        lb = size
    lft, rgt = lb, ub
    #print("hello")
    while rgt - lft > 10 ** -5:
        mid = lft + (rgt - lft) / 2
        if getHeight(mid) <= height:
            lft = mid
        else: rgt = mid
    return lft, True

def findMaxFontSizeGivenHeight(font: "pg.freetype",\
        text_lst: List[str], height: Optional[int]=None, min_lowercase: bool=False,\
        max_size: Optional[Real]=None) -> Tuple[Union[Optional[Real], bool]]:
    ad_tup = findLargestAscentAndDescentCharacters(font, text_lst,\
            font_size=height * 10, min_lowercase=min_lowercase)
    if ad_tup is None: return None, False
    return findMaxFontSizeGivenHeightAndAscDescChars(font, *ad_tup,\
            height=height, max_size=max_size)

def findWidestText(font: "pg.freetype",\
        text_lst: List[str], font_size: Optional[Real]=None) -> Tuple[int]:
    if font_size is None: font_size = 1000
    max_width = -float("inf")
    for i, text in enumerate(text_lst):
        text_rect = font.get_rect(text, size=font_size)
        if text_rect.w > max_width:
            max_width = text_rect.w
            idx = i
    return idx, max_width

def findMaxFontSizeGivenWidth(font: "pg.freetype",\
        text_lst: List[str], width: Optional[int]=None,\
        max_size: Optional[Real]=None) -> Union[Optional[Real], bool]:
    if width is None:
        return max_size, False
    size = 1000 if max_size is None else max_size
    idx, w0 = findWidestText(font, text_lst, size)
    if w0 <= 0:
        return max_size, False
    text = text_lst[idx]
    def getWidth(font_size: Real) -> int:
        text_rect = font.get_rect(text, size=font_size)
        return text_rect.w
    lb = None
    if max_size is None:
        size *= width / w0
        w = getWidth(size)
        while w <= width:
            lb = size
            size *= 2
            w = getWidth(size)
        ub = size
    else:
        w = getWidth(max_size)
        if w <= width:
            return max_size, False
        size = max_size
    if lb is None:
        while w > width:
            ub = size
            size /= 2
            w = getWidth(size)
        lb = size
    lft, rgt = lb, ub
    while rgt - lft > 10 ** -5:
        mid = lft + (rgt - lft) / 2
        if getWidth(mid) <= width:
            lft = mid
        else: rgt = mid
    return lft, True

def findMaxFontSizeGivenDimensions(font: "pg.freetype",\
        text_lst: List[str], width: Optional[int]=None, height: Optional[int]=None, min_lowercase: bool=False, max_size: Optional[Real]=None) -> Tuple[Union[Real, bool]]:
    chng = False
    sz, b = findMaxFontSizeGivenHeight(font, text_lst, height=height, min_lowercase=min_lowercase, max_size=max_size)
    if b: chng = True
    #print(res)
    sz, b = findMaxFontSizeGivenWidth(font, text_lst, width=width,\
            max_size=sz)
    if b: chng = True
    return sz, chng
