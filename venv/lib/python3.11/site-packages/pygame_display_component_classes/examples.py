# pygame_display_component_classes/examples.py

import ctypes
import functools
import gc
import os
import sys

from typing import Tuple, Union, List, Optional, Callable

import pygame as pg
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

#sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from pygame_display_component_classes import (
    Button,
    ButtonGroup,
    ButtonGrid,
    Slider,
    SliderGroup,
    SliderPlus,
    SliderPlusGroup,
    SliderPlusGrid,
    #SliderPlusVerticalBattery,
    MenuOverlayBase,
    ButtonMenuOverlay,
    SliderAndButtonMenuOverlay,
    Text,
    TextGroup,
    named_colors_def
)

def runExampleButton1() -> None:
    screen_size = (700, 700)
    framerate = 60
    pg.init()
    screen = pg.display.set_mode(screen_size)
    screen_color = named_colors_def["gray"]
    screen.fill(screen_color)
    pg.display.update(pg.Rect(0, 0, *screen_size))
    
    screen_cp = pg.Surface.copy(screen)
    
    """
    text_objects = tuple(
        (Text(
            text="Hi",
            max_shape=(200, 200),
            font=None,
            font_size=None,
            font_color=None,
            anchor_rel_pos0=None,
            anchor_type0=None,
            text_global_asc_desc_chars0=None,
            name=None,
        ),)
        for _ in range(4)
    )
    """
    
    #print(text_objects)
    button = Button(
        shape=(200, 100),
        text="Goodbye",
        text_objects=None,
        anchor_rel_pos=(100, 100),
        anchor_type="topleft",
        screen_topleft_to_parent_topleft_offset=None,
        font_colors=((named_colors_def["white"], 0.5), (named_colors_def["yellow"], 1), (named_colors_def["blue"], 1), (named_colors_def["green"], 1)),
        text_borders_rel=((0.1, 0.2), (0, 0), 1, 0),
        text_anchor_types=(("midleft",), 0, 0, 0),
        fill_colors=(None, 0, (named_colors_def["red"], 0.2), (named_colors_def["red"], 0.5)),
        outline_widths=((1,), (2,), (3,), 1),
        outline_colors=((named_colors_def["black"], 1), (named_colors_def["blue"], 1), 1, 1),
        mouse_enabled=True,
        name=None,
    )
    #print(button.topleft)
    #print(button.shape)
    #button.shape = (300, 100)
    #button.text_borders_rel=((0, 0), (0.2, 0.2), 1, 0)
    #button.mouse_enabled = False
    
    
    screen_changed = True
    #print("\nhello\n")
    button.text = "change"
    button.shape = (500, 500)
    clock = pg.time.Clock()
    
    while True:
        quit, esc_pressed, event_loop_kwargs =\
                button.getRequiredInputs()
        #print(event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            break
        quit, running, chng, selected = button.eventLoop(check_axes=(0, 1),\
                **event_loop_kwargs)
        if quit or not running:
            pg.quit()
            break
        if chng: screen_changed = True
        if selected:
            print("button selected")
        if screen_changed:
            screen.blit(screen_cp, (0, 0))
            button.draw(screen)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return

def runExampleButtonGroup1() -> None:
    screen_size = (700, 700)
    framerate = 60
    pg.init()
    screen = pg.display.set_mode(screen_size)
    screen_color = named_colors_def["gray"]
    screen.fill(screen_color)
    pg.display.update(pg.Rect(0, 0, *screen_size))
    
    screen_cp = pg.Surface.copy(screen)
    
    """
    text_objects = tuple(
        (Text(
            text="Hi",
            max_shape=(200, 200),
            font=None,
            font_size=None,
            font_color=None,
            anchor_rel_pos0=None,
            anchor_type0=None,
            text_global_asc_desc_chars0=None,
            name=None,
        ),)
        for _ in range(4)
    )
    """

    button_group = ButtonGroup(
        button_shape=(200, 100),
        text_groups=None,
        text_borders_rel=((0.1, 0.2), (0, 0), 1, 0),
        font_colors=((named_colors_def["white"], 0.5), (named_colors_def["yellow"], 1), (named_colors_def["blue"], 1), (named_colors_def["green"], 1)),
        fill_colors=(None, 0, (named_colors_def["red"], 0.2), (named_colors_def["red"], 0.5)),
        outline_widths=((1,), (2,), (3,), 1),
        outline_colors=((named_colors_def["black"], 1), (named_colors_def["blue"], 1), 1, 1),
    )

    buttons = []
    #button_group.text_groups[0][0].max_font_sizes_given_widths_dict)
    #print(button_group.text_groups[0][0].heights_dict)
    buttons.append(
        button_group.addButton(
            text="adfsadfdsafdsafdsa",
            anchor_rel_pos=(350, 350),
            anchor_type="center",
            screen_topleft_to_parent_topleft_offset=(0, 0),
            text_anchor_types="center",
            mouse_enabled=True,
            name=None,
        )
    )
    
    #print(button_group.text_groups[0][0].max_font_sizes_given_widths_dict)
    #print(button_group.text_groups[0][0].heights_dict)
    
    buttons.append(
        button_group.addButton(
            text="Hello",
            anchor_rel_pos=(10, 10),
            anchor_type="topleft",
            screen_topleft_to_parent_topleft_offset=(0, 0),
            text_anchor_types="center",
            mouse_enabled=True,
            name=None,
        )
    )
    
    def drawButtons(screen: "pg.Surface", buttons: List[Button]) -> None:
        for button in buttons:
            button.draw(screen)
        return
    drawButtons(screen, buttons)
    screen_changed = True
    #print("hi")
    button_group.button_shape = (500, 200)

    #print(buttons[0].__dict__.get("_text_anchor_rel_positions", None))
    #print(buttons[0].__dict__.get("_button_surfs", None))
    
    #button_group.button_shape = (500, 300)
    #print(button_group.text_groups[0][0].max_font_sizes_given_widths_dict)
    #print(button_group.text_groups[0][0].heights_dict)
    buttons[0].text = "goodbye"
    #print(button_group.text_groups[0][0].max_font_sizes_given_widths_dict)
    #print(button_group.text_groups[0][0].heights_dict)
    
    clock = pg.time.Clock()
    
    while True:
        
        quit, esc_pressed, event_loop_kwargs =\
                buttons[0].getRequiredInputs()
        #print(event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            return
        for button in buttons:
            quit, running, chng, selected = button.eventLoop(check_axes=(0, 1),\
                **event_loop_kwargs)
            if quit or not running:
                pg.quit()
                break
            if selected:
                print(f"button {button.name} selected")
            if not chng: continue
            screen_changed = True
            #print(f"new slider value for {slider.name} = {val}")
        if screen_changed:
            screen.blit(screen_cp, (0, 0))
            #print("drawing buttons")
            drawButtons(screen, buttons)
            #print(buttons[0].__dict__.get("_text_anchor_rel_positions", None))
            #print(buttons[0].__dict__.get("_button_surfs", None))
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return


    #print(button.topleft)
    #print(button.shape)
    #button.shape = (300, 100)
    button.text_borders_rel=((0, 0), (0.2, 0.2), 1, 0)
    #button.mouse_enabled = False

