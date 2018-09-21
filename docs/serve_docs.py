#!/usr/bin/env python
from livereload import Server, shell


server = Server()
server.watch(
    '**/*.rst',
    shell('cd .. && make html')
)
server.serve(root='../build/html')
