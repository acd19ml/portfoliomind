import pandas as pd
import lightgbm as lgb
import os
from typing import List
from src.tools.crypto_api import get_coins

# === 1. 加载模型 ===
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'lgbm_model.txt')
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"模型文件不存在：{MODEL_PATH}")
model = lgb.Booster(model_file=MODEL_PATH)

def predict_from_coin_data(coins: List) -> pd.DataFrame:
    """
    使用coin_data进行预测
    Args:
        coins: 从get_coins()获取的加密货币数据列表
    Returns:
        包含预测结果的DataFrame
    """
    # 将coin_data转换为DataFrame
    data = []
    for coin in coins:
        data.append({
            'symbol': coin.symbol,
            'time': coin.time if hasattr(coin, 'time') else None,
            'galaxy_score': coin.galaxy_score,
            'galaxy_score_previous': coin.galaxy_score_previous if hasattr(coin, 'galaxy_score_previous') else None,
            'alt_rank': coin.alt_rank,
            'alt_rank_previous': coin.alt_rank_previous if hasattr(coin, 'alt_rank_previous') else None,
            'market_cap': coin.market_cap if hasattr(coin, 'market_cap') else None,
            'market_cap_rank': coin.market_cap_rank,
            'volume_24h': coin.volume_24h if hasattr(coin, 'volume_24h') else None,
            'interactions_24h': coin.interactions_24h,
            'social_volume_24h': coin.social_volume_24h,
            'social_dominance': coin.social_dominance,
            'sentiment': coin.sentiment,
            'percent_change_1h': coin.percent_change_1h if hasattr(coin, 'percent_change_1h') else None,
            'percent_change_7d': coin.percent_change_7d if hasattr(coin, 'percent_change_7d') else None,
            'percent_change_30d': coin.percent_change_30d if hasattr(coin, 'percent_change_30d') else None,
            'market_dominance': coin.market_dominance,
            'market_dominance_prev': coin.market_dominance_prev if hasattr(coin, 'market_dominance_prev') else None,
            'volatility': coin.volatility
        })
    
    df = pd.DataFrame(data)
    print(f"Initial DataFrame shape: {df.shape}")
    
    # Store original symbols before any transformations
    original_symbols = df['symbol'].copy()
    
    # === 3. 筛选与训练一致的特征字段 ===
    feature_cols = [
        'symbol', 'time', 'galaxy_score', 'galaxy_score_previous', 'alt_rank', 'alt_rank_previous',
        'market_cap', 'market_cap_rank', 'volume_24h', 'interactions_24h',
        'social_volume_24h', 'social_dominance', 'sentiment',
        'percent_change_1h', 'percent_change_7d', 'percent_change_30d',
        'market_dominance', 'market_dominance_prev', 'volatility'
    ]
    df = df[feature_cols].copy()
    print(f"After feature selection shape: {df.shape}")
    
    # Check for missing values
    missing_values = df.isnull().sum()
    print("\nMissing values per column:")
    print(missing_values[missing_values > 0])
    
    # Fill missing values with appropriate defaults
    df['time'] = pd.Timestamp.now()  # Use current time for missing time values
    df['galaxy_score_previous'] = df['galaxy_score_previous'].fillna(df['galaxy_score'])  # Use current score if previous is missing
    df['alt_rank_previous'] = df['alt_rank_previous'].fillna(df['alt_rank'])  # Use current rank if previous is missing
    df['sentiment'] = df['sentiment'].fillna(0.0)  # Neutral sentiment for missing values
    df['percent_change_30d'] = df['percent_change_30d'].fillna(0.0)  # No change for missing values
    
    # Drop any remaining rows with missing values in critical fields
    critical_fields = ['symbol', 'galaxy_score', 'alt_rank', 'market_cap_rank', 
                      'interactions_24h', 'social_volume_24h', 'social_dominance']
    df = df.dropna(subset=critical_fields)
    print(f"After handling missing values shape: {df.shape}")
    
    if df.empty:
        raise ValueError("DataFrame is empty after preprocessing. Check the input data and missing values.")

    # Convert numeric columns to appropriate types
    numeric_columns = {
        'galaxy_score': 'float64',
        'galaxy_score_previous': 'float64',
        'alt_rank': 'int64',
        'alt_rank_previous': 'int64',
        'market_cap': 'float64',
        'market_cap_rank': 'int64',
        'volume_24h': 'float64',
        'interactions_24h': 'int64',
        'social_volume_24h': 'int64',
        'social_dominance': 'float64',
        'sentiment': 'float64',
        'percent_change_1h': 'float64',
        'percent_change_7d': 'float64',
        'percent_change_30d': 'float64',
        'market_dominance': 'float64',
        'market_dominance_prev': 'float64',
        'volatility': 'float64'
    }
    
    for col, dtype in numeric_columns.items():
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].astype(dtype)
    
    # Remove time column as it's not needed for prediction
    df = df.drop('time', axis=1)
    
    # Get the feature names from the model
    model_feature_names = model.feature_name()
    print(f"\nModel expects {len(model_feature_names)} features")
    print("\nModel feature names:")
    print(model_feature_names[:10], "...")  # Print first 10 features
    
    # === 4. 独热编码 symbol ===
    # First, get the unique symbols from the model's feature names
    model_symbols = set()
    for feature in model_feature_names:
        if feature.startswith('symbol_'):
            model_symbols.add(feature[7:])  # Remove 'symbol_' prefix
    
    print("\nModel symbols:")
    print(list(model_symbols)[:10], "...")  # Print first 10 symbols
    
    # Filter symbols to only include those present in the model
    df['symbol'] = df['symbol'].apply(lambda x: x if x in model_symbols else 'UNKNOWN')
    
    # Perform one-hot encoding
    symbol_dummies = pd.get_dummies(df['symbol'], prefix='symbol')
    
    # Drop the original symbol column
    df = df.drop('symbol', axis=1)
    
    # Create a dictionary of all features with default values
    feature_dict = {col: 0 for col in model_feature_names}
    
    # Update the dictionary with actual values from numeric features
    for col in df.columns:
        if col in model_feature_names:
            feature_dict[col] = df[col].values
    
    # Update the dictionary with one-hot encoded symbol values
    for col in symbol_dummies.columns:
        if col in model_feature_names:
            feature_dict[col] = symbol_dummies[col].values
    
    # Create the final DataFrame using pd.concat
    template_df = pd.DataFrame(feature_dict, index=df.index)
    
    print(f"\nFinal feature count: {len(template_df.columns)}")
    print("\nInput symbols:")
    print(df.index[:10], "...")  # Print first 10 input symbols
    
    # === 5. 模型预测 ===
    y_pred = model.predict(template_df)
    y_pred_label = (y_pred > 0.35).astype(int)

    # === 6. 将预测结果附加到 DataFrame 中 ===
    # Create result DataFrame with all data at once
    result_df = pd.DataFrame({
        'symbol': df.index,  # Use the original index as symbol
        'predicted_label': y_pred_label.astype('float64'),
        'confidence': y_pred.astype('float64')
    })
    
    # Map the index back to the original symbol
    symbol_map = {i: s for i, s in enumerate(original_symbols)}
    result_df['symbol'] = result_df['symbol'].map(symbol_map)
    
    # 按置信度降序排序
    result_df = result_df.sort_values(by='confidence', ascending=False)
    
    print("\nPrediction results:")
    print(result_df.head())

    return result_df

# 示例使用
if __name__ == "__main__":
    # 获取最新的加密货币数据
    coins = get_coins()
    
    # 进行预测
    df = predict_from_coin_data(coins)
    
    # 输出结果
    print("🔮 Top 10 Predictions:")
    print(df[['predicted_label', 'confidence']].head(10))
    
    # 保存结果
    OUTPUT_PATH = 'prediction_result.csv'
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ 预测结果已保存到：{OUTPUT_PATH}")
