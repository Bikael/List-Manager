import discord
from discord.ext import commands
from datetime import datetime

class SimpleView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="🔔",style=discord.ButtonStyle.success)
    async def notify(self,interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.send_message("")
    
    @discord.ui.button(label="Help",style=discord.ButtonStyle.success)
    async def Help(self,interaction:discord.Interaction,button:discord.ui.Button):
        await help_todo(interaction)

async def help_todo(interaction):
        help_embed = discord.Embed(title='Todo Commands Help', color=discord.Colour.blurple())

        help_embed.add_field(name='.todo [optional title] [optional member]', value='Creates a new todo list', inline=False)
        help_embed.add_field(name='.add <task>', value='Adds a task to the todo list', inline=False)
        help_embed.add_field(name='.rm <task_number>', value='Removes a task from the todo list', inline=False)
        help_embed.add_field(name='.e <task_number> <new_task>', value='Edits a task in the todo list', inline=False)
        help_embed.add_field(name='.uncheck <task_number>', value='Marks a completed task as incomplete', inline=False)
        help_embed.add_field(name='.complete <task_number>', value='Marks a task as completed', inline=False)
        help_embed.add_field(name='.help_todo', value='Displays this help message', inline=False)

        await interaction.response.send_message(embed=help_embed)
    

class todo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.todo_list_active = False
        self.tasks = {}
        self.num_complete = 0 
        self.name = ''
        self.pfp = 0
        
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("the bot is ready")

    @commands.command(name='todo', help='Creates a todo list')
    async def todo(self, ctx, *args, member: discord.Member = None):
        self.todo_list_active = True

        view = SimpleView()

        if member is None:
            member = ctx.author

        if len(args) == 0: 
            list_title = "TODO List"
        else:
            list_title = ' '.join(args)
            
        self.name = member.display_name
        self.pfp = member.display_avatar

        self.tasks = {}  # Reset tasks when a new todo list is created

        todo = discord.Embed(title= f"{list_title}", description="Add tasks using `.add <task>`", color=discord.Colour.blurple(), timestamp= datetime.now())
        todo.set_author(name=f"{self.name}", icon_url=f"{self.pfp}")

        await ctx.send(embed=todo, view = view)
        
    
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author == self.bot.user:
            return
        # print(f"message contents: {message.content}")
        # print(f"tasks: {len(self.tasks)}")
        if self.todo_list_active and (message.content.startswith('add ') or message.content.startswith('+ ')):
            task = message.content.split(' ')[1:]
            task = ' '.join(task)
            self.tasks[task] = 0
            # Update the embedded todo list
            await self.update_todo_embed(message.channel)

        elif self.todo_list_active and message.content.startswith('rm '):
            task_num = int(message.content.split(' ')[1:][0])
            keys_list = list(self.tasks.keys())
            task = keys_list[task_num - 1]
            if self.tasks[task] == 1:
                self.num_complete -=1
            self.tasks[task] = -1
            await self.update_todo_embed(message.channel)
        
        elif self.todo_list_active and message.content.startswith('e '):

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
        
        elif self.todo_list_active and message.content.startswith('uncheck '):
            task = int(message.content.split(' ')[1:][0])
            keys_list = list(self.tasks.keys())
            self.tasks[keys_list[task - 1]] = 0
            self.num_complete -= 1

            await self.update_todo_embed(message.channel)

        # PUT THIS LAST
        elif self.todo_list_active and 0 < int(message.content) <= len(self.tasks):
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

        todo = discord.Embed(title=f"TODO List ({self.num_complete}/{len(self.tasks)} complete)", description="Add tasks using ` add <task>`", color=discord.Colour.blurple(), timestamp= datetime.now())
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