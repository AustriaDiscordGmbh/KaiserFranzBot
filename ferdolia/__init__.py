#!/usr/bin/env python3
from .ferdolia import Ferdolia


def setup(bot):
    bot.add_cog(Ferdolia(bot))
