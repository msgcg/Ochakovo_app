/**
 * ОЧАКОВО: PWA И КЛИЕНТСКИЙ СКРИПТ ПРИЛОЖЕНИЯ
 * Регистрация Service Worker, управление установкой PWA, оффлайн-статус и Lucide иконки
 */

(function () {
  'use strict';

  // 1. Инициализация иконок Lucide
  function initIcons() {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  // 2. Регистрация Service Worker
  let deferredPrompt = null;

  function registerPWA() {
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
          .then((reg) => {
            console.log('[Ochakovo PWA] Service Worker успешно зарегистрирован:', reg.scope);
          })
          .catch((err) => {
            console.warn('[Ochakovo PWA] Ошибка регистрации Service Worker:', err);
          });
      });
    }

    // Перехват события установки PWA на главный экран
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      const installBtn = document.getElementById('och-pwa-install-btn');
      if (installBtn) {
        installBtn.style.display = 'inline-flex';
      }
    });

    window.addEventListener('appinstalled', () => {
      console.log('[Ochakovo PWA] Приложение успешно установлено на устройство');
      const installBtn = document.getElementById('och-pwa-install-btn');
      if (installBtn) {
        installBtn.style.display = 'none';
      }
      deferredPrompt = null;
    });
  }

  window.installPWA = function () {
    if (!deferredPrompt) {
      alert('Приложение уже установлено или ваш браузер поддерживает установку через меню «Добавить на главный экран».');
      return;
    }
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('[Ochakovo PWA] Пользователь принял установку');
      }
      deferredPrompt = null;
    });
  };

  // 3. Отслеживание подключения сети
  function initNetworkMonitor() {
    const banner = document.getElementById('och-offline-indicator');
    function updateOnlineStatus() {
      if (banner) {
        banner.style.display = navigator.onLine ? 'none' : 'flex';
      }
    }
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();
  }

  // 4. Мобильное меню
  function initMobileMenu() {
    const burgerBtn = document.getElementById('och-burger-btn');
    const navList = document.getElementById('och-nav-list');
    if (burgerBtn && navList) {
      burgerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = navList.classList.toggle('mobile-open');
        navList.style.display = isOpen ? 'flex' : '';
      });

      document.addEventListener('click', (e) => {
        if (!burgerBtn.contains(e.target) && !navList.contains(e.target)) {
          navList.classList.remove('mobile-open');
          navList.style.display = '';
        }
      });
    }
  }

  // 5. Быстрая подача заявки (модальное окно отклика с реальным переходом на hh.ru)
  window.submitFastApplication = async function (e, formId) {
    if (e && e.preventDefault) e.preventDefault();
    const form = document.getElementById(formId);
    if (!form) return;

    // Подтягиваем сохраненный карьерный прогресс из localStorage
    const savedProgress = JSON.parse(localStorage.getItem('ochakovo_career_progress') || '{}');
    const cases = savedProgress.completedCases || [];

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    payload.completed_cases = JSON.stringify(cases);

    const submitBtn = form.querySelector('button[type="submit"]');
    const origHtml = submitBtn ? submitBtn.innerHTML : '';

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span style="display: inline-block; animation: spin 0.8s linear infinite;">⏳</span> Регистрируем отклик...';
    }

    try {
      const resp = await fetch('/api/candidate/apply/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();

      if (data.ok) {
        // Копируем сгенерированный производственный сертификат в буфер обмена для вставки на hh.ru
        if (data.cover_letter && navigator.clipboard) {
          try {
            await navigator.clipboard.writeText(data.cover_letter);
          } catch (clipErr) {
            console.warn('[Clipboard] Copy warning:', clipErr);
          }
        }

        // Закрываем исходное окно формы, если есть
        const parentBackdrop = form.closest('.och-modal-backdrop');
        if (parentBackdrop) parentBackdrop.style.display = 'none';

        // Открываем модальное окно успешной регистрации и перехода на hh.ru
        showHhRedirectModal(data);
        form.reset();
      } else {
        alert(data.error || 'Ошибка при отправке заявки.');
      }
    } catch (err) {
      console.error('[Apply] Request error:', err);
      alert('Ошибка соединения с сервером. Попробуйте еще раз.');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = origHtml;
      }
    }
  };

  // 5b. Интерактивное модальное окно подтверждения и автоматического перехода на hh.ru
  function showHhRedirectModal(data) {
    let modal = document.getElementById('och-hh-redirect-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'och-hh-redirect-modal';
      modal.className = 'och-modal-backdrop';
      modal.style.display = 'flex';
      modal.style.zIndex = '10000';
      document.body.appendChild(modal);
    }

    const hhTargetUrl = data.hh_url || 'https://hh.ru/vacancies/ochakovo';
    const totalScore = data.total_score || 0;
    const rankTitle = data.rank_title || 'Кандидат-практикант';

    modal.innerHTML = `
      <div class="och-modal-box" style="max-width: 540px; border: 2px solid var(--och-gold); animation: modalFadeIn 0.3s ease;">
        <div class="och-modal-header" style="background: linear-gradient(135deg, rgba(213,0,50,0.06), rgba(217,119,6,0.06));">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="width: 44px; height: 44px; border-radius: var(--radius-sm); background: #D50032; color: #fff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 1.4rem;">
              ✓
            </div>
            <div>
              <div style="font-size: 0.72rem; text-transform: uppercase; font-weight: 800; color: var(--och-red);">Заявка сохранена в АО «Очаково»</div>
              <h3 style="font-size: 1.25rem; font-weight: 900; color: var(--och-text-heading); margin: 0;">Переход на официальный отклик hh.ru</h3>
            </div>
          </div>
          <button type="button" class="och-modal-close-btn" onclick="document.getElementById('och-hh-redirect-modal').style.display='none'">✕</button>
        </div>

        <div class="och-modal-body" style="padding: 1.25rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; background: #F8FAFC; border: 1px solid var(--och-border); border-radius: var(--radius-sm); padding: 0.75rem 1rem; margin-bottom: 1rem;">
            <div>
              <div style="font-size: 0.75rem; color: var(--och-text-dim); text-transform: uppercase; font-weight: 700;">Ваш карьерный разряд:</div>
              <div style="font-size: 0.95rem; font-weight: 800; color: var(--och-text-heading);">${rankTitle}</div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 0.75rem; color: var(--och-text-dim); text-transform: uppercase; font-weight: 700;">Рейтинг:</div>
              <div style="font-size: 1.15rem; font-weight: 900; color: var(--och-red);">${totalScore} XP</div>
            </div>
          </div>

          <div style="background: rgba(5,150,105,0.08); border-left: 4px solid #059669; padding: 0.85rem 1rem; border-radius: 0 var(--radius-sm) var(--radius-sm) 0; margin-bottom: 1.25rem;">
            <div style="font-size: 0.84rem; font-weight: 800; color: #065f46; margin-bottom: 0.25rem;">
              📋 Сопроводительное письмо скопировано в буфер обмена!
            </div>
            <div style="font-size: 0.82rem; color: #1e293b; line-height: 1.45;">
              На открывшейся странице вакансии на <strong>hh.ru</strong> нажмите <em>«Откликнуться»</em> и вставьте готовый производственный сертификат комбинации клавиш <strong>Ctrl+V</strong> (или «Вставить»).
            </div>
          </div>

          <div style="display: flex; flex-direction: column; gap: 0.65rem;">
            <a id="och-hh-direct-link" href="${hhTargetUrl}" target="_blank" class="och-btn-primary" style="justify-content: center; padding: 0.9rem; font-size: 1rem; text-decoration: none; width: 100%;">
              <span>Открыть вакансию на hh.ru</span>
              <span id="och-hh-countdown-pill" style="background: rgba(255,255,255,0.25); padding: 0.15rem 0.5rem; border-radius: 12px; font-size: 0.8rem; margin-left: 0.5rem;">(2с)</span>
              <span style="margin-left: 0.25rem;">▶</span>
            </a>
            <button type="button" class="och-btn-secondary" onclick="document.getElementById('och-hh-redirect-modal').style.display='none'" style="justify-content: center; width: 100%;">
              <span>Остаться на сайте «Очаково»</span>
            </button>
          </div>
        </div>
      </div>
    `;

    modal.style.display = 'flex';

    // Автоматический переход на hh.ru через 2 секунды
    let timeLeft = 2;
    const countdownPill = document.getElementById('och-hh-countdown-pill');
    const timer = setInterval(() => {
      timeLeft--;
      if (countdownPill) {
        countdownPill.innerText = `(${timeLeft}с)`;
      }
      if (timeLeft <= 0) {
        clearInterval(timer);
        if (countdownPill) countdownPill.style.display = 'none';
        try {
          window.open(hhTargetUrl, '_blank');
        } catch (e) {
          console.warn('[Popup] Browser blocked window.open, user can click button:', e);
        }
      }
    }, 1000);
  }
  window.showHhRedirectModal = showHhRedirectModal;

  // 5c. Обновление бейджа рейтинга в глобальной навигации
  function updateNavProgressBadge() {
    try {
      const prog = JSON.parse(localStorage.getItem('ochakovo_career_progress') || '{}');
      const total = prog.totalScore || 0;
      const navBadge = document.getElementById('nav-user-score-badge');
      if (navBadge) {
        navBadge.innerText = `${total} XP`;
        if (total > 0) {
          navBadge.classList.add('has-points');
        }
      }
    } catch (e) {}
  }
  window.updateNavProgressBadge = updateNavProgressBadge;

  // Вспомогательная функция для CSRF токена Django
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  window.getCookie = getCookie;

  // 6. Интерактивный виджет: Заводской фольклор и байки со смены
  const LORE_QUOTES = [
    {
      name: "Михалыч говорит:",
      role: "Главный технолог-квасовар комбината",
      avatar: "/static/img/mentor_brewer.jpg",
      quote: "«Двойное брожение — это когда сначала дрожжи волнуются за судьбу партии, а потом молочнокислые бактерии добавляют резкости и бодрости!»",
      location: "Цех брожения №1 • Москва",
      badge: "Партия: «Очаковский 1978»"
    },
    {
      name: "Анна (АСУ ТП):",
      role: "Ведущий инженер робототехники",
      avatar: "/static/img/mentor_engineer.jpg",
      quote: "«Когда робот Krones упаковывает 50 000 банок в час, стажёр понимает: детский Тетрис был не развлечением, а предварительной производственной практикой.»",
      location: "Линия розлива №3 • Krones",
      badge: "Скорость: 50 000 бут/ч"
    },
    {
      name: "Елена (Лаборатория ОТК):",
      role: "Руководитель микробиологического контроля",
      avatar: "/static/img/mentor_lab.jpg",
      quote: "«В нашей лаборатории спор об окрошке решается за 30 секунд: титрование показало, что квас вне конкуренции, а всё остальное — просто салат, залитый не тем напитком!»",
      location: "Центральная лаборатория ОТК",
      badge: "ГОСТ 31494-2012"
    },
    {
      name: "Михалыч говорит:",
      role: "Главный технолог-квасовар комбината",
      avatar: "/static/img/mentor_brewer.jpg",
      quote: "«Стажёр думает, что квас делают из порошка. Старший мастер молча наливает сусло прямо из варочного котла — и возвращает человеку веру в натуральный мир.»",
      location: "Варочный порядок №2",
      badge: "100% солод и рожь"
    },
    {
      name: "Роман (WMS-логистика):",
      role: "Диспетчер автоматизированного хаба",
      avatar: "/static/img/mentor_logistics.jpg",
      quote: "«У логистов закон простой: летом +30°C на термометре — это не жара, это вызов! 500 фур в сутки отгружаем так слаженно, будто это телепортация.»",
      location: "Логистический хаб «Очаково»",
      badge: "Отгрузка: 24/7"
    },
    {
      name: "Артём (Бренд-маркетинг):",
      role: "Бренд-стратег молодежных напитков",
      avatar: "/static/img/mentor_marketing.jpg",
      quote: "«Когда мы запускали CoolCola и обновляли линейку кваса, главное правило было: вкус решает всё. Если зумер пробует наш квас и говорит «это база», значит кампания удалась!»",
      location: "Креативный хаб Очаково",
      badge: "Трендсеттер 2026"
    },
    {
      name: "Михалыч говорит:",
      role: "Главный технолог-квасовар комбината",
      avatar: "/static/img/mentor_brewer.jpg",
      quote: "«— Михалыч, а что делать, если квас получился чересчур вкусным? — Разливать в танки быстрее, пока коллеги из соседнего цеха на дегустацию не сбежались!»",
      location: "Дегустационный зал",
      badge: "Секрет рецепта"
    },
    {
      name: "Анна (АСУ ТП):",
      role: "Ведущий инженер робототехники",
      avatar: "/static/img/mentor_engineer.jpg",
      quote: "«Если инженер молча смотрит на датчик давления дольше 15 секунд — не отвлекайте. Он мысленно общается с контроллером Siemens на машинном языке.»",
      location: "Щит управления SCADA",
      badge: "ПЛК онлайн"
    },
    {
      name: "Елена (Лаборатория ОТК):",
      role: "Руководитель микробиологического контроля",
      avatar: "/static/img/mentor_lab.jpg",
      quote: "«У химиков-пивоваров нет ошибок. Если цвет или плотность немного отклонились от стандарта — значит, только что родился новый крафтовый эксклюзив!»",
      location: "Микробиология",
      badge: "Чистая культура"
    }
  ];

  function initFactoryJokes() {
    const btn = document.getElementById('btn-next-joke');
    const quoteEl = document.getElementById('lore-quote');
    const nameEl = document.getElementById('lore-name');
    const roleEl = document.getElementById('lore-role');
    const avatarEl = document.getElementById('lore-avatar');
    const locEl = document.getElementById('lore-location');
    const badgeEl = document.getElementById('lore-badge');

    if (!btn || !quoteEl) return;

    let currentIndex = 0;

    btn.addEventListener('click', () => {
      let nextIndex = Math.floor(Math.random() * LORE_QUOTES.length);
      if (nextIndex === currentIndex) {
        nextIndex = (currentIndex + 1) % LORE_QUOTES.length;
      }
      currentIndex = nextIndex;
      const item = LORE_QUOTES[currentIndex];

      quoteEl.style.opacity = '0';
      if (avatarEl) avatarEl.style.transform = 'scale(0.85)';

      setTimeout(() => {
        quoteEl.textContent = item.quote;
        if (nameEl) nameEl.textContent = item.name;
        if (roleEl) roleEl.textContent = item.role;
        if (avatarEl) {
          avatarEl.src = item.avatar;
          avatarEl.style.transform = 'scale(1)';
        }
        if (locEl) locEl.textContent = item.location;
        if (badgeEl) badgeEl.textContent = item.badge;
        quoteEl.style.opacity = '1';
      }, 200);
    });
  }

  // 7. Интерактивный батл за окрошку (story.html)
  function initOkroshkaBattle() {
    const btnKvass = document.getElementById('btn-vote-kvass');
    const btnKefir = document.getElementById('btn-vote-kefir');
    const voteStatus = document.getElementById('vote-status-msg');

    if (btnKvass && voteStatus) {
      btnKvass.addEventListener('click', () => {
        voteStatus.innerHTML = '🌾 <strong>Наш человек!</strong> Михалыч лично жмёт вам руку. Белый квас с хреном — золотой стандарт русской кухни!';
        voteStatus.style.color = 'var(--och-gold-light)';
        btnKvass.style.transform = 'scale(1.05)';
        btnKefir.style.transform = 'scale(0.95)';
        btnKefir.style.opacity = '0.5';
      });
    }

    if (btnKefir && voteStatus) {
      btnKefir.addEventListener('click', () => {
        voteStatus.innerHTML = '🥛 <strong>Ой-ой!</strong> Михалыч неодобрительно покачал головой: <em>«Окрошка на кефире — это просто салат, залитый не тем напитком!»</em> Попробуйте наш Очаковский белый квас — изменим ваше мнение за 1 глоток!';
        voteStatus.style.color = '#fca5a5';
      });
    }
  }

  // 8. Пасхалка в консоли браузера для жюри и разработчиков
  function initDevToolsEasterEgg() {
    if (typeof console !== 'undefined' && console.log) {
      console.log(
        '%c🍺 АО МПБК «ОЧАКОВО» • КАРЬЕРНЫЙ ПОРТАЛ 2026\n' +
        '%cСтудент или разработчик? Ищешь баги или секрет двойного брожения?\n' +
        'Приходи к нам на оплачиваемую практику в отдел промышленной автоматизации (КИПиА, SCADA, Python/Django)!\n' +
        'Телефон HR: +7 (495) 785-39-30 (доб. 1155) • rabota@ochakovo.ru',
        'color: #D50032; font-size: 16px; font-weight: 900; text-shadow: 0 1px 2px rgba(0,0,0,0.4);',
        'color: #f59e0b; font-size: 12px; font-weight: 600; line-height: 1.5;'
      );
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    initIcons();
    registerPWA();
    initNetworkMonitor();
    initMobileMenu();
    initFactoryJokes();
    initOkroshkaBattle();
    initDevToolsEasterEgg();
    updateNavProgressBadge();
  });
})();
