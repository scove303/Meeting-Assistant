import sys, re, io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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

def render_latex_image(latex_str):
    try:
        expr = _preprocess_latex(latex_str)
        if not expr: return None
        fig, ax = plt.subplots(figsize=(20, 3))
        ax.text(0.5, 0.5, f'${expr}$', usetex=False)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        plt.close(fig)
        return "OK"
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
]

for t in tests:
    print(f"TEXT: {t}")
    print(f"RESULT: {render_latex_image(t)}")
    print("-" * 40)
