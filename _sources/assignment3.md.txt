# Assignment 3

## I. Online Agent

### 1. Platform Used
Dify

### 2. API Used
Qwen (Alibaba Cloud Tongyi Qianwen)

### 3. Implemented Features
Create an Agent capable of analyzing files and answering specific questions about file content.

### 4. Steps

#### (1) Deploy Dify
- Download and install Docker
- Deploy Dify using Docker
[![pmFWisU.png](https://s41.ax1x.com/2026/05/29/pmFWisU.png)](https://imgchr.com/i/pmFWisU)

#### (2) Install Ollama and Download Models (for local backup, or use only online API)
- Download Ollama
- Download the qwen2:7b model in Ollama
[![pmFWmJ1.png](https://s41.ax1x.com/2026/05/29/pmFWmJ1.png)](https://imgchr.com/i/pmFWmJ1)

#### (3) Create an Agent in Dify
- Select "Online Model" → Add Qwen API (requires applying for an Alibaba Cloud API Key)
- Create "Travel Assistant":
- [![pmFWeiR.png](https://s41.ax1x.com/2026/05/29/pmFWeiR.png)](https://imgchr.com/i/pmFWeiR)

#### (4) Results
[![pmFWVo9.png](https://s41.ax1x.com/2026/05/29/pmFWVo9.png)](https://imgchr.com/i/pmFWVo9)

## II. Local Model Deployment

### 1. Deployment Method
Use Ollama to deploy a local model. Installation was already completed in the first section and will not be repeated here.

### 2. Deployed Model
qwen2:7b

### 3. Interaction Demo

Run in the terminal:
```bash
ollama run qwen2:7b
```

Enter a question:
> "Who are you"

Model output:
> I am Qwen, a large language model developed by Alibaba Cloud.

### 4. Results
[![pmFWEdJ.png](https://s41.ax1x.com/2026/05/29/pmFWEdJ.png)](https://imgchr.com/i/pmFWEdJ)

## III. IDE Integration

### 1. Environment
- VSCode
- Plugin: Continue (configured to connect to DeepSeek API)

### 2. Task: AI Helps Explain and Refactor Code

#### Original Code
```python
def calculate_average(grades):
    """Calculate the average score of student grades"""
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
        avg = calculate_average(scores)  # Potential error: scores may be an empty list
        grade = get_letter_grade(avg)
        results.append(f"{name}: {avg} ({grade})")
    return results

# Test data
class_data = [
    {"name": "Alice", "scores": [85, 90, 88]},
    {"name": "Bob", "scores": []},          # Empty scores list → division by zero error
    {"name": "Charlie", "scores": [70, 65, 75]},
    {"name": "Diana", "scores": [95, None, 92]},  # None value → type error
]

print(process_students(class_data))
```
[![pmFWuz6.png](https://s41.ax1x.com/2026/05/29/pmFWuz6.png)](https://imgchr.com/i/pmFWuz6)
#### Refactoring with Continue + DeepSeek
#### Results
[![pmFWnRx.png](https://s41.ax1x.com/2026/05/29/pmFWnRx.png)](https://imgchr.com/i/pmFWnRx)

## IV. Documentation & Reflection

### 1. Challenges and Solutions

| Challenge | Solution |
|-----------|----------|
| Docker port conflict during Dify deployment | Modify the port mapping in docker-compose.yml, use `8080:80` |
| Qwen API call failure after application | Check API Key permissions on Alibaba Cloud DashScope, add `qwen-turbo` model access |
| Slow model download speed in Ollama | Use a domestic mirror or manually download model files to `~/.ollama/models` |
| Continue plugin needs API proxy to connect to DeepSeek | Set VSCode HTTP proxy environment variable |

### 2. Online Model vs Local Model Comparison

| Dimension | Online Model (Qwen API) | Local Model (Ollama + qwen2:7b) |
|-----------|-------------------------|----------------------------------|
| **Performance** | Fast response (<2s), supports parallel requests | Slower (5-15s), high GPU usage |
| **Ease of Use** | Only need API Key, no hardware configuration required | Need to install Ollama, download large files, requires GPU |
| **Practicality** | Suitable for document analysis, web search and other complex tasks | Suitable for code completion, offline development environments |
| **Cost** | Billed per token (free for low usage) | Free (but requires own hardware) |
| **Data Privacy** | Data uploaded to third party | Data completely local, suitable for sensitive code |
