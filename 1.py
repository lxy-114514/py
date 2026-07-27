import pandas as pd
import time
import tinyshare as ts
ts.set_token('U1BvGc8IU1F7Sp9t0h11f3dddi1fv6UUG6Y10g0yzyt7roIGJQ6nUxa87a9f51e7')
pro = ts.pro_api()

hangye=pd.read_parquet('D:/学习资料/数据/行业.parquet')

# 存储全市场汇总数据
all_daily = pd.DataFrame()
all_daily_list = []

#交易日历  是否交易 0休市 1交易,补齐交易日历
trade_canlendar = pro.trade_cal(exchange='', start_date='20160101', end_date='20180420')
trade_date_=trade_canlendar.loc[trade_canlendar['is_open']==1,'cal_date'].to_list()
#trade_date_.to_parquet('D:/学习资料/数据/行业.parquet',index=False)

# 缓存路径
save_path = "D:/学习资料/数据/1/"

# 获取当日有效股票列表
def get_universe_stocks (trade_date):

    trade_dt = pd.to_datetime(trade_date)
    
    
    #  获取当日停牌复牌信息
    suspend_info = pro.suspend_d(suspend_type=['S','R'], trade_date=trade_date,fields='ts_code,trade_date,suspend_type')
    # 【关键修复】空表时强制补齐需要的列，防止merge KeyError
    need_suspend_cols = ['ts_code','trade_date','suspend_type']
    if suspend_info.empty:
        suspend_info = pd.DataFrame(columns=need_suspend_cols)
    time.sleep(0.3)
    

    #  获取当日所有的ST股票
    st_info = pro.stock_st(trade_date=trade_date,fields='ts_code,trade_date,type')
    need_st_cols = ['ts_code','trade_date','type']
    if st_info.empty:
        st_info = pd.DataFrame(columns=need_st_cols)
    time.sleep(0.3)
    
    

    
    #  获取当日全部股票的 行情以及====涨跌停====
    daily_basic = pro.daily_basic(trade_date=trade_date, fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pb,ps,float_share,total_mv,circ_mv,limit_status')

    daily_basic1=pd.merge(daily_basic,suspend_info,on=['ts_code','trade_date'],how='left')
    daily_basic2=pd.merge(daily_basic1,st_info,on=['ts_code','trade_date'],how='left')
    
    time.sleep(0.3)  # 第1次接口后
    #return selected_stocks============================================================================

    # 一天只请求一次全市场
    #daily_basic_all = pro.daily_basic(trade_date=d, fields='ts_code,trade_date,turnover_rate,volume_ratio,pe_ttm,pb,ps_ttm,total_mv')
    daily_all = pro.daily(trade_date=d,fields='ts_code,trade_date,open,high,low,close,change,pct_chg,vol,amount')
    #提取当日全部股票的复权因子
    fq_factor_all = pro.adj_factor(ts_code='', trade_date=d)

    #合并
    df0=pd.merge(daily_basic2,daily_all,on=['ts_code','trade_date'],how='left')
    df1=pd.merge(df0,fq_factor_all,on=['ts_code','trade_date'],how='left')
    df2=pd.merge(df1,hangye,on=['ts_code'],how='left')

    return df2

cnt = 0

for d in trade_date_:
    #d1=pd.to_datetime(d)
    df=get_universe_stocks(d)
    
    #all_daily = pd.concat([all_daily, df2],axis=0,ignore_index=True)
    all_daily_list.append(df)
    
    time.sleep(0.5)

    cnt += 1
    if cnt % 10 == 0:
        chunk_df = pd.concat(all_daily_list, axis=0, ignore_index=True)
        chunk_df.to_parquet(f"D:/学习资料/数据/1/中间缓存_{d}.parquet", index=False)
        print(f"已缓存至中间缓存_{d}.parquet")
        all_daily_list.clear()
        # 4. 手动删除临时df，加速GC垃圾回收
        del chunk_df


# 循环结束，落地剩余未保存数据
if len(all_daily_list) > 0:
    final_df = pd.concat(all_daily_list, axis=0, ignore_index=True)
    final_df.to_parquet(f"D:/学习资料/数据/1/最后缓存.parquet", index=False)
    print('全部数据处理完成')