def runExampleButtonGrid1() -> None:
    screen_size = (700, 700)
    framerate = 60
    pg.init()
    screen = pg.display.set_mode(screen_size)
    screen_color = named_colors_def["gray"]
    screen.fill(screen_color)
    pg.display.update(pg.Rect(0, 0, *screen_size))
    
    screen_cp = pg.Surface.copy(screen)

    button_text0 = [["Hello", "Hello", ",", "pog", "Log"], ["Hello", "Hello", "'", "now", "bye"]]# "Helloasdfsfdsafa", "Goodbye"]]
    grid_dims = len(button_text0), len(button_text0[0])
    button_text = []
    
    
    text_groups = tuple((TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None),) for _ in range(4))
    
    button_grid = ButtonGrid(
        grid_dims=grid_dims,
        shape=(500, 400),
        anchor_rel_pos=(100, 100),
        anchor_type="topleft",
        screen_topleft_to_parent_topleft_offset=(0, 0),
        button_gaps_rel_shape=(0.2, 0.2),
        text_groups=text_groups,
        font_colors=((named_colors_def["white"], 0.5), (named_colors_def["yellow"], 1), (named_colors_def["blue"], 1), (named_colors_def["green"], 1)),
        text_borders_rel=((0.1, 0.2), (0, 0), 1, 0),
        fill_colors=(None, (named_colors_def["red"], 0.2), (named_colors_def["red"], 0.5), 2),
        outline_widths=((1,), (2,), (3,), 1),
        outline_colors=((named_colors_def["black"], 1), (named_colors_def["blue"], 0.8), 1, 1),
        mouse_enabled=True,
        navkeys_enabled=True,
        navkey_cycle_delay_frame=(30, 10, 10, 10, 5),
    )

    for i1, text_col in enumerate(button_text0):
        align = "right" if i1 else "left"
        anchor_tup = ((f"mid{align}",), 0, ("center",), 2)
        setup_kwargs = {
            "text_anchor_types": anchor_tup,
        }
        #button_text.append([(text, anchor_tup) for text in text_row])
        for i2, txt in enumerate(text_col):
            setup_kwargs["grid_inds"] = (i1, i2)
            setup_kwargs["text"] = txt
            button_grid.setupButtonGridElement(**setup_kwargs)

    #print("hi1")
    #button_grid.button_shape = (100, 50)
    #print(button_grid.button_shape, button_grid.button_shape_fixed)
    #button_grid.anchor_type = "center"
    #button_grid.anchor_rel_pos = tuple(x / 2 for x in screen_size)
    #print(button_grid.button_shape_fixed)
    
    #button_grid.dims = (100, 100, 500, 800)
    
    screen_changed = True
    clock = pg.time.Clock()
    
    while True:
        quit, esc_pressed, event_loop_kwargs = button_grid.getRequiredInputs()
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            #sys.exit()
            return
        change = False
        chng, buttons_pressed = button_grid.eventLoop(check_axes=(0, 1), **event_loop_kwargs)[2:]
        if buttons_pressed:
            print(f"buttons pressed: {buttons_pressed}")
        if chng: change = True
        if change: screen_changed = True
        if screen_changed:
            screen.blit(screen_cp, (0, 0))
            button_grid.draw(screen)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return
    
    """
    button_text0 = [["Hello", "Hello", ",", "pog", "Log"], ["Hello", "Hello", "'", "now", "bye"]]# "Helloasdfsfdsafa", "Goodbye"]]
    button_text = []
    for i, text_row in enumerate(button_text0):
        align = "right" if i else "left"
        anchor_tup = ((f"mid{align}",), 0, ("center",), 2)
        button_text.append([(text, anchor_tup) for text in text_row])
    
    text_groups = tuple((TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None),) for _ in range(4))
    
    button_grid = ButtonGrid((500, 400),\
            button_text, text_groups, (100, 100),\
            anchor_type="topleft", screen_topleft_to_parent_topleft_offset=(0, 0),\
            button_gaps_rel_shape=(0.2, 0.2),\
            font_colors=((named_colors_def["white"], 0.5), (named_colors_def["yellow"], 1), (named_colors_def["blue"], 1), (named_colors_def["green"], 1)),\
            text_borders_rel=((0.1, 0.2), (0, 0), 1, 0),\
            fill_colors=(None, (named_colors_def["red"], 0.2), (named_colors_def["red"], 0.5), 2),\
            outline_widths=((1,), (2,), (3,), 1),\
            outline_colors=((named_colors_def["black"], 1), (named_colors_def["blue"], 0.8), 1, 1),\
            mouse_enabled=True, navkeys_enabled=True,\
            navkeys=None, navkey_cycle_delay_frame=(30, 10, 10, 10, 5))
    #print("hi1")
    #button_grid.button_shape = (100, 50)
    #print(button_grid.button_shape, button_grid.button_shape_fixed)
    button_grid.anchor_type = "center"
    button_grid.anchor_rel_pos = tuple(x / 2 for x in screen_size)
    #print(button_grid.button_shape_fixed)
    
    #button_grid.dims = (100, 100, 500, 800)
    
    screen_changed = True
    clock = pg.time.Clock()
    
    while True:
        quit, esc_pressed, event_loop_kwargs = button_grid.getRequiredInputs()
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            #sys.exit()
            return
        change = False
        chng, buttons_pressed = button_grid.eventLoop(check_axes=(0, 1), **event_loop_kwargs)[2:]
        if buttons_pressed:
            print(f"buttons pressed: {buttons_pressed}")
        if chng: change = True
        if change: screen_changed = True
        if screen_changed:
            screen.blit(screen_cp, (0, 0))
            button_grid.draw(screen)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return
    """

