#!/usr/bin/env python

import bisect
import copy
import functools
import os
import sys

from typing import Union, Tuple, List, Set, Dict, Optional, Callable, Any, Generator

import pygame as pg
import pygame.freetype
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
    K_RETURN,
    K_KP_ENTER,
)

from pygame_display_component_classes.config import (
    enter_keys_def_glob,
    navkeys_def_glob,
    mouse_lclicks,
    named_colors_def,
    font_def_func,
)
from pygame_display_component_classes.utils import Real, ColorOpacity

from pygame_display_component_classes.display_base_classes import (
    InteractiveDisplayComponentBase,
    ComponentGroupBaseClass,
    ComponentGroupElementBaseClass,
    checkHiddenKwargs,
)
from pygame_display_component_classes.user_input_processing import UserInputProcessor, checkEvents, checkKeysPressed, getMouseStatus, createNavkeyDict
from pygame_display_component_classes.text_manager import Text, TextGroup

from pygame_display_component_classes.font_size_calculators import getCharAscent, getCharDescent, findLargestAscentAndDescentCharacters, findMaxAscentDescentGivenMaxCharacters, findMaxFontSizeGivenDimensions
from pygame_display_component_classes.position_offset_calculators import topLeftAnchorOffset, topLeftFromAnchorPosition

mouse_lclicks_set = mouse_lclicks[0].union(mouse_lclicks[1])

def simplifyReferences(tup: Tuple[Union[int, Tuple[Any]]]) -> Tuple[Union[int, Tuple[Any]]]:
    n = len(tup)
    res = list(tup)
    remain = set(range(n))
    def recur(idx: int) -> None:
        remain.remove(idx)
        if res[idx] is None or not isinstance(res[idx], int):
            return
        if res[idx] in remain:
            recur(res[idx])
        idx2 = res[idx]
        if isinstance(res[idx2], int) or res[idx2] is None:
            res[idx] = res[idx2]
        return
    
    while remain:
        recur(next(iter(remain)))
    return tuple(res)

def createSingleStateReferenceStructure(val: Any, n_states: int) -> Tuple[Union[int, Tuple[Any]]]:
    return tuple([(val,)] + [0] * (n_states - 1))

def processReferenceStructure(val: Union[Any, Tuple[Union[int, Tuple[Any]]]], n_states: int) -> Tuple[Union[int, Tuple[Any]]]:
    if not isinstance(val, tuple) or len(val) != n_states or any(not isinstance(x, (int, tuple)) and x is not None for x in val):
        return createSingleStateReferenceStructure(val, n_states)
    return simplifyReferences(val)

def getProperties(obj: Any, attr_list: List[str], idx: int)\
        -> Optional[Union[int, Tuple[Optional[Tuple[Any]]]]]:
    #print("using getProperties()")
    #print(attr_list)
    res = []
    ind_set = set()
    all_inds = True
    for attr in attr_list:
        idx2 = idx
        val = getattr(obj, attr, None)
        #print(attr, val)
        if val is None or val[idx2] is None:
            return None
        elif isinstance(val[idx2], int):
            idx2 = val[idx2]
            ind_set.add(idx2)
        else: all_inds = False
        res.append(val[idx2])
    return next(iter(ind_set)) if all_inds and len(ind_set) == 1 else tuple(res)

def getTextMaxShape(shape: Tuple[Real],\
        text_borders_rel: Tuple[Real]) -> Tuple[Real]:
    text_shape_rel = [1 - 2 * x for x in text_borders_rel]
    return tuple(x * y for x, y in zip(shape, text_shape_rel))

