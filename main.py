import asyncio
from aiohttp import web, ClientSession
import yt_dlp

async def handle_stream_video(request):
    video_url = request.query.get('url', '')
    if not video_url:
        return web.json_response({'error': 'No URL provided'}, status=400)

    try:
        ydl_opts = {
            'format': '18',  # 360p format for faster loading
            'extract_flat': 'in_playlist',
            'nocheckcertificate': True,
            'geo_bypass': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/',
            },
            'cookies': {},  # Add any necessary cookies here
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            video_stream_url = info_dict.get('url', None)
            if not video_stream_url:
                return web.json_response({'error': 'No suitable stream found'}, status=404)

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
            }
            async with ClientSession() as session:
                async with session.get(video_stream_url, headers=headers) as resp:
                    if resp.status != 200:
                        return web.json_response({'error': 'Failed to fetch video'}, status=500)

                    content_type = resp.headers.get('Content-Type', 'video/mp4')
                    content_disposition = f'attachment; filename="{info_dict.get("title", "video").replace("/", "_")}.mp4"'

                    response = web.StreamResponse(
                        headers={
                            'Content-Type': content_type,
                            'Content-Disposition': content_disposition
                        })
                    await response.prepare(request)

                    async for chunk in resp.content.iter_chunked(2 * 1024 * 1024):
                        await response.write(chunk)
                    await response.write_eof()
                    return response
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

async def init_app():
    app = web.Application()
    app.add_routes([web.get('/stream_video', handle_stream_video)])
    return app

async def main():
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print('Server started at http://localhost:8000')
    await asyncio.sleep(3600)  # Run for 1 hour

if __name__ == '__main__':
    asyncio.run(main())
