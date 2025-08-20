#! /usr/bin/env python

import pygame as pg
import pygame.freetype
#from pygame.locals import *
from pygame.locals import (
    RLEACCEL,
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

enter_keys_def_glob = {K_RETURN, K_KP_ENTER}
navkeys_def_glob = (({K_LEFT}, {K_RIGHT}), ({K_UP}, {K_DOWN}))

mouse_lclicks = ({pg.MOUSEBUTTONDOWN}, {pg.MOUSEBUTTONUP})

# Codes names from https://htmlcolorcodes.com/
named_colors_def = {
    "white": (255, 255, 255),
    "silver": (192, 192, 192),
    "gray": (128, 128, 128),
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "maroon": (128, 0, 0),
    "yellow": (255, 255, 0),
    "olive": (128, 128, 0),
    "lime": (0, 255, 0),
    "green": (0, 128, 0),
    "aqua": (0, 255, 255),
    "teal": (0, 128, 128),
    "blue": (0, 0, 255),
    "navy": (0, 0, 128),
    "fuchsia": (255, 0, 255),
    "purple": (128, 0, 128),
}

"""
named_colors_def = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "light_grey": (150, 150, 150),
    "dark_grey": (100, 100, 100),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
}
"""

lower_char = "v"

font_def_func = lambda: pg.freetype.SysFont("unjamonovel", 30)

#from config import enter_keys, navkeys_def_glob, mouse_lclicks, named_colors_def, lower_char, font_def_func
