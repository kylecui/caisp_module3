from flask import Flask, jsonify, render_template_string
import numpy as np
import json
import functools
import operator
import random

# 引入同态加密库 phe（Python Paillier 实现）
# 教学环境若未安装 phe，则给出友好提示，不影响其他模块演示。
import importlib.util
PHE_AVAILABLE = importlib.util.find_spec("phe") is not None

app = Flask(__name__)

# 用于 MPC 演示的素数域，保证份额求和正确且不溢出
PRIME_FIELD = 2**61 - 1


class DataOwner:
    """
    数据拥有方（Data Owner）：模拟医院/机构。
    持有私有数据，只能用公钥加密后把密文发送给聚合方；
    自身并不持有私钥，无法解密其他方的数据。
    """
    def __init__(self, name, value, public_key):
        self.name = name
        self.value = value
        self.public_key = public_key

    def encrypt(self):
        # 使用公钥加密本地私有数据
        return self.public_key.encrypt(self.value)


class Aggregator:
    """
    聚合方（Aggregator）：负责在密文上执行计算。
    关键特性：Aggregator 只处理密文，从不接触私钥，
    因此无法从密文中获知任何原始数据。
    """
    def __init__(self):
        # 保存各数据方上传的密文
        self.encrypted_values = []

    def add_encrypted(self, ciphertext):
        self.encrypted_values.append(ciphertext)

    def encrypted_sum(self):
        """
        同态加密的加法同态性：
        E(m1) * E(m2) = E(m1 + m2)
        这里我们对密文序列做连加，得到密文形式的累加和。
        注意：不能使用内置 sum()，因为 phe 对象对右加（__radd__）支持不完善。
        """
        if not self.encrypted_values:
            return None
        return functools.reduce(operator.add, self.encrypted_values)


class ResultParty:
    """
    结果方（Result Party）：持有私钥，只解密最终聚合结果。
    在整个过程中，结果方不会看到任何单个数据方的原始密文内容。
    """
    def __init__(self, private_key):
        self.private_key = private_key

    def decrypt(self, encrypted_value):
        return self.private_key.decrypt(encrypted_value)


def secret_share(v, prime=PRIME_FIELD):
    """
    加法秘密分享：将 v 拆成 (a, b)，满足 a + b ≡ v (mod p)。
    两个份额在 Z_p 上均独立均匀分布，任何单个份额都不泄露 v。
    """
    a = random.randrange(prime)
    b = (v - a) % prime
    return a, b


def run_he_demo(hospital_data):
    """模拟三角色 HE 流程并返回可视化信息。"""
    if not PHE_AVAILABLE:
        return {
            "方案": "同态加密 (HE)",
            "错误": "Paillier 加密库 (phe) 未安装，请在本地安装 'pip install phe' 后使用该功能。"
        }

    # 本地导入 Paillier 模块，仅在确认已安装后执行
    import phe.paillier as paillier  # type: ignore

    # 1. 结果方生成密钥对，并公布公钥
    public_key, private_key = paillier.generate_paillier_keypair()
    result_party = ResultParty(private_key)

    # 2. 各医院作为数据方，使用公钥加密本地数据
    owners = [DataOwner(name, val, public_key) for name, val in hospital_data.items()]
    encrypted_values = [owner.encrypt() for owner in owners]

    # 3. 聚合方只接收密文，在密文上求和
    aggregator = Aggregator()
    for enc in encrypted_values:
        aggregator.add_encrypted(enc)
    encrypted_total = aggregator.encrypted_sum()

    # 4. 结果方解密最终结果
    final_result = result_party.decrypt(encrypted_total)

    return {
        "方案": "同态加密 (HE)",
        "流程说明": "ResultParty 生成密钥对 → DataOwner 用公钥加密 → Aggregator 密文求和 → ResultParty 私钥解密",
        "医院数据（各医院持有，不离开本地）": hospital_data,
        "加密后示意（部分展示）": {
            owner.name: str(enc.ciphertext())[:24] + "..."
            for owner, enc in zip(owners, encrypted_values)
        },
        "聚合方是否接触私钥": False,
        "聚合方是否接触明文": False,
        "最终解密结果": final_result
    }


