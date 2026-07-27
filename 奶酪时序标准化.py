import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

import time

df1= pd.read_parquet("D:/学习资料/奶酪/exam_data/table_1.parquet")
df2= pd.read_parquet("D:/学习资料/奶酪/exam_data/table_2.parquet")
df3= pd.read_parquet("D:/学习资料/奶酪/exam_data/table_3.parquet")
df4= pd.read_parquet("D:/学习资料/奶酪/exam_data/table_4.parquet")
df5= pd.read_parquet("D:/学习资料/奶酪/exam_data/table_5.parquet")

# ========== 配置区（按需修改列名、因子） ==========

jiezhiri = "2022-12-30"#截止日
mubiaori = "2023-01-03"#目标日

col_df1=df1.columns.to_list()
col_df2=df2.columns.to_list()
col_df3=df3.columns.to_list()
col_df4=df4.columns.to_list()
col_df5=df5.columns.to_list()
col_ls=[col_df1,col_df2,col_df3,col_df4,col_df5]##因子列
df_l=[df1,df2,df3,df4,df5]
ans=[]#存储答案

# 计时起点
start = time.time()

for df,col_l  in zip(df_l,col_ls):
    df=df.reset_index()
    df['Date']=pd.to_datetime(df['Date'],errors='coerce')
    df['Datetime']=pd.to_datetime(df['Datetime'],errors='coerce')

    history_df=df[df['Date']<=jiezhiri ]#到参考数据
    target_df=df[df['Date']==mubiaori]#⽬标数据数据点

    shixu_df=pd.concat([history_df,target_df],axis=0)

    #缺失值填充：缺失值无效，直接删除
    shixu_df=shixu_df.dropna(subset=col_l)

    #MAD去极值
    def qujizhi(df,target_cols,n=3):
        for col in  target_cols:
            med=df[col].median()
            mad=np.median(abs(df[col]-med))
            low=med-3*1.4826*mad
            high=med+3*1.4826*mad
            df[col]=df[col].clip(low,high)
        return df

    shixu_df=qujizhi(shixu_df,col_l)

    #Rank时序标准化
    def shixubiaozhun(df,target_cols):
        for col in target_cols:
            # 前置判断：前面已经删除缺失值，现在，当期x为0 → 输出NaN
            df[col]=df[col].replace(0,np.nan)
            N=len(df[col])##有效因子数
            
            df[col]=df[col].rank(method='min',ascending=True)###从小到大排序，同分位取最小名次
            #因子值排序（处理大量重复值的情况）
            #规则：不重复的值：使用标准升序 rank（midrank）； 重复的值：取升序 rank 和降序 rank 的均值
            #数学上，重复值的 (升序+降序)/2 恒等于 (n+1)/2，
    
            #标记重复值
            duplicate_mask=df[col].duplicated(keep=False)
            df.loc[duplicate_mask, col] = (N + 1) / 2
            df[col]=df[col]/N-0.5
        return df

    shixu_df=shixubiaozhun(shixu_df,col_l)
    
    target_shixubiaozhun=shixu_df[shixu_df['Date']==mubiaori]#需要标准化的因⼦数据为2023-01-03每⼀个时刻截⾯
    target_shixubiaozhun.set_index(['Date','Contract','Datetime'])
    ans.append(target_shixubiaozhun)

# 计时终点
end = time.time()
# 耗时（秒）
cost = end - start
print(f"代码运行耗时：{cost:.4f} 秒")

#转为parquet文件
for i,df in enumerate(ans):
    df.to_parquet(f"D:/学习资料/奶酪/exam_data/result_{i+1}.parquet",index=False)