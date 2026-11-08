from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['FreeSerif', 'Liberation Serif', 'DejaVu Serif']})
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
OUT = Path(__file__).resolve().parents[1] / 'results'

def box(ax, x, y, text, color, width=1.65):
    patch = FancyBboxPatch((x, y), width, 0.72, boxstyle='round,pad=0.08,rounding_size=0.08', facecolor=color, edgecolor='none')
    ax.add_patch(patch)
    ax.text(x + width / 2, y + 0.36, text, ha='center', va='center', fontsize=11, color='white', weight='bold')

def arrow(ax, x1, y1, x2, y2, color='#333333'):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=14, linewidth=1.7, color=color))

def flow(filename, labels, colors, title, subtitle):
    fig, ax = plt.subplots(figsize=(11, 3.2))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 3.2)
    ax.axis('off')
    xs = [0.2, 2.35, 4.5, 6.65, 8.8]
    for x, label, color in zip(xs, labels, colors):
        box(ax, x, 1.25, label, color)
    for i in range(4):
        arrow(ax, xs[i] + 1.67, 1.61, xs[i + 1] - 0.05, 1.61)
    ax.text(5.5, 2.75, title, ha='center', fontsize=17, weight='bold', color='#111111')
    ax.text(5.5, 0.52, subtitle, ha='center', fontsize=10.5, color='#333333')
    fig.tight_layout()
    fig.savefig(OUT / filename, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)

def main():
    OUT.mkdir(exist_ok=True)
    flow('cipher_architecture.png', ['Plaintext\nA–Z', 'Stage I\nVigenère', 'Split into\nletter pairs', 'Stage II\n2×2 Hill', 'Ciphertext'], ['#5b5b5b', '#1f3a5f', '#7a7a7a', '#4f7cac', '#2b2b2b'], 'VHC encryption architecture', 'Keyword K (10+ letters) drives Stage I; an independent 4-letter Hill key gives an invertible matrix for Stage II. An odd final letter skips Hill. Decryption reverses the order.')
    flow('attack_pipeline.png', ['Ciphertext\npairs', 'Key length\nL = 10…20', 'IC ranks\nHill rows', 'χ² recovers\nshifts', 'Quadgram\nranking'], ['#2b2b2b', '#4f7cac', '#7a7a7a', '#1f3a5f', '#4d7c59'], 'Frequency-only attack pipeline', 'Each row of the inverse Hill matrix is found on its own (42 row groups, not 157,248 matrices); shifts per class come from chi-squared.')
if __name__ == '__main__':
    main()
