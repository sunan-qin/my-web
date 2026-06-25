
# Assignment 3

## 一、Online Agent 

### 1. 使用平台
Dify

### 2. 使用的API
Qwen（阿里云通义千问）

### 3. 实现功能
创建一个能够分析文件的Agent，回答关于文件内容的特定问题。

### 4. 步骤

#### (1) 部署Dify
- 下载并安装 Docker
- 使用 Docker 部署 Dify  
[![pmFWisU.png](https://s41.ax1x.com/2026/05/29/pmFWisU.png)](https://imgchr.com/i/pmFWisU)

#### (2) 安装Ollama并下载模型（用于本地备用，也可仅用在线API）
- 下载 Ollama  
- 在 Ollama 中下载 qwen2:7b 模型  
[![pmFWmJ1.png](https://s41.ax1x.com/2026/05/29/pmFWmJ1.png)](https://imgchr.com/i/pmFWmJ1)

#### (3) 在Dify中创建Agent
- 选择“在线模型” → 添加 Qwen API（需申请阿里云API Key）
- 创建“旅行助手”：
- [![pmFWeiR.png](https://s41.ax1x.com/2026/05/29/pmFWeiR.png)](https://imgchr.com/i/pmFWeiR)

#### (4) 结果展示
[![pmFWVo9.png](https://s41.ax1x.com/2026/05/29/pmFWVo9.png)](https://imgchr.com/i/pmFWVo9)
## 二、Local Model Deployment 

### 1. 部署方式
使用 Ollama 部署本地模型，已在第一部分中的安装完毕不在此赘述

### 2. 部署的模型
qwen2:7b

### 3. 交互演示

在终端中运行：
```bash
ollama run qwen2:7b
```

输入问题：
> “你是谁”

模型输出：
> 我是Qwen，由阿里云开发的大语言模型。

### 4. 结果展示  
[![pmFWEdJ.png](https://s41.ax1x.com/2026/05/29/pmFWEdJ.png)](https://imgchr.com/i/pmFWEdJ)

## 三、IDE Integration 

### 1. 环境
- VSCode
- 插件：Continue（已配置连接到 DeepSeek API）

### 2. 任务：AI帮助解释并重构代码

#### 原始代码
```python
def calculate_average(grades):
    """计算学生成绩的平均分"""
    total = 0
    for grade in grades:
        total += grade
    average = total / len(grades)
    return average

def get_letter_grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def process_students(students):
    results = []
    for student in students:
        name = student['name']
        scores = student['scores']
        avg = calculate_average(scores)  # 潜在错误：scores 可能为空列表
        grade = get_letter_grade(avg)
        results.append(f"{name}: {avg} ({grade})")
    return results

# 测试数据
class_data = [
    {"name": "Alice", "scores": [85, 90, 88]},
    {"name": "Bob", "scores": []},          # 空成绩列表 → 除零错误
    {"name": "Charlie", "scores": [70, 65, 75]},
    {"name": "Diana", "scores": [95, None, 92]},  # None 值 → 类型错误
]

print(process_students(class_data))
```
[![pmFWuz6.png](https://s41.ax1x.com/2026/05/29/pmFWuz6.png)](https://imgchr.com/i/pmFWuz6)
#### 使用 Continue + DeepSeek 进行重构
#### 运行结果  
[![pmFWnRx.png](https://s41.ax1x.com/2026/05/29/pmFWnRx.png)](https://imgchr.com/i/pmFWnRx)

## 四、Documentation & Reflection 

### 1. 遇到的挑战与解决方案

| 挑战 | 解决方案 |
|------|----------|
| Dify 部署时 Docker 端口冲突 | 修改 docker-compose.yml 中的端口映射，使用 `8080:80` |
| Qwen API 申请后调用失败 | 检查阿里云 DashScope 的 API Key 权限，添加 `qwen-turbo` 模型访问 |
| Ollama 下载模型速度慢 | 使用国内镜像或手动下载模型文件到 `~/.ollama/models` |
| Continue 插件连接 DeepSeek 需要 API 代理 | 设置 VSCode 的 HTTP 代理环境变量 |

### 2. 在线模型 vs 本地模型 对比

| 维度 | 在线模型 (Qwen API) | 本地模型 (Ollama + qwen2:7b) |
|------|---------------------|-------------------------------|
| **性能** | 响应快（<2s），可并行多请求 | 较慢（5-15s），GPU占用高 |
| **易用性** | 仅需API Key，无需硬件配置 | 需安装Ollama、下载大文件，需GPU支持 |
| **实用性** | 适合文档分析、联网搜索等复杂任务 | 适合代码补全、离线开发环境 |
| **成本** | 按token计费（低量免费） | 免费（但需自备硬件） |
| **数据隐私** | 数据上传至第三方 | 数据完全本地，适合敏感代码 |


