import os
from PIL import Image, ImageDraw, ImageFont

def generate_pwa_icons():
    img_dir = os.path.join('static', 'img')
    os.makedirs(img_dir, exist_ok=True)
    
    sizes = [
        (192, 'icon-192.png'),
        (512, 'icon-512.png'),
        (180, 'apple-touch-icon.png'),
        (64, 'favicon.png'),
        (32, 'favicon-32x32.png')
    ]
    
    for size, fname in sizes:
        # Create image with brand gradient background (Ochakovo Crimson to Deep Wine)
        im = Image.new('RGBA', (size, size), (213, 0, 50, 255))
        draw = ImageDraw.Draw(im)
        
        # Rounded corner mask or circular border
        pad = int(size * 0.05)
        r = size // 2
        # Concentric golden ring
        gold_color = (253, 230, 138, 240)
        draw.ellipse([pad, pad, size - pad, size - pad], outline=gold_color, width=max(2, size // 64))
        
        # Central letter 'О' with wheat ear / malt element
        center = size // 2
        inner_r = int(size * 0.28)
        draw.ellipse([center - inner_r, center - inner_r, center + inner_r, center + inner_r], fill=(255, 255, 255, 255))
        hole_r = int(size * 0.17)
        draw.ellipse([center - hole_r, center - hole_r, center + hole_r, center + hole_r], fill=(213, 0, 50, 255))
        
        # Star or malt accent in the center
        star_r = int(size * 0.06)
        draw.ellipse([center - star_r, center - star_r, center + star_r, center + star_r], fill=gold_color)
        
        # Bottom small ribbon
        if size >= 180:
            font_size = int(size * 0.09)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()
            text = "ОЧАКОВО"
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((center - tw // 2, int(size * 0.82)), text, fill=(255, 255, 255, 255), font=font)
            
        out_path = os.path.join(img_dir, fname)
        im.save(out_path, format='PNG')
        print(f'Saved {fname} ({size}x{size})')

if __name__ == '__main__':
    generate_pwa_icons()
