from flask import Flask, jsonify, render_template_string
import numpy as np
import json

try:
    from phe import paillier
    PHE_AVAILABLE = True
except ImportError:
    PHE_AVAILABLE = False

app = Flask(__name__)

@app.route('/')
def index():
    hospital_data = {"A": 45, "B": 70, "C": 35}

    # 同态加密（HE）
    if PHE_AVAILABLE:
        public_key, private_key = paillier.generate_paillier_keypair()
        encrypted_data = {k: public_key.encrypt(v) for k, v in hospital_data.items()}
        encrypted_sum = sum(encrypted_data.values())
        he_result = private_key.decrypt(encrypted_sum)
        he_info = {
            "方案": "同态加密 (HE)",
            "医院数据（明文）": hospital_data,
            "加密后（示意）": {k: str(v.ciphertext()) for k, v in encrypted_data.items()},
            "加密求和后密文": str(encrypted_sum.ciphertext()),
            "最终解密结果": he_result
        }
    else:
        he_info = {"方案": "同态加密 (HE)", "错误": "Paillier 加密库 (phe) 未安装，请在本地安装 'pip install phe' 后使用该功能。"}

    # 差分隐私（DP）
    true_sum = sum(hospital_data.values())
    def laplace_mechanism(value, sensitivity=1.0, epsilon=1.0):
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        return value + noise
    dp_result = laplace_mechanism(true_sum)
    dp_info = {
        "方案": "差分隐私 (DP)",
        "真实总和": true_sum,
        "添加的噪声": round(dp_result - true_sum, 2),
        "最终输出": round(dp_result, 2)
    }

    # 多方计算（MPC 模拟）
    mpc_result = true_sum
    mpc_info = {
        "方案": "多方计算 (MPC)",
        "医院数据（各自持有）": hospital_data,
        "模拟加和结果": mpc_result,
        "说明": "实际MPC协议中，各方通过加密/通信协作实现此加法，无需暴露原始数据"
    }

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