# -------------------------------------------------- # 
# Kintone REST API モジュール 
# -------------------------------------------------- #   


# iniファイルから設定を読み込む
def readConfigIni(filePath):
  import configparser

  #ConfigParserオブジェクトを生成
  config = configparser.ConfigParser()

  #設定ファイル読み込み
  config.read(filePath,encoding='utf8')

  #設定情報取得
  if(config.has_option('kintone','DOMAIN')
      and config.has_option('kintone','APP_ID')
      and config.has_option('kintone','TOKEN')
      and config.has_option('kintone','ACTION')
      and config.has_option('kintone','UPDATE_KEY')
      ):
    kintoneConfigData = {
      'domain' : config.get('kintone','DOMAIN'),
      'appId'  : config.get('kintone','APP_ID'),
      'token'  : config.get('kintone','TOKEN'),
      'action' : config.get('kintone','ACTION'),
      'upkey'  : config.get('kintone','UPDATE_KEY'),
    }
    return kintoneConfigData
  else:
    return {'type':'error','hasOptions':config.options(str(appId))}

# iniファイルからアプリごとの設定を読み込む
def readAppConfig(filePath,appId):
  import configparser

  #ConfigParserオブジェクトを生成
  config = configparser.ConfigParser()

  #設定ファイル読み込み
  config.read(filePath,encoding='utf8')

  #設定情報取得
  if(config.has_option('kintone','DOMAIN')
      and config.has_option(str(appId),'TOKEN')
      and config.has_option(str(appId),'ACTION')
      and config.has_option(str(appId),'UPDATE_KEY')
      ):
    kintoneAppConfigData = {
      'domain' : config.get('kintone','DOMAIN'),
      'appId'  : appId,
      'token'  : config.get(str(appId),'TOKEN'),
      'action' : config.get(str(appId),'ACTION'),
      'upkey'  : config.get(str(appId),'UPDATE_KEY'),
    }
    return kintoneAppConfigData
  else:
    return {'type':'error','hasOptions':config.options(str(appId))}

# iniファイルの設定項目が必要な項目のテンプレートを返す
def getTemplateConfig():
  return {'domain': 'サブドメイン', 'appId': 'アプリ番号', 'token': 'トークン', 'action': 'Update/Insert/Delete', 'upkey': '更新用キー'}

# kintoneのレコード更新用JSONを生成する
def makeUpdateRecordsJson(kintoneConfigData,updateKeyValues,recordsKeyFields,recordsKeyValues):
  import json
  templateConfig = {'domain': 'サブドメイン', 'appId': 'アプリ番号', 'token': 'トークン', 'action': 'Update/Insert/Delete', 'upkey': '更新用キー'}

  # 更新用キーの数と更新データの件数が一致
  # かつ iniファイルの設定項目が必要な項目だけあれば更新用のデータを作成する。
  if(len(updateKeyValues) == len(recordsKeyValues)
     and kintoneConfigData.keys() == getTemplateConfig().keys()
    ):
    appId          = kintoneConfigData['appId']
    updateKeyField = kintoneConfigData['upkey']

    # JSONにする文字列を配列に格納
    jsonStrList = []

    # app,recordsの設定
    jsonStrList.append('{')
    jsonStrList.append('"app":'+str(appId)+',')
    jsonStrList.append('"records": [')
    # updatekeyの設定
    for updateKeyValue,recordsKeyValue in zip(updateKeyValues,recordsKeyValues):
      jsonStrList.append('{')
      jsonStrList.append('"updateKey": {')
      jsonStrList.append('"field": "'+str(updateKeyField)+'",')
      jsonStrList.append('"value": "'+str(updateKeyValue)+'"')
      jsonStrList.append('},')
    # recordの設定
      jsonStrList.append('"record": {')
      for field,value in zip(recordsKeyFields,recordsKeyValue):
        jsonStrList.append('"'+str(field)+'":{"value":"'+str(value)+'"},')
      # recordの最終行のカンマは不要なので、スライスで削除する
      jsonStrList[-1] = jsonStrList[-1][:-1]
      jsonStrList.append('}')
      jsonStrList.append('},')
    # recordsの最終行のカンマは不要なので、スライスで削除する
    jsonStrList[-1] = jsonStrList[-1][:-1]
    jsonStrList.append(']')
    jsonStrList.append('}')

    # 配列に格納されたJSONにする文字列を結合
    jsonStr = ''.join(jsonStrList)

    # 文字列からJSONを作成
    jsonData = json.loads(jsonStr)

    return jsonData
  else:
    return {'type':'error','updateKeyValues':len(updateKeyValues),'recordsKeyValues':len(recordsKeyValues),'hasKintoneConfigKeys':kintoneConfigData.keys()}


def updateRecords(kintoneConfigData,recordsData):
  import requests
  import json
  import unicodedata

  domain = kintoneConfigData['domain']
  appId  = kintoneConfigData['appId']
  token  = kintoneConfigData['token']
  action = kintoneConfigData['action']

  # action指定がUPDATEのみ実行
  if(unicodedata.normalize('NFKC', action).upper() == 'UPDATE'):

    # KintoneのURLを指定してcurl経由でAPIを叩く
    # 単レコードは　'https://(サブドメイン).cybozu.com/k/v1/record.json'
    # 複数レコードは'https://(サブドメイン).cybozu.com/k/v1/records.json'
    url = 'https://'+domain+'.cybozu.com/k/v1/records.json'

    # token指定
    headers = {
      'X-Cybozu-API-Token': token,
      'Content-Type': 'application/json',
      }

    # 流し込みデータ作成
    data = recordsData

    # GETで参照、POSTで追加、PUTで更新
    response = requests.put(url+'?app='+str(appId), json=data, headers=headers, timeout=60)

    # レスポンスがJSON形式で返却されるので、JSONをパースする
    if(response.ok == False):
      return response
    return json.dumps(response.json(), indent=2, ensure_ascii=False)


def makeUpdateData(csvFilePath,kintoneAppConfigData):
    import csv
    import copy

    with open(csvFilePath) as f:
        reader = csv.DictReader(f)
        importDict = [row for row in reader]

    # 最初の行はカラム行
    importDataColumns = list(importDict[0].keys())

    # 更新用のキーの値を抽出
    updateKeyValues = [lineDict.get(kintoneAppConfigData['upkey']) for lineDict in importDict]

    # 更新用のキー以外のカラムを抽出
    recordsKeyFields = [col for col in importDataColumns if col!=kintoneAppConfigData['upkey']]

    # 更新レコードの値を抽出
    recordsKeyValues = []
    # deepcopyで入れ子構造の配列を値渡しで複製する
    # （単なるcopyだと入れ子部分が参照渡しなので、元データが破壊される）
    for line in copy.deepcopy(importDict):
        # 更新用のキーを削除し、更新レコードのみにする
        del line[kintoneAppConfigData['upkey']]
        recordsKeyValues.append(list(line.values()))
    
    return updateKeyValues,recordsKeyFields,recordsKeyValues