def runExampleSlider1() -> None:
    screen_size = (600, 600)
    framerate = 5
    pg.init()
    screen = pg.display.set_mode(screen_size)
    screenColor = named_colors_def["white"]
    screen.fill(screenColor)
    pg.display.update(pg.Rect(0, 0, *screen_size))
    screen_cp = pg.Surface.copy(screen)
    """
    shape: Tuple[Real],
            anchor_rel_pos: Tuple[Real], anchor_type: str="topleft",
            demarc_numbers_text_group: Optional["Text"]=None,
            surf_screen_topleft_to_parent_topleft_offset: Tuple[Real]=(0, 0),
            val_range=(0, 100),
            demarc_intervals=(20, 10, 5), demarc_start_val=0, increment=None,
            increment_start=None, track_color=None, thumb_color=None, thumb_radius_rel=1,
            default_val=None, name=None,
            demarc_line_lens_rel=None, demarc_numbers_dp=0, demarc_number_size_rel=2,
            demarc_numbers_color=None, demarc_line_colors=None,
            thumb_outline_color=None, mouse_enabled: bool=True)
    """
    slider = Slider(
        shape=(500, 150),
        anchor_rel_pos=(300, 200),
        val_range=(0, 100),
        increment_start=15,
        increment=5,
        anchor_type="center",
        screen_topleft_to_parent_topleft_offset=None,
        init_val=None,
        demarc_numbers_text_group=None,
        demarc_numbers_dp=None,
        thumb_radius_rel=1,
        demarc_line_lens_rel=None,
        demarc_intervals=(20, 10, 5),
        demarc_start_val=None,#35,
        demarc_numbers_max_height_rel=1,
        track_color=(named_colors_def["gray"], 1),
        thumb_color=(named_colors_def["silver"], 1),
        demarc_numbers_color=None,
        demarc_line_colors=None,
        thumb_outline_color=None,
        mouse_enabled=True,
        name=None,
    )
    #slider2 = slider
    #print(f"reference count = {sys.getrefcount(slider)}")
    #print(gc.get_referrers(slider))
    """
    slider = Slider((500, 70), (300, 200), anchor_type="center",
            demarc_numbers_text_group=None,
            screen_topleft_to_parent_topleft_offset=(0, 0), val_range=(0, 100),
            demarc_intervals=(20, 10, 5), demarc_start_val=35,
            increment=10, increment_start=15, track_color=(named_colors_def["gray"], 1),
            thumb_color=(named_colors_def["silver"], 1), thumb_radius_rel=1, init_val=None,
            name=None, demarc_line_lens_rel=None, demarc_numbers_dp=0,
            demarc_numbers_max_height_rel=2, demarc_numbers_color=None,
            demarc_line_colors=None, thumb_outline_color=None,
            mouse_enabled=True)
    """
    address = id(slider)
    slider.draw(screen)
    screen_changed = True

    #print(f"reference count = {ctypes.c_long.from_address(address)}")
    slider.shape = (400, 70)
    #print(slider.is_default_set)
    #print(slider.track_color)
    #print(slider.demarc_line_colors)
    slider.track_color = (named_colors_def["black"], 0.5)
    #print(slider.is_default_set)
    #print(slider.track_color)
    #print(slider.__dict__["_demarc_line_colors"])
    #print(slider.demarc_line_colors)
    #print(slider.__dict__.keys())
    #print(slider.mouse_enabled)
    #print(slider.mouse_enablement)
    
    
    
    clock = pg.time.Clock()
    
    while True:
        quit, esc_pressed, event_loop_kwargs =\
                slider.getRequiredInputs()
        #print(event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            break
        quit, running, chng, val = slider.eventLoop(check_axes=(0, 1),\
                **event_loop_kwargs)
        if quit or not running:
            pg.quit()
            break
        if chng: screen_changed = True
        #print(f"redraw required = {screen_changed}")
        if screen_changed:
            print(f"new slider value = {val}")
            screen.blit(screen_cp, (0, 0))
            slider.draw(screen)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    
    #print(f"reference count = {sys.getrefcount(slider)}")
    #print(gc.get_referrers(slider))
    #asdfasf = []
    #print(sys.getrefcount(asdfasf))
    #print(gc.get_referrers(asdfasf))
    #print(Slider.__dict__.keys())
    #del slider
    #print("hello")
    #print(sys.getrefcount(slider))
    #print(f"reference count = {ctypes.c_long.from_address(address)}")
    return address

def runExampleSliderGroup1() -> None:
    screen_size = (600, 600)
    framerate = 5
    pg.init()
    screen = pg.display.set_mode(screen_size)
    screenColor = named_colors_def["white"]
    screen.fill(screenColor)
    pg.display.update(pg.Rect(0, 0, *screen_size))
    screen_cp = pg.Surface.copy(screen)
    
    slider_group = SliderGroup(
        slider_shape=(500, 150),
        demarc_numbers_text_group=None,
        thumb_radius_rel=1,
        demarc_line_lens_rel=None,
        demarc_numbers_max_height_rel=1,
        track_color=(named_colors_def["gray"], 1),
        thumb_color=(named_colors_def["silver"], 1),
        demarc_numbers_color=None,
        demarc_line_colors=None,
        thumb_outline_color=None,
    )

    sliders = []

    sliders.append(
        slider_group.addSlider(
            anchor_rel_pos=(300, 400),
            val_range=(0, 50),
            increment_start=15,
            increment=5,
            anchor_type="center",
            screen_topleft_to_parent_topleft_offset=None,
            init_val=None,
            demarc_numbers_dp=0,
            demarc_intervals=(5,),
            demarc_start_val=1,
            mouse_enabled=True,
            name=None,
        )
    )
    
    
    sliders.append(
        slider_group.addSlider(
            anchor_rel_pos=(300, 200),
            val_range=(0, 100),
            increment_start=15,
            increment=0,
            anchor_type="center",
            screen_topleft_to_parent_topleft_offset=None,
            init_val=None,
            demarc_numbers_dp=None,
            demarc_intervals=(20, 10, 5),
            demarc_start_val=None,
            mouse_enabled=True,
            name=None,
        )
    )
    
    #print("hello3")
    #print(type(sliders[0]).mro())
    #print(sliders[0].track_shape)
    #print(slider_group.is_default_set)
    #print(slider_group.demarc_line_colors)
    #slider_group.slider_shape = (600, 600)
    
    def drawSliders(screen: "pg.Surface", sliders: List["Slider"]) -> None:
        for slider in sliders:
            slider.draw(screen)
        return
    """
    slider = Slider((500, 70), (300, 200), anchor_type="center",
            demarc_numbers_text_group=None,
            screen_topleft_to_parent_topleft_offset=(0, 0), val_range=(0, 100),
            demarc_intervals=(20, 10, 5), demarc_start_val=35,
            increment=10, increment_start=15, track_color=(named_colors_def["gray"], 1),
            thumb_color=(named_colors_def["silver"], 1), thumb_radius_rel=1, init_val=None,
            name=None, demarc_line_lens_rel=None, demarc_numbers_dp=0,
            demarc_numbers_max_height_rel=2, demarc_numbers_color=None,
            demarc_line_colors=None, thumb_outline_color=None,
            mouse_enabled=True)
    """
    drawSliders(screen, sliders)
    #sliders[0].shape = (300, 70)
    #slider_group.slider_shape = (600, 600)
    #print("hello")
    
    screen_changed = True
    #print(slider.__dict__.keys())
    #print(slider.mouse_enabled)
    #print(slider.mouse_enablement)
    #print(slider_group.is_default_set)
    #print(slider_group.demarc_line_colors)
    #print(sliders[0].demarc_line_colors)
    slider_group.track_color = (named_colors_def["black"], 0.5)
    #print(f"changing the slider group shape")
    slider_group.slider_shape = (300, 200)
    
    clock = pg.time.Clock()
    
    while True:
        
        quit, esc_pressed, event_loop_kwargs =\
                sliders[0].getRequiredInputs()
        #print(event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            return
        for slider in sliders:
            quit, running, chng, val = slider.eventLoop(check_axes=(0, 1),\
                **event_loop_kwargs)
            if quit or not running:
                pg.quit()
                break
            if not chng: continue
            screen_changed = True
            print(f"new slider value for {slider.name} = {val}")
        #print(f"redraw required = {screen_changed}")
        if screen_changed:
            screen.blit(screen_cp, (0, 0))
            drawSliders(screen, sliders)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return

