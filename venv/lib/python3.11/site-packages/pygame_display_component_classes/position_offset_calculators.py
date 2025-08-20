#! /usr/bin/env python

from typing import Union, Tuple, List, Optional, Set

from pygame_display_component_classes.utils import Real

# from position_offset_calculators import topLeftAnchorOffset, topLeftFromAnchorPosition, topLeftGivenOffset

def topLeftAnchorOffset(shape: Tuple[Real], anchor: str)\
        -> Tuple[Real]:
    """
    The vector from the anchor point topleft of a rectangle
    with shape equal to shape2 to the anchor point anchor
    of the same rectangle.
    """
    res = [0.5, 0.5]
    if anchor.endswith("left"):
        res[0] = 0
    elif anchor.endswith("right"):
        res[0] = 1
    res[0] *= shape[0]
    if anchor.startswith("top") or anchor == "midtop":
        res[1] = 0
    elif anchor.startswith("bottom") or anchor == "midbottom":
        res[1] = 1
    res[1] *= shape[1]
    return tuple(res)

def topLeftFromAnchorPosition(shape: Tuple[Real], anchor: str,\
        anchor_pos: Tuple[Real]) -> Tuple[Real]:
    """
    Finds the position of the anchor point topleft of a rectangle
    of a given shape given the position of the anchor point
    anchor_pos
    """
    offset = topLeftAnchorOffset(shape, anchor)
    return tuple(x - y for x, y in zip(anchor_pos, offset))
    

def topLeftGivenOffset(rect1, shape2, offset, anchor1="center",\
        anchor2="center"):
    """
    Finding the position of the upper left corner a rectangle with
    shape equal to shape2 should take in order for a given anchor
    point (anchor2) of that rectangle to have a given
    offset to a given anchor point (anchor1) of rect1 (where the
    offset is scaled by a factor scale).
    """
    rect2_offset = topLeftAnchorOffset(shape2, anchor2)
    return tuple(x - y + z for x, y, z in\
            zip(getattr(rect1, anchor1), rect2_offset, offset))
