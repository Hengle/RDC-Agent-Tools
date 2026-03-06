# `rdx-tools`

`rdx-tools` 鏄潰鍚?`RenderDoc` 鐨勬湰鍦?`MCP` + `CLI` 宸ュ叿闆嗐€?
`rdx.bat` 鐜板湪鏄粺涓€鐨勫弻妯″紡 launcher锛?
- 榛樿妯″紡锛氱粰浜虹被浣跨敤鐨勪氦浜掑叆鍙?- `--non-interactive`锛氱粰鑴氭湰銆乻moke銆乤gent銆乺elease gate 浣跨敤鐨勬満鍣ㄥ叆鍙?
## 蹇€熷紑濮?
鐩存帴杩愯锛?
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

## `Start CLI`

`Start CLI` 鏄汉绫绘墜鍔ㄨ皟璇?`.rdc` 鐨勯閫夊叆鍙ｃ€?
瀹冧細锛?
- 閫夋嫨 `default` 鎴栬嚜瀹氫箟 context
- 鍚姩鎴栭檮鐫€鍒板搴?context 鐨?daemon
- 鎵撳紑涓€涓彲杩炵画浣跨敤鐨?`CLI` shell
- 淇濈暀 daemon / context锛岀洿鍒版樉寮忔墽琛屽仠姝㈡垨娓呯悊鍛戒护

鍦?shell 鍐呭彲浠ョ洿鎺ユ墽琛岋細

```bat
rdx capture open --file "C:\path\capture.rdc" --frame-index 0 --connect
rdx capture status
rdx call rd.event.get_actions --args-json "{\"session_id\":\"<session_id>\"}" --json --connect
rdx call rd.shader.debug_start --args-json "{\"session_id\":\"<session_id>\",\"event_id\":17}" --json --connect
rdx daemon status
rdx daemon stop
rdx context clear
```

涔熷彲浠ヤ娇鐢ㄥ唴缃埆鍚嶏細

```bat
status
stop
clear
quit
```

`exit` / `quit` 鍙€€鍑哄綋鍓?shell锛屼笉浼氳嚜鍔?stop daemon锛屼篃涓嶄細鑷姩 clear context銆?
## `Start MCP`

`Start MCP` 涔熸槸鍩轰簬鍚屼竴濂?daemon / context 鏈哄埗锛屼絾闈㈠悜 `MCP` consumer銆?
鍙€?transport锛?
- `stdio`
  - 鏃?URL
  - 閫傚悎琚閮?client 鐩存帴鎺ョ鏍囧噯杈撳叆杈撳嚭
- `streamable-http`
  - 鏄剧ず `host:port`
  - 閫傚悎閫氳繃 HTTP 璁块棶

## `Help`

`Help` 浼氭樉绀猴細

- `rdx-tools` / `Start CLI` / `Start MCP` 鐨勫畾浣?- `stdio` / `streamable-http` 鐨勫樊寮?- 甯歌 `CLI` 鍛戒护绀轰緥
- context 闅旂妯″瀷
- `spec/tool_catalog_196.json` 涓?`docs/` 鐨勫彂鐜拌矾寰?
## context 妯″瀷

context 鐢ㄤ簬闅旂锛?
- capture 鐘舵€?- replay / session 鐘舵€?- active event
- debug 杩囩▼

鎺ㄨ崘锛?
- 鍗曟潯璋冭瘯閾捐矾浣跨敤 `default`
- 澶氭潯骞惰璋冭瘯閾捐矾浣跨敤鑷畾涔?context

## 闈炰氦浜掓ā寮?
浠ヤ笅鍛戒护淇濈暀缁欒嚜鍔ㄥ寲璺緞浣跨敤锛?
```bat
rdx.bat --help
rdx.bat --non-interactive mcp --ensure-env
rdx.bat --non-interactive cli-shell --help
rdx.bat --non-interactive daemon-shell --daemon-context smoke-test start status stop
```

## legacy 鍏煎鍒悕

浠ヤ笅鏃у懡浠や粛鐒跺彲鐢紝浣嗕細鏄犲皠鍒版柊鐨?`Start CLI` 璇箟锛?
```bat
rdx.bat cli-shell
rdx.bat daemon-shell
```

鏂囨。涓嶅啀涓绘帹杩欎袱涓棫鍚嶇О銆?
