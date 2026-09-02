#!/usr/bin/env python3
"""
Layout Perfect Typesetting Engine â "From These Streets" Template
=================================================================
Biographical/portrait profile layout for D&H Publishing International.
5.5 x 8.5 inch trim, mirrored margins, warm brown accents, centred folios,
fleuron ornaments, three-dot profile separators, themed chapter openers.
"""

import re, os
import pyphen
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from templates import TEMPLATES, draw_ornament, draw_scene_break, format_chapter_number

# Supported image formats
SUPPORTED_IMG = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)|]+)(?:\|(\w+))?\)')
CAPTION_SZ_OFFSET = 1.5  # caption is this many pt smaller than body
C_CAPTION = HexColor('#666666')
IMG_SPACING = 0.4 * 72 / 2.54  # 0.4cm in points
CAPTION_GAP = 0.15 * 72 / 2.54  # 0.15cm in points
IMG_HEIGHT_CAP = 0.6  # max 60% of text block height

# ââ Dimensions ââââââââââââââââââââââââââââââââââââââââââââââââââââââ
PAGE_W = 5.5 * inch
PAGE_H = 8.5 * inch
# D&H house margins: 2.54cm top/bottom, 1.54cm left, 1.6cm right, 1cm gutter
# Inside (spine) = left + gutter = 1.54 + 1.0 = 2.54cm = 1.0 inch
# Outside = right = 1.6cm = 0.630 inch
MARGIN_INSIDE  = 1.0 * inch     # 2.54cm (1.54cm + 1cm gutter)
MARGIN_OUTSIDE = 0.630 * inch   # 1.6cm
MARGIN_TOP     = 1.0 * inch     # 2.54cm
MARGIN_BOTTOM  = 1.0 * inch     # 2.54cm
HEADER_Y = PAGE_H - 0.5 * inch
FOOTER_Y = 0.5 * inch

def set_trim_size(width_in, height_in):
    """Set page dimensions globally. Must be called before building.
    Supports all 14 KDP trim sizes."""
    global PAGE_W, PAGE_H, HEADER_Y, FOOTER_Y
    PAGE_W = width_in * inch
    PAGE_H = height_in * inch
    HEADER_Y = PAGE_H - 0.5 * inch
    FOOTER_Y = 0.5 * inch

# ââ Colours âââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
C_BODY    = HexColor('#2C2C2C')
C_BROWN   = HexColor('#8B7355')
C_GREY    = HexColor('#999999')
C_MID     = HexColor('#888888')
C_DARK    = HexColor('#4A4A4A')

# ââ Fonts âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
FD = '/usr/share/fonts/truetype/freefont'
pdfmetrics.registerFont(TTFont('Gar',   f'{FD}/FreeSerif.ttf'))
pdfmetrics.registerFont(TTFont('GarB',  f'{FD}/FreeSerifBold.ttf'))
pdfmetrics.registerFont(TTFont('GarI',  f'{FD}/FreeSerifItalic.ttf'))
pdfmetrics.registerFont(TTFont('GarBI', f'{FD}/FreeSerifBoldItalic.ttf'))
pdfmetrics.registerFontFamily('Gar', normal='Gar', bold='GarB',
                              italic='GarI', boldItalic='GarBI')

# Sans-serif fonts (for Modernist, Thriller, Minimal, etc.)
pdfmetrics.registerFont(TTFont('Sans',   f'{FD}/FreeSans.ttf'))
pdfmetrics.registerFont(TTFont('SansB',  f'{FD}/FreeSansBold.ttf'))
pdfmetrics.registerFont(TTFont('SansI',  f'{FD}/FreeSansOblique.ttf'))
pdfmetrics.registerFont(TTFont('SansBI', f'{FD}/FreeSansBoldOblique.ttf'))
pdfmetrics.registerFontFamily('Sans', normal='Sans', bold='SansB', italic='SansI', boldItalic='SansBI')

# Monospace fonts (for Screenplay)
pdfmetrics.registerFont(TTFont('Mono',   f'{FD}/FreeMono.ttf'))
pdfmetrics.registerFont(TTFont('MonoB',  f'{FD}/FreeMonoBold.ttf'))
pdfmetrics.registerFont(TTFont('MonoI',  f'{FD}/FreeMonoOblique.ttf'))
pdfmetrics.registerFont(TTFont('MonoBI', f'{FD}/FreeMonoBoldOblique.ttf'))
pdfmetrics.registerFontFamily('Mono', normal='Mono', bold='MonoB', italic='MonoI', boldItalic='MonoBI')

# ── Multilingual support ─────────────────────────────────────────────
_CJK_FONT_CANDIDATES = [
    '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
    '/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc',
]
_CJK_FONT_CANDIDATES_BOLD = [
    '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',
    '/usr/share/fonts/truetype/noto/NotoSerifCJK-Bold.ttc',
]

def _find_cjk_font(bold=False):
    candidates = _CJK_FONT_CANDIDATES_BOLD if bold else _CJK_FONT_CANDIDATES
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

QUOTE_STYLES = {
    'en': {'open': '\u201C', 'close': '\u201D', 'single_open': '\u2018', 'single_close': '\u2019'},
    'fr': {'open': '\u00AB\u00A0', 'close': '\u00A0\u00BB', 'single_open': '\u2018', 'single_close': '\u2019'},
    'de': {'open': '\u201E', 'close': '\u201C', 'single_open': '\u201A', 'single_close': '\u2018'},
    'it': {'open': '\u00AB', 'close': '\u00BB', 'single_open': '\u2018', 'single_close': '\u2019'},
    'es': {'open': '\u00AB', 'close': '\u00BB', 'single_open': '\u2018', 'single_close': '\u2019'},
    'nl': {'open': '\u201C', 'close': '\u201D', 'single_open': '\u2018', 'single_close': '\u2019'},
    'ja': {'open': '\u300C', 'close': '\u300D', 'single_open': '\u300E', 'single_close': '\u300F'},
}

LABELS = {
    'en': {'chapter': 'Chapter', 'page': 'Page', 'contents': 'Contents', 'bibliography': 'Bibliography', 'glossary': 'Glossary', 'index': 'Index', 'acknowledgements': 'Acknowledgements', 'foreword': 'Foreword'},
    'fr': {'chapter': 'Chapitre', 'page': 'Page', 'contents': 'Table des mati\u00e8res', 'bibliography': 'Bibliographie', 'glossary': 'Glossaire', 'index': 'Index', 'acknowledgements': 'Remerciements', 'foreword': 'Avant-propos'},
    'de': {'chapter': 'Kapitel', 'page': 'Seite', 'contents': 'Inhaltsverzeichnis', 'bibliography': 'Literaturverzeichnis', 'glossary': 'Glossar', 'index': 'Register', 'acknowledgements': 'Danksagung', 'foreword': 'Vorwort'},
    'it': {'chapter': 'Capitolo', 'page': 'Pagina', 'contents': 'Indice', 'bibliography': 'Bibliografia', 'glossary': 'Glossario', 'index': 'Indice analitico', 'acknowledgements': 'Ringraziamenti', 'foreword': 'Prefazione'},
    'es': {'chapter': 'Cap\u00edtulo', 'page': 'P\u00e1gina', 'contents': '\u00cdndice', 'bibliography': 'Bibliograf\u00eda', 'glossary': 'Glosario', 'index': '\u00cdndice anal\u00edtico', 'acknowledgements': 'Agradecimientos', 'foreword': 'Pr\u00f3logo'},
    'nl': {'chapter': 'Hoofdstuk', 'page': 'Pagina', 'contents': 'Inhoudsopgave', 'bibliography': 'Bibliografie', 'glossary': 'Woordenlijst', 'index': 'Register', 'acknowledgements': 'Dankwoord', 'foreword': 'Voorwoord'},
    'ja': {'chapter': '\u7b2c{n}\u7ae0', 'page': '\u30da\u30fc\u30b8', 'contents': '\u76ee\u6b21', 'bibliography': '\u53c2\u8003\u6587\u732e', 'glossary': '\u7528\u8a9e\u96c6', 'index': '\u7d20\u5f15', 'acknowledgements': '\u8b1d\u8f9e', 'foreword': '\u5e8f\u6587'},
}

def is_japanese(lang):
    return lang is not None and lang.startswith('ja')

def _lang_base(lang):
    if not lang:
        return 'en'
    return lang.split('_')[0]

def get_quote_style(lang='en_GB'):
    return QUOTE_STYLES.get(_lang_base(lang), QUOTE_STYLES['en'])

def get_label(lang, key, n=None):
    base = _lang_base(lang)
    labels = LABELS.get(base, LABELS['en'])
    label = labels.get(key, LABELS['en'].get(key, key))
    if n is not None and '{n}' in label:
        label = label.replace('{n}', str(n))
    return label

def convert_quotation_marks(text, lang='en_GB'):
    """Convert straight double quotes to language-specific typographic marks.
    Existing curly quotes, guillemets, etc. are left untouched."""
    style = get_quote_style(lang)
    result = []
    in_double = False
    for ch in text:
        if ch == '"':
            if not in_double:
                result.append(style['open'])
                in_double = True
            else:
                result.append(style['close'])
                in_double = False
        else:
            result.append(ch)
    return ''.join(result)

