# Simple gamble game based on the Casino of Ferdolia
# https://www.fwwiki.de/index.php/Tipps/Tricks:Gewinnstrategien_Casino_von_Ferdolien
from redbot.core import commands
from redbot.core import bank
from redbot.core import Config
import random


class Ferdolia(commands.Cog):
    """
    Allows you to play the game of Ferdolia's Casino in Discord
    """

    def __init__(self, bot):
        """
        Inits bot and checkpot
        """
        self.bot = bot
        self.config = Config.get_conf(self, identifier=7147929432)
        default_guild = {
                "base_jackpot": 1000,
                "jackpot": 1000,
                "bid": 25,
                "fee": 5
                }
        self.config.register_guild(**default_guild)
        if(default_guild["fee"] > default_guild["bid"]):
            raise ValueError("Fee higher than bid")

    @commands.command(name="ferdolia", aliases=["fd"])
    async def play(self, ctx):
        """
        You play the game, it costs 25 coins, 20 go to the jackpot, 5 are fee.
        You will roll 4 seven sided dices, if you have the same number 4 times
        you take the jackpot
        """
        jackpot = await self.config.guild(ctx.guild).jackpot()
        bid = await self.config.guild(ctx.guild).bid()
        fee = await self.config.guild(ctx.guild).fee()
        try:
            await bank.withdraw_credits(ctx.author, bid)
        except ValueError:
            ans = ":disappointed: You don't even have "
            ans += str(bid) + " coins."
            return await ctx.send(ans)

        jackpot += (bid - fee)
        await self.config.guild(ctx.guild).jackpot.set(jackpot)
        ans = ":slot_machine: You bet " + str(bid) + ", " + str(fee)
        ans += " go to the bank, " + str(bid - fee)
        ans += " go to the jackpot. :slot_machine:\n"
        ans += "The jackpot is now " + str(jackpot) + ".\n"

        dices = [random.randint(1, 7) for _ in range(4)]
        ans += ":game_die: You've rolled " + str(dices) + ". :game_die:\n"
        unique_cnt = len(set(dices))

        if unique_cnt == 1:
            balance = await bank.deposit_credits(ctx.author, jackpot)
            base_jackpot = await self.config.guild(ctx.guild).base_jackpot()
            await self.config.guild(ctx.guild).jackpot.set(base_jackpot)
            ans += ":trophy: You won the jackpot!\n"
            ans += ":moneybag: You now have a balance of " + str(balance) + "."
        else:
            ans += str(unique_cnt) + " unique numbers. "
            ans += "Thanks for playing, try again soon. :money_with_wings:"

        await ctx.send(ans)
