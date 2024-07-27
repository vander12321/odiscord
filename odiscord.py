import discord
from discord.ext import commands
import requests
import json
import asyncio
import traceback

# Bot configuration
TOKEN = 'DISCORD_BOT_TOKEN_HERE' # CHANGE THIS!
OLLAMA_URL = 'http://localhost:11434/api/generate'  # Adjust if your Ollama instance is not local

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True  # Enable DM messages
bot = commands.Bot(command_prefix='!', intents=intents)

def generate_response(content):
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "dolphin-llama3", # Change this if you do not want dolphin-llama3
            "prompt": content
        }, stream=True)
        
        response.raise_for_status()  # Raise an exception for bad status codes
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        full_response += json_response['response']
                    if json_response.get('done', False):
                        break
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error on line: {e}")
                    print("Problematic line:", line)
        return full_response
    except requests.RequestException as e:
        print(f"Request Exception: {e}")
        return None

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    if (bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel)) and not message.author.bot:
        content = message.content.replace(f'<@!{bot.user.id}>', '').strip()
        
        async with message.channel.typing():
            try:
                response = await asyncio.to_thread(generate_response, content)
                
                if response:
                    # Split long messages if they exceed Discord's character limit
                    max_length = 1994  # 2000 - 6 characters for mention
                    chunks = [response[i:i+max_length] for i in range(0, len(response), max_length)]
                    
                    # Send the first chunk with the mention
                    first_chunk = f"{message.author.mention} {chunks[0]}"
                    await message.channel.send(first_chunk)
                    
                    # Send any remaining chunks without the mention
                    for chunk in chunks[1:]:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(f"{message.author.mention} I'm sorry, but I couldn't generate a response. There might be an issue with the language model.")
            except Exception as e:
                print(f"Error generating response: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                await message.channel.send(f"{message.author.mention} Sorry, I encountered an error while generating a response. Error details: {str(e)}")

    await bot.process_commands(message)

bot.run(TOKEN)