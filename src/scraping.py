import re
import csv
import json
import glob
import datetime
import requests
import collections
import pandas as pd
from bs4 import BeautifulSoup


#市原市HPからソースを取得
url ='https://www.city.ichihara.chiba.jp/kenko/iryo_kansensyou/kansensyouyobou/covid-19/about/kanja.html'
r=requests.get(url)
r.raise_for_status()
r.encoding = r.apparent_encoding
soup = BeautifulSoup(r.text, 'html.parser')

#スクレイピングした日付をyyyy-mm-dd形式に
def data_shaping(date):
    m = re.match(r'[0-9]+月[0-9]+日', date)
    m_text = m.group()
    pos = re.split('[月日]', m_text)
    datetime_data = datetime.datetime(2020, int(pos[0]), int(pos[1]))
    date = datetime_data.strftime("%Y-%m-%d")
    return date

#テーブルを取得、保存
table = soup.findAll("table",{"class":"table01"})[1]
tr = table.findAll("tr")

with open("./src/Downloads/table_data/corona_t.csv", "w", encoding='utf-8') as file:
    writer = csv.writer(file)
    for i in tr:
        row = []
        for cell in i.findAll(['td', 'th']):
            row.append(cell.get_text().replace('\u3000','').replace('：',':').replace(' ', ''))
        writer.writerow(row)
table_df = pd.read_csv('./src/Downloads/table_data/corona_t.csv')
table_df_dict = table_df.to_dict('index')
data1 = [table_df_dict.get(i) for i in range(len(table_df))]

df = pd.DataFrame([], columns=['陽性判明日','公表日','居住地', '年代', '性別','職業'])
#open_date, found_date,residence, age, sex ,job = create_pacients_table_DataFrame(all_contents_list)

open_date = []
foud_date=[]
residence = []
age = []
sex = []
job = []

for i in data1:
    if i['事例'] =='149例目':
        continue
    elif i['事例'] =='245例目（無症状33例目）':
        continue

    #年代
    #m=re.search(r'年代:(.+?)■',i['感染者の概要'])
    #age_num=m.group(1)
    age_num=i['年代']
    age.append(age_num)
    #性別
    #m=re.search(r'性別:(.+?)■',i['感染者の概要'])
    #sex_text=m.group(1)
    sex_text=i['性別']
    sex.append(sex_text)
    #居住地
    #m=re.search(r'居住地:(.+?)■',i['感染者の概要'])
    #residence_text=m.group(1)
    residence_text= '-'
    residence.append(residence_text)
    #職業
    #m=re.search(r'職業:(.+?)■',i['感染者の概要'])
    m=i['職業(種別)']
    if m:
        #job_text=m.group(1)
        job_text=m
        job.append(job_text)
    else:
        job.append('未公表')

    #陽性判明日
    #m=re.search(r'([0-9]+月[0-9]+日)検査の結果、陽性と判明',i['感染者の概要'])
    #found_date_num=m.group(1)
    found_date_num= i['職業(種別)']
    found_date_num=data_shaping(found_date_num)
    foud_date.append(found_date_num)
    #公表日
    open_date_num=i['検査確定日']
    open_date_num=data_shaping(open_date_num)
    open_date.append(open_date_num)

df = pd.DataFrame([], columns=['公表日','居住地', '年代', '性別','職業','陽性判明日'])
df['公表日'] = open_date
df['居住地'] = residence
df['年代'] = age
df['性別'] = sex
df['職業'] = job
df['陽性判明日'] = foud_date

patients_df = df.sort_values('公表日').reset_index(drop=True)
patients_df.to_csv('./src/Downloads/patients_data/patients.csv', index=False)
patients_df_dict = patients_df.to_dict('index')
data2 = [patients_df_dict.get(i) for i in range(len(patients_df_dict))]
    
# 日付と日別感染者数、２つデータの作成する関数
def create_patients_column(this_year, this_month, this_day):
    today_info = datetime.datetime(this_year, this_month, 1)
    start_date = today_info.strftime("%Y-%m-%d")
    date_column = pd.date_range(start_date, freq='D', periods=this_day)
    subtotal_column = [0 for i in range(this_day)]
    return date_column, subtotal_column

# pacients_summary_DataFrameを作成する関数
def create_x_month_data(open_date, date_column, subtotal_column):
    # 空のデータフレームの作成
    progress_map = {'日付': date_column, '小計': subtotal_column}
    df = pd.DataFrame(progress_map)

    # 条件にマッチした日にデータを挿入
    infect_date_count = collections.Counter(open_date)
    for num, i in enumerate(df.iloc[0:, 0]):
        for j in infect_date_count.keys():
            if j in str(i):
                df.iloc[num, 1] = infect_date_count[j]
    return df

# 陽性判明者数データ
today = datetime.datetime.now()
this_year = today.year
this_month = today.month
this_day = today.day
this_hour = today.hour
this_minute = today.minute

date_column, subtotal_column = create_patients_column(
    this_year, this_month, this_day)
x_month_data = create_x_month_data(open_date, date_column, subtotal_column)
x_month_data.to_csv(
    './src/Downloads/each_data/{}_{}.csv'.format(this_year, this_month), index=False)

csv_files = glob.glob('./src/Downloads/each_data/*.csv')
each_csv = []
for i in csv_files:
    each_csv.append(pd.read_csv(i))
sum_x_month_data = pd.concat(each_csv).reset_index(drop=True)

patients_summary_df = sum_x_month_data.sort_values("日付").reset_index(drop=True)
patients_summary_df.to_csv("./src/Downloads/final_data/total.csv", index=False)
patients_summary_df_dict = patients_summary_df.to_dict('index')
data3 = [patients_summary_df_dict.get(i)for i in range(len(patients_summary_df))]

# makejsonData
update_at = "{}/{}/{} {}:{}".format(this_year,this_month, this_day, this_hour, this_minute)
data_json = {
    "lastUpdate": update_at,
    "patients": {
        "date": update_at,
        "data": data2
    },
    "patients_summary": {
        "date": update_at,
        "data": data3
    }
}
with open('./src/data.json', 'w') as f:
    json.dump(data_json, f, indent=4, ensure_ascii=False)
