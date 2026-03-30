import httpx
from pathlib import Path
p = Path('sample_note.txt')
p.write_text('Sample upload note\nThis is a test.')
with httpx.Client() as client:
    r = client.post('http://127.0.0.1:8000/api/notes/upload', files={'file': ('sample_note.txt', p.read_bytes(), 'text/plain')})
    print(r.status_code)
    print(r.text)
