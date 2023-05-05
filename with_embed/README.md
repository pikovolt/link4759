# link4759/with_embed
Python(embeddable)で動作させる GUIサンプル。

このサンプルのバッチファイルは、以下の場所に配置されている前提です。
必要に応じて、バッチファイルを変更してください。

- Python3.10.11 : C:\Users\%USERNAME%\Documents\Python\Python3.10.11
- link4759 : C:\Users\%USERNAME%\Documents\GitHub\link4759

embedable pythonは、PYTHONPATH指定が無効なので、ソースコード(ui.py)内で sys.path.appendでモジュールのパスを追加しています。Python3のバージョンは、3.10.11で記述していますが、特にこのバージョンである必要はありません。

embedable pythonには、pyserial, pyside2を pip installしておく必要があります。

以上。