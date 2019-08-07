#!/usr/bin/env python
from livereload import Server, shell


server = Server()
server.watch(
    'src/',
    shell('make html')
)
server.watch(
    '../piccolo',
    shell('make html')
)
server.serve(root='build/html')
