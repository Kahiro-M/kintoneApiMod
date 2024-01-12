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


# UPDATE処理でiniファイルの設定項目が必要な項目のテンプレートを返す
def getUpdateTemplateConfig():
  return {'domain': 'サブドメイン', 'appId': 'アプリ番号', 'token': 'トークン', 'action': 'Update/Insert/Delete', 'upkey': '更新用キー'}

# INSERT処理でiniファイルの設定項目が必要な項目のテンプレートを返す
def getInsertTemplateConfig():
  return {'domain': 'サブドメイン', 'appId': 'アプリ番号', 'token': 'トークン', 'action': 'Update/Insert/Delete'}

# 配列をN分割した配列を返す
def getSplitedList(list, n):
    for idx in range(0, len(list), n):
        yield list[idx:idx + n]


# kintoneのレコード更新用JSONを指定行ずつに区切って生成する
def makeUpdateRecordsJsonList(kintoneConfigData,updateKeyValues,recordsKeyFields,recordsKeyValues,splitUnit=100):
  if(len(updateKeyValues) == len(recordsKeyValues)
    and set(kintoneConfigData.keys()).issuperset(set(getUpdateTemplateConfig().keys()))
  ):

    # 更新用キーの値、recordsの値を指定行数ごとに区切る
    updateKeyValuesList = list(getSplitedList(updateKeyValues,splitUnit))
    recordsKeyValuesList = list(getSplitedList(recordsKeyValues,splitUnit))

    jsonList = []
    for updateValuesList,recordsValuesList in zip(updateKeyValuesList,recordsKeyValuesList):
      tmp = getUpdateRecordsJson(kintoneConfigData,updateValuesList,recordsKeyFields,recordsValuesList)
      jsonList.append(tmp)
  else:
    jsonList = {'type':'error','updateKeyValues':len(updateKeyValues),'recordsKeyValues':len(recordsKeyValues),'hasKintoneConfigKeys':kintoneConfigData.keys()}
  return jsonList

