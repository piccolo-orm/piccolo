#!/bin/bash
python profiling/setup.py
pyinstrument profiling/profile_select.py
