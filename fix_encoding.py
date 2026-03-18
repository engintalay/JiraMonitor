with open('monitor.py', 'rb') as f:
    raw = f.read()
bad = [(i, b) for i, b in enumerate(raw) if b > 127]
print(f'Total non-ASCII bytes: {len(bad)}')
for i, b in bad[:10]:
    print(f'  index {i}: 0x{b:02x}')
