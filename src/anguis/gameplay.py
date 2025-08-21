# library/src/anguis/gameplay.py

from __future__ import annotations

from typing import Union, Tuple, List, Set, Dict, Optional, Callable, Any, Generator, TYPE_CHECKING

from collections import deque

from sortedcontainers import SortedSet, SortedDict

import pygame as pg

from anguis.utils import randomKTupleGenerator, findKthMissing

#sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
#sys.path.append(os.path.abspath('../'))
from pygame_display_component_classes import (
    createNavkeyDict,
    Real,
    enter_keys_def_glob,
    navkeys_def_glob,
    named_colors_def,
    font_def_func,
    MenuOverlayBase,
    ButtonMenuOverlay,
    Text,
    TextGroup,
    UserInputProcessor
)

from anguis.bots import TailChaserBot

class NoSpaceToCreateError(Exception):
    """
    Raised when trying to create an object with a spatial location
    but unable due to all possible spatial locations being occupied
    """
    pass


class SquareSprite(pg.sprite.Sprite):
    def __init__(self, screen, arena_shape: Tuple[int], pos_flat: int, color: Tuple[Union[Tuple[int]], Real], size: int, screen_pos_func: Callable[[Tuple[Real]], Tuple[int]]):
        super().__init__()
        self._screen = screen
        self.size = size
        self.color = color
        self.pos_flat = pos_flat
        self.screen_pos_func = screen_pos_func
    
    @property
    def screen(self):
        return self._screen
    
    @property
    def size(self):
        return self._size
    
    @size.setter
    def size(self, size):
        if size == getattr(self, "_size", None):
            return
        self._size = size
        self._surf = None
        return
    
    @property
    def shape(self):
        size = self.size
        return (size, size)
    
    @property
    def surf(self):
        res = getattr(self, "_surf", None)
        if res is None:
            res = self._createSurface(self.color)
            self._surf = res
        return res
    
    def _createSurface(self, color):
        res = pg.Surface(self.shape)
        self._setSurfaceColor(res, color)
        return res
    
    @staticmethod
    def _setSurfaceColor(surf, color: Tuple[Union[Tuple[int], Real]]) -> None:
        if surf is None:
            return
        surf.set_alpha(color[1] * 255)
        surf.fill(color[0])
        return
    
    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, color):
        if color == getattr(self, "_color", None):
            return
        self._color = color
        if getattr(self, "_surf", None) is not None:
            self._setSurfaceColor(self.surf, color)
        return
    
    @property
    def pos_flat(self):
        return self._pos_flat
    
    @pos_flat.setter
    def pos_flat(self, pos_flat):
        if pos_flat == getattr(self, "_pos_flat", None):
            return
        self._pos_flat = pos_flat
        self._obj_topleft_screen = None
        self._rect = None
    
    @property
    def obj_topleft_screen(self):
        res = getattr(self, "_obj_topleft_screen", None)
        if res is None:
            res = self.screen_pos_func(self.pos_flat)
            self._obj_topleft_screen = res
        return res
    
    @property
    def rect(self):
        res = getattr(self, "_rect", None)
        if res is None:
            res = self.surf.get_rect(topleft=self.obj_topleft_screen)
            self._rect = res
        return res
    
    def draw(self) -> None:
        #print("hi")
        self.rect
        #print(self.screen)
        #print(self.surf)
        self.screen.blit(self.surf, self.obj_topleft_screen)
        return

# Defining the head of the snake (effectively the player)
class HeadSprite(SquareSprite):
    
    def __init__(self, gameplay, pos_flat: int, mv: Tuple[int]=(0, 1)):
        super().__init__(gameplay.screen, gameplay.arena_shape, pos_flat,\
                color=gameplay.head_color, size=gameplay.head_size,\
                screen_pos_func=gameplay.screen_pos_func)
        self.gameplay = gameplay
        self.tail = TailSpriteQueue(self, gameplay.tail_colors)
        self.mv = mv
        self.fruits = gameplay.fruits
        self.arena_shape = gameplay.arena_shape
    
    def move(self, mv: Optional[Tuple[int]]=None) -> Tuple[bool]:
        """
        Updates the position of the head, including performing the
        corresponding required updates to the tail, checking if
        has collided with the tail or walls and checking if has
        collided with fruit (and if so, removing that fruit and
        spawning a new one).
        
        Args:
        pressed_keys (tuple), optional: the output of
            pygame.key.get_pressed() representing the keys that are
            being pressed at the time when that function is called.
            If not given, or given as None, evaluates this function
            at the beginning of this method.
        
        Returns:
        2-tuple of bools, of which the 0th index corresponds to
        whether the snake is still alive and the second to
        whether it has eaten fruit.
        """
        if mv is None:
            mv = self.mv
        else: self.mv = mv
        # Finding the position after the move
        pos2 = self.pos_flat
        shape = self.arena_shape
        x = pos2 % shape[1] if mv[0] else pos2 // shape[1]
        #print(f"mv = {mv}, pos2 = {pos2}, x = {x}")
        if not 0 <= x + mv[1] < shape[mv[0]]:
            return (False, False)
        pos2 += mv[1] * (1 if mv[0] else shape[1])
        hit_fruit = self.fruits.remove(pos2)
        occ_pos_flat = self.gameplay.occ_pos_flat
        for pos_flat in self.tail.move(extend_tail=hit_fruit)[0]:
            occ_pos_flat.remove(pos_flat)
        if self.tail.includesPosition(pos2):
            return (False, False)
        if not hit_fruit:
            occ_pos_flat.add(pos2)
        #if hit_fruit:
        #    self.fruits.randomSpawn()
        self.pos_flat = pos2
        return (True, hit_fruit)
    
    def drawHeadAndTail(self) -> None:
        #print("Drawing head")
        self.draw()
        self.tail.draw()
        return
    
