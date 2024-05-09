import discord
from discord.ext import commands
from datetime import datetime
import ast
import re

class SimpleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.help_message_visible = False
    
    # Help Button
    @discord.ui.button(label="Help")
    async def Help(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        await self.help_todo(interaction)
        button.disabled = True
        await interaction.response.edit_message(view=self)

        

    async def help_todo(self, interaction):
            
            help_embed = discord.Embed(title='Todo Commands Help', color=discord.Colour.blurple())

            help_embed.add_field(name='.todo [optional title]', value='Creates a new todo list', inline=False)
            help_embed.add_field(name='add <item>', value='Adds a task to the todo list', inline=False)
            help_embed.add_field(name='<item_number>', value='Marks a task as complete', inline=False)
            help_embed.add_field(name='rm <item_number>', value='Removes a task from the todo list', inline=False)
            help_embed.add_field(name='e <item_number> <new_task>', value='Edits a task in the todo list', inline=False)
            help_embed.add_field(name='uncheck <item_number>', value='Marks a completed task as incomplete', inline=False)
            help_embed.add_field(name='clear', value='Removes all tasks from list', inline=False)


            self.help_message_visible = True

            await interaction.response.send_message(embed=help_embed)
    


class todo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.todo_list_active = False
        self.task_dict = {}
        self.num_complete = 0 
        self.name = ''
        self.pfp = 0
        self.list_title = 'TODO List'
        self.active_channel_id = 0
        self.active_channel = 0
        self.storage_channel = 0
        self.id_dict = {}
        self.master_id = 0
        self.view = SimpleView()
        self.valid_commands = ['.todo','.clearchannel','.delete','.show','.setstorage']
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("The bot is ready")

    @commands.command(name='todo', help='Creates a todo list')
    async def todo(self, ctx, *args, member: discord.Member = None):
        self.todo_list_active = True
        self.active_channel_id = ctx.channel.id
        self.active_channel = self.bot.get_channel(self.active_channel_id)
        if self.storage_channel == 0:
            self.storage_channel = self.active_channel
            print(self.storage_channel)
        
        await ctx.message.delete()

        if member is None:
            member = ctx.author

        # Sets title name to be the argument values or a default name of 'TODO List'
        if args:
            self.list_title = ' '.join(args)
            print(self.list_title)
        else:
            self.list_title = 'TODO List'
        
        # Sets the author and authors pfp
        self.name = member.display_name 
        self.pfp = member.display_avatar
        self.task_dict = {}  # Reset tasks when a new todo list is created
        
        await self.load_dict(ctx)
        
        # Check if the title is in the first message dictionary
        if self.list_title in self.id_dict.keys():
            # Gets the message id of the list with the desired title
            message = await self.storage_channel.fetch_message(self.id_dict[self.list_title])
            await self.load_embed(message)
            del self.id_dict[self.list_title]
            todo = message.embeds[0]
            await message.delete()
            message = await self.storage_channel.send(embed=todo, view = self.view)
            if self.storage_channel != self.active_channel:
                await ctx.send(embed=todo, view = self.view)

        else:
            # creates the embed with time and author 
            todo = discord.Embed(title= f"{self.list_title}", description="Add tasks using `add <task>`", color=discord.Colour.blurple(), timestamp= datetime.now())
            todo.set_author(name=f"{self.name}", icon_url=f"{self.pfp}")

            message = await self.storage_channel.send(embed=todo, view = self.view)
            if self.storage_channel != self.active_channel:
                await ctx.send(embed=todo, view = self.view)

        self.id_dict[self.list_title] = message.id
        print(self.id_dict)

        message = await self.storage_channel.fetch_message(self.master_id)
        print(message)

        await message.edit(content=self.id_dict)
    


    @commands.command(name='delete', help='Deletes a list by name')
    async def delete(self,ctx,*args):

        await self.load_dict(ctx)
        list_title = ' '.join(args)
        await ctx.message.delete()
        if list_title in self.id_dict:
            message = await self.storage_channel.fetch_message(self.id_dict[list_title])
            await message.delete()
            del self.id_dict[list_title]
        
        self.id_dict[self.list_title] = message.id
        print(self.id_dict)

        message = await self.storage_channel.fetch_message(self.master_id)
        print(message)

        await message.edit(content=self.id_dict)

    @commands.command(name='clearchannel', help='Clears all messages from channel (with confirmation)')
    async def clear_channel(self, ctx):
        # Ask for confirmation
        await ctx.send("Are you sure you want to clear all messages from this channel? Type `yes` to confirm.")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() == 'yes'  
        await self.bot.wait_for('message', check=check)
        # If user confirms, proceed with clearing the channel
        await ctx.channel.purge()
        


    @commands.command(name='setstorage', help='Sets a channel to store all the embeds')
    async def setstorage(self,ctx,*args):
        guild = ctx.guild
        channel_name = '-'.join(args)
        await ctx.message.delete()
        channel = discord.utils.get(guild.channels, name=channel_name)
        if channel:
            self.storage_channel = channel
        else:
            await guild.create_text_channel(channel_name)
            channel = discord.utils.get(guild.channels, name=channel_name)
            self.storage_channel = channel

        print(f"storage has been set to: {channel_name}")

    @commands.command(name='show', help='displays all lists in the storage channel')
    async def show(self, ctx):

        # Get the keys of the dictionary and sort them alphabetically
        sorted_keys = sorted(self.id_dict.keys())

        # Create a formatted string with the sorted keys
        keys_list = "\n".join(sorted_keys)

        # Send the sorted keys as a message
        await ctx.send(f"**Keys of the dictionary (in alphabetical order):**\n```{keys_list}```")

        
    async def load_embed(self, message):
        pattern = r'^.*?\[(.*?)\]\s*'
        task_dict = {}
        todos = []
        num_complete = 0
        embed = message.embeds[0]
        print(embed.fields)
        if embed.fields: 
            fields = embed.fields[0].value.strip("`")
            print(fields)
            todos = fields.split("\n")
            print(todos)   
        for todo in todos:
            parsed_todo = re.sub(pattern, r'\1', todo)
            print(parsed_todo)
            if "✓" in todo:
                task_dict[parsed_todo] = 1
                num_complete+=1
            else:
                task_dict[parsed_todo] = 0
        print(task_dict)
        self.task_dict = task_dict
        self.num_complete = num_complete

    async def load_dict(self, ctx):
        # Retrieves the first message in the channel
        messages = [message async for message in self.storage_channel.history(limit=1, oldest_first=True)]
        print(messages)

        # Creates a first message if it does not exists, then sets master id to first message id
        if len(messages) == 0:
            await self.storage_channel.send(self.id_dict)
            messages = [message async for message in self.storage_channel.history(limit=1, oldest_first=True)]
            self.master_id = messages[0].id
        else:
            self.master_id = messages[0].id
            print(self.master_id)

        # Convert String from first message to a dictionary
        self.id_dict = ast.literal_eval(messages[0].content)
        print(self.list_title)  
        

    @commands.Cog.listener()
    async def on_message(self, message):
        
        if self.view.help_message_visible == True :
            
            # Delete the help message if it's visible
            if message.author != self.bot.user and self.active_channel == message.channel.id: 
                # Fetch the original todo message
                async for curr_message in message.channel.history():
                    if curr_message.author == self.bot.user and curr_message.embeds:
                        await curr_message.delete()
                        self.view.help_message_visible = False
                        break

        # Don't react to bot messages 
        if message.author == self.bot.user:
            return
        
        if self.todo_list_active:

            # Add command (add <task>)
            if message.content.startswith('add '):
                # Handle block add
                if "\n" in message.content:
                    task_dict = message.content.split("\n")
                    # removes add from the first message
                    task = ' '.join(task_dict[0].split(" ")[1:])
                    task_dict[0] = task

                    for task in task_dict:
                        self.task_dict[task] = 0
                    await self.update_todo_embed(message.channel)   
                # Handle single add
                else:
                    # removes add from the message
                    task = ' '.join(message.content.split(' ')[1:])
                    self.task_dict[task] = 0
                    await self.update_todo_embed(message.channel)
                print(self.task_dict)
            
            # Remove command (rm <task>)
            elif message.content.startswith('rm '):
                # Handle multi remove
                print("in here")
                if "," in message.content:
                    print("in block")
                    task_nums = ''.join(message.content.split(' ')[1:]).split(',')
                    keys_list = list(self.task_dict.keys())
                    print("before for ")
                    for task_num in task_nums:
                        task_num = int(task_num)
                        task = keys_list[task_num - 1]
                        if self.task_dict[task] == 1:
                            self.num_complete -=1
                        self.task_dict[task] = -1
                    print(self.task_dict)
                    await self.update_todo_embed(message.channel)


                # Handle range remove
                elif "-" in message.content:
                    task_nums = ''.join(message.content.split(' ')[1:]).split('-')
                    keys_list = list(self.task_dict.keys())
                    lower_bound = int(task_nums[0]) - 1
                    upper_bound = int(task_nums[1])
                    
                    if lower_bound < 0: 
                        lower_bound = 0 
                    if lower_bound > len(self.task_dict) - 1 :
                        lower_bound = (len(self.task_dict)) - 1
                    if upper_bound > len(self.task_dict) - 1:
                        upper_bound = (len(self.task_dict))
                    
                    for task_num in range(lower_bound, upper_bound):
                        task = keys_list[task_num]
                        if self.task_dict[task] == 1:
                            self.num_complete -=1
                        self.task_dict[task] = -1
                    await self.update_todo_embed(message.channel)
 
                # Handle single remove
                else:
                    task_num = int(message.content.split(' ')[1:][0])
                    keys_list = list(self.task_dict.keys())
                    task = keys_list[task_num - 1]
                    if self.task_dict[task] == 1:
                        self.num_complete -=1
                    self.task_dict[task] = -1
                    await self.update_todo_embed(message.channel)
            
            # Edit command (e <task>)
            elif message.content.startswith('e '):

                temp_tasks = self.task_dict.copy()
                task = message.content.split(' ')[1:]
                task_num = int(task[0])
                task = task[1:]
                replacement_task = ' '.join(task)
                keys_list = list(self.task_dict.keys())
                curr_task = keys_list[task_num - 1]
                # clear the tasks dictionary to reorder it after
                self.task_dict = {}
                for task in temp_tasks:
                    if task == curr_task:
                        self.task_dict[replacement_task] = temp_tasks[task]
                    else:
                        self.task_dict[task] = temp_tasks[task]

                await self.update_todo_embed(message.channel)

            # Uncheck command (uncheck <task>)
            elif message.content.startswith('uncheck '):
                task = int(message.content.split(' ')[1:][0])
                keys_list = list(self.task_dict.keys())
                self.task_dict[keys_list[task - 1]] = 0
                self.num_complete -= 1

                await self.update_todo_embed(message.channel)
                task = int(message.content.split(' ')[1:][0])
                
            # Rename command (rename <list_name>)
            elif message.content.startswith('rename '):
                list_name = ' '.join(message.content.split(' ')[1:])
                self.list_title = list_name
                await self.update_todo_embed(message.channel)
            
            # Clear command (clear)
            elif message.content.startswith('clear'):
                self.task_dict.clear()
                await self.update_todo_embed(message.channel)
            
            # Complete command (<task number>)
            elif message.content.isnumeric() and 0 < int(message.content) <= len(self.task_dict):
                keys_list = list(self.task_dict.keys())
                task = keys_list[int(message.content) - 1]
                if self.task_dict[task] != 1:
                    self.num_complete +=1
                    self.task_dict[task] = 1

                await self.update_todo_embed(message.channel)
            
            # quit the todo list
            elif message.content.startswith('quit'):
                self.todo_list_active = False
                await message.delete()

        # Deletes all non command messages that are sent by the user in the channel with the todo list
        if message.author != self.bot.user and self.active_channel_id == message.channel.id and self.todo_list_active:
            if not any(message.content.startswith(command) for command in self.valid_commands):
                print("message deleted")
                await message.delete()

    async def update_todo_embed(self, channel):
        task_dict = []
        keys_list = list(self.task_dict.keys())

        # Create a new dictionary to avoid modifying self.tasks during the loop
        temp_tasks = self.task_dict.copy()

        for task in temp_tasks:
            if temp_tasks[task] == 0:
                task_dict.append(f"{keys_list.index(task) + 1}. [ ] {task}")
            elif temp_tasks[task] == 1:
                task_dict.append(f"{keys_list.index(task) + 1}. [✓] {task}")
            elif temp_tasks[task] == -1:
                self.task_dict.pop(task, None)
                keys_list.remove(task)

        if len(self.task_dict) > 0:
            todo = discord.Embed(title=f"{self.list_title} ({self.num_complete}/{len(self.task_dict)} complete)", description="Add tasks using ` add <task>`", color=discord.Colour.blurple(), timestamp= datetime.now())
        else:
            todo = discord.Embed(title=f"{self.list_title}", description="Add tasks using ` add <task>`", color=discord.Colour.blurple(), timestamp= datetime.now())
        todo.set_author(name=f"{self.name}", icon_url=f"{self.pfp}")
        # print(f"task_dict: {task_dict}")
        task_dict = "\n".join(task_dict)
        if len(task_dict) != 0:
            todo.add_field(name="", value=f"```{task_dict}```", inline=True) 

        # Fetch the original todo message
        async for message in channel.history():
            if message.author == self.bot.user and message.embeds:
                # Edit the original message with the updated embed
                await message.edit(embed=todo)
                break
            
        if channel != self.storage_channel:
            # Fetch the original todo message
            async for message in self.storage_channel.history():
                if message.author == self.bot.user and message.embeds:
                    # Edit the original message with the updated embed
                    await message.edit(embed=todo)
                    break
        


async def setup(bot):
    await bot.add_cog(todo(bot))