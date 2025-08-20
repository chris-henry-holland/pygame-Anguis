#!/usr/bin/env python

import functools
import heapq

from typing import Union, Dict, Tuple, List, Optional, Set, Callable, Any

import pygame as pg
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYUP,
    KEYDOWN,
    QUIT,
    K_RETURN,
    K_KP_ENTER,
)

# from user_input_processing import checkEvents, checkKeysPressed, getMouseStatus, createNavkeyDict

def createNavkeyDict(navkeys: Tuple[Tuple[Set[int]]]) -> Dict[int, Tuple[int]]:
    res = {}
    for i1, navkey_sets in enumerate(navkeys):
        for i2, navkey_set in enumerate(navkey_sets):
            for navkey in navkey_set:
                res[navkey] = (i1, i2)
    return res

class UserInputProcessor:
    
    def __init__(self, keys_down_func: Union[Callable[[Any], Set[int]], bool]=True,
            key_press_event_filter: Union[Callable, bool]=True,
            key_release_event_filter: Union[Callable, bool]=True,
            mouse_press_event_filter: Union[Callable, bool]=True,
            mouse_release_event_filter: Union[Callable, bool]=True,
            other_event_filter: Union[Callable, bool]=True,
            get_mouse_status_func: Union[Callable, bool]=False):
        
        #print("initialising UserInputProcessor")
        """
        self.keys_down0 = () if keys_down is None else keys_down
        self.key_press_event_filter0 = (lambda event: True)\
                if key_press_event_filter is None else\
                key_press_event_filter
        self.key_release_event_filter0 = (lambda event: True)\
                if key_release_event_filter is None else\
                key_release_event_filter
        self.mouse_press_event_filter0 = (lambda event: True)\
                if mouse_press_event_filter is None else\
                mouse_press_event_filter
        self.mouse_release_event_filter0 = (lambda event: True)\
                if mouse_release_event_filter is None else\
                mouse_release_event_filter
        self.other_event_filter0 = (lambda event: True)\
                if other_event_filter is None else\
                other_event_filter
        self.get_mouse_status0 = get_mouse_status
        """
        self.keys_down_func0 = keys_down_func
        #print(f"keys_down_func0: {keys_down_func}")
        self.key_press_event_filter0 = key_press_event_filter
        self.key_release_event_filter0 = key_release_event_filter
        self.mouse_press_event_filter0 = mouse_press_event_filter
        self.mouse_release_event_filter0 = mouse_release_event_filter
        self.other_event_filter0 = other_event_filter
        self.get_mouse_status_func0 = get_mouse_status_func
        
        #print(self.keys_down_func0)
        #print(self.keys_down_func)
        #print(self.mouse_press_event_filter0)
        #print(self.mouse_press_event_filter)
        
        # Consider splitting into uips from ancestors of the calling object's
        # class and uips from components of the calling object's class
        # In fact, consider creating a descendent class of UserInputProcessor
        # that is associated with a InteractiveDisplayComponentBase object
        self.sub_uips = []
        
        
        self.sub_uips_free_inds = []
    
    @staticmethod
    def mergeSetFunctions(set_func1: Union[Callable[[Any], Set[int]], bool], set_func2: Union[Callable[[Any], Set[int]], bool]) -> Union[Callable[[Any], Set[int]], bool]:
        if set_func1 is True or set_func2 is True:
            return True
        elif set_func1 is False:
            return set_func2
        elif set_func2 is False:
            return set_func1
        return lambda obj: set_func1(obj).union(set_func2(obj))
    
    def findKeysDownFunction(self, attr_name: str) -> Union[Set[int], bool]:
        #print("calling findKeysDownFunction")
        attr_name0 = f"{attr_name}0"
        #print(attr_name0, hasattr(self, attr_name0))
        res = getattr(self, attr_name0)
        #print(res)
        if res is True:
            return True
        for uip in getattr(self, "sub_uips", []):
            #print("hello")
            if uip is None: continue
            res = self.mergeSetFunctions(res, getattr(uip, attr_name))
            if res is True:
                return res
        #print(res)
        return res
    
    @property
    def keys_down_func(self):
        res = getattr(self, "_keys_down_func", None)
        if res is None:
            res = self.findKeysDownFunction("keys_down_func")
            self._keys_down_func = res
        return res
    
    @property
    def keys_down_func_actual(self):
        func = self.keys_down_func
        #print(f"keys_down_func = {func}")
        return (lambda obj: func) if isinstance(func, bool) else func
    
    @staticmethod
    def mergeFilters(filter1: Union[Callable, bool], filter2: Union[Callable, bool]) -> Union[Callable, bool]:
        if filter1 is True or filter2 is True:
            return True
        elif filter1 is False:
            return filter2
        elif filter2 is False:
            return filter1
        return (lambda obj, event: filter1(obj, event) or filter2(obj, event))
    
    def findFilter(self, attr_name: str) -> Union[Callable, bool]:
        attr_name0 = f"{attr_name}0"
        res = getattr(self, attr_name0)
        if res is True:
            return res
        for uip in getattr(self, "sub_uips", []):
            if uip is None: continue
            res = self.mergeFilters(res, getattr(uip, attr_name))
            if res is True:
                return res
        return res
    
    @property
    def key_press_event_filter(self):
        res = getattr(self, "_key_press_event_filter", None)
        if res is None:
            res = self.findFilter("key_press_event_filter")
            self._key_press_event_filter = res
        return res
    
    @property
    def key_press_event_filter_actual(self):
        func = self.key_press_event_filter
        return (lambda obj, event: func) if isinstance(func, bool) else func
    
    @property
    def key_release_event_filter(self):
        res = getattr(self, "_key_release_event_filter", None)
        if res is None:
            res = self.findFilter("key_release_event_filter")
            self._key_release_event_filter = res
        return res
    
    @property
    def key_release_event_filter_actual(self):
        func = self.key_release_event_filter
        return (lambda obj, event: func) if isinstance(func, bool) else func
    
    @property
    def mouse_press_event_filter(self):
        res = getattr(self, "_mouse_press_event_filter", None)
        if res is None:
            res = self.findFilter("mouse_press_event_filter")
            self._mouse_press_event_filter = res
        #print("mouse press event filter")
        return res
    
    @property
    def mouse_press_event_filter_actual(self):
        func = self.mouse_press_event_filter
        return (lambda obj, event: func) if isinstance(func, bool) else func
    
    @property
    def mouse_release_event_filter(self):
        res = getattr(self, "_mouse_release_event_filter", None)
        if res is None:
            res = self.findFilter("mouse_release_event_filter")
            self._mouse_release_event_filter = res
        return res
    
    @property
    def mouse_release_event_filter_actual(self):
        func = self.mouse_release_event_filter
        return (lambda obj, event: func) if isinstance(func, bool) else func
    
    @property
    def other_event_filter(self):
        res = getattr(self, "_other_event_filter", None)
        if res is None:
            res = self.findFilter("other_event_filter")
            self._other_event_filter = res
        return res
    
    @property
    def other_event_filter_actual(self):
        func = self.other_event_filter
        return (lambda obj, event: func) if isinstance(func, bool) else func
    
    @staticmethod
    def mergeBooleanFunctions(bool_func1: Union[Callable[[Any], bool], bool], bool_func2: Union[Callable[[Any], bool], bool]) -> Union[Callable[[Any], bool], bool]:
        if bool_func1 is True or bool_func2 is True:
            return True
        elif not bool_func1:
            return bool_func2
        elif not bool_func2:
            return bool_func1
        return (lambda obj: bool_func1(obj) or bool_func2(obj))
    
    def findBooleanFunction(self, attr_name: str) -> bool:
        attr_name0 = f"{attr_name}0"
        res = getattr(self, attr_name0)
        if res is True:
            return True
        for uip in getattr(self, "sub_uips", []):
            #if attr_name == "get_mouse_status_func":
            #    print("found sub uip for mouse status")
            #    print(uip)
            if uip is None: continue
            res = self.mergeBooleanFunctions(res, getattr(uip, attr_name))
            if res is True:
                return res
        return res
    
    @property
    def get_mouse_status_func(self):
        res = getattr(self, "_get_mouse_status_func", None)
        if res is None:
            res = self.findBooleanFunction("get_mouse_status_func")
            self._get_mouse_status_func = res
        return res
    
    @property
    def get_mouse_status_func_actual(self):
        func = self.get_mouse_status_func
        #print(f"get_mouse_status_func = {func}")
        return (lambda obj: func) if isinstance(func, bool) else func
    
    def addSubUIP(self, sub_uip: "UserInputProcessor", obj_func: Optional[Callable[[Any], Any]]=None) -> int:
        #print("calling addSubUIP()")
        #print(f"mouse press event filter = {self.mouse_press_event_filter}")
        #print(f"key press event filter = {self.key_press_event_filter}")
        if self.sub_uips_free_inds:
            idx = heapq.heappop(self.sub_uips_free_inds)
            self.sub_uips[idx] = sub_uip
        else:
            idx = len(self.sub_uips)
            self.sub_uips.append(sub_uip)
        keys_down_prev = getattr(self, "_keys_down_func", False)
        add_func = sub_uip.keys_down_func
        keys_down_add = add_func if obj_func is None else (lambda obj: add_func(obj_func(obj)))
            
        self._keys_down_func = self.mergeSetFunctions(keys_down_prev, keys_down_add)
        
        def otherObjectFilter(attr: str, sub_uip: "UserInputProcessor", obj_func: Optional[Callable[[Any], Any]]) -> Union[Callable[[Any, int], bool]]:
            fltr_orig = getattr(sub_uip, attr, False)
            if isinstance(fltr_orig, bool) or obj_func is None:
                return fltr_orig
            func = lambda obj_func, fltr_orig, obj, event: fltr_orig(obj_func(obj), event)
            return functools.partial(func, obj_func, fltr_orig)
        
        for attr in ("key_press_event_filter",\
                "key_release_event_filter",\
                "mouse_press_event_filter",\
                "mouse_release_event_filter",\
                "other_event_filter"):
            sub_attr = f"_{attr}"
            fltr1 = getattr(self, attr)
            fltr2 = otherObjectFilter(attr, sub_uip, obj_func)
            setattr(self, sub_attr, self.mergeFilters(fltr1, fltr2))
            
        #get_mouse_status_prev =\
        #        getattr(self, "_get_mouse_status", None)
        #if get_mouse_status_prev is False and\
        #        uip.get_mouse_status is True:
        #    self._get_mouse_status = True
        get_mouse_status_prev = getattr(self, "_get_mouse_status_func", False)
        bool_func1 = get_mouse_status_prev
        bool_func2 = getattr(sub_uip, "get_mouse_status_func", False)
        #print(f"bool_func2 = {bool_func2}")
        #print(hasattr(sub_uip, "_get_mouse_status_func")
        if not isinstance(bool_func2, bool) and obj_func is not None:
            #print("hello")
            bool_func2 = functools.partial(lambda bf, of, obj: bf(of(obj)), bool_func2, obj_func)
        self._get_mouse_status_func = self.mergeBooleanFunctions(bool_func1, bool_func2)
        #print(bool_func1, bool_func2, self._get_mouse_status_func)
        #print(f"mouse press event filter = {self.mouse_press_event_filter}")
        #print(f"key press event filter = {self.key_press_event_filter}")
        #print(f"get_mouse_status_func = {self.get_mouse_status_func}")
        return idx
    
    def removeSubUIP(self, idx: int) -> None:
        uip = self.sub_uips
        if idx == len(self.sub_uips) - 1:
            self.sub_uips.pop()
        else:
            heapq.heappush(self.sub_uips_free_inds, idx)
            self.sub_uips[idx] = None
        if uip.keys_down_func is not False:
            self._keys_down_func = None
        for attr in ("key_press_event_filter",\
                "key_release_event_filter",\
                "mouse_press_event_filter",\
                "mouse_release_event_filter",\
                "other_event_filter"):
            if getattr(uip, attr) is not False:
                setattr(self, f"_{attr}", None)
        if uip.get_mouse_status is not False:
            self._get_mouse_status = None
        return
    
    def getEvents(self, obj: Any) -> Tuple[Union[bool, List[Tuple[int]]]]:
        quit = False
        esc_pressed = False
        events = []
        all_events = pg.event.get()
        #if all_events:
        #    print(all_events)
        #print(all_events)
        #if all_events: print(all_events)
        #print(f"mouse release filter: {self.mouse_release_event_filter_actual}")
        for event in all_events:
            if event.type == KEYDOWN:
                #print(event, self.key_press_event_filter_actual(obj, event))
                #print("hi")
                if event.key == K_ESCAPE:
                    esc_pressed = True
                if self.key_press_event_filter_actual(obj, event):
                    #print("passed filter")
                    events.append((event, 0))
                #else:
                #    print("did not pass filter")
            elif event.type == KEYUP:
                if self.key_release_event_filter_actual(obj, event):
                    events.append((event, 1))
            elif event.type == pg.MOUSEBUTTONDOWN:
                if self.mouse_press_event_filter_actual(obj, event):
                    events.append((event, 2))
            elif event.type == pg.MOUSEBUTTONUP:
                if self.mouse_release_event_filter_actual(obj, event):
                    events.append((event, 3))
            elif self.other_event_filter_actual(obj, event):
                events.append((event, 4))
                #print(event)
            if event.type == QUIT:
                quit = True
        return (quit, esc_pressed, events)
    
    def getKeysHeldDown(self, obj: Any) -> Set[int]:
        #print("Using getKeysHeldDown()")
        #print(self.keys_down_func_actual)
        #print(self.keys_down_func)
        keys_down_set = self.keys_down_func_actual(obj)
        #print(keys_down_set)
        if keys_down_set is False: return set()
        kp = pg.key.get_pressed()
        if keys_down_set is True: keys_down_set = range(len(kp))
        return {x for x in keys_down_set if kp[x]}
        #keys_to_check = range(len(kp)) if self.keys_down == ()\
        #        else self.keys_down
        #return {x for x in keys_to_check if kp[x]}
    
    def getMouseStatus(self, obj: Any) -> Tuple[Tuple[int]]:
        #print("Using getMouseStatus()")
        gms = self.get_mouse_status_func_actual(obj)
        #print(gms)
        return (pg.mouse.get_pos(), pg.mouse.get_pressed())\
                if gms and pg.mouse.get_focused()\
                else ()
    
    def getUserInputs(self):
        return (*self.getEvents(), self.getKeysHeldDown(),\
                self.getMouseStatus())

