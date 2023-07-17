.. _PiccoloV1:


About Piccolo v1
================

**17th July 2023**

Piccolo started in August 2018, and as of this writing is close to 5 years old.

During that time we've had very few, if any, breaking changes. Stability has
always been very important, as we rely on it for our production apps.

So why release v1 now? We probably should have released v1 several years ago,
but such are things. We now have some unavoidable breaking changes due to one
of our main dependencies (Pydantic) releasing v2.

In v2, the core of Pydantic has been rewritten in Rust, and has impressive
improvements in performance. Likewise, other libraries in the ecosystem (such
as FastAPI) have moved to Pydantic v2. It only makes sense that Piccolo does it
too.

In terms of your own code, you shouldn't see much difference. We removed the
``pydantic_config_class`` from ``create_pydantic_model``, and replaced it with
``pydantic_config``, but that's about it.

However, quite a bit of internal code in Piccolo and its sister libraries
`Piccolo API <https://piccolo-api.readthedocs.io>`_ and
`Piccolo Admin <https://piccolo-admin.readthedocs.io>`_ had to be changed to
support Pydantic v2. Supporting both Pydantic v1 and Pydantic v2 would be quite
burdensome.

So Piccolo v1 will just use Pydantic v2 and above.

If you can't upgrade to Pydantic v2, then pin your Piccolo version to ``0.108.0``.
You can find the `docs here for 0.108.0 <https://piccolo-orm.readthedocs.io/en/v0.108.0/>`_.

**Timeline and alpha builds**

Several alpha builds for v1 of Piccolo / Piccolo API / Piccolo Admin will be
released as we make sure they all work seamlessly together. We don't recommend
using these alpha releases - the final releases will be available soon.
