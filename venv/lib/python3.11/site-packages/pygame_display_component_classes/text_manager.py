#!/usr/bin/env python

import functools
import heapq
import os
import sys

from sortedcontainers import SortedList, SortedDict

from typing import Union, Tuple, List, Set, Dict, Optional, Callable, Any

import pygame as pg
import pygame.freetype

from pygame_display_component_classes.config import named_colors_def, font_def_func
from pygame_display_component_classes.utils import Real, ColorOpacity

from pygame_display_component_classes.position_offset_calculators import topLeftFromAnchorPosition
from pygame_display_component_classes.font_size_calculators import (
    findLargestAscentAndDescentCharacters,
    findMaxAscentDescentGivenMaxCharacters,
    findHeightGivenAscDescChars,
    findMaxFontSizeGivenHeightAndAscDescChars,
    findMaxFontSizeGivenHeight,
    findMaxFontSizeGivenWidth,
    getCharAscent,
    getCharDescent,
)
from pygame_display_component_classes.display_base_classes import (
    ComponentBaseClass,
    ComponentGroupElementBaseClass,
    ComponentGroupBaseClass,
    checkHiddenKwargs,
)

# Review- Need to reconsider how max height and max font size given width
# is communicated between the TextGroupElement obejcts and the TextGroup

class Text(ComponentBaseClass):
    text_obj_names = set()
    unnamed_count = 0
    
    #font_color,font,max_shape,text,text_global_asc_desc_chars0,text_global_asc_desc_chars,font_size,asc_desc_sizes_local,asc_desc_sizes_global,top_offset,shape,shape_eff,text_rect,text_img_constructor
    
    reset_graph_edges = {
        "text": {"text_rect": True, "text_local_asc_desc_chars": True, "max_font_size_given_width": True, "updated": True},
        "font": {"text_local_asc_desc_chars": True, "font_size_actual": (lambda obj: obj.font_size is None), "max_font_size_given_width": True, "updated": True},
        "font_color": {"updated": True},
        "max_shape": {"max_font_size_given_width": True, "font_size_actual": (lambda obj: obj.font_size is None), "max_shape_actual": True},
        "max_font_size_given_width": {"font_size_actual": True},
        "font_size": {"font_size_actual": True},
        "font_size_actual": {"text_rect": True, "asc_desc_sizes_local": True, "asc_desc_sizes_global": True, "updated": True},
        "text_rect": {"shape": True},
        "shape": {"shape_eff": True},
        
        "text_local_asc_desc_chars": {"text_global_asc_desc_chars": (lambda obj: obj.text_global_asc_desc_chars0 is None), "asc_desc_sizes_local": True},
        "text_global_asc_desc_chars0": {"text_global_asc_desc_chars": True},
        "text_global_asc_desc_chars": {"asc_desc_sizes_global": True},
        "asc_desc_sizes_local": {"top_offset": True},
        "asc_desc_sizes_global": {"top_offset": True},
        "top_offset": {"updated": True},
    }
    
    
    custom_attribute_change_propogation_methods = {}
    
    attribute_calculation_methods = {
        "max_shape_actual": "calculateMaxShapeActual",
        "max_font_size_given_width": "calculateMaxFontSizeGivenWidth",
        "font_size_actual": "calculateFontSizeActual",
        "text_local_asc_desc_chars": "calculateTextLocalAscDescChars",
        "text_global_asc_desc_chars": "calculateTextGlobalAscDescChars",
        "asc_desc_sizes_local": "calculateAscDescSizesLocal",
        "asc_desc_sizes_global": "calculateAscDescSizesGlobal",
        "top_offset": "calculateTopOffset",
        "shape": "calculateShape",
        "shape_eff": "calculateEffectiveShape",
        "text_rect": "calculateTextRectangle",
        "text_img_constructor": "createTextConstructor",
        "updated": "calculateUpdated",
    }
    
    attribute_default_functions = {
        "font": ((lambda obj: font_def_func()),),
        "font_size": ((lambda obj: None),),
        "font_color": ((lambda obj: ((0, 0, 0), 1)),),
        "anchor_rel_pos0": ((lambda obj: (0, 0)),),
        "anchor_type0": ((lambda obj: "topleft"),),
        "text_global_asc_desc_chars0": ((lambda obj: ()),),
    }
    
    fixed_attributes = set()
    
    displ_attrs = ["text_img_constructor"]
    
    def __init__(
        self,
        max_shape: Tuple[Optional[Real]],
        text: str,
        font: Optional["pg.freetype"]=None,
        font_size: Optional[Real]=None,
        font_color: Optional[ColorOpacity]=None,
        anchor_rel_pos0: Optional[Tuple[int]]=None,
        anchor_type0: Optional[str]=None,
        text_global_asc_desc_chars0: Optional[Tuple[Optional[str]]]=None,
        name: Optional[str]=None,
        **kwargs,
    ):
        #print("howdy")
        #print(kwargs)
        # Note- font_size if specified overrides max_shape. Thus,
        # if font_size is given then the shape of the text can
        # exceed max_shape. 
        
        checkHiddenKwargs(type(self), kwargs)
        if name is None:
            Text.unnamed_count += 1
            name = f"text object {self.unnamed_count}"
        #self.name = name
        Text.text_obj_names.add(name)
        super().__init__(**self.initArgsManagement(locals(), kwargs=kwargs))#, rm_args=["name"]))
        pg.init()
    
    def calculateTextLocalAscDescChars(self) -> Tuple[Tuple[str, str], Tuple[str, str]]:
        return tuple(findLargestAscentAndDescentCharacters(\
                self.font, [self.text], font_size=100,\
                min_lowercase=b) for b in (False, True))
    
    def calculateTextGlobalAscDescChars(self) -> Tuple[str, str]:
        res = self.text_global_asc_desc_chars0
        if not res:
            res = self.text_local_asc_desc_chars[1]
        return res
    
    """
    def _setTextLocalAscDescChars(self,\
            text_local_asc_desc_chars: Tuple[Optional[Tuple[str]]])\
            -> Tuple[Tuple[bool]]:
        prev = getattr(self, "_text_local_asc_desc_chars", (None, None))
        self._text_local_asc_desc_chars = text_local_asc_desc_chars
        #if prev is None:
        #    self._text_local_asc_desc_chars = text_local_asc_desc_chars
        res = []
        for tup1, tup2 in zip(prev, text_local_asc_desc_chars):
            if tup1 is None or tup2 is None:
                res.append(tuple([tup1 is not tup2] * 2))
                continue
            res.append(tuple(x == y for x, y in zip(tup1, tup2)))
        res = tuple(res)
        #res = ((True, True), (True, True)) if prev is None else\
        #        tuple(tuple(x == y for x, y in zip(tup1, tup2))\
        #        for tup1, tup2 in zip(prev, text_local_asc_desc_chars))
        if res[0][0]:
            self._top_offset = None
        if self._text_global_asc_desc_chars0 is None and\
                res[1] != (False, False):
            self._text_global_asc_desc_chars = None
        return res
        
        
        #return tuple(tuple(x == y for x, y in zip(tup1, tup2))\
        #        for tup1, tup2 in zip(prev, text_local_asc_desc_chars))
    
    
    def _calculateAndSetTextLocalAscDescChars(self) -> Tuple[Tuple[bool]]:
        ad_chars = self._calculateTextLocalAscDescChars()
        #print(str(ad_chars))
        res = self._setTextLocalAscDescChars(ad_chars)
        return res
    """
    
    def calculateMaxShapeActual(self) -> Tuple[Optional[int], Optional[int]]:
        return None if self.max_shape is None else self.max_shape
    
    def calculateMaxFontSizeGivenWidth(self) -> Real:
        #print("using Text method calculateMaxFontSizeGivenWidth()")
        #print(self.max_shape)
        if self.max_shape is None:
            return float("inf")
        if self.max_shape_actual[0] == float("inf"):
            return float("inf")
        res = findMaxFontSizeGivenWidth(self.font, [self.text], width=self.max_shape_actual[0],\
                max_size=None)[0]
        #print(self.text, self.max_shape_actual[0], res)
        return res
    
    def _calculateFontSize(self) -> Real:
        #print("running _calculateFontSize()")
        asc_desc_chars = self.text_global_asc_desc_chars
        #print(f"self.font_size = {self.font_size}")
        w, h = self.max_shape_actual
        #print(w, h)
        if w == float("inf") and h == float("inf"):
            raise ValueError("No restrictions given on text height or width")
        res = None
        if asc_desc_chars is not None:
            res = findMaxFontSizeGivenHeightAndAscDescChars(self.font,\
                    *asc_desc_chars, height=h)[0]
        #print(f"res = {res}")
        #res = findMaxFontSizeGivenWidth(self.font, [self.text], width=w,\
        #        max_size=res)[0]
        res2 = self.max_font_size_given_width
        if res is None: return res2
        #print(f"font size = {res}")
        return min(res, res2)
    
    def calculateFontSizeActual(self) -> Real:
        #print("running calculateFontSizeActual()")
        res = self.font_size
        #print(f"font_size = {self.text_group.font_size}")
        #print(f"font_size_actual = {self.text_group.font_size_actual}")
        #if hasattr(self, "text_group"):
        #    print(f"text group max height = {self.text_group.max_height}")
        #    print(f"text_group.max_height0 = {self.text_group.max_height0}")
        #    print(f"text_group.heights_dict = {self.text_group.heights_dict}")
        #    print(f"self.font_size = {self.font_size}")
        #    print(f"text_group.font_size_actual = {self.text_group.font_size_actual}")
        #print(f"font_size = {res}")
        res = self._calculateFontSize() if res is None else res
        #print(f"font_size = {res}")
        return res
    
    def _calculateAscDescSizes(self, asc_desc_chars: Optional[Tuple[str]]) -> Tuple[int]:
        #print("\nrunning _calculateAscDescSizes()")
        #print(asc_desc_chars)
        if not asc_desc_chars:
            return (0, 0)
        font_size = self.font_size_actual
        if font_size == float("inf"): return (float("inf"), float("inf"))
        #print("hello")
        #print(f"font_size = {font_size}, _font_size_actual = {self._font_size_actual}")
        return findMaxAscentDescentGivenMaxCharacters(\
                self.font, font_size,\
                *asc_desc_chars)
    
    def calculateAscDescSizesLocal(self) -> Tuple[int]:
        return self._calculateAscDescSizes(self.text_local_asc_desc_chars[0])
    
    def calculateAscDescSizesGlobal(self) -> Tuple[int]:
        return self._calculateAscDescSizes(self.text_global_asc_desc_chars)
    
    
    def calculateTopOffset(self) -> int:
        if not self.text: return 0
        return self.asc_desc_sizes_global[0] - self.asc_desc_sizes_local[0]
    
    def calculateShape(self) -> Tuple[Real]:
        rect = self.text_rect
        return (rect.w, rect.h)
    
    def calculateEffectiveShape(self) -> Tuple[Real]:
        #print(f"calculating effective shape of text: {self.text}")
        h = sum(self.asc_desc_sizes_global)
        w = self.shape[0]
        return (w, h)
        
    def calculateTopleftEffective(self, anchor_rel_pos: Tuple[Real], anchor_type: str="topleft") -> Tuple[Real]:
        #print("using calculateTopleftEffective()")
        #print(f"self.shape_eff = {self.shape_eff}")
        return topLeftFromAnchorPosition(self.shape_eff,\
                anchor_type, anchor_rel_pos)
    
    
    def calculateTopleftActual(self, anchor_rel_pos: Tuple[Real], anchor_type: str="topleft") -> Tuple[Real]:
        topleft_eff = self.calculateTopleftEffective(anchor_rel_pos, anchor_type=anchor_type)
        return (topleft_eff[0], topleft_eff[1] + self.top_offset)
    
    def calculateTextRectangle(self):
        #print(f"\ncalculating text_rect for {self.text}")
        #print(type(self).__name__)
        #print(f"font_size_actual = {self.font_size_actual}")
        #print(f"max_shape_actual = {self.max_shape_actual}")
        if isinstance(self, TextGroupElement):
            text_group = self.text_group
            #print(f"text_group.max_height = {text_group.max_height}")
            #print(f"text_group.max_font_size_given_heights = {text_group.max_font_size_given_heights}")
            #print(f"text_group.max_font_sizes_given_widths = {text_group.max_font_sizes_given_widths}")
            #print(f"text_group.font_size = {text_group.font_size}")
            #print(f"text_group.font_size_actual = {text_group.font_size_actual}")
        return self.font.get_rect(self.text, size=self.font_size_actual)
    
    def calculateUpdated(self) -> bool:
        #print("Text object updated")
        return True
    
    def createTextConstructor(self) -> Callable:
        if self.font_color is None:
            # If font_color given as None then the text does not
            # display
            return (lambda surf, anchor_rel_pos, anchor_type: None)
        
        def textConstructor(surf: "pg.Surface", anchor_rel_pos: Tuple[int], anchor_type: str="topleft") -> None:
            font_color = self.font_color
            if not font_color: return
            color, alpha0 = self.font_color
            #print(f"shape = {self.shape}, shape_eff = {self.shape_eff}")
            text_rect = self.text_rect#self.getTextRect(anchor_rel_pos, anchor_type=anchor_type)
            #setattr(text_rect, anchor_type, anchor_rel_pos)#
            topleft = self.calculateTopleftActual(anchor_rel_pos, anchor_type=anchor_type)
            #print(f"anchor_rel_pos = {anchor_rel_pos}, anchor_type = {anchor_type}, shape = {self.shape}, shape_eff = {self.shape_eff}, topleft = {topleft}")
            text_rect.topleft = topleft
            self.font.render_to(surf, text_rect, self.text, (*color, alpha0 * 255), size=self.font_size_actual)
            self._updated = False
            return
        return textConstructor
    
    def draw(self, surf: "pg.Surface", anchor_rel_pos: Optional[Tuple[int]]=None, anchor_type: Optional[str]=None):
        if anchor_rel_pos is None: anchor_rel_pos = self.anchor_rel_pos0
        if anchor_type is None: anchor_type = self.anchor_type0
        #print(f"anchor_rel_pos = {anchor_rel_pos}, anchor_type = {anchor_type}")
        #print(f"surf dimensions = {(surf.get_width(), surf.get_height())}")
        for attr in self.displ_attrs:
            func = getattr(self, attr, None)
            if func is None:
                raise ValueError(f"Attribute {attr} not found")
            #print(anchor_rel_pos, anchor_type)
            func(surf, anchor_rel_pos, anchor_type=anchor_type)
        return

