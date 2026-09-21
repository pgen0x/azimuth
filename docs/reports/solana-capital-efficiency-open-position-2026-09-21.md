## azimuth · BUTTHOLE-SOL · CANoDuDqwG8zr97dy9946io569GFgj5ssxJ8EBjxKXsY — masih terbuka

Entry 21 September 2026 14:21:57 WIB; belum ditutup pada snapshot utama. Pool `EAf6shtt8QGJ7UiSRrDc6pzwXKEmb5s7tCCpSDe5zpzZ`.

1. **Market → volatility → depth:** entry TVL $78807.56, volatility feed 3.0079, fee/TVL snapshot 0.05318%. Regime dan expected fee posisi belum terkalibrasi.
2. **Active bin → range:** active entry -1371, harga 0.00001801401325076514 SOL/token, range -1424…-1371, bin step 80 bps. Current active bin pada response -1373. Downside nominal 34.447%, BidAsk single-sided SOL; tidak ada up-side token ladder.
3. **Distribusi → inventory:** 54 bin, model linear bobot ke sisi bawah. Deposit 0.119999974 SOL, nol token awal. Inventory current 27.167296158 BUTTHOLE + 0.119515257 SOL; mark total 0.119991908 SOL.
4. **Fee opportunity → keputusan:** entry mengandalkan snapshot fee pool; tidak ada forecast fee posisi yang tersimpan. Pada snapshot posisi masih di dalam range; monitor belum meminta close/rebalance. Outcome masa depan tidak dipakai untuk menilai hold ini.
5. **Fees → drift → divergence:** unclaimed fee 0.000023771 SOL, perubahan principal terhadap deposit sekitar -0.000008066 SOL pada mark current. Nested SOL PnL +0.000015705 SOL. Seluruhnya masih unrealized, belum hasil swap atau net gas.
6. **Kualitas data:** legacy currentValue/liquidity nol dan legacy impermanentLoss negatif seluruh deposit bertentangan dengan inventory/value pada response yang sama. Dossier memakai field inventory, valueNative, dan unCollectedFeeNative yang bisa direkonsiliasi; bukan menganggap legacy IL sebagai rugi nyata.
7. **Penilaian saat keputusan:** orientasi/range sesuai single-sided SOL, tidak ada bukti final profit/loss karena masih terbuka. Exact share historis per bin dan expected fee tidak tersedia.

