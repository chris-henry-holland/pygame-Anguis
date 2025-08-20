#!/usr/bin/env python
import math

from typing import Any, Tuple, Union, List, Optional, Callable, Generator, Dict

import pygame as pg

from pygame_display_component_classes.config import (
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
from pygame_display_component_classes.text_manager import Text, TextGroup
from pygame_display_component_classes.position_offset_calculators import topLeftAnchorOffset

track_color_def = (named_colors_def["silver"], 1)
thumb_color_def = (named_colors_def["white"], 1)
text_color_def = (named_colors_def["black"], 1)

def sliderValuesInteger(obj: "Slider") -> bool:
    return isinstance(obj.increment_start, int) and bool(obj.increment) and isinstance(obj.increment, int)

def sliderPrimaryDemarcationsInteger(obj: "Slider") -> bool:
    res = sliderValuesInteger(obj) and isinstance(obj.demarc_start_val, int) and (obj.__dict__.get("_demarc_intervals", None) is None or isinstance(obj.demarc_intervals[0], int))
    #print(f"demarcations integer = {res}")
    return res

def sliderDemarcationsIntervalDefault(obj: "Slider") -> Real:
    pow10 = math.floor(math.log(obj.val_range[1] - obj.val_range[0], 10) - 0.5)
    return (10 ** pow10,) if sliderPrimaryDemarcationsInteger(obj) or pow10 > 1 else (1,)

def sliderDemarcationsDPDefault(obj: "Slider") -> int:
    if sliderPrimaryDemarcationsInteger(obj):
        return 0
    res = max(0, -math.floor(math.log(obj.demarc_intervals[0], 10) - 1.5))
    return res

def sliderPlusDemarcationsDPDefault(obj: "SliderPlus") -> int:
    return sliderDemarcationsDPDefault(obj.slider)

class Slider(InteractiveDisplayComponentBase):
    slider_names = set()
    unnamed_count = 0
    
    reset_graph_edges = {
        "screen_topleft_to_component_topleft_offset": {"thumb_x_screen": True, "slider_ranges_screen": True},
        #"mouse_enabled": {"mouse_enablement": True},
        "track_color": {"track_surf": True},

        #"component_dimensions": {"track_topleft": True, "track_shape": True, "thumb_radius": True, "demarc_numbers_max_height": True}

        "track_topleft": {"x_range": True, "thumb_x": True, "static_bg_surf": True, "demarc_surf": True, "slider_ranges_surf": True},
        "track_shape": {"x_range": True, "thumb_x": True, "track_surf": True, "demarc_surf": True, "slider_ranges_surf": True},
        "demarc_line_colors": {"demarc_surf": True},
        
        "demarc_numbers_color": {"demarc_surf": True},
        
        "increment_start": {"val_range_actual": True},
        "increment": {"val_range_actual": True},
        "val_range": {"val_range_actual": True},
        "val_range_actual": {"x_range": True},
        "x_range": {"thumb_x": True},
        
        "thumb_radius": {"thumb_surf": True, "slider_ranges_surf": True},
        "thumb_color": {"thumb_surf": True},
        
        "val_raw": {"val": True, "thumb_x_screen_raw": True},
        "thumb_x_screen_raw": {"val": True},

        "val": {"thumb_x": True},
        "thumb_x": {"thumb_x_screen": True, "display_surf": True},
        "thumb_x_screen": {"display_surf": True},
        
        "slider_ranges_surf": {"slider_ranges_screen": True},
        
        "track_surf": {"static_bg_surf": True},
        "demarc_surf": {"static_bg_surf": True},
        "static_bg_surf": {"display_surf": True},
        "thumb_surf": {"display_surf": True},
    }
    
    component_dim_determiners = ["shape", "demarc_numbers_max_height_rel", "demarc_numbers_dp", "val_range", "demarc_intervals", "demarc_start_val", "thumb_radius_rel", "demarc_line_lens_rel", "demarc_numbers_text_group", "demarc_numbers_text_objects"]
    component_dim_dependent = ["track_shape", "track_topleft", "demarc_numbers_max_height", "thumb_radius"]
    
    #for attr1 in component_dim_determiners:
    #    reset_graph_edges.setdefault(attr1, {})
    #    for attr2 in dim_dependent:
    #        reset_graph_edges[attr1][attr2] = True
    
    for attr in component_dim_determiners:
        reset_graph_edges.setdefault(attr, {})
        reset_graph_edges[attr]["slider_component_dimensions"] = True
    reset_graph_edges.setdefault("slider_component_dimensions", {})
    for attr in component_dim_dependent:
        reset_graph_edges["slider_component_dimensions"][attr] = True
    
    #custom_attribute_change_propogation_methods = {
    #    "val_raw": "customValueRawChangePropogation",
    #}
    
    attribute_calculation_methods = {
        "mouse_enablement": "calculateMouseEnablement",
        "slider_component_dimensions": "calculateComponentDimensions",
        "track_topleft": "calculateTrackTopleft",
        "track_shape": "calculateTrackShape",
        "thumb_radius": "calculateThumbRadius",
        "demarc_numbers_max_height": "calculateDemarcNumbersMaxHeight",
        "val_range_actual": "calculateValueRangeActual",
        "x_range": "calculateXRange",
        "val": "calculateValue",
        "thumb_x": "calculateThumbX",
        "thumb_x_screen": "calculateThumbXScreen",
        "slider_ranges_surf": "calculateSliderRangesSurface",
        "slider_ranges_screen": "calculateSliderRangesScreen",
        
        "static_bg_surf": "createStaticBackgroundSurface",
        "track_surf": "createTrackSurface",
        "demarc_numbers_text_objects": "createDemarcationNumbersTextObjects",
        "demarc_surf": "createDemarcationSurface",
        "thumb_surf": "createThumbSurface",
        #"display_surf": "createDisplaySurface",
        
        "track_img_constructor": "createTrackImageConstructor",
        "demarc_img_constructor": "createDemarcationsImageConstructor",
        "static_bg_img_constructor": "createStaticBackgroundImageConstructor",
        "thumb_img_constructor": "createThumbImageConstructor",
    }
    
    @staticmethod
    def demarcNumsTextGroup():
        #print("\ncreating TextGroup for the final Slider object")
        res = Slider.createDemarcationNumbersTextGroup(max_height=None)#self.demarc_numbers_max_height)
        #print("finished creating TextGroup for final Slider object")
        return res
    
    attribute_default_functions = {
        "increment": ((lambda obj: 0),),
        "val_raw": ((lambda obj: -float("inf")),),
        "demarc_numbers_text_group": ((lambda obj: TextGroup.createDefaultTextGroup()),),#((lambda obj: Slider.demarcNumsTextGroup()),),#createDemarcationNumbersTextGroup()),),
        "demarc_numbers_dp": (sliderDemarcationsDPDefault, ("demarc_intervals", "demarc_start_val", "increment", "increment_start")),
        "thumb_radius_rel": ((lambda obj: 1),),
        "demarc_line_lens_rel": ((lambda obj: tuple(0.5 ** i for i in range(10))),),
        "demarc_intervals": (sliderDemarcationsIntervalDefault, ("val_range", "increment", "increment_start")),
        "demarc_start_val": ((lambda obj: obj.val_range[0]), ("val_range",)),
        "demarc_numbers_max_height_rel": ((lambda obj: 2),),
        
        "demarc_numbers_color": ((lambda obj: text_color_def),),
        "track_color": ((lambda obj: track_color_def),),
        "demarc_line_colors": ((lambda obj: (obj.track_color,)), ("track_color",)),
        "thumb_color": ((lambda obj: thumb_color_def),),
        "thumb_outline_color": ((lambda obj: ()),),
        
        "mouse_enabled": ((lambda obj: True),),
    }
    
    fixed_attributes = set()
    static_bg_components = ["track", "demarc"]
    displ_component_attrs = ["static_bg", "thumb"]
    
    def __init__(self,
        shape: Tuple[Real],
        anchor_rel_pos: Tuple[Real],
        val_range: Tuple[Real],
        increment_start: Real,
        increment: Optional[Real]=None,
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        init_val: Optional[Real]=None,
        demarc_numbers_text_group: Optional["TextGroup"]=None,
        demarc_numbers_dp: Optional[int]=None,
        thumb_radius_rel: Optional[Real]=None,
        demarc_line_lens_rel: Optional[Tuple[Real]]=None,
        demarc_intervals: Optional[Tuple[Real]]=None,
        demarc_start_val: Optional[Real]=None,
        demarc_numbers_max_height_rel: Optional[Real]=None,
        track_color: Optional[ColorOpacity]=None,
        thumb_color: Optional[ColorOpacity]=None,
        demarc_numbers_color: Optional[ColorOpacity]=None,
        demarc_line_colors: Optional[ColorOpacity]=None,
        thumb_outline_color: Optional[ColorOpacity]=None,
        mouse_enabled: Optional[bool]=None,
        name: Optional[str]=None,
        **kwargs,
    ) -> None:
        #print("Creating Slider")
        checkHiddenKwargs(type(self), kwargs)
        if name is None:
            Slider.unnamed_count += 1
            name = f"slider {self.unnamed_count}"
        #self.name = name
        Slider.slider_names.add(name)
        kwargs2 = self.initArgsManagement(locals(), kwargs=kwargs, rm_args=["init_val"])
        super().__init__(**kwargs2, slider_held=False, val_raw=init_val)
    
    #def setMouseEnabled(self, prev_val: bool) -> None:
    #    #print("using method setMouseEnablement()")
    #    mouse_enabled = self.mouse_enabled
    #    self.mouse_enablement = (mouse_enabled, mouse_enabled, mouse_enabled)
    #    #print(f"self.mouse_enablement = {self.mouse_enablement}")
    #    return

    def setAttributes(self, setattr_dict: Dict[str, Any], _from_container: bool=False, _calculated_override: bool=False, **kwargs) -> Dict[str, Tuple[Any, Any]]:
        changed_attrs_dict = super().setAttributes(setattr_dict, _from_container=_from_container, _calculated_override=_calculated_override, **kwargs)
        #if changed_attrs_dict:
        #    print(f"setAttributes() called for {self} with setattr_dict = {setattr_dict}\nchanged_attrs_dict = {changed_attrs_dict}")
        #if "_display_surf" in self.__dict__.keys():
        #    print(f"self._display_surf = {self.__dict__['_display_surf']}")
        return changed_attrs_dict

    def setValueDirectly(self, new_val: Real) -> None:
        #print(f"new_val = {new_val}")
        thumb_x_screen_raw = getattr(self, "thumb_x_screen_raw", None)
        if thumb_x_screen_raw is not None:
            # Ensuring that val_raw is reset in the case where the value
            # specified is identical to the previous one when the actual
            # value has been changed in the meantime by the setting of
            # thumb_x_screen_raw to a new value
            self.val_raw = None
            self.val_raw
        #self.val_raw = None
        #self.val_raw
        self.val_raw = new_val
        #print(f"new_val = {new_val}, self.val_raw = {self.val_raw}")
        return
    
    def calculateMouseEnablement(self) -> None:
        #print("calculating mouse enablement")
        mouse_enabled = self.mouse_enabled
        return (mouse_enabled, mouse_enabled, mouse_enabled)
    
    def customValueRawChangePropogation(self, new_val: Real, prev_val: Real) -> None:
        #print("Using customValueRawChangePropogation()")
        self.__dict__["_thumb_x_screen_raw"] = None
        chng_dict = self.getPendingAttributeChanges()
        if "thumb_x_screen_raw" in chng_dict.keys():
            chng_dict.pop("thumb_x_screen_raw")
        return
    
    def calculateValueRangeActual(self) -> Tuple[Real]:
        increment = self.increment
        increment_start = self.increment_start
        val_range = self.val_range
        if not increment:
            return val_range
        vra = [val_range[0] if increment_start is None else\
                increment_start + math.ceil((val_range[0] - increment_start) / increment) * increment]
        vra.append(vra[0] + math.floor((val_range[1] - vra[0]) / increment) * increment)
        return tuple(vra)
    
    def calculateXRange(self) -> Tuple[int]:
        return tuple(map(self.val2X, self.val_range_actual))
    
    def calculateValue(self) -> Real:
        #print("calculating value")
        #thumb_x_screen_raw = self.__dict__.get("_thumb_x_screen_raw", self.getPendingAttributeChanges().get("thumb_x_screen_raw", None))#getattr(self, "thumb_x_screen_raw", None) #__dict__.get("_thumb_x_screen_raw", None)
        thumb_x_screen_raw = getattr(self, "thumb_x_screen_raw", None)
        #print(f"thumb_x_screen_raw = {thumb_x_screen_raw}")
        if thumb_x_screen_raw is not None:
            return self.x2Val(thumb_x_screen_raw - self.screen_topleft_to_component_topleft_offset[0])
        return self.findNearestValue(self.val_raw)
    
    def calculateThumbX(self) -> int:
        #print("Using calculateThumbX()")
        #print(f"new thumb x value = {self.val2X(self.val)}")
        return self.val2X(self.val)
    
    def calculateThumbXScreen(self) -> int:
        #print("Using calculateThumbXScreen()")
        return () if self.thumb_x == () else self.thumb_x + self.screen_topleft_to_component_topleft_offset[0]
    
    #def createDemarcationNumbersTextGroup(self, max_height: Optional[Real]=None) -> "TextGroup":
    #    text_group = self.__dict__.get("_demarc_numbers_text_group", None)
    #    font = None if text_group is None else text_group.font
    #    return self._createDemarcationNumbersTextGroupGivenFontAndMaxHeight(font=font, max_height=max_height)
    
    @staticmethod
    def createDemarcationNumbersTextGroup(
        font: Optional["pg.freetype"]=None,
        max_height: Optional[int]=None,
    ) -> "TextGroup":
        #print("hello")
        dig_txt_lst = [str(d) for d in range(10)]
        dig_txt_lst.append(".")
        text_list = [{"text": "".join(dig_txt_lst)}]
        if font is None:
            font = font_def_func()
        #text_list = [{"text": str(d)} for d in range(10)]
        return TextGroup(text_list,\
                max_height0=max_height, font=font,\
                font_size=None, min_lowercase=True,\
                text_global_asc_desc_chars=None)
    
    def createDemarcationNumbersTextGroupCurrentFont(
        self,
        max_height: Optional[int]=None,
    ) -> "TextGroup":
        text_group = self.__dict__.get("_demarc_numbers_text_group", None)
        font = None if text_group is None else text_group.font
        return self.createDemarcationNumbersTextGroup(font=font, max_height=max_height)
    
    def findNearestValue(self, val: Real):
        vra = self.val_range_actual
        if val <= vra[0]:
            return vra[0]
        elif val >= vra[1]:
            return vra[1]
        elif not self.increment:
            return val
        return vra[0] + round((val - vra[0]) / self.increment) * self.increment
    
    @staticmethod
    def _calculateMultipleSliderComponentDimensions(slider_objs: List["Slider"], slider_shape: Tuple[int, int], demarc_numbers_max_height_rel: Optional[Real], demarc_line_lens_rel: Tuple[Real], thumb_radius_rel: Real, demarc_numbers_min_gap_rel_height: Real=1, demarc_numbers_min_gap_pixel: int=0) -> Tuple[Union[Tuple[Real], Real]]:
        #print("using _calculateMultipleSliderComponentDimensions()")
        #text_obj_lists: List[Tuple[List[Tuple["TextGroupElement", Real]]]
        #print(len(slider_objs))
        y0 = 0
        y_sz0 = slider_shape[1]
        y_sz_ratio = demarc_numbers_max_height_rel + (3 * demarc_line_lens_rel[0] / 2) + 1 + max(thumb_radius_rel - 0.5, 0)
        track_y_sz = math.floor(y_sz0 / y_sz_ratio)
        track_topleft_y = y0 + math.ceil(track_y_sz * max(thumb_radius_rel - 0.5, 0))
        thumb_radius = math.ceil(track_y_sz * thumb_radius_rel)
        
        min_end_gaps = (thumb_radius, thumb_radius)
        #min_demarc_numbers_gap = 10

        text_h_max = math.floor(demarc_numbers_max_height_rel * track_y_sz)

        slider_text_grp_lst = []
        slider_text_objs_lst = []
        for slider in slider_objs:
            if slider is None: continue
            text_grp = slider.createDemarcationNumbersTextGroupCurrentFont(max_height=text_h_max)
            text_objs = slider._createDemarcationNumbersTextObjectsGivenTextGroupAndMaxHeight(demarc_numbers_text_group=text_grp, max_height=None)
            #print(f"text_objs = {text_objs}")
            slider_text_grp_lst.append((slider, text_grp))
            slider_text_objs_lst.append((slider, text_objs))
        
        def setTextHeight(new_text_height: int):
            for (_, text_grp) in slider_text_grp_lst:
                text_grp.max_height0 = new_text_height
            return
        
        #print(f"text_h_max = {text_h_max}")
        def textHeightAllowed(text_h: int) -> bool:
            setTextHeight(text_h)
            track_x_size = Slider._maxXTrackDimensionsGivenTextObjects(slider_text_objs_lst, max_x_size=slider_shape[0], min_gaps=min_end_gaps)[1]
            min_demarc_gap = max(demarc_numbers_min_gap_rel_height * text_h, demarc_numbers_min_gap_pixel)
            for (slider, text_objs) in slider_text_objs_lst:
                if slider._numbersOverlapGivenTrackXSizeAndTextHeight(text_objs, val_range=slider.val_range, track_x_size=track_x_size, text_height=text_h, min_gap=min_demarc_gap):
                    return False
            return True
        lft, rgt = 0, text_h_max
        while lft < rgt:
            mid = lft - ((lft - rgt) >> 1)
            if textHeightAllowed(mid):
                lft = mid
            else: rgt = mid - 1
        new_text_h = lft
        setTextHeight(new_text_h)
        end_gaps, track_x_sz = Slider._maxXTrackDimensionsGivenTextObjects(slider_text_objs_lst, max_x_size=slider_shape[0], min_gaps=min_end_gaps)
        track_topleft_x = end_gaps[0]
        return ((track_x_sz, track_y_sz), (track_topleft_x, track_topleft_y), thumb_radius, new_text_h)
    
    def calculateComponentDimensions(self) -> Tuple[Tuple[int, int], Tuple[int, int], Real]:
        #print("Using Slider method calculateComponentDimensions()")
        return self._calculateMultipleSliderComponentDimensions([self], slider_shape=self.shape, demarc_numbers_max_height_rel=self.demarc_numbers_max_height_rel, demarc_line_lens_rel=self.demarc_line_lens_rel, thumb_radius_rel=self.thumb_radius_rel, demarc_numbers_min_gap_rel_height=1, demarc_numbers_min_gap_pixel=0)

    """
    #def calculateTrackDimensions(self) -> Tuple[Real]:
    def calculateComponentDimensions(self) -> Tuple[Union[Tuple[Real], Real]]:
        #print("using calculateComponentDimensions()")
        #print("creating demarcation numbers text group")
        #print("\ncreating TextGroup to calculate Slider component dimensions")
        text_group = self.createDemarcationNumbersTextGroupCurrentFont()
        #print("finished creating TextGroup to calculate Slider component dimensions")
        #print("creating demarcation numbers text objects")
        #print("creating TextGroup elements to calculate Slider component dimensions")
        text_objs = self._createDemarcationNumbersTextObjectsGivenTextGroupAndMaxHeight(demarc_numbers_text_group=text_group, max_height=None)
        #print("finished creating TextGroup elements to calculate Slider component dimensions")
        #print("finished creating demarcation numbers text objects")
        res = self._calculateComponentDimensions([text_objs])
        #print(f"component dimensions = {res}")
        return res
    """
    
    def calculateTrackShape(self) -> Tuple[int, int]:
        return getattr(self, "slider_component_dimensions")[0]

    def calculateTrackTopleft(self) -> Tuple[int, int]:
        return getattr(self, "slider_component_dimensions")[1]

    def calculateThumbRadius(self) -> Real:
        return getattr(self, "slider_component_dimensions")[2]

    def calculateDemarcNumbersMaxHeight(self) -> Real:
        return getattr(self, "slider_component_dimensions")[3]
    
    """
    def setTrackDimensions(self, shape: Tuple[int], topleft: Tuple[int]) -> None:
        self._track_shape = shape
        self._track_topleft = topleft
        return
    
    def setThumbRadius(self, thumb_radius: int) -> None:
        self._thumb_radius = thumb_radius
        return
    
    def setDemarcationNumbersMaxHeight(self, height: int) -> None:
        self._demarc_numbers_max_height = height
        text_objs = getattr(self, "_demarc_numbers_text_objects", None)
        if text_objs is None:
            return
        for text_obj_tup in text_objs:
            text_obj_tup[0].max_height = height
        return
    """
    #def setComponentDimensions(self, track_shape: Tuple[int], track_topleft: Tuple[int], thumb_radius: int, text_height: int) -> None:
    #    self.setTrackDimensions(track_shape, track_topleft)
    #    self.setThumbRadius(thumb_radius)
    #    self.setDemarcationNumbersMaxHeight(text_height)
    #    return
    
    #def calculateAndSetTrackDimensions(self) -> None:
    #def calculateAndSetComponentDimensions(self) -> Optional[Tuple[Union[Tuple[Real], Real]]]:
    #    res = self.calculateComponentDimensions()
    #    self.setComponentDimensions(*res)
    #    return res
    
    @staticmethod
    def _maxXTrackDimensionsGivenTextObjects(slider_text_objs_list: List[Tuple["Slider", List[Tuple["Text", Real]]]], max_x_size: int, min_gaps: Tuple[int]=(0, 0)) -> Tuple[Union[Tuple[int], int]]:
        #mx_w = self.shape[0]
        #mx_w = max_width
        
        text_end_pairs = []
        for slider, text_objs in slider_text_objs_list:
            if not text_objs: continue
            #print(text_objs)
            text_obj1, val1 = text_objs[0]
            text_obj2, val2 = text_objs[-1]
            text_end_pairs.append((slider, ((text_obj1, val1, -text_obj1.calculateTopleftEffective((0, 0), anchor_type="midtop")[0]),\
                    (text_obj2, val2, text_obj2.calculateTopleftEffective((0, 0), anchor_type="midtop")[0] + text_obj2.shape_eff[0]))))
        if not text_end_pairs:
            gaps = tuple(math.ceil(gap) for gap in min_gaps)
            return (gaps, max_x_size - sum(gaps))
        
        #print(text_end_pairs)
        #print(min_gaps)
        def trackEndGaps(track_width: int) -> Tuple[int]:
            gaps = list(min_gaps)
            for slider, pair in text_end_pairs:
                (text_obj1, val1, gap1), (text_obj2, val2, gap2) = pair
                gaps[0] = max(gaps[0], gap1 - slider.val2TrackLeftDistGivenTrackWidth(val1, track_width))
                gaps[1] = max(gaps[1], gap2 - track_width + slider.val2TrackLeftDistGivenTrackWidth(val2, track_width))
            return tuple(math.ceil(gap) for gap in gaps)
        
        lft, rgt = 0, max_x_size - sum(min_gaps)
        while lft < rgt:
            mid = lft - ((lft - rgt) >> 1)
            gaps = trackEndGaps(mid)
            #print(mid, gaps, mid + sum(gaps))
            if mid + sum(gaps) <= max_x_size:
                lft = mid
            else: rgt = mid - 1
        x_sz_mx = lft
        gaps = trackEndGaps(x_sz_mx)
        #print(f"max track x dimension calculated by _maxXTrackDimensionsGivenTextObjects() = {x_sz_mx}, max_x_size = {max_x_size}")
        return (gaps, x_sz_mx)
    
    """
    def maxXTrackDimensionsGivenTextHeight(self, text_height: int, min_gaps: Tuple[int]=(0, 0)) -> Tuple[Union[Tuple[int], int]]:
        #print("\nUsing maxXTrackDimensionsGivenTextHeight()")
        #print(f"text_height = {text_height}")
        #print("\ncreating TextGroup to calculate Slider x-dimension for a given text height")
        text_group = self.createDemarcationNumbersTextGroupCurrentFont(max_height=text_height)
        #text_group = Slider.createDemarcationNumbersTextGroup(font, max_height=text_height)
        #print("finished creating TextGroup to calculate Slider x-dimension for a given text height")
        #print("creating TextGroup elements to calculate Slider x-dimension for a given text height")
        text_obj_lists = [(self, self._createDemarcationNumbersTextObjectsGivenTextGroupAndMaxHeight(demarc_numbers_text_group=text_group, max_height=None))]
        #print("finished creating TextGroup elements to calculate Slider x-dimension for a given text height")
        #res = _maxXTrackDimensionsGivenTextObjects(text_obj_lists: List[Tuple["Slider", List[Tuple["Text", Real]]]], max_width: int, min_gaps: Tuple[int]=(0, 0))
        res = self._maxXTrackDimensionsGivenTextObjects(text_obj_lists, max_x_size=self.shape[0], min_gaps=min_gaps)
        #print("finished calculating Slider x-dimension")
        #print(f"calculated max track x dimension = {res}")
        return res
    """
    # Review- try to make a static method
    def _numbersOverlapGivenTrackXSizeAndTextHeight(self, text_objs: List[Tuple["Text", Real]], val_range: Tuple[Real, Real], track_x_size: int, text_height: int, min_gap: int=2) -> bool:
        if not text_objs:
            return False
        text_group = text_objs[0][0].text_group
        text_group.max_height0 = text_height
        curr_right = -float("inf")
        #_val2TrackLeftDistGivenTrackWidth(val: Real, track_width: int, val_range: Tuple[Real, Real])
        for text_obj_tup in text_objs:
            text_obj, val = text_obj_tup
            curr_left = text_obj.calculateTopleftEffective((self._val2TrackLeftDistGivenTrackWidth(val, track_x_size, val_range), 0), anchor_type="midtop")[0]
            if curr_left <= curr_right + min_gap:
                return True
            curr_right = curr_left + text_obj.shape_eff[0]
        return False
    """
    def maxTextHeightGivenTrackWidth(self, track_width: int, text_height_max: Optional[int]=None, min_gap: int=2) -> Union[int, bool]:
        #if not self.demarc_numbers_text_objects:
        #    return 0
        if text_height_max is None:
            text_height_max = self.shape[1]
        
        print("\ncreating TextGroup to calculate max Slider text height for a given track width")
        text_group = self.createDemarcationNumbersTextGroupCurrentFont()
        print("finished creating TextGroup to calculate max Slider text height for a given track width")
        print("creating TextGroup elements to calculate max Slider text height for a given track width")
        text_objs = self.createDemarcationNumbersTextObjects(demarc_numbers_text_group=text_group)
        print("finished creating TextGroup elements to calculate max Slider text height for a given track width")
        if not text_objs: return 0
        
        def numbersOverlap(text_height: int) -> bool:
            return self._numbersOverlapGivenTrackXSizeAndTextHeight(text_objs, track_width, text_height, min_gap=min_gap)
        
        if not numbersOverlap(text_height_max):
            return text_height_max
        
        lft, rgt = 0, text_height_max
        while lft < rgt:
            #print()
            mid = lft - ((lft - rgt) >> 1)
            #print(lft, rgt, mid)
            if numbersOverlap(mid):
                rgt = mid - 1
            else: lft = mid
        #print(f"text_height = {lft}")
        return lft
    """
    def createTrackSurface(self) -> "pg.Surface":
        #print("creating track surface")
        if not self.track_color: return ()
        shape = [x + 1 - i for i, x in enumerate(self.track_shape)]
        track_surf = pg.Surface(shape, pg.SRCALPHA)
        track_surf.set_alpha(self.track_color[1] * 255)
        track_surf.fill(self.track_color[0])
        return track_surf
    
    def createTrackImageConstructor(self) -> Callable[["pg.Surface"], None]:
        return lambda obj, surf: (None if obj.track_surf == () else surf.blit(obj.track_surf, obj.track_topleft))
    
    
    def resetDemarcationNumbersTextObjects(self) -> None:
        text_objs = getattr(self, "_demarc_numbers_text_objects", None)
        if not text_objs: return
        self.demarc_numbers_text_group.removeTextObjects([x[0] for x in text_objs])
        self._demarc_numbers_text_objects = None
        return
    
    def createDemarcationNumbersTextObjects(self)\
            -> List[Tuple["Text", Real]]:
        #print("using createDemarcationNumbersTextObjects()")
        demarc_numbers_text_group = self.demarc_numbers_text_group
        max_height = self.demarc_numbers_max_height
        #print(f"max_height = {max_height}")
        res = self._createDemarcationNumbersTextObjectsGivenTextGroupAndMaxHeight(demarc_numbers_text_group, max_height=max_height, displ_text=True)
        #if res:
        #    print(f"text object reset functions = {getattr(res[0][0], '_attr_reset_funcs', None)}")
        return res
    
    def _createDemarcationNumbersTextObjectsGivenTextGroupAndMaxHeight(
        self,
        demarc_numbers_text_group: "TextGroup",
        max_height: Optional[Real]=None,
        displ_text: bool=False,
    ) -> List[Tuple["Text", Real]]:
        #print("creating demarcation numbers text objects")
        if not self.demarc_intervals:
            return []
        #if demarc_numbers_text_group is None:
        #    demarc_numbers_text_group = self.demarc_numbers_text_group
        intvl = self.demarc_intervals[0]
        val_start = self.demarc_start_val + math.ceil((self.val_range[0] - self.demarc_start_val) / intvl) * intvl
        #print(f"val_start = {val_start}")
        val = val_start
        add_text_dicts = []
        dp = self.demarc_numbers_dp
        color = self.demarc_numbers_color
        vals = []
        #def updateFunction(obj: "Slider", prev_val: Optional["Text"]) -> None:
        #    #print("updated text")
        #    setattr(obj, "demarc_surf", None)
        #    return
        #print(f"demarc numbers font size actual = {demarc_numbers_text_group.font_size_actual}, {self}")
        while val <= self.val_range[1]:
            val_txt = f"{val:.{dp}f}"
            add_text_dict = {"text": val_txt, "font_color": color}
            if max_height is not None:
                add_text_dict["max_shape"] = (None, max_height)
            if displ_text:
                #print("hi")
                #add_text_dict["_attr_reset_funcs"] = {"updated": [updateFunction]}
                add_text_dict["_from_container"] = True
                add_text_dict["_container_obj"] = self
                add_text_dict["_container_attr_reset_dict"] = {"updated": {"demarc_surf": (lambda container_obj, obj: getattr(obj, "updated", False))}}
            add_text_dicts.append(add_text_dict)
            vals.append(val)
            val += self.demarc_intervals[0]
        #print(add_text_dicts)
        #print(demarc_numbers_text_group.max_height)
        res = list(zip(demarc_numbers_text_group.addTextObjects(add_text_dicts), vals))
        #print("added text objects")
        #print(demarc_numbers_text_group.max_height)
        return res
    
    def createDemarcationSurface(self) -> Union["pg.Surface", tuple]:
        #print("creating demarcation surface")
        demarc_intvls = self.demarc_intervals
        if not demarc_intvls: return ()
        line_lens_rel = self.demarc_line_lens_rel
        #if not line_lens_rel: return ()
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        
        line_upper_y = self.track_topleft[1] + self.track_shape[1]
        line_colors = self.demarc_line_colors
        line_lens = tuple(round(self.track_shape[1] * x) for x in line_lens_rel)
        
        numbers_color = self.demarc_numbers_color
        numbers_upper_y = int(line_upper_y + line_lens[0] * 1.5)
        numbers_height = self.demarc_numbers_max_height #self.demarc_number_size_rel * self.track_shape[1]
        
        seen_x = set()
        
        def lineRenderer(line_idx: int) -> List[int]:
            if not line_lens_rel: return []
            line_surf = pg.Surface(self.shape, pg.SRCALPHA)
            line_x_vals = []
            line_color = line_colors[min(line_idx, len(line_colors) - 1)] if line_colors else ()
            line_len = line_lens[min(line_idx, len(line_lens) - 1)] if line_lens else 0
            intvl = demarc_intvls[line_idx]
            val = self.demarc_start_val + math.ceil((self.val_range[0] - self.demarc_start_val) / intvl) * intvl
            while val <= self.val_range[1]:
                line_x = round(self.val2X(val))
                line_x_vals.append(line_x)
                if line_len and line_color and line_x not in seen_x:
                    seen_x.add(line_x)
                    line_y_rng = [round(line_upper_y + dy) for dy in (0, line_len)]
                    #print(f"drawing line {[(line_x, y) for y in line_y_rng]} with color {line_color[0]}")
                    pg.draw.line(line_surf, line_color[0], *[(line_x, y) for y in line_y_rng])
                val += intvl
            line_surf.set_alpha(255 * line_color[1])
            surf.blit(line_surf, (0, 0))
            return line_x_vals
            
        x_lst = lineRenderer(0)
        for x, text_obj_tup in zip(x_lst, self.demarc_numbers_text_objects):
            text_obj = text_obj_tup[0]
            anchor_rel_pos = (x, numbers_upper_y)
            #print(f"numbers_height = {numbers_height}")
            text_obj.max_shape = (None, numbers_height)
            #print(f"text_obj shape = {text_obj.shape}")
            text_obj.draw(surf, anchor_rel_pos=anchor_rel_pos, anchor_type="midtop")
        
        for line_idx in range(1, len(demarc_intvls)):
            lineRenderer(line_idx)
    
        return surf
    
    def createDemarcationsImageConstructor(self)\
            -> Callable[["pg.Surface"], None]:
        return lambda obj, surf: (None if obj.demarc_surf == () else surf.blit(obj.demarc_surf, (0, 0)))
    
    def createStaticBackgroundSurface(self)\
            -> Union["pg.Surface", tuple]:
        #print("creating static background surface")
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        #surf.set_alpha(255)
        #surf.fill((255, 0, 0))
        
        constructor_attrs = [f"{attr}_img_constructor"\
                for attr in self.static_bg_components]
        #print(constructor_attrs)
        for constructor_attr in constructor_attrs:
            
            constructor_func =\
                    getattr(self, constructor_attr, (lambda obj, surf: None))
            #print(constructor_attr)
            constructor_func(self, surf)
        return surf
    
    def createStaticBackgroundImageConstructor(self)\
            -> Callable[["pg.Surface"], None]:
        return lambda obj, surf: (None if obj.static_bg_surf == () else surf.blit(obj.static_bg_surf, (0, 0)))
        
    def createThumbSurface(self) -> Union["pg.Surface", tuple]:
        thumb_color = self.thumb_color
        if not thumb_color:
            return ()
        rad = self.thumb_radius
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        pg.draw.circle(surf, thumb_color[0], (rad, rad), rad)
        surf.set_alpha(thumb_color[1] * 255)
        return surf
    
    def createThumbImageConstructor(self)\
            -> Callable[["pg.Surface"], None]:
        def thumbRenderer(obj: "Slider", surf: "pg.Surface") -> None:
            if obj.thumb_surf == () or obj.thumb_x == ():
                return
            topleft = (obj.thumb_x - obj.thumb_radius, obj.track_topleft[1] + (obj.track_shape[1] / 2) - obj.thumb_radius)
            #print(f"thumb topleft = {topleft}")
            surf.blit(obj.thumb_surf, topleft)
            return
        return thumbRenderer
    
    def createDisplaySurface(self) -> Optional["pg.Surface"]:
        #print(f"creating display surface for Slider object {self}")
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        for attr in self.displ_component_attrs:
            #print(f"{attr}_img_constructor")
            constructor_func = getattr(self, f"{attr}_img_constructor", (lambda obj, surf: None))
            #print(f"  {attr}, {surf}")
            constructor_func(self, surf)
        #print(f"surf = {surf}")
        return surf
    
    #def draw(self, surf: "pg.Surface") -> None:
    #    #print("\ndrawing slider")
    #    #print("display_surf" in self.__dict__.keys())
    #    #print(self.__dict__.get("display_surf", None))
    #    #print("_display_surf" in self.__dict__.keys())
    #    #print(self.__dict__.get("_display_surf", None))
    #    #print(f"self.display_surf = {self.display_surf}")
    #    #print("display_surf" in self.__dict__.keys())
    #    #print(self.__dict__.get("display_surf", None))
    #    #print("_display_surf" in self.__dict__.keys())
    #    #print(self.__dict__.get("_display_surf", None))
    #    surf.blit(self.display_surf, self.topleft_rel_pos)
    #    return
    
    @staticmethod
    def _val2TrackLeftDistGivenTrackWidth(val: Real, track_width: int, val_range: Tuple[Real, Real]) -> int:
        return round(track_width * (val - val_range[0]) / (val_range[1] - val_range[0]))
    
    def val2TrackLeftDistGivenTrackWidth(self, val: Real, track_width: int) -> int:
        return self._val2TrackLeftDistGivenTrackWidth(val, track_width, self.val_range)
        #return round(track_width * (val - self.val_range[0]) / (self.val_range[1] - self.val_range[0]))
    
    def val2X(self, val: Union[Real, tuple]) -> Union[int, tuple]:
        if isinstance(val, tuple): return ()
        return self.track_topleft[0] +\
                self.val2TrackLeftDistGivenTrackWidth(val, self.track_shape[0])
    
    def x2Val(self, x):
        x_range = self.x_range
        vra = self.val_range_actual
        if x < x_range[0]:
            return vra[0]
        elif x > x_range[1]:
            return vra[1]
        elif not self.increment:
            return vra[0] + ((vra[1] - vra[0]) * ((x - x_range[0]) / float(x_range[1] - x_range[0])))
        return vra[0] + round((vra[1] - vra[0]) * ((x - x_range[0]) / (self.increment * (x_range[1] - x_range[0])))) * self.increment
    
    def calculateSliderRangesSurface(self) -> Tuple[Tuple[Real]]:
        #print("Using calculateSliderRangesSurface()")
        y_extend = max(1, self.thumb_radius_rel - 1) * self.track_shape[1]
        x_extend = self.thumb_radius_rel * self.track_shape[1]
        return ((self.track_topleft[0] - x_extend, self.track_topleft[0] + self.track_shape[0] + x_extend), (self.track_topleft[1] - y_extend, self.track_topleft[1] + self.track_shape[1] + y_extend))
    
    def calculateSliderRangesScreen(self) -> Tuple[Tuple[Real]]:
        #print("Using calculateSliderRangesScreen()")
        res = self.rangesSurface2RangesScreen(self.slider_ranges_surf)
        #print(f"new slider ranges screen = {res}")
        return res

    
    def mouseOverSlider(self, mouse_pos: Tuple[int], check_axes: Tuple[int]=(0, 1)):
        #print("checking mouseOverSlider()")
        rngs = self.slider_ranges_screen
        #print(rngs, mouse_pos)
        #print(mouse_pos, rngs, self.slider_ranges_surf, self.screen_topleft_to_parent_topleft_offset)
        res = all(rngs[i][0] <= mouse_pos[i] <= rngs[i][1] for i in check_axes)
        #print(f"mouse over slider = {res}")
        return res
    
    def processEvents(self, events: List[Tuple[int]]) -> List[Tuple[int]]:
        res = []
        for event_tup in events:
            if 2 <= event_tup[1] <= 3 and event_tup[0].button == 1:
                res.append((event_tup[0].pos, event_tup[1]))
        return res
    
    def eventLoop(self, events: Optional[List[int]]=None,\
            keys_down: Optional[List[int]]=None,\
            mouse_status: Optional[Tuple[int]]=None,\
            check_axes: Tuple[int]=(0, 1))\
            -> Tuple[bool, bool, bool, Any]:
        #print("calling Slider eventLoop()")
        #print(events)
        ((quit, esc_pressed), (events, keys_down, mouse_status, check_axes)) = self.getEventLoopArguments(events=events, keys_down=keys_down, mouse_status=mouse_status, check_axes=check_axes)
        #print(events, mouse_status)
        running = not quit and not esc_pressed
        screen_changed = False
        
        """
        quit = False
        running = True
        screen_changed = False
        
        if events is None:
            quit, esc_pressed, events = user_input_processor.getEvents()
            if esc_pressed or quit:
                running = False
        
        if mouse_status is None:
            mouse_status = user_input_processor.getMouseStatus() if self.mouse_enablement[0] else ()
        """
        slider_held = self.slider_held
        thumb_x_screen_raw_changed = False
        for event_tup in self.processEvents(events):
            if event_tup[1] == 2:
                slider_held = self.mouseOverSlider(event_tup[0], check_axes=check_axes)
                #print(f"slider_held = {slider_held}")
            elif event_tup[1] == 3 and slider_held:
                thumb_x_screen_raw_changed = True
                thumb_x_screen_raw = event_tup[0][0]
                slider_held = False
        #print(mouse_status)
        slider_held = slider_held and mouse_status and mouse_status[1][0]
        #print(f"slider_held 2 = {slider_held}")
        if slider_held:
            thumb_x_screen_raw_changed = True
            thumb_x_screen_raw = mouse_status[0][0]
        
        self.slider_held = slider_held

        if thumb_x_screen_raw_changed:
            #thumb_x0 = self.thumb_x
            self.thumb_x_screen_raw = thumb_x_screen_raw
            #screen_changed = (self.thumb_x != thumb_x0)
        #else: screen_changed = False
        screen_changed = self.drawUpdateRequired()
        #print(screen_changed)
        #print(screen_changed, self.slider_held, self.val)
        return quit, running, screen_changed, self.val

class SliderGroupElement(ComponentGroupElementBaseClass, Slider):
    
    group_cls_func = lambda: SliderGroup
    group_obj_attr = "slider_group"
    #fixed_attributes = {group_obj_attr}
    
    def __init__(
        self,
        slider_group: "SliderGroup",
        anchor_rel_pos: Tuple[Real],
        val_range: Tuple[Real],
        increment_start: Real,
        increment: Optional[Real]=None,
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        init_val: Optional[Real]=None,
        demarc_numbers_dp: Optional[int]=None,
        demarc_intervals: Optional[Tuple[Real]]=None,
        demarc_start_val: Optional[Real]=None,
        mouse_enabled: Optional[bool]=None,
        name: Optional[str]=None,
        **kwargs,
    ) -> None:
        
        checkHiddenKwargs(type(self), kwargs)
        
        #self.__dict__[f"_{self.group_obj_attr}"] = slider_group
        super().__init__(
            shape=slider_group.slider_shape,
            anchor_rel_pos=anchor_rel_pos,
            val_range=val_range,
            increment_start=increment_start,
            increment=increment,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=screen_topleft_to_parent_topleft_offset,
            init_val=init_val,
            demarc_numbers_text_group=slider_group.demarc_numbers_text_group,
            demarc_numbers_dp=demarc_numbers_dp,
            thumb_radius_rel=slider_group.thumb_radius_rel,
            demarc_line_lens_rel=slider_group.demarc_line_lens_rel,
            demarc_intervals=demarc_intervals,
            demarc_start_val=demarc_start_val,
            demarc_numbers_max_height_rel=slider_group.demarc_numbers_max_height_rel,
            track_color=slider_group.track_color,
            thumb_color=slider_group.thumb_color,
            demarc_numbers_color=slider_group.demarc_numbers_color,
            demarc_line_colors=slider_group.demarc_line_colors,
            thumb_outline_color=slider_group.thumb_outline_color,
            mouse_enabled=mouse_enabled,
            name=name,
            _group=slider_group,
            **kwargs,
        )
    
    """
    def calculateComponentDimensions(self) -> Tuple[Union[Tuple[Real], Real]]:
        #print("\ncreating TextGroup to calculate SliderGroup component dimensions")
        text_group = self.createDemarcationNumbersTextGroupCurrentFont()
        #print("finished creating TextGroup to calculate SliderGroup component dimensions")
        #print("creating TextGroup elements to calculate SliderGroup component dimensions")
        text_obj_lists = [slider_weakref()._createDemarcationNumbersTextObjectsGivenTextGroupAndMaxHeight(demarc_numbers_text_group=text_group, max_height=None) for slider_weakref in self.slider_group._elements_weakref]
        #print("finished creating TextGroup elements to calculate SliderGroup component dimensions")
        return self._calculateComponentDimensions(text_obj_lists)
    
    def setComponentDimensions(self, track_shape: Tuple[int], track_topleft: Tuple[int], thumb_radius: int, text_height: int) -> None:
        for cls2 in type(self).mro()[1:]:
            if "setComponentDimensions" in cls2.__dict__.keys():
                ancestor_method = cls2.setComponentDimensions
                break
        else: return
        if ancestor_method is None:
            return
        for slider_weakref in self.slider_group._elements_weakref:
            ancestor_method(slider_weakref(), track_shape, track_topleft, thumb_radius, text_height)
        return
    
    def maxXTrackDimensionsGivenTextHeight(self, text_height: int, min_gaps: Tuple[int]=(0, 0)) -> Tuple[Union[Tuple[int], int]]:
        #print("\ncreating TextGroup to calculate SliderGroup x-dimension for a given text height")
        text_group = self.createDemarcationNumbersTextGroupCurrentFont(max_height=text_height)
        #print("finished creating TextGroup to calculate SliderGroup x-dimension for a given text height")
        #print("creating TextGroup elements to calculate SliderGroup x-dimension for a given text height")
        text_obj_lists = []
        for slider_weakref in self.slider_group._elements_weakref:
            text_obj_lists.append((slider_weakref(), slider_weakref()._createDemarcationNumbersTextObjectsGivenTextGroupAndMaxHeight(demarc_numbers_text_group=text_group, max_height=None)))
        #print("finished creating TextGroup elements to calculate SliderGroup x-dimension for a given text height")
        return self._maxXTrackDimensionsGivenTextObjects(text_obj_lists, max_x_size=self.shape[0], min_gaps=min_gaps)
    """
        
class SliderGroup(ComponentGroupBaseClass):
    group_element_cls_func = lambda: SliderGroupElement
    
    reset_graph_edges = {"slider_shape": {"slider_component_dimensions": True}}

    component_dim_determiners = ["shape", "demarc_numbers_max_height_rel", "thumb_radius_rel", "demarc_line_lens_rel"]
    for attr in component_dim_determiners:
        reset_graph_edges.setdefault(attr, {})
        reset_graph_edges[attr]["slider_component_dimensions"] = True
    
    """
    custom_attribute_change_propogation_methods = {
        "slider_shape": "setSliderShape",
        "demarc_numbers_text_group": "setDemarcationNumbersTextGroup",
        "thumb_radius_rel": "setThumbRadiusRelative",
        "demarc_line_lens_rel": "setDemarcationLineLengthsRelative",
        "demarc_numbers_max_height_rel": "setDemarcationNumbersMaxHeightRelative",
        "track_color": "setTrackColor",
        "thumb_color": "setThumbColor",
        "demarc_numbers_color": "setDemarcationNumbersColor",
        "demarc_line_colors": "setDemarcationLineColors",
        "thumb_outline_color": "setThumbOutlineColor",
        "mouse_enabled": "setMouseEnabled",
    }
    """
    attribute_calculation_methods = {
        "slider_component_dimensions": "calculateSliderComponentDimensions",
    }
    
    # Review- account for using element_inherited_attributes in ComponentGroupBaseClass
    attribute_default_functions = {
        attr: Slider.attribute_default_functions.get(attr) for attr in
        [
            "demarc_numbers_text_group",
            "thumb_radius_rel",
            "demarc_line_lens_rel",
            "demarc_numbers_max_height_rel",
            "track_color",
            "thumb_color",
            "demarc_numbers_color",
            "demarc_line_colors",
            "thumb_outline_color",
            #"mouse_enabled",
        ]
    }
    
    #fixed_attributes = {"sliders"}
    
    element_inherited_attributes = {
        "slider_shape": "shape",
        "slider_component_dimensions": "slider_component_dimensions",
        "demarc_numbers_text_group": "demarc_numbers_text_group",
        "thumb_radius_rel": "thumb_radius_rel",
        "demarc_line_lens_rel": "demarc_line_lens_rel",
        "demarc_numbers_max_height_rel": "demarc_numbers_max_height_rel",
        "track_color": "track_color",
        "demarc_numbers_color": "demarc_numbers_color",
        "demarc_line_colors": "demarc_line_colors",
        "thumb_outline_color": "thumb_outline_color",
        #"mouse_enabled": "mouse_enabled",
    }

    element_attributes_affecting_group_attributes = {
        "val_range": "slider_component_dimensions",
        "demarc_numbers_dp": "slider_component_dimensions",
        "demarc_intervals": "slider_component_dimensions",
        "demarc_start_val": "slider_component_dimensions",
    }
    # Review- consider transferring mouse_enabled to the group elements
    def __init__(self, 
        slider_shape: Tuple[Real],
        demarc_numbers_text_group: Optional["TextGroup"]=None,
        thumb_radius_rel: Optional[Real]=None,
        demarc_line_lens_rel: Optional[Tuple[Real]]=None,
        demarc_numbers_max_height_rel: Optional[Real]=None,
        track_color: Optional[ColorOpacity]=None,
        thumb_color: Optional[ColorOpacity]=None,
        demarc_numbers_color: Optional[ColorOpacity]=None,
        demarc_line_colors: Optional[ColorOpacity]=None,
        thumb_outline_color: Optional[ColorOpacity]=None,
        #mouse_enabled: Optional[bool]=None,
        **kwargs,
    ) -> None:
        checkHiddenKwargs(type(self), kwargs)
        
        kwargs2 = self.initArgsManagement(locals(), kwargs=kwargs)
        super().__init__(**kwargs2)
        
    
    def addSlider(
        self,
        anchor_rel_pos: Tuple[Real],
        val_range: Tuple[Real],
        increment_start: Real,
        increment: Optional[Real]=None,
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        init_val: Optional[Real]=None,
        demarc_numbers_dp: Optional[int]=None,
        demarc_intervals: Optional[Tuple[Real]]=None,
        demarc_start_val: Optional[Real]=None,
        mouse_enabled: Optional[bool]=None,
        name: Optional[str]=None,
        **kwargs,
    ) -> "SliderGroupElement":
        #print("Using SliderGroup method addSlider()")
        res = self._addElement(
            anchor_rel_pos=anchor_rel_pos,
            val_range=val_range,
            increment_start=increment_start,
            increment=increment,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=screen_topleft_to_parent_topleft_offset,
            init_val=init_val,
            demarc_numbers_dp=demarc_numbers_dp,
            demarc_intervals=demarc_intervals,
            demarc_start_val=demarc_start_val,
            mouse_enabled=mouse_enabled,
            name=name,
            **kwargs,
        )
        return res
    
    def calculateSliderComponentDimensions(self):
        #print("Using SliderGroup method calculateSliderComponentDimensions()")
        #print(len(self._elements_weakref))
        res = Slider._calculateMultipleSliderComponentDimensions(
            [slider_weakref() for slider_weakref in self._elements_weakref if slider_weakref is not None],
            slider_shape=self.slider_shape,
            demarc_numbers_max_height_rel=self.demarc_numbers_max_height_rel,
            demarc_line_lens_rel=self.demarc_line_lens_rel,
            thumb_radius_rel=self.thumb_radius_rel,
            demarc_numbers_min_gap_rel_height=1,
            demarc_numbers_min_gap_pixel=0,
        )
        #print(f"value = {res}")
        return res
        """
        #print("\ncreating TextGroup to calculate SliderGroup component dimensions")
        text_group = Slider.createDemarcationNumbersTextGroup(font=self.demarc_numbers_text_group, max_height=None)
        
        #print("finished creating TextGroup to calculate SliderGroup component dimensions")
        #print("creating TextGroup elements to calculate SliderGroup component dimensions")
        text_obj_lists = [slider_weakref()._createDemarcationNumbersTextObjectsGivenTextGroupAndMaxHeight(demarc_numbers_text_group=text_group, max_height=None) for slider_weakref in self._elements_weakref if slider_weakref is not None]
        #print("finished creating TextGroup elements to calculate SliderGroup component dimensions")
        return self._calculateComponentDimensions(text_obj_lists)
        """

class SliderPlus(InteractiveDisplayComponentBase):
    sliderplus_names = set()
    unnamed_count = 0
    
    reset_graph_edges = {
        "shape": {"slider_shape": True, "slider_bottomleft": True, "title_shape": True, "val_text_shape": True},
        "slider_shape_rel": {"slider_shape": True},
        "slider_borders_rel": {"slider_borders": True},
        "slider_shape": {"title_shape": True},
        "slider_borders": {"title_shape": True},
        "title_shape": {"title_anchor_rel_pos": (lambda obj: obj.title_anchor_type != "topleft"), "title_surf": True},
        "title_anchor_type": {"display_surf": True},
        "title_anchor_rel_pos": {"display_surf": True},
        "title_color": {"title_surf": True},

        "val": {"val_str": True},
        "val_text_dp": {"val_str": True},
        "val_str": {"val_text_surf": True},
        "val_text_color": {"val_text_surf": True},

        "val_text_shape": {"val_text_anchor_rel_pos": (lambda obj: obj.val_text_anchor_type != "topleft"), "val_text_surf": True},
        "val_text_anchor_type": {"display_surf": True},
        "val_text_anchor_rel_pos": {"display_surf": True},
        
        "title_surf": {"static_bg_surf": True},
        "val_text_surf": {"display_surf": True},
        "static_bg_surf": {"display_surf": True},
    }
    
    #custom_attribute_change_propogation_methods = {
    #    "title_shape": "setTitleShape",
    #}
    
    attribute_calculation_methods = {
        #"slider": "createSlider",
        "slider_shape": "calculateSliderShape",
        "slider_bottomleft": "calculateSliderBottomLeft",
        "slider_borders": "calculateSliderBorders",

        "val": "calculateValue",
        "val_str": "calculateValueString",

        #"title_text_group": "createTitleTextGroup",
        "title_shape": "calculateTitleShape",
        "title_anchor_rel_pos": "calculateTitleAnchorPosition",
        "title_text_obj": "createTitleTextObject",

        #"val_text_group": "createValueTextGroup",
        "val_text_shape": "calculateValueTextShape",
        "val_text_anchor_rel_pos": "calculateValueTextAnchorPosition",
        
        "title_surf": "createTitleSurface",
        "val_text_surf": "createValueTextSurface",
        "static_bg_surf": "createStaticBackgroundSurface",
        #"display_surf": "createDisplaySurface",
        
        "title_img_constructor": "createTitleImageConstructor",
        "val_text_img_constructor": "createValueTextImageConstructor",
        "static_bg_img_constructor": "createStaticBackgroundImageConstructor",
        "slider_img_constructor": "createSliderImageConstructor",
    }

    #@staticmethod
    #def valueTextGroup():
    #    #print("\ncreating TextGroup for the final Slider object")
    #    res = SliderPlus.createValueTextGroup(font=None, max_height=None)#self.demarc_numbers_max_height)
    #    #print("finished creating TextGroup for final Slider object")
    #    return res

    attribute_default_functions = {
        **{
            "slider_shape_rel": ((lambda obj: (0.7, 0.6)),),
            "slider_borders_rel": ((lambda obj: (0., 0.)),),
            "title_text_group": ((lambda obj: TextGroup.createDefaultTextGroup()),),
            "title_anchor_type": ((lambda obj: "topleft"),),
            "title_color": ((lambda obj: text_color_def),),
            "val_text_group": ((lambda obj: TextGroup.createDefaultTextGroup()),),
            "val_text_anchor_type": ((lambda obj: "topleft"),),
            "val_text_color": ((lambda obj: text_color_def),),
            "val_text_dp": (sliderPlusDemarcationsDPDefault, ("slider",)),
        },
        **{
            attr: Slider.attribute_default_functions.get(attr) for attr in
            [
                "increment",
                "val_raw",
                "demarc_numbers_text_group",
                "demarc_numbers_dp",
                "thumb_radius_rel",
                "demarc_line_lens_rel",
                "demarc_intervals",
                "demarc_start_val",
                "demarc_numbers_max_height_rel",
                "demarc_numbers_color",
                "track_color",
                "demarc_line_colors",
                "thumb_color",
                "thumb_outline_color",
                "mouse_enabled",
            ]
        }
    }
    
    fixed_attributes = set()
    
    sub_components = {
        "slider": {
            "class": Slider,
            "attribute_correspondence": {
                "shape": "slider_shape",
                "anchor_rel_pos": "slider_bottomleft",
                "val_range": "val_range",
                "increment_start": "increment_start",
                "increment": "increment",
                "anchor_type": ((), lambda: "bottomleft"),
                "screen_topleft_to_parent_topleft_offset": "screen_topleft_to_component_topleft_offset",
                "init_val": "init_val",
                "demarc_numbers_text_group": "demarc_numbers_text_group",
                "demarc_numbers_dp": "demarc_numbers_dp",
                "thumb_radius_rel": "thumb_radius_rel",
                "demarc_line_lens_rel": "demarc_line_lens_rel",
                "demarc_intervals": "demarc_intervals",
                "demarc_start_val": "demarc_start_val",
                "demarc_numbers_max_height_rel": "demarc_numbers_max_height_rel",
                "track_color": "track_color",
                "thumb_color": "thumb_color",
                "demarc_numbers_color": "demarc_numbers_color",
                "demarc_line_colors": "demarc_line_colors",
                "thumb_outline_color": "thumb_outline_color",
                "mouse_enabled": "mouse_enabled",
                "name": "name",
            },
            #"creation_function": Slider,
            "creation_function_args": {
                "shape": None,
                "anchor_rel_pos": None,
                "val_range": None,
                "increment_start": None,
                "increment": None,
                "anchor_type": None,
                "screen_topleft_to_parent_topleft_offset": None,
                "init_val": None,
                "demarc_numbers_text_group": None,
                "demarc_numbers_dp": None,
                "thumb_radius_rel": None,
                "demarc_line_lens_rel": None,
                "demarc_intervals": None,
                "demarc_start_val": None,
                "demarc_numbers_max_height_rel": None,
                "track_color": None,
                "thumb_color": None,
                "demarc_numbers_color": None,
                "demarc_line_colors": None,
                "thumb_outline_color": None,
                "mouse_enabled": None,
                "name": None,
            },
            "container_attr_resets": {
                "changed_since_last_draw": {"display_surf": (lambda container_obj, obj: obj.drawUpdateRequired())},
            },
            #"attr_reset_component_funcs": {},
            "container_attr_derivation": {
                "val": ["val"],
            }
        }
    }
    
    static_bg_components = ["title"]
    displ_component_attrs = ["static_bg", "slider", "val_text"]
    
    def __init__(self,
        title: str,
        shape: Tuple[Real],
        anchor_rel_pos: Tuple[Real],
        val_range: Tuple[Real],
        increment_start: Real,
        increment: Optional[Real]=None,
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        init_val: Optional[Real]=None,
        demarc_numbers_text_group: Optional["TextGroup"]=None,
        demarc_numbers_dp: Optional[int]=None,
        thumb_radius_rel: Optional[Real]=None,
        demarc_line_lens_rel: Optional[Tuple[Real]]=None,
        demarc_intervals: Optional[Tuple[Real]]=None,
        demarc_start_val: Optional[Real]=None,
        demarc_numbers_max_height_rel: Optional[Real]=None,
        track_color: Optional[ColorOpacity]=None,
        thumb_color: Optional[ColorOpacity]=None,
        demarc_numbers_color: Optional[ColorOpacity]=None,
        demarc_line_colors: Optional[ColorOpacity]=None,
        thumb_outline_color: Optional[ColorOpacity]=None,
        mouse_enabled: Optional[bool]=None,
        
        slider_shape_rel: Optional[Tuple[Real]]=None,
        slider_borders_rel: Optional[Tuple[Real]]=None,
        title_text_group: Optional["TextGroup"]=None,
        title_anchor_type: Optional[str]=None,
        title_color: Optional[ColorOpacity]=None,
        val_text_group: Optional["TextGroup"]=None,
        val_text_anchor_type: Optional[str]=None,
        val_text_color: Optional[ColorOpacity]=None,
        val_text_dp: Optional[int]=None,
        
        name: Optional[str]=None,
        **kwargs,
    ) -> None:
        checkHiddenKwargs(type(self), kwargs)
        if name is None:
            SliderPlus.unnamed_count += 1
            name = f"slider plus {self.unnamed_count}"
        #self.name = name
        SliderPlus.sliderplus_names.add(name)
        #print(locals().keys())
        kwargs2 = self.initArgsManagement(locals(), kwargs=kwargs)#, rm_args=["name"])
        #print(kwargs2.keys())
        #print("init_val" in kwargs2)
        super().__init__(**kwargs2)
        #print("\nAfter initialisation")
        #print(self.__dict__.keys())
        #print("_init_val" in self.__dict__.keys())


        #super().__init__(**self.initArgsManagement(locals(), kwargs=kwargs, rm_args=["name", "init_val"]), slider_held=False, val_raw=init_val)

    #def _createSlider(
    #    self,
    #    func: Callable,
    #    attr_arg_dict: Dict[str, str],
    #) -> "Slider":
    #    kwargs = {attr: getattr(self, arg) for arg, attr in attr_arg_dict.items()}
    #    res = func(**kwargs)
    
    #def createSlider(self) -> "Slider":
    #    #print("Creating slider")
    #    return self.createSubComponent("slider")
    """
    def createComponent(self, component: str) -> Optional[Any]:
        #return self._createSlider(Slider, attr_arg_dict)
        cls = type(self)
        comp_dict = cls.__dict__.get("component_dict", cls.createComponentDictionary())
        if component not in comp_dict.keys(): return None
        component_creator_func, component_attr_dict = comp_dict[component]
        component_creator = component_creator_func()
        kwargs = {attr: (getattr(self, arg) if isinstance(arg, str) else arg[0]) for arg, attr in component_attr_dict.items()}
        return component_creator(**kwargs)
        
        return res
            shape=self.slider_shape,
            anchor_rel_pos=self.slider_topleft,
            val_range=self.val_range,
            increment_start=self.increment_start,
            increment=self.increment,
            anchor_type="topleft",
            screen_topleft_to_parent_topleft_offset=self.screen_topleft_to_component_topleft_offset,
            init_val=self.init_val,
            demarc_numbers_text_group=self.demarc_numbers_text_group,
            demarc_numbers_dp=self.demarc_numbers_dp,
            thumb_radius_rel=self.thumb_radius_rel,
            demarc_line_lens_rel=self.demarc_line_lens_rel,
            demarc_intervals: Optional[Tuple[Real]]=None,
            demarc_start_val: Optional[Real]=None,
            demarc_numbers_max_height_rel: Optional[Real]=None,
            track_color: Optional[ColorOpacity]=None,
            thumb_color: Optional[ColorOpacity]=None,
            demarc_numbers_color: Optional[ColorOpacity]=None,
            demarc_line_colors: Optional[ColorOpacity]=None,
            thumb_outline_color: Optional[ColorOpacity]=None,
            mouse_enabled: Optional[bool]=None,
            name: Optional[str]=None,
        )
    """
    def calculateValue(self) -> Real:
        #print("Using calculateValue()")
        #print(f"slider value = {self.slider.val}")
        return self.slider.val

    @staticmethod
    def sliderShapeCalculator(slider_plus_shape: Tuple[int, int], slider_shape_rel: Tuple[float, float]) -> Tuple[int, int]:
        #print("Using SliderPlus method sliderShapeCalculator()")
        return tuple(math.floor(x * y) for x, y in zip(slider_plus_shape, slider_shape_rel)) 

    def calculateSliderShape(self) -> Tuple[int, int]:
        return self.sliderShapeCalculator(self.shape, self.slider_shape_rel)
    
    def calculateSliderBottomLeft(self) -> Tuple[int]:
        #print(f"Using calculateSliderBottomLeft()")
        return (0, self.shape[1])
    
    def calculateSliderBorders(self) -> Tuple[int]:
        #print("Using calculateSliderBorders()")
        #print(f"self.shape = {self.shape}")
        #print(f"self.slider_borders_rel = {self.slider_borders_rel}")
        res = tuple(round(x * y) for x, y in zip(self.shape, self.slider_borders_rel))
        #print(f"calculated slider borders = {res}")
        return res

    def _setTitleTextObjectAttribute(self, attr: str, text_obj_attr: str) -> None:
        #print(f"Using _setTitleTextObjectAttribute() to set title text object attribute {text_obj_attr} from SliderPlus attribute {attr}")
        title_text_obj = self.__dict__.get("_title_text_obj", None)
        if title_text_obj is None:
            #print("title_text_obj is None")
            return
        #print("hi2")
        val = getattr(self, attr)
        #print(f"setting title object attribute {text_obj_attr} to {val}")
        #print(attr, val)
        orig_val = getattr(title_text_obj, text_obj_attr, None)
        setattr(title_text_obj, text_obj_attr, val)
        chng_val = getattr(title_text_obj, text_obj_attr, None)
        #print(orig_val, chng_val)
        if orig_val != chng_val:
            self.title_surf = None
        return
    
    def calculateTitleShape(self) -> Tuple[int]:
        #print("Using calculateTitleShape()")
        shape = self.shape
        slider_shape = self.slider_shape
        slider_borders = self.slider_borders
        #print(f"overall shape = {shape}, slider_shape = {slider_shape}, slider_borders = {slider_borders}")
        res = (slider_shape[0], shape[1] - (slider_shape[1] + slider_borders[1]))
        #print(f"title shape = {res}")
        return res 
    
    def calculateTitleAnchorPosition(self) -> Tuple[int]:
        res = topLeftAnchorOffset(self.title_shape, self.title_anchor_type)
        #print(f"title anchor position = {res}")
        return res
    
    @staticmethod
    def createTitleTextGroup(
        font: Optional["pg.freetype"]=None,
        max_height: Optional[int]=None,
    ) -> "TextGroup":
        #print("Using SliderPlus method createTitleTextGroup()")
        if font is None:
            font = font_def_func()
        return TextGroup(
            text_list=[],
            max_height0=max_height,
            font=None,
            font_size=None,
            min_lowercase=True,
            text_global_asc_desc_chars=None
        )
    
    def createTitleTextObject(self, title_text_group: Optional["TextGroup"]=None)\
            -> Union["Text", tuple]:
        #print("creating title text object")
        txt = self.title
        if not txt: return ()
        if title_text_group is None:
            title_text_group = self.title_text_group
        color = self.title_color
        txt = self.title
        #print(f"self.title_shape = {self.title_shape}")
        #container_attr_resets = {"display_surf": {"display_surf": True}}
        #self.sliders[grid_inds[0]][grid_inds[1]] = self.slider_plus_group.addSliderPlus(
        #    _from_container=True,
        #    _container_obj=self,
        #    _container_attr_reset_dict=container_attr_resets,
        #    **attr_dict,
        #    **kwargs,
        #)
        #container_attr_resets = {"display_surf": {"display_surf": True}}
        #def titleSurfReset(obj, prev_val):
        #    print("resetting title surface")
        #    print(obj)
        #    setattr(obj, "title_surf", None)
        #    return

        add_text_dicts = [
            {
                "text": txt,
                "font_color": color,
                "max_shape": self.title_shape,
                #"_attr_reset_funcs": {"updated": [titleSurfReset]},#[lambda obj, prev_val: setattr(obj, "title_surf", None)]},
                "_from_container": True,
                "_container_obj": self,
                "_container_attr_reset_dict": {"updated": {"title_surf": (lambda container_obj, obj: getattr(obj, "updated", False))}},
            }
        ]
        text_obj = title_text_group.addTextObjects(add_text_dicts)[0]
        #print(f"text_obj.max_shape_actual = {text_obj.max_shape_actual}")
        #text_obj.max_shape = self.title_shape
        return text_obj
    
    def setTitleShape(self, prev_val: Optional[Tuple[int, int]]) -> None:
        #print("setting title shape for text object")
        return self._setTitleTextObjectAttribute("title_shape", "max_shape")
    
    def createTitleSurface(self)\
            -> Union["pg.Surface", tuple]:
        #print(f"using createTitleSurface() for {self}")
        #print("hello1")
        title_text_obj = self.title_text_obj
        #print(f"title font size = {title_text_obj.font_size}")
        #print(title_text_obj)
        if not title_text_obj: return ()
        #print("hello2")
        surf = pg.Surface(self.title_shape, pg.SRCALPHA)
        #surf.set_alpha(255)
        #surf.fill((0, 0, 255))
        #print(self.title_anchor_rel_pos, self.title_anchor_type)
        #print(title_text_obj.font_size)
        title_text_obj.draw(surf, anchor_rel_pos=self.title_anchor_rel_pos, anchor_type=self.title_anchor_type)
        return surf
    
    #def createTitleImageConstructor(self)\
    #        -> Callable[["pg.Surface"], None]:
    #    #return lambda obj, surf: (None if obj.title_surf == () else surf.blit(obj.title_surf, (0, 0)))

    def createTitleImageConstructor(self) -> Callable[["SliderPlus", "pg.Surface"], None]:
        #print("creating text image constructors")
        res = []
        def textImageConstructor(obj: SliderPlus, surf: "pg.Surface") -> None:
            obj.title_text_obj.font_color = obj.title_color
            #obj.title_text_obj.text = obj.val_str
            obj.title_text_obj.max_shape = obj.title_shape
            text_img = obj.title_surf
            if text_img == (): return
            surf.blit(text_img, obj.title_anchor_rel_pos)
            #return lambda obj, surf: (None if obj.static_bg_surf == () else surf.blit(obj.static_bg_surf, (0, 0)))
            #obj.val_text_obj.draw(surf, anchor_rel_pos=obj.val_text_anchor_rel_pos, anchor_type=obj.val_text_anchor_type)
            #print("hello2")
            return
        return textImageConstructor
    
    
    def createStaticBackgroundSurface(self)\
            -> Union["pg.Surface", tuple]:
        #print("creating static background surface")
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        #surf.set_alpha(255)
        #surf.fill((0, 255, 0))
        
        constructor_attrs = [f"{attr}_img_constructor"\
                for attr in self.static_bg_components]
        for constructor_attr in constructor_attrs:
            #print(f"adding {constructor_attr}")
            constructor_func =\
                    getattr(self, constructor_attr, (lambda obj, surf: None))
            constructor_func(self, surf)
        return surf
    
    def createStaticBackgroundImageConstructor(self)\
            -> Callable[["pg.Surface"], None]:
        return lambda obj, surf: (None if obj.static_bg_surf == () else surf.blit(obj.static_bg_surf, (0, 0)))
    
    def createSliderImageConstructor(self) -> Callable[["pg.Surface"], None]:
        #print("creating slider image constructor")
        return lambda obj, surf: obj.slider.draw(surf)


    def _setValueTextObjectAttribute(self, attr: str, text_obj_attr: str) -> None:
        #print("hi1")
        val_text_objs = self.__dict__.get("_val_text_objs", None)
        if val_text_objs is None: return
        #print("hi2")
        val = getattr(self, attr)
        #print(attr, val)
        orig_val = getattr(val_text_objs[0], text_obj_attr, None)
        it = [0] if attr == "text" else range(len(val_text_objs))
        for i in it:
            setattr(val_text_objs[i], text_obj_attr, val)
        chng_val = getattr(val_text_objs[0], text_obj_attr, None)
        #print(orig_val, chng_val)
        if orig_val != chng_val:
            self.val_text_surf = None
        return

    #@property
    #def val_text_group(self):
    #    res = getattr(self, "_val_text_group", None)
    #    if res is None:
    #        res = self.createValueTextGroup()
    #        self._val_text_group = res
    #    return res
    
    @property
    def val_text_objs(self):
        res = getattr(self, "_val_text_objs", None)
        #print(res)
        if res is None:
            res = self.createValueTextObjects()
            self._val_text_objs = res
        #print("hello")
        #print(res)
        return res
    
    def createValueTextGroup(
        font: Optional["pg.freetype"]=None,
        max_height: Optional[int]=None,
    ) -> "TextGroup":
        #print("Using SliderPlus method createValueTextGroup()")
        if font is None:
            font = font_def_func()
        return TextGroup(
            text_list=[],
            max_height0=max_height,
            font=None,
            font_size=None,
            min_lowercase=True,
            text_global_asc_desc_chars=None
        )
        #return TextGroup([], max_height0=None, font=None,\
        #        font_size=None, min_lowercase=True)

    def createValueTextObjects(self) -> List[Text]:
        #print("Using createValueTextObjects()")
        max_val = self.slider.val_range_actual[1]
        max_val_int = math.floor(max_val)
        max_int_n_dig = 0
        while max_val_int:
            max_val_int //= 10
            max_int_n_dig += 1
        max_int_n_dig = max(max_int_n_dig, 1)
        dp = self.val_text_dp
        #print(f"max_val_int = {max_val_int}, max_int_n_dig {max_int_n_dig}")
        def repeatedDigitString(d: int) -> str:
            l = str(d)
            res = l * max_int_n_dig if dp <= 0 else ".".join([l * max_int_n_dig, l * dp])
            #print(res)
            return res
            #return ".".join([l * max_int_n_dig, l * ])

        #nums = [str(d) * max_n_dig for d in range(10)]
        """
        val_max_width = self.arena_shape[0] * 0.1
        val_max_width_pixel = num_max_width * self.head_size
        num_anchor_rel_pos = (self.border[0][0] + self.arena_shape[0] - num_max_width, self.border[1][0] * 0.9)
        num_anchor_rel_pos_pixel = tuple(x * self.head_size for x in num_anchor_rel_pos)
        txt_max_width = self.arena_shape[0] * 0.3
        txt_max_width_pixel = txt_max_width * self.head_size
        txt_anchor_rel_pos = num_anchor_rel_pos
        txt_anchor_rel_pos_pixel = tuple(x * self.head_size for x in txt_anchor_rel_pos)

        
        
        max_h = self.border[1][0] * 0.25
        max_h_pixel = max_h * self.head_size
        """
        #txt_shape = (10, 10)
        #add_text_dicts = [{"text": txt, "font_color": color, "max_shape": self.title_shape, "_attr_reset_funcs": {"updated": [lambda obj, prev_val: setattr(obj, "title_surf", None)]}}]
        text_dict = {
            "text": self.val_str,
            "anchor_rel_pos0": self.val_text_anchor_rel_pos,
            "anchor_type0": self.val_text_anchor_type,
            "max_shape": self.val_text_shape,
            "font_color": self.val_text_color,
            #"_attr_reset_funcs": {"updated": [lambda obj, prev_val: setattr(obj, "val_text_surf", None)]},
            "_from_container": True,
            "_container_obj": self,
            "_container_attr_reset_dict": {"updated": {"val_text_surf": (lambda container_obj, obj: getattr(obj, "updated", False))}},
        }
        text_list = []
        
        text_list.append(dict(text_dict))
        #text_dict.pop("_attr_reset_funcs")
        for attr in ["_from_container", "_container_obj", "_container_attr_reset_dict"]:
            text_dict.pop(attr)
        for d in range(10):
            text_dict["text"] = repeatedDigitString(d)
            #print(text_dict["text"])
            text_list.append(dict(text_dict))
        grp = self.val_text_group
        text_objs = grp.addTextObjects(text_list)
        #print(text_objs)
        return text_objs

    def calculateValueString(self) -> str:
        #print("Using calculateValueString()")
        dp = self.val_text_dp
        #print(f"val_text_dp = {dp}")
        s = f"{self.val:.{dp}f}"
        #print(f"value string = {s}")
        return f"{s}"

    @property
    def val_text_obj(self):
        return self.val_text_objs[0]

    def calculateValueTextShape(self) -> Tuple[int]:
        #print("Using calculateValueTextShape()")
        shape = self.shape
        #print(f"object shape = {shape}")
        slider_shape = self.slider_shape
        slider_borders = self.slider_borders
        #print(f"slider shape = {slider_shape}")
        #print(f"slider borders = {slider_borders}")
        res = (shape[0] - (slider_shape[0] + slider_borders[0]), shape[1])
        #print(f"value shape = {res}")
        return res 
    
    def calculateValueTextAnchorPosition(self) -> Tuple[int]:
        slider_shape = self.slider_shape
        slider_borders = self.slider_borders
        res = tuple([slider_shape[0] + slider_borders[0], 0])
        #print(f"value text anchor position = {res}")
        return res
    
    #def setValueTextShape(self, prev_val: Optional[Tuple[int, int]]) -> None:
    #    #print("setting title shape for text object")
    #    return self._setValueTextObjectAttribute("val_text_shape", "max_shape")
    
    def createValueTextImageConstructor(self) -> Callable[["SliderPlus", "pg.Surface"], None]:
        #print("creating text image constructors")
        res = []
        def textImageConstructor(obj: SliderPlus, surf: "pg.Surface") -> None:
            obj.val_text_obj.font_color = obj.val_text_color
            obj.val_text_obj.text = obj.val_str
            obj.val_text_obj.max_shape = obj.val_text_shape
            #print(f"value text shape = {obj.val_text_shape}, text object max text shape = {obj.val_text_obj.max_shape}")
            #print(f"number of val_text_objs = {len(obj.val_text_objs)}")
            for i in range(1, len(obj.val_text_objs)):
                #print(f"i = {i}, text = {obj.val_text_objs[i].text}")
                obj.val_text_objs[i].max_shape = obj.val_text_shape
            text_img = obj.val_text_surf
            if text_img == (): return
            surf.blit(text_img, obj.val_text_anchor_rel_pos)
            #return lambda obj, surf: (None if obj.static_bg_surf == () else surf.blit(obj.static_bg_surf, (0, 0)))
            #obj.val_text_obj.draw(surf, anchor_rel_pos=obj.val_text_anchor_rel_pos, anchor_type=obj.val_text_anchor_type)
            #print("hello2")
            return
        return textImageConstructor

    #def createValueTextImageConstructor(self)\
    #        -> Callable[["pg.Surface"], None]:
    #    print("calling createValueTextImageConstructor()")
    #    return lambda obj, surf: (None if obj.val_text_surf == () else surf.blit(obj.val_text_surf, (0, 0)))

    def createValueTextSurface(self)\
            -> Union["pg.Surface", tuple]:
        #print("Using createValueTextSurface()")
        #print("hello1")
        #print("about to get val_text_obj")
        val_text_obj = self.val_text_obj
        #print(val_text_obj)
        #print(title_text_obj)
        if not val_text_obj: return ()
        #print("hello2")
        surf = pg.Surface(self.val_text_shape, pg.SRCALPHA)
        #surf.set_alpha(100)
        #surf.fill((0, 255, 255))
        #print(self.title_anchor_rel_pos, self.title_anchor_type)
        anchor_offset = topLeftAnchorOffset(self.val_text_shape, self.val_text_anchor_type)
        #print(f"anchor offset = {anchor_offset}")
        val_text_obj.draw(surf, anchor_rel_pos=anchor_offset, anchor_type=self.val_text_anchor_type)
        return surf
    
    """
    def createStaticBackgroundSurface(self)\
            -> Union["pg.Surface", tuple]:
        #print("creating static background surface")
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        surf.set_alpha(255)
        surf.fill((0, 255, 0))
        
        constructor_attrs = [f"{attr}_img_constructor"\
                for attr in self.static_bg_components]
        for constructor_attr in constructor_attrs:
            #print(f"adding {constructor_attr}")
            constructor_func =\
                    getattr(self, constructor_attr, (lambda obj, surf: None))
            constructor_func(self, surf)
        return surf
    """
    def createDisplaySurface(self) -> Optional["pg.Surface"]:
        #print("creating display surface for SliderPlus object")
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
    
    #def draw(self, surf: "pg.Surface") -> None:
    #    print("Using SliderPlus method draw()")
    #    #print(f"self._display_surf = {getattr(self, '_display_surf', None)}")
    #    #print(f"self.display_surf = {self.display_surf}")
    #    surf.blit(self.display_surf, self.topleft_rel_pos)
    #    return

    def eventLoop(self, events: Optional[List[int]]=None,\
            keys_down: Optional[List[int]]=None,\
            mouse_status: Optional[Tuple[int]]=None,\
            check_axes: Tuple[int]=(0, 1))\
            -> Tuple[bool, bool, bool, Any]:
        #print("calling SliderPlus method eventLoop()")
        #print(self.mouse_enabled)
        #print(events)
        ((quit, esc_pressed), (events, keys_down, mouse_status, check_axes)) = self.getEventLoopArguments(events=events, keys_down=keys_down, mouse_status=mouse_status, check_axes=check_axes)
        #print(events, mouse_status)
        running = not quit and not esc_pressed
        screen_changed = False
        
        (quit2, running2, screen_changed2, val_dict) = self.eventLoopComponents(
            events=events,
            keys_down=keys_down,
            mouse_status=mouse_status,
            check_axes=check_axes,
        )
        quit = quit or quit2
        running = running and running2
        #screen_changed = screen_changed or screen_changed2
        screen_changed = self.drawUpdateRequired()
        #if screen_changed:
        #    print(f"slider {self} has attribute display_surf of {self.__dict__.get('_display_surf', None)}")
        #print(screen_changed, self.val)
        #print()
        #print("end of SliderPlus eventLoop()")
        #print(quit, running, screen_changed, self.slider.val)
        #print(getattr(self, "_display_surf", None))
        return quit, running, screen_changed, self.val

class SliderPlusGroupElement(ComponentGroupElementBaseClass, SliderPlus):
    
    group_cls_func = lambda: SliderPlusGroup
    group_obj_attr = "slider_plus_group"
    #fixed_attributes = {group_obj_attr}

    #sub_components = dict(SliderPlus.sub_components)
    #sub_components["slider"]["class"] = SliderGroupElement

    sub_components = {
        "slider": {
            "class": SliderGroupElement,
            "attribute_correspondence": {
                "anchor_rel_pos": "slider_bottomleft",
                "val_range": "val_range",
                "increment_start": "increment_start",
                "increment": "increment",
                "screen_topleft_to_parent_topleft_offset": "screen_topleft_to_component_topleft_offset",
                "init_val": "init_val",
                "demarc_numbers_dp": "demarc_numbers_dp",
                "demarc_intervals": "demarc_intervals",
                "demarc_start_val": "demarc_start_val",
                "mouse_enabled": "mouse_enabled",
                "name": "name",
            },
            "creation_function": (lambda slider_plus_group, **kwargs: slider_plus_group.slider_group.addSlider(**kwargs)),
            "creation_function_args": {
                "slider_plus_group": "slider_plus_group",
                #"shape": (("shape", "slider_shape_rel"), SliderPlus.sliderShapeCalculator),
                "anchor_rel_pos": None,
                "val_range": None,
                "increment_start": None,
                "increment": None,
                "anchor_type": ((), (lambda: "bottomleft")),
                "screen_topleft_to_parent_topleft_offset": None,
                "init_val": None,
                "demarc_numbers_dp": None,
                "demarc_intervals": None,
                "demarc_start_val": None,
                "mouse_enabled": None,
                "name": None,
            },
            "container_attr_resets": {
                "changed_since_last_draw": {"display_surf": (lambda container_obj, obj: obj.drawUpdateRequired())},
            },
            #"attr_reset_component_funcs": {},
            "container_attr_derivation": {
                "val": ["val"],
            }
        }
    }

    def __init__(
        self,
        slider_plus_group: "SliderPlusGroup",
        title: str,
        anchor_rel_pos: Tuple[Real],
        val_range: Tuple[Real],
        increment_start: Real,
        increment: Optional[Real]=None,
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        init_val: Optional[Real]=None,
        demarc_numbers_dp: Optional[int]=None,
        demarc_intervals: Optional[Tuple[Real]]=None,
        demarc_start_val: Optional[Real]=None,
        
        val_text_dp: Optional[int]=None,

        mouse_enabled: Optional[bool]=None,
        
        name: Optional[str]=None,
        **kwargs,
    ) -> None:
        
        checkHiddenKwargs(type(self), kwargs)
        
        #self.__dict__[f"_{self.group_obj_attr}"] = slider_group
        super().__init__(
            shape=slider_plus_group.shape,
            title=title,
            anchor_rel_pos=anchor_rel_pos,
            val_range=val_range,
            increment_start=increment_start,
            increment=increment,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=screen_topleft_to_parent_topleft_offset,
            init_val=init_val,
            demarc_numbers_text_group=slider_plus_group.demarc_numbers_text_group,
            demarc_numbers_dp=demarc_numbers_dp,
            thumb_radius_rel=slider_plus_group.thumb_radius_rel,
            demarc_line_lens_rel=slider_plus_group.demarc_line_lens_rel,
            demarc_intervals=demarc_intervals,
            demarc_start_val=demarc_start_val,
            demarc_numbers_max_height_rel=slider_plus_group.demarc_numbers_max_height_rel,
            track_color=slider_plus_group.track_color,
            thumb_color=slider_plus_group.thumb_color,
            demarc_numbers_color=slider_plus_group.demarc_numbers_color,
            demarc_line_colors=slider_plus_group.demarc_line_colors,
            thumb_outline_color=slider_plus_group.thumb_outline_color,
            slider_shape_rel=slider_plus_group.slider_shape_rel,
            slider_borders_rel=slider_plus_group.slider_borders_rel,
            title_text_group=slider_plus_group.title_text_group,
            title_anchor_type=slider_plus_group.title_anchor_type,
            title_color=slider_plus_group.title_color,
            val_text_group=slider_plus_group.val_text_group,
            val_text_anchor_type=slider_plus_group.val_text_anchor_type,
            val_text_color=slider_plus_group.val_text_color,
            val_text_dp=val_text_dp,

            mouse_enabled=mouse_enabled,
            name=name,
            _group=slider_plus_group,
            **kwargs,
        )
        #print(f"slider plus group title text group = {slider_plus_group.title_text_group}")
        #print(f"new slider plus group element title text group = {getattr(self, '_title_text_group', None)}")
        return

    def calculateSliderShape(self) -> Tuple[int, int]:
        return self.slider.shape

class SliderPlusGroup(ComponentGroupBaseClass):
    group_element_cls_func = lambda: SliderPlusGroupElement
    
    reset_graph_edges = {}
    
    """
    custom_attribute_change_propogation_methods = {
        "slider_shape": "setSliderShape",
        "demarc_numbers_text_group": "setDemarcationNumbersTextGroup",
        "thumb_radius_rel": "setThumbRadiusRelative",
        "demarc_line_lens_rel": "setDemarcationLineLengthsRelative",
        "demarc_numbers_max_height_rel": "setDemarcationNumbersMaxHeightRelative",
        "track_color": "setTrackColor",
        "thumb_color": "setThumbColor",
        "demarc_numbers_color": "setDemarcationNumbersColor",
        "demarc_line_colors": "setDemarcationLineColors",
        "thumb_outline_color": "setThumbOutlineColor",
        "mouse_enabled": "setMouseEnabled",
    }
    """
    attribute_calculation_methods = {}
    
    # Review- account for using element_inherited_attributes in ComponentGroupBaseClass
    attribute_default_functions = {
        attr: SliderPlus.attribute_default_functions.get(attr) for attr in
        [
            "slider_shape_rel",
            "slider_borders_rel",
            "title_text_group",
            "title_anchor_type",
            "title_color",
            "val_text_group",
            "val_text_anchor_type",
            "val_text_color",
        ]
    }
    
    #fixed_attributes = {"sliders"}

    """
    slider_shape: Tuple[Real],
        demarc_numbers_text_group: Optional["TextGroup"]=None,
        thumb_radius_rel: Optional[Real]=None,
        demarc_line_lens_rel: Optional[Tuple[Real]]=None,
        demarc_numbers_max_height_rel: Optional[Real]=None,
        track_color: Optional[ColorOpacity]=None,
        thumb_color: Optional[ColorOpacity]=None,
        demarc_numbers_color: Optional[ColorOpacity]=None,
        demarc_line_colors: Optional[ColorOpacity]=None,
        thumb_outline_color: Optional[ColorOpacity]=None,
        mouse_enabled
    """

    sub_components = {
        "slider_group": {
            "class": SliderGroup,
            "attribute_correspondence": {
                "slider_shape": (("shape", "slider_shape_rel"), SliderPlus.sliderShapeCalculator),
                "demarc_numbers_text_group": "demarc_numbers_text_group",
                "thumb_radius_rel": "thumb_radius_rel",
                "demarc_line_lens_rel": "demarc_line_lens_rel",
                "demarc_numbers_max_height_rel": "demarc_numbers_max_height_rel",
                "track_color": "track_color",
                "thumb_color": "thumb_color",
                "demarc_numbers_color": "demarc_numbers_color",
                "demarc_line_colors": "demarc_line_colors",
                "thumb_outline_color": "thumb_outline_color",
                #"mouse_enabled": "mouse_enabled",
            },
            #"creation_function": SliderGroup,
            "creation_function_args": {
                "slider_shape": None,#(("shape", "slider_shape_rel"), SliderPlus.sliderShapeCalculator),
                "demarc_numbers_text_group": None,
                "thumb_radius_rel": None,
                "demarc_line_lens_rel": None,
                "demarc_numbers_max_height_rel": None,
                "track_color": None,
                "thumb_color": None,
                "demarc_numbers_color": None,
                "demarc_line_colors": None,
                "thumb_outline_color": None,
                #"mouse_enabled": None,
            },
        }
    }
    
    element_inherited_attributes = {
        "shape": "shape",
        "demarc_numbers_text_group": "demarc_numbers_text_group",
        "thumb_radius_rel": "thumb_radius_rel",
        "demarc_line_lens_rel": "demarc_line_lens_rel",
        "demarc_numbers_max_height_rel": "demarc_numbers_max_height_rel",
        "track_color": "track_color",
        "demarc_numbers_color": "demarc_numbers_color",
        "demarc_line_colors": "demarc_line_colors",
        "thumb_outline_color": "thumb_outline_color",
        #"mouse_enabled": "mouse_enabled",
        "slider_shape_rel": "slider_shape_rel",
        "slider_borders_rel": "slider_borders_rel",
        "title_text_group": "title_text_group",
        "title_anchor_type": "title_anchor_type",
        "title_color": "title_color",
        "val_text_group": "val_text_group",
        "val_text_anchor_type": "val_text_anchor_type",
        "val_text_color": "val_text_color",
    }

    def __init__(self, 
        shape: Tuple[Real],
        demarc_numbers_text_group: Optional["TextGroup"]=None,
        thumb_radius_rel: Optional[Real]=None,
        demarc_line_lens_rel: Optional[Tuple[Real]]=None,
        demarc_numbers_max_height_rel: Optional[Real]=None,
        track_color: Optional[ColorOpacity]=None,
        thumb_color: Optional[ColorOpacity]=None,
        demarc_numbers_color: Optional[ColorOpacity]=None,
        demarc_line_colors: Optional[ColorOpacity]=None,
        thumb_outline_color: Optional[ColorOpacity]=None,
        #mouse_enabled: Optional[bool]=None,
        slider_shape_rel: Optional[Tuple[Real]]=None,
        slider_borders_rel: Optional[Tuple[Real]]=None,
        title_text_group: Optional["TextGroup"]=None,
        title_anchor_type: Optional[str]=None,
        title_color: Optional[ColorOpacity]=None,
        val_text_group: Optional["TextGroup"]=None,
        val_text_anchor_type: Optional[str]=None,
        val_text_color: Optional[ColorOpacity]=None,
        **kwargs,
    ) -> None:

        checkHiddenKwargs(type(self), kwargs)
        
        kwargs2 = self.initArgsManagement(locals(), kwargs=kwargs)
        super().__init__(**kwargs2)

    def addSliderPlus(
        self,
        title: str,
        anchor_rel_pos: Tuple[Real],
        val_range: Tuple[Real],
        increment_start: Real,
        increment: Optional[Real]=None,
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real]]=None,
        init_val: Optional[Real]=None,
        demarc_numbers_dp: Optional[int]=None,
        demarc_intervals: Optional[Tuple[Real]]=None,
        demarc_start_val: Optional[Real]=None,
        val_text_dp: Optional[int]=None,
        mouse_enabled: Optional[bool]=None,
        name: Optional[str]=None,
        **kwargs,
    ) -> "SliderGroupElement":
        #print("using addSliderPlus()")
        #print(kwargs)
        res = self._addElement(
            title=title,
            anchor_rel_pos=anchor_rel_pos,
            val_range=val_range,
            increment_start=increment_start,
            increment=increment,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=screen_topleft_to_parent_topleft_offset,
            init_val=init_val,
            demarc_numbers_dp=demarc_numbers_dp,
            demarc_intervals=demarc_intervals,
            demarc_start_val=demarc_start_val,
            val_text_dp=val_text_dp,
            mouse_enabled=mouse_enabled,
            name=name,
            **kwargs,
        )
        return res


