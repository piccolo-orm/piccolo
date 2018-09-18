#!/usr/bin/env python
from livereload import Server, shell


server = Server()
server.watch('docs/*.rst', shell('make html', cwd='docs'))
server.serve(root='build/html')