class TextGroupElement(ComponentGroupElementBaseClass, Text):
    #finalizer_attrs = {"name", "slider_group"}
    
    group_cls_func = lambda: TextGroup
    group_obj_attr = "text_group"
    
    
    custom_attribute_change_propogation_methods = {
        "max_shape": "customMaxShapeChangePropogation",
        "max_font_size_given_width": "customMaxFontSizeGivenWidthChangePropogation",
    }
    
    def __init__(
        self,
        text_group: "TextGroup",
        text: str,
        max_shape: Optional[Real]=None,
        font_color: Optional[Tuple[Union[Tuple[int], Real]]]=None,
        anchor_rel_pos0: Optional[Tuple[Real]]=None,
        anchor_type0: Optional[str]=None,
        name: Optional[str]=None,
        **kwargs,
    ):
        checkHiddenKwargs(type(self), kwargs)
        #max_shape = (max_width, text_group.max_height)
        super().__init__(
            max_shape=max_shape,
            text=text,
            font=text_group.font,
            font_size=text_group.font_size_actual,
            font_color=font_color,
            anchor_rel_pos0=anchor_rel_pos0,
            anchor_type0=anchor_type0,
            text_global_asc_desc_chars0=text_group.text_global_asc_desc_chars,
            name=name,
            _group=text_group,
            **kwargs,
        )
    
    """
    @classmethod
    def remove(cls, attrs: Dict[str, Any]) -> None:
        
        group = attrs.get(cls.group_obj_attr, None)
    
        super().remove(attrs)
        nm = attrs.get("name", None)
        if nm is not None:
            print(f"Removed {cls.__name__} object {nm}")
        else: print(f"Removed {cls.__name__}")
        return
    """
    def customMaxHeightChangePropogation(self, new_val: Optional[int], prev_val: Optional[int]) -> None:
        #print("using customMaxHeightChangePropogation()")
        #print(f"max_shape = {self.max_shape}")
        #val = None if self.max_shape is None else self.max_shape[1]
        if prev_val == float("inf"): prev_val = None
        if new_val == float("inf"): new_val = None
        if new_val == prev_val: return
        mx_shape = self.__dict__.get("_max_shape", None)
        if mx_shape is None: mx_shape = (None, None)
        #self.__dict__["_max_shape"] = (mx_shape[0], new_val)
        rm_dict = {} if prev_val is None or prev_val == float("inf")\
                else {prev_val: 1}
        add_dict = {} if new_val is None or new_val == float("inf")\
                else {new_val: 1}
        #print(f"prev_val = {prev_val}, val = {val}")
        #print(f"rm_dict = {rm_dict}, add_dict = {add_dict}")
        self.text_group._updateHeights(rm_dict, add_dict)
        #print(self.text_group.heights_dict)
        #print(self.text_group)
        #print("hello")
        #print(rm_dict, add_dict)
        #if self.text_group._updateHeights(rm_dict, add_dict):
        #    #print(f"hello there, {self.text}")
        #    self.text_group.calculateAndSetFontSize()
        return
    
    #def calculateMaxFontSizeGivenWidth(self, max_size: Optional[Real]=None) -> Real:
    #    return findMaxFontSizeGivenWidth(self.font,\
    #            [self.text], width=self.max_width,\
    #            max_size=max_size)[0]
    
    def customMaxFontSizeGivenWidthChangePropogation(self, new_val: Optional[Real], prev_val: Optional[Real]) -> None:#, _update_textgroup_max_font_size_given_width: bool=True) -> None:
        #print(f"Using TextGroupElement {self} method customMaxFontSizeGivenWidthChangePropogation()")
        #print(f"prev_val = {prev_val}, new_val = {new_val}")
        #prev_val = self.__dict__.get("_max_font_size_given_width", None)
        #print("Setting max font size given widths")
        if prev_val == float("inf"): prev_val = None
        if new_val == float("inf"): new_val = None
        if new_val == prev_val: return
        add_font_size = new_val
        # Review- hacky workaround
        #add_font_size = self.__dict__.get("_max_font_size_given_#self.calculateMaxFontSizeGivenWidth()
        #self._max_font_size_given_width = add_font_size
        #print(prev_val, add_font_size)
        #if add_font_size == float("inf"): add_font_size = None
        #rm_font_size = None if prev_val == float("inf") else prev_val
        rm_font_size = prev_val
        #rm_font_size = getattr(self,\
        #        "_max_font_size_given_width", None)
        #self._max_font_size_given_width = font_size
        #self.__dict__["_max_font_size_given_width"] = new_val
        rm_font_sizes = {} if rm_font_size is None else {rm_font_size: 1}
        add_font_sizes = {} if add_font_size is None else {add_font_size: 1}
        #print(f"rm_font_sizes = {rm_font_sizes}, add_font_sizes = {add_font_sizes}")
        self.text_group._updateMaxFontSizesGivenWidths(\
                rm_font_sizes, add_font_sizes)
        #print(self.text_group.max_font_sizes_given_widths_dict)
        #if _update_textgroup_max_font_size_given_width and\
        #        self.text_group._updateMaxFontSizesGivenWidths(\
        #        rm_font_sizes, add_font_sizes):
        #    #print("hello")
        #    #print(self.text_group.font_size)
        #    self.font_size = self.text_group.font_size
        #print("finished using customMaxFontSizeGivenWidthChangePropogation()")
        return
    
    #def _calculateAndcustomMaxFontSizeGivenWidthChangePropogation(self, prev_val: Optional[int], max_size: Optional[Real]=None, _update_textgroup_max_font_size_given_width: bool=True) -> Real:
    #    #print("howdy")
    #    res = self._calculateMaxFontSizeGivenWidth(max_size=max_size)
    #    self._customMaxFontSizeGivenWidthChangePropogations(res, prev_val: Optional[int], _update_textgroup_max_font_size_given_width=_update_textgroup_max_font_size_given_width)
    #    return res
    
    def customMaxShapeChangePropogation(self, new_val: Optional[Tuple[Optional[Real]]], prev_val: Optional[Tuple[Optional[Real]]]) -> None:
        #print(f"Setting max shape for text {self.text}")
        #if hasattr(super(), "customMaxShapeChangePropogation"):
        #    super().customMaxShapeChangePropogation(max_shape)
        #print("setting max_width and max_height_local")
        #print(max_shape)
        #prev_val
        #self.customMaxHeightChangePropogation(None if not prev_val else prev_val[1])
        #prev_mx_w = None if not prev_val else prev_val[0]
        #prev_mx_font_sz_given_w = None if prev_mx_w is None else findMaxFontSizeGivenWidth(self.font, [self.text], width=prev_mx_w,\
        #        max_size=None)[0]
        if prev_val is None: prev_val = (None, None)
        if new_val is None: new_val = (None, None)
        self.customMaxHeightChangePropogation(new_val[1], prev_val[1])
        #prev_val = self.__dict__.get("_max_shape", None)
        """
        prev_mx_w = None if prev_val[0] == float("inf") else prev_val[0]
        new_mx_w = None if new_val == float("inf") else new_val[0]
        if new_mx_w == prev_mx_w: return
        #self.__dict__["_max_shape"] = (new_mx_w, prev_val[1])
        prev_mx_font_sz_given_w = None if prev_mx_w is None else findMaxFontSizeGivenWidth(self.font, [self.text], width=prev_mx_w,\
                max_size=None)[0]
        new_mx_font_sz_given_w = None if new_mx_w is None else findMaxFontSizeGivenWidth(self.font, [self.text], width=new_mx_w,\
                max_size=None)[0]
        print(f"calling customMaxFontSizeGivenWidthChangePropogation() from TextGroupElement method customMaxShapeChangePropogation()")
        self.customMaxFontSizeGivenWidthChangePropogation(new_mx_font_sz_given_w, prev_mx_font_sz_given_w)
        """
        return
    
    def calculateMaxShapeActual(self) -> Tuple[Optional[int], Optional[int]]:
        #print("calculating max shape actual")
        #print(self.text)
        #print("max_shape" in self.__dict__.keys())
        #print("_max_shape" in self.__dict__.keys())
        #print(self.__dict__.get("_max_shape", None))
        #print(self.max_shape)
        return (float("inf") if self.max_shape is None else self.max_shape[0], self.text_group.max_height)
    
    """
    @property
    def max_height_group(self):
        return self.text_group.max_height
    
    @property
    def max_height_local(self):
        return getattr(self, "_max_height_local", self.max_height_group)
    
    @max_height_local.setter
    def max_height_local(self, max_height_local):
        prev = getattr(self, "_max_height_local", None)
        print("setting max_height_local")
        print(prev, max_height_local)
        if max_height_local == prev:
            return
        self._max_height_local = max_height_local
        #print()
        #print("Setting max height local")
        #if self.text_group._replaceHeight(prev, max_height_local)
        rm_dict = {} if prev is None else {prev: 1}
        add_dict = {} if max_height_local is None else {max_height_local: 1}
        #print("hello")
        #print(rm_dict, add_dict)
        if self.text_group._updateHeights(rm_dict, add_dict):
            print(f"hello there, {self.text}")
            self.text_group.calculateAndSetFontSize()
        #print("bye")
        return
    """
    
    """
    def _setTextLocalAscDescChars(self,\
            text_local_asc_desc_chars: Tuple[Optional[Tuple[str]]],\
            update_textgroup_asc_desc_chars: bool=True)\
            -> Tuple[Tuple[bool]]:
        res = super()._setTextLocalAscDescChars(\
                text_local_asc_desc_chars)
        if not update_textgroup_asc_desc_chars:
            return res
        prev = getattr(self, "_text_local_asc_desc_chars", None)
        if prev is None:
            prev = ((None, None), (None, None))
        if res[1] == (False, False):
            return res
        rm_chars = [[], []]
        add_chars = [[], []]
        local_idx = self.text_group.min_lowercase 
        for idx, (prev_l, curr_l) in enumerate(zip(prev[local_idx], text_local_asc_desc_chars[local_idx])):
            if prev_l is not None:
                rm_chars[idx].append(prev_l)
            if curr_l is not None:
                add_chars[idx].append(curr_l)
        
        self.text_group._updateAscDescChars(rm_chars[0],\
                add_chars[0], rm_chars[1], add_chars[1], set_font_size=False)
        #self.text_group._replaceAscDescChars(prev[1], text_local_asc_desc_chars[1])
        return res
    
    def _calculateAndSetTextLocalAscDescChars(self, update_textgroup_asc_desc_chars: bool=True) -> Tuple[Tuple[bool]]:
        ad_chars = self._calculateTextLocalAscDescChars()
        res = self._setTextLocalAscDescChars(ad_chars, update_textgroup_asc_desc_chars=update_textgroup_asc_desc_chars)
        return res
    """