class SliderPlusGrid(InteractiveDisplayComponentBase):
    #sliderplus_names = set()
    #unnamed_count = 0
    
    reset_graph_edges = {
        "grid_dims": {"grid_layout": True},
        "shape": {"grid_layout": True},
        "slider_plus_gaps_rel_shape": {"grid_layout": True},
        "grid_layout": {"slider_plus_shape": True, "slider_gaps": True, "slider_topleft_locations": True, "display_surf": True},
        "slider_plus_shape": {"display_surf": True},
        "slider_gaps": {"display_surf": True},
        "slider_topleft_locations": {"display_surf": True},
    }
    
    custom_attribute_change_propogation_methods = {
        "screen_topleft_to_component_topleft_offset": "setTitleShape",
    }
    
    attribute_calculation_methods = {
        "mouse_enablement": "calculateMouseEnablement",

        #"slider": "createSlider",
        "grid_layout": "calculateGridLayout",
        "slider_plus_shape": "calculateSliderShape",
        "slider_gaps": "calculateSliderGaps",
        "slider_topleft_locations": "calculateSliderTopleftLocations",

        #"display_surf": "createDisplaySurface",

        "slider_grid_img_constructor": "createSliderGridImageConstructor",
    }
    
    attribute_default_functions = {
        **{
            attr: SliderPlus.attribute_default_functions.get(attr) for attr in
            [
                "thumb_radius_rel",
                "demarc_line_lens_rel",
                "demarc_numbers_max_height_rel",
                "track_color",
                "thumb_color",
                "demarc_numbers_color",
                "demarc_line_colors",
                "thumb_outline_color",
                "mouse_enabled",
                "slider_shape_rel",
                "slider_borders_rel",
                "title_text_group",
                "title_anchor_type",
                "title_color",
                "val_text_group",
                "val_text_anchor_type",
                "val_text_color",
            ]
        },
        **{
            "slider_plus_gaps_rel_shape": ((lambda obj: (0., 0.)),),
            "sliders": ((lambda obj: [[None] * obj.grid_dims[1] for _ in range(obj.grid_dims[0])])),
        }
    }
    
    fixed_attributes = set()
    
    sub_components = {
        "slider_plus_group": {
            "class": SliderPlusGroup,
            "attribute_correspondence": {
                "shape": "slider_plus_shape",
                "demarc_numbers_text_group": "demarc_numbers_text_group",
                "thumb_radius_rel": "thumb_radius_rel",
                "demarc_line_lens_rel": "demarc_line_lens_rel",
                "demarc_numbers_max_height_rel": "demarc_numbers_max_height_rel",
                "track_color": "track_color",
                "thumb_color": "thumb_color",
                "demarc_numbers_color": "demarc_numbers_color",
                "demarc_line_colors": "demarc_line_colors",
                "thumb_outline_color": "thumb_outline_color",
                #"mouse_enabled": "mouse_enabled",
                "slider_shape_rel": "slider_shape_rel",
                "slider_borders_rel": "slider_borders_rel",
                "title_text_group": "title_text_group",
                "title_anchor_type": "title_anchor_type",
                "title_color": "title_color",
                "val_text_group": "val_text_group",
                "val_text_anchor_type": "val_text_anchor_type",
                "val_text_color": "val_text_color",
            },
            "creation_function_args": {
                "shape": None,
                "demarc_numbers_text_group": None,
                "thumb_radius_rel": None,
                "demarc_line_lens_rel": None,
                "demarc_numbers_max_height_rel": None,
                "track_color": None,
                "thumb_color": None,
                "demarc_numbers_color": None,
                "demarc_line_colors": None,
                "thumb_outline_color": None,
                #"mouse_enabled": None,
                "slider_shape_rel": None,
                "slider_borders_rel": None,
                "title_text_group": None,
                "title_anchor_type": None,
                "title_color": None,
                "val_text_group": None,
                "val_text_anchor_type": None,
                "val_text_color": None,
            },
            #"container_attr_resets": {
            #    "display_surf": {"display_surf": True},
            #},
            #"attr_reset_component_funcs": {},
            #"container_attr_derivation": {
            #    "val": ["val"],
            #},
        }
    }
    
    #static_bg_components = []#["title"]
    displ_component_attrs = ["slider_grid"]

    def __init__(
        self,
        grid_dims: Tuple[int, int],
        shape: Tuple[Real, Real],
        slider_plus_gaps_rel_shape: Optional[Tuple[Real, Real]]=None,
        anchor_rel_pos: Tuple[Real, Real]=None,
        anchor_type: Optional[str]=None,
        screen_topleft_to_parent_topleft_offset: Optional[Tuple[Real, Real]]=None,
        demarc_numbers_text_group: Optional["TextGroup"]=None,
        thumb_radius_rel: Optional[Real]=None,
        demarc_line_lens_rel: Optional[Tuple[Real]]=None,
        demarc_numbers_max_height_rel: Optional[Real]=None,
        track_color: Optional[ColorOpacity]=None,
        thumb_color: Optional[ColorOpacity]=None,
        demarc_numbers_color: Optional[ColorOpacity]=None,
        demarc_line_colors: Optional[ColorOpacity]=None,
        thumb_outline_color: Optional[ColorOpacity]=None,
        slider_shape_rel: Optional[Tuple[Real]]=None,
        slider_borders_rel: Optional[Tuple[Real]]=None,
        title_text_group: Optional["TextGroup"]=None,
        title_anchor_type: Optional[str]=None,
        title_color: Optional[ColorOpacity]=None,
        val_text_group: Optional["TextGroup"]=None,
        val_text_anchor_type: Optional[str]=None,
        val_text_color: Optional[ColorOpacity]=None,
        mouse_enabled: Optional[bool]=None,
        **kwargs,
    ):
        
        #self.slider_shape_fixed = False

        checkHiddenKwargs(type(self), kwargs)
        
        kwargs2 = self.initArgsManagement(locals(), kwargs=kwargs)
        super().__init__(**kwargs2)
        #self.sliders = [[None] * self.grid_dims[1] for _ in range(self.grid_dims[0])]
        """
        super().__init__(
            shape,
            anchor_rel_pos,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=screen_topleft_to_parent_topleft_offset,
            mouse_enablement=(mouse_enabled, False, mouse_enabled),
        )
        
        #print(button_text)
        self._grid_dims = grid_dims

        shape = (100, 100) # Placeholder

        self._slider_group = SliderPlusGroup(
            shape=self.slider_plus_shape,
            demarc_numbers_text_group: Optional["TextGroup"]=None,
            thumb_radius_rel: Optional[Real]=None,
            demarc_line_lens_rel: Optional[Tuple[Real]]=None,
            demarc_intervals: Optional[Tuple[Real]]=None,
            demarc_start_val: Optional[Real]=None,
            demarc_numbers_max_height_rel: Optional[Real]=None,
            track_color: Optional[ColorOpacity]=None,
            thumb_color: Optional[ColorOpacity]=None,
            demarc_numbers_color: Optional[ColorOpacity]=None,
            demarc_line_colors: Optional[ColorOpacity]=None,
            thumb_outline_color: Optional[ColorOpacity]=None,
            mouse_enabled: Optional[bool]=None,
            slider_shape_rel: Optional[Tuple[Real]]=None,
            slider_borders_rel: Optional[Tuple[Real]]=None,
            title_text_group: Optional["TextGroup"]=None,
            title_anchor_type: Optional[str]=None,
            title_color: Optional[ColorOpacity]=None,
            val_text_group: Optional["TextGroup"]=None,
            val_text_anchor_type: Optional[str]=None,
            val_text_color: Optional[ColorOpacity]=None,
        )

        self._text_groups = text_groups
        
        self._button_gap_rel_shape = tuple(button_gap_rel_shape)
        
        """
    
    def setupSliderPlusGridElement(
        self,
        grid_inds: Tuple[int],
        title: str,
        val_range: Tuple[Real],
        increment_start: Real,
        increment: Optional[Real]=None,
        init_val: Optional[Real]=None,
        demarc_numbers_dp: Optional[int]=None,
        demarc_intervals: Optional[Tuple[Real]]=None,
        demarc_start_val: Optional[Real]=None,
        val_text_dp: Optional[int]=None,
        name: Optional[str]=None,
        **kwargs,
    ) -> SliderPlus:
        # Review- add mechanism for communicating from a constituent slider
        # that its value has changed.
        if any(idx < 0 or idx >= m for idx, m in zip(grid_inds, self.grid_dims)):
            raise IndexError("The grid indices given are not in the allowed range")
        attr_dict = {
            "title": title,
            "anchor_rel_pos": (0, 0),
            "val_range": val_range,
            "increment_start": increment_start,
            "increment": increment,
            "anchor_type": "topleft",
            #"screen_topleft_to_parent_topleft_offset": self.screen_topleft_to_component_topleft_offset,
            "init_val": init_val,
            "demarc_numbers_dp": demarc_numbers_dp,
            "demarc_intervals": demarc_intervals,
            "demarc_start_val": demarc_start_val,
            "val_text_dp": val_text_dp,
            "mouse_enabled": self.mouse_enabled,
            "name": name,
        }
        
        if self.sliders[grid_inds[0]][grid_inds[1]] is None:
            attr_corresp_dict = {
                "mouse_enabled": "mouse_enabled",
            }
            container_attr_resets = {"changed_since_last_draw": {"display_surf": (lambda container_obj, obj: obj.drawUpdateRequired())}}
            self.sliders[grid_inds[0]][grid_inds[1]] = self.createSubComponent(
                component_class=SliderPlusGroupElement,
                attr_correspondence_dict=attr_corresp_dict,
                creation_kwargs=attr_dict,
                container_attribute_resets=container_attr_resets,
                custom_creation_function=self.slider_plus_group.addSliderPlus
            )
            """
            #print(f"creating slider plus at grid indices {grid_inds}")
            container_attr_resets = {"changed_since_last_draw": {"display_surf": (lambda container_obj, obj: obj.drawUpdateRequired())}}
            self.sliders[grid_inds[0]][grid_inds[1]] = self.slider_plus_group.addSliderPlus(
                _from_container=True,
                _container_obj=self,
                _container_attr_reset_dict=container_attr_resets,
                **attr_dict,
                **kwargs,
            )
            #print(self.sliders[grid_inds[0]][grid_inds[1]].__dict__.get("_display_surf", None))
            """
        else:
            self.sliders[grid_inds[0]][grid_inds[1]].setAttributes(
                attr_dict,
                _from_container=True,
                **kwargs,
            )
        #self.setAttributes({"display_surf": None}, _from_container=True)
        # Workaround to ensure that the slider plus element is sufficiently
        # set up (in particular the slider component has been initialized)
        self.sliders[grid_inds[0]][grid_inds[1]].display_surf
        return self.sliders[grid_inds[0]][grid_inds[1]]

    def getSliderPlus(self, grid_inds: Tuple[int, int]) -> Optional[SliderPlus]:
        if any(idx < 0 or idx >= m for idx, m in zip(grid_inds, self.grid_dims)):
            raise IndexError("The grid indices given are not in the allowed range")
        return self.sliders[grid_inds[0]][grid_inds[1]]

    def __getitem__(self, grid_inds: Tuple[int]) -> Optional[SliderPlus]:
        return self.getSliderPlus(grid_inds)

    def getSliderPlusValue(self, grid_inds: Tuple[int, int]) -> Optional[Real]:
        slider = self.getSliderPlus(grid_inds)
        if slider is None: return None
        return slider.val

    def sliderPlusIterator(self) -> Generator[Tuple[SliderPlus, Tuple[int, int]], None, None]:
        for i1, slider_row in enumerate(self.sliders):
            for i2, slider in enumerate(slider_row):
                if slider is None: continue
                yield (slider, (i1, i2))
        return
    
    def sliderPlusValuesIterator(self) -> Generator[Tuple[Real, Tuple[int, int]], None, None]:
        for slider, grid_inds in self.sliderPlusIterator():
            yield (slider.val, grid_inds)
        return

    def calculateGridLayout(self) -> Tuple[Tuple[int, int], Tuple[float, float]]:
        shape = []
        gaps = []
        for tot_len, n_sliders, rel_gap_size in zip(self.shape, self.grid_dims, self.slider_plus_gaps_rel_shape):
            shape.append(round(tot_len / (rel_gap_size * (n_sliders - 1) + n_sliders)))
            gaps.append((tot_len - n_sliders * shape[-1]) / (n_sliders - 1) if n_sliders > 1 else 0.)
        return tuple(shape), tuple(gaps)
    
    def calculateSliderShape(self) -> Tuple[int, int]:
        return self.grid_layout[0]

    def calculateSliderGaps(self) -> Tuple[int, int]:
        return self.grid_layout[1]
    
    def calculateSliderTopleftLocations(self) -> Tuple[List[int], List[int]]:
        dims = self.grid_dims
        slider_plus_shape, gap_size = self.grid_layout
        x_lst = []
        y_lst = []
        for i1 in range(dims[0]):
            x_lst.append(round((slider_plus_shape[0] + gap_size[0]) * i1))
        for i2 in range(dims[1]):
            y_lst.append(round((slider_plus_shape[1] + gap_size[1]) * i2))

        return (x_lst, y_lst)

    def createDisplaySurface(self) -> "pg.Surface":
        #print("Using SliderPlusGrid method createDisplaySurface()")
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

    def createSliderGridImageConstructor(self) -> Callable:
        def constructor(obj: SliderPlusGrid, surf: "pg.Surface") -> None:
            #print("using slider grid constructor")
            n_slider = 0
            # Workaround to prevent the possibility that changes to one
            # of the later sliders causes the display surface of an earlier
            # one to be reset- moved to the addSliderPlus() method
            #for slider, _ in obj.sliderPlusIterator():
            #    slider.display_surf
            for slider, grid_inds in obj.sliderPlusIterator():
                i1, i2 = grid_inds
                #if i2 == 0: continue
                #print(f"grid inds {(i1, i2)}")
                slider.anchor_type = "topleft"
                slider.anchor_rel_pos = (self.slider_topleft_locations[0][i1], self.slider_topleft_locations[1][i2])
                slider.draw(surf)
                n_slider += 1
            #print(f"n_slider = {n_slider}")
            """
            for i1, slider_row in enumerate(self.sliders):
                x = self.slider_topleft_locations[0][i1]
                for i2, slider in enumerate(slider_row):
                    if slider is None: continue
                    slider.anchor_type = "topleft"
                    y = self.slider_topleft_locations[1][i2]
                    slider.anchor_rel_pos = (x, y)
                    slider.draw(surf)
            """
            return

        return constructor
        #return lambda obj, surf: obj.slider.draw(surf)
    
    def calculateMouseEnablement(self) -> None:
        #print("calculating mouse enablement")
        mouse_enabled = self.mouse_enabled
        return (mouse_enabled, mouse_enabled, mouse_enabled)

    
    #def draw(self, surf: "pg.Surface") -> None:
    #    print("Using SliderPlusGrid method draw()")
    #    print(f"self._display_surf = {self.__dict__.get('_display_surf', None)}")
    #    surf.blit(self.display_surf, self.topleft_rel_pos)
    #    print("finished using SliderPlusGrid method draw()")
    #    return
    
    """
    def processEvents(self, events: List[Tuple[int]]) -> List[Tuple[int]]:
        res = []
        for slider_row in self.sliders:
            for slider in slider_row:
                if slider is None: continue
                res.extend(slider.processEvents(events))
        return res
    """
    
    def eventLoop(self, events: Optional[List[int]]=None,\
            keys_down: Optional[List[int]]=None,\
            mouse_status: Optional[Tuple[int]]=None,\
            check_axes: Tuple[int]=(0, 1))\
            -> Tuple[bool, bool, bool, Any]:
        #print("Using SliderPlusGrid method eventLoop()")
        ((quit, esc_pressed), (events, keys_down, mouse_status, check_axes)) = self.getEventLoopArguments(events=events, keys_down=keys_down, mouse_status=mouse_status, check_axes=check_axes)
        #print(events)
        running = not quit and not esc_pressed
        screen_changed = False
        n_slider = 0
        for slider, inds in self.sliderPlusIterator():
            (quit2, running2, screen_changed2, val_dict) = slider.eventLoop(
                events=events,
                keys_down=keys_down,
                mouse_status=mouse_status,
                check_axes=check_axes,
            )
            #if screen_changed2:
            #    print(f"slider at {inds} changed")
            quit = quit or quit2
            running = running and running2
            #screen_changed = screen_changed or screen_changed2
            n_slider += 1
        screen_changed = self.drawUpdateRequired()
        #print(f"the number of sliders in grid is {n_slider}")
        #print("end of SliderPlusGrid eventLoop()")
        #print(quit, running, screen_changed, None)
        #print(getattr(self, "_display_surf", None))
        return quit, running, screen_changed, None
        """
        quit = False
        running = True
        screen_changed = False
        
        mouse_enabled = self.mouse_enabled and pg.mouse.get_focused()
        
        if mouse_enabled:
            if mouse_status is None:
                mouse_status = self.user_input_processor.getMouseStatus()
            b_inds0_mouse = self.mouse_over
            b_inds1_mouse = self.mouseOverButton(mouse_status[0])
            lmouse_down = mouse_status[1][0]
        else:
            b_inds0_mouse = None
            b_inds1_mouse = None
        
        if events is None:
            quit, esc_pressed, events = user_input_processor.getEvents()
            if quit or esc_pressed:
                running = False
        
        b_inds0 = b_inds0_mouse
        if b_inds0 is None and self.navkeys_enabled:
            b_inds0 = self.navkey_button
        b_inds1, selected_b_inds, b_reset, last_navkey = self.processEvents(b_inds0, b_inds0_mouse, b_inds1_mouse, events)
        
        # Checking for navkeys that are held down and have not yet
        # been overridden by new inputs
        #print(self._navkey_status)
        #print(keys_down)
        if b_reset:
            self._navkey_status = [last_navkey, [0, 0]]
        else:
            status = self._navkey_status
            if keys_down is None:
                keys_down = self.user_input_processor.getKeysHeldDown()
            if status[0] in keys_down:
                delay_lst = self.navkey_cycle_delay_frame
                status[1][1] += 1
                if status[1][1] == delay_lst[status[1][0]]:
                    b_inds1 = self.navkeyMoveCalculator(status[0], b_inds1)
                    status[1][1] = 0
                    status[1][0] += (status[1][0] < len(delay_lst) - 1)
            else:
                self._navkey_status = [None, [0, 0]]
        #print(self.navkey_status)
        if (mouse_enabled and self.setMouseOver(b_inds1_mouse, lmouse_down))\
                or (self.navkeys_enabled and self.setNavkeyButton(b_inds1)):
            screen_changed = True
        #print(quit, esc_pressed, (screen_changed, selected))
        if screen_changed:
            self._button_grid_surf = None
        return quit, running, (screen_changed, selected_b_inds)
        """