def set_language_fonts(lang='en_GB'):
    """Switch registered fonts to CJK-compatible versions for Japanese."""
    if is_japanese(lang):
        reg = _find_cjk_font(bold=False)
        bold = _find_cjk_font(bold=True)
        if reg:
            pdfmetrics.registerFont(TTFont('Gar', reg, subfontIndex=0))
            pdfmetrics.registerFont(TTFont('GarI', reg, subfontIndex=0))
            if bold:
                pdfmetrics.registerFont(TTFont('GarB', bold, subfontIndex=0))
                pdfmetrics.registerFont(TTFont('GarBI', bold, subfontIndex=0))
            else:
                pdfmetrics.registerFont(TTFont('GarB', reg, subfontIndex=0))
                pdfmetrics.registerFont(TTFont('GarBI', reg, subfontIndex=0))
            pdfmetrics.registerFontFamily('Gar', normal='Gar', bold='GarB',
                                          italic='GarI', boldItalic='GarBI')
        else:
            print('WARNING: CJK fonts not found')
    else:
        pdfmetrics.registerFont(TTFont('Gar', f'{FD}/FreeSerif.ttf'))
        pdfmetrics.registerFont(TTFont('GarB', f'{FD}/FreeSerifBold.ttf'))
        pdfmetrics.registerFont(TTFont('GarI', f'{FD}/FreeSerifItalic.ttf'))
        pdfmetrics.registerFont(TTFont('GarBI', f'{FD}/FreeSerifBoldItalic.ttf'))
        pdfmetrics.registerFontFamily('Gar', normal='Gar', bold='GarB',
                                      italic='GarI', boldItalic='GarBI')


BODY_SZ = 12
BODY_LD = 18
PROF_NAME_SZ = 12.5
PROF_TAG_SZ  = 9.5
CH_TITLE_SZ  = 22
CH_SUB_SZ    = 13
HDR_SZ = 8
FTR_SZ = 9
# Text alignment and hyphenation (LP-FEAT-007)
TEXT_ALIGNMENT = 'justified'
HYPHEN_LANGUAGE = 'en_GB'
HYPHENATE = True
SOFT_HYPHEN = '\u00AD'

_hyphenator_cache = {}

def get_hyphenator(lang='en_GB'):
    if lang not in _hyphenator_cache:
        try:
            _hyphenator_cache[lang] = pyphen.Pyphen(lang=lang)
        except Exception:
            _hyphenator_cache[lang] = None
    return _hyphenator_cache[lang]

