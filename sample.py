# モジュール読み込み
import kintoneApiMod as ktmod

# 設定ファイルから設定情報を読み込み
kintoneAppConfigData = ktmod.readAppConfig('kintone.ini','9999')

# csvからUPDATE用のレコードデータ整形
updateKeyValues,recordsKeyFields,recordsKeyValues = ktmod.makeUpdateData('import_sjis.csv',kintoneAppConfigData)

# 整形済みのレコードデータからUPDATE用のJSONを作成
data = ktmod.makeUpdateRecordsJson(kintoneAppConfigData,updateKeyValues,recordsKeyFields,recordsKeyValues)

# JSONを元にUPDATE実行
ret = ktmod.updateRecords(kintoneAppConfigData,data)