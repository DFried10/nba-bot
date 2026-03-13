import discord
from discord.ext import commands
from discord import app_commands
from utils.nba import find_team, get_team_stats
from config import NBA_BLUE


class TeamCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="team", description="Get NBA team stats and recent results")
    @app_commands.describe(name="Team name or abbreviation (e.g. Lakers, BOS)")
    async def team(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        team = find_team(name)
        if not team:
            await interaction.followup.send(f'❌ Could not find team "{name}".')
            return

        stats = get_team_stats(team["id"])
        if not stats:
            await interaction.followup.send(f'❌ No stats found for {team["full_name"]}.')
            return

        try:
            embed = discord.Embed(
                title=f"🏀 {stats['name']}",
                color=NBA_BLUE
            )

            # Record & ratings
            embed.add_field(
                name="Record",
                value=f"{stats['wins']}-{stats['losses']}",
                inline=True,
            )
            # embed.add_field(
            #     name="Net Rating",
            #     value=f"{'+' if stats['net_rating'] > 0 else ''}{stats['net_rating']}",
            #     inline=True,
            # )
            embed.add_field(name="** **", value="** **", inline=True)
            # embed.add_field(name="OFF RTG", value=stats["off_rating"], inline=True)
            # embed.add_field(name="DEF RTG", value=stats["def_rating"], inline=True)
            embed.add_field(name="** **", value="** **", inline=True)

            # Last 10
            l10 = stats["last10"]
            net = l10['net_rating']
            net_str = f"{'+' if isinstance(net, float) and net > 0 else ''}{net}"
            embed.add_field(
                name="Last 10 Games",
                value=f"{l10['wins']}-{l10['losses']}\nNet Rtg {net_str}",
                inline=False,
            )

            # Recent games
            if stats["recent_games"]:
                games_str = "\n".join(
                    f"{g['result']} {g['matchup']} — {g['pts']} pts ({g['date']})"
                    for g in stats["recent_games"]
                )
                embed.add_field(name="Recent Games", value=games_str, inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"Error building teams stats: {e}")
            return None


async def setup(bot):
    await bot.add_cog(TeamCommands(bot))