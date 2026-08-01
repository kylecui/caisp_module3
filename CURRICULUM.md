# CAISP 模块二：技术基础篇 — 实验课程大纲

本文件定义所有实验的**推荐教学顺序**，严格按照教材章节排列。全部实验文件统一存放在 `src/module2/` 目录下。

---

## 第一章–第二章：AI 基础与常见算法模型

| 序号 | 文件 | 主题 |
|:---:|------|------|
| 1 | `src/module2/01_basics_attention.ipynb` | 词向量与注意力入门 |
| 2 | `src/module2/02_logistic_softmax_nn.ipynb` | 逻辑回归 / Softmax / 神经网络 |
| 3 | `src/module2/03_nn_to_sin.ipynb` | 神经网络拟合非线性 |
| 4 | `src/module2/04_naive_bayes_spam.ipynb` | 朴素贝叶斯分类器 |
| 5 | `src/module2/05_transformers.ipynb` | Transformer 自注意力 |
| 6 | `src/module2/06_moe.ipynb` | 混合专家模型 (MoE) |
| 7 | `src/module2/07_rl_cartpole.ipynb` | 强化学习基础 (PPO) |

## 第三章：AI 安全概述（桥接实验）

| 序号 | 文件 | 主题 |
|:---:|------|------|
| 8 | `src/module2/08_bridge_adversarial_classifier.ipynb` | 对抗样本初探（2D 决策边界） |
| 9 | `src/module2/09_bridge_prompt_injection.ipynb` | 提示注入原理 |
| 10 | `src/module2/10_bridge_reward_hacking.ipynb` | 奖励黑客 |

## 第四章：AI 数据隐私与保护

### 4A. 隐私保护技术

| 序号 | 文件 | 主题 |
|:---:|------|------|
| 11 | `src/module2/11_privacy_k_anonymity.ipynb` | K-Anonymity / L-Diversity / T-Closeness |
| 12 | `src/module2/12_federated_learning.ipynb` | 联邦学习 (FedAvg) |
| 13 | `src/module2/13_mpc_voting.py` | 安全多方计算 (MPC) 投票 |
| 14 | `src/module2/14_mpc_he_dp.py` | 同态加密 / 差分隐私 / MPC 对比 |
| 15 | `src/module2/15_privacy_differential_privacy.ipynb` | 差分隐私训练 (DP-SGD) |

### 4B. 隐私攻击

| 序号 | 文件 | 主题 |
|:---:|------|------|
| 16 | `src/module2/16_privacy_membership_inference.ipynb` | 成员推理攻击 |
| 17 | `src/module2/17_privacy_model_extraction.ipynb` | 模型窃取攻击 |
| 18 | `src/module2/18_privacy_model_inversion.ipynb` | 模型反演攻击 |

## 第五章：AI 对抗攻击基础

### 5A. 白盒攻击

| 序号 | 文件 | 主题 |
|:---:|------|------|
| 19 | `src/module2/19_attack_lbfgs.ipynb` | L-BFGS 攻击 |
| 20 | `src/module2/20_attack_fgsm_pgd.ipynb` | FGSM 与 PGD 攻击 |
| 21 | `src/module2/21_attack_deepfool.ipynb` | DeepFool 攻击 |
| 22 | `src/module2/22_attack_cw.ipynb` | Carlini-Wagner L2 攻击 |
| 23 | `src/module2/23_attack_uap.ipynb` | 通用对抗扰动 (UAP) |

### 5B. 黑盒攻击

| 序号 | 文件 | 主题 |
|:---:|------|------|
| 24 | `src/module2/24_attack_bayesian.ipynb` | 贝叶斯优化攻击 |
| 25 | `src/module2/25_attack_zoo.ipynb` | ZOO 零阶优化攻击 |
| 26 | `src/module2/26_attack_simba.ipynb` | SimBA 简单黑盒攻击 |

## 第六章：AI 安全防御机制

| 序号 | 文件 | 主题 |
|:---:|------|------|
| 27 | `src/module2/27_defense_adversarial_training.ipynb` | 对抗训练 |
| 28 | `src/module2/28_defense_detection.ipynb` | 对抗样本检测 |
| 29 | `src/module2/29_defense_randomized_smoothing.ipynb` | 随机平滑认证防御 |

---

## 验证脚本

```bash
conda run -n py_gpu_new python tests/syntax_check.py
conda run -n py_gpu_new python tests/run_notebook.py "[('src/module2/20_attack_fgsm_pgd.ipynb','src/module2')]"
conda run -n py_gpu_new python tests/smoke_tests.py
```
