# PersistentTranslateServer：您的个人自学习翻译引擎

“PersistentTranslateServer”是一个完整的高性能翻译 Web 应用程序，可在您的计算机上本地运行。它为直接翻译提供了一个简单的 Web 界面，并为您的其他项目提供了一个强大的 API。它的核心功能是它的**永久记忆**：它从每次人工智能翻译中学习，随着时间的推移不断增长其本地数据库，变得更快、更智能。

## 主要特点

- **Web 界面**：干净简单的用户界面，可直接在浏览器中翻译文本。
- **强大的 API**：强大的 API 端点，可将高速翻译集成到您的任何项目中。
- **永久内存**：自动将新的 AI 翻译条目保存回其本地 SQLite 数据库。你使用它的次数越多，它就会变得越快。
- **数据库优先架构**：优先考虑从本地数据库进行闪电般的快速查找，只调用 AI 来查找真正的新文本。
- **可配置的 AI 后端**：轻松配置服务器以使用您首选的 AI 提供商，例如本地 Ollama 实例或任何外部 API。
- **批处理**：通过将大型请求拆分为较小的批次来智能处理大型请求，以确保稳定性，即使使用较小的 AI 模型也是如此。

---

## 快速入门指南

请按照以下步骤启动并运行您的翻译服务器。

### 第 1 步：安装依赖项

确保您安装了 Python。然后，在项目目录中打开终端并运行：

```bash
# 如果你有多个环境，建议使用特定的 python 可执行文件
python -m pip install -r requirements.txt
```

### 第 2 步：构建翻译数据库

此命令下载一个大型社区翻译包并构建您的初始“translations.db”文件。您只需运行一次，或者每当您想要更新基本翻译时。

```bash
python database_builder.py
```

### 第 3 步：启动服务器

此命令启动 Web 服务器。它将在您的终端中保持运行状态，随时可以接受请求。

```bash
# --reload 标志非常适合开发，因为它在代码更改时自动重新启动服务器。
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 第 4 步：使用服务！

- **Web 界面**：打开 Web 浏览器并导航至“http://127.0.0.1:8000”。
- **API**：开始向 API 端点发送请求（请参阅下面的详细信息）。

---

## API 文档

您可以通过向“/translate”端点发送 POST 请求以编程方式与服务器交互。

- **网址**： 'http://127.0.0.1:8000/translate'
- **方法**：“POST”
- **正文格式**：JSON

### 请求正文

请求正文必须是包含单个键 '“texts”' 的 JSON 对象，其值是要翻译的字符串列表。

**请求正文示例：****

```json
{
  "texts": [
    "Mob Alerted",
    "!",
    "This is a new sentence to translate.",
    "Done"
  ]
}
```

### 响应正文

服务器将使用一个 JSON 对象进行响应，其中键是原始英文文本，值是其中文翻译。

**示例响应正文：**

```json
{
  "Mob Alerted": "生物警觉",
  "!": "！",
  "This is a new sentence to translate.": "这是一个需要翻译的新句子。",
  "Done": "完成"
}
```

### Python 示例

下面是一个简单的 Python 脚本，演示如何调用 API：

```python
import requests
import json

# The URL of your running server
api_url = "http://127.0.0.1:8000/translate"

# The list of texts you want to translate
texts_to_translate = [
    "Settings",
    "Video Settings...",
    "A completely new phrase for the server to learn."
]

# The request payload
payload = {
    "texts": texts_to_translate
}

try:
    response = requests.post(api_url, json=payload)
    
    # Raise an exception if the request was unsuccessful
    response.raise_for_status()
    
    # Parse the JSON response
    translations = response.json()
    
    # Print the results beautifully
    print("--- Translation Results ---")
    for original, translated in translations.items():
        print(f'{original} -> {translated}')

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

```

# PersistentTranslateServer: Your Personal, Self-Learning Translation Engine

`PersistentTranslateServer` is a complete, high-performance translation web application that runs locally on your machine. It provides a simple web interface for direct translations and a powerful API for your other projects. Its core feature is its **permanent memory**: it learns from every AI translation, continuously growing its local database to become faster and smarter over time.

## Key Features

- **Web Interface**: A clean and simple UI to translate texts directly in your browser.
- **Powerful API**: A robust API endpoint to integrate high-speed translation into any of your projects.
- **Permanent Memory**: Automatically saves new AI-translated entries back into its local SQLite database. The more you use it, the faster it gets.
- **Database-First Architecture**: Prioritizes lightning-fast lookups from the local database, only calling the AI for truly new texts.
- **Configurable AI Backend**: Easily configure the server to use your preferred AI provider, such as a local Ollama instance or any external API.
- **Batch Processing**: Intelligently handles large requests by splitting them into smaller batches to ensure stability, even with smaller AI models.

---

## Quick Start Guide

Follow these steps to get your translation server up and running.

### Step 1: Install Dependencies

Make sure you have Python installed. Then, open your terminal in the project directory and run:

```bash
# It is recommended to use the specific python executable if you have multiple environments
python -m pip install -r requirements.txt
```

### Step 2: Build the Translation Database

This command downloads a large community translation pack and builds your initial `translations.db` file. You only need to run this once, or whenever you want to update the base translations.

```bash
python database_builder.py
```

### Step 3: Start the Server

This command starts the web server. It will remain running in your terminal, ready to accept requests.

```bash
# The --reload flag is great for development, as it automatically restarts the server on code changes.
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Use the Service!

- **Web Interface**: Open your web browser and navigate to `http://127.0.0.1:8000`.
- **API**: Start sending requests to the API endpoint (see details below).

---

## API Documentation

You can programmatically interact with the server by sending POST requests to the `/translate` endpoint.

- **URL**: `http://127.0.0.1:8000/translate`
- **Method**: `POST`
- **Body Format**: JSON

### Request Body

The request body must be a JSON object containing a single key, `"texts"`, whose value is a list of strings to be translated.

**Example Request Body:**

```json
{
  "texts": [
    "Mob Alerted",
    "!",
    "This is a new sentence to translate.",
    "Done"
  ]
}
```

### Response Body

The server will respond with a JSON object where the keys are the original English texts and the values are their Chinese translations.

**Example Response Body:**
```json
{
  "Mob Alerted": "生物警觉",
  "!": "！",
  "This is a new sentence to translate.": "这是一个需要翻译的新句子。",
  "Done": "完成"
}
```

### Python Example

Here is a simple Python script demonstrating how to call the API:

```python
import requests
import json

# The URL of your running server
api_url = "http://127.0.0.1:8000/translate"

# The list of texts you want to translate
texts_to_translate = [
    "Settings",
    "Video Settings...",
    "A completely new phrase for the server to learn."
]

# The request payload
payload = {
    "texts": texts_to_translate
}

try:
    response = requests.post(api_url, json=payload)
    
    # Raise an exception if the request was unsuccessful
    response.raise_for_status()
    
    # Parse the JSON response
    translations = response.json()
    
    # Print the results beautifully
    print("--- Translation Results ---")
    for original, translated in translations.items():
        print(f'{original} -> {translated}')

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

```