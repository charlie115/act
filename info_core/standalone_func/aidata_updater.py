import pandas as pd
import time
import datetime
from etc.db_handler.mongodb_client import InitDBClient
from etc.redis_connector.redis_helper import RedisHelper
from loggers.logger import InfoCoreLogger
import traceback
from standalone_func.store_exchange_status import fetch_market_servercheck
import numpy as np
from google import genai
import _pickle as pickle
import json
import concurrent.futures
from google.api_core.exceptions import DeadlineExceeded, GoogleAPIError

def get_volatility_data(market_code_combination, mongodb_client, collection_name='volatility_info'):
    """
    Fetch volatility data from MongoDB for a given market combination
    
    Args:
        market_code_combination (str): Market code combination in format 'MARKET1:MARKET2'
        mongodb_client (InitDBClient): Initialized MongoDB client instance
        
    Returns:
        pd.DataFrame: DataFrame containing volatility data
    """
    db_name = market_code_combination.replace('/', '__').replace(':', '-')
    # Fetch the collection
    mongo_db_conn = mongodb_client.get_conn()
    db = mongo_db_conn[db_name]

    # Get the collection
    collection = db[collection_name]

    # Fetch all the data, exclude the _id field
    volatility_data = collection.find({}, {"_id": 0})

    # Convert the data to a pandas DataFrame
    volatility_data_df = pd.DataFrame(list(volatility_data))

    # close the connection
    mongo_db_conn.close()
    
    return volatility_data_df

market_code_combination = 'UPBIT_SPOT/KRW:BINANCE_USD_M/USDT'


