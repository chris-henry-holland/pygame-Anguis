# library/src/anguis/gameplay.py

from __future__ import annotations

from typing import Union, Tuple, List, Set, Dict, Optional, Callable, Any, TYPE_CHECKING

import pygame as pg

from pygame.locals import (
    K_UP,
    K_DOWN,
)

from pygame_display_component_classes import (
    enter_keys_def_glob,
    named_colors_def,
    font_def_func,
    ButtonMenuOverlay,
    SliderAndButtonMenuOverlay,
    TextGroup,
)

from anguis.gameplay import GamePlay

class Game:
    def __init__(
        self,
        head_size: int=25,
        arena_shape: Tuple[int, int]=(16, 15),
        head_init_pos_func: Optional[Union[Tuple[int, int], Callable[[GamePlay], Tuple[int, int]]]]=None,
        head_init_direct: Tuple[int, int]=(0, 1),
        move_rate: float=15,
        n_frame_per_move: float=2,
        n_fruit: int=1,
        border: Tuple[Tuple[int, int], Tuple[int, int]]=((1, 1), (4, 1)),
        font: Optional["pg.freetype"]=None,
        auto: bool=False,
        auto_startpos: Tuple[int, int]=(1, 1),
        auto_fruitpos: List[Tuple[Tuple[int, int], Tuple[int, int]]]=(((-2, 1), (1, 0)), ((-2, -2), (0, 1)), ((1, -2), (-1, 0)), ((1, 1), (0, -1))),
        navkeys: Optional[Tuple[Tuple[Set[int]]]]=None,
        menu_framerate: int=60,
    ):
        pg.init()
        self.head_size = head_size
        self.arena_shape = arena_shape
        self.head_init_pos_func = head_init_pos_func
        self.head_init_direct = head_init_direct
        self.move_rate = move_rate
        self.n_frame_per_move = n_frame_per_move
        self.n_fruit = n_fruit
        self.border = border
        self.menu_framerate = menu_framerate
        self.font = font_def_func() if font is None else font
        self.auto_startpos = auto_startpos
        
        # Note that index 1 indicates the direction the snake should
        # turn when encounters this fruit
        self.auto_fruitpos_prov = auto_fruitpos
        
        
        self.playing = False
        self.quit = False
        #self.first_screen = SnakeGame
        
        
        self.pause_fr = 30
        self.death_screen_fr = 30
        self.font_sizes = (3, 1.8, 1.2) # relative to head_size
        self.pause_overlay_color = (named_colors_def["gray"], 0.5)
        self.death_screen_overlay_color = (named_colors_def["red"], 0.5)
        self.main_menu_overlay_color = (named_colors_def["green"], 1)
        self.settings_menu_overlay_color = (named_colors_def["green"], 1)
        self.button_border = 0.4 # relative to head_size
        self.menu_arrow_cycle_delay_s = (0.5, 0.1)
        
        self.navkeys = navkeys
        self.enter_keys = enter_keys_def_glob
        self.menu_nav_keys = ({K_DOWN}, {K_UP})
    
    @property
    def gameplay(self):
        res = getattr(self, "_gameplay", None)
        if res is None:
            res = GamePlay(
                screen=self.screen,
                head_size=self.head_size,
                arena_shape=self.arena_shape,
                head_init_pos_func=self.head_init_pos_func,
                head_init_direct=self.head_init_direct,
                move_rate=self.move_rate,
                n_frame_per_move=self.n_frame_per_move,
                n_fruit=self.n_fruit,
                border=self.border,
                font=self.font,
                auto=False,
                navkeys=self.navkeys,
            )
            self._gameplay = res
        return res
        
    def createMainMenuOverlay(self, mouse_enabled: bool=True, navkeys_enabled: bool=True) -> "ButtonMenuOverlay":
        
        max_height_rel = 0.2
        max_width_rel = 0.8
        anchor_type = "midbottom"
        anchor_pos_rel = (0.5, 0.3)
        font_color = (named_colors_def["white"], 1)
        navkey_cycle_delay_s = (0.4, 0.2, 0.2, 0.2, 0.1)

        #menu_overlay = ButtonMenuOverlay(self.screen_shape, framerate=self.menu_framerate,\
        #    overlay_color=self.menu_overlay_color,\
        #    mouse_enabled=mouse_enabled, navkeys_enabled=navkeys_enabled)
        #print(f"menu framerate = {self.menu_framerate}")
        main_menu_overlay = ButtonMenuOverlay(
            shape=self.screen_shape,
            framerate=self.menu_framerate,
            overlay_color=self.main_menu_overlay_color,
            mouse_enabled=mouse_enabled,
            navkeys_enabled=navkeys_enabled,
            navkey_cycle_delay_s=navkey_cycle_delay_s,
            #navkeys=None,
            #enter_keys=None,
        )
        
        text_group = TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None)
        text_list = [
            ({"text": "Main menu", "font_color": font_color, "anchor_type0": anchor_type}, ((max_width_rel, max_height_rel), anchor_pos_rel)),
        ]
        
        add_text_list = [x[0] for x in text_list]
        text_objs = text_group.addTextObjects(add_text_list)
        #print(text_objs)
        for text_obj, (_, pos_tup) in zip(text_objs, text_list):
            max_shape_rel, anchor_pos_rel = pos_tup
            main_menu_overlay.addText(text_obj, max_shape_rel,\
                    anchor_pos_rel)
        
        #button_text_groups = tuple((TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None),) for _ in range(4))
        #button_text_and_actions =\
        #        [[(("Play game", "center"), (lambda: (0, True, False, True, False))),\
        #        (("Options", "center"), (lambda: (-1, True, False, True, False))),\
        #        (("Exit", "center"), (lambda: (-1, True, False, False, True)))]]
        button_anchor_pos_tup = (("center",), 0, 0, 0)
        button_text_anchortype_and_actions = [
            [("Play game", button_anchor_pos_tup, 1)],
            [("Watch bot", button_anchor_pos_tup, 2)],
            [("Settings", button_anchor_pos_tup, 3)],
            [("Exit", button_anchor_pos_tup, 0)],
        ]
        
        main_menu_overlay.setupButtonGrid(
            anchor_pos_norm=(0.5, 0.35),
            anchor_type="midtop",
            button_grid_max_shape_norm=(0.5, 0.55),
            button_text_anchortype_and_actions=button_text_anchortype_and_actions,
            wh_ratio_range=(0.1, 10),
            text_groups=None,#button_text_groups,
            button_gaps_rel_shape=(0.1, 0.1),
            font_colors=((named_colors_def["white"], 0.5), (named_colors_def["yellow"], 1), (named_colors_def["blue"], 1), (named_colors_def["green"], 1)),
            text_borders_rel=((0.2, 0.2), (0.1, 0.1), 1, 0),
            fill_colors=(None, (named_colors_def["red"], 0.2), (named_colors_def["red"], 0.5), 2),
            outline_widths=((1,), (2,), (3,), 1),
            outline_colors=((named_colors_def["black"], 1), (named_colors_def["blue"], 1), 1, 1),
        )
        
        return main_menu_overlay
    
    @property
    def main_menu_overlay(self):
        res = getattr(self, "_main_menu_overlay", None)
        if res is None:
            res = self.createMainMenuOverlay()
            self._main_menu_overlay = res
        return res
    
    def createSettingsMenuOverlay(self, mouse_enabled: bool=True, navkeys_enabled: bool=True) -> "SliderAndButtonMenuOverlay":
        
        title_max_height_rel = 0.15
        title_max_width_rel = 0.8
        #anchor_type = "midbottom"
        #anchor_pos_rel = (0.5, 0.3)
        title_anchor_type = "midtop"
        title_anchor_pos_rel = (0.5, 0.05)
        font_color = (named_colors_def["white"], 1)
        navkey_cycle_delay_s = (0.4, 0.2, 0.2, 0.2, 0.1)

        #menu_overlay = ButtonMenuOverlay(self.screen_shape, framerate=self.menu_framerate,\
        #    overlay_color=self.menu_overlay_color,\
        #    mouse_enabled=mouse_enabled, navkeys_enabled=navkeys_enabled)
        #print(f"menu framerate = {self.menu_framerate}")
        settings_menu_overlay = SliderAndButtonMenuOverlay(
            shape=self.screen_shape,
            framerate=self.menu_framerate,
            overlay_color=self.settings_menu_overlay_color,
            mouse_enabled=mouse_enabled,
            navkeys_enabled=navkeys_enabled,
            navkey_cycle_delay_s=navkey_cycle_delay_s,
            navkeys=self.navkeys,
            enter_keys=self.enter_keys,
        )
        
        text_group = TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None)
        text_list = [
            ({"text": "Settings", "font_color": font_color, "anchor_type0": title_anchor_type}, ((title_max_width_rel, title_max_height_rel), title_anchor_pos_rel)),
        ]
        
        add_text_list = [x[0] for x in text_list]
        text_objs = text_group.addTextObjects(add_text_list)
        #print(text_objs)
        for text_obj, (_, pos_tup) in zip(text_objs, text_list):
            max_shape_rel, anchor_pos_rel = pos_tup
            settings_menu_overlay.addText(text_obj, max_shape_rel,\
                    anchor_pos_rel)


        slider_plus_parameters = []
    
        slider_plus_parameters.append([{
            "title": "Number of fruits",
            "val_range": (1, 6),
            "increment_start": 1,
            "increment": 1,
            "init_val": 1,
            "demarc_numbers_dp": 0,
            "demarc_intervals": (1,),
            "demarc_start_val": 1,
            "val_text_dp": 0,
        }])

        slider_plus_parameters.append([{
            "title": "Speed",
            "val_range": (4, 24),
            "increment_start": 0,
            "increment": 1,
            "init_val": 1,
            "demarc_numbers_dp": 0,
            "demarc_intervals": (4,),
            "demarc_start_val": 0,
            "val_text_dp": 0,
        }])

        slider_plus_parameters.append([{
            "title": "Arena width",
            "val_range": (10, 100),
            "increment_start": 0,
            "increment": 1,
            "init_val": 10,
            "demarc_numbers_dp": 0,
            "demarc_intervals": (10,),
            "demarc_start_val": 0,
            "val_text_dp": 0,
        }])
        
        slider_plus_parameters.append([{
            "title": "Arena height",
            "val_range": (10, 100),
            "increment_start": 0,
            "increment": 1,
            "init_val": 10,
            "demarc_numbers_dp": 0,
            "demarc_intervals": (10,),
            "demarc_start_val": 0,
            "val_text_dp": 0,
        }])

        settings_menu_overlay.setupSliderPlusGrid(
            anchor_pos_norm=(0.5, 0.5),
            anchor_type="center",
            slider_plus_grid_max_shape_norm=(0.8, 0.55),
            slider_plus_parameters=slider_plus_parameters,
            slider_plus_gaps_rel_shape=(0.2, 0.2),
            wh_ratio_range=(0.5, 2),
            demarc_numbers_text_group=None,
            thumb_radius_rel=1,
            demarc_line_lens_rel=(0.5,),
            demarc_numbers_max_height_rel=1.5,
            track_color=(named_colors_def["gray"], 1),
            thumb_color=(named_colors_def["silver"], 1),
            demarc_numbers_color=(named_colors_def["white"], 1),
            demarc_line_colors=((named_colors_def["gray"], 1),),
            thumb_outline_color=None,
            slider_shape_rel=(0.7, 0.6),
            slider_borders_rel=(0.05, 0.1),
            title_text_group=None,
            title_anchor_type="topleft",
            title_color=(named_colors_def["white"], 1),
            val_text_group=None,
            val_text_anchor_type="midright",
            val_text_color=(named_colors_def["white"], 1),
        )

        button_anchor_pos_tup = (("center",), 0, 0, 0)
        button_text_anchortype_and_actions = [
            [
                ("Apply", button_anchor_pos_tup, 1),
                ("Revert", button_anchor_pos_tup, 2),
                ("Return", button_anchor_pos_tup, 0),
            ]
        ]
        
        settings_menu_overlay.setupButtonGrid(
            anchor_pos_norm=(0.5, 0.9),
            anchor_type="midbottom",
            button_grid_max_shape_norm=(0.8, 0.1),
            button_text_anchortype_and_actions=button_text_anchortype_and_actions,
            wh_ratio_range=(1, 20),
            text_groups=None,#button_text_groups,
            button_gaps_rel_shape=(0.2, 0.2),
            font_colors=((named_colors_def["white"], 0.5), (named_colors_def["yellow"], 1), (named_colors_def["blue"], 1), (named_colors_def["green"], 1)),
            text_borders_rel=((0.2, 0.2), (0.1, 0.1), 1, 0),
            fill_colors=(None, (named_colors_def["red"], 0.2), (named_colors_def["red"], 0.5), 2),
            outline_widths=((1,), (2,), (3,), 1),
            outline_colors=((named_colors_def["black"], 1), (named_colors_def["blue"], 1), 1, 1),
        )
        
        return settings_menu_overlay

    @property
    def settings_menu_overlay(self):
        res = getattr(self, "_settings_menu_overlay", None)
        if res is None:
            res = self.createSettingsMenuOverlay()
            self._settings_menu_overlay = res
        return res

    def resetSettingsMenuSliders(self) -> None:
        #print("Using resetSettingsMenuSliders()")
        smo = self.settings_menu_overlay
        # Number of fruits
        smo.slider_plus_grid[0, 0].slider.setValueDirectly(self.n_fruit)
        #print(f"self.n_fruit = {self.n_fruit}, fruit count slider value = {smo.slider_plus_grid[0, 0].val}, slider value raw = {getattr(smo.slider_plus_grid[0, 0], '_val_raw', None)}")
        smo.slider_plus_grid[0, 1].slider.setValueDirectly(self.move_rate)
        smo.slider_plus_grid[0, 2].slider.setValueDirectly(self.arena_shape[0])
        smo.slider_plus_grid[0, 3].slider.setValueDirectly(self.arena_shape[1])
        return

    def applySettingsMenuSliders(self) -> None:
        smo = self.settings_menu_overlay
        self.n_fruit = smo.slider_plus_grid[0, 0].val
        self.move_rate = smo.slider_plus_grid[0, 1].val
        self.arena_shape = (smo.slider_plus_grid[0, 2].val, smo.slider_plus_grid[0, 3].val)
        return

    def _resetScreen(self) -> None:
        self._screen = pg.display.set_mode(self.screen_shape)
        for menu_attr in ("_main_menu_overlay", "_settings_menu_overlay"):
            menu = getattr(self, menu_attr, None)
            if menu is None: continue
            menu.shape = self.screen_shape
            #print(f"self.screen_shape = {self.screen_shape}, {menu} shape = {menu.shape}")
        #gameplay_obj = getattr(self, "_gameplay", None)
        #if gameplay_obj is not None:
        #    gameplay_obj.head_size = self.head_size
        #     gameplay_obj.arena_shape = self.arena_shape
        #    gameplay_obj.border = self.border
        return

    @property
    def border(self):
        return self._border
    
    @border.setter
    def border(self, border):
        self._arena_ul = None
        self._border = border

        gameplay_obj = getattr(self, "_gameplay", None)
        if gameplay_obj is not None:
            gameplay_obj.border = border
        
        if getattr(self, "_screen", None) is not None:
            self._resetScreen()
        return
    
    @property
    def head_size(self):
        return self._head_size
    
    @head_size.setter
    def head_size(self, head_size):
        self._arena_dims = None
        self._screen_shape = None
        self._arena_ul = None
        self._head_size = head_size

        gameplay_obj = getattr(self, "_gameplay", None)
        if gameplay_obj is not None:
            gameplay_obj.head_size = head_size
        
        if getattr(self, "_screen", None) is not None:
            self._resetScreen()
        return
    
    @property
    def arena_shape(self):
        return self._arena_shape
    
    @arena_shape.setter
    def arena_shape(self, arena_shape):
        self._arena_dims = None
        self._screen_shape = None
        self._auto_fruitpos = None
        self._arena_ul = None
        self._arena_shape = arena_shape
        
        gameplay_obj = getattr(self, "_gameplay", None)
        if gameplay_obj is not None:
            #print("setting gameplay object arena shape")
            gameplay_obj.arena_shape = arena_shape
        
        if getattr(self, "_screen", None) is not None:
            self._resetScreen()
        return
    
    @property
    def arena_dims(self):
        arena_dims = getattr(self, "_arena_dims", None)
        if arena_dims is not None:
            return arena_dims
        self._arena_dims = tuple(self._head_size * x for x in\
                                self._arena_shape)
        return self._arena_dims
    
    @property
    def screen_shape(self):
        screen_shape = getattr(self, "_screen_shape", None)
        if screen_shape is not None:
            return screen_shape
        self._screen_shape = tuple(self.head_size * (x + sum(y))\
                for x, y in zip(self.arena_shape, self.border))
        #screen = getattr(self, "_screen", None)
        #if screen is not None:
        #    #screen.size = self._screen_shape
        #    self._screen = pg.display.set_mode(self._screen_shape)
        return self._screen_shape
    
    @property
    def screen(self):
        screen = getattr(self, "_screen", None)
        if screen is None:
            self._resetScreen()
            #self._screen = pg.display.set_mode(self.screen_shape)
            pg.display.set_caption("Anguis")
        return self._screen
    
    @property
    def n_fruit(self) -> int:
        return self._n_fruit
    
    @n_fruit.setter
    def n_fruit(self, new_n_fruit: int) -> None:
        if new_n_fruit == getattr(self, "_n_fruit", None): return
        self._n_fruit = new_n_fruit
        gameplay_obj = getattr(self, "_gameplay", None)
        if gameplay_obj is not None:
            gameplay_obj.n_fruit = new_n_fruit
        return
    
    @property
    def move_rate(self) -> int:
        return self._move_rate
    
    @move_rate.setter
    def move_rate(self, new_move_rate: int) -> None:
        if new_move_rate == getattr(self, "_move_rate", None): return
        self._move_rate = new_move_rate
        gameplay_obj = getattr(self, "_gameplay", None)
        if gameplay_obj is not None:
            gameplay_obj.move_rate = new_move_rate
        return
    
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
    
    def mainMenuActionResolver(self, action: int) -> Tuple[bool, bool, bool, bool]:
        #print(f"action = {action}")
        if not action:
            return (True, True, False, True)
        elif action == 3:
            # Settings
            quit = self.settingsMenu()
            return (True, True, not quit, quit)
        #elif action > 2:
        #    # Quit
        #    return (False, False, True, False)
        
        # Play (action == 1) or watch bot (action == 2)
        score, retry, quit = self.gameplay.run(auto=(action == 2))
        #print(f"quit = {quit}")
        if not retry:
            return (True, True, not quit, quit)
        # Retry
        return self.mainMenuActionResolver(action)
    
    def settingsMenuActionResolver(self, action: int) -> Tuple[bool, bool, bool, bool]:
        if action == 1:
            # Apply the slider settings
            self.applySettingsMenuSliders()
            return (False, False, True, False)
        if action == 2:
            # Reset
            self.resetSettingsMenuSliders()
            return (False, False, True, False)
        # Return to main menu
        return (True, True, False, False)
    
    def actionResolver(self, overlay_attr: str, action: int) -> Tuple[bool, bool, bool, bool]:
        # return: ignore_subsequent, screen_changed, running, quit

        if overlay_attr == "main_menu_overlay":
            return self.mainMenuActionResolver(action)
        elif overlay_attr == "settings_menu_overlay":
            return self.settingsMenuActionResolver(action)
        return (False, False, True, False)
    
    def menuOverlay(self, overlay_attr: str) -> bool:
        
        screen = self.screen
        screen_cp = pg.Surface.copy(screen)
        overlay = getattr(self, overlay_attr)
        framerate = overlay.framerate
        #restart = False
        quit = False
        screen_changed = True
        
        clock = pg.time.Clock()
        while True:
            quit, esc_pressed, event_loop_kwargs = overlay.getRequiredInputs()
            running = not esc_pressed
            if quit or not running:
                break
            change = False
            quit2, running2, chng, actions = overlay.eventLoop(check_axes=(0, 1), **event_loop_kwargs)
            if not running2: running = False
            if quit2: quit = True
            for action in actions:
                #print(action)
                ignore_subsequent, chng2, running2, quit2 = self.actionResolver(overlay_attr, action)
                
                if chng2: chng = True
                if not running2: running = False
                if quit2: quit = True
                if ignore_subsequent: break
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
        return quit
    
    def mainMenu(self) -> bool:
        return self.menuOverlay(overlay_attr="main_menu_overlay")
    
    def settingsMenu(self) -> bool:
        self.resetSettingsMenuSliders()
        return self.menuOverlay(overlay_attr="settings_menu_overlay")
    
    def run(self) -> bool:
        return self.mainMenu()

if __name__ == "__main__":
    game = Game(
        arena_shape=(15, 16),
        move_rate=15,
        n_fruit=1,
        head_init_direct=(0, 0)
    )
    game.run()
