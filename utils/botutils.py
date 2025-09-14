import aiofiles
import aiohttp

async def download_squad_icon(icon_url: str, squad_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(icon_url) as resp:
            data = await resp.read()
    filename = f"static/public/squads/{squad_id}.jpg"
    async with aiofiles.open(filename, 'wb') as f:
        await f.write(data)
        
    return filename