# Define a tail section object
class TailSprite(SquareSprite):
    def __init__(self, head: "HeadSprite", pos_flat: Tuple[int], color: Tuple[Union[Tuple[int], Real]]):
        super().__init__(
            head.screen,
            head.arena_shape,
            pos_flat,
            color=color, size=head.size,
            screen_pos_func=head.screen_pos_func,
        )

# Define the tail as a whole
class TailSpriteQueue:
    def __init__(self, head: "HeadSprite", tail_colors: Tuple[Tuple[Union[Tuple[int], Real]]]):
        self.head = head
        self.tail_qu = deque()
        self.pos_in_qu = set()
        self.tail_colors = tail_colors
    
    def includesPosition(self, pos_flat: int):
        return pos_flat in self.pos_in_qu
    
    def move(self, extend_tail: bool=False) -> Tuple[Set[int]]:
        res = (set(), set())
        if not self.tail_qu and not extend_tail:
            return res
        head = self.head
        self.tail_qu.append(TailSprite(self.head, self.head.pos_flat,\
                color=self.tail_colors[0]))
        res[1].add(self.head.pos_flat)
        self.pos_in_qu.add(self.head.pos_flat)
        if not extend_tail:
            tail_end = self.tail_qu.popleft()
            self.pos_in_qu.remove(tail_end.pos_flat)
            res[0].add(tail_end.pos_flat)
            tail_end.kill()
        return res
    
    def draw(self) -> None:
        if len(self.tail_colors) != 1 and len(self.tail_qu) > 1:
            length = len(self.tail_qu) - 1
            for i, tail_sprite in enumerate(self.tail_qu):
                r = i / length
                ratios = (1 - r, r)
                colors = self.tail_colors[0][0], self.tail_colors[1][0]
                color = tuple(c1 * ratios[0] + c2 * ratios[1] for c1, c2 in zip(*colors)) 
                opacities = self.tail_colors[0][1], self.tail_colors[1][1]
                opacity = opacities[0] * ratios[0] + opacities[1] * ratios[1]
                tail_sprite.color = (color, opacity)
        for tail_sprite in self.tail_qu:
            tail_sprite.draw()
        return

# Define a fruit object
class FruitSprite(SquareSprite):
    def __init__(self, gameplay, pos_flat: Tuple[int]):
        super().__init__(gameplay.screen, gameplay.arena_shape,\
                pos_flat, color=gameplay.fruit_color,\
                size=gameplay.head_size,\
                screen_pos_func=gameplay.screen_pos_func)

class Fruits:
    def __init__(self, gameplay):
        self.gameplay = gameplay
        self.fruit_dict = SortedDict()
        
    def remove(self, pos_flat: Tuple[int]) -> bool:
        if pos_flat not in self.fruit_dict.keys():
            return False
        self.fruit_dict.pop(pos_flat)
        return True
        
    def randomSpawn(self, occ_pos_flat: SortedSet, count: int=1) -> List[int]:
        shape = self.gameplay.arena_shape
        mx = shape[0] * shape[1] - len(occ_pos_flat)
        if mx < count:
            raise NoSpaceToCreateError("Insufficient valid spaces to "
                    "place the specified number of fruits.")
        idx_lst = next(iter(randomKTupleGenerator(mx, count,\
                mx_n_samples=1, allow_index_repeats=False,\
                allow_tuple_repeats=False,
                nondecreasing=True)))
        res = []
        for idx in reversed(idx_lst):
            pos_flat = findKthMissing(occ_pos_flat, idx)
            res.append(pos_flat)
            occ_pos_flat.add(pos_flat)
            self.fruit_dict[pos_flat] =\
                    FruitSprite(self.gameplay, pos_flat)
        return res
    
    def draw(self) -> None:
        for fruit_sprite in self.fruit_dict.values():
            fruit_sprite.draw()
        return