def runExampleSliderPlus1() -> None:
    screen_size = (600, 600)
    framerate = 5
    pg.init()
    screen = pg.display.set_mode(screen_size)
    screenColor = named_colors_def["white"]
    screen.fill(screenColor)
    pg.display.update(pg.Rect(0, 0, *screen_size))
    screen_cp = pg.Surface.copy(screen)
    """
    shape: Tuple[Real],
            anchor_rel_pos: Tuple[Real], anchor_type: str="topleft",
            demarc_numbers_text_group: Optional["Text"]=None,
            surf_screen_topleft_to_parent_topleft_offset: Tuple[Real]=(0, 0),
            val_range=(0, 100),
            demarc_intervals=(20, 10, 5), demarc_start_val=0, increment=None,
            increment_start=None, track_color=None, thumb_color=None, thumb_radius_rel=1,
            default_val=None, name=None,
            demarc_line_lens_rel=None, demarc_numbers_dp=0, demarc_number_size_rel=2,
            demarc_numbers_color=None, demarc_line_colors=None,
            thumb_outline_color=None, mouse_enabled: bool=True)
    """
    slider_plus = SliderPlus(
        title="Slider 1",
        shape=(800, 100),
        anchor_rel_pos=(300, 200),
        val_range=(0, 100),
        increment_start=15,
        increment=None,
        anchor_type="center",
        screen_topleft_to_parent_topleft_offset=None,
        init_val=None,
        demarc_numbers_text_group=None,
        demarc_numbers_dp=2,
        thumb_radius_rel=1,
        demarc_line_lens_rel=None,
        demarc_intervals=(20, 10, 5),
        demarc_start_val=None,#35,
        demarc_numbers_max_height_rel=1,
        track_color=(named_colors_def["gray"], 1),
        thumb_color=(named_colors_def["silver"], 1),
        demarc_numbers_color=None,
        demarc_line_colors=None,
        thumb_outline_color=None,
        mouse_enabled=True,
        
        slider_shape_rel=(0.7, 0.5),
        slider_borders_rel=(0.05, 0.03),
        title_text_group=None,
        title_anchor_type="topleft",
        title_color=None,
        val_text_group=None,
        val_text_anchor_type="midright",
        val_text_color=(named_colors_def["black"], 1),
        val_text_dp=2,
        
        name=None,
    )
    address = id(slider_plus)
    slider_plus.draw(screen)
    screen_changed = True
    #print(slider_plus.sub_component_dict)
    #print(slider_plus.slider)
    #print(f"mouse enabled = {slider_plus.slider.mouse_enabled}")
    #print(f"mouse enablement = {slider_plus.slider.mouse_enablement}")
    #print(slider_plus.slider.slider_ranges_screen)
    #print("######################### changing shape")
    #print(f"original title shape = {slider_plus.title_shape}")
    #ttg = slider_plus.title_text_group
    #tto = slider_plus.title_text_obj
    #print("\nhello\n")
    
    #slider_plus.slider_borders_rel = (0, 0)

    #print(slider_plus.shape)
    #print(ttg.max_font_size_given_heights)
    #print(ttg.max_font_size_given_widths)
    #print(ttg.max_font_sizes_given_widths_dict)
    #print(tto.max_shape)
    #print(tto.max_shape_actual)
    #print(tto.max_font_size_given_width)
    #slider_plus.shape = (600, 300)
    #print(slider_plus.shape)
    #print(ttg.max_font_size_given_heights)
    #print(ttg.max_font_size_given_widths)
    #print(ttg.max_font_sizes_given_widths_dict)
    #print(tto.max_shape)
    #print(tto.max_shape_actual)
    #print(tto.max_font_size_given_width)
    
    #print(f"new title shape = {slider_plus.title_shape}")

    slider_plus.track_color = (named_colors_def["black"], 0.2)
    slider_plus.shape = (500, 100)
    
    clock = pg.time.Clock()
    
    while True:
        quit, esc_pressed, event_loop_kwargs =\
                slider_plus.getRequiredInputs()
        #print(event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            break
        quit, running, chng, val = slider_plus.eventLoop(check_axes=(0, 1),\
                **event_loop_kwargs)
        if quit or not running:
            pg.quit()
            break
        if chng: screen_changed = True
        #print(f"redraw required = {screen_changed}")
        if screen_changed:
            print(f"new slider value = {val}")
            screen.blit(screen_cp, (0, 0))
            slider_plus.draw(screen)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    
    #print(f"reference count = {sys.getrefcount(slider)}")
    #print(gc.get_referrers(slider))
    #asdfasf = []
    #print(sys.getrefcount(asdfasf))
    #print(gc.get_referrers(asdfasf))
    #print(Slider.__dict__.keys())
    #del slider
    #print("hello")
    #print(sys.getrefcount(slider))
    #print(f"reference count = {ctypes.c_long.from_address(address)}")
    return address

