# Rekonstruksi posisi LP — snapshot 21 September 2026 14:43:06 WIB

Setiap bagian memisahkan informasi entry, keputusan saat posisi berjalan, dan outcome. Hasil sesudah entry tidak dipakai sebagai sinyal yang dianggap tersedia saat entry. `volatility` adalah angka feed yang tercatat, bukan estimasi sigma harian yang telah diverifikasi. TVL adalah kedalaman agregat, bukan kedalaman eksekusi per bin. Rasio fee entry adalah snapshot pool sesuai timeframe sumber, bukan expected return posisi.

Deposit/withdrawal/fee berasal dari Meteora API dan masih memakai valuasi token API. Divergence di sini adalah perubahan principal terhadap HOLD inventory awal yang seluruhnya SOL, sebelum fee; bukan rumus IL pool constant-product 50:50. Exact swap hanya dicocokkan jika mint, jumlah token penuh, dan waktu cocok unik; sisanya tidak dianggap nol. Gas yang terhubung bukan seluruh overhead wallet.

Distribusi nominal BidAsk adalah model linear SDK satu sisi (bobot 1..N dari active bin ke ujung bawah), bukan snapshot historis likuiditas aktual. Perubahan bin saat inclusion, share terhadap liquidity pesaing, dynamic fee per swap, price-impact quote, dan price path lengkap tidak tersimpan. Tidak ada counterfactual profit yang diklaim. In-range Azimuth adalah observasi monitor dengan gap >180 detik dikeluarkan. In-range Meridian dari journal hanya mengurangi episode OOR terakhir, bukan cumulative occupancy yang terverifikasi.

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

