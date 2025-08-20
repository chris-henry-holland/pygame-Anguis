#!/usr/bin/env python

import functools
import os
import sys

from typing import Union, Tuple, List, Set, Dict, Optional, Callable, Any

import pygame as pg
import pygame.freetype

from pygame_display_component_classes.config import(
    enter_keys_def_glob,
    navkeys_def_glob,
    mouse_lclicks,
    named_colors_def,
    font_def_func,
)
from pygame_display_component_classes.utils import Real, ColorOpacity

from pygame_display_component_classes.user_input_processing import (
    checkEvents,
    checkKeysPressed,
    getMouseStatus,
    createNavkeyDict,
    UserInputProcessor,
    UserInputProcessorMinimal,
)
from pygame_display_component_classes.position_offset_calculators import topLeftFromAnchorPosition

from pygame_display_component_classes.buttons import ButtonGrid
from pygame_display_component_classes.sliders import SliderPlusGrid
from pygame_display_component_classes.text_manager import TextGroup

from pygame_display_component_classes.display_base_classes import (
    InteractiveDisplayComponentBase,
    checkHiddenKwargs,
)

overlay_color_def = (named_colors_def["white"], 0.5)
framerate_def = 60

class MenuOverlayBase(InteractiveDisplayComponentBase):
    #navkeys_def = navkeys_def_glob
    #navkey_dict_def = createNavkeyDict(navkeys_def)

    reset_graph_edges = {
        #"screen_shape": {"shape": True},
        "shape": {"overlay_bg_surf": True, "text_surf": True},

        "overlay_color": {"overlay_bg_surf": True},

        "overlay_bg_surf": {"static_bg_surf": True},
        "text_surf": {"static_bg_surf": True},
        "static_bg_surf": {"display_surf": True},
    }

    attribute_calculation_methods = {
        #"shape": "calculateShape",
        #"anchor_type": "calculateAnchorType",
        #"anchor_rel_pos": "calculateAnchorRelativePosition",

        "overlay_bg_surf": "createOverlayBackgroundSurface",
        "text_surf": "createTextSurface",
        "static_bg_surf": "createStaticBackgroundSurface",

        "overlay_bg_img_constructor": "createOverlayBackgroundImageConstructor",
        "text_img_constructor": "createTextImageConstructor",
        "static_bg_img_constructor": "createStaticBackgroundImageConstructor",
    }

    attribute_default_functions = {
        "text_objects": ((lambda obj: []),),
        "framerate": ((lambda obj: framerate_def),),
        "overlay_color": ((lambda obj: overlay_color_def),),
        "navkeys_enabled": ((lambda obj: True),),
        "mouse_enabled": ((lambda obj: True),),
        "key_press_actions": ((lambda obj: {}),),
        "key_release_actions": ((lambda obj: {}),),
    }

    
    static_bg_components = ["overlay_bg", "text"]
    dynamic_displ_attrs = []
    #displ_component_attrs = ["static_bg", "dynamic_displ_attrs"]

    _user_input_processor = UserInputProcessor(
        key_press_event_filter=lambda obj, event: MenuOverlayBase.menuKeyEventFilter(obj, event, obj.key_press_actions),
        key_release_event_filter=lambda obj, event: MenuOverlayBase.menuKeyEventFilter(obj, event, obj.key_release_actions),
    )

    def __init__(
        self,
        shape: Tuple[Real],
        framerate: Real,
        overlay_color: Optional[Tuple[Union[Tuple[int], Real]]]=None,
        mouse_enabled: Optional[bool]=None,
        navkeys_enabled: Optional[bool]=None,
        navkeys: Optional[Tuple[Tuple[Set[int]]]]=None,
        enter_keys: Optional[Set[int]]=None,
        key_press_actions: Optional[Dict[int, Any]]=None,
        key_release_actions: Optional[Dict[int, Any]]=None,
        #exit_press_keys: Optional[Set[int]]=None,
        #exit_release_keys: Optional[Set[int]]=None,
        **kwargs,
    ) -> None:
        
        #print("Initializing menu overlay")

        checkHiddenKwargs(type(self), kwargs)
        #kwargs["shape"] = screen_shape
        #kwargs["anchor_rel_pos"] = (0, 0)
        #kwargs["anchor_type"] = "topleft"

        kwargs2 = self.initArgsManagement(locals(), kwargs=kwargs)
        super().__init__(**kwargs2, anchor_rel_pos=(0, 0), anchor_type="topleft")
        """
        super().__init__(
            screen_shape, (0, 0),
            anchor_type="topleft",
            screen_topleft_to_parent_topleft_offset=(0, 0),
            mouse_enablement=(mouse_enabled, False, mouse_enabled),
            navkeys_enablement=(navkeys_enabled, navkeys_enabled, False),
            navkeys=navkeys,
            enter_keys_enablement=(False, navkeys_enabled, False),
            enter_keys=enter_keys,
            
        )

        # Resetting the user input processor
        self._user_input_processor = None
        
        self._screen_shape = screen_shape
        
        self._framerate = framerate
        
        self.overlay_color = overlay_color
        
        self.mouse_enabled = mouse_enabled
        self.navkeys_enabled = navkeys_enabled
        self.navkeys = navkeys_def_glob if navkeys is None else navkeys
        
        #print("Setting exit_press_keys")
        self._exit_press_keys = set() if exit_press_keys is None else exit_press_keys
        #print(f"self._exit_press_keys = {self._exit_press_keys}")
        #print(f"self._user_input_processor = {self._user_input_processor}")
        #print("Finished setting exit_press_keys")
        self._exit_release_keys = set() if exit_release_keys is None else exit_release_keys
        
        self.text_objects = []

        return
        """
    #def calculateShape(self):
    #    return self.screen_shape

    @staticmethod
    def menuKeyEventFilter(obj: "MenuOverlayBase", event, key_actions: Dict[str, Any]) -> bool:
        #print("Using menuKeyEventFilter()")
        return event.key in key_actions.keys()

    def calculateAnchorType(self):
        return "topleft"
    
    def calculateAnchorRelativePosition(self):
        return (0, 0)
    """
    @property
    def exit_press_keys(self):
        return self._exit_press_keys
    
    @exit_press_keys.setter
    def exit_press_keys(self, exit_press_keys):
        if exit_press_keys is None:
            exit_press_keys = set()
        if exit_press_keys == getattr(self, "_exit_press_keys", None):
            return
        self._exit_press_keys = exit_press_keys
        self._user_input_processor = None
    
    @property
    def exit_release_keys(self):
        return self._exit_release_keys
    
    @exit_release_keys.setter
    def exit_release_keys(self, exit_release_keys):
        if exit_release_keys is None:
            exit_release_keys = set()
        if exit_release_keys == getattr(self, "_exit_release_keys", None):
            return
        self._exit_release_keys = exit_release_keys
        self._user_input_processor = None
    """
    """
    @property
    def user_input_processor(self):
        res = getattr(self, "_user_input_processor", None)
        
        if res is None:
            keys_down_func=(lambda obj: set(self.navkey_dict.keys()) if self.navkeys_enabled else set())
            key_press_event_filter = False if not self.exit_press_keys else\
                    (lambda obj, event: event.key in self.exit_press_keys)
            key_release_event_filter = False if not self.exit_release_keys else\
                    (lambda obj, event: event.key in self.exit_release_keys)
            res = UserInputProcessor(keys_down_func=keys_down_func,
                key_press_event_filter=key_press_event_filter,
                key_release_event_filter=key_release_event_filter,
                mouse_press_event_filter=False,
                mouse_release_event_filter=False,
                other_event_filter=False,
                get_mouse_status_func=False)
            self._user_input_processor = res
        return res
    
    
    @property
    def screen_shape(self):
        return self._screen_shape
    
    @screen_shape.setter
    def screen_shape(self, screen_shape):
        if screen_shape == getattr(self, "_screen_shape", None):
            return
        self._screen_shape = screen_shape
        self.screenShapeReset()
        return
    
    def screenShapeReset(self):
        self._resetButtonsSpatialProperties()
        self._resetTextGroupsSpatialProperties()
    
    @property
    def framerate(self):
        return self._framerate
    
    @framerate.setter
    def framerate(self, framerate):
        if framerate == self._framerate:
            return
        self._framerate = framerate
        self.setNavkeyCycleDelayFrame()
        return
    
    @property
    def navkeys(self):
        return self.navkeys_def if self._navkeys is None else self._navkeys
    
    @navkeys.setter
    def navkeys(self, navkeys):
        self._navkey_dict = None
        self._navkeys = navkeys
        return
    
    @property
    def navkey_dict(self):
        res = getattr(self, "_navkey_dict", None)
        if res is None:
            navkeys = self.navkeys
            if navkeys is not None:
                res = self.getNavkeyDict(navkeys)
        return self.navkey_dict_def if res is None else res
    
    @staticmethod
    def getNavkeyDict(navkeys: Tuple[Tuple[Set[int]]]):
        return createNavkeyDict(navkeys)
    
    #@property
    #def navkey_cycle_delay_frame(self):
    #    return self._navkey_cycle_delay_frame
    """
    @staticmethod
    def timeTupleSecondToFrame(framerate: Real, time_tuple: Tuple[Real]) -> Tuple[int]:
        return tuple(round(x * framerate) for x in time_tuple)
    
    def textPrinter(self, surf: "pg.Surface") -> None:
        #print("Using MenuOverlayBase method textPrinter()")
        surf_shape = (surf.get_width(), surf.get_height())
        for text_obj, max_shape_rel, anchor_screen_pos_norm in self.text_objects:
            #print(f"setting text object max shape to {tuple(x * y for x, y in zip(surf_shape, max_shape_rel))}")
            #print(text_obj.reset_graph_edges)#.get(text_obj.attr_dict["max_shape"], None))
            text_obj.max_shape = tuple(x * y for x, y in zip(surf_shape, max_shape_rel))
            #print(f"text_obj._max_font_size_given_width = {text_obj.__dict__.get('_max_font_size_given_width', None)}")
            #print(max_shape_rel, surf_shape, text_obj.max_shape)
            text_obj.anchor_rel_pos0 = tuple(x * y for x, y in zip(surf_shape, anchor_screen_pos_norm))
            #print(max_shape_rel, surf_shape, text_obj.max_shape, text_obj.anchor_rel_pos0)
            #print(text_obj.font_size)
        
        for text_obj, _, _ in self.text_objects:
            #anchor_screen_pos = tuple(x * y for x, y in zip(surf_shape, anchor_screen_pos_norm))
            #print(f"font size = {text_obj.font_size}")
            text_obj.draw(surf)
        return
    
    def addText(
        self,
        text_obj: "Text",
        max_shape_rel: Tuple[Real],
        anchor_screen_pos_norm: Tuple[Real]
    ) -> None:
        self.text_objects.append((text_obj, max_shape_rel, anchor_screen_pos_norm))
        text_obj.__dict__["container_obj"] = self
        text_obj.__dict__["_container_attr_reset_dict"] = {"updated": {"text_surf": (lambda container_obj, obj: getattr(obj, "updated", False))}}
        #print(f"max font size given width = {text_obj.max_font_size_given_width}")
        #text_obj.updated = True
        #text_obj.__dict__.setdefault("_container_attr_reset_dict", {})
        #text_obj.__dict__["_container_attr_reset_dict"].setdefault("updated", {})
        #text_obj.__dict__["_container_attr_reset_dict"]["updated"][""]
        return
    
    """
    @property
    def overlay_color(self):
        return self._overlay_color
    
    @overlay_color.setter
    def overlay_color(self, overlay_color):
        self._overlay_color = overlay_color
        self._overlay = None
        return
    """
    """
    @property
    def overlay_bg_surf(self):
        res = getattr(self, "_overlay_bg_surf", None)
        if res is None:
            res = self.createOverlayBackgroundSurface()
            self._overlay_bg_surf = res
        return res
    """
    def createOverlayBackgroundSurface(self) -> "pg.Surface":
        #print("Using createOverlayBackgroundSurface()")
        if self.overlay_color is None: return ()
        overlay_bg_surf = pg.Surface(self.shape, pg.SRCALPHA)
        color, alpha0 = self.overlay_color
        overlay_bg_surf.set_alpha(alpha0 * 255)
        overlay_bg_surf.fill(color)
        return overlay_bg_surf
    """
    @property
    def overlay_bg_img_constructor(self):
        res = getattr(self, "_overlay_bg_img_constructor", None)
        if res is None:
            res = self.createOverlayBackgroundImageConstructor()
            self._overlay_bg_img_constructor = res
        return res
    """
    def createOverlayBackgroundImageConstructor(self) -> Callable[["pg.Surface"], None]:
        overlay_bg_surf = self.overlay_bg_surf
        if overlay_bg_surf == ():
            return lambda surf: None
        
        def constructor(obj: "MenuOverlayBase", surf: "pg.Surface") -> None:
            #print("Using overlay background surface constructor")
            overlay_bg_surf = self.overlay_bg_surf
            if not overlay_bg_surf: return
            surf.blit(overlay_bg_surf, (0, 0))
            return
        
        return constructor
    """
    @property
    def text_surf(self):
        res = getattr(self, "_text_surf", None)
        if res is None:
            res = self.createTextSurface()
            self._text_surf = res
        return res
    """
    def createTextSurface(self) -> "pg.Surface":
        #print("Using createTextSurface()")
        if not self.text_objects:
            return ()
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        self.textPrinter(surf)
        return surf
    """
    @property
    def text_img_constructor(self):
        res = getattr(self, "_text_img_constructor", None)
        if res is None:
            res = self.createTextImageConstructor()
            self._text_img_constructor = res
        return res
    """
    def createTextImageConstructor(self) -> Callable[["MenuOverlayBase", "pg.Surface"], None]:
        def constructor(obj: "MenuOverlayBase", surf: "pg.Surface") -> None:
            #print("Using text image constructor")
            text_surf = self.text_surf
            if not text_surf: return
            surf.blit(text_surf, (0, 0))
            return

        #text_surf = self.text_surf
        #if text_surf == ():
        #    return lambda obj, surf: None
        
        return constructor
    """
    @property
    def static_bg_surf(self):
        res = getattr(self, "_static_bg_surf", None)
        if res is None:
            res = self.createStaticBackgroundSurface()
            self._static_bg_surf = res
        return res
    """
    def createStaticBackgroundSurface(self) -> None:
        #print("updating static background images")
        attrs = self.static_bg_components
        for attr in attrs:
            surf_attr = f"{attr}_surf"
            if getattr(self, surf_attr, None) != ():
                break
        else: return ()
        static_bg_surf = pg.Surface(self.shape, pg.SRCALPHA)
        for attr in attrs:
            img_constr_attr = f"{attr}_img_constructor"
            getattr(self, img_constr_attr)(self, static_bg_surf)
        return static_bg_surf
    """
    @property
    def static_bg_img_constructor(self):
        res = getattr(self, "_static_bg_img_constructor", None)
        if res is None:
            res = self.createStaticBackgroundImageConstructor()
            self._static_bg_img_constructor = res
        return res
    """
    def createStaticBackgroundImageConstructor(self) -> Callable[["MenuOverlayBase", "pg.Surface"], None]:
        def constructor(obj: "MenuOverlayBase", surf: "pg.Surface") -> None:
            static_bg_surf = self.static_bg_surf
            if not static_bg_surf: return
            surf.blit(static_bg_surf, (0, 0))
            return
        
        return constructor
        """
        #print("creating background constructor")
        static_bg_surf = self.static_bg_surf
        if static_bg_surf == ():
            return lambda surf: None
        return lambda obj, surf: surf.blit(static_bg_surf, (0, 0))
        """
    
    def createDisplaySurface(self) -> Optional["pg.Surface"]:
        #print("Using MenuOverlayBase method createDisplaySurface()")
        surf = pg.Surface(self.shape, pg.SRCALPHA)
        for attr in ["static_bg"] + self.dynamic_displ_attrs:
            #print(attr)
            constructor_func = getattr(self, f"{attr}_img_constructor", (lambda obj, surf: None))
            constructor_func(self, surf)
        return surf

    """
    def draw(self, surf: "pg.Surface") -> None:
        shape = surf.get_width(), surf.get_height()
        self.screen_shape = shape
        
        self.static_bg_img_constructor(surf)
        
        seen_attrs = set()
        for cls in type(self).mro():
            for attr in cls.__dict__.get("dynamic_displ_attrs", []):
                if attr in seen_attrs: continue
                seen_attrs.add(attr)
                obj = getattr(self, attr, None)
                if obj is None: continue
                elif isinstance(obj, (list, tuple)):
                    for obj2 in obj:
                        obj2.draw(surf)
                else:
                    obj.draw(surf)
        return
    """
    """
    def getRequiredInputs(self):
        #print("Using MenuOverlay method getRequiredInputs()")
        quit, esc_pressed, events = self.user_input_processor.getEvents(self)
        return quit, esc_pressed, {"events": events,\
                "keys_down": self.user_input_processor.getKeysHeldDown(self),\
                "mouse_status": self.user_input_processor.getMouseStatus(self)}
    """
    
    def eventLoop(
        self,
        events: Optional[List[Tuple["pg.Event", int]]]=None,
        keys_down: Optional[Set[int]]=None,
        mouse_status: Optional[Tuple[int]]=None,
        check_axes: Tuple[int]=(0, 1),
    ) -> Tuple[bool, bool, bool, Any]:
        ((quit, esc_pressed), (events, keys_down, mouse_status, check_axes)) = self.getEventLoopArguments(events=events, keys_down=keys_down, mouse_status=mouse_status, check_axes=check_axes)
        #print(events)
        running = not quit and not esc_pressed
        #screen_changed = False
        #print(f"mouse_status = {mouse_status}")
        screen_changed = False
        quit2, running2, screen_changed2, actions = self._eventLoop(events, keys_down, mouse_status, check_axes)
        #print(f"_eventLoop() screen changed = {screen_changed2}")
        if quit2: quit = True
        if not running2: running = False
        #if screen_changed2: screen_changed = True
        #screen_changed = self.drawUpdateRequired()
        if screen_changed2: screen_changed = True
        return quit, running, screen_changed, actions
        """
        #print("using menu eventLoop() method")
        running, quit = True, False
        #buttons = getattr(self, "buttons", None)
        screen_changed = False
        
        #print(mouse_status)
        #print(self.mouse_enablement, self.mouse_enabled)
        
        if events is None:
            #print(events)
            quit, esc_pressed, events = self.user_input_processor.getEvents()
            if esc_pressed:
                running = False
        #if events:
        #    print(events)
        #    print(self.exit_press_keys)
        #    print(self.exit_release_keys)
        events2 = []
        for event_tup in events:
            #print((event_tup[1] == 0 and event_tup[0].key in\
            #        self.exit_press_keys))
            if not (event_tup[1] == 0 and event_tup[0].key in\
                    self.exit_press_keys) and not (event_tup[1] == 1\
                    and event_tup[0].key in self.exit_release_keys):
                 events2.append(event_tup)
                 continue
            running = False
            break
        actions = []
        return quit, running, screen_changed, actions
        """
    
    def _eventLoop(
        self,
        events: List[Tuple["pg.Event", int]],
        keys_down: Set[int],
        mouse_status: Tuple[int],
        check_axes: Tuple[int]=(0, 1),
    ) -> Tuple[bool, bool, bool, list]:
        actions = []
        for event in events:
            if event[1] == 0: act_dict = self.key_press_actions
            elif event[1] == 1: act_dict = self.key_release_actions
            else: continue
            k = event[0].key
            if k in act_dict.keys():
                actions.append(act_dict[k])
        return False, True, False, actions

