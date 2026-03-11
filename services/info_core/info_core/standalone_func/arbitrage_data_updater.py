import pandas as pd
import time
import datetime
from etc.db_handler.mongodb_client import InitDBClient
from loggers.logger import InfoCoreLogger
import traceback
from standalone_func.store_exchange_status import fetch_market_servercheck
    
def store_funding_diff(mongo_db_client, total_enabled_market_klines, head=None, same_exchange=False):
        total_df = pd.DataFrame()
        mongo_db_conn = mongo_db_client.get_conn()

        exchange_list = []
        for each_market_code_combi in total_enabled_market_klines:
            first_market_code, second_market_code = each_market_code_combi.split(":")
            # Check whether first_market_code or second_market_code is in maintenance
            if fetch_market_servercheck(first_market_code) or fetch_market_servercheck(second_market_code):
                # TEST
                print(f"store_funding_diff:{first_market_code} or {second_market_code} is in maintenance.")
                time.sleep(1)
                continue
            first_market, first_quote_asset = first_market_code.split('/')
            first_exchange = first_market.split('_')[0]
            first_market_type = first_market.replace(f'{first_exchange}_','')
            second_market, second_quote_asset = second_market_code.split('/')
            second_exchange = second_market_code.split('_')[0]
            second_market_type = second_market.replace(f'{second_exchange}_','')
            if first_market_type in ["USD_M", "COIN_M"]:
                exchange_list.append(first_exchange)
            if second_market_type in ["USD_M", "COIN_M"]:
                exchange_list.append(second_exchange)
        exchange_list = list(set(exchange_list))
        perpetual_tup_list = []
        for each_exchange in exchange_list:
            for each_market_type in ['USD_M', 'COIN_M']:
                perpetual_tup_list.append((each_exchange, each_market_type))

        perpetual_combination_list = []
        for i, perpetual_tup_one in enumerate(perpetual_tup_list):
            for perpetual_tup_two in perpetual_tup_list[i+1:]:
                perpetual_combination_list.append((perpetual_tup_one, perpetual_tup_two))

        for perpetual_combination in perpetual_combination_list:
            perpetual_one = perpetual_combination[0]
            perpetual_two = perpetual_combination[1]

            mongo_db = mongo_db_conn[f"{perpetual_one[0]}_fundingrate"]
            mongo_db_collection = mongo_db[f"{perpetual_one[1]}"]

            pipeline = [
                # {"$match": {"quote_asset": perpetual_one[2], "perpetual":True}},
                {"$match": {"perpetual":True}},
                {"$sort": {"datetime_now": -1}},
                {"$group": {
                    "_id": "$symbol",  # Group by symbol
                    "latest_document": {"$first": "$$ROOT"}  # Get the first document after sorting (i.e., the latest)
                }}
            ]

            # Execute the aggregation pipeline
            result = list(mongo_db_collection.aggregate(pipeline))

            # Now `result` will have the latest document for each symbol with 'quote_asset'
            # Convert the result into a DataFrame
            # The latest documents are under 'latest_document' in the result
            latest_documents = [doc['latest_document'] for doc in result]
            if not latest_documents:
                # Skip if no funding data available for this exchange/market_type
                continue
            funding_df1 = pd.DataFrame(latest_documents).drop(columns=["_id", "perpetual"], errors='ignore')
            funding_df1['market_code'] = f"{perpetual_one[0]}_{perpetual_one[1]}"
            funding_df1['exchange'] = perpetual_one[0]

            # For funding_df2
            mongo_db = mongo_db_conn[f"{perpetual_two[0]}_fundingrate"]
            mongo_db_collection = mongo_db[f"{perpetual_two[1]}"]

            pipeline = [
                # {"$match": {"quote_asset": perpetual_two[2], "perpetual":True}},
                {"$match": {"perpetual":True}},
                {"$sort": {"datetime_now": -1}},
                {"$group": {
                    "_id": "$symbol",  # Group by symbol
                    "latest_document": {"$first": "$$ROOT"}  # Get the first document after sorting (i.e., the latest)
                }}
            ]

            # Execute the aggregation pipeline
            result = list(mongo_db_collection.aggregate(pipeline))

            # Now `result` will have the latest document for each symbol with 'quote_asset'
            # Convert the result into a DataFrame
            # The latest documents are under 'latest_document' in the result
            latest_documents = [doc['latest_document'] for doc in result]
            if not latest_documents:
                # Skip if no funding data available for this exchange/market_type
                continue
            funding_df2 = pd.DataFrame(latest_documents).drop(columns=["_id", "perpetual"], errors='ignore')
            funding_df2['market_code'] = f"{perpetual_two[0]}_{perpetual_two[1]}"
            funding_df2['exchange'] = perpetual_two[0]

            merged_df = funding_df1.merge(funding_df2, on='base_asset', how='inner')
            total_df = pd.concat([total_df, merged_df], axis=0)

        # Handle empty total_df (no funding data available for any exchange combination)
        if total_df.empty:
            return total_df

        total_df['funding_rate_diff'] = (total_df['funding_rate_x'] - total_df['funding_rate_y']).abs()
        total_df['last_update'] = datetime.datetime.utcnow()
        total_df = total_df.sort_values(by=['funding_rate_diff'], ascending=False).reset_index(drop=True)
        if same_exchange:
            total_df = total_df[total_df['market_code_x'].str.split('_').str[0]==total_df['market_code_y'].str.split('_').str[0]].reset_index(drop=True)
        if head is not None:
            total_df = total_df.head(head)

        # Save into Mongo DB
        fundingrate_diff_db_name = 'arbitrage_fundingrate'
        fundingrate_diff_db = mongo_db_conn[fundingrate_diff_db_name]
        fundingrate_diff_collection = fundingrate_diff_db['diff']
        temp_fundingrate_diff_collection = fundingrate_diff_db['temp_diff']
        temp_fundingrate_diff_collection.delete_many({})
        temp_fundingrate_diff_collection.insert_many(total_df.to_dict('records'))
        fundingrate_diff_db['temp_diff'].rename('diff', dropTarget=True)
        # NOTE: Do NOT close the connection - we use connection pooling now
        return total_df
    
