# 温度监控系统使用说明

## 系统概述
这是一个完整的硬件温度监控系统，可以定期监控CPU和GPU温度，并将数据保存到JSON文件中。系统还提供了数据可视化功能，可以生成温度变化的线段图表。

## 文件结构
```
Temperature Monitoring/
├── main.py              # 主程序文件（温度监控）
├── chart_generator.py   # 图表生成程序
├── temperature_viewer.html   # 图表网页预览
├── config.json          # 配置文件
├── data.json            # 数据存储文件（自动生成）
├── requirements.txt     # Python依赖包
└── README.md           # 使用说明（本文件）
```

## 安装依赖

### 1. 安装Python包
```bash
pip install -r requirements.txt
```


## 配置文件说明

### config.json 参数
```json
{
    "interval_seconds": 5,          // 监控间隔（秒）
    "monitor_components": {
        "cpu": true,                // 是否监控CPU温度
        "gpu": true                 // 是否监控GPU温度
    },
    "data_file": "data.json",       // 数据保存文件
    "auto_save": true               // 是否自动保存
}
```

## 使用方法

### 1. 运行温度监控
```bash
python main.py
```

程序将按照配置文件的设置开始监控温度，实时显示当前温度并保存到JSON文件。

### 2. 停止监控
按 `Ctrl+C` 停止监控程序。

### 3. 生成温度图表
```bash
python chart_generator.py
```

或者指定数据文件：
```bash
python chart_generator.py your_data_file.json
```
### 4. 使用web工具
使用浏览器打开temperature_viewer.html ，选择生成的data.json文件，会生成一个表格
![image](https://github.com/user-attachments/assets/7d27b46a-e1d1-4b5d-adf4-d8bd23b1ecf5)


## 数据格式

### JSON数据结构
```json
[
    {
        "timestamp": "2025-06-27T10:30:00.123456",
        "datetime": "2025-06-27 10:30:00",
        "cpu_temperature": 45.5,
        "gpu_temperature": 38.2
    },
    {
        "timestamp": "2025-06-27T10:30:05.654321",
        "datetime": "2025-06-27 10:30:05",
        "cpu_temperature": 46.1,
        "gpu_temperature": 39.0
    }
]
```

