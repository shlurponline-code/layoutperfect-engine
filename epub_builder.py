#!/usr/bin/env python3
"""ePub builder for Layout Perfect typesetting engine."""

import re
from ebooklib import epub


def build_epub(md_path, output_path, title='Untitled', author='Unknown',
               publisher='D&H Publishing International', isbn='', language='en-GB',
               subtitle=''):
    """Build an ePub from a markdown manuscript."""
    from typeset_engine import parse_manuscript_generic

    book = epub.EpubBook()
    book.set_identifier(isbn or 'layoutperfect-' + title.replace(' ', '-').lower())
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)
    book.add_publisher(publisher)

    blocks = parse_manuscript_generic(md_path)

    # Title page
    title_html = '<h1>' + title + '</h1>'
    if subtitle:
        title_html += '<h2><em>' + subtitle + '</em></h2>'
    title_html += '<p style="text-align:center;margin-top:2em">' + author + '</p>'
    title_html += '<p style="text-align:center;font-size:0.9em;color:#666">' + publisher + '</p>'

    title_chapter = epub.EpubHtml(title='Title', file_name='title.xhtml', lang=language)
    title_chapter.content = title_html
    book.add_item(title_chapter)

    toc = []
    spine = [title_chapter]

    for i, blk in enumerate(blocks):
        if blk['type'] in ('part', 'chapter'):
            ch_title = blk['title']
            if blk.get('subtitle'):
                ch_title = blk['title'] + ': ' + blk['subtitle']

            ch_file = 'chapter_' + str(i + 1) + '.xhtml'
            ch = epub.EpubHtml(title=ch_title, file_name=ch_file, lang=language)

            html = ''
            if blk['type'] == 'part':
                html = '<h1 style="text-align:center;margin-top:3em">' + blk['title'] + '</h1>'
                if blk.get('subtitle'):
                    html += '<h2 style="text-align:center"><em>' + blk['subtitle'] + '</em></h2>'
            else:
                html = '<h1>' + blk['title'] + '</h1>'
                if blk.get('subtitle'):
                    html += '<h2><em>' + blk['subtitle'] + '</em></h2>'

                for item in blk.get('body', []):
                    if item['type'] == 'para':
                        text = item['text']
                        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
                        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
                        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
                        html += '<p>' + text + '</p>'
                    elif item['type'] == 'scene_break':
                        html += '<p style="text-align:center;margin:1em 0">&#8226; &#8226; &#8226;</p>'

            ch.content = html
            book.add_item(ch)
            spine.append(ch)
            if blk['type'] == 'chapter':
                toc.append(ch)

    book.toc = toc
    book.spine = spine

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(output_path, book, {})
    return output_path
