from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

replacements = [
    ('"focus_session_coins": 0,\n    "focus_seconds_today": 0,', '"focus_session_coins": 0,\n    "focus_coins_today": 0,\n    "focus_seconds_today": 0,'),
    ('"focus_last_duration_minutes": 25,', '"focus_last_duration_minutes": 30,'),
    ('FOCUS_COINS_PER_BLOCK = 2\nFOCUS_REWARD_BLOCK_SECONDS = 5 * 60\nFOCUS_BREAK_SECONDS = 5 * 60', 'FOCUS_COINS_PER_BLOCK = 5\nFOCUS_REWARD_BLOCK_SECONDS = 10 * 60\nFOCUS_DAILY_COIN_CAP = 30\nFOCUS_BREAK_SECONDS = 5 * 60'),
    ('    earned = new_blocks * FOCUS_COINS_PER_BLOCK\n    st.session_state.focus_rewarded_blocks = completed_blocks\n    st.session_state.focus_session_coins += earned\n    st.session_state.coins += earned\n    if toast:\n        st.toast(f"專注滿 {completed_blocks * 5} 分鐘，+{earned} 🪙")', '    potential = new_blocks * FOCUS_COINS_PER_BLOCK\n    remaining_cap = max(0, FOCUS_DAILY_COIN_CAP - int(st.session_state.focus_coins_today or 0))\n    earned = min(potential, remaining_cap)\n    st.session_state.focus_rewarded_blocks = completed_blocks\n    if earned <= 0:\n        return\n    st.session_state.focus_session_coins += earned\n    st.session_state.focus_coins_today += earned\n    st.session_state.coins += earned\n    if toast:\n        st.toast(f"專注滿 {completed_blocks * 10} 分鐘，+{earned} 🪙")'),
    ('尚未滿 5 分鐘的區段不會另外給金幣。', '尚未滿 10 分鐘的區段不會另外給金幣。'),
    ('每完整 5 分鐘 +{FOCUS_COINS_PER_BLOCK} 🪙　<span class="focus-earned">這次已獲得 {st.session_state.focus_session_coins} 🪙</span>', '每完整 10 分鐘 +{FOCUS_COINS_PER_BLOCK} 🪙，每日最多 {FOCUS_DAILY_COIN_CAP} 🪙　<span class="focus-earned">今天計時器已獲得 {st.session_state.focus_coins_today} 🪙</span>'),
    ('休息時間不累積金幣　<span class="focus-earned">這次已獲得 {st.session_state.focus_session_coins} 🪙</span>', '休息時間不累積金幣　<span class="focus-earned">今天計時器已獲得 {st.session_state.focus_coins_today} 🪙</span>'),
    ('["25 分鐘", "50 分鐘", "自訂"]', '["30 分鐘", "60 分鐘", "自訂"]'),
    ('minutes = 25 if choice == "25 分鐘" else 50', 'minutes = 30 if choice == "30 分鐘" else 60'),
    ('目前暫定：每完整 5 分鐘 +{FOCUS_COINS_PER_BLOCK} 🪙。金幣經濟之後再一起平衡。', '每完整 10 分鐘 +{FOCUS_COINS_PER_BLOCK} 🪙，休息時間不計；每天最多從計時器獲得 {FOCUS_DAILY_COIN_CAP} 🪙。'),
]

for old, new in replacements:
    if old not in text:
        raise RuntimeError(f'anchor not found: {old[:80]}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('updated focus timer rewards and preset durations')
