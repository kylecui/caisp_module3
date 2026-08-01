# tests/ — 实验验证脚本

本目录包含 CAISP 模块二实验的验证脚本，用于快速检查所有 notebook 的正确性。

## 使用方法

```bash
# 在 py_gpu_new 环境中运行

# 1. 语法检查（秒级，验证所有 notebook 代码无语法错误）
conda run -n py_gpu_new python tests/syntax_check.py

# 2. 执行指定 notebook（完整运行，含训练）
conda run -n py_gpu_new python tests/run_notebook.py "[('src/module2/20_attack_fgsm_pgd.ipynb','src/module2')]"

# 3. 慢速 notebook 减配冒烟测试（ZOO / DP-SGD / Bayesian / RL，~1 分钟内完成）
conda run -n py_gpu_new python tests/smoke_tests.py
```

## 文件说明

| 文件 | 说明 | 耗时 |
|------|------|------|
| `syntax_check.py` | 全部 notebook 的 Python 语法校验 | <1s |
| `run_notebook.py` | 通用 notebook 执行器（含 IPython 兼容层） | 每个 1-6 min |
| `smoke_tests.py` | 慢速 notebook 的减配冒烟测试 | ~1 min |

## 减配说明

以下 notebook 的核心算法正确但因计算量大需要减配验证：

- **ZOO**：坐标有限差分 O(d) 查询/步，完整运行 >30 min。减配为 1 epoch / 1 sample / 3 iterations。
- **DP-SGD**：逐样本梯度裁剪，完整运行 >10 min。notebook 已内置 5000 样本子集；冒烟测试验证核心 DP step。
- **Bayesian**：CPU 上 PCA 逆变换 + 贝叶斯优化，10 样本 × 50 查询 ~8 min。减配为 2 epochs / 2 samples / 20 queries。
- **RL_sample**：SubprocVecEnv 在非交互式环境中会死锁，冒烟测试用 DummyVecEnv 验证 PPO 评估 + reward 逻辑。
