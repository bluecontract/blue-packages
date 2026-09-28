#!/usr/bin/env python3
"""Render the single normative Markdown document; not used in identity or admission."""
from pathlib import Path
from markdown_it import MarkdownIt
ROOT=Path(__file__).resolve().parents[1]
body=MarkdownIt('commonmark',{'html':True}).enable('table').render((ROOT/'SPECIFICATION.md').read_text())
css='''
:root{color-scheme:light;--ink:#172b3a;--muted:#536775;--line:#dce5eb;--accent:#076780}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#fff;color:var(--ink);font:16px/1.7 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{border-bottom:4px solid var(--accent);background:#f3f7f9;padding:28px max(24px,calc((100vw - 1080px)/2))}
header span{font-size:12px;font-weight:750;letter-spacing:.16em;color:var(--accent)}main{max-width:1080px;margin:0 auto;padding:36px 28px 100px}
h1{font-size:2.8rem;letter-spacing:-.045em;line-height:1.14;margin:.3em 0 .4em}h2{font-size:1.65rem;margin:2em 0 .6em;border-bottom:1px solid var(--line);padding-bottom:.4em;line-height:1.3}h3{font-size:1.16rem;margin:1.8em 0 .55em}h4{margin-top:1.5em}a{color:var(--accent);text-underline-offset:.16em}p{margin:.85em 0}blockquote{margin:1.3em 0;padding:.1em 1.2em;border-left:3px solid var(--accent);background:#f5f8fa}
code{font:13px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace}p code,li code,td code{background:#f0f4f7;border-radius:3px;padding:.1em .3em;overflow-wrap:anywhere}pre{font-size:13px;line-height:1.65;overflow-x:auto;background:#f4f7f9;border:1px solid var(--line);border-radius:4px;padding:18px 20px;tab-size:4}pre code{white-space:pre}table{width:100%;border-collapse:collapse;font-size:.9rem;line-height:1.6;margin:1.2em 0;display:block;overflow-x:auto}th,td{padding:10px 12px;border:1px solid var(--line);text-align:left;vertical-align:top}th{background:#edf3f6;font-weight:700}hr{border:0;border-top:1px solid var(--line);margin:2.5em 0}ul,ol{padding-left:1.5em}a[id]{scroll-margin-top:20px}
@media print{body{font-size:10pt}header{padding:16px}main{padding:8px;max-width:none}pre{white-space:pre-wrap}pre code{white-space:pre-wrap;overflow-wrap:anywhere}h2,h3{break-after:avoid}a{color:inherit}table{display:table}thead{display:table-header-group}}
'''
html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Blue Language 1.0 — Complete Specification</title><style>'+css+'</style></head><body><header><span>BLUE · LANGUAGE SPECIFICATION</span></header><main>'+body+'</main></body></html>\n'
(ROOT/'SPECIFICATION.html').write_text(html)