def laplace_mechanism(value, sensitivity=1.0, epsilon=1.0):
    """
    Laplace 机制实现差分隐私。

    参数说明：
    - sensitivity（敏感度）：对于计数/求和查询，若数据集中一条记录最多改变结果 1，则 sensitivity=1。
    - epsilon（隐私预算）：数值越小，隐私保护越强，但噪声越大、效用越低；反之隐私越弱、效用越高。
    """
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return value + noise


def run_dp_demo(true_sum):
    """展示不同隐私预算 ε 下的 DP 输出。"""
    epsilons = [0.1, 1.0, 10.0]
    results = []
    for eps in epsilons:
        noisy = laplace_mechanism(true_sum, sensitivity=1.0, epsilon=eps)
        results.append({
            "epsilon（隐私预算）": eps,
            "添加的噪声": round(noisy - true_sum, 4),
            "带噪声输出": round(noisy, 4),
            "隐私强度": "高" if eps < 1 else ("中" if eps == 1 else "低"),
            "说明": "ε 越小隐私越强，噪声越大；ε 越大结果越接近真实值，但隐私保护减弱。"
        })

    return {
        "方案": "差分隐私 (DP)",
        "真实总和": true_sum,
        "敏感度 sensitivity": 1,
        "隐私预算说明": "epsilon 控制隐私-效用权衡。epsilon→0 隐私极强但噪声极大；epsilon→∞ 无噪声但无隐私保护。",
        "不同 epsilon 的结果": results
    }


def run_mpc_demo(hospital_data):
    """
    多方安全计算：3 家医院通过加法秘密分享把数据分给 2 个服务器，
    任一服务器都无法单独获知任何一家医院的真实数据。
    """
    server1_shares = []
    server2_shares = []

    # 每家医院把自己的计数拆成两个份额
    for name, value in hospital_data.items():
        a, b = secret_share(value, PRIME_FIELD)
        server1_shares.append(a)
        server2_shares.append(b)

    # 每个服务器在本地对自己的份额求和
    server1_local_sum = sum(server1_shares) % PRIME_FIELD
    server2_local_sum = sum(server2_shares) % PRIME_FIELD

    # 双方求和结果合并即可恢复总数
    total = (server1_local_sum + server2_local_sum) % PRIME_FIELD

    return {
        "方案": "多方计算 (MPC)",
        "流程说明": "每家医院把数据拆成两份 → Server1 与 Server2 各自在本地份额上求和 → 合并两个本地和得到最终结果",
        "医院数据（各自持有，不直接发送）": hospital_data,
        "Server1 本地和": server1_local_sum,
        "Server2 本地和": server2_local_sum,
        "MPC 求和结果": total,
        "安全性说明": "任意单个服务器只拿到均匀随机的份额，无法反推出任何一家医院的原始数据；只有两个服务器合作才能恢复总和。"
    }


@app.route('/')
def index():
    hospital_data = {"A": 45, "B": 70, "C": 35}

    # 同态加密（HE）三角色演示
    he_info = run_he_demo(hospital_data)

    # 差分隐私（DP）演示
    true_sum = sum(hospital_data.values())
    dp_info = run_dp_demo(true_sum)

    # 多方计算（MPC）演示
    mpc_info = run_mpc_demo(hospital_data)

    return render_template_string("""
    <h1>三种隐私计算方案对比</h1>
    <h2>{{ he['方案'] }}</h2>
    <pre>{{ he_json }}</pre>

    <h2>{{ dp['方案'] }}</h2>
    <pre>{{ dp_json }}</pre>

    <h2>{{ mpc['方案'] }}</h2>
    <pre>{{ mpc_json }}</pre>
    """,
    he=he_info,
    dp=dp_info,
    mpc=mpc_info,
    he_json=json.dumps(he_info, indent=2, ensure_ascii=False),
    dp_json=json.dumps(dp_info, indent=2, ensure_ascii=False),
    mpc_json=json.dumps(mpc_info, indent=2, ensure_ascii=False)
    )


if __name__ == '__main__':
    app.run(debug=True)
