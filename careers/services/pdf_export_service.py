# -*- coding: utf-8 -*-
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class SkillsPdfService:
    """Генератор официального PDF паспорта компетенций соискателя комбината «Очаково»"""

    _fonts_registered = False

    @classmethod
    def _ensure_fonts(cls):
        if cls._fonts_registered:
            return
        
        # Регистрация стандартных системных шрифтов Windows с поддержкой кириллицы
        candidates_regular = [
            r'C:\Windows\Fonts\arial.ttf',
            r'C:\Windows\Fonts\segoeui.ttf',
            r'C:\Windows\Fonts\tahoma.ttf'
        ]
        candidates_bold = [
            r'C:\Windows\Fonts\arialbd.ttf',
            r'C:\Windows\Fonts\segoeuib.ttf',
            r'C:\Windows\Fonts\tahomabd.ttf'
        ]

        reg_path = next((p for p in candidates_regular if os.path.exists(p)), None)
        bold_path = next((p for p in candidates_bold if os.path.exists(p)), None)

        if reg_path:
            pdfmetrics.registerFont(TTFont('OchSans', reg_path))
        if bold_path:
            pdfmetrics.registerFont(TTFont('OchSans-Bold', bold_path))
        
        cls._fonts_registered = True

    @classmethod
    def generate_passport(cls, candidate_data: dict) -> bytes:
        cls._ensure_fonts()

        full_name = candidate_data.get('full_name') or 'Стажёр комбината «Очаково»'
        university = candidate_data.get('university') or 'Профильный пищевой/технический вуз'
        score = candidate_data.get('total_score', 380)
        rank_title = candidate_data.get('rank_title') or 'Младший технолог-практикант (Разряд II)'
        completed_cases = candidate_data.get('completed_cases') or []
        issue_date = datetime.now().strftime("%d.%m.%Y")

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # 1. Шапка документа: фирменный красный Очаково
        c.setFillColor(colors.HexColor('#D50032'))
        c.rect(0, height - 90, width, 90, fill=True, stroke=False)

        # Акцентная золотая полоса под шапкой
        c.setFillColor(colors.HexColor('#F59E0B'))
        c.rect(0, height - 94, width, 4, fill=True, stroke=False)

        # Белый заголовок
        c.setFillColor(colors.white)
        c.setFont('OchSans-Bold', 20)
        c.drawString(40, height - 42, "АО «ОЧАКОВО» | КАРЬЕРНАЯ ПЛАТФОРМА 2026")
        c.setFont('OchSans', 10.5)
        c.drawString(40, height - 66, "ОФИЦИАЛЬНЫЙ ПАСПОРТ ПРОИЗВОДСТВЕННЫХ КОМПЕТЕНЦИЙ СТАЖЁРА")

        # 2. Главный заголовок
        c.setFillColor(colors.HexColor('#0F172A'))
        c.setFont('OchSans-Bold', 15)
        c.drawString(40, height - 128, "СЕРТИФИКАТ ПРАКТИЧЕСКИХ НАВЫКОВ И ДОПУСКА К СТАЖИРОВКЕ")

        # 3. Информационный блок соискателя
        c.setFillColor(colors.HexColor('#F8FAFC'))
        c.setStrokeColor(colors.HexColor('#CBD5E1'))
        c.setLineWidth(1.2)
        c.roundRect(40, height - 225, width - 80, 85, 8, fill=True, stroke=True)

        c.setFillColor(colors.HexColor('#0F172A'))
        c.setFont('OchSans-Bold', 12.5)
        c.drawString(60, height - 160, f"Соискатель: {full_name}")
        c.setFont('OchSans', 9.5)
        c.drawString(60, height - 180, f"Учебное заведение: {university}")
        c.drawString(60, height - 200, f"Квалификация: {rank_title} | Заработано баллов: {score} XP")

        # QR код верификации (графическая имитация)
        c.setStrokeColor(colors.HexColor('#1E293B'))
        c.setFillColor(colors.HexColor('#FFFFFF'))
        c.roundRect(width - 110, height - 215, 60, 60, 4, fill=True, stroke=True)
        c.setFillColor(colors.HexColor('#1E293B'))
        c.setFont('OchSans-Bold', 8)
        c.drawCentredString(width - 80, height - 188, "[ QR ]")
        c.setFont('OchSans', 6.5)
        c.drawCentredString(width - 80, height - 202, "HR ВЕРИФИКАЦИЯ")

        # 4. Блок подтверждённых навыков
        c.setFont('OchSans-Bold', 13)
        c.setFillColor(colors.HexColor('#D50032'))
        c.drawString(40, height - 255, "ПОДТВЕРЖДЁННЫЕ ПРОИЗВОДСТВЕННЫЕ КОМПЕТЕНЦИИ НА СТЕНДЕ / В СИМУЛЯТОРЕ:")

        standard_skills = [
            ("Управление терморежимом ЦКТ №7 (500 000 л)", "Контроль давления CO2 2.5 бар, рубашка гликоля -3°C, защита от автолиза"),
            ("Эксплуатация автоматизированных линий Krones", "Скорость розлива до 40 000 бут/час, изобарический налив, защита ПЭТ"),
            ("Физико-химический лабораторный анализ (Brix & pH)", "Рефрактометрическое определение сухих веществ 8.4°Bx, ГОСТ 31494-2012"),
            ("Бережливое производство 5S и логистика WMS", "Адресное хранение FIFO, лазерная навигация AGV, терморежим +2..+12°C")
        ]

        y = height - 285
        for name, desc in standard_skills:
            # Зелёный чекбокс
            c.setFillColor(colors.HexColor('#10B981'))
            c.setFont('OchSans-Bold', 10.5)
            c.drawString(45, y, "✔")

            c.setFillColor(colors.HexColor('#0F172A'))
            c.drawString(65, y, name)
            c.setFont('OchSans', 8.5)
            c.setFillColor(colors.HexColor('#64748B'))
            c.drawString(65, y - 13, desc)
            y -= 34

        # 5. Блок полученных бонусов
        c.setFillColor(colors.HexColor('#FEF3C7'))
        c.setStrokeColor(colors.HexColor('#F59E0B'))
        c.roundRect(40, y - 95, width - 80, 85, 8, fill=True, stroke=True)

        c.setFillColor(colors.HexColor('#92400E'))
        c.setFont('OchSans-Bold', 11)
        c.drawString(55, y - 25, "ОФИЦИАЛЬНО НАЧИСЛЕННЫЕ БОНУСЫ СОИСКАТЕЛЯ В АО «ОЧАКОВО»:")
        c.setFont('OchSans', 9)
        c.drawString(55, y - 44, "• Сокращение срока вводной практики с 3 месяцев до 1 месяца (акселерация адаптации).")
        c.drawString(55, y - 60, "• Право прохождения квалификационного теста на должности 2 категории (оклад от 80 000 ₽).")
        c.drawString(55, y - 76, "• Прямой приоритетный допуск к собеседованию с Главным технологом комбината.")

        # 6. Подписи и печать комбината
        y_sign = y - 160
        c.setFillColor(colors.HexColor('#0F172A'))
        c.setFont('OchSans-Bold', 9.5)
        c.drawString(45, y_sign, "Директор департамента по управлению персоналом:")
        c.setFont('OchSans', 9)
        c.drawString(45, y_sign - 16, "АО «Очаково» ____________________ / Савельева Н.В. /")

        c.setFont('OchSans-Bold', 9.5)
        c.drawString(width - 250, y_sign, "Главный технолог комбината:")
        c.setFont('OchSans', 9)
        c.drawString(width - 250, y_sign - 16, "«Очаково» ____________________ / Михалыч П.С. /")

        # Синяя печать комбината
        c.setStrokeColor(colors.HexColor('#1D4ED8'))
        c.setFillColor(colors.HexColor('#EFF6FF'))
        c.circle(width / 2, y_sign - 10, 36, fill=False, stroke=True)
        c.setFont('OchSans-Bold', 6.5)
        c.setFillColor(colors.HexColor('#1D4ED8'))
        c.drawCentredString(width / 2, y_sign + 4, "АО «ОЧАКОВО»")
        c.drawCentredString(width / 2, y_sign - 8, "* ДЛЯ СТАЖИРОВОК *")
        c.drawCentredString(width / 2, y_sign - 20, "МОСКВА, 1978-2026")

        # Подвал
        c.setFillColor(colors.HexColor('#94A3B8'))
        c.setFont('OchSans', 7.5)
        c.drawString(40, 35, f"Дата формирования документа: {issue_date} | Документ имеет юридическую силу для HR-отбора комбината.")
        c.drawRightString(width - 40, 35, "ochakovo.ru/careers · Тел. HR: +7 (495) 787-88-88")

        c.showPage()
        c.save()

        return buffer.getvalue()
