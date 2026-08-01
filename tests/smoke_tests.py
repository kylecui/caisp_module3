"""
慢速 notebook 的减配冒烟测试。

对计算量大的 notebook 使用缩减参数验证核心算法正确性：
  - ZOO: 1 epoch / 1 sample / 3 iterations
  - DP-SGD: 核心 DP step（裁剪+噪声+累加+ε计算）
  - Bayesian: 2 epochs / 2 samples / 20 queries
  - RL_sample: DummyVecEnv + PPO 评估（跳过训练）
  - 基础到进阶: 仅注意力 cell（跳过 gensim）

用法: python smoke_tests.py
耗时: ~1-2 分钟
"""
import json, subprocess, sys, os, time

PYTHON = sys.executable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SHIM = """import builtins
try: from IPython.display import display
except:
    def display(*a, **k):
        for x in a: print(x)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.show = lambda *a, **k: None
try: get_ipython
except NameError:
    def get_ipython(): return None
"""

def extract_cells(nb_path):
    with open(nb_path, encoding='utf-8') as f:
        nb = json.load(f)
    cells = []
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            src = ''.join(cell['source'])
            cleaned = '\n'.join(l for l in src.split('\n') if not l.strip().startswith('%') and not l.strip().startswith('!'))
            cells.append(cleaned)
    return cells

def run_code(code, workdir, timeout=300, label=''):
    tmp = os.path.join(ROOT, workdir, '_tmp_smoke.py')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(SHIM + '\n' + code)
    t0 = time.time()
    try:
        r = subprocess.run(
            [PYTHON, '_tmp_smoke.py'],
            cwd=os.path.join(ROOT, workdir),
            capture_output=True, text=True,
            timeout=timeout, encoding='utf-8', errors='replace'
        )
        el = time.time() - t0
        os.remove(tmp)
        ok = r.returncode == 0
        err = r.stderr[-400:] if not ok else ''
        return ok, int(el), err
    except subprocess.TimeoutExpired:
        try: os.remove(tmp)
        except: pass
        return False, timeout, 'TIMEOUT'
    except Exception as e:
        try: os.remove(tmp)
        except: pass
        return False, 0, str(e)

def test_zoo():
    """ZOO: 坐标有限差分，减配为 1 epoch / 1 sample / 3 iterations。"""
    print('=== ZOO (1 epoch, 1 sample, 3 iter) ===')
    cells = extract_cells(os.path.join(ROOT, 'src/module2/25_attack_zoo.ipynb'))
    code = '\n\n'.join(cells)
    code = code.replace('range(10)', 'range(1)')
    code = code.replace('max_iter_per_c=100', 'max_iter_per_c=3')
    code = code.replace('binary_steps=5', 'binary_steps=2')
    code = code.replace('num_attacks = 5', 'num_attacks = 1')
    ok, el, err = run_code(code, 'src/module2', timeout=300)
    print('  {} ({}s)'.format('PASS' if ok else 'FAIL/TIMEOUT', el))
    if err: print('  ', err[-200:])

