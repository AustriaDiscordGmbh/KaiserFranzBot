#!/usr/bin/env python3
from .quote import Quote


def setup(bot):
    bot.add_cog(Quote(bot))
