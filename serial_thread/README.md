# link4759/serial_thread
Python(installer版)で動作させるサンプル。
シリアル受信の一部をスレッド動作に変えたもの。（再生中に fmsコマンドで１秒毎にレジスタ内容を受信できます）

このサンプルは、以下の場所に配置されている前提です。
実行するには、PYTHONPATHの設定で下記のモジュールにパスを通しておく必要があります。（4759PlayerをPCに接続後、ui.pyを実行すると GUIが表示されます。）

- link4759 : C:\Users\\%USERNAME%\Documents\GitHub\link4759

Python3のバージョンは、3.10.11で記述していますが、特にこのバージョンである必要はありません。

pythonには、pyserial, pyside2を pip installしておく必要があります。

以上。