def store_funding_diff_loop(total_enabled_market_klines, mongodb_dict, logging_dir, loop_time_secs=60):
    logger = InfoCoreLogger("arbitrage_core", logging_dir).logger
    logger.info(f"store_funding_diff_loop started.")
    mongo_db_client = InitDBClient(**mongodb_dict)
    while True:
        try:
            start = time.time()
            store_funding_diff(mongo_db_client, total_enabled_market_klines)
            logger.info(f"store_funding_diff took {time.time()-start} seconds.")
        except Exception as e:
            logger.error(f"Error in store_arbitrage_diff_loop: {e}\n{traceback.format_exc()}")
        time.sleep(loop_time_secs)
        
        
def store_average_funding_rate(mongo_db_client, total_enabled_market_klines, logger, maximum_history_depth=100):
        total_df = pd.DataFrame()
        mongo_db_conn = mongo_db_client.get_conn()

        exchange_list = []
        for each_market_code_combi in total_enabled_market_klines:
            first_market_code, second_market_code = each_market_code_combi.split(":")
            # Check whether first_market_code or second_market_code is in maintenance
            if fetch_market_servercheck(first_market_code) or fetch_market_servercheck(second_market_code):
                # TEST
                print(f"store_average_funding_rate:{first_market_code} or {second_market_code} is in maintenance.")
                time.sleep(1)
                continue
            first_market, first_quote_asset = first_market_code.split('/')
            first_exchange = first_market.split('_')[0]
            first_market_type = first_market.replace(f'{first_exchange}_','')
            second_market, second_quote_asset = second_market_code.split('/')
            second_exchange = second_market_code.split('_')[0]
            second_market_type = second_market.replace(f'{second_exchange}_','')
            if first_market_type in ["USD_M", "COIN_M"]:
                exchange_list.append(first_exchange)
            if second_market_type in ["USD_M", "COIN_M"]:
                exchange_list.append(second_exchange)
        exchange_list = list(set(exchange_list))
        perpetual_tup_list = []
        for each_exchange in exchange_list:
            for each_market_type in ['USD_M', 'COIN_M']:
                perpetual_tup_list.append((each_exchange, each_market_type))

        perpetual_combination_list = []
        for i, perpetual_tup_one in enumerate(perpetual_tup_list):
            for perpetual_tup_two in perpetual_tup_list[i+1:]:
                perpetual_combination_list.append((perpetual_tup_one, perpetual_tup_two))

        for perpetual_tup in perpetual_tup_list:
            exchange = perpetual_tup[0]
            market_type = perpetual_tup[1]
            mongo_db = mongo_db_conn[f"{exchange}_fundingrate"]
            mongo_db_collection = mongo_db[f"{market_type}"]

            pipeline = [
                {"$match": {"perpetual": True}},
                {"$sort": {"datetime_now": -1}},
                {"$group": {
                    "_id": "$symbol",  # Group by symbol
                    "recent_documents": {"$push": "$$ROOT"}  # Collect all documents in an array
                }},
                {"$project": {
                    "recent_documents": {"$slice": ["$recent_documents", maximum_history_depth]}
                }}
            ]

            # Execute the aggregation pipeline
            result = list(mongo_db_collection.aggregate(pipeline))

            # Now `result` will have the latest document for each symbol with 'quote_asset'
            # Convert the result into a DataFrame
            # The latest documents are under 'latest_document' in the result
            nested_recent_documents = [doc['recent_documents'] for doc in result]
            flattened_recent_documents = [item for sublist in nested_recent_documents for item in sublist]
            if not flattened_recent_documents:
                # Skip if no funding data available for this exchange/market_type
                continue
            funding_df = pd.DataFrame(flattened_recent_documents).drop(columns=["_id", "perpetual"], errors='ignore')
            funding_df['market_code'] = f"{exchange}_{market_type}"
            total_df = pd.concat([total_df, funding_df], axis=0)

        # Handle empty total_df (no funding data available for any exchange)
        if total_df.empty:
            return

        total_df = total_df.sort_values('funding_time', ascending=False).reset_index(drop=True)

        average_df = None
        for i in range(1, maximum_history_depth+1):
            new_averaged_df = total_df.groupby(['symbol','base_asset','quote_asset','market_code']).head(i)[['symbol','base_asset','quote_asset','market_code','funding_rate']].groupby(['symbol','base_asset','quote_asset','market_code']).mean().reset_index()
            # Check whether new_averaged_df is same as average_df
            if average_df is not None:
                if new_averaged_df.equals(average_df):
                    logger.info(f"recent_{i}_fundingrate_mean is the same as recent_{i-1}_fundingrate_mean.") # TEST
                    break
                else:
                    average_df = new_averaged_df
            else:
                average_df = new_averaged_df
            average_df['last_update'] = datetime.datetime.utcnow()
            
            arbitrage_collection_name = f"recent_{i}_fundingrate_mean"
            temp_arbitrage_collection_name = f"temp_{i}_fundingrate_mean"
            arbitrage_fundingrate_db = mongo_db_conn['arbitrage_fundingrate']
            temp_arbitrage_fundingrate_collection = arbitrage_fundingrate_db[temp_arbitrage_collection_name]
            temp_arbitrage_fundingrate_collection.delete_many({})
            temp_arbitrage_fundingrate_collection.insert_many(average_df.sort_values('funding_rate', ascending=False).to_dict('records'))
            temp_arbitrage_fundingrate_collection.rename(arbitrage_collection_name, dropTarget=True)
        # NOTE: Do NOT close the connection - we use connection pooling now
        return
    