def get_funding_data(market_code, mongodb_client):
    """
    Fetch funding data from MongoDB for a given market code
    
    Args:
        market_code (str): Market code, e.g. 'UPBIT_SPOT/KRW'
        mongodb_client (InitDBClient): Initialized MongoDB client instance
    
    Returns:
        pd.DataFrame: DataFrame containing funding data
    """
    market = market_code.split('/')[0]
    quote_asset = market_code.split('/')[1]
    exchange = market.split('_')[0]
    margin_type = '_'.join(market.split('_')[1:])
    db_name = f"{exchange}_fundingrate"
    # Fetch the collection
    mongo_db_conn = mongodb_client.get_conn()
    db = mongo_db_conn[db_name]
    
    # Get the collection
    collection = db[margin_type]

    # Use MongoDB aggregation to get latest record for each symbol in single query
    pipeline = [
        {"$match": {"quote_asset": quote_asset, "perpetual": True}},
        {"$sort": {"datetime_now": -1}},
        {"$group": {
            "_id": "$symbol",
            "latest_record": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$latest_record"}},
        {"$project": {"_id": 0}}
    ]
    funding_data = list(collection.aggregate(pipeline))
    
    # Convert the data to a pandas DataFrame
    funding_data_df = pd.DataFrame(list(funding_data))

    # close the connection
    mongo_db_conn.close()
    
    return funding_data_df

def get_kline_now_data(market_code_combination, local_redis):
    while True:
        kline_data = local_redis.get_data(f'INFO_CORE|{market_code_combination}_1T_now')
        if kline_data is not None:
            break
        time.sleep(1)
    kline_1T_df = pickle.loads(kline_data)[['base_asset','tp','LS_close','SL_close','atp24h']]
    kline_1T_df['spread'] = kline_1T_df['SL_close'] - kline_1T_df['LS_close']
    kline_1T_df['atp24h'] = kline_1T_df['atp24h'].astype(float)
    kline_1T_df['tp'] = kline_1T_df['tp'].astype(float)
    kline_1T_df['LS_close'] = kline_1T_df['LS_close'].astype(float)
    kline_1T_df['SL_close'] = kline_1T_df['SL_close'].astype(float)
    kline_1T_df['base_asset'] = kline_1T_df['base_asset'].astype(str)
    return kline_1T_df

def get_merged_data(market_code_combination, local_redis, mongodb_client):
    if 'SPOT' in market_code_combination.split(':')[0] and 'SPOT' not in market_code_combination.split(':')[1]:
        volatility_data = get_volatility_data(market_code_combination, mongodb_client)
        funding_data = get_funding_data(market_code_combination.split(':')[1], mongodb_client)
        kline_now_data = get_kline_now_data(market_code_combination, local_redis)
        
        # Merge volatility data into kline_now_data
        kline_now_data = pd.merge(kline_now_data, volatility_data, on='base_asset', how='left')
        
        # Merge funding data into kline_now_data
        funding_data = funding_data[['base_asset', 'funding_rate', 'funding_time']]
        kline_now_data = pd.merge(kline_now_data, funding_data, on='base_asset', how='left')
        kline_now_data['LS_close'] = kline_now_data['LS_close'].astype(float).round(3)
        kline_now_data['SL_close'] = kline_now_data['SL_close'].astype(float).round(3)
        kline_now_data['LS_z_score'] = ((kline_now_data['LS_close'] - kline_now_data['LS_close'].mean()) / kline_now_data['LS_close'].std()).round(3)
        kline_now_data['atp24h'] = kline_now_data['atp24h'].astype(float).round(0)
        # kline_now_data['atp24h_z_score'] = ((kline_now_data['atp24h'] - kline_now_data['atp24h'].mean()) / kline_now_data['atp24h'].std()).round(3)
        kline_now_data['spread'] = kline_now_data['spread'].astype(float).round(3)
        kline_now_data['abs_spread'] = kline_now_data['spread'].abs()
        # kline_now_data['abs_spread_z_score'] = ((kline_now_data['abs_spread'] - kline_now_data['abs_spread'].mean()) / kline_now_data['abs_spread'].std()).round(3)
        kline_now_data['mean_diff'] = kline_now_data['mean_diff'].astype(float).round(3)
        # kline_now_data['mean_diff_z_score'] = ((kline_now_data['mean_diff'] - kline_now_data['mean_diff'].mean()) / kline_now_data['mean_diff'].std()).round(3)
        kline_now_data['funding_rate'] = (kline_now_data['funding_rate'].astype(float) * 100).round(4)
        kline_now_data.drop(columns=['funding_time'], inplace=True)
        # Move LS_z_score next to LS_close
        ls_close_idx = kline_now_data.columns.get_loc('LS_close')
        kline_now_data.insert(ls_close_idx + 1, 'LS_z_score', kline_now_data.pop('LS_z_score'))
        
        # # Move atp24h_z_score next to atp24h
        # atp24h_idx = kline_now_data.columns.get_loc('atp24h')
        # kline_now_data.insert(atp24h_idx + 1, 'atp24h_z_score', kline_now_data.pop('atp24h_z_score'))
        
        # Move abs_spread next to spread
        spread_idx = kline_now_data.columns.get_loc('spread')
        kline_now_data.insert(spread_idx + 1, 'abs_spread', kline_now_data.pop('abs_spread'))
        kline_now_data.drop(columns=['spread'], inplace=True)
        
        # # Move abs_spread_z_score next to abs_spread
        # spread_idx = kline_now_data.columns.get_loc('abs_spread')
        # kline_now_data.insert(spread_idx + 1, 'abs_spread_z_score', kline_now_data.pop('abs_spread_z_score'))
        
        # # Move mean_diff_z_score next to mean_diff
        # mean_diff_idx = kline_now_data.columns.get_loc('mean_diff')
        # kline_now_data.insert(mean_diff_idx + 1, 'mean_diff_z_score', kline_now_data.pop('mean_diff_z_score'))
        
        return kline_now_data
    else:
        raise ValueError("Invalid market code combination. Currently only supports SPOT to Futures")

def generate_ai_recommendation_data(market_code_combination, ai_api_key, local_redis, mongodb_client, logger, timeout=60):
    merged_df = get_merged_data(market_code_combination, local_redis, mongodb_client).head(50)

    origin_market_code, target_market_code = market_code_combination.split(':')
    system_prompt = f"""Below is the premium data of crypto currencies between {origin_market_code} and {target_market_code}.

    You are a professional crypto analyst specializing in arbitrage trading. Analyze the provided data and generate a ranked list of the top 10 recommended cryptocurrencies for arbitrage trading, along with a brief explanation(3 ~ 4 sentences) without mentioning column names for each recommendation in Korean.

    The arbitrage trade is executed as follows:
    - **Enter trade**: Long target market (SPOT), Short origin market (FUTURES)
    - **Exit trade**: Short target market (SPOT), Long origin market (FUTURES)
    ** Since the premium gap between Enter trade and Exit trade leads to the profit, high mean_diff(premium movement) is very important.

    To maximize profit, the investor should execute the Enter trade when `LS_close` is low and the Exit trade when `SL_close` is high. A higher `mean_diff` indicates more potential arbitrage opportunities.

    The data includes the following columns:
    - **base_asset**: Name of the cryptocurrency
    - **LS_close**: Premium percentage for Enter trade. Premiums significantly higher than the average across all cryptocurrencies may indicate a higher risk of mean reversion, potentially reducing profitability.
    - **SL_close**: Premium percentage for Exit trade. Similarly, premiums significantly higher than the average may indicate a higher risk of mean reversion.
    - **LS_z_score**: Z-score of `LS_close`. A higher value indicates a higher risk of mean reversion.
    - **atp24h**: 24-hour trading volume in KRW. Higher values indicate better liquidity, which is essential for efficient arbitrage trading.
    - **abs_spread**: Absolute difference between `LS_close` and `SL_close`. A smaller spread (close to 0) is better, indicating less slippage.
    - **mean_diff**: Standard deviation of the last 180 minutes of premium movement. Higher values present more arbitrage opportunities. It's not a risk factor. Rather, if it's too low, it's not a good opportunity.
    - **funding_rate**: Funding rate percentage for the origin market. A positive funding rate is preferable, as it means the short position receives payments from the long position, potentially increasing profitability. A negative funding rate is less desirable, as the short position must pay the long position. If it's lower than -0.3%, it's risky.

    **Task**:
    Rank the top 10 cryptocurrencies based on their arbitrage potential, considering the following factors:
    - Low `abs_spread` (for minimal slippage)
    - High `mean_diff` (very important for arbitrage opportunities, high mean_diff is not a risk factor. rather, if it's too low, it's might not be profitable since there might be less premium movement)
    - High `atp24h` (for liquidity)
    - Avoid too low(lower than -0.3%) `funding_rate` (for risk management)
    - Avoid high `LS_close` and `SL_close` compared to other cryptocurrencies (for risk management)

    When ranking, prioritize cryptocurrencies that offer a good balance of these factors to optimize profitability while managing risk. For each recommendation, provide a brief explanation in Korean, including a mention of the risk level associated with the recommendation (e.g., due to premium levels or spread or atp24h).
    Also, the risk level should be 1~3, and all recommendations should be evenly dispersed based on each risk level.

    **Output Format**:
    [
        {{
            "rank": "rank",
            "base_asset": "base_asset",
            "risk_level": "risk_level", // 1~3, all recommendations should be allocated to 1~3
            "explanation": "explanation in Korean",
        }},
        ...
    ]
    
    **Note**:
    - Do not include raw column names in explanation.
    - Do not forget to consider all factores.
    """

    input_data = merged_df.drop(columns=['tp','datetime_now']).to_csv()

    client = genai.Client(api_key=ai_api_key)
    
    # Define the function to make the API call
    def call_api():
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-thinking-exp-01-21", 
                contents=system_prompt + "\n\n" + input_data,
                config={"temperature": 0}
            )
            return response.text
        except (DeadlineExceeded, GoogleAPIError) as e:
            return f"API Error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    # Execute the API call with a timeout
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(call_api)
        try:
            result = future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"AI API request timed out after {timeout} seconds")
    
    # Check if result contains an error message
    if isinstance(result, str) and (result.startswith("API Error") or result.startswith("Unexpected error")):
        raise RuntimeError(f"Error in AI API call: {result}")
    
    try:
        result_list = json.loads(result.replace("```json", "").replace("```", ""))
        return result_list
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}. result: {result}...")
        raise ValueError(f"Failed to parse AI response as JSON: {e}. Response: {result[:200]}...")

