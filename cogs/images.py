import discord
from discord.ext import commands
import PIL
from PIL import Image, ImageDraw, ImageFont
import time
import textwrap
import os
import pytesseract
import io

class Images(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

    @commands.command()
    async def car(self, ctx, car, first_board, second_board):
        car = textwrap.fill(car,7)
        first_board = textwrap.fill(first_board, 6)
        second_board = textwrap.fill(second_board,8)
        def do_edit():
            dir_path = os.path.dirname(os.path.realpath(__file__))
            car_path = dir_path + "/memes/car.jpg"
            img = Image.open(car_path)
            draw = ImageDraw.Draw(img)
            impact_path = dir_path + "/memes/impact.ttf"
            font = ImageFont.truetype(impact_path,40)
            draw.text((330, 515),car,(255,255,255),font=font)
            draw.text((190, 90),first_board,(255,255,255),font=font)
            draw.text((427, 90),second_board,(255,255,255),font=font)
            img.save("car-out.jpg")
            f = discord.File("car-out.jpg", filename="image.png")
            return f
        t1 = time.perf_counter()
        f =await self.bot.loop.run_in_executor(None,do_edit)
        t2 = time.perf_counter()
        t = round((t2-t1),2)
        gold = discord.Color.gold()
        em = discord.Embed(title = "Your Meme", description="Took "+ str(t) + " Seconds",color = gold)
        em.set_image(url= "attachment://image.png")
        em.set_footer(text="Requested by "+ ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(file = f, embed = em)
        
    @commands.command(aliases = ['tesseract'])
    async def ocr(self, ctx, language="eng"):
        '''Does OCR on the first attachment from the message'''
        try:
            image = Image.open(io.BytesIO(await ctx.message.attachments[0].read()))
            def tesseract():
                return pytesseract.image_to_string(image)
            text = await self.bot.loop.run_in_executor(None, tesseract)
            embed = discord.Embed(title="Text", description=text, lang=language)
            await ctx.send(embed=embed)
        except:
            await ctx.send("There was an error processing your image, make sure you sent an attachment and used a valid language (ISO 639 3-letter code).")

def setup(bot):
    bot.add_cog(Images(bot))