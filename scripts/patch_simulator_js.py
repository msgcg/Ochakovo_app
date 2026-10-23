import os

def run():
    path = os.path.join('static', 'js', 'simulator.js')
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()

    # 1. Video funcs
    old_video_funcs = """  // Управление видео-инструктажем мастера цеха
  function openVideoBriefingModal() {
    const modal = document.getElementById('och-video-briefing-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    const video = document.getElementById('och-briefing-video-player');
    if (video) {
      try {
        video.play().catch(() => {});
      } catch (e) {}
    }
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  function closeVideoBriefingModal() {
    const modal = document.getElementById('och-video-briefing-modal');
    if (modal) modal.style.display = 'none';
    const video = document.getElementById('och-briefing-video-player');
    if (video) {
      video.pause();
    }
  }"""

    new_video_funcs = """  // Управление видео-инструктажем мастера цеха (с поддержкой звука и Range 206)
  let currentActiveSpeech = '';

  function openVideoBriefingModal() {
    const modal = document.getElementById('och-video-briefing-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    const video = document.getElementById('och-briefing-video-player');
    if (video) {
      try {
        video.muted = false;
        video.volume = 1.0;
        video.currentTime = 0;
        const playPromise = video.play();
        if (playPromise !== undefined) {
          playPromise.catch((err) => {
            console.log('[Video] Browser autoplay policy required user click:', err);
          });
        }
      } catch (e) {
        console.warn('[Video] Play error:', e);
      }
    }
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  function closeVideoBriefingModal() {
    const modal = document.getElementById('och-video-briefing-modal');
    if (modal) modal.style.display = 'none';
    const video = document.getElementById('och-briefing-video-player');
    if (video) {
      try {
        video.pause();
      } catch (e) {}
    }
  }

  function toggleHistoryDrawer() {
    const drawer = document.getElementById('och-history-drawer');
    if (!drawer) return;
    drawer.classList.toggle('open');
    if (drawer.classList.contains('open')) {
      const list = document.getElementById('och-history-drawer-list');
      if (list) list.scrollTop = list.scrollHeight;
    }
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  function replayCurrentSpeech(btn) {
    if (currentActiveSpeech) {
      playMentorVoice(currentActiveSpeech, btn);
    } else {
      const activeTextEl = document.getElementById('och-vn-active-text');
      if (activeTextEl && activeTextEl.innerText.trim()) {
        playMentorVoice(activeTextEl.innerText.trim(), btn);
      }
    }
  }"""

    assert old_video_funcs in code, 'old_video_funcs not found'
    code = code.replace(old_video_funcs, new_video_funcs)

    # 2. Append turn
    old_turn_append = """    feed.appendChild(row);
    feed.scrollTop = feed.scrollHeight;

    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }"""

    new_turn_append = """    feed.appendChild(row);
    feed.scrollTop = feed.scrollHeight;

    // Обновляем диалоговую консоль визуальной новеллы
    currentActiveSpeech = text || '';
    const vnSpeakerBadge = document.getElementById('och-vn-speaker-badge');
    const vnSpeakerName = document.getElementById('och-vn-speaker-name');
    const vnSpeakerRole = document.getElementById('och-vn-speaker-role');
    const vnSpeakerAvatar = document.getElementById('och-vn-speaker-avatar');
    const vnActiveText = document.getElementById('och-vn-active-text');
    const vnActiveSub = document.getElementById('och-vn-active-sub');

    if (vnSpeakerBadge) {
      vnSpeakerBadge.className = `och-vn-speaker-badge ${role === 'candidate' ? 'intern' : 'mentor'}`;
    }
    if (vnSpeakerName) vnSpeakerName.innerText = name;
    if (vnSpeakerRole) vnSpeakerRole.innerText = role === 'candidate' ? 'Стажёр' : 'Наставник';
    if (vnSpeakerAvatar) vnSpeakerAvatar.src = avatarSrc;
    if (vnActiveText) vnActiveText.innerText = text;
    if (vnActiveSub) {
      if (subtext) {
        vnActiveSub.style.display = 'flex';
        vnActiveSub.innerHTML = `<i data-lucide="info" style="width: 14px; height: 14px; color: #B45309;"></i><span>${subtext}</span>`;
      } else {
        vnActiveSub.style.display = 'none';
      }
    }

    // Добавляем реплику в выдвижной журнал переговоров смены
    const histList = document.getElementById('och-history-drawer-list');
    if (histList) {
      const cloned = row.cloneNode(true);
      histList.appendChild(cloned);
      histList.scrollTop = histList.scrollHeight;
    }

    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }"""

    assert old_turn_append in code, 'old_turn_append not found'
    code = code.replace(old_turn_append, new_turn_append)

    # 3. DOMContentLoaded
    old_dom_init = """    // Инициализируем стрик и начальные значения датчиков
    renderStreakBadge();"""

    new_dom_init = """    // Инициализируем стрик и начальные значения датчиков
    renderStreakBadge();

    // Автоматически предлагаем обучающий видео-инструктаж перед началом смены
    const pathSlug = window.location.pathname.split('/').filter(Boolean).pop() || 'shift';
    const videoStorageKey = 'och_video_offered_' + pathSlug;
    if (!sessionStorage.getItem(videoStorageKey)) {
      setTimeout(() => {
        openVideoBriefingModal();
        sessionStorage.setItem(videoStorageKey, 'true');
      }, 500);
    }"""

    assert old_dom_init in code, 'old_dom_init not found'
    code = code.replace(old_dom_init, new_dom_init)

    # 4. Exports
    old_export = """    openVideoBriefingModal,
    closeVideoBriefingModal,
    updateStudentSprite
  };"""

    new_export = """    openVideoBriefingModal,
    closeVideoBriefingModal,
    toggleHistoryDrawer,
    replayCurrentSpeech,
    updateStudentSprite
  };"""

    assert old_export in code, 'old_export not found'
    code = code.replace(old_export, new_export)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)

    print('static/js/simulator.js patched successfully!')

if __name__ == '__main__':
    run()
