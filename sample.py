# モジュール読み込み
import kintoneApiMod as ktmod

# 設定ファイルから設定情報を読み込み
kintoneAppConfigData = ktmod.readAppConfig('kintone.ini','9999')

# csvからINSERT用のレコードデータ整形
recordsKeyFields,recordsKeyValues = ktmod.makeInsertData('import_sjis.csv',kintoneAppConfigData)

# 整形済みのレコードデータからUPDATE用のJSONを作成
data = ktmod.makeInsertRecordsJsonList(kintoneAppConfigData, recordsKeyFields,recordsKeyValues,100)

# JSONを元にinsert実行
ret = ktmod.insertRecords(kintoneAppConfigData,data)



# # 設定ファイルから設定情報を読み込み
kintoneAppConfigData = ktmod.readAppConfig('kintone.ini','9999')

# csvからUPDATE用のレコードデータ整形
updateKeyValues,recordsKeyFields,recordsKeyValues = ktmod.makeUpdateData('import_sjis.csv',kintoneAppConfigData)

# 整形済みのレコードデータからUPDATE用のJSONを作成
data = ktmod.makeUpdateRecordsJsonList(kintoneAppConfigData,updateKeyValues,recordsKeyFields,recordsKeyValues,100)

# JSONを元にUPDATE実行
ret = ktmod.updateRecords(kintoneAppConfigData,data)