class Button(InteractiveDisplayComponentBase):
    button_names = set()
    unnamed_count = 0
    
    reset_graph_edges = {
        "shape": {"text_shapes": True, "text_anchor_rel_positions": True, "fill_img_constructors": True, "outline_img_constructors": True},
        "text_borders_rel": {"text_shapes": True, "text_anchor_rel_positions": True},
        "text_anchor_types": {"text_img_constructors": True},
        "text_anchor_rel_positions": {"text_img_constructors": True},
        "outline_widths": {"outline_img_constructors": True},
        "text_objects": {"text_img_constructors": True},
        
        "font_colors": {"text_img_constructors": True},
        "fill_colors": {"fill_img_constructors": True},
        "outline_colors": {"outline_img_constructors": True},

        "fill_img_constructors": {"button_surfs": True},
        "text_img_constructors": {"button_surfs": True},
        "outline_img_constructors": {"button_surfs": True},

        "state": {"display_surf": True},
        
        "button_surfs": {"display_surf": True},#, "button_img_constructors": True},
        
        "mouse_enabled": {"mouse_enablement": True},
    }
    
    
    custom_attribute_change_propogation_methods = {
        "text": "customButtonTextChangePropogation",
        "text_shapes": "customTextShapesChangePropogation",
        #"text_anchor_rel_positions": "setTextAnchorPositions",
        #"text_objects": "setTextObjects",
    }
    
    attribute_calculation_methods = {
        "mouse_enablement": "calculateMouseEnablement",
        "text_shapes": "calculateTextShapes",
        "text_anchor_rel_positions": "calculateTextAnchorPositions",
        
        "button_surfs": "createButtonSurfaces",
        
        "fill_img_constructors": "createFillImageConstructors",
        "text_img_constructors": "createTextImageConstructors",
        "outline_img_constructors": "createOutlineImageConstructors",
        
        #"button_img_constructors": "createButtonImageConstructors",
    }
    
    attribute_default_functions = {
        "state": ((lambda obj: 0),),

        #"text_groups": ((lambda obj: [TextGroup.createDefaultTextGroup()] + [0] * (obj.n_state - 1)), ("n_state",)),
        "text_objects": ((lambda obj: obj.createTextObjects()), ("n_state",)),
        "text_borders_rel": ((lambda obj: tuple([(0.2, 0.2)] + [0] * (obj.n_state - 1))), ("n_state",)),
        "text_anchor_types": ((lambda obj: tuple([("center",)] + [0] * (obj.n_state - 1))), ("n_state",)),
        "outline_widths": ((lambda obj: tuple([(1,)] + [0] * (obj.n_state - 1))), ("n_state",)),
        
        "font_colors": ((lambda obj: tuple([(named_colors_def["white"], 1)] + [0] * (obj.n_state - 1))), ("n_state",)),
        "fill_colors": ((lambda obj: tuple([(named_colors_def["white"], 0)] + [0] * (obj.n_state - 1))), ("n_state",)),
        "outline_colors": ((lambda obj: tuple([(named_colors_def["black"], 1)] + [0] * (obj.n_state - 1))), ("n_state",)),
        
        "mouse_enabled": ((lambda obj: True),),
    }
    
    fixed_attributes = set()
    
    attribute_processing = {
        "text": lambda val, obj: processReferenceStructure(val, obj.n_state),
        #"text_objects": simplifyReferences,
        "text_borders_rel": lambda val, obj: processReferenceStructure(val, obj.n_state),
        "text_anchor_types": lambda val, obj: processReferenceStructure(val, obj.n_state),
        "outline_widths": lambda val, obj: processReferenceStructure(val, obj.n_state),
        "font_colors": lambda val, obj: processReferenceStructure(val, obj.n_state),
        "fill_colors": lambda val, obj: processReferenceStructure(val, obj.n_state),
        "outline_colors": lambda val, obj: processReferenceStructure(val, obj.n_state),
    }
    
    
    n_state = 4
    
    #button_img_lst = ["button_surfs", "button_img_constructors"]
    #change_reset_attrs = {"shape": ["text_anchor_rel_positions", "text_img_constructors", *button_img_lst], "text_nonspatial": ["text_img_constructors", *button_img_lst], "text_spatial": ["text_anchor_rel_positions", "text_img_constructors", *button_img_lst], "fill": ["fill_img_constructors", *button_img_lst], "outline": ["outline_img_constructors", *button_img_lst]}
    
    #displ_attrs = ["button"]#("background_imgs", "outline_imgs", "text_imgs")
    button_img_component_attrs = ["fill_img", "text_img", "outline_img"]
    #sub_displ_attrs = tupl,e(f"_{attr}" for attr in displ_attrs)
    
    def __init__(
        self,
        shape: Tuple[Real],
        text: Tuple[Union[Tuple[str], int]],
        anchor_rel_pos: Tuple[Real],
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        text_objects: Tuple[Union[Optional["Text"], int]]=None,
        font_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        text_borders_rel: Optional[Tuple[Union[Optional[Tuple[Real]], int]]]=None,
        text_anchor_types: Optional[Tuple[Union[Optional[Tuple[str]], int]]]=None,
        fill_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        outline_widths: Optional[Tuple[Union[Real, int]]]=None,
        outline_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        mouse_enabled: Optional[bool]=None,
        name: Optional[str]=None,
        **kwargs,
    ):
        
        checkHiddenKwargs(type(self), kwargs)
        if name is None:
            Button.unnamed_count += 1
            name = f"button {self.unnamed_count}"
        #self.name = name
        Button.button_names.add(name)
        super().__init__(**self.initArgsManagement(locals(), kwargs=kwargs))
        """
        super().__init__(shape, anchor_rel_pos, anchor_type=anchor_type,\
            screen_topleft_to_parent_topleft_offset=screen_topleft_to_parent_topleft_offset)
        
        self.state = 0
        #self._shape = shape
        #self._anchor_rel_pos = anchor_rel_pos
        #self._anchor_type = anchor_type
        self._text_borders_rel = tuple([(0.2, 0.2)] + [0] * (self.n_state - 1)) if text_borders_rel is None else text_borders_rel
        self._text_anchor_types = tuple([("center",)] + [0] * (self.n_state - 1)) if text_anchor_types is None else text_anchor_types
        self._screen_topleft_to_parent_topleft_offset = screen_topleft_to_parent_topleft_offset
        #print(f"self.text_anchor_types = {self.text_anchor_types}")
        
        self.text_objects = text_objects
        
        self.outline_widths = tuple([(1,)] + [0] * (self.n_state - 1)) if outline_widths is None else outline_widths
        
        self.font_colors = tuple([(named_colors_def["white"], 1)] + [0] * (self.n_state - 1)) if font_colors is None else font_colors
        self.fill_colors = tuple([(named_colors_def["white"], 0)] + [0] * (self.n_state - 1)) if fill_colors is None else fill_colors
        self.outline_colors = tuple([(named_colors_def["black"], 1)] + [0] * (self.n_state - 1)) if outline_colors is None else outline_colors
        
        self.mouse_enabled = mouse_enabled
        
        if name is None:
            Button.unnamed_count += 1
            name = f"button {self.unnamed_count}"
        self.name = name
        Button.button_names.add(name)
        """
    
    
    
    def calculateMouseEnablement(self) -> None:
        #print("calculating mouse enablement")
        mouse_enabled = self.mouse_enabled
        return (mouse_enabled, False, mouse_enabled)

    def createTextObjects(self) -> None:
        res = []
        for _ in range(self.n_state):
            res.append((Text(
                max_shape=(None, None),
                text="lorem",
                _from_container=True,
                _container_obj=self,
                _container_attr_reset_dict={"updated": {"text_img_constructors": (lambda container_obj, obj: getattr(obj, "updated", False))}},
            ),))
        #print(res)
        return res
    
    def setTextObjectsUpdates(
        self,
        text_objs: Tuple[Union[int, Optional["Text"]]],
    ) -> None:
        for text_obj_tup in text_objs:
            if isinstance(text_obj_tup, int) or text_obj_tup is None:
                continue
            text_obj_tup[0]._attr_reset_funcs = {"updated": [lambda obj, prev_val: setattr(obj, "button_surfs", None)]}
        return
    
    def setTextObjects(self, prev_val: Tuple[Union[int, Optional["Text"]]]) -> None:
        return self.setTextObjectsUpdates(self.text_objects)
    
    def customButtonTextChangePropogation(self, new_val: Tuple[Union[int, Tuple[str]]], prev_val: Tuple[Union[int, Tuple[str]]]) -> None:
        #print(f"Using customButtonTextChangePropogation() with new_val = {new_val}, prev_val = {prev_val}")
        #print(self.text, len(self.text))
        #print(self.text_objects, len(self.text_objects))
        for idx, s_tup in enumerate(new_val):
            if isinstance(s_tup, int): s_tup = self.text[s_tup]
            self.text_objects[idx][0].text = s_tup[0]
        return

    """
    def _shapeCustomUpdate(self, change: bool=True) -> None:
        if change: self.calculateAndSetTextMaxShapes()
        return
    
    @property
    def fill_colors(self):
        return self._fill_colors
    
    @fill_colors.setter
    def fill_colors(self, fill_colors):
        fill_colors = simplifyReferences(fill_colors)
        self.setAttribute("fill_colors", fill_colors, "_fillColorsCustomUpdate", reset_type="fill", replace_attr=True)
        return
        #if fill_colors == getattr(self, "_fill_colors", None):
        #    return
        #self.setFillColors(fill_colors)
        #return
    
    @property
    def outline_colors(self):
        return self._outline_colors
    
    @outline_colors.setter
    def outline_colors(self, outline_colors):
        outline_colors = simplifyReferences(outline_colors)
        self.setAttribute("outline_colors", outline_colors, "_outlineColorsCustomUpdate", reset_type="outline", replace_attr=True)
        return
    
    @property
    def outline_widths(self):
        return self._outline_widths
    
    @outline_widths.setter
    def outline_widths(self, outline_widths):
        outline_widths = simplifyReferences(outline_widths)
        self.setAttribute("outline_widths", outline_widths, "_outlineWidthsCustomUpdate", reset_type="outline", replace_attr=True)
        return
    
    #def setFillColors(self, fill_colors: Tuple[Union[Optional[Tuple[Tuple[int], float]], int]]) -> None:
    #    self._fill_colors = fill_colors
    #    return
    
    @property
    def font_colors(self):
        return self._font_colors
    
    @font_colors.setter
    def font_colors(self, font_colors):
        font_colors = simplifyReferences(font_colors)
        self.setAttribute("font_colors", font_colors, "_fontColorsCustomUpdate", reset_type="text_nonspatial", replace_attr=True)
        return
        #if font_colors == getattr(self, "_font_colors", None):
        #    return
        #self.setFontColors(font_colors)
        #return
    
    #def setFontColors(self, font_colors: Tuple[Union[Optional[Tuple[Tuple[int], float]], int]]) -> None:
    #    self._font_colors = font_colors
    #    return
    
    @property
    def text_borders_rel(self):
        return self._text_borders_rel
    
    @text_borders_rel.setter
    def text_borders_rel(self, text_borders_rel):
        text_borders_rel = simplifyReferences(text_borders_rel)
        self.setAttribute("text_borders_rel", text_borders_rel, "_textBordersRelativeCustomUpdate", reset_type="text_spatial", replace_attr=True)
        return
        #if text_borders_rel == getattr(self, "_text_borders_rel", None):
        #    return
        #self._text_borders_rel = text_borders_rel
        #self.calculateAndSetTextMaxShapes()
        #self._button_surfs = None
        #return
    
    def _textBordersRelativeCustomUpdate(self, change: bool=True) -> None:
        if change: self.calculateAndSetTextMaxShapes()
        return
    
    @property
    def text_anchor_types(self):
        return self._text_anchor_types
    
    @text_anchor_types.setter
    def text_anchor_types(self, text_anchor_types):
        text_anchor_types = simplifyReferences(text_anchor_types)
        self.setAttribute("text_anchor_types", text_anchor_types, "_textAnchorTypesCustomUpdate", reset_type="text_spatial", replace_attr=True)
        return
        #if text_anchor_types == getattr(self, "_text_anchor_types", None):
        #    return
        #self._text_anchor_types = text_anchor_types
        #self.resetAttributes("text_anchors")
        #return
    
    @property
    def text_max_shapes(self):
        res = getattr(self, "_text_max_shapes", None)
        if res is None:
            res = self.calculateAndSetTextMaxShapes()
        return res
    """
    def calculateTextShapes(
        self,
        shape: Optional[Tuple[Real]]=None,
    ) -> None:
        #print("Using calculateTextShapes()")
        if shape is None:
            shape = self.shape
        res = []
        for i in range(self.n_state):
            props = getProperties(self, ["text_objects", "text_borders_rel"], i)
            if props is None:
                res.append(None)
                if self.text_objects[i] is not None:
                    raise ValueError("An element of attribute text_borders_rel "
                            "may only be None if the corresponding element of "
                            "attribute text_objects is also None")
                continue
            elif isinstance(props, int):
                res.append(props)
                continue
            text_object_tup, text_borders_rel = props
            text_shape = getTextMaxShape(self.shape, text_borders_rel)
            res.append(text_shape)
        #print(f"calculated text shapes = {res}")
        return res
    
    def customTextShapesChangePropogation(
        self,
        new_val: Optional[Tuple[Real]],
        prev_val: Optional[Tuple[Real]],
    ) -> None:
        #print("using customTextShapesChangePropogation()")
        text_objs = self.text_objects
        text_shapes = new_val#self.text_shapes
        for text_obj_tup, text_shape in zip(text_objs, text_shapes):
            if text_obj_tup is None or isinstance(text_obj_tup, int):
                continue
            if isinstance(text_shape, int):
                text_shape = text_shapes[text_shape]
            #print(f"setting text object max shape to {text_shape}")
            text_obj_tup[0].max_shape = text_shape
        return
    """
    @property
    def text_anchor_rel_positions(self):
        res = getattr(self, "_text_anchor_rel_positions", None)
        if res is None:
            res = self.calculateAndSetTextAnchorPositions()
        return res
    """
    def calculateTextAnchorPositions(
        self
    ) -> Tuple[Union[int, Tuple[Real, Real]]]:
        #print("Using calculateTextAnchorPositions()")
        shape = self.shape
        res = []
        for i in range(self.n_state):
            props = getProperties(self, ["text_shapes", "text_borders_rel", "text_anchor_types"], i)
            if props is None or isinstance(props, int):
                res.append(props)
                continue
            text_max_shape, text_borders_rel,\
                    text_anchor_type_tup = props
            text_anchor_rel_pos = self._calculateTextAnchorPosition(
                text_max_shape=text_max_shape,
                topleft_pos=(0, 0),
                text_anchor_type=text_anchor_type_tup[0],
                shape=shape,
                text_borders_rel=text_borders_rel,
            )
            res.append(text_anchor_rel_pos)
        return tuple(res)
    
    @staticmethod
    def _calculateTextAnchorPosition(
        text_max_shape: Tuple[Real],
        topleft_pos: Tuple[Real],
        text_anchor_type: str,
        shape: Tuple[Real],
        text_borders_rel: Tuple[Real],
    ) -> Tuple[Real]:
        text_topleft = tuple(x + y * z for x, y, z in\
                zip(topleft_pos, shape, text_borders_rel))
        #print(text_max_shape, text_anchor_type)
        anchor_offset = topLeftAnchorOffset(text_max_shape, text_anchor_type)
        text_anchor_rel_pos = tuple(x + y for x, y in zip(text_topleft, anchor_offset))
        return text_anchor_rel_pos
    
    """
    def setTextAnchorPositions(
        self,
        prev_val: Optional[Tuple[Real]],
    ) -> None:
        for text_obj_tup, text_anchor_rel_pos in zip(self.text_objects, self.text_anchor_rel_positions):
            if text_obj_tup is None or isinstance(text_obj_tup, int):
                continue
            if isinstance(text_anchor_rel_pos, int):
                text_anchor_rel_pos = self.text_anchor_rel_positions[text_anchor_rel_pos]
            text_obj_tup.anchor_rel_pos0 = text_anchor_rel_pos
        return
    """
    """
    def calculateAndSetTextAnchorPositions(self) -> None:
        #print("running calculateAndSetTextAnchorPositions()")
        shape = self.shape
        res = []
        for i in range(self.n_state):
            props = getProperties(self, ["text_max_shapes", "text_borders_rel", "text_anchor_types"], i)
            if props is None or isinstance(props, int):
                res.append(props)
                continue
            text_max_shape, text_borders_rel,\
                    text_anchor_type_tup = props
            text_anchor_rel_pos = self.calculateTextAnchorPosition(\
                    text_max_shape, (0, 0),\
                    text_anchor_type_tup[0], shape, text_borders_rel)
            res.append(text_anchor_rel_pos)
        res = tuple(res)
        self._text_anchor_rel_positions = res
        return res
    """
    """
    @property
    def text_objects(self):
        return self._text_objects
    
    @text_objects.setter
    def text_objects(self, text_objects):
        text_objects = simplifyReferences(text_objects)
        self.setAttribute("text_objects", text_objects, "_textObjectsCustomUpdate", reset_type="text_spatial", replace_attr=True)
        return
        #if text_objects == getattr(self, "_text_objects", None):
        #    return
        #self._text_objects = text_objects
        #self.calculateAndSetTextMaxShapes()
        #self.resetAttributes("text_shapes")
        #return
    
    def _textObjectsCustomUpdate(self, change: bool=True) -> None:
        if change: self.calculateAndSetTextMaxShapes()
        return
    
    @property
    def fill_surfs(self):
        #print("getting fill_surfs")
        res = getattr(self, "_fill_surfs", None)
        if res is None:
            res = self.createFillSurfaces()
            self._fill_surf = res
        return res
    
    def createFillSurfaces(self):
        #print("running createFillSurface()")
        return tuple([(pg.Surface(self.shape, pg.SRCALPHA),)] + [0] * (self.n_state - 1))
    
    @property
    def fill_img_constructors(self):
        res = getattr(self, "_fill_img_constructors", None)
        if res is None:
            res = self.createFillImageConstructors()
            self._fill_img_constructors = res
        return res
    """
    def createFillImageConstructors(self) -> Callable[[], None]:
        #print("running createFillImageConstructors")
        res = []
        #shape = self.shape
        def fillImageConstructor(surf: "pg.Surface",\
                fill_color: ColorOpacity=()) -> None:
            fill_surf = pg.Surface(self.shape, pg.SRCALPHA)
            #print(f"opacity = {fill_color[1] * 255}")
            #print(fill_color)
            fill_surf.set_alpha(fill_color[1] * 255)
            fill_surf.fill(fill_color[0])
            surf.blit(fill_surf, (0, 0))
            return
        #print("hi")
        #print(self.fill_surfs)
        #print(self.fill_colors)
        for i in range(self.n_state):
            props = getProperties(self, ["fill_colors"],\
                    i)
            #print(f"props = {props}")
            if props is None or isinstance(props, int):
                res.append(props)
                continue
            fill_color = props[0]
            res.append((functools.partial(fillImageConstructor,\
                    fill_color=fill_color),))
        return tuple(res)
    
        #return lambda surf: surf.blit(self.fill_surf, (0, 0))
    """
    @property
    def outline_img_constructors(self):
        #print("getting outline_img_constructors")
        res = getattr(self, "_outline_img_constructors", None)
        #print(res)
        if res is None:
            res = self.createOutlineImageConstructors()
            self._outline_img_constructors = res
        return res
    """
    def createOutlineImageConstructors(self):
        #print("running createOutlineImageConstructors")
        res = []
        #shape = self.shape
        def outlineImageConstructor(surf: "pg.Surface",\
                outline_color: ColorOpacity=(),\
                outline_width: int=1) -> None:
            outline_surf = pg.Surface(self.shape, pg.SRCALPHA)
            pg.draw.rect(outline_surf, outline_color[0], (0, 0, *self.shape), outline_width)
            #print(f"opacity = {fill_color[1] * 255}")
            outline_surf.set_alpha(outline_color[1] * 255)
            surf.blit(outline_surf, (0, 0))
            return
        #print("hi")
        #print(self.fill_surfs)
        #print(self.fill_colors)
        for i in range(self.n_state):
            props = getProperties(self,\
                    ["outline_colors", "outline_widths"], i)
            #print(f"props = {props}")
            if props is None or isinstance(props, int):
                res.append(props)
                continue
            outline_color, outline_width_tup = props
            #print(outline_width_tup)
            res.append((functools.partial(outlineImageConstructor,\
                    outline_color=outline_color,\
                    outline_width=outline_width_tup[0]),))
        return tuple(res)
        
        """
        #print("running createOutlineImageConstructors")
        res = []
        dims = (0, 0, *self.shape)
        def outlineImageConstructor(surf: "pg.Surface",\
                outline_color: Tuple[Union[Tuple[int], Real]]=(),\
                width: Real=1)\
                -> None:
            pg.draw.rect(surf, outline_color[0], dims, width)
            return
        #print("hi")
        #print(self.outline_colors)
        #print(self.outline_widths)
        for i in range(self.n_state):
            props = getProperties(self, ["outline_colors", "outline_widths"], i)
            if props is None or isinstance(props, int):
                res.append(props)
                continue
            outline_color, width_tup = props
            res.append((functools.partial(outlineImageConstructor,\
                    outline_color=outline_color, width=width_tup[0]),))
        return tuple(res)
        """
    """
    @property
    def text_img_constructors(self):
        #print("getting text_img_constructors")
        res = getattr(self, "_text_img_constructors", None)
        if res is None:
            res = self.createTextImageConstructors()
            self._text_img_constructors = res
        return res
    """
    def createTextImageConstructors(self):
        #print("creating text image constructors")
        res = []
        def textImageConstructor(surf: "pg.Surface", text_obj: "Text",\
                text_anchor_rel_pos: Tuple[int]=(0, 0),\
                text_anchor_type: str="topleft",\
                font_color: ColorOpacity=((0, 0, 0), 1))\
                -> None:
            #print("hello")
            #print(surf, text_obj, text_anchor_rel_pos, text_anchor_type, font_color)
            text_obj.font_color = font_color
            text_obj.draw(surf, anchor_rel_pos=text_anchor_rel_pos, anchor_type=text_anchor_type)
            #print("hello2")
            return
        #for attr in ["text_objects", "text_anchor_rel_positions", "text_anchor_types", "font_colors"]:
        #    print(attr, getattr(self, attr, None))
        for i in range(self.n_state):
            props = getProperties(self, ["text_objects", "text_anchor_rel_positions", "text_anchor_types", "font_colors"], i)
            if props is None or isinstance(props, int):
                res.append(props)
                continue
            text_obj_tup, text_anchor_rel_pos, text_anchor_type_tup, font_color = props
            res.append((functools.partial(textImageConstructor,\
                    text_obj=text_obj_tup[0], text_anchor_rel_pos=text_anchor_rel_pos,\
                    text_anchor_type=text_anchor_type_tup[0],\
                    font_color=font_color),))
        #print(res)
        return tuple(res)
    """
    @property
    def button_surfs(self):
        res = getattr(self, "_button_surfs", None)
        if res is None:
            #print("hi")
            res = self.createButtonSurfaces()
            #print(f"button_surfs = {res}")
            self._button_surfs = res
        return res
    """
    def createButtonSurfaces(self) -> Tuple[Union[None, int, "pg.Surface"]]:
        res = []
        #def buttonImageConstructor(surf: "pg.Surface",\
        #        button_surf: Optional["pg.Surface"]=None)\
        #        -> None:
        #    surf.blit(button_surf, (0, 0))
        #    return
        constructors = [f"{attr}_constructors"\
                for attr in self.button_img_component_attrs]
        #for constructor in constructors:
        #    print(constructor)
        #    print(f"{constructor} = {getattr(self, constructor, None)}")
        for i in range(self.n_state):
            funcs = []
            none_seen = False
            funcs_seen = False
            inds = set()
            for nm in constructors:
                #if nm.startswith("text"): continue
                #print(constructor)
                constr_funcs = getattr(self, nm, None)
                #print(tup)
                if constr_funcs is None: continue
                else: func_tup = constr_funcs[i]
                #print(f"func_tup pre = {func_tup}")
                if isinstance(func_tup, int):
                    inds.add(func_tup)
                    func_tup = constr_funcs[func_tup]
                if func_tup is None:
                    none_seen = True
                    continue
                else: funcs_seen = True
                #print(f"func_tup post = {func_tup}")
                funcs.append(func_tup[0])
            #print(f"funcs = {funcs}")
            if not funcs: res.append(None)
            elif not none_seen and not funcs_seen and len(inds) == 1:
                res.append(next(iter(inds)))
            else:
                surf = pg.Surface(self.shape, pg.SRCALPHA)
                #print(funcs)
                for func in funcs:
                    #print(func)
                    func(surf)
                res.append((surf,))
            """
            props = getProperties(self, constructors, i)
            if props is None or isinstance(props, int):
                res.append(props)
                continue
            print("howdy")
            surf = pg.Surface(self.shape)#, pygame.SRCALPHA)
            for constructor_tup in props:
                constructor_tup[0](surf)
            res.append(surf)
            """
        return tuple(res)
        #tuple(pg.Surface(self.shape, pygame.SRCALPHA) for _ in range(self.n_state))
    """
    @property
    def button_img_constructors(self):
        #print("hello")
        res = getattr(self, "_button_img_constructors", None)
        if res is None:
            res = self.createButtonImageConstructors()
            #print(f"res = {res}")
            self._button_img_constructors = res
        return res
    
    def createButtonImageConstructors(self) -> Callable[["pg.Surface"], None]:
        res = []
        def buttonImageConstructor(surf: "pg.Surface",\
                button_surf: Optional["pg.Surface"]=None)\
                -> None:
            surf.blit(button_surf, self.topleft_rel_pos)
            return
        for i in range(self.n_state):
            props = getProperties(self, ["button_surfs"], i)
            #print(f"props = {props}")
            if props is None or isinstance(props, int):
                res.append(props)
                continue
            button_surf_tup = props[0]
            res.append((functools.partial(buttonImageConstructor,\
                    button_surf=button_surf_tup[0]),))
        return tuple(res)
    """
    def createDisplaySurface(self) -> Optional["pg.Surface"]:
        idx = self.state
        button_surfs = self.button_surfs
        if isinstance(button_surfs[idx], int):
            idx = button_surfs[idx]
        return button_surfs[idx][0]
    """
    def draw(self, surf: "pg.Surface"):
        idx = self.state
        button_img_constructors = self.button_img_constructors
        if isinstance(button_img_constructors[idx], int):
            idx = button_img_constructors[idx]
        if button_img_constructors[idx] is None:
            return
        self.button_img_constructors[idx][0](surf)
        return
        ""
        idx = self.state
        for displ_attr in self.displ_attrs:
            attr = f"{displ_attr}_img_constructors"
            img_constructors = getattr(self, attr, None)
            if img_constructors is None:
                raise ValueError(f"Attribute {attr} not found")
            img_constructor_tup = img_constructors[idx]
            if img_constructor_tup is None: continue
            if isinstance(img_constructor_tup, int):
                img_constructor_tup = img_constructors[img_constructor_tup]
            img_constructor_tup[0](surf)
        return
        ""
    """
    """
    def getRequiredInputs(self) -> Tuple[Union[bool, Dict[str, Union[List[int], Tuple[Union[Tuple[int], int]]]]]]:
        quit, esc_pressed, events = self.user_input_processor.getEvents()
        return quit, not esc_pressed, {"events": events,\
                "keys_down": self.user_input_processor.getKeysHeldDown(),\
                "mouse_status": self.user_input_processor.getMouseStatus()}
    
    def mouseOverButton(self, mouse_pos: Optional[Tuple]=None, check_axes: Tuple[int]=(0, 1)) -> bool:
        if not self.mouse_enabled: return False
        if mouse_pos is None:
            if not pg.mouse.get_focused():
                return False
            mouse_pos = pg.mouse.get_pos()
        
        ranges = self.ranges_screen
        for i in check_axes:
            x, rng = mouse_pos[i], ranges[i]
            if x < rng[0] or x > rng[1]:
                return False
        return True
    """
    """
    def processEvents(self, events: List[Tuple[int]]) -> List[Tuple[int]]:
        res = []
        for event_tup in events:
            if event_tup[1] == 3 and event_tup[0].button == 1:
                res.append(event_tup[0].pos)
        return res
    
    def eventLoop(self, events: Optional[List[int]]=None,\
            keys_down: Optional[List[int]]=None,\
            mouse_status: Optional[Tuple[int]]=None,\
            check_axes: Tuple[int]=(0, 1))\
            -> Tuple[Union[bool, Tuple[bool]]]:
        quit = False
        running = True
        screen_changed = False
        selected = False
        prev_state = self.state
        
        if events is None:
            quit, esc_pressed, events = user_input_processor.getEvents()
            if esc_pressed:
                running = False
        for pos in self.processEvents(events):
            if self.mouseOverSurface(pos, check_axes=check_axes):
                selected = True
                break
        
        if mouse_status is None:
            mouse_status = user_input_processor.getMouseStatus() if self.mouse_enablement[0] else ()
        mouse_over = self.mouseOverSurface(mouse_status[0], check_axes=check_axes) if mouse_status else False
        self.state = 2 + mouse_status[1][0] if mouse_over else 0
        return quit, running, (self.state != prev_state, selected)
    """
    def processEvents(self, events: List[Tuple[int]]) -> List[Tuple[int]]:
        res = []
        for event_tup in events:
            if event_tup[1] == 3 and event_tup[0].button == 1:
                res.append((event_tup[0].pos, event_tup[1]))
        return res
    
    def eventLoop(
        self,
        events: Optional[List[int]]=None,
        keys_down: Optional[List[int]]=None,
        mouse_status: Optional[Tuple[int]]=None,
        check_axes: Tuple[int]=(0, 1),
    ) -> Tuple[bool, bool, bool, Any]:
        #print("calling Slider eventLoop()")
        #print(events)
        ((quit, esc_pressed), (events, keys_down, mouse_status, check_axes)) = self.getEventLoopArguments(events=events, keys_down=keys_down, mouse_status=mouse_status, check_axes=check_axes)
        running = not quit and not esc_pressed
        prev_state = self.state
        selected = False
        
        for event_tup in self.processEvents(events):
            if event_tup[1] != 3:
                continue
            if self.mouseOverSurface(event_tup[0], check_axes=check_axes):
                selected = True
                break
        
        mouse_over = self.mouseOverSurface(mouse_status[0], check_axes=check_axes) if mouse_status else False
        self.state = 2 + mouse_status[1][0] if mouse_over else 0
        screen_changed = self.drawUpdateRequired()
        #screen_changed = True
        #print(f"screen_changed = {screen_changed}")
        return quit, running, screen_changed, selected

