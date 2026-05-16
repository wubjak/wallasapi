import os
import sys
from dotenv import load_dotenv

# Make 'wallasAPI' importable from tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv('wallasAPI/.env')
from wallasAPI.router import AIRouter

r = AIRouter()
result = r.generate_image('A beautiful sunset over snowy mountains, digital art', 'nvidia', 'flux.1-schnell')
if result:
    print('SUCCESS')
    print(f'Filename: {result["filename"]}')
    print(f'Base64 length: {len(result.get("b64_data", ""))}')
else:
    print('FAILED')
