/**
 * ОЧАКОВО: ИНТЕРАКТИВНЫЙ СИМУЛЯТОР ЗАВОДА (SIMULATOR.JS)
 * Молодежная карьерная платформа АО МПБК «Очаково» 2026
 * Chat-first интерфейс, интерактивно всплывающие чипы действий (Action Chips),
 * голосовая рация PTT с поддержкой Web Audio и распознавания речи,
 * живые анимированные маскоты: Банка Очаково, Килька, Чайный гриб, Жёлтая бочка и Роборука Krones.
 */

window.simulator = (function () {
  'use strict';

  let currentAudio = null;
  let persistentAudio = null;
  let audioUnlocked = false;
  let recognition = null;
  let isRecording = false;
  let audioStream = null;
  let audioContext = null;
  let analyser = null;
  let animFrameId = null;
  let recognizedSpeechText = '';
  let mediaRecorder = null;
  let audioChunks = [];

  // Разблокировка аудио в браузере по первому пользовательскому действию
  function unlockAudio() {
    if (audioUnlocked) return;
    try {
      if (!persistentAudio) {
        persistentAudio = new Audio();
      }
      persistentAudio.src = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';
      const p = persistentAudio.play();
      if (p !== undefined) {
        p.then(() => {
          audioUnlocked = true;
          persistentAudio.pause();
          persistentAudio.currentTime = 0;
        }).catch(() => {});
      } else {
        audioUnlocked = true;
      }
    } catch (e) {
      console.warn('[Audio] Unlock error:', e);
    }
  }

  // Определение типа голоса наставника (мужской / женский)
  function getMentorVoiceType() {
    const hud = document.getElementById('och-sim-hud');
    const mentorName = (hud?.dataset?.mentorName || '').toLowerCase();
    if (mentorName.includes('елен') || mentorName.includes('анн')) {
      return 'female';
    }
    return 'male';
  }

  // Получение CSRF токена Django из cookie или DOM
  function getCsrfToken() {
    if (window.getCookie) return window.getCookie('csrftoken');
    const match = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
    if (match) return match[2];
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    return '';
  }

  // Визуальная подсветка поля ввода при успешном распознавании речи
  function highlightInput(el) {
    if (!el) return;
    el.classList.add('och-input-highlight');
    setTimeout(() => {
      el.classList.remove('och-input-highlight');
    }, 1800);
  }

  // Сброс кнопки озвучивания реплики
  function resetAudioButton(btn) {
    if (!btn) return;
    btn.classList.remove('playing');
    btn.innerHTML = `<i data-lucide="volume-2" style="width: 14px; height: 14px;"></i><span>Озвучить</span>`;
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  // Слушатели разблокировки звука
  ['pointerdown', 'keydown', 'touchstart'].forEach(evt => {
    document.addEventListener(evt, unlockAudio, { passive: true, once: true });
  });

  // 1. Коллекция маскотов комбината «Очаково» и их уникальных цитат
  const mascots = [
    {
      id: 'och-mascot-kombucha',
      name: 'Чайный гриб',
      phrases: [
        '«Чайный гриб в трехлитровой банке мне всё рассказал: охлаждай сусло до 25.5°C и не спорь со старшими!»',
        '«Я настаиваюсь с 1980 года, меня температурой брожения не испугаешь!»',
        '«Чайный гриб видит будущее: охладишь рубашку — смена будет в шоколаде (в смысле в квасе)!»',
        '«Моя марля дрожит от гордости: натуральное брожение идет по высшему разряду!»',
        '«Чайный гриб подмигивает: "Кто квас уважает, тот сессию без хвостов сдает!"»',
        '«Чайный гриб прошептал секрет: идеальная кислотность рождается в покое и прохладе.»'
      ],
      failPhrases: [
        '«Чайный гриб в осадке: перегрели сусло! Жми рестарт, спасем закваску!»',
        '«Моя марля поникла... Михалыч недоволен, давай переиграем смену по канону!»'
      ]
    },
    {
      id: 'och-mascot-sprat',
      name: 'Килька-напарник',
      phrases: [
        '«Килька в деле — квас в теле! Следим за балансом брожения!»',
        '«Килька советует не зевать: конвейер Очаково ждать не будет!»',
        '«Одобрено союзом балтийских и черноморских килек: вкус стабилен!»',
        '«Качественный квас — это вам не в масле плавать, тут наука двойного брожения!»',
        '«На таком квасе даже окрошка с килькой станет кулинарным шедевром!»',
        '«Килька виляет хвостом: на линии розлива чистота и порядок!»'
      ],
      failPhrases: [
        '«Авария на линии! Килька уплыла в шоке! Нужно срочно охладить контур!»',
        '«Сусло убежало! Килька требует немедленного рестарта смены!»'
      ]
    },
    {
      id: 'och-mascot-can',
      name: 'Банка Очаково',
      phrases: [
        '«Дрожжевой флекс на максимуме! Михалыч ставит высший балл!»',
        '«Квас льётся — сессия сдаётся! Держим производственный темп!»',
        '«Роботы Krones аплодируют захватами! Чистая победа цеха!»',
        '«Очаковский квас — натуральный вайб с 1978 года!»',
        '«Окрошка на очаковском квасе — абсолютная база всея Руси!»',
        '«300 тонн сусла спасены, брожение идёт по золотому стандарту!»'
      ],
      failPhrases: [
        '«Банка упала на ребро! Конвейер встал, перезапусти смену!»',
        '«Температура зашкалила! Спасай квас, открывай гликоль сразу!»'
      ]
    },
    {
      id: 'och-mascot-barrel',
      name: 'Жёлтая бочка',
      phrases: [
        '«Мой латунный кран помнит ещё Олимпиаду-80, лей увереннее!»',
        '«Кто на смене первый — тот всю Москву квасом поит!»',
        '«Главное в нашем деле — чтобы контур не закис, а квас искрился!»',
        '«Ретро-бочка одобряет: традиции живого брожения сохранены на 100%!»'
      ],
      failPhrases: [
        '«Кран перекрыт, сусло перегрето! Делай по регламенту 1978 года!»'
      ]
    },
    {
      id: 'och-mascot-robot',
      name: 'Роборука Krones',
      phrases: [
        '«Бип-буп! Оптический датчик зафиксировал 100% мастерство стажёра!»',
        '«01001011 ВАС! Я бы сам нажал на клапан, но у меня лапки-присоски.»',
        '«Скорость конвейера: 35 000 банок в час. Полет нормальный!»',
        '«Сбой устранён. Программа манипулятора выполнена без ошибок.»'
      ],
      failPhrases: [
        '«Отказ оптического датчика! Аварийный останов! Требуется сброс ошибки!»'
      ]
    }
  ];

  // 2. Инициализация и обработка голосовой связи как в симуляторе проводников (VSM_game)
  function initSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {
      try {
        recognition = new SpeechRec();
        recognition.lang = 'ru-RU';
        recognition.interimResults = true;
        recognition.continuous = true;

        recognition.onresult = function (event) {
          let interim = '';
          let final = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              final += event.results[i][0].transcript;
            } else {
              interim += event.results[i][0].transcript;
            }
          }
          const recognized = (final || interim).trim();
          if (recognized) {
            recognizedSpeechText = recognized;
            const textInput = document.getElementById('och-sim-text-input');
            if (textInput) {
              textInput.value = recognized;
            }
          }
        };

        recognition.onerror = function (e) {
          console.warn('[SpeechRec] Warning:', e.error);
        };
      } catch (err) {
        console.warn('[SpeechRec] Init error:', err);
      }
    }
  }

  function startMicVisualizer(stream) {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        audioContext = new AudioCtx();
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 64;
        source.connect(analyser);

        const waveBars = document.querySelectorAll('.och-mic-wave-bar');
        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        function updateWaves() {
          if (!isRecording) return;
          analyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
          const avg = sum / dataArray.length;
          waveBars.forEach((b, idx) => {
            const h = Math.max(4, Math.min(22, (avg / 7) * (idx + 1) * 0.65));
            b.style.height = `${h}px`;
          });
          animFrameId = requestAnimationFrame(updateWaves);
        }
        updateWaves();
      }
    } catch (audioErr) {
      console.warn('[AudioContext] Visualizer error:', audioErr);
    }
  }

  function stopMicVisualizer() {
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
    if (audioContext) {
      try { audioContext.close(); } catch (e) {}
      audioContext = null;
    }
  }

  // Редактирование распознанной речи перед отправкой (как в VSM_game)
  function showRecognizedSpeechForEditing(text) {
    const textInput = document.getElementById('och-sim-text-input');
    const banner = document.getElementById('och-mic-banner');
    const bannerText = document.getElementById('och-mic-banner-text');

    if (!text || !text.trim()) return;
    const cleanText = text.trim();
    recognizedSpeechText = cleanText;

    if (textInput) {
      textInput.value = cleanText;
      highlightInput(textInput);
      setTimeout(() => {
        textInput.focus();
        if (typeof textInput.setSelectionRange === 'function') {
          const len = textInput.value.length;
          textInput.setSelectionRange(len, len);
        }
      }, 50);
    }

    if (banner && bannerText) {
      banner.style.display = 'flex';
      bannerText.innerText = 'Речь распознана! Отредактируйте или нажмите «Сказать»';
      setTimeout(() => {
        if (!isRecording && banner) {
          banner.style.display = 'none';
        }
      }, 4000);
    }
  }

  async function startVoiceRecording() {
    unlockAudio();
    const banner = document.getElementById('och-mic-banner');
    const bannerText = document.getElementById('och-mic-banner-text');
    const micBtn = document.getElementById('och-mic-btn');

    recognizedSpeechText = '';

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Микрофон не поддерживается этим браузером или требуется защищенное соединение (localhost / HTTPS).');
      return;
    }

    try {
      // 1. Запрашиваем микрофон
      audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      isRecording = true;
      audioChunks = [];

      if (micBtn) {
        micBtn.classList.add('recording');
        micBtn.title = 'Идет запись... Нажмите для завершения';
      }
      if (banner) {
        banner.style.display = 'flex';
        if (bannerText) bannerText.innerText = 'Рация мастера активна... Говорите в микрофон';
      }

      // 2. Запуск визуализатора частот звука
      startMicVisualizer(audioStream);

      // 3. Запуск Web Speech API для мгновенного отображения текста
      if (recognition) {
        try {
          recognition.start();
        } catch (e) {
          console.warn('[SpeechRec] Already started or error:', e);
        }
      }

      // 4. Запуск MediaRecorder для аппаратно-ускоренного Whisper Vulkan GPU
      try {
        const mimeType = (window.MediaRecorder && MediaRecorder.isTypeSupported('audio/webm;codecs=opus'))
          ? 'audio/webm;codecs=opus'
          : ((window.MediaRecorder && MediaRecorder.isTypeSupported('audio/webm')) ? 'audio/webm' : '');
        mediaRecorder = mimeType ? new MediaRecorder(audioStream, { mimeType: mimeType }) : new MediaRecorder(audioStream);
        mediaRecorder.ondataavailable = function (e) {
          if (e.data && e.data.size > 0) {
            audioChunks.push(e.data);
          }
        };
        mediaRecorder.start();
      } catch (recErr) {
        console.warn('[MediaRecorder] Start error:', recErr);
      }

    } catch (err) {
      console.warn('[GetUserMedia] Microphone error:', err);
      isRecording = false;
      if (micBtn) micBtn.classList.remove('recording');
      if (banner && bannerText) {
        bannerText.innerText = 'Доступ к микрофону отклонен. Разрешите микрофон в браузере.';
      }
      alert('Пожалуйста, разрешите доступ к микрофону в браузере для работы голосовой связи.');
    }
  }

  async function stopVoiceRecording() {
    isRecording = false;
    const banner = document.getElementById('och-mic-banner');
    const bannerText = document.getElementById('och-mic-banner-text');
    const micBtn = document.getElementById('och-mic-btn');
    const textInput = document.getElementById('och-sim-text-input');

    if (micBtn) {
      micBtn.classList.remove('recording');
      micBtn.title = 'Нажмите для голосовой передачи (Push-to-Talk)';
    }

    stopMicVisualizer();

    if (banner && bannerText) {
      banner.style.display = 'flex';
      bannerText.innerText = 'Обработка радиосигнала речи...';
    }

    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }

    // Если MediaRecorder активен, останавливаем его и передаем аудио в Whisper Vulkan GPU
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.onstop = async function () {
        // Останавливаем дорожки микрофона ПОСЛЕ завершения рекордера
        if (audioStream) {
          audioStream.getTracks().forEach(track => track.stop());
          audioStream = null;
        }

        const mimeType = mediaRecorder.mimeType || 'audio/webm;codecs=opus';
        const audioBlob = new Blob(audioChunks, { type: mimeType });
        audioChunks = [];

        if (bannerText) bannerText.innerText = 'Распознавание речи через Whisper Vulkan GPU...';

        let finalSpeech = '';

        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');

          const resp = await fetch('/api/game/stt/', {
            method: 'POST',
            headers: {
              'X-CSRFToken': getCsrfToken()
            },
            body: formData
          });
          const data = await resp.json();
          if (data && data.ok && data.text && data.text.trim()) {
            finalSpeech = data.text.trim();
          }
        } catch (sttErr) {
          console.warn('[Whisper STT] Request error:', sttErr);
        }

        // Если локальный Whisper вернул текст, либо браузерный Web Speech API успел распознать речь
        if (!finalSpeech && (textInput?.value || recognizedSpeechText)) {
          finalSpeech = (textInput?.value || recognizedSpeechText).trim();
        }

        if (finalSpeech) {
          showRecognizedSpeechForEditing(finalSpeech);
        } else {
          if (bannerText) {
            bannerText.innerText = 'Речь не расслышана. Нажмите на микрофон еще раз или введите текст вручную.';
          }
          setTimeout(() => {
            if (!isRecording && banner) banner.style.display = 'none';
          }, 3500);
        }
      };

      try {
        mediaRecorder.stop();
      } catch (stopErr) {
        console.warn('[MediaRecorder] Stop error:', stopErr);
      }
    } else {
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
      }
      const finalSpeech = (textInput?.value || recognizedSpeechText || '').trim();
      if (finalSpeech) {
        showRecognizedSpeechForEditing(finalSpeech);
      } else {
        if (bannerText) {
          bannerText.innerText = 'Речь не услышана. Нажмите на микрофон и четко произнесите реплику.';
        }
        setTimeout(() => {
          if (!isRecording && banner) banner.style.display = 'none';
        }, 3000);
      }
    }
  }

  function toggleVoiceRecording() {
    if (isRecording) {
      stopVoiceRecording();
    } else {
      startVoiceRecording();
    }
  }

  // 3. Использование оборудования цеха
  function useEquipment(code, title) {
    unlockAudio();
    const drawer = document.getElementById('och-tool-drawer');
    if (drawer) drawer.classList.remove('open');

    submitTurn({
      equipment_code: code,
      user_text: `Применение в цеху: [${title || code}]`
    });
  }

  // 4. Переключение всплывающего ящика оборудования
  function toggleToolDrawer() {
    unlockAudio();
    const drawer = document.getElementById('och-tool-drawer');
    if (drawer) {
      drawer.classList.toggle('open');
    }
  }

  // Helper: Active mentor name from HUD
  function getActiveMentorName() {
    return document.getElementById('och-sim-hud')?.dataset?.mentorName || 'Михалыч';
  }

  // 5. Запрос тактической подсказки наставника (динамическое имя)
  function requestHint() {
    unlockAudio();
    const mentorName = getActiveMentorName();
    submitTurn({
      user_text: `${mentorName}, подскажи, пожалуйста: что сейчас делать по датчикам цеха?`
    });
  }

  // 6. Выбор кнопки быстрого действия (Action Chip)
  function chooseAction(choiceId, btn, text, equipmentCode) {
    unlockAudio();
    if (btn) {
      btn.style.opacity = '0.5';
      btn.disabled = true;
    }
    if (choiceId) {
      submitTurn({ choice_id: choiceId, user_text: text || '', is_recommended_choice: true });
    } else {
      submitTurn({ user_text: text || '', equipment_code: equipmentCode || '', is_recommended_choice: true });
    }
  }

  // 7. Отправка свободного текстового ввода
  function sendTextTurn(e) {
    if (e && e.preventDefault) e.preventDefault();
    unlockAudio();
    const textInput = document.getElementById('och-sim-text-input');
    if (!textInput) return;
    const text = textInput.value.trim();
    if (!text) return;

    textInput.value = '';
    submitTurn({ user_text: text });
  }

  // 8. Главный AJAX запрос хода к бэкенду
  async function submitTurn(params) {
    unlockAudio();
    const sessionUuid = document.getElementById('och-sim-hud')?.dataset?.sessionId;
    if (!sessionUuid) return;

    const payload = Object.assign({ session_id: sessionUuid }, params);

    // Добавляем реплику кандидата в ленту
    if (params.user_text) {
      appendChatTurn('candidate', 'Вы (Стажёр)', params.user_text);
      updateStudentSprite('talking');
    } else {
      updateStudentSprite('thinking');
    }

    try {
      const resp = await fetch('/api/game/action/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();

      if (data.ok) {
        // Обновляем датчики на динамическом HUD
        updateGauges(data);

        // Обновляем маскотов и цитаты
        updateMascots(data.verdict);

        // Добавляем ответ наставника в чат
        if (data.mentor_reply) {
          const mentorName = getActiveMentorName();
          appendChatTurn('mentor', mentorName, data.mentor_reply, data.feedback);
          const lastBtn = document.querySelector('#och-chat-feed .och-chat-row.mentor:last-child .och-bubble-audio-btn');
          playMentorVoice(data.mentor_reply, lastBtn);
        }

        // Обновляем всплывающие чипы действий
        updateChoices(data.choices);

        // Проверяем окончание смены (как в симуляторе проводников VSM_game)
        if (data.is_completed || data.status === 'completed') {
          updateStudentSprite('success');
          setTimeout(() => showSuccessModal(data), 600);
        } else if (data.is_failed || data.status === 'failed') {
          updateStudentSprite('thinking');
          setTimeout(() => showFailureModal(data), 600);
        } else {
          updateStudentSprite('neutral');
        }
      }
    } catch (err) {
      console.error('[Simulator] Action error:', err);
    }
  }

  // Текущее состояние телеметрии для плавной анимации
  let telemetryState = {
    temp: 25.0,
    brix: 8.4,
    speed: 28000,
    score: 50
  };

  // Плавная анимация изменения числовых значений (Counter Animation)
  function animateNumber(element, start, end, decimals = 0, suffix = '') {
    if (!element) return;
    if (isNaN(start)) start = 0;
    if (isNaN(end)) end = 0;
    if (Math.abs(start - end) < 0.001) {
      element.innerText = `${end.toFixed(decimals)}${suffix}`;
      return;
    }
    const duration = 500;
    const startTime = performance.now();
    function tick(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const val = start + (end - start) * ease;
      element.innerText = `${val.toFixed(decimals)}${suffix}`;
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        element.innerText = `${end.toFixed(decimals)}${suffix}`;
      }
    }
    requestAnimationFrame(tick);
  }

  // Проверка порогов датчиков с подсветкой статуса
  function evaluateGaugeThresholds(temp, brix, speed) {
    const hud = document.getElementById('och-sim-hud');
    if (!hud) return;

    const tempMin = parseFloat(hud.dataset.tempMin) || 24.0;
    const tempMax = parseFloat(hud.dataset.tempMax) || 26.5;
    const chipTemp = document.getElementById('chip-temp');
    const dotTemp = document.getElementById('dot-temp');
    const valTemp = document.getElementById('val-temp');

    if (chipTemp && valTemp) {
      chipTemp.classList.remove('gauge-opt', 'gauge-warn', 'gauge-danger');
      if (temp >= 28.5) {
        chipTemp.classList.add('gauge-danger');
        valTemp.style.color = '#D50032';
        if (dotTemp) dotTemp.className = 'och-gauge-status-dot dot-danger';
      } else if (temp > tempMax || temp < tempMin) {
        chipTemp.classList.add('gauge-warn');
        valTemp.style.color = '#D97706';
        if (dotTemp) dotTemp.className = 'och-gauge-status-dot dot-warn';
      } else {
        chipTemp.classList.add('gauge-opt');
        valTemp.style.color = '#059669';
        if (dotTemp) dotTemp.className = 'och-gauge-status-dot dot-opt';
      }
    }

    const brixMin = parseFloat(hud.dataset.brixMin) || 7.0;
    const brixMax = parseFloat(hud.dataset.brixMax) || 7.6;
    const chipBrix = document.getElementById('chip-brix');
    const dotBrix = document.getElementById('dot-brix');
    const valBrix = document.getElementById('val-brix');

    if (chipBrix && valBrix) {
      chipBrix.classList.remove('gauge-opt', 'gauge-warn');
      if (brix > brixMax || brix < brixMin) {
        chipBrix.classList.add('gauge-warn');
        if (dotBrix) dotBrix.className = 'och-gauge-status-dot dot-warn';
      } else {
        chipBrix.classList.add('gauge-opt');
        if (dotBrix) dotBrix.className = 'och-gauge-status-dot dot-opt';
      }
    }
  }

  // Всплывающий анимированный бейдж изменения очков (+15 XP / -10 XP)
  function showScoreDeltaFloater(diff) {
    const floater = document.getElementById('och-score-delta-floater');
    if (!floater) return;
    const sign = diff > 0 ? '+' : '';
    floater.innerText = `${sign}${diff} XP ${diff > 0 ? '🔥' : '⚠️'}`;
    floater.className = 'och-score-delta-floater ' + (diff > 0 ? 'fly-positive' : 'fly-negative');
    setTimeout(() => {
      floater.className = 'och-score-delta-floater';
    }, 1200);
  }

  // 9. Обновление датчиков на динамическом HUD
  function updateGauges(data) {
    if (data.temperature !== undefined) {
      const oldTemp = telemetryState.temp;
      telemetryState.temp = data.temperature;
      animateNumber(document.getElementById('val-temp'), oldTemp, data.temperature, 1, '°C');
    }
    if (data.brix !== undefined) {
      const oldBrix = telemetryState.brix;
      telemetryState.brix = data.brix;
      animateNumber(document.getElementById('val-brix'), oldBrix, data.brix, 1, '°Bx');
    }
    if (data.line_speed !== undefined) {
      const oldSpeed = telemetryState.speed;
      telemetryState.speed = data.line_speed;
      animateNumber(document.getElementById('val-speed'), oldSpeed, data.line_speed, 0, ' б/ч');
    }
    if (data.score !== undefined) {
      const oldScore = telemetryState.score;
      telemetryState.score = data.score;
      animateNumber(document.getElementById('val-score'), oldScore, data.score, 0, '');

      const diff = data.score - oldScore;
      if (diff !== 0) {
        showScoreDeltaFloater(diff);
      }
    }

    evaluateGaugeThresholds(telemetryState.temp, telemetryState.brix, telemetryState.speed);
  }

  // 9b. Менеджер серии успешных смен без брака (Win Streak & Overclocking)
  const STREAK_STORAGE_KEY = 'ochakovo_shift_streak_count';

  function getStreak() {
    return parseInt(localStorage.getItem(STREAK_STORAGE_KEY) || '0', 10);
  }

  function setStreak(count) {
    const val = Math.max(0, count);
    localStorage.setItem(STREAK_STORAGE_KEY, val.toString());
    renderStreakBadge();
  }

  function getMultiplier(streak) {
    if (streak >= 4) return 2.0;
    if (streak === 3) return 1.5;
    if (streak === 2) return 1.2;
    if (streak === 1) return 1.1;
    return 1.0;
  }

  function renderStreakBadge() {
    const streak = getStreak();
    const mult = getMultiplier(streak);
    const countEl = document.getElementById('val-streak-count');
    const multEl = document.getElementById('val-streak-mult');
    const badgeEl = document.getElementById('och-streak-container');

    if (countEl) countEl.innerText = streak;
    if (multEl) multEl.innerText = `x${mult.toFixed(1)}`;
    if (badgeEl) {
      badgeEl.classList.toggle('has-streak', streak > 0);
      badgeEl.classList.toggle('overclock-max', streak >= 3);
    }
  }

  // 10. Рандомизация маскотов и цитат (Чайный гриб, Килька, Банка, Бочка, Роборука)
  function updateMascots(verdict) {
    const commentEl = document.getElementById('och-mascot-comment');
    if (!commentEl) return;

    // Выбираем случайного маскота
    const chosenMascot = mascots[Math.floor(Math.random() * mascots.length)];

    // Скрываем всех маскотов, показываем выбранного
    mascots.forEach(m => {
      const el = document.getElementById(m.id);
      if (el) el.style.display = 'none';
    });

    const activeEl = document.getElementById(chosenMascot.id);
    if (activeEl) {
      activeEl.style.display = 'block';
    }

    // Подбираем реплику
    let pool = chosenMascot.phrases;
    if ((verdict === 'critical_fail' || verdict === 'danger') && chosenMascot.failPhrases) {
      pool = chosenMascot.failPhrases;
    }

    const randomQuote = pool[Math.floor(Math.random() * pool.length)];
    commentEl.innerText = randomQuote;
    commentEl.style.transform = 'scale(1.04)';
    setTimeout(() => {
      commentEl.style.transform = 'scale(1)';
    }, 220);
  }

  // 11. Добавление реплики в просторную ленту диалога
  function appendChatTurn(role, name, text, subtext) {
    const feed = document.getElementById('och-chat-feed');
    if (!feed) return;

    // Очистка реплики от случайного псевдокода вызова функций (resolve_production_incident и т.д.)
    if (text && typeof text === 'string') {
      text = text.replace(/\(?\b(?:resolve_production_incident|complete_shift|offer_hints)\s*\([\s\S]*?\)\)?/g, '').trim();
      text = text.replace(/^[\s:\-\)]+/, '').trim();
    }

    const row = document.createElement('div');
    row.className = `och-chat-row ${role}`;

    const avatarSrc = role === 'candidate' 
      ? '/static/img/ochakovo_emblem.svg'
      : (feed.dataset.mentorAvatar ? `/static/img/${feed.dataset.mentorAvatar}` : '/static/img/mentor_brewer.jpg');

    let subHtml = '';
    if (subtext) {
      subHtml = `<div class="och-bubble-sub"><i data-lucide="info" style="width: 14px; height: 14px; color: var(--och-red);"></i><span>${subtext}</span></div>`;
    }

    const cleanEscapedText = (text || '').replace(/'/g, "\\'");

    row.innerHTML = `
      <div class="och-speaker-col">
        <img src="${avatarSrc}" alt="${name}" class="och-speaker-avatar">
        <span class="och-speaker-role-pill">${role === 'candidate' ? 'Стажёр' : 'Наставник'}</span>
      </div>
      <div class="och-bubble">
        <div class="och-bubble-head">
          <span class="och-speaker-name">${name}</span>
          ${role === 'mentor' ? `<button type="button" class="och-bubble-audio-btn" onclick="simulator.playMentorVoice('${cleanEscapedText}', this)"><i data-lucide="volume-2" style="width: 14px; height: 14px;"></i><span>Озвучить</span></button>` : ''}
        </div>
        <div class="och-bubble-text">${text}</div>
        ${subHtml}
      </div>
    `;

    feed.appendChild(row);
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

    // Переключение хвостика комиксного облачка и активного говорящего
    const vnConsoleEl = document.querySelector('.och-vn-console');
    const studentActorEl = document.getElementById('vn-actor-student');
    const mentorActorEl = document.getElementById('vn-actor-mentor');
    if (vnConsoleEl) {
      if (role === 'candidate') {
        vnConsoleEl.classList.remove('speaker-mentor');
        vnConsoleEl.classList.add('speaker-intern');
        if (studentActorEl) studentActorEl.classList.add('active-speaker');
        if (mentorActorEl) mentorActorEl.classList.remove('active-speaker');
      } else {
        vnConsoleEl.classList.remove('speaker-intern');
        vnConsoleEl.classList.add('speaker-mentor');
        if (mentorActorEl) mentorActorEl.classList.add('active-speaker');
        if (studentActorEl) studentActorEl.classList.remove('active-speaker');
      }
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

    // Добавляем реплику в выдвижной комиксный журнал переговоров смены
    const histList = document.getElementById('och-history-drawer-list');
    if (histList) {
      const isMentor = (role === 'mentor');
      const isEquip = (text && (text.includes('Разыграна карта') || text.includes('карта:'))) || (subtext && subtext.includes('карта'));
      const roleClass = isEquip ? 'equipment' : (isMentor ? 'mentor' : 'intern');
      const badgeText = isEquip ? '🃏 ОБОРУДОВАНИЕ ЦЕХА' : (isMentor ? `${(name || 'Наставник').toUpperCase()} (НАСТАВНИК)` : 'ВЫ (СТАЖЁР)');
      const avatarSrcVal = isMentor 
        ? (feed.dataset.mentorAvatar ? `/static/img/${feed.dataset.mentorAvatar}` : '/static/img/mentor_brewer.jpg')
        : (isEquip ? '/static/img/equipment/pressure_gauge.svg' : '/static/img/avatar_student_boy.jpg');

      const entry = document.createElement('div');
      entry.className = `och-comic-history-entry ${roleClass}`;
      entry.innerHTML = `
        <div class="och-comic-history-header">
          <div class="och-comic-history-author">
            <img src="${avatarSrcVal}" alt="${name}" class="och-comic-history-avatar">
            <span class="och-comic-history-badge ${roleClass}">${badgeText}</span>
          </div>
          ${isMentor ? `
            <button type="button" class="och-comic-history-audio-btn" onclick="simulator.playMentorVoice('${cleanEscapedText}', this)">
              <i data-lucide="volume-2" style="width: 12px; height: 12px;"></i>
              <span>Озвучить</span>
            </button>
          ` : ''}
        </div>
        <div class="och-comic-history-bubble">
          <div class="och-comic-history-text">${text}</div>
          ${subtext ? `
            <div class="och-comic-history-note">
              <i data-lucide="wrench" style="width: 13px; height: 13px; flex-shrink: 0; color: #D97706;"></i>
              <span>${subtext}</span>
            </div>
          ` : ''}
        </div>
      `;
      histList.appendChild(entry);
      histList.scrollTop = histList.scrollHeight;

      const counterEl = document.getElementById('och-history-counter');
      if (counterEl) {
        const count = histList.querySelectorAll('.och-comic-history-entry').length;
        const lastDigit = count % 10;
        const lastTwo = count % 100;
        let word = 'реплик';
        if (lastTwo < 11 || lastTwo > 19) {
          if (lastDigit === 1) word = 'реплика';
          else if (lastDigit >= 2 && lastDigit <= 4) word = 'реплики';
        }
        counterEl.innerText = `${count} ${word}`;
      }
    }

    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  // 12. Обновление всплывающих кнопок действий (Action Chips) без эмодзи
  function updateChoices(choices) {
    const container = document.getElementById('och-choices-container');
    if (!container) return;

    const mentorName = getActiveMentorName();

    if (!choices || choices.length === 0) {
      container.innerHTML = `
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
          <span>Спросить совет ${mentorName}</span>
        </button>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    let html = '';
    choices.forEach((ch) => {
      // Очищаем от возможных остаточных эмодзи
      const cleanText = (ch.choice_text || '').replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '').trim();
      const cleanHint = (ch.tactical_hint || '').replace(/'/g, "\\'");
      const cleanTextEsc = cleanText.replace(/'/g, "\\'");
      const eq = ch.equipment_code || '';
      const idVal = ch.id ? ch.id : 'null';

      html += `
        <button type="button" class="och-action-chip" onclick="simulator.chooseAction(${idVal}, this, '${cleanTextEsc}', '${eq}')" title="${cleanHint}">
          <i data-lucide="zap" style="width: 15px; height: 15px; color: var(--och-red);"></i>
          <span>${cleanText}</span>
        </button>
      `;
    });

    container.innerHTML = html;

    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  // 13. Озвучивание реплики наставника (Edge-TTS нейроголос + Web Speech API fallback)
  async function playMentorVoice(text, btnEl) {
    if (!text) return;
    unlockAudio();

    // Если кликнули на кнопку реплики, которая уже играет (HTML5 Audio или SpeechSynthesis) — останавливаем её
    if (window.speechSynthesis && window.speechSynthesis.speaking && btnEl && btnEl.classList.contains('playing')) {
      window.speechSynthesis.cancel();
      resetAudioButton(btnEl);
      return;
    }

    if (currentAudio && !currentAudio.paused && btnEl && btnEl.classList.contains('playing')) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      resetAudioButton(btnEl);
      return;
    }

    if (window.speechSynthesis && window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }

    if (currentAudio) {
      try {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      } catch (e) {}
      currentAudio = null;
    }

    // Сбрасываем другие активные кнопки озвучки
    document.querySelectorAll('.och-bubble-audio-btn.playing').forEach(b => resetAudioButton(b));

    const voiceType = getMentorVoiceType();
    const ttsUrl = `/api/game/tts/?text=${encodeURIComponent(text)}&voice=${voiceType}`;

    if (btnEl) {
      btnEl.classList.add('playing');
      btnEl.innerHTML = `<i data-lucide="square" style="width: 13px; height: 13px; fill: currentColor;"></i><span>Стоп</span>`;
      if (window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
      }
    }

    // Попытка 1: Загрузка нейроаудио (Edge-TTS / дисковый кэш) с бэкенда
    let serverAudioSuccess = false;
    try {
      const resp = await fetch(ttsUrl);
      if (resp.ok && resp.status === 200) {
        const blob = await resp.blob();
        if (blob && blob.size > 200) {
          if (!persistentAudio) {
            persistentAudio = new Audio();
          }
          currentAudio = persistentAudio;
          const blobUrl = URL.createObjectURL(blob);
          persistentAudio.src = blobUrl;

          persistentAudio.onended = function () {
            URL.revokeObjectURL(blobUrl);
            if (btnEl) resetAudioButton(btnEl);
          };

          persistentAudio.onerror = function (e) {
            URL.revokeObjectURL(blobUrl);
            console.warn('[TTS] Audio playback error from blob, falling back to browser speech:', e);
            fallbackToBrowserSpeech(text, voiceType, btnEl);
          };

          await persistentAudio.play();
          serverAudioSuccess = true;
          return;
        }
      }
    } catch (netErr) {
      console.warn('[TTS] Server TTS fetch failed (container offline/DNS issue):', netErr);
    }

    // Попытка 2: Если бэкенд в Docker оффлайн или Edge-TTS недоступен — мгновенный голосовой синтез в браузере
    if (!serverAudioSuccess) {
      fallbackToBrowserSpeech(text, voiceType, btnEl);
    }
  }

  // Резервный синтез речи через Web Speech API (гарантирует озвучку Елены и всех наставников даже при полном отсутствии интернета в Docker)
  function fallbackToBrowserSpeech(text, voiceType, btnEl) {
    if (!('speechSynthesis' in window)) {
      if (btnEl) resetAudioButton(btnEl);
      return;
    }

    try {
      window.speechSynthesis.cancel();

      // Очистка текста от технических скобок и кавычек для идеальной дикции
      const clean = (text || '')
        .replace(/\(.*?\)|\[.*?\]/g, '')
        .replace(/[«»"]/g, '')
        .trim();

      if (!clean) {
        if (btnEl) resetAudioButton(btnEl);
        return;
      }

      const utter = new SpeechSynthesisUtterance(clean);
      utter.lang = 'ru-RU';

      // Подбор наиболее естественного голоса из установленных в системе браузера
      const voices = window.speechSynthesis.getVoices() || [];
      const ruVoices = voices.filter(v => v.lang && v.lang.toLowerCase().replace('_', '-').startsWith('ru'));

      if (voiceType === 'female') {
        const femaleVoice = ruVoices.find(v => {
          const n = (v.name || '').toLowerCase();
          return n.includes('female') || n.includes('svetlana') || n.includes('irina') ||
                 n.includes('daria') || n.includes('milena') || n.includes('tatyana') ||
                 n.includes('elena') || n.includes('anna');
        }) || ruVoices[0];
        if (femaleVoice) utter.voice = femaleVoice;
        utter.pitch = 1.15; // Мягкий приятный женский тембр для Елены и Анны
        utter.rate = 1.0;
      } else {
        const maleVoice = ruVoices.find(v => {
          const n = (v.name || '').toLowerCase();
          return n.includes('male') || n.includes('dmitry') || n.includes('pavel') ||
                 n.includes('aleksandr') || n.includes('yuri');
        }) || ruVoices[0];
        if (maleVoice) utter.voice = maleVoice;
        utter.pitch = 0.92; // Уверенный мужской тон для Михалыча и Романа
        utter.rate = 0.95;
      }

      if (btnEl) {
        btnEl.classList.add('playing');
        btnEl.innerHTML = `<i data-lucide="square" style="width: 13px; height: 13px; fill: currentColor;"></i><span>Стоп</span>`;
        if (window.lucide && typeof window.lucide.createIcons === 'function') {
          window.lucide.createIcons();
        }
      }

      utter.onend = function () {
        if (btnEl) resetAudioButton(btnEl);
      };

      utter.onerror = function (e) {
        console.warn('[BrowserSpeech] Utterance error:', e);
        if (btnEl) resetAudioButton(btnEl);
      };

      window.speechSynthesis.speak(utter);
    } catch (e) {
      console.warn('[BrowserSpeech] Synthesis exception:', e);
      if (btnEl) resetAudioButton(btnEl);
    }
  }

  // 14. Закрытие модальных окон
  function closeModals() {
    const successModal = document.getElementById('och-success-modal');
    if (successModal) successModal.style.display = 'none';

    const failModal = document.getElementById('och-failure-modal');
    if (failModal) failModal.style.display = 'none';

    const briefingModal = document.getElementById('och-briefing-modal');
    if (briefingModal) briefingModal.style.display = 'none';

    closeVideoBriefingModal();
  }

  // Управление видео-инструктажем мастера цеха (с поддержкой звука и Range 206)
  let currentActiveSpeech = '';

  
  // 18. Профессиональные производственные факты цеха (После смены)
  function openProFactsModal() {
    const modal = document.getElementById('och-pro-facts-modal');
    if (modal) {
      modal.style.display = 'flex';
      if (window.lucide) window.lucide.createIcons();
    }
  }

  function closeProFactsModal() {
    const modal = document.getElementById('och-pro-facts-modal');
    if (modal) modal.style.display = 'none';
  }

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
    const backdrop = document.getElementById('och-history-drawer-backdrop');
    if (!drawer) return;
    const isOpen = drawer.classList.toggle('open');
    if (backdrop) {
      backdrop.style.display = isOpen ? 'block' : 'none';
    }
    if (isOpen) {
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
  }

  // Обновление эмоции студента в визуальной новелле
  function updateStudentSprite(mood) {
    const sprite = document.getElementById('vn-sprite-student');
    if (!sprite) return;
    const moodMap = {
      'neutral': '/static/img/avatar_student_boy.jpg',
      'talking': '/static/img/avatar_student_boy.jpg',
      'thinking': '/static/img/avatar_student_boy.jpg',
      'success': '/static/img/avatar_student_girl.jpg'
    };
    if (moodMap[mood]) {
      sprite.src = moodMap[mood];
    }
  }

  // Сохранение завершенного кейса в карьерный прогресс стажёра
  function saveCompletedCaseToProgress(finalScore) {
    const hud = document.getElementById('och-sim-hud');
    if (!hud) return;
    const slug = hud.dataset.scenarioSlug || '';
    const title = hud.dataset.scenarioTitle || 'Смена на комбинате «Очаково»';
    const workshop = hud.dataset.workshopName || '';
    const mentor = hud.dataset.mentorName || getActiveMentorName();

    try {
      const prog = JSON.parse(localStorage.getItem('ochakovo_career_progress') || '{}');
      const cases = prog.completedCases || [];

      const existingIdx = cases.findIndex(c => c.slug === slug);
      const entry = {
        slug: slug,
        title: title,
        workshop: workshop,
        mentor: mentor,
        score: Math.max(finalScore, existingIdx >= 0 ? (cases[existingIdx].score || 0) : 0),
        date: new Date().toLocaleDateString('ru-RU')
      };

      if (existingIdx >= 0) {
        cases[existingIdx] = entry;
      } else {
        cases.push(entry);
      }

      prog.completedCases = cases;
      let total = 0;
      cases.forEach(c => { total += (c.score || 0); });
      prog.totalScore = total;
      localStorage.setItem('ochakovo_career_progress', JSON.stringify(prog));

      // Обновляем бейдж в навигации
      const navBadge = document.getElementById('nav-user-score-badge');
      if (navBadge) navBadge.innerText = `${total} XP`;

      // Фоновая синхронизация с сервером
      fetch('/api/candidate/progress/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ total_score: total, completed_cases: cases })
      }).catch(() => {});
    } catch (e) {
      console.warn('[Progress] Save error:', e);
    }
  }

  // 15. Модальное окно победы (с учетом серии смен и множителя)
  function showSuccessModal(data) {
    const modal = document.getElementById('och-success-modal');
    if (!modal) return;

    // Накопление победной серии смен (Win Streak Combo)
    const currentStreak = getStreak();
    const newStreak = currentStreak + 1;
    setStreak(newStreak);
    const mult = getMultiplier(newStreak);

    // Расчет бонусных баллов с множителем
    const rawScore = data.score || 95;
    const finalScore = Math.min(100, Math.round(rawScore * mult));

    // Фиксация в карьерном прогрессе стажёра для сертификата и отклика на hh.ru
    saveCompletedCaseToProgress(finalScore);

    const streakVal = document.getElementById('och-modal-streak-val');
    if (streakVal) streakVal.innerText = newStreak;

    const multVal = document.getElementById('och-modal-mult-val');
    if (multVal) multVal.innerText = `x${mult.toFixed(1)}`;

    const scoreElem = document.getElementById('och-modal-score');
    if (scoreElem) scoreElem.innerText = finalScore;

    const feedbackElem = document.getElementById('och-modal-feedback');
    if (feedbackElem) feedbackElem.innerText = data.feedback || 'Смена успешно завершена! Технологические параметры соответствуют золотому стандарту Очаково.';

    const vacElem = document.getElementById('och-modal-vac-title');
    if (vacElem && data.target_vacancy) {
      vacElem.innerText = `${data.target_vacancy.title} (${data.target_vacancy.salary})`;
    }

    modal.style.display = 'flex';
    if (window.lucide) window.lucide.createIcons();
  }

  // 16. Модальное окно сбоя (обнуление серии смен)
  function showFailureModal(data) {
    // При аварии/срыве смены стрик обнуляется
    setStreak(0);

    const modal = document.getElementById('och-failure-modal');
    if (!modal) return;

    const feedbackElem = document.getElementById('och-fail-feedback');
    if (feedbackElem) feedbackElem.innerText = data.feedback || 'Допущено нарушение технологического регламента производства.';

    modal.style.display = 'flex';
    if (window.lucide) window.lucide.createIcons();
  }

  // 17. Управление предсменным инструктажем и настройкой ИИ
  function openBriefingModal() {
    // Окно ввода ключа отключено: единый ключ задается владельцем сайта в .env или админке
    return;
  }

  function closeBriefingModal() {
    closeModals();
  }

  function switchBriefingTab(tabName) {
    const btnGiga = document.getElementById('tab-btn-gigachat');
    const btnOff = document.getElementById('tab-btn-offline');
    const contentGiga = document.getElementById('tab-content-gigachat');
    const contentOff = document.getElementById('tab-content-offline');

    if (tabName === 'gigachat') {
      if (btnGiga) btnGiga.classList.add('active');
      if (btnOff) btnOff.classList.remove('active');
      if (contentGiga) contentGiga.style.display = 'block';
      if (contentOff) contentOff.style.display = 'none';
    } else {
      if (btnOff) btnOff.classList.add('active');
      if (btnGiga) btnGiga.classList.remove('active');
      if (contentOff) contentOff.style.display = 'block';
      if (contentGiga) contentGiga.style.display = 'none';
    }

    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  function updateAiHudBadge(mode) {
    const dot = document.getElementById('och-hud-ai-dot');
    const label = document.getElementById('och-hud-ai-label');
    const hud = document.getElementById('och-sim-hud');

    if (dot) {
      dot.className = `och-ai-mode-dot ${mode === 'gigachat' ? 'dot-gigachat' : 'dot-offline'}`;
    }
    if (label) {
      label.innerText = mode === 'gigachat' ? 'GigaChat AI' : 'Офлайн AI';
    }
    if (hud) {
      hud.dataset.aiMode = mode;
      if (mode === 'gigachat') hud.dataset.hasCredentials = 'true';
    }
  }

  async function submitGigaChatCredentials() {
    const clientIdInput = document.getElementById('och-input-client-id');
    const clientSecretInput = document.getElementById('och-input-client-secret');
    const authKeyInput = document.getElementById('och-input-auth-key');
    const statusEl = document.getElementById('och-briefing-status');
    const submitBtn = document.getElementById('och-btn-connect-gigachat');
    const submitText = document.getElementById('och-btn-connect-text');

    const clientId = (clientIdInput?.value || '').trim();
    const clientSecret = (clientSecretInput?.value || '').trim();
    const authKey = (authKeyInput?.value || '').trim();

    if (!authKey && (!clientId || !clientSecret)) {
      if (statusEl) {
        statusEl.className = 'och-briefing-status status-error';
        statusEl.innerHTML = 'Пожалуйста, укажите Client ID и Client Secret (или введите Base64 Auth Key).';
        statusEl.style.display = 'block';
      }
      return;
    }

    if (statusEl) {
      statusEl.className = 'och-briefing-status status-loading';
      statusEl.innerHTML = 'Проверка подключения к GigaChat API...';
      statusEl.style.display = 'block';
    }

    if (submitBtn) submitBtn.disabled = true;
    if (submitText) submitText.innerText = 'Проверка ключей...';

    try {
      const resp = await fetch('/api/game/credentials/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
          action: 'set_gigachat',
          client_id: clientId,
          client_secret: clientSecret,
          auth_key: authKey
        })
      });

      const data = await resp.json();

      if (resp.ok && data.status === 'ok') {
        if (statusEl) {
          statusEl.className = 'och-briefing-status status-success';
          statusEl.innerHTML = 'Авторизация в GigaChat подтверждена! Заступаем на смену...';
        }
        updateAiHudBadge('gigachat');
        sessionStorage.setItem('och_briefing_completed', 'true');
        setTimeout(() => {
          closeModals();
        }, 800);
      } else {
        if (statusEl) {
          statusEl.className = 'och-briefing-status status-error';
          statusEl.innerHTML = (data && data.message) ? data.message : 'Не удалось авторизоваться в GigaChat API. Проверьте правильность введенных ключей.';
        }
      }
    } catch (err) {
      if (statusEl) {
        statusEl.className = 'och-briefing-status status-error';
        statusEl.innerHTML = 'Сетевая ошибка при проверке ключей GigaChat. Проверьте подключение к сети.';
      }
    } finally {
      if (submitBtn) submitBtn.disabled = false;
      if (submitText) submitText.innerText = 'Проверить и заступить на смену';
    }
  }

  async function useSmartOfflineMode() {
    try {
      await fetch('/api/game/credentials/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ action: 'set_offline' })
      });
    } catch (e) {
      // Игнорируем сетевые сбои в автономном режиме
    }

    updateAiHudBadge('offline');
    sessionStorage.setItem('och_briefing_completed', 'true');
    closeModals();
  }

  document.addEventListener('DOMContentLoaded', () => {
    // Инициализируем голосовое распознавание речи
    initSpeechRecognition();

    // Инициализируем случайного маскота при старте игры
    updateMascots('normal');
    initCardTouchDrag();

    // Инициализируем стрик и начальные значения датчиков
    renderStreakBadge();

    // Автоматически предлагаем обучающий видео-инструктаж перед началом смены
    const pathSlug = window.location.pathname.split('/').filter(Boolean).pop() || 'shift';
    const videoStorageKey = 'och_video_offered_' + pathSlug;
    // Авто-показ видео убран по ТЗ: видео доступно по кнопке в HUD, а факты цеха открываются после смены
    sessionStorage.setItem(videoStorageKey, 'true');
    const tempEl = document.getElementById('val-temp');
    if (tempEl) {
      const parsedTemp = parseFloat(tempEl.innerText);
      if (!isNaN(parsedTemp)) telemetryState.temp = parsedTemp;
    }
    const brixEl = document.getElementById('val-brix');
    if (brixEl) {
      const parsedBrix = parseFloat(brixEl.innerText);
      if (!isNaN(parsedBrix)) telemetryState.brix = parsedBrix;
    }
    const speedEl = document.getElementById('val-speed');
    if (speedEl) {
      const parsedSpeed = parseInt(speedEl.innerText.replace(/\D/g, ''), 10);
      if (!isNaN(parsedSpeed)) telemetryState.speed = parsedSpeed;
    }
    const scoreEl = document.getElementById('val-score');
    if (scoreEl) {
      const parsedScore = parseInt(scoreEl.innerText, 10);
      if (!isNaN(parsedScore)) telemetryState.score = parsedScore;
    }
    evaluateGaugeThresholds(telemetryState.temp, telemetryState.brix, telemetryState.speed);

    // Живой фоновый пульс датчиков завода (Live Sensor Micro-pulse)
    setInterval(() => {
      const tempVal = document.getElementById('val-temp');
      if (tempVal && !document.hidden) {
        const jitter = (Math.random() - 0.5) * 0.08;
        const disp = (telemetryState.temp + jitter).toFixed(1);
        tempVal.innerText = `${disp}°C`;
      }
    }, 2400);

    // Закрытие модалок по клавише Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModals();
    });

    // Проверка необходимости предсменного инструктажа перед заступлением на смену
    const hudEl = document.getElementById('och-sim-hud');
    const hasCreds = hudEl && hudEl.dataset.hasCredentials === 'true';
    const briefingDone = sessionStorage.getItem('och_briefing_completed') === 'true';

    // Окно ввода ключа отключено: единый ключ задается владельцем сайта в .env или админке
  });


  // ==========================================
  // DRAG & DROP ПАНЕЛИ КАРТ ОБОРУДОВАНИЯ ЦЕХА (HTML5 + TOUCH/POINTER)
  // ==========================================
  let draggedEquipment = null;
  window._draggedEquipment = null;

  function onEquipmentDragStart(e, code, title) {
    draggedEquipment = { code, title };
    window._draggedEquipment = { code, title };
    if (e && e.dataTransfer) {
      try {
        e.dataTransfer.setData('text/plain', code);
        e.dataTransfer.effectAllowed = 'copyMove';
      } catch (err) {
        console.warn('[Drag] dataTransfer error', err);
      }
    }
    const cardEl = e ? e.currentTarget : null;
    if (cardEl) {
      cardEl.classList.add('och-card-dragging');
    }
    const dropZones = document.querySelectorAll('.och-comic-drop-target, #och-comic-stage, .och-vn-stage');
    dropZones.forEach(dz => dz.classList.add('och-dropzone-active'));
  }

  function onEquipmentDragEnd(e) {
    const cardEl = e ? e.currentTarget : null;
    if (cardEl) {
      cardEl.classList.remove('och-card-dragging');
    }
    const dropZones = document.querySelectorAll('.och-comic-drop-target, #och-comic-stage, .och-vn-stage');
    dropZones.forEach(dz => dz.classList.remove('och-dropzone-active', 'och-dropzone-hover'));
  }

  function onDropZoneDragEnter(e) {
    if (e) {
      e.preventDefault();
      if (e.dataTransfer) {
        try { e.dataTransfer.dropEffect = 'copy'; } catch (_) {}
      }
      const dz = e.currentTarget;
      if (dz) dz.classList.add('och-dropzone-hover');
    }
  }

  function onDropZoneDragOver(e) {
    if (e) {
      e.preventDefault();
      if (e.dataTransfer) {
        try { e.dataTransfer.dropEffect = 'copy'; } catch (_) {}
      }
      const dz = e.currentTarget;
      if (dz && !dz.classList.contains('och-dropzone-hover')) {
        dz.classList.add('och-dropzone-hover');
      }
    }
  }

  function onDropZoneDragLeave(e) {
    if (e && e.currentTarget) {
      if (e.relatedTarget && e.currentTarget.contains(e.relatedTarget)) {
        return; // курсор перешёл во внутренний элемент, игнорируем
      }
      e.currentTarget.classList.remove('och-dropzone-hover');
    }
  }

  function onEquipmentDrop(e) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    const dropZones = document.querySelectorAll('.och-comic-drop-target, #och-comic-stage, .och-vn-stage');
    dropZones.forEach(dz => dz.classList.remove('och-dropzone-active', 'och-dropzone-hover'));

    let code = null;
    if (e && e.dataTransfer) {
      try {
        code = e.dataTransfer.getData('text/plain');
      } catch (err) {
        console.warn('[Drop] getData error', err);
      }
    }
    let title = '';
    if (!code && window._draggedEquipment) {
      code = window._draggedEquipment.code;
      title = window._draggedEquipment.title;
    } else if (draggedEquipment) {
      code = code || draggedEquipment.code;
      title = draggedEquipment.title;
    }

    if (code) {
      useEquipment(code, title || code);
      showActionToast(`🎯 Разыграна карта: ${title || code}`);
    }
    draggedEquipment = null;
    window._draggedEquipment = null;
  }

  function isPointInside(element, x, y) {
    if (!element) return false;
    const rect = element.getBoundingClientRect();
    return x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom;
  }

  function initCardTouchDrag() {
    const cards = document.querySelectorAll('.och-comic-card');
    cards.forEach(card => {
      let touchStartX = 0;
      let touchStartY = 0;
      let isDragging = false;
      let ghost = null;
      const code = card.dataset.code || card.getAttribute('onclick')?.match(/useEquipment\('([^']+)'/)?.[1];
      const title = card.dataset.title || card.querySelector('.och-comic-card-name')?.innerText || code;

      card.addEventListener('touchstart', (e) => {
        if (e.touches.length !== 1) return;
        const touch = e.touches[0];
        touchStartX = touch.clientX;
        touchStartY = touch.clientY;
        isDragging = false;
      }, { passive: true });

      card.addEventListener('touchmove', (e) => {
        if (e.touches.length !== 1) return;
        const touch = e.touches[0];
        const dy = touch.clientY - touchStartY;

        // Если сдвинули вверх больше чем на 25px — активируем перетаскивание
        if (dy < -25 && !isDragging) {
          isDragging = true;
          window._draggedEquipment = { code, title };
          onEquipmentDragStart(null, code, title);

          ghost = card.cloneNode(true);
          ghost.classList.add('och-touch-ghost');
          ghost.style.position = 'fixed';
          ghost.style.pointerEvents = 'none';
          ghost.style.zIndex = '99999';
          ghost.style.width = card.offsetWidth + 'px';
          ghost.style.opacity = '0.92';
          ghost.style.transform = 'translate(-50%, -50%) scale(1.08) rotate(3deg)';
          document.body.appendChild(ghost);
        }

        if (isDragging && ghost) {
          ghost.style.left = touch.clientX + 'px';
          ghost.style.top = touch.clientY + 'px';

          const dropTarget = document.getElementById('och-comic-drop-target');
          const stage = document.getElementById('och-comic-stage');
          const isOverDrop = isPointInside(dropTarget, touch.clientX, touch.clientY) ||
                             isPointInside(stage, touch.clientX, touch.clientY);

          if (isOverDrop) {
            dropTarget?.classList.add('och-dropzone-hover');
            stage?.classList.add('och-dropzone-hover');
          } else {
            dropTarget?.classList.remove('och-dropzone-hover');
            stage?.classList.remove('och-dropzone-hover');
          }
        }
      }, { passive: true });

      card.addEventListener('touchend', (e) => {
        if (isDragging) {
          if (ghost && ghost.parentNode) ghost.parentNode.removeChild(ghost);
          const changedTouch = e.changedTouches[0];
          const dropTarget = document.getElementById('och-comic-drop-target');
          const stage = document.getElementById('och-comic-stage');
          const isOverDrop = isPointInside(dropTarget, changedTouch.clientX, changedTouch.clientY) ||
                             isPointInside(stage, changedTouch.clientX, changedTouch.clientY) ||
                             (changedTouch.clientY < touchStartY - 60);

          if (isOverDrop && code) {
            useEquipment(code, title);
            showActionToast(`🎯 Разыграна карта: ${title}`);
          }
          onEquipmentDragEnd(null);
          isDragging = false;
        }
      });
    });
  }

  function showActionToast(msg) {
    let toast = document.getElementById('och-sim-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'och-sim-toast';
      toast.className = 'och-sim-comic-toast';
      document.body.appendChild(toast);
    }
    toast.innerText = msg;
    toast.classList.add('visible');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
      toast.classList.remove('visible');
    }, 2400);
  }

  return {
    toggleVoiceRecording,
    stopVoiceRecording,
    useEquipment,
    onEquipmentDragStart,
    onEquipmentDragEnd,
    onDropZoneDragEnter,
    onDropZoneDragOver,
    onDropZoneDragLeave,
    onEquipmentDrop,
    showActionToast,
    toggleToolDrawer,
    requestHint,
    chooseAction,
    sendTextTurn,
    playMentorVoice,
    closeModals,
    openBriefingModal,
    closeBriefingModal,
    switchBriefingTab,
    submitGigaChatCredentials,
    useSmartOfflineMode,
    openProFactsModal,
    closeProFactsModal,
    openVideoBriefingModal,
    closeVideoBriefingModal,
    toggleHistoryDrawer,
    replayCurrentSpeech,
    updateStudentSprite
  };
})();