class TextGroup(ComponentGroupBaseClass):
    group_element_cls_func = lambda: TextGroupElement
    
    reset_graph_edges = {
        "font": {"text_global_asc_desc_chars": (lambda obj: obj.text_global_asc_desc_chars0 is None), "font_size_actual": (lambda obj: obj.font_size is None), "max_font_size_given_heights": True},
        "max_height0": {"max_height": True},
        "max_height": {"max_font_size_given_heights": True},
        "max_font_size_given_heights": {"font_size_actual": (lambda obj: obj.font_size is None)},
        "max_font_sizes_given_widths": {"font_size_actual": (lambda obj: obj.font_size is None)},
        "font_size": {"font_size_actual": True},
        #"font_size_actual": {"asc_desc_sizes_global": True},
        "min_lowercase": {"text_global_asc_desc_chars": (lambda obj: obj.text_global_asc_desc_chars0 is None)},
        
        "text_global_asc_desc_chars0": {"text_global_asc_desc_chars": True},
        "text_global_asc_desc_chars": {"max_font_size_given_heights": True},# "asc_desc_sizes_global": True}
    }
    
    custom_attribute_change_propogation_methods = {
        "max_height0": "customMaxHeight0ChangePropogation",
    }
    
    attribute_calculation_methods = {
        "font_size_actual": "calculateFontSizeActual",
        "text_global_asc_desc_chars": "calculateTextGlobalAscDescChars",
        "asc_desc_sizes_global": "calculateAscDescSizesGlobal",
        "max_height": "calculateMaxHeight",
        "max_font_size_given_heights": "calculateMaxFontSizeGivenHeights",
        "max_font_sizes_given_widths": "calculateMaxFontSizeGivenWidths",
    }
    
    # Review- account for using element_inherited_attributes in ComponentGroupBaseClass
    attribute_default_functions = {
        "max_height0": ((lambda obj: float("inf")),),
        "min_lowercase": ((lambda obj: True),),
        
        "heights_dict": ((lambda obj: SortedDict()),),
        "max_font_sizes_given_widths_dict": ((lambda obj: SortedDict()),),
        "asc_char_dict": ((lambda obj: SortedDict()),),
        "desc_char_dict": ((lambda obj: SortedDict()),),
        "asc_char_h100": ((lambda obj: {}),),
        "desc_char_h100": ((lambda obj: {}),),
    }
    
    attribute_default_functions = {
        **attribute_default_functions,
        **{
            attr: Text.attribute_default_functions.get(attr) for attr in
            [
                "font",
                "font_size",
                "text_global_asc_desc_chars0",
            ]
        }
    }
    
    
    fixed_attributes = {"text_objects"}
    
    element_inherited_attributes = {
        "text_global_asc_desc_chars": "text_global_asc_desc_chars0",
        "font_size_actual": "font_size",
    }
    
    def __init__(
        self,
        text_list: List[Tuple[Union[str, Real]]],
        max_height0: Optional[Real]=None,
        font: Optional["pg.freetype"]=None,
        font_size: Optional[Real]=None,
        min_lowercase: Optional[bool]=None,
        text_global_asc_desc_chars: Optional[Tuple[Optional[str]]]=None,
        **kwargs,
    ):
        #print("Creating TextGroup object")
        #print(text_list, max_height0, font, font_size)
        #self.font_size_set = False
        #self._min_lowercase = min_lowercase
        #print("hi3")
        #self._heights_dict = SortedDict()
        #self.max_height0 = max_height0
        #print(f"max_height0 = {self.max_height0}")
        
        checkHiddenKwargs(type(self), kwargs)
        super().__init__(**self.initArgsManagement(locals(), kwargs=kwargs, rm_args=["text_list"]))
        #self.setupTextObjects(text_list)
        #print("Adding text objects to TextGroup object")
        #print(text_list)
        self.addTextObjects(text_list)
        #print("Finished adding text objects to TextGroup object")
        #print(self.heights_dict)
        #print(self.max_height)
        
        # text_list = [{"text": "Hello", "max_shape": (200, 50), "color": (named_colors_def["red"], 1)), "anchor_rel_pos0": (0, 0), "anchor_type0": "topleft"}]
    """
    def addSlider(self,
        anchor_rel_pos: Tuple[Real],
        val_range: Tuple[Real],
        increment_start: Real,
        increment: Optional[Real]=None,
        anchor_type: Optional[str]=None,
        screen_topleft_offset: Optional[Tuple[Real]]=None,
        init_val: Optional[Real]=None,
        demarc_numbers_dp: Optional[int]=None,
        demarc_intervals: Optional[Tuple[Real]]=None,
        demarc_start_val: Optional[Real]=None,
        name: Optional[str]=None,
    ) -> "SliderGroupElement":
        
        res = self._addElement(
            slider_group=self,
            anchor_rel_pos=anchor_rel_pos,
            val_range=val_range,
            increment_start=increment_start,
            increment=increment,
            anchor_type=anchor_type,
            screen_topleft_offset=screen_topleft_offset,
            init_val=init_val,
            demarc_numbers_dp=demarc_numbers_dp,
            demarc_intervals=demarc_intervals,
            demarc_start_val=demarc_start_val,
            name=name,
        )
        return res
    """
    """
    def _setGroupAscDescChars(self, ad_chars: Tuple[str]) -> None:
        # Note- does not update attribute font_sizes, which (if there
        # are any changes) needs to be done separately
        #print(f"Setting _text_global_asc_desc_chars to {ad_chars}")
        self._text_global_asc_desc_chars = ad_chars
        if self.text_global_asc_desc_chars0 is not None:
            return
        for text_obj in self.text_objects:
            text_obj.text_global_asc_desc_chars0 = ad_chars
        return
    """
    @staticmethod
    def createDefaultTextGroup(font: Optional["pg.freetype"]=None):
        #print("\ncreating TextGroup for the final Slider object")
        #res = SliderPlus.createTitleTextGroup(font=None, max_height=None)#self.demarc_numbers_max_height)
        #print("finished creating TextGroup for final Slider object")
        if font is None: font = font_def_func()
        return TextGroup(
            text_list=[],
            max_height0=None,
            font=font_def_func(),
            font_size=None,
            min_lowercase=True,
            text_global_asc_desc_chars=None
        )

    def _updateAscDescChars(
        self,
        rm_asc_chars: List[str],
        add_asc_chars: List[str],
        rm_desc_chars: List[str],
        add_desc_chars: List[str],
        #set_font_size: bool=True,
    ) -> None:
        #print("Using _updateAscDescChars()")
        ad_pair = [None, None]
        ad_pair_chng = False
        
        
        for idx, (add_chars, rm_chars, char_dict, char_h100, char_h_func) in\
                enumerate(zip((add_asc_chars, add_desc_chars),\
                (rm_asc_chars, rm_desc_chars),\
                (self.asc_char_dict, self.desc_char_dict),\
                (self.asc_char_h100, self.desc_char_h100),\
                (getCharAscent, getCharDescent))):
            curr_mx_tup, curr_mx_f = char_dict.peekitem(-1) if char_dict else ((-float("inf"), None), 0)
            ad_pair[idx] = curr_mx_tup[1]
            add = {}
            mx_add_tup = (-float("inf"), None)
            for i, l in enumerate(add_chars):
                if l in add.keys():
                    add[l][1] += 1
                    continue
                char_h100.setdefault(l, char_h_func(self.font, l, 100))
                h = char_h100[l]
                add[l] = [h, 1]
                mx_add_tup = max(mx_add_tup, (h, l))
            #print(f"add = {add}")
            rm = {}
            mx_rm_tup = (-float("inf"), None)
            for i, l in enumerate(rm_chars):
                if l in add.keys():
                    add[l][1] -=- 1
                    if not add[l][1]:
                        add.pop(l)
                    continue
                if l in rm.keys():
                    rm[l][1] += 1
                    continue
                #char_h100.setdefault(l,\
                #        getCharAscent(self.font, l, 100)) # Should already be in the dictionary
                h = char_h100[l]
                rm[l] = [h, 1]
                mx_rm_tup = max(mx_rm_tup, (h, l))
            if mx_add_tup[1] is None and mx_rm_tup[1] is None:
                continue
            for l, (h, f) in add.items():
                tup = (h, l)
                char_dict.setdefault(tup, 0)
                char_dict[tup] += f
            for l, (h, f) in rm.values():
                tup = (h, l)
                char_dict[tup] -= f
                if not char_dict[tup]:
                    char_dict.pop(tup)
            if mx_add_tup > mx_rm_tup:
                if mx_add_tup > curr_mx_tup:
                    ad_pair[idx] = mx_add_tup[1]
                    ad_pair_chng = True
                continue
            rm_f = rm[mx_rm_tup[1]][1]
            if mx_rm_tup == curr_mx_tup and rm_f == curr_mx_f:
                ad_pair_chng = True
                ad_pair[idx] = char_dict.peekitem(-1)[0][1]
        if ad_pair_chng:
            # Uses setAttributes to reset text_global_asc_desc_chars
            # and pass on the new value to the elements of the
            # group as the attribute text_global_asc_desc_chars0
            self.text_global_asc_desc_chars = None
        #self._setGroupAscDescChars(tuple(ad_pair))
        #if set_font_size and self.max_height is not None:
        #    #print("setting font size")
        #    self.calculateAndSetFontSize()
        return
    
    def calculateTextGlobalAscDescChars(self) -> Tuple[str, str]:
        res = self.text_global_asc_desc_chars0
        if not res:
            res = (self.asc_char_dict.peekitem(-1)[0][1], self.desc_char_dict.peekitem(-1)[0][1]) if self.asc_char_h100 else ()
        return res
    
    @staticmethod
    def _calculateAscDescSizesGivenFontAndFontSize(
        asc_desc_chars: Tuple[str, str],
        font: "pg.freetype",
        font_size: Real
    ) -> Tuple[Real, Real]:
        if not asc_desc_chars:
            return (0, 0)
        return findMaxAscentDescentGivenMaxCharacters(
            font,
            font_size,
            *asc_desc_chars,
        )
    
    @staticmethod
    def _calculateMaxFontSizeGivenHeightAndAscDescChars(
        asc_desc_chars: Tuple[str, str],
        font: "pg.freetype",
        max_height: Real,
    ) -> Real:
        if not asc_desc_chars or max_height == float("inf"):
            return float("inf")
        return findMaxFontSizeGivenHeightAndAscDescChars(
            font,
            *asc_desc_chars,
            height=max_height,
        )[0]
    
    def calculateAscDescSizesGlobal(self) -> Tuple[int, int]:
        return self._calculateAscDescSizesGivenFontAndFontSize(
            self.font,
            self.font_size_actual,
            self.text_global_asc_desc_chars,
        )
    
    
    
    """
    @property
    def max_height0(self):
        return self._max_height0
    
    @max_height0.setter
    def max_height0(self, max_height0):
        prev = getattr(self, "_max_height0", None)
        self._max_height0 = max_height0
        if max_height0 == prev:
            return
        #print(f"Updating max_height0")
        rm_dict = {} if prev is None else {prev: 1}
        add_dict = {} if max_height0 is None else {max_height0: 1}
        self._updateHeights(rm_dict, add_dict)
        return
    """
    
    """
    @property
    def max_height(self):
        return getattr(self, "_max_height", self.max_height0)
    
    @property
    def max_font_size_given_heights(self):
        res = getattr(self, "_max_font_size_given_heights", None)
        if res is None:
            if self.text_global_asc_desc_chars is None:
                return None
            res = float("inf") if self.max_height is None else findMaxFontSizeGivenHeightAndAscDescChars(self.font,\
                    *self.text_global_asc_desc_chars, height=self.max_height)[0]
            self._max_font_size_given_heights = res
        return res
    """
    """
    def _setGroupMaxHeight(self, max_height: Real) -> None:
        #print(f"Setting group max height as {max_height}")
        curr_font_size = -float("inf") if getattr(self, "_font_size", None) is None else self._font_size
        self._max_height = max_height
        if getattr(self, "_text_global_asc_desc_chars", None) is None:
            return
        #print("hi1")
        font_size = findMaxFontSizeGivenHeightAndAscDescChars(self.font,\
                *self._text_global_asc_desc_chars, height=self.max_height)[0]
        #print("hi2")
        self._max_font_size_given_heights = font_size
        #print("hi3")
        if self.font_size_set:
            return
        mx_sz_w = self.max_font_sizes_given_widths
        #print("hi4")
        if mx_sz_w is None: mx_sz_w = float("inf")
        #print("hi5")
        if font_size < mx_sz_w:
            #print("opt1")
            self.setFontSize(font_size)
        elif curr_font_size < mx_sz_w:
            #print("opt2")
            self.setFontSize(mx_sz_w)
        #print("hi7")
        return
    """
    def _addHeight(self, height: Real, f: int=1) -> bool:
        #print(f"using _addHeight(), height = {height}")
        if not self.heights_dict or height < self.max_height:
            #print("setting group max height")
            #self._setGroupMaxHeight(height)
            self.max_height = None
            #print("finished setting")
            res = True
        else: res = False
        self.heights_dict.setdefault(height, 0)
        self.heights_dict[height] += f
        return res 
            
    def _removeHeight(self, height: Real, f: int=1) -> bool:
        #print(f"using _removeHeight(), height = {height}")
        if self.heights_dict[height] > f:
            self.heights_dict[height] -= f
            return False
        self.heights_dict.pop(height)
        if self.__dict__.get("_max_height", None) is not None and self._max_height < height:
            return False
        h0 = self.heights_dict.peekitem(0)[0]
        if h0 <= height:
            return False
        #self._setGroupMaxHeight(h0)
        self.max_height = None
        return True
    
    def _updateHeights(
        self,
        rm_heights: Dict[Real, int],
        add_heights: Dict[Real, int],
    ) -> bool:
        #print("Updating heights")
        #print(f"rm_heights = {rm_heights}, add_heights = {add_heights}")
        #print(self.heights_dict)
        for k in set(rm_heights.keys()).intersection(add_heights):
            rm_f = rm_heights[k]
            add_f = add_heights[k]
            d_f = add_heights[k] - rm_heights[k]
            if not d_f:
                add_heights.pop(k)
                rm_heights.pop(k)
            elif d_f > 0:
                add_heights = d_f
                rm_heights.pop(k)
            else:
                add_heights.pop(k)
                rm_heights = -d_f
        #print("hi1")
        if not rm_heights and not add_heights:
            return False
        #print(add_heights, rm_heights)
        #print(self._heights_dict)
        #print("hi2")
        if add_heights:
            mn_add = min(add_heights.keys())
            mn_add_f = add_heights[mn_add]
        else: mn_add = float("inf")
        #print("hi3")
        if rm_heights:
            mn_rm = min(rm_heights.keys())
            mn_rm_f = rm_heights[mn_rm]
        else: mn_rm = float("inf")
        #print("hi4")
        if mn_add < mn_rm:
            add_heights.pop(mn_add)
        else: rm_heights.pop(mn_rm)
        #print("hi5")
        for k, f in add_heights.items():
            self.heights_dict.setdefault(k, 0)
            self.heights_dict[k] += f
        #print("hi6")
        for k, f in rm_heights.items():
            if self.heights_dict[k] == f:
                self.heights_dict.pop(k)
            else: self.heights_dict[k] -= f
        #print("hi7")
        #print(mn_add, mn_rm)
        #if mn_add < mn_rm:
        #    #print("adding")
        #    #print(mn_add, mn_add_f)
        #    res = self._addHeight(mn_add, f=mn_add_f)
        #else:
        #    #print("removing")
        #    #print(mn_rm, mn_rm_f)
        #    res = self._removeHeight(mn_rm, f=mn_rm_f)
        res = self._addHeight(mn_add, f=mn_add_f)\
                if mn_add < mn_rm else\
                self._removeHeight(mn_rm, f=mn_rm_f)
        #print("hi8")
        if not res: return False
        self.max_height = None
        """
        for text_obj in getattr(self, "text_objects", []):
            if text_obj is None: continue
            text_obj._font_size = None
            text_obj._top_offset = None
            text_obj._shape = None
            text_obj._shape_eff = None
            text_obj._text_img = None
        """
        return res
    
    def customMaxHeight0ChangePropogation(self, new_val: Optional[Real], prev_val: Optional[Real]) -> None:
        #print("using customMaxHeight0ChangePropogation()")
        if prev_val == float("inf"): prev_val = None
        if new_val == float("inf"): new_val = None
        if prev_val == new_val: return
        #self.__dict__["_max_height0"] = new_val
        #val = self.max_height0
        #print(f"prev_val = {prev_val}, val = {val}")
        rm_dict = {} if prev_val is None or prev_val == float("inf")\
                else {prev_val: 1}
        add_dict = {} if new_val is None or new_val == float("inf")\
                else {new_val: 1}
        self._updateHeights(rm_dict, add_dict)
        #print("hello")
        #print(rm_dict, add_dict)
        #if self.text_group._updateHeights(rm_dict, add_dict):
        #    #print(f"hello there, {self.text}")
        #    self.text_group.calculateAndSetFontSize()
        return
    
    def calculateMaxHeight(self) -> Real:
        #print("Using calculateMaxHeight()")
        heights_dict = self.heights_dict
        #print(f"heights_dict = {heights_dict}")
        return heights_dict.peekitem(0)[0] if heights_dict\
                else float("inf")
    
    def calculateMaxFontSizeGivenHeights(self) -> Real:
        #print("calling calculateMaxFontSizeGivenHeights()")
        #print(self.text_global_asc_desc_chars, self.font, self.max_height)
        return self._calculateMaxFontSizeGivenHeightAndAscDescChars(
            self.text_global_asc_desc_chars,
            self.font,
            self.max_height,
        )
    
    
    
    #@property
    #def max_font_sizes_given_widths(self):
    #    return getattr(self, "_max_font_sizes_given_widths", None)
    """
    def _setGroupMaxFontSizeGivenWidths(self, font_size: Real) -> None:
        curr_font_size = self.font_size
        self._max_font_sizes_given_widths = font_size
        if self.font_size_set:
            return
        mx_sz_h = self.max_font_size_given_heights
        if mx_sz_h is None: mx_sz_h = float("inf")
        if font_size < mx_sz_h:
            self.setFontSize(font_size)
        elif curr_font_size < mx_sz_h:
            self.setFontSize(mx_sz_h)
        return
    """
    def _addMaxFontSizeGivenWidth(
        self,
        font_size: Real,
        f: int=1,
        reset_max_font_sizes_given_widths: bool=True,
    ) -> bool:
        #print("Using _addMaxFontSizeGivenWidth()")
        res = (font_size < self.max_font_sizes_given_widths)
        self.max_font_sizes_given_widths_dict.setdefault(font_size, 0)
        self.max_font_sizes_given_widths_dict[font_size] += f
        if res and reset_max_font_sizes_given_widths:
            self.max_font_sizes_given_widths = None
        return res 
            
    def _removeMaxFontSizeGivenWidth(
        self,
        font_size: Real,
        f: int=1,
        reset_max_font_sizes_given_widths: bool=True,
    ) -> bool:
        if self.max_font_sizes_given_widths_dict[font_size] > f:
            self.max_font_sizes_given_widths_dict[font_size] -= f
            return False
        fs = self.max_font_sizes_given_widths
        self.max_font_sizes_given_widths_dict.pop(font_size)
        res = (fs == font_size)
        if res and reset_max_font_sizes_given_widths:
            self.max_font_sizes_given_widths = None
        return res
        
        #fs0 = self._max_font_sizes_given_widths_dict.peekitem(0)[0]
        #if fs0 <= font_size:
        #    return False
        #self._setGroupMaxFontSizeGivenWidths(fs0)
        #return True
    
    def _updateMaxFontSizesGivenWidths(
        self,
        rm_font_sizes: Dict[Real, int],
        add_font_sizes: Dict[Real, int],
        reset_max_font_sizes_given_widths: bool=True
    ) -> bool:
        #print("Using _updateMaxFontSizesGivenWidths()")
        #print(self.max_font_sizes_given_widths_dict)
        #print(rm_font_sizes)
        #print(add_font_sizes)
        if float("inf") in rm_font_sizes.keys():
            rm_font_sizes.pop(float("inf"))
        if float("inf") in add_font_sizes.keys():
            add_font_sizes.pop(float("inf"))
           
        #print("applying _updateMaxFontSizesGivenWidths")
        #print(rm_font_sizes, add_font_sizes)
        for k in set(rm_font_sizes.keys()).intersection(add_font_sizes):
            rm_f = rm_font_sizes[k]
            add_f = add_font_sizes[k]
            d_f = add_font_sizes[k] - rm_font_sizes[k]
            if not d_f:
                add_font_sizes.pop(k)
                rm_font_sizes.pop(k)
            elif d_f > 0:
                add_font_sizes = d_f
                rm_font_sizes.pop(k)
            else:
                add_font_sizes.pop(k)
                rm_font_sizes = -d_f
        #print(rm_font_sizes, add_font_sizes)
        if not rm_font_sizes and not add_font_sizes:
            return False
        #print(add_font_sizes, rm_font_sizes)
        if add_font_sizes:
            mn_add = min(add_font_sizes.keys())
            mn_add_f = add_font_sizes[mn_add]
        else: mn_add = float("inf")
        if rm_font_sizes:
            mn_rm = min(rm_font_sizes.keys())
            mn_rm_f = rm_font_sizes[mn_rm]
        else: mn_rm = float("inf")
        if mn_add < mn_rm:
            add_font_sizes.pop(mn_add)
        elif mn_rm != float("inf"): rm_font_sizes.pop(mn_rm)
        for k, f in add_font_sizes.items():
            self.max_font_sizes_given_widths_dict.setdefault(k, 0)
            self.max_font_sizes_given_widths_dict[k] += f
        for k, f in rm_font_sizes.items():
            #print(self.max_font_sizes_given_widths_dict.keys())
            # Hacky fix
            if k not in self.max_font_sizes_given_widths_dict.keys(): continue
            if self.max_font_sizes_given_widths_dict[k] == f:
                self.max_font_sizes_given_widths_dict.pop(k)
            else: self.max_font_sizes_given_widths_dict[k] -= f
        res = self._addMaxFontSizeGivenWidth(mn_add, f=mn_add_f, reset_max_font_sizes_given_widths=reset_max_font_sizes_given_widths)\
                if mn_add < mn_rm else\
                self._removeMaxFontSizeGivenWidth(mn_rm, f=mn_rm_f, reset_max_font_sizes_given_widths=reset_max_font_sizes_given_widths)
        #print("Finished using _updateMaxFontSizesGivenWidths()")
        #print(self.max_font_sizes_given_widths_dict)
        return res
    
    def calculateMaxFontSizeGivenWidths(self) -> Real:
        #print(f"Using TextGroup method calculateMaxFontSizeGivenWidths() for text group {self}")
        res = self.max_font_sizes_given_widths_dict.peekitem(0)[0] if\
                self.max_font_sizes_given_widths_dict else float("inf")
        #print(self.max_font_sizes_given_widths_dict)
        #print(res)
        return res
    
    def calculateFontSizeActual(self) -> Tuple[Tuple[Real]]:
        #print("Calling calculateFontSizeActual()")
        #print(self.font_size)
        if self.font_size is not None:# and self.font_size != ():
            return self.font_size
        #print("hello")
        #print(self.max_font_size_given_heights, self.max_font_sizes_given_widths)
        #print(self.max_height0)
        #print(self.max_height)
        return min(self.max_font_size_given_heights, self.max_font_sizes_given_widths)
    
    """
    def setupTextObjects(
        self,
        text_dicts: List[Dict[str, Any]]
    ) -> List[Tuple]:
        #print("Setting up text objects")
        if not self.font_size_set:
            self._font_size = None
        self._text_local_asc_desc_chars = None
        self._text_global_asc_desc_chars = None
        self._asc_desc_sizes_local = None
        self._asc_desc_sizes_global = None
        
        self._text_list = []
        self.text_objects = []
        return self.addTextObjects(text_dicts)
    """
    def replaceTextObjects(self, rm_text_objs: Optional[List["TextGroupElement"]]=None, add_text_dicts: Optional[List[dict]]=None) -> List["Text"]:
        #print(f"Using replaceTextObjects() for {self}")
        #print(f"add_text_dicts = {add_text_dicts}")
        #print(f"rm_text_objs = {rm_text_objs}")
        #print(self.max_font_sizes_given_widths_dict)
        if rm_text_objs is None:
            rm_text_objs = []
        for rm_obj in rm_text_objs:
            self._removeElementFromRecord(rm_obj)
        """
        inds = sorted(text_obj.text_group_idx for text_obj in rm_text_objs)
        for i in reversed(range(len(inds))):
            idx = inds[i]
            if idx == len(self.text_objects) - 1:
                break
            self.text_objects.pop()
            while self.text_objects and self.text_objects[-1] is None:
                self.text_objects.pop()
        else: i = -1
        for i in reversed(range(i + 1)):
            idx = inds[i]
            self.text_objects[idx] = None
            heapq.heappush(self.free_inds_heap, inds[idx])
        """
        rm_font_sizes = {}
        rm_heights = {}
        rm_ad_chars = [[], []]
        for text_obj in rm_text_objs:
            rm_font_size = getattr(text_obj, "_max_font_size_given_width", None)
            if rm_font_size is not None:
                rm_font_sizes[rm_font_size] =\
                        rm_font_sizes.get(rm_font_size, 0) + 1
            max_shape = getattr(text_obj, "_max_shape", None)
            rm_h = max_shape[1] if max_shape else None
            if rm_h is not None and rm_h != float("inf"):
                rm_heights[rm_h] =\
                        rm_heights.get(rm_h, 0) + 1
            rm_ad = text_obj.text_local_asc_desc_chars[self.min_lowercase]
            if rm_ad is not None:
                rm_ad_chars[0].append(rm_ad[0])
                rm_ad_chars[1].append(rm_ad[1])
        #print("hello1")
        if add_text_dicts is None:
            add_text_dicts = []
        res = []
        add_ad_chars = [[], []]
        add_font_sizes = {}
        add_heights = {}
        group_element_cls = type(self).group_element_cls_func()
        grp_attr = group_element_cls.group_obj_attr
        #print("hello2")
        for text_dict in add_text_dicts:
            #print("howdy")
            text_dict.setdefault("text", "")
            max_shape = text_dict.get("max_shape", None)
            text_dict["max_shape"] = None
            """
            if self.free_inds_heap:
                idx = heapq.heappop(self.free_inds_heap)
                if idx >= len(self.text_objects):
                    self.free_inds_heap = []
                    idx = len(self.text_objects)
                    self.text_objects.append(None)
            else:
                idx = len(self.text_objects)
                self.text_objects.append(None)
            """
            #print(text_dict)
            #print("Creating text object in TextGroup")
            #print("hi1")
            #print(f"text_dict = {text_dict}")
            #text_obj = group_element_cls(**text_dict, **{"_from_group": True, grp_attr: self})#TextGroupElement(self, _from_group=True, **text_dict)
            #print("pre _addElement():")
            #print(self.max_font_sizes_given_widths_dict)
            text_obj = self._addElement(_from_group=True, **text_dict)
            #print("post _addElement():")
            #print(self.max_font_sizes_given_widths_dict)
            #print("hi2")
            #text_obj.setMaxWidth(max_width, _update_textgroup_max_font_size_given_width=False)
            #print(f"text_obj._max_shape_actual = {text_obj.__dict__.get('_max_shape_actual', None)}")
            text_obj._max_shape = max_shape
            #print(self.max_font_sizes_given_widths_dict)
            add_font_size = text_obj.max_font_size_given_width
            #print(self.max_font_sizes_given_widths_dict)
            if add_font_size is not None:
                add_font_sizes[add_font_size] = add_font_sizes.get(add_font_size, 0) + 1
            #print(f"max_shape = {max_shape}")
            if max_shape is not None and max_shape[1] is not None and max_shape[1] != float("inf"):
                #print("hi")
                add_heights[max_shape[1]] = add_heights.get(max_shape[1], 0) + 1
            #text_obj._calculateAndcustomMaxFontSizeGivenWidthChangePropogation(max_size=None, _update_textgroup_max_font_size_given_width=False)
            #text_obj._calculateAndSetTextLocalAscDescChars(update_textgroup_asc_desc_chars=False)
            ad_chars = text_obj.text_local_asc_desc_chars[self.min_lowercase]
            #print("hi3")
            if ad_chars is not None:
                add_ad_chars[0].append(ad_chars[0])
                add_ad_chars[1].append(ad_chars[1])
            #print("Using _addElementToRecord() from replaceTextObjects()")
            #self._addElementToRecord(text_obj)
            res.append(text_obj)
            #self.text_objects[idx] = text_obj
        #print("hello3")
        #print(self.max_font_sizes_given_widths_dict)
        self._updateAscDescChars(
            rm_ad_chars[0],
            add_ad_chars[0],
            rm_ad_chars[1],
            add_ad_chars[1]
        )
        #print(f"rm_font_sizes = {rm_font_sizes}")
        #print(f"add_font_sizes = {add_font_sizes}")
        #print("pre _updateMaxFontSizesGivenWidths()")
        #print(self.max_font_sizes_given_widths_dict)
        self._updateMaxFontSizesGivenWidths(
            rm_font_sizes,
            {},#add_font_sizes, # adding was handled when calling text_obj.max_font_size_given_width
            reset_max_font_sizes_given_widths=True,
        )
        #print("post _updateMaxFontSizesGivenWidths()")
        #print(self.max_font_sizes_given_widths_dict)
        self._updateHeights(
            rm_heights,
            add_heights,
        )
        #print(f"Finished using replaceTextObjects() for {self}")
        #print(self.max_font_sizes_given_widths_dict)
        return res
        """
        self._text_list.extend(text_list)
        res = []
        add_ad_chars = [[], []]
        for text_dict in text_list:
            text = text_dict.setdefault("text", "")
            
            text_obj = TextGroupElement(self, len(self.text_objects),\
                    **text_dict)#text, max_width, font_color=font_color)
            text_obj._calculateAndSetTextLocalAscDescChars(update_textgroup_asc_desc_chars=False)
            ad_chars = text_obj.text_local_asc_desc_chars[self.min_lowercase]
            if ad_chars is not None:
                add_ad_chars[0].append(ad_chars[0])
                add_ad_chars[1].append(ad_chars[1])
            res.append((text_obj, len(self.text_objects)))
            self.text_objects.append(text_obj)
        self._updateAscDescChars([], add_ad_chars[0], [], add_ad_chars[1], set_font_size=True)
        return res
        """
    
    def addTextObjects(self, add_text_dicts: List[dict]) -> List[Text]:
        return self.replaceTextObjects(rm_text_objs=[], add_text_dicts=add_text_dicts)
    
    def removeTextObjects(self, rm_text_objs: List["Text"]) -> None:
        return self.replaceTextObjects(rm_text_objs=rm_text_objs)
    
    """
    @staticmethod
    def findTextAscDescChars(font: "pg.freetype",\
            text_list: List[str], min_lowercase: bool=True):
        return findLargestAscentAndDescentCharacters(font, text_list,\
                font_size=100, min_lowercase=min_lowercase)
    """
    
    """
    def setFont(self, font: "pg.freetype") -> None:
        self._font = font
        self._text_global_asc_desc_chars = None
        self._asc_desc_sizes_local = None
        self._asc_desc_sizes_global = None
        self._asc_char_dict = SortedDict()
        self._desc_char_dict = SortedDict()
        self._asc_char_h100 = {}
        self._desc_char_h100 = {}
        for text_obj in getattr(self, "text_objects", []):
            text_obj.font = font
            return
        if not font_size_set:
            self.calculateAndSetFontSize()
        return
    """
    
    
    
    
