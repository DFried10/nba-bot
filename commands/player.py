import discord
from discord.ext import commands
from discord import app_commands
from utils.nba import find_player, get_player_stats
from config import NBA_RED, CURRENT_SEASON


class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="player", description="Get NBA player stats")
    @app_commands.describe(
        name="Player name (e.g. LeBron James)",
        per36="Show per 36 minute stats instead",
    )
    async def player(
        self,
        interaction: discord.Interaction,
        name: str,
        per36: bool = False,
    ):
        await interaction.response.defer()

        player = find_player(name)
        if not player:
            await interaction.followup.send(f'❌ Could not find player "{name}".')
            return

        stats = get_player_stats(player["id"])
        if not stats:
            await interaction.followup.send(f'❌ No stats found for {player["full_name"]}.')
            return

        embed = discord.Embed(
            title=f"{'📊 Per 36 Min Stats' if per36 else '📊 Season Stats'} — {player['full_name']}",
            color=NBA_RED
        )
        embed.set_footer(text=f"{stats['season']} Season • {stats['team']} • {stats['gp']} GP • {stats['mpg']} MPG")

        if per36 and stats["per36"]:
            p = stats["per36"]
            embed.add_field(name="PTS", value=p["pts"], inline=True)
            embed.add_field(name="REB", value=p["reb"], inline=True)
            embed.add_field(name="AST", value=p["ast"], inline=True)
            embed.add_field(name="STL", value=p["stl"], inline=True)
            embed.add_field(name="BLK", value=p["blk"], inline=True)
            embed.add_field(name="** **", value="** **", inline=True)
            embed.add_field(name="FG%", value=f"{stats['fg_pct']}%", inline=True)
            embed.add_field(name="3P%", value=f"{stats['fg3_pct']}%", inline=True)
            embed.add_field(name="FT%", value=f"{stats['ft_pct']}%", inline=True)
        else:
            embed.add_field(name="PPG", value=stats["ppg"], inline=True)
            embed.add_field(name="RPG", value=stats["rpg"], inline=True)
            embed.add_field(name="APG", value=stats["apg"], inline=True)
            embed.add_field(name="SPG", value=stats["spg"], inline=True)
            embed.add_field(name="BPG", value=stats["bpg"], inline=True)
            embed.add_field(name="** **", value="** **", inline=True)
            embed.add_field(name="FG%", value=f"{stats['fg_pct']}%", inline=True)
            embed.add_field(name="3P%", value=f"{stats['fg3_pct']}%", inline=True)
            embed.add_field(name="FT%", value=f"{stats['ft_pct']}%", inline=True)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))