# kintoneのレコード更新用JSONを生成する
def getUpdateRecordsJson(kintoneConfigData,updateKeyValues,recordsKeyFields,recordsKeyValues):
  import json

  # 更新用キーの数と更新データの件数が一致
  # かつ iniファイルの設定項目のうち必須項目がすべて存在すれば更新用のデータを作成する。
  if(len(updateKeyValues) == len(recordsKeyValues)
    and set(kintoneConfigData.keys()).issuperset(set(getUpdateTemplateConfig().keys()))
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
    jsonList = json.loads(jsonStr)

    return jsonList
  else:
    return {'type':'error','updateKeyValues':len(updateKeyValues),'recordsKeyValues':len(recordsKeyValues),'hasKintoneConfigKeys':kintoneConfigData.keys()}

# JSON配列をもとに更新処理
def updateRecords(kintoneConfigData,jsonList):
  import requests
  import json
  import unicodedata

  domain = kintoneConfigData['domain']
  appId  = kintoneConfigData['appId']
  token  = kintoneConfigData['token']
  action = kintoneConfigData['action']

  # action指定がUPDATE/UPSERTで実行可能
  if(unicodedata.normalize('NFKC', action).upper() in ['UPDATE','UPSERT']):

    # KintoneのURLを指定してcurl経由でAPIを叩く
    # 単レコードは　'https://(サブドメイン).cybozu.com/k/v1/record.json'
    # 複数レコードは'https://(サブドメイン).cybozu.com/k/v1/records.json'
    url = 'https://'+domain+'.cybozu.com/k/v1/records.json'

    # token指定
    headers = {
      'X-Cybozu-API-Token': token,
      'Content-Type': 'application/json',
      }

    ret = []
    for jsonData in jsonList:
      # GETで参照、POSTで追加、PUTで更新
      response = requests.put(url+'?app='+str(appId), json=jsonData, headers=headers, timeout=60)

      # レスポンスがJSON形式で返却されるので、JSONをパースする
      if(response.text == ''):
        ret.append(response)
      else:
        ret.append(response.json())
    return ret

# 更新用のデータをCSVから生成
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

# 登録用のデータをCSVから生成
def makeInsertData(csvFilePath,kintoneAppConfigData):
    import csv
    import copy

    with open(csvFilePath) as f:
        reader = csv.DictReader(f)
        importDict = [row for row in reader]

    # 最初の行はカラム行
    importDataColumns = list(importDict[0].keys())

    # 更新用のキーの値を抽出
    # updateKeyValues = [lineDict.get(kintoneAppConfigData['upkey']) for lineDict in importDict]

    # カラムを抽出
    recordsKeyFields = [col for col in importDataColumns]

    # レコードの値を抽出
    recordsKeyValues = []
    # deepcopyで入れ子構造の配列を値渡しで複製する
    # （単なるcopyだと入れ子部分が参照渡しなので、元データが破壊される）
    for line in copy.deepcopy(importDict):
        recordsKeyValues.append(list(line.values()))
    
    # return updateKeyValues,recordsKeyFields,recordsKeyValues
    return recordsKeyFields,recordsKeyValues

# kintoneのレコード登録用JSONを指定行ずつに区切って生成する
def makeInsertRecordsJsonList(kintoneConfigData,recordsKeyFields,recordsKeyValues,splitUnit=100):
  if(set(kintoneConfigData.keys()).issuperset(set(getInsertTemplateConfig().keys()))):
    # recordsの値を指定行数ごとに区切る
    recordsKeyValuesList = list(getSplitedList(recordsKeyValues,splitUnit))

    jsonList = []
    for recordsValuesList in recordsKeyValuesList:
      tmp = getInsertRecordsJson(kintoneConfigData,recordsKeyFields,recordsValuesList)
      jsonList.append(tmp)
  else:
    jsonList = {'type':'error','recordsKeyValues':len(recordsKeyValues),'hasKintoneConfigKeys':kintoneConfigData.keys()}
  return jsonList

# kintoneのレコード更新用JSONを生成する
def getInsertRecordsJson(kintoneConfigData,recordsKeyFields,recordsKeyValues):
  import json

  # iniファイルの設定項目のうち必須項目がすべて存在すれば登録用のデータを作成する。
  if(set(kintoneConfigData.keys()).issuperset(set(getInsertTemplateConfig().keys()))):

    appId          = kintoneConfigData['appId']

    # JSONにする文字列を配列に格納
    jsonStrList = []

    # app,recordsの設定
    jsonStrList.append('{')
    jsonStrList.append('"app":'+str(appId)+',')
    # recordsの設定
    jsonStrList.append('"records": [')
    for recordsKeyValue in recordsKeyValues:
      jsonStrList.append('{')
      for field,value in zip(recordsKeyFields,recordsKeyValue):
        jsonStrList.append('"'+str(field)+'":{"value":"'+str(value)+'"},')
      # recordの最終行のカンマは不要なので、スライスで削除する
      jsonStrList[-1] = jsonStrList[-1][:-1]
      jsonStrList.append('},')
    # recordsの最終行のカンマは不要なので、スライスで削除する
    jsonStrList[-1] = jsonStrList[-1][:-1]
    jsonStrList.append(']')
    jsonStrList.append('}')

    # 配列に格納されたJSONにする文字列を結合
    jsonStr = ''.join(jsonStrList)

    # 文字列からJSONを作成
    jsonList = json.loads(jsonStr)

    return jsonList
  else:
    return {'type':'error','updateKeyValues':len(updateKeyValues),'recordsKeyValues':len(recordsKeyValues),'hasKintoneConfigKeys':kintoneConfigData.keys()}

# JSON配列をもとに登録処理
def insertRecords(kintoneConfigData,jsonList):
  import requests
  import json
  import unicodedata

  domain = kintoneConfigData['domain']
  appId  = kintoneConfigData['appId']
  token  = kintoneConfigData['token']
  action = kintoneConfigData['action']

  # action指定がINSERT/UPSERTのみ実行
  if(unicodedata.normalize('NFKC', action).upper() in ['INSERT','UPSERT']):

    # KintoneのURLを指定してcurl経由でAPIを叩く
    # 単レコードは　'https://(サブドメイン).cybozu.com/k/v1/record.json'
    # 複数レコードは'https://(サブドメイン).cybozu.com/k/v1/records.json'
    url = 'https://'+domain+'.cybozu.com/k/v1/records.json'

    # token指定
    headers = {
      'X-Cybozu-API-Token': token,
      'Content-Type': 'application/json',
      }

    ret = []
    for jsonData in jsonList:
      # GETで参照、POSTで追加、PUTで更新
      response = requests.post(url+'?app='+str(appId), json=jsonData, headers=headers, timeout=60)

      # レスポンスがJSON形式で返却されるので、JSONをパースする
      if(response.text == ''):
        ret.append(response)
      else:
        ret.append(response.json())
    return ret