class ButtonMenuOverlay(MenuOverlayBase):
    #navkeys_def = navkeys_def_glob
    #navkey_dict_def = createNavkeyDict(navkeys_def)

    reset_graph_edges = {
        "shape": {"button_grid_shape_actual": True, "button_grid_anchor_pos_actual": True},
        "button_grid_max_shape_norm": {"button_grid_shape_actual": True},
        "button_grid_wh_ratio_range": {"button_grid_shape_actual": True},
        "button_grid_anchor_pos_norm": {"button_grid_anchor_pos_actual": True},
        #"button_grid_shape_actual": {"button_grid_surf": True},
        #"button_grid_surf": {"display_surf": True},
        "framerate": {"navkey_cycle_delay_frame": True},
        "navkey_cycle_delay_s": {"navkey_cycle_delay_frame": True},
    }

    custom_attribute_change_propogation_methods = {
        "button_grid_shape_actual": "customButtonGridShapeActualChangePropogation",
        "button_grid_anchor_pos_actual": "customButtonGridAnchorPositionActualChangePropogation",
        "navkey_cycle_delay_frame": "customNavkeyCycleDelayFrameChangePropogation",
    }

    attribute_calculation_methods = {
        "navkey_cycle_delay_frame": "calculateNavkeyCycleDelayFrame",
        #"button_grid_spatial_props": "calculateButtonGridSpatialProperties",
        "button_grid_shape_actual": "calculateButtonGridShapeActual",
        "button_grid_anchor_pos_actual": "calculateButtonGridAnchorPositionActual",

        #"button_grid_surf": "createStaticButtonGridSurface",

        "button_grid_img_constructor": "createButtonGridImageConstructor",
    }

    attribute_default_functions = {
        "navkey_cycle_delay_s": ((lambda obj: (0.3, 0.2)),),
        "button_grid_uip_idx": ((lambda obj: -1),),
        "button_grid_max_shape_norm": ((lambda obj: ()),),
        "button_grid_wh_ratio_range": ((lambda obj: ()),),
        "button_grid_anchor_pos_norm": ((lambda obj: ()),),
        "button_grid": ((lambda obj: None),),
    }

    #dynamic_displ_attrs = []
    dynamic_displ_attrs = MenuOverlayBase.dynamic_displ_attrs + ["button_grid"]
    #static_bg_components = MenuOverlayBase.static_bg_components
    
    
    #static_bg_components = ["overlay_bg", "text"]

    def __init__(
        self,
        shape: Tuple[Real],
        framerate: Real,
        overlay_color: Optional[Tuple[Union[Tuple[int], Real]]]=None,
        mouse_enabled: bool=True,
        navkeys_enabled: bool=True,
        navkeys: Optional[Tuple[Tuple[Set[int]]]]=None,
        navkey_cycle_delay_s: Optional[Tuple[Real]]=None,
        enter_keys: Optional[Set[int]]=None,
        #exit_press_keys: Optional[Set[int]]=None,
        #exit_release_keys: Optional[Set[int]]=None,
        **kwargs,
    ):
        #print(f"__init__() navkey_cycle_delay_s = {navkey_cycle_delay_s}")
        #print(kwargs)
        checkHiddenKwargs(type(self), kwargs)

        kwargs2 = self.initArgsManagement(locals(), kwargs=kwargs, rm_args=["navkey_cycle_delay_s"])
        super().__init__(**kwargs2)
        self.setAttributes({"navkey_cycle_delay_s": navkey_cycle_delay_s})
        
        """
        super().__init__(
            shape=shape,
            framerate=framerate,
            overlay_color=overlay_color,
            mouse_enabled=mouse_enabled,
            navkeys=navkeys,
            enter_keys=enter_keys,
            #exit_press_keys=exit_press_keys,
            #exit_release_keys=exit_release_keys,
        )

        self._navkey_cycle_delay_s = navkey_cycle_delay_s
        self.setNavkeyCycleDelayFrame()
        self.button_grid_uip_idx = None
        """
    
    def customButtonGridShapeActualChangePropogation(
        self,
        new_val: Optional[Tuple[int, int]],
        prev_val: Optional[Tuple[int, int]],
    ) -> None:
        #print("Using customButtonGridShapeActualChangePropogation()")
        button_grid = self.button_grid
        if button_grid is None: return
        button_grid.shape = new_val
        return
    
    def customButtonGridAnchorPositionActualChangePropogation(
        self,
        new_val: Optional[Tuple[int, int]],
        prev_val: Optional[Tuple[int, int]],
    ) -> None:
        #print("Using customButtonGridAnchorPositionActualChangePropogation()")
        #print(f"new anchor position = {new_val}")
        button_grid = self.button_grid
        if button_grid is None: return
        button_grid.anchor_rel_pos = new_val
        return

    def customNavkeyCycleDelayFrameChangePropogation(
        self,
        new_val: Optional[Tuple[int, int]],
        prev_val: Optional[Tuple[int, int]],
    ) -> None:
        button_grid = self.button_grid
        if button_grid is None: return
        button_grid.navkey_cycle_delay_frame = new_val
        return
    
    def calculateNavkeyCycleDelayFrame(self) -> int:
        return self.timeTupleSecondToFrame(self.framerate, self.navkey_cycle_delay_s)

    def calculateButtonGridShapeActual(self) -> Tuple[int, int]:
        max_shape_norm = self.button_grid_max_shape_norm
        wh_ratio_rng = self.button_grid_wh_ratio_range

        return self.calculateMaxShapeActualGivenWidthHeightRatioRange(
            max_shape_norm,
            self.shape,
            wh_ratio_rng,
        )
        """
        if not max_shape_norm or not wh_rng: return ()
        parent_shape = self.shape
        shape_actual = [x * y for x, y in zip(parent_shape, max_shape_norm)]
        
        wh_ratio = shape_actual[0] / shape_actual[1]
        if wh_ratio < wh_rng[0]:
            shape_actual[1] *= wh_ratio / wh_rng[0]
        elif wh_ratio > shape_actual[1]:
            shape_actual[0] *= wh_rng[1] / wh_ratio
        return tuple(shape_actual)
        """
    
    def calculateButtonGridAnchorPositionActual(self) -> Tuple[int, int]:
        anchor_pos_norm = self.button_grid_anchor_pos_norm
        if not anchor_pos_norm: return ()
        parent_shape = self.shape
        anchor_pos_actual = tuple(x * y for x, y in zip(parent_shape, anchor_pos_norm))
        #print(f"button grid anchor position actual = {anchor_pos_actual}")
        return anchor_pos_actual
    
    def createButtonGridImageConstructor(self) -> Callable[["ButtonMenuOverlay", "pg.Surface"], None]:
        def constructor(obj: ButtonMenuOverlay, surf: "pg.Surface") -> None:
            #print("Using button grid constructor")
            button_grid = obj.button_grid
            if not button_grid: return
            #print("button grid is not None")
            #print(button_grid.anchor_rel_pos, button_grid.anchor_type)
            return button_grid.draw(surf)
        return constructor
    
    # Review- add type hints
    def setupButtonGrid(
        self,
        anchor_pos_norm: Tuple[Real],
        anchor_type: str,
        button_grid_max_shape_norm: Tuple[Real],
        button_text_anchortype_and_actions: List[List[Optional[Tuple[Union[str, Tuple[Union[Tuple[str], int]]], Union[str, Tuple[Union[Tuple[str], int]]], Callable]]]],
        wh_ratio_range: Optional[Tuple[Real]]=None,
        text_groups: Optional[Tuple[Union[Optional[Tuple["TextGroup"]], int]]]=None,
        button_gaps_rel_shape=None,
        #fonts=None,
        #font_sizes=None,
        font_colors=None,
        text_borders_rel=None,
        fill_colors=None,
        outline_widths=None,
        outline_colors=None,
    ) -> None:
        
        grid_dims = (len(button_text_anchortype_and_actions[0]), len(button_text_anchortype_and_actions))
        if wh_ratio_range is None:
            wh_ratio_range = (0, float("inf"))
        self.setAttributes({
            "button_grid_max_shape_norm": button_grid_max_shape_norm,
            "button_grid_anchor_pos_norm": anchor_pos_norm,
            "button_grid_wh_ratio_range": wh_ratio_range,
        })
        #print(f"navkey_cycle_delay_s = {self.navkey_cycle_delay_s}")
        #print(f"navkey_cycle_delay_frame = {self.navkey_cycle_delay_frame}")
        button_grid = ButtonGrid(
            grid_dims=grid_dims,
            shape=self.button_grid_shape_actual,
            anchor_rel_pos=self.button_grid_anchor_pos_actual,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=self.screen_topleft_to_parent_topleft_offset,
            button_gaps_rel_shape=button_gaps_rel_shape,
            text_groups=text_groups,
            font_colors=font_colors,
            text_borders_rel=text_borders_rel,
            fill_colors=fill_colors,
            outline_widths=outline_widths,
            outline_colors=outline_colors,
            mouse_enabled=self.mouse_enabled,
            navkeys_enabled=self.navkeys_enabled,
            navkeys=self.navkeys,
            navkey_cycle_delay_frame=self.navkey_cycle_delay_frame,
            enter_keys=self.enter_keys,
            _from_container=True,
            _container_obj=self,
            _container_attr_reset_dict={"changed_since_last_draw": {"display_surf": (lambda container_obj, obj: obj.drawUpdateRequired())}},
        )
        
        button_actions = [[] for _ in range(grid_dims[0])]
        for i2, row in enumerate(button_text_anchortype_and_actions):
            for i1, tup in enumerate(row):
                if tup is None:
                    button_actions[i1].append(None)
                (text, anchor_types, action) = tup
                button_grid.setupButtonGridElement(
                    grid_inds=(i1, i2),
                    text=text,
                    text_anchor_types=anchor_types,
                )
                button_actions[i1].append(action)
        
        self.button_grid = button_grid
        self.button_actions = button_actions
        if self.button_grid_uip_idx != -1:
            self.user_input_processor.removeSubUIP(self.button_grid_uip_idx)
        #print("adding button grid uip")
        self.button_grid_uip_idx = self.user_input_processor.addSubUIP(button_grid.user_input_processor, obj_func=(lambda obj: obj.button_grid))
        #print("added button grid uip to button menu uip")
        
        #print(button_grid.mouse_enabled)
        #button_grid.grid_shape = overall_shape
        #button_grid.dims = (*topleft, *overall_shape)
        #print(button_grid.dims)
        return
    
    def _eventLoop(
        self,
        events: List[int],
        keys_down: Set[int],
        mouse_status: Tuple[int],
        check_axes: Tuple[int]=(0, 1),
    ) -> Tuple[bool, bool, bool, list]:
        #print("Using ButtonMenuOverlay method _eventLoop()")
        #print(f"button menu overlay display surface = {self.__dict__.get('_display_surf', None)}, {'display_surf' in self.getPendingAttributeChanges()}")
        #((quit, esc_pressed), (events, keys_down, mouse_status, check_axes)) = self.getEventLoopArguments(events=events, keys_down=keys_down, mouse_status=mouse_status, check_axes=check_axes)
        #print(events)
        #running = not quit and not esc_pressed
        #screen_changed = False
        

        quit, running, screen_changed, actions = super()._eventLoop(events, keys_down, mouse_status, check_axes)
        #print(f"mouse_status = {mouse_status}")

        button_grid = getattr(self, "button_grid", None)
        if button_grid is not None:
            quit2, running2, change, selected_b_inds = button_grid.eventLoop(
                events=events,
                keys_down=keys_down,
                mouse_status=mouse_status,
                check_axes=check_axes
            )
            if change: screen_changed = True
            if quit2: quit = True
            if not running2: running = False
            actions.extend([self.button_actions[b_inds[0]][b_inds[1]] for b_inds in selected_b_inds])
        screen_changed = self.drawUpdateRequired()
        #if screen_changed: print(f"button menu overlay redraw required")
        #print("Finishing ButtonMenuOverlay method _eventLoop()")
        #print(f"button menu overlay display surface = {self.__dict__.get('_display_surf', None)}, {'display_surf' in self.getPendingAttributeChanges()}")#{self.__dict__.get('_display_surf', None)}")
        return quit, running, screen_changed, actions
    """
    def calculateButtonGridSpatialProperties(self) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
        bsp_rel = self.buttons_spatial_props_rel
        if bsp_rel is None:
            return ()
        (anchor_screen_pos_norm, anchor_type, overall_shape_rel,\
                wh_ratio_range) = bsp_rel
        
        screen_shape = self.shape
        anchor_screen_pos = tuple(x * y for x, y in zip(screen_shape, anchor_screen_pos_norm))
        
        overall_shape = [x * y for x, y in zip(screen_shape, overall_shape_rel)]
        #print(overall_shape)
        wh_ratio = overall_shape[0] / overall_shape[1]
        if wh_ratio < wh_ratio_range[0]:
            overall_shape[1] *= wh_ratio / wh_ratio_range[0]
        elif wh_ratio > wh_ratio_range[1]:
            overall_shape[0] *= wh_ratio_range[1] / wh_ratio
        
        overall_shape = tuple(overall_shape)
        topleft_pos = topLeftFromAnchorPosition(overall_shape, anchor_type, anchor_screen_pos)
        
        return (anchor_screen_pos, topleft_pos, overall_shape)
    """
    """
    @property
    def exit_press_keys(self):
        return self._exit_press_keys
    
    @exit_press_keys.setter
    def exit_press_keys(self, exit_press_keys):
        #print("using setter")
        if exit_press_keys is None:
            exit_press_keys = set()
        #print(getattr(self, "_exit_press_keys", None))
        if exit_press_keys == getattr(self, "_exit_press_keys", None):
            return
        #print(f"setting exit_press_keys to {exit_press_keys}")
        self._exit_press_keys = exit_press_keys
        self._user_input_processor = None
    
    @property
    def exit_release_keys(self):
        return self._exit_release_keys
    
    @exit_release_keys.setter
    def exit_release_keys(self, exit_release_keys):
        #print("setter for exit_release_keys")
        if exit_release_keys is None:
            exit_release_keys = set()
        if exit_release_keys == getattr(self, "_exit_release_keys", None):
            return
        self._exit_release_keys = exit_release_keys
        self._user_input_processor = None
    
    
    @property
    def user_input_processor(self):
        res = getattr(self, "_user_input_processor", None)
        #print("getting user_input_processor")
        
        if res is None:
            keys_down_func=(lambda obj: set(self.navkey_dict.keys()) if self.navkeys_enabled else set())
            key_press_event_filter = False if not self.exit_press_keys else\
                    (lambda obj, event: event.key in self.exit_press_keys)
            key_release_event_filter = False if not self.exit_release_keys else\
                    (lambda obj, event: event.key in self.exit_release_keys)
            #print("creating UserInputProcessor object")
            #print(f"exit press keys = {self.exit_press_keys}")
            res = UserInputProcessor(keys_down_func=keys_down_func,
                key_press_event_filter=key_press_event_filter,
                key_release_event_filter=key_release_event_filter,
                mouse_press_event_filter=False,
                mouse_release_event_filter=False,
                other_event_filter=False,
                get_mouse_status_func=False)
            self._user_input_processor = res
        return res
    
    
    @property
    def screen_shape(self):
        return self._screen_shape
    
    @screen_shape.setter
    def screen_shape(self, screen_shape):
        if screen_shape == getattr(self, "_screen_shape", None):
            return
        self._screen_shape = screen_shape
        self.screenShapeReset()
        return
    
    def screenShapeReset(self):
        self._resetButtonsSpatialProperties()
        self._resetTextGroupsSpatialProperties()
    
    @property
    def framerate(self):
        return self._framerate
    
    @framerate.setter
    def framerate(self, framerate):
        if framerate == self._framerate:
            return
        self._framerate = framerate
        self.setNavkeyCycleDelayFrame()
        return
    
    @property
    def navkeys(self):
        return self.navkeys_def if self._navkeys is None else self._navkeys
    
    @navkeys.setter
    def navkeys(self, navkeys):
        self._navkey_dict = None
        self._navkeys = navkeys
        return
    
    @property
    def navkey_dict(self):
        res = getattr(self, "_navkey_dict", None)
        if res is None:
            navkeys = self.navkeys
            if navkeys is not None:
                res = self.getNavkeyDict(navkeys)
        return self.navkey_dict_def if res is None else res
    
    @staticmethod
    def getNavkeyDict(navkeys: Tuple[Tuple[Set[int]]]):
        return createNavkeyDict(navkeys)
    """

    
    """
    @property
    def navkey_cycle_delay_s(self):
        return self._navkey_cycle_delay_s
    
    @navkey_cycle_delay_s.setter
    def navkey_cycle_delay_s(self, navkey_cycle_delay_s):
        if navkey_cycle_delay_s == self._navkey_cycle_delay_s:
            return
        self._navkey_cycle_delay_s = navkey_cycle_delay_s
        self.setNavkeyCycleDelayFrame()
        return
    
    @property
    def navkey_cycle_delay_frame(self):
        return self._navkey_cycle_delay_frame
    """
    """
    @staticmethod
    def timeTupleSecondToFrame(framerate: Real, time_tuple: Tuple[Real]) -> Tuple[int]:
        return tuple(round(x * framerate) for x in time_tuple)
    """
    """
    def setNavkeyCycleDelayFrame(self) -> None:
        res = self.timeTupleSecondToFrame(self.framerate, self.navkey_cycle_delay_s)
        self._navkey_cycle_delay_frame = res
        buttons = getattr(self, "buttons", None)
        if buttons is not None:
            buttons.navkey_cycle_delay_frame = res
        return
    """
    """
    def textPrinter(self, surf: "pg.Surface") -> None:
        print("Using ButtonMenuOverlay method textPrinter()")
        surf_shape = (surf.get_width(), surf.get_height())
        for text_obj, max_shape_rel, anchor_screen_pos_norm in self.text_objects:
            text_obj.max_shape = tuple(x * y for x, y in zip(surf_shape, max_shape_rel))
            print(max_shape_rel, surf_shape, text_obj.max_shape)
            text_obj.anchor_rel_pos0 = tuple(x * y for x, y in zip(surf_shape, anchor_screen_pos_norm))
        for text_obj, _, _ in self.text_objects:
            #anchor_rel_pos = tuple(x * y for x, y in zip(surf_shape, anchor_screen_pos_norm))
            text_obj.draw(surf)
        return
    
    def addText(self, text_obj: "Text", max_shape_rel: Tuple[Real],\
            anchor_screen_pos_norm: Tuple[Real]) -> None:
        self.text_objects.append((text_obj, max_shape_rel, anchor_screen_pos_norm))
        return
    """
    """
    @property
    def buttons_spatial_props_rel(self):
        return getattr(self, "_buttons_spatial_props_rel", None)
    
    @buttons_spatial_props_rel.setter
    def buttons_spatial_props_rel(self, buttons_spatial_props_rel):
        prev = getattr(self, "_buttons_spatial_props_rel", None)
        if buttons_spatial_props_rel == prev:
            return
        self._resetButtonsSpatialProperties()
        return
    
    
    @property
    def buttons_spatial_props(self):
        res = getattr(self, "_buttons_spatial_props", None)
        if res is None:
            res = self.findButtonsSpatialProperties()
            self._buttons_spatial_props = res
        return res
    
    def findButtonsSpatialProperties(self) -> Tuple[Any]:
        bsp_rel = self.buttons_spatial_props_rel
        if bsp_rel is None:
            return ()
        (anchor_screen_pos_norm, anchor_type, overall_shape_rel,\
                wh_ratio_range) = bsp_rel
        
        screen_shape = self.shape
        anchor_screen_pos = tuple(x * y for x, y in zip(screen_shape, anchor_screen_pos_norm))
        
        overall_shape = [x * y for x, y in zip(screen_shape, overall_shape_rel)]
        #print(overall_shape)
        wh_ratio = overall_shape[0] / overall_shape[1]
        if wh_ratio < wh_ratio_range[0]:
            overall_shape[1] *= wh_ratio / wh_ratio_range[0]
        elif wh_ratio > wh_ratio_range[1]:
            overall_shape[0] *= wh_ratio_range[1] / wh_ratio
        
        overall_shape = tuple(overall_shape)
        topleft = topLeftFromAnchorPosition(overall_shape, anchor_type, anchor_screen_pos)
        
        return (anchor_screen_pos, topleft, overall_shape)
    
    def _resetButtonsSpatialProperties(self) -> None:
        if not self.buttons: return
        #bsp_rel = self.buttons_spatial_props_rel
        bsp = self.findButtonsSpatialProperties()
        if not bsp: return
        _, topleft, overall_shape = bsp
        self.buttons.dims = (*topleft, *overall_shape)
        return
    """
    """
    def setupButtons(
        self,
        anchor_screen_pos_norm: Tuple[Real],
        anchor_type: str,
        overall_shape_rel: Tuple[Real],
        wh_ratio_range: Tuple[Real],
        button_text_anchortype_and_actions: List[List[Optional[Tuple[Union[str, Tuple[Union[Tuple[str], int]]], Union[str, Tuple[Union[Tuple[str], int]]], Callable]]]],
        text_groups: Optional[Tuple[Union[Optional[Tuple["TextGroup"]], int]]]=None,
        button_gaps_rel_shape=(0.2, 0.2),
        #fonts=None,
        #font_sizes=None,
        font_colors=None,
        text_borders_rel=None,
        fill_colors=None,
        outline_widths=None,
        outline_colors=None
    ) -> None:
        
        self._buttons_spatial_props_rel = (anchor_screen_pos_norm, anchor_type,\
                overall_shape_rel, wh_ratio_range)
        
        (anchor_screen_pos, topleft, overall_shape) = self.findButtonsSpatialProperties()
        
        grid_dims = (len(button_text_anchortype_and_actions[0]), len(button_text_anchortype_and_actions))

        button_grid = ButtonGrid(
            grid_dims=grid_dims,
            shape=overall_shape,
            anchor_rel_pos=anchor_screen_pos,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=self.screen_topleft_to_parent_topleft_offset,
            button_gaps_rel_shape=button_gaps_rel_shape,
            text_groups=text_groups,
            font_colors=font_colors,
            text_borders_rel=text_borders_rel,
            fill_colors=fill_colors,
            outline_widths=outline_widths,
            outline_colors=outline_colors,
            mouse_enabled=self.mouse_enabled,
            navkeys_enabled=self.navkeys_enabled,
            navkeys=self.navkeys,
            navkey_cycle_delay_frame=self.navkey_cycle_delay_frame,
            enter_keys=self.enter_keys,
        )
        
        button_actions = [[] for _ in range(grid_dims[0])]
        for i2, row in enumerate(button_text_anchortype_and_actions):
            for i1, tup in enumerate(row):
                if tup is None:
                    button_actions[i1].append(None)
                (text, anchor_types, action) = tup
                button_grid.setupButtonGridElement(
                    grid_inds=(i1, i2),
                    text=text,
                    text_anchor_types=anchor_types,
                )
                button_actions[i1].append(action)
        
        if self.buttons_uip_idx != -1:
            self.user_input_processor.removeSubUIP(self.buttons_uip_idx)
        self.buttons_uip_idx = self.user_input_processor.addSubUIP(button_grid.user_input_processor)
        ""
        button_grid = ButtonGrid(topleft, (200, 50),
            button_text, button_gap_rel_shape=button_gap_rel_shape,
            fonts=fonts, font_sizes=font_sizes,
            font_colors=font_colors, text_borders_rel=text_borders_rel,
            fill_colors=fill_colors, outline_widths=outline_widths,
            outline_colors=outline_colors,
            mouse_enabled=self.mouse_enabled,
            navkeys_enabled=self.navkeys_enabled,
            navkeys=self.navkeys,
            navkey_cycle_delay_frame=self.navkey_cycle_delay_frame,
            text_global_asc_desc_chars=None)
        ""
        
        #print(button_grid.mouse_enabled)
        #button_grid.grid_shape = overall_shape
        #button_grid.dims = (*topleft, *overall_shape)
        #print(button_grid.dims)
        self.buttons = button_grid
        self.button_actions = button_actions
        return
    """
    """
    @property
    def overlay_color(self):
        return self._overlay_color
    
    @overlay_color.setter
    def overlay_color(self, overlay_color):
        self._overlay_color = overlay_color
        self._overlay = None
        return
    
    @property
    def overlay_bg_surf(self):
        res = getattr(self, "_overlay_bg_surf", None)
        if res is None:
            res = self.createOverlayBackgroundSurface()
            self._overlay_bg_surf = res
        return res
    
    def createOverlayBackgroundSurface(self) -> "pg.Surface":
        if self.overlay_color is None: return ()
        overlay_bg_surf = pg.Surface(self.screen_shape, pg.SRCALPHA)
        color, alpha0 = self.overlay_color
        overlay_bg_surf.set_alpha(alpha0 * 255)
        overlay_bg_surf.fill(color)
        return overlay_bg_surf
    
    @property
    def overlay_bg_img_constructor(self):
        res = getattr(self, "_overlay_bg_img_constructor", None)
        if res is None:
            res = self.createOverlayBackgroundImageConstructor()
            self._overlay_bg_img_constructor = res
        return res
    
    def createOverlayBackgroundImageConstructor(self):
        overlay_bg_surf = self.overlay_bg_surf
        if overlay_bg_surf == ():
            return lambda surf: None
        return lambda surf: surf.blit(overlay_bg_surf, (0, 0))
    
    @property
    def text_surf(self):
        res = getattr(self, "_text_surf", None)
        if res is None:
            res = self.createTextSurface()
            self._text_surf = res
        return res
    
    def createTextSurface(self):
        if not self.text_objects:
            return ()
        surf = pg.Surface(self.screen_shape, pg.SRCALPHA)
        self.textPrinter(surf)
        return surf
    
    @property
    def text_img_constructor(self):
        res = getattr(self, "_text_img_constructor", None)
        if res is None:
            res = self.createTextImageConstructor()
            self._text_img_constructor = res
        return res
    
    def createTextImageConstructor(self):
        text_surf = self.text_surf
        if text_surf == ():
            return lambda surf: None
        return lambda surf: surf.blit(text_surf, (0, 0))
        
    @property
    def static_bg_surf(self):
        res = getattr(self, "_static_bg_surf", None)
        if res is None:
            res = self.createStaticBackgroundSurface()
            self._static_bg_surf = res
        return res
    
    def createStaticBackgroundSurface(self) -> None:
        #print("updating static background images")
        attrs = self.static_bg_components
        for attr in attrs:
            surf_attr = f"{attr}_surf"
            if getattr(self, surf_attr, None) != ():
                break
        else: return ()
        static_bg_surf = pg.Surface(self.screen_shape, pg.SRCALPHA)
        for attr in attrs:
            img_constr_attr = f"{attr}_img_constructor"
            getattr(self, img_constr_attr)(static_bg_surf)
        return static_bg_surf
    
    @property
    def static_bg_img_constructor(self):
        res = getattr(self, "_static_bg_img_constructor", None)
        if res is None:
            res = self.createStaticBackgroundImageConstructor()
            self._static_bg_img_constructor = res
        return res
    
    def createStaticBackgroundImageConstructor(self):
        #print("creating background constructor")
        static_bg_surf = self.static_bg_surf
        if static_bg_surf == ():
            return lambda surf: None
        return lambda surf: surf.blit(static_bg_surf, (0, 0))
    """
    """
    def draw(self, surf: "pg.Surface") -> None:
        shape = surf.get_width(), surf.get_height()
        self.screen_shape = shape
        
        self.static_bg_img_constructor(surf)
        
        seen_attrs = set()
        for cls in type(self).mro():
            for attr in cls.__dict__.get("dynamic_displ_attrs", []):
                if attr in seen_attrs: continue
                seen_attrs.add(attr)
                obj = getattr(self, attr, None)
                if obj is None: continue
                elif isinstance(obj, (list, tuple)):
                    for obj2 in obj:
                        obj2.draw(surf)
                else:
                    obj.draw(surf)
        return
    """
    """
    @property
    def input_check_parameters(self):
        res = getattr(self, "_input_check_parameters", None)
        if res is None:
            res = self._findInputCheckParameters()
            self._input_check_parameters = res
        return res
    
    def _findInputCheckParameters(self):
        #print("hi")
        if hasattr(self, "buttons") and\
                hasattr(self.buttons, "input_check_parameters"):
            #print(self.buttons.input_check_parameters)
            return self.buttons.input_check_parameters
        return (None, None, None, False)
    """
    """
    def getRequiredInputs(self):
        #print("Using MenuOverlay method getRequiredInputs()")
        quit, esc_pressed, events = self.user_input_processor.getEvents(self)
        return quit, esc_pressed, {"events": events,\
                "keys_down": self.user_input_processor.getKeysHeldDown(self),\
                "mouse_status": self.user_input_processor.getMouseStatus(self)}
    """
    
    #def eventLoop(self, mouse_pos: Optional[Tuple[bool]]=None,\
    #        events: Optional[List[int]]=None,\
    #        keys_pressed: Optional[List[int]]=None,\
    #        mouse_pressed: Optional[Tuple[int]]=None,\
    #        check_axes: Tuple[int]=(0, 1))\
    #        -> Tuple[Union[bool, Tuple[int]]]:
    """
    def _eventLoop(
        self,
        events: List[int],
        keys_down: Set[int],
        mouse_status: Tuple[int],
        check_axes: Tuple[int]=(0, 1),
    ) -> Tuple[bool, bool, bool, list]:
        #print("Using ButtonMenuOverlay method _eventLoop()")
        #((quit, esc_pressed), (events, keys_down, mouse_status, check_axes)) = self.getEventLoopArguments(events=events, keys_down=keys_down, mouse_status=mouse_status, check_axes=check_axes)
        #print(events)
        #running = not quit and not esc_pressed
        #screen_changed = False
        buttons = getattr(self, "buttons", None)

        quit, running, screen_changed, actions = super()._eventLoop(events, keys_down, mouse_status, check_axes)

        if buttons is not None:
            quit2, running2, change, selected_b_inds = buttons.eventLoop(
                events=events,
                keys_down=keys_down,
                mouse_status=mouse_status,
                check_axes=check_axes
            )
            if change: screen_changed = True
            if quit2: quit = True
            if not running2: running = False
            actions.extend([self.button_actions[b_inds[0]][b_inds[1]] for b_inds in selected_b_inds])
        screen_changed = self.drawUpdateRequired()
        return quit, running, screen_changed, actions
        ""
        for slider, inds in self.sliderPlusIterator():
            (quit2, running2, screen_changed2, val_dict) = slider.eventLoop(
                events=events,
                keys_down=keys_down,
                mouse_status=mouse_status,
                check_axes=check_axes,
            )
            if screen_changed2:
                print(f"slider at {inds} changed")
            quit = quit or quit2
            running = running and running2
            screen_changed = screen_changed or screen_changed2
            n_slider += 1
        #print(f"the number of sliders in grid is {n_slider}")
        #print("end of SliderPlusGrid eventLoop()")
        #print(quit, running, screen_changed, None)
        #print(getattr(self, "_display_surf", None))
        return quit, running, screen_changed, None

        #print("using menu eventLoop() method")
        running, quit = True, False
        buttons = getattr(self, "buttons", None)
        screen_changed = False
        
        #print(mouse_status)
        #print(self.mouse_enablement, self.mouse_enabled)
        
        if events is None:
            #print(events)
            quit, esc_pressed, events = self.user_input_processor.getEvents()
            if esc_pressed:
                running = False
        #if events:
        #    print(events)
        #    print(self.exit_press_keys)
        #    print(self.exit_release_keys)
        events2 = []
        for event_tup in events:
            #print((event_tup[1] == 0 and event_tup[0].key in\
            #        self.exit_press_keys))
            if not (event_tup[1] == 0 and event_tup[0].key in\
                    self.exit_press_keys) and not (event_tup[1] == 1\
                    and event_tup[0].key in self.exit_release_keys):
                 events2.append(event_tup)
                 continue
            running = False
            break
        actions = []
        if buttons is not None:
            quit2, running2, (change, selected_b_inds) = buttons.eventLoop(\
                    events=events, keys_down=keys_down,\
                    mouse_status=mouse_status, check_axes=check_axes)
            if change: screen_changed = True
            if quit2: quit = True
            if not running2: running = False
            actions = [self.button_actions[b_inds[0]][b_inds[1]] for b_inds in selected_b_inds]
        #action = None if selected is None else\
        #        self.button_actions[selected[0]][selected[1]]
        return quit, running, (screen_changed, actions)
        ""
    """

