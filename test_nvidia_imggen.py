import os
from dotenv import load_dotenv
load_dotenv('ai_services/.env')
from ai_services.router import AIRouter

r = AIRouter()
result = r.generate_image('A beautiful sunset over snowy mountains, digital art', 'nvidia', 'flux.1-schnell')
if result:
    print('SUCCESS')
    print(f'Filename: {result["filename"]}')
    print(f'Base64 length: {len(result.get("b64_data", ""))}')
else:
    print('FAILED')
