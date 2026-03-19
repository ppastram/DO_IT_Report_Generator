#!/usr/bin/env python3
"""
DO IT Report Generator
Genera: (1) Infografía PNG para email, (2) Reporte web HTML interactivo
"""

import csv
import json
import math
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Colores ──────────────────────────────────────────────────
TEAL_DARK   = (0, 106, 145)
TEAL_MID    = (0, 134, 172)
TEAL_LIGHT  = (81, 195, 202)
GOLD        = (249, 180, 1)
GREY        = (166, 166, 166)
BG_DARK     = (13, 43, 56)
BG_LIGHT    = (237, 246, 249)
WHITE       = (255, 255, 255)
TEXT_DARK   = (26, 58, 74)
DIVIDER_BG  = (232, 241, 244)


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


class DOITReportGenerator:
    """Generador de reportes DO IT."""

    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir or os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = self.base_dir / "assets"
        self.entrada_dir = self.base_dir / "entrada"
        self.fotos_dir = self.base_dir / "fotos_curso"
        self.gerente_dir = self.base_dir / "gerente"
        self.salida_dir = self.base_dir / "salida"
        self.salida_dir.mkdir(exist_ok=True)

        # Scale factor for crisp rendering (3x for high quality output)
        self.S = 3
        self.W = 600 * self.S  # 1800px real

        # Load fonts
        self._load_fonts()

        # Load config
        config_path = self.base_dir / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "gerente_nombre": "Gerente",
                "gerente_email": "email@doit.com.mx",
                "gerente_telefono": "000 0000000",
                "gerente_web": "www.doit.com.mx"
            }

    def _load_fonts(self):
        """Load Poppins and Roboto fonts."""
        S = self.S
        def load(name, size):
            path = self.assets_dir / name
            if path.exists():
                return ImageFont.truetype(str(path), size * S)
            # Fallback
            try:
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size * S)
            except:
                return ImageFont.load_default()

        self.font = {
            'title_lg':  load("Poppins-Bold.ttf", 30),
            'title_md':  load("Poppins-Bold.ttf", 20),
            'title_sm':  load("Poppins-Bold.ttf", 15),
            'heading':   load("Poppins-Bold.ttf", 13),
            'label_lg':  load("Poppins-Bold.ttf", 18),
            'label_md':  load("Poppins-Bold.ttf", 14),
            'label_sm':  load("Poppins-Medium.ttf", 11),
            'body':      load("Roboto-Regular.ttf", 13),
            'body_sm':   load("Roboto-Regular.ttf", 11),
            'body_xs':   load("Roboto-Regular.ttf", 9),
            'caption':   load("Roboto-Regular.ttf", 8),
            'pct_lg':    load("Poppins-Bold.ttf", 22),
            'pct_sm':    load("Poppins-Bold.ttf", 16),
            'badge':     load("Poppins-Bold.ttf", 10),
            'upper_xs':  load("Roboto-Bold.ttf", 9),
        }

    # ── CSV Parsing ──────────────────────────────────────────

    def parse_csv(self, csv_path):
        """Parse Fillout CSV and compute metrics."""
        rows = []
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if len(row) >= 19:
                    rows.append(row)

        if not rows:
            raise ValueError("CSV vacío o formato incorrecto")

        data = {
            'empresa': rows[0][3].strip(),
            'codigo': rows[0][5].strip(),
            'instructor': rows[0][7].strip(),
            'fecha_raw': rows[0][0].strip(),
            'participantes': [],
            'q2_valores': [],     # Valor inversión
            'q3_valores': [],     # Satisfacción
            'q4_resenas': [],     # Reseñas
            'q5_valores': [],     # Instructor
            'q6_comentarios': [], # Comentarios instructor
            'q7_expectativas': [],
            'q8_comparacion': [],
        }

        for r in rows:
            nombre = f"{r[16].strip()} {r[17].strip()}"
            email = r[18].strip() if len(r) > 18 else ""
            data['participantes'].append({'nombre': nombre, 'email': email})

            try: data['q2_valores'].append(float(r[9]))
            except: pass
            try: data['q3_valores'].append(float(r[10]))
            except: pass
            if r[11].strip():
                data['q4_resenas'].append({
                    'texto': r[11].strip(),
                    'nombre': nombre
                })
            try: data['q5_valores'].append(float(r[12]))
            except: pass
            if r[13].strip():
                data['q6_comentarios'].append({
                    'texto': r[13].strip(),
                    'nombre': nombre
                })
            data['q7_expectativas'].append(r[14].strip())
            data['q8_comparacion'].append(r[15].strip())

        # Parse date
        try:
            parts = data['fecha_raw'].split(' ')[0].split('/')
            data['fecha'] = f"{parts[0]} {'Ene Feb Mar Abr May Jun Jul Ago Sep Oct Nov Dic'.split()[int(parts[1])-1]} {parts[2]}"
            data['fecha_iso'] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        except:
            data['fecha'] = data['fecha_raw']
            data['fecha_iso'] = ''

        # Compute metrics
        n = len(data['participantes'])
        data['n_participantes'] = n
        data['prom_satisfaccion'] = sum(data['q3_valores']) / len(data['q3_valores']) if data['q3_valores'] else 0
        data['prom_inversion'] = sum(data['q2_valores']) / len(data['q2_valores']) if data['q2_valores'] else 0
        data['prom_instructor'] = sum(data['q5_valores']) / len(data['q5_valores']) if data['q5_valores'] else 0

        # Expectativas
        supero = sum(1 for x in data['q7_expectativas'] if 'Mejor' in x)
        cumplio = sum(1 for x in data['q7_expectativas'] if 'Como' in x or 'esperaba' in x.lower() and 'Mejor' not in x)
        debajo = n - supero - cumplio
        data['expect_supero'] = round(supero / n * 100) if n else 0
        data['expect_cumplio'] = round(cumplio / n * 100) if n else 0
        data['expect_debajo'] = round(debajo / n * 100) if n else 0

        # Comparación
        superior = sum(1 for x in data['q8_comparacion'] if 'Superior' in x or 'Muy superior' in x)
        igual = sum(1 for x in data['q8_comparacion'] if x.strip() == 'Igual')
        inferior = n - superior - igual
        data['comp_superior'] = round(superior / n * 100) if n else 0
        data['comp_igual'] = round(igual / n * 100) if n else 0
        data['comp_inferior'] = round(inferior / n * 100) if n else 0

        return data

    # ── Image Helpers ────────────────────────────────────────

    def _remove_black_bg(self, img, threshold=35):
        """Remove black background from logo."""
        img = img.convert("RGBA")
        pixels = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if r < threshold and g < threshold and b < threshold:
                    pixels[x, y] = (r, g, b, 0)
        return img

    def _draw_rounded_rect(self, draw, xy, radius, fill=None, outline=None, width=1):
        """Draw a rounded rectangle."""
        x1, y1, x2, y2 = xy
        r = radius
        if fill:
            draw.rectangle([x1+r, y1, x2-r, y2], fill=fill)
            draw.rectangle([x1, y1+r, x2, y2-r], fill=fill)
            draw.pieslice([x1, y1, x1+2*r, y1+2*r], 180, 270, fill=fill)
            draw.pieslice([x2-2*r, y1, x2, y1+2*r], 270, 360, fill=fill)
            draw.pieslice([x1, y2-2*r, x1+2*r, y2], 90, 180, fill=fill)
            draw.pieslice([x2-2*r, y2-2*r, x2, y2], 0, 90, fill=fill)
        if outline:
            # Top
            draw.line([x1+r, y1, x2-r, y1], fill=outline, width=width)
            # Bottom
            draw.line([x1+r, y2, x2-r, y2], fill=outline, width=width)
            # Left
            draw.line([x1, y1+r, x1, y2-r], fill=outline, width=width)
            # Right
            draw.line([x2, y1+r, x2, y2-r], fill=outline, width=width)
            draw.arc([x1, y1, x1+2*r, y1+2*r], 180, 270, fill=outline, width=width)
            draw.arc([x2-2*r, y1, x2, y1+2*r], 270, 360, fill=outline, width=width)
            draw.arc([x1, y2-2*r, x1+2*r, y2], 90, 180, fill=outline, width=width)
            draw.arc([x2-2*r, y2-2*r, x2, y2], 0, 90, fill=outline, width=width)

    def _draw_donut(self, img, center, outer_r, thickness, pct, color, bg_color=DIVIDER_BG):
        """Draw a donut arc chart."""
        draw = ImageDraw.Draw(img)
        cx, cy = center
        # Background circle
        bbox_outer = [cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r]
        inner_r = outer_r - thickness

        # Draw background arc (full circle)
        draw.arc(bbox_outer, 0, 360, fill=bg_color, width=thickness)

        # Draw filled arc (from top, counterclockwise = from 270 going negative)
        # Pillow arcs go clockwise from 3 o'clock
        # We want to start from 12 o'clock (270°) and go clockwise
        start_angle = -90
        sweep = pct / 100 * 360
        end_angle = start_angle + sweep
        draw.arc(bbox_outer, start_angle, end_angle, fill=color, width=thickness)

    def _draw_gradient_rect(self, img, xy, color_top, color_bottom):
        """Draw a vertical gradient rectangle."""
        x1, y1, x2, y2 = xy
        h = y2 - y1
        draw = ImageDraw.Draw(img)
        for i in range(h):
            ratio = i / max(h - 1, 1)
            r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
            g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
            b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
            draw.line([x1, y1+i, x2, y1+i], fill=(r, g, b))

    def _text_size(self, draw, text, font):
        """Get text bounding box size."""
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _draw_icon_placeholder(self, draw, x, y, size, icon_type, color=TEAL_MID):
        """Draw a simple icon placeholder."""
        S = self.S
        # Draw rounded rect background
        self._draw_rounded_rect(draw, [x, y, x+size, y+size], size//6, fill=BG_LIGHT)
        # Simple icon symbols
        cx, cy = x + size//2, y + size//2
        r = size // 4
        if icon_type == 'company':
            draw.rectangle([cx-r, cy-r, cx+r, cy+r], outline=color, width=S)
            draw.line([cx-r, cy, cx+r, cy], fill=color, width=S)
        elif icon_type == 'location':
            draw.ellipse([cx-r//2, cy-r, cx+r//2, cy], fill=color)
            draw.polygon([(cx, cy+r), (cx-r//2, cy), (cx+r//2, cy)], fill=color)
        elif icon_type == 'person':
            draw.ellipse([cx-r//3, cy-r, cx+r//3, cy-r//2], fill=color)
            draw.arc([cx-r, cy-r//4, cx+r, cy+r], 180, 360, fill=color, width=S*2)
        elif icon_type == 'calendar':
            draw.rectangle([cx-r, cy-r//2, cx+r, cy+r], outline=color, width=S)
            draw.line([cx-r, cy-r//4+S, cx+r, cy-r//4+S], fill=color, width=S)
        elif icon_type == 'clock':
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=color, width=S)
            draw.line([cx, cy, cx, cy-r+S*2], fill=color, width=S)
            draw.line([cx, cy, cx+r//2, cy], fill=color, width=S)
        elif icon_type == 'people':
            draw.ellipse([cx-r//2, cy-r, cx, cy-r//2], fill=color)
            draw.ellipse([cx, cy-r, cx+r//2, cy-r//2], fill=color)
            draw.arc([cx-r, cy-r//3, cx+r, cy+r], 180, 360, fill=color, width=S*2)

    def _wrap_text(self, draw, text, font, max_width):
        """Word-wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test = f"{current_line} {word}".strip()
            tw, _ = self._text_size(draw, test, font)
            if tw <= max_width:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    # ── PNG Infographic Generator ────────────────────────────

    def generate_png(self, data, nombre_taller, duracion, lugar, logo_cliente_path=None, qr_path=None, progress_callback=None, instructor2=None, total_participantes=None):
        """Generate the PNG infographic."""
        S = self.S
        W = self.W
        PAD = 36 * S  # lateral padding

        # Initial canvas height (will be cropped to actual content)
        H = 920 * S

        img = Image.new('RGBA', (W, H), WHITE)
        draw = ImageDraw.Draw(img)

        y = 0

        # ═══ HEADER (logos on light bg) ═══
        header_h = 70 * S
        draw.rectangle([0, y, W, y + header_h], fill=BG_LIGHT)

        # DO IT logo
        try:
            logo_doit = Image.open(self.assets_dir / "logo_doit_dark.png").convert("RGBA")
            logo_doit = self._remove_black_bg(logo_doit)
            lh = 48 * S
            lr = lh / logo_doit.height
            lw = int(logo_doit.width * lr)
            logo_doit = logo_doit.resize((lw, lh), Image.LANCZOS)
            img.paste(logo_doit, (PAD, y + (header_h - lh) // 2), logo_doit)
        except Exception as e:
            draw.text((PAD, y + 20*S), "DO IT", fill=TEAL_MID, font=self.font['title_md'])

        # Client logo
        if logo_cliente_path and os.path.exists(logo_cliente_path):
            try:
                logo_client = Image.open(logo_cliente_path).convert("RGBA")
                logo_client = self._remove_black_bg(logo_client)
                lh = 32 * S
                lr = lh / logo_client.height
                lw = int(logo_client.width * lr)
                logo_client = logo_client.resize((lw, lh), Image.LANCZOS)
                img.paste(logo_client, (W - PAD - lw, y + (header_h - lh) // 2), logo_client)
            except:
                draw.text((W - PAD - 100*S, y + 25*S), data['empresa'],
                         fill=TEAL_DARK, font=self.font['label_md'])
        else:
            tw, th = self._text_size(draw, data['empresa'], self.font['label_md'])
            draw.text((W - PAD - tw, y + (header_h - th) // 2), data['empresa'],
                     fill=TEAL_DARK, font=self.font['label_md'])

        y += header_h
        if progress_callback: progress_callback(15)

        # ═══ TITLE BAND (gradient) ═══
        # Calculate title layout first to determine band height
        max_title_w = W - 2 * PAD
        full_title = f'Resultados "{nombre_taller}"'
        tw_full, _ = self._text_size(draw, full_title, self.font['title_lg'])

        if tw_full <= max_title_w:
            # Single line — default band height
            band_h = 72 * S
            title_mode = 'single'
        else:
            # Two lines needed — try auto-sizing the taller name
            taller_text = f'"{nombre_taller}"'
            title_font_2 = None
            for fkey in ['title_lg', 'title_md', 'title_sm']:
                tw_t, _ = self._text_size(draw, taller_text, self.font[fkey])
                if tw_t <= max_title_w:
                    title_font_2 = self.font[fkey]
                    break
            if title_font_2 is None:
                title_font_2 = self.font['title_sm']
            title_mode = 'double'
            band_h = 110 * S

        self._draw_gradient_rect(img, [0, y, W, y + band_h], TEAL_DARK, TEAL_MID)

        # Label
        draw.text((PAD, y + 10*S), "RESULTADOS DEL TALLER", fill=TEAL_LIGHT, font=self.font['badge'])

        # Title
        if title_mode == 'single':
            draw.text((PAD, y + 26*S), 'Resultados ', fill=WHITE, font=self.font['title_lg'])
            tw_r, _ = self._text_size(draw, 'Resultados ', self.font['title_lg'])
            draw.text((PAD + tw_r, y + 26*S), f'"{nombre_taller}"', fill=GOLD, font=self.font['title_lg'])
        else:
            draw.text((PAD, y + 26*S), 'Resultados', fill=WHITE, font=self.font['title_lg'])
            _, th_r = self._text_size(draw, 'Resultados', self.font['title_lg'])
            taller_y = y + 26*S + th_r + 4*S
            # Wrap the taller name if it still overflows
            tw_t, _ = self._text_size(draw, taller_text, title_font_2)
            if tw_t > max_title_w:
                lines = self._wrap_text(draw, taller_text, title_font_2, max_title_w)
                for li, line in enumerate(lines[:2]):
                    draw.text((PAD, taller_y + li * 22*S), line, fill=GOLD, font=title_font_2)
            else:
                draw.text((PAD, taller_y), taller_text, fill=GOLD, font=title_font_2)

        y += band_h
        if progress_callback: progress_callback(25)

        # ═══ FICHA TÉCNICA ═══
        # Determinar label y valor de participantes/evaluaciones
        n_evaluaciones = data['n_participantes']
        if total_participantes and total_participantes != n_evaluaciones:
            part_label = 'EVALUACIONES / PARTICIPANTES'
            part_value = f"{n_evaluaciones} / {total_participantes}"
        else:
            part_label = 'PARTICIPANTES'
            part_value = str(n_evaluaciones)

        instructor_label = 'INSTRUCTORES' if instructor2 else 'INSTRUCTOR/A'
        instructor_value = f"{data['instructor']} y {instructor2}" if instructor2 else data['instructor']

        ficha_items = [
            ('company', 'CLIENTE', data['empresa']),
            ('location', 'LUGAR', lugar),
            ('person', instructor_label, instructor_value),
        ]
        ficha_items += [
            ('calendar', 'FECHA', data['fecha']),
            ('clock', 'DURACIÓN', duracion),
            ('people', part_label, part_value),
        ]

        ficha_pad_y = 18 * S
        y += ficha_pad_y
        icon_size = 28 * S
        col_w = (W - 2 * PAD) // 2
        row_h = 36 * S

        for i, (icon, label, value) in enumerate(ficha_items):
            col = i % 2
            row = i // 2
            fx = PAD + col * col_w
            fy = y + row * row_h

            self._draw_icon_placeholder(draw, fx, fy, icon_size, icon)
            draw.text((fx + icon_size + 8*S, fy), label,
                     fill=GREY, font=self.font['caption'])
            draw.text((fx + icon_size + 8*S, fy + 11*S), value,
                     fill=TEXT_DARK, font=self.font['label_sm'])

        n_rows = (len(ficha_items) + 1) // 2  # ceiling division for 2-column grid
        y += n_rows * row_h + ficha_pad_y
        if progress_callback: progress_callback(35)

        # ═══ GOLD DIVIDER ═══
        div_h = 3 * S
        for x_pos in range(PAD, PAD + (W - 2*PAD) * 40 // 100):
            ratio = (x_pos - PAD) / ((W - 2*PAD) * 40 // 100)
            alpha = int(255 * (1 - ratio * 0.5))
            draw.line([x_pos, y, x_pos, y + div_h], fill=(*GOLD, alpha))
        y += div_h + 6 * S

        # ═══ SECTION TITLE: Indicadores clave ═══
        # Gold bar accent
        draw.rectangle([PAD, y + 2*S, PAD + 4*S, y + 18*S], fill=GOLD)
        draw.text((PAD + 12*S, y), "Indicadores clave", fill=TEXT_DARK, font=self.font['title_sm'])
        y += 30 * S
        if progress_callback: progress_callback(45)

        # ═══ INDICATOR 1: Expectativas (donut + text) ═══
        donut_size = 72 * S
        donut_cx = PAD + donut_size // 2
        donut_cy = y + donut_size // 2
        thickness = 8 * S

        self._draw_donut(img, (donut_cx, donut_cy), donut_size // 2, thickness,
                        data['expect_supero'], TEAL_LIGHT)

        # Value in center
        pct_text = f"{data['expect_supero']}%"
        tw, th = self._text_size(draw, pct_text, self.font['pct_sm'])
        draw.text((donut_cx - tw//2, donut_cy - th//2), pct_text,
                 fill=TEAL_DARK, font=self.font['pct_sm'])

        # Description text
        text_x = PAD + donut_size + 16 * S
        text_max_w = W - text_x - PAD
        desc1 = f"Para el {data['expect_supero']}% de los participantes, el taller superó las expectativas; para el {data['expect_cumplio']}% las cumplió."
        lines = self._wrap_text(draw, desc1, self.font['body'], text_max_w)
        for i, line in enumerate(lines):
            draw.text((text_x, y + 8*S + i * 18*S), line, fill=TEXT_DARK, font=self.font['body'])

        y += donut_size + 14 * S

        # Separator line
        draw.line([PAD, y, W - PAD, y], fill=DIVIDER_BG, width=S)
        y += 14 * S

        # ═══ INDICATOR 2: Satisfacción (bar + text) ═══
        bar_w = 72 * S
        bar_h = 14 * S
        bar_x = PAD
        bar_y = y + 4 * S

        # Track
        self._draw_rounded_rect(draw, [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                               bar_h // 2, fill=DIVIDER_BG)
        # Fill
        fill_w = int(bar_w * data['prom_satisfaccion'] / 10)
        if fill_w > bar_h:
            self._draw_rounded_rect(draw, [bar_x, bar_y, bar_x + fill_w, bar_y + bar_h],
                                   bar_h // 2, fill=GOLD)

        # Value below bar
        sat_pct = f"{int(data['prom_satisfaccion'] * 10)}%"
        tw, th = self._text_size(draw, sat_pct, self.font['pct_sm'])
        draw.text((bar_x + (bar_w - tw) // 2, bar_y + bar_h + 6*S), sat_pct,
                 fill=TEXT_DARK, font=self.font['pct_sm'])

        # Description
        text_x = PAD + bar_w + 16 * S
        sat_val = f"{data['prom_satisfaccion']:.1f}".rstrip('0').rstrip('.')
        desc2 = f"El nivel de satisfacción fue {sat_val}/10"
        lines = self._wrap_text(draw, desc2, self.font['body'], text_max_w)
        for i, line in enumerate(lines):
            draw.text((text_x, y + 4*S + i * 18*S), line, fill=TEXT_DARK, font=self.font['body'])

        y += 50 * S

        # Separator
        draw.line([PAD, y, W - PAD, y], fill=DIVIDER_BG, width=S)
        y += 14 * S
        if progress_callback: progress_callback(60)

        # ═══ INDICATOR 3: Comparación (donut + text) ═══
        donut_cx = PAD + donut_size // 2
        donut_cy = y + donut_size // 2

        self._draw_donut(img, (donut_cx, donut_cy), donut_size // 2, thickness,
                        data['comp_superior'], TEAL_DARK)

        pct_text = f"{data['comp_superior']}%"
        tw, th = self._text_size(draw, pct_text, self.font['pct_sm'])
        draw.text((donut_cx - tw//2, donut_cy - th//2), pct_text,
                 fill=TEAL_DARK, font=self.font['pct_sm'])

        desc3 = f"El {data['comp_superior']}% calificó el taller como superior, frente a otros cursos que han tomado."
        lines = self._wrap_text(draw, desc3, self.font['body'], text_max_w)
        for i, line in enumerate(lines):
            draw.text((text_x, y + 8*S + i * 18*S), line, fill=TEXT_DARK, font=self.font['body'])

        y += donut_size + 20 * S
        if progress_callback: progress_callback(70)

        # ═══ CTA BOX ═══
        cta_h = 80 * S
        cta_r = 14 * S

        # Background
        self._draw_rounded_rect(draw, [PAD, y, W - PAD, y + cta_h], cta_r, fill=BG_LIGHT)
        # Border
        self._draw_rounded_rect(draw, [PAD, y, W - PAD, y + cta_h], cta_r,
                               outline=TEAL_LIGHT, width=2*S)

        # Headline
        headline = "Haz clic en la imagen"
        tw, _ = self._text_size(draw, headline, self.font['heading'])
        draw.text(((W - tw)//2, y + 18*S), headline, fill=TEAL_DARK, font=self.font['heading'])

        # Subtitle
        subtitle = "para conocer todos los resultados del taller"
        tw, _ = self._text_size(draw, subtitle, self.font['body_sm'])
        draw.text(((W - tw)//2, y + 38*S), subtitle, fill=GREY, font=self.font['body_sm'])

        # Button
        btn_text = "Ver reporte completo →"
        btw, bth = self._text_size(draw, btn_text, self.font['label_sm'])
        btn_w = btw + 50 * S
        btn_h = bth + 16 * S
        btn_x = (W - btn_w) // 2
        btn_y = y + 52 * S
        self._draw_rounded_rect(draw, [btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
                               btn_h // 2, fill=TEAL_MID)
        draw.text((btn_x + (btn_w - btw)//2, btn_y + (btn_h - bth)//2), btn_text,
                 fill=WHITE, font=self.font['label_sm'])

        y += cta_h + 20 * S
        if progress_callback: progress_callback(80)

        # ═══ FOOTER (agent + QR) ═══
        footer_h = 72 * S
        draw.rectangle([0, y, W, y + footer_h], fill=BG_DARK)

        # Agent initials circle
        initials = "".join(w[0].upper() for w in self.config['gerente_nombre'].split()[:2])
        circle_r = 22 * S
        circle_x = PAD + circle_r
        circle_y = y + footer_h // 2
        draw.ellipse([circle_x - circle_r, circle_y - circle_r,
                     circle_x + circle_r, circle_y + circle_r], fill=TEAL_DARK)
        draw.ellipse([circle_x - circle_r, circle_y - circle_r,
                     circle_x + circle_r, circle_y + circle_r], outline=TEAL_LIGHT, width=2*S)
        tw, th = self._text_size(draw, initials, self.font['label_md'])
        draw.text((circle_x - tw//2, circle_y - th//2), initials,
                 fill=WHITE, font=self.font['label_md'])

        # Agent details
        ax = PAD + circle_r * 2 + 14 * S
        draw.text((ax, y + 12*S), "TU GERENTE COMERCIAL",
                 fill=TEAL_LIGHT, font=self.font['caption'])
        draw.text((ax, y + 24*S), self.config['gerente_nombre'],
                 fill=WHITE, font=self.font['label_md'])
        contact = f"{self.config['gerente_email']}  ·  {self.config['gerente_telefono']}"
        draw.text((ax, y + 42*S), contact, fill=TEAL_LIGHT, font=self.font['body_xs'])

        # QR
        qr_size = 52 * S
        qr_x = W - PAD - qr_size
        qr_y = y + (footer_h - qr_size) // 2
        self._draw_rounded_rect(draw, [qr_x, qr_y, qr_x + qr_size, qr_y + qr_size],
                               6*S, fill=WHITE)

        if qr_path and os.path.exists(qr_path):
            try:
                qr_img = Image.open(qr_path).convert("RGBA")
                qr_inner = qr_size - 8*S
                qr_img = qr_img.resize((qr_inner, qr_inner), Image.LANCZOS)
                img.paste(qr_img, (qr_x + 4*S, qr_y + 4*S), qr_img)
            except:
                pass
        else:
            draw.text((qr_x + 12*S, qr_y + 18*S), "QR", fill=GREY, font=self.font['body_sm'])

        y += footer_h

        # Watermark bar
        wm_h = 14 * S
        draw.rectangle([0, y, W, y + wm_h], fill=BG_DARK)
        wm_text = self.config['gerente_web']
        tw, _ = self._text_size(draw, wm_text, self.font['caption'])
        draw.text(((W - tw)//2, y + 2*S), wm_text, fill=(*TEAL_LIGHT, 80), font=self.font['caption'])
        y += wm_h

        if progress_callback: progress_callback(90)

        # ═══ CROP & SAVE ═══
        img = img.crop((0, 0, W, y))
        final = img.convert('RGB')

        safe_name = data['empresa'].replace(' ', '_')
        safe_taller = nombre_taller.replace(' ', '_')[:40]
        fecha_suffix = f"_{data['fecha_iso']}" if data.get('fecha_iso') else ''
        out_path = self.salida_dir / f"Infografia_{safe_name}_{safe_taller}{fecha_suffix}.png"
        final.save(str(out_path), 'PNG', dpi=(300, 300))

        if progress_callback: progress_callback(95)
        return str(out_path)

    # ── HTML Web Report Generator ────────────────────────────

    def generate_html(self, data, nombre_taller, duracion, lugar, fotos_paths=None, progress_callback=None, instructor2=None, total_participantes=None, logo_cliente_path=None, qr_path=None):
        """Generate interactive HTML web report."""

        import base64

        # Encode DO IT logo as base64
        doit_logo_b64 = ""
        logo_path = self.assets_dir / "logo_doit_light.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                doit_logo_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

        # Encode client logo as base64
        client_logo_b64 = ""
        if logo_cliente_path and os.path.exists(logo_cliente_path):
            try:
                with open(logo_cliente_path, "rb") as f:
                    ext = Path(logo_cliente_path).suffix.lower()
                    mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'
                    client_logo_b64 = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
            except:
                pass

        # Encode QR as base64
        qr_b64 = ""
        if qr_path and os.path.exists(qr_path):
            try:
                with open(qr_path, "rb") as f:
                    ext = Path(qr_path).suffix.lower()
                    mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'
                    qr_b64 = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
            except:
                pass

        # Encode photos as base64
        photos_b64 = []
        if fotos_paths:
            for fp in fotos_paths[:4]:
                if os.path.exists(fp):
                    try:
                        with open(fp, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                            ext = Path(fp).suffix.lower()
                            mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'
                            photos_b64.append(f"data:{mime};base64,{b64}")
                    except:
                        pass

        # Build testimonials HTML
        testimonials_html = ""
        colors = ['#F9B401', '#51C3CA', '#006A91', '#0086AC', '#F9B401', '#51C3CA']
        for i, review in enumerate(data['q4_resenas'][:8]):
            color = colors[i % len(colors)]
            testimonials_html += f'''
            <div class="testimonial-card" style="border-left-color:{color}">
              <div class="tc-quote" style="color:{color}">&ldquo;</div>
              <div class="tc-text">{review['texto']}</div>
              <div class="tc-author">{review['nombre']}</div>
            </div>'''

        # Build participants HTML
        participants_html = ""
        for i, p in enumerate(data['participantes']):
            participants_html += f'''
            <div class="participant-row">
              <span class="pr-num">{i+1}</span>
              <div>
                <div class="pr-name">{p['nombre']}</div>
                <div class="pr-email">{p['email']}</div>
              </div>
            </div>'''

        # Build photo gallery HTML
        gallery_html = ""
        if photos_b64:
            for i, photo in enumerate(photos_b64):
                gallery_html += f'''
                <div class="gallery-item">
                  <img src="{photo}" alt="Foto {i+1}" style="width:100%;height:100%;object-fit:cover;">
                </div>'''

        # Instructor comments HTML
        instructor_html = ""
        for i, comment in enumerate(data['q6_comentarios'][:6]):
            color = colors[i % len(colors)]
            instructor_html += f'''
            <div class="testimonial-card" style="border-left-color:{color}">
              <div class="tc-quote" style="color:{color}">&ldquo;</div>
              <div class="tc-text">{comment['texto']}</div>
              <div class="tc-author">{comment['nombre']}</div>
            </div>'''

        sat_val = f"{data['prom_satisfaccion']:.1f}".rstrip('0').rstrip('.')
        inv_val = f"{data['prom_inversion']:.1f}".rstrip('0').rstrip('.')
        inst_val = f"{data['prom_instructor']:.1f}".rstrip('0').rstrip('.')
        sat_pct = int(data['prom_satisfaccion'] * 10)
        inv_pct = int(data['prom_inversion'] * 10)
        inst_pct = int(data['prom_instructor'] * 10)

        html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{nombre_taller} — Resultados | {data['empresa']} × DO IT</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800;900&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--teal-dark:#006A91;--teal-mid:#0086AC;--teal-light:#51C3CA;--gold:#F9B401;--grey:#A6A6A6;--bg-dark:#0D2B38;--bg-light:#EDF6F9;--white:#FFF;--text:#1A3A4A}}
html{{scroll-behavior:smooth}}
body{{font-family:'Roboto',sans-serif;color:var(--text);background:#F7FBFC;overflow-x:hidden}}

/* Hero */
.hero{{min-height:100vh;background:linear-gradient(160deg,var(--bg-dark) 0%,#0A3D52 50%,var(--teal-dark) 100%);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:60px 24px;position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;width:500px;height:500px;background:radial-gradient(circle,var(--teal-light) 0%,transparent 70%);opacity:.08;top:-100px;right:-100px;border-radius:50%}}
.hero .logos{{display:flex;align-items:center;gap:24px;margin-bottom:40px;opacity:0;animation:fadeUp .8s ease forwards .2s}}
.hero .logo-text{{font-family:'Poppins',sans-serif;font-weight:800;font-size:28px;color:var(--teal-light)}}
.hero .logo-text small{{display:block;font-size:10px;font-weight:400;color:var(--teal-light);letter-spacing:3px;opacity:.7}}
.hero .divider-x{{font-family:'Poppins',sans-serif;font-size:16px;color:var(--gold);font-weight:300}}
.hero .client-text{{font-family:'Poppins',sans-serif;font-weight:700;font-size:22px;color:var(--white);letter-spacing:3px}}
.hero .badge{{display:inline-block;background:var(--gold);color:var(--bg-dark);font-family:'Poppins',sans-serif;font-weight:700;font-size:11px;padding:6px 18px;border-radius:20px;letter-spacing:2px;text-transform:uppercase;margin-bottom:20px;opacity:0;animation:fadeUp .8s ease forwards .4s}}
.hero h1{{font-family:'Poppins',sans-serif;font-weight:900;font-size:clamp(42px,7vw,72px);color:var(--white);line-height:1.05;margin-bottom:16px;opacity:0;animation:fadeUp .8s ease forwards .6s}}
.hero h1 span{{color:var(--gold);display:block}}
.hero .hero-sub{{font-family:'Roboto',sans-serif;font-size:16px;color:var(--teal-light);font-weight:300;max-width:500px;opacity:0;animation:fadeUp .8s ease forwards .8s}}
.hero .scroll-hint{{position:absolute;bottom:30px;left:50%;transform:translateX(-50%);color:var(--teal-light);opacity:.5;animation:bounce 2s infinite;font-size:24px}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(30px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes bounce{{0%,100%{{transform:translateX(-50%) translateY(0)}}50%{{transform:translateX(-50%) translateY(10px)}}}}

/* Sections */
section{{padding:80px 24px;max-width:960px;margin:0 auto}}
.section-label{{font-family:'Poppins',sans-serif;font-size:11px;font-weight:700;color:var(--teal-mid);letter-spacing:3px;text-transform:uppercase;margin-bottom:8px}}
.section-heading{{font-family:'Poppins',sans-serif;font-weight:800;font-size:32px;color:var(--bg-dark);line-height:1.2;margin-bottom:40px}}
.section-heading span{{color:var(--gold)}}

/* Ficha */
.ficha-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:40px}}
.ficha-card{{background:var(--white);border-radius:16px;padding:24px;box-shadow:0 4px 20px rgba(0,106,145,.06);border-left:4px solid var(--teal-light);transition:transform .3s,box-shadow .3s}}
.ficha-card:hover{{transform:translateY(-4px);box-shadow:0 8px 30px rgba(0,106,145,.12)}}
.ficha-card .fc-label{{font-size:10px;color:var(--grey);text-transform:uppercase;letter-spacing:1.5px;font-weight:500;margin-bottom:4px}}
.ficha-card .fc-value{{font-family:'Poppins',sans-serif;font-weight:700;font-size:18px;color:var(--bg-dark)}}

/* Metrics */
.metrics-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:40px}}
.metric-card{{background:var(--white);border-radius:20px;padding:32px 24px;text-align:center;box-shadow:0 4px 24px rgba(0,106,145,.06);position:relative;overflow:hidden;transition:transform .3s}}
.metric-card:hover{{transform:translateY(-6px)}}
.metric-card::before{{content:'';position:absolute;bottom:0;left:0;right:0;height:5px}}
.metric-card:nth-child(1)::before{{background:linear-gradient(90deg,var(--teal-light),var(--teal-mid))}}
.metric-card:nth-child(2)::before{{background:linear-gradient(90deg,var(--gold),#FDCB4A)}}
.metric-card:nth-child(3)::before{{background:linear-gradient(90deg,var(--teal-dark),var(--teal-mid))}}
.metric-ring{{width:130px;height:130px;margin:0 auto 16px;position:relative}}
.metric-ring svg{{width:130px;height:130px;transform:rotate(-90deg)}}
.metric-ring .ring-bg{{fill:none;stroke:#E8F4F8;stroke-width:8}}
.metric-ring .ring-fill{{fill:none;stroke-width:8;stroke-linecap:round;stroke-dasharray:0 377;transition:stroke-dasharray 1.5s cubic-bezier(.4,0,.2,1)}}
.metric-ring .ring-value{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-family:'Poppins',sans-serif;font-weight:900;font-size:32px;color:var(--bg-dark)}}
.metric-ring .ring-value small{{font-size:14px;font-weight:500;color:var(--grey)}}
.metric-label{{font-family:'Poppins',sans-serif;font-weight:600;font-size:14px;color:var(--bg-dark)}}

/* Bars */
.highlight-row{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:40px}}
.highlight-card{{background:var(--white);border-radius:20px;padding:32px;box-shadow:0 4px 24px rgba(0,106,145,.06)}}
.highlight-card h3{{font-family:'Poppins',sans-serif;font-weight:700;font-size:16px;color:var(--bg-dark);margin-bottom:20px;display:flex;align-items:center;gap:8px}}
.highlight-card h3 .dot{{width:8px;height:8px;border-radius:50%}}
.bar-item{{margin-bottom:14px}}
.bar-item .bar-header{{display:flex;justify-content:space-between;margin-bottom:6px}}
.bar-item .bar-label{{font-family:'Poppins',sans-serif;font-size:13px;font-weight:600}}
.bar-item .bar-pct{{font-family:'Poppins',sans-serif;font-size:13px;font-weight:700}}
.bar-track{{width:100%;height:12px;background:#E8F4F8;border-radius:6px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:6px;transition:width 1.2s cubic-bezier(.4,0,.2,1);width:0%}}

/* Testimonials */
.testimonials-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.testimonial-card{{background:var(--white);border-radius:16px;padding:24px;box-shadow:0 4px 20px rgba(0,106,145,.06);border-left:4px solid;transition:transform .3s}}
.testimonial-card:hover{{transform:translateY(-3px)}}
.tc-quote{{font-family:'Poppins',sans-serif;font-size:28px;font-weight:800;line-height:1;margin-bottom:8px;opacity:.15}}
.tc-text{{font-size:14px;line-height:1.6;font-style:italic;margin-bottom:12px}}
.tc-author{{font-family:'Poppins',sans-serif;font-size:12px;font-weight:600;color:var(--teal-dark)}}

/* Gallery */
.gallery{{display:grid;grid-template-columns:2fr 1fr;grid-template-rows:220px 220px;gap:12px}}
.gallery-item{{border-radius:16px;overflow:hidden;transition:transform .3s}}
.gallery-item:hover{{transform:scale(1.02)}}
.gallery-item:first-child{{grid-row:1/3}}
.gallery-item img{{width:100%;height:100%;object-fit:cover}}

/* Participants */
.participants-list{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.participant-row{{display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:10px;background:var(--white);transition:background .2s}}
.participant-row:hover{{background:var(--bg-light)}}
.participant-row .pr-num{{width:28px;height:28px;background:var(--bg-light);border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Poppins',sans-serif;font-size:11px;font-weight:700;color:var(--teal-dark);flex-shrink:0}}
.participant-row .pr-name{{font-family:'Poppins',sans-serif;font-size:13px;font-weight:600;color:var(--bg-dark)}}
.participant-row .pr-email{{font-size:11px;color:var(--grey)}}

/* Footer */
.cta-footer{{background:var(--bg-dark);padding:60px 24px;text-align:center;position:relative;overflow:hidden}}
.cta-footer h2{{font-family:'Poppins',sans-serif;font-weight:800;font-size:28px;color:var(--white);margin-bottom:4px}}
.cta-footer h2 span{{color:var(--gold)}}
.cta-footer p{{color:var(--teal-light);font-size:14px;margin-bottom:30px;max-width:400px;margin-left:auto;margin-right:auto}}
.agent-card-footer{{display:inline-flex;align-items:center;gap:20px;background:rgba(81,195,202,.08);border:1px solid rgba(81,195,202,.2);border-radius:16px;padding:20px 32px}}
.agent-card-footer .acf-photo{{width:56px;height:56px;border-radius:50%;background:var(--teal-dark);border:2px solid var(--teal-light);display:flex;align-items:center;justify-content:center;color:white;font-family:'Poppins',sans-serif;font-weight:700;font-size:18px}}
.agent-card-footer .acf-details{{text-align:left}}
.agent-card-footer .acf-name{{font-family:'Poppins',sans-serif;font-weight:700;font-size:16px;color:var(--white)}}
.agent-card-footer .acf-role{{font-size:11px;color:var(--teal-light)}}
.agent-card-footer .acf-contact{{font-size:12px;color:var(--grey);margin-top:4px}}
.agent-card-footer .acf-qr{{width:72px;height:72px;border-radius:10px;object-fit:contain;background:var(--white);padding:4px}}
.powered-by{{text-align:center;padding:16px;background:var(--bg-dark);font-size:10px;color:rgba(81,195,202,.3);letter-spacing:2px}}

/* Nav */
.nav-sticky{{position:fixed;top:0;left:0;right:0;background:rgba(13,43,56,.95);backdrop-filter:blur(12px);z-index:100;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;transform:translateY(-100%);transition:transform .3s}}
.nav-sticky.visible{{transform:translateY(0)}}
.nav-sticky .nav-logo{{font-family:'Poppins',sans-serif;font-weight:800;font-size:16px;color:var(--teal-light)}}
.nav-sticky .nav-logo-img{{height:32px;object-fit:contain}}
.nav-sticky .nav-links{{display:flex;gap:24px}}
.nav-sticky .nav-links a{{color:var(--teal-light);text-decoration:none;font-family:'Poppins',sans-serif;font-size:12px;font-weight:600;opacity:.7;transition:opacity .2s}}
.nav-sticky .nav-links a:hover{{opacity:1}}

@media(max-width:768px){{
  .ficha-grid{{grid-template-columns:1fr 1fr}}
  .metrics-row{{grid-template-columns:1fr}}
  .highlight-row{{grid-template-columns:1fr}}
  .testimonials-grid{{grid-template-columns:1fr}}
  .participants-list{{grid-template-columns:1fr}}
  .gallery{{grid-template-columns:1fr;grid-template-rows:auto}}
  .gallery-item:first-child{{grid-row:auto}}
}}
</style>
</head>
<body>

<nav class="nav-sticky" id="stickyNav">
  {f'<img src="{doit_logo_b64}" alt="DO IT" class="nav-logo-img">' if doit_logo_b64 else '<div class="nav-logo">DO IT</div>'}
  <div class="nav-links">
    <a href="#metricas">Métricas</a>
    <a href="#testimonios">Testimonios</a>
    {"<a href='#galeria'>Galería</a>" if photos_b64 else ""}
    <a href="#participantes">Participantes</a>
  </div>
</nav>

<header class="hero">
  <div class="logos">
    {f'<img src="{doit_logo_b64}" alt="DO IT" style="height:60px;object-fit:contain;">' if doit_logo_b64 else '<div class="logo-text">DO IT<small>Deep Human Learning</small></div>'}
    <span class="divider-x">×</span>
    {f'<img src="{client_logo_b64}" alt="{data["empresa"]}" style="height:50px;object-fit:contain;">' if client_logo_b64 else f'<span class="client-text">{data["empresa"]}</span>'}
  </div>
  <div class="badge">Resultados del taller</div>
  <h1>{' '.join(nombre_taller.split()[:len(nombre_taller.split())//2]) if len(nombre_taller.split()) > 2 else (nombre_taller.split()[0] if len(nombre_taller.split()) > 1 else nombre_taller)}<span>{' '.join(nombre_taller.split()[len(nombre_taller.split())//2:]) if len(nombre_taller.split()) > 2 else (' '.join(nombre_taller.split()[1:]) if len(nombre_taller.split()) > 1 else '')}</span></h1>
  <p class="hero-sub">{data['fecha']} · {lugar} · {data['n_participantes']} participantes</p>
  <div class="scroll-hint">↓</div>
</header>

<section>
  <div class="section-label">Ficha técnica</div>
  <div class="section-heading">Detalles del <span>taller</span></div>
  <div class="ficha-grid">
    <div class="ficha-card"><div class="fc-label">Cliente</div><div class="fc-value">{data['empresa']}</div></div>
    <div class="ficha-card"><div class="fc-label">Taller</div><div class="fc-value">{nombre_taller}</div></div>
    <div class="ficha-card"><div class="fc-label">{"Instructores" if instructor2 else "Instructor/a"}</div><div class="fc-value">{data['instructor'] + " y " + instructor2 if instructor2 else data['instructor']}</div></div>
    <div class="ficha-card"><div class="fc-label">Fecha</div><div class="fc-value">{data['fecha']}</div></div>
    <div class="ficha-card"><div class="fc-label">Duración</div><div class="fc-value">{duracion}</div></div>
    <div class="ficha-card"><div class="fc-label">{"Evaluaciones / Participantes" if total_participantes and total_participantes != data['n_participantes'] else "Participantes"}</div><div class="fc-value">{str(data['n_participantes']) + " / " + str(total_participantes) if total_participantes and total_participantes != data['n_participantes'] else data['n_participantes']}</div></div>
  </div>
</section>

<section id="metricas">
  <div class="section-label">Indicadores</div>
  <div class="section-heading">Métricas <span>clave</span></div>
  <div class="metrics-row">
    <div class="metric-card">
      <div class="metric-ring">
        <svg viewBox="0 0 130 130"><circle class="ring-bg" cx="65" cy="65" r="55"/><circle class="ring-fill" cx="65" cy="65" r="55" stroke="#51C3CA" data-pct="{sat_pct}"/></svg>
        <div class="ring-value">{sat_val}<small>/10</small></div>
      </div>
      <div class="metric-label">Satisfacción general</div>
    </div>
    <div class="metric-card">
      <div class="metric-ring">
        <svg viewBox="0 0 130 130"><circle class="ring-bg" cx="65" cy="65" r="55"/><circle class="ring-fill" cx="65" cy="65" r="55" stroke="#F9B401" data-pct="{inv_pct}"/></svg>
        <div class="ring-value">{inv_val}<small>/10</small></div>
      </div>
      <div class="metric-label">Valor de la inversión</div>
    </div>
    <div class="metric-card">
      <div class="metric-ring">
        <svg viewBox="0 0 130 130"><circle class="ring-bg" cx="65" cy="65" r="55"/><circle class="ring-fill" cx="65" cy="65" r="55" stroke="#006A91" data-pct="{inst_pct}"/></svg>
        <div class="ring-value">{inst_val}<small>/10</small></div>
      </div>
      <div class="metric-label">Calificación instructor/a</div>
    </div>
  </div>

  <div class="highlight-row">
    <div class="highlight-card">
      <h3><span class="dot" style="background:var(--gold)"></span>Expectativas</h3>
      <div class="bar-item"><div class="bar-header"><span class="bar-label">Superó expectativas</span><span class="bar-pct" style="color:var(--teal-light)">{data['expect_supero']}%</span></div><div class="bar-track"><div class="bar-fill" data-width="{data['expect_supero']}" style="background:var(--teal-light)"></div></div></div>
      <div class="bar-item"><div class="bar-header"><span class="bar-label">Como esperaba</span><span class="bar-pct" style="color:var(--gold)">{data['expect_cumplio']}%</span></div><div class="bar-track"><div class="bar-fill" data-width="{data['expect_cumplio']}" style="background:var(--gold)"></div></div></div>
      <div class="bar-item"><div class="bar-header"><span class="bar-label">Por debajo</span><span class="bar-pct" style="color:var(--grey)">{data['expect_debajo']}%</span></div><div class="bar-track"><div class="bar-fill" data-width="{data['expect_debajo']}" style="background:var(--grey)"></div></div></div>
    </div>
    <div class="highlight-card">
      <h3><span class="dot" style="background:var(--teal-mid)"></span>Frente a otros cursos</h3>
      <div class="bar-item"><div class="bar-header"><span class="bar-label">Superior</span><span class="bar-pct" style="color:var(--teal-mid)">{data['comp_superior']}%</span></div><div class="bar-track"><div class="bar-fill" data-width="{data['comp_superior']}" style="background:var(--teal-mid)"></div></div></div>
      <div class="bar-item"><div class="bar-header"><span class="bar-label">Igual</span><span class="bar-pct" style="color:var(--teal-light)">{data['comp_igual']}%</span></div><div class="bar-track"><div class="bar-fill" data-width="{data['comp_igual']}" style="background:var(--teal-light)"></div></div></div>
      <div class="bar-item"><div class="bar-header"><span class="bar-label">Inferior</span><span class="bar-pct" style="color:var(--grey)">{data['comp_inferior']}%</span></div><div class="bar-track"><div class="bar-fill" data-width="{data['comp_inferior']}" style="background:var(--grey)"></div></div></div>
    </div>
  </div>
</section>

<section id="testimonios">
  <div class="section-label">La voz del equipo</div>
  <div class="section-heading">Lo que dijeron los <span>participantes</span></div>
  <div class="testimonials-grid">{testimonials_html}</div>
</section>

{f"""<section id="instructor-feedback">
  <div class="section-label">Sobre el/la instructor/a</div>
  <div class="section-heading">Evaluación de <span>{data['instructor']}{' y ' + instructor2 if instructor2 else ''}</span></div>
  <div class="testimonials-grid">{instructor_html}</div>
</section>""" if instructor_html else ""}

{f"""<section id="galeria">
  <div class="section-label">Momentos</div>
  <div class="section-heading">Galería del <span>taller</span></div>
  <div class="gallery">{gallery_html}</div>
</section>""" if gallery_html else ""}

<section id="participantes">
  <div class="section-label">Asistencia</div>
  <div class="section-heading">Participantes que <span>evaluaron</span></div>
  <div class="participants-list">{participants_html}</div>
</section>

<footer class="cta-footer">
  <h2>Revisemos juntos los <span>resultados</span></h2>
  <p>Contacta a tu gerente comercial para agendar una reunión donde revisaremos hallazgos y oportunidades de mejora.</p>
  <div class="agent-card-footer">
    <div class="acf-photo">{"".join(w[0].upper() for w in self.config['gerente_nombre'].split()[:2])}</div>
    <div class="acf-details">
      <div class="acf-name">{self.config['gerente_nombre']}</div>
      <div class="acf-role">Gerente Comercial</div>
      <div class="acf-contact">{self.config['gerente_email']} · {self.config['gerente_telefono']}</div>
    </div>
    {f'<img src="{qr_b64}" alt="QR" class="acf-qr">' if qr_b64 else ''}
  </div>
</footer>
<div class="powered-by">POWERED BY DO IT · DEEP HUMAN LEARNING</div>

<script>
const nav=document.getElementById('stickyNav');
window.addEventListener('scroll',()=>{{nav.classList.toggle('visible',window.scrollY>window.innerHeight*.8)}});
const observer=new IntersectionObserver((entries)=>{{
  entries.forEach(entry=>{{
    if(entry.isIntersecting){{
      entry.target.querySelectorAll('.ring-fill').forEach(ring=>{{
        const pct=parseInt(ring.dataset.pct);
        const circ=2*Math.PI*55;
        ring.style.strokeDasharray=`${{(pct/100)*circ}} ${{circ}}`;
      }});
      entry.target.querySelectorAll('.bar-fill').forEach(bar=>{{
        bar.style.width=bar.dataset.width+'%';
      }});
      observer.unobserve(entry.target);
    }}
  }});
}},{{threshold:.3}});
document.querySelectorAll('#metricas').forEach(el=>observer.observe(el));
</script>

</body>
</html>'''

        safe_name = data['empresa'].replace(' ', '_')
        safe_taller = nombre_taller.replace(' ', '_')[:40]
        fecha_suffix = f"_{data['fecha_iso']}" if data.get('fecha_iso') else ''
        out_path = self.salida_dir / f"Reporte_{safe_name}_{safe_taller}{fecha_suffix}.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        if progress_callback: progress_callback(100)
        return str(out_path)


# ── CLI Entry Point ──────────────────────────────────────────

def main():
    """Quick CLI test."""
    gen = DOITReportGenerator()
    csv_path = gen.entrada_dir / "datos_curso.csv"
    if not csv_path.exists():
        print("No se encontró datos_curso.csv en entrada/")
        sys.exit(1)

    data = gen.parse_csv(str(csv_path))
    print(f"Empresa: {data['empresa']}")
    print(f"Participantes: {data['n_participantes']}")
    print(f"Satisfacción: {data['prom_satisfaccion']:.1f}/10")

    # Generate PNG
    logo_path = gen.entrada_dir / "logo_cliente.png"
    qr_path = gen.gerente_dir / "qr_gerente.png"
    fotos = sorted(gen.fotos_dir.glob("*"))

    png_path = gen.generate_png(
        data, "Power Team", "8 horas", "CDMX",
        logo_cliente_path=str(logo_path) if logo_path.exists() else None,
        qr_path=str(qr_path) if qr_path.exists() else None,
        progress_callback=lambda p: print(f"  PNG: {p}%")
    )
    print(f"\n✅ PNG: {png_path}")

    # Generate HTML
    html_path = gen.generate_html(
        data, "Power Team", "8 horas", "CDMX",
        fotos_paths=[str(f) for f in fotos],
        progress_callback=lambda p: print(f"  HTML: {p}%")
    )
    print(f"✅ HTML: {html_path}")


if __name__ == "__main__":
    main()