class UserInputProcessorMinimal(UserInputProcessor):
    def __init__(self):
        super().__init__(keys_down_func=False,
            key_press_event_filter=False,
            key_release_event_filter=False,
            mouse_press_event_filter=False,
            mouse_release_event_filter=False,
            other_event_filter=False,
            get_mouse_status_func=False)

def checkEvents(extra_events: Optional[Set]=None,\
        new_keys_to_check: Optional[Set]=None)\
        -> Tuple[Union[bool, List[int]]]:
    if extra_events is None:
        extra_events = set()
    if new_keys_to_check is None:
        new_keys_to_check = set()
    events = []
    
    running = True
    quit = False
    for event in pg.event.get():
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            if event.key in new_keys_to_check:
                events.append((event.key, 0))
        elif event.type == QUIT:
            quit = True
            running = False
        elif event.type in extra_events:
            events.append((event, 1))
            #print(event)
    return (quit, running, events)
    
def checkKeysPressed(keys_to_check: Optional[Set[int]]=None) -> Set[int]:
    keys_pressed = pg.key.get_pressed()
    if keys_to_check is None:
        keys_to_check = range(len(keys_pressed))
    return {x for x in keys_to_check if keys_pressed[x]}

def getMouseStatus() -> Tuple[Tuple[int]]:
    return (pg.mouse.get_pos(), pg.mouse.get_pressed())
