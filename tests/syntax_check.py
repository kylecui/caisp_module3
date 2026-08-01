"""
全部 notebook 的 Python 语法校验。

用法: python syntax_check.py
耗时: <1 秒
"""
import json, glob, os, ast

def main():
    results = []
    for pattern in ['src/module2/*.ipynb', 'discussions_on_basis/*.ipynb']:
        for f in sorted(glob.glob(pattern)):
            name = os.path.basename(f)
            try:
                with open(f, encoding='utf-8') as fh:
                    nb = json.load(fh)
                code = '\n\n'.join(
                    ''.join(c['source'])
                    for c in nb['cells']
                    if c['cell_type'] == 'code'
                )
                # 剥离 IPython magic 行后再检查
                cleaned = '\n'.join(
                    l for l in code.split('\n')
                    if not l.strip().startswith('%') and not l.strip().startswith('!')
                )
                ast.parse(cleaned)
                results.append((name, 'OK', str(len(code)) + ' chars'))
            except SyntaxError as e:
                results.append((name, 'SYNTAX_ERR', 'line ' + str(e.lineno) + ': ' + str(e.msg)))
            except Exception as e:
                results.append((name, 'ERROR', str(e)[:100]))

    for name, status, detail in results:
        print('{:12s} {:55s} {}'.format(status, name, detail))

    errs = [r for r in results if r[1] != 'OK']
    print('\n{} OK, {} issues'.format(len(results) - len(errs), len(errs)))
    return 0 if not errs else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
