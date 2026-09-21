# Rekonstruksi posisi LP — snapshot 21 September 2026 14:43:06 WIB

Setiap bagian memisahkan informasi entry, keputusan saat posisi berjalan, dan outcome. Hasil sesudah entry tidak dipakai sebagai sinyal yang dianggap tersedia saat entry. `volatility` adalah angka feed yang tercatat, bukan estimasi sigma harian yang telah diverifikasi. TVL adalah kedalaman agregat, bukan kedalaman eksekusi per bin. Rasio fee entry adalah snapshot pool sesuai timeframe sumber, bukan expected return posisi.

Deposit/withdrawal/fee berasal dari Meteora API dan masih memakai valuasi token API. Divergence di sini adalah perubahan principal terhadap HOLD inventory awal yang seluruhnya SOL, sebelum fee; bukan rumus IL pool constant-product 50:50. Exact swap hanya dicocokkan jika mint, jumlah token penuh, dan waktu cocok unik; sisanya tidak dianggap nol. Gas yang terhubung bukan seluruh overhead wallet.

Distribusi nominal BidAsk adalah model linear SDK satu sisi (bobot 1..N dari active bin ke ujung bawah), bukan snapshot historis likuiditas aktual. Perubahan bin saat inclusion, share terhadap liquidity pesaing, dynamic fee per swap, price-impact quote, dan price path lengkap tidak tersimpan. Tidak ada counterfactual profit yang diklaim. In-range Azimuth adalah observasi monitor dengan gap >180 detik dikeluarkan. In-range Meridian dari journal hanya mengurangi episode OOR terakhir, bukan cumulative occupancy yang terverifikasi.

## azimuth · NINA-SOL · ETdENm4quvn6RXatsNcF9CCEyHWdwQbsiCEHBf5yKtSZ

2026-09-14T11:59:53+07:00 → 2026-09-14T15:28:15+07:00 · 208.37 menit · pool `GfC7qSh4LXp847xxF493D2UjYC1eViMzPKJHfXeYXDdK`.

1. **Market → volatilitas → depth:** Volatility feed 3.293; TVL $10727.95; fee/TVL entry 0.2989%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -610; harga snapshot tidak tersedia SOL/token; range [-654, -610] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.096522344 SOL + 1575.770554000 token. Porsi token pada mark withdrawal 3.40%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -3.2% <= -3.0% with PnL +5.17%, peak +5.67%) — realizing before floor gap-through; hold journal: NINA m5 +2.73% h1 +7.90% pnl +2.73% in-range - 5m bounce with hourly positive, trailing ratchet floor 2.17% about to close into rising price; expect push back toward peak +2.77%
5. **Jalur yang teramati:** 109 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.005194888 SOL (5.1949% modal), divergence principal vs HOLD SOL -0.000079776 SOL, PnL LP +0.005115112 SOL (5.1151%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.005302419; setelah gas terhubung +0.005177419. Swap cocok unik, jeda 1336 detik; selisih terhadap mark token +0.000187307 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · EMBERCAT-SOL · CtSrDcexXrrj8avejZRpMbBqGYWv8baFb3sGJG8Yed2R

2026-09-14T14:33:54+07:00 → 2026-09-14T14:45:04+07:00 · 11.17 menit · pool `CnK1jPqSuhbz1ZEHHhVmud3bkUQyHWsqvRuvW1wQGF9f`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -502; harga snapshot tidak tersedia SOL/token; range [-522, -502] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099998978 SOL + 0.000000000 token; withdraw 0.099990155 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m); recenter parent/root `CR6BCdxZRoeP5LtCuwBudShdEU8emrfeMHv8XvVLB2gT`
5. **Jalur yang teramati:** 0 sampel; in-range teramati tidak tersedia%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000039872 SOL (0.0399% modal), divergence principal vs HOLD SOL -0.000008823 SOL, PnL LP +0.000031049 SOL (0.0310%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · EMBERCAT-SOL · BDtVzqE5n4WNpz3bGJ1APGbQZm6nMJm5p7oB97k8n1QR

2026-09-14T14:45:48+07:00 → 2026-09-14T16:30:32+07:00 · 104.73 menit · pool `CnK1jPqSuhbz1ZEHHhVmud3bkUQyHWsqvRuvW1wQGF9f`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -495; harga snapshot tidak tersedia SOL/token; range [-515, -495] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099998978 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 15747.196584000 token. Porsi token pada mark withdrawal 100.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Hard Stop-Loss hit (-8.83% <= -8.0%)
5. **Jalur yang teramati:** 264 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.002540182 SOL (2.5402% modal), divergence principal vs HOLD SOL -0.009964209 SOL, PnL LP -0.007424027 SOL (-7.4241%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · NINA-SOL · 8mPzwh8TUDp1hda7oimRVVpKpc9GD11R28x17N71rVRA

2026-09-14T15:28:30+07:00 → 2026-09-14T15:48:56+07:00 · 20.43 menit · pool `GfC7qSh4LXp847xxF493D2UjYC1eViMzPKJHfXeYXDdK`.

1. **Market → volatilitas → depth:** Volatility feed 3.293; TVL $10727.95; fee/TVL entry 0.2989%; base fee pool 1.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -617; harga snapshot 0.000002156316 SOL/token; range [-637, -617] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099990494 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 18.8m (limit 5m); recenter parent/root `ETdENm4quvn6RXatsNcF9CCEyHWdwQbsiCEHBf5yKtSZ`
5. **Jalur yang teramati:** 44 sampel; in-range teramati 5.7%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000008345 SOL (0.0083% modal), divergence principal vs HOLD SOL -0.000009496 SOL, PnL LP -0.000001151 SOL (-0.0012%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001151; setelah gas terhubung -0.000021151.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · TWINE-SOL · FDmikzHN3BPL5kW8RJqn1BfxYzRnBdfiakjjMyXg17GM

2026-09-14T16:40:38+07:00 → 2026-09-14T16:52:23+07:00 · 11.75 menit · pool `WRq4e6x2hzEX5hgdyq8KybpLCuxh3YDh2ApGdjERUhZ`.

1. **Market → volatilitas → depth:** Volatility feed 1.699; TVL $72969.42; fee/TVL entry 0.1801%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -371; harga snapshot 0.000024932758 SOL/token; range [-415, -371] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.159999977 SOL + 0.000000000 token; withdraw 0.159999980 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.3m (limit 5m)
5. **Jalur yang teramati:** 30 sampel; in-range teramati 55.0%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000003 SOL (0.0000% modal), divergence principal vs HOLD SOL 0.000000003 SOL, PnL LP +0.000000006 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000000006; setelah gas terhubung -0.000019994.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · Noiz-SOL · 3cwZEfQwmX6sh8aTQjvHpawbFnHb1nyHxx8wUtvKLE3b

2026-09-14T17:58:45+07:00 → 2026-09-14T19:28:57+07:00 · 90.20 menit · pool `8BD8x5Ms3f1unL9YiDGG4XQYxEcot1UqCkqkyTjniUNZ`.

1. **Market → volatilitas → depth:** Volatility feed 2.410; TVL $34958.01; fee/TVL entry 0.8299%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -424; harga snapshot tidak tersedia SOL/token; range [-468, -424] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.159999977 SOL + 0.000000000 token; withdraw 0.092441926 SOL + 5544.277377000 token. Porsi token pada mark withdrawal 39.81%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing Take-Profit hit (Peak: 1.92%, Current: -1.31% <= ratchet floor 1.32%)
5. **Jalur yang teramati:** 241 sampel; in-range teramati 95.2%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.005896813 SOL (3.6855% modal), divergence principal vs HOLD SOL -0.006426893 SOL, PnL LP -0.000530079 SOL (-0.3313%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.002300968; setelah gas terhubung -0.002328771. Swap cocok unik, jeda 179 detik; selisih terhadap mark token -0.001770889 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · STONK10-SOL · PxqcB93KHpFgi8dugFYHxfKEMNaoTAxWRMPi2xZDEU5

2026-09-15T09:17:46+07:00 → 2026-09-15T09:49:08+07:00 · 31.37 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 1.557; TVL $22331.77; fee/TVL entry 0.0523%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -493; harga snapshot 0.000019676945 SOL/token; range [-546, -493] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.159999973 SOL + 0.000000000 token; withdraw 0.159998091 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 1.35% < 5.0% after 30.8m); hold journal: DexScreener SOL pair m5 +14.9% h1 +46.8% — strong bounce off lows, price 0.00002567 climbing back toward upper range 0.00002580 after 21m OOR; expect re-entry into range within 15m
5. **Jalur yang teramati:** 60 sampel; in-range teramati 11.4%; maksimum penurunan teramati sejak snapshot 3.14%.
6. **Fee → drift → divergence → hasil:** Fee +0.000047035 SOL (0.0294% modal), divergence principal vs HOLD SOL -0.000001882 SOL, PnL LP +0.000045153 SOL (0.0282%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · PVE-SOL · 8Q65qQXiXJYFfCvFqA1U5pAnmcNnMcZYHPc6PVSWckDB

2026-09-15T09:31:12+07:00 → 2026-09-15T09:31:28+07:00 · 0.27 menit · pool `4apFUjxT1BrvmuPHzxxMnerMHxzYKG64GePi8ApnSaqg`.

1. **Market → volatilitas → depth:** Volatility feed 4.387; TVL $14010.64; fee/TVL entry 0.1292%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -432; harga snapshot 0.000013588344 SOL/token; range [-476, -432] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099903634 SOL + 6.819175000 token. Porsi token pada mark withdrawal 0.09%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** journal unavailable
5. **Jalur yang teramati:** 0 sampel; in-range teramati tidak tersedia%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000003684 SOL, PnL LP -0.000003684 SOL (-0.0037%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · Noiz-SOL · FqcSZqcAzMdEJb3g6pQPtS5QJVjr6LPByuUZqVmFvh6h

2026-09-15T09:53:32+07:00 → 2026-09-15T10:54:40+07:00 · 61.13 menit · pool `8BD8x5Ms3f1unL9YiDGG4XQYxEcot1UqCkqkyTjniUNZ`.

1. **Market → volatilitas → depth:** Volatility feed 1.355; TVL $13455.35; fee/TVL entry 0.5700%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -481; harga snapshot 0.000008344863 SOL/token; range [-525, -481] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099434529 SOL + 68.629659000 token. Porsi token pada mark withdrawal 0.56%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stale ticket re-pin (60m in range, peak +0.12% never armed the 1.2% ratchet, fee/TVL 7.1%)
5. **Jalur yang teramati:** 116 sampel; in-range teramati 90.8%; maksimum penurunan teramati sejak snapshot 4.85%.
6. **Fee → drift → divergence → hasil:** Fee +0.000302507 SOL (0.3025% modal), divergence principal vs HOLD SOL -0.000004029 SOL, PnL LP +0.000298478 SOL (0.2985%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Batas umur/peak sendiri belum membuktikan biaya reposisi layak; snapshot fee pace posisi diperlukan. 

## azimuth · DOGE-1-SOL · 4Dv6BkpjNgPSdraYZLSWFavP6NkNyZAKrznbspwhL1pq

2026-09-15T11:16:49+07:00 → 2026-09-15T12:17:27+07:00 · 60.63 menit · pool `ErwEeF8y8uLR7LkJcL3xRUuN1d8SrMLZJB92Ydq8vfdw`.

1. **Market → volatilitas → depth:** Volatility feed 6.198; TVL $56109.19; fee/TVL entry 0.2255%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1696; harga snapshot 0.000001351878 SOL/token; range [-1749, -1696] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999975 SOL + 0.000000000 token; withdraw 0.143622868 SOL + 4968.999636142 token. Porsi token pada mark withdrawal 4.14%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 2.28% < 5.0% after 60.2m)
5. **Jalur yang teramati:** 104 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 7.66%.
6. **Fee → drift → divergence → hasil:** Fee +0.000141804 SOL (0.0945% modal), divergence principal vs HOLD SOL -0.000174115 SOL, PnL LP -0.000032312 SOL (-0.0215%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · HUHCAT-SOL · 6WzHs9Ncvs79pbAMF8xSjUys9TKxkWz6GSDAw87g4qan

2026-09-15T11:28:40+07:00 → 2026-09-15T11:35:30+07:00 · 6.83 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 10.699; TVL $141611.46; fee/TVL entry 4.5034%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -471; harga snapshot 0.000009217920 SOL/token; range [-515, -471] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099998530 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.3m (limit 5m)
5. **Jalur yang teramati:** 9 sampel; in-range teramati 11.6%; maksimum penurunan teramati sejak snapshot 2.94%.
6. **Fee → drift → divergence → hasil:** Fee +0.000146507 SOL (0.1465% modal), divergence principal vs HOLD SOL -0.000001449 SOL, PnL LP +0.000145058 SOL (0.1451%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · HUHCAT-SOL · EwyYWKJsRUp14sou5XuFpYCmQWH6KhhP18exsf6kgHT7

2026-09-15T11:36:01+07:00 → 2026-09-15T11:41:25+07:00 · 5.40 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 10.699; TVL $141611.46; fee/TVL entry 4.5034%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -443; harga snapshot 0.000012179555 SOL/token; range [-463, -443] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.055410788 SOL + 3989.730501000 token. Porsi token pada mark withdrawal 43.52%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -5.4% <= -3.0% with PnL +1.56%, peak +1.56%) — realizing before floor gap-through; recenter parent/root `6WzHs9Ncvs79pbAMF8xSjUys9TKxkWz6GSDAw87g4qan`
5. **Jalur yang teramati:** 7 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 13.87%.
6. **Fee → drift → divergence → hasil:** Fee +0.003222461 SOL (3.2225% modal), divergence principal vs HOLD SOL -0.001892226 SOL, PnL LP +0.001330235 SOL (1.3302%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · HUHCAT-SOL · 9vhEK5xXoSWbfpYfvji2n9bXFmH9pLP7QutthVsoEZJc

2026-09-15T11:42:07+07:00 → 2026-09-15T11:48:09+07:00 · 6.03 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -457; harga snapshot 0.000010595762 SOL/token; range [-477, -457] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099994275 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m); recenter parent/root `6WzHs9Ncvs79pbAMF8xSjUys9TKxkWz6GSDAw87g4qan`
5. **Jalur yang teramati:** 8 sampel; in-range teramati 0.0%; maksimum penurunan teramati sejak snapshot -6.15%.
6. **Fee → drift → divergence → hasil:** Fee +0.000005082 SOL (0.0051% modal), divergence principal vs HOLD SOL -0.000005715 SOL, PnL LP -0.000000633 SOL (-0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000633; setelah gas terhubung -0.000020633.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · Noiz-SOL · 2cDpaVhCk8hBAwRBHvWzKTyKMmqHzmJywqk9AdkWTQTE

2026-09-15T12:19:46+07:00 → 2026-09-15T13:07:17+07:00 · 47.52 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 4.397; TVL $33564.44; fee/TVL entry 0.6924%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -504; harga snapshot 0.000006637853 SOL/token; range [-548, -504] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999978 SOL + 0.000000000 token; withdraw 0.149996871 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m)
5. **Jalur yang teramati:** 77 sampel; in-range teramati 90.0%; maksimum penurunan teramati sejak snapshot 6.73%.
6. **Fee → drift → divergence → hasil:** Fee +0.001060141 SOL (0.7068% modal), divergence principal vs HOLD SOL -0.000003107 SOL, PnL LP +0.001057034 SOL (0.7047%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · PURPS-SOL · 4bjah6TboD5sbh3bupFkjUukjKKQU4Ttwb9kLJ8Wu742

2026-09-15T12:40:15+07:00 → 2026-09-15T13:41:11+07:00 · 60.93 menit · pool `5vTfWvfTcMzcshVVC47TAwwvRikLQgBaJnKoJWGjS9hE`.

1. **Market → volatilitas → depth:** Volatility feed 2.635; TVL $76189.46; fee/TVL entry 0.2344%; base fee pool 2.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -320; harga snapshot 0.000018775426 SOL/token; range [-355, -320] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.099845274 SOL + 8.028446000 token. Porsi token pada mark withdrawal 0.15%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 4.51% < 5.0% after 60.4m)
5. **Jalur yang teramati:** 103 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 6.02%.
6. **Fee → drift → divergence → hasil:** Fee +0.000189750 SOL (0.1898% modal), divergence principal vs HOLD SOL -0.000005832 SOL, PnL LP +0.000183918 SOL (0.1839%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · HUHCAT-SOL · 7bb76pKaUG1RzH1jw6PZFLmJ35QgkBp9CsQwTfzegro5

2026-09-15T13:46:01+07:00 → 2026-09-15T14:01:56+07:00 · 15.92 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 2.555; TVL $117959.44; fee/TVL entry 0.8884%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -472; harga snapshot 0.000009126654 SOL/token; range [-516, -472] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.159999977 SOL + 0.000000000 token; withdraw 0.145483450 SOL + 1727.147034000 token. Porsi token pada mark withdrawal 8.69%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -7.1% <= -3.0% with PnL +1.12%, peak +1.40%) — realizing before floor gap-through
5. **Jalur yang teramati:** 29 sampel; in-range teramati 85.6%; maksimum penurunan teramati sejak snapshot 19.66%.
6. **Fee → drift → divergence → hasil:** Fee +0.002852464 SOL (1.7828% modal), divergence principal vs HOLD SOL -0.000666104 SOL, PnL LP +0.002186359 SOL (1.3665%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001494232; setelah gas terhubung +0.001464150. Swap cocok unik, jeda 85 detik; selisih terhadap mark token -0.000692127 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · PUMPCADE-SOL · 2H3cL8Qjd5KMxEfrsd7zGsDW9y3gJHoA6BNZC7cvFJF8

2026-09-15T14:04:39+07:00 → 2026-09-15T14:35:38+07:00 · 30.98 menit · pool `AY2GKBFGhFKJ7vzy5V7fYzRu7kbWByfFSG8zZQjPqVSe`.

1. **Market → volatilitas → depth:** Volatility feed 4.021; TVL $86707.63; fee/TVL entry 0.0898%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -235; harga snapshot 0.000096488857 SOL/token; range [-279, -235] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.159999977 SOL + 0.000000000 token; withdraw 0.159998450 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.04% < 5.0% after 30.2m)
5. **Jalur yang teramati:** 57 sampel; in-range teramati 30.3%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000001326 SOL (0.0008% modal), divergence principal vs HOLD SOL -0.000001527 SOL, PnL LP -0.000000201 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000201; setelah gas terhubung -0.000020201.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · HUHCAT-SOL · 65uyPDPCoehgoRZfDrMPMbcBwPQBWSqQXGueUV566h2P

2026-09-15T14:18:41+07:00 → 2026-09-15T14:19:12+07:00 · 0.52 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 3.686; TVL $114110.25; fee/TVL entry 1.0896%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -477; harga snapshot 0.000008683698 SOL/token; range [-521, -477] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099973086 SOL + 2.796184000 token. Porsi token pada mark withdrawal 0.02%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** journal unavailable
5. **Jalur yang teramati:** 0 sampel; in-range teramati tidak tersedia%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000001453 SOL (0.0015% modal), divergence principal vs HOLD SOL -0.000002612 SOL, PnL LP -0.000001159 SOL (-0.0012%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · MINI-SOL · EzzhMAhzSEaPKimr3TYig85ZNpiw7ShJptog7eJnUG5N

2026-09-15T14:44:32+07:00 → 2026-09-15T15:01:20+07:00 · 16.80 menit · pool `64BSmy7BESiHnWYzLdPso6FuXymh7H8jTkaiyfbBg1YD`.

1. **Market → volatilitas → depth:** Volatility feed 10.418; TVL $54580.76; fee/TVL entry 0.5298%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -267; harga snapshot 0.000036268240 SOL/token; range [-302, -267] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.159999982 SOL + 0.000000000 token; withdraw 0.159988237 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.1m (limit 5m)
5. **Jalur yang teramati:** 31 sampel; in-range teramati 71.3%; maksimum penurunan teramati sejak snapshot 3.66%.
6. **Fee → drift → divergence → hasil:** Fee +0.000295619 SOL (0.1848% modal), divergence principal vs HOLD SOL -0.000011745 SOL, PnL LP +0.000283874 SOL (0.1774%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · MINI-SOL · 3thBu6P7VqKQijkEQQMgiVQ2rXsMfqHrK94Z9H1YgAQK

2026-09-15T15:01:52+07:00 → 2026-09-15T16:50:48+07:00 · 108.93 menit · pool `64BSmy7BESiHnWYzLdPso6FuXymh7H8jTkaiyfbBg1YD`.

1. **Market → volatilitas → depth:** Volatility feed 10.418; TVL $54580.76; fee/TVL entry 0.5298%; base fee pool 5.0%; bin step 125 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -259; harga snapshot 0.000040057767 SOL/token; range [-279, -259] (21 bin), downside 22.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.159999990 SOL + 0.000000000 token; withdraw 0.105976353 SOL + 1479.058748000 token. Porsi token pada mark withdrawal 32.78%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing Take-Profit hit (Peak: 1.26%, Current: 0.19% <= ratchet floor 0.66%); recenter parent/root `EzzhMAhzSEaPKimr3TYig85ZNpiw7ShJptog7eJnUG5N`
5. **Jalur yang teramati:** 197 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 12.77%.
6. **Fee → drift → divergence → hasil:** Fee +0.003590584 SOL (2.2441% modal), divergence principal vs HOLD SOL -0.002343124 SOL, PnL LP +0.001247460 SOL (0.7797%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · PERPSPAD-SOL · 2rJZV5J7LtQxsbuMnxrQ3XSDcpeNWge4NBCdSvVK4XHZ

2026-09-15T15:16:14+07:00 → 2026-09-15T15:47:40+07:00 · 31.43 menit · pool `EHqk4Fw3pTCf9UW75dWoCMf6a2GxyJ8FGYEj2Qmw9rfr`.

1. **Market → volatilitas → depth:** Volatility feed 2.005; TVL $49742.45; fee/TVL entry 0.0546%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -344; harga snapshot 0.000064502560 SOL/token; range [-397, -344] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.098846229 SOL + 18.294437000 token. Porsi token pada mark withdrawal 1.13%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 3.63% < 5.0% after 30.3m); hold journal: PERPSPAD-SOL OOR 2.4m, dexscreener SOL pair m5 +2.31% h1 +28.53% (pnl +0.08%, peak +0.19%); price rising back toward range, expect re-entry above entry 0.00006149 vs pool 0.00006519
5. **Jalur yang teramati:** 46 sampel; in-range teramati 89.2%; maksimum penurunan teramati sejak snapshot 4.67%.
6. **Fee → drift → divergence → hasil:** Fee +0.000076999 SOL (0.0770% modal), divergence principal vs HOLD SOL -0.000019797 SOL, PnL LP +0.000057201 SOL (0.0572%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · BUTTHOLE-SOL · EK8v7VeXy11UPhJtPHknYrYuWixpsJ7oCdjNribg81MR

2026-09-15T17:47:58+07:00 → 2026-09-15T17:54:36+07:00 · 6.63 menit · pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatilitas → depth:** Volatility feed 1.387; TVL $96391.95; fee/TVL entry 0.3139%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1344; harga snapshot 0.000022338029 SOL/token; range [-1397, -1344] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999975 SOL + 0.000000000 token; withdraw 0.149999740 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m)
5. **Jalur yang teramati:** 11 sampel; in-range teramati 18.9%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000211 SOL (0.0001% modal), divergence principal vs HOLD SOL -0.000000235 SOL, PnL LP -0.000000024 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000024; setelah gas terhubung -0.000020024.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · UBI-SOL · 5aZhWN5UF9CD8qUJwddGaaHjPLVBHqb296SLjh2e7TVo

2026-09-15T17:53:37+07:00 → 2026-09-15T18:44:00+07:00 · 50.38 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 1.723; TVL $29484.22; fee/TVL entry 0.1081%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1172; harga snapshot 0.000008616878 SOL/token; range [-1216, -1172] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099888557 SOL + 13.671848906 token. Porsi token pada mark withdrawal 0.12%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 4.97% < 5.0% after 49.8m)
5. **Jalur yang teramati:** 96 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.000170533 SOL (0.1705% modal), divergence principal vs HOLD SOL 0.000005220 SOL, PnL LP +0.000175753 SOL (0.1758%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · TOAD-SOL · DCYP7zKDz3AYr53ZJJjLBpZy5rgEzavjquVPoLsvj58y

2026-09-15T18:59:43+07:00 → 2026-09-15T19:30:40+07:00 · 30.95 menit · pool `AFT9ZhYVHMRQrnntMYnqVrKvVrAxpaspCEMBXQNVMwLo`.

1. **Market → volatilitas → depth:** Volatility feed 4.011; TVL $126970.30; fee/TVL entry 0.1185%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -374; harga snapshot 0.000024199490 SOL/token; range [-418, -374] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999978 SOL + 0.000000000 token; withdraw 0.149130403 SOL + 36.398750000 token. Porsi token pada mark withdrawal 0.57%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.16% < 5.0% after 30.4m)
5. **Jalur yang teramati:** 59 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000008543 SOL (0.0057% modal), divergence principal vs HOLD SOL -0.000014649 SOL, PnL LP -0.000006106 SOL (-0.0041%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · BULLSHIT-SOL · B91YPxdk3qdqyTJxWhwWnnNMbBHNKoAspM94Ygax8ATv

2026-09-15T19:10:12+07:00 → 2026-09-15T19:10:30+07:00 · 0.30 menit · pool `DchDNJc71s11WaHzJRjzW4qG6qbYC8ySzbBMcFmnAThk`.

1. **Market → volatilitas → depth:** Volatility feed 2.071; TVL $12591.35; fee/TVL entry 0.0551%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -500; harga snapshot 0.000006907376 SOL/token; range [-544, -500] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099326399 SOL + 99.016038000 token. Porsi token pada mark withdrawal 0.66%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** journal unavailable
5. **Jalur yang teramati:** 0 sampel; in-range teramati tidak tersedia%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000006012 SOL (0.0060% modal), divergence principal vs HOLD SOL -0.000009754 SOL, PnL LP -0.000003742 SOL (-0.0037%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · SCRIBE-SOL · CrK3wB1HKoaVCadTk361j6MbzgVg9nf3Tq2gNjMi4Sdp

2026-09-15T19:38:45+07:00 → 2026-09-15T20:08:57+07:00 · 30.20 menit · pool `9VGCLeeBDrE1CP3QDpd6rHLqBkqCJPVw4xWpPFMpGbqd`.

1. **Market → volatilitas → depth:** Volatility feed 5.436; TVL $12766.02; fee/TVL entry 1.5355%; base fee pool 0.6%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -511; harga snapshot 0.000017047790 SOL/token; range [-564, -511] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999975 SOL + 0.000000000 token; withdraw 0.122300212 SOL + 1827.413530000 token. Porsi token pada mark withdrawal 17.61%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-26.8% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 58 sampel; in-range teramati 24.1%; maksimum penurunan teramati sejak snapshot 16.08%.
6. **Fee → drift → divergence → hasil:** Fee +0.002761605 SOL (1.8411% modal), divergence principal vs HOLD SOL -0.001555692 SOL, PnL LP +0.001205913 SOL (0.8039%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001647518; setelah gas terhubung +0.001522518. Swap cocok unik, jeda 32 detik; selisih terhadap mark token +0.000441605 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · Noiz-SOL · iLqAXd979jkzxz58b8GKiDuhwiPvsazPEc3sqJc2x2T

2026-09-15T20:47:34+07:00 → 2026-09-15T21:07:32+07:00 · 19.97 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 1.950; TVL $16784.49; fee/TVL entry 0.2406%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -521; harga snapshot 0.000005604853 SOL/token; range [-565, -521] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999978 SOL + 0.000000000 token; withdraw 0.149999927 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m)
5. **Jalur yang teramati:** 38 sampel; in-range teramati 52.3%; maksimum penurunan teramati sejak snapshot 4.85%.
6. **Fee → drift → divergence → hasil:** Fee +0.000221543 SOL (0.1477% modal), divergence principal vs HOLD SOL -0.000000051 SOL, PnL LP +0.000221492 SOL (0.1477%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · Noiz-SOL · Cs42t2hT9m1aiTUdsgaUzEqDUNXXZeBhxMz98rvCjUat

2026-09-15T21:08:01+07:00 → 2026-09-15T21:15:58+07:00 · 7.95 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 1.950; TVL $16784.49; fee/TVL entry 0.2406%; base fee pool 3.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -511; harga snapshot 0.000006191245 SOL/token; range [-531, -511] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999989 SOL + 0.000000000 token; withdraw 0.148296811 SOL + 271.713983000 token. Porsi token pada mark withdrawal 1.11%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m); recenter parent/root `iLqAXd979jkzxz58b8GKiDuhwiPvsazPEc3sqJc2x2T`
5. **Jalur yang teramati:** 12 sampel; in-range teramati 22.8%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000073729 SOL (0.0492% modal), divergence principal vs HOLD SOL -0.000037586 SOL, PnL LP +0.000036143 SOL (0.0241%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · fart-SOL · 4uj7SGhMaUaPrU1P9u67LGgHuqgACnsbBNUsvQHkAURR

2026-09-15T21:10:44+07:00 → 2026-09-15T21:31:43+07:00 · 20.98 menit · pool `Bq3PKRZ8bUzNry7rKd85DrQ6yJYKycpkN2uZcfYh6mCH`.

1. **Market → volatilitas → depth:** Volatility feed 6.258; TVL $11591.55; fee/TVL entry 1.0380%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -623; harga snapshot 0.000002031347 SOL/token; range [-667, -623] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.025746385 SOL + 47141.695808000 token. Porsi token pada mark withdrawal 71.82%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-24.4% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 28 sampel; in-range teramati 57.7%; maksimum penurunan teramati sejak snapshot 11.26%.
6. **Fee → drift → divergence → hasil:** Fee +0.002765670 SOL (2.7657% modal), divergence principal vs HOLD SOL -0.008642522 SOL, PnL LP -0.005876853 SOL (-5.8769%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.006152314; setelah gas terhubung -0.006277314. Swap cocok unik, jeda 29 detik; selisih terhadap mark token -0.000275461 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · Noiz-SOL · HRZwfeQPfGK5VV8wVTXGMVrsPrpaLvFMgqbSgtRdbFtp

2026-09-15T21:16:28+07:00 → 2026-09-15T21:30:28+07:00 · 14.00 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 3.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -512; harga snapshot 0.000006129946 SOL/token; range [-532, -512] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999989 SOL + 0.000000000 token; withdraw 0.149980828 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m); recenter parent/root `iLqAXd979jkzxz58b8GKiDuhwiPvsazPEc3sqJc2x2T`; hold journal: m5 +5.94% h1 +6.37% on SOL pair; OOR 4.5m price rebounding back toward range, expect re-entry
5. **Jalur yang teramati:** 19 sampel; in-range teramati 62.1%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000022261 SOL (0.0148% modal), divergence principal vs HOLD SOL -0.000019161 SOL, PnL LP +0.000003100 SOL (0.0021%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · LMAO!-SOL · FgQExpZDAaE7XHCVZvwtTK5auGrwtzbQRugPfyQ6N9f9

2026-09-15T22:18:15+07:00 → 2026-09-15T23:19:21+07:00 · 61.10 menit · pool `8k61EzwUzjdCZqKqGWTW2ygjmAdWGV6VZNPpDNkmo9dd`.

1. **Market → volatilitas → depth:** Volatility feed 1.723; TVL $21444.72; fee/TVL entry 0.1574%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -378; harga snapshot 0.000023255234 SOL/token; range [-422, -378] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999978 SOL + 0.000000000 token; withdraw 0.149358213 SOL + 27.884964000 token. Porsi token pada mark withdrawal 0.42%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.28% < 5.0% after 60.4m)
5. **Jalur yang teramati:** 119 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 2.94%.
6. **Fee → drift → divergence → hasil:** Fee +0.000019163 SOL (0.0128% modal), divergence principal vs HOLD SOL -0.000006071 SOL, PnL LP +0.000013092 SOL (0.0087%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · UBI-SOL · CQ1BcC8WAABUKSnGvnbSkezie9SRuC1pJorGQjaPKsAf

2026-09-15T23:17:37+07:00 → 2026-09-16T00:18:25+07:00 · 60.80 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $38260.11; fee/TVL entry 0.7512%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1173; harga snapshot 0.000008531562 SOL/token; range [-1217, -1173] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.096491477 SOL + 431.015890432 token. Porsi token pada mark withdrawal 3.40%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stale ticket re-pin (60m in range, peak +0.44% never armed the 1.2% ratchet, fee/TVL 5.6%)
5. **Jalur yang teramati:** 110 sampel; in-range teramati 97.6%; maksimum penurunan teramati sejak snapshot 7.65%.
6. **Fee → drift → divergence → hasil:** Fee +0.000236474 SOL (0.2365% modal), divergence principal vs HOLD SOL -0.000112634 SOL, PnL LP +0.000123840 SOL (0.1238%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Batas umur/peak sendiri belum membuktikan biaya reposisi layak; snapshot fee pace posisi diperlukan. 

## azimuth · FLAME-SOL · 66cxUpaCA6QmQTsG1e1z94xiEV86xrYHRTfTTKtu4aoA

2026-09-15T23:30:02+07:00 → 2026-09-15T23:35:33+07:00 · 5.52 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 1.680; TVL $40022.25; fee/TVL entry 0.1914%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -624; harga snapshot 0.000006928320 SOL/token; range [-677, -624] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999314 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m)
5. **Jalur yang teramati:** 8 sampel; in-range teramati 0.0%; maksimum penurunan teramati sejak snapshot -2.42%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000589 SOL (0.0006% modal), divergence principal vs HOLD SOL -0.000000661 SOL, PnL LP -0.000000072 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000072; setelah gas terhubung -0.000020072.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · CAT-SOL · 2H9yJdoHtd6D8imqwcBmJY2NsFo9mibX8MeS27UJr7NF

2026-09-16T00:26:58+07:00 → 2026-09-16T00:33:37+07:00 · 6.65 menit · pool `Hcm1L9GY3xGd6XXQRYdzB5LFhF1vTq6uQQd1tB5qQTKh`.

1. **Market → volatilitas → depth:** Volatility feed 13.188; TVL $10361.97; fee/TVL entry 2.3271%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -430; harga snapshot 0.000004787803 SOL/token; range [-465, -430] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999982 SOL + 0.000000000 token; withdraw 0.139999284 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.4m (limit 5m)
5. **Jalur yang teramati:** 11 sampel; in-range teramati 9.0%; maksimum penurunan teramati sejak snapshot -0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000609 SOL (0.0004% modal), divergence principal vs HOLD SOL -0.000000698 SOL, PnL LP -0.000000089 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000089; setelah gas terhubung -0.000020089.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · SCRIBE-SOL · Ap6Gv6ucv3wU8xb5Xijq13xwe6HdbP3FLjhYvTfZWkJk

2026-09-16T00:30:49+07:00 → 2026-09-16T00:56:00+07:00 · 25.18 menit · pool `BZJTiubWLruAhoBxCTgU3uVdvXFztsr4cKG7SZcxoQdC`.

1. **Market → volatilitas → depth:** Volatility feed 3.270; TVL $45096.42; fee/TVL entry 0.6904%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -543; harga snapshot 0.000004502918 SOL/token; range [-587, -543] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099034087 SOL + 218.897546000 token. Porsi token pada mark withdrawal 0.95%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -6.4% <= -3.0% with PnL +1.21%, peak +1.55%) — realizing before floor gap-through
5. **Jalur yang teramati:** 40 sampel; in-range teramati 86.7%; maksimum penurunan teramati sejak snapshot 8.57%.
6. **Fee → drift → divergence → hasil:** Fee +0.000333749 SOL (0.3337% modal), divergence principal vs HOLD SOL -0.000018675 SOL, PnL LP +0.000315073 SOL (0.3151%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · FROGE-SOL · EjNfTGDNdhb95y2tMtRq91t6QfPsyNxu288uBBHTrbfD

2026-09-16T00:45:39+07:00 → 2026-09-16T01:45:41+07:00 · 60.03 menit · pool `5Vo1BAJ888m3Mn5dVxLNXtCkdmxVN6RDNDocMHM75yG`.

1. **Market → volatilitas → depth:** Volatility feed 2.150; TVL $22573.98; fee/TVL entry 0.2987%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1241; harga snapshot 0.000004336857 SOL/token; range [-1285, -1241] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.095683358 SOL + 1049.076712865 token. Porsi token pada mark withdrawal 4.21%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -3.1% <= -3.0% with PnL -1.52% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 109 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 2.94%.
6. **Fee → drift → divergence → hasil:** Fee +0.000117924 SOL (0.1179% modal), divergence principal vs HOLD SOL -0.000115053 SOL, PnL LP +0.000002871 SOL (0.0029%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · HUHCAT-SOL · 4te9rr9JEwFahU8WcDVfVvGL7gtFvGzWLx7xCUYv3gNk

2026-09-16T02:46:53+07:00 → 2026-09-16T02:57:56+07:00 · 11.05 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 4.289; TVL $72101.54; fee/TVL entry 0.4804%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -427; harga snapshot 0.000014281486 SOL/token; range [-471, -427] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.139848452 SOL + 10.423790000 token. Porsi token pada mark withdrawal 0.11%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.1m (limit 5m)
5. **Jalur yang teramati:** 18 sampel; in-range teramati 41.1%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000050327 SOL (0.0359% modal), divergence principal vs HOLD SOL -0.000004134 SOL, PnL LP +0.000046193 SOL (0.0330%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · FLAME-SOL · Gad39TXZsb8EXQrKxbiP2zhCTyMu9caUQthiZH3pDShE

2026-09-16T02:53:18+07:00 → 2026-09-16T03:09:34+07:00 · 16.27 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 2.481; TVL $32719.29; fee/TVL entry 0.6811%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -639; harga snapshot tidak tersedia SOL/token; range [-692, -639] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999531 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 27 sampel; in-range teramati 62.4%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000003807 SOL (0.0038% modal), divergence principal vs HOLD SOL -0.000000444 SOL, PnL LP +0.000003363 SOL (0.0034%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · SCRIBE-SOL · GpDYNd1dythhkMdKauz6pNVws3DAsFRzbBZDSsfmfoKc

2026-09-16T03:07:57+07:00 → 2026-09-16T03:17:11+07:00 · 9.23 menit · pool `BZJTiubWLruAhoBxCTgU3uVdvXFztsr4cKG7SZcxoQdC`.

1. **Market → volatilitas → depth:** Volatility feed 5.046; TVL $45741.78; fee/TVL entry 1.4836%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -494; harga snapshot 0.000007332319 SOL/token; range [-538, -494] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.060993808 SOL + 6373.828815000 token. Porsi token pada mark withdrawal 36.94%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -4.3% <= -3.0% with PnL -1.95% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 13 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 21.24%.
6. **Fee → drift → divergence → hasil:** Fee +0.001623412 SOL (1.6234% modal), divergence principal vs HOLD SOL -0.003281795 SOL, PnL LP -0.001658382 SOL (-1.6584%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · PAID-SOL · e3EFDh52HmxqPWe83BXWC28d5ryRbfFf41EF8AvVFE2

2026-09-16T03:44:19+07:00 → 2026-09-16T03:57:17+07:00 · 12.97 menit · pool `6xf7dn56P55zJEL9CoMDiDLqqTo7zF1dScEPqNZm92PF`.

1. **Market → volatilitas → depth:** Volatility feed 14.171; TVL $27232.42; fee/TVL entry 25.5801%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -492; harga snapshot 0.000007479699 SOL/token; range [-536, -492] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999978 SOL + 0.000000000 token; withdraw 0.149996563 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.3m (limit 5m)
5. **Jalur yang teramati:** 23 sampel; in-range teramati 15.7%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000160187 SOL (0.1068% modal), divergence principal vs HOLD SOL -0.000003415 SOL, PnL LP +0.000156772 SOL (0.1045%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000156772; setelah gas terhubung +0.000136772.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · FLAME-SOL · 7UJbvyTQ3E43miQ5arGzueSddhEWBBnBCk6wyNN49AHF

2026-09-16T04:11:42+07:00 → 2026-09-16T04:46:50+07:00 · 35.13 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 3.662; TVL $37403.94; fee/TVL entry 0.1885%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -610; harga snapshot 0.000007745963 SOL/token; range [-663, -610] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999975 SOL + 0.000000000 token; withdraw 0.116508657 SOL + 4924.364031000 token. Porsi token pada mark withdrawal 21.15%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -5.4% <= -3.0% with PnL -1.57% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 68 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 17.41%.
6. **Fee → drift → divergence → hasil:** Fee +0.000747143 SOL (0.4981% modal), divergence principal vs HOLD SOL -0.002236839 SOL, PnL LP -0.001489696 SOL (-0.9931%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · SCRIBE-SOL · Ct9mqu5C7J6MQg7WNyuqovWvH7e8e2vrSe3nDgxbXoQV

2026-09-16T05:55:42+07:00 → 2026-09-16T06:45:56+07:00 · 50.23 menit · pool `BZJTiubWLruAhoBxCTgU3uVdvXFztsr4cKG7SZcxoQdC`.

1. **Market → volatilitas → depth:** Volatility feed 6.527; TVL $51195.38; fee/TVL entry 1.6394%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -488; harga snapshot 0.000007783404 SOL/token; range [-532, -488] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999978 SOL + 0.000000000 token; withdraw 0.085394763 SOL + 10043.327727000 token. Porsi token pada mark withdrawal 40.69%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Sustained downtrend dump (1h -20.7% <= -5.0% & PnL -3.13% <= -2.5%) — risk floor
5. **Jalur yang teramati:** 81 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 20.46%.
6. **Fee → drift → divergence → hasil:** Fee +0.003859164 SOL (2.5728% modal), divergence principal vs HOLD SOL -0.006028179 SOL, PnL LP -0.002169016 SOL (-1.4460%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.006185843; setelah gas terhubung -0.006210843. Swap cocok unik, jeda 139 detik; selisih terhadap mark token -0.004016827 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · ELON-SOL · 4qYviNAxbXMntzVoACKCmaLAAEtKFbQMZcZJGASU3C5p

2026-09-16T06:00:40+07:00 → 2026-09-16T06:06:31+07:00 · 5.85 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 8.376; TVL $13247.88; fee/TVL entry 8.7198%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -509; harga snapshot 0.000017321646 SOL/token; range [-562, -509] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999976 SOL + 0.000000000 token; withdraw 0.099999429 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -5.0% <= -3.0% with PnL +1.62%, peak +1.62%) — realizing before floor gap-through; hold journal: Dexscreener ELON-SOL pool m5 +9.71% h1 +24.61% - OOR only 0.7m, price bouncing back toward range; trailing floor 0.94% not yet hit, expect re-entry
5. **Jalur yang teramati:** 8 sampel; in-range teramati 42.5%; maksimum penurunan teramati sejak snapshot 8.39%.
6. **Fee → drift → divergence → hasil:** Fee +0.001503631 SOL (1.5036% modal), divergence principal vs HOLD SOL -0.000000547 SOL, PnL LP +0.001503084 SOL (1.5031%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · biketyson-SOL · 3i6e4TsWXovuKZT9GPAhzkKURj4imG694sapEyP8Jyp4

2026-09-16T06:21:56+07:00 → 2026-09-16T06:29:43+07:00 · 7.78 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $92184.98; fee/TVL entry 0.1629%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -348; harga snapshot 0.000031344542 SOL/token; range [-392, -348] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099998998 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.3m (limit 5m)
5. **Jalur yang teramati:** 11 sampel; in-range teramati 28.2%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000874 SOL (0.0009% modal), divergence principal vs HOLD SOL -0.000000981 SOL, PnL LP -0.000000107 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000107; setelah gas terhubung -0.000020107.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · biketyson-SOL · GMZUg6Wd3UfAnhT41HT66E4o4mJb7uikBvAHz7R3tKiD

2026-09-16T06:30:12+07:00 → 2026-09-16T07:10:59+07:00 · 40.78 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $92184.98; fee/TVL entry 0.1629%; base fee pool 1.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -346; harga snapshot 0.000031974567 SOL/token; range [-366, -346] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.100003228 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 12.5m (limit 5m); recenter parent/root `3i6e4TsWXovuKZT9GPAhzkKURj4imG694sapEyP8Jyp4`; hold journal: m5 +10.51% h1 -0.28% on DLMM SOL pair 9F5zc (token-level m5 +8.75% h1 -2.16%); in-range +1.36% PnL, fresh 5m bounce off h6 -27.7% downtrend - deferring trailing close to let bounce extend
5. **Jalur yang teramati:** 70 sampel; in-range teramati 60.8%; maksimum penurunan teramati sejak snapshot 11.26%.
6. **Fee → drift → divergence → hasil:** Fee +0.001904317 SOL (1.9043% modal), divergence principal vs HOLD SOL 0.000003238 SOL, PnL LP +0.001907555 SOL (1.9076%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · DOGE-1-SOL · 9pYrAB7CiYCHdmmZ77XYz3EK24AXQTaGHTobnNprjsHT

2026-09-16T08:26:22+07:00 → 2026-09-16T09:27:31+07:00 · 61.15 menit · pool `ErwEeF8y8uLR7LkJcL3xRUuN1d8SrMLZJB92Ydq8vfdw`.

1. **Market → volatilitas → depth:** Volatility feed 3.266; TVL $23646.49; fee/TVL entry 0.2219%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1738; harga snapshot 0.000000967376 SOL/token; range [-1791, -1738] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.149999975 SOL + 0.000000000 token; withdraw 0.148418213 SOL + 1671.527612549 token. Porsi token pada mark withdrawal 1.04%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.44% < 5.0% after 60.2m)
5. **Jalur yang teramati:** 116 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 3.14%.
6. **Fee → drift → divergence → hasil:** Fee +0.000029342 SOL (0.0196% modal), divergence principal vs HOLD SOL -0.000027923 SOL, PnL LP +0.000001419 SOL (0.0009%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · BUTTHOLE-SOL · 6W9E3TEusrmuocYaG2MBibWc9pcDZq3ywPaPcHQKdBiq

2026-09-16T09:23:38+07:00 → 2026-09-16T09:45:01+07:00 · 21.38 menit · pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatilitas → depth:** Volatility feed 1.572; TVL $74945.70; fee/TVL entry 0.1692%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1388; harga snapshot 0.000015731909 SOL/token; range [-1441, -1388] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999787 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.1m (limit 5m)
5. **Jalur yang teramati:** 33 sampel; in-range teramati 72.3%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000947 SOL (0.0009% modal), divergence principal vs HOLD SOL -0.000000188 SOL, PnL LP +0.000000759 SOL (0.0008%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · ELON-SOL · GKPgoxLw6ShrAnziRygq4P8CzwXoiA7S7CZXdSGxzdNp

2026-09-16T09:36:25+07:00 → 2026-09-16T10:06:20+07:00 · 29.92 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 7.746; TVL $69735.50; fee/TVL entry 4.1068%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -441; harga snapshot 0.000029778673 SOL/token; range [-494, -441] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.097028416 SOL + 104.100412000 token. Porsi token pada mark withdrawal 2.91%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -7.6% <= -3.0% with PnL +1.58%, peak +1.70%) — realizing before floor gap-through
5. **Jalur yang teramati:** 47 sampel; in-range teramati 79.3%; maksimum penurunan teramati sejak snapshot 18.06%.
6. **Fee → drift → divergence → hasil:** Fee +0.001953171 SOL (1.9532% modal), divergence principal vs HOLD SOL -0.000063029 SOL, PnL LP +0.001890142 SOL (1.8901%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · Noiz-SOL · 8XvtuxAM5wk4P24DAi4ReFQ7BFZQcJdRhbJy8cLoCqNh

2026-09-16T09:59:37+07:00 → 2026-09-16T10:08:38+07:00 · 9.02 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 1.483; TVL $11795.69; fee/TVL entry 0.4566%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -564; harga snapshot 0.000003653803 SOL/token; range [-608, -564] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099998761 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.1m (limit 5m)
5. **Jalur yang teramati:** 10 sampel; in-range teramati 41.8%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000919 SOL (0.0009% modal), divergence principal vs HOLD SOL -0.000001218 SOL, PnL LP -0.000000299 SOL (-0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000299; setelah gas terhubung -0.000020299.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · biketyson-SOL · DLUfGTNqRrxsEEMeA1dVeYWNXBeDa2VFRqgSEVb2mjpQ

2026-09-16T10:59:16+07:00 → 2026-09-16T11:28:59+07:00 · 29.72 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 3.044; TVL $96044.00; fee/TVL entry 0.2141%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -349; harga snapshot 0.000031034200 SOL/token; range [-393, -349] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.139998598 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 20.4m (limit 5m); hold journal: biketyson OOR 3.4m; m5 +5.18%, h1 +11.15% (DLMM SOL pair 9F5zc) - sharp 5m bounce off OOR low, expect price to re-enter range before 30m OOR close
5. **Jalur yang teramati:** 44 sampel; in-range teramati 29.4%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000016689 SOL (0.0119% modal), divergence principal vs HOLD SOL -0.000001381 SOL, PnL LP +0.000015308 SOL (0.0109%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · NASDUCK-SOL · 6eKgM6GQGzmosamGvtxoCjztsrDQBo5LXuA7tgBRwmMZ

2026-09-16T11:01:45+07:00 → 2026-09-16T12:02:43+07:00 · 60.97 menit · pool `3vnFSkGU2foSKWsbH5pEJ6HFstugb5YBELkRGgUdJAeA`.

1. **Market → volatilitas → depth:** Volatility feed 0.439; TVL $12489.63; fee/TVL entry 0.2068%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -539; harga snapshot 0.000004685755 SOL/token; range [-583, -539] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099710137 SOL + 61.695237000 token. Porsi token pada mark withdrawal 0.29%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 2.44% < 5.0% after 60.5m)
5. **Jalur yang teramati:** 90 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 4.85%.
6. **Fee → drift → divergence → hasil:** Fee +0.000104089 SOL (0.1041% modal), divergence principal vs HOLD SOL -0.000003616 SOL, PnL LP +0.000100473 SOL (0.1005%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · biketyson-SOL · 2dQKWJgrXi3yRaw8CwFyQQFYv9jzzoZX2T3eQYX4juLd

2026-09-16T11:29:30+07:00 → 2026-09-16T12:05:22+07:00 · 35.87 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 3.044; TVL $96044.00; fee/TVL entry 0.2141%; base fee pool 1.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -348; harga snapshot 0.000031344542 SOL/token; range [-368, -348] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999990 SOL + 0.000000000 token; withdraw 0.140007917 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.3m (limit 5m); recenter parent/root `DLUfGTNqRrxsEEMeA1dVeYWNXBeDa2VFRqgSEVb2mjpQ`
5. **Jalur yang teramati:** 53 sampel; in-range teramati 86.5%; maksimum penurunan teramati sejak snapshot 3.90%.
6. **Fee → drift → divergence → hasil:** Fee +0.000238117 SOL (0.1701% modal), divergence principal vs HOLD SOL 0.000007927 SOL, PnL LP +0.000246044 SOL (0.1757%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · ELON-SOL · mW5CHDVxbyH4MDNHjMkr6n742nL4uGPhBrFJqMoKkE4

2026-09-16T13:06:24+07:00 → 2026-09-16T13:36:54+07:00 · 30.50 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 4.956; TVL $62220.04; fee/TVL entry 1.4586%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -506; harga snapshot 0.000017740700 SOL/token; range [-559, -506] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999973 SOL + 0.000000000 token; withdraw 0.096268634 SOL + 2879.724934000 token. Porsi token pada mark withdrawal 29.64%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -9.6% <= -3.0% with PnL -1.82% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 58 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 18.71%.
6. **Fee → drift → divergence → hasil:** Fee +0.001427924 SOL (1.0199% modal), divergence principal vs HOLD SOL -0.003183629 SOL, PnL LP -0.001755706 SOL (-1.2541%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · baton-SOL · Brw4qbpJthDzZ9zcPvtHb8LHtsDfToQbxxRpe7odrdfS

2026-09-16T13:40:47+07:00 → 2026-09-16T13:48:45+07:00 · 7.97 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 0.461; TVL $142961.93; fee/TVL entry 0.1509%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -315; harga snapshot 0.000043527854 SOL/token; range [-359, -315] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.139997061 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m)
5. **Jalur yang teramati:** 15 sampel; in-range teramati 35.7%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000002570 SOL (0.0018% modal), divergence principal vs HOLD SOL -0.000002918 SOL, PnL LP -0.000000348 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000348; setelah gas terhubung -0.000020348.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · HUHCAT-SOL · 755TXX4ef2DkuQD2tgDefZQ4RxhjA68cK9ECJDHNgi7G

2026-09-16T16:15:56+07:00 → 2026-09-16T17:05:28+07:00 · 49.53 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 2.205; TVL $80480.92; fee/TVL entry 0.3161%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -474; harga snapshot 0.000008946823 SOL/token; range [-518, -474] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.077103033 SOL + 8543.074950000 token. Porsi token pada mark withdrawal 42.62%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -8.4% <= -3.0% with PnL -2.20% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 90 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 24.32%.
6. **Fee → drift → divergence → hasil:** Fee +0.003400483 SOL (2.4289% modal), divergence principal vs HOLD SOL -0.005622196 SOL, PnL LP -0.002221712 SOL (-1.5869%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · biketyson-SOL · 6f9UdXkgJ362nCsim7x9KhjaUm5PBbeeW9sFcxKKNfVM

2026-09-16T16:49:17+07:00 → 2026-09-16T18:21:24+07:00 · 92.12 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 2.858; TVL $125051.65; fee/TVL entry 0.2432%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -341; harga snapshot 0.000033605591 SOL/token; range [-385, -341] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999173 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.42% < 5.0% after 91.7m)
5. **Jalur yang teramati:** 56 sampel; in-range teramati 78.6%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000026602 SOL (0.0266% modal), divergence principal vs HOLD SOL -0.000000806 SOL, PnL LP +0.000025796 SOL (0.0258%). Gas transaksi posisi yang terhubung 0.000025000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · GIN-CHAN-SOL · 43sbfQ8oz2NbAh7jGX74qpmLgwtipjjLtpomBijTPp4V

2026-09-16T18:20:01+07:00 → 2026-09-16T18:26:20+07:00 · 6.32 menit · pool `FWYZSdGT6fZREpeH2f7TcS4GChqUsUv4onXr88c72oYP`.

1. **Market → volatilitas → depth:** Volatility feed 9.064; TVL $12066.15; fee/TVL entry 0.4826%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -443; harga snapshot 0.000004073811 SOL/token; range [-478, -443] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.082883690 SOL + 4707.259865000 token. Porsi token pada mark withdrawal 16.28%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-21.3% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 8 sampel; in-range teramati 85.8%; maksimum penurunan teramati sejak snapshot 13.85%.
6. **Fee → drift → divergence → hasil:** Fee +0.000856359 SOL (0.8564% modal), divergence principal vs HOLD SOL -0.001000985 SOL, PnL LP -0.000144626 SOL (-0.1446%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.002416375; setelah gas terhubung -0.002449789. Swap cocok unik, jeda 513 detik; selisih terhadap mark token -0.002271749 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · TOAD-SOL · 2898jWFCmKcpdFD9H9XBiHih3bnc7D1nMqpoXpLsa3Th

2026-09-16T19:04:52+07:00 → 2026-09-16T19:36:42+07:00 · 31.83 menit · pool `AFT9ZhYVHMRQrnntMYnqVrKvVrAxpaspCEMBXQNVMwLo`.

1. **Market → volatilitas → depth:** Volatility feed 1.635; TVL $110886.17; fee/TVL entry 0.0479%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -391; harga snapshot 0.000020433504 SOL/token; range [-435, -391] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.139864712 SOL + 6.619922000 token. Porsi token pada mark withdrawal 0.10%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.07% < 5.0% after 30.6m)
5. **Jalur yang teramati:** 56 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000002110 SOL (0.0015% modal), divergence principal vs HOLD SOL -0.000001338 SOL, PnL LP +0.000000772 SOL (0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · lockinu-SOL · 5okcXbK9Wn3vi6JRqE9VSBNATbcGJ4Dyr4ZrLCHxjEGF

2026-09-16T19:31:55+07:00 → 2026-09-16T19:34:35+07:00 · 2.67 menit · pool `9PxMQ7Ny9NMurjKwSQMeNrE9yvdML6HVCXo8EzedLvJw`.

1. **Market → volatilitas → depth:** Volatility feed 12.994; TVL $38129.40; fee/TVL entry 2.3093%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -515; harga snapshot 0.000005949665 SOL/token; range [-559, -515] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.080993376 SOL + 3612.237754000 token. Porsi token pada mark withdrawal 18.01%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-29.7% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 3 sampel; in-range teramati 50.0%; maksimum penurunan teramati sejak snapshot 18.05%.
6. **Fee → drift → divergence → hasil:** Fee +0.004704716 SOL (4.7047% modal), divergence principal vs HOLD SOL -0.001217145 SOL, PnL LP +0.003487571 SOL (3.4876%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.002297582; setelah gas terhubung +0.002272582. Swap cocok unik, jeda 32 detik; selisih terhadap mark token -0.001189989 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · DOGE-1-SOL · DU8P1nRuwwwBPvprjkVYk5FdHu18ohdEFDFP6fWvxtJ4

2026-09-16T20:29:20+07:00 → 2026-09-16T21:00:05+07:00 · 30.75 menit · pool `ErwEeF8y8uLR7LkJcL3xRUuN1d8SrMLZJB92Ydq8vfdw`.

1. **Market → volatilitas → depth:** Volatility feed 2.005; TVL $19599.52; fee/TVL entry 0.0748%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1740; harga snapshot 0.000000952082 SOL/token; range [-1793, -1740] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999973 SOL + 0.000000000 token; withdraw 0.139348664 SOL + 690.345425830 token. Porsi token pada mark withdrawal 0.46%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.35% < 5.0% after 30.1m)
5. **Jalur yang teramati:** 60 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 2.36%.
6. **Fee → drift → divergence → hasil:** Fee +0.000010382 SOL (0.0074% modal), divergence principal vs HOLD SOL -0.000009569 SOL, PnL LP +0.000000813 SOL (0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · BUTTHOLE-SOL · GpU2kLn7WdbtGCC7GNYQdZi1HF6Kt98UcMnKDwMiKvkm

2026-09-16T21:31:29+07:00 → 2026-09-16T22:02:40+07:00 · 31.18 menit · pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatilitas → depth:** Volatility feed 1.840; TVL $90252.07; fee/TVL entry 0.0588%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1356; harga snapshot 0.000020301048 SOL/token; range [-1409, -1356] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999973 SOL + 0.000000000 token; withdraw 0.138639674 SOL + 68.341804809 token. Porsi token pada mark withdrawal 0.96%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.55% < 5.0% after 30.4m)
5. **Jalur yang teramati:** 59 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 3.91%.
6. **Fee → drift → divergence → hasil:** Fee +0.000016219 SOL (0.0116% modal), divergence principal vs HOLD SOL -0.000016412 SOL, PnL LP -0.000000193 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · PURPS-SOL · 2KLDX5n1LHbEqTnLsWMk6Gwvv2JrddiukkDCZkrFuUZG

2026-09-16T22:10:50+07:00 → 2026-09-16T23:11:42+07:00 · 60.87 menit · pool `5LjukK9FDhTo51wp2zkKdAgSk7yg4khr1v9d3HwKFsQJ`.

1. **Market → volatilitas → depth:** Volatility feed 1.520; TVL $28672.17; fee/TVL entry 0.8209%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -468; harga snapshot 0.000009497232 SOL/token; range [-512, -468] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.139188376 SOL + 86.433372000 token. Porsi token pada mark withdrawal 0.57%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.60% < 5.0% after 60.3m)
5. **Jalur yang teramati:** 98 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 2.94%.
6. **Fee → drift → divergence → hasil:** Fee +0.000035170 SOL (0.0251% modal), divergence principal vs HOLD SOL -0.000014867 SOL, PnL LP +0.000020303 SOL (0.0145%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · biketyson-SOL · HcnMKoBUSgbqLe9QwNpsbDnw2WXBVmXifjZVHcif62C5

2026-09-16T22:23:15+07:00 → 2026-09-16T23:23:51+07:00 · 60.60 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 1.382; TVL $51537.97; fee/TVL entry 0.1791%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -370; harga snapshot 0.000025182086 SOL/token; range [-414, -370] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.096523411 SOL + 144.653964000 token. Porsi token pada mark withdrawal 3.37%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stale ticket re-pin (60m in range, peak +0.83% never armed the 1.2% ratchet, fee/TVL 16.7%)
5. **Jalur yang teramati:** 96 sampel; in-range teramati 95.7%; maksimum penurunan teramati sejak snapshot 14.72%.
6. **Fee → drift → divergence → hasil:** Fee +0.000730264 SOL (0.7303% modal), divergence principal vs HOLD SOL -0.000112606 SOL, PnL LP +0.000617658 SOL (0.6177%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Batas umur/peak sendiri belum membuktikan biaya reposisi layak; snapshot fee pace posisi diperlukan. 

## azimuth · lockinu-SOL · ESNa6SCaGzmZLZzN6j6ByQMMjhNjmToY5A2EHWkZ5goo

2026-09-16T23:28:55+07:00 → 2026-09-16T23:39:36+07:00 · 10.68 menit · pool `9PxMQ7Ny9NMurjKwSQMeNrE9yvdML6HVCXo8EzedLvJw`.

1. **Market → volatilitas → depth:** Volatility feed 7.448; TVL $23308.48; fee/TVL entry 3.4446%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -491; harga snapshot 0.000007554496 SOL/token; range [-535, -491] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.139996775 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m)
5. **Jalur yang teramati:** 19 sampel; in-range teramati 51.5%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.000222968 SOL (0.1593% modal), divergence principal vs HOLD SOL -0.000003204 SOL, PnL LP +0.000219764 SOL (0.1570%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · UBI-SOL · E2gH5JRGjaRGNd2ecAvUk6CePkfjQ1262vMvUr4FQEKW

2026-09-17T00:18:33+07:00 → 2026-09-17T01:43:33+07:00 · 85.00 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 0.574; TVL $25774.00; fee/TVL entry 0.1061%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1202; harga snapshot 0.000006393059 SOL/token; range [-1246, -1202] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099769117 SOL + 35.870711062 token. Porsi token pada mark withdrawal 0.23%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.42% < 5.0% after 84.7m)
5. **Jalur yang teramati:** 61 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000025211 SOL (0.0252% modal), divergence principal vs HOLD SOL -0.000003809 SOL, PnL LP +0.000021402 SOL (0.0214%). Gas transaksi posisi yang terhubung 0.000030000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · ELON-SOL · 519pnqNanLAJNTpKhPE9GTYeTxXGQ6RYgvUGBYD8ydXt

2026-09-17T01:42:39+07:00 → 2026-09-17T02:12:06+07:00 · 29.45 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 6.945; TVL $63807.82; fee/TVL entry 1.4546%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -490; harga snapshot 0.000020152980 SOL/token; range [-543, -490] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.091851515 SOL + 435.886513000 token. Porsi token pada mark withdrawal 7.82%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -3.9% <= -3.0% with PnL +0.82%, peak +1.28%) — realizing before floor gap-through
5. **Jalur yang teramati:** 55 sampel; in-range teramati 88.1%; maksimum penurunan teramati sejak snapshot 18.06%.
6. **Fee → drift → divergence → hasil:** Fee +0.001429844 SOL (1.4298% modal), divergence principal vs HOLD SOL -0.000353665 SOL, PnL LP +0.001076179 SOL (1.0762%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000888604; setelah gas terhubung +0.000763604. Swap cocok unik, jeda 397 detik; selisih terhadap mark token -0.000187575 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · ELON-SOL · 4RezzzZP77eaC2nxtCX95SeTyLjpwCW6moEfB7rcGbHx

2026-09-17T02:12:35+07:00 → 2026-09-17T02:29:52+07:00 · 17.28 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 6.945; TVL $63807.82; fee/TVL entry 1.4546%; base fee pool 1.0%; bin step 80 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -506; harga snapshot 0.000017740700 SOL/token; range [-526, -506] (21 bin), downside 14.73%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.076190471 SOL + 1407.556698000 token. Porsi token pada mark withdrawal 23.38%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -5.4% <= -3.0% with PnL -1.53% <= -1.5%) — cutting before the downtrend level; recenter parent/root `519pnqNanLAJNTpKhPE9GTYeTxXGQ6RYgvUGBYD8ydXt`
5. **Jalur yang teramati:** 32 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 6.18%.
6. **Fee → drift → divergence → hasil:** Fee +0.000408774 SOL (0.4088% modal), divergence principal vs HOLD SOL -0.000566536 SOL, PnL LP -0.000157762 SOL (-0.1578%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.005275359; setelah gas terhubung -0.005400359. Swap cocok unik, jeda 248 detik; selisih terhadap mark token -0.005117597 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · biketyson-SOL · Eriah3ujk472Dv6XZsEjUBgaDcLKrbH7vbBkWVBMz2ou

2026-09-17T03:45:15+07:00 → 2026-09-17T03:54:36+07:00 · 9.35 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 4.007; TVL $45229.29; fee/TVL entry 0.3031%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -347; harga snapshot 0.000031657987 SOL/token; range [-391, -347] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.139999143 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m)
5. **Jalur yang teramati:** 17 sampel; in-range teramati 41.4%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.000128375 SOL (0.0917% modal), divergence principal vs HOLD SOL -0.000000836 SOL, PnL LP +0.000127539 SOL (0.0911%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · biketyson-SOL · AJotFmui7kBAuQ3Gopp5MF1oRDzChE2TCoC3BY1uDCtz

2026-09-17T03:55:07+07:00 → 2026-09-17T04:03:30+07:00 · 8.38 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 4.007; TVL $45229.29; fee/TVL entry 0.3031%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -344; harga snapshot 0.000032617256 SOL/token; range [-364, -344] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999990 SOL + 0.000000000 token; withdraw 0.140000512 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m); recenter parent/root `Eriah3ujk472Dv6XZsEjUBgaDcLKrbH7vbBkWVBMz2ou`
5. **Jalur yang teramati:** 15 sampel; in-range teramati 34.8%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000452 SOL (0.0003% modal), divergence principal vs HOLD SOL 0.000000522 SOL, PnL LP +0.000000974 SOL (0.0007%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000000974; setelah gas terhubung -0.000019026.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · DONO-SOL · AVuyZSD6ouNuWKuQP6AUd2MG3wqp9T7DZjcEtpqJQFY8

2026-09-17T04:18:31+07:00 → 2026-09-17T04:25:24+07:00 · 6.88 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 12.713; TVL $55778.30; fee/TVL entry 24.4240%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -481; harga snapshot 0.000008344863 SOL/token; range [-525, -481] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999977 SOL + 0.000000000 token; withdraw 0.139995867 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.1m (limit 5m)
5. **Jalur yang teramati:** 12 sampel; in-range teramati 17.3%; maksimum penurunan teramati sejak snapshot 3.90%.
6. **Fee → drift → divergence → hasil:** Fee +0.000238870 SOL (0.1706% modal), divergence principal vs HOLD SOL -0.000004110 SOL, PnL LP +0.000234760 SOL (0.1677%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · DONO-SOL · 8pfKqHbL7T69Rqm3cSyuoTjHqknm4VfpqDgzXAkq3KTP

2026-09-17T04:25:55+07:00 → 2026-09-17T04:28:18+07:00 · 2.38 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 12.713; TVL $55778.30; fee/TVL entry 24.4240%; base fee pool 3.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -453; harga snapshot 0.000011025992 SOL/token; range [-473, -453] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999990 SOL + 0.000000000 token; withdraw 0.017932412 SOL + 12538.252433000 token. Porsi token pada mark withdrawal 86.45%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Downtrend dump, unconfirmed (PnL -7.36% <= -2.5%, no 1h confirmation) — risk floor; recenter parent/root `AVuyZSD6ouNuWKuQP6AUd2MG3wqp9T7DZjcEtpqJQFY8`
5. **Jalur yang teramati:** 3 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 6.73%.
6. **Fee → drift → divergence → hasil:** Fee +0.008914037 SOL (6.3672% modal), divergence principal vs HOLD SOL -0.007635289 SOL, PnL LP +0.001278748 SOL (0.9134%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · UBI-SOL · 9jrYwkB4mi2iS2iDWrVm3QK386deyjVQzqV9neQUohkY

2026-09-17T05:51:02+07:00 → 2026-09-17T06:50:18+07:00 · 59.27 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 7.468; TVL $18848.76; fee/TVL entry 0.6406%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1175; harga snapshot 0.000008363457 SOL/token; range [-1219, -1175] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.139271528 SOL + 88.191942640 token. Porsi token pada mark withdrawal 0.52%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -5.3% <= -3.0% with PnL +1.26%, peak +1.39%) — realizing before floor gap-through
5. **Jalur yang teramati:** 107 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.000254730 SOL (0.1820% modal), divergence principal vs HOLD SOL -0.000005395 SOL, PnL LP +0.000249335 SOL (0.1781%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · biketyson-SOL · JDFBgJQWxQD4YYuX5Qa84nwpZNp9degtiwYNJP1JuMrd

2026-09-17T06:10:05+07:00 → 2026-09-17T06:17:54+07:00 · 7.82 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 1.902; TVL $88085.34; fee/TVL entry 0.1602%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -361; harga snapshot 0.000027541276 SOL/token; range [-405, -361] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999043 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.4m (limit 5m)
5. **Jalur yang teramati:** 10 sampel; in-range teramati 20.5%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000834 SOL (0.0008% modal), divergence principal vs HOLD SOL -0.000000936 SOL, PnL LP -0.000000102 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000102; setelah gas terhubung -0.000020102.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · baton-SOL · 4bAFe1e8Y6s9q6bnSKn33uhU3Ty1qSd6KbzyehSNDbG5

2026-09-17T06:40:44+07:00 → 2026-09-17T07:05:54+07:00 · 25.17 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 2.484; TVL $70578.61; fee/TVL entry 0.1667%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -327; harga snapshot 0.000038628761 SOL/token; range [-371, -327] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099997849 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m)
5. **Jalur yang teramati:** 41 sampel; in-range teramati 81.4%; maksimum penurunan teramati sejak snapshot 2.94%.
6. **Fee → drift → divergence → hasil:** Fee +0.000040795 SOL (0.0408% modal), divergence principal vs HOLD SOL -0.000002130 SOL, PnL LP +0.000038665 SOL (0.0387%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000038665; setelah gas terhubung +0.000018665.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · baton-SOL · 3utWaf9siDkDRKfZn8xr32jzTFgajS1DxZrUndB4B3eY

2026-09-17T07:06:24+07:00 → 2026-09-17T07:13:13+07:00 · 6.82 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 2.484; TVL $70578.61; fee/TVL entry 0.1667%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -323; harga snapshot 0.000040197243 SOL/token; range [-343, -323] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099999850 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m); recenter parent/root `4bAFe1e8Y6s9q6bnSKn33uhU3Ty1qSd6KbzyehSNDbG5`
5. **Jalur yang teramati:** 12 sampel; in-range teramati 17.4%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000125 SOL (0.0001% modal), divergence principal vs HOLD SOL -0.000000140 SOL, PnL LP -0.000000015 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000015; setelah gas terhubung -0.000020015.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · Noiz-SOL · 75UxxXVzpGPQq1LccGiTDwsTR3UG5pjK5fyLewpRi2B1

2026-09-17T07:18:05+07:00 → 2026-09-17T07:27:13+07:00 · 9.13 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 1.520; TVL $10105.00; fee/TVL entry 0.2829%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -556; harga snapshot tidak tersedia SOL/token; range [-600, -556] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999979 SOL + 0.000000000 token; withdraw 0.139997600 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 16 sampel; in-range teramati 36.0%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000004669 SOL (0.0033% modal), divergence principal vs HOLD SOL -0.000002379 SOL, PnL LP +0.000002290 SOL (0.0016%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · Noiz-SOL · BKSfWJhBhYSkgyMVZoSEmLUHB2izsMTt6xQAiDBpMcyZ

2026-09-17T07:27:42+07:00 → 2026-09-17T08:00:54+07:00 · 33.20 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 1.520; TVL $10105.00; fee/TVL entry 0.2829%; base fee pool 3.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -553; harga snapshot 0.000004076433 SOL/token; range [-573, -553] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.139999990 SOL + 0.000000000 token; withdraw 0.068112004 SOL + 19348.959723000 token. Porsi token pada mark withdrawal 50.19%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -8.1% <= -3.0% with PnL -2.12% <= -1.5%) — cutting before the downtrend level; recenter parent/root `75UxxXVzpGPQq1LccGiTDwsTR3UG5pjK5fyLewpRi2B1`
5. **Jalur yang teramati:** 50 sampel; in-range teramati 83.2%; maksimum penurunan teramati sejak snapshot 11.26%.
6. **Fee → drift → divergence → hasil:** Fee +0.002198526 SOL (1.5704% modal), divergence principal vs HOLD SOL -0.003269886 SOL, PnL LP -0.001071360 SOL (-0.7653%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · ZEREBLAST-SOL · FtZqfCwHxysvrJ8Qr9edEuyghZ1EuoFKAYonAS23qfDu

2026-09-17T07:40:26+07:00 → 2026-09-17T07:47:14+07:00 · 6.80 menit · pool `9EJVbU6r2eshpNLxvVEhL9Kzra5ob5TJSzaDb1Hy222q`.

1. **Market → volatilitas → depth:** Volatility feed 14.046; TVL $15272.69; fee/TVL entry 14.6563%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -553; harga snapshot 0.000004076433 SOL/token; range [-597, -553] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.097294668 SOL + 690.065320000 token. Porsi token pada mark withdrawal 2.65%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m)
5. **Jalur yang teramati:** 9 sampel; in-range teramati 12.3%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000128035 SOL (0.1280% modal), divergence principal vs HOLD SOL -0.000055333 SOL, PnL LP +0.000072702 SOL (0.0727%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · ZEREBLAST-SOL · 9SApW4enBgVjuxEiY9rHbKboKBcyZJGTWp72MKunESiL

2026-09-17T07:47:45+07:00 → 2026-09-17T07:59:16+07:00 · 11.52 menit · pool `9EJVbU6r2eshpNLxvVEhL9Kzra5ob5TJSzaDb1Hy222q`.

1. **Market → volatilitas → depth:** Volatility feed 14.046; TVL $15272.69; fee/TVL entry 14.6563%; base fee pool 1.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -540; harga snapshot 0.000004639361 SOL/token; range [-560, -540] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 24722.817633000 token. Porsi token pada mark withdrawal 100.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -19.2% <= -3.0% with PnL -1.79% <= -1.5%) — cutting before the downtrend level; recenter parent/root `FtZqfCwHxysvrJ8Qr9edEuyghZ1EuoFKAYonAS23qfDu`
5. **Jalur yang teramati:** 16 sampel; in-range teramati 53.0%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.002947111 SOL (2.9471% modal), divergence principal vs HOLD SOL -0.012324333 SOL, PnL LP -0.009377222 SOL (-9.3772%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · CTO-SOL · H8md4qq3qseoMyPBcj1U4A7WCNK9FJEDvzunjV6uxRfJ

2026-09-17T08:32:06+07:00 → 2026-09-17T08:48:23+07:00 · 16.28 menit · pool `54sbyULrreD9HBoV5wRWedeCBEw6gQ7VkdHW18rLX78e`.

1. **Market → volatilitas → depth:** Volatility feed 8.380; TVL $12104.65; fee/TVL entry 1.1066%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1292; harga snapshot 0.000002610869 SOL/token; range [-1336, -1292] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.129998340 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m)
5. **Jalur yang teramati:** 27 sampel; in-range teramati 37.6%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000010552 SOL (0.0081% modal), divergence principal vs HOLD SOL -0.000001637 SOL, PnL LP +0.000008915 SOL (0.0069%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · biketyson-SOL · 3n2KN1ZnwCAbaqneARfAZwBX7CTd2LXUCvuLazSiR7im

2026-09-17T08:39:49+07:00 → 2026-09-17T11:03:28+07:00 · 143.65 menit · pool `ARqHS4dXM989rYBjDKzx249yqBXQtdrUioemyoGEnAnk`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -357; harga snapshot tidak tersedia SOL/token; range [-401, -357] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.071014728 SOL + 1179.963982000 token. Porsi token pada mark withdrawal 27.27%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stale ticket re-pin (143m in range, peak +0.20% never armed the 1.2% ratchet, fee/TVL 15.3%)
5. **Jalur yang teramati:** 62 sampel; in-range teramati 90.4%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.001508417 SOL (1.5084% modal), divergence principal vs HOLD SOL -0.002351929 SOL, PnL LP -0.000843512 SOL (-0.8435%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Batas umur/peak sendiri belum membuktikan biaya reposisi layak; snapshot fee pace posisi diperlukan. 

## azimuth · CTO-SOL · H3Y5AF3VtwPP7i2mx74xxygBWXCrsetyZC1RmEtVjYX1

2026-09-17T08:48:54+07:00 → 2026-09-17T09:08:27+07:00 · 19.55 menit · pool `54sbyULrreD9HBoV5wRWedeCBEw6gQ7VkdHW18rLX78e`.

1. **Market → volatilitas → depth:** Volatility feed 8.380; TVL $12104.65; fee/TVL entry 1.1066%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1290; harga snapshot 0.000002663347 SOL/token; range [-1310, -1290] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999990 SOL + 0.000000000 token; withdraw 0.129996848 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m); recenter parent/root `H8md4qq3qseoMyPBcj1U4A7WCNK9FJEDvzunjV6uxRfJ`
5. **Jalur yang teramati:** 28 sampel; in-range teramati 75.2%; maksimum penurunan teramati sejak snapshot 2.94%.
6. **Fee → drift → divergence → hasil:** Fee +0.000554479 SOL (0.4265% modal), divergence principal vs HOLD SOL -0.000003142 SOL, PnL LP +0.000551337 SOL (0.4241%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · OTC-SOL · DcaDSpWHa7wzNoJUfZQsWxCrRkRJFYde96oi3NZQVDFK

2026-09-17T11:03:34+07:00 → 2026-09-17T11:20:22+07:00 · 16.80 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 4.283; TVL $22727.91; fee/TVL entry 0.3730%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -314; harga snapshot 0.000043963133 SOL/token; range [-358, -314] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999913 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.6m (limit 5m)
5. **Jalur yang teramati:** 29 sampel; in-range teramati 66.6%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000003706 SOL (0.0037% modal), divergence principal vs HOLD SOL -0.000000066 SOL, PnL LP +0.000003640 SOL (0.0036%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · CTO-SOL · 9HfPk39gQaWkPwGgFSZujTXcyhX4kJw5EAQoZeq5gxZR

2026-09-17T11:18:26+07:00 → 2026-09-17T12:40:37+07:00 · 82.18 menit · pool `54sbyULrreD9HBoV5wRWedeCBEw6gQ7VkdHW18rLX78e`.

1. **Market → volatilitas → depth:** Volatility feed 4.950; TVL $11685.07; fee/TVL entry 1.1071%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1282; harga snapshot 0.000002884024 SOL/token; range [-1326, -1282] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.096731267 SOL + 1184.987086110 token. Porsi token pada mark withdrawal 3.19%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 4.98% < 5.0% after 79.9m)
5. **Jalur yang teramati:** 112 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 6.73%.
6. **Fee → drift → divergence → hasil:** Fee +0.000328051 SOL (0.3281% modal), divergence principal vs HOLD SOL -0.000081119 SOL, PnL LP +0.000246932 SOL (0.2469%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · OTC-SOL · Dz5aWA6HrttJF2V2aCL4eU6F9V5EauS5uMzP7CdKWjCA

2026-09-17T11:20:52+07:00 → 2026-09-17T12:38:53+07:00 · 78.02 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 4.283; TVL $22727.91; fee/TVL entry 0.3730%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -304; harga snapshot 0.000048562649 SOL/token; range [-324, -304] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099900411 SOL + 1.904471000 token. Porsi token pada mark withdrawal 0.09%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -4.8% <= -3.0% with PnL +1.27%, peak +1.43%) — realizing before floor gap-through; recenter parent/root `DcaDSpWHa7wzNoJUfZQsWxCrRkRJFYde96oi3NZQVDFK`
5. **Jalur yang teramati:** 110 sampel; in-range teramati 74.2%; maksimum penurunan teramati sejak snapshot 9.47%.
6. **Fee → drift → divergence → hasil:** Fee +0.001228767 SOL (1.2288% modal), divergence principal vs HOLD SOL -0.000007093 SOL, PnL LP +0.001221674 SOL (1.2217%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · OTC-SOL · BV1hUo42bZTVFoJViRbgnMcFX9CJdtUVTUJjYFzxQkys

2026-09-17T12:39:41+07:00 → 2026-09-17T13:39:12+07:00 · 59.52 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -304; harga snapshot 0.000048562649 SOL/token; range [-324, -304] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099999596 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.1m (limit 5m); recenter parent/root `DcaDSpWHa7wzNoJUfZQsWxCrRkRJFYde96oi3NZQVDFK`
5. **Jalur yang teramati:** 77 sampel; in-range teramati 91.6%; maksimum penurunan teramati sejak snapshot 2.94%.
6. **Fee → drift → divergence → hasil:** Fee +0.000238633 SOL (0.2386% modal), divergence principal vs HOLD SOL -0.000000394 SOL, PnL LP +0.000238239 SOL (0.2382%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · KEVIN-SOL · 8Acq8VsGP42zj3VBr1GP4eU5RQZvWLtFahW2Jd5cgKKV

2026-09-17T13:00:04+07:00 → 2026-09-17T13:15:48+07:00 · 15.73 menit · pool `4bDCwoR6TZdiUAQd6vjEYYFkV6mqykdgQ6WaT6JUy8Th`.

1. **Market → volatilitas → depth:** Volatility feed 3.616; TVL $10064.55; fee/TVL entry 0.8577%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -560; harga snapshot 0.000003802163 SOL/token; range [-604, -560] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.085192671 SOL + 4334.270289000 token. Porsi token pada mark withdrawal 14.04%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing Take-Profit hit (Peak: 3.73%, Current: 0.79% <= ratchet floor 3.13%)
5. **Jalur yang teramati:** 16 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 20.46%.
6. **Fee → drift → divergence → hasil:** Fee +0.001652862 SOL (1.6529% modal), divergence principal vs HOLD SOL -0.000892305 SOL, PnL LP +0.000760558 SOL (0.7606%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000523132; setelah gas terhubung +0.000470910. Swap cocok unik, jeda 92 detik; selisih terhadap mark token -0.000237426 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · OTC-SOL · 5FUJshoYvVwvTquiAahjtQaUfjviGcm5PMFFcQiJSTCs

2026-09-17T13:39:56+07:00 → 2026-09-17T15:42:44+07:00 · 122.80 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -299; harga snapshot 0.000051039832 SOL/token; range [-319, -299] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099999441 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 4.96% < 5.0% after 122.2m); recenter parent/root `DcaDSpWHa7wzNoJUfZQsWxCrRkRJFYde96oi3NZQVDFK`
5. **Jalur yang teramati:** 83 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000415446 SOL (0.4154% modal), divergence principal vs HOLD SOL -0.000000549 SOL, PnL LP +0.000414897 SOL (0.4149%). Gas transaksi posisi yang terhubung 0.000030000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · HUHCAT-SOL · 8YZwLuVFxcR6GqVnTxEUMNiEumXsSLr54AKs9vcwmnom

2026-09-17T14:25:09+07:00 → 2026-09-17T14:38:36+07:00 · 13.45 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 3.235; TVL $17032.24; fee/TVL entry 0.1901%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -493; harga snapshot 0.000007405642 SOL/token; range [-537, -493] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999270 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.1m (limit 5m)
5. **Jalur yang teramati:** 12 sampel; in-range teramati 59.9%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000003284 SOL (0.0033% modal), divergence principal vs HOLD SOL -0.000000709 SOL, PnL LP +0.000002575 SOL (0.0026%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · lockinu-SOL · 9DEaxqd1ZkgBaNmUqKGFGiDkwj1FBuQpeXKYx6qiVt8A

2026-09-17T15:41:37+07:00 → 2026-09-17T16:24:14+07:00 · 42.62 menit · pool `9PxMQ7Ny9NMurjKwSQMeNrE9yvdML6HVCXo8EzedLvJw`.

1. **Market → volatilitas → depth:** Volatility feed 2.884; TVL $12218.78; fee/TVL entry 0.7266%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -549; harga snapshot 0.000004241952 SOL/token; range [-593, -549] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.095134078 SOL + 1215.153699000 token. Porsi token pada mark withdrawal 4.72%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -3.8% <= -3.0% with PnL +1.21%, peak +1.34%) — realizing before floor gap-through; hold journal: lockinu DLMM SOL pair m5 +14.99% h1 +1.68% (pumpswap token m5 +14.41% h1 -0.73%); in-range pnl +1.21% at trailing peak, ratchet floor 0.61% - 5m bounce well above +1.0% bar, expect peak to ratchet higher and give the trailing floor room rather than selling into the spike
5. **Jalur yang teramati:** 50 sampel; in-range teramati 93.8%; maksimum penurunan teramati sejak snapshot 18.05%.
6. **Fee → drift → divergence → hasil:** Fee +0.000836115 SOL (0.8361% modal), divergence principal vs HOLD SOL -0.000152823 SOL, PnL LP +0.000683292 SOL (0.6833%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · WANG-SOL · 3CxWKny9iBuuo5dXgmaaa7SjTQc3pQ2Q5pjyY3USGEg3

2026-09-17T15:54:01+07:00 → 2026-09-17T15:58:44+07:00 · 4.72 menit · pool `8ACe6Q57ULDvEbdo4QjhtE5BzuqCXuqNJZdnzw7jT9tu`.

1. **Market → volatilitas → depth:** Volatility feed 4.806; TVL $42159.50; fee/TVL entry 3.2750%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -543; harga snapshot 0.000004502918 SOL/token; range [-587, -543] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.096420538 SOL + 833.070952000 token. Porsi token pada mark withdrawal 3.47%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-27.3% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 4 sampel; in-range teramati 32.7%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000155617 SOL (0.1556% modal), divergence principal vs HOLD SOL -0.000115224 SOL, PnL LP +0.000040393 SOL (0.0404%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · UBI-SOL · 6FGVsZhtPRqV5g4xHPc7nmQ8VTN1JMdsZhNBaZDfudNG

2026-09-17T16:02:50+07:00 → 2026-09-17T17:04:05+07:00 · 61.25 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 1.541; TVL $21022.04; fee/TVL entry 0.2459%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1189; harga snapshot 0.000007275898 SOL/token; range [-1233, -1189] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099483759 SOL + 71.808208173 token. Porsi token pada mark withdrawal 0.51%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.57% < 5.0% after 60.2m)
5. **Jalur yang teramati:** 62 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000024578 SOL (0.0246% modal), divergence principal vs HOLD SOL -0.000004046 SOL, PnL LP +0.000020533 SOL (0.0205%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · lockinu-SOL · hhhBkRgcmYTMNp2WteqQxYijSKEPNGCvCRBjKebewUq

2026-09-17T16:24:59+07:00 → 2026-09-17T17:00:36+07:00 · 35.62 menit · pool `9PxMQ7Ny9NMurjKwSQMeNrE9yvdML6HVCXo8EzedLvJw`.

1. **Market → volatilitas → depth:** Volatility feed 2.884; TVL $12218.78; fee/TVL entry 0.7266%; base fee pool 1.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -559; harga snapshot 0.000003840184 SOL/token; range [-579, -559] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.041061007 SOL + 16966.828306000 token. Porsi token pada mark withdrawal 57.51%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -5.2% <= -3.0% with PnL -2.20% <= -1.5%) — cutting before the downtrend level; recenter parent/root `9DEaxqd1ZkgBaNmUqKGFGiDkwj1FBuQpeXKYx6qiVt8A`
5. **Jalur yang teramati:** 36 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 13.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.002053633 SOL (2.0536% modal), divergence principal vs HOLD SOL -0.003372778 SOL, PnL LP -0.001319144 SOL (-1.3191%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.003525207; setelah gas terhubung -0.003576497. Swap cocok unik, jeda 46 detik; selisih terhadap mark token -0.002206063 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · DONO-SOL · 73ErxTpYywpzqKmnUH3gNivx1besjjSXoKYNZCSNQsBM

2026-09-17T17:22:20+07:00 → 2026-09-17T17:45:06+07:00 · 22.77 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 5.201; TVL $10045.60; fee/TVL entry 1.0052%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -559; harga snapshot 0.000003840184 SOL/token; range [-603, -559] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.107815650 SOL + 3462.233561000 token. Porsi token pada mark withdrawal 9.69%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -7.5% <= -3.0% with PnL +1.87%, peak +1.87%) — realizing before floor gap-through
5. **Jalur yang teramati:** 34 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 19.66%.
6. **Fee → drift → divergence → hasil:** Fee +0.002667928 SOL (2.2233% modal), divergence principal vs HOLD SOL -0.000617639 SOL, PnL LP +0.002050289 SOL (1.7086%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001283971; setelah gas terhubung +0.001158971. Swap cocok unik, jeda 93 detik; selisih terhadap mark token -0.000766318 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · DONO-SOL · HmnfRQ2Y9561yvGauauaaYeR9qJfhrk4fvyreXPyahmt

2026-09-17T17:46:21+07:00 → 2026-09-17T17:47:42+07:00 · 1.35 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 5.201; TVL $10045.60; fee/TVL entry 1.0052%; base fee pool 3.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -576; harga snapshot 0.000003242565 SOL/token; range [-596, -576] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999990 SOL + 0.000000000 token; withdraw 0.119270364 SOL + 217.852839000 token. Porsi token pada mark withdrawal 0.58%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-20.2% in 5m <= -20%) — emergency exit before it goes to zero; recenter parent/root `73ErxTpYywpzqKmnUH3gNivx1besjjSXoKYNZCSNQsBM`
5. **Jalur yang teramati:** 0 sampel; in-range teramati tidak tersedia%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000009474 SOL (0.0079% modal), divergence principal vs HOLD SOL -0.000030218 SOL, PnL LP -0.000020744 SOL (-0.0173%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · WANG-SOL · 7huiqNmtutXgp23eADipHYpCPfmzg3otwt2rHAyMNxZr

2026-09-17T19:14:16+07:00 → 2026-09-17T19:29:04+07:00 · 14.80 menit · pool `8ACe6Q57ULDvEbdo4QjhtE5BzuqCXuqNJZdnzw7jT9tu`.

1. **Market → volatilitas → depth:** Volatility feed 6.486; TVL $11643.52; fee/TVL entry 1.4101%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -562; harga snapshot 0.000003727245 SOL/token; range [-606, -562] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.120000284 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 21 sampel; in-range teramati 43.4%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.000292728 SOL (0.2439% modal), divergence principal vs HOLD SOL 0.000000303 SOL, PnL LP +0.000293031 SOL (0.2442%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · PERPSPAD-SOL · CbrHo7hewrinJBMkg1bHQDnwzFCHVjLCDoQNyeXcWntB

2026-09-17T20:01:24+07:00 → 2026-09-17T20:33:47+07:00 · 32.38 menit · pool `EHqk4Fw3pTCf9UW75dWoCMf6a2GxyJ8FGYEj2Qmw9rfr`.

1. **Market → volatilitas → depth:** Volatility feed 2.935; TVL $118759.78; fee/TVL entry 0.0515%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -350; harga snapshot 0.000061491312 SOL/token; range [-403, -350] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999974 SOL + 0.000000000 token; withdraw 0.117742307 SOL + 37.902624000 token. Porsi token pada mark withdrawal 1.85%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.87% < 5.0% after 30.9m)
5. **Jalur yang teramati:** 41 sampel; in-range teramati 97.9%; maksimum penurunan teramati sejak snapshot 4.67%.
6. **Fee → drift → divergence → hasil:** Fee +0.000022777 SOL (0.0190% modal), divergence principal vs HOLD SOL -0.000035791 SOL, PnL LP -0.000013014 SOL (-0.0108%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · baton-SOL · 8gGf3Nk2x4cf8RZu1pmpUwNFzjGA6bjY4qtmHsqYpA2W

2026-09-17T20:09:00+07:00 → 2026-09-17T20:16:14+07:00 · 7.23 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 1.489; TVL $61869.44; fee/TVL entry 0.1567%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -338; harga snapshot 0.000034623874 SOL/token; range [-382, -338] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999978 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.6m (limit 5m)
5. **Jalur yang teramati:** 7 sampel; in-range teramati 15.5%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000001 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000001 SOL, PnL LP +0.000000000 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000020000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · KET-SOL · AnjjNrjgyHohi5XhcNtFuk3cgEHgmASgmS5MPJ93Xbg7

2026-09-17T20:28:35+07:00 → 2026-09-17T21:30:11+07:00 · 61.60 menit · pool `2TD1fMPg2w7Hjt8bASSdxi92YFNQFgvdznqVApe3NGpn`.

1. **Market → volatilitas → depth:** Volatility feed 4.222; TVL $56187.68; fee/TVL entry 0.1712%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -354; harga snapshot 0.000029527976 SOL/token; range [-398, -354] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099439833 SOL + 19.194275000 token. Porsi token pada mark withdrawal 0.56%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.11% < 5.0% after 60.5m)
5. **Jalur yang teramati:** 71 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000004790 SOL (0.0048% modal), divergence principal vs HOLD SOL -0.000004545 SOL, PnL LP +0.000000244 SOL (0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · WANG-SOL · k6URjzrpmh48P9arWez6hjGqVxqothoubM6SzWbSNgf

2026-09-17T20:49:18+07:00 → 2026-09-17T21:21:36+07:00 · 32.30 menit · pool `8ACe6Q57ULDvEbdo4QjhtE5BzuqCXuqNJZdnzw7jT9tu`.

1. **Market → volatilitas → depth:** Volatility feed 4.721; TVL $16376.79; fee/TVL entry 1.1412%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -584; harga snapshot 0.000002994454 SOL/token; range [-628, -584] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.094645313 SOL + 1899.048490000 token. Porsi token pada mark withdrawal 5.16%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -7.3% <= -3.0% with PnL +1.75%, peak +1.97%) — realizing before floor gap-through; hold journal: WANG-SOL trailing-floor close deferred: DLMM pair m5 +19.28% (pumpswap m5 +13.71%), h1 -0.76% (not a sustained bleed), pnl +1.76% vs ratchet floor 1.37%; strong 5m bounce off range low, expect price to hold above floor and re-run to new peak before trailing fires
5. **Jalur yang teramati:** 34 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 14.72%.
6. **Fee → drift → divergence → hasil:** Fee +0.001212910 SOL (1.2129% modal), divergence principal vs HOLD SOL -0.000206648 SOL, PnL LP +0.001006262 SOL (1.0063%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · WANG-SOL · HfEMaPkbdw53TYG9wS3haZPZeRpzzMpghnjBJWMcpKhv

2026-09-17T21:22:23+07:00 → 2026-09-17T21:24:20+07:00 · 1.95 menit · pool `8ACe6Q57ULDvEbdo4QjhtE5BzuqCXuqNJZdnzw7jT9tu`.

1. **Market → volatilitas → depth:** Volatility feed 4.721; TVL $16376.79; fee/TVL entry 1.1412%; base fee pool 3.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -594; harga snapshot 0.000002710841 SOL/token; range [-614, -594] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.076191043 SOL + 9325.699318000 token. Porsi token pada mark withdrawal 23.28%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-20.1% in 5m <= -20%) — emergency exit before it goes to zero; recenter parent/root `k6URjzrpmh48P9arWez6hjGqVxqothoubM6SzWbSNgf`
5. **Jalur yang teramati:** 0 sampel; in-range teramati tidak tersedia%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000996432 SOL (0.9964% modal), divergence principal vs HOLD SOL -0.000693994 SOL, PnL LP +0.000302438 SOL (0.3024%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · UBI-SOL · AajXiwP1WXLmg2eiGv8bawg2Zx3wRm6jNcmRm7WJpwrf

2026-09-17T21:46:31+07:00 → 2026-09-17T22:48:05+07:00 · 61.57 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 3.518; TVL $36151.18; fee/TVL entry 0.2109%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1226; harga snapshot 0.000005034957 SOL/token; range [-1270, -1226] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119493202 SOL + 101.235208315 token. Porsi token pada mark withdrawal 0.42%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 2.00% < 5.0% after 60.5m)
5. **Jalur yang teramati:** 94 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 3.90%.
6. **Fee → drift → divergence → hasil:** Fee +0.000103516 SOL (0.0863% modal), divergence principal vs HOLD SOL -0.000007108 SOL, PnL LP +0.000096408 SOL (0.0803%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · PURPS-SOL · GL1WorxZ3LCM73Ju1jP2u5qb1gyr7xd8LuaoNDB3xrUi

2026-09-17T22:48:34+07:00 → 2026-09-17T23:19:53+07:00 · 31.32 menit · pool `5LjukK9FDhTo51wp2zkKdAgSk7yg4khr1v9d3HwKFsQJ`.

1. **Market → volatilitas → depth:** Volatility feed 3.447; TVL $16707.07; fee/TVL entry 0.2224%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -472; harga snapshot 0.000009126654 SOL/token; range [-516, -472] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999923 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.00% < 5.0% after 30.4m)
5. **Jalur yang teramati:** 47 sampel; in-range teramati 23.2%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000047 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000056 SOL, PnL LP -0.000000009 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000009; setelah gas terhubung -0.000020009.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · LMAO!-SOL · 4okgpLcp8XV62GrMjrC7bnra9pC3DmsZUABirknYpcCj

2026-09-17T23:50:18+07:00 → 2026-09-18T00:24:30+07:00 · 34.20 menit · pool `8k61EzwUzjdCZqKqGWTW2ygjmAdWGV6VZNPpDNkmo9dd`.

1. **Market → volatilitas → depth:** Volatility feed 0.704; TVL $13844.07; fee/TVL entry 0.0564%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -378; harga snapshot 0.000023255234 SOL/token; range [-422, -378] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119642089 SOL + 15.449626000 token. Porsi token pada mark withdrawal 0.29%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.08% < 5.0% after 33.6m)
5. **Jalur yang teramati:** 35 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000002349 SOL (0.0020% modal), divergence principal vs HOLD SOL -0.000005687 SOL, PnL LP -0.000003338 SOL (-0.0028%). Gas transaksi posisi yang terhubung 0.000025000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · BUTTHOLE-SOL · 6TtHeuFaEgnGqu8GqyBnq76DsfDWkz5ojAs74mvsMcgb

2026-09-17T23:54:48+07:00 → 2026-09-18T00:57:11+07:00 · 62.38 menit · pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatilitas → depth:** Volatility feed 2.946; TVL $105883.04; fee/TVL entry 0.1529%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1342; harga snapshot 0.000022696867 SOL/token; range [-1395, -1342] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.092488602 SOL + 355.621525541 token. Porsi token pada mark withdrawal 7.24%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 4.80% < 5.0% after 60.3m)
5. **Jalur yang teramati:** 70 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 13.36%.
6. **Fee → drift → divergence → hasil:** Fee +0.000203651 SOL (0.2037% modal), divergence principal vs HOLD SOL -0.000291883 SOL, PnL LP -0.000088232 SOL (-0.0882%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · SUUB-SOL · CrQNmBzegtn9z2NTQwHrzcFHtQmEZCuYijhCyW5UgZLz

2026-09-18T00:30:06+07:00 → 2026-09-18T00:34:00+07:00 · 3.90 menit · pool `25XBgCNPhiqi2BmD2toUpitqcaycmENBcs16yarphy3w`.

1. **Market → volatilitas → depth:** Volatility feed 13.547; TVL $41834.57; fee/TVL entry 15.2850%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -542; harga snapshot 0.000004547947 SOL/token; range [-586, -542] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.100002609 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-21.8% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 3 sampel; in-range teramati 49.1%; maksimum penurunan teramati sejak snapshot 14.72%.
6. **Fee → drift → divergence → hasil:** Fee +0.002530852 SOL (2.5309% modal), divergence principal vs HOLD SOL 0.000002630 SOL, PnL LP +0.002533482 SOL (2.5335%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.002533482; setelah gas terhubung +0.002513482.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · SEND-SOL · BkYx3KvK9BpspaCGiPsqVojopcsVspMmbge3qrKrXXt8

2026-09-18T00:48:36+07:00 → 2026-09-18T01:29:40+07:00 · 41.07 menit · pool `9x4aKowDDz2yBNXW1ER7LZs6XJ3gxdWuy6fQtMLLa3y4`.

1. **Market → volatilitas → depth:** Volatility feed 6.856; TVL $32160.89; fee/TVL entry 0.2645%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -595; harga snapshot 0.000002684001 SOL/token; range [-639, -595] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.082062695 SOL + 7527.873036000 token. Porsi token pada mark withdrawal 17.07%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing Take-Profit hit (Peak: 1.92%, Current: 1.22% <= ratchet floor 1.32%)
5. **Jalur yang teramati:** 46 sampel; in-range teramati 58.1%; maksimum penurunan teramati sejak snapshot 19.66%.
6. **Fee → drift → divergence → hasil:** Fee +0.002361168 SOL (2.3612% modal), divergence principal vs HOLD SOL -0.001045709 SOL, PnL LP +0.001315460 SOL (1.3155%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000528292; setelah gas terhubung +0.000503012. Swap cocok unik, jeda 45 detik; selisih terhadap mark token -0.000787168 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · ALL-SOL · 8Mf1y4TFMug7gvPk1D9PxuBzZ4PCkHXTViJFZcSdPVzB

2026-09-18T01:08:40+07:00 → 2026-09-18T02:09:56+07:00 · 61.27 menit · pool `FpP5SnzBnHJ5M9wS7fCuYiiSuXUPLNQKpk7qndeZxKZZ`.

1. **Market → volatilitas → depth:** Volatility feed 4.487; TVL $29573.29; fee/TVL entry 0.1708%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -542; harga snapshot 0.000004547947 SOL/token; range [-586, -542] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.096403675 SOL + 828.632986000 token. Porsi token pada mark withdrawal 3.48%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 3.03% < 5.0% after 60.3m)
5. **Jalur yang teramati:** 66 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 8.57%.
6. **Fee → drift → divergence → hasil:** Fee +0.000158271 SOL (0.1583% modal), divergence principal vs HOLD SOL -0.000116084 SOL, PnL LP +0.000042187 SOL (0.0422%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · FRIES-SOL · 3L9WMiFBxXMt6vENDWJXRWYQ3jYkt3wSTMMi5wg5EQQe

2026-09-18T01:45:36+07:00 → 2026-09-18T01:54:07+07:00 · 8.52 menit · pool `953MwRPrSjhY6FzjaiGLcEMTKbiXmdfrx6oCs2dx4oAy`.

1. **Market → volatilitas → depth:** Volatility feed 5.293; TVL $17260.24; fee/TVL entry 2.3457%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1424; harga snapshot 0.000011808705 SOL/token; range [-1477, -1424] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099995191 SOL + 0.284451606 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.4m (limit 5m)
5. **Jalur yang teramati:** 8 sampel; in-range teramati 28.4%; maksimum penurunan teramati sejak snapshot 5.43%.
6. **Fee → drift → divergence → hasil:** Fee +0.000591082 SOL (0.5911% modal), divergence principal vs HOLD SOL -0.000001425 SOL, PnL LP +0.000589657 SOL (0.5897%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · FRIES-SOL · BxgoHLka32dpDiAg3QLJXbLW6BQ6WNVNdhBe41rS3Q4d

2026-09-18T01:54:52+07:00 → 2026-09-18T02:04:39+07:00 · 9.78 menit · pool `953MwRPrSjhY6FzjaiGLcEMTKbiXmdfrx6oCs2dx4oAy`.

1. **Market → volatilitas → depth:** Volatility feed 5.293; TVL $17260.24; fee/TVL entry 2.3457%; base fee pool 1.0%; bin step 80 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1425; harga snapshot 0.000011714985 SOL/token; range [-1445, -1425] (21 bin), downside 14.73%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099996204 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m); recenter parent/root `3L9WMiFBxXMt6vENDWJXRWYQ3jYkt3wSTMMi5wg5EQQe`
5. **Jalur yang teramati:** 8 sampel; in-range teramati 42.4%; maksimum penurunan teramati sejak snapshot 3.14%.
6. **Fee → drift → divergence → hasil:** Fee +0.000581612 SOL (0.5816% modal), divergence principal vs HOLD SOL -0.000003786 SOL, PnL LP +0.000577826 SOL (0.5778%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000577826; setelah gas terhubung +0.000557826.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · HUHCAT-SOL · FEaJWKrNxQJsxz9teSmDo54i4v5m7aWLwEuTZfbqdELC

2026-09-18T02:34:15+07:00 → 2026-09-18T04:18:03+07:00 · 103.80 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 1.990; TVL $48403.73; fee/TVL entry 0.1203%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -467; harga snapshot 0.000009592205 SOL/token; range [-511, -467] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.090231732 SOL + 4861.079880000 token. Porsi token pada mark withdrawal 28.93%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing Take-Profit hit (Peak: 1.69%, Current: 0.63% <= ratchet floor 1.09%); hold journal: m5 +1.13% h1 -2.85% (token-level pumpswap pair m5 +2.84% h1 -4.02%); PnL +1.41% in range, trailing floor 0.81% - price rising now, expecting bounce to extend before ratchet close
5. **Jalur yang teramati:** 136 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 22.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.003539751 SOL (2.7229% modal), divergence principal vs HOLD SOL -0.003045238 SOL, PnL LP +0.000494512 SOL (0.3804%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · SOLCAT-SOL · 5YrBbjYFiSA7LwGx2QXNvFy97dnnZkS4mG3Bda4zn6r6

2026-09-18T02:56:38+07:00 → 2026-09-18T03:01:13+07:00 · 4.58 menit · pool `FEBzyyXLew5E9JngX7CKumHr5ehdUhRb7G6kjouo77dn`.

1. **Market → volatilitas → depth:** Volatility feed 13.842; TVL $62239.95; fee/TVL entry 21.6259%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -399; harga snapshot 0.000007036915 SOL/token; range [-434, -399] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.099600456 SOL + 58.750900000 token. Porsi token pada mark withdrawal 0.41%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-21.8% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 4 sampel; in-range teramati 0.0%; maksimum penurunan teramati sejak snapshot 7.18%.
6. **Fee → drift → divergence → hasil:** Fee +0.005813057 SOL (5.8131% modal), divergence principal vs HOLD SOL 0.000008794 SOL, PnL LP +0.005821851 SOL (5.8219%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · CLANKER-SOL · 69MpiVwR453XFdWkTDKXUTrUh5MKeSLa2nHDsTbgERsf

2026-09-18T03:07:18+07:00 → 2026-09-18T03:13:49+07:00 · 6.52 menit · pool `9aXA6qqqXueA6Eq9WPRgas4wQgjPCEspzutbaS3UZkXT`.

1. **Market → volatilitas → depth:** Volatility feed 4.568; TVL $11823.52; fee/TVL entry 0.8874%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1178; harga snapshot 0.000008117489 SOL/token; range [-1222, -1178] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.096749054 SOL + 418.882761979 token. Porsi token pada mark withdrawal 3.17%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -5.7% <= -3.0% with PnL +1.78%, peak +1.78%) — realizing before floor gap-through
5. **Jalur yang teramati:** 4 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.002501335 SOL (2.5013% modal), divergence principal vs HOLD SOL -0.000079426 SOL, PnL LP +0.002421909 SOL (2.4219%). Gas transaksi posisi yang terhubung 0.000025000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · Tilcayo-SOL · 8R7vPnQRS3GxyWAvUgyPMiAwsftBz6ggoYAoThzGk8yP

2026-09-18T03:20:48+07:00 → 2026-09-18T03:29:52+07:00 · 9.07 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 8.612; TVL $73554.13; fee/TVL entry 7.1928%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -419; harga snapshot 0.000015464803 SOL/token; range [-463, -419] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.085218368 SOL + 1063.801112000 token. Porsi token pada mark withdrawal 14.02%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-24.3% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 9 sampel; in-range teramati 35.8%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.001345124 SOL (1.3451% modal), divergence principal vs HOLD SOL -0.000890356 SOL, PnL LP +0.000454767 SOL (0.4548%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001123743; setelah gas terhubung +0.001094170. Swap cocok unik, jeda 46 detik; selisih terhadap mark token +0.000668976 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · ELON-SOL · hbErz2UgE2V6A5GMA8fdegELQZ577RLcz121mPNCZAQ

2026-09-18T03:49:59+07:00 → 2026-09-18T03:59:15+07:00 · 9.27 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 5.120; TVL $129099.62; fee/TVL entry 0.2867%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -425; harga snapshot 0.000033827808 SOL/token; range [-478, -425] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999693 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.3m (limit 5m)
5. **Jalur yang teramati:** 9 sampel; in-range teramati 37.3%; maksimum penurunan teramati sejak snapshot 2.36%.
6. **Fee → drift → divergence → hasil:** Fee +0.000009280 SOL (0.0093% modal), divergence principal vs HOLD SOL -0.000000282 SOL, PnL LP +0.000008998 SOL (0.0090%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · DOGE-1-SOL · KcqxDBhtcUyieM9d847MmW8MPSredjw8dJbr4QQRi9E

2026-09-18T05:05:31+07:00 → 2026-09-18T06:03:41+07:00 · 58.17 menit · pool `ErwEeF8y8uLR7LkJcL3xRUuN1d8SrMLZJB92Ydq8vfdw`.

1. **Market → volatilitas → depth:** Volatility feed 3.702; TVL $14637.94; fee/TVL entry 0.4263%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1778; harga snapshot 0.000000703354 SOL/token; range [-1831, -1778] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999974 SOL + 0.000000000 token; withdraw 0.129998093 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 19.1m (limit 5m); hold journal: DOGE-1 OOR 2.6m, dexscreener DLMM SOL pair m5 +4.15% h1 +16.40% pnl +0.26%; price pushing back toward range, expect re-entry into bins within hold window
5. **Jalur yang teramati:** 74 sampel; in-range teramati 56.7%; maksimum penurunan teramati sejak snapshot 0.79%.
6. **Fee → drift → divergence → hasil:** Fee +0.000006561 SOL (0.0050% modal), divergence principal vs HOLD SOL -0.000001881 SOL, PnL LP +0.000004680 SOL (0.0036%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · OTC-SOL · FQUujB4HgfpxnWMdYK2WzfGqqZCzWKofDARrAQJTscux

2026-09-18T05:20:02+07:00 → 2026-09-18T05:50:55+07:00 · 30.88 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 1.723; TVL $18001.06; fee/TVL entry 0.0541%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -294; harga snapshot 0.000053643377 SOL/token; range [-338, -294] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099919142 SOL + 1.505293000 token. Porsi token pada mark withdrawal 0.08%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.12% < 5.0% after 30.2m)
5. **Jalur yang teramati:** 33 sampel; in-range teramati 85.4%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000002485 SOL (0.0025% modal), divergence principal vs HOLD SOL -0.000000088 SOL, PnL LP +0.000002397 SOL (0.0024%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · Tilcayo-SOL · 48HP2JPX5NwbFwG8nfEofwfP9pBg57squPBWx3UNVkhJ

2026-09-18T06:06:24+07:00 → 2026-09-18T06:33:37+07:00 · 27.22 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 3.895; TVL $78459.03; fee/TVL entry 1.0017%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -418; harga snapshot 0.000015619451 SOL/token; range [-462, -418] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.130000264 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 40 sampel; in-range teramati 80.6%; maksimum penurunan teramati sejak snapshot 18.05%.
6. **Fee → drift → divergence → hasil:** Fee +0.003924563 SOL (3.0189% modal), divergence principal vs HOLD SOL 0.000000287 SOL, PnL LP +0.003924850 SOL (3.0191%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · Tilcayo-SOL · BTDkznH83ThthFjN5RmCJuoYoX9sAC5pi8PAQBv6Ed4L

2026-09-18T06:34:22+07:00 → 2026-09-18T06:39:58+07:00 · 5.60 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 3.895; TVL $78459.03; fee/TVL entry 1.0017%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -374; harga snapshot 0.000024199490 SOL/token; range [-394, -374] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999990 SOL + 0.000000000 token; withdraw 0.078798473 SOL + 2292.761443000 token. Porsi token pada mark withdrawal 38.22%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -11.2% <= -3.0% with PnL -2.11% <= -1.5%) — cutting before the downtrend level; recenter parent/root `48HP2JPX5NwbFwG8nfEofwfP9pBg57squPBWx3UNVkhJ`
5. **Jalur yang teramati:** 7 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 13.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.002754722 SOL (2.1190% modal), divergence principal vs HOLD SOL -0.002450103 SOL, PnL LP +0.000304619 SOL (0.2343%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · ELON-SOL · Bamvbb3JQgDkwVrKqsmUQ2T1R6BJeTqSPgkcs8ScHbZv

2026-09-18T06:42:45+07:00 → 2026-09-18T06:58:58+07:00 · 16.22 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 3.748; TVL $146265.48; fee/TVL entry 0.2636%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -415; harga snapshot 0.000036633564 SOL/token; range [-468, -415] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999974 SOL + 0.000000000 token; withdraw 0.129999664 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 22 sampel; in-range teramati 51.7%; maksimum penurunan teramati sejak snapshot 0.79%.
6. **Fee → drift → divergence → hasil:** Fee +0.000003880 SOL (0.0030% modal), divergence principal vs HOLD SOL -0.000000310 SOL, PnL LP +0.000003570 SOL (0.0027%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · FRIES-SOL · 31NnhoQwZZCpdcU5QQHybGrXoGKgvnkjLMgy4RSzyyWN

2026-09-18T07:03:04+07:00 → 2026-09-18T07:12:59+07:00 · 9.92 menit · pool `953MwRPrSjhY6FzjaiGLcEMTKbiXmdfrx6oCs2dx4oAy`.

1. **Market → volatilitas → depth:** Volatility feed 2.755; TVL $20132.68; fee/TVL entry 0.1881%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1486; harga snapshot 0.000007205254 SOL/token; range [-1539, -1486] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999268 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.8m (limit 5m)
5. **Jalur yang teramati:** 12 sampel; in-range teramati 37.5%; maksimum penurunan teramati sejak snapshot 0.79%.
6. **Fee → drift → divergence → hasil:** Fee +0.000003092 SOL (0.0031% modal), divergence principal vs HOLD SOL -0.000000707 SOL, PnL LP +0.000002385 SOL (0.0024%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000002385; setelah gas terhubung -0.000017615.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · MCAT-SOL · RFG5wnRSWEAGRnvK6R1tqg2nbAkUY3iLzTcnQn8Wq4L

2026-09-18T07:08:47+07:00 → 2026-09-18T07:16:05+07:00 · 7.30 menit · pool `HHgxEaEw1Wq9pSmMXp1dmf7vpDq7CegXbHVwtfYwcZRr`.

1. **Market → volatilitas → depth:** Volatility feed 2.264; TVL $86984.52; fee/TVL entry 0.7090%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -373; harga snapshot 0.000024441484 SOL/token; range [-417, -373] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999419 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 6.1m (limit 5m)
5. **Jalur yang teramati:** 4 sampel; in-range teramati 0.0%; maksimum penurunan teramati sejak snapshot -1.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000502 SOL (0.0005% modal), divergence principal vs HOLD SOL -0.000000560 SOL, PnL LP -0.000000058 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000058; setelah gas terhubung -0.000020058.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · MCAT-SOL · 3r5DB5S3HrgYX9JP2LQgcFc5Jk1aPAE5sPnZcdQMgHf2

2026-09-18T07:16:49+07:00 → 2026-09-18T07:20:22+07:00 · 3.55 menit · pool `HHgxEaEw1Wq9pSmMXp1dmf7vpDq7CegXbHVwtfYwcZRr`.

1. **Market → volatilitas → depth:** Volatility feed 2.264; TVL $86984.52; fee/TVL entry 0.7090%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -364; harga snapshot 0.000026731292 SOL/token; range [-384, -364] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.071988618 SOL + 1118.846392000 token. Porsi token pada mark withdrawal 27.33%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -12.7% <= -3.0% with PnL -2.36% <= -1.5%) — cutting before the downtrend level; recenter parent/root `RFG5wnRSWEAGRnvK6R1tqg2nbAkUY3iLzTcnQn8Wq4L`
5. **Jalur yang teramati:** 3 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 9.47%.
6. **Fee → drift → divergence → hasil:** Fee +0.002199634 SOL (2.1996% modal), divergence principal vs HOLD SOL -0.000935860 SOL, PnL LP +0.001263774 SOL (1.2638%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.001810563; setelah gas terhubung -0.001935563. Swap cocok unik, jeda 570 detik; selisih terhadap mark token -0.003074337 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · FRIES-SOL · CjTU6qX2BDnhm1iYF4JuPpTvmS77EmsisHu2v1Kr97L2

2026-09-18T08:19:17+07:00 → 2026-09-18T09:21:12+07:00 · 61.92 menit · pool `953MwRPrSjhY6FzjaiGLcEMTKbiXmdfrx6oCs2dx4oAy`.

1. **Market → volatilitas → depth:** Volatility feed 3.040; TVL $19644.07; fee/TVL entry 0.1639%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1481; harga snapshot 0.000007498112 SOL/token; range [-1534, -1481] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999974 SOL + 0.000000000 token; withdraw 0.119999770 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 1.41% < 5.0% after 60.7m)
5. **Jalur yang teramati:** 76 sampel; in-range teramati 89.6%; maksimum penurunan teramati sejak snapshot 4.67%.
6. **Fee → drift → divergence → hasil:** Fee +0.000071127 SOL (0.0593% modal), divergence principal vs HOLD SOL -0.000000204 SOL, PnL LP +0.000070923 SOL (0.0591%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000070923; setelah gas terhubung +0.000050923.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · PERK-SOL · 4ToMKaPuB5gkbEGZ3CfqGYa1ZkVy4EPxBEbhmGp2XfTV

2026-09-18T08:22:49+07:00 → 2026-09-18T08:31:52+07:00 · 9.05 menit · pool `8d6dxZomEUj3vKxYZQcor7Tdn924swbMCXkaJJozdFQ6`.

1. **Market → volatilitas → depth:** Volatility feed 5.280; TVL $11921.37; fee/TVL entry 1.6793%; base fee pool 1.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -325; harga snapshot 0.000017644715 SOL/token; range [-360, -325] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.099999291 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m)
5. **Jalur yang teramati:** 8 sampel; in-range teramati 26.2%; maksimum penurunan teramati sejak snapshot -0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000005238 SOL (0.0052% modal), divergence principal vs HOLD SOL -0.000000692 SOL, PnL LP +0.000004546 SOL (0.0045%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · SOLCAT-SOL · Drmj7QwQPYkhdJ1y1VK26a2Rxzqegwh6NU9ayNPMXsTi

2026-09-18T09:01:46+07:00 → 2026-09-18T09:09:05+07:00 · 7.32 menit · pool `FEBzyyXLew5E9JngX7CKumHr5ehdUhRb7G6kjouo77dn`.

1. **Market → volatilitas → depth:** Volatility feed 5.678; TVL $24390.66; fee/TVL entry 1.0584%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -373; harga snapshot 0.000009719705 SOL/token; range [-408, -373] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.099999983 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.4m (limit 5m)
5. **Jalur yang teramati:** 7 sampel; in-range teramati 16.5%; maksimum penurunan teramati sejak snapshot -0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · SOLCAT-SOL · HKktqUhf5cQ6KSpe8XN7U5kJJ5ibFhYRSVCCtbwrnBv7

2026-09-18T09:09:50+07:00 → 2026-09-18T09:22:50+07:00 · 13.00 menit · pool `FEBzyyXLew5E9JngX7CKumHr5ehdUhRb7G6kjouo77dn`.

1. **Market → volatilitas → depth:** Volatility feed 5.678; TVL $24390.66; fee/TVL entry 1.0584%; base fee pool 5.0%; bin step 125 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -357; harga snapshot 0.000011856967 SOL/token; range [-377, -357] (21 bin), downside 22.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099984097 SOL + 0.000620000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.9m (limit 5m); recenter parent/root `Drmj7QwQPYkhdJ1y1VK26a2Rxzqegwh6NU9ayNPMXsTi`
5. **Jalur yang teramati:** 11 sampel; in-range teramati 51.6%; maksimum penurunan teramati sejak snapshot -0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000009656 SOL (0.0097% modal), divergence principal vs HOLD SOL -0.000015886 SOL, PnL LP -0.000006230 SOL (-0.0062%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · SOLCAT-SOL · GAvb11LjNCbJErKpXxAvxPBHg8M7QSnHHbsxxANc1Wz4

2026-09-18T09:23:41+07:00 → 2026-09-18T09:55:30+07:00 · 31.82 menit · pool `FEBzyyXLew5E9JngX7CKumHr5ehdUhRb7G6kjouo77dn`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 5.0%; bin step 125 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -358; harga snapshot 0.000011710585 SOL/token; range [-378, -358] (21 bin), downside 22.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099975015 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 20.7m (limit 5m); recenter parent/root `Drmj7QwQPYkhdJ1y1VK26a2Rxzqegwh6NU9ayNPMXsTi`
5. **Jalur yang teramati:** 40 sampel; in-range teramati 32.5%; maksimum penurunan teramati sejak snapshot 6.02%.
6. **Fee → drift → divergence → hasil:** Fee +0.001053174 SOL (1.0532% modal), divergence principal vs HOLD SOL -0.000024975 SOL, PnL LP +0.001028199 SOL (1.0282%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001028199; setelah gas terhubung +0.001008199.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · UBI-SOL · GQ7egAjDCkhEHAaDTymyUCuJ9zvE64YcD2ACcjErdni5

2026-09-18T09:40:49+07:00 → 2026-09-18T10:20:20+07:00 · 39.52 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 4.694; TVL $13705.47; fee/TVL entry 0.1168%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1228; harga snapshot 0.000004935748 SOL/token; range [-1272, -1228] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099392700 SOL + 124.762856539 token. Porsi token pada mark withdrawal 0.60%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 1.55% < 5.0% after 38.4m); hold journal: Dexscreener SOL pair m5 +6.26% h1 +10.80% - OOR 4.8m with price climbing back toward range top (pool 4.985e-6 vs range 4.94e-6-4.99e-6); pnl +0.16% not underwater. Expect re-entry into range within 15m.
5. **Jalur yang teramati:** 47 sampel; in-range teramati 84.9%; maksimum penurunan teramati sejak snapshot 3.90%.
6. **Fee → drift → divergence → hasil:** Fee +0.000041896 SOL (0.0419% modal), divergence principal vs HOLD SOL -0.000009591 SOL, PnL LP +0.000032304 SOL (0.0323%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · MCAT-SOL · GNasmyeBWHNiVvfyZufFT9pU1ub1zrvJPhtoeZ2Wiccb

2026-09-18T10:13:38+07:00 → 2026-09-18T10:22:18+07:00 · 8.67 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 3.750; TVL $102310.38; fee/TVL entry 1.3026%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -330; harga snapshot 0.000016582098 SOL/token; range [-365, -330] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.099997413 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.6m (limit 5m)
5. **Jalur yang teramati:** 7 sampel; in-range teramati 27.6%; maksimum penurunan teramati sejak snapshot 1.23%.
6. **Fee → drift → divergence → hasil:** Fee +0.000020205 SOL (0.0202% modal), divergence principal vs HOLD SOL -0.000002570 SOL, PnL LP +0.000017635 SOL (0.0176%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · Tilcayo-SOL · DPqnDY25Jg5WJzUhPY7wkUAy73v2VrNQkjuqc9DMPURS

2026-09-18T10:29:56+07:00 → 2026-09-18T10:36:23+07:00 · 6.45 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 4.729; TVL $98395.26; fee/TVL entry 0.5926%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -399; harga snapshot 0.000018869998 SOL/token; range [-443, -399] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.118483459 SOL + 82.368947000 token. Porsi token pada mark withdrawal 1.24%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-20.6% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 8 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.000073021 SOL (0.0609% modal), divergence principal vs HOLD SOL -0.000022868 SOL, PnL LP +0.000050152 SOL (0.0418%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · PERPSPAD-SOL · G9smSfmZeLvSG2YtY6Cxbok4sjQCHn9WQdT27MGBFYkP

2026-09-18T11:03:17+07:00 → 2026-09-18T11:34:48+07:00 · 31.52 menit · pool `EHqk4Fw3pTCf9UW75dWoCMf6a2GxyJ8FGYEj2Qmw9rfr`.

1. **Market → volatilitas → depth:** Volatility feed 0.426; TVL $97656.86; fee/TVL entry 0.0723%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -347; harga snapshot 0.000062978942 SOL/token; range [-400, -347] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999974 SOL + 0.000000000 token; withdraw 0.119669119 SOL + 5.301423000 token. Porsi token pada mark withdrawal 0.27%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.80% < 5.0% after 30.4m)
5. **Jalur yang teramati:** 44 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 3.14%.
6. **Fee → drift → divergence → hasil:** Fee +0.000020711 SOL (0.0173% modal), divergence principal vs HOLD SOL -0.000002256 SOL, PnL LP +0.000018455 SOL (0.0154%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · PERK-SOL · 5zK5kndvi7dnaw7nQ6ifTpZoDq6rHLuw8Q6xPZaXzg2G

2026-09-18T11:28:28+07:00 → 2026-09-18T11:38:58+07:00 · 10.50 menit · pool `8d6dxZomEUj3vKxYZQcor7Tdn924swbMCXkaJJozdFQ6`.

1. **Market → volatilitas → depth:** Volatility feed 5.080; TVL $20724.18; fee/TVL entry 1.2915%; base fee pool 1.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -359; harga snapshot 0.000011566010 SOL/token; range [-394, -359] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.100000526 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 10 sampel; in-range teramati 44.4%; maksimum penurunan teramati sejak snapshot 8.33%.
6. **Fee → drift → divergence → hasil:** Fee +0.000720571 SOL (0.7206% modal), divergence principal vs HOLD SOL 0.000000543 SOL, PnL LP +0.000721114 SOL (0.7211%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · PERK-SOL · 9pjfz6zD2KcjLirhcxLmXZyApVVsDUR6i8XdSH5PKk8T

2026-09-18T11:39:45+07:00 → 2026-09-18T11:53:34+07:00 · 13.82 menit · pool `8d6dxZomEUj3vKxYZQcor7Tdn924swbMCXkaJJozdFQ6`.

1. **Market → volatilitas → depth:** Volatility feed 5.080; TVL $20724.18; fee/TVL entry 1.2915%; base fee pool 1.0%; bin step 125 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -353; harga snapshot 0.000012461024 SOL/token; range [-373, -353] (21 bin), downside 22.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099984457 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m); recenter parent/root `5zK5kndvi7dnaw7nQ6ifTpZoDq6rHLuw8Q6xPZaXzg2G`
5. **Jalur yang teramati:** 19 sampel; in-range teramati 58.2%; maksimum penurunan teramati sejak snapshot 7.18%.
6. **Fee → drift → divergence → hasil:** Fee +0.000866454 SOL (0.8665% modal), divergence principal vs HOLD SOL -0.000015533 SOL, PnL LP +0.000850921 SOL (0.8509%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · PERK-SOL · AAj9sHxFVtqQSLNW2pUdzTMMK7nHT4R68C7jFxETHUVp

2026-09-18T11:55:27+07:00 → 2026-09-18T12:03:57+07:00 · 8.50 menit · pool `8d6dxZomEUj3vKxYZQcor7Tdn924swbMCXkaJJozdFQ6`.

1. **Market → volatilitas → depth:** Volatility feed 7.079; TVL $18551.97; fee/TVL entry 2.2984%; base fee pool 1.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -347; harga snapshot 0.000013425298 SOL/token; range [-382, -347] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999982 SOL + 0.000000000 token; withdraw 0.119995555 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.4m (limit 5m)
5. **Jalur yang teramati:** 11 sampel; in-range teramati 28.5%; maksimum penurunan teramati sejak snapshot -0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000004178 SOL (0.0035% modal), divergence principal vs HOLD SOL -0.000004427 SOL, PnL LP -0.000000249 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · MCAT-SOL · BtHn7dPKAySxAmNT8KPmdGiZBvNr3VsYeyS4WsKMhMnY

2026-09-18T12:50:06+07:00 → 2026-09-18T13:01:44+07:00 · 11.63 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 4.539; TVL $72395.40; fee/TVL entry 1.3229%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -355; harga snapshot 0.000012155244 SOL/token; range [-390, -355] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999982 SOL + 0.000000000 token; withdraw 0.119995991 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.6m (limit 5m)
5. **Jalur yang teramati:** 16 sampel; in-range teramati 49.3%; maksimum penurunan teramati sejak snapshot 1.23%.
6. **Fee → drift → divergence → hasil:** Fee +0.000015768 SOL (0.0131% modal), divergence principal vs HOLD SOL -0.000003991 SOL, PnL LP +0.000011777 SOL (0.0098%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · MCAT-SOL · uvYzxzyFj6Wnxta5ENtKypkeVFvzStrPBEnyexNDufi

2026-09-18T13:02:30+07:00 → 2026-09-18T13:12:37+07:00 · 10.12 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 4.539; TVL $72395.40; fee/TVL entry 1.3229%; base fee pool 1.5%; bin step 125 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -352; harga snapshot 0.000012616787 SOL/token; range [-372, -352] (21 bin), downside 22.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999990 SOL + 0.000000000 token; withdraw 0.119987556 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.1m (limit 5m); recenter parent/root `BtHn7dPKAySxAmNT8KPmdGiZBvNr3VsYeyS4WsKMhMnY`
5. **Jalur yang teramati:** 14 sampel; in-range teramati 37.7%; maksimum penurunan teramati sejak snapshot 1.23%.
6. **Fee → drift → divergence → hasil:** Fee +0.000041968 SOL (0.0350% modal), divergence principal vs HOLD SOL -0.000012434 SOL, PnL LP +0.000029534 SOL (0.0246%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · MCAT-SOL · A9XX7PAksEoYQjNGm3S1Ts9gXYSeY7BeGZsQZvUpgjns

2026-09-18T14:50:16+07:00 → 2026-09-18T15:04:09+07:00 · 13.88 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 2.628; TVL $54936.29; fee/TVL entry 0.3253%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -344; harga snapshot 0.000013935066 SOL/token; range [-379, -344] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999982 SOL + 0.000000000 token; withdraw 0.119999682 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m)
5. **Jalur yang teramati:** 19 sampel; in-range teramati 56.9%; maksimum penurunan teramati sejak snapshot 3.66%.
6. **Fee → drift → divergence → hasil:** Fee +0.000032945 SOL (0.0275% modal), divergence principal vs HOLD SOL -0.000000300 SOL, PnL LP +0.000032645 SOL (0.0272%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · UBI-SOL · Gk4qFeB1fkXhCj9zzYPCd5cNBZsvhzgZSMDJQ2T56TSv

2026-09-18T15:05:25+07:00 → 2026-09-18T15:36:45+07:00 · 31.33 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 1.149; TVL $16054.05; fee/TVL entry 0.1116%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1222; harga snapshot 0.000005239396 SOL/token; range [-1266, -1222] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119996649 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.11% < 5.0% after 30.0m)
5. **Jalur yang teramati:** 42 sampel; in-range teramati 37.4%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000002849 SOL (0.0024% modal), divergence principal vs HOLD SOL -0.000003332 SOL, PnL LP -0.000000483 SOL (-0.0004%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000483; setelah gas terhubung -0.000020483.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · PERPSPAD-SOL · GLVe9nTD9Ge1oaujAriwUej7U2736fBe9NCrcw9grFjS

2026-09-18T15:24:35+07:00 → 2026-09-18T15:56:06+07:00 · 31.52 menit · pool `D2Z3uVsqgLHxe5C5H3F3PjqkCWsq4AqdYn1K91DVNknV`.

1. **Market → volatilitas → depth:** Volatility feed 22.432; TVL $10117.93; fee/TVL entry 4.1780%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -254; harga snapshot 0.000079867678 SOL/token; range [-298, -254] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.100000144 SOL + 0.000001000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 1.95% < 5.0% after 30.6m)
5. **Jalur yang teramati:** 38 sampel; in-range teramati 24.8%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000042748 SOL (0.0427% modal), divergence principal vs HOLD SOL 0.000000165 SOL, PnL LP +0.000042913 SOL (0.0429%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · MCAT-SOL · 8xKkiirdCT1Dvj4QyAYtzEBTq5nGYGgtT4XVA15HHYZD

2026-09-18T16:10:03+07:00 → 2026-09-18T16:37:47+07:00 · 27.73 menit · pool `HHgxEaEw1Wq9pSmMXp1dmf7vpDq7CegXbHVwtfYwcZRr`.

1. **Market → volatilitas → depth:** Volatility feed 3.216; TVL $30547.91; fee/TVL entry 0.1990%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -420; harga snapshot 0.000015311686 SOL/token; range [-464, -420] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.103623253 SOL + 1957.459313000 token. Porsi token pada mark withdrawal 19.32%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -7.4% <= -3.0% with PnL -1.58% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 41 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 16.40%.
6. **Fee → drift → divergence → hasil:** Fee +0.000740697 SOL (0.5698% modal), divergence principal vs HOLD SOL -0.001567701 SOL, PnL LP -0.000827005 SOL (-0.6362%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · biketyson-SOL · HUAcLbA27H3wwJq3mZbc5xFUgnyTBMTYpNystkuBoz1N

2026-09-18T17:28:33+07:00 → 2026-09-18T18:00:12+07:00 · 31.65 menit · pool `ARqHS4dXM989rYBjDKzx249yqBXQtdrUioemyoGEnAnk`.

1. **Market → volatilitas → depth:** Volatility feed 2.985; TVL $62264.16; fee/TVL entry 0.0888%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -388; harga snapshot 0.000021052660 SOL/token; range [-432, -388] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119998160 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 2.43% < 5.0% after 30.6m)
5. **Jalur yang teramati:** 47 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 2.94%.
6. **Fee → drift → divergence → hasil:** Fee +0.000063110 SOL (0.0526% modal), divergence principal vs HOLD SOL -0.000001821 SOL, PnL LP +0.000061289 SOL (0.0511%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000061289; setelah gas terhubung +0.000041289.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · HUHCAT-SOL · hFwB8aDV1UMpNNhnCvhwQdMwtZMyteUDxBnWLccFh4S

2026-09-18T18:06:16+07:00 → 2026-09-18T19:07:23+07:00 · 61.12 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 3.811; TVL $23020.57; fee/TVL entry 0.2969%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -536; harga snapshot 0.000004827738 SOL/token; range [-580, -536] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.115830976 SOL + 905.835910000 token. Porsi token pada mark withdrawal 3.40%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stale ticket re-pin (60m in range, peak +0.35% never armed the 1.2% ratchet, fee/TVL 5.5%)
5. **Jalur yang teramati:** 81 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 7.65%.
6. **Fee → drift → divergence → hasil:** Fee +0.000278456 SOL (0.2320% modal), divergence principal vs HOLD SOL -0.000090100 SOL, PnL LP +0.000188356 SOL (0.1570%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Batas umur/peak sendiri belum membuktikan biaya reposisi layak; snapshot fee pace posisi diperlukan. 

## azimuth · MCAT-SOL · 6KtMeTcCcET3Korv7Q9AC2CjYiJZH6uFEaRRMzkx74fj

2026-09-18T18:38:49+07:00 → 2026-09-18T19:00:18+07:00 · 21.48 menit · pool `HHgxEaEw1Wq9pSmMXp1dmf7vpDq7CegXbHVwtfYwcZRr`.

1. **Market → volatilitas → depth:** Volatility feed 2.717; TVL $35985.16; fee/TVL entry 0.3447%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -404; harga snapshot 0.000017954156 SOL/token; range [-448, -404] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999992 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 22 sampel; in-range teramati 77.1%; maksimum penurunan teramati sejak snapshot 11.26%.
6. **Fee → drift → divergence → hasil:** Fee +0.000559085 SOL (0.5591% modal), divergence principal vs HOLD SOL 0.000000013 SOL, PnL LP +0.000559098 SOL (0.5591%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · HUHCAT-SOL · 2v5bRsKifaGqX1Ti6okBbGzhiq4KCxdtnvcFDNUb8cNU

2026-09-18T19:08:08+07:00 → 2026-09-18T20:08:05+07:00 · 59.95 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 3.811; TVL $23020.57; fee/TVL entry 0.2969%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -543; harga snapshot 0.000004502918 SOL/token; range [-563, -543] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999990 SOL + 0.000000000 token; withdraw 0.095752663 SOL + 5686.008653000 token. Porsi token pada mark withdrawal 19.65%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stale ticket re-pin (61m in range, peak +0.96% never armed the 1.2% ratchet, fee/TVL 32.8%); recenter parent/root `hFwB8aDV1UMpNNhnCvhwQdMwtZMyteUDxBnWLccFh4S`
5. **Jalur yang teramati:** 89 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 12.13%.
6. **Fee → drift → divergence → hasil:** Fee +0.001607639 SOL (1.3397% modal), divergence principal vs HOLD SOL -0.000836908 SOL, PnL LP +0.000770731 SOL (0.6423%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Batas umur/peak sendiri belum membuktikan biaya reposisi layak; snapshot fee pace posisi diperlukan. 

## azimuth · SOLCAT-SOL · 4C1UTUrd2dseSKmutZi5uUYF4qeGdhFPivJcx4d9TWNM

2026-09-18T20:51:56+07:00 → 2026-09-18T21:23:35+07:00 · 31.65 menit · pool `FEBzyyXLew5E9JngX7CKumHr5ehdUhRb7G6kjouo77dn`.

1. **Market → volatilitas → depth:** Volatility feed 2.684; TVL $34720.64; fee/TVL entry 0.0911%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -379; harga snapshot 0.000009021586 SOL/token; range [-414, -379] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999982 SOL + 0.000000000 token; withdraw 0.129999925 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.00% < 5.0% after 30.1m)
5. **Jalur yang teramati:** 41 sampel; in-range teramati 8.4%; maksimum penurunan teramati sejak snapshot -0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000051 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000057 SOL, PnL LP -0.000000006 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000006; setelah gas terhubung -0.000020006.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · biketyson-SOL · 3QTSgmxNHg2bP6f1iV7FVVq2U8MQrosGWTzt7EemxNfP

2026-09-18T21:11:32+07:00 → 2026-09-18T21:42:49+07:00 · 31.28 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 2.952; TVL $62969.75; fee/TVL entry 0.0665%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -393; harga snapshot 0.000020030883 SOL/token; range [-437, -393] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999954 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.03% < 5.0% after 30.3m)
5. **Jalur yang teramati:** 32 sampel; in-range teramati 7.0%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000674 SOL (0.0007% modal), divergence principal vs HOLD SOL -0.000000025 SOL, PnL LP +0.000000649 SOL (0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · UBI-SOL · 23zkVFEytjRV4zTeVKDkGAowyA4Xht5qMv9fUcT17yPA

2026-09-18T21:24:35+07:00 → 2026-09-18T21:32:56+07:00 · 8.35 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 2.699; TVL $15630.37; fee/TVL entry 0.4726%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1186; harga snapshot 0.000007496364 SOL/token; range [-1230, -1186] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099997546 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.7m (limit 5m)
5. **Jalur yang teramati:** 7 sampel; in-range teramati 15.7%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000004697 SOL (0.0047% modal), divergence principal vs HOLD SOL -0.000002433 SOL, PnL LP +0.000002264 SOL (0.0023%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · baton-SOL · 2fS7gYYTQAFsgg1GhnhuYM1nxV2cvYe8724k7R1mKgHH

2026-09-18T22:06:19+07:00 → 2026-09-18T23:05:56+07:00 · 59.62 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 3.428; TVL $48170.63; fee/TVL entry 0.1521%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -382; harga snapshot 0.000022347823 SOL/token; range [-426, -382] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.123091791 SOL + 328.133565000 token. Porsi token pada mark withdrawal 5.12%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -3.2% <= -3.0% with PnL +1.48%, peak +1.56%) — realizing before floor gap-through; hold journal: trailing gate: DexScreener SOL pair m5 +5.61% h1 -4.45% (pool 9NdiyGf...), pnl +1.38% in range, ratchet floor 0.96% only 0.42pp away - 5m bounce off the low, expecting ratchet floor to hold and fees to keep accruing
5. **Jalur yang teramati:** 70 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 12.13%.
6. **Fee → drift → divergence → hasil:** Fee +0.000646427 SOL (0.4973% modal), divergence principal vs HOLD SOL -0.000269653 SOL, PnL LP +0.000376774 SOL (0.2898%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000115129; setelah gas terhubung +0.000088905. Swap cocok unik, jeda 970 detik; selisih terhadap mark token -0.000261645 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · ELON-SOL · 8C5j4mPQ4KGfaeSAxXBiuhimTePCMaVqjHQT3FsVU9AY

2026-09-18T22:24:53+07:00 → 2026-09-18T22:44:30+07:00 · 19.62 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 3.000; TVL $139271.20; fee/TVL entry 0.3127%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -413; harga snapshot 0.000037222046 SOL/token; range [-466, -413] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999890 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m); hold journal: ELON-SOL OOR 4.9m; own DLMM pool m5 +2.26% h1 +30.16% - bounce toward range, pnl -0.03%
5. **Jalur yang teramati:** 19 sampel; in-range teramati 53.7%; maksimum penurunan teramati sejak snapshot 2.36%.
6. **Fee → drift → divergence → hasil:** Fee +0.000028521 SOL (0.0285% modal), divergence principal vs HOLD SOL -0.000000085 SOL, PnL LP +0.000028436 SOL (0.0284%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · baton-SOL · 9firhTjVeGc84cyyMEKVrJxKpRxnJEr6iBi7HADrCsj6

2026-09-18T23:06:42+07:00 → 2026-09-19T00:29:02+07:00 · 82.33 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 3.428; TVL $48170.63; fee/TVL entry 0.1521%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -392; harga snapshot 0.000020231192 SOL/token; range [-412, -392] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999990 SOL + 0.000000000 token; withdraw 0.111428275 SOL + 959.754510000 token. Porsi token pada mark withdrawal 13.98%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -6.2% <= -3.0% with PnL +1.79%, peak +1.97%) — realizing before floor gap-through; recenter parent/root `2fS7gYYTQAFsgg1GhnhuYM1nxV2cvYe8724k7R1mKgHH`; hold journal: m5 +7.83% h1 +5.09% (SOL DLMM pair) - turnover trailing band, peak +1.97% vs 1.2/0.6 ratchet floor 1.37%, price rising into range
5. **Jalur yang teramati:** 121 sampel; in-range teramati 95.2%; maksimum penurunan teramati sejak snapshot 8.57%.
6. **Fee → drift → divergence → hasil:** Fee +0.002011831 SOL (1.5476% modal), divergence principal vs HOLD SOL -0.000461149 SOL, PnL LP +0.001550682 SOL (1.1928%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001800674; setelah gas terhubung +0.001742603. Swap cocok unik, jeda 45 detik; selisih terhadap mark token +0.000249992 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · NASDOG-SOL · 5xtnBkvoVHXRHjx5Ni9cktcWkpbQuemLkYEwAru4KEb4

2026-09-19T00:00:02+07:00 → 2026-09-19T00:00:46+07:00 · 0.73 menit · pool `GfCnfPzeSppL8B3DBU6B8sYrtEAEugMjowFBKVviAins`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $60885.34; fee/TVL entry 1.7462%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -491; harga snapshot 0.000007554496 SOL/token; range [-535, -491] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099897427 SOL + 13.451637000 token. Porsi token pada mark withdrawal 0.10%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** journal unavailable
5. **Jalur yang teramati:** 0 sampel; in-range teramati tidak tersedia%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000020707 SOL (0.0207% modal), divergence principal vs HOLD SOL -0.000001938 SOL, PnL LP +0.000018769 SOL (0.0188%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · OTC-SOL · EeyotoE6krpTtHwEcnjS6ptcm18QpsbZzBs9wPhPF2q1

2026-09-19T00:26:10+07:00 → 2026-09-19T00:57:39+07:00 · 31.48 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 1.090; TVL $12689.93; fee/TVL entry 0.2091%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -313; harga snapshot 0.000044402764 SOL/token; range [-357, -313] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099996651 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.14% < 5.0% after 30.7m)
5. **Jalur yang teramati:** 39 sampel; in-range teramati 15.4%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000002895 SOL (0.0029% modal), divergence principal vs HOLD SOL -0.000003328 SOL, PnL LP -0.000000433 SOL (-0.0004%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000433; setelah gas terhubung -0.000020433.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · Tilcayo-SOL · GDTn9SuZu19ePznsRLjt3dNkGjz2GYktFRwRPovGxvF6

2026-09-19T00:47:27+07:00 → 2026-09-19T00:59:09+07:00 · 11.70 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 5.346; TVL $100041.68; fee/TVL entry 0.6870%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -425; harga snapshot 0.000014568544 SOL/token; range [-469, -425] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.019396026 SOL + 7216.443612000 token. Porsi token pada mark withdrawal 78.45%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Downtrend dump, unconfirmed (PnL -4.55% <= -2.5%, no 1h confirmation) — risk floor
5. **Jalur yang teramati:** 11 sampel; in-range teramati 81.8%; maksimum penurunan teramati sejak snapshot 17.23%.
6. **Fee → drift → divergence → hasil:** Fee +0.003168736 SOL (3.1687% modal), divergence principal vs HOLD SOL -0.009990994 SOL, PnL LP -0.006822258 SOL (-6.8223%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · SOLCAT-SOL · FomsQRfUnTt71nEiyJumb5ygirofe1FH5ZrTFdu1NFUL

2026-09-19T02:17:34+07:00 → 2026-09-19T02:26:05+07:00 · 8.52 menit · pool `HGF6LLmPghmtE9cuCEemeZiz8pv2G5G5HNJbnfECfmKf`.

1. **Market → volatilitas → depth:** Volatility feed 3.217; TVL $14951.48; fee/TVL entry 0.7284%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -472; harga snapshot 0.000009126654 SOL/token; range [-516, -472] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119999974 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.4m (limit 5m)
5. **Jalur yang teramati:** 11 sampel; in-range teramati 29.2%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000006 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000007 SOL, PnL LP -0.000000001 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000001; setelah gas terhubung -0.000020001.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · SOLCAT-SOL · 9fPRjQj419wFDTn48PxsUrxfeR8NKxYEoVUpPk4Rtxyi

2026-09-19T02:26:50+07:00 → 2026-09-19T02:45:22+07:00 · 18.53 menit · pool `HGF6LLmPghmtE9cuCEemeZiz8pv2G5G5HNJbnfECfmKf`.

1. **Market → volatilitas → depth:** Volatility feed 3.217; TVL $14951.48; fee/TVL entry 0.7284%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -468; harga snapshot 0.000009497232 SOL/token; range [-488, -468] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999990 SOL + 0.000000000 token; withdraw 0.096625377 SOL + 2595.439735000 token. Porsi token pada mark withdrawal 19.07%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -5.7% <= -3.0% with PnL +1.30%, peak +1.30%) — realizing before floor gap-through; recenter parent/root `FomsQRfUnTt71nEiyJumb5ygirofe1FH5ZrTFdu1NFUL`
5. **Jalur yang teramati:** 20 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 9.47%.
6. **Fee → drift → divergence → hasil:** Fee +0.002090355 SOL (1.7420% modal), divergence principal vs HOLD SOL -0.000611218 SOL, PnL LP +0.001479136 SOL (1.2326%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · BUTTHOLE-SOL · H5ziC61AK9LreMRoMLeYHFWew2kv6hJajwndCGu7Vtc

2026-09-19T02:30:32+07:00 → 2026-09-19T03:02:38+07:00 · 32.10 menit · pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatilitas → depth:** Volatility feed 4.313; TVL $81422.36; fee/TVL entry 0.0924%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1358; harga snapshot 0.000019980088 SOL/token; range [-1411, -1358] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.096489602 SOL + 184.160262919 token. Porsi token pada mark withdrawal 3.43%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 1.83% < 5.0% after 30.6m)
5. **Jalur yang teramati:** 31 sampel; in-range teramati 54.2%; maksimum penurunan teramati sejak snapshot 6.92%.
6. **Fee → drift → divergence → hasil:** Fee +0.000043609 SOL (0.0436% modal), divergence principal vs HOLD SOL -0.000085468 SOL, PnL LP -0.000041859 SOL (-0.0419%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · SOLCAT-SOL · 49BuYaEX9nP5gbL3xsZ3TfzeDmPCab6rNS6DkUNcQW5e

2026-09-19T02:46:39+07:00 → 2026-09-19T03:16:49+07:00 · 30.17 menit · pool `HGF6LLmPghmtE9cuCEemeZiz8pv2G5G5HNJbnfECfmKf`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -475; harga snapshot 0.000008858240 SOL/token; range [-495, -475] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999990 SOL + 0.000000000 token; withdraw 0.120000082 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m); recenter parent/root `FomsQRfUnTt71nEiyJumb5ygirofe1FH5ZrTFdu1NFUL`
5. **Jalur yang teramati:** 36 sampel; in-range teramati 83.6%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.000570112 SOL (0.4751% modal), divergence principal vs HOLD SOL 0.000000092 SOL, PnL LP +0.000570204 SOL (0.4752%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · 67-SOL · HchcxYCbfLTUmiTykM9wprKMWVKQssobDWdJoa2txUJT

2026-09-19T03:31:33+07:00 → 2026-09-19T04:28:36+07:00 · 57.05 menit · pool `CNU1FQNdm2RXUotU8sw7HttcN5WsXVfsn28c8NDEvEN7`.

1. **Market → volatilitas → depth:** Volatility feed 1.217; TVL $11824.34; fee/TVL entry 0.0432%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -519; harga snapshot 0.000015994985 SOL/token; range [-572, -519] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999974 SOL + 0.000000000 token; withdraw 0.119787510 SOL + 13.332857000 token. Porsi token pada mark withdrawal 0.18%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.06% < 5.0% after 56.5m)
5. **Jalur yang teramati:** 48 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 0.79%.
6. **Fee → drift → divergence → hasil:** Fee +0.000002739 SOL (0.0023% modal), divergence principal vs HOLD SOL -0.000000898 SOL, PnL LP +0.000001841 SOL (0.0015%). Gas transaksi posisi yang terhubung 0.000030000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · MCAT-SOL · 3fwrHzGbTu1rML2umfhq4LkZnXyyPe3PTVeYN1BYuLZL

2026-09-19T04:27:29+07:00 → 2026-09-19T04:53:49+07:00 · 26.33 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 7.518; TVL $57370.85; fee/TVL entry 3.3890%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -375; harga snapshot 0.000009481194 SOL/token; range [-410, -375] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.098751037 SOL + 136.169040000 token. Porsi token pada mark withdrawal 1.24%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -16.5% <= -3.0% with PnL +2.14%, peak +2.14%) — realizing before floor gap-through
5. **Jalur yang teramati:** 9 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 14.91%.
6. **Fee → drift → divergence → hasil:** Fee +0.002280174 SOL (2.2802% modal), divergence principal vs HOLD SOL -0.000005129 SOL, PnL LP +0.002275044 SOL (2.2750%). Gas transaksi posisi yang terhubung 0.000030000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · SOLCAT-SOL · DoRnXvpPwutAGm69jyXn94bhCfdeh99XWN6TexrbVXfv

2026-09-19T04:52:36+07:00 → 2026-09-19T05:12:37+07:00 · 20.02 menit · pool `HGF6LLmPghmtE9cuCEemeZiz8pv2G5G5HNJbnfECfmKf`.

1. **Market → volatilitas → depth:** Volatility feed 6.119; TVL $14754.21; fee/TVL entry 1.1344%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -487; harga snapshot 0.000007861238 SOL/token; range [-531, -487] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.077681148 SOL + 3245.737775000 token. Porsi token pada mark withdrawal 21.21%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Sustained downtrend dump (1h -29.5% <= -5.0% & PnL -4.01% <= -2.5%) — risk floor
5. **Jalur yang teramati:** 24 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 18.86%.
6. **Fee → drift → divergence → hasil:** Fee +0.004799285 SOL (4.7993% modal), divergence principal vs HOLD SOL -0.001407729 SOL, PnL LP +0.003391556 SOL (3.3916%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · FLAME-SOL · 9Yvuyj23EFiccwvRAA5MxcsCgZNFMqfUDH6A9S2L6pUK

2026-09-19T05:04:34+07:00 → 2026-09-19T05:14:37+07:00 · 10.05 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 1.237; TVL $34745.44; fee/TVL entry 0.1566%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -665; harga snapshot 0.000004997423 SOL/token; range [-718, -665] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999036 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 6.9m (limit 5m)
5. **Jalur yang teramati:** 8 sampel; in-range teramati 24.1%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000833 SOL (0.0008% modal), divergence principal vs HOLD SOL -0.000000939 SOL, PnL LP -0.000000106 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000106; setelah gas terhubung -0.000020106.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · STONK10-SOL · 97Vts2ze9Vy4gzEyMm7oh2HD6BrPYEipPoQL8vot426X

2026-09-19T05:30:52+07:00 → 2026-09-19T07:33:22+07:00 · 122.50 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 3.506; TVL $14706.54; fee/TVL entry 0.0513%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -499; harga snapshot 0.000018758343 SOL/token; range [-552, -499] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999974 SOL + 0.000000000 token; withdraw 0.119999740 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 30.8m (limit 30m); hold journal: OOR 13m: m5 +4.60% h1 +15.79% (Meteora pool A8Ui81JD) - rallying back toward range, expect re-entry before 30m OOR limit
5. **Jalur yang teramati:** 151 sampel; in-range teramati 75.3%; maksimum penurunan teramati sejak snapshot 11.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.001196355 SOL (0.9970% modal), divergence principal vs HOLD SOL -0.000000234 SOL, PnL LP +0.001196121 SOL (0.9968%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · world-SOL · DHpPqcCPUvL8yz3y9pC7w5iiBy6ta1mkbu39gERUVGd5

2026-09-19T05:48:48+07:00 → 2026-09-19T06:50:31+07:00 · 61.72 menit · pool `R88hawBDy3CTiX7F7woKgMJAXbed7f5H38qR4FB2eav`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $10653.19; fee/TVL entry 0.4755%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -571; harga snapshot 0.000003407968 SOL/token; range [-615, -571] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.092463544 SOL + 2378.832664000 token. Porsi token pada mark withdrawal 7.22%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 4.91% < 5.0% after 60.6m)
5. **Jalur yang teramati:** 66 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 11.26%.
6. **Fee → drift → divergence → hasil:** Fee +0.000208989 SOL (0.2090% modal), divergence principal vs HOLD SOL -0.000341896 SOL, PnL LP -0.000132907 SOL (-0.1329%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000386452; setelah gas terhubung -0.000413135. Swap cocok unik, jeda 1104 detik; selisih terhadap mark token -0.000253545 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · MCAT-SOL · 2gJjyLmcdmDyX86G1kt1WUm6QSMTXUriKXDoGYKHxEse

2026-09-19T07:19:56+07:00 → 2026-09-19T07:53:28+07:00 · 33.53 menit · pool `HHgxEaEw1Wq9pSmMXp1dmf7vpDq7CegXbHVwtfYwcZRr`.

1. **Market → volatilitas → depth:** Volatility feed 3.076; TVL $11191.78; fee/TVL entry 0.4108%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -503; harga snapshot 0.000006704231 SOL/token; range [-547, -503] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999980 SOL + 0.000000000 token; withdraw 0.039898985 SOL + 11306.319436000 token. Porsi token pada mark withdrawal 57.28%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-23.7% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 43 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 8.57%.
6. **Fee → drift → divergence → hasil:** Fee +0.002474207 SOL (2.4742% modal), divergence principal vs HOLD SOL -0.006592571 SOL, PnL LP -0.004118364 SOL (-4.1184%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · Prism-SOL · CfHiz3Aam8fqJSgPKJM4CAtyWeFftJaCSEds8ffeW64N

2026-09-19T07:51:02+07:00 → 2026-09-19T08:01:37+07:00 · 10.58 menit · pool `9xCHQgVQ3DSDcHu8h2A4njrsWB1J7JceZpEqFLXdmh8f`.

1. **Market → volatilitas → depth:** Volatility feed 9.327; TVL $40803.66; fee/TVL entry 8.9547%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -486; harga snapshot 0.000007939851 SOL/token; range [-530, -486] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.080564255 SOL + 2771.773337000 token. Porsi token pada mark withdrawal 18.44%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-20.2% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 11 sampel; in-range teramati 69.4%; maksimum penurunan teramati sejak snapshot 15.56%.
6. **Fee → drift → divergence → hasil:** Fee +0.001276843 SOL (1.2768% modal), divergence principal vs HOLD SOL -0.001219265 SOL, PnL LP +0.000057578 SOL (0.0576%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000806491; setelah gas terhubung +0.000727157. Swap cocok unik, jeda 43 detik; selisih terhadap mark token +0.000748913 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · baton-SOL · 5phL4jvD2odmzbqYHXJzcFfBPdupufUVdXHqeRXwV1or

2026-09-19T08:31:48+07:00 → 2026-09-19T09:02:53+07:00 · 31.08 menit · pool `BN7CfsGm6Vq9w8NibLZXRGW2tp5y2axwXuLAs85NGakf`.

1. **Market → volatilitas → depth:** Volatility feed 1.579; TVL $138383.49; fee/TVL entry 0.0613%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -507; harga snapshot 0.000017599901 SOL/token; range [-560, -507] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999974 SOL + 0.000000000 token; withdraw 0.119999524 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.01% < 5.0% after 30.1m)
5. **Jalur yang teramati:** 47 sampel; in-range teramati 6.2%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000327 SOL (0.0003% modal), divergence principal vs HOLD SOL -0.000000450 SOL, PnL LP -0.000000123 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000123; setelah gas terhubung -0.000020123.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · OTC-SOL · GEDyJciZaFhbjJSzv8nSg97yxcxg7iHiVFBHi6bApNVX

2026-09-19T09:45:16+07:00 → 2026-09-19T09:47:18+07:00 · 2.03 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -272; harga snapshot tidak tersedia SOL/token; range [-316, -272] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119999799 SOL + 0.002033000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** journal unavailable
5. **Jalur yang teramati:** 0 sampel; in-range teramati tidak tersedia%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000046 SOL, PnL LP -0.000000046 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · PURPS-SOL · J8wFm5AHJjUV4r618LfvSAcD2VtiQwGgDk7LcjNwcmYK

2026-09-19T10:45:55+07:00 → 2026-09-19T11:17:03+07:00 · 31.13 menit · pool `5LjukK9FDhTo51wp2zkKdAgSk7yg4khr1v9d3HwKFsQJ`.

1. **Market → volatilitas → depth:** Volatility feed 2.111; TVL $17981.85; fee/TVL entry 0.1412%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -451; harga snapshot 0.000011247615 SOL/token; range [-495, -451] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119999525 SOL + 0.000735000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.01% < 5.0% after 30.1m)
5. **Jalur yang teramati:** 46 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000352 SOL (0.0003% modal), divergence principal vs HOLD SOL -0.000000448 SOL, PnL LP -0.000000096 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · BIDDY-SOL · BrNAsRzrYhSCw7gtUjbQnyohmAL5VHvCXSpHautWT4cf

2026-09-19T14:53:50+07:00 → 2026-09-19T15:21:19+07:00 · 27.48 menit · pool `HsEApMAQdfECUtxuHxPpDgf7afsm4zKyepkAepCkJMKV`.

1. **Market → volatilitas → depth:** Volatility feed 4.409; TVL $15676.74; fee/TVL entry 0.8396%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -606; harga snapshot 0.000002405733 SOL/token; range [-650, -606] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.058398676 SOL + 31565.328942000 token. Porsi token pada mark withdrawal 48.61%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -16.5% <= -3.0% with PnL -1.83% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 41 sampel; in-range teramati 85.0%; maksimum penurunan teramati sejak snapshot 22.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.003575559 SOL (2.9796% modal), divergence principal vs HOLD SOL -0.006371457 SOL, PnL LP -0.002795898 SOL (-2.3299%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.015239694; setelah gas terhubung -0.015269001. Swap cocok unik, jeda 44 detik; selisih terhadap mark token -0.012443796 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · STONK10-SOL · 9Zp2YmoNPqyfTCw8WtJ9QEfe9pRaxrF6RDgVyQum4nnA

2026-09-19T15:25:48+07:00 → 2026-09-19T15:57:11+07:00 · 31.38 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 1.374; TVL $12679.60; fee/TVL entry 0.0742%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -465; harga snapshot 0.000024595325 SOL/token; range [-518, -465] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999974 SOL + 0.000000000 token; withdraw 0.119998428 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.05% < 5.0% after 30.0m)
5. **Jalur yang teramati:** 47 sampel; in-range teramati 8.4%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000001365 SOL (0.0011% modal), divergence principal vs HOLD SOL -0.000001546 SOL, PnL LP -0.000000181 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000181; setelah gas terhubung -0.000020181.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · Tilcayo-SOL · HrBAHkjyN1EcGkYuwQsfEkwuaS6urTwVX3FUVmzEfhpB

2026-09-19T16:16:25+07:00 → 2026-09-19T17:23:34+07:00 · 67.15 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 2.988; TVL $139046.18; fee/TVL entry 0.2940%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -411; harga snapshot 0.000016746165 SOL/token; range [-455, -411] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.120003963 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.6m (limit 5m)
5. **Jalur yang teramati:** 103 sampel; in-range teramati 92.3%; maksimum penurunan teramati sejak snapshot 15.56%.
6. **Fee → drift → divergence → hasil:** Fee +0.000930048 SOL (0.7750% modal), divergence principal vs HOLD SOL 0.000003982 SOL, PnL LP +0.000934030 SOL (0.7784%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · Tilcayo-SOL · bHLVEmMujx8KyqZiMMo1oVnwe5y476PSty7KstYNay3

2026-09-19T17:24:21+07:00 → 2026-09-19T18:16:43+07:00 · 52.37 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 2.988; TVL $139046.18; fee/TVL entry 0.2940%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -404; harga snapshot 0.000017954156 SOL/token; range [-424, -404] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999990 SOL + 0.000000000 token; withdraw 0.119991963 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m); recenter parent/root `HrBAHkjyN1EcGkYuwQsfEkwuaS6urTwVX3FUVmzEfhpB`
5. **Jalur yang teramati:** 77 sampel; in-range teramati 90.9%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.000836238 SOL (0.6969% modal), divergence principal vs HOLD SOL -0.000008027 SOL, PnL LP +0.000828211 SOL (0.6902%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · ELON-SOL · 9QVF8P3TPcZrgKTjEYTSALtDpH7QSE21Ct7hyUnNtZ2s

2026-09-19T19:44:09+07:00 → 2026-09-19T19:56:26+07:00 · 12.28 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 2.076; TVL $137650.95; fee/TVL entry 0.1621%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -502; harga snapshot 0.000018315251 SOL/token; range [-555, -502] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999974 SOL + 0.000000000 token; withdraw 0.119999321 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.4m (limit 5m)
5. **Jalur yang teramati:** 17 sampel; in-range teramati 54.3%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000575 SOL (0.0005% modal), divergence principal vs HOLD SOL -0.000000653 SOL, PnL LP -0.000000078 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000078; setelah gas terhubung -0.000020078.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · biketyson-SOL · 9J4Y94thpKN9YHkGUzfTgGFLHHApJRTg5jsjiCYgZVvL

2026-09-19T20:01:47+07:00 → 2026-09-19T20:32:45+07:00 · 30.97 menit · pool `ARqHS4dXM989rYBjDKzx249yqBXQtdrUioemyoGEnAnk`.

1. **Market → volatilitas → depth:** Volatility feed 1.149; TVL $45857.88; fee/TVL entry 0.0593%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -408; harga snapshot 0.000017253591 SOL/token; range [-452, -408] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119999970 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.00% < 5.0% after 30.1m)
5. **Jalur yang teramati:** 46 sampel; in-range teramati 89.3%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000009 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000011 SOL, PnL LP -0.000000002 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000002; setelah gas terhubung -0.000020002.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · FLAME-SOL · 5JwUx9aQnccMmXLEy5QUHh8QYu645RTwSL3UJp2ck8nu

2026-09-19T21:02:05+07:00 → 2026-09-19T23:04:02+07:00 · 121.95 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 3.613; TVL $20916.46; fee/TVL entry 0.6374%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -667; harga snapshot 0.000004918414 SOL/token; range [-720, -667] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999974 SOL + 0.000000000 token; withdraw 0.100846193 SOL + 4340.855905000 token. Porsi token pada mark withdrawal 15.19%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stale ticket re-pin (121m in range, peak +1.18% never armed the 1.2% ratchet, fee/TVL 15.9%)
5. **Jalur yang teramati:** 185 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 14.73%.
6. **Fee → drift → divergence → hasil:** Fee +0.001591413 SOL (1.3262% modal), divergence principal vs HOLD SOL -0.001093301 SOL, PnL LP +0.000498111 SOL (0.4151%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000080064; setelah gas terhubung +0.000015774. Swap cocok unik, jeda 45 detik; selisih terhadap mark token -0.000418047 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Batas umur/peak sendiri belum membuktikan biaya reposisi layak; snapshot fee pace posisi diperlukan. 

## azimuth · FLEX-SOL · HQvXjTgVj2CKVKMSDJKJ9A9ZPiFuX9Wx8YFqySY8PfMG

2026-09-19T23:12:03+07:00 → 2026-09-20T09:03:57+07:00 · 591.90 menit · pool `B3Me7MhVX5XPb4UHpnvYiac8KaTu26uxPzi36GksoUL9`.

1. **Market → volatilitas → depth:** Volatility feed 9.762; TVL $50718.08; fee/TVL entry 2.3175%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -377; harga snapshot 0.000023487786 SOL/token; range [-421, -377] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 6881.138063000 token. Porsi token pada mark withdrawal 100.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -11.5% <= -3.0% with PnL +24.39%, peak +24.39%) — realizing before floor gap-through
5. **Jalur yang teramati:** 14 sampel; in-range teramati 71.4%; maksimum penurunan teramati sejak snapshot 12.13%.
6. **Fee → drift → divergence → hasil:** Fee +0.060976012 SOL (50.8134% modal), divergence principal vs HOLD SOL -0.027422486 SOL, PnL LP +0.033553526 SOL (27.9613%). Gas transaksi posisi yang terhubung 0.000030000 SOL. Hasil dalam SOL sebelum gas +0.028107538; setelah gas terhubung +0.028072538. Swap cocok unik, jeda 44 detik; selisih terhadap mark token -0.005445988 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · UBI-SOL · 7eFvUBQRgUFzA8qKxpexskLb9AGmcWNyB1so3J96Ug7o

2026-09-20T09:02:48+07:00 → 2026-09-20T09:30:04+07:00 · 27.27 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 3.436; TVL $11494.95; fee/TVL entry 0.4102%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1131; harga snapshot 0.000012957650 SOL/token; range [-1175, -1131] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.081548628 SOL + 1606.804031726 token. Porsi token pada mark withdrawal 17.45%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -5.5% <= -3.0% with PnL -1.56% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 27 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 16.40%.
6. **Fee → drift → divergence → hasil:** Fee +0.000817832 SOL (0.8178% modal), divergence principal vs HOLD SOL -0.001217471 SOL, PnL LP -0.000399639 SOL (-0.3996%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000045033; setelah gas terhubung +0.000020033. Swap cocok unik, jeda 86 detik; selisih terhadap mark token +0.000444672 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · FLEX-SOL · DAhuyRMxMy9WZjP5wGiarCv25W2ZjJQALDb5E8uzMpWf

2026-09-20T09:05:01+07:00 → 2026-09-20T09:21:32+07:00 · 16.52 menit · pool `B3Me7MhVX5XPb4UHpnvYiac8KaTu26uxPzi36GksoUL9`.

1. **Market → volatilitas → depth:** Volatility feed 9.762; TVL $50718.08; fee/TVL entry 2.3175%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -433; harga snapshot 0.000013453806 SOL/token; range [-453, -433] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999990 SOL + 0.000000000 token; withdraw 0.119980234 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -3.3% <= -3.0% with PnL +1.99%, peak +2.34%) — realizing before floor gap-through; recenter parent/root `HQvXjTgVj2CKVKMSDJKJ9A9ZPiFuX9Wx8YFqySY8PfMG`
5. **Jalur yang teramati:** 16 sampel; in-range teramati 72.4%; maksimum penurunan teramati sejak snapshot 10.37%.
6. **Fee → drift → divergence → hasil:** Fee +0.002597391 SOL (2.1645% modal), divergence principal vs HOLD SOL -0.000019756 SOL, PnL LP +0.002577635 SOL (2.1480%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · JEANPHIL-SOL · Q1BbSpiBSmJ1a8iTcXMKHWgh23vC1an5RAeXzvumAvk

2026-09-20T10:05:27+07:00 → 2026-09-20T10:25:08+07:00 · 19.68 menit · pool `5u7PMsDxbaALbV9viti9Y4pEBVJqWSSp69uEsXGtiANq`.

1. **Market → volatilitas → depth:** Volatility feed 2.617; TVL $11171.83; fee/TVL entry 0.4677%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -311; harga snapshot 0.000045295260 SOL/token; range [-355, -311] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.127260827 SOL + 62.577605000 token. Porsi token pada mark withdrawal 2.06%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -3.3% <= -3.0% with PnL +1.26%, peak +1.44%) — realizing before floor gap-through
5. **Jalur yang teramati:** 26 sampel; in-range teramati 79.6%; maksimum penurunan teramati sejak snapshot 10.37%.
6. **Fee → drift → divergence → hasil:** Fee +0.001432181 SOL (1.1017% modal), divergence principal vs HOLD SOL -0.000068952 SOL, PnL LP +0.001363229 SOL (1.0486%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · LMAO!-SOL · 5mka16L4dHC4r3UoG6catrgiYWRtpEuysWnjM2nHGN9T

2026-09-20T10:17:40+07:00 → 2026-09-20T10:33:26+07:00 · 15.77 menit · pool `EWBCL4hKY6VdzZVcCY7pMPvRhG78koHY6nQnt8EW99Br`.

1. **Market → volatilitas → depth:** Volatility feed 1.509; TVL $20207.27; fee/TVL entry 0.6718%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -386; harga snapshot 0.000021475818 SOL/token; range [-430, -386] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099998136 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 17 sampel; in-range teramati 63.6%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000001625 SOL (0.0016% modal), divergence principal vs HOLD SOL -0.000001843 SOL, PnL LP -0.000000218 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000218; setelah gas terhubung -0.000020218.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · FLAME-SOL · Hcdb74FcBdrZKZPMfzjxvpd5Z6yw8TVeYCJ99wgTnKUb

2026-09-20T10:35:18+07:00 → 2026-09-20T10:45:09+07:00 · 9.85 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 3.906; TVL $14815.81; fee/TVL entry 0.4144%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -706; harga snapshot tidak tersedia SOL/token; range [-759, -706] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999974 SOL + 0.000000000 token; withdraw 0.129999540 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 13 sampel; in-range teramati 38.3%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000389 SOL (0.0003% modal), divergence principal vs HOLD SOL -0.000000434 SOL, PnL LP -0.000000045 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000045; setelah gas terhubung -0.000020045.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · MINI-SOL · H3u3NdBoNx4heTgp8bdJUbEdARUzVn85j27TdKkqt77c

2026-09-20T10:44:48+07:00 → 2026-09-20T11:16:34+07:00 · 31.77 menit · pool `64BSmy7BESiHnWYzLdPso6FuXymh7H8jTkaiyfbBg1YD`.

1. **Market → volatilitas → depth:** Volatility feed 17.568; TVL $66355.93; fee/TVL entry 0.3847%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -263; harga snapshot 0.000038115938 SOL/token; range [-298, -263] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.098778264 SOL + 32.611463000 token. Porsi token pada mark withdrawal 1.20%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 2.76% < 5.0% after 30.5m)
5. **Jalur yang teramati:** 32 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 3.66%.
6. **Fee → drift → divergence → hasil:** Fee +0.000059469 SOL (0.0595% modal), divergence principal vs HOLD SOL -0.000024174 SOL, PnL LP +0.000035295 SOL (0.0353%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · WOJAK-SOL · 5ZefgyTnpPZxPnG89o1J8QabMAjYGSbq5pufCvuwoTw3

2026-09-20T10:49:50+07:00 → 2026-09-20T13:51:30+07:00 · 181.67 menit · pool `2RX1ZogEMsjv1YjMF3m5U1DN7gVCtSLaQHs27F17ECve`.

1. **Market → volatilitas → depth:** Volatility feed 1.722; TVL $53817.32; fee/TVL entry 0.1728%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -482; harga snapshot 0.000021479468 SOL/token; range [-535, -482] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.096871706 SOL + 152.104093000 token. Porsi token pada mark withdrawal 3.04%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stale ticket re-pin (180m in range, peak +0.95% never armed the 1.2% ratchet, fee/TVL 9.9%)
5. **Jalur yang teramati:** 234 sampel; in-range teramati 99.5%; maksimum penurunan teramati sejak snapshot 13.36%.
6. **Fee → drift → divergence → hasil:** Fee +0.001255124 SOL (1.2551% modal), divergence principal vs HOLD SOL -0.000087246 SOL, PnL LP +0.001167877 SOL (1.1679%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Batas umur/peak sendiri belum membuktikan biaya reposisi layak; snapshot fee pace posisi diperlukan. 

## azimuth · JEANPHIL-SOL · D8hZBVwWCNNrLZEQZLtsPk71mEpLzJuQtpYWYQEd9ZmV

2026-09-20T11:35:00+07:00 → 2026-09-20T11:51:01+07:00 · 16.02 menit · pool `5u7PMsDxbaALbV9viti9Y4pEBVJqWSSp69uEsXGtiANq`.

1. **Market → volatilitas → depth:** Volatility feed 3.168; TVL $77233.68; fee/TVL entry 0.7865%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -338; harga snapshot 0.000034623874 SOL/token; range [-382, -338] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999979 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 16 sampel; in-range teramati 66.1%; maksimum penurunan teramati sejak snapshot 1.97%.
6. **Fee → drift → divergence → hasil:** Fee +0.000025421 SOL (0.0254% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000025421 SOL (0.0254%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · STONK10-SOL · 3PPL6MoCjmonHcCNgKzJU989SqDbDWoRAacYtYPueeBa

2026-09-20T12:28:48+07:00 → 2026-09-20T12:29:24+07:00 · 0.60 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 1.248; TVL $14229.32; fee/TVL entry 0.0528%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -509; harga snapshot 0.000017321646 SOL/token; range [-562, -509] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099958359 SOL + 2.363699000 token. Porsi token pada mark withdrawal 0.04%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** journal unavailable
5. **Jalur yang teramati:** 0 sampel; in-range teramati tidak tersedia%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000104 SOL (0.0001% modal), divergence principal vs HOLD SOL -0.000000673 SOL, PnL LP -0.000000569 SOL (-0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · FLEX-SOL · 4oaSfUSXrsuMDoQjX7jj4EKRdWPx3YnBG15FnaxwmHuQ

2026-09-20T12:36:26+07:00 → 2026-09-20T12:51:10+07:00 · 14.73 menit · pool `B3Me7MhVX5XPb4UHpnvYiac8KaTu26uxPzi36GksoUL9`.

1. **Market → volatilitas → depth:** Volatility feed 1.417; TVL $29330.50; fee/TVL entry 0.2299%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -468; harga snapshot 0.000009497232 SOL/token; range [-512, -468] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099998001 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.3m (limit 5m)
5. **Jalur yang teramati:** 12 sampel; in-range teramati 9.5%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000001744 SOL (0.0017% modal), divergence principal vs HOLD SOL -0.000001978 SOL, PnL LP -0.000000234 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000025000 SOL. Hasil dalam SOL sebelum gas -0.000000234; setelah gas terhubung -0.000025234.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · JEANPHIL-SOL · 9pTYfLEMcYgNV5bt1MM8nrhWwjeDoEi2GAxonaEH6tKb

2026-09-20T13:33:25+07:00 → 2026-09-20T13:41:55+07:00 · 8.50 menit · pool `5u7PMsDxbaALbV9viti9Y4pEBVJqWSSp69uEsXGtiANq`.

1. **Market → volatilitas → depth:** Volatility feed 1.536; TVL $63938.32; fee/TVL entry 0.3676%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -351; harga snapshot 0.000030422703 SOL/token; range [-395, -351] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999979 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.6m (limit 5m)
5. **Jalur yang teramati:** 8 sampel; in-range teramati 27.2%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000024 SOL (0.0000% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000024 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · TIPPED-SOL · f3fNChSLqhTXs8hphUju7RJ2WvNWfQZBVbVFWcpfdGo

2026-09-20T13:47:01+07:00 → 2026-09-20T13:59:21+07:00 · 12.33 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 2.484; TVL $21731.53; fee/TVL entry 0.3055%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -580; harga snapshot 0.000003116041 SOL/token; range [-624, -580] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999344 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m); hold journal: dexscreener pool 66RWZy7x: m5 +9.12% h1 +3.31% (liq 23.7k) - OOR 3m with m5>+2%, price rising back toward range, expect re-entry
5. **Jalur yang teramati:** 13 sampel; in-range teramati 52.0%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000008916 SOL (0.0089% modal), divergence principal vs HOLD SOL -0.000000635 SOL, PnL LP +0.000008281 SOL (0.0083%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · TIPPED-SOL · GYodkrHiMKYsBfGYLz3Aebb5gUcPyV4TfTPHCmXVj7Ea

2026-09-20T14:00:06+07:00 → 2026-09-20T14:06:52+07:00 · 6.77 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 2.484; TVL $21731.53; fee/TVL entry 0.3055%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -581; harga snapshot 0.000003085189 SOL/token; range [-601, -581] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.099994594 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m); recenter parent/root `f3fNChSLqhTXs8hphUju7RJ2WvNWfQZBVbVFWcpfdGo`
5. **Jalur yang teramati:** 9 sampel; in-range teramati 0.0%; maksimum penurunan teramati sejak snapshot -2.01%.
6. **Fee → drift → divergence → hasil:** Fee +0.000004798 SOL (0.0048% modal), divergence principal vs HOLD SOL -0.000005396 SOL, PnL LP -0.000000598 SOL (-0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000598; setelah gas terhubung -0.000020598.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · baton-SOL · FLx3cS1JAAqH1nYN9at6NHcwrqyqdVeY6ejRR6MuPz94

2026-09-20T14:13:19+07:00 → 2026-09-20T14:44:02+07:00 · 30.72 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 2.861; TVL $24644.22; fee/TVL entry 0.2812%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -386; harga snapshot 0.000021475818 SOL/token; range [-430, -386] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.129995990 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.6m (limit 5m)
5. **Jalur yang teramati:** 46 sampel; in-range teramati 83.0%; maksimum penurunan teramati sejak snapshot 6.73%.
6. **Fee → drift → divergence → hasil:** Fee +0.000253150 SOL (0.1947% modal), divergence principal vs HOLD SOL -0.000003987 SOL, PnL LP +0.000249163 SOL (0.1917%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000249163; setelah gas terhubung +0.000229163.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · baton-SOL · 6MW5WMfekTwfeaYu3TzVyMXPG7sacj2aPC7VYp8smcQN

2026-09-20T14:44:48+07:00 → 2026-09-20T14:51:14+07:00 · 6.43 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 2.861; TVL $24644.22; fee/TVL entry 0.2812%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -380; harga snapshot 0.000022797014 SOL/token; range [-400, -380] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999990 SOL + 0.000000000 token; withdraw 0.129998080 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.0m (limit 5m); recenter parent/root `FLx3cS1JAAqH1nYN9at6NHcwrqyqdVeY6ejRR6MuPz94`
5. **Jalur yang teramati:** 7 sampel; in-range teramati 0.0%; maksimum penurunan teramati sejak snapshot -1.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000001716 SOL (0.0013% modal), divergence principal vs HOLD SOL -0.000001910 SOL, PnL LP -0.000000194 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000194; setelah gas terhubung -0.000020194.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · CHILLHOUSE-SOL · 6EYgnDBNuG3SUhzFusyKVgB7qi9MPDFA4X8nNDXG97Tq

2026-09-20T15:42:46+07:00 → 2026-09-20T16:05:28+07:00 · 22.70 menit · pool `Fx4jn8KxoShhfsGJ8heuFh2JiwhWYCodaPiZTt7W4DBx`.

1. **Market → volatilitas → depth:** Volatility feed 1.541; TVL $14548.89; fee/TVL entry 0.1724%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -402; harga snapshot 0.000018315034 SOL/token; range [-446, -402] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.129999933 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.6m (limit 5m)
5. **Jalur yang teramati:** 33 sampel; in-range teramati 76.1%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000024 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000044 SOL, PnL LP -0.000000020 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000020; setelah gas terhubung -0.000020020.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · CHILLHOUSE-SOL · 5uSWVZxpkUMsuuQtbLDuCw82wHhBERHBNARuZ6vP9Kbb

2026-09-20T16:06:14+07:00 → 2026-09-20T17:05:19+07:00 · 59.08 menit · pool `Fx4jn8KxoShhfsGJ8heuFh2JiwhWYCodaPiZTt7W4DBx`.

1. **Market → volatilitas → depth:** Volatility feed 1.541; TVL $14548.89; fee/TVL entry 0.1724%; base fee pool 1.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -401; harga snapshot 0.000018498185 SOL/token; range [-421, -401] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999990 SOL + 0.000000000 token; withdraw 0.129437221 SOL + 30.115229000 token. Porsi token pada mark withdrawal 0.43%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.00% < 5.0% after 60.1m); recenter parent/root `6EYgnDBNuG3SUhzFusyKVgB7qi9MPDFA4X8nNDXG97Tq`
5. **Jalur yang teramati:** 78 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000003 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000005692 SOL, PnL LP -0.000005689 SOL (-0.0044%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · TIPPED-SOL · AtdjiFJMf4yLpXCY7w8hFUzBnsPmyirsbW5ZeQGiXAdn

2026-09-20T16:43:07+07:00 → 2026-09-20T16:51:50+07:00 · 8.72 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 2.432; TVL $17020.63; fee/TVL entry 0.5134%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -587; harga snapshot 0.000002906388 SOL/token; range [-631, -587] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999128 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.3m (limit 5m)
5. **Jalur yang teramati:** 8 sampel; in-range teramati 28.3%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000759 SOL (0.0008% modal), divergence principal vs HOLD SOL -0.000000851 SOL, PnL LP -0.000000092 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000092; setelah gas terhubung -0.000020092.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · TIPPED-SOL · 31UUoVdc5zHe4BoM5MsDMerFS1py6drBvfe8PrDCWX3n

2026-09-20T16:52:36+07:00 → 2026-09-20T17:35:38+07:00 · 43.03 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 2.432; TVL $17020.63; fee/TVL entry 0.5134%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -587; harga snapshot 0.000002906388 SOL/token; range [-607, -587] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999990 SOL + 0.000000000 token; withdraw 0.100000007 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m); recenter parent/root `AtdjiFJMf4yLpXCY7w8hFUzBnsPmyirsbW5ZeQGiXAdn`
5. **Jalur yang teramati:** 57 sampel; in-range teramati 88.7%; maksimum penurunan teramati sejak snapshot 9.47%.
6. **Fee → drift → divergence → hasil:** Fee +0.001262022 SOL (1.2620% modal), divergence principal vs HOLD SOL 0.000000017 SOL, PnL LP +0.001262039 SOL (1.2620%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · Tilcayo-SOL · EgrvPhf7HhxnZtZknVacXSxtKM5iLxmsozSqa1jnvfPo

2026-09-20T18:11:38+07:00 → 2026-09-20T19:12:34+07:00 · 60.93 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 2.047; TVL $71169.41; fee/TVL entry 0.1980%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -448; harga snapshot 0.000011588428 SOL/token; range [-492, -448] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.129996856 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 66 sampel; in-range teramati 92.1%; maksimum penurunan teramati sejak snapshot 10.37%.
6. **Fee → drift → divergence → hasil:** Fee +0.000512524 SOL (0.3942% modal), divergence principal vs HOLD SOL -0.000003121 SOL, PnL LP +0.000509403 SOL (0.3918%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · SCRIBE-SOL · 6R5SXYr5s75rrYSJ3T4n3M2LNaoxAi5Bc38vWXJP356Q

2026-09-20T18:17:50+07:00 → 2026-09-20T18:21:26+07:00 · 3.60 menit · pool `BZJTiubWLruAhoBxCTgU3uVdvXFztsr4cKG7SZcxoQdC`.

1. **Market → volatilitas → depth:** Volatility feed 6.250; TVL $11006.29; fee/TVL entry 1.0108%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -506; harga snapshot 0.000006507061 SOL/token; range [-550, -506] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.045785907 SOL + 10333.804166000 token. Porsi token pada mark withdrawal 51.40%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -13.5% <= -3.0% with PnL -1.51% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 3 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 11.26%.
6. **Fee → drift → divergence → hasil:** Fee +0.001758620 SOL (1.7586% modal), divergence principal vs HOLD SOL -0.005792403 SOL, PnL LP -0.004033782 SOL (-4.0338%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.002370260; setelah gas terhubung -0.002395260. Swap cocok unik, jeda 85 detik; selisih terhadap mark token +0.001663522 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · baton-SOL · qmbs7Nv2d2t6282WaGLwzyZxjdVXsCqCuzy5tyUYdvo

2026-09-20T18:23:37+07:00 → 2026-09-20T19:15:35+07:00 · 51.97 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 2.318; TVL $26541.84; fee/TVL entry 0.2368%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -352; harga snapshot 0.000030121488 SOL/token; range [-396, -352] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.100001082 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 7.8m (limit 5m)
5. **Jalur yang teramati:** 53 sampel; in-range teramati 92.0%; maksimum penurunan teramati sejak snapshot 14.72%.
6. **Fee → drift → divergence → hasil:** Fee +0.000884919 SOL (0.8849% modal), divergence principal vs HOLD SOL 0.000001103 SOL, PnL LP +0.000886022 SOL (0.8860%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000886022; setelah gas terhubung +0.000866022.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · OTC-SOL · 5Qs9m7abpy9noZWEgUEH1zVuKGzmqkXPTLQ8qRgAAqf5

2026-09-20T20:32:19+07:00 → 2026-09-20T21:03:57+07:00 · 31.63 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 0.704; TVL $18924.70; fee/TVL entry 0.0497%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -287; harga snapshot 0.000057512961 SOL/token; range [-331, -287] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.129999930 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.00% < 5.0% after 30.3m)
5. **Jalur yang teramati:** 40 sampel; in-range teramati 57.0%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000041 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000047 SOL, PnL LP -0.000000006 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000006; setelah gas terhubung -0.000020006.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · JEANPHIL-SOL · GRvBabWfGnmSgNpKDjvYv2qjSGZywdM81Njz9pgLEVmv

2026-09-20T20:46:36+07:00 → 2026-09-20T21:11:01+07:00 · 24.42 menit · pool `CzVhSwrx9VQmBJTP2BdHgWiRPEcbWBNEAmPCPH1BMJTS`.

1. **Market → volatilitas → depth:** Volatility feed 3.188; TVL $11568.50; fee/TVL entry 0.3099%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -280; harga snapshot 0.000061661678 SOL/token; range [-324, -280] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099999980 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 27 sampel; in-range teramati 77.6%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000009632 SOL (0.0096% modal), divergence principal vs HOLD SOL 0.000000001 SOL, PnL LP +0.000009633 SOL (0.0096%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · CHILLHOUSE-SOL · FQkn6MsqqmijaR6WuCbYEwnPofVDe2GoPL9Jo8fq9aJ4

2026-09-20T22:44:37+07:00 → 2026-09-20T23:46:08+07:00 · 61.52 menit · pool `Fx4jn8KxoShhfsGJ8heuFh2JiwhWYCodaPiZTt7W4DBx`.

1. **Market → volatilitas → depth:** Volatility feed 1.990; TVL $14862.56; fee/TVL entry 0.2134%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -393; harga snapshot 0.000020030883 SOL/token; range [-437, -393] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.128758640 SOL + 63.111733000 token. Porsi token pada mark withdrawal 0.94%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 1.32% < 5.0% after 60.6m)
5. **Jalur yang teramati:** 87 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 4.85%.
6. **Fee → drift → divergence → hasil:** Fee +0.000071259 SOL (0.0548% modal), divergence principal vs HOLD SOL -0.000014333 SOL, PnL LP +0.000056926 SOL (0.0438%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · FLAME-SOL · 36bvyv1LjdjMKM8aR48ebNjZJ9LCc6U8A1VSybborJpE

2026-09-20T23:10:35+07:00 → 2026-09-20T23:20:39+07:00 · 10.07 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 2.465; TVL $15524.05; fee/TVL entry 0.3277%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -670; harga snapshot 0.000004802236 SOL/token; range [-723, -670] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999975 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 6.0m (limit 5m)
5. **Jalur yang teramati:** 9 sampel; in-range teramati 36.6%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000117228 SOL (0.1172% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000117228 SOL (0.1172%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · baton-SOL · EBvE3rLZXF5xZXmJKkLpkaWmiTTckUqxbSbjkrHzetaA

2026-09-20T23:49:45+07:00 → 2026-09-21T02:07:38+07:00 · 137.88 menit · pool `BN7CfsGm6Vq9w8NibLZXRGW2tp5y2axwXuLAs85NGakf`.

1. **Market → volatilitas → depth:** Volatility feed 2.171; TVL $107722.70; fee/TVL entry 0.0631%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -441; harga snapshot 0.000029778673 SOL/token; range [-494, -441] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999974 SOL + 0.000000000 token; withdraw 0.078103768 SOL + 2080.370818000 token. Porsi token pada mark withdrawal 37.88%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Sustained downtrend dump (1h -10.8% <= -5.0% & PnL -2.67% <= -2.5%) — risk floor
5. **Jalur yang teramati:** 169 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 23.12%.
6. **Fee → drift → divergence → hasil:** Fee +0.002919324 SOL (2.2456% modal), divergence principal vs HOLD SOL -0.004269721 SOL, PnL LP -0.001350396 SOL (-1.0388%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.001639895; setelah gas terhubung -0.001764895. Swap cocok unik, jeda 44 detik; selisih terhadap mark token -0.000289499 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · LMAO!-SOL · 8Kh5935dy2S5Z6BficB2EfN2nLuNi9cskbB3XBFfeD7k

2026-09-21T00:10:53+07:00 → 2026-09-21T01:14:41+07:00 · 63.80 menit · pool `8k61EzwUzjdCZqKqGWTW2ygjmAdWGV6VZNPpDNkmo9dd`.

1. **Market → volatilitas → depth:** Volatility feed 0.890; TVL $11142.94; fee/TVL entry 0.2771%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -385; harga snapshot 0.000021690576 SOL/token; range [-429, -385] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099863226 SOL + 6.285819000 token. Porsi token pada mark withdrawal 0.13%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.20% < 5.0% after 63.2m)
5. **Jalur yang teramati:** 66 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000008944 SOL (0.0089% modal), divergence principal vs HOLD SOL -0.000001760 SOL, PnL LP +0.000007184 SOL (0.0072%). Gas transaksi posisi yang terhubung 0.000030000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · TYLER-SOL · H5BKrq8j9sQYAay5dtDED1CNjYZodE6X4h9jCb2M3Aut

2026-09-21T01:17:34+07:00 → 2026-09-21T01:23:59+07:00 · 6.42 menit · pool `7U1LVkLoSjAganjRv39d3GYdMBqqc2FcVcwvKN7LfmZG`.

1. **Market → volatilitas → depth:** Volatility feed 11.165; TVL $37284.94; fee/TVL entry 0.0924%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -385; harga snapshot 0.000008373610 SOL/token; range [-420, -385] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999983 SOL + 0.000000000 token; withdraw 0.099196000 SOL + 97.471598000 token. Porsi token pada mark withdrawal 0.80%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** RUG velocity dump (-24.4% in 5m <= -20%) — emergency exit before it goes to zero
5. **Jalur yang teramati:** 6 sampel; in-range teramati 19.7%; maksimum penurunan teramati sejak snapshot 4.85%.
6. **Fee → drift → divergence → hasil:** Fee +0.000210340 SOL (0.2103% modal), divergence principal vs HOLD SOL -0.000007822 SOL, PnL LP +0.000202518 SOL (0.2025%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · fone-SOL · Er6gjvNiV54unS6124imryg1Hvz2Z5BWBPFxf9yvyNX

2026-09-21T01:50:30+07:00 → 2026-09-21T03:30:36+07:00 · 100.10 menit · pool `fAeDy2q7ZjZZZFt6Q1FtbHaCU5dtLEPmYcwcwfAexNA`.

1. **Market → volatilitas → depth:** Volatility feed 4.741; TVL $83273.67; fee/TVL entry 0.0495%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -301; harga snapshot 0.000050034146 SOL/token; range [-345, -301] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.099712101 SOL + 5.815802000 token. Porsi token pada mark withdrawal 0.29%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 1.04% < 5.0% after 99.4m); hold journal: low-yield band; m5 +2.66% h1 +6.81% (DLMM fone-SOL pair), fee/TVL 1.86% >= 0.5, in range pnl +0.57% - rising m5 with h1 positive, expect bounce to keep position in range and resume fee accrual
5. **Jalur yang teramati:** 38 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.000071004 SOL (0.0710% modal), divergence principal vs HOLD SOL 0.000000230 SOL, PnL LP +0.000071233 SOL (0.0712%). Gas transaksi posisi yang terhubung 0.000035000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · STONK10-SOL · Cnc7QLbu8mg9VDJhVE9txzuh88mXHoFFPot46MP412y3

2026-09-21T03:26:56+07:00 → 2026-09-21T03:58:09+07:00 · 31.22 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 3.171; TVL $14157.90; fee/TVL entry 0.1080%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -428; harga snapshot tidak tersedia SOL/token; range [-481, -428] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999971 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 4.62% < 5.0% after 30.2m)
5. **Jalur yang teramati:** 41 sampel; in-range teramati 63.7%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000100056 SOL (0.1001% modal), divergence principal vs HOLD SOL -0.000000004 SOL, PnL LP +0.000100052 SOL (0.1001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · Stamp-SOL · GGzcoahTFcPWE7B5VaSSAze8PZUf5MWTWNWNFHkMzqhP

2026-09-21T05:03:12+07:00 → 2026-09-21T05:18:03+07:00 · 14.85 menit · pool `F6H5zJeZEUDnYPtcXM3LwQkkcsg1XHLvEJGpB9Mizu1E`.

1. **Market → volatilitas → depth:** Volatility feed 4.837; TVL $100126.62; fee/TVL entry 4.3953%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -343; harga snapshot 0.000032943428 SOL/token; range [-387, -343] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999978 SOL + 0.000000000 token; withdraw 0.130002269 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 22 sampel; in-range teramati 57.7%; maksimum penurunan teramati sejak snapshot 9.47%.
6. **Fee → drift → divergence → hasil:** Fee +0.001097071 SOL (0.8439% modal), divergence principal vs HOLD SOL 0.000002291 SOL, PnL LP +0.001099362 SOL (0.8457%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · Stamp-SOL · Hjd9qwmaKkVajwKqYjLXPazBuDX85DvSbCW8Yabext9w

2026-09-21T05:18:49+07:00 → 2026-09-21T05:27:26+07:00 · 8.62 menit · pool `F6H5zJeZEUDnYPtcXM3LwQkkcsg1XHLvEJGpB9Mizu1E`.

1. **Market → volatilitas → depth:** Volatility feed 4.837; TVL $100126.62; fee/TVL entry 4.3953%; base fee pool 1.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -317; harga snapshot 0.000042670184 SOL/token; range [-337, -317] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999990 SOL + 0.000000000 token; withdraw 0.129994188 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m); recenter parent/root `GGzcoahTFcPWE7B5VaSSAze8PZUf5MWTWNWNFHkMzqhP`
5. **Jalur yang teramati:** 11 sampel; in-range teramati 26.4%; maksimum penurunan teramati sejak snapshot 5.80%.
6. **Fee → drift → divergence → hasil:** Fee +0.001123629 SOL (0.8643% modal), divergence principal vs HOLD SOL -0.000005802 SOL, PnL LP +0.001117827 SOL (0.8599%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · JEANPHIL-SOL · GSduza2k4j86bvxeemjfdHf5BHnRJUgXLPjnCjhVHkqP

2026-09-21T06:14:57+07:00 → 2026-09-21T07:16:45+07:00 · 61.80 menit · pool `CzVhSwrx9VQmBJTP2BdHgWiRPEcbWBNEAmPCPH1BMJTS`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $21333.12; fee/TVL entry 0.2040%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -324; harga snapshot 0.000039799251 SOL/token; range [-368, -324] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.129999977 SOL + 0.000000000 token; withdraw 0.098208719 SOL + 919.491441000 token. Porsi token pada mark withdrawal 23.04%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stale ticket re-pin (60m in range, peak +1.11% never armed the 1.2% ratchet, fee/TVL 32.1%)
5. **Jalur yang teramati:** 92 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 19.66%.
6. **Fee → drift → divergence → hasil:** Fee +0.001724953 SOL (1.3269% modal), divergence principal vs HOLD SOL -0.002390917 SOL, PnL LP -0.000665964 SOL (-0.5123%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Batas umur/peak sendiri belum membuktikan biaya reposisi layak; snapshot fee pace posisi diperlukan. 

## azimuth · ZEBRA-SOL · HoMdcA84baXgLDhsLkacPjasgdwcQxWiUFLymYaM7aYd

2026-09-21T07:11:48+07:00 → 2026-09-21T07:18:53+07:00 · 7.08 menit · pool `BjobrawhmMaLZArDayqAQJgztjCrfxkfWgD9w39R7ZPj`.

1. **Market → volatilitas → depth:** Volatility feed 12.291; TVL $56898.02; fee/TVL entry 12.7747%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -418; harga snapshot 0.000015619451 SOL/token; range [-462, -418] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.094846442 SOL + 350.093935000 token. Porsi token pada mark withdrawal 5.01%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit (5m -3.5% <= -3.0% with PnL +1.62%, peak +1.62%) — realizing before floor gap-through
5. **Jalur yang teramati:** 5 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 6.73%.
6. **Fee → drift → divergence → hasil:** Fee +0.001393586 SOL (1.3936% modal), divergence principal vs HOLD SOL -0.000153675 SOL, PnL LP +0.001239911 SOL (1.2399%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · TIPPED-SOL · 5235RdFQBdvogwgLA1GhFZuUQ6TKMewW5SXqy5YCL1pL

2026-09-21T07:35:05+07:00 → 2026-09-21T07:41:28+07:00 · 6.38 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 2.606; TVL $11837.01; fee/TVL entry 0.2234%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -605; harga snapshot tidak tersedia SOL/token; range [-649, -605] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119999937 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.5m (limit 5m)
5. **Jalur yang teramati:** 9 sampel; in-range teramati 0.0%; maksimum penurunan teramati sejak snapshot tidak tersedia%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000044 SOL, PnL LP -0.000000044 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas -0.000000044; setelah gas terhubung -0.000015044.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · MINI-SOL · Dk7YGhpQgTngFRn6fR4kisZoBhQWLHoUtq9A9AvfVZge

2026-09-21T07:54:24+07:00 → 2026-09-21T08:25:50+07:00 · 31.43 menit · pool `64BSmy7BESiHnWYzLdPso6FuXymh7H8jTkaiyfbBg1YD`.

1. **Market → volatilitas → depth:** Volatility feed 0.878; TVL $63191.72; fee/TVL entry 0.0898%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -296; harga snapshot 0.000025297090 SOL/token; range [-331, -296] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999982 SOL + 0.000000000 token; withdraw 0.119999947 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.00% < 5.0% after 30.2m)
5. **Jalur yang teramati:** 47 sampel; in-range teramati 25.1%; maksimum penurunan teramati sejak snapshot -0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000035 SOL, PnL LP -0.000000035 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas -0.000000035; setelah gas terhubung -0.000015035.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · BUTTHOLE-SOL · C7UUAwmwWvjwhswTTnWaZtGr3sX6iPmbEb1PvjEuTNok

2026-09-21T09:40:08+07:00 → 2026-09-21T10:11:34+07:00 · 31.43 menit · pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatilitas → depth:** Volatility feed 2.105; TVL $77410.71; fee/TVL entry 0.0465%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1376; harga snapshot 0.000017310428 SOL/token; range [-1429, -1376] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.097841429 SOL + 129.097805010 token. Porsi token pada mark withdrawal 2.11%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.65% < 5.0% after 30.5m)
5. **Jalur yang teramati:** 37 sampel; in-range teramati 97.9%; maksimum penurunan teramati sejak snapshot 1.58%.
6. **Fee → drift → divergence → hasil:** Fee +0.000030044 SOL (0.0300% modal), divergence principal vs HOLD SOL -0.000045043 SOL, PnL LP -0.000014999 SOL (-0.0150%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## azimuth · ZEBRA-SOL · FfEHaGvk2Gr4rKBiDSLLmkX7CvyKZ8efnTQJuvXCfwn1

2026-09-21T09:53:50+07:00 → 2026-09-21T10:08:58+07:00 · 15.13 menit · pool `BjobrawhmMaLZArDayqAQJgztjCrfxkfWgD9w39R7ZPj`.

1. **Market → volatilitas → depth:** Volatility feed 3.581; TVL $39322.88; fee/TVL entry 1.7550%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -499; harga snapshot 0.000006976450 SOL/token; range [-543, -499] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999979 SOL + 0.000000000 token; withdraw 0.061792377 SOL + 6549.406062000 token. Porsi token pada mark withdrawal 36.11%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Fast-out dump exit, underwater (5m -9.8% <= -3.0% with PnL -1.54% <= -1.5%) — cutting before the downtrend level
5. **Jalur yang teramati:** 15 sampel; in-range teramati 100.0%; maksimum penurunan teramati sejak snapshot 21.24%.
6. **Fee → drift → divergence → hasil:** Fee +0.001913040 SOL (1.9130% modal), divergence principal vs HOLD SOL -0.003280761 SOL, PnL LP -0.001367721 SOL (-1.3677%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Exit merespons risiko yang sudah teramati; profit bot lain pada entry berikutnya tidak membuktikan exit ini salah. 

## azimuth · ZEBRA-SOL · 4nx2W3WhePBr6y78Gu9AiXFSJR25EKb67tTqzhgdDgMK

2026-09-21T12:17:02+07:00 → 2026-09-21T12:35:19+07:00 · 18.28 menit · pool `BjobrawhmMaLZArDayqAQJgztjCrfxkfWgD9w39R7ZPj`.

1. **Market → volatilitas → depth:** Volatility feed 3.646; TVL $26341.80; fee/TVL entry 0.9511%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -560; harga snapshot 0.000003802163 SOL/token; range [-604, -560] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999981 SOL + 0.000000000 token; withdraw 0.119997471 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m)
5. **Jalur yang teramati:** 26 sampel; in-range teramati 60.5%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000021531 SOL (0.0179% modal), divergence principal vs HOLD SOL -0.000002510 SOL, PnL LP +0.000019021 SOL (0.0159%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000019021; setelah gas terhubung -0.000000979.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · ZEBRA-SOL · 8tn5YsFwfwLYZTLSGbpYQCQsEiEjxcBM3vCU7MJjJPsC

2026-09-21T12:36:08+07:00 → 2026-09-21T12:49:24+07:00 · 13.27 menit · pool `BjobrawhmMaLZArDayqAQJgztjCrfxkfWgD9w39R7ZPj`.

1. **Market → volatilitas → depth:** Volatility feed 3.646; TVL $26341.80; fee/TVL entry 0.9511%; base fee pool 2.0%; bin step 100 bps. Snapshot signal diwarisi dari posisi induk; tidak membuktikan refresh pada redeploy.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -548; harga snapshot 0.000004284372 SOL/token; range [-568, -548] (21 bin), downside 18.05%; bentuk BidAskImBalanced. Model bobot: active bin 0.4329% modal, lima bin terdekat 6.494%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.119999990 SOL + 0.000000000 token; withdraw 0.119996343 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of Range for 5.2m (limit 5m); recenter parent/root `4nx2W3WhePBr6y78Gu9AiXFSJR25EKb67tTqzhgdDgMK`
5. **Jalur yang teramati:** 16 sampel; in-range teramati 65.9%; maksimum penurunan teramati sejak snapshot 0.99%.
6. **Fee → drift → divergence → hasil:** Fee +0.000053374 SOL (0.0445% modal), divergence principal vs HOLD SOL -0.000003647 SOL, PnL LP +0.000049727 SOL (0.0414%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000049727; setelah gas terhubung +0.000029727.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## azimuth · FLAME-SOL · 9q8JShPqLgi4BtuWtQasTytouU55wXz1PrumSJ1d5gZ6

2026-09-21T12:43:04+07:00 → 2026-09-21T13:26:32+07:00 · 43.47 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 1.526; TVL $26596.11; fee/TVL entry 0.0500%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -680; harga snapshot 0.000004434434 SOL/token; range [-733, -680] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.099999975 SOL + 0.000000000 token; withdraw 0.099999971 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield (Fee/TVL 24h: 0.00% < 5.0% after 42.4m); hold journal: m5 +3.81% h1 +6.20% (SOL pair JBGqmRZB); OOR 20m of 30m limit, price recovering toward range - expect re-entry within 15m
5. **Jalur yang teramati:** 59 sampel; in-range teramati 9.6%; maksimum penurunan teramati sejak snapshot 0.00%.
6. **Fee → drift → divergence → hasil:** Fee +0.000000004 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000004 SOL, PnL LP -0.000000000 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000020000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Hold terakhir bertentangan dengan geometri: harga sudah di atas range, momentum naik menjauh dari bid ladder; fee saat hold nol. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · DOGE-1-SOL · CmTn33Q7aU1sF1DChEawT4SVKNzZ4WzwQ9ugd1C2BYCF

2026-09-14T14:45:32+07:00 → 2026-09-14T14:51:21+07:00 · 5.82 menit · pool `ErwEeF8y8uLR7LkJcL3xRUuN1d8SrMLZJB92Ydq8vfdw`.

1. **Market → volatilitas → depth:** Volatility feed 4.134; TVL $47626.91; fee/TVL entry 0.1633%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1654; harga snapshot 0.000001889208 SOL/token; range [-1689, -1654] (36 bin), downside 24.34%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499988963 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000009780 SOL (0.0020% modal), divergence principal vs HOLD SOL -0.000011023 SOL, PnL LP -0.000001243 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001243; setelah gas terhubung -0.000021243.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · BTC-SOL · 4Ndx5NMdcjhVkLNSkDcWjxnG8oxswMRbqadK2PShTdwn

2026-09-14T15:10:19+07:00 → 2026-09-14T15:50:19+07:00 · 40.00 menit · pool `2tFYCTqYJ2pyrb7CeA824o2Ybq3jq7agvr3Qpv2uVDmL`.

1. **Market → volatilitas → depth:** Volatility feed 3.109; TVL $16323.37; fee/TVL entry 0.0807%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -598; harga snapshot 0.000008523183 SOL/token; range [-654, -598] (57 bin), downside 36.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.0605% modal, lima bin terdekat 0.907%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.252627500 SOL + 35795.657822000 token. Porsi token pada mark withdrawal 46.95%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** take profit
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006009705 SOL (1.2019% modal), divergence principal vs HOLD SOL -0.023772681 SOL, PnL LP -0.017762975 SOL (-3.5526%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.018851118; setelah gas terhubung -0.018879809. Swap cocok unik, jeda 8 detik; selisih terhadap mark token -0.001088143 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · EMBERCAT-SOL · Cg3AyqPEfeXfXMdsCj9oitpB8qJGiXi9Yva4zNX4gUHz

2026-09-14T16:35:31+07:00 → 2026-09-14T16:50:10+07:00 · 14.65 menit · pool `CnK1jPqSuhbz1ZEHHhVmud3bkUQyHWsqvRuvW1wQGF9f`.

1. **Market → volatilitas → depth:** Volatility feed 4.483; TVL $45083.49; fee/TVL entry 0.3109%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -517; harga snapshot 0.000005832433 SOL/token; range [-582, -517] (66 bin), downside 47.63%; bentuk BidAskImBalanced. Model bobot: active bin 0.0452% modal, lima bin terdekat 0.678%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499997827 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 64.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000024037 SOL (0.0048% modal), divergence principal vs HOLD SOL -0.000002143 SOL, PnL LP +0.000021894 SOL (0.0044%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · CTO-SOL · J1mVoXRK5M3J1FyuSiMErq8dwk4cVPXKi6Z1e1bcAWcT

2026-09-14T17:30:11+07:00 → 2026-09-14T18:21:34+07:00 · 51.38 menit · pool `54sbyULrreD9HBoV5wRWedeCBEw6gQ7VkdHW18rLX78e`.

1. **Market → volatilitas → depth:** Volatility feed 4.466; TVL $38384.52; fee/TVL entry 0.2622%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1244; harga snapshot 0.000004209311 SOL/token; range [-1309, -1244] (66 bin), downside 47.63%; bentuk BidAskImBalanced. Model bobot: active bin 0.0452% modal, lima bin terdekat 0.678%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.500000672 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 90.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000908751 SOL (0.1818% modal), divergence principal vs HOLD SOL 0.000000702 SOL, PnL LP +0.000909453 SOL (0.1819%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · TWINE-SOL · CTT7cafewCpHPY6jhbgZnvMCfm8yHLjRPDJuGeC2YeWa

2026-09-14T17:44:49+07:00 → 2026-09-14T17:50:15+07:00 · 5.43 menit · pool `WRq4e6x2hzEX5hgdyq8KybpLCuxh3YDh2ApGdjERUhZ`.

1. **Market → volatilitas → depth:** Volatility feed 3.528; TVL $84069.84; fee/TVL entry 0.1622%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -330; harga snapshot 0.000037492694 SOL/token; range [-389, -330] (60 bin), downside 44.40%; bentuk BidAskImBalanced. Model bobot: active bin 0.0546% modal, lima bin terdekat 0.820%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999973 SOL + 0.000000000 token; withdraw 0.499999918 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000049 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000055 SOL, PnL LP -0.000000006 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000006; setelah gas terhubung -0.000020006.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · NINA-SOL · HKeUnsZcE5qxBHnpjosEnG7gjWkzBeGzLSNSKVDixvup

2026-09-14T18:05:23+07:00 → 2026-09-14T19:17:08+07:00 · 71.75 menit · pool `GfC7qSh4LXp847xxF493D2UjYC1eViMzPKJHfXeYXDdK`.

1. **Market → volatilitas → depth:** Volatility feed 3.304; TVL $17014.31; fee/TVL entry 0.0556%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -577; harga snapshot 0.000003210460 SOL/token; range [-634, -577] (58 bin), downside 43.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0584% modal, lima bin terdekat 0.877%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.499997864 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 93%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.003311171 SOL (0.6622% modal), divergence principal vs HOLD SOL -0.000002107 SOL, PnL LP +0.003309064 SOL (0.6618%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · OTC-SOL · 8RxWDyTExjp3eQJns9GMLWMGbgpxauBHQgAEGu5EJzk2

2026-09-14T19:00:40+07:00 → 2026-09-14T20:00:49+07:00 · 60.15 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 3.889; TVL $65693.12; fee/TVL entry 0.0809%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -285; harga snapshot 0.000058668971 SOL/token; range [-346, -285] (62 bin), downside 45.50%; bentuk BidAskImBalanced. Model bobot: active bin 0.0512% modal, lima bin terdekat 0.768%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999973 SOL + 0.000000000 token; withdraw 0.497267750 SOL + 48.361335000 token. Porsi token pada mark withdrawal 0.53%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 3.71% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000756428 SOL (0.1513% modal), divergence principal vs HOLD SOL -0.000059349 SOL, PnL LP +0.000697079 SOL (0.1394%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · MADE-SOL · 5DYpMvh9QfKnD3HtuaTrJ986K66dEtrNtAgsrLYUH5rP

2026-09-14T19:34:51+07:00 → 2026-09-14T19:50:44+07:00 · 15.88 menit · pool `FxPPZGPiTNYzgdMkNgAkA8QRZjNxurjBo7JgPt9z4T5X`.

1. **Market → volatilitas → depth:** Volatility feed 5.648; TVL $23124.86; fee/TVL entry 0.0866%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -441; harga snapshot 0.000012424364 SOL/token; range [-514, -441] (74 bin), downside 51.63%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499999500 SOL + 0.000000000 token; withdraw 0.499999492 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 66.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000010206 SOL (0.0020% modal), divergence principal vs HOLD SOL -0.000000008 SOL, PnL LP +0.000010198 SOL (0.0020%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LMAO!-SOL · EJArSmKcSoHDEUbT3sAS31wzBSCjddrCzs2mwsuzKPhV

2026-09-14T20:58:09+07:00 → 2026-09-14T21:11:21+07:00 · 13.20 menit · pool `EWBCL4hKY6VdzZVcCY7pMPvRhG78koHY6nQnt8EW99Br`.

1. **Market → volatilitas → depth:** Volatility feed 7.796; TVL $99538.80; fee/TVL entry 0.1641%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -340; harga snapshot 0.000033941647 SOL/token; range [-409, -340] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.499998456 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 7m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 46.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000071349 SOL (0.0143% modal), divergence principal vs HOLD SOL -0.000001510 SOL, PnL LP +0.000069839 SOL (0.0140%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FLAME-SOL · Gfvk79FWE7deBEHkr6nErs8MBLWdd15R1XGe2vJ7ZzrL

2026-09-14T21:05:19+07:00 → 2026-09-14T21:24:48+07:00 · 19.48 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 1.532; TVL $102986.76; fee/TVL entry 0.0747%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -557; harga snapshot 0.000011816357 SOL/token; range [-593, -557] (37 bin), downside 24.94%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499988649 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 73.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000016551 SOL (0.0033% modal), divergence principal vs HOLD SOL -0.000011332 SOL, PnL LP +0.000005219 SOL (0.0010%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · INDEX-SOL · BUg6wbakd61wnWu7Z9eRXcya8VvdjGwn17iEYRmsgPuE

2026-09-14T21:15:20+07:00 → 2026-09-14T21:32:15+07:00 · 16.92 menit · pool `2qHigfUSvv4r8QTEfZCVJ8yXRiqHx93gGXJ1P2vv3iUD`.

1. **Market → volatilitas → depth:** Volatility feed 3.491; TVL $20633.76; fee/TVL entry 0.1076%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1190; harga snapshot 0.000007203859 SOL/token; range [-1247, -1190] (58 bin), downside 43.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0584% modal, lima bin terdekat 0.877%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.426045166 SOL + 11817.112648891 token. Porsi token pada mark withdrawal 13.83%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.35% → current 0.74% (dropped 0.61% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.008463492 SOL (1.6927% modal), divergence principal vs HOLD SOL -0.005562640 SOL, PnL LP +0.002900852 SOL (0.5802%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.002599963; setelah gas terhubung +0.002473568. Swap cocok unik, jeda 9 detik; selisih terhadap mark token -0.000300889 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PERPSPAD-SOL · DvdZhiykwrBiSTUv3ZLns7dEKrEBWhSq2sKkoMvy6xyj

2026-09-14T21:31:29+07:00 → 2026-09-14T21:37:01+07:00 · 5.53 menit · pool `EHqk4Fw3pTCf9UW75dWoCMf6a2GxyJ8FGYEj2Qmw9rfr`.

1. **Market → volatilitas → depth:** Volatility feed 2.309; TVL $19720.15; fee/TVL entry 0.1262%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -375; harga snapshot 0.000050384907 SOL/token; range [-426, -375] (52 bin), downside 33.39%; bentuk BidAskImBalanced. Model bobot: active bin 0.0726% modal, lima bin terdekat 1.089%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999974 SOL + 0.000000000 token; withdraw 0.499997374 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000002323 SOL (0.0005% modal), divergence principal vs HOLD SOL -0.000002600 SOL, PnL LP -0.000000277 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000277; setelah gas terhubung -0.000020277.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · TOAD-SOL · 4iavL2z4pvV1fSLLX8easPtvoWEjvCtVfMbvSJphcrDm

2026-09-14T21:50:52+07:00 → 2026-09-14T21:58:01+07:00 · 7.15 menit · pool `AFT9ZhYVHMRQrnntMYnqVrKvVrAxpaspCEMBXQNVMwLo`.

1. **Market → volatilitas → depth:** Volatility feed 2.256; TVL $120514.55; fee/TVL entry 0.0514%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -400; harga snapshot 0.000018683167 SOL/token; range [-450, -400] (51 bin), downside 39.20%; bentuk BidAskImBalanced. Model bobot: active bin 0.0754% modal, lima bin terdekat 1.131%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999974 SOL + 0.000000000 token; withdraw 0.499999941 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 6m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000033 SOL, PnL LP -0.000000033 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas -0.000000033; setelah gas terhubung -0.000015033.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · Noiz-SOL · 5nDUStMRHukoEHBH93VRDpbYy2uDLpbg39J6xgaYX9DM

2026-09-14T22:05:36+07:00 → 2026-09-14T22:37:51+07:00 · 32.25 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 1.225; TVL $35858.20; fee/TVL entry 0.0555%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -451; harga snapshot 0.000011247615 SOL/token; range [-494, -451] (44 bin), downside 34.81%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.309099034 SOL + 20209.060087000 token. Porsi token pada mark withdrawal 36.21%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.54% → current 0.45% (dropped 2.09% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.016787066 SOL (3.3574% modal), divergence principal vs HOLD SOL -0.015411578 SOL, PnL LP +0.001375488 SOL (0.2751%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PURPS-SOL · BXZUkcNHDiLC1n9oseWhZgaeMbvKVXeHbmdruyU4GVJf

2026-09-14T22:10:28+07:00 → 2026-09-14T22:38:16+07:00 · 27.80 menit · pool `5vTfWvfTcMzcshVVC47TAwwvRikLQgBaJnKoJWGjS9hE`.

1. **Market → volatilitas → depth:** Volatility feed 2.913; TVL $70064.07; fee/TVL entry 0.0724%; base fee pool 2.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -292; harga snapshot 0.000026585859 SOL/token; range [-345, -292] (54 bin), downside 48.23%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499995050 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 81.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000109653 SOL (0.0219% modal), divergence principal vs HOLD SOL -0.000004927 SOL, PnL LP +0.000104726 SOL (0.0209%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FRIES-SOL · AQBQvnqiBaM9Qz17VABtoJs726f8UbwFWNURdoeTEVm3

2026-09-15T00:00:33+07:00 → 2026-09-15T00:50:42+07:00 · 50.15 menit · pool `5QpDQ6ddkv1ArytJQ991kh8doeXPrt9hHFWK2HmEToDm`.

1. **Market → volatilitas → depth:** Volatility feed 2.206; TVL $17344.26; fee/TVL entry 0.0728%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1257; harga snapshot 0.000003698564 SOL/token; range [-1292, -1257] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999982 SOL + 0.000000000 token; withdraw 0.499987272 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 90%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000866196 SOL (0.1732% modal), divergence principal vs HOLD SOL -0.000012710 SOL, PnL LP +0.000853486 SOL (0.1707%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000853486; setelah gas terhubung +0.000833486.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · 9TuYV3bdZKBmA6qftm6o41SpLYUFju2PxUoCV2YrcyTr

2026-09-15T00:13:32+07:00 → 2026-09-15T00:39:59+07:00 · 26.45 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 3.315; TVL $68055.69; fee/TVL entry 0.0733%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -242; harga snapshot 0.000089996899 SOL/token; range [-300, -242] (59 bin), downside 43.85%; bentuk BidAskImBalanced. Model bobot: active bin 0.0565% modal, lima bin terdekat 0.847%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.422030443 SOL + 1004.023762000 token. Porsi token pada mark withdrawal 14.55%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.62% → current 1.01% (dropped 0.61% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.010735849 SOL (2.1472% modal), divergence principal vs HOLD SOL -0.006094185 SOL, PnL LP +0.004641664 SOL (0.9283%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.003705601; setelah gas terhubung +0.003677961. Swap cocok unik, jeda 9 detik; selisih terhadap mark token -0.000936063 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · UBI-SOL · DfJei1WKYeqhX5z8faVTZdXAawJaDeKkwMu424veGaXk

2026-09-15T00:47:04+07:00 → 2026-09-15T01:47:13+07:00 · 60.15 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 4.169; TVL $46304.84; fee/TVL entry 0.1186%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1164; harga snapshot 0.000009330844 SOL/token; range [-1227, -1164] (64 bin), downside 46.57%; bentuk BidAskImBalanced. Model bobot: active bin 0.0481% modal, lima bin terdekat 0.721%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.498537758 SOL + 157.594530988 token. Porsi token pada mark withdrawal 0.29%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 2.94% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000660961 SOL (0.1322% modal), divergence principal vs HOLD SOL -0.000034969 SOL, PnL LP +0.000625992 SOL (0.1252%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · biketyson-SOL · EsxJKfsPhiZdjd4EThLzGjLmSpC9BVsNH2aWyeTuTVv

2026-09-15T01:05:31+07:00 → 2026-09-15T01:28:21+07:00 · 22.83 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 1.861; TVL $72014.45; fee/TVL entry 0.0713%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -268; harga snapshot 0.000069481922 SOL/token; range [-316, -268] (49 bin), downside 37.97%; bentuk BidAskImBalanced. Model bobot: active bin 0.0816% modal, lima bin terdekat 1.224%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999976 SOL + 0.000000000 token; withdraw 0.499998802 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 77.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000078809 SOL (0.0158% modal), divergence principal vs HOLD SOL -0.000001174 SOL, PnL LP +0.000077635 SOL (0.0155%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · Brb24UNzmtRToenYqDDFSvmwqe3t9HyQ7snzrKk8Syyb

2026-09-15T01:40:19+07:00 → 2026-09-15T01:48:15+07:00 · 7.93 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 2.401; TVL $77921.99; fee/TVL entry 0.2060%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -268; harga snapshot 0.000069481922 SOL/token; range [-319, -268] (52 bin), downside 39.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.0726% modal, lima bin terdekat 1.089%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999974 SOL + 0.000000000 token; withdraw 0.499999974 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000000 SOL, PnL LP -0.000000000 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas -0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · RUSH-SOL · 46wCnitkN9GsTABbpmtKsjsdJTzq4LEyriVtKMJ5iCo2

2026-09-15T01:50:12+07:00 → 2026-09-15T02:00:04+07:00 · 9.87 menit · pool `G6eJgyVdupYx23TD3auEr9PFtv2q98jk3pbg5nP58rdh`.

1. **Market → volatilitas → depth:** Volatility feed 1.446; TVL $14428.02; fee/TVL entry 2.5582%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -65; harga snapshot 0.523733922321 SOL/token; range [-101, -65] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499993798 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 44.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000301525 SOL (0.0603% modal), divergence principal vs HOLD SOL -0.000006183 SOL, PnL LP +0.000295342 SOL (0.0591%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000295342; setelah gas terhubung +0.000275342.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · 4vsdasBmpwxZ7Zf5umZ6jwMZsABw6wNyDLGtatSvzpeg

2026-09-15T02:53:45+07:00 → 2026-09-15T03:01:32+07:00 · 7.78 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 1.810; TVL $67926.53; fee/TVL entry 0.0783%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -285; harga snapshot 0.000058668971 SOL/token; range [-321, -285] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499992497 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000010548 SOL (0.0021% modal), divergence principal vs HOLD SOL -0.000007484 SOL, PnL LP +0.000003064 SOL (0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · NEARKAT-SOL · 8KshNF3eRAG2qjdBQNmsLu6MxeNjCzbU3brUvmcnKAdE

2026-09-15T02:59:33+07:00 → 2026-09-15T03:56:30+07:00 · 56.95 menit · pool `B8BH6ZKr64agqNWG51CQWUKrLZZw5L31u2K6hubsZfyf`.

1. **Market → volatilitas → depth:** Volatility feed 4.066; TVL $61612.49; fee/TVL entry 0.1724%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -327; harga snapshot 0.000038628761 SOL/token; range [-389, -327] (63 bin), downside 46.04%; bentuk BidAskImBalanced. Model bobot: active bin 0.0496% modal, lima bin terdekat 0.744%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999969 SOL + 0.000000000 token; withdraw 0.493012456 SOL + 188.083682000 token. Porsi token pada mark withdrawal 1.36%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.81% → current 1.21% (dropped 0.60% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001577009 SOL (0.3154% modal), divergence principal vs HOLD SOL -0.000210906 SOL, PnL LP +0.001366103 SOL (0.2732%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · BUTTHOLE-SOL · EoayEM2rYegWv5Jg2k8eqAVsjEZjNGQgAHJjhCZzQ5av

2026-09-15T03:40:24+07:00 → 2026-09-15T04:31:29+07:00 · 51.08 menit · pool `3T6pPCvChxMWvGavkyNSFN7UyiMeUwV3NbHHTybPogFC`.

1. **Market → volatilitas → depth:** Volatility feed 0.704; TVL $25329.25; fee/TVL entry 0.0566%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1065; harga snapshot 0.000024988312 SOL/token; range [-1105, -1065] (41 bin), downside 32.83%; bentuk BidAskImBalanced. Model bobot: active bin 0.1161% modal, lima bin terdekat 1.742%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.499987813 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 90.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000010441 SOL (0.0021% modal), divergence principal vs HOLD SOL -0.000012167 SOL, PnL LP -0.000001726 SOL (-0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001726; setelah gas terhubung -0.000021726.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ALL-SOL · CjdiqnJQQfQPdL3ZEkQPBhyViPsSFV6kcsTELaydRevn

2026-09-15T04:35:13+07:00 → 2026-09-15T04:38:27+07:00 · 3.23 menit · pool `FpP5SnzBnHJ5M9wS7fCuYiiSuXUPLNQKpk7qndeZxKZZ`.

1. **Market → volatilitas → depth:** Volatility feed 6.423; TVL $12280.94; fee/TVL entry 0.6228%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -579; harga snapshot 0.000003147202 SOL/token; range [-614, -579] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499977194 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 33.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000019905 SOL (0.0040% modal), divergence principal vs HOLD SOL -0.000022792 SOL, PnL LP -0.000002887 SOL (-0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000002887; setelah gas terhubung -0.000022887.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · NASDUCK-SOL · 4zbforVgP1cfmaqMBqQ9iVqFDdkmkAiVDfz5K6b6eYGR

2026-09-15T05:57:10+07:00 → 2026-09-15T06:57:20+07:00 · 60.17 menit · pool `3vnFSkGU2foSKWsbH5pEJ6HFstugb5YBELkRGgUdJAeA`.

1. **Market → volatilitas → depth:** Volatility feed 4.945; TVL $21233.30; fee/TVL entry 0.1216%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -481; harga snapshot 0.000008344863 SOL/token; range [-550, -481] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.487927397 SOL + 1582.528864000 token. Porsi token pada mark withdrawal 2.32%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 3.50% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000892874 SOL (0.1786% modal), divergence principal vs HOLD SOL -0.000468964 SOL, PnL LP +0.000423910 SOL (0.0848%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · BTC-SOL · GX2EC5nc1EgfCxtMD7hCj657HKKjvS9g1PTREyP545gp

2026-09-15T06:05:19+07:00 → 2026-09-15T06:14:13+07:00 · 8.90 menit · pool `2tFYCTqYJ2pyrb7CeA824o2Ybq3jq7agvr3Qpv2uVDmL`.

1. **Market → volatilitas → depth:** Volatility feed 3.085; TVL $11772.25; fee/TVL entry 0.1698%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -630; harga snapshot 0.000006604878 SOL/token; range [-686, -630] (57 bin), downside 36.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.0605% modal, lima bin terdekat 0.907%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499994943 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000006636 SOL (0.0013% modal), divergence principal vs HOLD SOL -0.000005029 SOL, PnL LP +0.000001607 SOL (0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MANLET-SOL · DugaM4XUpjZDBMZgJkG2oUtke3pktaf5kgber4MriqJc

2026-09-15T06:35:14+07:00 → 2026-09-15T06:41:11+07:00 · 5.95 menit · pool `68C62WPYiiNZxprbuaMj2ULXpiTDKcs5xsX7kBGnyajR`.

1. **Market → volatilitas → depth:** Volatility feed 1.493; TVL $35518.54; fee/TVL entry 0.3030%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1500; harga snapshot 0.000006444687 SOL/token; range [-1536, -1500] (37 bin), downside 24.94%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499995622 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000003897 SOL (0.0008% modal), divergence principal vs HOLD SOL -0.000004359 SOL, PnL LP -0.000000462 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000462; setelah gas terhubung -0.000020462.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · DOGE-1-SOL · EJKQPnC7ADWo8RLZ2UtSkhWsJCuPA4mjyYHRShJbah5t

2026-09-15T06:49:09+07:00 → 2026-09-15T07:49:18+07:00 · 60.15 menit · pool `ErwEeF8y8uLR7LkJcL3xRUuN1d8SrMLZJB92Ydq8vfdw`.

1. **Market → volatilitas → depth:** Volatility feed 0.797; TVL $60807.91; fee/TVL entry 0.0847%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1687; harga snapshot 0.000001452387 SOL/token; range [-1722, -1687] (36 bin), downside 24.34%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.487493792 SOL + 8804.976003669 token. Porsi token pada mark withdrawal 2.46%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 2.27% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000441832 SOL (0.0884% modal), divergence principal vs HOLD SOL -0.000217440 SOL, PnL LP +0.000224392 SOL (0.0449%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000017930; setelah gas terhubung -0.000007146. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.000206462 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · PVE-SOL · H67n1ByrX5Xqtf67J6qWWMrqczihT3tdG2AQ3caVhCXk

2026-09-15T08:05:14+07:00 → 2026-09-15T08:49:06+07:00 · 43.87 menit · pool `4apFUjxT1BrvmuPHzxxMnerMHxzYKG64GePi8ApnSaqg`.

1. **Market → volatilitas → depth:** Volatility feed 7.593; TVL $13425.53; fee/TVL entry 0.4323%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -433; harga snapshot 0.000013453806 SOL/token; range [-519, -433] (87 bin), downside 57.50%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499998048 SOL + 0.000000000 token; withdraw 0.463494276 SOL + 3148.997334000 token. Porsi token pada mark withdrawal 6.78%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.46% → current 0.81% (dropped 0.65% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.007484865 SOL (1.4970% modal), divergence principal vs HOLD SOL -0.002804086 SOL, PnL LP +0.004680778 SOL (0.9362%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil dalam SOL sebelum gas +0.003565368; setelah gas terhubung +0.003482011. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.001115410 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · STONK10-SOL · 74Ap7SHbag2iAPjnRo75AQ34JzSZtjN82MB8np3ddJmF

2026-09-15T08:13:49+07:00 → 2026-09-15T09:32:42+07:00 · 78.88 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 4.997; TVL $18145.90; fee/TVL entry 0.1598%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -478; harga snapshot 0.000022175103 SOL/token; range [-547, -478] (70 bin), downside 42.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500003410 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 97.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.008365456 SOL (1.6731% modal), divergence principal vs HOLD SOL 0.000003445 SOL, PnL LP +0.008368901 SOL (1.6738%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Jimothy-SOL · FEFYEonuPaxiA5aFL284aDtp3Xj3rihmQXSTUJmLVCT

2026-09-15T08:54:29+07:00 → 2026-09-15T09:15:48+07:00 · 21.32 menit · pool `5pjRzUQan6bYynQERLK499fq48LiD5ryZrf9adZX1HQo`.

1. **Market → volatilitas → depth:** Volatility feed 1.259; TVL $11596.87; fee/TVL entry 0.0903%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -312; harga snapshot 0.000044846792 SOL/token; range [-356, -312] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499999922 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 76.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000009 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000055 SOL, PnL LP -0.000000046 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000046; setelah gas terhubung -0.000020046.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLAME-SOL · FG2vPmoZc8CaSsEDErcAdeu8pn6z3pTg9fkebfUVRMd9

2026-09-15T09:28:02+07:00 → 2026-09-15T09:33:24+07:00 · 5.37 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 3.261; TVL $47243.64; fee/TVL entry 0.0526%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -642; harga snapshot 0.000006002586 SOL/token; range [-699, -642] (58 bin), downside 36.50%; bentuk BidAskImBalanced. Model bobot: active bin 0.0584% modal, lima bin terdekat 0.877%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.499999076 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000759 SOL (0.0002% modal), divergence principal vs HOLD SOL -0.000000895 SOL, PnL LP -0.000000136 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000136; setelah gas terhubung -0.000020136.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MINI-SOL · 7c77axpQRMxoSAPyAuRa8tgaRo1fNNv12k9t8XJtQ5eo

2026-09-15T09:40:20+07:00 → 2026-09-15T10:09:41+07:00 · 29.35 menit · pool `64BSmy7BESiHnWYzLdPso6FuXymh7H8jTkaiyfbBg1YD`.

1. **Market → volatilitas → depth:** Volatility feed 4.592; TVL $48871.92; fee/TVL entry 0.1945%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -295; harga snapshot 0.000025613303 SOL/token; range [-361, -295] (67 bin), downside 55.95%; bentuk BidAskImBalanced. Model bobot: active bin 0.0439% modal, lima bin terdekat 0.658%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499999930 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 82.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000057729 SOL (0.0115% modal), divergence principal vs HOLD SOL -0.000000037 SOL, PnL LP +0.000057692 SOL (0.0115%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · OTC-SOL · BJYwoTG76ukrLyks4FZVwDSy3m7Dpa7SxmwQenUvvZWt

2026-09-15T10:20:14+07:00 → 2026-09-15T10:33:19+07:00 · 13.08 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 4.664; TVL $61972.81; fee/TVL entry 0.1620%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -291; harga snapshot 0.000055268825 SOL/token; range [-360, -291] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999967 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 61.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000023098 SOL (0.0046% modal), divergence principal vs HOLD SOL 0.000000002 SOL, PnL LP +0.000023100 SOL (0.0046%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · PVE-SOL · 8zL4jpwRM2e6b5B9j5XtfpCVGdfvGD1zx8L9bzSvNzqR

2026-09-15T10:25:15+07:00 → 2026-09-15T10:30:46+07:00 · 5.52 menit · pool `4apFUjxT1BrvmuPHzxxMnerMHxzYKG64GePi8ApnSaqg`.

1. **Market → volatilitas → depth:** Volatility feed 1.387; TVL $13964.05; fee/TVL entry 0.2759%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -480; harga snapshot 0.000008428312 SOL/token; range [-524, -480] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499999916 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000015 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000061 SOL, PnL LP -0.000000046 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000046; setelah gas terhubung -0.000020046.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LEVERHEDGE-SOL · BQ1ikwEUQjBAZMJBphBB8AjfyJjm4FAaR9frta65JkAw

2026-09-15T10:35:11+07:00 → 2026-09-15T10:57:17+07:00 · 22.10 menit · pool `Cv2Vj7YJdwEbNj3jBWZd6dKRKFvfCLRw2Up1Lxw6KC9w`.

1. **Market → volatilitas → depth:** Volatility feed 1.502; TVL $13223.67; fee/TVL entry 0.1157%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -532; harga snapshot 0.000005023763 SOL/token; range [-567, -532] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499996503 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 77.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000011857 SOL (0.0024% modal), divergence principal vs HOLD SOL -0.000003483 SOL, PnL LP +0.000008374 SOL (0.0017%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000008374; setelah gas terhubung -0.000011626.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · PERPSPAD-SOL · 3EDe63htET7uNrgC5GXHE4KKKiQJ85eBrYrdFEXuW92g

2026-09-15T11:00:08+07:00 → 2026-09-15T11:06:04+07:00 · 5.93 menit · pool `EHqk4Fw3pTCf9UW75dWoCMf6a2GxyJ8FGYEj2Qmw9rfr`.

1. **Market → volatilitas → depth:** Volatility feed 1.739; TVL $35615.22; fee/TVL entry 0.0976%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -379; harga snapshot 0.000048804327 SOL/token; range [-415, -379] (37 bin), downside 24.94%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499999960 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000019 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000021 SOL, PnL LP -0.000000002 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000002; setelah gas terhubung -0.000020002.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · HUHCAT-SOL · EXkEbhPunNFT2VLB7rauwjLc7FCrF4hV8PaiF5253e97

2026-09-15T11:22:06+07:00 → 2026-09-15T11:32:23+07:00 · 10.28 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 12.067; TVL $133329.26; fee/TVL entry 0.9728%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -465; harga snapshot 0.000009785008 SOL/token; range [-534, -465] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499998801 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 80%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001805393 SOL (0.3611% modal), divergence principal vs HOLD SOL -0.000001164 SOL, PnL LP +0.001804229 SOL (0.3608%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001992931; setelah gas terhubung +0.001966298. Swap cocok unik, jeda 1124 detik; selisih terhadap mark token +0.000188702 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Noiz-SOL · J8fFtogKhevJaaLSXJNTJLzQHdaLn35S9bzUES2WD7mi

2026-09-15T11:30:15+07:00 → 2026-09-15T11:49:38+07:00 · 19.38 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 4.527; TVL $40896.20; fee/TVL entry 0.0885%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -504; harga snapshot 0.000006637853 SOL/token; range [-570, -504] (67 bin), downside 48.15%; bentuk BidAskImBalanced. Model bobot: active bin 0.0439% modal, lima bin terdekat 0.658%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.473733184 SOL + 4343.946926000 token. Porsi token pada mark withdrawal 5.03%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.65% → current 0.93% (dropped 0.72% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.008373226 SOL (1.6746% modal), divergence principal vs HOLD SOL -0.001181853 SOL, PnL LP +0.007191373 SOL (1.4383%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.005649548; setelah gas terhubung +0.005624025. Swap cocok unik, jeda 12 detik; selisih terhadap mark token -0.001541825 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · HUHCAT-SOL · 2PTpDYNphs6ZeCmAU2MNwhHFdRi7gXLovQtHbx1XL6o6

2026-09-15T11:48:20+07:00 → 2026-09-15T11:50:56+07:00 · 2.60 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 5.965; TVL $107733.11; fee/TVL entry 0.0589%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -446; harga snapshot 0.000011821356 SOL/token; range [-515, -446] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499994635 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000004676 SOL (0.0009% modal), divergence principal vs HOLD SOL -0.000005330 SOL, PnL LP -0.000000654 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000654; setelah gas terhubung -0.000020654.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · HUHCAT-SOL · 2mLN3i3z46XVwJRWB7q567qMkemkPuoBws9Z2DQh7iwD

2026-09-15T11:52:19+07:00 → 2026-09-15T12:00:28+07:00 · 8.15 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 5.650; TVL $98827.78; fee/TVL entry 0.2298%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -432; harga snapshot 0.000013588344 SOL/token; range [-502, -429] (74 bin), downside 51.63%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499999608 SOL + 0.000000000 token; withdraw 0.500006524 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 87.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001366760 SOL (0.2734% modal), divergence principal vs HOLD SOL 0.000006916 SOL, PnL LP +0.001373676 SOL (0.2747%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. 

## meridian · PVE-SOL · AWKn5JU1f7CFA8FNEgWQvTmTZMxbN5UmsXT7L7L5dUMf

2026-09-15T13:00:16+07:00 → 2026-09-15T15:14:57+07:00 · 134.68 menit · pool `4apFUjxT1BrvmuPHzxxMnerMHxzYKG64GePi8ApnSaqg`.

1. **Market → volatilitas → depth:** Volatility feed 4.788; TVL $13118.94; fee/TVL entry 0.1147%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -518; harga snapshot 0.000005774686 SOL/token; range [-585, -518] (68 bin), downside 48.66%; bentuk BidAskImBalanced. Model bobot: active bin 0.0426% modal, lima bin terdekat 0.639%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.202981939 SOL + 72830.875087000 token. Porsi token pada mark withdrawal 55.26%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -8.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.012761485 SOL (2.5523% modal), divergence principal vs HOLD SOL -0.046330647 SOL, PnL LP -0.033569162 SOL (-6.7138%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.042060692; setelah gas terhubung -0.042086143. Swap cocok unik, jeda 12 detik; selisih terhadap mark token -0.008491530 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PURPS-SOL · 9McQ1cM1XpZ9Gf2puc5yFYrBHSFrhJXxkwNmRMbtYYAW

2026-09-15T13:43:11+07:00 → 2026-09-15T14:16:09+07:00 · 32.97 menit · pool `5vTfWvfTcMzcshVVC47TAwwvRikLQgBaJnKoJWGjS9hE`.

1. **Market → volatilitas → depth:** Volatility feed 2.079; TVL $65575.75; fee/TVL entry 0.0574%; base fee pool 2.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -322; harga snapshot 0.000018314697 SOL/token; range [-371, -322] (50 bin), downside 45.59%; bentuk BidAskImBalanced. Model bobot: active bin 0.0784% modal, lima bin terdekat 1.176%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999975 SOL + 0.000000000 token; withdraw 0.499989741 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 84.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000029740 SOL (0.0059% modal), divergence principal vs HOLD SOL -0.000010234 SOL, PnL LP +0.000019506 SOL (0.0039%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · biketyson-SOL · AqGT1b6LvTFGxuzJMn4UpRnepdHUsy2ar7x7EFySFFoh

2026-09-15T15:48:20+07:00 → 2026-09-15T15:53:58+07:00 · 5.63 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 2.173; TVL $95263.59; fee/TVL entry 0.0604%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -274; harga snapshot 0.000065455114 SOL/token; range [-324, -274] (51 bin), downside 39.20%; bentuk BidAskImBalanced. Model bobot: active bin 0.0754% modal, lima bin terdekat 1.131%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999974 SOL + 0.000000000 token; withdraw 0.499989921 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000008813 SOL (0.0018% modal), divergence principal vs HOLD SOL -0.000010053 SOL, PnL LP -0.000001240 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001240; setelah gas terhubung -0.000021240.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MADE-SOL · CcW38FtCEpEcGy27g4XF35nQJpEKE1iFP8Lm7KwTNLRs

2026-09-15T16:10:19+07:00 → 2026-09-15T17:15:08+07:00 · 64.82 menit · pool `FxPPZGPiTNYzgdMkNgAkA8QRZjNxurjBo7JgPt9z4T5X`.

1. **Market → volatilitas → depth:** Volatility feed 4.702; TVL $23599.03; fee/TVL entry 0.0676%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -443; harga snapshot 0.000012179555 SOL/token; range [-478, -443] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.491931468 SOL + 676.910806000 token. Porsi token pada mark withdrawal 1.59%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 1.52% < min 7% (age: 64m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000340622 SOL (0.0681% modal), divergence principal vs HOLD SOL -0.000145742 SOL, PnL LP +0.000194880 SOL (0.0390%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · LEVERCAT-SOL · CrkonaKpoNocjDjZ6BQxTWJfp4wSqEsaL7c6fmdPcUKf

2026-09-15T17:26:29+07:00 → 2026-09-15T17:42:36+07:00 · 16.12 menit · pool `42JnUXw5N9ftMkbM1tMzJw2tnzqs1U9RxWBk5LzNv4gD`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $134708.97; fee/TVL entry 0.0936%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -400; harga snapshot 0.000018683167 SOL/token; range [-445, -400] (46 bin), downside 36.09%; bentuk BidAskImBalanced. Model bobot: active bin 0.0925% modal, lima bin terdekat 1.388%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499993579 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 68.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000049485 SOL (0.0099% modal), divergence principal vs HOLD SOL -0.000006398 SOL, PnL LP +0.000043087 SOL (0.0086%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · UBI-SOL · 6pfKEvH5zYbcazk8DstffesGyDEzVDMfud98fSabX8Fh

2026-09-15T17:55:30+07:00 → 2026-09-15T18:55:39+07:00 · 60.15 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 2.858; TVL $29458.53; fee/TVL entry 0.1224%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1172; harga snapshot 0.000008616878 SOL/token; range [-1227, -1172] (56 bin), downside 42.15%; bentuk BidAskImBalanced. Model bobot: active bin 0.0627% modal, lima bin terdekat 0.940%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499208199 SOL + 94.788948870 token. Porsi token pada mark withdrawal 0.16%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 2.91% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000590100 SOL (0.1180% modal), divergence principal vs HOLD SOL 0.000016925 SOL, PnL LP +0.000607025 SOL (0.1214%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · LEVERCAT-SOL · AQVyW3fDNte9hFhkqScMYfCYb4B2FiLphZNxrw1sPYoD

2026-09-15T18:20:34+07:00 → 2026-09-15T18:26:09+07:00 · 5.58 menit · pool `42JnUXw5N9ftMkbM1tMzJw2tnzqs1U9RxWBk5LzNv4gD`.

1. **Market → volatilitas → depth:** Volatility feed 3.221; TVL $136888.42; fee/TVL entry 0.0670%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -378; harga snapshot 0.000023255234 SOL/token; range [-435, -378] (58 bin), downside 43.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0584% modal, lima bin terdekat 0.877%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.499993204 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000014216 SOL (0.0028% modal), divergence principal vs HOLD SOL -0.000006767 SOL, PnL LP +0.000007449 SOL (0.0015%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · BULLSHIT-SOL · DaJfDKoEPhB9HAxcp78ovdzTtsZyVeRVMCK6vTak8fXx

2026-09-15T19:10:08+07:00 → 2026-09-15T19:36:52+07:00 · 26.73 menit · pool `DchDNJc71s11WaHzJRjzW4qG6qbYC8ySzbBMcFmnAThk`.

1. **Market → volatilitas → depth:** Volatility feed 2.071; TVL $12549.16; fee/TVL entry 0.0583%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -500; harga snapshot 0.000006907376 SOL/token; range [-536, -500] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499998516 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 80.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000168536 SOL (0.0337% modal), divergence principal vs HOLD SOL -0.000001465 SOL, PnL LP +0.000167071 SOL (0.0334%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SCRIBE-SOL · 8gu3UAurVJ53gQzzwyxgPfwPttTanABbvynPStRyo9mC

2026-09-15T19:46:38+07:00 → 2026-09-15T19:49:17+07:00 · 2.65 menit · pool `9VGCLeeBDrE1CP3QDpd6rHLqBkqCJPVw4xWpPFMpGbqd`.

1. **Market → volatilitas → depth:** Volatility feed 5.459; TVL $15566.63; fee/TVL entry 0.6393%; base fee pool 0.6%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -516; harga snapshot 0.000016381944 SOL/token; range [-585, -516] (70 bin), downside 42.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499998673 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000023891 SOL (0.0048% modal), divergence principal vs HOLD SOL -0.000001292 SOL, PnL LP +0.000022599 SOL (0.0045%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · SCRIBE-SOL · HcqEYsPC5a2dDaE4yNtyiKswgWKxJayd89auYrtSRafp

2026-09-15T19:50:56+07:00 → 2026-09-15T19:52:02+07:00 · 1.10 menit · pool `9VGCLeeBDrE1CP3QDpd6rHLqBkqCJPVw4xWpPFMpGbqd`.

1. **Market → volatilitas → depth:** Volatility feed 5.368; TVL $16850.64; fee/TVL entry 0.7043%; base fee pool 0.6%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -504; harga snapshot 0.000018025687 SOL/token; range [-572, -501] (72 bin), downside 43.21%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499999395 SOL + 0.000000000 token; withdraw 0.499999193 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000051577 SOL (0.0103% modal), divergence principal vs HOLD SOL -0.000000202 SOL, PnL LP +0.000051375 SOL (0.0103%). Gas transaksi posisi yang terhubung 0.000035000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. 

## meridian · SCRIBE-SOL · DtFfrFYDb8oLG3ybrJrXnYia43hZMtP81FSLidznnCmW

2026-09-15T20:06:02+07:00 → 2026-09-15T20:18:26+07:00 · 12.40 menit · pool `9VGCLeeBDrE1CP3QDpd6rHLqBkqCJPVw4xWpPFMpGbqd`.

1. **Market → volatilitas → depth:** Volatility feed 3.412; TVL $32312.90; fee/TVL entry 0.5134%; base fee pool 0.6%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -511; harga snapshot 0.000017047790 SOL/token; range [-569, -511] (59 bin), downside 37.01%; bentuk BidAskImBalanced. Model bobot: active bin 0.0565% modal, lima bin terdekat 0.847%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.374413745 SOL + 8577.492945000 token. Porsi token pada mark withdrawal 23.66%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.66% → current 1.92% (dropped 0.74% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.019146648 SOL (3.8293% modal), divergence principal vs HOLD SOL -0.009528775 SOL, PnL LP +0.009617873 SOL (1.9236%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · fart-SOL · 49Fbk7UHXKYUvKQygHtkU7hazyU4Ehx9MKW4XKuRNr7S

2026-09-15T21:12:25+07:00 → 2026-09-15T21:30:15+07:00 · 17.83 menit · pool `Bq3PKRZ8bUzNry7rKd85DrQ6yJYKycpkN2uZcfYh6mCH`.

1. **Market → volatilitas → depth:** Volatility feed 6.258; TVL $11576.14; fee/TVL entry 0.1968%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -618; harga snapshot 0.000002134966 SOL/token; range [-687, -618] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.404543030 SOL + 55602.463676000 token. Porsi token pada mark withdrawal 17.73%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.03% → current -1.27% (dropped 3.30% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.004333686 SOL (0.8667% modal), divergence principal vs HOLD SOL -0.008255739 SOL, PnL LP -0.003922053 SOL (-0.7844%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.007629222; setelah gas terhubung -0.007658364. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.003707169 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FLAME-SOL · B5GYj3SaqkBVThU7pzSxgBpwHmKoRV4VppY26n3tznXR

2026-09-15T21:55:14+07:00 → 2026-09-15T22:03:13+07:00 · 7.98 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 1.127; TVL $35569.46; fee/TVL entry 0.0623%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -633; harga snapshot 0.000006448863 SOL/token; range [-676, -633] (44 bin), downside 29.01%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.499999969 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 75%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000074862 SOL (0.0150% modal), divergence principal vs HOLD SOL -0.000000015 SOL, PnL LP +0.000074847 SOL (0.0150%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · STONK10-SOL · 641ZBhvcC6s7cCwyMnLDj9BCymXqFfZXubPVQXFtFx3K

2026-09-15T22:32:21+07:00 → 2026-09-15T22:40:34+07:00 · 8.22 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 2.056; TVL $45786.30; fee/TVL entry 0.1576%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -526; harga snapshot 0.000015127254 SOL/token; range [-575, -526] (50 bin), downside 32.32%; bentuk BidAskImBalanced. Model bobot: active bin 0.0784% modal, lima bin terdekat 1.176%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999975 SOL + 0.000000000 token; withdraw 0.499992463 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000216962 SOL (0.0434% modal), divergence principal vs HOLD SOL -0.000007512 SOL, PnL LP +0.000209450 SOL (0.0419%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · NEARKAT-SOL · 41VnmZV4tqhd7tKjZP9T4nokHaViVtwJe9sFapRjcKHd

2026-09-15T22:40:14+07:00 → 2026-09-15T22:48:14+07:00 · 8.00 menit · pool `B8BH6ZKr64agqNWG51CQWUKrLZZw5L31u2K6hubsZfyf`.

1. **Market → volatilitas → depth:** Volatility feed 0.890; TVL $63262.05; fee/TVL entry 0.1670%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -312; harga snapshot 0.000044846792 SOL/token; range [-353, -312] (42 bin), downside 33.50%; bentuk BidAskImBalanced. Model bobot: active bin 0.1107% modal, lima bin terdekat 1.661%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499999972 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000005 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000005 SOL, PnL LP +0.000000000 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000020000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · BUTTHOLE-SOL · BQc574bXTCBiCwNU5n2qJzeEeqSHF8fqs5wswK9XRhWt

2026-09-15T23:51:17+07:00 → 2026-09-16T01:00:51+07:00 · 69.57 menit · pool `3T6pPCvChxMWvGavkyNSFN7UyiMeUwV3NbHHTybPogFC`.

1. **Market → volatilitas → depth:** Volatility feed 4.251; TVL $22808.12; fee/TVL entry 0.1823%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1088; harga snapshot 0.000019876748 SOL/token; range [-1152, -1088] (65 bin), downside 47.10%; bentuk BidAskImBalanced. Model bobot: active bin 0.0466% modal, lima bin terdekat 0.699%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.493481502 SOL + 341.547410474 token. Porsi token pada mark withdrawal 1.28%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.51% → current 1.88% (dropped 0.63% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.005087713 SOL (1.0175% modal), divergence principal vs HOLD SOL -0.000123060 SOL, PnL LP +0.004964653 SOL (0.9929%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.004910354; setelah gas terhubung +0.004885097. Swap cocok unik, jeda 12 detik; selisih terhadap mark token -0.000054299 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Noiz-SOL · BabvYdNSrVcmroY1xsL8vk8UyeAzJwog1JetHcp5mzFt

2026-09-15T23:55:17+07:00 → 2026-09-16T00:29:42+07:00 · 34.42 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 3.282; TVL $15985.01; fee/TVL entry 0.1245%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -517; harga snapshot 0.000005832433 SOL/token; range [-574, -517] (58 bin), downside 43.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0584% modal, lima bin terdekat 0.877%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.500001166 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 85.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000308627 SOL (0.0617% modal), divergence principal vs HOLD SOL 0.000001195 SOL, PnL LP +0.000309822 SOL (0.0620%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · CAT-SOL · 4Y7qN2yBWBAiPY6pQDV3cxneBC8XPQtidn76GjjLA5M2

2026-09-16T00:47:04+07:00 → 2026-09-16T00:59:33+07:00 · 12.48 menit · pool `Hcm1L9GY3xGd6XXQRYdzB5LFhF1vTq6uQQd1tB5qQTKh`.

1. **Market → volatilitas → depth:** Volatility feed 14.183; TVL $38067.51; fee/TVL entry 0.5453%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -389; harga snapshot 0.000007967693 SOL/token; range [-424, -389] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.439473751 SOL + 8347.429362000 token. Porsi token pada mark withdrawal 11.53%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.48% → current 1.84% (dropped 0.64% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.009980341 SOL (1.9961% modal), divergence principal vs HOLD SOL -0.003227509 SOL, PnL LP +0.006752832 SOL (1.3506%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.009814775; setelah gas terhubung +0.009787041. Swap cocok unik, jeda 12 detik; selisih terhadap mark token +0.003061943 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · CAT-SOL · GoRHDZzspibfCdjhKDhC5QZdELcdjivn7ZgRQGow7otp

2026-09-16T01:00:15+07:00 → 2026-09-16T01:12:13+07:00 · 11.97 menit · pool `Hcm1L9GY3xGd6XXQRYdzB5LFhF1vTq6uQQd1tB5qQTKh`.

1. **Market → volatilitas → depth:** Volatility feed 10.483; TVL $62266.08; fee/TVL entry 1.0808%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -400; harga snapshot 0.000006950039 SOL/token; range [-469, -400] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.463561919 SOL + 6202.971181000 token. Porsi token pada mark withdrawal 6.76%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.65% → current 1.71% (dropped 0.94% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.015798094 SOL (3.1596% modal), divergence principal vs HOLD SOL -0.002811183 SOL, PnL LP +0.012986911 SOL (2.5974%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.013833505; setelah gas terhubung +0.013806555. Swap cocok unik, jeda 11 detik; selisih terhadap mark token +0.000846594 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · HUHCAT-SOL · Gvi3yZdX4gDzgAURK1YZoqYjj8GHGDx1RW58U1kj6e8M

2026-09-16T01:10:14+07:00 → 2026-09-16T01:51:47+07:00 · 41.55 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 2.204; TVL $67095.45; fee/TVL entry 0.0596%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -447; harga snapshot 0.000011704313 SOL/token; range [-496, -447] (50 bin), downside 38.59%; bentuk BidAskImBalanced. Model bobot: active bin 0.0784% modal, lima bin terdekat 1.176%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999975 SOL + 0.000000000 token; withdraw 0.499997105 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 10m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 75.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.008505964 SOL (1.7012% modal), divergence principal vs HOLD SOL -0.000002870 SOL, PnL LP +0.008503094 SOL (1.7006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · CAT-SOL · HTit7yTPoi4zVpLoLHrHudNWDpUf5Baam5rfmQjdg5xM

2026-09-16T01:23:02+07:00 → 2026-09-16T01:34:29+07:00 · 11.45 menit · pool `Hcm1L9GY3xGd6XXQRYdzB5LFhF1vTq6uQQd1tB5qQTKh`.

1. **Market → volatilitas → depth:** Volatility feed 7.099; TVL $46614.28; fee/TVL entry 0.1270%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -412; harga snapshot 0.000005987518 SOL/token; range [-460, -412] (49 bin), downside 44.91%; bentuk BidAskImBalanced. Model bobot: active bin 0.0816% modal, lima bin terdekat 1.224%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999976 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 125538.450655000 token. Porsi token pada mark withdrawal 100.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -28.55% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.030895581 SOL (6.1791% modal), divergence principal vs HOLD SOL -0.164767137 SOL, PnL LP -0.133871556 SOL (-26.7743%). Gas transaksi posisi yang terhubung 0.000025000 SOL. Hasil dalam SOL sebelum gas -0.107241209; setelah gas terhubung -0.107300541. Swap cocok unik, jeda 11 detik; selisih terhadap mark token +0.026630347 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ALL-SOL · EAjs4x8RkfpUce2NPnDXhGMQcWMwpEnVvBYfhGsxk7Gt

2026-09-16T01:40:49+07:00 → 2026-09-16T02:54:50+07:00 · 74.02 menit · pool `FpP5SnzBnHJ5M9wS7fCuYiiSuXUPLNQKpk7qndeZxKZZ`.

1. **Market → volatilitas → depth:** Volatility feed 5.955; TVL $17341.46; fee/TVL entry 0.1847%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -452; harga snapshot 0.000011136252 SOL/token; range [-521, -452] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.334011299 SOL + 19409.977030000 token. Porsi token pada mark withdrawal 30.30%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.45% → current -2.07% (dropped 3.52% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.015791082 SOL (3.1582% modal), divergence principal vs HOLD SOL -0.020807888 SOL, PnL LP -0.005016806 SOL (-1.0034%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PUMPCADE-SOL · 8NHN8BnJebfhkQ4EB56FsSSiFsj4pDR6u31STMsVnAvJ

2026-09-16T01:57:40+07:00 → 2026-09-16T02:04:25+07:00 · 6.75 menit · pool `AY2GKBFGhFKJ7vzy5V7fYzRu7kbWByfFSG8zZQjPqVSe`.

1. **Market → volatilitas → depth:** Volatility feed 7.036; TVL $tidak tersedia; fee/TVL entry 0.1355%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -257; harga snapshot 0.000077518782 SOL/token; range [-346, -277] (70 bin), downside 49.67%; bentuk unknown.
3. **Inventory → fee opportunity:** Entry 0.000000000 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 0.000000000 token. Porsi token pada mark withdrawal tidak tersedia%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (tidak tersedia% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (tidak tersedia%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Posisi kosong/tidak didanai menurut API; jangan dihitung sebagai trade bermodal atau return nol yang sukses.

## meridian · PERPSPAD-SOL · HHkJXFejS5McCsVtUJGPXPrWwakwiFXXjgeXVAMFRmo3

2026-09-16T03:20:22+07:00 → 2026-09-16T03:26:55+07:00 · 6.55 menit · pool `EHqk4Fw3pTCf9UW75dWoCMf6a2GxyJ8FGYEj2Qmw9rfr`.

1. **Market → volatilitas → depth:** Volatility feed 1.893; TVL $53959.74; fee/TVL entry 0.0596%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -408; harga snapshot 0.000038734941 SOL/token; range [-456, -408] (49 bin), downside 31.78%; bentuk BidAskImBalanced. Model bobot: active bin 0.0816% modal, lima bin terdekat 1.224%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999976 SOL + 0.000000000 token; withdraw 0.499997747 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000021079 SOL (0.0042% modal), divergence principal vs HOLD SOL -0.000002229 SOL, PnL LP +0.000018850 SOL (0.0038%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · PAID-SOL · EdeTqE2PJqxzUysmR4gJPbSXfumVYykdfgCmxNjz38Sf

2026-09-16T03:26:18+07:00 → 2026-09-16T03:30:57+07:00 · 4.65 menit · pool `6xf7dn56P55zJEL9CoMDiDLqqTo7zF1dScEPqNZm92PF`.

1. **Market → volatilitas → depth:** Volatility feed 19.954; TVL $23853.58; fee/TVL entry 6.5839%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -468; harga snapshot 0.000009497232 SOL/token; range [-537, -468] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500006940 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.011060689 SOL (2.2121% modal), divergence principal vs HOLD SOL 0.000006975 SOL, PnL LP +0.011067664 SOL (2.2135%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.011067664; setelah gas terhubung +0.011047664.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PAID-SOL · 6gJJTKPEwcEjhaKhFCp3GYwEV9kSDARSeCxNHdMo6VKa

2026-09-16T03:41:23+07:00 → 2026-09-16T03:58:01+07:00 · 16.63 menit · pool `6xf7dn56P55zJEL9CoMDiDLqqTo7zF1dScEPqNZm92PF`.

1. **Market → volatilitas → depth:** Volatility feed 16.568; TVL $29578.64; fee/TVL entry 2.0600%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -473; harga snapshot 0.000009036291 SOL/token; range [-542, -473] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500017075 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 81.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.014035105 SOL (2.8070% modal), divergence principal vs HOLD SOL 0.000017110 SOL, PnL LP +0.014052215 SOL (2.8104%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.014052215; setelah gas terhubung +0.014032215.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · DOGE-1-SOL · 4V6DZCqj7gb37zZVYnKYgavfp8LpSVUi3wsNaiQHrpSg

2026-09-16T03:55:16+07:00 → 2026-09-16T04:12:35+07:00 · 17.32 menit · pool `ErwEeF8y8uLR7LkJcL3xRUuN1d8SrMLZJB92Ydq8vfdw`.

1. **Market → volatilitas → depth:** Volatility feed 0.976; TVL $24784.61; fee/TVL entry 0.0502%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1737; harga snapshot 0.000000975115 SOL/token; range [-1772, -1737] (36 bin), downside 24.34%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499995836 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000003584 SOL (0.0007% modal), divergence principal vs HOLD SOL -0.000004150 SOL, PnL LP -0.000000566 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000566; setelah gas terhubung -0.000020566.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · PAID-SOL · Bj9kGrNdgKmu16rxTLqFLj5BAMuTxuWZQr4hqM1AL7JB

2026-09-16T04:01:47+07:00 → 2026-09-16T04:04:34+07:00 · 2.78 menit · pool `6xf7dn56P55zJEL9CoMDiDLqqTo7zF1dScEPqNZm92PF`.

1. **Market → volatilitas → depth:** Volatility feed 8.198; TVL $41596.03; fee/TVL entry 1.1406%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -405; harga snapshot 0.000017776392 SOL/token; range [-440, -405] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.410548470 SOL + 5532.446341000 token. Porsi token pada mark withdrawal 17.25%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.24% → current 0.06% (dropped 1.18% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.007719021 SOL (1.5438% modal), divergence principal vs HOLD SOL -0.003893325 SOL, PnL LP +0.003825696 SOL (0.7651%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.004472304; setelah gas terhubung +0.004445883. Swap cocok unik, jeda 11 detik; selisih terhadap mark token +0.000646608 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MANLET-SOL · 8LEhCt5uKZe8xPT5ij4z1DCi75EgTUhBTQoXW7485bDA

2026-09-16T04:10:16+07:00 → 2026-09-16T04:36:29+07:00 · 26.22 menit · pool `68C62WPYiiNZxprbuaMj2ULXpiTDKcs5xsX7kBGnyajR`.

1. **Market → volatilitas → depth:** Volatility feed 1.686; TVL $26562.21; fee/TVL entry 0.0622%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1514; harga snapshot 0.000005764404 SOL/token; range [-1552, -1514] (39 bin), downside 26.12%; bentuk BidAskImBalanced. Model bobot: active bin 0.1282% modal, lima bin terdekat 1.923%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499999077 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 80.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000099432 SOL (0.0199% modal), divergence principal vs HOLD SOL -0.000000904 SOL, PnL LP +0.000098528 SOL (0.0197%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · CMDT-SOL · RiRy7xF47pmH5S62C7Cma3b7QCACBE2rs6EXJ7Smi25

2026-09-16T04:16:22+07:00 → 2026-09-16T04:29:41+07:00 · 13.32 menit · pool `EwNsvkbUgHLZMR64B3MxcfYVxj4YtRLLJvNjwsR9usNG`.

1. **Market → volatilitas → depth:** Volatility feed 19.310; TVL $10175.41; fee/TVL entry 0.5105%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -598; harga snapshot 0.000002605064 SOL/token; range [-667, -598] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.443541755 SOL + 25151.005990000 token. Porsi token pada mark withdrawal 10.51%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 3.35% → current 2.39% (dropped 0.96% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.025017620 SOL (5.0035% modal), divergence principal vs HOLD SOL -0.004340870 SOL, PnL LP +0.020676750 SOL (4.1354%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.022101152; setelah gas terhubung +0.022073996. Swap cocok unik, jeda 12 detik; selisih terhadap mark token +0.001424402 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · EaUkFcZJwSte6B74836K34wNHCRqGF2Gp6WDGUho2nE2

2026-09-16T04:30:31+07:00 → 2026-09-16T04:47:18+07:00 · 16.78 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 2.056; TVL $131018.48; fee/TVL entry 0.0570%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -328; harga snapshot 0.000038246298 SOL/token; range [-377, -328] (50 bin), downside 38.59%; bentuk BidAskImBalanced. Model bobot: active bin 0.0784% modal, lima bin terdekat 1.176%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999975 SOL + 0.000000000 token; withdraw 0.444507635 SOL + 1607.732457000 token. Porsi token pada mark withdrawal 10.55%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.27% → current 0.63% (dropped 0.64% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.005974729 SOL (1.1949% modal), divergence principal vs HOLD SOL -0.003052519 SOL, PnL LP +0.002922209 SOL (0.5844%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ELON-SOL · FoMc1A1qrpE8McqmMuaeJnnFZssaog7uegS2NW4R6kdP

2026-09-16T05:10:08+07:00 → 2026-09-16T05:11:42+07:00 · 1.57 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 14.183; TVL $11192.90; fee/TVL entry 4.9851%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -584; harga snapshot 0.000009529042 SOL/token; range [-653, -584] (70 bin), downside 42.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500000718 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.003088637 SOL (0.6177% modal), divergence principal vs HOLD SOL 0.000000753 SOL, PnL LP +0.003089390 SOL (0.6179%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.003099163; setelah gas terhubung +0.003073286. Swap cocok unik, jeda 9 detik; selisih terhadap mark token +0.000009773 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · 38Hc5iQsJj12EYG1ZqVpuBM5vgH16iGZ1w2CsvvAorcC

2026-09-16T05:25:14+07:00 → 2026-09-16T05:33:55+07:00 · 8.68 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 2.643; TVL $125533.08; fee/TVL entry 0.2829%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -347; harga snapshot 0.000031657987 SOL/token; range [-400, -347] (54 bin), downside 40.98%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499989675 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000004913 SOL (0.0010% modal), divergence principal vs HOLD SOL -0.000010302 SOL, PnL LP -0.000005389 SOL (-0.0011%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ELON-SOL · GW9CKW2xNYXJf4dYBg8jo6dDtWpZmFY25KTjaC88e9Vd

2026-09-16T05:31:06+07:00 → 2026-09-16T05:35:20+07:00 · 4.23 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 13.146; TVL $18591.02; fee/TVL entry 3.0128%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -528; harga snapshot 0.000014888092 SOL/token; range [-597, -528] (70 bin), downside 42.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999609 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.015526975 SOL (3.1054% modal), divergence principal vs HOLD SOL -0.000000356 SOL, PnL LP +0.015526619 SOL (3.1053%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.015056528; setelah gas terhubung +0.015020547. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.000470091 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ELON-SOL · 6eqyMZqwPk8DudJK6rRYabPvVwGQ4KVLgNYxrarQDKLG

2026-09-16T05:40:11+07:00 → 2026-09-16T05:48:28+07:00 · 8.28 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 12.335; TVL $13815.99; fee/TVL entry 1.9926%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -540; harga snapshot 0.000013530463 SOL/token; range [-583, -540] (44 bin), downside 29.01%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.481826581 SOL + 1394.547525000 token. Porsi token pada mark withdrawal 3.54%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 3.11% → current 2.37% (dropped 0.74% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.017266066 SOL (3.4532% modal), divergence principal vs HOLD SOL -0.000469798 SOL, PnL LP +0.016796269 SOL (3.3593%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.016653428; setelah gas terhubung +0.016624258. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.000142841 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · HKcow8GQLbiYq2prxHchYvP5Z1YGVxi7Qtk5UY3f7hJv

2026-09-16T06:10:09+07:00 → 2026-09-16T06:17:54+07:00 · 7.75 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 1.149; TVL $125601.22; fee/TVL entry 0.0551%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -351; harga snapshot 0.000030422703 SOL/token; range [-394, -351] (44 bin), downside 34.81%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.499988651 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000009953 SOL (0.0020% modal), divergence principal vs HOLD SOL -0.000011333 SOL, PnL LP -0.000001380 SOL (-0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001380; setelah gas terhubung -0.000021380.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · xBTC-SOL · 6c3qKLJt2UjLimmpDcH3515DSPu3CTxekBijkZdN8esg

2026-09-16T06:40:19+07:00 → 2026-09-16T07:40:29+07:00 · 60.17 menit · pool `A7N89BDRnHTqiHXu8MMymdn34Vopb9sbtzm5gErN65zB`.

1. **Market → volatilitas → depth:** Volatility feed 1.492; TVL $35031.87; fee/TVL entry 0.0722%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot 289; harga snapshot 0.017736871644 SOL/token; range [244, 289] (46 bin), downside 36.09%; bentuk BidAskImBalanced. Model bobot: active bin 0.0925% modal, lima bin terdekat 1.388%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.498493970 SOL + 0.085508000 token. Porsi token pada mark withdrawal 0.30%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.12% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000024465 SOL (0.0049% modal), divergence principal vs HOLD SOL -0.000019246 SOL, PnL LP +0.000005219 SOL (0.0010%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LEVERCAT-SOL · FjZkbRfrGyNFGpW4qfFeYwbs5wKYHRykamhnUEfwduDp

2026-09-16T06:45:14+07:00 → 2026-09-16T06:57:52+07:00 · 12.63 menit · pool `42JnUXw5N9ftMkbM1tMzJw2tnzqs1U9RxWBk5LzNv4gD`.

1. **Market → volatilitas → depth:** Volatility feed 3.399; TVL $91768.38; fee/TVL entry 0.0786%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -389; harga snapshot 0.000020844218 SOL/token; range [-447, -389] (59 bin), downside 43.85%; bentuk BidAskImBalanced. Model bobot: active bin 0.0565% modal, lima bin terdekat 0.847%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499993518 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 58.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000005206 SOL (0.0010% modal), divergence principal vs HOLD SOL -0.000006454 SOL, PnL LP -0.000001248 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001248; setelah gas terhubung -0.000021248.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · CTO-SOL · 4QiwDvVrdRzfgkJPwnnxYmK5hK1R6fkyVcLGF7PHK1zC

2026-09-16T07:25:22+07:00 → 2026-09-16T10:59:24+07:00 · 214.03 menit · pool `54sbyULrreD9HBoV5wRWedeCBEw6gQ7VkdHW18rLX78e`.

1. **Market → volatilitas → depth:** Volatility feed 2.111; TVL $12981.19; fee/TVL entry 0.8605%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1290; harga snapshot 0.000002663347 SOL/token; range [-1326, -1290] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.303942439 SOL + 85298.122362095 token. Porsi token pada mark withdrawal 37.52%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.52% → current -0.30% (dropped 1.82% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.015718917 SOL (3.1438% modal), divergence principal vs HOLD SOL -0.013543170 SOL, PnL LP +0.002175747 SOL (0.4351%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SCRIBE-SOL · 9Ku3B4jcsa9KmdrQxfJYA6WNQju9RxsYF7r4o1yx1wwe

2026-09-16T08:23:12+07:00 → 2026-09-16T08:59:51+07:00 · 36.65 menit · pool `BZJTiubWLruAhoBxCTgU3uVdvXFztsr4cKG7SZcxoQdC`.

1. **Market → volatilitas → depth:** Volatility feed 11.430; TVL $31445.00; fee/TVL entry 0.5484%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -579; harga snapshot 0.000003147202 SOL/token; range [-622, -579] (44 bin), downside 34.81%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.499993227 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 86.1%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.003856982 SOL (0.7714% modal), divergence principal vs HOLD SOL -0.000006757 SOL, PnL LP +0.003850225 SOL (0.7700%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.003818891; setelah gas terhubung +0.003783949. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.000031334 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · TRUMP-SOL · AxYW2EfJ4dJnM5qCAV78Pwfzu4URFwHocnuKAmxrheRu

2026-09-16T09:36:03+07:00 → 2026-09-16T09:39:41+07:00 · 3.63 menit · pool `7XXugGEq5r2CpTdzXnDTwfTHkUg92e91N8RnzuGuir2r`.

1. **Market → volatilitas → depth:** Volatility feed 15.703; TVL $10733.05; fee/TVL entry 1.5981%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -529; harga snapshot 0.000005175988 SOL/token; range [-598, -529] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499994746 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.003448232 SOL (0.6896% modal), divergence principal vs HOLD SOL -0.000005219 SOL, PnL LP +0.003443013 SOL (0.6886%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.003283366; setelah gas terhubung +0.003256504. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.000159647 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SCRIBE-SOL · HENXJMaZm2foT5SiDSE62dyiCjHXrktkbUdKA7PU5otV

2026-09-16T09:40:24+07:00 → 2026-09-16T09:46:17+07:00 · 5.88 menit · pool `BZJTiubWLruAhoBxCTgU3uVdvXFztsr4cKG7SZcxoQdC`.

1. **Market → volatilitas → depth:** Volatility feed 2.744; TVL $20520.57; fee/TVL entry 0.1231%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -586; harga snapshot 0.000002935452 SOL/token; range [-623, -586] (38 bin), downside 30.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.499984420 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000013691 SOL (0.0027% modal), divergence principal vs HOLD SOL -0.000015558 SOL, PnL LP -0.000001867 SOL (-0.0004%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001867; setelah gas terhubung -0.000021867.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · SCRIBE-SOL · 8ZwS6FmXR5XR7sht8n5KzuQ8dZiq76LaGRHqDEJGZa8h

2026-09-16T10:08:58+07:00 → 2026-09-16T10:19:24+07:00 · 10.43 menit · pool `BZJTiubWLruAhoBxCTgU3uVdvXFztsr4cKG7SZcxoQdC`.

1. **Market → volatilitas → depth:** Volatility feed 2.124; TVL $20556.26; fee/TVL entry 0.2316%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -573; harga snapshot 0.000003340818 SOL/token; range [-609, -573] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499987396 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 50%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000365219 SOL (0.0730% modal), divergence principal vs HOLD SOL -0.000012585 SOL, PnL LP +0.000352634 SOL (0.0705%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FLAME-SOL · 7GeRkqhFWuYFP6N5HcjzvL5ZXjjB6ehqonU2BioDeM7g

2026-09-16T10:52:22+07:00 → 2026-09-16T11:02:36+07:00 · 10.23 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 5.372; TVL $23803.88; fee/TVL entry 0.1408%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -667; harga snapshot 0.000004918414 SOL/token; range [-736, -667] (70 bin), downside 42.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499994781 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 50%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000004583 SOL (0.0009% modal), divergence principal vs HOLD SOL -0.000005184 SOL, PnL LP -0.000000601 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · EMBER-SOL · F1NLA2G4nb4vpfRwHGjbsdfzDGFZu1kx88PWLbyFvffq

2026-09-16T11:20:19+07:00 → 2026-09-16T12:20:28+07:00 · 60.15 menit · pool `G6migXbRRTvVhWLQC1KyqXDT2xjVkjcgcyDxSWt3URXG`.

1. **Market → volatilitas → depth:** Volatility feed 0.833; TVL $83249.85; fee/TVL entry 0.0544%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -233; harga snapshot 0.000098428283 SOL/token; range [-274, -233] (42 bin), downside 33.50%; bentuk BidAskImBalanced. Model bobot: active bin 0.1107% modal, lima bin terdekat 1.661%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499446353 SOL + 5.616842000 token. Porsi token pada mark withdrawal 0.11%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 4.08% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000844135 SOL (0.1688% modal), divergence principal vs HOLD SOL -0.000006242 SOL, PnL LP +0.000837894 SOL (0.1676%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · pill-SOL · D69eh65vcNhLU31XgNUpAA47ih1TCGrdrsXg6TkG69Ge

2026-09-16T12:45:14+07:00 → 2026-09-16T12:56:32+07:00 · 11.30 menit · pool `GndPdxFgRU2iwd6CmFzoYZrjad7Ft6bNNzc84cMLcLvQ`.

1. **Market → volatilitas → depth:** Volatility feed 5.449; TVL $43512.37; fee/TVL entry 0.9895%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -454; harga snapshot 0.000010916824 SOL/token; range [-523, -454] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999679 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 90.9%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.002730076 SOL (0.5460% modal), divergence principal vs HOLD SOL -0.000000286 SOL, PnL LP +0.002729790 SOL (0.5460%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.002729790; setelah gas terhubung +0.002709790.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · pill-SOL · AqdAEPz7XMTUfYJGhvRXiqCcqPkmuuQuYa14dc367ygN

2026-09-16T13:00:14+07:00 → 2026-09-16T13:07:52+07:00 · 7.63 menit · pool `GndPdxFgRU2iwd6CmFzoYZrjad7Ft6bNNzc84cMLcLvQ`.

1. **Market → volatilitas → depth:** Volatility feed 5.830; TVL $39797.42; fee/TVL entry 1.0397%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -423; harga snapshot 0.000014861371 SOL/token; range [-492, -423] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.434620023 SOL + 5167.377816000 token. Porsi token pada mark withdrawal 12.22%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.06% → current -0.55% (dropped 2.61% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.002901654 SOL (0.5803% modal), divergence principal vs HOLD SOL -0.004899336 SOL, PnL LP -0.001997682 SOL (-0.3995%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.002319720; setelah gas terhubung -0.002344950. Swap cocok unik, jeda 12 detik; selisih terhadap mark token -0.000322038 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · pill-SOL · 6vTUxoQgBscF9fgfc8pb2G3X4Wm7UXq9i32crDZZwjkx

2026-09-16T13:10:22+07:00 → 2026-09-16T14:09:07+07:00 · 58.75 menit · pool `GndPdxFgRU2iwd6CmFzoYZrjad7Ft6bNNzc84cMLcLvQ`.

1. **Market → volatilitas → depth:** Volatility feed 5.708; TVL $40055.41; fee/TVL entry 0.4294%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -446; harga snapshot 0.000011821356 SOL/token; range [-515, -446] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.418519679 SOL + 8260.772401000 token. Porsi token pada mark withdrawal 15.14%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.45% → current 0.24% (dropped 1.21% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.008532632 SOL (1.7065% modal), divergence principal vs HOLD SOL -0.006833544 SOL, PnL LP +0.001699088 SOL (0.3398%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.005471068; setelah gas terhubung -0.005499867. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.007170156 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · HUHCAT-SOL · 4zir1eiVpgvAzEZVsUG3LoWCewAk8hq6cnmp8ad3YEYC

2026-09-16T13:53:16+07:00 → 2026-09-16T14:05:46+07:00 · 12.50 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 2.676; TVL $74422.70; fee/TVL entry 0.1064%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -445; harga snapshot 0.000011939569 SOL/token; range [-482, -445] (38 bin), downside 30.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.500000134 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 58.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000035535 SOL (0.0071% modal), divergence principal vs HOLD SOL 0.000000156 SOL, PnL LP +0.000035691 SOL (0.0071%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · OTC-SOL · 3JudVUKZo3nuibZ8gfBmZXxYx7MKErNu2iA2KHeydr8X

2026-09-16T15:40:13+07:00 → 2026-09-16T16:40:21+07:00 · 60.13 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 3.518; TVL $25016.08; fee/TVL entry 0.0850%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -304; harga snapshot 0.000048562649 SOL/token; range [-361, -304] (58 bin), downside 43.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0584% modal, lima bin terdekat 0.877%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.489479919 SOL + 226.822825000 token. Porsi token pada mark withdrawal 2.06%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.96% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000203055 SOL (0.0406% modal), divergence principal vs HOLD SOL -0.000246053 SOL, PnL LP -0.000042999 SOL (-0.0086%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · Noiz-SOL · 6QnqUkEakZUj3Ut7xor2ZGWeGhBMhZxp5dvmB3ARsMJQ

2026-09-16T15:45:21+07:00 → 2026-09-16T16:45:30+07:00 · 60.15 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 3.747; TVL $12036.07; fee/TVL entry 0.2290%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -566; harga snapshot 0.000003581809 SOL/token; range [-626, -566] (61 bin), downside 44.96%; bentuk BidAskImBalanced. Model bobot: active bin 0.0529% modal, lima bin terdekat 0.793%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.481931909 SOL + 5398.729142000 token. Porsi token pada mark withdrawal 3.47%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 5.82% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001235148 SOL (0.2470% modal), divergence principal vs HOLD SOL -0.000735654 SOL, PnL LP +0.000499493 SOL (0.0999%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · PAID-SOL · FhmEZgnNbbLdVZAMz7uDaPfL4Uq3DrkUzaps9xdvDCag

2026-09-16T17:00:17+07:00 → 2026-09-16T18:45:02+07:00 · 104.75 menit · pool `6xf7dn56P55zJEL9CoMDiDLqqTo7zF1dScEPqNZm92PF`.

1. **Market → volatilitas → depth:** Volatility feed 2.375; TVL $117594.11; fee/TVL entry 0.0970%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -237; harga snapshot 0.000094587645 SOL/token; range [-288, -237] (52 bin), downside 39.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.0726% modal, lima bin terdekat 1.089%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999974 SOL + 0.000000000 token; withdraw 0.500001284 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 95.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006364424 SOL (1.2729% modal), divergence principal vs HOLD SOL 0.000001310 SOL, PnL LP +0.006365734 SOL (1.2731%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.006365734; setelah gas terhubung +0.006345734.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PERPSPAD-SOL · GQA8WSzhCLvEMW8mu4mBuvd3c6wmzzTv6kVNjtc8q6XW

2026-09-16T18:00:12+07:00 → 2026-09-16T18:06:59+07:00 · 6.78 menit · pool `D2Z3uVsqgLHxe5C5H3F3PjqkCWsq4AqdYn1K91DVNknV`.

1. **Market → volatilitas → depth:** Volatility feed 1.990; TVL $16775.17; fee/TVL entry 0.1177%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -356; harga snapshot 0.000028946158 SOL/token; range [-405, -356] (50 bin), downside 38.59%; bentuk BidAskImBalanced. Model bobot: active bin 0.0784% modal, lima bin terdekat 1.176%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999975 SOL + 0.000000000 token; withdraw 0.499990229 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000008526 SOL (0.0017% modal), divergence principal vs HOLD SOL -0.000009746 SOL, PnL LP -0.000001220 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001220; setelah gas terhubung -0.000021220.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ELON-SOL · LDyHbskQwEBDXQYLSpg3ppq4FrojVoX4zajr9YnFNsX

2026-09-16T18:10:10+07:00 → 2026-09-16T18:14:25+07:00 · 4.25 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 2.779; TVL $38269.95; fee/TVL entry 0.0898%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -560; harga snapshot 0.000011537242 SOL/token; range [-597, -560] (38 bin), downside 25.53%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.499986672 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000011712 SOL (0.0023% modal), divergence principal vs HOLD SOL -0.000013306 SOL, PnL LP -0.000001594 SOL (-0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001594; setelah gas terhubung -0.000021594.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · GIN-CHAN-SOL · 5zcG3upSKdiu4zxt3qNwne2C8bBDvCnVEoNW7mipFQNK

2026-09-16T18:18:06+07:00 → 2026-09-16T18:40:02+07:00 · 21.93 menit · pool `FWYZSdGT6fZREpeH2f7TcS4GChqUsUv4onXr88c72oYP`.

1. **Market → volatilitas → depth:** Volatility feed 9.064; TVL $12066.15; fee/TVL entry 0.5685%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -437; harga snapshot 0.000004389055 SOL/token; range [-506, -437] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.123073517 SOL + 143026.544829000 token. Porsi token pada mark withdrawal 70.77%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -13.63% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.023015143 SOL (4.6030% modal), divergence principal vs HOLD SOL -0.079015955 SOL, PnL LP -0.056000812 SOL (-11.2002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.055880964; setelah gas terhubung -0.055909627. Swap cocok unik, jeda 12 detik; selisih terhadap mark token +0.000119848 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · GIN-CHAN-SOL · 9WJAX8rSgygTxfVmJNKk6hr92ywmLA2vVdbVQhvNmiDk

2026-09-16T18:40:35+07:00 → 2026-09-16T18:43:33+07:00 · 2.97 menit · pool `FWYZSdGT6fZREpeH2f7TcS4GChqUsUv4onXr88c72oYP`.

1. **Market → volatilitas → depth:** Volatility feed 6.458; TVL $15310.59; fee/TVL entry 1.4600%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -497; harga snapshot 0.000002082904 SOL/token; range [-561, -497] (65 bin), downside 54.84%; bentuk BidAskImBalanced. Model bobot: active bin 0.0466% modal, lima bin terdekat 0.699%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499998137 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 33.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001636 SOL (0.0003% modal), divergence principal vs HOLD SOL -0.000001830 SOL, PnL LP -0.000000194 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000194; setelah gas terhubung -0.000020194.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · GIN-CHAN-SOL · ANTKdDow8fQxSwHE8oh3ttJbz1upT8unxyHCApqCmQJC

2026-09-16T18:48:51+07:00 → 2026-09-16T19:15:51+07:00 · 27.00 menit · pool `FWYZSdGT6fZREpeH2f7TcS4GChqUsUv4onXr88c72oYP`.

1. **Market → volatilitas → depth:** Volatility feed 5.091; TVL $13349.21; fee/TVL entry 0.3232%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -483; harga snapshot 0.000002478561 SOL/token; range [-552, -483] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.377088923 SOL + 65767.648980000 token. Porsi token pada mark withdrawal 22.08%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.54% → current 1.87% (dropped 0.67% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.028764470 SOL (5.7529% modal), divergence principal vs HOLD SOL -0.016059491 SOL, PnL LP +0.012704979 SOL (2.5410%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.019316240; setelah gas terhubung +0.019280114. Swap cocok unik, jeda 12 detik; selisih terhadap mark token +0.006611261 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · 7p6oy7KYoSeh6fDKXqhZwV3kWsbyg55oaaxUW65EcbKJ

2026-09-16T18:53:21+07:00 → 2026-09-16T19:53:32+07:00 · 60.18 menit · pool `ARqHS4dXM989rYBjDKzx249yqBXQtdrUioemyoGEnAnk`.

1. **Market → volatilitas → depth:** Volatility feed 7.463; TVL $148810.93; fee/TVL entry 0.0734%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -340; harga snapshot 0.000033941647 SOL/token; range [-380, -340] (41 bin), downside 32.83%; bentuk BidAskImBalanced. Model bobot: active bin 0.1161% modal, lima bin terdekat 1.742%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.484817965 SOL + 464.876094000 token. Porsi token pada mark withdrawal 2.97%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 4.05% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000848810 SOL (0.1698% modal), divergence principal vs HOLD SOL -0.000317803 SOL, PnL LP +0.000531007 SOL (0.1062%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000175474; setelah gas terhubung +0.000150333. Swap cocok unik, jeda 12 detik; selisih terhadap mark token -0.000355533 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · MANLET-SOL · 8pHqWg7tUFEtGp9DN2VSjyfmE7FRhQ62cU7qdvJRyzgV

2026-09-16T19:30:16+07:00 → 2026-09-16T20:30:37+07:00 · 60.35 menit · pool `68C62WPYiiNZxprbuaMj2ULXpiTDKcs5xsX7kBGnyajR`.

1. **Market → volatilitas → depth:** Volatility feed 4.318; TVL $25806.25; fee/TVL entry 0.1555%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1521; harga snapshot 0.000005451684 SOL/token; range [-1559, -1521] (39 bin), downside 26.12%; bentuk BidAskImBalanced. Model bobot: active bin 0.1282% modal, lima bin terdekat 1.923%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.498869896 SOL + 207.654624029 token. Porsi token pada mark withdrawal 0.22%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.50% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000111126 SOL (0.0222% modal), divergence principal vs HOLD SOL -0.000007002 SOL, PnL LP +0.000104124 SOL (0.0208%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · lockinu-SOL · GgqLB7miteZ1LMs7k3KJq6BuHSkGbU3SpEQy3ZrMrRd4

2026-09-16T20:16:40+07:00 → 2026-09-16T20:34:25+07:00 · 17.75 menit · pool `9PxMQ7Ny9NMurjKwSQMeNrE9yvdML6HVCXo8EzedLvJw`.

1. **Market → volatilitas → depth:** Volatility feed 8.867; TVL $92252.06; fee/TVL entry 0.1249%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -475; harga snapshot 0.000008858240 SOL/token; range [-575, -480] (96 bin), downside 61.14%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499998528 SOL + 0.000000000 token; withdraw 0.477286805 SOL + 3062.362163000 token. Porsi token pada mark withdrawal 4.24%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.33% → current 0.73% (dropped 0.60% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.005755339 SOL (1.1511% modal), divergence principal vs HOLD SOL -0.001558836 SOL, PnL LP +0.004196504 SOL (0.8393%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil dalam SOL sebelum gas +0.004298010; setelah gas terhubung +0.004249735. Swap cocok unik, jeda 10 detik; selisih terhadap mark token +0.000101506 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. 

## meridian · lockinu-SOL · 6eHuraiWA3tSwxMZCuH1LqCyDiCqKUgZ38TbtLNKQYG

2026-09-16T21:10:16+07:00 → 2026-09-16T21:20:07+07:00 · 9.85 menit · pool `9PxMQ7Ny9NMurjKwSQMeNrE9yvdML6HVCXo8EzedLvJw`.

1. **Market → volatilitas → depth:** Volatility feed 7.180; TVL $57917.79; fee/TVL entry 0.1926%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -487; harga snapshot 0.000007861238 SOL/token; range [-572, -488] (85 bin), downside 56.65%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499996690 SOL + 0.000000000 token; withdraw 0.447558262 SOL + 8032.946083000 token. Porsi token pada mark withdrawal 9.65%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.34% → current 0.73% (dropped 0.61% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.009668423 SOL (1.9337% modal), divergence principal vs HOLD SOL -0.004645091 SOL, PnL LP +0.005023332 SOL (1.0047%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil dalam SOL sebelum gas +0.006063553; setelah gas terhubung +0.006011349. Swap cocok unik, jeda 16 detik; selisih terhadap mark token +0.001040221 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. 

## meridian · lockinu-SOL · B2BrLiKwqc7z5D1xGQtneYjSMTY76fPBWBfqMhzTVBcz

2026-09-16T21:22:35+07:00 → 2026-09-16T21:41:56+07:00 · 19.35 menit · pool `9PxMQ7Ny9NMurjKwSQMeNrE9yvdML6HVCXo8EzedLvJw`.

1. **Market → volatilitas → depth:** Volatility feed 7.002; TVL $53412.34; fee/TVL entry 0.1251%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -510; harga snapshot 0.000006253158 SOL/token; range [-579, -510] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999160 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 73.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006361045 SOL (1.2722% modal), divergence principal vs HOLD SOL -0.000000805 SOL, PnL LP +0.006360240 SOL (1.2720%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.006198279; setelah gas terhubung +0.006162969. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.000161961 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · LOOP-SOL · BHw7W2YfmfsCmfpqmfq31cPCVcXbvmXkHF1RewAZa8ba

2026-09-16T22:20:21+07:00 → 2026-09-16T22:26:01+07:00 · 5.67 menit · pool `8TNPC3TCLaKQsEkSWk2MzHLpD57rVc2uUMgVKJrytgbk`.

1. **Market → volatilitas → depth:** Volatility feed 2.551; TVL $19292.84; fee/TVL entry 0.1407%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -521; harga snapshot 0.000005604853 SOL/token; range [-573, -521] (53 bin), downside 40.39%; bentuk BidAskImBalanced. Model bobot: active bin 0.0699% modal, lima bin terdekat 1.048%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499996387 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000003195 SOL (0.0006% modal), divergence principal vs HOLD SOL -0.000003599 SOL, PnL LP -0.000000404 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000404; setelah gas terhubung -0.000020404.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · PERPSPAD-SOL · 4xozAXKCvLXLNK368fFpRRsovicvt1Lo6Dy212Lu5s21

2026-09-16T22:50:15+07:00 → 2026-09-16T23:52:02+07:00 · 61.78 menit · pool `EHqk4Fw3pTCf9UW75dWoCMf6a2GxyJ8FGYEj2Qmw9rfr`.

1. **Market → volatilitas → depth:** Volatility feed 5.802; TVL $78806.83; fee/TVL entry 0.0677%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -407; harga snapshot 0.000039044821 SOL/token; range [-442, -407] (36 bin), downside 24.34%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499999633 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 91.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.003233093 SOL (0.6466% modal), divergence principal vs HOLD SOL -0.000000353 SOL, PnL LP +0.003232740 SOL (0.6465%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · baton-SOL · 44yaGgRezDha7mLjk27m8Qssn8ajUtN6xc6DewKyFYnU

2026-09-16T23:43:45+07:00 → 2026-09-16T23:48:08+07:00 · 4.38 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 4.271; TVL $81152.28; fee/TVL entry 0.0564%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -338; harga snapshot 0.000034623874 SOL/token; range [-401, -338] (64 bin), downside 46.57%; bentuk BidAskImBalanced. Model bobot: active bin 0.0481% modal, lima bin terdekat 0.721%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499999972 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000016258 SOL (0.0033% modal), divergence principal vs HOLD SOL 0.000000002 SOL, PnL LP +0.000016260 SOL (0.0033%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000016260; setelah gas terhubung -0.000003740.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLAME-SOL · 8q348oqTz7JjG7VzZHDVYodjLxTE9K56pvHn6uikKmFL

2026-09-16T23:49:18+07:00 → 2026-09-16T23:49:28+07:00 · 0.17 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 3.635; TVL $22472.31; fee/TVL entry 0.0636%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -688; harga snapshot 0.000004160580 SOL/token; range [-748, -688] (61 bin), downside 38.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.0529% modal, lima bin terdekat 0.793%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499972576 SOL + 6.380237000 token. Porsi token pada mark withdrawal 0.01%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000849 SOL, PnL LP -0.000000849 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · NEARKAT-SOL · 4cnXdDzC6gE5aG16DPUUh6WdovPHC34VgQ3psxQW4mNn

2026-09-17T01:40:16+07:00 → 2026-09-17T01:46:09+07:00 · 5.88 menit · pool `B8BH6ZKr64agqNWG51CQWUKrLZZw5L31u2K6hubsZfyf`.

1. **Market → volatilitas → depth:** Volatility feed 4.641; TVL $94056.73; fee/TVL entry 0.4553%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -319; harga snapshot 0.000041829412 SOL/token; range [-386, -319] (68 bin), downside 48.66%; bentuk BidAskImBalanced. Model bobot: active bin 0.0426% modal, lima bin terdekat 0.639%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.499994286 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000004981 SOL (0.0010% modal), divergence principal vs HOLD SOL -0.000005680 SOL, PnL LP -0.000000699 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000699; setelah gas terhubung -0.000020699.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · xBTC-SOL · BzGu3ckez9YkEYpxaaeeCvoyowRPMbz51Rf4KJMnb8te

2026-09-17T01:55:12+07:00 → 2026-09-17T02:55:20+07:00 · 60.13 menit · pool `A7N89BDRnHTqiHXu8MMymdn34Vopb9sbtzm5gErN65zB`.

1. **Market → volatilitas → depth:** Volatility feed 1.149; TVL $24509.81; fee/TVL entry 0.1416%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot 288; harga snapshot 0.017561259053 SOL/token; range [253, 288] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.500001908 SOL + 0.000071000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.09% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000018920 SOL (0.0038% modal), divergence principal vs HOLD SOL 0.000003169 SOL, PnL LP +0.000022089 SOL (0.0044%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MADE-SOL · 3oZXQkE13awtaELto2H1VrL9bLR3ziz77SpoGNRgGVhq

2026-09-17T02:18:49+07:00 → 2026-09-17T03:04:59+07:00 · 46.17 menit · pool `FxPPZGPiTNYzgdMkNgAkA8QRZjNxurjBo7JgPt9z4T5X`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $28907.00; fee/TVL entry 0.0545%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -470; harga snapshot 0.000009310099 SOL/token; range [-515, -470] (46 bin), downside 36.09%; bentuk BidAskImBalanced. Model bobot: active bin 0.0925% modal, lima bin terdekat 1.388%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499999885 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 89.1%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000022382 SOL (0.0045% modal), divergence principal vs HOLD SOL -0.000000092 SOL, PnL LP +0.000022290 SOL (0.0045%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLAME-SOL · FCWPDJuGPBo3Wpy6XcGvtJy4X4e9nYWQjWKcDgTe2tRz

2026-09-17T03:15:15+07:00 → 2026-09-17T04:02:49+07:00 · 47.57 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 5.455; TVL $23997.99; fee/TVL entry 0.2354%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -640; harga snapshot 0.000006099011 SOL/token; range [-712, -640] (73 bin), downside 43.66%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499998316 SOL + 0.000000000 token; withdraw 0.436804989 SOL + 11826.529256000 token. Porsi token pada mark withdrawal 11.92%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.23% → current 0.31% (dropped 0.92% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006212916 SOL (1.2426% modal), divergence principal vs HOLD SOL -0.004091153 SOL, PnL LP +0.002121764 SOL (0.4244%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ALL-SOL · 7V542653TFv3H7PB7Fx6ie3d1ztfQZouEv5PH8a2M6r6

2026-09-17T03:49:05+07:00 → 2026-09-17T04:00:26+07:00 · 11.35 menit · pool `FpP5SnzBnHJ5M9wS7fCuYiiSuXUPLNQKpk7qndeZxKZZ`.

1. **Market → volatilitas → depth:** Volatility feed 5.861; TVL $27327.62; fee/TVL entry 0.0678%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -525; harga snapshot 0.000005386154 SOL/token; range [-589, -525] (65 bin), downside 47.10%; bentuk BidAskImBalanced. Model bobot: active bin 0.0466% modal, lima bin terdekat 0.699%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499999869 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 54.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000194 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000098 SOL, PnL LP +0.000000096 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · DONO-SOL · 2nuf1iW5QR9K16PfRzmjqm2VCs9GY4WDVo7EZPyNw9oK

2026-09-17T04:05:17+07:00 → 2026-09-17T04:06:26+07:00 · 1.15 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 14.119; TVL $93904.40; fee/TVL entry 2.8275%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -471; harga snapshot 0.000009217920 SOL/token; range [-506, -471] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499997009 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001758895 SOL (0.3518% modal), divergence principal vs HOLD SOL -0.000002977 SOL, PnL LP +0.001755918 SOL (0.3512%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · DONO-SOL · 5NKDHwnmCDA1DyJxCVEuYLoHSVxpQjG1uDUpvzYjQdNt

2026-09-17T04:25:13+07:00 → 2026-09-17T04:28:54+07:00 · 3.68 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 11.157; TVL $45731.95; fee/TVL entry 0.8425%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -445; harga snapshot 0.000011939569 SOL/token; range [-514, -445] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.443780871 SOL + 5679.238397000 token. Porsi token pada mark withdrawal 10.55%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.52% → current 1.83% (dropped 0.69% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.014949521 SOL (2.9899% modal), divergence principal vs HOLD SOL -0.003868329 SOL, PnL LP +0.011081192 SOL (2.2162%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · DONO-SOL · 6jU6aEXbZYnF9RuaQ53nE6n6HMH3LMspmKze5o3FvPn7

2026-09-17T04:50:14+07:00 → 2026-09-17T04:51:26+07:00 · 1.20 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 11.917; TVL $35787.63; fee/TVL entry 3.7975%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -558; harga snapshot 0.000003878586 SOL/token; range [-627, -558] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999965 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · DONO-SOL · 7usmaLMqYLQV5Fqt9sn2PHQzFy3P5Sy2ppDrpnmWVtJL

2026-09-17T04:55:26+07:00 → 2026-09-17T05:06:34+07:00 · 11.13 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 14.543; TVL $37841.80; fee/TVL entry 2.3446%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -536; harga snapshot 0.000004827738 SOL/token; range [-605, -536] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.493947109 SOL + 1310.062770000 token. Porsi token pada mark withdrawal 1.18%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.05% → current 1.28% (dropped 0.77% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.010074715 SOL (2.0149% modal), divergence principal vs HOLD SOL -0.000153751 SOL, PnL LP +0.009920965 SOL (1.9842%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.009360538; setelah gas terhubung +0.009333906. Swap cocok unik, jeda 9 detik; selisih terhadap mark token -0.000560427 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · LEVERCAT-SOL · 6xyBSFsADYSJ1RgbXydJiFuPmJPHxx9p2zCFoKru5veM

2026-09-17T05:00:15+07:00 → 2026-09-17T05:04:52+07:00 · 4.62 menit · pool `42JnUXw5N9ftMkbM1tMzJw2tnzqs1U9RxWBk5LzNv4gD`.

1. **Market → volatilitas → depth:** Volatility feed 4.339; TVL $105744.79; fee/TVL entry 0.2151%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -297; harga snapshot 0.000052065733 SOL/token; range [-362, -297] (66 bin), downside 47.63%; bentuk BidAskImBalanced. Model bobot: active bin 0.0452% modal, lima bin terdekat 0.678%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499992753 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 25%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000537535 SOL (0.1075% modal), divergence principal vs HOLD SOL -0.000007217 SOL, PnL LP +0.000530318 SOL (0.1061%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · DONO-SOL · EUbozDP5Z7j2B9BpsvHio8RmfiTP5W22RELvWwfgvqfe

2026-09-17T05:08:11+07:00 → 2026-09-17T05:16:08+07:00 · 7.95 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 14.648; TVL $29523.36; fee/TVL entry 0.7100%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -555; harga snapshot 0.000003996111 SOL/token; range [-624, -555] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.443527595 SOL + 16405.776439000 token. Porsi token pada mark withdrawal 10.52%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.56% → current 0.36% (dropped 1.20% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006896466 SOL (1.3793% modal), divergence principal vs HOLD SOL -0.004323759 SOL, PnL LP +0.002572707 SOL (0.5145%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.003930077; setelah gas terhubung +0.003903841. Swap cocok unik, jeda 11 detik; selisih terhadap mark token +0.001357370 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · HUHCAT-SOL · 4NNV57shG1w4JjXx62SxT4ArcZ4PphJU14brghJMZqMk

2026-09-17T05:12:54+07:00 → 2026-09-17T05:22:59+07:00 · 10.08 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 1.955; TVL $22002.44; fee/TVL entry 0.1670%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -545; harga snapshot 0.000004414193 SOL/token; range [-593, -545] (49 bin), downside 37.97%; bentuk BidAskImBalanced. Model bobot: active bin 0.0816% modal, lima bin terdekat 1.224%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999976 SOL + 0.000000000 token; withdraw 0.499999926 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 6m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 40%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000031 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000050 SOL, PnL LP -0.000000019 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000019; setelah gas terhubung -0.000020019.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · DONO-SOL · 5Q2T46nDdjxnWVao3CbEGcDwQwCbUUryRXc8QzvnLZ8J

2026-09-17T05:23:30+07:00 → 2026-09-17T05:27:55+07:00 · 4.42 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 9.109; TVL $22427.05; fee/TVL entry 0.2066%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -546; harga snapshot 0.000004370488 SOL/token; range [-581, -546] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.429650493 SOL + 17467.669046000 token. Porsi token pada mark withdrawal 13.50%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.89% → current 1.17% (dropped 0.72% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.011702809 SOL (2.3406% modal), divergence principal vs HOLD SOL -0.003270426 SOL, PnL LP +0.008432383 SOL (1.6865%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.003767038; setelah gas terhubung +0.003741190. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.004665345 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · BUTTHOLE-SOL · E9b71KsFeFRsLPdgd6Dx8YG7KuHQhpcWXsg8nyJkxm8U

2026-09-17T05:40:10+07:00 → 2026-09-17T05:53:40+07:00 · 13.50 menit · pool `3T6pPCvChxMWvGavkyNSFN7UyiMeUwV3NbHHTybPogFC`.

1. **Market → volatilitas → depth:** Volatility feed 1.520; TVL $18677.94; fee/TVL entry 0.0611%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1079; harga snapshot 0.000021738906 SOL/token; range [-1124, -1079] (46 bin), downside 36.09%; bentuk BidAskImBalanced. Model bobot: active bin 0.0925% modal, lima bin terdekat 1.388%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499999909 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 61.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000019 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000068 SOL, PnL LP -0.000000049 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000049; setelah gas terhubung -0.000020049.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LEVERHEDGE-SOL · DV2xpPgqdUbCwyTZS6NQm1BGBtfNmP8vYvusrzghaULq

2026-09-17T05:53:24+07:00 → 2026-09-17T06:01:25+07:00 · 8.02 menit · pool `Fc6mmuQNKEoq6C7c1dwh6ppE54tEA2fTWs6ZjFvk4CdA`.

1. **Market → volatilitas → depth:** Volatility feed 5.058; TVL $18784.37; fee/TVL entry 0.2022%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -367; harga snapshot 0.000025945128 SOL/token; range [-436, -367] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499998354 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 6m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 25%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001436 SOL (0.0003% modal), divergence principal vs HOLD SOL -0.000001611 SOL, PnL LP -0.000000175 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000175; setelah gas terhubung -0.000020175.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · OTC-SOL · FKYm2sw6B3yX13pbcH74iG32jPUs8JdsPBCV2gqnUnfh

2026-09-17T06:05:20+07:00 → 2026-09-17T06:05:30+07:00 · 0.17 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 1.502; TVL $14861.19; fee/TVL entry 0.1251%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -352; harga snapshot 0.000030121488 SOL/token; range [-397, -352] (46 bin), downside 36.09%; bentuk BidAskImBalanced. Model bobot: active bin 0.0925% modal, lima bin terdekat 1.388%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499607400 SOL + 12.649100000 token. Porsi token pada mark withdrawal 0.08%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000011567 SOL, PnL LP -0.000011567 SOL (-0.0023%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLAME-SOL · 31aop6mRzyr7soN8Meroo683dDAmrRxrgpgq8uNtKL2s

2026-09-17T06:20:13+07:00 → 2026-09-17T06:22:07+07:00 · 1.90 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 5.743; TVL $18010.51; fee/TVL entry 0.1034%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -685; harga snapshot 0.000004261235 SOL/token; range [-754, -685] (70 bin), downside 42.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999957 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000008 SOL, PnL LP -0.000000008 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas -0.000000008; setelah gas terhubung -0.000015008.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ELON-SOL · 511tb5T5HtkcgqbTowZaXr6MtBWznQTaCYVBp6fMxSh4

2026-09-17T06:30:12+07:00 → 2026-09-17T06:41:21+07:00 · 11.15 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 2.317; TVL $83850.50; fee/TVL entry 0.1728%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -470; harga snapshot 0.000023634690 SOL/token; range [-506, -470] (37 bin), downside 24.94%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499990120 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 54.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000051591 SOL (0.0103% modal), divergence principal vs HOLD SOL -0.000009861 SOL, PnL LP +0.000041730 SOL (0.0083%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PURPS-SOL · 4deBwxijNcnuKKa8kQq8xQceMu6shKqyP3N4yP8jpGSX

2026-09-17T06:40:35+07:00 → 2026-09-17T06:40:47+07:00 · 0.20 menit · pool `5LjukK9FDhTo51wp2zkKdAgSk7yg4khr1v9d3HwKFsQJ`.

1. **Market → volatilitas → depth:** Volatility feed 10.554; TVL $24754.55; fee/TVL entry 0.5205%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -444; harga snapshot 0.000012058965 SOL/token; range [-513, -444] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499846470 SOL + 11.831188000 token. Porsi token pada mark withdrawal 0.03%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000010823 SOL, PnL LP -0.000010823 SOL (-0.0022%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LOOP-SOL · 4obYbwMDxMUgrRGQfYcA4QQ51pWckxVXQdMaMguggvT2

2026-09-17T06:45:16+07:00 → 2026-09-17T06:50:02+07:00 · 4.77 menit · pool `6gQTdHry76sCzBAeCR8f2EkNYpgWrJjwb9352mF9ts5i`.

1. **Market → volatilitas → depth:** Volatility feed 6.430; TVL $10354.21; fee/TVL entry 0.4169%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -453; harga snapshot 0.000011025992 SOL/token; range [-522, -453] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999741 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 50%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000192 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000224 SOL, PnL LP -0.000000032 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000032; setelah gas terhubung -0.000020032.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LEVERHEDGE-SOL · CUkv8muc4MMdsCLS5mQ25ULdfMvUJFw9Hq83YQa8rtGG

2026-09-17T06:59:25+07:00 → 2026-09-17T07:15:21+07:00 · 15.93 menit · pool `Fc6mmuQNKEoq6C7c1dwh6ppE54tEA2fTWs6ZjFvk4CdA`.

1. **Market → volatilitas → depth:** Volatility feed 3.219; TVL $27658.67; fee/TVL entry 0.1576%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -374; harga snapshot 0.000024199490 SOL/token; range [-431, -374] (58 bin), downside 43.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0584% modal, lima bin terdekat 0.877%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.499999970 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 68.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000038541 SOL (0.0077% modal), divergence principal vs HOLD SOL -0.000000001 SOL, PnL LP +0.000038540 SOL (0.0077%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LOOP-SOL · 2Eq6F9EsqBxExEdWos3oMPoWR7cTKYRXaSurLhXeafXg

2026-09-17T07:00:09+07:00 → 2026-09-17T07:08:15+07:00 · 8.10 menit · pool `6gQTdHry76sCzBAeCR8f2EkNYpgWrJjwb9352mF9ts5i`.

1. **Market → volatilitas → depth:** Volatility feed 5.747; TVL $10860.95; fee/TVL entry 0.1159%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -445; harga snapshot 0.000011939569 SOL/token; range [-484, -445] (40 bin), downside 32.16%; bentuk BidAskImBalanced. Model bobot: active bin 0.1220% modal, lima bin terdekat 1.829%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.499992540 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000058231 SOL (0.0116% modal), divergence principal vs HOLD SOL -0.000007440 SOL, PnL LP +0.000050791 SOL (0.0102%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ZEREBLAST-SOL · J9vJEnV5BGKi5TBDkqUhkbyCR55A8gDJSZxwWkQQhxrB

2026-09-17T07:11:26+07:00 → 2026-09-17T07:13:44+07:00 · 2.30 menit · pool `9EJVbU6r2eshpNLxvVEhL9Kzra5ob5TJSzaDb1Hy222q`.

1. **Market → volatilitas → depth:** Volatility feed 18.721; TVL $15802.65; fee/TVL entry 0.3600%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -520; harga snapshot 0.000005660902 SOL/token; range [-555, -520] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499999993 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000176331 SOL (0.0353% modal), divergence principal vs HOLD SOL 0.000000007 SOL, PnL LP +0.000176338 SOL (0.0353%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · LOOP-SOL · Gtp8rXNY9usJdeDS4L988bFWaF7KF4kr7GqsAwRUWTkj

2026-09-17T07:30:30+07:00 → 2026-09-17T07:39:07+07:00 · 8.62 menit · pool `6gQTdHry76sCzBAeCR8f2EkNYpgWrJjwb9352mF9ts5i`.

1. **Market → volatilitas → depth:** Volatility feed 5.170; TVL $12153.32; fee/TVL entry 0.2723%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -435; harga snapshot 0.000013188713 SOL/token; range [-473, -435] (39 bin), downside 31.48%; bentuk BidAskImBalanced. Model bobot: active bin 0.1282% modal, lima bin terdekat 1.923%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499986041 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000782636 SOL (0.1565% modal), divergence principal vs HOLD SOL -0.000013940 SOL, PnL LP +0.000768696 SOL (0.1537%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Noiz-SOL · H7JwXjP9YjhNxbDR6ebjs3KpPvPwu8cZQ8CgfABrUUhf

2026-09-17T07:45:11+07:00 → 2026-09-17T08:29:38+07:00 · 44.45 menit · pool `4YAs6WdHjCLxrnvfFaSXMj12KwLF1ioyXmLZ1ENbBDEB`.

1. **Market → volatilitas → depth:** Volatility feed 2.990; TVL $10703.58; fee/TVL entry 0.2084%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -561; harga snapshot 0.000003764517 SOL/token; range [-616, -561] (56 bin), downside 42.15%; bentuk BidAskImBalanced. Model bobot: active bin 0.0627% modal, lima bin terdekat 0.940%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.428789568 SOL + 21602.015046000 token. Porsi token pada mark withdrawal 13.45%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.37% → current 0.55% (dropped 0.82% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.007622402 SOL (1.5245% modal), divergence principal vs HOLD SOL -0.004564096 SOL, PnL LP +0.003058306 SOL (0.6117%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001610986; setelah gas terhubung +0.001585678. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.001447320 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FLAME-SOL · FNcCGHfReUterEAPVyVsnzuFCRwsFc1DLWaaHBmNp9SZ

2026-09-17T08:00:09+07:00 → 2026-09-17T08:07:42+07:00 · 7.55 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 2.981; TVL $22550.20; fee/TVL entry 0.0775%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -672; harga snapshot 0.000004726312 SOL/token; range [-727, -672] (56 bin), downside 35.48%; bentuk BidAskImBalanced. Model bobot: active bin 0.0627% modal, lima bin terdekat 0.940%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499999971 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000001 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000001 SOL, PnL LP -0.000000000 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000000; setelah gas terhubung -0.000020000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLAME-SOL · 6xh9kbkA7yxYychg4LMevrqeESrbvRmWcADfELHtHVKv

2026-09-17T08:18:16+07:00 → 2026-09-17T08:19:22+07:00 · 1.10 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 3.363; TVL $23238.24; fee/TVL entry 0.2752%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -650; harga snapshot 0.000005631890 SOL/token; range [-708, -650] (59 bin), downside 37.01%; bentuk BidAskImBalanced. Model bobot: active bin 0.0565% modal, lima bin terdekat 0.847%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499996053 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000003478 SOL (0.0007% modal), divergence principal vs HOLD SOL -0.000003919 SOL, PnL LP -0.000000441 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000441; setelah gas terhubung -0.000020441.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LEVERHEDGE-SOL · HLqqHhKNpbZoXrCDziSiDxMDXXuFqLhW7hbUDpuCDtqD

2026-09-17T08:45:56+07:00 → 2026-09-17T08:51:20+07:00 · 5.40 menit · pool `Fc6mmuQNKEoq6C7c1dwh6ppE54tEA2fTWs6ZjFvk4CdA`.

1. **Market → volatilitas → depth:** Volatility feed 6.666; TVL $42636.01; fee/TVL entry 0.3134%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -382; harga snapshot 0.000022347823 SOL/token; range [-451, -382] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499998755 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001083 SOL (0.0002% modal), divergence principal vs HOLD SOL -0.000001210 SOL, PnL LP -0.000000127 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000127; setelah gas terhubung -0.000020127.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · KEVIN-SOL · GwBruUZVXbDxwTb3uGBYLPAHVYyt71CpkadSbhBxMxer

2026-09-17T11:06:36+07:00 → 2026-09-17T11:21:09+07:00 · 14.55 menit · pool `4bDCwoR6TZdiUAQd6vjEYYFkV6mqykdgQ6WaT6JUy8Th`.

1. **Market → volatilitas → depth:** Volatility feed 8.019; TVL $17704.93; fee/TVL entry 0.3005%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -512; harga snapshot 0.000006129946 SOL/token; range [-581, -512] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.393762261 SOL + 21349.129304000 token. Porsi token pada mark withdrawal 19.47%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.85% → current 1.59% (dropped 1.26% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.018754584 SOL (3.7509% modal), divergence principal vs HOLD SOL -0.011056142 SOL, PnL LP +0.007698443 SOL (1.5397%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.009366960; setelah gas terhubung +0.009339913. Swap cocok unik, jeda 8 detik; selisih terhadap mark token +0.001668517 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · DCBVpK3qBoKqeiWqTxuaA1SymBT1S43my4nDD2YbP14

2026-09-17T11:10:36+07:00 → 2026-09-17T11:11:15+07:00 · 0.65 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 1.687; TVL $37063.86; fee/TVL entry 0.0652%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -378; harga snapshot 0.000023255234 SOL/token; range [-414, -378] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499466830 SOL + 22.453653000 token. Porsi token pada mark withdrawal 0.10%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000010986 SOL, PnL LP -0.000010986 SOL (-0.0022%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · KEVIN-SOL · BrMis97BGdW1Hr2f7fPs4jxqqb2mug475nAMU8GbmhYX

2026-09-17T11:30:15+07:00 → 2026-09-17T12:03:57+07:00 · 33.70 menit · pool `4bDCwoR6TZdiUAQd6vjEYYFkV6mqykdgQ6WaT6JUy8Th`.

1. **Market → volatilitas → depth:** Volatility feed 8.329; TVL $14225.07; fee/TVL entry 0.6883%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -543; harga snapshot 0.000004502918 SOL/token; range [-634, -543] (92 bin), downside 59.57%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499999806 SOL + 0.000000000 token; withdraw 0.368157038 SOL + 39973.757008000 token. Porsi token pada mark withdrawal 23.45%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.84% → current 1.16% (dropped 0.68% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.019133540 SOL (3.8267% modal), divergence principal vs HOLD SOL -0.019080335 SOL, PnL LP +0.000053205 SOL (0.0106%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil dalam SOL sebelum gas -0.007631101; setelah gas terhubung -0.007680416. Swap cocok unik, jeda 12 detik; selisih terhadap mark token -0.007684306 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · KEVIN-SOL · GpNs4XWkQzruV6pL7QUoa3QhXbymoPSRmyBMhQeXqgPE

2026-09-17T12:05:17+07:00 → 2026-09-17T12:10:58+07:00 · 5.68 menit · pool `4bDCwoR6TZdiUAQd6vjEYYFkV6mqykdgQ6WaT6JUy8Th`.

1. **Market → volatilitas → depth:** Volatility feed 5.434; TVL $12366.47; fee/TVL entry 0.3719%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -592; harga snapshot 0.000002765328 SOL/token; range [-658, -586] (73 bin), downside 51.15%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499998316 SOL + 0.000000000 token; withdraw 0.499998316 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000030000 SOL. Hasil dalam SOL sebelum gas -0.000000000; setelah gas terhubung -0.000030000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · WISH-SOL · 63cFQywBPBLmqcBbbPQtiG7BeMTMmqfSs6mc3wbXxpQR

2026-09-17T12:10:14+07:00 → 2026-09-17T12:10:45+07:00 · 0.52 menit · pool `vhimiWAiS12txu5Wj4EEZmyqf1CJK3KmSTvubmmTHT4`.

1. **Market → volatilitas → depth:** Volatility feed 12.937; TVL $19714.73; fee/TVL entry 2.0420%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -480; harga snapshot 0.000008428312 SOL/token; range [-549, -480] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999965 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000019482 SOL (0.0039% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000019482 SOL (0.0039%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · lockinu-SOL · 8w5dii3ds3dGxaEuToPziVAaCPn5HzyqqBThiwY79aHe

2026-09-17T12:15:34+07:00 → 2026-09-17T14:04:50+07:00 · 109.27 menit · pool `9PxMQ7Ny9NMurjKwSQMeNrE9yvdML6HVCXo8EzedLvJw`.

1. **Market → volatilitas → depth:** Volatility feed 2.039; TVL $11576.28; fee/TVL entry 0.1402%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -581; harga snapshot 0.000003085189 SOL/token; range [-630, -581] (50 bin), downside 38.59%; bentuk BidAskImBalanced. Model bobot: active bin 0.0784% modal, lima bin terdekat 1.176%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999975 SOL + 0.000000000 token; withdraw 0.500074268 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 7m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 93.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.009159543 SOL (1.8319% modal), divergence principal vs HOLD SOL 0.000074293 SOL, PnL LP +0.009233836 SOL (1.8468%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.009064322; setelah gas terhubung +0.009037477. Swap cocok unik, jeda 8 detik; selisih terhadap mark token -0.000169514 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · WISH-SOL · AFpE4d6sAgoe1sWzG1sUAMoQDqiqBffbGAwLhdSgHPY7

2026-09-17T12:33:34+07:00 → 2026-09-17T12:39:57+07:00 · 6.38 menit · pool `vhimiWAiS12txu5Wj4EEZmyqf1CJK3KmSTvubmmTHT4`.

1. **Market → volatilitas → depth:** Volatility feed 10.200; TVL $30641.01; fee/TVL entry 0.5941%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -509; harga snapshot 0.000006315689 SOL/token; range [-578, -509] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.416364590 SOL + 15912.337703000 token. Porsi token pada mark withdrawal 15.45%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.25% → current 0.36% (dropped 0.89% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.008303540 SOL (1.6607% modal), divergence principal vs HOLD SOL -0.007575385 SOL, PnL LP +0.000728155 SOL (0.1456%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · WISH-SOL · 3tvtkAgocA5EXmVtJTkaHVGeCx6G6YVXLaWxwayEoVUT

2026-09-17T12:40:52+07:00 → 2026-09-17T12:44:53+07:00 · 4.02 menit · pool `vhimiWAiS12txu5Wj4EEZmyqf1CJK3KmSTvubmmTHT4`.

1. **Market → volatilitas → depth:** Volatility feed 9.384; TVL $18375.65; fee/TVL entry 4.0452%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -535; harga snapshot 0.000004876015 SOL/token; range [-576, -535] (42 bin), downside 33.50%; bentuk BidAskImBalanced. Model bobot: active bin 0.1107% modal, lima bin terdekat 1.661%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.144022320 SOL + 92022.284385000 token. Porsi token pada mark withdrawal 68.74%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.85% → current -2.03% (dropped 3.88% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.025510765 SOL (5.1022% modal), divergence principal vs HOLD SOL -0.039232521 SOL, PnL LP -0.013721757 SOL (-2.7444%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.018895114; setelah gas terhubung -0.018920696. Swap cocok unik, jeda 14 detik; selisih terhadap mark token -0.005173357 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · baton-SOL · 7RjWxuigB86nW6nUNb4eFvqg9qPw3qn1NVouF5zhbYdJ

2026-09-17T14:10:13+07:00 → 2026-09-17T14:32:22+07:00 · 22.15 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 3.270; TVL $64041.81; fee/TVL entry 0.1320%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -362; harga snapshot 0.000027268591 SOL/token; range [-419, -362] (58 bin), downside 43.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0584% modal, lima bin terdekat 0.877%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.499999795 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 6m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 72.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000003135 SOL (0.0006% modal), divergence principal vs HOLD SOL -0.000000176 SOL, PnL LP +0.000002959 SOL (0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000002959; setelah gas terhubung -0.000017041.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · WANG-SOL · E2bEGWZhgzviH5nwZe9aPw8Z3UPDGa6KUDwWVBLQAXEo

2026-09-17T14:21:42+07:00 → 2026-09-17T14:24:43+07:00 · 3.02 menit · pool `8ACe6Q57ULDvEbdo4QjhtE5BzuqCXuqNJZdnzw7jT9tu`.

1. **Market → volatilitas → depth:** Volatility feed 17.851; TVL $61336.25; fee/TVL entry 0.0544%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -519; harga snapshot 0.000005717511 SOL/token; range [-554, -519] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.131357572 SOL + 79448.374344000 token. Porsi token pada mark withdrawal 71.75%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** take profit
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.017424341 SOL (3.4849% modal), divergence principal vs HOLD SOL -0.034962982 SOL, PnL LP -0.017538641 SOL (-3.5077%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.002383560; setelah gas terhubung -0.002428303. Swap cocok unik, jeda 9 detik; selisih terhadap mark token +0.015155081 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · WANG-SOL · 8Zpb9qMW2GFCgs9S5jAySZLrUEWbJUo2yMRnxw2iUnVu

2026-09-17T14:27:12+07:00 → 2026-09-17T14:27:34+07:00 · 0.37 menit · pool `8ACe6Q57ULDvEbdo4QjhtE5BzuqCXuqNJZdnzw7jT9tu`.

1. **Market → volatilitas → depth:** Volatility feed 16.523; TVL $49506.10; fee/TVL entry 0.3279%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -532; harga snapshot 0.000005023763 SOL/token; range [-601, -532] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499633456 SOL + 72.360706000 token. Porsi token pada mark withdrawal 0.07%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000017707 SOL (0.0035% modal), divergence principal vs HOLD SOL -0.000006585 SOL, PnL LP +0.000011121 SOL (0.0022%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · WANG-SOL · CbK15mngfKt7VEVVJ5VeZQh91Vie4M4buVkP2CnLyqtb

2026-09-17T14:35:14+07:00 → 2026-09-17T14:37:30+07:00 · 2.27 menit · pool `8ACe6Q57ULDvEbdo4QjhtE5BzuqCXuqNJZdnzw7jT9tu`.

1. **Market → volatilitas → depth:** Volatility feed 12.777; TVL $39396.62; fee/TVL entry 3.3150%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -552; harga snapshot 0.000004117197 SOL/token; range [-596, -552] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499990094 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 50%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000029386 SOL (0.0059% modal), divergence principal vs HOLD SOL -0.000009883 SOL, PnL LP +0.000019503 SOL (0.0039%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · baton-SOL · 4kWRxTy5FepTHJCRUpHcbQukHpxhM45c5nSZNmqTzsbP

2026-09-17T15:10:22+07:00 → 2026-09-17T15:21:03+07:00 · 10.68 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 1.723; TVL $66272.51; fee/TVL entry 0.0971%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -344; harga snapshot 0.000032617256 SOL/token; range [-391, -344] (48 bin), downside 37.35%; bentuk BidAskImBalanced. Model bobot: active bin 0.0850% modal, lima bin terdekat 1.276%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499994392 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 7m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 30%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000004961 SOL (0.0010% modal), divergence principal vs HOLD SOL -0.000005585 SOL, PnL LP -0.000000624 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000624; setelah gas terhubung -0.000020624.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · biketyson-SOL · HwjuhRBhMerGiTKRF332PPsUWQeqryoD2kVFyBo62FSM

2026-09-17T15:22:47+07:00 → 2026-09-17T15:22:56+07:00 · 0.15 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 1.149; TVL $27953.17; fee/TVL entry 0.0525%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -374; harga snapshot 0.000024199490 SOL/token; range [-410, -374] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499522596 SOL + 19.214445000 token. Porsi token pada mark withdrawal 0.09%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000739 SOL (0.0001% modal), divergence principal vs HOLD SOL -0.000012405 SOL, PnL LP -0.000011666 SOL (-0.0023%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · biketyson-SOL · 5uqm6tq24h7hpn8RHqAqr2YW3nNNdeLTxMAn4n85iFAm

2026-09-17T15:56:03+07:00 → 2026-09-17T16:28:26+07:00 · 32.38 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 1.849; TVL $28903.66; fee/TVL entry 0.0525%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -362; harga snapshot 0.000027268591 SOL/token; range [-410, -362] (49 bin), downside 37.97%; bentuk BidAskImBalanced. Model bobot: active bin 0.0816% modal, lima bin terdekat 1.224%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999976 SOL + 0.000000000 token; withdraw 0.499994439 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 84.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000112960 SOL (0.0226% modal), divergence principal vs HOLD SOL -0.000005537 SOL, PnL LP +0.000107423 SOL (0.0215%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PERPSPAD-SOL · 9xc5f3i2z92tSruJrQP4jacqdMttKu18GP5H2BB6Fn9e

2026-09-17T16:00:12+07:00 → 2026-09-17T16:08:56+07:00 · 8.73 menit · pool `EHqk4Fw3pTCf9UW75dWoCMf6a2GxyJ8FGYEj2Qmw9rfr`.

1. **Market → volatilitas → depth:** Volatility feed 2.941; TVL $137656.40; fee/TVL entry 0.0940%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -340; harga snapshot 0.000066591544 SOL/token; range [-395, -340] (56 bin), downside 35.48%; bentuk BidAskImBalanced. Model bobot: active bin 0.0627% modal, lima bin terdekat 0.940%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499996632 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 50%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000141312 SOL (0.0283% modal), divergence principal vs HOLD SOL -0.000003340 SOL, PnL LP +0.000137972 SOL (0.0276%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PURPS-SOL · 8FdfBUZfMpBFQZ1Nf9cn3CADcWa4qeCdekn6ZGvXJpys

2026-09-17T16:11:04+07:00 → 2026-09-17T16:25:06+07:00 · 14.03 menit · pool `5LjukK9FDhTo51wp2zkKdAgSk7yg4khr1v9d3HwKFsQJ`.

1. **Market → volatilitas → depth:** Volatility feed 8.443; TVL $22504.47; fee/TVL entry 0.1531%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -467; harga snapshot 0.000009592205 SOL/token; range [-536, -467] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999351 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 64.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000500 SOL (0.0001% modal), divergence principal vs HOLD SOL -0.000000614 SOL, PnL LP -0.000000114 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000114; setelah gas terhubung -0.000020114.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · biketyson-SOL · 7QDHTQf5wnKbXGJWPtKEz5DkHyavCXwEvomTPUreWeiC

2026-09-17T16:45:31+07:00 → 2026-09-17T17:45:48+07:00 · 60.28 menit · pool `73SXBZfHzrsFmwU6RpvR4dTPzSdsNB66PaaUqtzEL9qt`.

1. **Market → volatilitas → depth:** Volatility feed 1.411; TVL $31648.79; fee/TVL entry 0.0708%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -364; harga snapshot 0.000026731292 SOL/token; range [-409, -364] (46 bin), downside 36.09%; bentuk BidAskImBalanced. Model bobot: active bin 0.0925% modal, lima bin terdekat 1.388%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499614276 SOL + 14.081133000 token. Porsi token pada mark withdrawal 0.08%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 2.45% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000518553 SOL (0.1037% modal), divergence principal vs HOLD SOL -0.000009294 SOL, PnL LP +0.000509259 SOL (0.1019%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · PURPS-SOL · G3Nu9u5JwBXBcuc3rWdkDUY9Pzia25tMVXGoyhVMZ67v

2026-09-17T16:50:16+07:00 → 2026-09-17T17:08:37+07:00 · 18.35 menit · pool `5LjukK9FDhTo51wp2zkKdAgSk7yg4khr1v9d3HwKFsQJ`.

1. **Market → volatilitas → depth:** Volatility feed 5.629; TVL $19006.20; fee/TVL entry 0.4270%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -470; harga snapshot 0.000009310099 SOL/token; range [-539, -470] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499996783 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 72.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000002614 SOL (0.0005% modal), divergence principal vs HOLD SOL -0.000003182 SOL, PnL LP -0.000000568 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000568; setelah gas terhubung -0.000020568.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · DONO-SOL · E69quR1EW5QZMmSyHuJRgnT12V3Rwsw8pR5RroAARbnn

2026-09-17T17:30:31+07:00 → 2026-09-17T17:37:31+07:00 · 7.00 menit · pool `2aCnxjDkBrucj9FMUfQX6ow72UaNxhin3r4HiHv714J2`.

1. **Market → volatilitas → depth:** Volatility feed 4.505; TVL $12056.94; fee/TVL entry 0.2013%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -570; harga snapshot 0.000003442048 SOL/token; range [-636, -570] (67 bin), downside 48.15%; bentuk BidAskImBalanced. Model bobot: active bin 0.0439% modal, lima bin terdekat 0.658%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499990229 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000008367 SOL (0.0017% modal), divergence principal vs HOLD SOL -0.000009738 SOL, PnL LP -0.000001371 SOL (-0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001371; setelah gas terhubung -0.000021371.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MANLET-SOL · 37ED8GXzsQQ5nXdxB47xk2iFtpq1VixwpmJpaF45E1GT

2026-09-17T17:43:53+07:00 → 2026-09-17T17:57:55+07:00 · 14.03 menit · pool `68C62WPYiiNZxprbuaMj2ULXpiTDKcs5xsX7kBGnyajR`.

1. **Market → volatilitas → depth:** Volatility feed 2.798; TVL $21590.14; fee/TVL entry 0.0503%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1494; harga snapshot 0.000006760285 SOL/token; range [-1548, -1494] (55 bin), downside 34.97%; bentuk BidAskImBalanced. Model bobot: active bin 0.0649% modal, lima bin terdekat 0.974%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.499997368 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 64.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000002034 SOL (0.0004% modal), divergence principal vs HOLD SOL -0.000002603 SOL, PnL LP -0.000000569 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000569; setelah gas terhubung -0.000020569.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · HUHCAT-SOL · EfJXGn8rjW6w5QZUqZEqYQE5AzdEhM86kKP2wN1SXC9o

2026-09-17T17:57:31+07:00 → 2026-09-17T18:30:06+07:00 · 32.58 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 2.478; TVL $21790.22; fee/TVL entry 0.1300%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -504; harga snapshot 0.000006637853 SOL/token; range [-556, -504] (53 bin), downside 40.39%; bentuk BidAskImBalanced. Model bobot: active bin 0.0699% modal, lima bin terdekat 1.048%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.500001709 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 84.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000762991 SOL (0.1526% modal), divergence principal vs HOLD SOL 0.000001723 SOL, PnL LP +0.000764714 SOL (0.1529%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FLAME-SOL · DNpEM3Fc2KhbhzBXPkfpb93XXVZaypbjhc5rjqGtrm8j

2026-09-17T18:29:13+07:00 → 2026-09-17T19:02:46+07:00 · 33.55 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 3.546; TVL $34123.76; fee/TVL entry 0.1079%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -631; harga snapshot 0.000006552458 SOL/token; range [-690, -631] (60 bin), downside 37.51%; bentuk BidAskImBalanced. Model bobot: active bin 0.0546% modal, lima bin terdekat 0.820%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999973 SOL + 0.000000000 token; withdraw 0.499995199 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 84.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000575141 SOL (0.1150% modal), divergence principal vs HOLD SOL -0.000004774 SOL, PnL LP +0.000570367 SOL (0.1141%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SI-SOL · F9SCJt4CbFwsKtvpVLqoUdk4GK9UCv2duoP7jP8sGgtW

2026-09-17T18:42:49+07:00 → 2026-09-17T18:50:48+07:00 · 7.98 menit · pool `DdQXnjqzjU2zuMEp23mn58FJwnAxfFeEC2GrRS2xyJWy`.

1. **Market → volatilitas → depth:** Volatility feed 9.312; TVL $11416.52; fee/TVL entry 0.4617%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -585; harga snapshot 0.000002964806 SOL/token; range [-620, -585] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 213493.223404000 token. Porsi token pada mark withdrawal 100.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.15% → current 0.68% (dropped 1.47% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.027512385 SOL (5.5025% modal), divergence principal vs HOLD SOL -0.079075581 SOL, PnL LP -0.051563196 SOL (-10.3126%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.048764004; setelah gas terhubung -0.048789337. Swap cocok unik, jeda 8 detik; selisih terhadap mark token +0.002799192 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · CTO-SOL · 8bQJNv2cTWbE1fUZAeV2tnb2xUS1pC8TgAyKw9qfZcYf

2026-09-17T19:30:17+07:00 → 2026-09-17T20:24:15+07:00 · 53.97 menit · pool `54sbyULrreD9HBoV5wRWedeCBEw6gQ7VkdHW18rLX78e`.

1. **Market → volatilitas → depth:** Volatility feed 3.045; TVL $10713.43; fee/TVL entry 0.2125%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1291; harga snapshot 0.000002636978 SOL/token; range [-1347, -1291] (57 bin), downside 42.72%; bentuk BidAskImBalanced. Model bobot: active bin 0.0605% modal, lima bin terdekat 0.907%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499995753 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 90.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000966883 SOL (0.1934% modal), divergence principal vs HOLD SOL -0.000004219 SOL, PnL LP +0.000962664 SOL (0.1925%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · UBI-SOL · F3B1ZiDXqZuo9q4X1kG28j3UuyPWCd2q4JhBzLk5aVju

2026-09-17T19:45:04+07:00 → 2026-09-17T21:01:28+07:00 · 76.40 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 0.575; TVL $23163.61; fee/TVL entry 0.1409%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1210; harga snapshot 0.000005903883 SOL/token; range [-1249, -1210] (40 bin), downside 32.16%; bentuk BidAskImBalanced. Model bobot: active bin 0.1220% modal, lima bin terdekat 1.829%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.375542516 SOL + 23900.584016403 token. Porsi token pada mark withdrawal 23.72%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.21% → current -0.43% (dropped 1.64% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.010616595 SOL (2.1233% modal), divergence principal vs HOLD SOL -0.007658192 SOL, PnL LP +0.002958403 SOL (0.5917%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.001373509; setelah gas terhubung -0.001399236. Swap cocok unik, jeda 7 detik; selisih terhadap mark token -0.004331912 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ALL-SOL · 74ntUApPNJkR8rQYzLmWDFa8oyyjGBQ8vjmeAtcxEz5U

2026-09-17T20:30:23+07:00 → 2026-09-17T21:22:40+07:00 · 52.28 menit · pool `FpP5SnzBnHJ5M9wS7fCuYiiSuXUPLNQKpk7qndeZxKZZ`.

1. **Market → volatilitas → depth:** Volatility feed 1.990; TVL $29129.04; fee/TVL entry 0.0990%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -548; harga snapshot 0.000004284372 SOL/token; range [-583, -548] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499995588 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 90.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000610973 SOL (0.1222% modal), divergence principal vs HOLD SOL -0.000004398 SOL, PnL LP +0.000606575 SOL (0.1213%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SEND-SOL · 9qQF9EHj8o9PK8283tS4QRxQWF6dv6ciqAsChE8Qsw2Y

2026-09-17T21:11:15+07:00 → 2026-09-17T21:21:36+07:00 · 10.35 menit · pool `9x4aKowDDz2yBNXW1ER7LZs6XJ3gxdWuy6fQtMLLa3y4`.

1. **Market → volatilitas → depth:** Volatility feed 10.891; TVL $126667.28; fee/TVL entry 0.1851%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -469; harga snapshot 0.000009403200 SOL/token; range [-538, -469] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.455008190 SOL + 5546.248913000 token. Porsi token pada mark withdrawal 8.43%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.36% → current 0.75% (dropped 0.61% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006422413 SOL (1.2845% modal), divergence principal vs HOLD SOL -0.003092663 SOL, PnL LP +0.003329750 SOL (0.6660%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.003294171; setelah gas terhubung +0.003184486. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.000035579 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SEND-SOL · 2PGrMRthwygQfMZC63AegVFfeyboeAQj3qRpv3att1Bt

2026-09-17T21:30:13+07:00 → 2026-09-17T21:38:33+07:00 · 8.33 menit · pool `9x4aKowDDz2yBNXW1ER7LZs6XJ3gxdWuy6fQtMLLa3y4`.

1. **Market → volatilitas → depth:** Volatility feed 8.304; TVL $142833.08; fee/TVL entry 0.4854%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -509; harga snapshot 0.000006315689 SOL/token; range [-578, -509] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499993970 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 62.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000140567 SOL (0.0281% modal), divergence principal vs HOLD SOL -0.000005995 SOL, PnL LP +0.000134572 SOL (0.0269%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SEND-SOL · HzvzTZ5jTzappCL5aVruzA3qCLiqiaViC241M3M4exmh

2026-09-17T21:41:43+07:00 → 2026-09-17T22:01:49+07:00 · 20.10 menit · pool `9x4aKowDDz2yBNXW1ER7LZs6XJ3gxdWuy6fQtMLLa3y4`.

1. **Market → volatilitas → depth:** Volatility feed 5.022; TVL $95626.01; fee/TVL entry 0.4836%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -513; harga snapshot 0.000006069253 SOL/token; range [-582, -513] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.476585295 SOL + 4274.197590000 token. Porsi token pada mark withdrawal 4.48%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.65% → current 0.97% (dropped 0.68% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.009925803 SOL (1.9852% modal), divergence principal vs HOLD SOL -0.001070244 SOL, PnL LP +0.008855559 SOL (1.7711%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · OTC-SOL · 5GAJj3C47bbNo58QQvGjeEK9zWS698aGT23wPGXikbcR

2026-09-17T21:45:16+07:00 → 2026-09-17T22:46:19+07:00 · 61.05 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 1.855; TVL $19478.77; fee/TVL entry 0.0710%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -278; harga snapshot 0.000062901078 SOL/token; range [-314, -278] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.492887675 SOL + 115.071563000 token. Porsi token pada mark withdrawal 1.41%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 5.14% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001083580 SOL (0.2167% modal), divergence principal vs HOLD SOL -0.000087053 SOL, PnL LP +0.000996527 SOL (0.1993%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · MINI-SOL · 7LdZiTJKnBnxG4UY6jofvYcvv5RPSWkf4pLzdZAM7UZb

2026-09-17T22:30:22+07:00 → 2026-09-17T22:30:32+07:00 · 0.17 menit · pool `64BSmy7BESiHnWYzLdPso6FuXymh7H8jTkaiyfbBg1YD`.

1. **Market → volatilitas → depth:** Volatility feed 0.878; TVL $35563.15; fee/TVL entry 0.1004%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -275; harga snapshot 0.000032837209 SOL/token; range [-310, -275] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499965428 SOL + 0.998763000 token. Porsi token pada mark withdrawal 0.01%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000001761 SOL, PnL LP -0.000001761 SOL (-0.0004%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · PURPS-SOL · EtoCo9s1KcZ3nZ8taHdj8fmCYekaGcwXRdK6kk9XhsrG

2026-09-17T23:05:11+07:00 → 2026-09-17T23:12:56+07:00 · 7.75 menit · pool `5LjukK9FDhTo51wp2zkKdAgSk7yg4khr1v9d3HwKFsQJ`.

1. **Market → volatilitas → depth:** Volatility feed 4.337; TVL $17660.16; fee/TVL entry 0.4011%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -462; harga snapshot 0.000010081504 SOL/token; range [-525, -462] (64 bin), downside 46.57%; bentuk BidAskImBalanced. Model bobot: active bin 0.0481% modal, lima bin terdekat 0.721%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499992764 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000009369 SOL (0.0019% modal), divergence principal vs HOLD SOL -0.000007206 SOL, PnL LP +0.000002163 SOL (0.0004%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000002163; setelah gas terhubung -0.000017837.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FRIES-SOL · 4SNRcfqs4EXciEzaHN4FkucikmadFiKrixgXhbZhLq6n

2026-09-17T23:15:17+07:00 → 2026-09-18T01:01:02+07:00 · 105.75 menit · pool `5QpDQ6ddkv1ArytJQ991kh8doeXPrt9hHFWK2HmEToDm`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $14615.61; fee/TVL entry 0.1424%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1224; harga snapshot 0.000005136159 SOL/token; range [-1269, -1224] (46 bin), downside 36.09%; bentuk BidAskImBalanced. Model bobot: active bin 0.0925% modal, lima bin terdekat 1.388%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499990185 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 95.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.005222065 SOL (1.0444% modal), divergence principal vs HOLD SOL -0.000009792 SOL, PnL LP +0.005212273 SOL (1.0425%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.005212273; setelah gas terhubung +0.005192273.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · NEARKAT-SOL · 87L4yykgC8DJWViB5svupCxiAAuqKsjrZSX5wMG9tNMV

2026-09-17T23:41:45+07:00 → 2026-09-17T23:56:41+07:00 · 14.93 menit · pool `B8BH6ZKr64agqNWG51CQWUKrLZZw5L31u2K6hubsZfyf`.

1. **Market → volatilitas → depth:** Volatility feed 8.649; TVL $136795.56; fee/TVL entry 0.0639%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -230; harga snapshot 0.000101410758 SOL/token; range [-265, -230] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.417936491 SOL + 884.541871000 token. Porsi token pada mark withdrawal 15.73%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.78% → current 0.99% (dropped 0.79% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.008581698 SOL (1.7163% modal), divergence principal vs HOLD SOL -0.004026023 SOL, PnL LP +0.004555675 SOL (0.9111%). Gas transaksi posisi yang terhubung 0.000025000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SUUB-SOL · 4Cfe95p4GWqKX84aKaVM3Nr4fNpUtNMMw5zbbVPXcV8Z

2026-09-18T00:30:15+07:00 → 2026-09-18T00:32:42+07:00 · 2.45 menit · pool `25XBgCNPhiqi2BmD2toUpitqcaycmENBcs16yarphy3w`.

1. **Market → volatilitas → depth:** Volatility feed 13.506; TVL $30200.63; fee/TVL entry 2.5117%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -540; harga snapshot 0.000004639361 SOL/token; range [-575, -540] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.349749881 SOL + 36667.985393000 token. Porsi token pada mark withdrawal 28.70%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.30% → current 0.33% (dropped 0.97% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.014321638 SOL (2.8643% modal), divergence principal vs HOLD SOL -0.009438287 SOL, PnL LP +0.004883351 SOL (0.9767%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000027531; setelah gas terhubung -0.000055561. Swap cocok unik, jeda 7 detik; selisih terhadap mark token -0.004910882 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SUUB-SOL · 3Z9JDRyBfHamAZwr8GEtq6eyKkgW9RHx6i8HJt5KA4Fa

2026-09-18T00:35:14+07:00 → 2026-09-18T00:36:17+07:00 · 1.05 menit · pool `25XBgCNPhiqi2BmD2toUpitqcaycmENBcs16yarphy3w`.

1. **Market → volatilitas → depth:** Volatility feed 13.900; TVL $31890.85; fee/TVL entry 2.1129%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -536; harga snapshot 0.000004827738 SOL/token; range [-605, -536] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999964 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000793 SOL (0.0002% modal), divergence principal vs HOLD SOL -0.000000001 SOL, PnL LP +0.000000792 SOL (0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000000792; setelah gas terhubung -0.000019208.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · SUUB-SOL · 4dQ51jXmVgRKzZwrQyfAiugJZVPSTQYqj2ugFonn4Bfn

2026-09-18T00:46:24+07:00 → 2026-09-18T00:53:22+07:00 · 6.97 menit · pool `25XBgCNPhiqi2BmD2toUpitqcaycmENBcs16yarphy3w`.

1. **Market → volatilitas → depth:** Volatility feed 12.180; TVL $28604.99; fee/TVL entry 0.0763%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -552; harga snapshot 0.000004117197 SOL/token; range [-621, -552] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500000269 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 85.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.004128973 SOL (0.8258% modal), divergence principal vs HOLD SOL 0.000000304 SOL, PnL LP +0.004129277 SOL (0.8259%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.004129277; setelah gas terhubung +0.004109277.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · OTC-SOL · 7zfU4b6KwS59kZCrG2VP8VjtzXmt85fu2ScV7DtjmhuS

2026-09-18T01:05:37+07:00 → 2026-09-18T02:07:38+07:00 · 62.02 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 3.928; TVL $19740.17; fee/TVL entry 0.1610%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -303; harga snapshot 0.000049048276 SOL/token; range [-338, -303] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.497749194 SOL + 46.195604000 token. Porsi token pada mark withdrawal 0.45%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 2.75% < min 7% (age: 61m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000591288 SOL (0.1183% modal), divergence principal vs HOLD SOL -0.000007411 SOL, PnL LP +0.000583877 SOL (0.1168%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000554111; setelah gas terhubung +0.000524040. Swap cocok unik, jeda 7 detik; selisih terhadap mark token -0.000029766 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · CLANKER-SOL · HG9i8aW4yZi1z6SjRyyN7q5V7XtksTzbXM6hLNp61AAg

2026-09-18T01:24:54+07:00 → 2026-09-18T01:54:11+07:00 · 29.28 menit · pool `9aXA6qqqXueA6Eq9WPRgas4wQgjPCEspzutbaS3UZkXT`.

1. **Market → volatilitas → depth:** Volatility feed 4.145; TVL $11456.55; fee/TVL entry 0.3896%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1176; harga snapshot 0.000008280650 SOL/token; range [-1239, -1176] (64 bin), downside 46.57%; bentuk BidAskImBalanced. Model bobot: active bin 0.0481% modal, lima bin terdekat 0.721%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.467555733 SOL + 4329.558735796 token. Porsi token pada mark withdrawal 6.20%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 3.32% → current 2.60% (dropped 0.72% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.016214986 SOL (3.2430% modal), divergence principal vs HOLD SOL -0.001563514 SOL, PnL LP +0.014651472 SOL (2.9303%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.013430979; setelah gas terhubung +0.013404852. Swap cocok unik, jeda 8 detik; selisih terhadap mark token -0.001220493 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Tilcayo-SOL · G52hFif92iKPFHo6JEFdrYSthJbqDLdjHJ8yffMf5jFT

2026-09-18T02:40:09+07:00 → 2026-09-18T02:47:29+07:00 · 7.33 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 3.348; TVL $115002.35; fee/TVL entry 0.6156%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -411; harga snapshot 0.000016746165 SOL/token; range [-448, -411] (38 bin), downside 30.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.499977362 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000052409 SOL (0.0105% modal), divergence principal vs HOLD SOL -0.000022616 SOL, PnL LP +0.000029793 SOL (0.0060%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Tilcayo-SOL · CQi2Zmr8J2A19yrJgqj7AuqNHnaoXZfeBVfYnaSaBPBc

2026-09-18T02:56:40+07:00 → 2026-09-18T02:58:06+07:00 · 1.43 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 5.308; TVL $96210.80; fee/TVL entry 0.2812%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -428; harga snapshot 0.000014140085 SOL/token; range [-503, -432] (72 bin), downside 50.66%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499998024 SOL + 0.000000000 token; withdraw 0.484542922 SOL + 1226.636050000 token. Porsi token pada mark withdrawal 2.96%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.57% → current 0.44% (dropped 1.13% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.002922287 SOL (0.5845% modal), divergence principal vs HOLD SOL -0.000663141 SOL, PnL LP +0.002259146 SOL (0.4518%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. 

## meridian · Tilcayo-SOL · 8B69n6UfC1FqhUVEMmZ8ADKcu2zNZJ2Zp2YZuHzX4JMu

2026-09-18T03:02:19+07:00 → 2026-09-18T03:07:22+07:00 · 5.05 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 6.158; TVL $106103.88; fee/TVL entry 1.5602%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -439; harga snapshot 0.000012674094 SOL/token; range [-481, -439] (43 bin), downside 34.16%; bentuk BidAskImBalanced. Model bobot: active bin 0.1057% modal, lima bin terdekat 1.586%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499988307 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.004887858 SOL (0.9776% modal), divergence principal vs HOLD SOL -0.000011670 SOL, PnL LP +0.004876188 SOL (0.9752%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.004831225; setelah gas terhubung +0.004799078. Swap cocok unik, jeda 7 detik; selisih terhadap mark token -0.000044963 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SOLCAT-SOL · CH1kkWAnuK5HJ9DvGwe6CcERVLiAQWpNZHBCK5JtPUJB

2026-09-18T03:05:10+07:00 → 2026-09-18T03:10:37+07:00 · 5.45 menit · pool `FEBzyyXLew5E9JngX7CKumHr5ehdUhRb7G6kjouo77dn`.

1. **Market → volatilitas → depth:** Volatility feed 14.571; TVL $29829.80; fee/TVL entry 0.9682%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -393; harga snapshot 0.000007581453 SOL/token; range [-462, -393] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499985255 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001768912 SOL (0.3538% modal), divergence principal vs HOLD SOL -0.000014710 SOL, PnL LP +0.001754202 SOL (0.3508%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001754202; setelah gas terhubung +0.001734202.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SOLCAT-SOL · B1g3y1dNkmpd4YuwZihBcSAst4BYauHzFBt2UAuJRj7W

2026-09-18T03:15:13+07:00 → 2026-09-18T03:16:44+07:00 · 1.52 menit · pool `FEBzyyXLew5E9JngX7CKumHr5ehdUhRb7G6kjouo77dn`.

1. **Market → volatilitas → depth:** Volatility feed 14.131; TVL $39723.11; fee/TVL entry 0.3667%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -378; harga snapshot 0.000009134356 SOL/token; range [-447, -378] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999948 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000015 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000017 SOL, PnL LP -0.000000002 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000002; setelah gas terhubung -0.000020002.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · UNI-USDC · 3XW9GGBZhHhdBVkVAY8zEtXT8cTi24HR742VgHHBrBEQ

2026-09-18T03:30:13+07:00 → 2026-09-18T03:35:02+07:00 · 4.82 menit · pool `43wQydX3UuRKVief4bkPxNz31inxCwvBNY7s1C9rK1XD`.

1. **Market → volatilitas → depth:** Volatility feed 7.541; TVL $tidak tersedia; fee/TVL entry 0.9680%; base fee pool 0.25%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -222; harga snapshot 10.981331960309 SOL/token; range [-311, -242] (70 bin), downside 49.67%; bentuk unknown.
3. **Inventory → fee opportunity:** Entry 0.000000000 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 0.000000000 token. Porsi token pada mark withdrawal tidak tersedia%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (tidak tersedia% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (tidak tersedia%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Posisi kosong/tidak didanai menurut API; jangan dihitung sebagai trade bermodal atau return nol yang sukses.

## meridian · UNI-USDC · 82HVUnk33oCC9yEcxeTNxG77KA7kNm6MWDUDST5jHCF4

2026-09-18T03:45:13+07:00 → 2026-09-18T04:45:28+07:00 · 60.25 menit · pool `43wQydX3UuRKVief4bkPxNz31inxCwvBNY7s1C9rK1XD`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 0.25%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -258; harga snapshot 7.675126887199 SOL/token; range [-318, -249] (70 bin), downside 49.67%; bentuk unknown.
3. **Inventory → fee opportunity:** Entry 0.000000000 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 0.000000000 token. Porsi token pada mark withdrawal tidak tersedia%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.00% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (tidak tersedia% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (tidak tersedia%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Posisi kosong/tidak didanai menurut API; jangan dihitung sebagai trade bermodal atau return nol yang sukses.

## meridian · SOLCAT-SOL · DNWELx83vBK4iayRVJ9Vfgn4gHGsAJ928NMRgkBwHg6v

2026-09-18T04:00:33+07:00 → 2026-09-18T04:00:47+07:00 · 0.23 menit · pool `HGF6LLmPghmtE9cuCEemeZiz8pv2G5G5HNJbnfECfmKf`.

1. **Market → volatilitas → depth:** Volatility feed 6.574; TVL $22947.44; fee/TVL entry 1.1964%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -461; harga snapshot 0.000010182319 SOL/token; range [-530, -461] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.499998624 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001189 SOL (0.0002% modal), divergence principal vs HOLD SOL -0.000001342 SOL, PnL LP -0.000000153 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas -0.000000153; setelah gas terhubung -0.000015153.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LOOP-SOL · 6dh9n3i35wGT7EPmeZ1DFa2AUWow67fJSFnyGV9LvbvK

2026-09-18T04:10:11+07:00 → 2026-09-18T04:22:38+07:00 · 12.45 menit · pool `6gQTdHry76sCzBAeCR8f2EkNYpgWrJjwb9352mF9ts5i`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -518; harga snapshot 0.000005774686 SOL/token; range [-588, -518] (71 bin), downside 50.17%; bentuk unknown.
3. **Inventory → fee opportunity:** Entry 0.499803990 SOL + 0.000000000 token; withdraw 0.499803920 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 50%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000070 SOL, PnL LP -0.000000070 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000070; setelah gas terhubung -0.000020070.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ELON-SOL · Cyf4KHA8Kby59fsfT5oEwxJbQU3tksVCHyjP2C314GTF

2026-09-18T04:15:16+07:00 → 2026-09-18T05:43:10+07:00 · 87.90 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 1.877; TVL $130233.12; fee/TVL entry 0.0581%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -429; harga snapshot 0.000032766626 SOL/token; range [-477, -429] (49 bin), downside 31.78%; bentuk BidAskImBalanced. Model bobot: active bin 0.0816% modal, lima bin terdekat 1.224%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999976 SOL + 0.000000000 token; withdraw 0.406532864 SOL + 3173.985699000 token. Porsi token pada mark withdrawal 17.91%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.70% → current 1.05% (dropped 0.65% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.010940105 SOL (2.1880% modal), divergence principal vs HOLD SOL -0.004787038 SOL, PnL LP +0.006153067 SOL (1.2306%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MCAT-SOL · 9ceVQo3XViA1Nt8aGRCqTBm4k579Newh1Vp8gBqVJJBE

2026-09-18T04:23:48+07:00 → 2026-09-18T04:26:05+07:00 · 2.28 menit · pool `HHgxEaEw1Wq9pSmMXp1dmf7vpDq7CegXbHVwtfYwcZRr`.

1. **Market → volatilitas → depth:** Volatility feed 14.279; TVL $58252.46; fee/TVL entry 1.5490%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -414; harga snapshot 0.000016253663 SOL/token; range [-483, -414] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499998882 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000463867 SOL (0.0928% modal), divergence principal vs HOLD SOL -0.000001083 SOL, PnL LP +0.000462784 SOL (0.0926%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MCAT-SOL · DjR2sCU39kAKCTMNy98ctcaQYu94pXrXwZbsBB3DEv3N

2026-09-18T04:29:10+07:00 → 2026-09-18T04:46:45+07:00 · 17.58 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 14.492; TVL $94083.74; fee/TVL entry 1.6597%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -293; harga snapshot 0.000026257638 SOL/token; range [-328, -293] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.456552938 SOL + 1863.169599000 token. Porsi token pada mark withdrawal 8.36%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 3.68% → current 2.97% (dropped 0.71% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.017845154 SOL (3.5690% modal), divergence principal vs HOLD SOL -0.001820284 SOL, PnL LP +0.016024870 SOL (3.2050%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MCAT-SOL · GM9CwgKNumiknnX4FdRsMPPvXvqRpDTY1jcAejUPrMuW

2026-09-18T04:49:44+07:00 → 2026-09-18T04:52:27+07:00 · 2.72 menit · pool `HHgxEaEw1Wq9pSmMXp1dmf7vpDq7CegXbHVwtfYwcZRr`.

1. **Market → volatilitas → depth:** Volatility feed 9.264; TVL $79710.30; fee/TVL entry 0.3778%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -383; harga snapshot 0.000022126557 SOL/token; range [-452, -383] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499996250 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000328722 SOL (0.0657% modal), divergence principal vs HOLD SOL -0.000003715 SOL, PnL LP +0.000325007 SOL (0.0650%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MCAT-SOL · 7ibABUuMyXYUEdixox9rEu7iX5dSwDFFbj12WdVXpe3k

2026-09-18T04:53:11+07:00 → 2026-09-18T04:53:24+07:00 · 0.22 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 9.305; TVL $tidak tersedia; fee/TVL entry 0.5319%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -291; harga snapshot 0.000026918182 SOL/token; range [-388, -319] (70 bin), downside 57.56%; bentuk unknown.
3. **Inventory → fee opportunity:** Entry 0.000000000 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 0.000000000 token. Porsi token pada mark withdrawal tidak tersedia%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (tidak tersedia% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (tidak tersedia%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Posisi kosong/tidak didanai menurut API; jangan dihitung sebagai trade bermodal atau return nol yang sukses.

## meridian · MCAT-SOL · Ert1FKVso3Si5j8THXMNi6iWWc8C2ZeGtyoRQpPCLv6M

2026-09-18T05:00:14+07:00 → 2026-09-18T05:01:40+07:00 · 1.43 menit · pool `HHgxEaEw1Wq9pSmMXp1dmf7vpDq7CegXbHVwtfYwcZRr`.

1. **Market → volatilitas → depth:** Volatility feed 8.364; TVL $83827.00; fee/TVL entry 2.2128%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -347; harga snapshot 0.000031657987 SOL/token; range [-416, -347] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499997547 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000002425 SOL (0.0005% modal), divergence principal vs HOLD SOL -0.000002418 SOL, PnL LP +0.000000007 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.000000007; setelah gas terhubung -0.000019993.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · SOLCAT-SOL · xDucXDueWUYec5Hb7rtothnDDP6QBzohB5SizwJR6Wg

2026-09-18T06:32:29+07:00 → 2026-09-18T07:03:36+07:00 · 31.12 menit · pool `HGF6LLmPghmtE9cuCEemeZiz8pv2G5G5HNJbnfECfmKf`.

1. **Market → volatilitas → depth:** Volatility feed 6.895; TVL $11497.49; fee/TVL entry 0.3651%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -446; harga snapshot 0.000011821356 SOL/token; range [-515, -446] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.429366897 SOL + 7066.514279000 token. Porsi token pada mark withdrawal 13.06%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.84% → current 1.08% (dropped 0.76% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.010259863 SOL (2.0520% modal), divergence principal vs HOLD SOL -0.006139439 SOL, PnL LP +0.004120424 SOL (0.8241%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.003231624; setelah gas terhubung +0.003184339. Swap cocok unik, jeda 9 detik; selisih terhadap mark token -0.000888800 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SOLCAT-SOL · 3A5xdoB46vCChWHbZvrB2XUndZ1VKcLBBZTPaxGm6fxj

2026-09-18T07:05:06+07:00 → 2026-09-18T07:10:54+07:00 · 5.80 menit · pool `HGF6LLmPghmtE9cuCEemeZiz8pv2G5G5HNJbnfECfmKf`.

1. **Market → volatilitas → depth:** Volatility feed 5.870; TVL $12674.74; fee/TVL entry 0.2354%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -468; harga snapshot 0.000009497232 SOL/token; range [-507, -468] (40 bin), downside 32.16%; bentuk BidAskImBalanced. Model bobot: active bin 0.1220% modal, lima bin terdekat 1.829%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.499997978 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001799 SOL (0.0004% modal), divergence principal vs HOLD SOL -0.000002002 SOL, PnL LP -0.000000203 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000203; setelah gas terhubung -0.000020203.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MADE-SOL · AFSKr8TPiCCAJ7ppAqD9UTYeCtDKyL1xgbN77x3aKah6

2026-09-18T07:25:11+07:00 → 2026-09-18T07:33:53+07:00 · 8.70 menit · pool `FxPPZGPiTNYzgdMkNgAkA8QRZjNxurjBo7JgPt9z4T5X`.

1. **Market → volatilitas → depth:** Volatility feed 8.923; TVL $16059.09; fee/TVL entry 0.4664%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -464; harga snapshot 0.000009882858 SOL/token; range [-533, -464] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499996100 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000003389 SOL (0.0007% modal), divergence principal vs HOLD SOL -0.000003865 SOL, PnL LP -0.000000476 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000476; setelah gas terhubung -0.000020476.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · biketyson-SOL · FaVfS3LzRR4TmLWqA5DmQWUy8gJqAbYwDBGVfS5Q8uw6

2026-09-18T07:50:06+07:00 → 2026-09-18T08:11:11+07:00 · 21.08 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 1.634; TVL $82826.91; fee/TVL entry 0.0858%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -409; harga snapshot 0.000017082763 SOL/token; range [-445, -409] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499992093 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 76.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000032161 SOL (0.0064% modal), divergence principal vs HOLD SOL -0.000007888 SOL, PnL LP +0.000024273 SOL (0.0049%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · PERK-SOL · 5Df7tft7zxYDqdm75E7fpfGdavtfPF77JEQr9kqrLLdx

2026-09-18T08:20:12+07:00 → 2026-09-18T08:26:29+07:00 · 6.28 menit · pool `8d6dxZomEUj3vKxYZQcor7Tdn924swbMCXkaJJozdFQ6`.

1. **Market → volatilitas → depth:** Volatility feed 5.292; TVL $10173.45; fee/TVL entry 0.9128%; base fee pool 1.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -328; harga snapshot 0.000016999241 SOL/token; range [-397, -328] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999571 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000352 SOL (0.0001% modal), divergence principal vs HOLD SOL -0.000000394 SOL, PnL LP -0.000000042 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000042; setelah gas terhubung -0.000020042.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · PERK-SOL · CKSmasRun5LwwfPUaGKsEuqKz7TqCumDYoGF5KRNo96U

2026-09-18T08:40:08+07:00 → 2026-09-18T09:23:19+07:00 · 43.18 menit · pool `8d6dxZomEUj3vKxYZQcor7Tdn924swbMCXkaJJozdFQ6`.

1. **Market → volatilitas → depth:** Volatility feed tidak tersedia; TVL $tidak tersedia; fee/TVL entry tidak tersedia%; base fee pool 1.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -337; harga snapshot 0.000015201073 SOL/token; range [-415, -346] (70 bin), downside 57.56%; bentuk unknown.
3. **Inventory → fee opportunity:** Entry 0.000000000 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 0.000000000 token. Porsi token pada mark withdrawal tidak tersedia%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 86.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (tidak tersedia% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (tidak tersedia%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Posisi kosong/tidak didanai menurut API; jangan dihitung sebagai trade bermodal atau return nol yang sukses.

## meridian · HUHCAT-SOL · DJDHQvR2gaGCuWsRcuxqkohpLDdNhAGfRRTWCPe3PAhV

2026-09-18T09:20:02+07:00 → 2026-09-18T09:43:41+07:00 · 23.65 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 3.483; TVL $32328.52; fee/TVL entry 0.1173%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -534; harga snapshot 0.000004924775 SOL/token; range [-592, -534] (59 bin), downside 43.85%; bentuk BidAskImBalanced. Model bobot: active bin 0.0565% modal, lima bin terdekat 0.847%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499997249 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 95.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001378512 SOL (0.2757% modal), divergence principal vs HOLD SOL -0.000002723 SOL, PnL LP +0.001375789 SOL (0.2752%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PERK-SOL · 2SuADnW9f1NXfff6d16q4PmUTovpjYpHfgzAJ2d42ZWE

2026-09-18T09:42:18+07:00 → 2026-09-18T10:04:32+07:00 · 22.23 menit · pool `8d6dxZomEUj3vKxYZQcor7Tdn924swbMCXkaJJozdFQ6`.

1. **Market → volatilitas → depth:** Volatility feed 4.481; TVL $14814.80; fee/TVL entry 0.1290%; base fee pool 1.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -340; harga snapshot 0.000014644993 SOL/token; range [-405, -340] (66 bin), downside 55.40%; bentuk BidAskImBalanced. Model bobot: active bin 0.0452% modal, lima bin terdekat 0.678%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.461335039 SOL + 3043.524203000 token. Porsi token pada mark withdrawal 7.25%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.75% → current -0.04% (dropped 1.79% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.002080749 SOL (0.4161% modal), divergence principal vs HOLD SOL -0.002577965 SOL, PnL LP -0.000497216 SOL (-0.0994%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.001234829; setelah gas terhubung -0.001261442. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.000737613 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PERK-SOL · 8H5YAh45niScZhXrtgKuMVvyZqsiL1q68816EsQzjoVz

2026-09-18T10:05:16+07:00 → 2026-09-18T10:11:02+07:00 · 5.77 menit · pool `8d6dxZomEUj3vKxYZQcor7Tdn924swbMCXkaJJozdFQ6`.

1. **Market → volatilitas → depth:** Volatility feed 5.039; TVL $13624.76; fee/TVL entry 0.7580%; base fee pool 1.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -357; harga snapshot 0.000011856967 SOL/token; range [-426, -357] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499992444 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000006520 SOL (0.0013% modal), divergence principal vs HOLD SOL -0.000007521 SOL, PnL LP -0.000001001 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001001; setelah gas terhubung -0.000021001.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ZPOOL-SOL · FUtSwSfyAkvXrQySTxFGUxEW5xTPUg6sq455uRv23YD8

2026-09-18T10:20:34+07:00 → 2026-09-18T10:24:24+07:00 · 3.83 menit · pool `3FQAJw11M2k7aGAdCKs2b1vZfg8MxEMqrcZeQiQrBqx6`.

1. **Market → volatilitas → depth:** Volatility feed 7.306; TVL $34889.08; fee/TVL entry 2.6585%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -539; harga snapshot 0.000004685755 SOL/token; range [-624, -540] (85 bin), downside 56.65%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499996690 SOL + 0.000000000 token; withdraw 0.361903549 SOL + 39924.704950000 token. Porsi token pada mark withdrawal 24.85%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** take profit
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.041200346 SOL (8.2401% modal), divergence principal vs HOLD SOL -0.018424081 SOL, PnL LP +0.022776265 SOL (4.5553%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil dalam SOL sebelum gas +0.023365963; setelah gas terhubung +0.023276902. Swap cocok unik, jeda 11 detik; selisih terhadap mark token +0.000589698 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. 

## meridian · ZPOOL-SOL · CsPZzJsPKjZ6msaPfStRnkiD6Z5LRVrqkHCpAkZYvgQF

2026-09-18T10:25:27+07:00 → 2026-09-18T10:44:10+07:00 · 18.72 menit · pool `3FQAJw11M2k7aGAdCKs2b1vZfg8MxEMqrcZeQiQrBqx6`.

1. **Market → volatilitas → depth:** Volatility feed 11.978; TVL $22365.04; fee/TVL entry 6.4657%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -587; harga snapshot 0.000002906388 SOL/token; range [-656, -587] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499752278 SOL + 82.997753000 token. Porsi token pada mark withdrawal 0.05%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 72.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.021317177 SOL (4.2634% modal), divergence principal vs HOLD SOL -0.000008852 SOL, PnL LP +0.021308325 SOL (4.2617%). Gas transaksi posisi yang terhubung 0.000025000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · POT-SOL · 6ZGN5dafog8GZivBxLARN3gRSkvGCK1yLH4R18DgQ1G5

2026-09-18T10:35:48+07:00 → 2026-09-18T10:39:37+07:00 · 3.82 menit · pool `7apm6xkdM9bZj1c1N2zPjHaMv1wGcTTDTUCbD4e7KFMP`.

1. **Market → volatilitas → depth:** Volatility feed 24.785; TVL $100109.76; fee/TVL entry 4.4681%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -418; harga snapshot 0.000015619451 SOL/token; range [-478, -418] (61 bin), downside 44.96%; bentuk BidAskImBalanced. Model bobot: active bin 0.0529% modal, lima bin terdekat 0.793%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.082622280 SOL + 38737.191432000 token. Porsi token pada mark withdrawal 80.90%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -10.63% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.028797642 SOL (5.7595% modal), divergence principal vs HOLD SOL -0.067337162 SOL, PnL LP -0.038539520 SOL (-7.7079%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.087964547; setelah gas terhubung -0.088000557. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.049425027 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PERK-SOL · BeVjpGSa3ov1vAKfDpVziN2rXkcEpxEzrvN15m6d4pU9

2026-09-18T10:50:16+07:00 → 2026-09-18T11:02:22+07:00 · 12.10 menit · pool `8d6dxZomEUj3vKxYZQcor7Tdn924swbMCXkaJJozdFQ6`.

1. **Market → volatilitas → depth:** Volatility feed 7.092; TVL $13463.91; fee/TVL entry 0.3053%; base fee pool 1.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -376; harga snapshot 0.000009364142 SOL/token; range [-445, -376] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999027 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 58.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000961366 SOL (0.1923% modal), divergence principal vs HOLD SOL -0.000000938 SOL, PnL LP +0.000960428 SOL (0.1921%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MANLET-SOL · 9kT3hKoXqFnVpVrx3ZXUPpaJ5s5R3VMzCz5ZPm7pKTZ4

2026-09-18T11:11:26+07:00 → 2026-09-18T11:18:23+07:00 · 6.95 menit · pool `68C62WPYiiNZxprbuaMj2ULXpiTDKcs5xsX7kBGnyajR`.

1. **Market → volatilitas → depth:** Volatility feed 5.515; TVL $25128.70; fee/TVL entry 0.0534%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1486; harga snapshot 0.000007205254 SOL/token; range [-1555, -1486] (70 bin), downside 42.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999447 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000002009 SOL (0.0004% modal), divergence principal vs HOLD SOL -0.000000518 SOL, PnL LP +0.000001491 SOL (0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLAME-SOL · 8jm2NQ9oKRag4Wcjt5F5dRfQNoZ5BomXjcV5iXtrE6XQ

2026-09-18T11:20:07+07:00 → 2026-09-18T11:41:07+07:00 · 21.00 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 5.657; TVL $37749.61; fee/TVL entry 0.0514%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -657; harga snapshot 0.000005326359 SOL/token; range [-729, -657] (73 bin), downside 43.66%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499998316 SOL + 0.000000000 token; withdraw 0.499994846 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 6m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 65%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001790 SOL (0.0004% modal), divergence principal vs HOLD SOL -0.000003470 SOL, PnL LP -0.000001680 SOL (-0.0003%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil dalam SOL sebelum gas -0.000001680; setelah gas terhubung -0.000041680.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · DEX-SOL · 1pW7aGDz7QzmCKyxSwnb4cS58Yi8hGmNUhrseg3EvYG

2026-09-18T11:30:52+07:00 → 2026-09-18T11:41:35+07:00 · 10.72 menit · pool `GCV7jiFniYQgfi9SPWW9qutZ446AKhZwqeG5wGpYaMVn`.

1. **Market → volatilitas → depth:** Volatility feed 14.127; TVL $54265.17; fee/TVL entry 0.1236%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -478; harga snapshot 0.000008597721 SOL/token; range [-547, -478] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.424151460 SOL + 10506.713455000 token. Porsi token pada mark withdrawal 14.12%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.29% → current 1.68% (dropped 0.61% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.018444438 SOL (3.6889% modal), divergence principal vs HOLD SOL -0.006106488 SOL, PnL LP +0.012337950 SOL (2.4676%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.009965177; setelah gas terhubung +0.009934375. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.002372773 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · DEX-SOL · 4XDtzfjMBfkGAijPjMiQtashXH8hRwECL6HfmKL5RpHB

2026-09-18T11:43:01+07:00 → 2026-09-18T11:44:23+07:00 · 1.37 menit · pool `GCV7jiFniYQgfi9SPWW9qutZ446AKhZwqeG5wGpYaMVn`.

1. **Market → volatilitas → depth:** Volatility feed 12.672; TVL $66752.95; fee/TVL entry 0.3051%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -506; harga snapshot 0.000006507061 SOL/token; range [-575, -506] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.437371922 SOL + 11265.097766000 token. Porsi token pada mark withdrawal 11.66%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.47% → current 0.84% (dropped 0.63% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.012745760 SOL (2.5492% modal), divergence principal vs HOLD SOL -0.004897338 SOL, PnL LP +0.007848422 SOL (1.5697%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.006025039; setelah gas terhubung +0.005998603. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.001823383 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · DEX-SOL · 7Qu8fenoiD9RHNwGVp5dabPkB1MDNR9EtLVy9QVWYPAF

2026-09-18T11:50:14+07:00 → 2026-09-18T11:55:01+07:00 · 4.78 menit · pool `GCV7jiFniYQgfi9SPWW9qutZ446AKhZwqeG5wGpYaMVn`.

1. **Market → volatilitas → depth:** Volatility feed 11.319; TVL $53837.67; fee/TVL entry 1.3206%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -546; harga snapshot 0.000004370488 SOL/token; range [-615, -546] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499996580 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 75%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006338024 SOL (1.2676% modal), divergence principal vs HOLD SOL -0.000003385 SOL, PnL LP +0.006334639 SOL (1.2669%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.006420838; setelah gas terhubung +0.006392784. Swap cocok unik, jeda 9 detik; selisih terhadap mark token +0.000086199 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MINI-SOL · 5zJY7C4ReuvDN3Ukt52ZjQe4NBgGk4ejieaPCzXu9hSV

2026-09-18T12:35:11+07:00 → 2026-09-18T13:35:20+07:00 · 60.15 menit · pool `64BSmy7BESiHnWYzLdPso6FuXymh7H8jTkaiyfbBg1YD`.

1. **Market → volatilitas → depth:** Volatility feed 7.027; TVL $36989.33; fee/TVL entry 0.2218%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -263; harga snapshot 0.000038115938 SOL/token; range [-302, -263] (40 bin), downside 38.40%; bentuk BidAskImBalanced. Model bobot: active bin 0.1220% modal, lima bin terdekat 1.829%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.499390375 SOL + 15.627331000 token. Porsi token pada mark withdrawal 0.12%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.08% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000017255 SOL (0.0035% modal), divergence principal vs HOLD SOL -0.000013955 SOL, PnL LP +0.000003300 SOL (0.0007%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ALL-SOL · C5sUfHDt7APjoxEvfHUrxBe9E7BsU3YDGJ3J5fKJJPQw

2026-09-18T13:19:15+07:00 → 2026-09-18T14:03:45+07:00 · 44.50 menit · pool `FpP5SnzBnHJ5M9wS7fCuYiiSuXUPLNQKpk7qndeZxKZZ`.

1. **Market → volatilitas → depth:** Volatility feed 2.488; TVL $26365.91; fee/TVL entry 0.0797%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -572; harga snapshot 0.000003374226 SOL/token; range [-609, -572] (38 bin), downside 30.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.499995540 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 88.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000079570 SOL (0.0159% modal), divergence principal vs HOLD SOL -0.000004438 SOL, PnL LP +0.000075132 SOL (0.0150%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · PERPSPAD-SOL · 6hVNBqNHgfk6rvH9NWBqqXXa6NeXVii1jeLMwqRJ87vo

2026-09-18T15:05:11+07:00 → 2026-09-18T15:10:40+07:00 · 5.48 menit · pool `EHqk4Fw3pTCf9UW75dWoCMf6a2GxyJ8FGYEj2Qmw9rfr`.

1. **Market → volatilitas → depth:** Volatility feed 1.824; TVL $101698.61; fee/TVL entry 0.0622%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -372; harga snapshot 0.000051603844 SOL/token; range [-408, -372] (37 bin), downside 24.94%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499999888 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000051 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000093 SOL, PnL LP -0.000000042 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000042; setelah gas terhubung -0.000020042.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · Tilcayo-SOL · DbRJXXWXfnq2WNXs3QNtKXFKDXwSsnjgCPNU4zfeKk38

2026-09-18T15:35:12+07:00 → 2026-09-18T15:35:24+07:00 · 0.20 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 2.881; TVL $77900.49; fee/TVL entry 0.0616%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -378; harga snapshot 0.000023255234 SOL/token; range [-431, -378] (54 bin), downside 40.98%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499669103 SOL + 13.680848000 token. Porsi token pada mark withdrawal 0.06%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000012723 SOL, PnL LP -0.000012723 SOL (-0.0025%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · Tilcayo-SOL · 7B68Vhgz3sWY2vvZuL21bWQ3qTqn7ywwPcFWr1UxTkqK

2026-09-18T16:20:11+07:00 → 2026-09-18T16:27:01+07:00 · 6.83 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 4.518; TVL $133324.44; fee/TVL entry 0.3143%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -377; harga snapshot 0.000023487786 SOL/token; range [-443, -377] (67 bin), downside 48.15%; bentuk BidAskImBalanced. Model bobot: active bin 0.0439% modal, lima bin terdekat 0.658%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499993424 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000055859 SOL (0.0112% modal), divergence principal vs HOLD SOL -0.000006543 SOL, PnL LP +0.000049316 SOL (0.0099%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · baton-SOL · FPwrSVzuAQ4MEBuc8rF2gWXiNpfA2aXKDxrKDJrEa7bt

2026-09-18T16:50:10+07:00 → 2026-09-18T17:00:01+07:00 · 9.85 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 0.704; TVL $45462.99; fee/TVL entry 0.0730%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -394; harga snapshot 0.000019832558 SOL/token; range [-429, -394] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499999951 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 44.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000035 SOL, PnL LP -0.000000035 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas -0.000000035; setelah gas terhubung -0.000015035.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · CLANKER-SOL · DUewC1oHyZiouLSiup5BCNfMJSpS3khND8mS6pPzUTAH

2026-09-18T17:25:09+07:00 → 2026-09-18T17:30:57+07:00 · 5.80 menit · pool `9aXA6qqqXueA6Eq9WPRgas4wQgjPCEspzutbaS3UZkXT`.

1. **Market → volatilitas → depth:** Volatility feed 6.028; TVL $13016.89; fee/TVL entry 0.1300%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1184; harga snapshot 0.000007647041 SOL/token; range [-1260, -1184] (77 bin), downside 53.06%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499999500 SOL + 0.000000000 token; withdraw 0.499999382 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000037 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000118 SOL, PnL LP -0.000000081 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil dalam SOL sebelum gas -0.000000081; setelah gas terhubung -0.000040081.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · Tilcayo-SOL · 65Seaj9AQm6MZQmpiQ5RGFuhF9zYZXQXbSUvvKAQict9

2026-09-18T18:20:10+07:00 → 2026-09-18T18:40:21+07:00 · 20.18 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 3.743; TVL $146100.67; fee/TVL entry 0.0510%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -402; harga snapshot 0.000018315034 SOL/token; range [-465, -402] (64 bin), downside 46.57%; bentuk BidAskImBalanced. Model bobot: active bin 0.0481% modal, lima bin terdekat 0.721%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499996446 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 80%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000413044 SOL (0.0826% modal), divergence principal vs HOLD SOL -0.000003524 SOL, PnL LP +0.000409520 SOL (0.0819%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MCAT-SOL · 32E9ZkkBiBY3hxHpmeFK6U1N5XWAitrAMQP9pcwGzTvm

2026-09-18T18:55:07+07:00 → 2026-09-18T19:02:33+07:00 · 7.43 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 3.427; TVL $61552.54; fee/TVL entry 0.1650%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -322; harga snapshot 0.000018314697 SOL/token; range [-359, -322] (38 bin), downside 36.85%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.499999892 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 14.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000075 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000086 SOL, PnL LP -0.000000011 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000011; setelah gas terhubung -0.000020011.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MCAT-SOL · AZ39XefnHGsKSM2UWoS5rd9hw86zTTCDaW6j7WMYfh1v

2026-09-18T19:20:11+07:00 → 2026-09-18T20:48:13+07:00 · 88.03 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 2.399; TVL $57952.09; fee/TVL entry 0.0865%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -304; harga snapshot 0.000022903946 SOL/token; range [-355, -304] (52 bin), downside 46.93%; bentuk BidAskImBalanced. Model bobot: active bin 0.0726% modal, lima bin terdekat 1.089%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999974 SOL + 0.000000000 token; withdraw 0.331315966 SOL + 9402.494419000 token. Porsi token pada mark withdrawal 31.19%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.40% → current 0.74% (dropped 0.66% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.011196679 SOL (2.2393% modal), divergence principal vs HOLD SOL -0.018474485 SOL, PnL LP -0.007277806 SOL (-1.4556%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Tilcayo-SOL · 5HV46ZP72NqRYjpDPg9PfPKM6N8FbF63S15DvhUvQwq9

2026-09-18T19:50:20+07:00 → 2026-09-18T20:30:59+07:00 · 40.65 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 3.027; TVL $140454.68; fee/TVL entry 0.0500%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -401; harga snapshot 0.000018498185 SOL/token; range [-456, -401] (56 bin), downside 42.15%; bentuk BidAskImBalanced. Model bobot: active bin 0.0627% modal, lima bin terdekat 0.940%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.367902594 SOL + 8648.261618000 token. Porsi token pada mark withdrawal 24.58%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.43% → current -1.02% (dropped 2.45% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.005148707 SOL (1.0297% modal), divergence principal vs HOLD SOL -0.012219762 SOL, PnL LP -0.007071055 SOL (-1.4142%). Gas transaksi posisi yang terhubung 0.000025000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MCAT-SOL · 8MLHSgPQwZZKUYTFtaj9Q1rVCsnCEkAqcWvH915Qfaj8

2026-09-18T21:30:08+07:00 → 2026-09-18T22:05:45+07:00 · 35.62 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 4.560; TVL $61927.02; fee/TVL entry 0.0546%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -335; harga snapshot 0.000015583475 SOL/token; range [-373, -335] (39 bin), downside 37.63%; bentuk BidAskImBalanced. Model bobot: active bin 0.1282% modal, lima bin terdekat 1.923%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.472424932 SOL + 1887.842089000 token. Porsi token pada mark withdrawal 5.34%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.42% → current 0.58% (dropped 0.84% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.002110540 SOL (0.4221% modal), divergence principal vs HOLD SOL -0.000939005 SOL, PnL LP +0.001171535 SOL (0.2343%). Gas transaksi posisi yang terhubung 0.000025000 SOL. Hasil dalam SOL sebelum gas +0.001297708; setelah gas terhubung +0.001254845. Swap cocok unik, jeda 8 detik; selisih terhadap mark token +0.000126173 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · 4qbLAHDfy3VMHTsicmtEjH4GRHJT7X5uuziooaQWycD8

2026-09-18T22:00:19+07:00 → 2026-09-18T22:11:12+07:00 · 10.88 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 6.822; TVL $65326.25; fee/TVL entry 0.0829%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -370; harga snapshot 0.000025182086 SOL/token; range [-439, -370] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499798765 SOL + 7.916633000 token. Porsi token pada mark withdrawal 0.04%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 50%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000006804 SOL (0.0014% modal), divergence principal vs HOLD SOL -0.000001843 SOL, PnL LP +0.000004962 SOL (0.0010%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ELON-SOL · 3qXJMziSxWi9ksL3MYLB3Lup68sF93V8TPS4zkX6Antw

2026-09-18T22:30:21+07:00 → 2026-09-18T22:42:26+07:00 · 12.08 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 3.781; TVL $148596.90; fee/TVL entry 0.0872%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -409; harga snapshot 0.000038427521 SOL/token; range [-469, -409] (61 bin), downside 38.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.0529% modal, lima bin terdekat 0.793%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499999502 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 58.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000211437 SOL (0.0423% modal), divergence principal vs HOLD SOL -0.000000470 SOL, PnL LP +0.000210967 SOL (0.0422%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SOLCAT-SOL · 4RY1XnxGrf5HxBcFSJ6EatfQ5zVPtkra4ZYaK8EDWdJh

2026-09-18T22:57:29+07:00 → 2026-09-18T23:03:03+07:00 · 5.57 menit · pool `HGF6LLmPghmtE9cuCEemeZiz8pv2G5G5HNJbnfECfmKf`.

1. **Market → volatilitas → depth:** Volatility feed 4.412; TVL $18543.20; fee/TVL entry 0.0814%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -448; harga snapshot 0.000011588428 SOL/token; range [-513, -448] (66 bin), downside 47.63%; bentuk BidAskImBalanced. Model bobot: active bin 0.0452% modal, lima bin terdekat 0.678%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499993848 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000005351 SOL (0.0011% modal), divergence principal vs HOLD SOL -0.000006122 SOL, PnL LP -0.000000771 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000771; setelah gas terhubung -0.000020771.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · HUHCAT-SOL · 5ckX1fEYKC3p1eWjboZLmg41B8siVLfjAikSdrqHNZyV

2026-09-18T23:05:07+07:00 → 2026-09-18T23:22:16+07:00 · 17.15 menit · pool `Crtx19GAMBhVh62cHArWYa2moRQeyMtzgsVjzX9NCDhy`.

1. **Market → volatilitas → depth:** Volatility feed 4.328; TVL $23034.95; fee/TVL entry 0.1952%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -576; harga snapshot 0.000003242565 SOL/token; range [-611, -576] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499999839 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 70.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000452264 SOL (0.0905% modal), divergence principal vs HOLD SOL -0.000000147 SOL, PnL LP +0.000452117 SOL (0.0904%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · LOOP-SOL · C7EUg4xvgVY85Zp1ndZHziECYRxEqqw7g1DoVZhqAtY1

2026-09-18T23:25:13+07:00 → 2026-09-18T23:38:15+07:00 · 13.03 menit · pool `6gQTdHry76sCzBAeCR8f2EkNYpgWrJjwb9352mF9ts5i`.

1. **Market → volatilitas → depth:** Volatility feed 3.777; TVL $13268.95; fee/TVL entry 0.1134%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -555; harga snapshot 0.000003996111 SOL/token; range [-618, -555] (64 bin), downside 46.57%; bentuk BidAskImBalanced. Model bobot: active bin 0.0481% modal, lima bin terdekat 0.721%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499999318 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 46.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000201101 SOL (0.0402% modal), divergence principal vs HOLD SOL -0.000000652 SOL, PnL LP +0.000200449 SOL (0.0401%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · OTC-SOL · 9J8xUAep8cncYr1JniEN45Qm1KeHEXEPVw5WW6stRZcd

2026-09-18T23:30:07+07:00 → 2026-09-18T23:30:18+07:00 · 0.18 menit · pool `Ekm4LYkihEdQgZx2UReDMJ3eCDDjExPQLG94WfWmfyWr`.

1. **Market → volatilitas → depth:** Volatility feed 3.045; TVL $116537.62; fee/TVL entry 0.0656%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -326; harga snapshot 0.000039015048 SOL/token; range [-382, -326] (57 bin), downside 42.72%; bentuk BidAskImBalanced. Model bobot: active bin 0.0605% modal, lima bin terdekat 0.907%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499742929 SOL + 6.507257000 token. Porsi token pada mark withdrawal 0.05%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000003162 SOL, PnL LP -0.000003162 SOL (-0.0006%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · OPENAI-SOL · CUBstjLjRXaFAoRFhMKKo4g73D5QRjxnR8nT9Krbp4jA

2026-09-19T00:15:44+07:00 → 2026-09-19T00:22:39+07:00 · 6.92 menit · pool `CoqYNCGKpiGgLJJ6DntdbcvKmqTZBrxdvQDrxDCfb9GH`.

1. **Market → volatilitas → depth:** Volatility feed 1.428; TVL $25751.09; fee/TVL entry 0.3047%; base fee pool 0.01%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot 335; harga snapshot 9.710019050592 SOL/token; range [300, 335] (36 bin), downside 24.34%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499999983 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000001 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000003 SOL, PnL LP -0.000000002 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000002; setelah gas terhubung -0.000020002.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLAME-SOL · 5G6HY84StpmhHSocCmvCLy3hvydvujPABDEGduDv5ajR

2026-09-19T00:20:11+07:00 → 2026-09-19T00:47:13+07:00 · 27.03 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 2.623; TVL $34651.71; fee/TVL entry 0.0700%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -673; harga snapshot 0.000004688802 SOL/token; range [-726, -673] (54 bin), downside 34.45%; bentuk BidAskImBalanced. Model bobot: active bin 0.0673% modal, lima bin terdekat 1.010%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499999956 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 81.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000425994 SOL (0.0852% modal), divergence principal vs HOLD SOL -0.000000021 SOL, PnL LP +0.000425973 SOL (0.0852%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · NASDOG-SOL · ABr867tzZciPHZErtD9jvsM1YsZeRqUoMSZrUkEN3HqK

2026-09-19T00:35:54+07:00 → 2026-09-19T00:41:34+07:00 · 5.67 menit · pool `GfCnfPzeSppL8B3DBU6B8sYrtEAEugMjowFBKVviAins`.

1. **Market → volatilitas → depth:** Volatility feed 9.247; TVL $140308.36; fee/TVL entry 1.2092%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -517; harga snapshot 0.000005832433 SOL/token; range [-586, -517] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499999068 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 60%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000018373 SOL (0.0037% modal), divergence principal vs HOLD SOL -0.000000899 SOL, PnL LP +0.000017474 SOL (0.0035%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · NASDOG-SOL · A1FX7hsecvMbzc8Sr3PQj2yfnYe5VUeqCq2doLVFAHCP

2026-09-19T00:46:23+07:00 → 2026-09-19T00:51:01+07:00 · 4.63 menit · pool `GfCnfPzeSppL8B3DBU6B8sYrtEAEugMjowFBKVviAins`.

1. **Market → volatilitas → depth:** Volatility feed 6.427; TVL $67103.54; fee/TVL entry 0.6579%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -553; harga snapshot 0.000004076433 SOL/token; range [-622, -553] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500003040 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.003785095 SOL (0.7570% modal), divergence principal vs HOLD SOL 0.000003075 SOL, PnL LP +0.003788170 SOL (0.7576%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · NASDOG-SOL · 4eNbRRsXZnBBr17sdVmV1bhjKEv4UgCpNjh4xdaCiWMF

2026-09-19T00:51:36+07:00 → 2026-09-19T00:56:08+07:00 · 4.53 menit · pool `GfCnfPzeSppL8B3DBU6B8sYrtEAEugMjowFBKVviAins`.

1. **Market → volatilitas → depth:** Volatility feed 8.556; TVL $72494.21; fee/TVL entry 0.4416%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -542; harga snapshot 0.000004547947 SOL/token; range [-583, -542] (42 bin), downside 33.50%; bentuk BidAskImBalanced. Model bobot: active bin 0.1107% modal, lima bin terdekat 1.661%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.399032009 SOL + 25322.260576000 token. Porsi token pada mark withdrawal 19.28%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.31% → current 0.48% (dropped 0.83% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.007005975 SOL (1.4012% modal), divergence principal vs HOLD SOL -0.005641881 SOL, PnL LP +0.001364094 SOL (0.2728%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.003113058; setelah gas terhubung -0.003138977. Swap cocok unik, jeda 8 detik; selisih terhadap mark token -0.004477152 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · STONK10-SOL · ATyyXEmfac6KMSsMGgczMixvoHEjHnscohB7wCksatcd

2026-09-19T01:15:22+07:00 → 2026-09-19T01:21:42+07:00 · 6.33 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 4.916; TVL $12756.22; fee/TVL entry 0.1606%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -486; harga snapshot 0.000020805655 SOL/token; range [-554, -486] (69 bin), downside 41.83%; bentuk BidAskImBalanced. Model bobot: active bin 0.0414% modal, lima bin terdekat 0.621%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499999961 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 33.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000045053 SOL (0.0090% modal), divergence principal vs HOLD SOL -0.000000006 SOL, PnL LP +0.000045047 SOL (0.0090%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · fone-SOL · E56HjMvLEtGgaZimDrq7ouEMJzA5EzqKwi89TrKDKWSC

2026-09-19T01:50:09+07:00 → 2026-09-19T02:17:34+07:00 · 27.42 menit · pool `fAeDy2q7ZjZZZFt6Q1FtbHaCU5dtLEPmYcwcwfAexNA`.

1. **Market → volatilitas → depth:** Volatility feed 2.929; TVL $106307.21; fee/TVL entry 0.0644%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -304; harga snapshot 0.000048562649 SOL/token; range [-341, -304] (38 bin), downside 30.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.499990477 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 81.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000094739 SOL (0.0189% modal), divergence principal vs HOLD SOL -0.000009501 SOL, PnL LP +0.000085238 SOL (0.0170%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · BUTTHOLE-SOL · 3ApeJ3BAvufBfZtc3VFr2BhvxibfRxq2hrAgf8gesiKv

2026-09-19T02:30:09+07:00 → 2026-09-19T02:44:43+07:00 · 14.57 menit · pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatilitas → depth:** Volatility feed 4.313; TVL $81643.05; fee/TVL entry 0.0951%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1358; harga snapshot 0.000019980088 SOL/token; range [-1422, -1358] (65 bin), downside 39.95%; bentuk BidAskImBalanced. Model bobot: active bin 0.0466% modal, lima bin terdekat 0.699%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499998884 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 64.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001259 SOL (0.0003% modal), divergence principal vs HOLD SOL -0.000001083 SOL, PnL LP +0.000000176 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MADE-SOL · 937spRLPVuhF84f99AfYyjAx8ejF9m1yFq6348Uavqjk

2026-09-19T04:15:24+07:00 → 2026-09-19T04:27:12+07:00 · 11.80 menit · pool `FxPPZGPiTNYzgdMkNgAkA8QRZjNxurjBo7JgPt9z4T5X`.

1. **Market → volatilitas → depth:** Volatility feed 2.504; TVL $26842.91; fee/TVL entry 0.0587%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -469; harga snapshot 0.000009403200 SOL/token; range [-506, -469] (38 bin), downside 30.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.499997494 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 54.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001910 SOL (0.0004% modal), divergence principal vs HOLD SOL -0.000002484 SOL, PnL LP -0.000000574 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000574; setelah gas terhubung -0.000020574.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MANLET-SOL · s98LiWtPVU5VeFeMXKSB4EFqKwwXounBph3PjJkdNpQ

2026-09-19T05:00:08+07:00 → 2026-09-19T06:00:14+07:00 · 60.10 menit · pool `68C62WPYiiNZxprbuaMj2ULXpiTDKcs5xsX7kBGnyajR`.

1. **Market → volatilitas → depth:** Volatility feed 4.646; TVL $30464.75; fee/TVL entry 0.0997%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1501; harga snapshot 0.000006393539 SOL/token; range [-1569, -1501] (69 bin), downside 41.83%; bentuk BidAskImBalanced. Model bobot: active bin 0.0414% modal, lima bin terdekat 0.621%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499182472 SOL + 128.839815899 token. Porsi token pada mark withdrawal 0.16%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.06% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000011859 SOL (0.0024% modal), divergence principal vs HOLD SOL -0.000006776 SOL, PnL LP +0.000005083 SOL (0.0010%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · CROSSR-SOL · 68CBnziP2f4Br2K4raSnnWdoa8DMeJuv5M39zCz4dzW

2026-09-19T05:27:08+07:00 → 2026-09-19T05:30:01+07:00 · 2.88 menit · pool `GFcwi23mNjzSekMvE7CarwBkuEsP48NTKnf4adrkGXvB`.

1. **Market → volatilitas → depth:** Volatility feed 14.630; TVL $37913.53; fee/TVL entry 0.4328%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -459; harga snapshot 0.000010386983 SOL/token; range [-528, -459] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.442961859 SOL + 6378.358649000 token. Porsi token pada mark withdrawal 10.63%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.14% → current 1.07% (dropped 1.07% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.011571051 SOL (2.3142% modal), divergence principal vs HOLD SOL -0.004338572 SOL, PnL LP +0.007232479 SOL (1.4465%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.004570186; setelah gas terhubung +0.004541086. Swap cocok unik, jeda 7 detik; selisih terhadap mark token -0.002662293 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · CROSSR-SOL · BEq2VHHHtoWZHwWuMPwLDKzvupbvGzRF9JXcfJwNBDLu

2026-09-19T05:35:09+07:00 → 2026-09-19T05:43:38+07:00 · 8.48 menit · pool `GFcwi23mNjzSekMvE7CarwBkuEsP48NTKnf4adrkGXvB`.

1. **Market → volatilitas → depth:** Volatility feed 13.398; TVL $33581.25; fee/TVL entry 1.1176%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -486; harga snapshot 0.000007939851 SOL/token; range [-555, -486] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.475848684 SOL + 3345.275524000 token. Porsi token pada mark withdrawal 4.59%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.25% → current 0.56% (dropped 0.69% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006482896 SOL (1.2966% modal), divergence principal vs HOLD SOL -0.001272987 SOL, PnL LP +0.005209909 SOL (1.0420%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.002684358; setelah gas terhubung +0.002644685. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.002525551 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · CROSSR-SOL · 8A577aZM2qbe5WSHfzLBYDxNGeFR42pdtEc6dyHMmJ1w

2026-09-19T05:52:12+07:00 → 2026-09-19T06:01:49+07:00 · 9.62 menit · pool `GFcwi23mNjzSekMvE7CarwBkuEsP48NTKnf4adrkGXvB`.

1. **Market → volatilitas → depth:** Volatility feed 8.234; TVL $27363.55; fee/TVL entry 0.1633%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -507; harga snapshot 0.000006442634 SOL/token; range [-576, -507] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.102885040 SOL + 93581.553174000 token. Porsi token pada mark withdrawal 75.97%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -8.44% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.028440017 SOL (5.6880% modal), divergence principal vs HOLD SOL -0.071781589 SOL, PnL LP -0.043341572 SOL (-8.6683%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.046870336; setelah gas terhubung -0.046896058. Swap cocok unik, jeda 7 detik; selisih terhadap mark token -0.003528764 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · OTC-SOL · EEijmkQEdq4pnR8YPBLF9FnFAW7JscokkY437ytSD4DD

2026-09-19T06:45:13+07:00 → 2026-09-19T07:45:19+07:00 · 60.10 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 3.546; TVL $17072.29; fee/TVL entry 0.1175%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -285; harga snapshot 0.000058668971 SOL/token; range [-322, -285] (38 bin), downside 30.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.499982540 SOL + 0.021553000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 1.00% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000207106 SOL (0.0414% modal), divergence principal vs HOLD SOL -0.000016174 SOL, PnL LP +0.000190932 SOL (0.0382%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · Prism-SOL · J3ESksLo2xDBm6YPibiTGcTRxqLLBXumxxC4r4L3vvd5

2026-09-19T07:21:52+07:00 → 2026-09-19T07:26:09+07:00 · 4.28 menit · pool `9xCHQgVQ3DSDcHu8h2A4njrsWB1J7JceZpEqFLXdmh8f`.

1. **Market → volatilitas → depth:** Volatility feed 11.360; TVL $32784.07; fee/TVL entry 0.1200%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -486; harga snapshot 0.000007939851 SOL/token; range [-555, -486] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499998591 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001406442 SOL (0.2813% modal), divergence principal vs HOLD SOL -0.000001376 SOL, PnL LP +0.001405066 SOL (0.2810%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Prism-SOL · GJXxBrqLtLGKQvujqQJz3h7CtZwmkzmvz27hxJCoGGpa

2026-09-19T07:37:54+07:00 → 2026-09-19T07:50:11+07:00 · 12.28 menit · pool `9xCHQgVQ3DSDcHu8h2A4njrsWB1J7JceZpEqFLXdmh8f`.

1. **Market → volatilitas → depth:** Volatility feed 9.363; TVL $74688.79; fee/TVL entry 0.8472%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -496; harga snapshot 0.000007187843 SOL/token; range [-565, -496] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999909 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.012474386 SOL (2.4949% modal), divergence principal vs HOLD SOL -0.000000056 SOL, PnL LP +0.012474330 SOL (2.4949%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Prism-SOL · fJ472co2fqC9e3epd2jqJBkuxmAv9DmVt5kNfrKNtNs

2026-09-19T07:55:12+07:00 → 2026-09-19T08:05:15+07:00 · 10.05 menit · pool `9xCHQgVQ3DSDcHu8h2A4njrsWB1J7JceZpEqFLXdmh8f`.

1. **Market → volatilitas → depth:** Volatility feed 9.866; TVL $38683.23; fee/TVL entry 0.2544%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -494; harga snapshot 0.000007332319 SOL/token; range [-563, -494] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499992694 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 90%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.004001160 SOL (0.8002% modal), divergence principal vs HOLD SOL -0.000007271 SOL, PnL LP +0.003993889 SOL (0.7988%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.004020847; setelah gas terhubung +0.003986224. Swap cocok unik, jeda 7 detik; selisih terhadap mark token +0.000026958 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · baton-SOL · 2d7fy9ESZU1F3h5N51jJbnrUKuyy8koSd8Tt5kqXE8ja

2026-09-19T08:30:15+07:00 → 2026-09-19T08:39:08+07:00 · 8.88 menit · pool `BN7CfsGm6Vq9w8NibLZXRGW2tp5y2axwXuLAs85NGakf`.

1. **Market → volatilitas → depth:** Volatility feed 1.579; TVL $138383.49; fee/TVL entry 0.0628%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -507; harga snapshot 0.000017599901 SOL/token; range [-543, -507] (37 bin), downside 24.94%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499996019 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000002884 SOL (0.0006% modal), divergence principal vs HOLD SOL -0.000003962 SOL, PnL LP -0.000001078 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001078; setelah gas terhubung -0.000021078.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MINI-SOL · 3QxcitHbbkHsV1Z7y9SfxwQAFQVVAVFkEGiob85Yq7D4

2026-09-19T08:35:15+07:00 → 2026-09-19T08:52:06+07:00 · 16.85 menit · pool `64BSmy7BESiHnWYzLdPso6FuXymh7H8jTkaiyfbBg1YD`.

1. **Market → volatilitas → depth:** Volatility feed 7.906; TVL $45146.78; fee/TVL entry 0.3616%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -291; harga snapshot 0.000026918182 SOL/token; range [-360, -291] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499998115 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 68.8%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001250 SOL (0.0003% modal), divergence principal vs HOLD SOL -0.000001850 SOL, PnL LP -0.000000600 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000600; setelah gas terhubung -0.000020600.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · Tilcayo-SOL · CwLRew8LVqvtGmWW579CxoJbe7zRH1rSYpNWPvJqJYza

2026-09-19T09:20:18+07:00 → 2026-09-19T09:22:00+07:00 · 1.70 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 2.535; TVL $32508.94; fee/TVL entry 0.0776%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -473; harga snapshot 0.000009036291 SOL/token; range [-525, -473] (53 bin), downside 40.39%; bentuk BidAskImBalanced. Model bobot: active bin 0.0699% modal, lima bin terdekat 1.048%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499987818 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000010584 SOL (0.0021% modal), divergence principal vs HOLD SOL -0.000012168 SOL, PnL LP -0.000001584 SOL (-0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001584; setelah gas terhubung -0.000021584.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · Pigeon-SOL · B9G2bjrUVr1EN7WFkSKRfKfw7ZYp8hGNypbc3gLoLHPB

2026-09-19T10:05:09+07:00 → 2026-09-19T10:06:49+07:00 · 1.67 menit · pool `2TeUzpJn1XJUXENNNk4mSH5mwkBampxjwsMgafUQuRiZ`.

1. **Market → volatilitas → depth:** Volatility feed 11.956; TVL $15540.09; fee/TVL entry 2.6805%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -574; harga snapshot 0.000003307741 SOL/token; range [-643, -574] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500001291 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.002344911 SOL (0.4690% modal), divergence principal vs HOLD SOL 0.000001326 SOL, PnL LP +0.002346237 SOL (0.4692%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.002329828; setelah gas terhubung +0.002302168. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.000016409 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MCAT-SOL · J7tGhPWpA4oy97gSBsgctQqdTbHLGVQuun7sZEy2QeFJ

2026-09-19T10:10:09+07:00 → 2026-09-19T10:17:34+07:00 · 7.42 menit · pool `5fjmuEN72LQeo9NjvhLyQTV3ezyNgQqUXzSXskD2SCcy`.

1. **Market → volatilitas → depth:** Volatility feed 1.871; TVL $37326.70; fee/TVL entry 0.0645%; base fee pool 1.5%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -420; harga snapshot 0.000005421090 SOL/token; range [-468, -420] (49 bin), downside 44.91%; bentuk BidAskImBalanced. Model bobot: active bin 0.0816% modal, lima bin terdekat 1.224%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999976 SOL + 0.000000000 token; withdraw 0.499994340 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000004997 SOL (0.0010% modal), divergence principal vs HOLD SOL -0.000005636 SOL, PnL LP -0.000000639 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000639; setelah gas terhubung -0.000020639.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · PEPE-SOL · 6KFEV52noGprW4CfN653um643tBQLwAMZC2adDoGYhG8

2026-09-19T10:15:16+07:00 → 2026-09-19T11:15:26+07:00 · 60.17 menit · pool `C1baVnbBd31ucGqvuKgeghtyX6Xpnq5cXxamLqXi9hVN`.

1. **Market → volatilitas → depth:** Volatility feed 1.127; TVL $101707.56; fee/TVL entry 0.2573%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -713; harga snapshot 0.000000034091 SOL/token; range [-756, -713] (44 bin), downside 29.01%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.499399734 SOL + 17599.076500000 token. Porsi token pada mark withdrawal 0.12%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.25% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000052534 SOL (0.0105% modal), divergence principal vs HOLD SOL -0.000005040 SOL, PnL LP +0.000047494 SOL (0.0095%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · Pigeon-SOL · 5fkKGrzEXQgdxf1mpXeoeNSPNLyC9BWXKHaK4X1Zi2Ew

2026-09-19T10:51:31+07:00 → 2026-09-19T10:56:28+07:00 · 4.95 menit · pool `2TeUzpJn1XJUXENNNk4mSH5mwkBampxjwsMgafUQuRiZ`.

1. **Market → volatilitas → depth:** Volatility feed 15.842; TVL $10826.15; fee/TVL entry 0.4595%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -601; harga snapshot 0.000002528450 SOL/token; range [-670, -601] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999965 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 80%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000304363 SOL (0.0609% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000304363 SOL (0.0609%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Pigeon-SOL · 53g9TYRQRkaAjAQ33FgmwWYewTtoKHA9PStkjpyEmxjM

2026-09-19T10:57:36+07:00 → 2026-09-19T11:25:44+07:00 · 28.13 menit · pool `2TeUzpJn1XJUXENNNk4mSH5mwkBampxjwsMgafUQuRiZ`.

1. **Market → volatilitas → depth:** Volatility feed 14.951; TVL $12974.27; fee/TVL entry 0.8965%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -580; harga snapshot 0.000003116041 SOL/token; range [-649, -580] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.335560681 SOL + 68627.034420000 token. Porsi token pada mark withdrawal 30.18%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.66% → current -1.07% (dropped 3.73% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.018708628 SOL (3.7417% modal), divergence principal vs HOLD SOL -0.019373543 SOL, PnL LP -0.000664915 SOL (-0.1330%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · BIDDY-SOL · 9UbkiCZPq6K1h5LbBMuQCVhEBKVmeMJNBWjMpSd3L3Ts

2026-09-19T11:37:49+07:00 → 2026-09-19T12:02:15+07:00 · 24.43 menit · pool `HsEApMAQdfECUtxuHxPpDgf7afsm4zKyepkAepCkJMKV`.

1. **Market → volatilitas → depth:** Volatility feed 6.603; TVL $19215.56; fee/TVL entry 1.1735%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -588; harga snapshot 0.000002877612 SOL/token; range [-657, -588] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.426100009 SOL + 30503.737365000 token. Porsi token pada mark withdrawal 13.72%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.64% → current 1.00% (dropped 0.64% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.012861172 SOL (2.5722% modal), divergence principal vs HOLD SOL -0.006131194 SOL, PnL LP +0.006729978 SOL (1.3460%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.009216686; setelah gas terhubung +0.009189575. Swap cocok unik, jeda 10 detik; selisih terhadap mark token +0.002486708 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · LOOP-SOL · 7hk7pHAaD3qYieoDjjtAs89nfrhny25QGWF63iHX6y7K

2026-09-19T11:40:09+07:00 → 2026-09-19T11:48:05+07:00 · 7.93 menit · pool `6gQTdHry76sCzBAeCR8f2EkNYpgWrJjwb9352mF9ts5i`.

1. **Market → volatilitas → depth:** Volatility feed 8.062; TVL $11912.84; fee/TVL entry 0.2877%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -609; harga snapshot 0.000002334981 SOL/token; range [-678, -609] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499995270 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000004079 SOL (0.0008% modal), divergence principal vs HOLD SOL -0.000004695 SOL, PnL LP -0.000000616 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000616; setelah gas terhubung -0.000020616.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · BIDDY-SOL · 5mDAsJGKMr8dH6PeeEQfut3fnDUAnXoJ1ck4GZ9UDkcN

2026-09-19T12:11:23+07:00 → 2026-09-19T12:18:38+07:00 · 7.25 menit · pool `HsEApMAQdfECUtxuHxPpDgf7afsm4zKyepkAepCkJMKV`.

1. **Market → volatilitas → depth:** Volatility feed 6.091; TVL $20827.43; fee/TVL entry 1.0125%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -592; harga snapshot 0.000002765328 SOL/token; range [-661, -592] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999961 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 85.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000178925 SOL (0.0358% modal), divergence principal vs HOLD SOL -0.000000004 SOL, PnL LP +0.000178921 SOL (0.0358%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · BIDDY-SOL · 8HNjNvxfAveA4qF584RP9gaoNLGYXQSw9EG5G9YLmm4h

2026-09-19T12:20:10+07:00 → 2026-09-19T13:04:08+07:00 · 43.97 menit · pool `HsEApMAQdfECUtxuHxPpDgf7afsm4zKyepkAepCkJMKV`.

1. **Market → volatilitas → depth:** Volatility feed 6.806; TVL $20553.29; fee/TVL entry 0.4457%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -583; harga snapshot 0.000003024399 SOL/token; range [-652, -583] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.441232173 SOL + 22628.263282000 token. Porsi token pada mark withdrawal 10.98%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.80% → current 1.19% (dropped 0.61% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.016663394 SOL (3.3327% modal), divergence principal vs HOLD SOL -0.004330224 SOL, PnL LP +0.012333169 SOL (2.4666%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FLAME-SOL · 9jgfhiQuNPGo6mC6qbFAxf7cWrxHeg7uN7on3uYZa58z

2026-09-19T12:49:14+07:00 → 2026-09-19T13:00:08+07:00 · 10.90 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 5.071; TVL $24310.30; fee/TVL entry 0.1305%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -690; harga snapshot 0.000004094801 SOL/token; range [-753, -690] (64 bin), downside 39.47%; bentuk BidAskImBalanced. Model bobot: active bin 0.0481% modal, lima bin terdekat 0.721%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499996629 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 54.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000010907 SOL (0.0022% modal), divergence principal vs HOLD SOL -0.000003341 SOL, PnL LP +0.000007566 SOL (0.0015%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · URANUS-SOL · GqXU1Pi39LsqVLNkWEoE29a2JQBcAKpomPYcSdf6vzQP

2026-09-19T13:27:12+07:00 → 2026-09-19T13:31:10+07:00 · 3.97 menit · pool `7BGoYpsiu8avFAzE8v6zaLx7Dbq7G1jov41VvFn5ncZi`.

1. **Market → volatilitas → depth:** Volatility feed 9.611; TVL $10817.02; fee/TVL entry 1.2904%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1236; harga snapshot 0.000004558081 SOL/token; range [-1305, -1236] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.372966120 SOL + 35049.787843525 token. Porsi token pada mark withdrawal 23.22%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.87% → current -0.37% (dropped 2.24% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.020197299 SOL (4.0395% modal), divergence principal vs HOLD SOL -0.014257162 SOL, PnL LP +0.005940136 SOL (1.1880%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.005592945; setelah gas terhubung +0.005567731. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.000347191 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · SOLCAT-SOL · 2eu4SNBW83C8v5cXrF5qYqKxGoZ8TWnKrGS6Z7bsc1bZ

2026-09-19T13:30:10+07:00 → 2026-09-19T13:38:03+07:00 · 7.88 menit · pool `FEBzyyXLew5E9JngX7CKumHr5ehdUhRb7G6kjouo77dn`.

1. **Market → volatilitas → depth:** Volatility feed 4.891; TVL $16597.93; fee/TVL entry 0.2699%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -453; harga snapshot 0.000003597912 SOL/token; range [-521, -453] (69 bin), downside 57.03%; bentuk BidAskImBalanced. Model bobot: active bin 0.0414% modal, lima bin terdekat 0.621%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.499986496 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000011297 SOL (0.0023% modal), divergence principal vs HOLD SOL -0.000013471 SOL, PnL LP -0.000002174 SOL (-0.0004%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000002174; setelah gas terhubung -0.000022174.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · STONK10-SOL · FhZsTKhs49rCa6hsuKtydJLBeso37dKuJqsoFu4PwqaU

2026-09-19T14:00:10+07:00 → 2026-09-19T15:00:21+07:00 · 60.18 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 2.386; TVL $14106.12; fee/TVL entry 0.0712%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -478; harga snapshot 0.000022175103 SOL/token; range [-515, -478] (38 bin), downside 25.53%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.497975642 SOL + 91.803187000 token. Porsi token pada mark withdrawal 0.40%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 4.62% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000957619 SOL (0.1915% modal), divergence principal vs HOLD SOL -0.000020776 SOL, PnL LP +0.000936843 SOL (0.1874%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · PEPE-SOL · DQLSb1453sW7XNqC7Jtg6DT8PFXje7EHCehGyQJK5mAZ

2026-09-19T14:27:40+07:00 → 2026-09-19T15:27:50+07:00 · 60.17 menit · pool `C1baVnbBd31ucGqvuKgeghtyX6Xpnq5cXxamLqXi9hVN`.

1. **Market → volatilitas → depth:** Volatility feed 1.234; TVL $47725.78; fee/TVL entry 0.0717%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -708; harga snapshot 0.000000035477 SOL/token; range [-744, -708] (37 bin), downside 24.94%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.485239374 SOL + 427716.674500000 token. Porsi token pada mark withdrawal 2.92%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 1.09% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000225966 SOL (0.0452% modal), divergence principal vs HOLD SOL -0.000179289 SOL, PnL LP +0.000046677 SOL (0.0093%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · LEVERHEDGE-SOL · EvdRjz7jZPErQBHycZf5FSTpNCFUkeoiRmVBBKUw38gh

2026-09-19T17:20:17+07:00 → 2026-09-19T17:32:08+07:00 · 11.85 menit · pool `Fc6mmuQNKEoq6C7c1dwh6ppE54tEA2fTWs6ZjFvk4CdA`.

1. **Market → volatilitas → depth:** Volatility feed 7.771; TVL $22016.21; fee/TVL entry 0.1248%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -437; harga snapshot 0.000012928843 SOL/token; range [-506, -437] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499994651 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 54.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000002344 SOL (0.0005% modal), divergence principal vs HOLD SOL -0.000005314 SOL, PnL LP -0.000002970 SOL (-0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000002970; setelah gas terhubung -0.000022970.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · BUTTHOLE-SOL · ERroJtUsS5C3MnQxtqekM9ybCD5QYpt5K516ucS6ucWq

2026-09-19T18:15:11+07:00 → 2026-09-19T18:34:31+07:00 · 19.33 menit · pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatilitas → depth:** Volatility feed 1.728; TVL $67143.67; fee/TVL entry 0.0663%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1392; harga snapshot 0.000015238398 SOL/token; range [-1428, -1392] (37 bin), downside 24.94%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499992081 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 73.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000010585 SOL (0.0021% modal), divergence principal vs HOLD SOL -0.000007900 SOL, PnL LP +0.000002685 SOL (0.0005%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ELON-SOL · 4N7RY2FqqUu8wX8YQei7q98Qkh1XYKpRq3t4sVsvGDBY

2026-09-19T20:00:42+07:00 → 2026-09-19T20:09:04+07:00 · 8.37 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 2.258; TVL $120750.00; fee/TVL entry 0.0507%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -497; harga snapshot 0.000019059677 SOL/token; range [-547, -497] (51 bin), downside 32.86%; bentuk BidAskImBalanced. Model bobot: active bin 0.0754% modal, lima bin terdekat 1.131%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999974 SOL + 0.000000000 token; withdraw 0.499999974 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000007576 SOL (0.0015% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000007576 SOL (0.0015%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · MINI-SOL · E6f1ryyuZBMHeKYXANjMjMUBqaCDzNYZqmp4ZzMga1TV

2026-09-19T20:10:15+07:00 → 2026-09-19T21:04:22+07:00 · 54.12 menit · pool `64BSmy7BESiHnWYzLdPso6FuXymh7H8jTkaiyfbBg1YD`.

1. **Market → volatilitas → depth:** Volatility feed 1.757; TVL $54963.80; fee/TVL entry 0.0906%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -289; harga snapshot 0.000027595342 SOL/token; range [-325, -289] (37 bin), downside 36.06%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499996455 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 90.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000025244 SOL (0.0050% modal), divergence principal vs HOLD SOL -0.000003526 SOL, PnL LP +0.000021718 SOL (0.0043%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · Prism-SOL · HKKyWe2JFtjy1NT1MTPHH8Wqdfsif387shFAdwJz2Dip

2026-09-19T21:25:20+07:00 → 2026-09-19T22:09:02+07:00 · 43.70 menit · pool `9xCHQgVQ3DSDcHu8h2A4njrsWB1J7JceZpEqFLXdmh8f`.

1. **Market → volatilitas → depth:** Volatility feed 4.189; TVL $10913.88; fee/TVL entry 0.1814%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -596; harga snapshot 0.000002657426 SOL/token; range [-659, -596] (64 bin), downside 46.57%; bentuk BidAskImBalanced. Model bobot: active bin 0.0481% modal, lima bin terdekat 0.721%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.500001669 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 6m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 81.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001936560 SOL (0.3873% modal), divergence principal vs HOLD SOL 0.000001699 SOL, PnL LP +0.001938259 SOL (0.3877%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.001971970; setelah gas terhubung +0.001936378. Swap cocok unik, jeda 7 detik; selisih terhadap mark token +0.000033711 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · MON-SOL · 7DFzsBG3HcNyAMfcHB46UJWhgpmsC3hjcQYo3wmt5GRX

2026-09-19T22:07:26+07:00 → 2026-09-19T23:09:15+07:00 · 61.82 menit · pool `6Sz8zKDJJbqJewwQtHvLABuR6zV4mPGAeQ4NY4knbrBu`.

1. **Market → volatilitas → depth:** Volatility feed 1.504; TVL $51527.85; fee/TVL entry 0.7468%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -612; harga snapshot 0.000226630963 SOL/token; range [-657, -612] (46 bin), downside 36.09%; bentuk BidAskImBalanced. Model bobot: active bin 0.0925% modal, lima bin terdekat 1.388%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499521765 SOL + 2.106274800 token. Porsi token pada mark withdrawal 0.09%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.04% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000009129 SOL (0.0018% modal), divergence principal vs HOLD SOL -0.000005591 SOL, PnL LP +0.000003538 SOL (0.0007%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · Tilcayo-SOL · 8tnZZB2uBr2PRbehVyKdz2iqNDYo4kRG1yQ8BiSFHbtK

2026-09-19T22:30:44+07:00 → 2026-09-19T22:37:05+07:00 · 6.35 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 1.556; TVL $124883.42; fee/TVL entry 0.1250%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -410; harga snapshot 0.000016913627 SOL/token; range [-456, -410] (47 bin), downside 36.73%; bentuk BidAskImBalanced. Model bobot: active bin 0.0887% modal, lima bin terdekat 1.330%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999976 SOL + 0.000000000 token; withdraw 0.499978848 SOL + 0.924927000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000005189 SOL (0.0010% modal), divergence principal vs HOLD SOL -0.000005484 SOL, PnL LP -0.000000295 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLEX-SOL · 12usZsaqWtYV522ceUAquyaUavhXZVmuQWjzNs4wnJMF

2026-09-19T23:05:19+07:00 → 2026-09-19T23:20:21+07:00 · 15.03 menit · pool `B3Me7MhVX5XPb4UHpnvYiac8KaTu26uxPzi36GksoUL9`.

1. **Market → volatilitas → depth:** Volatility feed 10.223; TVL $50964.92; fee/TVL entry 0.2769%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -380; harga snapshot 0.000022797014 SOL/token; range [-449, -380] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499996650 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 86.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001655569 SOL (0.3311% modal), divergence principal vs HOLD SOL -0.000003315 SOL, PnL LP +0.001652254 SOL (0.3305%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Aiden-SOL · G1wPGr8Lbbnmc7fFVHBhiD3i38KdQmwCAPVh5i215eTq

2026-09-19T23:19:12+07:00 → 2026-09-20T00:07:10+07:00 · 47.97 menit · pool `6ZVF2gFFMcZRqe5rJLmuzKkYVy6y1Zv6vTV6iRKSBUfX`.

1. **Market → volatilitas → depth:** Volatility feed 6.739; TVL $13574.00; fee/TVL entry 0.1948%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -391; harga snapshot 0.000007772174 SOL/token; range [-471, -391] (81 bin), downside 62.98%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499999797 SOL + 0.000000000 token; withdraw 0.462508930 SOL + 5746.273243000 token. Porsi token pada mark withdrawal 6.92%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.28% → current 1.64% (dropped 0.64% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.010854997 SOL (2.1710% modal), divergence principal vs HOLD SOL -0.003084950 SOL, PnL LP +0.007770047 SOL (1.5540%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil dalam SOL sebelum gas +0.005209204; setelah gas terhubung +0.005160392. Swap cocok unik, jeda 7 detik; selisih terhadap mark token -0.002560843 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FLEX-SOL · GguUAUgbTzxWVDFpTCrUqmVMz6P1HnTvzhS2PRr2mUac

2026-09-19T23:26:04+07:00 → 2026-09-19T23:32:37+07:00 · 6.55 menit · pool `B3Me7MhVX5XPb4UHpnvYiac8KaTu26uxPzi36GksoUL9`.

1. **Market → volatilitas → depth:** Volatility feed 5.343; TVL $50229.23; fee/TVL entry 1.0020%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -390; harga snapshot 0.000020637839 SOL/token; range [-459, -390] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999965 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLEX-SOL · 6Zn5QHKjFY8esvqS6XLhCm1PQ1P1rSKC7L1zytdZ8nH2

2026-09-20T00:25:12+07:00 → 2026-09-20T00:28:44+07:00 · 3.53 menit · pool `B3Me7MhVX5XPb4UHpnvYiac8KaTu26uxPzi36GksoUL9`.

1. **Market → volatilitas → depth:** Volatility feed 5.956; TVL $59304.30; fee/TVL entry 0.0626%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -375; harga snapshot 0.000023959891 SOL/token; range [-444, -375] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499993170 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 66.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001554006 SOL (0.3108% modal), divergence principal vs HOLD SOL -0.000006795 SOL, PnL LP +0.001547211 SOL (0.3094%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · TIPPED-SOL · FxpzPzwcDLr2B7wxVTXW56Vt1ZnBDBSkaBLTEkYP9uFA

2026-09-20T00:35:39+07:00 → 2026-09-20T00:36:40+07:00 · 1.02 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 17.722; TVL $78969.56; fee/TVL entry 4.4999%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -483; harga snapshot 0.000008180436 SOL/token; range [-552, -483] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499999312 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000591 SOL (0.0001% modal), divergence principal vs HOLD SOL -0.000000658 SOL, PnL LP -0.000000067 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000067; setelah gas terhubung -0.000020067.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLEX-SOL · C8edKHVFQfgondBptySqwHpfG8tPu6TmEE6oJvrghzfo

2026-09-20T01:00:19+07:00 → 2026-09-20T01:24:51+07:00 · 24.53 menit · pool `B3Me7MhVX5XPb4UHpnvYiac8KaTu26uxPzi36GksoUL9`.

1. **Market → volatilitas → depth:** Volatility feed 6.367; TVL $18260.86; fee/TVL entry 0.1648%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -342; harga snapshot 0.000033272863 SOL/token; range [-420, -342] (79 bin), downside 53.98%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499997320 SOL + 0.000000000 token; withdraw 0.499998302 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001493685 SOL (0.2987% modal), divergence principal vs HOLD SOL 0.000000982 SOL, PnL LP +0.001494667 SOL (0.2989%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FLEX-SOL · HkQpfUDLxDTRghN3gMT1hEFURNqLtWexdTKpwzeAXXsW

2026-09-20T01:29:19+07:00 → 2026-09-20T01:29:31+07:00 · 0.20 menit · pool `B3Me7MhVX5XPb4UHpnvYiac8KaTu26uxPzi36GksoUL9`.

1. **Market → volatilitas → depth:** Volatility feed 7.145; TVL $26947.61; fee/TVL entry 0.1930%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -330; harga snapshot 0.000037492694 SOL/token; range [-369, -330] (40 bin), downside 32.16%; bentuk BidAskImBalanced. Model bobot: active bin 0.1220% modal, lima bin terdekat 1.829%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.499997549 SOL + 0.000782000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000002154 SOL (0.0004% modal), divergence principal vs HOLD SOL -0.000002402 SOL, PnL LP -0.000000248 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · TIPPED-SOL · AigU9RzD1ZkAtiqhUXgzx2eTL6sgUa9ShczGfZzfcaNy

2026-09-20T02:00:09+07:00 → 2026-09-20T02:04:12+07:00 · 4.05 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 12.855; TVL $95945.33; fee/TVL entry 1.2258%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -445; harga snapshot 0.000011939569 SOL/token; range [-488, -445] (44 bin), downside 34.81%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.444940088 SOL + 5039.448614000 token. Porsi token pada mark withdrawal 10.53%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.36% → current 0.72% (dropped 0.64% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.007607876 SOL (1.5216% modal), divergence principal vs HOLD SOL -0.002715227 SOL, PnL LP +0.004892648 SOL (0.9785%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.002649230; setelah gas terhubung +0.002616344. Swap cocok unik, jeda 9 detik; selisih terhadap mark token -0.002243418 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · TIPPED-SOL · F2VqBA3XeYJqWiuTKyZavvSycgBEHDocrkvKug4sam66

2026-09-20T02:05:45+07:00 → 2026-09-20T02:06:26+07:00 · 0.68 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 13.370; TVL $88888.48; fee/TVL entry 0.8156%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -502; harga snapshot 0.000006771274 SOL/token; range [-537, -502] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499993855 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000005480 SOL (0.0011% modal), divergence principal vs HOLD SOL -0.000006131 SOL, PnL LP -0.000000651 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000651; setelah gas terhubung -0.000020651.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · biketyson-SOL · 6ojxF53zTxru2wvvF52dZSJ5UJJ6QsinQX3qjJhXBxa4

2026-09-20T02:30:06+07:00 → 2026-09-20T02:37:03+07:00 · 6.95 menit · pool `ARqHS4dXM989rYBjDKzx249yqBXQtdrUioemyoGEnAnk`.

1. **Market → volatilitas → depth:** Volatility feed 3.588; TVL $47315.18; fee/TVL entry 0.0910%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -424; harga snapshot 0.000014714229 SOL/token; range [-483, -424] (60 bin), downside 44.40%; bentuk BidAskImBalanced. Model bobot: active bin 0.0546% modal, lima bin terdekat 0.820%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999973 SOL + 0.000000000 token; withdraw 0.499999973 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 28.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · SOLCAT-SOL · 9JCz1cmD1XhEgeQ88yrKFJCXiSpmZ8zrozTMh2ovsWHX

2026-09-20T02:40:21+07:00 → 2026-09-20T04:02:30+07:00 · 82.15 menit · pool `FEBzyyXLew5E9JngX7CKumHr5ehdUhRb7G6kjouo77dn`.

1. **Market → volatilitas → depth:** Volatility feed 4.147; TVL $36444.23; fee/TVL entry 0.2329%; base fee pool 5.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -448; harga snapshot 0.000003828474 SOL/token; range [-483, -448] (36 bin), downside 35.26%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 175516.254978000 token. Porsi token pada mark withdrawal 100.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -11.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.033730409 SOL (6.7461% modal), divergence principal vs HOLD SOL -0.075647375 SOL, PnL LP -0.041916966 SOL (-8.3834%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.062267367; setelah gas terhubung -0.062294120. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.020350401 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · biketyson-SOL · BPe4KvgZ3G2rCdqGm6LAddYLjBYd5vcMXeqMfEkie797

2026-09-20T03:05:13+07:00 → 2026-09-20T04:06:06+07:00 · 60.88 menit · pool `9F5zcBtYYbXGqfMsMyWTKcZmmp3PLsefZCy8oohge9Bs`.

1. **Market → volatilitas → depth:** Volatility feed 2.443; TVL $71293.07; fee/TVL entry 0.0534%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -410; harga snapshot 0.000016913627 SOL/token; range [-462, -410] (53 bin), downside 40.39%; bentuk BidAskImBalanced. Model bobot: active bin 0.0699% modal, lima bin terdekat 1.048%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.497234181 SOL + 166.000984000 token. Porsi token pada mark withdrawal 0.55%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.84% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000177999 SOL (0.0356% modal), divergence principal vs HOLD SOL -0.000040700 SOL, PnL LP +0.000137300 SOL (0.0275%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · JEANPHIL-SOL · 4gi8jbjLZhUzyddYHDb119zMSPFJAcb3Uk8EXKReUY9i

2026-09-20T04:05:47+07:00 → 2026-09-20T04:08:36+07:00 · 2.82 menit · pool `CJab6RE2KNdhCLdY9sBxpijxpFegduaFg83UtEehLPh9`.

1. **Market → volatilitas → depth:** Volatility feed 10.666; TVL $37662.58; fee/TVL entry 1.8637%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -429; harga snapshot 0.000014000084 SOL/token; range [-498, -429] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499997331 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000472930 SOL (0.0946% modal), divergence principal vs HOLD SOL -0.000002634 SOL, PnL LP +0.000470296 SOL (0.0941%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · JEANPHIL-SOL · FZTft4AYJjW8SYP8st6X1uG75E5i47Vu115phVwSezFv

2026-09-20T04:10:09+07:00 → 2026-09-20T04:19:01+07:00 · 8.87 menit · pool `CzVhSwrx9VQmBJTP2BdHgWiRPEcbWBNEAmPCPH1BMJTS`.

1. **Market → volatilitas → depth:** Volatility feed 9.222; TVL $12654.12; fee/TVL entry 3.6130%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -407; harga snapshot 0.000017426127 SOL/token; range [-476, -407] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.470247515 SOL + 1929.668665000 token. Porsi token pada mark withdrawal 5.64%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.27% → current 0.66% (dropped 0.61% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.007693750 SOL (1.5388% modal), divergence principal vs HOLD SOL -0.001639989 SOL, PnL LP +0.006053761 SOL (1.2108%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · JEANPHIL-SOL · 68ro5zGuAbWJvvL9vvM1NXrNLDXDJvfcRA7dSt93ingg

2026-09-20T04:25:14+07:00 → 2026-09-20T04:39:04+07:00 · 13.83 menit · pool `CzVhSwrx9VQmBJTP2BdHgWiRPEcbWBNEAmPCPH1BMJTS`.

1. **Market → volatilitas → depth:** Volatility feed 8.221; TVL $18847.78; fee/TVL entry 1.4947%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -437; harga snapshot 0.000012928843 SOL/token; range [-506, -437] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500002372 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006132062 SOL (1.2264% modal), divergence principal vs HOLD SOL 0.000002407 SOL, PnL LP +0.006134469 SOL (1.2269%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.006296410; setelah gas terhubung +0.006270234. Swap cocok unik, jeda 9 detik; selisih terhadap mark token +0.000161941 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · JEANPHIL-SOL · FpEQFG5MKTxzaXRryvKdbsrPQz1oWiLsfjBkU9nV7xbC

2026-09-20T04:50:44+07:00 → 2026-09-20T04:51:48+07:00 · 1.07 menit · pool `CzVhSwrx9VQmBJTP2BdHgWiRPEcbWBNEAmPCPH1BMJTS`.

1. **Market → volatilitas → depth:** Volatility feed 8.404; TVL $10084.38; fee/TVL entry 0.4269%; base fee pool 5.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -393; harga snapshot 0.000020030883 SOL/token; range [-462, -393] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999958 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000006 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000007 SOL, PnL LP -0.000000001 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000001; setelah gas terhubung -0.000020001.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LOOP-SOL · Acq18gu311dsV1SN9zKKoQoAVepJr8ef6HMiVJKHyoH6

2026-09-20T05:05:12+07:00 → 2026-09-20T05:08:40+07:00 · 3.47 menit · pool `6gQTdHry76sCzBAeCR8f2EkNYpgWrJjwb9352mF9ts5i`.

1. **Market → volatilitas → depth:** Volatility feed 13.764; TVL $10469.26; fee/TVL entry 0.6451%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -555; harga snapshot 0.000003996111 SOL/token; range [-624, -555] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.477297181 SOL + 6218.456018000 token. Porsi token pada mark withdrawal 4.33%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.36% → current 0.69% (dropped 0.67% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.004148111 SOL (0.8296% modal), divergence principal vs HOLD SOL -0.001084517 SOL, PnL LP +0.003063594 SOL (0.6127%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · WOJAK-SOL · Beda7VNauQw5oekNsQqazV2iEaoGNssZzU4qHRKBMxZo

2026-09-20T05:25:13+07:00 → 2026-09-20T05:25:28+07:00 · 0.25 menit · pool `2RX1ZogEMsjv1YjMF3m5U1DN7gVCtSLaQHs27F17ECve`.

1. **Market → volatilitas → depth:** Volatility feed 2.449; TVL $37714.20; fee/TVL entry 0.1675%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -482; harga snapshot 0.000021479468 SOL/token; range [-534, -482] (53 bin), downside 33.92%; bentuk BidAskImBalanced. Model bobot: active bin 0.0699% modal, lima bin terdekat 1.048%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499802861 SOL + 9.146192000 token. Porsi token pada mark withdrawal 0.04%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Stop loss: PnL -100.00% <= -8%
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000003200 SOL (0.0006% modal), divergence principal vs HOLD SOL -0.000000670 SOL, PnL LP +0.000002531 SOL (0.0005%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · fomopay-SOL · EK3V8BK3nKT51BtNgy3ymtRJ95D4LB23kqw8yHA4bDkB

2026-09-20T06:31:16+07:00 → 2026-09-20T06:34:26+07:00 · 3.17 menit · pool `7HXZE3jaXKtToUTqbosSsW1kL8LTt242iaXzrguHhAp1`.

1. **Market → volatilitas → depth:** Volatility feed 21.471; TVL $21951.74; fee/TVL entry 5.3747%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -533; harga snapshot 0.000004974023 SOL/token; range [-602, -533] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.500017810 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.008686185 SOL (1.7372% modal), divergence principal vs HOLD SOL 0.000017844 SOL, PnL LP +0.008704029 SOL (1.7408%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.009177095; setelah gas terhubung +0.009148949. Swap cocok unik, jeda 10 detik; selisih terhadap mark token +0.000473066 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · fomopay-SOL · FJUxPRvbYXWSjMYGpFFUz9ShUEZRrDXCjNodakHViFPZ

2026-09-20T06:35:11+07:00 → 2026-09-20T06:37:24+07:00 · 2.22 menit · pool `7HXZE3jaXKtToUTqbosSsW1kL8LTt242iaXzrguHhAp1`.

1. **Market → volatilitas → depth:** Volatility feed 24.696; TVL $24469.80; fee/TVL entry 6.5908%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -517; harga snapshot 0.000005832433 SOL/token; range [-586, -517] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500000290 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.003531924 SOL (0.7064% modal), divergence principal vs HOLD SOL 0.000000325 SOL, PnL LP +0.003532249 SOL (0.7064%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.003451741; setelah gas terhubung +0.003425866. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.000080508 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · fomopay-SOL · CK8ZgkA8xfcotAZSM299FdoM2i9McbYQ9TWR1dothunD

2026-09-20T06:50:12+07:00 → 2026-09-20T06:54:36+07:00 · 4.40 menit · pool `7HXZE3jaXKtToUTqbosSsW1kL8LTt242iaXzrguHhAp1`.

1. **Market → volatilitas → depth:** Volatility feed 16.706; TVL $38639.94; fee/TVL entry 2.1001%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -503; harga snapshot 0.000006704231 SOL/token; range [-572, -503] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.399514297 SOL + 18358.620363000 token. Porsi token pada mark withdrawal 18.45%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 3.95% → current 2.91% (dropped 1.04% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.022820219 SOL (4.5640% modal), divergence principal vs HOLD SOL -0.010073592 SOL, PnL LP +0.012746627 SOL (2.5493%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.006817594; setelah gas terhubung +0.006791527. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.005929033 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · URANUS-SOL · 5GcucenE1CvaTTmwNyWr7oTZiqSZyCeix3sSac31SLyw

2026-09-20T07:45:21+07:00 → 2026-09-20T07:48:03+07:00 · 2.70 menit · pool `7BGoYpsiu8avFAzE8v6zaLx7Dbq7G1jov41VvFn5ncZi`.

1. **Market → volatilitas → depth:** Volatility feed 31.045; TVL $18681.16; fee/TVL entry 5.6719%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1129; harga snapshot 0.000013218099 SOL/token; range [-1198, -1129] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499994482 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000491873 SOL (0.0984% modal), divergence principal vs HOLD SOL -0.000005483 SOL, PnL LP +0.000486390 SOL (0.0973%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · URANUS-SOL · CoBgwFZ59TXTJ8kpgUz5gfiTyt1YZPN7APfV5QQqig8Y

2026-09-20T07:50:06+07:00 → 2026-09-20T08:07:36+07:00 · 17.50 menit · pool `7BGoYpsiu8avFAzE8v6zaLx7Dbq7G1jov41VvFn5ncZi`.

1. **Market → volatilitas → depth:** Volatility feed 27.419; TVL $33350.45; fee/TVL entry 1.5668%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1118; harga snapshot 0.000014747015 SOL/token; range [-1187, -1118] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500024891 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.022181908 SOL (4.4364% modal), divergence principal vs HOLD SOL 0.000024926 SOL, PnL LP +0.022206834 SOL (4.4414%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · FRIES-SOL · 7R5kTJEwbJZhxZknm2gMtqhEimLLDRMrM6FEeFy9onrV

2026-09-20T09:10:07+07:00 → 2026-09-20T10:10:17+07:00 · 60.17 menit · pool `5QpDQ6ddkv1ArytJQ991kh8doeXPrt9hHFWK2HmEToDm`.

1. **Market → volatilitas → depth:** Volatility feed 4.967; TVL $13986.58; fee/TVL entry 0.8925%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1240; harga snapshot 0.000004380226 SOL/token; range [-1309, -1240] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499798625 SOL + 44.496789950 token. Porsi token pada mark withdrawal 0.04%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.06% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000013269 SOL (0.0027% modal), divergence principal vs HOLD SOL -0.000008364 SOL, PnL LP +0.000004905 SOL (0.0010%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FLAME-SOL · 7kTuwc7qNf1PSGxHz4uGoMWQUPXExijhJ44zpw7ubxGr

2026-09-20T10:20:14+07:00 → 2026-09-20T10:40:04+07:00 · 19.83 menit · pool `JBGqmRZB4csWcQnTMaJGsKBoo4zC1dAoMs7LYGMKqEjD`.

1. **Market → volatilitas → depth:** Volatility feed 3.741; TVL $14758.04; fee/TVL entry 0.2141%; base fee pool 2.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -713; harga snapshot 0.000003409107 SOL/token; range [-773, -713] (61 bin), downside 38.00%; bentuk BidAskImBalanced. Model bobot: active bin 0.0529% modal, lima bin terdekat 0.793%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.499997948 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 73.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000099606 SOL (0.0199% modal), divergence principal vs HOLD SOL -0.000002022 SOL, PnL LP +0.000097584 SOL (0.0195%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ELON-SOL · BvoKCB3bCWXoaqXwtxbLwWmrcgi4EZ3eFkevBSaiG64g

2026-09-20T10:55:11+07:00 → 2026-09-20T11:05:07+07:00 · 9.93 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 7.215; TVL $102685.89; fee/TVL entry 0.0893%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -546; harga snapshot 0.000012898805 SOL/token; range [-585, -546] (40 bin), downside 26.71%; bentuk BidAskImBalanced. Model bobot: active bin 0.1220% modal, lima bin terdekat 1.829%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.499991121 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 66.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000133983 SOL (0.0268% modal), divergence principal vs HOLD SOL -0.000008859 SOL, PnL LP +0.000125124 SOL (0.0250%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Tilcayo-SOL · 8R4YgWDGBkmreUZunzYsKuSAXKkkpGoYYS9GWimYaBA3

2026-09-20T11:00:31+07:00 → 2026-09-20T11:06:53+07:00 · 6.37 menit · pool `DPCrHRkR5kFTYNNmoEz1fS98vgx47aTgkvt2n8haazQ5`.

1. **Market → volatilitas → depth:** Volatility feed 2.929; TVL $100726.71; fee/TVL entry 0.1143%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -453; harga snapshot 0.000011025992 SOL/token; range [-508, -453] (56 bin), downside 42.15%; bentuk BidAskImBalanced. Model bobot: active bin 0.0627% modal, lima bin terdekat 0.940%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499991479 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000007650 SOL (0.0015% modal), divergence principal vs HOLD SOL -0.000008493 SOL, PnL LP -0.000000843 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · TIPPED-SOL · EfsWetG9fnhZqViTVUnA8u7nMyJ7UYmjJVXrY1p6Q1wZ

2026-09-20T14:15:13+07:00 → 2026-09-20T14:58:14+07:00 · 43.02 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 3.314; TVL $18731.46; fee/TVL entry 0.2494%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -551; harga snapshot 0.000004158369 SOL/token; range [-586, -551] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499973109 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 88.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.002921362 SOL (0.5843% modal), divergence principal vs HOLD SOL -0.000026877 SOL, PnL LP +0.002894485 SOL (0.5789%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.002867088; setelah gas terhubung +0.002841930. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.000027397 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · CASHCAT-SOL · DrHKsCUUAUp1xKZwjC8GDcEjCGYTSvo2erFhzLzsDdvT

2026-09-20T14:41:39+07:00 → 2026-09-20T17:07:29+07:00 · 145.83 menit · pool `HqXpWfZdsJCMiwgR8FcmcEN3L7HUZsaifMunaa7ydxTz`.

1. **Market → volatilitas → depth:** Volatility feed 1.149; TVL $39186.58; fee/TVL entry 0.0730%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -421; harga snapshot 0.001516008504 SOL/token; range [-464, -421] (44 bin), downside 34.81%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.484662168 SOL + 10.565645450 token. Porsi token pada mark withdrawal 2.99%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.53% → current 0.92% (dropped 0.61% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.007093196 SOL (1.4186% modal), divergence principal vs HOLD SOL -0.000397903 SOL, PnL LP +0.006695292 SOL (1.3391%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.006727464; setelah gas terhubung +0.006146432. Swap cocok unik, jeda 11 detik; selisih terhadap mark token +0.000032172 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · BUTTHOLE-SOL · Ak8oHSSkunj5MjuxmHKtN4AgN8QquQ5mq5mvHPQudxc

2026-09-20T15:35:22+07:00 → 2026-09-20T15:43:21+07:00 · 7.98 menit · pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatilitas → depth:** Volatility feed 1.301; TVL $93086.46; fee/TVL entry 0.0544%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1392; harga snapshot 0.000015238398 SOL/token; range [-1435, -1392] (44 bin), downside 29.01%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999984 SOL + 0.000000000 token; withdraw 0.499999243 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000003888 SOL (0.0008% modal), divergence principal vs HOLD SOL -0.000000741 SOL, PnL LP +0.000003147 SOL (0.0006%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · JEANPHIL-SOL · ibewmYRQ2oAwrMTkAdNviMoSwMdDn5vGdd6GPE3WQib

2026-09-20T17:05:15+07:00 → 2026-09-20T17:15:07+07:00 · 9.87 menit · pool `5u7PMsDxbaALbV9viti9Y4pEBVJqWSSp69uEsXGtiANq`.

1. **Market → volatilitas → depth:** Volatility feed 2.567; TVL $37419.28; fee/TVL entry 0.0526%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -311; harga snapshot 0.000045295260 SOL/token; range [-363, -311] (53 bin), downside 40.39%; bentuk BidAskImBalanced. Model bobot: active bin 0.0699% modal, lima bin terdekat 1.048%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499999593 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 44.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000030107 SOL (0.0060% modal), divergence principal vs HOLD SOL -0.000000393 SOL, PnL LP +0.000029714 SOL (0.0059%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · JEANPHIL-SOL · 6f3Buc447qjoip9j3uVyeqgvH7H16TvT28o8sQZVfUJk

2026-09-20T17:16:58+07:00 → 2026-09-20T18:05:00+07:00 · 48.03 menit · pool `5u7PMsDxbaALbV9viti9Y4pEBVJqWSSp69uEsXGtiANq`.

1. **Market → volatilitas → depth:** Volatility feed 2.490; TVL $27624.68; fee/TVL entry 0.2547%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -302; harga snapshot 0.000049538758 SOL/token; range [-354, -302] (53 bin), downside 40.39%; bentuk BidAskImBalanced. Model bobot: active bin 0.0699% modal, lima bin terdekat 1.048%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.500008403 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 89.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.002722887 SOL (0.5446% modal), divergence principal vs HOLD SOL 0.000008417 SOL, PnL LP +0.002731304 SOL (0.5463%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · baton-SOL · 2mAgXPGAPEikUuMYMQ4zkDiJkrb9PUhpUuJ8YpcSkhqo

2026-09-20T17:34:43+07:00 → 2026-09-20T17:41:15+07:00 · 6.53 menit · pool `9NdiyGfthT9Co6cCMZG5t4YZXpf6hiJFAEvWRPSUz7s6`.

1. **Market → volatilitas → depth:** Volatility feed 7.026; TVL $31049.40; fee/TVL entry 0.0594%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -378; harga snapshot 0.000023255234 SOL/token; range [-427, -378] (50 bin), downside 38.59%; bentuk BidAskImBalanced. Model bobot: active bin 0.0784% modal, lima bin terdekat 1.176%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999975 SOL + 0.000000000 token; withdraw 0.499990495 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000008331 SOL (0.0017% modal), divergence principal vs HOLD SOL -0.000009480 SOL, PnL LP -0.000001149 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001149; setelah gas terhubung -0.000021149.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · JEANPHIL-SOL · vZeLEpn6UpKMuekHw8qELrVGbJK3ufYi1jeaTX7yrse

2026-09-20T18:07:01+07:00 → 2026-09-20T18:13:03+07:00 · 6.03 menit · pool `5u7PMsDxbaALbV9viti9Y4pEBVJqWSSp69uEsXGtiANq`.

1. **Market → volatilitas → depth:** Volatility feed 3.002; TVL $44871.16; fee/TVL entry 0.0643%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -305; harga snapshot 0.000048081831 SOL/token; range [-360, -305] (56 bin), downside 42.15%; bentuk BidAskImBalanced. Model bobot: active bin 0.0627% modal, lima bin terdekat 0.940%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999972 SOL + 0.000000000 token; withdraw 0.499993768 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 83.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000020660 SOL (0.0041% modal), divergence principal vs HOLD SOL -0.000006204 SOL, PnL LP +0.000014456 SOL (0.0029%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · SCRIBE-SOL · F2VLKzD8kFvvDYCBVAjMVVTNLjzJHLYBuWimkxgGcDj9

2026-09-20T18:30:24+07:00 → 2026-09-20T19:37:43+07:00 · 67.32 menit · pool `BZJTiubWLruAhoBxCTgU3uVdvXFztsr4cKG7SZcxoQdC`.

1. **Market → volatilitas → depth:** Volatility feed 6.239; TVL $12523.13; fee/TVL entry 0.2278%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -526; harga snapshot 0.000005332826 SOL/token; range [-601, -526] (76 bin), downside 52.59%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499997806 SOL + 0.000000000 token; withdraw 0.499993608 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 92.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.006949082 SOL (1.3898% modal), divergence principal vs HOLD SOL -0.000004198 SOL, PnL LP +0.006944884 SOL (1.3890%). Gas transaksi posisi yang terhubung 0.000040000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · OTC-SOL · AnvLEnDqsJ4jj6DL7Zy8vmCR8cswPnRdHw3gDSvJCA13

2026-09-20T18:48:26+07:00 → 2026-09-20T19:09:56+07:00 · 21.50 menit · pool `8LZK8W9Pp6GrMKCoTALS3AZ6eAX62uKv8bHPY57iXZkL`.

1. **Market → volatilitas → depth:** Volatility feed 2.157; TVL $14839.98; fee/TVL entry 0.0562%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -288; harga snapshot 0.000056943525 SOL/token; range [-323, -288] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499994465 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 76.2%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000004929 SOL (0.0010% modal), divergence principal vs HOLD SOL -0.000005521 SOL, PnL LP -0.000000592 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000592; setelah gas terhubung -0.000020592.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · UBI-SOL · NBVUwm4NEbmHp6Pg8KY4FBeWYfc7f4UU9EzegEj5dZc

2026-09-20T19:20:21+07:00 → 2026-09-20T19:43:56+07:00 · 23.58 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 0.890; TVL $20377.52; fee/TVL entry 0.1136%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1179; harga snapshot 0.000008037117 SOL/token; range [-1214, -1179] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499981047 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 78.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000270742 SOL (0.0541% modal), divergence principal vs HOLD SOL -0.000018939 SOL, PnL LP +0.000251803 SOL (0.0504%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · URANUS-SOL · HFqnCftH7wpPxpoqpV7VCpHmNnFLS1Tcjcgv1HwVr8o1

2026-09-20T20:18:46+07:00 → 2026-09-20T21:22:52+07:00 · 64.10 menit · pool `7BGoYpsiu8avFAzE8v6zaLx7Dbq7G1jov41VvFn5ncZi`.

1. **Market → volatilitas → depth:** Volatility feed 4.719; TVL $26328.96; fee/TVL entry 0.1960%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1150; harga snapshot 0.000010725564 SOL/token; range [-1217, -1150] (68 bin), downside 48.66%; bentuk BidAskImBalanced. Model bobot: active bin 0.0426% modal, lima bin terdekat 0.639%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.500000440 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 3.16% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000780739 SOL (0.1561% modal), divergence principal vs HOLD SOL 0.000000474 SOL, PnL LP +0.000781213 SOL (0.1562%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · FLEX-SOL · 3Fq8Qt9k4RtXL3GCFS2ihxCgDDy2MYKURCzqz4fH4QCd

2026-09-20T20:27:35+07:00 → 2026-09-20T22:48:49+07:00 · 141.23 menit · pool `B3Me7MhVX5XPb4UHpnvYiac8KaTu26uxPzi36GksoUL9`.

1. **Market → volatilitas → depth:** Volatility feed 3.471; TVL $26474.88; fee/TVL entry 0.0651%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -424; harga snapshot 0.000014714229 SOL/token; range [-481, -424] (58 bin), downside 43.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0584% modal, lima bin terdekat 0.877%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999971 SOL + 0.000000000 token; withdraw 0.450032742 SOL + 3804.913957000 token. Porsi token pada mark withdrawal 9.42%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 1.89% → current 1.26% (dropped 0.63% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.008935747 SOL (1.7871% modal), divergence principal vs HOLD SOL -0.003161649 SOL, PnL LP +0.005774097 SOL (1.1548%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · EMBER-SOL · 2qxq4JBow7chhTjinjra3HUogCWQtPCHWPHUhDWy7zRw

2026-09-20T21:24:59+07:00 → 2026-09-20T21:30:24+07:00 · 5.42 menit · pool `G6migXbRRTvVhWLQC1KyqXDT2xjVkjcgcyDxSWt3URXG`.

1. **Market → volatilitas → depth:** Volatility feed 2.111; TVL $77233.42; fee/TVL entry 0.0808%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -245; harga snapshot 0.000087350103 SOL/token; range [-294, -245] (50 bin), downside 38.59%; bentuk BidAskImBalanced. Model bobot: active bin 0.0784% modal, lima bin terdekat 1.176%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999975 SOL + 0.000000000 token; withdraw 0.499997642 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000002089 SOL (0.0004% modal), divergence principal vs HOLD SOL -0.000002333 SOL, PnL LP -0.000000244 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000244; setelah gas terhubung -0.000020244.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · STONK10-SOL · EALyvQZ5VJQDbomg3KcjgLnqAdFF5erFv2nWqeB2CeZ2

2026-09-20T22:20:21+07:00 → 2026-09-20T23:01:10+07:00 · 40.82 menit · pool `A8Ui81JDgxgux4iL1iFVHma44Boi3Pcu7UD7Xkm1bDVJ`.

1. **Market → volatilitas → depth:** Volatility feed 2.250; TVL $19816.39; fee/TVL entry 0.2437%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -434; harga snapshot 0.000031486839 SOL/token; range [-470, -434] (37 bin), downside 24.94%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499989173 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 87.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.005628954 SOL (1.1258% modal), divergence principal vs HOLD SOL -0.000010808 SOL, PnL LP +0.005618146 SOL (1.1236%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.005583306; setelah gas terhubung +0.005557848. Swap cocok unik, jeda 8 detik; selisih terhadap mark token -0.000034840 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ELON-SOL · 6FPf7yhzS28EUXZMwjugMvMzeiv3y4dnMVUAa2L6reth

2026-09-21T00:05:11+07:00 → 2026-09-21T00:11:31+07:00 · 6.33 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 2.263; TVL $97076.58; fee/TVL entry 0.1017%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -585; harga snapshot 0.000009453415 SOL/token; range [-634, -585] (50 bin), downside 32.32%; bentuk BidAskImBalanced. Model bobot: active bin 0.0784% modal, lima bin terdekat 1.176%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999975 SOL + 0.000000000 token; withdraw 0.499995259 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000004195 SOL (0.0008% modal), divergence principal vs HOLD SOL -0.000004716 SOL, PnL LP -0.000000521 SOL (-0.0001%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000521; setelah gas terhubung -0.000020521.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · CHILLHOUSE-SOL · NUhLe3APsaEtwyPbGbDm7qXiCfjAYuL8wUTh6U8smgR

2026-09-21T00:10:53+07:00 → 2026-09-21T01:11:24+07:00 · 60.52 menit · pool `Fx4jn8KxoShhfsGJ8heuFh2JiwhWYCodaPiZTt7W4DBx`.

1. **Market → volatilitas → depth:** Volatility feed 1.829; TVL $15446.13; fee/TVL entry 0.1622%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -391; harga snapshot 0.000020433504 SOL/token; range [-438, -391] (48 bin), downside 37.35%; bentuk BidAskImBalanced. Model bobot: active bin 0.0850% modal, lima bin terdekat 1.276%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.493622409 SOL + 320.296186000 token. Porsi token pada mark withdrawal 1.25%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.28% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000058827 SOL (0.0118% modal), divergence principal vs HOLD SOL -0.000150441 SOL, PnL LP -0.000091613 SOL (-0.0183%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · fomopay-SOL · Fa2GM621G13nCecxRBDa7zyovuCdSbEijuEMiP48DTwB

2026-09-21T00:35:44+07:00 → 2026-09-21T00:36:59+07:00 · 1.25 menit · pool `7HXZE3jaXKtToUTqbosSsW1kL8LTt242iaXzrguHhAp1`.

1. **Market → volatilitas → depth:** Volatility feed 15.935; TVL $11249.57; fee/TVL entry 9.3132%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -516; harga snapshot 0.000005890757 SOL/token; range [-585, -516] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999965 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000000 SOL (0.0000% modal), divergence principal vs HOLD SOL 0.000000000 SOL, PnL LP +0.000000000 SOL (0.0000%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil dalam SOL sebelum gas +0.000000000; setelah gas terhubung -0.000015000.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · fomopay-SOL · 9gp5e5sRo5sZnggHVcs15FoQstyYfPDWvRkQRgRyumom

2026-09-21T00:47:18+07:00 → 2026-09-21T00:48:20+07:00 · 1.03 menit · pool `7HXZE3jaXKtToUTqbosSsW1kL8LTt242iaXzrguHhAp1`.

1. **Market → volatilitas → depth:** Volatility feed 16.534; TVL $11894.47; fee/TVL entry 0.2009%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -554; harga snapshot 0.000004036072 SOL/token; range [-700, -554] (147 bin), downside 76.61%; bentuk bid_ask.
3. **Inventory → fee opportunity:** Entry 0.499996392 SOL + 0.000000000 token; withdraw 0.499996343 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000021 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000049 SOL, PnL LP -0.000000028 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000055000 SOL. Hasil dalam SOL sebelum gas -0.000000028; setelah gas terhubung -0.000055028.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · TYLER-SOL · EDhZ5pPJERraevMRE7eN811w3NPvWbb5TLGtDVb2wm5v

2026-09-21T01:22:05+07:00 → 2026-09-21T01:55:13+07:00 · 33.13 menit · pool `5zwSxWKthReYd7K65rmq9ePWFn1jNFRGhpzYaD937zUh`.

1. **Market → volatilitas → depth:** Volatility feed 12.165; TVL $36478.15; fee/TVL entry 2.3298%; base fee pool 1.0%; bin step 125 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -387; harga snapshot 0.000008168130 SOL/token; range [-456, -387] (70 bin), downside 57.56%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999970 SOL + 0.000000000 token; withdraw 0.000000000 SOL + 112243.782666000 token. Porsi token pada mark withdrawal 100.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 5.82% → current 3.57% (dropped 2.25% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.101116108 SOL (20.2232% modal), divergence principal vs HOLD SOL -0.129790413 SOL, PnL LP -0.028674305 SOL (-5.7349%). Gas transaksi posisi yang terhubung 0.000030000 SOL. Hasil dalam SOL sebelum gas +0.006963463; setelah gas terhubung +0.006920570. Swap cocok unik, jeda 7 detik; selisih terhadap mark token +0.035637768 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · GPRO-SOL · 4Nu3Tm83kB4zN2iZpofKLxS7D2tqBYsTcdbrEBxB8Av3

2026-09-21T01:30:09+07:00 → 2026-09-21T02:30:15+07:00 · 60.10 menit · pool `88zowTEupUxc85pjhLgzwiWYomAJyfy5p5i2XX4dDmfi`.

1. **Market → volatilitas → depth:** Volatility feed 1.407; TVL $57416.15; fee/TVL entry 0.2787%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot 250; harga snapshot 0.012032155768 SOL/token; range [206, 250] (45 bin), downside 35.46%; bentuk BidAskImBalanced. Model bobot: active bin 0.0966% modal, lima bin terdekat 1.449%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999977 SOL + 0.000000000 token; withdraw 0.499794618 SOL + 0.016285000 token. Porsi token pada mark withdrawal 0.04%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 0.16% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000034460 SOL (0.0069% modal), divergence principal vs HOLD SOL -0.000009415 SOL, PnL LP +0.000025044 SOL (0.0050%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · LMAO!-SOL · FZH9tdNvJ7myKvfENbyRDpiNkBGCFbcB6CCLDairiX91

2026-09-21T02:05:17+07:00 → 2026-09-21T03:06:13+07:00 · 60.93 menit · pool `EWBCL4hKY6VdzZVcCY7pMPvRhG78koHY6nQnt8EW99Br`.

1. **Market → volatilitas → depth:** Volatility feed 0.575; TVL $19947.07; fee/TVL entry 0.1204%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -381; harga snapshot 0.000022571301 SOL/token; range [-420, -381] (40 bin), downside 32.16%; bentuk BidAskImBalanced. Model bobot: active bin 0.1220% modal, lima bin terdekat 1.829%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.475611472 SOL + 1135.450140000 token. Porsi token pada mark withdrawal 4.74%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 6.21% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.001309004 SOL (0.2618% modal), divergence principal vs HOLD SOL -0.000720938 SOL, PnL LP +0.000588066 SOL (0.1176%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · Stamp-SOL · Eufim8QpCXMovkLhC73p6x4bbkC5hzMmofzHdeweHGsK

2026-09-21T02:35:16+07:00 → 2026-09-21T02:42:19+07:00 · 7.05 menit · pool `F6H5zJeZEUDnYPtcXM3LwQkkcsg1XHLvEJGpB9Mizu1E`.

1. **Market → volatilitas → depth:** Volatility feed 17.973; TVL $47143.78; fee/TVL entry 4.6732%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -376; harga snapshot 0.000023722664 SOL/token; range [-411, -376] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.500007112 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 85.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.014493816 SOL (2.8988% modal), divergence principal vs HOLD SOL 0.000007126 SOL, PnL LP +0.014500942 SOL (2.9002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.014508515; setelah gas terhubung +0.014317922. Swap cocok unik, jeda 7 detik; selisih terhadap mark token +0.000007573 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Stamp-SOL · 654cjDu7WHDohspEzz8XqxzoK4fbmPYNYarET6KGzXnq

2026-09-21T02:46:20+07:00 → 2026-09-21T02:52:36+07:00 · 6.27 menit · pool `J2TSxhVQofzzhpigvwwk2daW8nYziyriqGPx3q7NCXBd`.

1. **Market → volatilitas → depth:** Volatility feed 16.589; TVL $147032.56; fee/TVL entry 2.1477%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -379; harga snapshot 0.000023024984 SOL/token; range [-448, -379] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.499999165 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 33.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000376228 SOL (0.0752% modal), divergence principal vs HOLD SOL -0.000000800 SOL, PnL LP +0.000375428 SOL (0.0751%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Stamp-SOL · 9HUQ2pNiFfkBWeDJbXUSDEZsJr37HheP1EaU7YVgXdTj

2026-09-21T02:58:27+07:00 → 2026-09-21T03:05:55+07:00 · 7.47 menit · pool `F6H5zJeZEUDnYPtcXM3LwQkkcsg1XHLvEJGpB9Mizu1E`.

1. **Market → volatilitas → depth:** Volatility feed 13.196; TVL $54495.91; fee/TVL entry 1.4631%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -402; harga snapshot 0.000018315034 SOL/token; range [-471, -402] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999967 SOL + 0.000000000 token; withdraw 0.342814431 SOL + 11166.034310000 token. Porsi token pada mark withdrawal 28.81%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** take profit
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.098355271 SOL (19.6711% modal), divergence principal vs HOLD SOL -0.018454663 SOL, PnL LP +0.079900608 SOL (15.9801%). Gas transaksi posisi yang terhubung 0.000015000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Stamp-SOL · 2wRKjyqB3b9jCv62kXxzPJ22N3xP4hgz2bXebPLHJbjv

2026-09-21T03:15:24+07:00 → 2026-09-21T03:26:54+07:00 · 11.50 menit · pool `J2TSxhVQofzzhpigvwwk2daW8nYziyriqGPx3q7NCXBd`.

1. **Market → volatilitas → depth:** Volatility feed 11.851; TVL $81250.71; fee/TVL entry 2.1362%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -400; harga snapshot 0.000018683167 SOL/token; range [-469, -400] (70 bin), downside 49.67%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.500000382 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.005646450 SOL (1.1293% modal), divergence principal vs HOLD SOL 0.000000417 SOL, PnL LP +0.005646867 SOL (1.1294%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.005532066; setelah gas terhubung +0.005506318. Swap cocok unik, jeda 7 detik; selisih terhadap mark token -0.000114801 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · Stamp-SOL · C9MayBFAhcQrFdoW1X8q1UHfM8g5Q1JTC1PtX8ZD19xB

2026-09-21T03:30:16+07:00 → 2026-09-21T03:44:21+07:00 · 14.08 menit · pool `J2TSxhVQofzzhpigvwwk2daW8nYziyriqGPx3q7NCXBd`.

1. **Market → volatilitas → depth:** Volatility feed 11.097; TVL $111762.00; fee/TVL entry 0.7216%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -381; harga snapshot 0.000022571301 SOL/token; range [-423, -381] (43 bin), downside 34.16%; bentuk BidAskImBalanced. Model bobot: active bin 0.1057% modal, lima bin terdekat 1.586%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999979 SOL + 0.000000000 token; withdraw 0.398118910 SOL + 5096.163759000 token. Porsi token pada mark withdrawal 19.30%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.88% → current 2.00% (dropped 0.88% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.020592880 SOL (4.1186% modal), divergence principal vs HOLD SOL -0.006668592 SOL, PnL LP +0.013924288 SOL (2.7849%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.012274878; setelah gas terhubung +0.012249350. Swap cocok unik, jeda 6 detik; selisih terhadap mark token -0.001649410 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · TIPPED-SOL · 6KPuw5EHC4Wwswrgag4Qwx2Hsro5XY4bMUZ7D3BfLDu9

2026-09-21T03:45:12+07:00 → 2026-09-21T03:53:42+07:00 · 8.50 menit · pool `66RWZy7xGkUMQ4Aj3ws394nvfQJqFnfvsZmywZzfvwsi`.

1. **Market → volatilitas → depth:** Volatility feed 4.714; TVL $21741.38; fee/TVL entry 0.0947%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -567; harga snapshot 0.000003546346 SOL/token; range [-634, -567] (68 bin), downside 48.66%; bentuk BidAskImBalanced. Model bobot: active bin 0.0426% modal, lima bin terdekat 0.639%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999966 SOL + 0.000000000 token; withdraw 0.499997705 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 37.5%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000003858 SOL (0.0008% modal), divergence principal vs HOLD SOL -0.000002261 SOL, PnL LP +0.000001597 SOL (0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · FRIES-SOL · H1HC4385DcgeabMVs8MkaXZLAumvhd9hqCQdYEpSmeBk

2026-09-21T03:55:15+07:00 → 2026-09-21T04:04:54+07:00 · 9.65 menit · pool `5QpDQ6ddkv1ArytJQ991kh8doeXPrt9hHFWK2HmEToDm`.

1. **Market → volatilitas → depth:** Volatility feed 1.526; TVL $35094.55; fee/TVL entry 0.1881%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1178; harga snapshot 0.000008117489 SOL/token; range [-1214, -1178] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499423067 SOL + 71.057013731 token. Porsi token pada mark withdrawal 0.12%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 44.4%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000022108 SOL (0.0044% modal), divergence principal vs HOLD SOL -0.000000110 SOL, PnL LP +0.000021998 SOL (0.0044%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · fone-SOL · 3u2unAqCDmXcUDfWywstEqJdEwL9ZLh2RqT3m2AYEgai

2026-09-21T04:09:59+07:00 → 2026-09-21T04:54:06+07:00 · 44.12 menit · pool `fAeDy2q7ZjZZZFt6Q1FtbHaCU5dtLEPmYcwcwfAexNA`.

1. **Market → volatilitas → depth:** Volatility feed 2.298; TVL $79267.53; fee/TVL entry 0.0843%; base fee pool 1.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -307; harga snapshot 0.000047134429 SOL/token; range [-358, -307] (52 bin), downside 39.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.0726% modal, lima bin terdekat 1.089%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999974 SOL + 0.000000000 token; withdraw 0.499995672 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 88.6%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000010204 SOL (0.0020% modal), divergence principal vs HOLD SOL -0.000004302 SOL, PnL LP +0.000005902 SOL (0.0012%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · CASHCAT-SOL · 9QoWwY2Ggdiq3kY4XV3C8C6fgwfGhjhuoGTPyXRcoBpN

2026-09-21T05:15:10+07:00 → 2026-09-21T07:44:04+07:00 · 148.90 menit · pool `HqXpWfZdsJCMiwgR8FcmcEN3L7HUZsaifMunaa7ydxTz`.

1. **Market → volatilitas → depth:** Volatility feed 1.229; TVL $19722.88; fee/TVL entry 0.1438%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -415; harga snapshot 0.001609273576 SOL/token; range [-451, -415] (37 bin), downside 30.11%; bentuk BidAskImBalanced. Model bobot: active bin 0.1422% modal, lima bin terdekat 2.134%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999981 SOL + 0.000000000 token; withdraw 0.499370798 SOL + 0.393732970 token. Porsi token pada mark withdrawal 0.13%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 2.90% → current 2.26% (dropped 0.64% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.004014613 SOL (0.8029% modal), divergence principal vs HOLD SOL 0.000004441 SOL, PnL LP +0.004019054 SOL (0.8038%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.004013084; setelah gas terhubung +0.003832987. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.000005970 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · BOT-SOL · 3kNJCR8U2QneDcinBUyNCdYtCHYHfVnuxFDf3bk9yC6b

2026-09-21T05:20:28+07:00 → 2026-09-21T05:35:13+07:00 · 14.75 menit · pool `6fTztHYyqE7HYLrdrJtGd7N44FAS6yLv7jMcuWyB8uen`.

1. **Market → volatilitas → depth:** Volatility feed 1.690; TVL $20065.67; fee/TVL entry 0.0976%; base fee pool 0.8%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot 701; harga snapshot 0.266583342374 SOL/token; range [666, 701] (36 bin), downside 24.34%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499999843 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 64.3%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000001450 SOL (0.0003% modal), divergence principal vs HOLD SOL -0.000000143 SOL, PnL LP +0.000001307 SOL (0.0003%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · ZEBRA-SOL · ExHuwvz7kjCpu1pQQ6SuYGpjpajRgQy3W1t6fsg7iLEE

2026-09-21T05:51:46+07:00 → 2026-09-21T06:02:08+07:00 · 10.37 menit · pool `BjobrawhmMaLZArDayqAQJgztjCrfxkfWgD9w39R7ZPj`.

1. **Market → volatilitas → depth:** Volatility feed 11.922; TVL $20802.36; fee/TVL entry 1.5301%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -559; harga snapshot 0.000003840184 SOL/token; range [-602, -559] (44 bin), downside 34.81%; bentuk BidAskImBalanced. Model bobot: active bin 0.1010% modal, lima bin terdekat 1.515%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.499982656 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.021160256 SOL (4.2321% modal), divergence principal vs HOLD SOL -0.000017324 SOL, PnL LP +0.021142932 SOL (4.2286%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.021142932; setelah gas terhubung +0.021122932.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ZEBRA-SOL · 6feEiVBQs94ddeseRKxySDxgccSxb6zWkpc28B6MQxTB

2026-09-21T06:05:17+07:00 → 2026-09-21T06:06:41+07:00 · 1.40 menit · pool `BjobrawhmMaLZArDayqAQJgztjCrfxkfWgD9w39R7ZPj`.

1. **Market → volatilitas → depth:** Volatility feed 14.913; TVL $16226.93; fee/TVL entry 1.8730%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -573; harga snapshot 0.000003340818 SOL/token; range [-608, -573] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.466405374 SOL + 10598.161287000 token. Porsi token pada mark withdrawal 6.55%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Trailing TP: peak 4.82% → current 0.37% (dropped 4.45% >= 0.6%)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.003412698 SOL (0.6825% modal), divergence principal vs HOLD SOL -0.000897277 SOL, PnL LP +0.002515421 SOL (0.5031%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.003243798; setelah gas terhubung +0.003217783. Swap cocok unik, jeda 10 detik; selisih terhadap mark token +0.000728377 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · ZEBRA-SOL · DTzkinyEJG9y4LLvfpaLPUN1XtxNF54Nu3hsTqo9unwN

2026-09-21T06:27:03+07:00 → 2026-09-21T06:28:08+07:00 · 1.08 menit · pool `BjobrawhmMaLZArDayqAQJgztjCrfxkfWgD9w39R7ZPj`.

1. **Market → volatilitas → depth:** Volatility feed 11.010; TVL $13995.18; fee/TVL entry 0.5439%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -517; harga snapshot 0.000005832433 SOL/token; range [-559, -517] (43 bin), downside 34.16%; bentuk BidAskImBalanced. Model bobot: active bin 0.1057% modal, lima bin terdekat 1.586%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999979 SOL + 0.000000000 token; withdraw 0.499999976 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 0%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000000002 SOL (0.0000% modal), divergence principal vs HOLD SOL -0.000000003 SOL, PnL LP -0.000000001 SOL (-0.0000%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000000001; setelah gas terhubung -0.000020001.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · INU-SOL · 3nhaZ1KRe9ti4BYF2vFdbfvCupB4XHXGavVWcEHmDQzJ

2026-09-21T07:20:22+07:00 → 2026-09-21T07:23:24+07:00 · 3.03 menit · pool `3JgQfQSYuVp1zXF8QxBjiTSfe8bsBQHj1xaJzEDf6B4n`.

1. **Market → volatilitas → depth:** Volatility feed 14.068; TVL $10234.24; fee/TVL entry 1.3873%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -498; harga snapshot 0.000007046214 SOL/token; range [-544, -498] (47 bin), downside 36.73%; bentuk BidAskImBalanced. Model bobot: active bin 0.0887% modal, lima bin terdekat 1.330%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999976 SOL + 0.000000000 token; withdraw 0.500000406 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** pumped far above range
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.005860727 SOL (1.1721% modal), divergence principal vs HOLD SOL 0.000000430 SOL, PnL LP +0.005861157 SOL (1.1722%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas +0.005696342; setelah gas terhubung +0.005667311. Swap cocok unik, jeda 11 detik; selisih terhadap mark token -0.000164815 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. 

## meridian · UBI-SOL · CVkkf6w7zdUobzA86i2vBhg1eeTwacNY3x6DsKD9ozzJ

2026-09-21T07:55:19+07:00 → 2026-09-21T08:02:07+07:00 · 6.80 menit · pool `EyQTPRzUY2VcuiVhJNc8NaYoww2uxTeT4jfb6DqxLxwA`.

1. **Market → volatilitas → depth:** Volatility feed 0.575; TVL $36399.50; fee/TVL entry 0.0622%; base fee pool 3.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1147; harga snapshot 0.000011050560 SOL/token; range [-1182, -1147] (36 bin), downside 29.41%; bentuk BidAskImBalanced. Model bobot: active bin 0.1502% modal, lima bin terdekat 2.252%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999986 SOL + 0.000000000 token; withdraw 0.499998625 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000011330 SOL (0.0023% modal), divergence principal vs HOLD SOL -0.000001361 SOL, PnL LP +0.000009969 SOL (0.0020%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## meridian · RAWR-SOL · Gb41bKtckNkkfT6kTMCDeJqzqJzBzV9sXtkwmy66UofN

2026-09-21T10:10:18+07:00 → 2026-09-21T11:10:27+07:00 · 60.15 menit · pool `D1964idp6yAR2B977RsN9nENpDo5yQdRtf4PxbHSb6Wq`.

1. **Market → volatilitas → depth:** Volatility feed 5.580; TVL $17991.16; fee/TVL entry 0.3773%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -41; harga snapshot 0.000721303739 SOL/token; range [-110, -41] (70 bin), downside 42.29%; bentuk BidAskImBalanced. Model bobot: active bin 0.0402% modal, lima bin terdekat 0.604%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999965 SOL + 0.000000000 token; withdraw 0.449618781 SOL + 78.111045000 token. Porsi token pada mark withdrawal 9.58%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 4.16% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000872338 SOL (0.1745% modal), divergence principal vs HOLD SOL -0.002720589 SOL, PnL LP -0.001848252 SOL (-0.3697%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.003756614; setelah gas terhubung -0.003781839. Swap cocok unik, jeda 10 detik; selisih terhadap mark token -0.001908362 SOL (bukan otomatis slippage).
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · URANUS-SOL · 5Z25kmfRrsnoxzdmabJaMxdQJvdXjmFGYFNBWpjjV2t4

2026-09-21T12:15:23+07:00 → 2026-09-21T13:15:34+07:00 · 60.18 menit · pool `7BGoYpsiu8avFAzE8v6zaLx7Dbq7G1jov41VvFn5ncZi`.

1. **Market → volatilitas → depth:** Volatility feed 2.814; TVL $97370.61; fee/TVL entry 0.0682%; base fee pool 2.0%; bin step 100 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -1166; harga snapshot 0.000009146989 SOL/token; range [-1203, -1166] (38 bin), downside 30.80%; bentuk BidAskImBalanced. Model bobot: active bin 0.1350% modal, lima bin terdekat 2.024%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999978 SOL + 0.000000000 token; withdraw 0.471193541 SOL + 3316.795272372 token. Porsi token pada mark withdrawal 5.61%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Low yield: fee/TVL 3.32% < min 7% (age: 60m)
5. **Jalur yang teramati:** Range efficiency journal 100%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000676322 SOL (0.1353% modal), divergence principal vs HOLD SOL -0.000789165 SOL, PnL LP -0.000112843 SOL (-0.0226%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil net sesudah konversi tidak terisolasi: residual/dust atau swap bercampur inventory lain; jangan gunakan PnL LP sebagai net wallet.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Ada dasar melepaskan modal ketika yield melemah; durasi minimum dan fee posisi perlu dinilai terpisah dari fee/TVL pool. 

## meridian · ELON-SOL · 9M9JEJp7uj8dcHqNJVf7XyTrJCb4FGn1LjjymTM8K5QM

2026-09-21T12:54:52+07:00 → 2026-09-21T13:01:37+07:00 · 6.75 menit · pool `6DFDBDKKvYuVz8rSVg7a1zdhZKwZXG95CwH6uKwJUumq`.

1. **Market → volatilitas → depth:** Volatility feed 6.599; TVL $58132.53; fee/TVL entry 0.0678%; base fee pool 1.0%; bin step 80 bps.
2. **Active bin → range → distribusi:** Active bin pada instruksi/snapshot -601; harga snapshot 0.000008321856 SOL/token; range [-640, -601] (40 bin), downside 26.71%; bentuk BidAskImBalanced. Model bobot: active bin 0.1220% modal, lima bin terdekat 1.829%; distribusi aktual per bin historis tidak tersedia.
3. **Inventory → fee opportunity:** Entry 0.499999980 SOL + 0.000000000 token; withdraw 0.499990029 SOL + 0.000000000 token. Porsi token pada mark withdrawal 0.00%. Forecast fee posisi numerik tidak tercatat.
4. **Keputusan exit/rebalance:** Out of range for 5m (limit: 5m)
5. **Jalur yang teramati:** Range efficiency journal 16.7%; metrik ini hanya memakai OOR terakhir. Harga minimum/maksimum historis tidak direkonstruksi dari harga pool saat audit.
6. **Fee → drift → divergence → hasil:** Fee +0.000008807 SOL (0.0018% modal), divergence principal vs HOLD SOL -0.000009951 SOL, PnL LP -0.000001144 SOL (-0.0002%). Gas transaksi posisi yang terhubung 0.000020000 SOL. Hasil dalam SOL sebelum gas -0.000001144; setelah gas terhubung -0.000021144.
7. **Penilaian tanpa hindsight:** Keputusan entry tidak bisa dinilai optimal tanpa depth per bin dan forecast fee pada waktu entry. Penempatan batas atas sesuai desain single-sided SOL. Outcome fee <1 bp menunjukkan round-trip minim fee, bukan bukti entry salah tanpa data saat entry. 

## azimuth · BUTTHOLE-SOL · CANoDuDqwG8zr97dy9946io569GFgj5ssxJ8EBjxKXsY — masih terbuka

Entry 21 September 2026 14:21:57 WIB; belum ditutup pada snapshot utama. Pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatility → depth:** entry TVL $78807.56, volatility feed 3.0079, fee/TVL snapshot 0.05318%. Regime dan expected fee posisi belum terkalibrasi.
2. **Active bin → range:** active entry -1371, harga 0.00001801401325076514 SOL/token, range -1424…-1371, bin step 80 bps. Current active bin pada response -1373. Downside nominal 34.447%, BidAsk single-sided SOL; tidak ada up-side token ladder.
3. **Distribusi → inventory:** 54 bin, model linear bobot ke sisi bawah. Deposit 0.119999974 SOL, nol token awal. Inventory current 27.167296158 BUTTHOLE + 0.119515257 SOL; mark total 0.119991908 SOL.
4. **Fee opportunity → keputusan:** entry mengandalkan snapshot fee pool; tidak ada forecast fee posisi yang tersimpan. Pada snapshot posisi masih di dalam range; monitor belum meminta close/rebalance. Outcome masa depan tidak dipakai untuk menilai hold ini.
5. **Fees → drift → divergence:** unclaimed fee 0.000023771 SOL, perubahan principal terhadap deposit sekitar -0.000008066 SOL pada mark current. Nested SOL PnL +0.000015705 SOL. Seluruhnya masih unrealized, belum hasil swap atau net gas.
6. **Kualitas data:** legacy currentValue/liquidity nol dan legacy impermanentLoss negatif seluruh deposit bertentangan dengan inventory/value pada response yang sama. Dossier memakai field inventory, valueNative, dan unCollectedFeeNative yang bisa direkonsiliasi; bukan menganggap legacy IL sebagai rugi nyata.
7. **Penilaian saat keputusan:** orientasi/range sesuai single-sided SOL, tidak ada bukti final profit/loss karena masih terbuka. Exact share historis per bin dan expected fee tidak tersedia.

