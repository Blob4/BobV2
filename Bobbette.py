import os
import time
import discord
from discord.ext import commands
import whisper
import torch
import numpy as np
from dotenv import load_dotenv
from discord.ext import voice_recv
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


vc_instance = None
buffers = {}
current_model = None
transcribe_running = False
device = "cuda" if torch.cuda.is_available() else "cpu"

#audio
class WhisperSink(voice_recv.AudioSink):
    def __init__(self):
        super().__init__()
        self.buffers = {}

    def wants_opus(self) -> bool:
        return False

    def write(self, user, data):
        audio = np.frombuffer(data.pcm, np.int16).astype(np.float32) / 32768.0
        #audio = audio[::3] #change the kHz for whisper
        if np.abs(audio).mean() < 0.002: #skip air 🗣️
            return

        if user not in self.buffers: #different buffer for all users
            self.buffers[user] = []
        self.buffers[user].append(audio)

    def cleanup(self): #deletion from ze ram
        self.buffers.clear()

sink = WhisperSink()

#speech to text
async def transcribe_loop(channel):
    global transcribe_running, current_model, sink
    while transcribe_running:
        await asyncio.sleep(1)
        for user, arrs in list(sink.buffers.items()):
            if len(arrs) > 0 and sum(len(a) for a in arrs) >= 16000 * 3:  # 3 seconds <<<< important
                audio = np.concatenate(sink.buffers[user])
                sink.buffers[user] = []

                start_time = time.time()
                result = current_model.transcribe(audio, fp16=True) # use whisper ai to transcribe
                elapsed = time.time() - start_time

                text = result["text"].strip()
                if text:
                    await channel.send(
                        f"**{user.display_name}:** {text}\nstt time: {elapsed:.2f} seconds"
                    )

#!stt
@bot.command()
async def stt(ctx):
    global vc_instance, current_model, transcribe_running

    if not ctx.author.voice:
        await ctx.send("be in a vc silly")
        return

    if vc_instance and vc_instance.is_connected():
        await ctx.send("we are listening to your every word alr")
        return

    await ctx.send(f"loading medium model (english btw)...")
    current_model = whisper.load_model("medium.en").to(device)

    channel = ctx.author.voice.channel
    vc_instance = await channel.connect(cls=voice_recv.VoiceRecvClient)
    vc_instance.listen(sink)

    transcribe_running = True
    asyncio.create_task(transcribe_loop(channel))

    await ctx.send(f"joined {channel.name} to start stt")

#!stop
@bot.command()
async def stop(ctx):
    global vc_instance, transcribe_running, sink

    if not vc_instance or not vc_instance.is_connected():
        await ctx.send("i cant leave if i aint there")
        return

    transcribe_running = False
    vc_instance.stop_listening()
    await vc_instance.disconnect()
    vc_instance = None
    sink.cleanup()

    await ctx.send("stopped ✌️😭 twin")

@bot.event
async def on_voice_channel_effect(effect: discord.VoiceChannelEffect):
    print('effect detected')
    global vc_instance
    if effect.sound.id == 1213777673579528234 and effect.is_sound():
        print('leaving vc due to execution by firing squad')
        await vc_instance.disconnect()

#run
@bot.event
async def on_ready():
    print(f"{bot.user} alive")

bot.run(TOKEN)