class GamePlay:
    navkeys_def = navkeys_def_glob
    navkeys_dict_def = createNavkeyDict(navkeys_def)
    
    static_bg_imgs_constructor_names = ["arena", "title_text", "score_text_static"]
    
    pause_keys_def = {pg.K_p}

    def __init__(
        self,
        screen: Optional[pg.Display]=None,
        head_size: int=25,
        arena_shape: Tuple[int, int]=(16, 15),
        head_init_pos_func: Optional[Union[Tuple[int, int], Callable[[GamePlay], Tuple[int, int]]]]=None,
        head_init_direct: Tuple[int, int]=(0, 1),
        move_rate: Real=15,
        n_frame_per_move: int=2,
        n_fruit: int=1,
        border=((1, 1), (4, 1)),
        font: Optional["pg.freetype"]=None,
        auto: bool=False,
        navkeys: Optional[Set[int]]=None,
        pause_keys: Optional[Set[int]]=None,
    ):
        pg.init()
        self._screen = screen
        self.head_size = head_size
        self.arena_shape = arena_shape
        self.move_rate = move_rate
        self.n_frame_per_move = n_frame_per_move
        self.n_fruit = n_fruit
        self.border = border
        self.font = font_def_func() if font is None else font
        
        #self.head_init_pos = tuple(x // 2 for x in arena_shape)\
        #        if head_init_pos is None else head_init_pos
        if head_init_pos_func is None:
            head_init_pos_func = lambda gameplay_obj: tuple(x // 2 for x in gameplay_obj.arena_shape)
        elif not callable(head_init_pos_func):
            head_init_pos_func = lambda gameplay_obj: head_init_pos_func
        self.head_init_pos_func = head_init_pos_func
        self.head_init_direct = head_init_direct
        self.auto = auto
        
        self.navkeys = navkeys
        self.pause_keys = pause_keys
        
        self.head_color = (named_colors_def["red"], 1)
        self.tail_colors = ((named_colors_def["black"], 1), ((150, 0, 0), 1))
        self.fruit_color = (named_colors_def["lime"], 1)
        
        self.bg_color = (named_colors_def["gray"], 1)
                
        #self.curr_auto_fruit = 0
        
        #hp = self.head_init_pos
        #hp_flat = hp[0] * arena_shape[1] + hp[1]
        #self.head = HeadSprite(gameplay, pos_flat, mv=(1, 1))
        
        self.screen_pos_func = self.screenPositionFromFlat
        
        self.enter_keys = enter_keys_def_glob
        
        self.user_input_processor = UserInputProcessor(keys_down_func=False,
            key_press_event_filter=lambda obj, event: event.key in obj.pause_keys.union(obj.navkeys_dict.keys()),
            key_release_event_filter=False,
            mouse_press_event_filter=False,
            mouse_release_event_filter=False,
            other_event_filter=False,
            get_mouse_status_func=False)
    
    @property
    def pause_keys(self):
        return self.pause_keys_def if self._pause_keys is None else self._pause_keys
    
    @pause_keys.setter
    def pause_keys(self, pause_keys):
        self._pause_keys = pause_keys
        return
    
    def getPauseOverlay(self) -> "MenuOverlayBase":
        #print("Using getPauseOverlay()")
        #print("Creating MenuOverlay object")
        pause_overlay = MenuOverlayBase(
            shape=self.screen_shape,
            framerate=60,
            overlay_color=(named_colors_def["green"], 0.5),
            mouse_enabled=False,
            navkeys_enabled=False,
            key_press_actions={x: (lambda: ((False,), False, False)) for x in self.pause_keys}
            #exit_press_keys={pg.K_p},
            #navkey_cycle_delay_s=navkey_cycle_delay_s,
            #navkeys=None,
            #enter_keys=None,
        )

        max_height_rel = 0.3
        max_width_rel = 0.8
        anchor_type = "center"
        anchor_rel_pos_rel = (0.5, 0.5)
        font_color = (named_colors_def["red"], 1)
        #text_list = [
        #    ("Paused", anchor_rel_pos_rel, anchor_type, max_width_rel, font_color),
        #]
        #pause_overlay.addTextGroup(text_list, max_height_rel, font=None,\
        #        font_size=None)
        text_group = TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None)
        text_list = [
            ({"text": "Pause", "font_color": font_color, "anchor_type0": anchor_type}, ((max_width_rel, max_height_rel), anchor_rel_pos_rel)),
        ]
        
        add_text_list = [x[0] for x in text_list]
        text_objs = text_group.addTextObjects(add_text_list)
        for text_obj, (_, pos_tup) in zip(text_objs, text_list):
            max_shape_rel, anchor_rel_pos_rel = pos_tup
            pause_overlay.addText(text_obj, max_shape_rel,\
                    anchor_rel_pos_rel)
        return pause_overlay
    
    @property    
    def pause_overlay(self):
        res = getattr(self, "_pause_overlay", None)
        if res is None:
            res = self.getPauseOverlay()
            self._pause_overlay = res
        return res
    
    def getDeathOverlay(self, mouse_enabled: bool=True, navkeys_enabled: bool=True) -> "ButtonMenuOverlay":
        death_overlay = ButtonMenuOverlay(
            shape=self.screen_shape,
            framerate=60,
            overlay_color=(named_colors_def["red"], 0.5),
            mouse_enabled=mouse_enabled,
            navkeys_enabled=navkeys_enabled,
            #exit_press_keys={pg.K_p},
            #navkey_cycle_delay_s=navkey_cycle_delay_s,
            #navkeys=None,
            #enter_keys=None,
        )
        #death_overlay = ButtonMenuOverlay(self.screen_shape, framerate=60,\
        #    overlay_color=(named_colors_def["red"], 0.5),\
        #    mouse_enabled=navkeys_enabled, navkeys_enabled=navkeys_enabled,\
        #    exit_press_keys={pg.K_p})
        
        max_height_rel = 0.2
        max_width_rel = 0.8
        anchor_type = "midbottom"
        anchor_rel_pos_rel = (0.5, 0.45)
        font_color = (named_colors_def["white"], 1)
        
        text_group = TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None)
        text_list = [
            ({"text": "Game over", "font_color": font_color, "anchor_type0": anchor_type}, ((max_width_rel, max_height_rel), anchor_rel_pos_rel)),
        ]
        
        add_text_list = [x[0] for x in text_list]
        text_objs = text_group.addTextObjects(add_text_list)
        for text_obj, (_, pos_tup) in zip(text_objs, text_list):
            max_shape_rel, anchor_rel_pos_rel = pos_tup
            death_overlay.addText(text_obj, max_shape_rel,\
                    anchor_rel_pos_rel)
        
        #text_list = [
        #    ("Game Over", anchor_rel_pos_rel, anchor_type, max_width_rel, font_color),
        #]
        #death_overlay.addTextGroup(text_list, max_height_rel, font=None,\
        #        font_size=None)
        
        #button_text_groups = tuple((TextGroup([], max_height0=None, font=None, font_size=None, text_global_asc_desc_chars=None),) for _ in range(4))
        button_text_anchortypes_and_actions = [
            [
                ("Retry", "center", (lambda: ((True,), False, False))),
                ("Main menu", "center", (lambda: ((False,), False, False)))
            ]
        ]
        
        death_overlay.setupButtonGrid(
            anchor_pos_norm=(0.5, 0.55),
            anchor_type="midtop",
            button_grid_max_shape_norm=(0.8, 0.1),
            button_text_anchortype_and_actions=button_text_anchortypes_and_actions,
            wh_ratio_range=(2, 10),
            text_groups=None,
            button_gaps_rel_shape=(0.1, 0.2),
            font_colors=((named_colors_def["white"], 0.5), (named_colors_def["yellow"], 1), (named_colors_def["blue"], 1), (named_colors_def["green"], 1)),
            text_borders_rel=((0.2, 0.2), (0.1, 0.1), 1, 0),
            fill_colors=(None, (named_colors_def["red"], 0.2), (named_colors_def["red"], 0.5), 2),
            outline_widths=((1,), (2,), (3,), 1),
            outline_colors=((named_colors_def["black"], 1), (named_colors_def["blue"], 1), 1, 1),
        )
        return death_overlay
    
    @property
    def death_overlay(self):
        res = getattr(self, "_death_overlay", None)
        if res is None:
            res = self.getDeathOverlay()
            self._death_overlay = res
        return res
    
    def screenPosition(self, pos: Tuple[int]) -> Tuple[int]:
        return tuple((x + y[0]) * self.head_size\
                for x, y in zip(pos, self.border))
    
    def screenPositionFromFlat(self, pos_flat: int) -> Tuple[int]:
        pos = divmod(pos_flat, self.arena_shape[1])
        return self.screenPosition(pos)
    
    def _resetGameDimensions(self) -> None:
        #print("Using _resetGameDimensions()")
        self._arena_dims = None
        self._screen_shape = None
        self._auto_fruitpos = None
        self._arena_topleft = None
        self._arena = None
        self._score_text_max_height = None
        self._score_text_static_max_width = None
        self._score_text_number_max_width = None
        self._score_text_static_bottomright_pos = None
        self._score_text_number_bottomleft_pos = None
        self._static_bg_surf = None

        for menu_attr in ("_pause_overlay", "_death_overlay"):
            menu = getattr(self, menu_attr, None)
            if menu is None: continue
            menu.shape = self.screen_shape
            #print(f"self.screen_shape = {self.screen_shape}, {menu} shape = {menu.shape}")
        return

    @property
    def border(self):
        return self._border
    
    @border.setter
    def border(self, border):
        self._border = border
        self._resetGameDimensions()
        return
    
    @property
    def head_size(self):
        return self._head_size
    
    @head_size.setter
    def head_size(self, head_size):
        self._head_size = head_size
        self._resetGameDimensions()
        #self._arena_dims = None
        #self._screen_shape = None
        #self._arena_topleft = None
        return
    
    @property
    def arena_shape(self):
        return self._arena_shape
    
    @arena_shape.setter
    def arena_shape(self, arena_shape):
        self._arena_shape = arena_shape
        self._resetGameDimensions()
        return
    
    @property
    def arena_dims(self):
        arena_dims = getattr(self, "_arena_dims", None)
        if arena_dims is not None:
            return arena_dims
        #print("calculating arena_dims")
        self._arena_dims = tuple(self._head_size * x for x in\
                                self._arena_shape)
        return self._arena_dims
    
    @property
    def arena_topleft(self):
        # Position of the upper left corner of the arena
        arena_topleft = getattr(self, "_arena_topleft", None)
        if arena_topleft is not None:
            return arena_topleft
        self._arena_topleft = self.screenPosition((0, 0))
        return self._arena_topleft
    
    @property
    def screen_shape(self):
        screen_shape = getattr(self, "_screen_shape", None)
        if screen_shape is not None:
            return screen_shape
        self._screen_shape = tuple(self.head_size * (x + sum(y))\
                for x, y in zip(self.arena_shape, self.border))
        
        return self._screen_shape
    
    @property
    def screen(self):
        screen = getattr(self, "_screen", None)
        if screen is None:
            self._screen = pg.display.set_mode(self.screen_shape)
            pg.display.set_caption("Anguis")
        return self._screen
    
    @property
    def auto_fruitpos(self):
        auto_fruitpos = getattr(self, "_auto_fruitpos", None)
        if auto_fruitpos is not None:
            return auto_fruitpos
        auto_fruitpos = []
        for fruitpos_prov in self.auto_fruitpos_prov:
            auto_fruitpos.append([[]])
            for x, y in zip(fruitpos_prov[0], self.arena_shape):
                if x >= 0:
                    auto_fruitpos[-1][0].append(x)
                    continue
                #print(auto_fruitpos[-1])
                #print(auto_fruitpos[-1][0])
                auto_fruitpos[-1][0].append(x + y)
            auto_fruitpos[-1][0] = tuple(auto_fruitpos[-1][0])
            auto_fruitpos[-1].append(fruitpos_prov[1])
        self._auto_fruitpos = tuple(auto_fruitpos)
        return self._auto_fruitpos
    
    #@property
    #def bg_surf(self):
    #    res = getattr(self, "_bg_surf", None)
    #    if res is None:
    #        res = self.createBackgroundSurface()
    #        self._bg_surf = res
    #    return res
    
    #def createBackgroundSurface(self):
    #    surf = pg.Surface(self.screen_shape)
    #    color, alpha0 = self.bg_color
    #    surf.set_alpha(alpha0 * 255)
    #    surf.fill(color)
    #    return surf
    
    #@property
    #def bg_img_constructor(self):
    #    res = getattr(self, "_bg_img_constructor", None)
    #    if res is None:
    #        res = self.createBackgroudImageConstructor()
    #        self._bg_img_constructor = res
    #    return res
    #
    #def createBackgroundImageConstructor(self) -> Callable[[], None]:
    #    return lambda: self.screen.blit(self.bg_surf, (0, 0))
    
    @property
    def arena(self):
        res = getattr(self, "_arena", None)
        if res is None:
            res = self.createArena()
            self._arena = res
        return res
    
    def createArena(self):
        #print("Using createArena()")
        return pg.Rect(*self.arena_topleft, *self.arena_dims)
    
    @property
    def arena_img_constructor(self):
        res = getattr(self, "_arena_img_constructor", None)
        if res is None:
            res = self.createArenaImageConstructor()
            self._arena_img_constructor = res
        return res
    
    def createArenaImageConstructor(self) -> Callable[["pg.Surface"], None]:
        return lambda surf: pg.draw.rect(surf, named_colors_def["white"],\
                            self.arena, 0)
    
    @property
    def title_text(self):
        res = getattr(self, "_title_text", None)
        if res is None:
            res = self.createTitleText()
            self._title_text = res
        return res
    
    @property
    def title_text_anchor_rel_pos(self):
        res = getattr(self, "_title_text_anchor_rel_pos", None)
        if res is None:
            res = self.calculateTitleTextAnchorPosition()
            self._title_text_anchor_rel_pos = res
        return res
    
    def calculateTitleTextAnchorPosition(self):
        anchor_rel_pos = (self.border[0][0], self.border[1][0] / 2)
        return tuple(x * self.head_size for x in anchor_rel_pos)
    
    @property
    def title_text_max_shape(self):
        res = getattr(self, "_title_text_max_shape", None)
        if res is None:
            res = self.calculateTitleTextMaxShape()
            self._title_text_max_shape = res
        return res
    
    def calculateTitleTextMaxShape(self):
        max_shape = (self.arena_shape[0] * 0.48, self.border[1][0] * 0.9)
        return tuple(x * self.head_size for x in max_shape)
    
    def createTitleText(self):
        #anchor_rel_pos = self.title_text_anchor_rel_pos
        max_shape = self.title_text_max_shape
        return Text(max_shape, "Anguis", font=None,
            font_size=None, font_color=(named_colors_def["white"], 1))
    
    @property
    def title_text_img_constructor(self):
        res = getattr(self, "_title_text_img_constructor", None)
        if res is None:
            res = self.createTitleTextImageConstructor()
            self._title_text_img_constructor = res
        return res
    
    def createTitleTextImageConstructor(self) -> Callable[["pg.Surface"], None]:
        def constructor(surf) -> None:
            text_obj = self.title_text
            text_obj.max_shape = self.title_text_max_shape
            text_obj.anchor_rel_pos = self.title_text_anchor_rel_pos
            text_obj.draw(surf, self.title_text_anchor_rel_pos, anchor_type="midleft")
        return constructor
    
    def calculateScoreTextMaxHeight(self) -> float:
        return self.border[1][0] * 0.25 * self.head_size

    @property
    def score_text_max_height(self):
        res = getattr(self, "_score_text_max_height", None)
        if res is None:
            res = self.calculateScoreTextMaxHeight()
            self._score_text_max_height = res
        return res
    
    def calculateScoreTextStaticMaxWidth(self) -> float:
        self.arena_shape[0] * 0.3 * self.head_size

    @property
    def score_text_static_max_width(self):
        res = getattr(self, "_score_text_static_max_width", None)
        if res is None:
            res = self.calculateScoreTextStaticMaxWidth()
            self._score_text_static_max_width = res
        return res 
    
    def calculateScoreTextNumberMaxWidth(self) -> float:
        return self.arena_shape[0] * 0.1 * self.head_size

    @property
    def score_text_number_max_width(self):
        res = getattr(self, "_score_text_number_max_width", None)
        if res is None:
            res = self.calculateScoreTextNumberMaxWidth()
            self._score_text_number_max_width = res
        return res
    
    def calculateScoreTextStaticBottomRightPosition(self) -> Tuple[int, int]:
        return ((self.border[0][0] + self.arena_shape[0]) * self.head_size - self.score_text_number_max_width, self.border[1][0] * 0.9 * self.head_size)
        #re tuple(x * self.head_size for x in txt_anchor_rel_pos)

    @property
    def score_text_static_bottomright_pos(self):
        res = getattr(self, "_score_text_static_bottomright_pos", None)
        if res is None:
            res = self.calculateScoreTextStaticBottomRightPosition()
            self._score_text_static_bottomright_pos = res
        return res

    def calculateScoreTextNumberBottomLeftPosition(self) -> Tuple[int, int]:
        return ((self.border[0][0] + self.arena_shape[0]) * self.head_size - self.score_text_number_max_width, self.border[1][0] * 0.9 * self.head_size)
        #re tuple(x * self.head_size for x in txt_anchor_rel_pos)

    @property
    def score_text_number_bottomleft_pos(self):
        res = getattr(self, "_score_text_number_bottomleft_pos", None)
        if res is None:
            res = self.calculateScoreTextNumberBottomLeftPosition()
            self._score_text_number_bottomleft_pos = res
        return res

    def createScoreTextGroup(self):
        max_score = self.arena_shape[0] * self.arena_shape[1] - self.n_fruit
        max_n_dig = 0
        while max_score:
            max_score //= 10
            max_n_dig += 1
        max_n_dig = max(max_n_dig, 1)
        
        max_h_pixel = self.score_text_max_height

        txt_max_width_pixel = self.score_text_number_max_width
        txt_anchor_rel_pos_pixel = self.score_text_static_bottomright_pos

        num_max_width_pixel = self.score_text_number_max_width
        num_anchor_rel_pos_pixel = self.score_text_number_bottomleft_pos
        
        
        text_list = [{"text": "Score: ", "anchor_rel_pos0": txt_anchor_rel_pos_pixel, "anchor_type0": "bottomright", "max_shape": (None, txt_max_width_pixel), "font_color": (named_colors_def["black"], 1)},\
                {"text": "0", "anchor_rel_pos0": num_anchor_rel_pos_pixel, "anchor_type0": "bottomleft", "max_shape": (None, num_max_width_pixel), "font_color": (named_colors_def["black"], 1)}]
        for d in range(10):
            s = str(d) * max_n_dig
            text_list.append({"text": s, "max_shape": (None, num_max_width_pixel)})
        text_group = TextGroup([], max_h_pixel, font=None,\
                font_size=None, min_lowercase=True)
        text_objs = text_group.addTextObjects(text_list)
        return text_group, text_objs
    
    @property
    def score_text_group_and_objs(self):
        res = getattr(self, "_score_text_group_and_objs", None)
        if res is None:
            res = self.createScoreTextGroup()
            self._score_text_group_and_objs = res
        return res

    @property
    def score_text_static(self):
        return self.score_text_group_and_objs[1][0]
    
    @property
    def score_text_number(self):
        return self.score_text_group_and_objs[1][1]
    
    def updateScoreTextStaticDimensions(self) -> None:
        text_group, text_objs = self.score_text_group_and_objs
        
        max_h = self.score_text_max_height
        text_group.max_height0 = max_h

        max_w = self.score_text_static_max_width
        
        text_objs[0].max_shape = (None, max_w)
        
        anchor = self.score_text_static_bottomright_pos
        #print(f"static score text anchor position = {anchor}")
        text_objs[0].anchor_rel_pos0 = anchor
        return

    def updateScoreTextNumberDimensions(self) -> None:
        text_group, text_objs = self.score_text_group_and_objs
        
        max_h = self.score_text_max_height
        text_group.max_height0 = max_h

        max_w = self.score_text_number_max_width
        
        for i in range(1, len(text_objs)):
            text_objs[i].max_shape = (None, max_w)

        anchor = self.score_text_number_bottomleft_pos
        text_objs[1].anchor_rel_pos0 = anchor
        return

    
    
    def createScoreTextStaticImageConstructor(self) -> Callable[["pg.Surface"], None]:
        def constructor(surf) -> None:
            text_obj = self.score_text_static
            self.updateScoreTextStaticDimensions()
            text_obj.draw(surf, self.score_text_static_bottomright_pos, anchor_type="bottomright")
        return constructor

    @property
    def score_text_static_img_constructor(self):
        res = getattr(self, "_score_text_static_img_constructor", None)
        if res is None:
            res = self.createScoreTextStaticImageConstructor()
            self._score_text_static_img_constructor = res
        return res
    
    #def createTextImageConstructor(self, text_obj) -> Callable[["pg.Surface"], None]:
    #    def constructor(surf: "pg.Surface") -> None:
    #        #surf.set_alpha(255)
    #        #surf.fill((0, 255, 255))
    #        text_obj._screen = surf
    #        text_obj.draw(surf)
    #    return constructor
    
    @property
    def score_text_number_img_constructor(self):
        res = getattr(self, "_score_text_number_img_constructor", None)
        if res is None:
            res = self.createScoreTextNumberImageConstructor()
            self._score_text_number_img_constructor = res
        return res
    
    def createScoreTextNumberImageConstructor(self) -> Callable[["pg.Surface"], None]:
        def constructor(surf) -> None:
            #print(f"constructing score text number")
            self.updateScoreTextNumberDimensions()
            text_obj = self.score_text_number
            text_obj.draw(surf, self.score_text_number_bottomleft_pos, anchor_type="bottomleft")
        return constructor

    @property
    def static_bg_img_constructor(self):
        res = getattr(self, "_static_bg_img_constructor", None)
        if res is None:
            res = self.createStaticBackgroundImageConstructor()
            self._static_bg_imgs_constructor = res
        return res
    
    def createStaticBackgroundImageConstructor(self) -> Callable[[], None]:
        def constructor(surf: "pg.Surface") -> None:
            for nm in self.static_bg_imgs_constructor_names:
                constructor = getattr(self, f"{nm}_img_constructor", lambda surf: None)
                constructor(surf)
            
        return constructor
    
    def createBackgroundSurface(self):
        surf = pg.Surface(self.screen_shape)
        color, alpha0 = self.bg_color
        surf.set_alpha(alpha0 * 255)
        surf.fill(color)
        return surf

    @property
    def static_bg_surf(self) -> "pg.Surface":
        res = getattr(self, "_static_bg_surf", None)
        if res is None:
            res = self.createBackgroundSurface()
            self.static_bg_img_constructor(res)
            self._static_bg_surf = res
        return res

    def drawStaticBackgroundImages(self) -> None:
        #self._bg_surf = None
        #self.static_bg_imgs_constructor(self.bg_surf)
        surf = self.static_bg_surf
        if surf is not None:
            self.screen.blit(surf, (0, 0))
        return
    
    def draw(self, score: int, overlay=None) -> None:
        self.drawStaticBackgroundImages()
    
        # Fill the border with grey
        #self.screen.fill(named_colors_def["gray"])
        
        # Load the arena
        #self._arena = None
        #self.arena
        
        # Display the score
        self.score_text_number.text = str(score)
        self.score_text_number_img_constructor(self.screen)
        
        self.head.drawHeadAndTail()
        self.fruits.draw()
        
        # Add on overlay
        #if overlay_input is not None and iter_cycle_no == 0:
        #    self.overlay_screen(*overlay_input[0],\
        #            **overlay_input[1])
        return
    
    @property
    def navkeys(self):
        return self.navkeys_def if self._navkeys is None else self._navkeys
    
    @navkeys.setter
    def navkeys(self, navkeys):
        self._navkeys_dict = None
        self._navkeys = navkeys
        return
    
    @property
    def navkeys_dict(self):
        res = getattr(self, "_navkeys_dict", None)
        if res is None:
            navkeys = self.navkeys
            if navkeys is not None:
                res = self.getNavkeyDict(navkeys)
        return self.navkeys_dict_def if res is None else res
    
    @staticmethod
    def getNavkeyDict(navkeys: Tuple[Tuple[Set[int]]]):
        return createNavkeyDict(navkeys)
    
    def getRequiredInputs(self) -> Tuple[Union[bool, Dict[str, Union[List[int], Tuple[Union[Tuple[int], int]]]]]]:
        quit, esc_pressed, events = self.user_input_processor.getEvents(self)
        return quit, esc_pressed, {"events": events,\
                "keys_down": self.user_input_processor.getKeysHeldDown(self),\
                "mouse_status": self.user_input_processor.getMouseStatus(self)}
    
    def navkey2Move(self, navkey: int):
        inds = self.navkeys_dict[navkey]
        return (inds[0], inds[1] * 2 - 1)
    
    def updateKeyBuffer(self, key_buffer_qu: deque):
        # Checking user inputs
        quit, esc_pressed, input_dict = self.getRequiredInputs()
        
        running = not esc_pressed and not quit
        events = input_dict["events"]
        #quit, running, events = self.getRequiredInputs()[:3]
        
        # Find the keys pressed including Pause
        to_pause = False
        for event_tup in events:
            if event_tup[1] != 0: continue
            if event_tup[0].key in self.pause_keys:
                return (running, quit, True)
            if event_tup[0].key in self.navkeys_dict.keys():
                key_buffer_qu.append(event_tup[0].key)
        #if esc_pressed:
        #    print("escape key pressed")
        #    print(f"running = {running}, quit = {quit}")
        return (running, quit, False)
    
    @property
    def bot(self):
        res = getattr(self, "_bot", None)
        if res is None:
            snake_qu = deque(x.pos_flat for x in self.head.tail.tail_qu)
            snake_qu.append(self.head.pos_flat)
            res = TailChaserBot(
                self.arena_shape,
                self.head.pos_flat,
                head_direct=self.head.mv,
                fruits=set(self.head.fruits.fruit_dict.keys()),
                snake_qu=snake_qu,
            )
            self._bot = res
        return res
    
    def autoDirection(self, key_buffer_qu: deque, framerate: int, clock: "pg.time.Clock", add_fruit: Optional[int]=None):
        tail_end_idx = self.head.tail.tail_qu[0].pos_flat if self.head.tail.tail_qu else self.head.pos_flat
        res = self.bot.addFruitFindMoveAndUpdate(add_fruit=add_fruit, search_depth=4)
        clock.tick(framerate)
        (running, quit, to_pause) =\
                    self.updateKeyBuffer(key_buffer_qu)
        if to_pause:
            _, quit = self.pause()
        if quit: running = False
        while key_buffer_qu: key_buffer_qu.popleft()
        return running, quit, res
    
    def userInputDirection(self, key_buffer_qu: deque, framerate: int, clock: "pg.time.Clock") -> Tuple[int]:
        running = True
        quit = False
        t = 0
        while t < self.n_frame_per_move:
            t += 1
            # Ensure program maintains the specified frame rate
            clock.tick(framerate)
            (running, quit, to_pause) =\
                    self.updateKeyBuffer(key_buffer_qu)
            if not running: break
            if to_pause:
                _, quit = self.pause()
                if quit:
                    running = False
                    break
                if key_buffer_qu:
                    key_buffer_qu = deque([key_buffer_qu[0]])
        #print(f"running = {running}, quit = {quit}")
        if not running: return (running, quit, None)
        # Get move from key buffer
        if self.head.mv[1]:
            while key_buffer_qu:
                mv = self.navkey2Move(key_buffer_qu.popleft())
                if mv[0] != self.head.mv[0]: break
            else: mv = None
        else: mv = self.navkey2Move(key_buffer_qu.popleft())\
                if key_buffer_qu else None
        return (running, quit, mv)
    
    def run(self, overlay_input=None, auto: bool=False):
        # Setup the clock for a consistent framerate
        clock = pg.time.Clock()
        
        # Set or reset the fruits
        self.fruits = Fruits(self)
        
        # Set or reset the head to its initial position and direction
        hp = self.head_init_pos_func(self)
        hp_flat = hp[0] * self.arena_shape[1] + hp[1]
        self.head = HeadSprite(self, hp_flat, self.head_init_direct)
        
        # Record occupied flattened positions
        self.occ_pos_flat = SortedSet({self.head.pos_flat})
        
        # Add initial fruit(s)
        self.fruits.randomSpawn(self.occ_pos_flat, count=self.n_fruit)

        # Variable to keep the main loop running
        running = True
        
        key_buffer_qu = deque()
        prev_pressed_keys = None

        score = 0
        retry = False
        quit = False
        iter_cycle_no = 0
        
        framerate = self.move_rate * self.n_frame_per_move
        if auto:
            self._bot = None
            move_func = (lambda: self.autoDirection(key_buffer_qu, self.move_rate, clock, add_fruit=add_fruit))
            add_fruit = None
        else:
            move_func = (lambda: self.userInputDirection(key_buffer_qu, framerate, clock))

        # Main loop
        while True:
            # Update the display
            pg.display.flip()
            running, quit, mv = move_func()#self.userInputDirection(key_buffer_qu, framerate, clock)
            #print(f"running = {running}, quit = {quit}")
            #print(f"mv = {mv}")
            if not running: break
            alive, hit_fruit = self.head.move(mv)
            #print(f"head position flat = {self.head.pos_flat}, tail positions flat = {[x.pos_flat for x in self.head.tail.tail_qu]}")
            if alive and hit_fruit:
                score += 1
                try:
                    fruit_inds = self.fruits.randomSpawn(self.occ_pos_flat, count=1)
                except NoSpaceToCreateError:
                    alive = False
                    self.draw(score, overlay=None)
                else:
                    add_fruit = fruit_inds[0]
            else: add_fruit = None
            if not alive:
                retry, quit = self.death()
                break
            
            #print(f"fruit flat positions = {set(self.fruits.fruit_dict.keys())}")
            self.draw(score, overlay=None)
            #print(f"score = {score}")
        return score, retry, quit
    
    def menuOverlay(self, overlay_attr: str) -> Tuple[bool, bool]:
        
        screen = self.screen
        screen_cp = pg.Surface.copy(screen)
        overlay = getattr(self, overlay_attr)
        framerate = overlay.framerate
        restart = False
        quit = False
        screen_changed = True
        
        clock = pg.time.Clock()
        while True:
            quit, esc_pressed, event_loop_kwargs = overlay.getRequiredInputs()
            #print(event_loop_kwargs)
            running = not esc_pressed
            if quit or not running:
                break
            change = False
            quit2, running2, chng, actions = overlay.eventLoop(check_axes=(0, 1), **event_loop_kwargs)
            if not running2: running = False
            if quit2: quit = True
            for action in actions:
                #print(action)
                acts, running2, quit2 = action()
                #print(f"actions: acts = {acts}, running = {running2}, quit = {quit2}")
                if acts[0]: restart = True
                if not running2: running = False
                if quit2: quit = True
            if quit or not running:
                break
            if chng: change = True
            if change: screen_changed = True
            if screen_changed:
                screen.blit(screen_cp, (0, 0))
                overlay.draw(screen)
                pg.display.flip()
            clock.tick(framerate)
            screen_changed = False
        return restart, quit
    
    def pause(self) -> Tuple[bool, bool]:
        return self.menuOverlay(overlay_attr="pause_overlay")
    
    def death(self) -> Tuple[bool, bool]:
        return self.menuOverlay(overlay_attr="death_overlay")
    
if __name__ == "__main__":
    bot = False
    gameplay = GamePlay(move_rate=15, n_fruit=5, head_init_direct=(0, 0))
    gameplay.run(auto=bot)
