# 网络工具集 (Network Tools)

这是一个基于Python和PyQt6开发的网络工具集合，提供多种网络管理和分析功能，帮助网络管理员和IT专业人员更高效地完成日常工作。

## 功能特性

本工具集包含以下主要功能模块：

### 1. IP计算器
- IP地址详细信息查询
- 支持IPv4地址格式
- 显示网络地址、广播地址、子网掩码等信息
- 提供二进制、十六进制等多种格式显示

### 2. 子网计算器
- 根据需求划分子网
- 支持按子网数量或主机数量划分
- 生成详细的子网划分表

### 3. 掩码转换器
- 在CIDR格式和传统子网掩码格式之间转换
- 批量处理多个网络地址

### 4. 路由汇总
- 将多个路由条目汇总为更少的路由条目
- 支持精确汇总和非精确汇总
- 显示汇总前后的IP数量对比

### 5. 网络分析器
- 解析IP地址的地理位置信息
- 提供网络连通性测试
- 支持批量分析多个IP地址

### 6. NAT解析器
- 解析华为和H3C设备的NAT配置命令
- 支持多种NAT命令格式
- 可导出为Excel格式的映射表

### 7. VSR配置生成器
- 根据模板生成华为VSR路由器配置
- 支持自定义配置参数

## 安装与使用

### 系统要求
- Python 3.8+
- Windows/Linux/macOS

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行程序
```bash
python src/main.py
```

## NAT命令解析器说明

NAT命令解析器支持以下格式的命令：

### 1. 两个标识符 + protocol格式
```
nat server taiyuewangguan9 9 protocol tcp global 119.6.207.249 16079 inside 172.17.0.14 16079 no-reverse
```

### 2. 单个标识符 + protocol格式
```
nat server 99 protocol tcp global 119.6.207.248 30017 inside 172.18.1.50 27017 no-reverse
```

### 3. 两个标识符但没有protocol关键字
```
nat server 93 93 global 221.179.228.158 inside 172.17.4.80 no-reverse
```

### 4. 简化格式（单个标识符 + global）
```
nat server "vpn5 for liantong" global 119.6.207.197 inside 172.17.0.84 no-reverse
```

特殊处理：
- 支持带引号的标识符（包含空格的名称）
- 所有标识符都被视为名称，包括数字标识符
- 在有两个标识符的情况下，使用第一个标识符作为名称

## 开发说明

### 项目结构
```
network_tools/
├── resources/           # 资源文件
│   ├── icons/           # 图标文件
│   └── ip2region.xdb    # IP地址数据库
├── src/                 # 源代码
│   ├── gui/             # 图形界面
│   │   ├── tabs/        # 各功能选项卡
│   │   └── styles.py    # 界面样式
│   ├── templates/       # 配置模板
│   ├── utils/           # 工具类
│   ├── config.py        # 配置文件
│   └── main.py          # 主程序入口
└── requirements.txt     # 依赖列表
```

### 技术栈
- Python 3.8+
- PyQt6 (GUI框架)
- ipaddress (IP地址处理)
- openpyxl (Excel文件处理)
- jinja2 (模板引擎)

## 许可证

MIT License

## 贡献

欢迎提交问题和功能请求，也欢迎提交Pull Request。
