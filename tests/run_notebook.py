"""
通用 Jupyter Notebook 执行器。

用法:
    python run_notebook.py "[('path/to/nb.ipynb', 'workdir'), ...]"

特性:
    - 自动注入 IPython 兼容层（display, get_ipython, matplotlib Agg 后端）
    - 自动剥离 IPython magic 行（%pip, %matplotlib）
    - 逐 notebook 执行并报告 PASS/FAIL/TIMEOUT
"""
import json, subprocess, sys, os, time

PYTHON = sys.executable

SHIM = """# === IPython compatibility shim ===
import builtins
try:
    from IPython.display import display
except Exception:
    def display(*args, **kwargs):
        for a in args:
            print(a)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.show = lambda *a, **k: None
try:
    get_ipython
except NameError:
    def get_ipython():
        return None
# === End shim ===
"""

def extract_code(nb_path):
    """提取 notebook 中所有 code cell，剥离 IPython magic 行。"""
    with open(nb_path, encoding='utf-8') as f:
        nb = json.load(f)
    cells = []
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            src = ''.join(cell['source'])
            cleaned = '\n'.join(
                l for l in src.split('\n')
                if not l.strip().startswith('%') and not l.strip().startswith('!')
            )
            cells.append(cleaned)
    return SHIM + '\n\n'.join(cells)

def run_one(nb_path, workdir, timeout=480):
    """执行单个 notebook，返回 (name, status, elapsed, error)。"""
    nb_path = os.path.abspath(nb_path)
    workdir = os.path.abspath(workdir)
    name = os.path.basename(nb_path)
    t0 = time.time()
    tmp = None
    try:
        code = extract_code(nb_path)
        tmp = os.path.join(workdir, '_tmp_run.py')
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(code)
        r = subprocess.run(
            [PYTHON, '_tmp_run.py'],
            cwd=workdir,
            capture_output=True, text=True,
            timeout=timeout, encoding='utf-8', errors='replace'
        )
        el = time.time() - t0
        if r.returncode == 0:
            return (name, 'PASS', str(int(el)) + 's', '')
        err = r.stderr.strip().split('\n')
        return (name, 'FAIL', str(int(el)) + 's', '\n'.join(err[-12:]))
    except subprocess.TimeoutExpired:
        return (name, 'TIMEOUT', '>' + str(timeout) + 's', '')
    except Exception as e:
        return (name, 'ERROR', '0s', str(e))
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except:
                pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python run_notebook.py "[(\'path.ipynb\', \'workdir\'), ...]"')
        sys.exit(1)
    items = eval(sys.argv[1])
    results = []
    for nb, wd in items:
        name, status, el, err = run_one(nb, wd)
        print('[{:7s}] {:55s} ({})'.format(status, name, el))
        if err:
            for l in err.split('\n')[:8]:
                print('          ' + l)
            print()
        sys.stdout.flush()
        results.append((name, status))

    passed = sum(1 for _, s in results if s == 'PASS')
    print('\n{}/{} passed'.format(passed, len(results)))