def store_average_funding_loop(total_enabled_market_klines, mongodb_dict, logging_dir, loop_time_secs=120):
        logger = InfoCoreLogger("arbitrage_core", logging_dir).logger
        logger.info(f"store_average_funding_rate_loop started.")
        mongo_db_client = InitDBClient(**mongodb_dict)
        while True:
            try:
                start = time.time()
                store_average_funding_rate(mongo_db_client, total_enabled_market_klines, logger)
                logger.info(f"store_average_funding_rate took {time.time()-start} seconds.")
            except Exception as e:
                logger.error(f"Error in store_average_funding_rate_loop: {e}")
            time.sleep(loop_time_secs)
            
def remove_delisted_funding_rate(mongo_db_client, total_enabled_market_klines, logger, old_timewindow_hours=16):
        mongo_db_conn = mongo_db_client.get_conn()
        
        exchange_list = []
        for each_market_code_combi in total_enabled_market_klines:
            first_market_code, second_market_code = each_market_code_combi.split(":")
            first_market, first_quote_asset = first_market_code.split('/')
            first_exchange = first_market.split('_')[0]
            first_market_type = first_market.replace(f'{first_exchange}_','')
            second_market, second_quote_asset = second_market_code.split('/')
            second_exchange = second_market_code.split('_')[0]
            second_market_type = second_market.replace(f'{second_exchange}_','')
            if first_market_type in ["USD_M", "COIN_M"]:
                exchange_list.append(first_exchange)
            if second_market_type in ["USD_M", "COIN_M"]:
                exchange_list.append(second_exchange)
        exchange_list = list(set(exchange_list))
        perpetual_tup_list = []
        for each_exchange in exchange_list:
            for each_market_type in ['USD_M', 'COIN_M']:
                perpetual_tup_list.append((each_exchange, each_market_type))
                
        for perpetual_tup in perpetual_tup_list:
            exchange = perpetual_tup[0]
            market_type = perpetual_tup[1]
            mongo_db = mongo_db_conn[f"{exchange}_fundingrate"]
            mongo_db_collection = mongo_db[f"{market_type}"]
            
            pipeline = [
                {"$match": {"perpetual": True}},
                {"$sort": {"datetime_now": -1}},
                {"$group": {
                    "_id": "$symbol",  # Group by symbol
                    "latest_document": {"$first": "$$ROOT"}  # Get the first document after sorting (i.e., the latest)
                }}
            ]
            
            # Execute the aggregation pipeline
            result = list(mongo_db_collection.aggregate(pipeline))
            
            # Now `result` will have the latest document for each symbol with 'quote_asset'
            # Convert the result into a DataFrame
            # The latest documents are under 'latest_document' in the result
            latest_documents = [doc['latest_document'] for doc in result]
            if not latest_documents:
                # Skip if no funding data available for this exchange/market_type
                continue
            funding_df = pd.DataFrame(latest_documents).drop(columns=["_id", "perpetual"], errors='ignore')

            # Find symbols whose funding_time is older than current time - old_timewindow_hours
            funding_df['funding_time'] = pd.to_datetime(funding_df['funding_time'])
            funding_df = funding_df[funding_df['funding_time'] < datetime.datetime.utcnow() - datetime.timedelta(hours=old_timewindow_hours)]
            delisted_symbols = list(funding_df['symbol'].values)
            # Delete
            mongo_db_collection.delete_many({"symbol": {"$in": delisted_symbols}})
            # Log
            logger.info(f"Deleting funding_rate data for {exchange}_{market_type} delisted symbols: {delisted_symbols}")
        # NOTE: Do NOT close the connection - we use connection pooling now
        return
    
def remove_delisted_funding_rate_loop(total_enabled_market_klines, mongodb_dict, logging_dir, loop_time_secs=3600):
        logger = InfoCoreLogger("arbitrage_core", logging_dir).logger
        logger.info(f"remove_delisted_funding_rate_loop started.")
        mongo_db_client = InitDBClient(**mongodb_dict)
        while True:
            try:
                start = time.time()
                remove_delisted_funding_rate(mongo_db_client, total_enabled_market_klines, logger)
                logger.info(f"remove_delisted_funding_rate took {time.time()-start} seconds.")
            except Exception as e:
                logger.error(f"Error in remove_delisted_funding_rate_loop: {e}")
            time.sleep(loop_time_secs)