def store_ai_recommendation_data(market_code_combination, ai_api_key, mongo_db_dict, logger=None):
    try:
        local_redis = RedisHelper()
        mongodb_client = InitDBClient(**mongo_db_dict)
        database = market_code_combination.replace('/', '__').replace(':', '-')
        mongo_db_conn = mongodb_client.get_conn()
        db = mongo_db_conn[database]

        # Use the temporary collection in the target database
        temp_collection = db['ai_recommendation_info_temp']
        
        try:
            # Try to get AI recommendations with timeout handling
            ai_recommendation_data = generate_ai_recommendation_data(
                market_code_combination, 
                ai_api_key, 
                local_redis, 
                mongodb_client,
                logger,
                timeout=60  # Adjust timeout as needed
            )
        except TimeoutError as e:
            logger.error(f"AI API request timed out: {e}")
            return
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {e}\n{traceback.format_exc()}")
            return

        ai_recommendation_data_list = []
        for each_recommendation in ai_recommendation_data:
            # columns should be rank, base_asset, risk_level, explanation, datetime_now
            try:
                data = {
                    'rank': each_recommendation['rank'],
                    'base_asset': each_recommendation['base_asset'],
                    'risk_level': each_recommendation['risk_level'],
                    'explanation': each_recommendation['explanation'],
                    'datetime_now': datetime.datetime.utcnow()
                }
            except Exception as e:
                logger.error(f"An error occurred during storing ai recommendation data: {e}\n{traceback.format_exc()}")
                continue
            ai_recommendation_data_list.append(data)

        # Clear the temporary collection (optional, since we're overwriting)
        temp_collection.delete_many({})

        # Insert data into the temporary collection
        if ai_recommendation_data_list:
            temp_collection.insert_many(ai_recommendation_data_list)
        else:
            logger.info("No data to insert.")
            
        # Rename 'ai_recommendation_info_temp' to 'ai_recommendation_info', dropping the target if it exists
        temp_collection.rename('ai_recommendation_info', dropTarget=True)
        logger.info(f"AI recommendation data for {market_code_combination}, length: {len(ai_recommendation_data_list)}, stored in {database}.")
    except Exception as e:
        logger.error(f"An error occurred during storing ai recommendation data: {e}\n{traceback.format_exc()}")
    finally:
        mongo_db_conn.close()
        
def store_ai_recommendation_data_loop(market_code_combination, ai_api_key, mongo_db_dict, logger):
    if 'SPOT' in market_code_combination.split(':')[0] and 'SPOT' not in market_code_combination.split(':')[1]:
        while True:
            try:
                store_ai_recommendation_data(market_code_combination, ai_api_key, mongo_db_dict, logger)
            except Exception as e:
                logger.error(f"An error occurred during storing ai recommendation data: {e}\n{traceback.format_exc()}")
            finally:
                time.sleep(300)
    else:
        raise ValueError("Invalid market code combination. Currently only supports SPOT to Futures")
