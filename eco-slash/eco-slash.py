import discord
import asyncio
import typing
import random
USER_COOLDOWNS = {}
from discord import app_commands
from discord.ext import commands
import core.utils
import core
from .core.utils import Database,setSetting,getSetting,deleteSetting
from DiscordEconomy.Sqlite import Economy
economy = Economy("plugins/aunnux/modmail-plugins/eco-slash-master/db/economy.db")
items_list = {
    "Items": {
        "ring": {
            "available": True,
            "price": 15000,
            "description": "An expensive way to show you love someone"
        },
        "fishing rod": {
            "available": True,
            "price": 5000,
            "description": "feeeeshhhh"
        },
        "pickaxe": {
            "available": True,
            "price": 6000,
            "description": "Not diamond... but could help get some."
        },
        "sword": {
            "available": True,
            "price": 7000,
            "description": "Stabby thing!"
        },
        "dorayaki": {
            "available": True,
            "price": 12500,
            "description": "Special pancakes!"
        },
        "pancake": {
            "available": True,
            "price": 10000,
            "description": "Yummers! Pancake!"
        }
    }}

class Eco(commands.Cog):
    def __init__(self, client):
        self.bot = client
        self.client = client
        self.db = Database()
        self.dropped = {}

        @self.bot.tree.error
        async def on_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            print(USER_COOLDOWNS)
            embed = discord.Embed(
                colour=discord.Color.from_rgb(244, 182, 89)
            )

            embed.add_field(name="Error", value=str(error))
            embed.set_footer(text=f"Invoked by {interaction.user.name}",
                            icon_url=interaction.user.avatar.url)

            await interaction.response.send_message(embed=embed,ephemeral=True)

    g = app_commands.Group(
        name="eco", description="Economy Commands", )
    d = app_commands.Group(
        name="eco_staff", description="Economy Commands", )


    def is_owner():
        async def predicate(interaction: discord.Interaction) -> bool:
            return interaction.user.id == 398018466856304640
        return app_commands.check(predicate)

    def is_registered():
        async def predicate(interaction: discord.Interaction):
            await economy.ensure_registered(interaction.user.id)
            return True

        return app_commands.check(predicate)
    
    @g.command(description="See the list of all available items.")
    @is_registered()
    async def items(self, interaction: discord.Interaction):
        embed = discord.Embed(
            colour=discord.Color.from_rgb(244, 182, 89)
        )
        embed.set_author(name="Items")

        for item in items_list["Items"].items():

            if item[1]["available"]:
                embed.add_field(name=item[0].capitalize(), value=f"""Price: **{item[1]['price']}**
                                                                     Description: **{item[1]['description']}**""")

                embed.set_footer(text=f"Invoked by {interaction.user.name}",
                                 icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @g.command(description="Buy an item!")
    @is_registered()
    async def buy(self, interaction: discord.Interaction, *, item: str):

        _item = item.lower()
        _cache = []
        embed = discord.Embed(
            colour=discord.Color.from_rgb(244, 182, 89)
        )

        for item in items_list["Items"].items():
            if item[0] == _item:
                _cache.append(item[0])

                r = await economy.get_user(interaction.user.id)

                if item[0] in [item.name for item in r.items]:
                    embed.add_field(name="Error", value=f"You already have that item!")
                    embed.set_footer(text=f"Invoked by {interaction.user.name}",
                                     icon_url=interaction.user.avatar.url)
                    await interaction.response.send_message(embed=embed)

                    return

                if r.bank >= item[1]["price"]:
                    await economy.add_item(interaction.user.id, item[0])
                    await economy.remove_money(interaction.user.id, "bank", item[1]["price"])

                    embed.add_field(name="Success", value=f"Successfully bought **{item[0]}**!")
                    embed.set_footer(text=f"Invoked by {interaction.user.name}",
                                     icon_url=interaction.user.avatar.url)
                    await interaction.response.send_message(embed=embed)

                else:

                    embed.add_field(name="Error", value=f"You don't have enought money to buy this item!")
                    embed.set_footer(text=f"Invoked by {interaction.user.name}",
                                     icon_url=interaction.user.avatar.url)
                    await interaction.response.send_message(embed=embed)
                break

        if len(_cache) <= 0:
            embed.add_field(name="Error", value="Item with that name does not exists!")
            await interaction.response.send_message(embed=embed)

    @g.command(description="Sell an item from your inventory!")
    @is_registered()
    async def sell(self, interaction: discord.Interaction, *, item: str):
        r = await economy.get_user(interaction.user.id)

        _item = item.lower()

        embed = discord.Embed(
            colour=discord.Color.from_rgb(244, 182, 89)
        )

        if _item in [item.name for item in r.items]:
            for item in items_list["Items"].items():
                if item[0] == _item:
                    item_prc = item[1]["price"] / 2

                    await economy.add_money(interaction.user.id, "bank", item_prc)
                    await economy.remove_item(interaction.user.id, item[0])

                    embed.add_field(name="Success", value=f"Successfully sold **{item[0]}**!")
                    await interaction.response.send_message(embed=embed)
                    break
        else:

            embed.add_field(name="Error", value=f"You don't have this item!")
            await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        let = random.randint(1,100)
        drops  = await getSetting(msg.channel.id, "drops") or None
        if drops != None: drops = drops[0][1]
        if drops == None: drops = False
        if drops == True:
            try:
                print(let)
                if self.dropped[msg.channel.id] != None: return
                if  self.dropped[msg.channel.id] == True: return
            except KeyError:
                if let <= 3:
                    print(let)
                    await msg.channel.send("Currency Dropped! use </eco claim:1505228262366908439>")
                    self.dropped[msg.channel.id] = True

    def cooldown(when: typing.Union[int, float]):
        async def __handle_cooldown(when: typing.Union[int, float], interaction: discord.Interaction):
            USER_COOLDOWNS[interaction.user.id] = when
            await asyncio.sleep(when)
            USER_COOLDOWNS.pop(interaction.user.id)

        async def predicate(interaction: discord.Interaction):
            if interaction.user.id in USER_COOLDOWNS:
                raise app_commands.AppCommandError("User is on cooldown")

            asyncio.ensure_future(__handle_cooldown(when, interaction))

            return True

        return app_commands.check(predicate)
    
    @g.command(name="reward")
    @is_registered()
    @cooldown(60)
    async def reward(self,interaction: discord.Interaction):
        random_amount = random.randint(50, 150)
        await economy.add_money(interaction.user.id, "wallet", random_amount)

        embed = discord.Embed(
            colour=discord.Color.from_rgb(244, 182, 89)
        )
        embed.add_field(name=f"Reward", value=f"Successfully claimed reward!")
        embed.set_footer(text=f"Invoked by {interaction.user.name}",
                        icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @d.command(name="drop")
    @is_owner()
    async def szea(self,ctx: discord.Interaction):
        """  DEVLEOPER ONLY  """
        await ctx.channel.send("Currency Dropped! use </eco claim:1505228262366908439>")
        self.dropped[ctx.channel.id] = True
        await ctx.response.send_message(":+1:", ephemeral=True)

    @d.command(name="toggle")
    @app_commands.guild_only()
    @is_owner()
    async def szea(self,ctx: discord.Interaction):
        """  DEVLEOPER ONLY  """
        drops  = await getSetting(ctx.channel.id, "drops") or None
        if drops != None: drops = drops[0][1]
        if drops == None: drops = False
        if drops == False:
            await setSetting(ctx.channel.id, True)
            await ctx.channel.send("Currency Dropped! use </eco claim:1505228262366908439>")
            self.dropped[ctx.channel.id] = True
            await ctx.response.send_message(":+1:", ephemeral=True)
        else:
            await deleteSetting(ctx.channel_id)
            await ctx.response.send_message(":+1:", ephemeral=True)

    @d.command(name="add_bank")
    @is_owner()
    async def seb(self,ctx: discord.Interaction, member: discord.User, amnt: int):
        """  Developer ONLY """
        await economy.ensure_registered(member.id)
        user = await economy.get_user(member.id)
        await economy.add_money(member.id, "bank", amnt)
        await ctx.response.send_message(f"{member.name} has (:dollar: ${user.wallet}  | **+** :bank: ${user.bank+amnt})")

    @d.command(name="add_wallet")
    @is_owner()
    async def sea(self,ctx: discord.Interaction, member: discord.User, amnt: int):
        """  Developer ONLY """
        await economy.ensure_registered(member.id)
        user = await economy.get_user(member.id)
        await economy.add_money(member.id, "wallet", amnt)
        await ctx.response.send_message(f"{member.name} has (**+** :dollar: ${user.wallet+amnt}  | :bank: ${user.bank})")

    @g.command(name="claim")
    @is_registered()
    async def seaz(self,ctx: discord.Interaction):
        """  ECONOMY """
        member = ctx.user
        await economy.ensure_registered(member.id)
        try:
            user = await economy.get_user(member.id)
            if  self.dropped[ctx.channel.id] == True:
                self.dropped.pop(ctx.channel.id)
                await economy.add_money(member.id, "wallet", 100)
                await ctx.response.send_message(f"{member.name} has picked up the drop and now has (**+** :dollar: ${user.wallet+100})")
            else: return await ctx.response.send_message("No dropped money was found!", ephemeral=True)
        except KeyError:
            return await ctx.response.send_message("No dropped money was found!", ephemeral=True)
    
    @g.command(name="pay")
    @is_registered()
    async def pay(self,ctx: discord.Interaction, member: discord.User, amnt: int):
        """ ECONOMY """
        await economy.ensure_registered(member.id)
        await economy.ensure_registered(ctx.user.id)
        user = await economy.get_user(ctx.user.id)
        if user.wallet >= 0 and user.wallet >= amnt:
            await economy.remove_money(ctx.user.id, "wallet", amnt)
            await economy.add_money(member.id, "wallet", amnt)
            await ctx.response.send_message(f"{ctx.user.name} has sent :dollar: ${amnt}")
        else: return await ctx.response.send_message("You cant afford sending that much!")

    @g.command(name="flip")
    @is_registered()
    async def coinflip(self, interaction: discord.Interaction, money: int, side: str):
        """  ECONOMY """
        if money > 500: return await interaction.response.send_message(content="Max bet is 500!")
        side = side.lower()
        random_arg = random.choice(["tails", "heads"])

        r = await economy.get_user(interaction.user.id)
        embed = discord.Embed(
            colour=discord.Color.from_rgb(244, 182, 89)
        )

        if r.bank >= money:
            if side == random_arg:
                await economy.add_money(interaction.user.id, "wallet", money * 2)

                embed.add_field(name="Coinflip", value=f"You won coinflip! - {random_arg}")
                embed.set_footer(text=f"Invoked by {interaction.user.name}",
                                icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)
            else:
                await economy.remove_money(interaction.user.id, "wallet", money)

                embed.add_field(name="Coinflip", value=f"You lost coinflip! - {random_arg}")
                embed.set_footer(text=f"Invoked by {interaction.user.name}",
                                icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)

        else:
            embed.add_field(name="Coinflip", value=f"You don't have enough money!")
            embed.set_footer(text=f"Invoked by {interaction.user.name}",
                            icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

    @is_registered()
    @app_commands.command(name="duel")
    async def duel(self,interaction: discord.Interaction, opponent: discord.Member,bet: int):
        """Challenge another member to a duel."""
        challenger = interaction.user

        # Prevent dueling yourself or the bot
        if opponent == challenger:
            await interaction.response.send_message("You can't duel yourself!")
            return
        if opponent.bot:
            await interaction.response.send_message("You can't duel a bot!")
            return
        await economy.ensure_registered(opponent.id)
        await economy.ensure_registered(challenger.id)
        user = await economy.get_user(challenger.id)
        user2 = await economy.get_user(opponent.id)
        if user.bank >= 0 and user.bank <= bet:
            return await interaction.response.send_message("You cant afford betting that much!")
        if user2.bank >= 0 and user2.bank <= bet:
            return await interaction.response.send_message("They cant afford betting that much!")

        # Send challenge message
        await interaction.response.send_message(f"{opponent.mention}, {challenger.mention} has challenged you to a duel! "
                    f"Type `accept` to fight or `decline` to refuse. You have 30 seconds.")

        def check(m):
            return (
                m.author == opponent
                and m.channel == interaction.channel
                and m.content.lower() in ["accept", "decline"]
            )

        try:
            # Wait for opponent's response
            msg = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await interaction.edit_original_response(content=f"{opponent.mention} did not respond in time. Duel canceled.")
            return

        if msg.content.lower() == "decline":
            await interaction.edit_original_response(content=f"{opponent.mention} declined the duel. Coward!")
            return

        # Duel accepted — pick a winner
        winner = random.choice([challenger, opponent])
        loser = opponent if winner == challenger else challenger

        await interaction.edit_original_response(content=f"⚔️ The duel begins between {challenger.mention} and {opponent.mention}!")
        await asyncio.sleep(2)  # Dramatic pause
        await economy.remove_money(loser.id, "wallet", bet)
        await economy.add_money(winner.id, "wallet", bet)

        await interaction.edit_original_response(content=f"🏆 {winner.mention} has defeated {loser.mention} in the duel!")

    @g.command(name="slots")
    @is_registered()
    async def slots(self, interaction: discord.Interaction, money: int):
        """  ECONOMY """
        if money > 500: return await interaction.response.send_message(content="Max bet is 500!")
        random_slots_data = [None for _ in range(9)]
        i = 0
        for _ in random_slots_data:
            random_slots_data[i] = random.choice([":tada:", ":cookie:", ":large_blue_diamond:",
                                                ":money_with_wings:", ":moneybag:", ":cherries:"])

            i += 1
            if i == len(random_slots_data):
                break

        r = await economy.get_user(interaction.user.id)

        embed = discord.Embed(
            colour=discord.Color.from_rgb(244, 182, 89)
        )

        if r.bank >= money:

            embed.add_field(name="Slots", value=f"""{random_slots_data[0]} | {random_slots_data[1]} | {random_slots_data[2]}
                                                    {random_slots_data[3]} | {random_slots_data[4]} | {random_slots_data[5]}
                                                    {random_slots_data[6]} | {random_slots_data[7]} | {random_slots_data[8]}
                                                """)
            embed.set_footer(text=f"Invoked by {interaction.user.name}",
                            icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

            if random_slots_data[3] == random_slots_data[4] and random_slots_data[5] == random_slots_data[3]:
                await economy.add_money(interaction.user.id, "wallet", money * 2)
                await interaction.followup.send(content="You won!")

            else:
                await economy.remove_money(interaction.user.id, "bank", money)
                await interaction.followup.send(content="You lose!")

        else:
            embed.add_field(name="Slots", value=f"You don't have enough money!")
            embed.set_footer(text=f"Invoked by {interaction.user.name}",
                            icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
    
    @g.command(description="Play some horse racing.")
    @is_registered()
    async def horse_racing(self, interaction: discord.Interaction, money: int):
        """  ECONOMY """
        user = await economy.get_user(interaction.user.id)
        if money > 500: return await interaction.response.send_message(content="Max bet is 500!")

        if not user.bank >= money:
            return await interaction.response.send_message(content="You don't have enough money to play.")

        author_path = [":horse_racing:", ":blue_square:", ":blue_square:", ":blue_square:", ":blue_square:",
                    ":blue_square:",
                    ":blue_square:", ":blue_square:", ":blue_square:", ":blue_square:", "  :checkered_flag:"]

        enemy_path = [":horse_racing:", ":red_square:", ":red_square:", ":red_square:", ":red_square:", ":red_square:",
                    ":red_square:", ":red_square:", ":red_square:", ":red_square:", "  :checkered_flag:"]

        embed = discord.Embed(
            colour=discord.Color.from_rgb(244, 182, 89)
        )
        embed.set_author(name="Horse race")
        embed.add_field(name="You:", value="".join(author_path), inline=False)
        embed.add_field(name=f"Enemy:", value="".join(enemy_path),
                        inline=False)

        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(3)

        author_path[0] = ":blue_square:"
        enemy_path[0] = ":red_square:"

        author_path_update = random.randint(2, 6)
        enemy_path_update = random.randint(2, 6)

        author_path[author_path_update] = ":horse_racing:"
        enemy_path[enemy_path_update] = ":horse_racing:"

        embed.clear_fields()
        embed.add_field(name="You:", value="".join(author_path), inline=False)
        embed.add_field(name=f"Enemy:", value="".join(enemy_path),
                        inline=False)

        await interaction.edit_original_response(embed=embed)
        await asyncio.sleep(3)

        author_path[author_path_update] = ":blue_square:"
        enemy_path[enemy_path_update] = ":red_square:"

        author_path_update = random.randint(author_path_update, 9)
        enemy_path_update = random.randint(enemy_path_update, 9)

        author_path[author_path_update] = ":horse_racing:"
        enemy_path[enemy_path_update] = ":horse_racing:"

        embed.clear_fields()
        embed.add_field(name="You:", value="".join(author_path), inline=False)
        embed.add_field(name=f"Enemy:", value="".join(enemy_path),
                        inline=False)
        await interaction.edit_original_response(embed=embed)

        if author_path_update > enemy_path_update:
            await economy.add_money(interaction.user.id, "wallet", money * 2)

            await interaction.followup.send(content="You won!")

        else:
            await economy.remove_money(interaction.user.id, "bank", money)

            await interaction.followup.send(content="You lose!")

    @g.command(name="deposit")
    @is_registered()
    async def deposit(self, interaction: discord.Interaction, money: int):
        """  ECONOMY """
        r = await economy.get_user(interaction.user.id)

        embed = discord.Embed(
            colour=discord.Color.from_rgb(244, 182, 89)
        )

        if not r.wallet >= money:
            embed.add_field(name="Deposit", value=f"You don't have enough money to deposit!")
            embed.set_footer(text=f"Invoked by {interaction.user.name}",
                            icon_url=interaction.user.avatar.url)
            return await interaction.response.send_message(embed=embed)

        await economy.add_money(interaction.user.id, "bank", money)
        await economy.remove_money(interaction.user.id, "wallet", money)

        embed.add_field(name="Deposit", value=f"Successfully deposited {money} money!")
        embed.set_footer(text=f"Invoked by {interaction.user.name}",
                        icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @g.command(name="withdraw")
    @is_registered()
    async def withdraw(self, interaction: discord.Interaction, money: int):
        """ Withdraw money from your bank! """
        r = await economy.get_user(interaction.user.id)

        embed = discord.Embed(
            colour=discord.Color.from_rgb(244, 182, 89)
        )

        if r.bank >= money:
            await economy.add_money(interaction.user.id, "wallet", money)
            await economy.remove_money(interaction.user.id, "bank", money)

            embed.add_field(name="Withdraw", value=f"Successfully withdrawn {money} money!")
            embed.set_footer(text=f"Invoked by {interaction.user.name}",
                            icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

        else:

            embed.add_field(name="Withdraw", value=f"You don't have enough money to withdraw!")
            embed.set_footer(text=f"Invoked by {interaction.user.name}",
                            icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)


    @g.command(name="balance")
    @is_registered()
    async def bal(self,ctx: discord.Interaction):
        """ ECONOMY """
        await economy.ensure_registered(ctx.user.id)
        user = await economy.get_user(ctx.user.id)
        await ctx.response.send_message(f"{ctx.user.name} has (:dollar: ${user.wallet}  | :bank: ${user.bank})")

async def setup(client) -> None:
    await client.add_cog(Eco(client))
