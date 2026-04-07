from __future__ import annotations

import json
import re
import streamlit.components.v1 as components

from core.config import DATA_DIR

JSON_PATH = DATA_DIR / 'sigungu_paths.json'
SVG_WIDTH = 340
SVG_HEIGHT = 480
PADDING = 18


def parse_path_coords(path_str: str):
    nums = re.findall(r'[-+]?\d*\.?\d+', path_str)
    vals = list(map(float, nums))
    return [(vals[i], vals[i + 1]) for i in range(0, len(vals) - 1, 2)]


def extract_bounds(items):
    minx = miny = float('inf')
    maxx = maxy = float('-inf')
    for item in items:
        for x, y in parse_path_coords(item['path']):
            minx = min(minx, x)
            miny = min(miny, y)
            maxx = max(maxx, x)
            maxy = max(maxy, y)
    return minx, miny, maxx, maxy


def project_point(x, y, bounds, width, height, padding):
    minx, miny, maxx, maxy = bounds
    data_w = maxx - minx
    data_h = maxy - miny
    scale = min((width - padding * 2) / data_w, (height - padding * 2) / data_h)
    used_w = data_w * scale
    used_h = data_h * scale
    offset_x = (width - used_w) / 2
    offset_y = (height - used_h) / 2
    px = (x - minx) * scale + offset_x
    py = height - ((y - miny) * scale + offset_y)
    return px, py


def convert_path_to_svg(path_str, bounds, width, height, padding):
    tokens = re.findall(r'[MLZ]|[-+]?\d*\.?\d+', path_str)
    result = []
    i, cmd = 0, None
    while i < len(tokens):
        token = tokens[i]
        if token in ('M', 'L', 'Z'):
            cmd = token
            if cmd == 'Z':
                result.append('Z')
            i += 1
            continue
        if cmd not in ('M', 'L') or i + 1 >= len(tokens):
            i += 1
            continue
        x = float(tokens[i]); y = float(tokens[i + 1])
        px, py = project_point(x, y, bounds, width, height, padding)
        result.append(f'{cmd} {px:.2f},{py:.2f}')
        i += 2
        cmd = 'L'
    return ' '.join(result)


def render_map_from_json(json_path=None):
    target = json_path or JSON_PATH
    with open(target, 'r', encoding='utf-8') as f:
        data = json.load(f)
    bounds = extract_bounds(data)
    svg_items = [{'name': item['name'], 'path': convert_path_to_svg(item['path'], bounds, SVG_WIDTH, SVG_HEIGHT, PADDING)} for item in data]
    all_paths = ' '.join(item['path'] for item in svg_items)
    html = f'<svg viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" xmlns="http://www.w3.org/2000/svg"><path d="{all_paths}" fill="none" stroke="#94a3b8" stroke-width="0.8"/></svg>'
    components.html(html, height=520)
