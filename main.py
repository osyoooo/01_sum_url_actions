from bs4 import BeautifulSoup
import requests
import pandas as pd
import time
from datetime import datetime
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import pytz

#　大田区　＋　条件　23万円　10年　１LDKから３LDKの条件で検索
request_url = "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&pc=20&smk=&po1=25&po2=99&shkr1=03&shkr2=03&shkr3=03&shkr4=03&sc=13111&ta=13&cb=0.0&ct=23.0&md=03&md=04&md=05&md=06&md=07&md=08&md=09&md=10&et=9999999&mb=0&mt=9999999&cn=10&fw2="
res = requests.get(request_url)

soup = BeautifulSoup(res.text, 'html.parser')

# 取得したページ（検索結果）のページネーションの最後の数字を取得
pagination = soup.select_one('ol.pagination-parts li:last-child a').text
page_count = int(pagination)

# ページネーションの数だけURLを生成
page_urls = []
for page in range(1, page_count + 1):
    url = request_url + "&page=" + str(page)
    page_urls.append(url)

# 生成URLと追加URLを格納するためのリスト
link_urls = []

# 各ページURLに対して処理を実行
for page_url in page_urls:
    # ページのコンテンツを取得
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 'td.ui-text--midium.ui-text--bold' の後の a タグ内の href の数だけ href を取得
    hrefs = []
    for a in soup.select('td.ui-text--midium.ui-text--bold a'):
        href = a['href']
        base_url = 'https://suumo.jp' + href
        kankyo_url = 'https://suumo.jp' + href.split('?')[0] + '/kankyo/' + '?' + href.split('?')[1]

        # 生成URLと追加URLをタプルとしてlink_urlsリストに追加
        link_urls.append((base_url, kankyo_url))

    # 次のページのリクエスト前に3秒待機
    time.sleep(3)

# 現在時刻を取得　タイムゾーンを日本にする　githubはUS
jst = pytz.timezone('Asia/Tokyo')
current_time = datetime.now(jst)

# タイムスタンプ形式の文字列としてフォーマット
timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

# link_urls リストをdfに変換
df = pd.DataFrame(link_urls, columns=['Bukken_URL','Kankyo_url'])

# 'Bukken_URL' カラムの重複を削除
df = df.drop_duplicates(subset=['Bukken_URL'])

df['Timestamp'] = timestamp

# Google APIへのアクセスにはOAuth 2.0という認証プロトコルが使用されており、scope呼ばれる権限の範囲を使ってアクセスを制御
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# GCP認証情報を環境変数から読み込む
gcp_credentials_dict = json.loads(os.getenv('CREDENTIALS_JSON'))
credentials = Credentials.from_service_account_info(gcp_credentials_dict, scopes=scope)

#認証情報を取得
gc = gspread.authorize(credentials)

# スプレッドシートのIDを環境変数から取得
SPREADSHEET_KEY = os.getenv('SPREADSHEET_KEY')

# スプレッドシートを開く
spreadsheet = gc.open_by_key(SPREADSHEET_KEY)
worksheet = spreadsheet.worksheet('suumo_url')

# ワークシートの内容をクリア
worksheet.clear()

set_with_dataframe(worksheet, df)

##### EOF