"""
class SliderPlusVerticalBattery:
    def __init__(self, screen, x, y, w, h, slider_gap_rel=0.2, track_color=None,
            thumb_color=None, thumb_radius_rel=1, font=None,
            demarc_line_lens_rel=None, number_size_rel=2,
            numbers_color=None, demarc_line_colors=None,
            thumb_outline_color=None, slider_w_prop=0.75,
            title_size_rel=0.4, title_color=None, title_gap_rel=0.2,
            val_text_size_rel=0.4, val_text_color=None):
        self.screen = screen
        self.dims = (x, y, w, h)
        self.slider_gap_rel = slider_gap_rel
        self.track_color = track_color_def if track_color is None else\
            track_color
        self.thumb_radius_rel = thumb_radius_rel
        self.font = font_def_func() if font is None else font
        self.demarc_line_lens_rel = demarc_line_lens_rel
        self.number_size_rel = number_size_rel
        self.slider_w_prop = slider_w_prop
        self.title_size_rel = title_size_rel
        self.title_gap_rel = title_gap_rel
        self.val_text_size_rel = val_text_size_rel

        self.track_color = track_color_def if track_color is None else\
            track_color
        self.numbers_color = text_color_def if numbers_color is None\
            else numbers_color
        if demarc_line_colors is None:
            self.demarc_line_colors = (self.track_color,)
        elif isinstance(demarc_line_colors[0], int):
            self.demarc_line_colors = (tuple(demarc_line_colors),)
        else: self.demarc_line_colors = tuple(tuple(c) for c in demarc_line_colors)
        self.thumb_color = thumb_color_def if thumb_color is None\
                else thumb_color
        self.thumb_outline_color = thumb_outline_color
        self.title_color = text_color_def if title_color is None\
                else title_color
        self.val_text_color = self.title_color if val_text_color is None\
                else val_text_color
         
        self.sliderPlus_objects = []
        self.sliderPlus_dims_set = True
        self.vals = []

    def addSliderPlus(self, title, val_range=(0, 100), demarc_intervals=(20, 10, 5),\
            demarc_start_val=0, increment=None, increment_start=None, default_val=None, numbers_dp=0):
        self.sliderPlus_objects.append(
            SliderPlus(title, self.screen, *self.dims, val_range=val_range,
                demarc_intervals=demarc_intervals,
                demarc_start_val=demarc_start_val,
                increment=increment, increment_start=increment_start, track_color=self.track_color,
                thumb_color=self.thumb_color, thumb_radius_rel=self.thumb_radius_rel,
                default_val=default_val, font=self.font,
                demarc_line_lens_rel=self.demarc_line_lens_rel,
                numbers_dp=numbers_dp, number_size_rel=self.number_size_rel,
                numbers_color=self.numbers_color, demarc_line_colors=self.demarc_line_colors,
                thumb_outline_color=self.thumb_outline_color,
                slider_w_prop=self.slider_w_prop,
                title_size_rel=self.title_size_rel,
                title_color=self.title_color, title_gap_rel=self.title_gap_rel,
                val_text_size_rel=self.val_text_size_rel,
                val_text_color=self.val_text_color
            )
        )
        self.sliderPlus_dims_set = False
        self.vals.append(self.sliderPlus_objects[-1].val)
    
    @property
    def dims(self):
        return self._dims
    
    @dims.setter
    def dims(self, dims):
        self._sliderPlus_dims = None
        self._dims = dims
        return
    
    @property
    def sliderPlus_dims(self):
        res = getattr(self, "_sliderPlus_dims", None)
        if res is None:
            y_lst, h = self.findSliderPlusVerticalDimensions()
            res = [(self.dims[0], y, self.dims[2], h) for y in y_lst]
            self._sliderPlus_dims = res
        return res
    
    def findSliderPlusVerticalDimensions(self):
        n = len(self.sliderPlus_objects)
        h_plus_gap = self.dims[3] / (n - self.slider_gap_rel)
        h = math.floor((1 - self.slider_gap_rel) * h_plus_gap)
        y_lst = [self.dims[1] + math.floor(i * h_plus_gap) for i in range(n)]
        return y_lst, h
    
    def setSliderPlusDimensions(self):
        if self.sliderPlus_dims_set: return
        for slider_plus, dims in zip(self.sliderPlus_objects, self.sliderPlus_dims):
            slider_plus.dims = dims
        self.sliderPlus_dims_set = True
        return
    
    def event_loop(self, mouse_pos=None, keys_pressed=None,
            mouse_down=None, mouse_clicked=False,
            nav_keys=None, nav_keys_active=False):
        screen_changed = False
        for i, slider_plus in enumerate(self.sliderPlus_objects):
            change, val = slider_plus.event_loop(\
                    mouse_pos=mouse_pos, keys_pressed=keys_pressed,\
                    mouse_down=mouse_down, mouse_clicked=mouse_clicked,\
                    nav_keys=nav_keys, nav_keys_active=nav_keys_active)
            if change:
                screen_changed = True
                self.vals[i] = val
        return screen_changed, self.vals
    
    def draw(self):
        if not self.sliderPlus_dims_set:
            self.setSliderPlusDimensions()
        for slider_plus in self.sliderPlus_objects:
            slider_plus.draw()
        pygame.draw.rect(self.screen, (0, 100, 255), self.dims, 1)
        return

"""
        
        
        
