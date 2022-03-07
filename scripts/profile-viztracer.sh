#!/bin/bash
python profiling/setup.py
viztracer --log_async profiling/profile_select.py && vizviewer result.json