class ButtonGroupElement(ComponentGroupElementBaseClass, Button):
    
    group_cls_func = lambda: ButtonGroup
    group_obj_attr = "button_group"
    #fixed_attributes = {group_obj_attr}
    
    
    #reset_graph_edges = {
    #    "text": {"text_objects": True},
    #}
    
    
    def __init__(
        self,
        button_group: "ButtonGroup",
        text: Tuple[Union[Tuple[str], int]],
        #text_objects=text_objects,
        anchor_rel_pos: Tuple[Real],
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        text_anchor_types: Optional[Tuple[Union[Optional[Tuple[str]], int]]]=None,
        mouse_enabled: Optional[bool]=None,
        name: Optional[str]=None,

        #text: str,
        #anchor_rel_pos: Tuple[Real],
        #anchor_type: Optional[str]=None,
        #screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        #font_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        #fill_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        #outline_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        #name: Optional[str]=None,
        **kwargs,
    ) -> None:
        
        checkHiddenKwargs(type(self), kwargs)

        #text_objects = button_group.createTextObjects()#button_group.text_groups)
        
        #self.__dict__[f"_{self.group_obj_attr}"] = slider_group
        super().__init__(
            shape=button_group.button_shape,
            text=text,
            anchor_rel_pos=anchor_rel_pos,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=screen_topleft_to_parent_topleft_offset,
            text_objects=None,
            font_colors=button_group.font_colors,
            text_borders_rel=button_group.text_borders_rel,
            text_anchor_types=text_anchor_types,
            fill_colors=button_group.fill_colors,
            outline_widths=button_group.outline_widths,
            outline_colors=button_group.outline_colors,
            mouse_enabled=mouse_enabled,
            name=name,
            _group=button_group,
            **kwargs,
        )
    
    def createTextObjects(self) -> None:
        #print("Using ButtonGroupElement method createTextObjects()")
        add_text_dict_lsts = {}
        #print(self.button_group.text_groups)
        for idx, text_group_tup in enumerate(self.button_group.text_groups):
            if text_group_tup is None: continue
            elif isinstance(text_group_tup, int):
                text_group_tup = self.button_group.text_groups[text_group_tup]
            add_text_dict_lsts.setdefault(text_group_tup[0], [[], []])
            # Review- setting max_shape to a specific value should not make any difference
            # as it will be replaced, but it seems to limit the size
            add_text_dict_lsts[text_group_tup[0]][0].append(
                {
                    "max_shape": (200, None),
                    "text": "lorem",
                    "_from_container": True,
                    "_container_obj": self,
                    "_container_attr_reset_dict": {"updated": {"text_img_constructors": (lambda container_obj, obj: getattr(obj, "updated", False))}},
                }
            )
            add_text_dict_lsts[text_group_tup[0]][1].append(idx)
        #print(add_text_dict_lsts)
        res = [None] * self.n_state
        for grp, (add_text_dict_lst, idx_lst) in add_text_dict_lsts.items():
            #print(f"adding text objects for {grp}")
            text_objs = grp.addTextObjects(add_text_dict_lst)
            #print(f"finished adding text objects for {grp}")
            #print(grp.max_font_sizes_given_widths_dict)
            #print(grp.heights_dict)
            for text_obj, idx in zip(text_objs, idx_lst):
                res[idx] = (text_obj,)
        return res
    
