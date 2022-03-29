# -*- coding: utf-8 -*-
import rqdatac
import dqdatasdk.dqmodule.overwriteif as oi


__version__: str = ...
init = oi.init
reset = rqdatac.reset
initialized = rqdatac.initialized
concept_list = rqdatac.concept_list
concept = rqdatac.concept
concept_names = rqdatac.concept_names
shenwan_industry = rqdatac.shenwan_industry
shenwan_instrument_industry = rqdatac.shenwan_instrument_industry
zx_industry = rqdatac.zx_industry
zx_instrument_industry = rqdatac.zx_instrument_industry
get_industry = rqdatac.get_industry
get_instrument_industry = rqdatac.get_instrument_industry
get_industry_mapping = rqdatac.get_industry_mapping
industry_code = rqdatac.IndustryCode
IndustryCode = rqdatac.IndustryCode
sector_code = rqdatac.SectorCode
SectorCode = rqdatac.SectorCode
get_trading_dates = rqdatac.get_trading_dates
get_next_trading_date = rqdatac.get_next_trading_date
get_previous_trading_date = rqdatac.get_previous_trading_date
get_latest_trading_date = rqdatac.get_latest_trading_date
trading_date_offset = rqdatac.trading_date_offset
is_trading_date = rqdatac.is_trading_date
has_night_trading = rqdatac.has_night_trading
id_convert = rqdatac.id_convert
instruments = rqdatac.instruments

all_instruments = rqdatac.all_instruments
sector = rqdatac.sector
industry = rqdatac.industry
get_future_contracts = rqdatac.get_future_contracts


class futures:
    get_commission_margin = rqdatac.futures.get_commission_margin
    get_contracts = rqdatac.futures.get_contracts
    get_dominant = rqdatac.futures.get_dominant
    get_dominant_price = rqdatac.futures.get_dominant_price
    get_member_rank = rqdatac.futures.get_member_rank
    get_warehouse_stocks = rqdatac.futures.get_warehouse_stocks
    get_contract_multiplier = rqdatac.futures.get_contract_multiplier
    get_ex_factor = rqdatac.futures.get_ex_factor


jy_instrument_industry = rqdatac.jy_instrument_industry


class econ:
    get_factors = rqdatac.econ.get_factors
    get_money_supply = rqdatac.econ.get_money_supply
    get_reserve_ratio = rqdatac.econ.get_reserve_ratio


get_main_shareholder = rqdatac.get_main_shareholder
get_current_news = rqdatac.get_current_news
get_trading_hours = rqdatac.get_trading_hours
get_private_placement = rqdatac.get_private_placement
get_share_transformation = rqdatac.get_share_transformation


class user:
    get_quota = rqdatac.user.get_quota


get_update_status = rqdatac.get_update_status
info = oi.info # rqdatac.info
get_basic_info = rqdatac.get_basic_info


class convertible:
    all_instruments = rqdatac.convertible.all_instruments
    get_call_info = rqdatac.convertible.get_call_info
    get_cash_flow = rqdatac.convertible.get_cash_flow
    get_conversion_info = rqdatac.convertible.get_conversion_info
    get_conversion_price = rqdatac.convertible.get_conversion_price
    get_credit_rating = rqdatac.convertible.get_credit_rating
    get_indicators = rqdatac.convertible.get_indicators
    get_industry = rqdatac.convertible.get_industry
    get_instrument_industry = rqdatac.convertible.get_instrument_industry
    get_latest_rating = rqdatac.convertible.get_latest_rating
    get_put_info = rqdatac.convertible.get_put_info
    instruments = rqdatac.convertible.instruments
    is_suspended = rqdatac.convertible.is_suspended
    rating = rqdatac.convertible.rating


get_dominant_future = rqdatac.get_dominant_future
future_commission_margin = rqdatac.future_commission_margin
get_future_member_rank = rqdatac.get_future_member_rank
current_stock_connect_quota = rqdatac.current_stock_connect_quota
get_stock_connect_quota = rqdatac.get_stock_connect_quota
is_st_stock = rqdatac.is_st_stock
_is_st_stock = rqdatac._is_st_stock
is_suspended = rqdatac.is_suspended
get_stock_connect = rqdatac.get_stock_connect
get_securities_margin = rqdatac.get_securities_margin
get_margin_stocks = rqdatac.get_margin_stocks
get_shares = rqdatac.get_shares
get_allotment = rqdatac.get_allotment
current_snapshot = rqdatac.current_snapshot
get_ticks = rqdatac.get_ticks
current_minute = rqdatac.current_minute
get_live_ticks = rqdatac.get_live_ticks
get_price = rqdatac.get_price
LiveMarketDataClient = rqdatac.LiveMarketDataClient
get_all_factor_names = rqdatac.get_all_factor_names
get_factor = rqdatac.get_factor
get_factor_return = rqdatac.get_factor_return
get_factor_exposure = rqdatac.get_factor_exposure
get_style_factor_exposure = rqdatac.get_style_factor_exposure
get_descriptor_exposure = rqdatac.get_descriptor_exposure
get_stock_beta = rqdatac.get_stock_beta
get_factor_covariance = rqdatac.get_factor_covariance
get_specific_return = rqdatac.get_specific_return
get_specific_risk = rqdatac.get_specific_risk
get_index_factor_exposure = rqdatac.get_index_factor_exposure
Financials = rqdatac.Financials
financials = rqdatac.Financials
get_financials = rqdatac.get_financials
PitFinancials = rqdatac.PitFinancials
pit_financials = rqdatac.PitFinancials
get_pit_financials = rqdatac.get_pit_financials
get_pit_financials_ex = rqdatac.get_pit_financials_ex
get_fundamentals = rqdatac.get_fundamentals
deprecated_fundamental_data = rqdatac.deprecated_fundamental_data
current_performance = rqdatac.current_performance
performance_forecast = rqdatac.performance_forecast
Fundamentals = rqdatac.Fundamentals
fundamentals = rqdatac.Fundamentals
query = rqdatac.query
get_capital_flow = rqdatac.get_capital_flow
get_open_auction_info = rqdatac.get_open_auction_info
get_close_auction_info = rqdatac.get_close_auction_info
index_components = rqdatac.index_components
index_weights = rqdatac.index_weights
index_indicator = rqdatac.index_indicator
get_ksh_auction_info = rqdatac.get_ksh_auction_info
get_split = rqdatac.get_split
get_dividend = rqdatac.get_dividend
get_dividend_info = rqdatac.get_dividend_info
get_ex_factor = rqdatac.get_ex_factor
get_turnover_rate = rqdatac.get_turnover_rate
get_price_change_rate = rqdatac.get_price_change_rate
get_yield_curve = rqdatac.get_yield_curve
get_block_trade = rqdatac.get_block_trade
get_exchange_rate = rqdatac.get_exchange_rate
get_temporary_code = rqdatac.get_temporary_code


class options:
    get_contract_property = rqdatac.options.get_contract_property
    get_contracts = rqdatac.options.get_contracts
    get_greeks = rqdatac.options.get_greeks




class fenji:
    get = rqdatac.fenji.get
    get_a_by_interest_rule = rqdatac.fenji.get_a_by_interest_rule
    get_a_by_yield = rqdatac.fenji.get_a_by_yield
    get_all = rqdatac.fenji.get_all


ecommerce = rqdatac.ecommerce


class xueqiu:
    history = rqdatac.xueqiu.history
    top_stocks = rqdatac.xueqiu.top_stocks


get_consensus_indicator = rqdatac.services.consensus.get_consensus_indicator
get_consensus_price = rqdatac.services.consensus.get_consensus_price