def runExampleSliderPlusGroup1() -> None:
    screen_size = (600, 600)
    framerate = 5
    pg.init()
    screen = pg.display.set_mode(screen_size)
    screenColor = named_colors_def["white"]
    screen.fill(screenColor)
    pg.display.update(pg.Rect(0, 0, *screen_size))
    screen_cp = pg.Surface.copy(screen)

    slider_group = SliderPlusGroup(
        shape=(200, 70),
        demarc_numbers_text_group=None,
        thumb_radius_rel=1,
        demarc_line_lens_rel=None,
        demarc_numbers_max_height_rel=1,
        track_color=(named_colors_def["gray"], 1),
        thumb_color=(named_colors_def["silver"], 1),
        demarc_numbers_color=None,
        demarc_line_colors=None,
        thumb_outline_color=None,
        #mouse_enabled=True,
        slider_shape_rel=(.7, .7),
        slider_borders_rel=(0, 0),
        title_text_group=None,
        title_anchor_type="topleft",
        title_color=(named_colors_def["black"], 1.),
        val_text_group=None,
        val_text_anchor_type="midright",
        val_text_color=(named_colors_def["black"], 1.),
    )

    sliders = []
    
    
    sliders.append(
        slider_group.addSliderPlus(
            title="Slider 1",
            anchor_rel_pos=(50, 50),
            val_range=(0, 200),
            increment_start=15,
            increment=0,
            anchor_type="topleft",
            screen_topleft_to_parent_topleft_offset=None,
            init_val=None,
            demarc_numbers_dp=0,
            demarc_intervals=(50, 10, 5),
            demarc_start_val=None,
            val_text_dp=0,
            mouse_enabled=True,
            name=None,
        )
    )
    
    sliders.append(
        slider_group.addSliderPlus(
            title="Slider 2",
            anchor_rel_pos=(300, 400),
            val_range=(0, 50),
            increment_start=15,
            increment=5,
            anchor_type="center",
            screen_topleft_to_parent_topleft_offset=None,
            init_val=None,
            demarc_numbers_dp=2,
            demarc_intervals=(10,),
            demarc_start_val=1,
            val_text_dp=2,
            mouse_enabled=True,
            name=None,
        )
    )
    
    #print("hello3")
    #print(type(sliders[0]).mro())
    #print(sliders[0].track_shape)
    #print(slider_group.is_default_set)
    #print(slider_group.demarc_line_colors)
    #slider_group.shape = (300, 300)
    #slider_group.slider_shape_rel = (.5, .4)
    
    
    def drawSliders(screen: "pg.Surface", sliders: List["SliderPlus"]) -> None:
        for slider in sliders:
            slider.draw(screen)
        return
    """
    slider = Slider((500, 70), (300, 200), anchor_type="center",
            demarc_numbers_text_group=None,
            screen_topleft_to_parent_topleft_offset=(0, 0), val_range=(0, 100),
            demarc_intervals=(20, 10, 5), demarc_start_val=35,
            increment=10, increment_start=15, track_color=(named_colors_def["gray"], 1),
            thumb_color=(named_colors_def["silver"], 1), thumb_radius_rel=1, init_val=None,
            name=None, demarc_line_lens_rel=None, demarc_numbers_dp=0,
            demarc_numbers_max_height_rel=2, demarc_numbers_color=None,
            demarc_line_colors=None, thumb_outline_color=None,
            mouse_enabled=True)
    """
    drawSliders(screen, sliders)
    #sliders[0].shape = (300, 70)
    #slider_group.slider_shape = (600, 600)
    #print("hello")
    #slider_group.track_color = (named_colors_def["black"], 0.5)
    screen_changed = True
    #print(slider.__dict__.keys())
    #print(slider.mouse_enabled)
    #print(slider.mouse_enablement)
    #print(slider_group.is_default_set)
    #print(slider_group.demarc_line_colors)
    #print(sliders[0].demarc_line_colors)
    #slider_group.shape = (1200, 600)
    #slider_group.shape = (500, 100)
    #slider_group.track_color = (named_colors_def["black"], 1)
    #slider_group.val_text_color = (named_colors_def["white"], 1)
    #slider_group.shape = (300, 200)
    #slider_group.slider_borders = (0, 0)
    slider_group.title_color = (named_colors_def["silver"], .7)
    slider_group.val_text_color = (named_colors_def["gray"], .7)

    #print("Changing slider group shape")
    slider_group.shape = (500, 200)
    
    clock = pg.time.Clock()
    
    while True:
        
        quit, esc_pressed, event_loop_kwargs =\
                sliders[0].getRequiredInputs()
        #print(event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            return
        for slider in sliders:
            quit, running, chng, val = slider.eventLoop(check_axes=(0, 1),\
                **event_loop_kwargs)
            if quit or not running:
                pg.quit()
                break
            if not chng: continue
            screen_changed = True
            #print(f"new slider value for {slider.name} = {val}")
        #print(f"redraw required = {screen_changed}")
        if screen_changed:
            screen.blit(screen_cp, (0, 0))
            drawSliders(screen, sliders)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return

