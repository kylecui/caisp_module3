from flask import Flask, render_template_string, request, redirect
import random

app = Flask(__name__)

# 模拟数据库：存储秘密份额和可视化信息
shares_A = []
shares_B = []
shares_details = []

# 混淆电路投票记录（模拟结果）
garbled_votes = []

def garbled_circuit_sum(votes):
    # 模拟混淆电路求和：将投票加密后累加（不展示细节，仅用于演示）
    encrypted = [f"Enc({v})" for v in votes]
    total = sum(votes)
    return encrypted, total

# 投票页面模板
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
</style>
</head>
<body>
<h2>请投票（所有投票将被秘密处理）</h2>
<form method=post>
  <input type=radio name=vote value=1 required> 同意<br>
  <input type=radio name=vote value=0> 反对<br><br>
  <input type=submit value=提交投票>
</form>
<hr>
<h3>当前投票情况（仅展示总票数，不暴露任何人信息）</h3>
<p>已收到 {{ total_votes }} 票（同意票数：{{ total_yes }}）</p>

<hr>
<h3>秘密共享过程详情</h3>
<table>
  <tr><th>投票编号</th><th>原始投票</th><th>份额 A</th><th>份额 B</th></tr>
  {% for share in shares_details %}
  <tr class="fade-in">
    <td>{{ loop.index }}</td>
    <td>{{ share.original }}</td>
    <td>{{ share.a }}</td>
    <td>{{ share.b }}</td>
  </tr>
  {% endfor %}
</table>

<hr>
<h3>模拟混淆电路执行流程</h3>
<div class="flow-box">
  <div class="box">
    <strong>投票输入</strong><br>
    {% for v in garbled_encrypted %}
      {{ v }}<br>
    {% endfor %}
  </div>
  <div class="box">
    <strong>混淆电路</strong><br>
    <em>黑盒执行 Enc(v1)+Enc(v2)+...</em>
  </div>
  <div class="box">
    <strong>输出</strong><br>
    总票数：{{ garbled_total }}
  </div>
</div>
</body>
</html>
"""

def secret_share(v):
    part1 = random.randint(0, 100)
    part2 = v - part1
    return part1, part2

@app.route('/', methods=['GET', 'POST'])
def vote():
    global shares_A, shares_B, shares_details, garbled_votes
    if request.method == 'POST':
        vote_value = int(request.form['vote'])
        a, b = secret_share(vote_value)
        shares_A.append(a)
        shares_B.append(b)
        shares_details.append({'original': vote_value, 'a': a, 'b': b})
        garbled_votes.append(vote_value)
        return redirect('/')

    # 计算总票数和同意票数
    total_votes = len(shares_A)
    total_yes = sum(shares_A) + sum(shares_B)

    garbled_encrypted, garbled_total = garbled_circuit_sum(garbled_votes)

    return render_template_string(
        html_template,
        total_votes=total_votes,
        total_yes=total_yes,
        shares_details=shares_details,
        garbled_encrypted=garbled_encrypted,
        garbled_total=garbled_total
    )

if __name__ == '__main__':
    app.run(debug=True)
