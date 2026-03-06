# Troubleshooting

## 鍙屽嚮 `rdx.bat` 涔嬪悗绐楀彛鍍忔槸鈥滈棯閫€鈥?
褰撳墠琛屼负搴斾负杩涘叆浜や簰鑿滃崟锛岃€屼笉鏄洿鎺ユ墦鍗?help 閫€鍑恒€?
濡傛灉娌℃湁杩涘叆鑿滃崟锛岃鍏堟鏌ワ細

- `rdx.bat` 鏄惁鑳芥壘鍒?`scripts/rdx_bat_launcher.ps1`
- 褰撳墠鐩綍鏄惁鏄?`rdx-tools` 鏍圭洰褰?- `RDX_TOOLS_ROOT` 鏄惁琚閮ㄧ幆澧冮敊璇鐩?
## `Start CLI` 閫€鍑哄悗 daemon 杩樺湪

杩欐槸棰勬湡琛屼负銆?
`Start CLI` 鐨?shell 閫€鍑鸿涔夋槸锛?
- `exit` / `quit`
  - 鍙€€鍑哄綋鍓?shell
  - 榛樿淇濈暀 daemon 鍜?context

濡傛灉闇€瑕佹樉寮忓仠姝㈡垨娓呯悊锛岃浣跨敤锛?
```bat
rdx daemon status
rdx daemon stop
rdx context clear
```

## shell 寮傚父鍏抽棴鍚庝細涓嶄細鐣欎笅閲?daemon

launcher / daemon 宸插疄鐜帮細

- `attached_clients`
- lease / heartbeat
- idle TTL
- stale state cleanup

鐭椂闂磋鍏?shell 鍚庯紝浠嶅彲鍦ㄧ浉鍚?context 涓婇噸鏂伴檮鐫€銆?
闀挎椂闂存棤浜烘帴绠℃椂锛宒aemon 浼氬洜涓烘棤 attached client 涓旇秴杩?idle TTL 鑰岃嚜鍔ㄩ€€鍑恒€?
## `Start MCP` 閲岀殑 `stdio` 涓轰粈涔堟病鏈?URL

杩欐槸棰勬湡琛屼负銆?
`stdio` transport 涓嶆彁渚涚綉缁滅鐐癸紝鍥犳 launcher 浼氭槑纭樉绀猴細

```text
URL: no URL
```

濡傛灉闇€瑕佺綉缁滅鐐癸紝璇烽€夋嫨 `streamable-http`銆?
## `streamable-http` 鍚姩澶辫触

浼樺厛妫€鏌ワ細

- `host` / `port` 鏄惁鍙敤
- 褰撳墠鏈哄櫒鏄惁宸叉湁鍏朵粬杩涚▼鍗犵敤鍚屼竴绔彛
- daemon 鏄惁宸茬粡鎴愬姛鍚姩
- `python mcp/run_mcp.py --help` 鏄惁鍙繍琛?
## `rdx daemon status` 杩斿洖 `no active daemon`

鍙兘鍘熷洜锛?
- 璇?context 浠庢湭鍚姩 daemon
- daemon 宸茶鏄惧紡 `stop`
- daemon 鍥犳棤 attached client 涓旇秴杩?idle TTL 鑷姩閫€鍑?- state file 宸茶 stale cleanup 娓呯悊

鍙互閲嶆柊閫氳繃锛?
```bat
rdx.bat
```

杩涘叆 `Start CLI` 鎴?`Start MCP`锛屽啀闄勭潃鍒扮浉鍚?context銆?
## legacy 鍛戒护杩樿兘涓嶈兘鐢?
鍙互銆?
```bat
rdx.bat cli-shell
rdx.bat daemon-shell
```

瀹冧滑浼氭墦鍗颁竴娆″吋瀹规彁绀猴紝鐒跺悗鏄犲皠鍒版柊鐨?`Start CLI` 璇箟銆?
