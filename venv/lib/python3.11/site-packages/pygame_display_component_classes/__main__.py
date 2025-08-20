#!/usr/bin/env python3
import os
import sys

from pygame_display_component_classes import (
    runExampleButton1,
    runExampleButtonGroup1,
    runExampleButtonGrid1,
    runExampleSlider1,
    runExampleSliderGroup1,
    runExampleSliderPlus1,
    runExampleSliderPlusGroup1,
    runExampleSliderPlusGrid1,
    #runExampleSliders1,
    runExampleMenuOverlayBase1,
    runExampleButtonMenuOverlay1,
    runExampleSliderAndButtonMenuOverlay1,
)

def main() -> None:
    #runExampleButton1()
    #runExampleButtonGroup1()
    #runExampleButtonGrid1()

    #address = runExampleSlider1()
    #print(f"reference count = {ctypes.c_long.from_address(address)}")
    #runExampleSliderGroup1()
    #runExampleSliderPlus1()
    #runExampleSliderPlusGroup1()
    runExampleSliderPlusGrid1()

    #runExampleMenuOverlayBase1()
    #runExampleButtonMenuOverlay1()
    #runExampleSliderAndButtonMenuOverlay1()

if __name__ == "__main__":
    main()
