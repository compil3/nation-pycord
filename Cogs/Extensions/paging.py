import discord


class FirstPageButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="<<")

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        embed = self.view.pages[0]
        view: PaginatorView = self.view
        self.view.currentpage = 1
        self.view.set_page(self.view.currentpage)
        await interaction.response.edit_message(embed=embed, view=self.view)


class LeftButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="<")

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: PaginatorView = self.view

        if self.view.currentpage == 1:
            embed = self.view.pages[-1]
            self.view.currentpage = self.view.last_page
        else:
            embed = self.view.pages[self.view.currentpage - 2]
            self.view.currentpage -= 1
        self.view.previous_page()
        await interaction.response.edit_message(embed=embed, view=self.view)


class RightButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label=">")

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: PaginatorView = self.view

        if self.view.currentpage == self.view.last_page:
            embed = self.view.pages[0]
            self.view.currentpage = 1
        else:
            embed = self.view.pages[self.view.currentpage]
            self.view.currentpage += 1
        self.view.next_page()
        await interaction.response.edit_message(embed=embed, view=self.view)


class PageCounter(discord.ui.Button):
    def __init__(self, lastpage):
        super().__init__(
            label=f"Page 1/{lastpage}",
            style=discord.ButtonStyle.grey,
            custom_id="page_counter",
            disabled=True,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class LastPage(discord.ui.Button):
    def __init__(self):
        super().__init__(label=">>", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None

        embed = self.view.pages[self.view.last_page - 1]
        self.view.currentpage = self.view.last_page
        self.view.set_page(self.view.currentpage)
        await interaction.response.edit_message(embed=embed, view=self.view)


class Cancel(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=None)
        self.view.stop()


class PaginatorView(discord.ui.View):
    def __init__(self, pages: list, ctx, msg: discord.Message = None):
        self.ctx = ctx
        self.currentpage = 1
        self.pages = pages
        self.last_page = len(pages)
        self.message = msg
        super().__init__()
        self.add_item(FirstPageButton())
        self.add_item(LeftButton())
        self.page_counter = PageCounter(self.last_page)
        self.add_item(self.page_counter)
        self.add_item(RightButton())
        self.add_item(LastPage())
        self.add_item(Cancel())

    async def on_timeout(self) -> None:
        try:
            await self.message.edit(view=None)
        except:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.ctx.author.id:
            return True
        await interaction.response.send_message(
            "Only the author of that command can use buttons.", ephemeral=True
        )
        return False

    def previous_page(self):
        if self.currentpage == self.last_page:
            self.page_counter.label = f"Page {self.last_page}/{self.last_page}"
        else:
            self.page_counter.label = f"Page {self.currentpage}/{self.last_page}"

    def set_page(self, pagenumber) -> None:
        self.page_counter.label = f"Page {self.currentpage}/{self.last_page}"

    def next_page(self):
        if self.currentpage == self.last_page + 1:
            self.page_counter.label = f"Page 1/{self.last_page}"
        else:
            self.page_counter.label = f"Page {self.currentpage}/{self.last_page}"