def runExampleSliderPlusGrid1() -> None:
    screen_size = (600, 600)
    framerate = 5
    pg.init()
    screen = pg.display.set_mode(screen_size)
    screenColor = named_colors_def["white"]
    screen.fill(screenColor)
    pg.display.update(pg.Rect(0, 0, *screen_size))
    screen_cp = pg.Surface.copy(screen)

    grid_dims = (1, 3)

    slider_grid = SliderPlusGrid(
        grid_dims=grid_dims,
        shape=(400, 400),
        slider_plus_gaps_rel_shape=(0.1, 0.1),
        anchor_rel_pos=(300, 300),
        anchor_type="center",
        screen_topleft_to_parent_topleft_offset=None,
        demarc_numbers_text_group=None,
        thumb_radius_rel=1,
        demarc_line_lens_rel=None,
        demarc_numbers_max_height_rel=1,
        track_color=(named_colors_def["gray"], 1),
        thumb_color=(named_colors_def["silver"], 1),
        demarc_numbers_color=None,
        demarc_line_colors=None,
        thumb_outline_color=None,
        slider_shape_rel=(.7, .7),
        slider_borders_rel=(0, 0),
        title_text_group=None,
        title_anchor_type="topleft",
        title_color=(named_colors_def["black"], 1.),
        val_text_group=None,
        val_text_anchor_type="midright",
        val_text_color=(named_colors_def["black"], 1.),
        mouse_enabled=True,
    )
    
    slider_grid.setupSliderPlusGridElement(
        grid_inds=(0, 1),
        title="Slider 1",
        val_range=(0, 100),
        increment_start=15,
        increment=0,
        init_val=None,
        demarc_numbers_dp=None,
        demarc_intervals=(20, 10, 5),
        demarc_start_val=None,
        val_text_dp=0,
        name=None,
    )
    
    slider_grid.setupSliderPlusGridElement(
        grid_inds=(0, 0),
        title="Slider 2asdfsadfsad",
        val_range=(0, 200),
        increment_start=15,
        increment=0,
        init_val=None,
        demarc_numbers_dp=None,
        demarc_intervals=(50, 25),
        demarc_start_val=None,
        val_text_dp=2,
        name=None,
    )
    """
    slider_grid.setupSliderPlusGridElement(
        grid_inds=(0, 2),
        title="Slider 1",
        val_range=(0, 100),
        increment_start=15,
        increment=0,
        init_val=None,
        demarc_numbers_dp=None,
        demarc_intervals=(20, 10, 5),
        demarc_start_val=None,
        val_text_dp=0,
        name=None,
    )
    """
    slider_grid.setupSliderPlusGridElement(
        grid_inds=(0, 2),
        title="Slider 2asdfsadfsad",
        val_range=(0, 200),
        increment_start=15,
        increment=0,
        init_val=None,
        demarc_numbers_dp=None,
        demarc_intervals=(50, 25),
        demarc_start_val=None,
        val_text_dp=2,
        name=None,
    )
    
    """
    sliders.append(
        slider_group.addSliderPlus(
            title="Slider 2",
            anchor_rel_pos=(300, 400),
            val_range=(0, 100),
            increment_start=15,
            increment=5,
            anchor_type="center",
            screen_topleft_to_parent_topleft_offset=None,
            init_val=None,
            demarc_numbers_dp=3,
            demarc_intervals=(20,),
            demarc_start_val=1,
            val_text_dp=0,
            name=None,
        )
    )
    """
    #print("hello3")
    #print(type(sliders[0]).mro())
    #print(sliders[0].track_shape)
    #print(slider_group.is_default_set)
    #print(slider_group.demarc_line_colors)
    #slider_group.shape = (300, 300)
    #slider_group.slider_shape_rel = (.5, .4)
    #slider_group.title_color = (named_colors_def["silver"], .7)
    #slider_group.val_text_color = (named_colors_def["white"], .7)
    
    #def drawSliders(screen: "pg.Surface", sliders: List["SliderPlus"]) -> None:
    #    for slider in sliders:
    #        slider.draw(screen)
    #    return
    """
    slider = Slider((500, 70), (300, 200), anchor_type="center",
            demarc_numbers_text_group=None,
            screen_topleft_to_parent_topleft_offset=(0, 0), val_range=(0, 100),
            demarc_intervals=(20, 10, 5), demarc_start_val=35,
            increment=10, increment_start=15, track_color=(named_colors_def["gray"], 1),
            thumb_color=(named_colors_def["silver"], 1), thumb_radius_rel=1, init_val=None,
            name=None, demarc_line_lens_rel=None, demarc_numbers_dp=0,
            demarc_numbers_max_height_rel=2, demarc_numbers_color=None,
            demarc_line_colors=None, thumb_outline_color=None,
            mouse_enabled=True)
    """
    slider_grid.draw(screen)
    #sliders[0].shape = (300, 70)
    #slider_group.slider_shape = (600, 600)
    #print("hello")
    #slider_group.track_color = (named_colors_def["black"], 0.5)
    screen_changed = True
    #print(slider.__dict__.keys())
    #print(slider.mouse_enabled)
    #print(slider.mouse_enablement)
    #print(slider_group.is_default_set)
    #print(slider_group.demarc_line_colors)
    #print(sliders[0].demarc_line_colors)
    #slider_group.shape = (1200, 600)
    #slider_group.shape = (500, 100)
    #slider_group.track_color = (named_colors_def["black"], 1)
    #slider_group.val_text_color = (named_colors_def["white"], 1)
    #slider_group.shape = (300, 200)
    #slider_group.slider_borders = (0, 0)
    #print("changing slider grid shape")
    slider_grid.shape = (500, 600)
    
    clock = pg.time.Clock()
    
    while True:
        #print(slider_grid.mouse_enabled)
        quit, esc_pressed, event_loop_kwargs =\
                slider_grid.getRequiredInputs()
        
        #print(event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            return
        quit, running, chng, val = slider_grid.eventLoop(check_axes=(0, 1),\
                **event_loop_kwargs)
        
        if quit or not running:
            pg.quit()
            break
        #print(f"redraw required = {screen_changed}")
        if chng: screen_changed = True
        if screen_changed:
            screen.blit(screen_cp, (0, 0))
            #print(f"drawing slider grid")
            slider_grid.draw(screen)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return

"""
def runExampleSliders1() -> None:
    screen_size = (600, 600)
    framerate = 60
    pg.init()
    screen = pg.display.set_mode(screen_size)
    screenColor = (0, 0, 0)
    screen.fill(screenColor)
    pg.display.update(pg.Rect(0, 0, *screen_size))
    
    screen_cp = pg.Surface.copy(screen)
    slider_battery = SliderPlusVerticalBattery(screen, 50, 50, 500, 400, demark_colors=((255,0,0), (0, 255, 0)), slider_gap_rel=0.3, number_size_rel=1.5)
    slider_battery.addSliderPlus("discrete1", val_range=(0, 100),
            demark_intervals=(20, 10, 5), demark_start_val=0,
            increment=2, default_val=30, numbers_dp=0)
    slider_battery.addSliderPlus("discrete2", val_range=(5, 100),
            demark_intervals=(20, 10, 5), demark_start_val=0,
            increment=2, increment_start=0, default_val=0, numbers_dp=0)
    slider_battery.addSliderPlus("continuous", val_range=(0, 100),
            demark_intervals=(20, 10, 5), demark_start_val=0,
            increment=None, default_val=10, numbers_dp=1)
    screen_changed = True
    clock = pg.time.Clock()
    
    while True:
        mouse_clicked = False
        for event in pg.event.get():
            if event.type == QUIT:
                pg.quit()
                #sys.exit()
                return
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pg.quit()
                    sys.exit()
            elif event.type == pg.MOUSEBUTTONDOWN:
                mouse_clicked = True
        change, vals = slider_battery.event_loop(mouse_clicked=mouse_clicked)
        if change: screen_changed = True
        if not screen_changed: continue
        screen.blit(screen_cp, (0, 0))
        slider_battery.draw()
        pg.display.flip()
        screen_changed = False
    return
"""

def runExampleMenuOverlayBase1() -> None:
    screen_shape = (700, 700)
    framerate = 30
    pg.init()
    screen = pg.display.set_mode(screen_shape)
    screen_color = named_colors_def["gray"]
    screen.fill(screen_color)
    pg.display.update(pg.Rect(0, 0, *screen_shape))
    
    screen_cp = pg.Surface.copy(screen)
    
    exit_press_keys = None
    exit_release_keys = {pg.K_p}
    
    menu_overlay = MenuOverlayBase(
        shape=screen_shape,
        framerate=framerate,
        overlay_color=(named_colors_def["yellow"], 0.3),
        mouse_enabled=True,
        navkeys_enabled=True,
        navkeys=(({K_LEFT}, {K_RIGHT}), ({K_UP}, {K_DOWN})),
        #exit_press_keys=exit_press_keys,
        #exit_release_keys=exit_release_keys,
    )
    
    text_group = TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None)
    anchor_type = "centre"
    font_color = (named_colors_def["black"], 1)
    text_list = [
        ({"text": "Hello", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 1), (0.2, 0.5))),
        ({"text": "Goodbye", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.4, 0.5))),
        ({"text": "name", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.6, 0.5))),
        ({"text": ",", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.7, 0.5))),
        ({"text": "'", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.8, 0.5))),
    ]
    #print(f"menu text group: {text_group}")
    #text_list = [
    #    (("Hello", text_color), ((0.2, 0.2), (0.2, 0.1), anchor_type)),
    #    (("Goodbye", text_color), ((0.2, 0.2), (0.4, 0.1), anchor_type)),
    #    (("name", text_color), ((0.2, 0.2), (0.6, 0.1), anchor_type)),
    #    ((",", text_color), ((0.2, 0.2), (0.7, 0.1), anchor_type)),
    #    (("'", None, text_color), ((0.2, 0.2), (0.8, 0.1), anchor_type)),
    #]
    
    add_text_list = [x[0] for x in text_list]
    text_objs = text_group.addTextObjects(add_text_list)
    #print("added menu text objects to menu")
    for text_obj, (_, pos_tup) in zip(text_objs, text_list):
        max_shape_rel, anchor_rel_pos_rel = pos_tup
        menu_overlay.addText(text_obj, max_shape_rel, anchor_rel_pos_rel)
    #print("\nhello\n")
    #print(text_group.max_font_sizes_given_widths_dict)
    #print(text_group.heights_dict)
    #print(text_group)
    screen_changed = True
    clock = pg.time.Clock()
    
    while True:
        #print("hello")
        quit, esc_pressed, event_loop_kwargs = menu_overlay.getRequiredInputs()
        #print(quit, esc_pressed, event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            return
        change = False
        quit, running, chng, actions = menu_overlay.eventLoop(check_axes=(0, 1), **event_loop_kwargs)
        if quit or not running:
            pg.quit()
            return
        for action in actions:
            action()
        if chng: change = True
        if change: screen_changed = True
        if screen_changed:
            screen.blit(screen_cp, (0, 0))
            menu_overlay.draw(screen)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return

