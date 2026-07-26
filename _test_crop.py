import sys, re, io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

def _preprocess_latex(expr):
    expr = expr.replace(r'\1n', r'\ln')
    expr = re.sub(r'\\underbrace\{([^}]*)\}_\{[^}]*\}', r'\1', expr)
    expr = re.sub(r'\\underbrace\{([^}]*)\}', r'\1', expr)
    expr = re.sub(r'\\overbrace\{([^}]*)\}_\{[^}]*\}', r'\1', expr)
    expr = expr.replace(r'\implies', r'\Rightarrow')
    expr = expr.replace(r'\iff',     r'\Leftrightarrow')
    expr = re.sub(r'\\ge(?![a-zA-Z])', r'\\geq', expr)
    expr = re.sub(r'\\le(?![a-zA-Z])', r'\\leq', expr)
    expr = re.sub(r'\\ne(?![a-zA-Z])', r'\\neq', expr)
    def _replace_text(m):
        inner = m.group(1)
        if any(ord(c) > 127 for c in inner):
            return r'\;'
        return r'\mathrm{' + inner + '}'
    expr = re.sub(r'\\text\{([^}]*)\}', _replace_text, expr)
    expr = re.sub(r'\\label\{[^}]*\}', '', expr)
    expr = re.sub(r'\\tag\{[^}]*\}',   '', expr)
    expr = re.sub(r'\\nonumber',        '', expr)
    expr = re.sub(r'\\notag',           '', expr)
    return expr.strip()

def render_latex_image(latex_str, display=False):
    try:
        expr = _preprocess_latex(latex_str)
        if not expr: return "ERROR: empty expr"
        fontsize = 13 if display else 10
        dpi = 96
        bg_color = '#1e1e1e'
        bg_rgb = (30, 30, 30)
        fig, ax = plt.subplots(figsize=(20, 3))
        fig.patch.set_facecolor(bg_color)
        ax.set_axis_off()
        ax.set_facecolor(bg_color)
        ax.text(
            0.5, 0.5, f'${expr}$',
            fontsize=fontsize, color='#e8c77a',
            ha='center', va='center',
            transform=ax.transAxes, usetex=False
        )
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi,
                    facecolor=bg_color, edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        pil_img = Image.open(buf).convert('RGB')
        arr = np.array(pil_img)
        diff = (
            np.abs(arr[:,:,0].astype(int) - bg_rgb[0]) +
            np.abs(arr[:,:,1].astype(int) - bg_rgb[1]) +
            np.abs(arr[:,:,2].astype(int) - bg_rgb[2])
        )
        mask = diff > 8
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        if not rows.any():
            return "ERROR: cropped completely blank"
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        pad_px = 4 if display else 3
        h, w = arr.shape[:2]
        rmin = max(0, rmin - pad_px)
        rmax = min(h - 1, rmax + pad_px)
        cmin = max(0, cmin - pad_px)
        cmax = min(w - 1, cmax + pad_px)
        cropped = pil_img.crop((cmin, rmin, cmax + 1, rmax + 1))
        return f"OK: {cropped.size}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"

tests = [
    r"\vec{a}(t) = \left( -\frac{1}{(t+2)^2}; 4 \right)",
    r"x'(t)",
    r"y'(t)",
    r"S_1 = \sum_{n=1}^{\infty} \frac{(-1)^{kn}}{n}",
    r"S_2 = \sum_{n=1}^{\infty} \left(\frac{k}{8}\right)^n",
    r"k \in \{3, 5, 7\}",
    r"A = \sum_{n=1}^{\infty} \frac{2^n+1}{3^n}=\underbrace{\sum_{n=1}^{\infty} \left(\frac{2}{3}\right)^n}_{S_1} + \underbrace{\sum_{n=1}^{\infty} \left(\frac{1}{3}\right)^n}_{S_2}",
    r"A = \frac{5}{2}",
    r"2.5"
]

for t in tests:
    print(f"TEXT: {t[:60]}")
    print(f"RESULT: {render_latex_image(t)}")
    print("-" * 40)
