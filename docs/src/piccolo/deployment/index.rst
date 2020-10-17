Deployment
==========

Docker
------

Piccolo has several dependencies which are compiled (e.g. asyncpg, orjson),
which is great for performance, but you may run into difficulties when using
Alpine Linux as your base Docker image.

Alpine uses a different compiler toolchain to most Linux distros. It's
highly recommended to use Debian as your base Docker image. Many Python packages
have prebuilt versions for Debian, meaning you don't have to compile them at
all during install. The result is a much faster build process, and potentially
even a smaller overall Docker image size (the size of Alpine quickly balloons
after you've added all of the compilation dependencies).
