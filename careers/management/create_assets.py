import os

def create_svg_assets():
    icons = {
        'valve_cooling.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#38bdf8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="32" cy="32" r="24" fill="rgba(56,189,248,0.12)" stroke="#38bdf8"/>
  <path d="M32 12v40M12 32h40" stroke-dasharray="2 2" stroke="#0284c7"/>
  <polygon points="20,24 44,24 32,32" fill="#38bdf8" stroke="none"/>
  <polygon points="20,40 44,40 32,32" fill="#0284c7" stroke="none"/>
  <circle cx="32" cy="32" r="4" fill="#ffffff"/>
  <path d="M26 18c3-3 9-3 12 0" stroke="#38bdf8" stroke-width="2"/>
</svg>""",

        'starter_culture.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#f59e0b" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <path d="M26 12h12M32 12v12l14 24a4 4 0 0 1-3.5 6h-21a4 4 0 0 1-3.5-6L32 24" fill="rgba(245,158,11,0.15)"/>
  <circle cx="32" cy="44" r="3" fill="#f59e0b"/>
  <circle cx="27" cy="48" r="2" fill="#fbbf24"/>
  <circle cx="37" cy="47" r="2.5" fill="#f59e0b"/>
  <path d="M24 40c4-2 12-2 16 0" stroke="#f59e0b" stroke-width="2"/>
</svg>""",

        'cip_wash.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <rect x="14" y="16" width="36" height="36" rx="8" fill="rgba(16,185,129,0.12)"/>
  <path d="M32 24v12M24 30h16" stroke="#10b981" stroke-width="3.5"/>
  <circle cx="32" cy="30" r="12" stroke="#10b981" stroke-dasharray="4 3"/>
  <path d="M20 54l6-6M44 54l-6-6M20 14l6 6M44 14l-6 6" stroke="#34d399" stroke-width="2"/>
</svg>""",

        'emergency_stop.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#ef4444" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="32" cy="32" r="26" fill="rgba(239,68,68,0.15)" stroke="#ef4444"/>
  <circle cx="32" cy="32" r="18" fill="#ef4444" stroke="#b91c1c" stroke-width="2"/>
  <rect x="25" y="25" width="14" height="14" rx="2" fill="#ffffff" stroke="none"/>
  <path d="M16 16l32 32M48 16L16 48" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/>
</svg>""",

        'refractometer.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#8b5cf6" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <rect x="16" y="12" width="32" height="40" rx="6" fill="rgba(139,92,246,0.12)"/>
  <rect x="22" y="18" width="20" height="14" rx="2" fill="#1e1b4b" stroke="#a78bfa" stroke-width="1.5"/>
  <path d="M26 25h12M32 21v8" stroke="#38bdf8" stroke-width="2"/>
  <circle cx="26" cy="42" r="3" fill="#8b5cf6"/>
  <circle cx="38" cy="42" r="3" fill="#a78bfa"/>
</svg>""",

        'tasting_mug.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#f97316" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <path d="M18 20h22v26a6 6 0 0 1-6 6H24a6 6 0 0 1-6-6V20z" fill="rgba(249,115,22,0.15)"/>
  <path d="M40 24h6a5 5 0 0 1 5 5v8a5 5 0 0 1-5 5h-6" stroke="#f97316" stroke-width="3"/>
  <path d="M16 20c2-3 5-3 7 0s5 3 7 0 5-3 7 0 5 3 7 0" fill="#ffffff" stroke="#fed7aa" stroke-width="2"/>
  <path d="M24 28v14M29 28v14M34 28v14" stroke="rgba(249,115,22,0.4)" stroke-width="2"/>
</svg>""",

        'intercom_radio.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#06b6d4" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <rect x="20" y="20" width="24" height="34" rx="4" fill="rgba(6,182,212,0.12)"/>
  <path d="M26 20V10M26 10h4" stroke="#06b6d4" stroke-width="3"/>
  <circle cx="32" cy="30" r="6" fill="#0891b2" stroke="none"/>
  <path d="M25 44h14M25 48h10" stroke="#22d3ee" stroke-width="2"/>
</svg>""",

        'ph_meter.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none" stroke="#ec4899" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
  <path d="M28 12h8v24l-4 16-4-16V12z" fill="rgba(236,72,153,0.15)"/>
  <circle cx="32" cy="52" r="2.5" fill="#ec4899"/>
  <path d="M24 12h16M28 20h8M29 28h6" stroke="#f472b6" stroke-width="2"/>
</svg>"""
    }

    out_dir = os.path.join('static', 'img', 'equipment')
    os.makedirs(out_dir, exist_ok=True)
    for fname, content in icons.items():
        with open(os.path.join(out_dir, fname), 'w', encoding='utf-8') as f:
            f.write(content)
    print(f'Generated {len(icons)} equipment icons in {out_dir}')

    # Mentor avatars in SVG for Lab Elena, Logistics Roman, Marketing Artem
    mentors = {
        'mentor_lab.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" fill="none">
  <rect width="120" height="120" rx="24" fill="#0c192c"/>
  <circle cx="60" cy="46" r="22" fill="#fcd34d"/>
  <path d="M38 42c0-12 10-22 22-22s22 10 22 22c0 2-1 4-2 6-3-5-9-8-20-8s-17 3-20 8c-1-2-2-4-2-6z" fill="#78350f"/>
  <circle cx="53" cy="45" r="2.5" fill="#1e293b"/>
  <circle cx="67" cy="45" r="2.5" fill="#1e293b"/>
  <path d="M56 54c2 2 6 2 8 0" stroke="#b45309" stroke-width="2" stroke-linecap="round"/>
  <!-- Glasses -->
  <rect x="46" y="40" width="13" height="10" rx="3" stroke="#0284c7" stroke-width="1.5" fill="rgba(56,189,248,0.2)"/>
  <rect x="61" y="40" width="13" height="10" rx="3" stroke="#0284c7" stroke-width="1.5" fill="rgba(56,189,248,0.2)"/>
  <path d="M59 45h2" stroke="#0284c7" stroke-width="1.5"/>
  <!-- Lab Coat -->
  <path d="M28 112c0-22 14-38 32-38s32 16 32 38H28z" fill="#f8fafc"/>
  <path d="M60 74v38" stroke="#cbd5e1" stroke-width="2"/>
  <!-- Red Ochakovo Collar -->
  <path d="M50 74l10 14 10-14" fill="#d50032"/>
  <rect x="36" y="90" width="14" height="6" rx="2" fill="#d50032"/>
</svg>""",

        'mentor_logistics.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" fill="none">
  <rect width="120" height="120" rx="24" fill="#0f172a"/>
  <circle cx="60" cy="48" r="22" fill="#fed7aa"/>
  <path d="M38 42c0-12 10-22 22-22s22 10 22 22v4H38v-4z" fill="#1e293b"/>
  <!-- Headset -->
  <path d="M35 48c0-14 11-25 25-25s25 11 25 25" stroke="#94a3b8" stroke-width="3" stroke-linecap="round"/>
  <rect x="32" y="44" width="6" height="12" rx="2" fill="#0284c7"/>
  <rect x="82" y="44" width="6" height="12" rx="2" fill="#0284c7"/>
  <path d="M35 52l12 10h4" stroke="#0284c7" stroke-width="2"/>
  <circle cx="53" cy="46" r="2.5" fill="#0f172a"/>
  <circle cx="67" cy="46" r="2.5" fill="#0f172a"/>
  <path d="M56 55c2 2 6 2 8 0" stroke="#c2410c" stroke-width="2" stroke-linecap="round"/>
  <!-- High-Vis Vest -->
  <path d="M28 112c0-22 14-38 32-38s32 16 32 38H28z" fill="#f59e0b"/>
  <path d="M48 74v38M72 74v38" stroke="#f8fafc" stroke-width="4"/>
  <path d="M60 74l-6 10h12L60 74z" fill="#d50032"/>
</svg>""",

        'mentor_marketing.svg': """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" fill="none">
  <rect width="120" height="120" rx="24" fill="#18181b"/>
  <circle cx="60" cy="46" r="22" fill="#fde68a"/>
  <!-- Modern Stylish Hair -->
  <path d="M36 38c2-12 14-18 26-18 14 0 24 8 24 18 0 4-4 6-8 6-4-8-12-10-22-10-8 0-14 2-20 4z" fill="#451a03"/>
  <circle cx="53" cy="46" r="2.5" fill="#1c1917"/>
  <circle cx="67" cy="46" r="2.5" fill="#1c1917"/>
  <path d="M55 54c3 3 7 3 10 0" stroke="#b45309" stroke-width="2" stroke-linecap="round"/>
  <!-- Stylish Hoodie -->
  <path d="M28 112c0-22 14-38 32-38s32 16 32 38H28z" fill="#1e293b"/>
  <path d="M52 74c0 6 4 12 8 12s8-6 8-12" fill="#d50032"/>
  <circle cx="60" cy="100" r="10" fill="#d50032"/>
  <path d="M56 100l3 3 6-6" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
</svg>"""
    }

    img_dir = os.path.join('static', 'img')
    for fname, content in mentors.items():
        with open(os.path.join(img_dir, fname), 'w', encoding='utf-8') as f:
            f.write(content)
    print(f'Generated {len(mentors)} mentor avatars in {img_dir}')

    # Ochakovo Logo and PWA Icons
    ochakovo_emblem = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#D50032"/>
      <stop offset="100%" stop-color="#8B001F"/>
    </linearGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FDE68A"/>
      <stop offset="100%" stop-color="#F59E0B"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="112" fill="url(#bgGrad)"/>
  <circle cx="256" cy="256" r="200" stroke="rgba(255,255,255,0.15)" stroke-width="8"/>
  <circle cx="256" cy="256" r="184" stroke="url(#goldGrad)" stroke-width="4" stroke-dasharray="16 10"/>
  <!-- Malt Hops Motif -->
  <path d="M256 110c-35 50-25 110 0 160 25-50 35-110 0-160z" fill="url(#goldGrad)"/>
  <path d="M210 160c-40 40-30 90 0 130 20-40 25-90 0-130z" fill="url(#goldGrad)" opacity="0.85"/>
  <path d="M302 160c40 40 30 90 0 130-20-40-25-90 0-130z" fill="url(#goldGrad)" opacity="0.85"/>
  <!-- Central Letter O / Barrel Ring -->
  <circle cx="256" cy="300" r="72" fill="#ffffff"/>
  <circle cx="256" cy="300" r="46" fill="#D50032"/>
  <!-- 1978 Star -->
  <polygon points="256,282 260,294 272,294 262,301 266,312 256,305 246,312 250,301 240,294 252,294" fill="url(#goldGrad)"/>
  <text x="256" y="420" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="900" font-size="34" fill="#ffffff" letter-spacing="6">ОЧАКОВО</text>
  <text x="256" y="448" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="700" font-size="16" fill="url(#goldGrad)" letter-spacing="4">КАРЬЕРА 2026</text>
