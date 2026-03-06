# Quickstart

## 1. 鍚姩浜や簰 launcher

```bat
rdx.bat
```

涓昏彍鍗曞浐瀹氫负锛?
```text
1. Start CLI
2. Start MCP
3. Help
0. Exit
```

鏃犲弬鏁板惎鍔ㄦ椂涓嶄細鐩存帴鎵撳嵃 usage 骞堕€€鍑猴紝鍙湁閫夋嫨 `Exit` 鎵嶄細绂诲紑鑿滃崟銆?
## 2. 浣跨敤 `Start CLI`

`Start CLI` 鏄潰鍚戜汉绫荤殑杩炵画璋冭瘯鍏ュ彛銆?
鎺ㄨ崘娴佺▼锛?
1. 杩愯 `rdx.bat`
2. 閫夋嫨 `1`
3. 閫夋嫨 `default` 鎴栬緭鍏ヨ嚜瀹氫箟 context
4. 鍦ㄦ墦寮€鐨?shell 涓寔缁墽琛?`rdx ...`

甯歌鍛戒护锛?
```bat
rdx capture open --file "C:\path\capture.rdc" --frame-index 0 --connect
rdx capture status
rdx call rd.event.get_actions --args-json "{\"session_id\":\"<session_id>\"}" --json --connect
rdx daemon status
rdx daemon stop
rdx context clear
```

鍐呯疆鍒悕锛?
```bat
status
stop
clear
quit
```

閫€鍑鸿涔夛細

- `exit` / `quit`锛氬彧閫€鍑哄綋鍓?shell
- `rdx daemon stop`锛氭樉寮忓仠姝㈠綋鍓?context 鐨?daemon锛屽苟娓呯悊瀵瑰簲 session state
- `rdx context clear`锛氭竻绌哄綋鍓?context 鐨?capture / session / debug 鐘舵€侊紝浣嗕繚鐣?daemon

## 3. 浣跨敤 `Start MCP`

`Start MCP` 涔熶細鍏堥€夋嫨 context锛屽啀閫夋嫨 transport銆?
### `stdio`

```text
鏃?URL
```

閫傚悎琚閮?`MCP` client 閫氳繃鏍囧噯杈撳叆杈撳嚭鎺ョ銆?
### `streamable-http`

浼氭彁绀鸿緭鍏?`host` / `port`锛屽苟鏄剧ず锛?
```text
http://<host>:<port>
```

閫傚悎閫氳繃 HTTP 璁块棶銆?
## 4. context 璇存槑

`CLI` 鍜?`MCP` 鍏辩敤 daemon / context 鏈哄埗锛屼絾 state 鎸?context 闅旂銆?
- `default`
  - 閫傚悎鍗曟潯璋冭瘯閾捐矾
- custom context
  - 閫傚悎澶氭潯鐙珛閾捐矾骞惰

## 5. 鏈哄櫒妯″紡

淇濈暀缁欒嚜鍔ㄥ寲璺緞浣跨敤锛?
```bat
rdx.bat --help
rdx.bat --non-interactive mcp --ensure-env
rdx.bat --non-interactive cli-shell --help
rdx.bat --non-interactive daemon-shell --daemon-context smoke-test start status stop
```

## 6. legacy 鍒悕

浠ヤ笅鍛戒护浠嶇劧鍙繍琛岋紝浣嗕細鏄犲皠鍒版柊鐨?`Start CLI` 璇箟锛?
```bat
rdx.bat cli-shell
rdx.bat daemon-shell
```

