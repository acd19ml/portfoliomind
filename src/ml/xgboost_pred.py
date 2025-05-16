import pandas as pd
import lightgbm as lgb
import json
import os

# === 1. 加载模型 ===
MODEL_PATH = 'lgbm_model.txt'
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"模型文件不存在：{MODEL_PATH}")
model = lgb.Booster(model_file=MODEL_PATH)

# === 2. 加载最新数据（示例 JSON 文件）===
DATA_PATH = 'latest_data.json'
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"数据文件不存在：{DATA_PATH}")
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
df = pd.DataFrame(data)

# === 3. 筛选与训练一致的特征字段 ===
feature_cols = [
    'symbol', 'time', 'galaxy_score', 'galaxy_score_previous', 'alt_rank', 'alt_rank_previous',
    'market_cap', 'market_cap_rank', 'volume_24h', 'interactions_24h',
    'social_volume_24h', 'social_dominance', 'sentiment',
    'percent_change_1h', 'percent_change_7d', 'percent_change_30d',
    'market_dominance', 'market_dominance_prev', 'volatility'
]
df = df[feature_cols].copy()
df = df.dropna()

# === 4. 独热编码 symbol (确保与训练时逻辑一致) ===
df = pd.get_dummies(df, columns=['symbol'])

# 假设线上获取的数据已经保证了特征列与训练数据一致
# 例如，训练时和线上都按照相同逻辑进行了独热编码

# === 5. 模型预测 ===
y_pred = model.predict(df)
y_pred_label = (y_pred > 0.5).astype(int)

# === 6. 将预测结果附加到 DataFrame 中 ===
df['predicted_label'] = y_pred_label
df['confidence'] = y_pred

# 可以按置信度降序查看预测结果
df = df.sort_values(by='confidence', ascending=False)

# === 7. 输出结果 ===
print("🔮 Top 10 Predictions:")
print(df[['predicted_label', 'confidence']].head(10))

OUTPUT_PATH = 'prediction_result.csv'
df.to_csv(OUTPUT_PATH, index=False)
print(f"✅ 预测结果已保存到：{OUTPUT_PATH}")
