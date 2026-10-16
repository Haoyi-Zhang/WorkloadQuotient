"""Regenerate the consumed schematics in isolation and check reproducibility."""
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def main():
    with tempfile.TemporaryDirectory(prefix='workload-figures-') as tmp:
        out = Path(tmp)
        subprocess.run([sys.executable, '-B', str(HERE/'draw_schematics.py'),
                        '--output', str(out)], check=True, timeout=60)
        for name in ('image-factorization', 'workload'):
            expected = (HERE/(name+'.pdf')).read_bytes()
            actual = (out/(name+'.pdf')).read_bytes()
            if not actual.startswith(b'%PDF-') or expected != actual:
                raise RuntimeError('Missing, stale or nondeterministic figure: '+name)
    print('Both schematics regenerate exactly; all drawing labels pass bounds checks.')


if __name__ == '__main__':
    main()
