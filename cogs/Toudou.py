import discord
from discord.ext import commands
from datetime import datetime

class SimpleView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.help_message_visible = False

    # Notification button
    @discord.ui.button(label="🔕",style=discord.ButtonStyle.success)
    async def notifications(self, interaction:discord.Interaction, button:discord.ui.Button):
        print(button.label)
        if button.label == "🔕":
            button.label = "🔔"
        else:
            button.label = "🔕"

        await interaction.response.send_message("Notifications enabled")
    
    # Help Button
    @discord.ui.button(label="Help")
    async def Help(self, interaction:discord.Interaction, button:discord.ui.Button):
        
        print(button.disabled)
        await self.help_todo(interaction)

        button.disabled = True
        await interaction.response.edit_message(view=self)
 
        

    async def help_todo(self, interaction):
            
            help_embed = discord.Embed(title='Todo Commands Help', color=discord.Colour.blurple())

            help_embed.add_field(name='.todo [optional title]', value='Creates a new todo list', inline=False)
            help_embed.add_field(name='add <task>', value='Adds a task to the todo list', inline=False)
            help_embed.add_field(name='<task_number>', value='Marks a task as complete', inline=False)
            help_embed.add_field(name='rm <task_number>', value='Removes a task from the todo list', inline=False)
            help_embed.add_field(name='e <task_number> <new_task>', value='Edits a task in the todo list', inline=False)
            help_embed.add_field(name='uncheck <task_number>', value='Marks a completed task as incomplete', inline=False)
            
            self.help_message_visible = True

            await interaction.response.send_message(embed=help_embed)
    


class todo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.todo_list_active = False
        self.tasks = {}
        self.num_complete = 0 
        self.name = ''
        self.pfp = 0
        self.list_title = 'TODO List'
        self.view = SimpleView()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("the bot is ready")

    @commands.command(name='todo', help='Creates a todo list')
    async def todo(self, ctx, *args, member: discord.Member = None):
        self.todo_list_active = True

        if member is None:
            member = ctx.author
        if args:
            self.list_title = ' '.join(args)
        
        self.name = member.display_name 
        self.pfp = member.display_avatar
        self.tasks = {}  # Reset tasks when a new todo list is created

        # creates the embed with time and author 
        todo = discord.Embed(title= f"{self.list_title}", description="Add tasks using `add <task>`", color=discord.Colour.blurple(), timestamp= datetime.now())
        todo.set_author(name=f"{self.name}", icon_url=f"{self.pfp}")

        await ctx.send(embed=todo, view = self.view)

        
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if self.view.help_message_visible == True:
            # Delete the help message if it's visible
            if message.author != self.bot.user: 
                
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
            # Add command (add/+ <task>)
            if message.content.startswith('add ') or message.content.startswith('+ '):
                # Handle block add
                if "\n" in message.content:
                    task_list = message.content.split("\n")
                    # removes add from the first message
                    task = ' '.join(task_list[0].split(" ")[1:])
                    task_list[0] = task

                    for task in task_list:
                        self.tasks[task] = 0
                    await self.update_todo_embed(message.channel)   
                # Handle single add
                else:
                    # removes add from the message
                    task = ' '.join(message.content.split(' ')[1:])
                    self.tasks[task] = 0
                    await self.update_todo_embed(message.channel)
                print(self.tasks)
            
            # Remove command (rm/- <task>)
            elif message.content.startswith('rm ') or message.content.startswith('- '):
        
                task_num = int(message.content.split(' ')[1:][0])
                keys_list = list(self.tasks.keys())
                task = keys_list[task_num - 1]
                if self.tasks[task] == 1:
                    self.num_complete -=1
                self.tasks[task] = -1
                await self.update_todo_embed(message.channel)
            
            # Edit command (e <task>)
            elif message.content.startswith('e '):

                temp_tasks = self.tasks.copy()
                task = message.content.split(' ')[1:]
                task_num = int(task[0])
                task = task[1:]
                replacement_task = ' '.join(task)
                keys_list = list(self.tasks.keys())
                curr_task = keys_list[task_num - 1]
                # clear the tasks dictionary to reorder it after
                self.tasks = {}
                for task in temp_tasks:
                    if task == curr_task:
                        self.tasks[replacement_task] = temp_tasks[task]
                    else:
                        self.tasks[task] = temp_tasks[task]

                await self.update_todo_embed(message.channel)

            # Uncheck command (uncheck <task>)
            elif message.content.startswith('uncheck '):
                task = int(message.content.split(' ')[1:][0])
                keys_list = list(self.tasks.keys())
                self.tasks[keys_list[task - 1]] = 0
                self.num_complete -= 1

                await self.update_todo_embed(message.channel)
                task = int(message.content.split(' ')[1:][0])
                
            # Rename command (rename <list_name>)
            elif message.content.startswith('rename '):
                list_name = ' '.join(message.content.split(' ')[1:])
                self.list_title = list_name
                await self.update_todo_embed(message.channel)
            
            elif message.content.startswith('clear'):
                self.tasks.clear()
                await self.update_todo_embed(message.channel)
            

            # PUT THIS LAST
            # Complete command (<task number>)
            elif 0 < int(message.content) <= len(self.tasks):
                keys_list = list(self.tasks.keys())
                task = keys_list[int(message.content) - 1]
                self.tasks[task] = 1
                self.num_complete +=1
                await self.update_todo_embed(message.channel)

        await message.delete()
        


    async def update_todo_embed(self, channel):
        task_list = []
        keys_list = list(self.tasks.keys())

        # Create a new dictionary to avoid modifying self.tasks during the loop
        temp_tasks = self.tasks.copy()

        for task in temp_tasks:
            if temp_tasks[task] == 0:
                task_list.append(f"{keys_list.index(task) + 1}. [ ] {task}")
            elif temp_tasks[task] == 1:
                task_list.append(f"{keys_list.index(task) + 1}. [✓] {task}")
            elif temp_tasks[task] == -1:
                self.tasks.pop(task, None)
                keys_list.remove(task)

        if len(self.tasks) > 0:
            todo = discord.Embed(title=f"{self.list_title} ({self.num_complete}/{len(self.tasks)} complete)", description="Add tasks using ` add <task>`", color=discord.Colour.blurple(), timestamp= datetime.now())
        else:
            todo = discord.Embed(title=f"{self.list_title}", description="Add tasks using ` add <task>`", color=discord.Colour.blurple(), timestamp= datetime.now())
        todo.set_author(name=f"{self.name}", icon_url=f"{self.pfp}")
        print(f"task_list: {task_list}")
        task_list = "\n".join(task_list)
        if len(task_list) != 0:
            todo.add_field(name="", value=f"```{task_list}```", inline=True) 

        # Fetch the original todo message
        async for message in channel.history():
            if message.author == self.bot.user and message.embeds:
                original_embed = message.embeds[0]

                # Edit the original message with the updated embed
                await message.edit(embed=todo)
                break

    

async def setup(bot):
    await bot.add_cog(todo(bot))