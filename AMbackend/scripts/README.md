# 策略数据导入脚本

## 文件说明

- `export_sample_portfolio.py` - 生成示例策略数据
- `import_sample_portfolio.py` - 导入策略数据到数据库
- `sample_portfolios.json` - 示例策略数据文件

## 使用方法

### 在远程服务器上导入策略数据

1. **确保已登录应用创建用户**

   先访问 http://你的服务器IP 登录一次，创建用户账号

2. **拉取最新代码**

   ```bash
   cd ~/automoney/AutoMoney
   git pull origin main
   ```

3. **运行导入脚本**

   ```bash
   cd ~/automoney/AutoMoney/AMbackend
   source venv/bin/activate

   # 方式1: 自动使用第一个用户
   python scripts/import_sample_portfolio.py

   # 方式2: 指定用户ID
   python scripts/import_sample_portfolio.py 1
   ```

4. **验证导入结果**

   访问策略页面应该能看到 2 个示例策略：
   - 稳健型BTC策略（激活状态）
   - 激进型BTC策略（未激活状态）

## 策略说明

### 稳健型BTC策略

- 执行周期：30分钟
- 买入阈值：55分
- Agent权重：宏观40%、链上40%、技术20%
- 适合稳健投资者

### 激进型BTC策略

- 执行周期：15分钟
- 买入阈值：50分
- Agent权重：宏观25%、链上50%、技术25%
- 适合激进投资者
- 默认未激活（需要手动激活）

## 故障排除

### 问题：提示"用户ID不存在"

**解决：** 先访问网站登录创建用户，然后再运行导入脚本

### 问题：提示"策略已存在"

**解决：** 正常情况，重复运行会自动跳过已存在的策略

### 问题：ModuleNotFoundError

**解决：** 确保在虚拟环境中运行
```bash
source venv/bin/activate
python scripts/import_sample_portfolio.py
```

## 自定义策略

编辑 `sample_portfolios.json` 文件，添加或修改策略配置，然后运行导入脚本。
