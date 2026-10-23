import os

def run():
    path = os.path.join('careers', 'templates', 'careers', 'home.html')
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Enhance Handbook Section with Comic Character Cards
    old_handbook = """    <div class="och-handbook-grid">
      <div class="och-handbook-card">
        <h4><i data-lucide="home" style="width: 18px; height: 18px; color: var(--och-red);"></i> Общежитие в Москве</h4>
        <p>Комнаты на 4–6 человек, чистые душевые, общие кухни и зоны отдыха. Компания «Очаково» компенсирует 50% стоимости проживания для иногородних практикантов.</p>
      </div>

      <div class="och-handbook-card">
        <h4><i data-lucide="utensils" style="width: 18px; height: 18px; color: var(--och-gold-light);"></i> Заводская столовая</h4>
        <p>Сытные комплексные обеды из трёх блюд с выпечкой и натуральным квасом. Половину стоимости питания компенсирует завод — обед обходится всего в ~150 ₽.</p>
      </div>

      <div class="och-handbook-card">
        <h4><i data-lucide="shirt" style="width: 18px; height: 18px; color: var(--och-blue);"></i> Спецодежда и прачечная</h4>
        <p>Полный комплект удобной рабочей формы и спецобуви выдаётся бесплатно в первый рабочий день. На комбинате работает собственная бесплатная прачечная.</p>
      </div>

      <div class="och-handbook-card">
        <h4><i data-lucide="calendar" style="width: 18px; height: 18px; color: var(--och-purple);"></i> Сменный график 2/2</h4>
        <p>Смены по 12 часов (дневные и ночные) с перерывами на отдых. График составляется руководителем цеха заранее — можно согласовать дни под сдачу сессии и экзаменов.</p>
      </div>

      <div class="och-handbook-card">
        <h4><i data-lucide="credit-card" style="width: 18px; height: 18px; color: var(--och-green);"></i> Зарплата 12 и 27 числа</h4>
        <p>Белая зарплата перечисляется официально на банковскую карту 2 раза в месяц без задержек. Официальный трудовой стаж в резюме с первого дня практики.</p>
      </div>

      <div class="och-handbook-card">
        <h4><i data-lucide="heart-pulse" style="width: 18px; height: 18px; color: var(--och-red);"></i> Здравпункт на заводе</h4>
        <p>Круглосуточный медицинский пункт прямо на территории комбината. В случае недомогания врач окажет помощь, выдаст направление и поможет оформить больничный.</p>
      </div>
    </div>"""

    new_handbook = """    <div class="och-handbook-grid">
      <div class="och-handbook-card comic-card" style="padding: 1.25rem;">
        <div style="display: flex; gap: 0.85rem; align-items: flex-start;">
          <img src="{% static 'img/avatar_student.jpg' %}" alt="Студент" style="width: 52px; height: 52px; border-radius: 8px; border: 2px solid #1E293B; object-fit: cover; flex-shrink: 0; box-shadow: 2px 2px 0px #1E293B;">
          <div>
            <h4 style="margin: 0 0 0.35rem; font-size: 1.05rem; font-weight: 800; color: #1E293B; display: flex; align-items: center; gap: 0.4rem;">
              <i data-lucide="home" style="width: 17px; height: 17px; color: var(--och-red);"></i>
              <span>Общежитие в Москве</span>
            </h4>
            <p style="font-size: 0.85rem; color: #475569; line-height: 1.45; margin: 0;">ул. Рябиновая, 36 к2. Заселение до 14:00 или после 16:00. «Очаково» компенсирует 50% стоимости проживания.</p>
          </div>
        </div>
      </div>

      <div class="och-handbook-card comic-card" style="padding: 1.25rem;">
        <div style="display: flex; gap: 0.85rem; align-items: flex-start;">
          <img src="{% static 'img/mentor_chef.jpg' %}" alt="Шеф-повар" style="width: 52px; height: 52px; border-radius: 8px; border: 2px solid #1E293B; object-fit: cover; flex-shrink: 0; box-shadow: 2px 2px 0px #1E293B;">
          <div>
            <h4 style="margin: 0 0 0.35rem; font-size: 1.05rem; font-weight: 800; color: #1E293B; display: flex; align-items: center; gap: 0.4rem;">
              <i data-lucide="utensils" style="width: 17px; height: 17px; color: var(--och-gold-light);"></i>
              <span>Заводская столовая</span>
            </h4>
            <p style="font-size: 0.85rem; color: #475569; line-height: 1.45; margin: 0;">Обед с 11:30 до 14:30, ужин с 20:30. Завод компенсирует 50% чека — обед обходится в ~150 ₽ по карте сотрудника.</p>
          </div>
        </div>
      </div>

      <div class="och-handbook-card comic-card" style="padding: 1.25rem;">
        <div style="display: flex; gap: 0.85rem; align-items: flex-start;">
          <img src="{% static 'img/mentor_safety.jpg' %}" alt="СИЗ и ТБ" style="width: 52px; height: 52px; border-radius: 8px; border: 2px solid #1E293B; object-fit: cover; flex-shrink: 0; box-shadow: 2px 2px 0px #1E293B;">
          <div>
            <h4 style="margin: 0 0 0.35rem; font-size: 1.05rem; font-weight: 800; color: #1E293B; display: flex; align-items: center; gap: 0.4rem;">
              <i data-lucide="shirt" style="width: 17px; height: 17px; color: var(--och-blue);"></i>
              <span>Спецодежда & Прачечная</span>
            </h4>
            <p style="font-size: 0.85rem; color: #475569; line-height: 1.45; margin: 0;">Фирменный комплект спецодежды и обуви выдаётся бесплатно. На заводе работает бесплатная прачечная (8:30-16:30).</p>
          </div>
        </div>
      </div>

      <div class="och-handbook-card comic-card" style="padding: 1.25rem;">
        <div style="display: flex; gap: 0.85rem; align-items: flex-start;">
          <img src="{% static 'img/avatar_student_girl.jpg' %}" alt="График смен" style="width: 52px; height: 52px; border-radius: 8px; border: 2px solid #1E293B; object-fit: cover; flex-shrink: 0; box-shadow: 2px 2px 0px #1E293B;">
          <div>
            <h4 style="margin: 0 0 0.35rem; font-size: 1.05rem; font-weight: 800; color: #1E293B; display: flex; align-items: center; gap: 0.4rem;">
              <i data-lucide="calendar" style="width: 17px; height: 17px; color: var(--och-purple);"></i>
              <span>Сменный график 2/2</span>
            </h4>
            <p style="font-size: 0.85rem; color: #475569; line-height: 1.45; margin: 0;">Смены 12 часов. График составляется руководителем цеха — легко совмещать с зачётами и сессией в вузе.</p>
          </div>
        </div>
      </div>

      <div class="och-handbook-card comic-card" style="padding: 1.25rem;">
        <div style="display: flex; gap: 0.85rem; align-items: flex-start;">
          <img src="{% static 'img/mentor_director.jpg' %}" alt="Директор" style="width: 52px; height: 52px; border-radius: 8px; border: 2px solid #1E293B; object-fit: cover; flex-shrink: 0; box-shadow: 2px 2px 0px #1E293B;">
          <div>
            <h4 style="margin: 0 0 0.35rem; font-size: 1.05rem; font-weight: 800; color: #1E293B; display: flex; align-items: center; gap: 0.4rem;">
              <i data-lucide="credit-card" style="width: 17px; height: 17px; color: var(--och-green);"></i>
              <span>Зарплата 12 и 27 числа</span>
            </h4>
            <p style="font-size: 0.85rem; color: #475569; line-height: 1.45; margin: 0;">Официальный срочный трудовой договор по ТК РФ. Белая зарплата 2 раза в месяц без задержек. Стаж с 1-го дня.</p>
          </div>
        </div>
      </div>

      <div class="och-handbook-card comic-card" style="padding: 1.25rem;">
        <div style="display: flex; gap: 0.85rem; align-items: flex-start;">
          <img src="{% static 'img/mentor_brewer.jpg' %}" alt="Наставник" style="width: 52px; height: 52px; border-radius: 8px; border: 2px solid #1E293B; object-fit: cover; flex-shrink: 0; box-shadow: 2px 2px 0px #1E293B;">
          <div>
            <h4 style="margin: 0 0 0.35rem; font-size: 1.05rem; font-weight: 800; color: #1E293B; display: flex; align-items: center; gap: 0.4rem;">
              <i data-lucide="award" style="width: 17px; height: 17px; color: var(--och-red);"></i>
              <span>Опытный наставник</span>
            </h4>
            <p style="font-size: 0.85rem; color: #475569; line-height: 1.45; margin: 0;">За каждым стажёром закрепляется опытный мастер цеха из Учебного центра комбината, который обучает на месте.</p>
          </div>
        </div>
      </div>
    </div>"""

    assert old_handbook in text, 'old_handbook not found in home.html'
    text = text.replace(old_handbook, new_handbook)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('home.html updated with comic handbook cards!')

if __name__ == '__main__':
    run()
