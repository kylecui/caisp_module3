from flask import Flask, render_template_string, request, redirect
import random

app = Flask(__name__)

# 模拟两个互不信任的服务器（非共谋），分别保存秘密份额
# In a real MPC deployment, these would be in separate processes/machines.
shares_A = []      # 服务器 A 持有的份额 [a1, a2, ...]
shares_B = []      # 服务器 B 持有的份额 [b1, b2, ...]

# 一个足够大的素数域，保证份额相加不会溢出，且模运算构成有限域
# 这里使用 Mersenne 素数 2^61 - 1，便于教学演示
PRIME_FIELD = 2**61 - 1


def share_secret(v, prime=PRIME_FIELD):
    """
    加法秘密分享 (Additive Secret Sharing over Z_p)

    将单个秘密值 v ∈ {0, 1} 拆成两个份额 (a, b)，满足：
        a + b ≡ v (mod p)
    其中：
        - a 是 [0, p) 上的均匀随机数
        - b = (v - a) mod p

    安全性说明：单独一个份额在 Z_p 上均匀分布，泄露方差 1/p 可忽略，
    因此任何单一服务器都无法从自己的份额中推断出原始投票 v。
    """
    if v not in (0, 1):
        raise ValueError("投票值只能是 0 或 1")
    a = random.randrange(prime)
    b = (v - a) % prime
    return a, b


def reconstruct_sum(shares_a, shares_b, prime=PRIME_FIELD):
    """
    由两个服务器分别对本地份额求和，再相加模 p 得到最终结果。
    注意：在真正的 MPC 中，这一步由混淆电路/安全多方计算协议完成，
    任何一方都不会先看到对方单个份额。
    """
    local_sum_A = sum(shares_a) % prime
    local_sum_B = sum(shares_b) % prime
    return (local_sum_A + local_sum_B) % prime


# 投票页面模板：保持原有样式，但不再泄露单个份额
html_template = """
<!doctype html>
<html>
<head>
<title>私密投票系统</title>
<style>
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid black; padding: 8px; text-align: center; }
  .fade-in {
    animation: fadeIn 1s ease-in-out;
  }
  @keyframes fadeIn {
    0% { background-color: yellow; opacity: 0; }
    100% { background-color: white; opacity: 1; }
  }
  .flow-box {
    display: flex;
    justify-content: space-between;
    margin-top: 20px;
  }
  .box {
    width: 30%;
    padding: 10px;
    border: 2px dashed #888;
    border-radius: 10px;
    background-color: #f9f9f9;
    text-align: center;
    animation: popFade 1s ease-in-out;
  }
  @keyframes popFade {
    from { transform: scale(0.8); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
  }
  .note {
    background: #fffbe6;
    border-left: 4px solid #f0ad4e;
    padding: 10px;
    margin-top: 15px;
  }
</style>
</head>
<body>
<h2>请投票（所有投票将被秘密处理）</h2>
<form method=post>
  <input type=radio name=vote value=1 required> 同意<br>
  <input type=radio name=vote value=0> 反对<br><br>
  <input type=submit value="提交投票">
</form>
<hr>
<h3>当前投票情况（仅展示聚合结果，不暴露任何个人投票）</h3>
<p>已收到 {{ total_votes }} 票（同意票数：{{ total_yes }}；参与人数：{{ total_votes }}）</p>

<div class="note">
  <strong>隐私说明：</strong> 系统不会以明文保存您的投票。
  每一张投票会被<strong>加法秘密分享</strong>成两份，分别交给两个互不共谋的服务器。
  单个服务器仅拿到均匀随机的份额，无法反推出任何一张原始投票；
  只有经过混淆电路（Garbled Circuit）安全求和后，才会公布总同意票数。
</div>

<hr>
<h3>模拟混淆电路执行流程</h3>
<div class="flow-box">
  <div class="box">
    <strong>① 投票输入</strong><br>
    v ∈ {0, 1}<br>
    （由浏览器本地提交）
  </div>
  <div class="box">
    <strong>② 秘密分享</strong><br>
    a ← Z<sub>p</sub><br>
    b = (v - a) mod p<br>
    服务器 A 持有 a，服务器 B 持有 b
  </div>
  <div class="box">
    <strong>③ 混淆电路</strong><br>
    黑盒计算：<br>
    total = Σa<sub>i</sub> + Σb<sub>i</sub> mod p<br>
    任何一方都不看到对方的单个份额
  </div>
  <div class="box">
    <strong>④ 公开输出</strong><br>
    总票数：{{ total_votes }}<br>
    同意票数：{{ total_yes }}
  </div>
</div>

<div class="note">
  <strong>教学提示：</strong> 本演示使用素数域 Z<sub>{{ prime }}</sub> 上的加法秘密分享。
  真正的混淆电路会把“比较/求和”逻辑编译成加密真值表，由计算方在不解密的情况下安全求值，
  最终只泄露“总同意票数”这唯一的输出。
</div>
</body>
</html>
"""


@app.route('/', methods=['GET', 'POST'])
def vote():
    global shares_A, shares_B

    if request.method == 'POST':
        try:
            vote_value = int(request.form['vote'])
        except (ValueError, KeyError):
            return "无效的投票参数", 400

        # 输入校验：仅允许 0 或 1
        if vote_value not in (0, 1):
            return "投票值只能是 0（反对）或 1（同意）", 400

        # 将投票拆成两个份额，分别交给两个模拟服务器
        a, b = share_secret(vote_value)
        shares_A.append(a)
        shares_B.append(b)
        return redirect('/')

    # 计算总票数和同意票数
    total_votes = len(shares_A)
    # 在真实 MPC 中，这个求和由混淆电路在密文/份额上完成
    total_yes = reconstruct_sum(shares_A, shares_B)

    return render_template_string(
        html_template,
        prime=PRIME_FIELD,
        total_votes=total_votes,
        total_yes=total_yes
    )


if __name__ == '__main__':
    app.run(debug=True)
