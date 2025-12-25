#!/usr/bin/env python3
"""Upload backlog of elite videos to YouTube"""

import asyncio
from pathlib import Path
from engines.uploaders import YouTubeUploader

TOPICS = [
    'The Wealth Transfer Happening Now',
    'Why the Middle Class is Disappearing', 
    'The Hidden Tax Stealing Your Wealth',
    'Why Banks Want You Broke',
    'The Psychology of Why You Stay Poor',
    'The Credit Card Hack Banks Hate'
]

async def upload_backlog():
    # Get elite videos over 30MB (properly rendered)
    videos = [v for v in Path('data/output').glob('elite_*.mp4') 
              if v.stat().st_size > 30_000_000 and 'v2' not in v.name]
    videos = sorted(videos, key=lambda x: x.stat().st_mtime, reverse=True)[:6]
    
    print(f'Found {len(videos)} backlog videos to upload')
    u = YouTubeUploader()
    
    for i, v in enumerate(videos):
        title = TOPICS[i] if i < len(TOPICS) else f'Money Secret #{i+1}'
        print(f'\n[{i+1}/{len(videos)}] Uploading: {v.name}')
        print(f'Title: "{title}"')
        
        result = await u.upload_short(
            str(v),
            f'{title} 💰',
            f'{title}. The financial truth they hide from you.\n\n#money #wealth #finance #shorts',
            ['money', 'wealth', 'finance', 'investing', 'rich']
        )
        print(f'Result: {result}')
        
        if result.get('success'):
            print(f'✅ LIVE: {result.get("url")}')
        
        await asyncio.sleep(45)  # Rate limit between uploads

if __name__ == '__main__':
    asyncio.run(upload_backlog())