class ButtonGroup(ComponentGroupBaseClass):
    group_element_cls_func = lambda: ButtonGroupElement

    n_state = group_element_cls_func().n_state
    
    button_group_names = set()
    unnamed_count = 0

    reset_graph_edges = {}

    #component_dim_determiners = ["shape", "demarc_numbers_max_height_rel", "thumb_radius_rel", "demarc_line_lens_rel"]
    #for attr in component_dim_determiners:
    #    reset_graph_edges.setdefault(attr, {})
    #    reset_graph_edges[attr]["button_component_dimensions"] = True
    
    attribute_calculation_methods = {}
    #    "button_component_dimensions": "calculateButtonComponentDimensions",
    #}
    
    # Review- account for using element_inherited_attributes in ComponentGroupBaseClass
    attribute_default_functions = {
        **{
            attr: Button.attribute_default_functions.get(attr) for attr in
            [
                "text_borders_rel",
                "outline_widths",
                
                "font_colors",
                "fill_colors",
                "outline_colors",
            ]
        },
        **{
            "text_groups": ((lambda obj: ButtonGroup.createTextGroups()), ("n_state",)),
        }
    }

    attribute_processing = {
        **{
            attr: Button.attribute_processing.get(attr) for attr in
                [
                    "text_borders_rel",
                    "outline_widths",
                    "font_colors",
                    "fill_colors",
                    "outline_colors",
                ]
        },
        **{
            "text_groups": lambda val, obj: processReferenceStructure(val, obj.n_state),
        }
    }
    
    #fixed_attributes = {"buttons"}
    
    element_inherited_attributes = {
        #"text_groups": "text_groups",
        "button_shape": "shape",
        "text_borders_rel": "text_borders_rel",
        "outline_widths": "outline_widths",
        "font_colors": "font_colors",
        "fill_colors": "fill_colors",
        "outline_colors": "outline_colors",
    }
    
    def __init__(self, 
        button_shape: Tuple[Real],
        text_groups: Tuple[Union[TextGroup, int]]=None,
        text_borders_rel: Optional[Tuple[Union[Optional[Tuple[Real]], int]]]=None,
        font_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        fill_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        outline_widths: Optional[Tuple[Union[Real, int]]]=None,
        outline_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        name: Optional[str]=None,
        **kwargs,
    ) -> None:
        checkHiddenKwargs(type(self), kwargs)
        if name is None:
            ButtonGroup.unnamed_count += 1
            name = f"button group {self.unnamed_count}"
        #self.name = name
        ButtonGroup.button_group_names.add(name)
        super().__init__(**self.initArgsManagement(locals(), kwargs=kwargs))
        
    
    def addButton(
        self,
        text: Tuple[Union[Tuple[str], int]],
        anchor_rel_pos: Tuple[Real],
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        text_anchor_types: Optional[Tuple[Union[Optional[Tuple[str]], int]]]=None,
        mouse_enabled: Optional[bool]=None,
        name: Optional[str]=None,
        **kwargs,
    ) -> "ButtonGroupElement":
        
        #text_objects = () # TODO

        res = self._addElement(
            text=text,
            #text_objects=text_objects,
            anchor_rel_pos=anchor_rel_pos,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=screen_topleft_to_parent_topleft_offset,
            text_anchor_types=text_anchor_types,
            mouse_enabled=mouse_enabled,
            name=name,
            **kwargs,
        )
        return res

    #def createTextObjects(
    #    self,
    #    #text: Tuple[Union[Tuple[str], int]],
    #    #text_anchor_types: Optional[Tuple[Union[Optional[Tuple[str]], int]]]=None,
    #) -> Tuple[Union[Optional["Text"], int]]:
    #    return

    @classmethod
    def createTextGroups(cls) -> None:
        res = []
        for _ in range(cls.n_state):
            res.append((TextGroup(
                text_list=[],
                max_height0=None,
                font=None,
                font_size=None,
                min_lowercase=None,
                text_global_asc_desc_chars=None,
                #_from_container=True,
                #_container_obj=self,
            ),))
        #print(res)
        return tuple(res)
    
