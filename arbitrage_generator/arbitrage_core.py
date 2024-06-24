import pandas as pd
import json
import time
import datetime
from threading import Thread
import numpy as np
import os
import sys
from multiprocessing import Process
import traceback

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger
from etc.db_handler.mongodb_client import InitDBClient

class InitAbitrageCore:
    def __init__(self, admin_id, node, info_dict, register_monitor_msg, total_enabled_market_klines, db_client, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.info_dict = info_dict
        self.register_monitor_msg = register_monitor_msg
        self.total_enabled_market_klines = total_enabled_market_klines
        self.db_client = db_client
        self.logger = KimpBotLogger("arbitrage_core", logging_dir).logger
        self.logger.info(f"InitArbitrageCore Started.")
        self.store_funding_diff_proc = Process(target=self.store_funding_diff_loop, daemon=True)
        self.store_funding_diff_proc.start()
        self.store_average_fundingrate_proc = Process(target=self.store_average_funding_loop, daemon=True)
        self.store_average_fundingrate_proc.start()
        self.remove_delisted_funding_rate_proc = Process(target=self.remove_delisted_funding_rate_loop, daemon=True)
        self.remove_delisted_funding_rate_proc.start()
    
    def store_funding_diff_loop(self, loop_time_secs=60):
        self.logger.info(f"store_funding_diff_loop started.")
        while True:
            try:
                start = time.time()
                self.store_funding_diff()
                self.logger.info(f"store_funding_diff took {time.time()-start} seconds.")
            except Exception as e:
                self.logger.error(f"Error in store_arbitrage_diff_loop: {e}\n{traceback.format_exc()}")
            time.sleep(loop_time_secs)

    def store_average_funding_loop(self, loop_time_secs=120):
        self.logger.info(f"store_average_funding_rate_loop started.")
        while True:
            try:
                start = time.time()
                self.store_average_funding_rate()
                self.logger.info(f"store_average_funding_rate took {time.time()-start} seconds.")
            except Exception as e:
                self.logger.error(f"Error in store_average_funding_rate_loop: {e}")
            time.sleep(loop_time_secs)
            
    def remove_delisted_funding_rate_loop(self, loop_time_secs=3600):
        self.logger.info(f"remove_delisted_funding_rate_loop started.")
        while True:
            try:
                start = time.time()
                self.remove_delisted_funding_rate()
                self.logger.info(f"remove_delisted_funding_rate took {time.time()-start} seconds.")
            except Exception as e:
                self.logger.error(f"Error in remove_delisted_funding_rate_loop: {e}")
            time.sleep(loop_time_secs)

    def store_funding_diff(self, head=None, same_exchange=False):
        total_df = pd.DataFrame()
        mongo_db_conn = self.db_client.get_conn()

        exchange_list = []
        for each_market_code_combi in self.total_enabled_market_klines:
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
            funding_df1 = pd.DataFrame(latest_documents).drop(columns=["_id", "perpetual"])
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
            funding_df2 = pd.DataFrame(latest_documents).drop(columns=["_id", "perpetual"])
            funding_df2['market_code'] = f"{perpetual_two[0]}_{perpetual_two[1]}"
            funding_df2['exchange'] = perpetual_two[0]

            merged_df = funding_df1.merge(funding_df2, on='base_asset', how='inner')
            total_df = pd.concat([total_df, merged_df], axis=0)
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
        mongo_db_conn.close()
        return total_df

    def store_average_funding_rate(self, maximum_history_depth=100):
        total_df = pd.DataFrame()
        mongo_db_conn = self.db_client.get_conn()

        exchange_list = []
        for each_market_code_combi in self.total_enabled_market_klines:
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
            funding_df = pd.DataFrame(flattened_recent_documents).drop(columns=["_id", "perpetual"])
            funding_df['market_code'] = f"{exchange}_{market_type}"
            total_df = pd.concat([total_df, funding_df], axis=0)

        total_df = total_df.sort_values('funding_time', ascending=False).reset_index(drop=True)

        average_df = None
        for i in range(1, maximum_history_depth+1):
            new_averaged_df = total_df.groupby(['symbol','base_asset','quote_asset','market_code']).head(i)[['symbol','base_asset','quote_asset','market_code','funding_rate']].groupby(['symbol','base_asset','quote_asset','market_code']).mean().reset_index()
            # Check whether new_averaged_df is same as average_df
            if average_df is not None:
                if new_averaged_df.equals(average_df):
                    self.logger.info(f"recent_{i}_fundingrate_mean is the same as recent_{i-1}_fundingrate_mean.") # TEST
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
        mongo_db_conn.close()
        return
    
    def remove_delisted_funding_rate(self, old_timewindow_hours=16):
        mongo_db_conn = self.db_client.get_conn()
        
        exchange_list = []
        for each_market_code_combi in self.total_enabled_market_klines:
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
            funding_df = pd.DataFrame(latest_documents).drop(columns=["_id", "perpetual"])
            
            # Find symbols whose funding_time is older than current time - old_timewindow_hours
            funding_df['funding_time'] = pd.to_datetime(funding_df['funding_time'])
            funding_df = funding_df[funding_df['funding_time'] < datetime.datetime.utcnow() - datetime.timedelta(hours=old_timewindow_hours)]
            delisted_symbols = list(funding_df['symbol'].values)
            # Delete
            mongo_db_collection.delete_many({"symbol": {"$in": delisted_symbols}})
            # Log
            self.logger.info(f"Deleting funding_rate data for {exchange}_{market_type} delisted symbols: {delisted_symbols}")
        mongo_db_conn.close()
        return

        