</svg>"""

    with open(os.path.join(img_dir, 'ochakovo_emblem.svg'), 'w', encoding='utf-8') as f:
        f.write(ochakovo_emblem)

    # Official Ochakovo wordmark logo
    ochakovo_logo = """<svg width="220" height="48" viewBox="0 0 160 38" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M11.3328 16.9242C8.03224 16.9242 6.04674 14.3585 6.04674 11.1353C6.04674 7.88635 8.03224 5.21754 11.3328 5.21754C14.7365 5.21754 16.4641 7.88635 16.4641 11.1353C16.4641 14.3585 14.7236 16.9242 11.3328 16.9242ZM11.3328 0.0217285C4.78325 0.0217285 0 4.61156 0 10.9291C0 17.2981 4.09993 22.1071 11.3328 22.1071C18.3852 22.1071 22.5624 17.2981 22.5624 10.9291C22.5624 4.61156 17.8437 0.0217285 11.3328 0.0217285ZM37.1829 10.1426C36.2804 10.5165 34.888 10.7743 34.0886 10.7743C31.6906 10.7743 30.7107 9.92342 30.7107 6.5455V0.498757H24.664V7.26749C24.664 14.0878 28.1837 15.8283 32.2965 15.8283C34.0886 15.8283 35.9194 15.4802 37.1829 15.0934V21.643H43.2554V0.485851H37.1829V10.1426ZM89.7728 0.498757H83.1201L77.0991 10.0137V0.498757H70.975V21.6559H77.0991V12.012L83.4682 21.6559H90.6108L83.1072 10.5551L89.7728 0.498757ZM60.0548 13.7268H54.1628L57.0894 5.24331L60.0548 13.7268ZM53.0411 0.498757L45.9372 21.6559H52.2417L53.2216 18.5616H61.0089L61.9887 21.6559H68.3062L61.1765 0.498757H53.0411ZM122.353 16.8211V13.0693H126.981C128.593 13.0693 129.573 13.5978 129.573 14.9774C129.573 16.3569 128.774 16.8211 127.188 16.8211H122.353ZM126.698 5.41092C128.155 5.41092 128.993 5.83638 128.993 7.21591C128.993 8.60833 127.987 9.05957 126.53 9.05957H122.353V5.41092H126.698ZM131.288 11.0064C133.686 10.3489 134.756 8.41495 134.756 6.37788C134.756 2.36821 132.035 0.511623 127.304 0.511623H116.319V21.6688H128.683C132.667 21.6688 135.388 19.5801 135.388 16.1249C135.388 13.5721 134.008 11.7155 131.288 11.0064ZM101.802 16.9242C98.5012 16.9242 96.5157 14.3585 96.5157 11.1353C96.5157 7.88635 98.5012 5.21754 101.802 5.21754C105.205 5.21754 106.933 7.88635 106.933 11.1353C106.946 14.3585 105.205 16.9242 101.802 16.9242ZM101.802 0.0217285C95.2522 0.0217285 90.469 4.61156 90.469 10.9291C90.469 17.2981 94.5689 22.1071 101.802 22.1071C108.854 22.1071 113.031 17.2981 113.031 10.9291C113.031 4.61156 108.326 0.0217285 101.802 0.0217285ZM148.77 16.9242C145.47 16.9242 143.484 14.3585 143.484 11.1353C143.484 7.88635 145.47 5.21754 148.77 5.21754C152.174 5.21754 153.915 7.88635 153.915 11.1353C153.915 14.3585 152.174 16.9242 148.77 16.9242ZM148.77 0.0217285C142.221 0.0217285 137.438 4.61156 137.438 10.9291C137.438 17.2981 141.55 22.1071 148.77 22.1071C155.823 22.1071 160 17.2981 160 10.9291C160 4.61156 155.294 0.0217285 148.77 0.0217285Z" fill="#D50032"/>
  <path d="M6.99944 32.6922H2.49986V29.1467H0.978516V37.8106H2.49986V34.033H6.99944V37.8106H8.52083V29.1467H6.99944V32.6922ZM12.9172 29.1467L9.51356 37.8106H11.2412L11.8729 36.1475H15.8439L16.4757 37.8106H18.2033L14.7996 29.1467H12.9172ZM12.3113 34.8195L13.8713 30.6938L15.4314 34.8195H12.3113ZM17.5071 30.4875H20.1372V37.8106H21.6586V30.4875H24.2759V29.1467H17.5071V30.4875ZM29.1235 34.2006L26.7384 29.1467H25.0107L28.2726 35.5157C27.86 36.3151 27.5635 36.6245 26.8544 36.6245C26.4419 36.6245 26.0422 36.4053 25.7199 36.1346L25.1783 37.3852C25.4491 37.6688 26.1711 37.9783 26.9576 37.9783C28.4402 37.9783 29.0977 37.2434 29.6392 36.199L33.2493 29.1595H31.5087L29.1235 34.2006ZM38.0325 29.1467H34.2291V37.8106H35.7505V34.5745H38.0325C39.8375 34.5745 40.8689 33.3239 40.8689 31.867C40.8689 30.3973 39.8633 29.1467 38.0325 29.1467ZM37.8262 33.2466H35.7505V30.4875H37.8262C38.69 30.4875 39.3089 31.029 39.3089 31.867C39.3089 32.6922 38.69 33.2466 37.8262 33.2466ZM43.8858 29.1467L40.4821 37.8106H42.2098L42.8415 36.1475H46.8125L47.4442 37.8106H49.1719L45.7682 29.1467H43.8858ZM43.267 34.8195L44.827 30.6938L46.3871 34.8195H43.267ZM51.6344 33.6076C51.3379 36.1604 50.848 36.6245 49.9197 36.6245V37.9783C51.5957 37.9783 52.7174 37.3981 53.1429 33.7236L53.5039 30.5004H56.5079V37.8235H58.0293V29.1595H52.1502L51.6344 33.6076ZM63.6119 32.3827H61.3298V29.1467H59.8085V37.8106H63.6119C65.4297 37.8106 66.4483 36.56 66.4483 35.0902C66.4354 33.6334 65.4169 32.3827 63.6119 32.3827ZM63.4056 36.4698H61.3298V33.7236H63.4056C64.2565 33.7236 64.8883 34.2651 64.8883 35.1031C64.8754 35.9283 64.2565 36.4698 63.4056 36.4698ZM73.6038 32.6922H69.1042V29.1467H67.5829V37.8106H69.1042V34.033H73.6038V37.8106H75.1251V29.1467H73.6038V32.6922ZM84.3306 37.8106H85.852V29.1467H84.3306V37.8106ZM80.6949 32.3827H78.4128V29.1467H76.8915V37.8106H80.6949C82.5127 37.8106 83.5313 36.56 83.5313 35.0902C83.5313 33.6334 82.4998 32.3827 80.6949 32.3827ZM80.4886 36.4698H78.4128V33.7236H80.4886C81.3524 33.7236 81.9713 34.2651 81.9713 35.1031C81.9713 35.9283 81.3524 36.4698 80.4886 36.4698ZM87.6312 37.8106H93.5619V36.4698H89.1525V34.0717H93.4716V32.7309H89.1525V30.4875H93.5619V29.1467H87.6312V37.8106ZM105.217 32.6922H100.705V29.1467H99.1832V37.8106H100.705V34.033H105.217V37.8106H106.738V29.1467H105.217V32.6922ZM111.135 29.1467L107.731 37.8106H109.459L110.091 36.1475H114.062L114.693 37.8106H116.421L113.017 29.1467H111.135ZM110.516 34.8195L112.076 30.6938L113.636 34.8195H110.516ZM117.427 37.8106H118.948V30.4875H123.46V37.8106H124.982V29.1467H117.439V37.8106H117.427ZM128.257 35.1676V29.1595H126.735V37.8235H128.205L132.717 31.635V37.8235H134.239V29.1595H132.679L128.257 35.1676ZM135.386 30.4875H138.016V37.8106H139.538V30.4875H142.168V29.1467H135.399V30.4875H135.386ZM150.084 29.1467H148.202L144.811 33.2723V29.1467H143.29V37.8106H144.811V35.0516L145.559 34.162L148.472 37.8106H150.342L146.564 33.2466L150.084 29.1467ZM157.317 29.1467L152.882 35.1547V29.1467H151.36V37.8106H152.83L157.343 31.6221V37.8106H158.864V29.1467H157.317Z" fill="#D50032"/>
</svg>"""

    with open(os.path.join(img_dir, 'ochakovo_logo.svg'), 'w', encoding='utf-8') as f:
        f.write(ochakovo_logo)

    # White version for dark backgrounds
    ochakovo_logo_white = ochakovo_logo.replace('fill="#D50032"', 'fill="#FFFFFF"')
    with open(os.path.join(img_dir, 'ochakovo_logo_white.svg'), 'w', encoding='utf-8') as f:
        f.write(ochakovo_logo_white)

    print('Generated official Ochakovo logos and emblem successfully')

if __name__ == '__main__':
    create_svg_assets()