class ButtonGrid(InteractiveDisplayComponentBase):
    #navkeys_def = navkeys_def_glob
    #navkey_dict_def = createNavkeyDict(navkeys_def)
    
    n_state = Button.n_state

    reset_graph_edges = {
        "grid_dims": {"grid_layout": True},
        "shape": {"grid_layout": True},
        "button_gaps_rel_shape": {"grid_layout": True},
        "grid_layout": {"button_shape": True, "button_gaps": True, "button_topleft_locations": True, "display_surf": True},
        "button_shape": {"display_surf": True, "button_ranges_rel": True},
        "button_gaps": {"display_surf": True},
        "button_topleft_locations": {"display_surf": True, "button_ranges_rel": True},
        "button_ranges_rel": {"button_ranges_screen": True},
    }

    custom_attribute_change_propogation_methods = {
        "button_mouse_is_over": "customButtonMouseIsOverChangePropogation",
        "mouse_l_held": "customMouseLHeldChangePropogation",
        "navkey_button": "customNavkeyButtonChangePropogation",
    }
    
    attribute_calculation_methods = {
        "mouse_enablement": "calculateMouseEnablement",
        "navkeys_enablement": "calculateNavkeysEnablement",

        "grid_layout": "calculateGridLayout",
        "button_shape": "calculateButtonShape",
        "button_gaps": "calculateButtonGaps",
        "button_topleft_locations": "calculateButtonTopleftLocations",

        "button_ranges_rel": "calculateButtonRangesRelative",
        "button_ranges_screen": "calculateButtonRangesScreen",

        "button_grid_img_constructor": "createButtonGridImageConstructor",
    }
    
    attribute_default_functions = {
        **{
            attr: Button.attribute_default_functions.get(attr) for attr in
            [
                "mouse_enabled",
            ]
        },
        **{
            attr: ButtonGroup.attribute_default_functions.get(attr) for attr in
            [
                "text_groups",
                "font_colors",
                "text_borders_rel",
                "fill_colors",
                "outline_widths",
                "outline_colors",
            ]
        },
        **{
            "button_gaps_rel_shape": ((lambda obj: (0., 0.)),),
            "navkeys_enabled": ((lambda obj: True),),
            "navkey_cycle_delay_frame": ((lambda obj: (30, 10)),),
            "navkey_status": ((lambda obj: (None, [0, 0])),),
            "navkey_button": ((lambda obj: (0, 0)),),
            "enter_keys_enablement": ((lambda obj: (False, True, False)),),
            "buttons": ((lambda obj: [[None] * obj.grid_dims[1] for _ in range(obj.grid_dims[0])]),),
            "selected": ((lambda obj: 0),),
            "button_mouse_is_over": ((lambda obj: ()),),
            "mouse_l_held": ((lambda obj: False),),
        }
    }

    attribute_processing = {
        **{
            attr: Button.attribute_processing.get(attr) for attr in
                [
                    "text_borders_rel",
                    "outline_widths",
                    "font_colors",
                    "fill_colors",
                    "outline_colors",
                ]
        },
        **{
            attr: ButtonGroup.attribute_processing.get(attr) for attr in
                [
                    "text_groups",
                ]
        }
    }
    
    #fixed_attributes = set()
    
    sub_components = {
        "button_group": {
            "class": ButtonGroup,
            "attribute_correspondence": {
                "button_shape": "button_shape",
                "text_groups": "text_groups",
                "text_borders_rel": "text_borders_rel",
                "font_colors": "font_colors",
                "fill_colors": "fill_colors",
                "outline_widths": "outline_widths",
                "outline_colors": "outline_colors",
            },
            "creation_function_args": {
                "button_shape": None,
                "text_groups": None,
                "text_borders_rel": None,
                "font_colors": None,
                "fill_colors": None,
                "outline_widths": None,
                "outline_colors": None,
            },
        }
    }
    
    displ_component_attrs = ["button_grid"]

    def __init__(
        self,
        grid_dims: Tuple[int, int],
        shape: Tuple[Real, Real],
        anchor_rel_pos: Tuple[Real, Real],
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real, Real]]=None,
        button_gaps_rel_shape: Optional[Tuple[Optional[Real], Optional[Real]]]=None,
        text_groups: Optional[Tuple[Union[Optional[Tuple["TextGroup"]], int]]]=None,
        font_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        text_borders_rel: Optional[Tuple[Union[Optional[Tuple[Real]], int]]]=None,
        fill_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        outline_widths: Optional[Tuple[Union[Real, int]]]=None,
        outline_colors: Optional[Tuple[Optional[ColorOpacity], int]]=None,
        mouse_enabled: Optional[bool]=None,
        navkeys_enabled: Optional[bool]=None,
        navkeys: Optional[Tuple[Tuple[Set[int]]]]=None,
        navkey_cycle_delay_frame: Optional[Tuple[int]]=None,
        enter_keys: Optional[Set[int]]=None,
        **kwargs,
    ):

        #self.button_shape_fixed = False
        
        checkHiddenKwargs(type(self), kwargs)

        kwargs2 = self.initArgsManagement(locals(), kwargs=kwargs)
        super().__init__(**kwargs2)
        #self.buttons = [[None] * self.grid_dims[1] for _ in range(self.grid_dims[0])]

        
        """
        super().__init__(
            shape,
            anchor_rel_pos,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=screen_topleft_to_parent_topleft_offset,
            mouse_enablement=(mouse_enabled, False, mouse_enabled),
            navkeys_enablement=(navkeys_enabled, navkeys_enabled, False),
            navkeys=navkeys,
            enter_keys_enablement=(False, navkeys_enabled, False),
            enter_keys=enter_keys,
        )
        
        #self.n_state = 4
        #self.selected = 0
        
        #print(button_text)
        #self._button_array_shape = (len(button_text), len(button_text[0])) if button_text else (0, 0)
        """
        """
        self._screen_topleft_to_parent_topleft_offset = screen_topleft_to_parent_topleft_offset
        self._grid_anchor_rel_pos = grid_anchor_rel_pos
        self._grid_anchor_type = grid_anchor_type
        """
        """
        self._text_groups = None# text_groups
        
        self._button_gaps_rel_shape = tuple(button_gaps_rel_shape)
        
        #self._button_shape = button_shape
        #self.button_shape_fixed = True
        
        self.text_borders_rel = tuple([(0.2, 0.2)] + [0] * (self.n_state - 1)) if text_borders_rel is None else text_borders_rel
        self.outline_widths = tuple([(1,)] + [0] * (self.n_state - 1)) if outline_widths is None else outline_widths
        
        
        
        self.font_colors = tuple([(named_colors_def["white"], 1)] + [0] * (self.n_state - 1)) if font_colors is None else font_colors
        self.fill_colors = tuple([(named_colors_def["white"], 0)] + [0] * (self.n_state - 1)) if fill_colors is None else fill_colors
        self.outline_colors = tuple([(named_colors_def["black"], 1)] + [0] * (self.n_state - 1)) if outline_colors is None else outline_colors
        
        #self._button_text = button_text
        
        #self._text_list = []
        #for text_list in button_text:
        #    self._text_list.extend(text_list)
        
        self.mouse_enabled = mouse_enabled
        self.navkeys_enabled = navkeys_enabled
        
        self._setupButtons(button_text)
        
        self._mouse_over = None
        if navkeys_enabled:
            self.setNavkeyButton((0, 0))
        self._navkey_status = [None, [0, 0]] #[None, set(), [0, 0]]
        self._navkeys = navkeys
        self._navkey_cycle_delay_frame = navkey_cycle_delay_frame
        """
    
    def setupButtonGridElement(
        self,
        grid_inds: Tuple[int],
        text: Tuple[Union[Tuple[str], int]],
        text_anchor_types: Optional[Tuple[Union[Optional[Tuple[str]], int]]]=None,
        name: Optional[str]=None,
        **kwargs,
    ) -> Button:
        # Review- add mechanism for communicating from a constituent slider
        # that its value has changed.
        #print(grid_inds, self.grid_dims)
        if any(idx < 0 or idx >= m for idx, m in zip(grid_inds, self.grid_dims)):
            raise IndexError("The grid indices given are not in the allowed range")
        attr_dict = {
            "text": text,
            "anchor_rel_pos": (0, 0),
            "anchor_type": "topleft",
            #"screen_topleft_to_parent_topleft_offset": self.screen_topleft_to_component_topleft_offset,
            "text_anchor_types": text_anchor_types,
            "mouse_enabled": self.mouse_enabled,
            "name": name,
        }
        if self.buttons[grid_inds[0]][grid_inds[1]] is None:
            attr_corresp_dict = {
                "mouse_enabled": "mouse_enabled",
            }
            container_attr_resets = {"changed_since_last_draw": {"display_surf": (lambda container_obj, obj: obj.drawUpdateRequired())}}
            self.buttons[grid_inds[0]][grid_inds[1]] = self.createSubComponent(
                component_class=ButtonGroupElement,
                attr_correspondence_dict=attr_corresp_dict,
                creation_kwargs=attr_dict,
                container_attribute_resets=container_attr_resets,
                custom_creation_function=self.button_group.addButton
            )
            """
            #print(f"creating button at grid indices {grid_inds}")
            container_attr_resets = {"changed_since_last_draw": {"display_surf": (lambda container_obj, obj: obj.drawUpdateRequired())}}
            self.buttons[grid_inds[0]][grid_inds[1]] = self.button_group.addButton(
                _from_container=True,
                _container_obj=self,
                _container_attr_reset_dict=container_attr_resets,
                **attr_dict,
                **kwargs,
            )
            #print(self.buttons[grid_inds[0]][grid_inds[1]].__dict__.get("_display_surf", None))
            """
        else:
            self.buttons[grid_inds[0]][grid_inds[1]].setAttributes(
                attr_dict,
                _from_container=True,
                **kwargs,
            )
        #self.setAttributes({"display_surf": None}, _from_container=True)
        # Workaround to ensure that the button element is sufficiently
        # set up
        self.buttons[grid_inds[0]][grid_inds[1]].button_surfs
        # Ensure that the navkey button is highlighted (if applicable)
        navkey_button = self.navkey_button
        self.navkey_button = ()
        self.navkey_button = navkey_button
        return self.buttons[grid_inds[0]][grid_inds[1]]
    
    def getButton(self, grid_inds: Tuple[int, int]) -> Optional[Button]:
        if any(idx < 0 or idx >= m for idx, m in zip(grid_inds, self.grid_dims)):
            raise IndexError("The grid indices given are not in the allowed range")
        return self.buttons[grid_inds[0]][grid_inds[1]]
    
    def getButtonState(self, inds: Tuple[int]) -> int:
        return self.button_grid[inds[0]][inds[1]].state

    def buttonIterator(self) -> Generator[Tuple[Button, Tuple[int, int]], None, None]:
        for i1, button_row in enumerate(self.buttons):
            for i2, button in enumerate(button_row):
                if button is None: continue
                yield (button, (i1, i2))
        return
    

    def calculateGridLayout(self) -> Tuple[Tuple[int, int], Tuple[float, float]]:
        shape = []
        gaps = []
        for tot_len, n_buttons, rel_gap_size in zip(self.shape, self.grid_dims, self.button_gaps_rel_shape):
            shape.append(round(tot_len / (rel_gap_size * (n_buttons - 1) + n_buttons)))
            gaps.append((tot_len - n_buttons * shape[-1]) / (n_buttons - 1) if n_buttons > 1 else 0.)
        return tuple(shape), tuple(gaps)
    
    def calculateButtonShape(self) -> Tuple[int, int]:
        return self.grid_layout[0]

    def calculateButtonGaps(self) -> Tuple[int, int]:
        return self.grid_layout[1]
    
    def calculateButtonTopleftLocations(self) -> Tuple[List[int], List[int]]:
        dims = self.grid_dims
        button_shape, gap_size = self.grid_layout
        x_lst = []
        y_lst = []
        for i1 in range(dims[0]):
            x_lst.append(round((button_shape[0] + gap_size[0]) * i1))
        for i2 in range(dims[1]):
            y_lst.append(round((button_shape[1] + gap_size[1]) * i2))

        return (x_lst, y_lst)

    def createDisplaySurface(self) -> "pg.Surface":
        #print("creating display surface")
        #print(f"shape = {self.shape}")
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        #surf.set_alpha(100)
        #surf.fill((255, 0, 0))
        #print(self.displ_component_attrs)
        for attr in self.displ_component_attrs:
            #print(f"{attr}_img_constructor")
            constructor_func = getattr(self, f"{attr}_img_constructor", (lambda obj, surf: None))
            #print(attr, surf)
            constructor_func(self, surf)
            #print("howdy")
        #print(f"display surface = {surf}")
        return surf

    def createButtonGridImageConstructor(self) -> Callable[["ButtonGrid", "pg.Surface"], None]:
        def constructor(obj: ButtonGrid, surf: "pg.Surface") -> None:
            #print("using slider grid constructor")
            n_button = 0
            # Workaround to prevent the possibility that changes to one
            # of the later sliders causes the display surface of an earlier
            # one to be reset- moved to the addSliderPlus() method
            #for slider, _ in obj.sliderPlusIterator():
            #    slider.display_surf
            for button, grid_inds in obj.buttonIterator():
                i1, i2 = grid_inds
                #if i2 == 0: continue
                #print(f"grid inds {(i1, i2)}")
                button.anchor_type = "topleft"
                button.anchor_rel_pos = (self.button_topleft_locations[0][i1], self.button_topleft_locations[1][i2])
                button.draw(surf)
                n_button += 1
            #print(f"n_button = {n_button}")
            return

        return constructor

    #########################
    """
    def _setupText(
        self,
        button_text: List[List]
    ) -> List[List[List[Optional["Text"]]]]:
        res = [[[None] * self.n_state for _ in range(self.button_array_shape[1])] for _ in range(self.button_array_shape[0])]
        #anchor_type = "center"
        #print(button_text)
        button_text_simpl = []
        for row in button_text:
            button_text_simpl.append([])
            for tup in row:
                #print(tup)
                button_text_simpl[-1].append((tup[0], simplifyReferences(tup[1])))
        #print(button_text_simpl)
        button_shape = self.button_shape
        for i in range(self.n_state):
            text_list = []
            inds_list = []
            text_group_tup = self.text_groups[i]
            if text_group_tup is None:
                continue
            elif isinstance(text_group_tup, int):
                for idx1 in range(self.button_array_shape[0]):
                    for idx2 in range(self.button_array_shape[1]):
                        res[idx1][idx2][i] = text_group_tup
                continue
            text_group = text_group_tup[0]
            j0 = len(text_group)
            
            tbr = self.text_borders_rel[i]
            if tbr is None: tbr = (0, 0)
            elif isinstance(tbr, int): tbr = self.text_borders_rel[tbr]
            text_shape = self.text_max_shapes[i]
            if isinstance(text_shape, int):
                text_shape = self.text_max_shapes[text_shape]
            
            font_color = self.font_colors[i]
            if isinstance(font_color, int):
                font_color = self.font_colors[font_color]
            
            for idx1, text_row in enumerate(button_text_simpl):
                for idx2, text_tup in enumerate(text_row):
                    text, text_anchor_types = text_tup
                    tup = text_anchor_types[i]
                    if isinstance(tup, int): tup = text_anchor_types[tup]
                    text_anchor_type = tup[0]
                    #if text_tup is None: continue
                    #elif isinstance(text_tup, int):
                    #    text_tup = self.button_text[idx1][idx2][text_tup]
                    button_topleft = self.buttons_topleft[0][idx1], self.buttons_topleft[1][idx2]
                    #print(button_topleft, button_shape, tbr)
                    # Repeated code
                    text_topleft = tuple(x + y * z for x, y, z in\
                            zip(button_topleft, button_shape, tbr))
                    #print(text_shape, text_anchor_type)
                    anchor_offset = topLeftAnchorOffset(text_shape, text_anchor_type)
                    text_anchor_rel_pos = tuple(x + y for x, y in zip(text_topleft, anchor_offset))
                    
                    inds_list.append((idx1, idx2))
                    # text_list = [{"text": "Hello", "max_width": 200, "color": (named_colors_def["red"], 1)), "anchor_rel_pos0": (0, 0), "anchor_type0": "topleft"}]
                    text_list.append({"text": text, "max_shape": (text_shape[0], None), "font_color": font_color, "anchor_rel_pos0": text_anchor_rel_pos, "anchor_type0": "topleft"})
            text_objs = text_group.addTextObjects(text_list)
            for text_obj, (idx1, idx2) in zip(text_objs, inds_list):
                res[idx1][idx2][i] = (text_obj,)
        for idx1, row in enumerate(res):
            for idx2, text_objs in enumerate(row):
                res[idx1][idx2] = tuple(text_objs)
        return res
    
    def _setupButtons(self, button_text: List[List]) -> None:
        #print("using _setupButtons()")
        text_objs_grid = self._setupText(button_text)
        
        res = []
        x_lst, y_lst = self.buttons_topleft
        bs = tuple(round(z) for z in self.button_shape)
        for text_lst, x, text_objs_row in zip(button_text, x_lst, text_objs_grid):
            res.append([])
            for text_tup, y, text_objs in zip(text_lst, y_lst, text_objs_row):
                res[-1].append(Button(bs, text_objs,
                    (x, y), anchor_type="topleft",
                    font_colors=self.font_colors,
                    text_borders_rel=self.text_borders_rel,
                    text_anchor_types=text_tup[1],
                    fill_colors=self.fill_colors,
                    outline_widths=self.outline_widths,
                    outline_colors=self.outline_colors,
                    mouse_enabled=self.mouse_enabled))
        self._button_grid = res
        return
    
    @property
    def text_groups(self):
        return self._text_groups
    
    @text_groups.setter
    def text_groups(self, text_groups):
        text_groups = simplifyReferences(text_groups)
        self.setAttribute("text_groups", text_groups, "_textGroupsCustomUpdate", reset_type="text_groups", replace_attr=True)
        return
    
    @property
    def button_grid(self):
        return self._button_grid
    
    #@property
    #def button_text(self):
    #    return self._button_text
    
    @property
    def text_list(self):
        return self._text_list
    """
    """
    @property
    def screen_topleft_to_parent_topleft_offset(self):
        return self._screen_topleft_to_parent_topleft_offset
    
    @screen_topleft_to_parent_topleft_offset.setter
    def screen_topleft_to_parent_topleft_offset(self, screen_topleft_to_parent_topleft_offset: Tuple[Real]):
        if screen_topleft_to_parent_topleft_offset == getattr(self, "_screen_topleft_to_parent_topleft_offset", None):
            return
        self._screen_topleft_to_parent_topleft_offset = screen_topleft_to_parent_topleft_offset
        for attr in ("_button_ranges_screen",):
            setattr(self, attr, None)
        return
    
    @property
    def grid_anchor_type(self):
        return self._grid_anchor_type
    
    @grid_anchor_type.setter
    def grid_anchor_type(self, grid_anchor_type: str):
        if grid_anchor_type == getattr(self, "_grid_anchor_type", None):
            return
        self._grid_anchor_type = grid_anchor_type
        for attr in ("_grid_topleft", "_button_ranges_surf", "_button_ranges_screen"):
            setattr(self, attr, None)
        return
    
    @property
    def grid_anchor_rel_pos(self):
        return self._grid_anchor_rel_pos
    
    @grid_anchor_rel_pos.setter
    def grid_anchor_rel_pos(self, grid_anchor_rel_pos: Tuple[int]):
        if grid_anchor_rel_pos == getattr(self, "_grid_anchor_rel_pos", None):
            return
        self._grid_anchor_rel_pos = grid_anchor_rel_pos
        for attr in ("_grid_topleft", "_button_ranges_surf", "_button_ranges_screen"):
            setattr(self, attr, None)
        return
    
    @property
    def grid_topleft(self):
        res = getattr(self, "_grid_topleft", None)
        if res is None:
            res = self.findTopLeft()
            self._grid_topleft = res
        return res
    
    def findTopLeft(self) -> Tuple[int]:
        return topLeftFromAnchorPosition(self.grid_shape, self.grid_anchor_type,\
                self.grid_anchor_rel_pos)
    
    
    @property
    def grid_topleft(self):
        return self._grid_topleft
    
    @grid_topleft.setter
    def grid_topleft(self, grid_topleft):
        if grid_topleft == getattr(self, "_grid_topleft", None):
            return
        self._grid_topleft = grid_topleft
        self._buttons_topleft = None
        return
        ""
        if self.button_shape_fixed:
            button_shape = self._button_shape
            self._button_shape = None
            self.setButtonsShape(button_shape, update_font_sizes=False)
        else:
            self._buttons_topleft = None
            self.dims = (*grid_topleft, *self.dims[2:])
        return
        ""
    
    @property
    def button_array_shape(self):
        return self._button_array_shape
    
    
    @property
    def grid_shape(self):
        res = getattr(self, "_grid_shape", None)
        if res is None:
            res = self.findOverallShapeFromButtonShape()
            self._grid_shape = res
        return res
    
    @grid_shape.setter
    def grid_shape(self, grid_shape: Tuple[Real]):
        if grid_shape == getattr(self, "_grid_shape", None):
            return
        self.button_shape_fixed = False
        self._grid_shape = grid_shape
        self.setButtonsShape(self.findButtonShapeFromOverallShape(), update_font_sizes=True)
        return
    """
    """
    def _shapeCustomUpdate(self, change: bool=False) -> None:
        #print("hello")
        self.button_shape_fixed = False
        if change:
            self.setButtonsShape(self.findButtonShapeFromOverallShape(), update_font_sizes=True)
        return
    """
    """
    @property
    def button_shape(self):
        return self._button_shape
    
    @button_shape.setter
    def button_shape(self, button_shape):
        self.button_shape_fixed = True
        if not self.setButtonsShape(button_shape, update_font_sizes=True):
            return
        self._grid_shape = None
        if self.grid_anchor_type != "topleft":
            self._grid_topleft = None
        return
    """
    """
    @property
    def button_shape(self):
        
        res = getattr(self, "_button_shape", None)
        if res is None:
            res = self.findButtonShapeFromOverallShape()
            self.setButtonsShape(res, update_font_sizes=True)
        return res
        
    
    @button_shape.setter
    def button_shape(self, button_shape: Tuple[Real]):
        #print("setting button shape")
        #if shape == getattr(self, "_shape", None):
        #    return
        #self._shape = shape
        self.setAttribute("button_shape", button_shape, "_buttonShapeCustomUpdate", reset_type="button_shape", replace_attr=True)
        return
    
    def _buttonShapeCustomUpdate(self, change: bool=True) -> None:
        #print("using _buttonShapeCustomUpdate")
        self.button_shape_fixed = True
        if not change:
            return
        self.setButtonsShape(self._button_shape, update_font_sizes=True)
        return
    
    def setButtonsShape(self, button_shape: Tuple[Real], update_font_sizes: bool=True) -> bool:
        #print("howdy")
        #print(button_shape, getattr(self, "_button_shape", None))
        #if button_shape == getattr(self, "_button_shape", None):
        #    return False
        #print("howdy2")
        self._button_shape = button_shape
        self._shape = self.findOverallShapeFromButtonShape()
        #print(f"self._shape = {self._shape}")
        self._buttons_topleft = None
        self._button_ranges_gridwise = None
        self._button_ranges_surf = None
        self._button_ranges_screen = None
        self._grid_offsets = None
        self._button_grid_surf = None
        if self.anchor_type != "topleft":
            self._topleft = None
        x_lst, y_lst = self.buttons_topleft
        #print(getattr(self, "_button_grid", None))
        if getattr(self, "_button_grid", None) is None:
            return True
        #print("hello")
        #print(self.grid_offsets)
        #print(x_lst, y_lst)
        b_shape = tuple(round(z) for z in button_shape)
        #print(f"b_shape = {b_shape}")
        self.setTextMaxShape()
        for button_lst, x in zip(self.button_grid, x_lst):
            for button, y in zip(button_lst, y_lst):
                button.anchor_rel_pos = (x, y)
                button.shape = b_shape
        #if update_font_sizes and not self.font_sizes_set:
        #    self.calculateAndSetFontSizes()
        return True
    
    @property
    def buttons_topleft(self):
        res = getattr(self, "_buttons_topleft", None)
        if res is None:
            res = tuple(tuple(round(self.grid_offsets[j] * i) for i in range(self.button_array_shape[j])) for j in (0, 1))
            self._buttons_topleft = res
        return res
    
    @property
    def button_gaps_rel_shape(self):
        return self._button_gaps_rel_shape
    
    @button_gaps_rel_shape.setter
    def button_gaps_rel_shape(self, button_gaps_rel_shape):
        self.setAttribute("button_gaps_rel_shape", button_gaps_rel_shape, "_buttonGapRelativeToShapeCustomUpdate", reset_type="button_gaps_rel_shape", replace_attr=True)
        return
    
    def _buttonGapRelativeToShapeCustomUpdate(self, change: bool=True) -> None:
        #print("howdy")
        if not change: return
        if self.button_shape_fixed:
            self._button_ranges_surf = None
            self._button_ranges_screen = None
            #self._dims = None
            self._grid_offsets = None
            self._buttons_topleft = None
        else: self.setButtonsShape(self.findButtonShapeFromOverallShape(), update_font_sizes=True)
        return
    
    @property
    def grid_offsets(self):
        res = getattr(self, "_grid_offsets", None)
        if res is None:
            res = tuple(x * (1 + y) for x, y in zip(self.button_shape, self.button_gaps_rel_shape))
            self._grid_offsets = res
        return res
    
    
    def findButtonShapeFromOverallShape(self):
        return tuple(overall_sz / (n_button + (n_button - 1) * gap) for overall_sz, n_button, gap in zip(self.shape, self.button_array_shape, self.button_gaps_rel_shape))
    
    def findOverallShapeFromButtonShape(self):
        return tuple(button_sz * (n_button + (n_button - 1) * gap) for button_sz, n_button, gap in zip(self.button_shape, self.button_array_shape, self.button_gaps_rel_shape))
    """
    """
    @property
    def dims(self):
        res = getattr(self, "_dims", None)
        if res is None:
            res = (*self.grid_topleft, *self.findOverallDimensionsFromButtonShape())
            self._dims = res
        return self._dims
    
    @dims.setter
    def dims(self, dims):
        #print("hi", dims)
        self.button_shape_fixed = False
        if dims == getattr(self, "_dims", None):
            return
        self._dims = dims
        #print(self.findButtonShapeFromOverallDimensions())
        self.setButtonsShape(self.findButtonShapeFromOverallShape(), update_font_sizes=True)
        return
    """
    """
    @property
    def button_ranges_gridwise(self):
        res = getattr(self, "_button_ranges_gridwise", None)
        if res is None:
            res = self.findButtonRangesRelative()
            self._button_ranges_gridwise = res
            #print(f"button_ranges = {res}")
        return res
    """
    def calculateButtonRangesRelative(self) -> Tuple[Tuple[Real]]:
        res = [[], []]
        b_shape = self.button_shape
        b_topleft_locs = self.button_topleft_locations
        for x in b_topleft_locs[0]:
            res[0].append((x, x + b_shape[0]))
        res[0] = tuple(res[0])
        for y in b_topleft_locs[1]:
            res[1].append((y, y + b_shape[1]))
        res[1] = tuple(res[1])
        return tuple(res)
        """
        b_shape = self.button_shape
        for i1, button_row in enumerate(self.button_grid):
            button = button_row[0]
            topleft = button.topleft_rel_pos
            res[0].append((topleft[0], topleft[0] + b_shape[0]))
        for i2, button in enumerate(self.button_grid[0]):
            topleft = button.topleft
            res[1].append((topleft[1], topleft[1] + b_shape[1]))
        res[0] = tuple(res[0])
        res[1] = tuple(res[1])
        return tuple(res)
        """
    
    def calculateButtonRangesScreen(self) -> Tuple[Tuple[Real]]:
        offset = tuple(x + y for x, y in zip(self.screen_topleft_to_parent_topleft_offset, self.topleft_rel_pos))
        res = []
        for rngs, d in zip(self.button_ranges_rel, offset):
            res.append([tuple(x + d for x in rng) for rng in rngs])
        return res

    """
    @property
    def button_ranges_surf(self):
        res = getattr(self, "_button_ranges_surf", None)
        b_shape = self.button_shape
        if res is None:
            res = self.findButtonRangesSurface()
            self._button_ranges_surf = res
        return res
    
    def findButtonRangesSurface(self) -> Tuple[Tuple[Real]]:
        res = []
        for rngs, tl_displ in zip(self.button_ranges_gridwise, self.topleft_rel_pos):
            res.append([tuple(x + tl_displ for x in rng) for rng in rngs])
        return tuple(res)
    
    @property
    def button_ranges_screen(self):
        res = getattr(self, "_button_ranges_screen", None)
        b_shape = self.button_shape
        if res is None:
            res = self.findButtonRangesScreen()
            self._button_ranges_screen = res
        return res
   
    def findButtonRangesScreen(self):
        res = []
        #for rngs, tl_displ, tl_offset in zip(self.button_ranges_gridwise, self.topleft, self.screen_topleft_to_parent_topleft_offset):
        #    res.append([tuple(x + tl_displ + tl_offset for x in rng) for rng in rngs])
        for rngs, stl_offset in zip(self.button_ranges_surf, self.screen_topleft_to_parent_topleft_offset):
            res.append([tuple(x + stl_offset for x in rng) for rng in rngs])
        return tuple(res)
     """
    """
    @property
    def text_borders_rel(self):
        return self._text_borders_rel
    
    @text_borders_rel.setter
    def text_borders_rel(self, text_borders_rel):
        text_borders_rel = simplifyReferences(text_borders_rel)
        self.setAttribute("text_borders_rel", text_borders_rel, "_textBordersRelativeCustomUpdate", reset_type="text_borders_rel", replace_attr=True)
        #self._text_borders_rel = simplifyReferences(text_borders_rel)
        #self.setTextMaxShape()
        return
    
    def _textBordersRelativeCustomUpdate(self, change: bool=True) -> None:
        if change: self.setTextMaxShape()
        return
    
    @property
    def text_max_shapes(self):
        res = getattr(self, "_text_max_shapes", None)
        if res is None:
            self.setTextMaxShape()
            res = self._text_max_shapes
        return res
    
    def setTextMaxShape(self):
        res = []
        button_shape = self.button_shape
        for tbr in self.text_borders_rel:
            if tbr is None:
                res.append(button_shape)
                continue
            elif isinstance(tbr, int): res.append(tbr)
            else: res.append(getTextMaxShape(button_shape, tbr))
        self._text_max_shapes = tuple(res)
        for text_group_tup, tmd in zip(self.text_groups, res):
            if text_group_tup is None or isinstance(text_group_tup, int):
                continue
            text_group_tup[0].max_shape = tmd
        return
    
    def getState(self, inds: Tuple[int]) -> int:
        return self.button_grid[inds[0]][inds[1]].state
    
    @property
    def button_grid_surf(self):
        res = getattr(self, "_button_grid_surf", None)
        if res is None:
            res = self.createButtonGridSurface()
            self._button_grid_surf = res
        return res
    
    def createButtonGridSurface(self) -> "pg.Surface":
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        for row in self.button_grid:
            for button in row:
                button.draw(surf)
        return surf
    
    @property
    def button_grid_img_constructor(self):
        #print("hello")
        res = getattr(self, "_button_grid_img_constructors", None)
        if res is None:
            res = self.createButtonGridImageConstructor()
            #print(f"res = {res}")
            self._button_grid_img_constructors = res
        return res
    
    def createButtonGridImageConstructor(self) -> Callable[[], None]:
        return lambda surf: surf.blit(self.button_grid_surf, self.topleft_rel_pos)
    """
    #def draw(self, surf: "pg.Surface"):
    #    #self.button_grid_img_constructor(surf)
    #    surf.blit(self.display_surf, self.topleft_rel_pos)
    #    return
    
    def calculateMouseEnablement(self) -> None:
        #print("calculating mouse enablement")
        mouse_enabled = self.mouse_enabled
        return (mouse_enabled, False, mouse_enabled)
    
    def calculateNavkeysEnablement(self) -> None:
        #print("calculating mouse enablement")
        navkeys_enabled = self.navkeys_enabled
        return (navkeys_enabled, navkeys_enabled, False)

    #@property
    #def mouse_over(self):
    #    return self._mouse_over

    #def calculateButtonMouseIsOver(self) -> Optional[Tuple[int, int]]:
    #

    def customButtonMouseIsOverChangePropogation(
        self,
        new_val: Optional[Tuple[int, int]],
        prev_val: Optional[Tuple[int, int]],
    ) -> None:
        #print(new_val, prev_val)
        if not new_val:
            if not prev_val: return
            self.buttons[prev_val[0]][prev_val[1]].state = int(self.navkeys_enabled)
            return
        state = 2 + self.mouse_l_held
        button = self.buttons[new_val[0]][new_val[1]]
        if prev_val == new_val:
            if button.state == state:
                return False#, False
            #selected = (button.state == 3 and state == 2)
            button.state = state
            return True#, selected
        if self.navkeys_enabled:
            self.navkey_button = new_val
        if prev_val:
            self.buttons[prev_val[0]][prev_val[1]].state = 0
        button.state = state
        return True
    
    def customMouseLHeldChangePropogation(
        self,
        new_val: bool,
        prev_val: bool,
    ) -> None:
        mouse_button = self.button_mouse_is_over
        if not mouse_button: return
        button = self.buttons[mouse_button[0]][mouse_button[1]]
        button.state = 2 + new_val
        return
    """
    def setMouseOver(self, mouse_over: Optional[Tuple[int]],\
            mouse_down: bool) -> bool:
        prev = getattr(self, "_mouse_over", None)
        self._mouse_over = mouse_over
        
        if mouse_over is None:
            if prev is None: return False#, False
            self.buttons[prev[0]][prev[1]].state = int(self.navkeys_enabled)
            return True#, False
        state = 2 + mouse_down
        button = self.buttons[mouse_over[0]][mouse_over[1]]
        if prev == mouse_over:
            if button.state == state:
                return False#, False
            #selected = (button.state == 3 and state == 2)
            button.state = state
            return True#, selected
        if self.navkeys_enabled:
            self.buttons[self.navkey_button[0]][self.navkey_button[1]].state = 0
            self._navkey_button = mouse_over
        if prev is not None:
            self.buttons[prev[0]][prev[1]].state = 0
        button.state = state
        return True#, False
    """
    #@property
    #def navkeys(self):
    #    return self.navkeys_def if self._navkeys is None else self._navkeys
    
    #@navkeys.setter
    #def navkeys(self, navkeys):
    #    self._navkey_dict = None
    #    self._navkeys = navkeys
    #    return
    
    #@property
    #def navkey_dict(self):
    #    res = getattr(self, "_navkey_dict", None)
    #    if res is None:
    #        navkeys = self.navkeys
    #        if navkeys is not None:
    #            res = self.getNavkeyDict(navkeys)
    #    return self.navkey_dict_def if res is None else res
    
    #@staticmethod
    #def getNavkeyDict(navkeys: Tuple[Tuple[Set[int]]]):
    #    return createNavkeyDict(navkeys)
    
    #@property
    #def navkey_cycle_delay_frame(self):
    #    return self._navkey_cycle_delay_frame
    
    #@property
    #def navkey_status(self):
    #    return self._navkey_status
    
    #@property
    #def navkey_button(self):
    #    return self._navkey_button
    
    """
    def setNavkeyButton(self, navkey_button: Optional[Tuple[int]]) -> bool:
        prev = getattr(self, "_navkey_button", None)
        if self.mouse_over is not None or navkey_button == prev:
            return False
        self._navkey_button = navkey_button
        if prev is not None:
            self.buttons[prev[0]][prev[1]].state = 0
        self.buttons[navkey_button[0]][navkey_button[1]].state = 1
        return True
    """

    def customNavkeyButtonChangePropogation(
        self,
        new_val: Optional[Tuple[int, int]],
        prev_val: Optional[Tuple[int, int]],
    ) -> None:
        #print("Using customNavkeyButtonChangePropogation()")
        if prev_val and self.buttons[prev_val[0]][prev_val[1]] is not None:
            self.buttons[prev_val[0]][prev_val[1]].state = 0
        if self.button_mouse_is_over:
            return
        if prev_val and self.buttons[prev_val[0]][prev_val[1]] is not None:
            self.buttons[prev_val[0]][prev_val[1]].state = 0
        if new_val and self.buttons[new_val[0]][new_val[1]] is not None:
            self.buttons[new_val[0]][new_val[1]].state = 1
        return

    
    def navkeyMoveCalculator(self, navkey: int, start_button: Tuple[int]) -> Tuple[int]:
        #print(f"Using navkeyMoveCalculator() with navkey = {navkey} and start_button = {start_button}")
        if not self.navkeys_enabled: return start_button
        move = self.navkey_dict.get(navkey, None)
        if move is None: return start_button
        #print(f"move = {move}")
        res = list(start_button)
        grid_dims = self.grid_dims
        i = move[0]
        
        if move[1] == 0:
            res[i] = (res[i] - 1) % grid_dims[i]
        else: res[i] = (res[i] + 1) % grid_dims[i]
        return tuple(res)
    
    """
    def navkeyMove(self, navkey_events: Optional[List[Tuple[int]]], navkeys_pressed: Optional[Set[int]]=None) -> Tuple[bool]:
        print("Using ButtonGrid method navkeyMove()")
        # Consider adding option to ignore navigation keystrokes for
        # which the opposite navigation key is currently held down
        # (e.g. ignore left keystroke if the right navigation key
        # is currently held down)
        
        
        # In navkey_events, -1 represents enter keystroke,
        # and the other integers represent the navigation key pressed
        
        #print(navkeys_pressed)
        
        default_status_func = lambda curr_key, navkey_set: [curr_key, navkey_set, 0, 0]
        
        if navkeys_pressed is None:
            navkeys_pressed = checkKeysPressed(keys_to_check=self.navkey_dict.keys())
        
        #if navkey_events or navkeys_pressed:
        #    print(navkey_events, navkeys_pressed)
        
        screen_changed = False
        orig_button = self.navkey_button
        
        def updateStates(orig: Tuple[int], curr: Tuple[int]) -> None:
            self._navkey_button = curr
            self.buttons[orig[0]][orig[1]].state = 0
            self.buttons[curr[0]][curr[1]].state = 1
            return
        
        if navkey_events:
            curr_button = orig_button
            for navkey in navkey_events:
                if navkey == -1:
                    self._navkey_status = default_status_func(None, navkeys_pressed)
                    if curr_button != orig_button:
                        updateStates(orig_button, curr_button)
                        return True, True
                    return True, False
                curr_button = self.navkeyMoveCalculator(navkey, curr_button)
            self._navkey_status = default_status_func(navkey if navkey in navkeys_pressed else None, navkeys_pressed)
            if curr_button != orig_button:
                updateStates(orig_button, curr_button)
                return False, True
            return False, False
        
        #print("hi")
        status = self._navkey_status
        if status[0] not in navkeys_pressed:
            return False, False
        #print("hello")
        
        delay_lst = self.navkey_cycle_delay_frame
        print(f"delay_lst = {delay_lst}")
        status[3] = (status[3] + 1) % delay_lst[status[2]]
        #print(status)
        if not status[3]:
            status[2] += (status[2] < len(delay_lst) - 1)
            navkey = status[0]
            curr_button = self.navkeyMoveCalculator(navkey, orig_button)
            if curr_button != orig_button:
                updateStates(orig_button, curr_button)
                screen_changed = True
        status[1] = navkeys_pressed
        return False, screen_changed
    """
    """
    def getRequiredInputs(self) -> Tuple[Union[bool, Dict[str, Union[List[int], Tuple[Union[Tuple[int], int]]]]]]:
        quit, esc_pressed, events = self.user_input_processor.getEvents()
        return quit, not esc_pressed, {"events": events,\
                "keys_down": self.user_input_processor.getKeysHeldDown(),\
                "mouse_status": self.user_input_processor.getMouseStatus()}
    """
    #def processEvents(self, events: List[Tuple[int]]) -> List[Tuple[int]]:
    #    res = []
    #    for event_tup in events:
    #        if event_tup[1] == 3 and event_tup[0].button == 1:
    #            res.append(event_tup[0].pos)
    #    return res
    
    def mouseOverWhichButton(self, mouse_pos: Optional[Tuple]=None) -> Optional[Tuple[int]]:
        if not self.mouse_enabled: return None
        if mouse_pos is None:
            if not pg.mouse.get_focused():
                return None
            mouse_pos = pg.mouse.get_pos()
        
        res = []
        for x, rngs in zip(mouse_pos, self.button_ranges_screen):
            i = bisect.bisect_right(rngs, (x, float("inf"))) - 1
            if i < 0 or x > rngs[i][1]:
                return None
            res.append(i)
        return tuple(res)
    
    def processEvents(self, b_inds0: Optional[Tuple[int]], b_inds0_mouse: Optional[Tuple[int, int]], mouse_pos_curr: Optional[Tuple[int, int]], events: List[Tuple[int]]) -> Tuple[Union[List[int], List[Tuple[int]], bool]]:
        #print("Using processEvents()")
        #print(b_inds0, b_inds0_mouse, mouse_pos_curr, events)
        
        if not self.mouse_enabled and not self.navkeys_enabled:
            return None, [], False, None, False
        
        #enter_pressed = False
        selected_b_inds = []
        idx1 = 0
        b_inds_mouse = b_inds0_mouse
        b_inds = b_inds0
        b_reset = False
        last_navkey = None
        #mouse_over_button
        #button_mouse_is_over = self.mouseOverWhichButton(pos)
        for tup in events:
            if tup[1] == 3 and self.mouse_enabled:
                pos = tup[0].pos
                b_inds2 = self.mouseOverWhichButton(pos)
                if b_inds2 is None: continue
                b_inds = b_inds2
                b_reset = True
                last_navkey = None
                if b_inds == b_inds_mouse:
                    for idx in range(idx1, len(selected_b_inds)):
                        selected_b_inds[idx] = b_inds_mouse
                    idx1 = len(selected_b_inds)
                else: b_inds_mouse = b_inds
                if tup[0].button != 1:
                    continue
                #print("hi1")
                selected_b_inds.append(b_inds)
                continue
            elif tup[1] != 0 or not self.navkeys_enabled:
                continue
            #print(tup)
            if tup[0].key in self.enter_keys:
                #print("enter pressed")
                #enter_pressed = True
                #print("hi2")
                b_reset = True
                last_navkey = None
                selected_b_inds.append(b_inds)
            elif tup[0].key in self.navkey_dict.keys():
                b_reset = True
                last_navkey = tup[0].key
                b_inds = self.navkeyMoveCalculator(tup[0].key, b_inds)
                #print(f"post navkeyMoveCalculator() b_inds = {b_inds}")
        mouse_over_button = False
        b_inds1_mouse = None if mouse_pos_curr is None else self.mouseOverWhichButton(mouse_pos_curr)
        if b_inds1_mouse is not None:
            b_reset = True
            last_navkey = None
            b_inds = b_inds1_mouse
            mouse_over_button = True
            if b_inds_mouse == b_inds1_mouse:
                for idx in range(idx1, len(selected_b_inds)):
                    selected_b_inds[idx] = b_inds_mouse
        #if selected_b_inds:
        #    print(selected_b_inds)
        return b_inds, selected_b_inds, b_reset, last_navkey, mouse_over_button
    
    def eventLoop(
        self,
        events: Optional[List[int]]=None,
        keys_down: Optional[Set[int]]=None,
        mouse_status: Optional[Tuple[int]]=None,
        check_axes: Tuple[int]=(0, 1),
    ) -> Tuple[bool, bool, bool, Any]:
        quit = False
        running = True
        screen_changed = False
        
        mouse_enabled = self.mouse_enabled and pg.mouse.get_focused()
        
        if mouse_enabled:
            if mouse_status is None:
                mouse_status = self.user_input_processor.getMouseStatus()
            b_inds0_mouse = self.button_mouse_is_over
            #b_inds1_mouse = self.mouseOverWhichButton(mouse_status[0])
            #print(b_inds1_mouse)
            #print(f"mouse_status = {mouse_status}")
            self.mouse_l_held = mouse_status[1][0]
        else:
            b_inds0_mouse = None
            b_inds1_mouse = None
            self.mouse_l_held = False
        
        if events is None:
            quit, esc_pressed, events = self.user_input_processor.getEvents()
            if quit or esc_pressed:
                running = False
        
        b_inds0 = b_inds0_mouse
        if not b_inds0 and self.navkeys_enabled:
            b_inds0 = self.navkey_button
        #print(events)
        #print(self.navkeys)
        #print(self.navkeys_enabled, self.navkeys_enablement)
        #print(self.enter_keys)
        b_inds1, selected_b_inds, b_reset, last_navkey, mouse_over_button = self.processEvents(b_inds0, b_inds0_mouse, mouse_status[0] if mouse_enabled else None, events)
        #print(b_inds1, selected_b_inds, b_reset, last_navkey, mouse_over_button)
        #print(f"post processEvents(), b_inds1 = {b_inds1}")
        # Checking for navkeys that are held down and have not yet
        # been overridden by new inputs
        #print(self._navkey_status)
        #print(keys_down)
        if b_reset:
            self._navkey_status = [last_navkey, [0, 0]]
        else:
            status = self.__dict__.get("_navkey_status", [None, [0, 0]])
            
            if keys_down is None:
                keys_down = self.user_input_processor.getKeysHeldDown()
            #print(f"status = {status}, keys_down = {keys_down}")
            if status[0] in keys_down:
                delay_lst = self.navkey_cycle_delay_frame
                #print(f"delay_lst = {delay_lst}")
                status[1][1] += 1
                if status[1][1] == delay_lst[status[1][0]]:
                    b_inds1 = self.navkeyMoveCalculator(status[0], b_inds1)
                    status[1][1] = 0
                    status[1][0] += (status[1][0] < len(delay_lst) - 1)
            else:
                #print("resetting navkey status")
                self._navkey_status = [None, [0, 0]]
        #print(self.navkey_status)
        #self.navkey_button = b_inds1
        #if (mouse_enabled and self.setMouseOver(b_inds1_mouse, lmouse_down))\
        #        or (self.navkeys_enabled and self.setNavkeyButton(b_inds1)):
        #    screen_changed = True
        #if (mouse_enabled and self.setMouseOver(b_inds1_mouse, lmouse_down)):
        #    screen_changed = True
        #button_focus = False
        if mouse_enabled and mouse_over_button:
            self.button_mouse_is_over = b_inds1
            #button_focus = self.setMouseOver(b_inds1_mouse, lmouse_down)
        else:
            self.button_mouse_is_over = ()
            if self.navkeys_enabled:
                self.navkey_button = b_inds1
            #button_focus = b_inds1
        #print(self.navkey_button)
        #print(keys_down)
        screen_changed = self.drawUpdateRequired()
        #if screen_changed:
        #    print("button grid re-draw required")
        #print(quit, esc_pressed, (screen_changed, selected))
        #if screen_changed:
        #    self._button_grid_surf = None
        return quit, running, screen_changed, selected_b_inds