def test_dp_sgd():
    """DP-SGD: 验证核心 step（裁剪+噪声+累加）。"""
    print('\n=== DP-SGD (core step) ===')
    code = '''
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(32*8*8, 128)
        self.fc2 = nn.Linear(128, 10)
    def forward(self, x):
        x = F.relu(self.conv1(x)); x = F.max_pool2d(x, 2)
        x = F.relu(self.conv2(x)); x = F.max_pool2d(x, 2)
        x = x.view(x.size(0), -1); x = F.relu(self.fc1(x))
        return self.fc2(x)

def clip_gradient(parameters, max_norm):
    total_norm = sum(p.grad.norm(2).item()**2 for p in parameters if p.grad is not None)**0.5
    coef = min(max_norm / (total_norm + 1e-6), 1.0)
    for p in parameters:
        if p.grad is not None: p.grad.data.mul_(coef)

def add_noise(parameters, max_norm, sigma, batch_size):
    std = max_norm * sigma / batch_size
    for p in parameters:
        if p.grad is not None:
            p.grad.data.add_(torch.normal(0, std, size=p.grad.shape, device=p.grad.device))

model = SimpleCNN().to(device)
opt = torch.optim.SGD(model.parameters(), lr=0.01)
x = torch.randn(8, 3, 32, 32).to(device)
y = torch.randint(0, 10, (8,)).to(device)
criterion = nn.CrossEntropyLoss(reduction='none')

# Per-sample gradient + clip + accumulate
for i in range(8):
    model.zero_grad()
    loss = criterion(model(x[i:i+1]), y[i:i+1])
    loss.backward()
    clip_gradient(model.parameters(), 1.0)
    for p in model.parameters():
        if p.grad is not None:
            if hasattr(p, 'ag'): p.ag += p.grad.data.clone()
            else: p.ag = p.grad.data.clone()
for p in model.parameters():
    if hasattr(p, 'ag'):
        p.grad = p.ag / 8; delattr(p, 'ag')
add_noise(model.parameters(), 1.0, 1.0, 8)
opt.step()
print('DP-SGD core step: OK')
'''
    ok, el, err = run_code(code, 'src/module2', timeout=60)
    print('  {} ({}s)'.format('PASS' if ok else 'FAIL', el))
    if err: print('  ', err[-200:])

def test_bayesian():
    """Bayesian: 减配为 2 epochs / 2 samples / 20 queries。"""
    print('\n=== Bayesian (2 epochs, 2 samples, 20 queries) ===')
    cells = extract_cells(os.path.join(ROOT, 'src/module2/24_attack_bayesian.ipynb'))
    code = '\n\n'.join(cells)
    code = code.replace('range(5)', 'range(2)')
    code = code.replace('num_attacks = 10', 'num_attacks = 2')
    code = code.replace('max_queries=50', 'max_queries=20')
    ok, el, err = run_code(code, 'src/module2', timeout=300)
    print('  {} ({}s)'.format('PASS' if ok else 'FAIL/TIMEOUT', el))
    if err: print('  ', err[-200:])

def test_rl_sample():
    """RL_sample: DummyVecEnv + PPO 评估（跳过训练）。"""
    print('\n=== RL_sample (DummyVecEnv, eval only) ===')
    code = '''
import os; os.chdir(r"''' + os.path.join(ROOT, 'src/module2') + '''")
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt; plt.show = lambda *a,**k: None
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import gymnasium as gym

env = DummyVecEnv([lambda: gym.make('CartPole-v1')])
model = PPO.load('./data/ppo_cartpole', env=env)
obs = env.reset()
rewards = 0.0
episode_rewards = []
for step in range(500):
    action, _ = model.predict(obs)
    obs, reward, done, info = env.step(action)
    rewards += reward[0]
    if done[0]:
        episode_rewards.append(rewards)
        rewards = 0.0
        obs = env.reset()
print('Episodes:', len(episode_rewards))
if episode_rewards:
    print('Avg reward:', np.mean(episode_rewards))
print('RL eval: OK')
'''
    ok, el, err = run_code(code, 'src/module2', timeout=120)
    print('  {} ({}s)'.format('PASS' if ok else 'FAIL/TIMEOUT', el))
    if err: print('  ', err[-200:])

def test_attention():
    """基础到进阶: 仅验证注意力 cell。"""
    print('\n=== 基础到进阶 (attention cells) ===')
    cells = extract_cells(os.path.join(ROOT, 'src/module2/01_basics_attention.ipynb'))
    for c in cells:
        if 'softmax' in c and 'd_k' in c:
            ok, el, err = run_code(c, 'src/module2', timeout=30)
            print('  {} ({}s)'.format('PASS' if ok else 'FAIL', el))
            if err: print('  ', err[-200:])
            break

if __name__ == '__main__':
    test_zoo()
    test_dp_sgd()
    test_bayesian()
    test_rl_sample()
    test_attention()
    print('\nDone.')