def runExampleButtonMenuOverlay1() -> None:
    screen_shape = (700, 700)
    framerate = 30
    pg.init()
    screen = pg.display.set_mode(screen_shape)
    screen_color = named_colors_def["gray"]
    screen.fill(screen_color)
    pg.display.update(pg.Rect(0, 0, *screen_shape))
    
    screen_cp = pg.Surface.copy(screen)
    
    exit_press_keys = None
    exit_release_keys = {pg.K_p}
    
    #button_text = [["Hello", "Hello", "Hello", "Hello", "Goodbye"], ["Hello", "Hello", "Hello", "Hello", "Goodbye"]]
    button_text = [["Hello", "Hello"], ["Hello", "Hello"], ["Hello", "Hello"], ["Hello", "Hello"], ["Goodbye", "Goodbye"]]
    anchor_type = "center"
    
    button_text_anchortype_and_actions = []
    for i2, row in enumerate(button_text):
        button_text_anchortype_and_actions.append([])
        for i1, text in enumerate(row):
            action = functools.partial(print, f"selected button ({i1}, {i2})")
            button_text_anchortype_and_actions[-1].append((text, ((anchor_type,), 0, 0, 0), action))
    
    menu_overlay = ButtonMenuOverlay(
        shape=screen_shape,
        framerate=framerate,
        overlay_color=(named_colors_def["yellow"], 0.3),
        mouse_enabled=True,
        navkeys_enabled=True,
        navkeys=(({K_LEFT}, {K_RIGHT}), ({K_UP}, {K_DOWN})),
        navkey_cycle_delay_s=(.4, 0.2, 0.1, 0.05),
        #exit_press_keys=exit_press_keys,
        #exit_release_keys=exit_release_keys,
    )
    
    
    #button_text_groups = tuple((TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None),) for _ in range(4))
    menu_overlay.setupButtonGrid(
        anchor_pos_norm=(0.5, 0.2),
        anchor_type="midtop",
        button_grid_max_shape_norm=(0.6, 0.3),
        wh_ratio_range=(0.6, 2),
        button_text_anchortype_and_actions=button_text_anchortype_and_actions,
        text_groups=None,#button_text_groups,
        button_gaps_rel_shape=(0.2, 0.2),
        font_colors=((named_colors_def["white"], 0.5), (named_colors_def["yellow"], 1), (named_colors_def["blue"], 1), (named_colors_def["green"], 1)),
        text_borders_rel=((0.2, 0.2), (0, 0), 1, 0),
        fill_colors=(None, (named_colors_def["red"], 0.2), (named_colors_def["red"], 0.5), 2),
        outline_widths=((1,), (2,), (3,), 1),
        outline_colors=((named_colors_def["black"], 1), (named_colors_def["blue"], 1), 1, 1)
    )

    #print("\nhello\n")
    
    text_group = TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None)
    anchor_type = "centre"
    font_color = (named_colors_def["black"], 1)
    text_list = [
        ({"text": "Hello", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 1), (0.2, 0.1))),
        ({"text": "Goodbye", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.4, 0.1))),
        ({"text": "name", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.6, 0.1))),
        ({"text": ",", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.7, 0.1))),
        ({"text": "'", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.8, 0.1))),
    ]
    #print(f"menu text group: {text_group}")
    #text_list = [
    #    (("Hello", text_color), ((0.2, 0.2), (0.2, 0.1), anchor_type)),
    #    (("Goodbye", text_color), ((0.2, 0.2), (0.4, 0.1), anchor_type)),
    #    (("name", text_color), ((0.2, 0.2), (0.6, 0.1), anchor_type)),
    #    ((",", text_color), ((0.2, 0.2), (0.7, 0.1), anchor_type)),
    #    (("'", None, text_color), ((0.2, 0.2), (0.8, 0.1), anchor_type)),
    #]
    
    add_text_list = [x[0] for x in text_list]
    text_objs = text_group.addTextObjects(add_text_list)
    #print("added menu text objects to menu")
    for text_obj, (_, pos_tup) in zip(text_objs, text_list):
        max_shape_rel, anchor_rel_pos_rel = pos_tup
        menu_overlay.addText(text_obj, max_shape_rel,\
                anchor_rel_pos_rel)
    
    """
    max_height_rel = 0.2
    anchor_type = "bottomright"
    text_color = (named_colors_def["black"], 1)
    text_list = [
        ("Hello", (0.2, 0.1), anchor_type, 0.2, text_color),
        ("Goodbye", (0.4, 0.1), anchor_type, 0.2, text_color),
        ("name", (0.6, 0.1), anchor_type, 0.2, text_color),
        (",", (0.7, 0.1), anchor_type, 0.2, text_color),
        ("'", (0.8, 0.1), anchor_type, 0.2, text_color),
    ]
    menu_overlay.addTextGroup(text_list, max_height_rel, font=None,\
            font_size=None)
    """
    screen_changed = True
    clock = pg.time.Clock()
    
    while True:
        #print("hello")
        quit, esc_pressed, event_loop_kwargs = menu_overlay.getRequiredInputs()
        #print(f"event_loop_kwargs = {event_loop_kwargs}")
        #print(quit, esc_pressed, event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            return
        change = False
        quit, running, chng, actions = menu_overlay.eventLoop(check_axes=(0, 1), **event_loop_kwargs)
        if quit or not running:
            pg.quit()
            return
        for action in actions:
            action()
        if chng: change = True
        if change: screen_changed = True
        #print(f"screen changed = {screen_changed}")
        if screen_changed:
            #print("screen changed")
            screen.blit(screen_cp, (0, 0))
            menu_overlay.draw(screen)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return
    """
    while True:
        quit, running, events, keys_pressed, mouse_pos, mouse_pressed\
                = menu_overlay.getRequiredInputs()
        if quit or not running:
            pg.quit()
            sys.exit()
        change = False
        chng, action = menu_overlay.eventLoop(mouse_pos=mouse_pos, events=events, keys_pressed=keys_pressed, mouse_pressed=mouse_pressed, check_axes=(0, 1))
        if action is not None:
            action()
        if chng: change = True
        if change: screen_changed = True
        if screen_changed:
            screen.blit(screen_cp, (0, 0))
            menu_overlay.draw()
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    """
def runExampleSliderAndButtonMenuOverlay1() -> None:
    screen_shape = (700, 700)
    framerate = 30
    pg.init()
    screen = pg.display.set_mode(screen_shape)
    screen_color = named_colors_def["gray"]
    screen.fill(screen_color)
    pg.display.update(pg.Rect(0, 0, *screen_shape))
    
    screen_cp = pg.Surface.copy(screen)
    
    exit_press_keys = None
    exit_release_keys = {pg.K_p}

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
        "val_range": (1, 20),
        "increment_start": 0,
        "increment": 1,
        "init_val": 1,
        "demarc_numbers_dp": 0,
        "demarc_intervals": (4,),
        "demarc_start_val": 0,
        "val_text_dp": 0,
    }])
    
    #button_text = [["Hello", "Hello", "Hello", "Hello", "Goodbye"], ["Hello", "Hello", "Hello", "Hello", "Goodbye"]]
    button_text = [["Apply", "Reset", "Return"]]
    anchor_type = "center"
    
    button_text_anchortype_and_actions = []
    for i2, row in enumerate(button_text):
        button_text_anchortype_and_actions.append([])
        for i1, text in enumerate(row):
            action = functools.partial(print, f"selected button ({i1}, {i2})")
            button_text_anchortype_and_actions[-1].append((text, ((anchor_type,), 0, 0, 0), action))
    
    menu_overlay = SliderAndButtonMenuOverlay(
        shape=screen_shape,
        framerate=framerate,
        overlay_color=(named_colors_def["yellow"], 0.3),
        mouse_enabled=True,
        navkeys_enabled=True,
        navkeys=(({K_LEFT}, {K_RIGHT}), ({K_UP}, {K_DOWN})),
        navkey_cycle_delay_s=(.4, 0.2, 0.1),
        #exit_press_keys=exit_press_keys,
        #exit_release_keys=exit_release_keys,
    )
    
    menu_overlay.setupSliderPlusGrid(
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
    
    #button_text_groups = tuple((TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None),) for _ in range(4))
    menu_overlay.setupButtonGrid(
        anchor_pos_norm=(0.5, 0.9),
        anchor_type="midbottom",
        button_grid_max_shape_norm=(0.8, 0.1),
        wh_ratio_range=(1, 20),
        button_text_anchortype_and_actions=button_text_anchortype_and_actions,
        text_groups=None,#button_text_groups,
        button_gaps_rel_shape=(0.2, 0.2),
        font_colors=((named_colors_def["white"], 0.5), (named_colors_def["yellow"], 1), (named_colors_def["blue"], 1), (named_colors_def["green"], 1)),
        text_borders_rel=((0.2, 0.2), (0.1, 0.1), 1, 0),
        fill_colors=(None, (named_colors_def["red"], 0.2), (named_colors_def["red"], 0.5), 2),
        outline_widths=((1,), (2,), (3,), 1),
        outline_colors=((named_colors_def["black"], 1), (named_colors_def["blue"], 1), 1, 1),
    )
    
    #print("\nhello\n")
    
    text_group = TextGroup([], max_height0=None, font=None, font_size=None, min_lowercase=True, text_global_asc_desc_chars=None)
    anchor_type = "centre"
    font_color = (named_colors_def["black"], 1)
    text_list = [
        ({"text": "Hello", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 1), (0.2, 0.1))),
        ({"text": "Goodbye", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.4, 0.1))),
        ({"text": "name", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.6, 0.1))),
        ({"text": ",", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.7, 0.1))),
        ({"text": "'", "font_color": font_color, "anchor_type0": anchor_type}, ((0.2, 0.2), (0.8, 0.1))),
    ]
    #print(f"menu text group: {text_group}")
    #text_list = [
    #    (("Hello", text_color), ((0.2, 0.2), (0.2, 0.1), anchor_type)),
    #    (("Goodbye", text_color), ((0.2, 0.2), (0.4, 0.1), anchor_type)),
    #    (("name", text_color), ((0.2, 0.2), (0.6, 0.1), anchor_type)),
    #    ((",", text_color), ((0.2, 0.2), (0.7, 0.1), anchor_type)),
    #    (("'", None, text_color), ((0.2, 0.2), (0.8, 0.1), anchor_type)),
    #]
    
    add_text_list = [x[0] for x in text_list]
    text_objs = text_group.addTextObjects(add_text_list)
    #print("added menu text objects to menu")
    for text_obj, (_, pos_tup) in zip(text_objs, text_list):
        max_shape_rel, anchor_rel_pos_rel = pos_tup
        menu_overlay.addText(text_obj, max_shape_rel,\
                anchor_rel_pos_rel)
    
    """
    max_height_rel = 0.2
    anchor_type = "bottomright"
    text_color = (named_colors_def["black"], 1)
    text_list = [
        ("Hello", (0.2, 0.1), anchor_type, 0.2, text_color),
        ("Goodbye", (0.4, 0.1), anchor_type, 0.2, text_color),
        ("name", (0.6, 0.1), anchor_type, 0.2, text_color),
        (",", (0.7, 0.1), anchor_type, 0.2, text_color),
        ("'", (0.8, 0.1), anchor_type, 0.2, text_color),
    ]
    menu_overlay.addTextGroup(text_list, max_height_rel, font=None,\
            font_size=None)
    """
    menu_overlay.draw(screen)
    screen_changed = True
    #menu_overlay.shape = 
    clock = pg.time.Clock()
    
    while True:
        #print("hello")
        quit, esc_pressed, event_loop_kwargs = menu_overlay.getRequiredInputs()
        #print(f"event_loop_kwargs = {event_loop_kwargs}")
        #print(quit, esc_pressed, event_loop_kwargs)
        running = not esc_pressed
        if quit or not running:
            pg.quit()
            return
        change = False
        quit, running, chng, actions = menu_overlay.eventLoop(check_axes=(0, 1), **event_loop_kwargs)
        if quit or not running:
            pg.quit()
            return
        for action in actions:
            action()
        if chng: change = True
        if change: screen_changed = True
        #print(f"screen changed = {screen_changed}")
        if screen_changed:
            #print("screen changed")
            screen.blit(screen_cp, (0, 0))
            menu_overlay.draw(screen)
            pg.display.flip()
        clock.tick(framerate)
        screen_changed = False
    return