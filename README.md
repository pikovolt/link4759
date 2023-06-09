# link4759
4759Playerに対して、PCからシリアル接続でコマンド制御できる。ということを教えていただいたので、ターミナルソフトで繋いで聴きたい曲をディレクトリ探索して楽しんでいたのですが、ひとしきり楽しんでみるとキー入力は徐々に重荷のように感じ始めてきてしまいました。
試しにPythonからシリアル制御するクラスを作ってみました。（100行くらいで済ませたかったのですが、だらだら書くうちに200行近くなってしまいましたが…稚拙なのも恥ずかしくなってきました。）

動作には、Python3環境 + pyserialモジュールが必要です。

できることは、以下の通り。
※コードの一番下の example関数にざっくり関数の呼び方を書いてあります。

- 4759Playerとの接続・切断
- ディレクトリリストの取得
- カレントディレクトリの変更
- 楽曲データの再生・停止
- プレイリスト再生（中断処理なしのシンプルなもの）

再生用関数とカレントディレクトリ変更の関数は、ファイル名の一部を与えると（それが固有の文字列だった場合）対応する名前を取得する処理を追加しました。
（名前の末尾に ~1が付き始めると、名前がわけの判らない名前になって打ち間違いが多くなってしまうので…）

シリアル接続をする際は、FTDIのシリアルドライバが入っていないとUSBでPCBと繋いでもなにも起こりません。
その辺りは、gimicや spfmの接続と同じ環境が必要なので、検索してみればいろいろ出てくると思いますが、「ftdi windows ドライバ」で検索すればだいたいわかると思われます。

PySide2を使った簡単なUIサンプル(sample_ui.py)も追加しておきました。（追加で PySide2モジュールが必要です）

- with_embed フォルダのほうは、GUI前提で改変した別バージョンです


# RaspberryPiでシリアル接続する場合
　Raspberry Pi OSに、最初から FTDIデバイスドライバが含まれているようなので、USBポートに 4759Playerを接続すればシリアル通信ができるようです。  
　※RaspberryPi4 & 2023/5/03版のraspios_arm64版OSで動作を確認

 Python3, PySerialも入っていましたが PySide2が入っておらず、別途インストールが必要でした。  
 このページが参考になりました。（ https://matsujirushi.hatenablog.jp/entry/2021/04/10/212246 ）  
 ただ１点 'python3-pyside2uic'が見付からない。という警告で apt-getが止まってしまうので、'python3-pyside2uic'は、省く必要がありました。


以上です。
