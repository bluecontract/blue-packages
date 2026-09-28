from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST.json').read_text())
for item in manifest['examples']:
    assert hashlib.sha256((root/item['file']).read_bytes()).hexdigest()==item['sha256'],item['file']
    assert item['result']=='PASS'
print('PASS:',len(manifest['examples']),'positive example files verified')
