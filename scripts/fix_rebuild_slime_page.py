from pathlib import Path
p=Path('scripts/rebuild_slime_page.py')
s=p.read_text(encoding='utf-8')
old="s,n=re.subn(r'def slime_page\\(\\):.*?\\n\\ndef achievements_page\\(\\):',page+'\\n\\ndef achievements_page():',s,count=1,flags=re.S)"
new="s,n=re.subn(r'def slime_page\\(\\):.*?\\n\\ndef achievements_page\\(\\):',lambda m: page+'\\n\\ndef achievements_page():',s,count=1,flags=re.S)"
if old not in s: raise RuntimeError('replacement anchor not found')
p.write_text(s.replace(old,new,1),encoding='utf-8')
