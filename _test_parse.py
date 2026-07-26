import re

token_pattern = re.compile(
    r'(\*\*[^*]+\*\*'           # **bold**
    r'|`[^`]+`'                  # `code`
    r'|(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)'  # $inline math$
    r')', re.DOTALL
)

def test_parse(line):
    parts = token_pattern.split(line)
    return parts

lines = [
    r"$\vec{a}(t) = \left( -\frac{1}{(t+2)^2}; 4 \right)$",
    r"$x'(t)$ và $y'(t)$",
    r"$S_1 = \sum_{n=1}^{\infty} \frac{(-1)^{kn}}{n}$ (với $k$ nguyên)",
    r"$S_2 = \sum_{n=1}^{\infty} \left(\frac{k}{8}\right)^n$",
    r"$k \in \{3, 5, 7\}$ (nếu $k$ nguyên)",
    r"$A = \frac{5}{2}$ hoặc $2.5$",
    r"$A = \frac{5}{2}$",
    r"$2.5$"
]

for l in lines:
    print(f"LINE: {l}")
    print(f"PARSED: {test_parse(l)}")
    print("-" * 40)
