#!/usr/bin/env python3
from .modcolourmode import ModMode


def setup(bot):
    bot.add_cog(ModMode(bot))
