# -*- coding: utf-8 -*-
import httpx, os
from dotenv import load_dotenv
load_dotenv()

r = httpx.get(
    'https://openrouter.ai/api/v1/models',
    headers={'Authorization': 'Bearer ' + os.getenv('OPENROUTER_API_KEY')}
)
models = r.json()['data']
free = [m['id'] for m in models if ':free' in m['id']]
for m in free:
    print(m)