class SliderAndButtonMenuOverlay(ButtonMenuOverlay):
    
    reset_graph_edges = {
        "shape": {"slider_plus_grid_shape_actual": True, "slider_plus_grid_anchor_pos_actual": True},
        "slider_plus_grid_max_shape_norm": {"slider_plus_grid_shape_actual": True},
        "slider_plus_grid_wh_ratio_range": {"slider_plus_grid_shape_actual": True},
        "slider_plus_grid_anchor_pos_norm": {"slider_plus_grid_anchor_pos_actual": True},
    }

    custom_attribute_change_propogation_methods = {
        "slider_plus_grid_shape_actual": "customSliderGridShapeActualChangePropogation",
        "slider_plus_grid_anchor_pos_actual": "customSliderGridAnchorPositionActualChangePropogation",
    }

    attribute_calculation_methods = {
        "slider_plus_grid_shape_actual": "calculateSliderGridShapeActual",
        "slider_plus_grid_anchor_pos_actual": "calculateSliderGridAnchorPositionActual",

        "slider_plus_grid_img_constructor": "createSliderGridImageConstructor",
    }

    attribute_default_functions = {
        "slider_plus_grid_uip_idx": ((lambda obj: -1),),
        "slider_plus_grid_max_shape_norm": ((lambda obj: ()),),
        "slider_plus_grid_wh_ratio_range": ((lambda obj: ()),),
        "slider_plus_grid_anchor_pos_norm": ((lambda obj: ()),),
        "slider_plus_grid": ((lambda obj: None),),
    }

    dynamic_displ_attrs = ButtonMenuOverlay.dynamic_displ_attrs + ["slider_plus_grid"]

    def __init__(
        self,
        shape: Tuple[Real],
        framerate: Real,
        overlay_color: Optional[Tuple[Union[Tuple[int], Real]]]=None,
        mouse_enabled: bool=True,
        navkeys_enabled: bool=True,
        navkeys: Optional[Tuple[Tuple[Set[int]]]]=None,
        navkey_cycle_delay_s: Optional[Tuple[Real]]=None,
        enter_keys: Optional[Set[int]]=None,
        #exit_press_keys: Optional[Set[int]]=None,
        #exit_release_keys: Optional[Set[int]]=None,
        **kwargs,
    ):
        """
        super().__init__(
            shape=shape,
            framerate=framerate,
            overlay_color=overlay_color,
            mouse_enabled=mouse_enabled,
            navkeys=navkeys,
            navkey_cycle_delay_s=navkey_cycle_delay_s,
            enter_keys=enter_keys,
            #exit_press_keys=exit_press_keys,
            #exit_release_keys=exit_release_keys,
        )

        self.sliders_uip_idx = None
        """
        #print(f"__init__() navkey_cycle_delay_s = {navkey_cycle_delay_s}")
        #print(kwargs)
        checkHiddenKwargs(type(self), kwargs)

        kwargs2 = self.initArgsManagement(locals(), kwargs=kwargs)
        super().__init__(**kwargs2)
    
    def customSliderGridShapeActualChangePropogation(
        self,
        new_val: Optional[Tuple[int, int]],
        prev_val: Optional[Tuple[int, int]],
    ) -> None:
        slider_plus_grid = self.slider_plus_grid
        if slider_plus_grid is None: return
        slider_plus_grid.shape = new_val
        return
    
    def customSliderGridAnchorPositionActualChangePropogation(
        self,
        new_val: Optional[Tuple[int, int]],
        prev_val: Optional[Tuple[int, int]],
    ) -> None:
        slider_plus_grid = self.slider_plus_grid
        if slider_plus_grid is None: return
        slider_plus_grid.anchor_rel_pos = new_val
        return

    def calculateSliderGridShapeActual(self) -> Tuple[int, int]:
        max_shape_norm = self.slider_plus_grid_max_shape_norm
        wh_ratio_rng = self.slider_plus_grid_wh_ratio_range

        return self.calculateMaxShapeActualGivenWidthHeightRatioRange(
            max_shape_norm,
            self.shape,
            wh_ratio_rng,
        )
        """
        if not max_shape_norm or not wh_rng: return ()
        parent_shape = self.shape
        shape_actual = [x * y for x, y in zip(parent_shape, max_shape_norm)]
        
        wh_ratio = shape_actual[0] / shape_actual[1]
        if wh_ratio < wh_rng[0]:
            shape_actual[1] *= wh_ratio / wh_rng[0]
        elif wh_ratio > shape_actual[1]:
            shape_actual[0] *= wh_rng[1] / wh_ratio
        return tuple(shape_actual)
        """
    
    def calculateSliderGridAnchorPositionActual(self) -> Tuple[int, int]:
        anchor_pos_norm = self.slider_plus_grid_anchor_pos_norm
        if not anchor_pos_norm: return ()
        parent_shape = self.shape
        anchor_pos_actual = tuple(x * y for x, y in zip(parent_shape, anchor_pos_norm))
        #print(f"slider grid anchor position actual = {anchor_pos_actual}")
        return anchor_pos_actual
    
    def createSliderGridImageConstructor(self) -> Callable[["SliderAndButtonMenuOverlay", "pg.Surface"], None]:
        def constructor(obj: SliderAndButtonMenuOverlay, surf: "pg.Surface") -> None:
            slider_plus_grid = obj.slider_plus_grid
            if not slider_plus_grid: return
            return slider_plus_grid.draw(surf)
        return constructor
    
    def setupSliderPlusGrid(
        self,
        anchor_pos_norm: Tuple[Real],
        anchor_type: str,
        slider_plus_grid_max_shape_norm: Tuple[Real],
        slider_plus_parameters: List[List[Dict]],
        slider_plus_gaps_rel_shape: Optional[Tuple[Real, Real]]=None,
        wh_ratio_range: Optional[Tuple[Real]]=None,
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
    ) -> None:

        # slider_plus_parameters dictionary options:
        #    title: str,
        #    val_range: Tuple[Real],
        #    increment_start: Real,
        #    increment: Optional[Real]=None,
        #    init_val: Optional[Real]=None,
        #    demarc_numbers_dp: Optional[int]=None,
        #    demarc_intervals: Optional[Tuple[Real]]=None,
        #    demarc_start_val: Optional[Real]=None,
        #    val_text_dp: Optional[int]=None,
        #    name: Optional[str]=None,
        
        grid_dims = (len(slider_plus_parameters[0]), len(slider_plus_parameters))
        if wh_ratio_range is None:
            wh_ratio_range = (0, float("inf"))
        self.setAttributes({
            "slider_plus_grid_max_shape_norm": slider_plus_grid_max_shape_norm,
            "slider_plus_grid_anchor_pos_norm": anchor_pos_norm,
            "slider_plus_grid_wh_ratio_range": wh_ratio_range,
        })
        """
        kwargs = {
            grid_dims=grid_dims,
            shape=self.slider_plus_grid_shape_actual,
            slider_plus_gaps_rel_shape=slider_plus_gaps_rel_shape,
            anchor_rel_pos=self.slider_plus_grid_anchor_pos_actual,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=self.screen_topleft_to_parent_topleft_offset,
            demarc_numbers_text_group=demarc_numbers_text_group,
            thumb_radius_rel=thumb_radius_rel,
            demarc_line_lens_rel=demarc_line_lens_rel,
            demarc_numbers_max_height_rel=demarc_numbers_max_height_rel,
            track_color=track_color,
            thumb_color=thumb_color,
            demarc_numbers_color=demarc_numbers_color,
            demarc_line_colors=demarc_line_colors,
            thumb_outline_color=thumb_outline_color,
            slider_shape_rel=slider_shape_rel,
            slider_borders_rel=slider_borders_rel,
            title_text_group=title_text_group,
            title_anchor_type=title_anchor_type,
            title_color=title_color,
            val_text_group=val_text_group,
            val_text_anchor_type=val_text_anchor_type,
            val_text_color=val_text_color,
            mouse_enabled=self.mouse_enabled,
        }
        attr_corresp_dict = {

        }
        if self.buttons[grid_inds[0]][grid_inds[1]] is None:
            container_attr_resets = {"changed_since_last_draw": {"display_surf": (lambda container_obj, obj: obj.drawUpdateRequired())}}
            self.buttons[grid_inds[0]][grid_inds[1]] = self.createSubComponent(
                component_class=ButtonGroupElement,
                attr_correspondence_dict={},
                creation_kwargs=attr_dict,
                container_attribute_resets=container_attr_resets,
                custom_creation_function=self.button_group.addButton
            )
        """

        slider_plus_grid = SliderPlusGrid(
            grid_dims=grid_dims,
            shape=self.slider_plus_grid_shape_actual,
            slider_plus_gaps_rel_shape=slider_plus_gaps_rel_shape,
            anchor_rel_pos=self.slider_plus_grid_anchor_pos_actual,
            anchor_type=anchor_type,
            screen_topleft_to_parent_topleft_offset=self.screen_topleft_to_parent_topleft_offset,
            demarc_numbers_text_group=demarc_numbers_text_group,
            thumb_radius_rel=thumb_radius_rel,
            demarc_line_lens_rel=demarc_line_lens_rel,
            demarc_numbers_max_height_rel=demarc_numbers_max_height_rel,
            track_color=track_color,
            thumb_color=thumb_color,
            demarc_numbers_color=demarc_numbers_color,
            demarc_line_colors=demarc_line_colors,
            thumb_outline_color=thumb_outline_color,
            slider_shape_rel=slider_shape_rel,
            slider_borders_rel=slider_borders_rel,
            title_text_group=title_text_group,
            title_anchor_type=title_anchor_type,
            title_color=title_color,
            val_text_group=val_text_group,
            val_text_anchor_type=val_text_anchor_type,
            val_text_color=val_text_color,
            mouse_enabled=self.mouse_enabled,
            _from_container=True,
            _container_obj=self,
            _container_attr_reset_dict={"changed_since_last_draw": {"display_surf": (lambda container_obj, obj: obj.drawUpdateRequired())}},
        )
        
        for i2, row in enumerate(slider_plus_parameters):
            for i1, params_dict in enumerate(row):
                slider_plus_grid.setupSliderPlusGridElement(
                    grid_inds=(i1, i2),
                    **params_dict,
                )
        
        self.slider_plus_grid = slider_plus_grid
        if self.slider_plus_grid_uip_idx != -1:
            self.user_input_processor.removeSubUIP(self.slider_plus_grid_uip_idx)
        #print("adding button grid uip")
        self.slider_plus_grid_uip_idx = self.user_input_processor.addSubUIP(slider_plus_grid.user_input_processor, obj_func=(lambda obj: obj.slider_plus_grid))
        return
    
    def _eventLoop(
        self,
        events: List[int],
        keys_down: Set[int],
        mouse_status: Tuple[int],
        check_axes: Tuple[int]=(0, 1),
    ) -> Tuple[bool, bool, bool, list]:
        
        quit, running, screen_changed, actions = super()._eventLoop(events, keys_down, mouse_status, check_axes)
        #print(f"mouse_status = {mouse_status}")

        slider_plus_grid = getattr(self, "slider_plus_grid", None)
        if slider_plus_grid is not None:
            quit2, running2, change, selected_b_inds = slider_plus_grid.eventLoop(
                events=events,
                keys_down=keys_down,
                mouse_status=mouse_status,
                check_axes=check_axes
            )
            if change: screen_changed = True
            if quit2: quit = True
            if not running2: running = False
            #actions.extend([self.button_actions[b_inds[0]][b_inds[1]] for b_inds in selected_b_inds])
        screen_changed = self.drawUpdateRequired()
        #if screen_changed: print(f"slider and button menu overlay redraw required")
        #print("Finishing SliderAndButtonMenuOverlay method _eventLoop()")
        #print(f"button menu overlay display surface = {self.__dict__.get('_display_surf', None)}, {'display_surf' in self.getPendingAttributeChanges()}")#{self.__dict__.get('_display_surf', None)}")
        return quit, running, screen_changed, actions
    
    """
    @property
    def sliders_spatial_props_rel(self):
        return getattr(self, "_sliders_spatial_props_rel", None)
    
    @sliders_spatial_props_rel.setter
    def sliders_spatial_props_rel(self, sliders_spatial_props_rel):
        prev = getattr(self, "_sliders_spatial_props_rel", None)
        if sliders_spatial_props_rel == prev:
            return
        self._resetSliderssSpatialProperties()
        return
    
    
    def findSlidersSpatialProperties(self) -> Tuple[Any]:
        bsp_rel = self.buttons_spatial_props_rel
        if bsp_rel is None:
            return ()
        (anchor_screen_pos_norm, anchor_type, overall_shape_rel,\
                wh_ratio_range) = bsp_rel
        
        screen_shape = self.shape
        anchor_screen_pos = tuple(x * y for x, y in zip(screen_shape, anchor_screen_pos_norm))
        
        overall_shape = [x * y for x, y in zip(screen_shape, overall_shape_rel)]
        #print(overall_shape)
        wh_ratio = overall_shape[0] / overall_shape[1]
        if wh_ratio < wh_ratio_range[0]:
            overall_shape[1] *= wh_ratio / wh_ratio_range[0]
        elif wh_ratio > wh_ratio_range[1]:
            overall_shape[0] *= wh_ratio_range[1] / wh_ratio
        
        overall_shape = tuple(overall_shape)
        topleft = topLeftFromAnchorPosition(overall_shape, anchor_type, anchor_screen_pos)
        
        return (topleft, overall_shape)
    
    def _resetSlidersSpatialProperties(self) -> None:
        if not self.buttons: return
        #bsp_rel = self.buttons_spatial_props_rel
        ssp = self.findSlidersSpatialProperties()
        if not ssp: return
        topleft, overall_shape = ssp
        self.buttons.dims = (*topleft, *overall_shape)
        return
    
    def setSliders(
        self,
        slider_elements: List[List[Any]],
        anchor_screen_pos_norm: Tuple[Real],
        anchor_type: str,
        overall_shape_rel: Tuple[Real],
        wh_ratio_range: Tuple[Real],
        slider_gaps_rel_shape: Optional[Tuple[Real, Real]]=None,
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
        slider_shape_rel: Optional[Tuple[Real]]=None,
        slider_borders_rel: Optional[Tuple[Real]]=None,
        title_text_group: Optional["TextGroup"]=None,
        title_anchor_type: Optional[str]=None,
        title_color: Optional[ColorOpacity]=None,
        val_text_group: Optional["TextGroup"]=None,
        val_text_anchor_type: Optional[str]=None,
        val_text_color: Optional[ColorOpacity]=None,
    ) -> None:
        
        self._sliders_spatial_props_rel = (anchor_screen_pos_norm, anchor_type,\
                overall_shape_rel, wh_ratio_range)
        
        (topleft, overall_shape) = self.findSlidersSpatialProperties()
        ""
        button_text, button_actions = [], []
        for row in button_text_and_actions:
            button_text.append([])
            button_actions.append([])
            for text, action in row:
                button_text[-1].append(text)
                button_actions[-1].append(action)
        ""
        n_rows = len(slider_elements)
        if not n_rows: return
        n_cols = len(slider_elements[0])
        for row in slider_elements[1:]:
            if len(row) != n_cols:
                raise ValueError("In slider_elements, the length of each list must "
                        "be the same.")
        grid_dims = (n_cols, n_rows)

        slider_plus_grid = SliderPlusGrid(
            grid_dims,
            overall_shape,
            slider_gaps_rel_shape=slider_gaps_rel_shape,
            anchor_rel_pos=topleft,
            anchor_type="topleft",
            screen_topleft_to_parent_topleft_offset=self.screen_topleft_to_parent_topleft_offset,
            demarc_numbers_text_group=demarc_numbers_text_group,
            thumb_radius_rel=thumb_radius_rel,
            demarc_line_lens_rel=demarc_line_lens_rel,
            demarc_numbers_max_height_rel=demarc_numbers_max_height_rel,
            track_color=track_color,
            thumb_color=thumb_color,
            demarc_numbers_color=demarc_numbers_color,
            demarc_line_colors=demarc_line_colors,
            thumb_outline_color=thumb_outline_color,
            slider_shape_rel=slider_shape_rel,
            slider_borders_rel=slider_borders_rel,
            title_text_group=title_text_group,
            title_anchor_type=title_anchor_type,
            title_color=title_color,
            val_text_group=val_text_group,
            val_text_anchor_type=val_text_anchor_type,
            val_text_color=val_text_color,
            mouse_enabled=self.mouse_enabled,
        )
        
        if self.sliders_uip_idx is not None:
            self.user_input_processor.removeSubUIP(self.sliders_uip_idx)
        self.sliders_uip_idx = self.user_input_processor.addSubUIP(slider_plus_grid.user_input_processor)

        for idx2, slider_row in enumerate(slider_elements):
            for idx1, slider_dict in enumerate(slider_row):
                if slider_dict is None: continue
                slider_plus_grid.setupSliderPlusGridElement(
                    (idx1, idx2),
                    **slider_dict,
                )

        self.sliders = slider_plus_grid
        return
    
    def _eventLoop(
        self,
        events: List[int],
        keys_down: Set[int],
        mouse_status: Tuple[int],
        check_axes: Tuple[int]=(0, 1),
    ) -> Tuple[bool, bool, bool, list]:

        sliders = getattr(self, "sliders", None)

        quit, running, screen_changed, actions = super()._eventLoop(events, keys_down, mouse_status, check_axes)

        if sliders is not None:
            quit2, running2, change, _ = sliders.eventLoop(
                events=events,
                keys_down=keys_down,
                mouse_status=mouse_status,
                check_axes=check_axes
            )
            #if change: screen_changed = True
            if quit2: quit = True
            if not running2: running = False
        screen_changed = self.drawUpdateRequired()
        return quit, running, screen_changed, actions
    """