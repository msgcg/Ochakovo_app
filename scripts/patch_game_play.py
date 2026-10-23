import os

def run():
    target_path = os.path.join('careers', 'templates', 'careers', 'game_play.html')
    with open(target_path, 'r', encoding='utf-8') as f:
        text = f.read()

    start_marker = '  <!-- 2. ПРОСТОРНАЯ ГЛАВНАЯ СЦЕНА (ВИЗУАЛЬНАЯ НОВЕЛЛА ОЧАКОВО) -->'
    end_marker = '<!-- МОДАЛЬНОЕ ОКНО УСПЕХА СМЕНЫ И КАРЬЕРНОГО МЭТЧА -->'

    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print('Markers not found! start:', start_idx, 'end:', end_idx)
        return

    new_section = """  <!-- 2. СЦЕНА ВИЗУАЛЬНОЙ НОВЕЛЛЫ «ОЧАКОВО» -->
  <div class="och-vn-stage" style="background-image: url('{% static 'img/' %}{{ scenario.bg_image }}');">
    <div class="och-vn-stage-halftone"></div>
    
    <!-- Анимированные пузырьки брожения Очаково -->
    <div class="och-carbonation-container">
      <div class="och-fizzy-bubble" style="left: 12%; width: 14px; height: 14px; animation-duration: 7s; animation-delay: 0s;"></div>
      <div class="och-fizzy-bubble" style="left: 28%; width: 22px; height: 22px; animation-duration: 9s; animation-delay: 2s;"></div>
      <div class="och-fizzy-bubble" style="left: 48%; width: 12px; height: 12px; animation-duration: 6s; animation-delay: 1s;"></div>
      <div class="och-fizzy-bubble" style="left: 68%; width: 18px; height: 18px; animation-duration: 8s; animation-delay: 3s;"></div>
      <div class="och-fizzy-bubble" style="left: 84%; width: 24px; height: 24px; animation-duration: 10s; animation-delay: 1.5s;"></div>
    </div>

    <!-- Верхняя строка сцены: статус инцидента и контролы -->
    <div class="och-vn-stage-top">
      <div class="och-incident-pill">
        <span class="och-status-dot"></span>
        <span>Инцидент: {{ scenario.title }}</span>
      </div>
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <button type="button" class="och-hud-video-btn" onclick="simulator.openVideoBriefingModal()" title="Смотреть реальный видео-инструктаж наставника (30 сек)" style="background: rgba(255,255,255,0.95);">
          <i data-lucide="video" style="width: 14px; height: 14px; color: var(--och-red);"></i>
          <span>Видео цеха</span>
        </button>
        <button type="button" class="och-comic-btn-log" onclick="simulator.toggleHistoryDrawer()" title="Открыть полный журнал реплик смены">
          <i data-lucide="book-open" style="width: 14px; height: 14px;"></i>
          <span>История смены</span>
        </button>
      </div>
    </div>

    <!-- СЛОЙ ПЕРСОНАЖЕЙ НА ПОЛУ СЦЕНЫ (ВИЗУАЛЬНАЯ НОВЕЛЛА) -->
    <div class="och-vn-stage-floor">
      <!-- Студент-стажёр слева -->
      <div class="och-vn-character intern" id="vn-actor-student">
        <div class="och-vn-sprite-wrap">
          <img src="{% static 'img/vn_sprites/student_neutral.png' %}" onerror="this.src='{% static 'img/avatar_student.jpg' %}'" alt="Стажёр" class="och-vn-sprite" id="vn-sprite-student">
        </div>
        <div class="och-comic-nametag intern-tag" id="vn-tag-student">
          <i data-lucide="user" style="width: 12px; height: 12px;"></i>
          <span>Стажёр (Вы)</span>
        </div>
      </div>

      <!-- Живые анимированные маскоты завода по центру -->
      <div class="och-vn-stage-center-mascot">
        <div class="och-mascot-unit" id="och-mascot-unit">
          <!-- 1. Танцующая банка кваса Очаково -->
          <svg id="och-mascot-can" class="och-dancing-can" viewBox="0 0 100 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="25" y="20" width="50" height="75" rx="6" fill="#D50032" stroke="#A00024" stroke-width="2"/>
            <ellipse cx="50" cy="20" rx="25" ry="8" fill="#F59E0B"/>
            <ellipse cx="50" cy="95" rx="25" ry="8" fill="#82001E"/>
            <rect x="25" y="42" width="50" height="24" fill="#F8FAFC"/>
            <text x="50" y="58" font-size="10" font-weight="900" fill="#D50032" text-anchor="middle" font-family="sans-serif">ОЧАКОВО</text>
            <rect x="34" y="28" width="14" height="9" rx="2" fill="#0F172A"/>
            <rect x="52" y="28" width="14" height="9" rx="2" fill="#0F172A"/>
            <line x1="48" y1="32" x2="52" y2="32" stroke="#0F172A" stroke-width="2"/>
            <path d="M25 45 C10 40 12 25 5 35" stroke="#F59E0B" stroke-width="4" stroke-linecap="round"/>
            <path d="M75 45 C90 40 88 25 95 35" stroke="#F59E0B" stroke-width="4" stroke-linecap="round"/>
            <path d="M38 100 L32 114" stroke="#0F172A" stroke-width="4" stroke-linecap="round"/>
            <path d="M62 100 L68 114" stroke="#0F172A" stroke-width="4" stroke-linecap="round"/>
          </svg>

          <!-- 2. Танцующая килька с кружкой кваса -->
          <svg id="och-mascot-sprat" class="och-dancing-sprat" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 50 C30 30 75 35 95 50 C75 65 30 70 15 50 Z" fill="#94A3B8" stroke="#475569" stroke-width="2"/>
            <path d="M15 50 L2 36 L6 50 L2 64 Z" fill="#64748B"/>
            <path d="M85 38 C90 32 98 32 104 38 L92 38 Z" fill="#D50032"/>
            <ellipse cx="98" cy="38" rx="8" ry="3" fill="#D50032"/>
            <circle cx="88" cy="46" r="3" fill="#0F172A"/>
            <circle cx="89" cy="45" r="1" fill="#FFFFFF"/>
            <path d="M92 53 C90 56 84 56 82 53" stroke="#0F172A" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M55 52 C50 62 42 60 40 50" stroke="#64748B" stroke-width="3" stroke-linecap="round"/>
            <rect x="32" y="44" width="10" height="13" rx="2" fill="#F59E0B" stroke="#B45309" stroke-width="1"/>
            <ellipse cx="37" cy="44" rx="6" ry="3" fill="#FFFFFF"/>
          </svg>

          <!-- 3. Чайный гриб в банке -->
          <svg id="och-mascot-kombucha" class="och-mascot-kombucha" viewBox="0 0 100 110" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: none;">
            <rect x="20" y="30" width="60" height="70" rx="8" fill="rgba(224, 242, 254, 0.4)" stroke="#38BDF8" stroke-width="2"/>
            <path d="M28 30 L28 20 L72 20 L72 30" stroke="#38BDF8" stroke-width="2" fill="none"/>
            <ellipse cx="50" cy="18" rx="26" ry="6" fill="#F8FAFC" stroke="#94A3B8" stroke-width="1.5"/>
            <line x1="24" y1="22" x2="76" y2="22" stroke="#D97706" stroke-width="2" stroke-linecap="round"/>
            <rect x="22" y="42" width="56" height="56" rx="6" fill="rgba(217, 119, 6, 0.25)"/>
            <ellipse cx="50" cy="62" rx="22" ry="10" fill="#B45309"/>
            <ellipse cx="50" cy="58" rx="20" ry="8" fill="#D97706"/>
            <ellipse cx="50" cy="55" rx="18" ry="6" fill="#F59E0B"/>
            <circle cx="44" cy="56" r="2.5" fill="#0F172A"/>
            <circle cx="56" cy="56" r="2.5" fill="#0F172A"/>
            <circle cx="45" cy="55" r="0.8" fill="#FFFFFF"/>
            <circle cx="57" cy="55" r="0.8" fill="#FFFFFF"/>
            <path d="M48 61 C50 63 52 63 54 61" stroke="#0F172A" stroke-width="1.5" stroke-linecap="round"/>
          </svg>

          <!-- 4. Жёлтая бочка кваса -->
          <svg id="och-mascot-barrel" class="och-mascot-barrel" viewBox="0 0 110 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: none;">
            <rect x="25" y="24" width="60" height="48" rx="12" fill="#FBBF24" stroke="#D97706" stroke-width="2"/>
            <ellipse cx="85" cy="48" rx="8" ry="24" fill="#F59E0B" stroke="#D97706" stroke-width="2"/>
            <line x1="42" y1="24" x2="42" y2="72" stroke="#B45309" stroke-width="2"/>
            <line x1="68" y1="24" x2="68" y2="72" stroke="#B45309" stroke-width="2"/>
            <text x="55" y="52" font-size="10" font-weight="900" fill="#D50032" text-anchor="middle" font-family="sans-serif">КВАС</text>
            <path d="M25 54 L12 54 L12 62" stroke="#78350F" stroke-width="3" stroke-linecap="round"/>
            <circle cx="12" cy="66" r="2.5" fill="#FBBF24"/>
            <circle cx="42" cy="76" r="12" fill="#334155" stroke="#0F172A" stroke-width="2"/>
            <circle cx="74" cy="76" r="12" fill="#334155" stroke="#0F172A" stroke-width="2"/>
          </svg>

          <!-- 5. Роборука Krones -->
          <svg id="och-mascot-robot" class="och-mascot-robot" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: none;">
            <rect x="35" y="78" width="30" height="14" rx="3" fill="#334155" stroke="#0F172A" stroke-width="2"/>
            <circle cx="50" cy="76" r="8" fill="#EA580C" stroke="#9A3412" stroke-width="2"/>
            <path d="M50 76 L40 45" stroke="#F97316" stroke-width="6" stroke-linecap="round"/>
            <circle cx="40" cy="45" r="7" fill="#334155" stroke="#0F172A" stroke-width="2"/>
            <circle cx="40" cy="45" r="3" fill="#38BDF8"/>
            <path d="M40 45 L68 30" stroke="#F97316" stroke-width="5" stroke-linecap="round"/>
            <rect x="74" y="22" width="12" height="18" rx="2" fill="#D50032"/>
          </svg>
        </div>

        <div class="och-mascot-speech" id="och-mascot-comment">
          «Килька в деле — квас в теле! Следим за балансом брожения!»
        </div>
      </div>

      <!-- Наставник цеха справа -->
      <div class="och-vn-character mentor" id="vn-actor-mentor">
        <div class="och-vn-sprite-wrap">
          <img src="{% static 'img/vn_sprites/' %}{{ scenario.mentor_avatar|slice:':-4' }}_bust.png" onerror="this.src='{% static 'img/' %}{{ scenario.mentor_avatar }}'" alt="{{ scenario.mentor_name }}" class="och-vn-sprite" id="vn-sprite-mentor">
        </div>
        <div class="och-comic-nametag mentor-tag" id="vn-tag-mentor">
          <i data-lucide="award" style="width: 12px; height: 12px;"></i>
          <span>{{ scenario.mentor_name }}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- 3. ДИАЛОГОВАЯ КОМИКС-КОНСОЛЬ ВИЗУАЛЬНОЙ НОВЕЛЛЫ -->
  <div class="och-vn-console">
    <!-- Плашка говорящего и аудиоплеер реплики -->
    <div class="och-vn-console-header">
      <div class="och-vn-speaker-badge mentor" id="och-vn-speaker-badge">
        <img src="{% static 'img/' %}{{ scenario.mentor_avatar }}" alt="" id="och-vn-speaker-avatar" style="width: 26px; height: 26px; border-radius: 4px; object-fit: cover; border: 1.5px solid #1E293B;">
        <span id="och-vn-speaker-name">{{ current_node.speaker_name }}</span>
        <span class="och-speaker-role-pill" id="och-vn-speaker-role">Наставник</span>
      </div>

      <div class="och-vn-console-tools">
        <button type="button" class="och-comic-btn-audio" id="och-vn-audio-replay-btn" onclick="simulator.playMentorVoice('{{ current_node.dialogue_text|escapejs }}', this)" title="Озвучить текущую реплику наставника">
          <i data-lucide="volume-2" style="width: 14px; height: 14px;"></i>
          <span>Озвучить</span>
        </button>
      </div>
    </div>

    <!-- Текстовое поле текущей реплики (Visual Novel Typewriter Box) -->
    <div class="och-vn-text-box">
      <div class="och-vn-active-text" id="och-vn-active-text">{{ current_node.dialogue_text }}</div>
      {% if current_node.narrative_context %}
      <div class="och-vn-context-note" id="och-vn-active-sub">
        <i data-lucide="info" style="width: 14px; height: 14px; color: #B45309;"></i>
        <span>{{ current_node.narrative_context }}</span>
      </div>
      {% else %}
      <div class="och-vn-context-note" id="och-vn-active-sub" style="display: none;"></div>
      {% endif %}
    </div>

    <!-- Интерактивно всплывающие чипы действий (Action Chips) -->
    <div class="och-action-chips-wrapper" id="och-action-chips-wrapper">
      <div class="och-action-chips-header">
        <span>Быстрые действия и тактические решения смены:</span>
        <button type="button" class="och-action-chip och-action-chip-tool" onclick="simulator.toggleToolDrawer()" style="padding: 0.35rem 0.75rem; font-size: 0.76rem;">
          <i data-lucide="wrench" style="width: 13px; height: 13px;"></i>
          <span>Оборудование цеха (8)</span>
        </button>
      </div>

      <div class="och-action-chips-row" id="och-choices-container">
        {% for choice in choices %}
        <button type="button" class="och-action-chip" onclick="simulator.chooseAction({{ choice.id }}, this)">
          <i data-lucide="zap" style="width: 15px; height: 15px; color: var(--och-red);"></i>
          <span>{{ choice.choice_text }}</span>
        </button>
        {% empty %}
        <button type="button" class="och-action-chip" onclick="simulator.useEquipment('valve_cooling', 'Охлаждение рубашки ЦКТ')">
          <i data-lucide="snowflake" style="width: 15px; height: 15px; color: var(--och-cyan);"></i>
          <span>Охладить сусло гликолем (-3°C)</span>
        </button>
        <button type="button" class="och-action-chip" onclick="simulator.useEquipment('starter_culture', 'Закваска натурального брожения 1978')">
          <i data-lucide="flask-conical" style="width: 15px; height: 15px; color: var(--och-gold);"></i>
          <span>Добавить закваску 1978</span>
        </button>
        <button type="button" class="och-action-chip och-action-chip-hint" onclick="simulator.requestHint()">
          <i data-lucide="help-circle" style="width: 15px; height: 15px; color: var(--och-gold);"></i>
          <span>Спросить совет {{ scenario.mentor_name }}</span>
        </button>
        {% endfor %}
      </div>
    </div>

    <!-- Всплывающий ящик оборудования цеха -->
    <div class="och-tool-drawer" id="och-tool-drawer">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
        <div style="font-size: 0.85rem; font-weight: 800; color: var(--och-text-heading); display: flex; align-items: center; gap: 0.4rem;">
          <i data-lucide="wrench" style="width: 16px; height: 16px; color: var(--och-cyan);"></i>
          <span>Панель управления цехом и приборы мастера</span>
        </div>
        <button type="button" onclick="simulator.toggleToolDrawer()" style="background: none; border: none; font-size: 0.8rem; color: var(--och-text-dim); cursor: pointer;">
          Закрыть ✕
        </button>
      </div>

      <div class="och-tool-drawer-grid">
        <div class="och-tool-mini-card" onclick="simulator.useEquipment('valve_cooling', 'Клапан охлаждения рубашки ЦКТ')">
          <img src="{% static 'img/brand_icons/cooling_pipe.png' %}" onerror="this.src='{% static 'img/equipment/valve_cooling.svg' %}'" alt="Охлаждение" class="och-tool-mini-svg">
          <div class="och-tool-mini-name">Охлаждение ЦКТ</div>
        </div>

        <div class="och-tool-mini-card" onclick="simulator.useEquipment('starter_culture', 'Закваска натурального брожения 1978')">
          <img src="{% static 'img/brand_icons/yeast_culture.png' %}" onerror="this.src='{% static 'img/equipment/starter_culture.svg' %}'" alt="Закваска" class="och-tool-mini-svg">
          <div class="och-tool-mini-name">Закваска 1978</div>
        </div>

        <div class="och-tool-mini-card" onclick="simulator.useEquipment('cip_wash', 'Пульт контура CIP-мойки')">
          <img src="{% static 'img/brand_icons/boiler_valve.png' %}" onerror="this.src='{% static 'img/equipment/cip_wash.svg' %}'" alt="CIP-мойка" class="och-tool-mini-svg">
          <div class="och-tool-mini-name">CIP-мойка</div>
        </div>

        <div class="och-tool-mini-card" onclick="simulator.useEquipment('emergency_stop', 'Кнопка аварийного останова конвейера')">
          <img src="{% static 'img/brand_icons/conveyor_bottles.png' %}" onerror="this.src='{% static 'img/equipment/emergency_stop.svg' %}'" alt="Стоп" class="och-tool-mini-svg">
          <div class="och-tool-mini-name">Аварийный стоп</div>
        </div>

        <div class="och-tool-mini-card" onclick="simulator.useEquipment('refractometer', 'Оптический рефрактометр сахаров Brix')">
          <img src="{% static 'img/brand_icons/thermometer.png' %}" onerror="this.src='{% static 'img/equipment/refractometer.svg' %}'" alt="Рефрактометр" class="och-tool-mini-svg">
          <div class="och-tool-mini-name">Рефрактометр</div>
        </div>

        <div class="och-tool-mini-card" onclick="simulator.useEquipment('tasting_mug', 'Органолептическая проба кваса')">
          <img src="{% static 'img/brand_icons/cup_tasting.png' %}" onerror="this.src='{% static 'img/equipment/tasting_mug.svg' %}'" alt="Дегустация" class="och-tool-mini-svg">
          <div class="och-tool-mini-name">Дегустация</div>
        </div>

        <div class="och-tool-mini-card" onclick="simulator.useEquipment('intercom_radio', 'Интерком диспетчера производства')">
          <img src="{% static 'img/brand_icons/fermentation_cct.png' %}" onerror="this.src='{% static 'img/equipment/intercom_radio.svg' %}'" alt="Интерком" class="och-tool-mini-svg">
          <div class="och-tool-mini-name">Интерком связи</div>
        </div>

        <div class="och-tool-mini-card" onclick="simulator.useEquipment('ph_meter', 'Лабораторный экспресс pH-метр')">
          <img src="{% static 'img/brand_icons/lab_flask.png' %}" onerror="this.src='{% static 'img/equipment/ph_meter.svg' %}'" alt="pH-метр" class="och-tool-mini-svg">
          <div class="och-tool-mini-name">pH-метр</div>
        </div>
      </div>
    </div>

    <!-- Нижняя панель ввода стажёра -->
    <div class="och-sim-input-bar">
      <!-- Баннер активной голосовой записи / рации -->
      <div id="och-mic-banner" class="och-mic-banner" style="display: none;">
        <div class="och-mic-banner-left">
          <div class="och-mic-pulse-dot"></div>
          <div class="och-mic-waves">
            <div class="och-mic-wave-bar"></div>
            <div class="och-mic-wave-bar"></div>
            <div class="och-mic-wave-bar"></div>
            <div class="och-mic-wave-bar"></div>
          </div>
          <span id="och-mic-banner-text">Рация мастера активна... Говорите в микрофон</span>
        </div>
        <button type="button" class="och-mic-banner-btn" onclick="simulator.stopVoiceRecording()">
          <span>Завершить</span>
        </button>
      </div>

      <div class="och-sim-input-row">
        <button type="button" id="och-mic-btn" class="och-ptt-mini-btn" onclick="simulator.toggleVoiceRecording()" title="Нажмите для голосовой передачи (Push-to-Talk)">
          <i data-lucide="mic" style="width: 20px; height: 20px;"></i>
        </button>

        <form onsubmit="simulator.sendTextTurn(event)" style="display: flex; gap: 0.65rem; flex: 1; min-width: 0;">
          <input type="text" id="och-sim-text-input" class="och-text-input" placeholder="Решение или вопрос наставнику..." autocomplete="off">
          <button type="submit" class="och-text-submit-btn">
            <span>Сказать</span>
            <i data-lucide="send" style="width: 15px; height: 15px;"></i>
          </button>
        </form>
      </div>
    </div>

    <!-- Скрытый контейнер для совместимости ленты реплик -->
    <div class="och-sim-dialogue-feed" id="och-chat-feed" data-mentor-avatar="{{ scenario.mentor_avatar }}" style="display: none;"></div>
  </div>

</div>

<!-- ВЫЕЗДНОЙ ЖУРНАЛ ИСТОРИИ ПЕРЕГОВОРОВ СМЕНЫ -->
<div id="och-history-drawer" class="och-history-drawer">
  <div class="och-history-drawer-header">
    <div>
      <div style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; color: var(--och-red);">АО МПБК «Очаково»</div>
      <h3 style="margin: 0; font-size: 1.1rem; font-weight: 900; color: #1E293B;">Журнал переговоров смены</h3>
    </div>
    <button type="button" onclick="simulator.toggleHistoryDrawer()" style="background: none; border: 2px solid #1E293B; border-radius: 6px; padding: 0.35rem 0.75rem; cursor: pointer; font-weight: 800; font-size: 0.85rem; color: #1E293B;">
      ✕ Закрыть
    </button>
  </div>
  <div class="och-history-drawer-body" id="och-history-drawer-list">
    <div class="och-chat-row mentor">
      <div class="och-speaker-col">
        <img src="{% static 'img/' %}{{ scenario.mentor_avatar }}" alt="{{ scenario.mentor_name }}" class="och-speaker-avatar">
        <span class="och-speaker-role-pill">Наставник</span>
      </div>
      <div class="och-bubble">
        <div class="och-bubble-head">
          <span class="och-speaker-name">{{ current_node.speaker_name }}</span>
          <button type="button" class="och-bubble-audio-btn" onclick="simulator.playMentorVoice('{{ current_node.dialogue_text|escapejs }}', this)">
            <i data-lucide="volume-2" style="width: 14px; height: 14px;"></i>
            <span>Озвучить</span>
          </button>
        </div>
        <div class="och-bubble-text">{{ current_node.dialogue_text }}</div>
        {% if current_node.narrative_context %}
        <div class="och-bubble-sub">
          <i data-lucide="info" style="width: 14px; height: 14px; color: var(--och-red);"></i>
          <span>{{ current_node.narrative_context }}</span>
        </div>
        {% endif %}
      </div>
    </div>
  </div>
</div>
"""

    updated = text[:start_idx] + new_section + '\n\n' + text[end_idx:]
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(updated)
    print('Updated successfully!')

if __name__ == '__main__':
    run()