def add_soft_hyphens(text, lang='en_GB'):
    if not HYPHENATE or is_japanese(lang):
        return text
    hyphenator = get_hyphenator(lang)
    if not hyphenator:
        return text
    words = text.split()
    result = []
    for word in words:
        clean = re.sub(r'[^a-zA-Z]', '', word)
        if len(clean) <= 5:
            result.append(word)
            continue
        hyphenated = hyphenator.inserted(word, hyphen=SOFT_HYPHEN)
        result.append(hyphenated)
    return ' '.join(result)


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# PARAGRAPH JOINER â key fix for hard-wrapped markdown
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def join_paragraphs(lines):
    """Join hard-wrapped markdown lines into proper paragraphs.
    Paragraphs are separated by blank lines. Special lines (headings,
    separators, ornaments) are kept separate."""
    paragraphs = []
    current = []
    
    for line in lines:
        stripped = line.strip()
        
        # Blank line = paragraph break
        if not stripped:
            if current:
                paragraphs.append(' '.join(current))
                current = []
            continue
        
        # Image references â always their own block
        if IMAGE_PATTERN.match(stripped):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Special markers â always their own block
        if stripped in ('â¢ â¢ â¢', 'â¦') or stripped.startswith('--- '):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Headings
        if stripped.startswith('#'):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Bold name lines (profile names like **William Crabtree**)
        if (stripped.startswith('**') and stripped.endswith('**') 
            and len(stripped) < 80 and '\n' not in stripped
            and not stripped.startswith('**FROM')):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Tagline lines (italic dates like *1610--1644 Â· Broughton Â· Astronomer*)
        if (stripped.startswith('*') and stripped.endswith('*') 
            and not stripped.startswith('**')
            and 'Â·' in stripped and len(stripped) < 100):
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append(stripped)
            continue
        
        # Normal text â accumulate
        current.append(stripped)
    
    if current:
        paragraphs.append(' '.join(current))
    
    return paragraphs


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# MANUSCRIPT PARSER
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def parse_manuscript(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_lines = f.read().split('\n')
    
    blocks = []
    
    # ââ Locate key sections by line number ââ
    # Title page: lines 1-16 (before first â¦)
    blocks.append({'type': 'title_page'})
    
    # Copyright: between second "FROM THESE STREETS" and next â¦
    cp_lines = []
    found_second_title = False
    for j, line in enumerate(raw_lines):
        if j > 15 and '**FROM THESE STREETS**' in line and not found_second_title:
            found_second_title = True
            continue
        if found_second_title:
            if line.strip() == 'â¦':
                break
            cp_lines.append(line)
    blocks.append({'type': 'copyright_page', 'lines': cp_lines})
    
    # Dedication
    blocks.append({'type': 'dedication_page'})
    
    # Note on Inclusion
    note_lines = []
    in_note = False
    for j, line in enumerate(raw_lines):
        if line.strip() == '**A Note on Inclusion**':
            in_note = True
            continue
        if in_note:
            if is_toc_placeholder_line(line):
                break
            note_lines.append(line)
    note_paras = join_paragraphs(note_lines)
    blocks.append({'type': 'note_on_inclusion', 'paras': [p for p in note_paras if p.strip()]})
    
    # TOC placeholder
    blocks.append({'type': 'toc'})
    
    # ââ Find Introduction ââ
    intro_start = None
    for j, line in enumerate(raw_lines):
        if line.strip() == '# Introduction':
            intro_start = j
            break
    
    if intro_start is None:
        return blocks
    
    # Collect everything from Introduction to end, then parse
    # into chapters, profiles, afterword
    content_lines = raw_lines[intro_start:]
    
    # First join into paragraphs
    paras = join_paragraphs(content_lines)
    
    # Now parse the paragraph stream
    i = 0
    while i < len(paras):
        p = paras[i].strip()
        
        # Chapter heading: # or ##
        if p.startswith('# ') or p.startswith('## '):
            title = p.lstrip('#').strip()
            if title in ('Supplementary Material', 'Further Reading'):
                i += 1
                continue
            
            is_afterword = 'Afterword' in title
            subtitle = ''
            intro = []
            i += 1
            
            # Look for subtitle (italic line with no bold)
            if i < len(paras):
                candidate = paras[i].strip()
                if (candidate.startswith('*') and candidate.endswith('*')
                    and not candidate.startswith('**')):
                    subtitle = candidate.strip('*').strip('\\')
                    i += 1
            
            # Collect intro/body paragraphs
            # For Afterword, collect everything until end markers
            while i < len(paras):
                pp = paras[i].strip()
                if pp.startswith('--- ') or pp == 'â¦':
                    break
                if not is_afterword:
                    # Normal chapter: stop at first profile marker
                    if (pp == 'â¢ â¢ â¢'
                        or (pp.startswith('**') and pp.endswith('**') and len(pp) < 80
                            and '(' not in pp)):
                        break
                    if pp.startswith('*') and pp.endswith('*') and 'Â·' in pp:
                        break
                else:
                    # Afterword: skip separators but include everything else
                    if pp == 'â¢ â¢ â¢':
                        i += 1
                        continue
                    if pp.startswith('## ') or pp.startswith('# '):
                        break
                intro.append(pp)
                i += 1
            
            blocks.append({
                'type': 'chapter' if not is_afterword else 'afterword',
                'title': title,
                'subtitle': subtitle,
                'intro': intro,
            })
            continue
        
        # Bold section header (chapter-level for later sections)
        if (p.startswith('**The ') and p.endswith('**') and len(p) < 80):
            title = p.strip('*')
            subtitle = ''
            intro = []
            i += 1
            
            if i < len(paras):
                candidate = paras[i].strip()
                if (candidate.startswith('*') and candidate.endswith('*')
                    and not candidate.startswith('**') and 'Â·' not in candidate):
                    subtitle = candidate.strip('*').strip('\\')
                    i += 1
            
            while i < len(paras):
                pp = paras[i].strip()
                if (pp == 'â¢ â¢ â¢' or pp.startswith('--- ') or pp == 'â¦'
                    or (pp.startswith('**') and pp.endswith('**') and len(pp) < 80)):
                    break
                if pp.startswith('*') and pp.endswith('*') and 'Â·' in pp:
                    break
                intro.append(pp)
                i += 1
            
            blocks.append({
                'type': 'chapter',
                'title': title,
                'subtitle': subtitle,
                'intro': intro,
            })
            continue
        
        # Profile separator
        if p == 'â¢ â¢ â¢':
            i += 1
            continue
        
        # Profile name â but NOT inline bold names in Afterword body,
        # and NOT the back page URL or other non-profile bold text
        if (p.startswith('**') and p.endswith('**') and len(p) < 80
            and not p.startswith('**FROM') and not p.startswith('**A Note')
            and not is_toc_placeholder_line(p)
            and not p.startswith('**www.')
            and '(' not in p):  # Afterword inline profiles have (dates) after
            name = p.strip('*')
            tagline = ''
            body = []
            i += 1
            
            # Tagline
            if i < len(paras):
                candidate = paras[i].strip()
                if (candidate.startswith('*') and candidate.endswith('*')
                    and not candidate.startswith('**') and 'Â·' in candidate):
                    tagline = candidate.strip('*').strip('\\')
                    i += 1
            
            # Body paragraphs
            while i < len(paras):
                pp = paras[i].strip()
                if (pp == 'â¢ â¢ â¢' or pp.startswith('--- ') or pp == 'â¦'
                    or (pp.startswith('**') and pp.endswith('**') and len(pp) < 80)
                    or pp.startswith('# ') or pp.startswith('## ')):
                    break
                body.append(pp)
                i += 1
            
            blocks.append({
                'type': 'profile',
                'name': name,
                'tagline': tagline,
                'body': body,
            })
            continue
        
        # End markers â skip
        if p.startswith('--- ') or p == 'â¦':
            i += 1
            continue
        
        # Stray text (e.g. appendix placeholders, back page)
        i += 1
    
    return blocks


# Localised "Table of Contents" titles, keyed by language code.
# Used for the generated TOC heading and to recognise manuscript TOC
# placeholders (bold or markdown) so they are not rendered as body text.
TOC_TITLES = {
    'en_GB': 'Table of Contents',
    'en_US': 'Table of Contents',
    'en': 'Table of Contents',
    'fr': 'Table des matiÃ¨res',
    'de': 'Inhaltsverzeichnis',
    'es': 'Ãndice',
    'it': 'Indice',
    'pt': 'Ãndice',
    'pt_BR': 'SumÃ¡rio',
    'nl': 'Inhoudsopgave',
    'sv': 'InnehÃ¥llsfÃ¶rteckning',
    'da': 'Indholdsfortegnelse',
    'nb': 'Innholdsfortegnelse',
    'nn': 'Innhaldsfortegnelse',
    'fi': 'SisÃ¤llysluettelo',
    'pl': 'Spis treÅci',
    'cs': 'Obsah',
    'sk': 'Obsah',
    'hu': 'TartalomjegyzÃ©k',
    'ro': 'Cuprins',
    'ru': 'Ð¡Ð¾Ð´ÐµÑÐ¶Ð°Ð½Ð¸Ðµ',
    'uk': 'ÐÐ¼ÑÑÑ',
    'el': 'Î ÎµÏÎ¹ÎµÏÏÎ¼ÎµÎ½Î±',
    'tr': 'Ä°Ã§indekiler',
    'ar': 'ÙÙØ±Ø³ Ø§ÙÙØ­ØªÙÙØ§Øª',
    'he': '×ª××× ××¢× ××× ××',
    'ja': 'ç®æ¬¡',
    'zh': 'ç®å½',
    'zh_CN': 'ç®å½',
    'zh_TW': 'ç®é',
    'ko': 'ì°¨ë¡',
}

_TOC_PLACEHOLDER_TEXTS = set(TOC_TITLES.values()) | {'Contents'}


def get_toc_title(lang='en_GB'):
    """Return the localised 'Table of Contents' heading for a language code."""
    if not lang:
        return TOC_TITLES['en_GB']
    if lang in TOC_TITLES:
        return TOC_TITLES[lang]
    base = lang.split('_')[0]
    if base in TOC_TITLES:
        return TOC_TITLES[base]
    if base.startswith('en'):
        return TOC_TITLES['en_GB']
    return TOC_TITLES['en_GB']


def is_toc_placeholder_line(text):
    """True if a manuscript line is a TOC heading placeholder (markdown or bold)."""
    t = text.strip().lstrip('#').strip().strip('*').strip()
    return t in _TOC_PLACEHOLDER_TEXTS


def parse_manuscript_generic(filepath):
    """Generic parser for novels, non-fiction, and any standard markdown manuscript.
    Handles: # Part, # Chapter, ## Subtitle, body text, scene breaks (*** ---),
    and back matter (Author's Note, Acknowledgements, About, etc.)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_lines = f.read().split('\n')
    
    paras = join_paragraphs(raw_lines)
    blocks = []
    i = 0
    PLACEHOLDER_RE = re.compile(r'^\[Paste .* text here\]$')
    
    while i < len(paras):
        p = paras[i].strip()
        if not p:
            i += 1
            continue
        
        # # Heading (Part, Chapter, Prologue, Epilogue, back matter)
        if p.startswith('# '):
            title = p[2:].strip()
            subtitle = ''
            body = []
            i += 1
            
            # Check for ## subtitle
            if i < len(paras) and paras[i].strip().startswith('## '):
                subtitle = paras[i].strip()[3:].strip()
                i += 1
            
            # Collect body until next # heading
            while i < len(paras):
                pp = paras[i].strip()
                if pp.startswith('# '):
                    break
                if pp in ('***', '* * *') or (len(pp) >= 3 and all(c == '-' for c in pp)):
                    body.append({'type': 'scene_break'})
                    i += 1
                    continue
                if IMAGE_PATTERN.match(pp):
                    body.append({'type': 'image', 'text': pp})
                    i += 1
                    continue
                body.append({'type': 'para', 'text': pp})
                i += 1
            
            # Skip ghost sections from BookBuilder frameworks - chapters whose
            # body is only placeholder text ("[Paste ... text here]"), or known
            # framework section names (Supplementary Material, Further Reading)
            # with no real content.
            body_paras = [b for b in body if b.get('type') == 'para']
            if body_paras and all(PLACEHOLDER_RE.match(b['text'].strip()) for b in body_paras):
                continue
            if not body and title in ('Supplementary Material', 'Further Reading'):
                continue
            
            # Part headings typically have no body (just a title page)
            is_part = (title.lower().startswith('part ') and len(body) == 0)
            
            blocks.append({
                'type': 'part' if is_part else 'chapter',
                'title': title,
                'subtitle': subtitle,
                'body': body,
            })
            continue
        
        # ## Heading without parent #
        if p.startswith('## '):
            title = p[3:].strip()
            body = []
            i += 1
            while i < len(paras):
                pp = paras[i].strip()
                if pp.startswith('# ') or pp.startswith('## '):
                    break
                if pp in ('***', '* * *') or (len(pp) >= 3 and all(c == '-' for c in pp)):
                    body.append({'type': 'scene_break'})
                    i += 1
                    continue
                if IMAGE_PATTERN.match(pp):
                    body.append({'type': 'image', 'text': pp})
                    i += 1
                    continue
                body.append({'type': 'para', 'text': pp})
                i += 1
            blocks.append({
                'type': 'chapter', 'title': title,
                'subtitle': '', 'body': body,
            })
            continue
        
        i += 1
    
    return blocks


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# GENERIC BOOK BUILDER â works with any manuscript structure
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

class GenericBookBuilder:
    """Builds print-ready PDFs from any markdown manuscript.
    Uses parse_manuscript_generic for structure detection."""
    
    def __init__(self, md_path, output_path, title='Untitled', author='Unknown',
                 subtitle='', publisher='D&H Publishing International',
                 publisher_url='www.dandhpublishing.com',
                 chapter_end_ornament='fleuron',
                 language='en_GB',
                 template='narrative'):
        self.md_path = md_path
        self.output_path = output_path
        self.title = title
        self.subtitle = subtitle
        self.author = author
        self.publisher = publisher
        self.publisher_url = publisher_url
        self.chapter_end_ornament = chapter_end_ornament
        self.language = language
        self.template = template
        self.tpl = TEMPLATES.get(template, TEMPLATES['narrative'])
        self.toc_title = get_toc_title(language)
        self.blocks = parse_manuscript_generic(md_path)
        for _blk in self.blocks:
            if 'body' in _blk:
                for _item in _blk['body']:
                    if _item.get('type') == 'para':
                        _item['text'] = convert_quotation_marks(_item['text'], language)
            elif _blk.get('type') == 'para':
                _blk['text'] = convert_quotation_marks(_blk['text'], language)
        self.image_base_dir = os.path.dirname(os.path.abspath(md_path))
    
    def _render(self, path, toc_entries=None):
        r = BookRenderer(path)
        r.image_base_dir = self.image_base_dir
        r.header_text = self.title
        r.chapter_end_ornament = self.chapter_end_ornament
        r.toc_title = self.toc_title
        r.tpl = self.tpl
        r.author_name = self.author
        r.current_chapter_title = ''
        r.chapter_count = 0
        
        # ââ Front matter (generic, driven by title/author) ââ
        # Title page
        r._new_page(suppress=True)
        y = PAGE_H - 2.2 * inch
        
        # Auto-size title to fit within page margins
        # Start at 42pt, reduce until it fits (single or multi-line)
        tw = r._tw()
        title_sz = 42
        title_lines = [self.title]
        
        while title_sz >= 18:
            r.c.setFont('GarB', title_sz)
            single_w = r.c.stringWidth(self.title, 'GarB', title_sz)
            
            if single_w <= tw:
                # Fits on one line
                title_lines = [self.title]
                break
            
            # Try splitting into two lines
            words = self.title.split()
            best_split = None
            best_max_w = single_w
            for split_at in range(1, len(words)):
                line1 = ' '.join(words[:split_at])
                line2 = ' '.join(words[split_at:])
                w1 = r.c.stringWidth(line1, 'GarB', title_sz)
                w2 = r.c.stringWidth(line2, 'GarB', title_sz)
                max_w = max(w1, w2)
                if max_w < best_max_w:
                    best_max_w = max_w
                    best_split = (line1, line2)
            
            if best_split and best_max_w <= tw:
                title_lines = [best_split[0], best_split[1]]
                break
            
            title_sz -= 2
        
        # Render title lines
        for tl in title_lines:
            r._ctxt(y, tl, 'GarB', title_sz, C_BODY)
            y -= title_sz + 8
        
        y -= 8
        
        # Subtitle (if provided)
        if self.subtitle:
            # Auto-size subtitle too
            sub_sz = 16
            while sub_sz >= 10:
                if r.c.stringWidth(self.subtitle, 'GarI', sub_sz) <= tw:
                    break
                sub_sz -= 1
            r._ctxt(y, self.subtitle, 'GarI', sub_sz, C_BROWN)
            y -= sub_sz + 14
        
        r._divider(y, 'star'); y -= 35
        r._ctxt(y, self.author, 'GarI', 14, C_DARK); y -= 35
        r._divider(y, 'star'); y -= 50
        r._ctxt(y, 'published by:', 'Gar', 9, C_DARK); y -= 18
        r._ctxt(y, self.publisher, 'Gar', 11, C_BODY); y -= 35
        r._ornament(y)
        r._finish_page()
        
        # Blank verso
        r._new_page(suppress=True)
        r._finish_page()
        
        # Copyright page
        r._new_page(suppress=True)
        y = PAGE_H - 2.0 * inch
        r._ctxt(y, self.title, 'GarB', 14, C_BODY); y -= 20
        r._ctxt(y, self.author, 'GarI', 11, C_BROWN); y -= 30
        lm = r._lm()
        for line in [
            f'First published in 2026 by {self.publisher}.',
            f'\u00a9 2026 {self.author}. All rights reserved.',
            '',
            'No part of this publication may be reproduced, distributed, or transmitted '
            'in any form or by any means, including photocopying, recording, or other '
            'electronic or mechanical methods, without the prior written permission of '
            'the publisher, except in the case of brief quotations embodied in critical '
            'reviews and certain other non-commercial uses permitted by copyright law.',
            '',
            f'{self.publisher_url}',
        ]:
            if not line:
                y -= 8
                continue
            wrapped = r._wrap(line, 'Gar', 9.5, r._tw())
            for wl in wrapped:
                if y < MARGIN_BOTTOM + 30:
                    break
                r.c.setFont('Gar', 9.5)
                r.c.setFillColor(C_BODY)
                if line == self.publisher_url:
                    r.c.drawCentredString(PAGE_W / 2, y, wl)
                else:
                    r.c.drawString(lm, y, wl)
                y -= 13
            y -= 3
        y -= 10
        r._ornament(y)
        r._finish_page()
        
        # TOC placeholder or real TOC
        if toc_entries:
            r.render_toc(toc_entries)
        else:
            r._ensure_recto()
            r._ctxt(PAGE_H - MARGIN_TOP - 30, r.toc_title, 'GarB', 22, C_BODY)
            r._finish_page()
            r._new_page(suppress=True)
            r._finish_page()
        
        # ââ Body content ââ
        for i, blk in enumerate(self.blocks):
            t = blk['type']
            
            if t == 'part':
                # Part title page â centred, recto, no body text
                r._ensure_recto()
                r.is_front_matter = False
                r.toc_entries.append((blk['title'], r.page_num, 0))
                y = PAGE_H / 2 + 30
                r._ctxt(y, blk['title'].upper(), 'GarB', 24, C_BODY)
                if blk.get('subtitle'):
                    y -= 28
                    r._ctxt(y, blk['subtitle'], 'GarI', 14, C_BROWN)
                r._finish_page()
            
            elif t == 'chapter':
                # Build TOC entry with subtitle if available
                toc_title = blk['title']
                if blk.get('subtitle'):
                    toc_title = f"{blk['title']}: {blk['subtitle']}"
                r.toc_entries.append((toc_title, r.page_num + 1, 1 if any(
                    b['type'] == 'part' for b in self.blocks[:i]) else 0))
                r.render_chapter_opener(blk['title'], blk.get('subtitle', ''))
                
                # Render body content
                for item in blk.get('body', []):
                    if item['type'] == 'para':
                        r._draw_content(item['text'])
                    elif item['type'] == 'scene_break':
                        r._check_page(40)
                        r.current_y -= 12
                        cx = r._lm() + r._tw() / 2
                        _sb = r.tpl.get('scene_break', 'dots') if hasattr(r, 'tpl') else 'dots'
                        draw_scene_break(r.c, r.current_y, cx, _sb, C_MID)
                        r.current_y -= 20
                    elif item['type'] == 'image':
                        r._draw_content(item['text'])
                
                # Chapter end divider if next block is a part or it's the last
                if i + 1 < len(self.blocks):
                    nt = self.blocks[i + 1]['type']
                    if nt == 'part':
                        r.render_chapter_end()
                if i == len(self.blocks) - 1:
                    r.render_chapter_end()
        
        # ââ Back page ââ
        r._ensure_recto()
        y = PAGE_H / 2 + 20
        r._ctxt(y, self.publisher_url, 'GarB', 13, C_BODY); y -= 22
        r._ctxt(y, self.title, 'GarI', 11, C_DARK); y -= 30
        r._divider(y, 'star'); y -= 25
        r._ctxt(y, self.publisher, 'Gar', 10, C_DARK); y -= 18
        r.c.setFont('Gar', 8.5)
        r.c.setFillColor(C_GREY)
        r.c.drawCentredString(PAGE_W / 2, y,
                             f'\u00a9 2026 {self.author}. All rights reserved.')
        r._finish_page()
        
        r.c.save()
        self._last_image_log = r.image_log
        return r.toc_entries
    
    def build(self):
        print(f"Building: {self.title} by {self.author}")
        print("Pass 1: Collecting page numbers...")
        tmp = self.output_path.replace('.pdf', '_p1.pdf')
        toc = self._render(tmp)
        print(f"  {len(toc)} TOC entries")
        
        print("Pass 2: Final render with TOC...")
        self._render(self.output_path, toc)
        if os.path.exists(tmp):
            os.remove(tmp)
        
        self._set_trimbox()
        
        if self._last_image_log:
            print(f"\nIMAGES")
            print(f"------")
            placed = warnings = errors = 0
            for fname, page, hint, dpi, status in self._last_image_log:
                if status == 'OK':
                    print(f"  {fname:40s} placed p.{page} ({hint}, {dpi} DPI) \u2713")
                    placed += 1
                elif status == 'LOW RES':
                    print(f"  {fname:40s} placed p.{page} ({hint}, {dpi} DPI) \u26a0 LOW RES")
                    placed += 1; warnings += 1
                else:
                    print(f"  {fname:40s} {status} \u2717")
                    errors += 1
            print(f"\n  Total: {len(self._last_image_log)}, Placed: {placed}, Warnings: {warnings}, Errors: {errors}")
        
        print(f"Done: {self.output_path}")
        return self.output_path
    
    def _set_trimbox(self):
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, FloatObject, NameObject
        reader = PdfReader(self.output_path)
        writer = PdfWriter()
        for page in reader.pages:
            page[NameObject('/TrimBox')] = ArrayObject([
                FloatObject(0), FloatObject(0),
                FloatObject(PAGE_W), FloatObject(PAGE_H),
            ])
            writer.add_page(page)
        writer.add_metadata({
            '/Title': self.title,
            '/Author': self.author,
            '/Creator': 'Layout Perfect Typesetting Engine',
            '/Producer': 'ReportLab + pypdf',
        })
        with open(self.output_path, 'wb') as f:
            writer.write(f)

class BookRenderer:
    def __init__(self, output_path):
        self.c = canvas.Canvas(output_path, pagesize=(PAGE_W, PAGE_H))
        self.c.setTitle("From These Streets")
        self.c.setAuthor("David Oldham")
        self.page_num = 0
        self.toc_entries = []
        self.suppress_hdr = False
        self.is_front_matter = True  # suppress folios in front matter
        self.current_y = PAGE_H - MARGIN_TOP - 10
        self.output_path = output_path
        self.image_base_dir = ''  # set by BookBuilder
        self.image_log = []  # [(filename, page, size_hint, dpi, status)]
        self.header_text = ''  # set by builder
        self.toc_title = 'Table of Contents'  # localised by builder
        self.chapter_end_ornament = 'fleuron'  # fleuron | divider | none â used in running header
        
    def _margins(self):
        if self.page_num % 2 == 1:  # Recto: gutter left
            return MARGIN_INSIDE, MARGIN_OUTSIDE
        return MARGIN_OUTSIDE, MARGIN_INSIDE
    
    def _tw(self):
        l, r = self._margins()
        return PAGE_W - l - r
    
    def _lm(self):
        return self._margins()[0]
    
    def _draw_header(self):
        tpl = getattr(self, 'tpl', {})
        style = tpl.get('header_style', 'centered')
        if self.suppress_hdr or self.is_front_matter or style == 'none':
            return
        hdr_font = tpl.get('header_font', 'GarI')
        l, r = self._margins()
        
        self.c.setFont(hdr_font, HDR_SZ)
        self.c.setFillColor(C_GREY)
        
        if style == 'centered':
            txt = self.header_text or 'Layout Perfect'
            self.c.drawCentredString(PAGE_W/2, HEADER_Y, txt)
        elif style == 'title_left_chapter_right':
            self.c.drawString(l, HEADER_Y, self.header_text or '')
            if getattr(self, 'current_chapter_title', ''):
                self.c.drawRightString(PAGE_W - r, HEADER_Y, self.current_chapter_title)
        elif style == 'author_left_chapter_right':
            self.c.drawString(l, HEADER_Y, getattr(self, 'author_name', '') or '')
            ch = getattr(self, 'chapter_count', 0)
            if ch:
                self.c.drawRightString(PAGE_W - r, HEADER_Y, str(ch))
        elif style == 'chapter_left_section_right':
            if getattr(self, 'current_chapter_title', ''):
                self.c.drawString(l, HEADER_Y, self.current_chapter_title)
        
        if tpl.get('header_rule', True):
            self.c.setStrokeColor(HexColor('#D0C8B8'))
            self.c.setLineWidth(0.3)
            self.c.line(l, HEADER_Y - 6, PAGE_W - r, HEADER_Y - 6)
    
        def _draw_folio(self):
        tpl = getattr(self, 'tpl', {})
        if self.is_front_matter:
            return
        if getattr(self, '_suppress_folio_this_page', False):
            self._suppress_folio_this_page = False
            return
        pos = tpl.get('folio_position', 'centered')
        folio_font = tpl.get('folio_font', 'Gar')
        self.c.setFont(folio_font, FTR_SZ)
        self.c.setFillColor(C_GREY)
        l, r = self._margins()
        
        if pos == 'centered' or pos == 'centered_with_dots':
            num_str = str(self.page_num)
            self.c.drawCentredString(PAGE_W/2, FOOTER_Y, num_str)
            if pos == 'centered_with_dots':
                w = self.c.stringWidth(num_str, folio_font, FTR_SZ)
                cx = PAGE_W / 2
                self.c.setFillColor(C_MID)
                self.c.circle(cx - w/2 - 6, FOOTER_Y + 2, 1, fill=1, stroke=0)
                self.c.circle(cx + w/2 + 6, FOOTER_Y + 2, 1, fill=1, stroke=0)
        elif pos == 'bottom_outside':
            if self.page_num % 2 == 0:
                self.c.drawString(l, FOOTER_Y, str(self.page_num))
            else:
                self.c.drawRightString(PAGE_W - r, FOOTER_Y, str(self.page_num))
        elif pos == 'top_outside':
            hdr_style = tpl.get('header_style', 'centered')
            y_pos = HEADER_Y if hdr_style == 'none' else FOOTER_Y
            if self.page_num % 2 == 0:
                self.c.drawString(l, y_pos, str(self.page_num))
            else:
                self.c.drawRightString(PAGE_W - r, y_pos, str(self.page_num))
        else:
            self.c.drawCentredString(PAGE_W/2, FOOTER_Y, str(self.page_num))
    
        def _new_page(self, suppress=False):
        if self.page_num > 0:
            self.c.showPage()
        self.page_num += 1
        self.suppress_hdr = suppress
        self.current_y = PAGE_H - MARGIN_TOP - 10
    
    def _finish_page(self):
        self._draw_header()
        self._draw_folio()
    
    def _ensure_recto(self):
        """Finish current page and ensure next is recto (odd)."""
        self._finish_page()
        if self.page_num % 2 == 0:  # on verso, add blank recto? No â need blank verso
            # Actually: if on even page (verso), next page is odd (recto) â good
            pass
        else:
            # On odd (recto), need to add a blank verso first
            self._new_page(suppress=True)
            self._draw_folio()
            self._finish_page()
        self._new_page(suppress=True)
    
    def _ctxt(self, y, text, font, sz, color=C_BODY):
        self.c.setFont(font, sz)
        self.c.setFillColor(color)
        self.c.drawCentredString(PAGE_W/2, y, text)

    def _ctxt_block(self, y, text, font, sz, color=C_BODY):
        """Center text within the text block (accounts for gutter/inside-outside margins)."""
        self.c.setFont(font, sz)
        self.c.setFillColor(color)
        self.c.drawCentredString(self._lm() + self._tw() / 2, y, text)
    
    def _ornament(self, y, sz=18, color=C_BROWN):
        """Draw a decorative ornament: short rules flanking a filled diamond."""
        cx = self._lm() + self._tw() / 2
        self.c.setStrokeColor(color)
        self.c.setFillColor(color)
        self.c.setLineWidth(0.5)
        self.c.line(cx - 35, y, cx - 8, y)
        self.c.line(cx + 8, y, cx + 35, y)
        self.c.saveState()
        self.c.translate(cx, y)
        self.c.rotate(45)
        self.c.rect(-3, -3, 6, 6, fill=1, stroke=0)
        self.c.restoreState()
    
    def _divider(self, y, style='end'):
        """Draw a divider: short rules flanking a filled circle."""
        cx = self._lm() + self._tw() / 2
        self.c.setStrokeColor(C_BROWN)
        self.c.setFillColor(C_BROWN)
        self.c.setLineWidth(0.5)
        self.c.line(cx - 30, y, cx - 5, y)
        self.c.line(cx + 5, y, cx + 30, y)
        self.c.circle(cx, y, 2, fill=1, stroke=0)
    
    def _dot_sep(self, y):
        """Draw three small filled circles as a section separator."""
        cx = self._lm() + self._tw() / 2
        self.c.setFillColor(C_MID)
        for dx in (-12, 0, 12):
            self.c.circle(cx + dx, y, 1.5, fill=1, stroke=0)
        return y - 8
    
    def _wrap(self, text, font, sz, max_w):
        self.c.setFont(font, sz)
        words = text.split()
        lines = []
        cur = ''
        for w in words:
            clean_w = w.replace(SOFT_HYPHEN, '')
            clean_cur = cur.replace(SOFT_HYPHEN, '')
            test = f'{clean_cur} {clean_w}'.strip()
            if self.c.stringWidth(test, font, sz) <= max_w:
                cur = test
            else:
                if clean_cur:
                    lines.append(clean_cur)
                    cur = ''
                if SOFT_HYPHEN in w and HYPHENATE:
                    cur = self._fit_hyphenated(w, font, sz, max_w, lines)
                else:
                    cur = clean_w
        if cur:
            lines.append(cur.replace(SOFT_HYPHEN, ''))
        return lines or ['']
    
    def _fit_hyphenated(self, word, font, sz, max_w, lines):
        """Try to fit a word by breaking at soft hyphens."""
        parts = word.split(SOFT_HYPHEN)
        fitted = ''
        for i, part in enumerate(parts):
            candidate = fitted + part
            if i < len(parts) - 1:
                width = self.c.stringWidth(candidate + '-', font, sz)
            else:
                width = self.c.stringWidth(candidate, font, sz)
            if width <= max_w:
                fitted = candidate
            else:
                if fitted:
                    lines.append(fitted + '-')
                    return SOFT_HYPHEN.join(parts[i:])
                else:
                    return word.replace(SOFT_HYPHEN, '')
        return fitted
    
    def _check_page(self, needed=20):
        """If not enough room, finish page and start new one."""
        if self.current_y < MARGIN_BOTTOM + needed:
            self._finish_page()
            self._new_page()
            self.current_y = PAGE_H - MARGIN_TOP - 10
    
    def _draw_para(self, text, centered=False, font=None, sz=None, 
                   leading=None, color=C_BODY, indent=0, align=None):
        """Draw a wrapped paragraph. Updates self.current_y."""
        tpl = getattr(self, 'tpl', {})
        if font is None:
            font = tpl.get('body_font', 'Gar')
        if sz is None:
            sz = tpl.get('body_size', BODY_SZ)
        if leading is None:
            leading = tpl.get('leading', BODY_LD)
        if align is None:
            align = 'center' if centered else tpl.get('text_alignment', TEXT_ALIGNMENT)
        if indent == 0 and tpl.get('first_line_indent', 0):
            indent = tpl.get('first_line_indent', 0)
        # Strip remaining markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = text.replace('\\"', '"').replace("\\'", "'")
        
        # Apply hyphenation for justified text
        if align == 'justified' and HYPHENATE:
            text = add_soft_hyphens(text, HYPHEN_LANGUAGE)
        
        # Word-wrap using the NARROWER margin to be safe across page breaks
        min_tw = PAGE_W - MARGIN_INSIDE - MARGIN_OUTSIDE
        lines = self._wrap(text, font, sz, min_tw - indent)
        
        for i, line_text in enumerate(lines):
            self._check_page()
            lm = self._lm() + indent
            self.c.setFont(font, sz)
            self.c.setFillColor(color)
            if align == 'center':
                self.c.drawCentredString(PAGE_W/2, self.current_y, line_text)
            elif align == 'right':
                line_w = self.c.stringWidth(line_text, font, sz)
                self.c.drawString(PAGE_W - MARGIN_OUTSIDE - line_w, self.current_y, line_text)
            elif align == 'justified' and i < len(lines) - 1:
                self._draw_justified_line(line_text, lm, self.current_y, font, sz, min_tw - indent)
            else:
                self.c.drawString(lm, self.current_y, line_text)
            self.current_y -= leading
        
        self.current_y -= 2 + getattr(self, 'tpl', {}).get('paragraph_spacing', 0)
    
    def _draw_justified_line(self, line_text, x, y, font, sz, max_w):
        """Draw a line justified to fill max_w (not the last line)."""
        words = line_text.split()
        if len(words) <= 1:
            self.c.drawString(x, y, line_text)
            return
        self.c.setFont(font, sz)
        total_words_w = sum(self.c.stringWidth(w, font, sz) for w in words)
        space_w = self.c.stringWidth(' ', font, sz)
        natural_w = total_words_w + space_w * (len(words) - 1)
        extra = max_w - natural_w
        if extra <= 0:
            self.c.drawString(x, y, line_text)
            return
        gap = space_w + extra / (len(words) - 1)
        cur_x = x
        for w in words:
            self.c.drawString(cur_x, y, w)
            cur_x += self.c.stringWidth(w, font, sz) + gap
    
    def _draw_image(self, caption, img_path, size_hint='full'):
        """Render an image with caption. Supports six placement modes:
        full    â spans text width, inline in flow (default)
        half    â half text width, centred, inline
        quarter â quarter text width, centred, inline
        page    â full page, no header/folio, caption overlaid at bottom
        bleed   â edge-to-edge, no margins/header/folio
        facing  â full page on next recto/verso to face the text
        """
        # Resolve path
        full_path = os.path.join(self.image_base_dir, img_path) if self.image_base_dir else img_path
        
        # Check file exists
        if not os.path.exists(full_path):
            self._check_page(30)
            lm = self._lm()
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(HexColor('#CC0000'))
            self.c.drawString(lm, self.current_y, f'[IMAGE NOT FOUND: {img_path}]')
            self.current_y -= BODY_LD
            self.image_log.append((img_path, self.page_num, size_hint, 0, 'NOT FOUND'))
            return
        
        # Check format
        ext = os.path.splitext(full_path)[1].lower()
        if ext not in SUPPORTED_IMG:
            self._check_page(30)
            lm = self._lm()
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(HexColor('#CC0000'))
            self.c.drawString(lm, self.current_y, f'[UNSUPPORTED FORMAT: {img_path} â use JPG, PNG or TIFF]')
            self.current_y -= BODY_LD
            self.image_log.append((img_path, self.page_num, size_hint, 0, 'UNSUPPORTED'))
            return
        
        # Read image dimensions
        try:
            img_reader = ImageReader(full_path)
            native_w, native_h = img_reader.getSize()
        except Exception as e:
            self._check_page(30)
            lm = self._lm()
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(HexColor('#CC0000'))
            self.c.drawString(lm, self.current_y, f'[IMAGE ERROR: {img_path} â {str(e)}]')
            self.current_y -= BODY_LD
            self.image_log.append((img_path, self.page_num, size_hint, 0, 'ERROR'))
            return
        
        # ââ FULL PAGE mode ââ
        if size_hint == 'page':
            self._draw_image_page(full_path, caption, native_w, native_h, bleed=False)
            return
        
        # ââ BLEED mode (edge to edge, no margins) ââ
        if size_hint == 'bleed':
            self._draw_image_page(full_path, caption, native_w, native_h, bleed=True)
            return
        
        # ââ FACING mode (full page on facing page) ââ
        if size_hint == 'facing':
            self._draw_image_facing(full_path, caption, native_w, native_h)
            return
        
        # ââ INLINE modes (full, half, quarter) ââ
        tw = self._tw()
        text_height = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM
        
        if size_hint == 'half':
            target_w = tw / 2
        elif size_hint == 'quarter':
            target_w = tw / 4
        else:  # full
            target_w = tw
        
        # Scale maintaining aspect ratio
        scale = target_w / native_w
        render_w = target_w
        render_h = native_h * scale
        
        # Height cap at 60% of text block
        max_h = text_height * IMG_HEIGHT_CAP
        if render_h > max_h:
            render_h = max_h
            render_w = native_w * (max_h / native_h)
        
        # DPI check
        render_w_inches = render_w / 72
        effective_dpi = native_w / render_w_inches if render_w_inches > 0 else 0
        dpi_status = 'OK'
        if effective_dpi < 200:
            dpi_status = 'LOW RES'
            print(f"WARNING: {img_path} will print at {effective_dpi:.0f} DPI â minimum recommended is 300 DPI")
        
        # Calculate caption height
        caption_sz = BODY_SZ - CAPTION_SZ_OFFSET
        caption_lines = self._wrap(caption, 'GarI', caption_sz, render_w) if caption else []
        caption_height = len(caption_lines) * (caption_sz + 2) + CAPTION_GAP if caption_lines else 0
        
        # Total space needed
        total_needed = IMG_SPACING + render_h + caption_height + IMG_SPACING
        
        # Check if it fits on current page
        if self.current_y - total_needed < MARGIN_BOTTOM:
            self._finish_page()
            self._new_page()
            self.current_y = PAGE_H - MARGIN_TOP - 10
        
        # Top spacing
        self.current_y -= IMG_SPACING
        
        # Draw image centred
        lm = self._lm()
        img_x = lm + (tw - render_w) / 2
        img_y = self.current_y - render_h
        
        self.c.drawImage(full_path, img_x, img_y, render_w, render_h,
                        preserveAspectRatio=True, anchor='c')
        self.current_y = img_y
        
        # Draw caption
        if caption_lines:
            self.current_y -= CAPTION_GAP
            self.c.setFont('GarI', caption_sz)
            self.c.setFillColor(C_CAPTION)
            cap_x = lm + (tw - render_w) / 2 + render_w / 2
            for cap_line in caption_lines:
                self.c.drawCentredString(cap_x, self.current_y, cap_line)
                self.current_y -= (caption_sz + 2)
        
        # Bottom spacing
        self.current_y -= IMG_SPACING
        
        self.image_log.append((img_path, self.page_num, size_hint,
                              round(effective_dpi), dpi_status))
    
    def _draw_image_page(self, full_path, caption, native_w, native_h, bleed=False):
        """Render a full-page image. No running header, no folio.
        If bleed=True, image extends to page edges (trimmed at TrimBox).
        If bleed=False, image fills within margins."""
        
        # Finish current page if we have content on it
        if self.current_y < PAGE_H - MARGIN_TOP - 20:
            self._finish_page()
        else:
            # We're at the top of a fresh page already â just need to
            # suppress the header that _finish_page would draw
            pass
        
        # Start a dedicated image page â suppress header and folio
        self._new_page(suppress=True)
        self._suppress_folio_this_page = True
        
        if bleed:
            # Edge to edge â fill entire page
            target_w = PAGE_W
            target_h = PAGE_H
        else:
            # Within margins
            target_w = self._tw()
            target_h = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM
        
        # Scale to cover the target area (cover fit, may crop)
        scale_w = target_w / native_w
        scale_h = target_h / native_h
        scale = max(scale_w, scale_h)  # cover fit
        render_w = native_w * scale
        render_h = native_h * scale
        
        # Centre the image
        if bleed:
            img_x = (PAGE_W - render_w) / 2
            img_y = (PAGE_H - render_h) / 2
        else:
            lm = self._lm()
            tw = self._tw()
            img_x = lm + (tw - render_w) / 2
            img_y = MARGIN_BOTTOM + (target_h - render_h) / 2
        
        # Clip to target area and draw image
        self.c.saveState()
        if bleed:
            p = self.c.beginPath()
            p.rect(0, 0, PAGE_W, PAGE_H)
            self.c.clipPath(p, stroke=0, fill=0)
        else:
            lm = self._lm()
            p = self.c.beginPath()
            p.rect(lm, MARGIN_BOTTOM, self._tw(), target_h)
            self.c.clipPath(p, stroke=0, fill=0)
        
        self.c.drawImage(full_path, img_x, img_y, render_w, render_h,
                        preserveAspectRatio=False)
        self.c.restoreState()
        
        # Caption overlay at bottom (semi-transparent background)
        if caption:
            caption_sz = BODY_SZ - CAPTION_SZ_OFFSET
            cap_lines = self._wrap(caption, 'GarI', caption_sz, self._tw() * 0.8)
            if cap_lines:
                cap_h = len(cap_lines) * (caption_sz + 3) + 12
                cap_y_start = MARGIN_BOTTOM + 15 if not bleed else 20
                
                # Semi-transparent background for readability
                self.c.setFillColor(HexColor('#00000080'))
                bg_x = PAGE_W / 2 - self._tw() * 0.42
                self.c.rect(bg_x, cap_y_start - 4, self._tw() * 0.84, cap_h,
                           stroke=0, fill=1)
                
                self.c.setFont('GarI', caption_sz)
                self.c.setFillColor(HexColor('#FFFFFF'))
                cy = cap_y_start + cap_h - (caption_sz + 3) - 4
                for cap_line in cap_lines:
                    self.c.drawCentredString(PAGE_W / 2, cy, cap_line)
                    cy -= (caption_sz + 3)
        
        # DPI check
        render_w_inches = render_w / 72
        effective_dpi = native_w / render_w_inches if render_w_inches > 0 else 0
        dpi_status = 'OK'
        if effective_dpi < 200:
            dpi_status = 'LOW RES'
            print(f"WARNING: {os.path.basename(full_path)} will print at {effective_dpi:.0f} DPI")
        
        mode_str = 'bleed' if bleed else 'page'
        self.image_log.append((os.path.basename(full_path), self.page_num,
                              mode_str, round(effective_dpi), dpi_status))
        
        # This image page is complete â start a fresh page for following text
        # (no header/folio on the image page since suppress_hdr is True
        # and _suppress_folio_this_page is True)
        self._finish_page()
        self._new_page()
        self.current_y = PAGE_H - MARGIN_TOP - 10
    
    def _draw_image_facing(self, full_path, caption, native_w, native_h):
        """Place a full-page image on the next page so it faces the current text.
        The image goes on the next verso (left page) if we're on a recto,
        or next recto (right page) if we're on a verso, so it faces the text."""
        
        # Finish the current text page
        self._finish_page()
        
        # If we're on a recto (odd), the facing page is the next verso (even)
        # If we're on a verso (even), we need to add a blank recto first,
        # then the image goes on the following verso
        if self.page_num % 2 == 0:
            # Currently on verso â add blank recto, then image on next verso
            self._new_page(suppress=True)
            self._draw_folio()
            self._finish_page()
        
        # Now render the image as a full page
        self._draw_image_page(full_path, caption, native_w, native_h, bleed=False)
    
    def _draw_drop_cap(self, text, cap_lines=3):
        """Render the first letter of text as a drop cap spanning cap_lines lines.
        Used for children's book and novel chapter openers."""
        if not text or len(text) < 2:
            self._draw_para(text)
            return
        
        # Strip markdown
        clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        clean = re.sub(r'\*([^*]+)\*', r'\1', clean)
        clean = clean.replace('\\"', '"').replace("\\'", "'")
        
        if not clean:
            return
        
        self._check_page(60)
        
        first_char = clean[0]
        rest_text = clean[1:].strip()
        
        lm = self._lm()
        tw = self._tw()
        
        # Drop cap sizing: spans cap_lines of body text
        drop_sz = BODY_SZ * cap_lines * 0.85
        drop_leading = BODY_LD * cap_lines
        
        # Measure the drop cap width
        self.c.setFont('GarB', drop_sz)
        drop_w = self.c.stringWidth(first_char, 'GarB', drop_sz) + 4  # 4pt gap
        
        # Draw the drop cap
        drop_y = self.current_y - (drop_sz * 0.72)  # baseline offset
        self.c.setFillColor(C_BROWN)
        self.c.drawString(lm, drop_y, first_char)
        
        # Draw the first few lines of text indented around the drop cap
        indent_tw = tw - drop_w
        indent_lm = lm + drop_w
        
        # Wrap text for the indented region
        min_tw_safe = PAGE_W - MARGIN_INSIDE - MARGIN_OUTSIDE
        indent_lines = self._wrap(rest_text, 'Gar', BODY_SZ, 
                                  min(indent_tw, min_tw_safe - drop_w))
        
        # Draw lines next to the drop cap
        lines_beside = min(cap_lines, len(indent_lines))
        for j in range(lines_beside):
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(C_BODY)
            self.c.drawString(indent_lm, self.current_y, indent_lines[j])
            self.current_y -= BODY_LD
        
        # Remaining lines at full width
        for j in range(lines_beside, len(indent_lines)):
            self._check_page()
            lm = self._lm()
            self.c.setFont('Gar', BODY_SZ)
            self.c.setFillColor(C_BODY)
            self.c.drawString(lm, self.current_y, indent_lines[j])
            self.current_y -= BODY_LD
        
        self.current_y -= 2
    
    def _draw_content(self, text):
        """Route content: render as image if it's an image reference, otherwise as paragraph."""
        m = IMAGE_PATTERN.match(text.strip())
        if m:
            caption = m.group(1)
            img_path = m.group(2)
            size_hint = m.group(3) or 'full'
            self._draw_image(caption, img_path, size_hint)
        else:
            self._draw_para(text)
    
    # âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    # PAGE TYPES
    # âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    
    def render_title(self):
        self._new_page(suppress=True)
        y = PAGE_H - 2.2*inch
        self._ctxt(y, 'FROM THESE', 'GarB', 42, C_BODY); y -= 50
        self._ctxt(y, 'STREETS', 'GarB', 42, C_BODY); y -= 40
        self._divider(y, 'star'); y -= 30
        self._ctxt(y, 'Salfordians who Changed the World', 'GarI', 14, C_BROWN); y -= 30
        self._divider(y, 'star'); y -= 50
        self._ctxt(y, 'David Oldham', 'GarI', 12, C_DARK); y -= 40
        self._ctxt(y, 'published by:', 'Gar', 9, C_DARK); y -= 18
        self._ctxt(y, 'D&H Publishing International', 'Gar', 11, C_BODY); y -= 35
        self._ornament(y)
        self._finish_page()
    
    def render_copyright(self, lines):
        self._new_page(suppress=True)
        y = PAGE_H - 2.0*inch
        self._ctxt(y, 'FROM THESE STREETS', 'GarB', 14, C_BODY); y -= 20
        self._ctxt(y, 'Salfordians who Changed the World', 'GarI', 11, C_BROWN); y -= 30
        
        # Join the copyright lines into paragraphs
        paras = join_paragraphs(lines)
        lm = self._lm()
        tw = self._tw()
        
        for para in paras:
            para = para.strip()
            if not para:
                continue
            # Clean markdown artifacts
            para = re.sub(r'\*([^*]+)\*', r'\1', para)
            para = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', para)
            
            centered_markers = ['Paperback', 'www.']
            is_centered = any(m in para for m in centered_markers)
            
            wrapped = self._wrap(para, 'Gar', 9.5, tw)
            for wl in wrapped:
                if y < MARGIN_BOTTOM + 30:
                    break
                self.c.setFont('Gar', 9.5)
                self.c.setFillColor(C_BODY)
                if is_centered:
                    self.c.drawCentredString(PAGE_W/2, y, wl)
                else:
                    self.c.drawString(lm, y, wl)
                y -= 13
            y -= 5
        
        y -= 10
        self._ornament(y)
        self._finish_page()
    
    def render_dedication(self):
        self._ensure_recto()
        y = PAGE_H/2 + 30
        self.c.setFont('GarI', 12)
        self.c.setFillColor(C_DARK)
        self.c.drawCentredString(PAGE_W/2, y, '"For anyone who\'s ever said:')
        y -= 18
        self.c.drawCentredString(PAGE_W/2, y, 'I\'m not from Manchester, I\'m from Salford."')
        self._finish_page()
    
    def render_note(self, paras):
        self._ensure_recto()
        self.current_y = PAGE_H - MARGIN_TOP - 40
        self._ctxt(self.current_y, 'A Note on Inclusion', 'GarB', 14, C_BODY)
        self.current_y -= 28
        for para in paras:
            self._draw_para(para, align='left')
        self._finish_page()
    
    def render_toc(self, entries):
        self._ensure_recto()
        self.current_y = PAGE_H - MARGIN_TOP - 30
        self._ctxt(self.current_y, self.toc_title, 'GarB', 22, C_BODY)
        self.current_y -= 40

        lm = self._lm()
        tw = self._tw()

        # Reserve space for page number on the right (e.g. "210" max width)
        pg_num_reserve = 28  # points â enough for a 3-digit page number
        title_max_w = tw - pg_num_reserve - 12  # 12pt gap between title and leaders

        for title, page, level in entries:
            if level == 0:
                font, sz = 'GarB', 11
                indent = 0
                line_h = 16
                pre_gap = 6
            else:
                font, sz = 'Gar', 10
                indent = 18
                line_h = 14
                pre_gap = 0

            self.c.setFont(font, sz)

            pg_str = str(page)
            x_start = lm + indent
            x_end = lm + tw

            # Wrap title into lines that fit within title_max_w
            max_title_w = title_max_w - indent
            words = title.split()
            wrapped_lines = []
            current_line = ''
            for word in words:
                test = (current_line + ' ' + word).strip()
                if self.c.stringWidth(test, font, sz) <= max_title_w:
                    current_line = test
                else:
                    if current_line:
                        wrapped_lines.append(current_line)
                    current_line = word
            if current_line:
                wrapped_lines.append(current_line)
            if not wrapped_lines:
                wrapped_lines = [title]

            total_h = len(wrapped_lines) * line_h + pre_gap + 2
            self._check_page(total_h + 10)

            self.current_y -= pre_gap
            self.c.setFillColor(C_BODY)

            # Draw all lines except the last
            for line in wrapped_lines[:-1]:
                self.c.drawString(x_start, self.current_y, line)
                self.current_y -= line_h

            # Last line: draw title text, dot leaders, and page number on same baseline
            last_line = wrapped_lines[-1]
            self.c.setFont(font, sz)
            self.c.setFillColor(C_BODY)
            self.c.drawString(x_start, self.current_y, last_line)
            self.c.drawRightString(x_end, self.current_y, pg_str)

            # Dot leaders on last line
            last_w = self.c.stringWidth(last_line, font, sz)
            pg_w = self.c.stringWidth(pg_str, font, sz)
            dot_s = x_start + last_w + 6
            dot_e = x_end - pg_w - 6
            if dot_e > dot_s + 10:
                self.c.setFont('Gar', sz)
                self.c.setFillColor(C_GREY)
                dot_w = self.c.stringWidth('.', 'Gar', sz) + 1
                x = dot_s
                while x + dot_w <= dot_e:
                    self.c.drawString(x, self.current_y, '.')
                    x += dot_w

            self.current_y -= line_h + 2

        self.current_y -= 20
        self._ornament(self.current_y)
        self._finish_page()
    
    def render_chapter_opener(self, title, subtitle=''):
        """Start chapter on recto page, return with current_y set."""
        tpl = getattr(self, 'tpl', {})
        self._ensure_recto()
        self.is_front_matter = False
        
        self.chapter_count = getattr(self, 'chapter_count', 0) + 1
        self.current_chapter_title = title
        
        offset = tpl.get('chapter_start_offset', 80)
        self.current_y = PAGE_H - MARGIN_TOP - offset
        
        tw = self._tw()
        cx = self._lm() + tw / 2
        
        # Chapter number
        num_style = tpl.get('chapter_number_style', 'none')
        num_text = format_chapter_number(self.chapter_count, num_style)
        if num_text:
            num_font = tpl.get('heading_font', 'GarB')
            if num_style == 'large_sans_topleft':
                num_sz = tpl.get('chapter_title_size', 48)
                self.c.setFont(num_font, num_sz)
                self.c.setFillColor(C_BODY)
                self.c.drawString(self._lm(), self.current_y, num_text)
                self.current_y -= num_sz + 16
            elif num_style == 'smallcaps_spaced':
                self._ctxt(self.current_y, num_text, num_font, 11, C_BROWN)
                self.current_y -= 20
            elif num_style == 'italic_centered':
                self._ctxt(self.current_y, num_text, 'GarI', 16, C_BROWN)
                self.current_y -= 24
            elif num_style == 'sans_medium':
                self.c.setFont('SansB', 11)
                self.c.setFillColor(C_MID)
                self.c.drawString(self._lm(), self.current_y, num_text)
                self.current_y -= 22
            elif num_style == 'large_centered':
                self._ctxt(self.current_y, num_text, 'GarB', 26, C_BROWN)
                self.current_y -= 34
            elif num_style == 'centered_caps':
                self._ctxt(self.current_y, num_text, 'MonoB', 14, C_BODY)
                self.current_y -= 26
        
        # Chapter title
        title_pos = tpl.get('chapter_title_position', 'centered')
        title_font = tpl.get('chapter_title_font', 'GarB')
        title_sz = tpl.get('chapter_title_size', CH_TITLE_SZ)
        
        if title_pos != 'none' and title:
            if title_pos == 'centered_caps_spaced':
                title_text = ' '.join(title.upper())
            else:
                title_text = title
            
            title_w = self.c.stringWidth(title_text, title_font, title_sz)
            
            if title_w > tw:
                words = title_text.split()
                mid = len(words) // 2
                l1 = ' '.join(words[:mid])
                l2 = ' '.join(words[mid:])
                if title_pos in ('left', 'left_below'):
                    self.c.setFont(title_font, title_sz)
                    self.c.setFillColor(C_BODY)
                    self.c.drawString(self._lm(), self.current_y, l1)
                    self.current_y -= title_sz + 4
                    self.c.drawString(self._lm(), self.current_y, l2)
                    self.current_y -= title_sz + 8
                else:
                    self._ctxt(self.current_y, l1, title_font, title_sz, C_BODY)
                    self.current_y -= 28
                    self._ctxt(self.current_y, l2, title_font, title_sz, C_BODY)
                    self.current_y -= 25
            else:
                if title_pos in ('left', 'left_below'):
                    self.c.setFont(title_font, title_sz)
                    self.c.setFillColor(C_BODY)
                    self.c.drawString(self._lm(), self.current_y, title_text)
                    self.current_y -= title_sz + 12
                else:
                    self._ctxt(self.current_y, title_text, title_font, title_sz, C_BODY)
                    self.current_y -= 25
        
        # Subtitle
        if subtitle and title_pos != 'none':
            sub_w = self.c.stringWidth(subtitle, 'GarI', CH_SUB_SZ)
            if sub_w > tw:
                sub_lines = self._wrap(subtitle, 'GarI', CH_SUB_SZ, tw)
                for sl in sub_lines:
                    self._ctxt(self.current_y, sl, 'GarI', CH_SUB_SZ, C_BROWN)
                    self.current_y -= 18
                self.current_y -= 12
            else:
                self._ctxt(self.current_y, subtitle, 'GarI', CH_SUB_SZ, C_BROWN)
                self.current_y -= 30
        else:
            self.current_y -= 10
        
        # Ornament below title
        ornament_style = tpl.get('ornament_below_title', 'rule')
        if ornament_style and ornament_style != 'none':
            draw_ornament(self.c, self.current_y, cx, ornament_style, C_BROWN)
            self.current_y -= 30
        
        # Drop cap flag for first paragraph
        self._drop_cap_style = tpl.get('drop_cap', 'none')
    
        def render_chapter_end(self):
        self._check_page(50)
        self.current_y -= 15
        tpl = getattr(self, 'tpl', {})
        ornament = tpl.get('chapter_end_ornament', getattr(self, 'chapter_end_ornament', 'fleuron'))
        if ornament == 'none' or not ornament:
            pass
        elif ornament == 'divider':
            self._divider(self.current_y)
        else:
            cx = self._lm() + self._tw() / 2
            draw_ornament(self.c, self.current_y, cx, ornament, C_BROWN)
        self._finish_page()
    
        def render_profile(self, name, tagline, body, is_first=False):
        if not is_first:
            self._check_page(80)
            self._dot_sep(self.current_y)
            self.current_y -= 22
        
        self._check_page(60)
        
        # Name
        lm = self._lm()
        self.c.setFont('GarB', PROF_NAME_SZ)
        self.c.setFillColor(C_BODY)
        self.c.drawString(lm, self.current_y, name)
        self.current_y -= 18
        
        # Tagline
        if tagline:
            tag = tagline.replace('--', '\u2013')
            self.c.setFont('GarI', PROF_TAG_SZ)
            self.c.setFillColor(C_MID)
            self.c.drawString(lm, self.current_y, tag)
            self.current_y -= 20
        else:
            self.current_y -= 6
        
        # Body
        for para in body:
            self._draw_content(para)
    
    def render_also_available(self):
        """Also available page â nod to Not Manchester."""
        self._ensure_recto()
        y = PAGE_H / 2 + 80
        
        self._ctxt(y, 'Also available from', 'Gar', 10, C_DARK)
        y -= 16
        self._ctxt(y, 'D&H Publishing International', 'GarI', 11, C_DARK)
        y -= 35
        
        # Decorative rule above title
        cx = PAGE_W / 2
        self.c.setStrokeColor(C_BROWN)
        self.c.setLineWidth(0.5)
        self.c.line(cx - 60, y, cx + 60, y)
        y -= 30
        
        self._ctxt(y, 'NOT MANCHESTER', 'GarB', 20, C_BODY)
        y -= 26
        self._ctxt(y, 'The Proud Story of Salford', 'GarI', 13, C_BROWN)
        y -= 30
        
        # Rule below
        self.c.setStrokeColor(C_BROWN)
        self.c.setLineWidth(0.5)
        self.c.line(cx - 60, y, cx + 60, y)
        y -= 28
        
        self._ctxt(y, 'David Oldham', 'GarI', 11, C_DARK)
        y -= 35
        
        self._ctxt(y, 'www.dandhpublishing.com', 'Gar', 9.5, C_GREY)
        y -= 30
        
        self._ornament(y)
        self._finish_page()
    
    def render_back_page(self):
        self._ensure_recto()
        y = PAGE_H/2 + 20
        self._ctxt(y, 'www.dandhpublishing.com', 'GarB', 13, C_BODY); y -= 22
        self._ctxt(y, 'Salfordians who Changed the World', 'GarI', 11, C_DARK); y -= 30
        self._divider(y, 'star'); y -= 25
        self._ctxt(y, 'D&H Publishing International', 'Gar', 10, C_DARK); y -= 18
        self.c.setFont('Gar', 8.5)
        self.c.setFillColor(C_GREY)
        self.c.drawCentredString(PAGE_W/2, y, '\u00a9 2026 David Oldham. All rights reserved.')
        self._finish_page()


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# TWO-PASS BUILDER
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

class BookBuilder:
    def __init__(self, md_path, output_path, language='en_GB'):
        self.md_path = md_path
        self.output_path = output_path
        self.language = language
        self.toc_title = get_toc_title(language)
        self.blocks = parse_manuscript(md_path)
        for _blk in self.blocks:
            if 'body' in _blk:
                for _item in _blk['body']:
                    if _item.get('type') == 'para':
                        _item['text'] = convert_quotation_marks(_item['text'], language)
            elif _blk.get('type') == 'para':
                _blk['text'] = convert_quotation_marks(_blk['text'], language)
        # Image base directory: same folder as the manuscript
        self.image_base_dir = os.path.dirname(os.path.abspath(md_path))
    
    def _render(self, path, toc_entries=None):
        r = BookRenderer(path)
        r.image_base_dir = self.image_base_dir
        r.header_text = 'FROM THESE STREETS \u2013 Salfordians who Changed the World'
        r.toc_title = self.toc_title
        first_in_ch = True
        
        for i, blk in enumerate(self.blocks):
            t = blk['type']
            
            if t == 'title_page':
                r.render_title()
            elif t == 'copyright_page':
                # blank verso
                r._new_page(suppress=True)
                r._finish_page()
                r.render_copyright(blk['lines'])
            elif t == 'dedication_page':
                r.render_dedication()
            elif t == 'note_on_inclusion':
                r.render_note(blk['paras'])
            elif t == 'toc':
                if toc_entries:
                    r.render_toc(toc_entries)
                else:
                    # Placeholder pages
                    r._ensure_recto()
                    r._ctxt(PAGE_H - MARGIN_TOP - 30, r.toc_title, 'GarB', 22, C_BODY)
                    r._finish_page()
                    r._new_page(suppress=True)
                    r._finish_page()
            elif t in ('chapter', 'afterword'):
                r.toc_entries.append((blk['title'], r.page_num + 1, 0))
                r.render_chapter_opener(blk['title'], blk.get('subtitle', ''))
                first_in_ch = True
                for para in blk.get('intro', []):
                    r._draw_content(para)
                if t == 'afterword':
                    r.render_chapter_end()
            elif t == 'profile':
                r.toc_entries.append((blk['name'], r.page_num, 1))
                r.render_profile(blk['name'], blk.get('tagline',''),
                                blk.get('body',[]), is_first=first_in_ch)
                first_in_ch = False
                
                # Check if next block starts a new chapter or afterword
                if i+1 < len(self.blocks):
                    nt = self.blocks[i+1]['type']
                    if nt in ('chapter', 'afterword'):
                        r.render_chapter_end()
                elif i == len(self.blocks) - 1:
                    r.render_chapter_end()
        
        r.render_also_available()
        r.render_back_page()
        r.c.save()
        self._last_image_log = r.image_log
        return r.toc_entries
    
    def build(self):
        print("Pass 1: Collecting page numbers...")
        tmp = self.output_path.replace('.pdf', '_p1.pdf')
        toc = self._render(tmp)
        print(f"  {len(toc)} TOC entries, last page ~{toc[-1][1] if toc else '?'}")
        
        print("Pass 2: Final render with TOC...")
        self._render(self.output_path, toc)
        if os.path.exists(tmp):
            os.remove(tmp)
        
        # Set TrimBox
        self._set_trimbox()
        
        # Print image log
        if self._last_image_log:
            print(f"\nIMAGES")
            print(f"------")
            placed = 0
            warnings = 0
            errors = 0
            for fname, page, hint, dpi, status in self._last_image_log:
                if status == 'OK':
                    print(f"  {fname:40s} placed p.{page} ({hint} width, {dpi} DPI) â")
                    placed += 1
                elif status == 'LOW RES':
                    print(f"  {fname:40s} placed p.{page} ({hint} width, {dpi} DPI) â  LOW RES")
                    placed += 1
                    warnings += 1
                else:
                    print(f"  {fname:40s} {status} â")
                    errors += 1
            print(f"\n  Total images: {len(self._last_image_log)}")
            print(f"  Placed: {placed}")
            if warnings:
                print(f"  Warnings: {warnings} (low resolution)")
            if errors:
                print(f"  Errors: {errors}")
        
        print(f"\nDone: {self.output_path}")
    
    def _set_trimbox(self):
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, FloatObject, NameObject
        
        reader = PdfReader(self.output_path)
        writer = PdfWriter()
        for page in reader.pages:
            page[NameObject('/TrimBox')] = ArrayObject([
                FloatObject(0), FloatObject(0),
                FloatObject(PAGE_W), FloatObject(PAGE_H),
            ])
            writer.add_page(page)
        writer.add_metadata({
            '/Title': 'From These Streets \u2014 Salfordians who Changed the World',
            '/Author': 'David Oldham',
            '/Creator': 'Layout Perfect Typesetting Engine',
            '/Producer': 'ReportLab + pypdf',
        })
        with open(self.output_path, 'wb') as f:
            writer.write(f)


if __name__ == '__main__':
    builder = BookBuilder(
        '/mnt/user-data/uploads/From_These_Streets_-_Revised_Manuscript.md',
        '/mnt/user-data/outputs/From_These_Streets_PRINT.pdf'
    )
    builder.build()
