# bot.py

import os, discord
from discord import Intents
from discord.ext import commands

# Reads the server info in from another file
with open('server_info.txt', 'r') as f:
    server_info = f.readlines()

TOKEN = server_info[0][:-1]
SERVER_ID = int(server_info[1])

# Initializes the dictionary to store the assignments for each person
ward_list = {}

# Begins to sort through the data, this code is specific to each project
with open('ward_data - eqrs_data.csv', 'r') as f:
    people = f.readlines()

for person in people:
    person = person.split(',')
    assignments = []
    for calling in person[1:]:
        calling = calling.split('\n')[0]
        if calling != '':
            assignments.append(calling)
    ward_list[person[0].lower()] = assignments

with open('ward_data - fhe_data.csv', 'r') as f:
    groups = f.readlines()

for group in groups:
    group = group.split(',')
    group_name = group[0]
    for person in group[1:]:
        person = person.split('\n')[0]
        if person != '':
            if person.lower() in ward_list.keys():
                ward_list[person.lower()].append(group_name)
            else:
                print(f"{person} is not in the list")

# Print statements to ensure the ward list is accurate (uncomment these lines for debugging)
# for person in ward_list.keys():
#     print(f"{person}: {ward_list[person]}")


# Creates the Bot with the correct permissions
intents = Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="!")


async def dm_about_roles(member):
    """
    This runs either when new members join the server, or when users send !roles to the bot.
    It prompts users to send their name to the bot, first by creating a DM channel with them

    :param member:
    :return None:
    """
    print(f"DMing {member.name}...")

    await member.create_dm()

    await member.dm_channel.send(
        f"""Hi {member.name}, welcome to the Provo YSA 21st Ward Discord!
I'm Bouncer Bot, I'll make sure you're in the right place, and then help you get into the channels you should be in.
Send me your name as it's found in the ward list and I'll get you added to the right channels.
        """
    )


async def assign_roles(message):
    """
    BULK OF THE PROGRAM RIGHT HERE
    This function reads the message sent to the bot, extracts the name, finds the associated assignments,
    and assigns the author of the message to those roles.

    :param message:
    :return None:
    """

    # Sets the name to lower case
    name = message.content.lower()

    # Checks whether we are expecting to receive the name
    if name in ward_list.keys():
        # Receives the sender's assignments from the dictionary created above, prints to the console
        assignments = ward_list[name]
        print(assignments)

        # Ensuring that assignments is nonempty
        if assignments:
            # grabs the server ID
            server = bot.get_guild(SERVER_ID)

            assert server is not None, 'server is None'

            # Gets the role objects for the user, by name (matching case)
            roles = [discord.utils.get(server.roles, name=assignment) for assignment in assignments]

            # Gets the id of the sender of the message
            member = await server.fetch_member(message.author.id)

            try:
                # Adds the roles to their profile
                print(f"Adding roles for {member}...")
                await member.add_roles(*roles, reason="Roles assigned by BouncerBot")
            except Exception as e:
                # If any exceptions are raised, catches them, informs the user of the problem, and prints
                # the error to the console for debugging
                print(e)
                await member.send("Error assigning roles")
            else:
                # Sends the member a message informing them which roles were added
                await message.channel.send(
                    f"""You've been assigned to the following role{"s" if len(assignments) > 1 else ""} on {server.name}:
                { ', '.join(assignments) }.
                """
                )

    # If the name is unexpected, provides the sender with information
    else:
        await message.channel.send("I couldn't find your name... Maybe try sending me a variation on your "
                                             "name, or reach out to a server admin for help.")


@bot.event
async def on_ready():
    """
    Sends messages to the console once the bot is connected to the server

    :return None:
    """
    print(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        print(f'{bot.user} is connected to: {guild.name}')


@bot.event
async def on_member_join(member):
    """
    This runs each time a new member joins, sending them a message to provide their names
    :param member:
    :return None:
    """
    await dm_about_roles(member)


@bot.event
async def on_message(message):
    """
    This runs each time the bot gets a message, and either dms the author about roles,
    or runs the assign_roles() function to gather and assign the correct roles to the user.

    :param message:
    :return None:
    """
    # Ensures the bot is not the author, so we don't get stuck in an infinite loop
    if message.author == bot.user:
        return

    # Checks for the input being !roles, which is a code to allow testing of the functions
    if message.content.startswith("!roles"):
        await dm_about_roles(message.author)

    # Checks whether the message is a DM, and if so, tries to assign roles to the user based on the input
    elif isinstance(message.channel, discord.channel.DMChannel):
        await assign_roles(message)
        return


bot.run(TOKEN)
