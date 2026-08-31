from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

old_css = '''    .focus-runner { position:absolute; bottom:34px; width:70px; height:55px; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; transform:translateX(-50%); box-shadow:inset -7px -9px 0 rgba(20,70,45,.08),0 8px 15px rgba(35,118,69,.13); z-index:4; transition:left .85s linear; animation:focusHop .65s ease-in-out infinite; }\n    .focus-runner::before,.focus-runner::after { content:\"\"; position:absolute; top:22px; width:6px; height:9px; border-radius:50%; background:#173b2b; }\n'''
new_css = '''    .focus-runner { position:absolute; bottom:34px; width:70px; height:55px; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; transform:translateX(-50%); box-shadow:inset -7px -9px 0 rgba(20,70,45,.08),0 8px 15px rgba(35,118,69,.13); z-index:4; transition:left .85s linear; animation:focusHop .65s ease-in-out infinite; }\n    .focus-runner.has-art { width:88px; height:72px; bottom:28px; border-radius:0; box-shadow:none; background:transparent !important; overflow:visible; }\n    .focus-runner.has-art::before,.focus-runner.has-art::after { display:none; }\n    .focus-runner.has-art .focus-runner-mouth { display:none; }\n    .focus-runner-art { width:100%; height:100%; object-fit:contain; display:block; filter:drop-shadow(0 7px 8px rgba(35,118,69,.12)); }\n    .focus-runner::before,.focus-runner::after { content:\"\"; position:absolute; top:22px; width:6px; height:9px; border-radius:50%; background:#173b2b; }\n'''
if '.focus-runner.has-art {' not in text:
    if old_css not in text:
        raise RuntimeError('focus runner css anchor not found')
    text = text.replace(old_css, new_css, 1)

old_mobile = '''        .focus-runner { width:60px; height:47px; }\n        .focus-runner::before,.focus-runner::after { top:19px; width:5px; height:8px; }\n'''
new_mobile = '''        .focus-runner { width:60px; height:47px; }\n        .focus-runner.has-art { width:76px; height:62px; bottom:27px; }\n        .focus-runner::before,.focus-runner::after { top:19px; width:5px; height:8px; }\n'''
if '.focus-runner.has-art { width:76px;' not in text:
    if old_mobile not in text:
        raise RuntimeError('mobile focus runner css anchor not found')
    text = text.replace(old_mobile, new_mobile, 1)

old_markup = '''    resting_class = \" resting\" if resting else \"\"\n    sleep = '<span class=\"focus-sleep\">💤</span>' if resting else \"\"\n    return (\n        '<div class=\"focus-path\">'\n        f'<div class=\"focus-path-fill\" style=\"width:{fill:.2f}%\"></div>'\n        f'<div class=\"focus-runner{resting_class}\" style=\"left:{left:.2f}%;background:{background}\">'\n        f'{sleep}<div class=\"focus-runner-mouth\"></div></div>'\n        '<div class=\"focus-finish\">🏁</div></div>'\n    )\n'''
new_markup = '''    resting_class = \" resting\" if resting else \"\"\n    sleep = '<span class=\"focus-sleep\">💤</span>' if resting else \"\"\n    selected_item = slime_data(st.session_state.selected_slime)\n    asset_path = Path(f\"assets/slimes/{selected_item.get('theme')}.PNG\")\n    if asset_path.exists():\n        art_uri = _local_asset_data_uri(asset_path)\n        safe_alt = html.escape(st.session_state.selected_slime)\n        runner_class = f\"focus-runner has-art{resting_class}\"\n        runner_inner = f'{sleep}<img class=\"focus-runner-art\" src=\"{art_uri}\" alt=\"{safe_alt}\">'\n        runner_style = f\"left:{left:.2f}%;\"\n    else:\n        runner_class = f\"focus-runner{resting_class}\"\n        runner_inner = f'{sleep}<div class=\"focus-runner-mouth\"></div>'\n        runner_style = f\"left:{left:.2f}%;background:{background}\"\n    return (\n        '<div class=\"focus-path\">'\n        f'<div class=\"focus-path-fill\" style=\"width:{fill:.2f}%\"></div>'\n        f'<div class=\"{runner_class}\" style=\"{runner_style}\">{runner_inner}</div>'\n        '<div class=\"focus-finish\">🏁</div></div>'\n    )\n'''
if 'runner_class = f\"focus-runner has-art' not in text:
    if old_markup not in text:
        raise RuntimeError('focus runner markup anchor not found')
    text = text.replace(old_markup, new_markup, 1)

path.write_text(text, encoding='utf-8')
print('focus timer now uses selected slime artwork')
