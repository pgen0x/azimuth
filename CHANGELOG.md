# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.10.0](https://github.com/pgen0x/azimuth/compare/v2.9.0...v2.10.0) (2026-10-09)


### Features

* **accounting:** bound pool cash across shared rent refunds ([7dd5860](https://github.com/pgen0x/azimuth/commit/7dd5860884c2f9a54582ba83fe5d6e320104f92e))
* **accounting:** bound pool cash across shared rent refunds ([0f4ccf8](https://github.com/pgen0x/azimuth/commit/0f4ccf81a97f9839bc3976e5d08147f87d5af5c5))
* add local operational dashboard for Solana evidence ([#166](https://github.com/pgen0x/azimuth/issues/166)) ([3ba4be0](https://github.com/pgen0x/azimuth/commit/3ba4be0780732c6a49eabdbabc3f2afe197ef7e0))


### Bug Fixes

* accept valid non-tool AI health responses ([72b934c](https://github.com/pgen0x/azimuth/commit/72b934c192dda43563bde5c08acc2b0ba9a63f05))
* **accounting:** pace keyless NAV quotes within rate and time limits ([f585507](https://github.com/pgen0x/azimuth/commit/f585507e3a017d8a1b81afd81572126ecf822d87))
* **accounting:** preserve exact SOL value in cached quotes ([#164](https://github.com/pgen0x/azimuth/issues/164)) ([5a19cfd](https://github.com/pgen0x/azimuth/commit/5a19cfd88915bcff291ed50abcf709a3fe42c72a))
* **accounting:** reconcile rent for reused route accounts ([311e4b5](https://github.com/pgen0x/azimuth/commit/311e4b509da5a7fda23707fcf4b3bd1d4474eb58))
* **accounting:** reconcile rent for reused route accounts ([8535a46](https://github.com/pgen0x/azimuth/commit/8535a46309228596256cbdcbe4305874c004fd60))
* **accounting:** require a valid balance slot for quote marks ([883f6aa](https://github.com/pgen0x/azimuth/commit/883f6aa76550dbde56b236c4409f70cf08009974))
* **accounting:** respect keyless quote rate and snapshot budget ([163fa07](https://github.com/pgen0x/azimuth/commit/163fa078a1f1066ee83899213f5e909d7ea09327))
* **accounting:** validate quote provenance and rotate attempted accounts ([c53b05f](https://github.com/pgen0x/azimuth/commit/c53b05ffe075698160a5ad58caa43ed9b0faea9b))
* **accounting:** validate quote slots and fair bounded rotation ([522bbbd](https://github.com/pgen0x/azimuth/commit/522bbbd32e096a8d9bedbaa99ed0cfbfdc373db5))
* **audit:** distinguish missing evidence from measured token risk ([4111952](https://github.com/pgen0x/azimuth/commit/4111952d67b6d7d8077cac9d9e7d7b3979618eaf))
* **audit:** retain unknown token evidence and measured failures ([0190ec8](https://github.com/pgen0x/azimuth/commit/0190ec8b09944f36fbc7951aa47b4c8587669e23))
* avoid false AI fallback from truncated health probes ([#167](https://github.com/pgen0x/azimuth/issues/167)) ([63b24a2](https://github.com/pgen0x/azimuth/commit/63b24a28fcc96a0c5d8ecf8273b26c63d494b1a5))
* cache fresh Jupiter quote marks ([86f7fbb](https://github.com/pgen0x/azimuth/commit/86f7fbb50b5ae39d2dba3c81545705965e893f5f))
* classify funded LP cohorts and avoid sub-lamport wins ([#168](https://github.com/pgen0x/azimuth/issues/168)) ([e7e75b6](https://github.com/pgen0x/azimuth/commit/e7e75b69d8b5bb98582ddbd1bad7610cca272848))
* **evaluation:** correlate guarded pipeline receipts with AI deliveries ([08856ee](https://github.com/pgen0x/azimuth/commit/08856ee76dc771ce774d759d0c77249073e96025))
* **evaluation:** correlate guarded pipeline receipts with AI deliveries ([39e751a](https://github.com/pgen0x/azimuth/commit/39e751ab602efd0d75792c12dc54286888d71dd9))
* **evaluation:** correlate Hermes multiplex webhook sessions ([#165](https://github.com/pgen0x/azimuth/issues/165)) ([ceed70f](https://github.com/pgen0x/azimuth/commit/ceed70f57bbb3e798e4283d6cd61b8ea7498f769))
* **evaluation:** report root cash after proved rent refunds ([468372d](https://github.com/pgen0x/azimuth/commit/468372d0abe84189b0fa17230bd7db467cdc319b))
* **evaluation:** show root cash after proved rent refunds ([f1035bf](https://github.com/pgen0x/azimuth/commit/f1035bf875b8f5e469ec006afdeb002fdedd7793))
* **hermes:** avoid setup work during DLMM webhook batches ([30713a2](https://github.com/pgen0x/azimuth/commit/30713a2d31848b96c395d8d4b4e84635db2ad73d))
* **hermes:** keep webhook batches out of dependency setup ([bc180fc](https://github.com/pgen0x/azimuth/commit/bc180fc3aba7d359e283ecc523470911fa514ffc))
* **hermes:** require execution receipts for deployment reports ([1143b01](https://github.com/pgen0x/azimuth/commit/1143b0145ecd95ccb55db4e390789ec8c5748167))
* **hermes:** specify absolute command paths and timeout seconds ([5075347](https://github.com/pgen0x/azimuth/commit/5075347efb0cbc0b62f391320bc28aa418e143e3))
* **hermes:** specify absolute command paths and timeout seconds ([523e8d9](https://github.com/pgen0x/azimuth/commit/523e8d9c3a85f9c40f7ea51960f3f8f1acdc27b6))
* **hermes:** verify deployment reports against pipeline receipts ([a4470b7](https://github.com/pgen0x/azimuth/commit/a4470b74c7bb6ba704e55801509093338e2582aa))
* **ops:** honor router account limits across models ([5a744ec](https://github.com/pgen0x/azimuth/commit/5a744ecccef35ff0ea10ec63f49c59e0577a563c))
* **ops:** honor shared router account cooldowns ([dab21db](https://github.com/pgen0x/azimuth/commit/dab21dbe2fa8102542c72a105e1c28e657170671))
* **ops:** preserve provider quota reset deadlines ([9c4b294](https://github.com/pgen0x/azimuth/commit/9c4b29418766179dc51eeddad86b2d059e83a3b2))
* **ops:** stop exhausted quota retries and persist cached resets ([546a1f8](https://github.com/pgen0x/azimuth/commit/546a1f87b04f4bfd969b466a469d0ffd17a938c6))
* **ops:** stop exhausted quota retries and preserve resets ([c10f0f1](https://github.com/pgen0x/azimuth/commit/c10f0f136e7676075e032ba737917b66dcfd844e))
* **pipeline:** apply the learned weight envelope in fallback ranking ([6683cef](https://github.com/pgen0x/azimuth/commit/6683cefd599cbf3c32d80366c4da4f648708e3b1))
* **pipeline:** preserve measured predeploy gate evidence ([20835e0](https://github.com/pgen0x/azimuth/commit/20835e013e8df9d340ebf7ddccc420420ada476c))
* **pipeline:** preserve measured predeploy gate evidence ([660814d](https://github.com/pgen0x/azimuth/commit/660814de3f092bb8ba4c9c1554a2d1c259230ead))
* **pipeline:** read learned weights from the writer envelope ([a0ad422](https://github.com/pgen0x/azimuth/commit/a0ad4229855e8b35409e7bb55b85c0efcaecfe08))
* **pipeline:** share live entry gates before any token swap ([93dd3f0](https://github.com/pgen0x/azimuth/commit/93dd3f0f0df92bb9c7a706112b7e7b797d964fe8))
* **pipeline:** share live entry gates before any token swap ([13387ff](https://github.com/pgen0x/azimuth/commit/13387ff0b4e72f77540ac1c4504f26ae3fb733dc))
* preflight local Hermes webhook before AI route ([26f9b93](https://github.com/pgen0x/azimuth/commit/26f9b937114f0e8e8acc36e854bee28b5d39b594))
* **pulse:** cap bot holder share at 25% ([#201](https://github.com/pgen0x/azimuth/issues/201)) ([43a1121](https://github.com/pgen0x/azimuth/commit/43a1121e9aeb5eb6e60039a18b9d1031754e81e3))
* **report:** label fee TVL timeframe accurately ([#200](https://github.com/pgen0x/azimuth/issues/200)) ([113951f](https://github.com/pgen0x/azimuth/commit/113951f7a5c9020fb0fdf5550a8a49f1ddc76e90))
* **router:** cool definitively retired Gemini models ([3431ff3](https://github.com/pgen0x/azimuth/commit/3431ff3bf68cfe199ce25d837c9800793503d528))
* **router:** cool definitively retired Gemini models ([382c3c7](https://github.com/pgen0x/azimuth/commit/382c3c796711f17a4ab75ffb878fd38388bf0501))
* **router:** cool down exhausted provider budgets across models ([15309c5](https://github.com/pgen0x/azimuth/commit/15309c587f96cd03b712ac88151307b1f116e11c))
* **router:** cool down exhausted provider budgets across models ([b8607ae](https://github.com/pgen0x/azimuth/commit/b8607ae410bf7de09ab936a8ab79e380fda89282))
* **router:** cool down unavailable public and free models ([a6d49b9](https://github.com/pgen0x/azimuth/commit/a6d49b9281021838a5b1607a8ed30f7ff4117834))
* **router:** cool down unavailable public and free models ([9fdc3fc](https://github.com/pgen0x/azimuth/commit/9fdc3fc464cb21c5a88f87c00f3738312767bc6d))
* **router:** fall back on Antigravity retirement notices ([34e3b61](https://github.com/pgen0x/azimuth/commit/34e3b61ec9aadb27168f615042ae982c7afb35ff))
* **router:** fall back on Antigravity retirement notices ([46ec7e1](https://github.com/pgen0x/azimuth/commit/46ec7e1d0751890568aacaf3b921d4b1d4be08ba))
* **router:** honor Gemini daily quota reset per model ([4966e12](https://github.com/pgen0x/azimuth/commit/4966e12acd6ef90de121d7b5650701429609d579))
* **router:** respect Gemini API daily quota reset deadlines ([60c44be](https://github.com/pgen0x/azimuth/commit/60c44bee27c0890c7e993456aa63db443e8f662c))
* **scanner:** log AI probe HTTP status ([51e2662](https://github.com/pgen0x/azimuth/commit/51e266264875009732ad05ae25b867468d50233a))
* **scanner:** log AI probe HTTP status ([58e5f56](https://github.com/pgen0x/azimuth/commit/58e5f56a60e088cd6a3e47db32d11f507a9a0cb9))
* **settlement:** recover rent atomically for residual swaps ([dba5db7](https://github.com/pgen0x/azimuth/commit/dba5db795fc6a05ec32d59c13a48c2c9482a6db0))
* **settlement:** recover rent atomically for uneconomic residual swaps ([5bf571d](https://github.com/pgen0x/azimuth/commit/5bf571dd21a68f46b7ea6ab5fbe6acc92b604bf4))
* **solana:** benchmark SOL-only bin replay against held SOL ([7a07cce](https://github.com/pgen0x/azimuth/commit/7a07cce3f923d7e15c2e13050a966b337639bc48))
* **solana:** benchmark SOL-only bin replay against held SOL ([69a314e](https://github.com/pgen0x/azimuth/commit/69a314e4040c72e6dcd74f67333dc59636f46e36))
* **solana:** exclude unmeasured atomic rent from swap fills ([ee34ba5](https://github.com/pgen0x/azimuth/commit/ee34ba57bad4d3f37d03174d606d82295fde78c4))
* **solana:** exclude unmeasured atomic rent from swap fills ([86d8d55](https://github.com/pgen0x/azimuth/commit/86d8d55dc3501854b9699cfcfb6fb92aa6a61359))
* **solana:** fit NAV quotes within cache freshness ([c8badbe](https://github.com/pgen0x/azimuth/commit/c8badbef8ce48b46abad3118c0676fde3fbeb7ce))
* **solana:** fit NAV quotes within cache freshness ([082235a](https://github.com/pgen0x/azimuth/commit/082235aec3010c04aa76ace051f53f85d1850e8c))
* **solana:** give tied signals equal ranking weight ([ec6f3e5](https://github.com/pgen0x/azimuth/commit/ec6f3e51de63e1679c42b3f988133058beef837e))
* **solana:** give tied signals equal ranking weight ([b2e354a](https://github.com/pgen0x/azimuth/commit/b2e354a254387ee0588df035242a32ac1ba346c8))
* **solana:** learn cash signal weights per entry mode ([0052811](https://github.com/pgen0x/azimuth/commit/0052811e2fdd681ec2ce363daf8bfbc13c822938))
* **solana:** learn cash signal weights per entry mode ([514e6a3](https://github.com/pgen0x/azimuth/commit/514e6a3c00f5a990eedf19a28b8c9cb7a598e050))
* **solana:** learn signal weights from proved cash outcomes ([55eae85](https://github.com/pgen0x/azimuth/commit/55eae85279c6adb4d1860f719bcdc1b65bd813e4))
* **solana:** learn signal weights from proved cash outcomes ([ac0d3df](https://github.com/pgen0x/azimuth/commit/ac0d3df269306b6cb6f94837c938380f511a8864))
* **solana:** preserve legacy balances without stranding fresh lots ([cf61543](https://github.com/pgen0x/azimuth/commit/cf615436e81da5b34ec06cbdfda05332d03d1e24))
* **solana:** preserve legacy tokens during automatic settlement ([4c302ff](https://github.com/pgen0x/azimuth/commit/4c302ffa919f62ba6171fee96885609c56852d4b))
* **solana:** prove fresh settlement lots despite historical residues ([f20112d](https://github.com/pgen0x/azimuth/commit/f20112d56ff1f2ff38d79ad59e778fe9ad04aaec))
* **solana:** reclaim empty hook and pausable route accounts ([4cffb04](https://github.com/pgen0x/azimuth/commit/4cffb04a490b323fffa6415f8d5bb078bffa34e7))
* **solana:** reclaim empty hook and pausable route accounts ([2bf7bff](https://github.com/pgen0x/azimuth/commit/2bf7bff7ea375e3f761ff9cab220f30dbe6d76cb))
* **solana:** reconcile signed transactions after broadcast errors ([f2849f8](https://github.com/pgen0x/azimuth/commit/f2849f828bbbdc5391ea156b01450d74a620fe70))
* **solana:** reconcile signed transactions after broadcast errors ([89bdf28](https://github.com/pgen0x/azimuth/commit/89bdf28e4aefc689d2c32d9678f0c43554429838))
* **solana:** settle only proved position token inventory ([1820819](https://github.com/pgen0x/azimuth/commit/182081957712d4e12ed953523056c6a89c627316))
* **solana:** use finalized blockhash for rent fee checks ([6d2b65c](https://github.com/pgen0x/azimuth/commit/6d2b65c0cb29614fb5850a0e3ae615bc3e120dcb))
* **solana:** use finalized blockhash for rent fee checks ([b994d95](https://github.com/pgen0x/azimuth/commit/b994d95838d77d6d1f5f1d287013a98f7671e2dd))


### Performance Improvements

* **hermes:** consolidate local AI pick context reads ([6d3c270](https://github.com/pgen0x/azimuth/commit/6d3c270bb8af895340519952812937c6cc24242e))
* **hermes:** consolidate local AI pick context reads ([586a379](https://github.com/pgen0x/azimuth/commit/586a37981e16e68ef8cfa4ac55a8e2e5860c703b))
* **hermes:** scope DLMM webhook tools to terminal ([c00bee1](https://github.com/pgen0x/azimuth/commit/c00bee14c9024a0c010a7456311bf324ef8d7676))
* **hermes:** scope DLMM webhook tools to terminal ([13527e7](https://github.com/pgen0x/azimuth/commit/13527e74bc8bb8c7868e4ef425c796be7ec99d65))

## [2.9.0](https://github.com/pgen0x/azimuth/compare/v2.8.0...v2.9.0) (2026-10-05)


### Features

* **accounting:** collect bounded rent account histories ([#143](https://github.com/pgen0x/azimuth/issues/143)) ([ad19477](https://github.com/pgen0x/azimuth/commit/ad19477b9c83dc61e2c08dbf8ec1fde894692964))
* **accounting:** report cash with proven rent refunds ([#144](https://github.com/pgen0x/azimuth/issues/144)) ([4796837](https://github.com/pgen0x/azimuth/commit/479683771034c16dfd18796f3128511b9ab0af10))
* **accounting:** retain exact token account rent evidence ([#140](https://github.com/pgen0x/azimuth/issues/140)) ([8c8e211](https://github.com/pgen0x/azimuth/commit/8c8e211b642a1949ffab52d7d9365277017e9be3))
* **evaluation:** report swap fills and failed fees by slippage ([#160](https://github.com/pgen0x/azimuth/issues/160)) ([69ccf7b](https://github.com/pgen0x/azimuth/commit/69ccf7b2a43ce13d98970717cb59c1914f7f57aa))
* observe liquidation quotes alongside LP marks ([#161](https://github.com/pgen0x/azimuth/issues/161)) ([5b4d317](https://github.com/pgen0x/azimuth/commit/5b4d317f86652d6af4079e7adb8504c39c39b437))
* **solana:** add Helius supplementary NAV valuation ([497cd49](https://github.com/pgen0x/azimuth/commit/497cd491660681ae5da4b19bee527d3a5ceba737))
* **solana:** add Helius supplementary NAV valuation ([d3a6001](https://github.com/pgen0x/azimuth/commit/d3a60013651be8ef1b93e06c03bf6628fffcfaed))
* **solana:** reclaim empty SPL account rent with execution guards ([5d80b17](https://github.com/pgen0x/azimuth/commit/5d80b1725b5baefd3613a9fd144a604b41479181))
* **solana:** safely reclaim empty classic token account rent ([5732dbf](https://github.com/pgen0x/azimuth/commit/5732dbf0b2004359d860a50df2eaa84cc010f889))


### Bug Fixes

* account for program funding via allocate and assign ([dfede39](https://github.com/pgen0x/azimuth/commit/dfede3976e42fffaf8746691249030e4b9788903))
* account for program funding via allocate and assign ([92ec196](https://github.com/pgen0x/azimuth/commit/92ec1964cd6c2ed117e827c54f7e914a4978e473))
* **accounting:** keep incomplete realized values retryable ([#142](https://github.com/pgen0x/azimuth/issues/142)) ([2bc9689](https://github.com/pgen0x/azimuth/commit/2bc9689e56c647b4cc10fb6acf118c7d48350ef8))
* **accounting:** retain swap quotes before broadcast ([#145](https://github.com/pgen0x/azimuth/issues/145)) ([01591f8](https://github.com/pgen0x/azimuth/commit/01591f8e4ed201c82d3dcf6015adf08c5ac59521))
* **ai:** keep zero-position checks from aborting webhook picks ([#150](https://github.com/pgen0x/azimuth/issues/150)) ([09fba24](https://github.com/pgen0x/azimuth/commit/09fba242330fa90290bd0fd95093ee6428c4b62f))
* allow configured AI fallback chain to finish probing ([0621c86](https://github.com/pgen0x/azimuth/commit/0621c86660d280ee4e27c08d97ef72be89fb58c6))
* allow configured AI fallback chain to finish probing ([17094e8](https://github.com/pgen0x/azimuth/commit/17094e8b1d4f52a3b17077ea44ecc148fcf02a03))
* apply configured cleanup floor to both post-close swaps ([640d3bc](https://github.com/pgen0x/azimuth/commit/640d3bc9b00be1a0b988d510aeaa42709da41c40))
* avoid redundant fee transaction before combined close ([#133](https://github.com/pgen0x/azimuth/issues/133)) ([823aec1](https://github.com/pgen0x/azimuth/commit/823aec1e287a9dc00d177d447db4d0938e2a2158))
* classify memo transfers without counting inflows as profit ([bce6491](https://github.com/pgen0x/azimuth/commit/bce64918b751c866def7a0f2d6241757380ed861))
* classify split rent service fees with balance proof ([#127](https://github.com/pgen0x/azimuth/issues/127)) ([9498d3a](https://github.com/pgen0x/azimuth/commit/9498d3aefbc5451db91a602c8db233f0bf8fc57f))
* compare entry yield using scanner timeframe ([#135](https://github.com/pgen0x/azimuth/issues/135)) ([8e6c71d](https://github.com/pgen0x/azimuth/commit/8e6c71dc918e0c821746b7279809b6cc964b878a))
* distinguish expired swaps in execution evaluation ([#162](https://github.com/pgen0x/azimuth/issues/162)) ([6187d28](https://github.com/pgen0x/azimuth/commit/6187d2817a83a6b1102fc1f365bb717dd99b634e))
* durable exits and independent SOL settlement retries ([6726831](https://github.com/pgen0x/azimuth/commit/67268311ec515e16ae555859552db327d8f7fb29))
* estimate swap compute limit instead of reserving maximum ([#134](https://github.com/pgen0x/azimuth/issues/134)) ([9dc647a](https://github.com/pgen0x/azimuth/commit/9dc647a0844255851951cbd5c32265444fd4c5ba))
* expose root settlement cash in evaluation reports ([#132](https://github.com/pgen0x/azimuth/issues/132)) ([e3ec4d4](https://github.com/pgen0x/azimuth/commit/e3ec4d433e18e34e123dd97e79af3d457754cddf))
* gate residual recovery on simulated net SOL proceeds ([#120](https://github.com/pgen0x/azimuth/issues/120)) ([96691db](https://github.com/pgen0x/azimuth/commit/96691dba5de819bd5636c1be97029b5f2bdb6e72))
* **hermes:** persist delivery identity and separate session lifecycle from execution ([#154](https://github.com/pgen0x/azimuth/issues/154)) ([6c5b053](https://github.com/pgen0x/azimuth/commit/6c5b0536a2ad519147940a4cb23e63134aca3064))
* isolate economic settlement retries from risk monitoring ([#124](https://github.com/pgen0x/azimuth/issues/124)) ([873513c](https://github.com/pgen0x/azimuth/commit/873513c4c623a65c9d79a5cc140e4348121e1d95))
* label close-time LP marks as estimates ([cc30f53](https://github.com/pgen0x/azimuth/commit/cc30f530bc151a6ded2704ab9909464c1483dd4c))
* label close-time LP marks as estimates ([e04d90d](https://github.com/pgen0x/azimuth/commit/e04d90de1cc8241159adcfd5cfb3e94f3322337d))
* **learning:** exclude unreconciled and invalid LP outcomes ([#153](https://github.com/pgen0x/azimuth/issues/153)) ([f2925ab](https://github.com/pgen0x/azimuth/commit/f2925ab4d15bdb0b27c46805b9d98b18ae84a22b))
* make costly undated Wallet API estimates opt-in ([bea9eaa](https://github.com/pgen0x/azimuth/commit/bea9eaa22b0662a18dea95240fa29ca91f1f9c7b))
* **monitor:** keep daily reporting off the risk-check loop ([#149](https://github.com/pgen0x/azimuth/issues/149)) ([bfdead5](https://github.com/pgen0x/azimuth/commit/bfdead59f6e3803e423d12e7120759e944682ce6))
* normalize SDK account keys in maintenance classifier ([#129](https://github.com/pgen0x/azimuth/issues/129)) ([6bffbb0](https://github.com/pgen0x/azimuth/commit/6bffbb0352df28da8711fd8e6231a2afc9da63de))
* persist exits and retry unsettled tokens without stalling risk checks ([b817872](https://github.com/pgen0x/azimuth/commit/b817872b6d76248b0dc622afe31e51066bb0c32e))
* prefilter mint and pool cooldowns before AI dispatch ([4e6e2a1](https://github.com/pgen0x/azimuth/commit/4e6e2a17de768651aacb981aab334097b79efbbe))
* prefilter mint and pool cooldowns before AI dispatch ([6c8a308](https://github.com/pgen0x/azimuth/commit/6c8a30814896e5018c42c5294f5c83cc423efaaf))
* preserve exact decimal amounts in token swaps ([#121](https://github.com/pgen0x/azimuth/issues/121)) ([23f7be1](https://github.com/pgen0x/azimuth/commit/23f7be169c600764c6e814cd034f7782042cd1a2))
* preserve native SOL reserve after rent and fees ([#131](https://github.com/pgen0x/azimuth/issues/131)) ([09ebcee](https://github.com/pgen0x/azimuth/commit/09ebcee895ae1e5b973277efc1839ac9a6708e85))
* reclaim empty immutable-owner Token-2022 rent ([#130](https://github.com/pgen0x/azimuth/issues/130)) ([ec99814](https://github.com/pgen0x/azimuth/commit/ec99814c6b235436614d6b0ded89c8513c825e58))
* reconcile memo-bearing native transfers without broad cache refresh ([fd0e2c3](https://github.com/pgen0x/azimuth/commit/fd0e2c394280afdb672f58001a0c80f9dbe90f14))
* reconcile proven Pump cashback and rent maintenance ([#128](https://github.com/pgen0x/azimuth/issues/128)) ([a9128e6](https://github.com/pgen0x/azimuth/commit/a9128e607ce1af86454cd3686f4ba632e9673f30))
* recover live positions when Redis tracking is empty ([#126](https://github.com/pgen0x/azimuth/issues/126)) ([d8428b5](https://github.com/pgen0x/azimuth/commit/d8428b5fdb664e735d19ed29175b8211a620dfab))
* reduce accounting RPC reads and disable automatic Wallet API spend ([5fa9d23](https://github.com/pgen0x/azimuth/commit/5fa9d237d3fad2076d216cb402fb78bb4194b79b))
* report pooled settlement cash without inventing root allocation ([7333bcc](https://github.com/pgen0x/azimuth/commit/7333bcccdda718e3277ac8d6dd390cb9416f62b5))
* report pooled settlement cash without inventing root allocation ([5eb2e05](https://github.com/pgen0x/azimuth/commit/5eb2e055d4f5b2189babd7cb7f943d16aec48ad8))
* **report:** separate reconciled LP outcomes from matched wallet cash ([#148](https://github.com/pgen0x/azimuth/issues/148)) ([eab5cd3](https://github.com/pgen0x/azimuth/commit/eab5cd3fb6da7aaeadde88c2841e7540f0816964))
* require RPC absence before pruning position tracking ([#125](https://github.com/pgen0x/azimuth/issues/125)) ([89520f0](https://github.com/pgen0x/azimuth/commit/89520f004ba29c6a377a96d2765e111f1046c163))
* retry signed deployment bytes across RPC endpoints ([#136](https://github.com/pgen0x/azimuth/issues/136)) ([78e14d2](https://github.com/pgen0x/azimuth/commit/78e14d279d1ae9e0bd75cbc450d6290668904bab))
* retry signed DLMM closes across RPC endpoints ([#122](https://github.com/pgen0x/azimuth/issues/122)) ([c8b93f0](https://github.com/pgen0x/azimuth/commit/c8b93f0f418c080774b66fca5f2cdfb7e63dda44))
* reuse finalized transaction evidence across accounting collectors ([103c763](https://github.com/pgen0x/azimuth/commit/103c763dab6c9c1caa927f2f82f6951ccbc90677))
* **scanner:** resume capacity checks after verified settlement ([#147](https://github.com/pgen0x/azimuth/issues/147)) ([6256526](https://github.com/pgen0x/azimuth/commit/6256526a383cc9ac9fc326edce5a07ffd61162ff))
* **scanner:** use reconciled cash for pool history ([#152](https://github.com/pgen0x/azimuth/issues/152)) ([8772d07](https://github.com/pgen0x/azimuth/commit/8772d079acd66a1d8fe02f6a1557802734ac12a3))
* **shadow:** bound bin sampling to mode horizons ([#146](https://github.com/pgen0x/azimuth/issues/146)) ([c798d04](https://github.com/pgen0x/azimuth/commit/c798d04c7851fc29308ee76f190ea048f531f8e7))
* show native cash separately in evaluation reports ([#119](https://github.com/pgen0x/azimuth/issues/119)) ([92359a6](https://github.com/pgen0x/azimuth/commit/92359a6a8f87b3b32e8166f0774f94e2beb2901c))
* **solana:** accept valid AI health tool arguments and classify failures ([138453b](https://github.com/pgen0x/azimuth/commit/138453b59915dde04457a71a929d81fa3b911df9))
* **solana:** avoid provider rejection of AI probe tool choice ([240b280](https://github.com/pgen0x/azimuth/commit/240b280910fb4fbad56db6c654af78eb4fa817ba))
* **solana:** bound signal dedup after wallet capacity skips ([#138](https://github.com/pgen0x/azimuth/issues/138)) ([38e173c](https://github.com/pgen0x/azimuth/commit/38e173c3bde9e57482da04351482b3c08a94f8b3))
* **solana:** classify fully reconciled rent maintenance ([69bad8c](https://github.com/pgen0x/azimuth/commit/69bad8c3c9de62dac49605029ad4ad503711c339))
* **solana:** classify passive token inflows without counting gifts as profit ([f2403d5](https://github.com/pgen0x/azimuth/commit/f2403d5d4bf7198eebbc6838b752880be050cca1))
* **solana:** enforce turnover stale ticket age exit ([#141](https://github.com/pgen0x/azimuth/issues/141)) ([02fa837](https://github.com/pgen0x/azimuth/commit/02fa8373d6239784b1b9ae9fccba45595752c78d))
* **solana:** exclude unvalued token gifts from evaluation profit ([233e374](https://github.com/pgen0x/azimuth/commit/233e374f7c26d5c7df7a0f2fe4bf8dab7622cd1e))
* **solana:** guard evaluation profit against unvalued token gifts ([85be9f0](https://github.com/pgen0x/azimuth/commit/85be9f09fcbbf893d449e940be0d688718a5c6a2))
* **solana:** isolate passive token inflows from bot accounting ([f284846](https://github.com/pgen0x/azimuth/commit/f28484630f043ff18c0f833b818cbf9be4b32209))
* **solana:** keep defensive exits out of profitable churn ([#137](https://github.com/pgen0x/azimuth/issues/137)) ([7d13f16](https://github.com/pgen0x/azimuth/commit/7d13f16cf10606cc71fae0bac39c8342d7f436b1))
* **solana:** pace NAV quotes and stop on rate limits ([0129715](https://github.com/pgen0x/azimuth/commit/01297153b6babac2c5310c0f4b46c1a2b0ffa1c6))
* **solana:** pace NAV quotes and stop on rate limits ([14ea4af](https://github.com/pgen0x/azimuth/commit/14ea4af75b36ca93fd39094e07ed837f9806f6e3))
* **solana:** pause AI dispatch after measured capacity refusals ([#139](https://github.com/pgen0x/azimuth/issues/139)) ([24c22e5](https://github.com/pgen0x/azimuth/commit/24c22e55a67c82705180ec8490b15959202de7b5))
* **solana:** prefer Hermes AI with deterministic availability fallback ([485809c](https://github.com/pgen0x/azimuth/commit/485809caedaba9bf8b453c552fb8b8a99d3ef125))
* **solana:** prefer Hermes AI with pre-dispatch deterministic fallback ([9abdf82](https://github.com/pgen0x/azimuth/commit/9abdf820f209ab8b3e1ecdf698f4f5eaff306f23))
* **solana:** preserve complete candidate batches in Hermes prompts ([#155](https://github.com/pgen0x/azimuth/issues/155)) ([4a14864](https://github.com/pgen0x/azimuth/commit/4a1486477482cfec95cca0bb73b5adfb1c5e680d))
* **solana:** prevent empty-position cleanup from withdrawing funded liquidity ([#156](https://github.com/pgen0x/azimuth/issues/156)) ([62eac3a](https://github.com/pgen0x/azimuth/commit/62eac3aabbd97d88833d92f9dc57fa5e84105c91))
* **solana:** read finalized version 1 accounting transactions ([#157](https://github.com/pgen0x/azimuth/issues/157)) ([a7d23ea](https://github.com/pgen0x/azimuth/commit/a7d23ea2f58c71a35c2ba316a6987716c27b8435))
* **solana:** read Meteora position maps and nested fees ([d483af2](https://github.com/pgen0x/azimuth/commit/d483af25a594d7e3c5e61455386842ca233d232a))
* **solana:** read Meteora position maps in every executor path ([732b598](https://github.com/pgen0x/azimuth/commit/732b5986d376ec6338d37603520ed4eadca06aa9))
* **solana:** reconcile evaluation blockers and replay actual root decisions ([21a0317](https://github.com/pgen0x/azimuth/commit/21a0317d9ed351368dec2153486e9fc3c3d6755d))
* **solana:** reconcile evaluation blockers and root decision evidence ([c45d035](https://github.com/pgen0x/azimuth/commit/c45d035fe513ea6c39af30d06f79465918ee08e8))
* **solana:** reconcile proven cleanup settlements with closed roots ([5dfec86](https://github.com/pgen0x/azimuth/commit/5dfec86057c59ec18ea30f6ce9f7e52e4b0cdbfb))
* **solana:** reconcile proven cleanup swaps with closed roots ([a7a8541](https://github.com/pgen0x/azimuth/commit/a7a85419612215e852a0ad7431db42691b9dd94d))
* **solana:** reconcile proven external rent maintenance ([8a6c402](https://github.com/pgen0x/azimuth/commit/8a6c4022ce2365c1af2d82ccf3b4ec0b381c9290))
* **solana:** stop false AI availability failures ([d130903](https://github.com/pgen0x/azimuth/commit/d130903f0dcbec0d8f374aeed5d94aca90d05336))
* **solana:** stop RPC failover on rent safety refusal ([#151](https://github.com/pgen0x/azimuth/issues/151)) ([87d4f31](https://github.com/pgen0x/azimuth/commit/87d4f314289591a2e9a3ce53631034ea2e1baadc))
* **solana:** tighten first exit settlement slippage ([#159](https://github.com/pgen0x/azimuth/issues/159)) ([640816e](https://github.com/pgen0x/azimuth/commit/640816e6502defc7511a7026f06160cce748d298))
* **solana:** use compatible required tool choice for AI probe ([3715450](https://github.com/pgen0x/azimuth/commit/3715450fefdada9937050b74513ca392eea9f6bc))
* use configured cleanup floor for post-close residual swaps ([0df26f2](https://github.com/pgen0x/azimuth/commit/0df26f2481524d49b3f10ca35e95cb940d5b8c03))

## [2.8.0](https://github.com/pgen0x/azimuth/compare/v2.7.6...v2.8.0) (2026-09-25)


### Features

* **solana:** add wallet NAV, root cost guard and forward shadow evaluation ([273831b](https://github.com/pgen0x/azimuth/commit/273831b179942de0d39d0752700d72904998b0de))
* **solana:** complete accounting, root cost guard and shadow evaluation paths ([f5cf4bc](https://github.com/pgen0x/azimuth/commit/f5cf4bcd277d2dbb654c4947e8a8578d9ff2d410))
* **solana:** record settlement cash flows and root-chain evidence ([f0f7860](https://github.com/pgen0x/azimuth/commit/f0f786010aca1b17cec458297b42e0bf199d1c36))
* **solana:** record transaction cash flows and root-chain evidence ([e0eb963](https://github.com/pgen0x/azimuth/commit/e0eb963fe117f37402cd5ee89daef4bef3f35c3e))


### Bug Fixes

* **solana:** address 24h audit execution gaps ([b3e2267](https://github.com/pgen0x/azimuth/commit/b3e2267c551c380494e8acd754ac8fe90df13629))
* **solana:** address 24h audit execution gaps ([f8ae238](https://github.com/pgen0x/azimuth/commit/f8ae238e3b997c0a1c58678514eadc86a018abc3))
* **solana:** keep liquidation available during accounting storage failure ([951986c](https://github.com/pgen0x/azimuth/commit/951986cd370e1aa9fe4e0bdac9d1a8ab6b663cb3))
* **solana:** link pre-entry token purchases to the deployed root ([b99129e](https://github.com/pgen0x/azimuth/commit/b99129e16186d9f592a091e1fcbda5463242318c))
* **solana:** preserve explicit roots across monitor reentries ([2ae3c6e](https://github.com/pgen0x/azimuth/commit/2ae3c6e348633b7323f59b12e496ef2f381a4c2d))
* **solana:** reconcile uncertain sends and require active depth ([8a60295](https://github.com/pgen0x/azimuth/commit/8a602955c9d490fe2908c7441cef10b818d55661))
* **solana:** refresh cached facts when attribution schema changes ([80f97c6](https://github.com/pgen0x/azimuth/commit/80f97c67a46db452dfa59be91525731c1b151a63))
* **solana:** require finalized account deletion in root settlement proof ([faa6366](https://github.com/pgen0x/azimuth/commit/faa6366917cecd6b86c6fe5a5f2bdd56b465ab61))
* **solana:** rotate bin sampling fairly and reject undated LP marks ([fe763ce](https://github.com/pgen0x/azimuth/commit/fe763ce1a5876c9c66ff55898aad23a3e0a3f8cd))

## [2.7.6](https://github.com/pgen0x/azimuth/compare/v2.7.5...v2.7.6) (2026-09-21)


### Bug Fixes

* **solana:** make entry routing deterministic ([#91](https://github.com/pgen0x/azimuth/issues/91)) ([05451c8](https://github.com/pgen0x/azimuth/commit/05451c83b5265d4870eb20409a420eaa20ff4007))

## [2.7.5](https://github.com/pgen0x/azimuth/compare/v2.7.4...v2.7.5) (2026-09-21)


### Bug Fixes

* **solana:** tighten LP capital controls ([#88](https://github.com/pgen0x/azimuth/issues/88)) ([ff2694e](https://github.com/pgen0x/azimuth/commit/ff2694e44f621bb926231b0484707ae8781d26dc))

## [2.7.4](https://github.com/pgen0x/azimuth/compare/v2.7.3...v2.7.4) (2026-09-15)


### Bug Fixes

* **solana:** restore Redis-authenticated scanning and safety guards ([#86](https://github.com/pgen0x/azimuth/issues/86)) ([7d04e6f](https://github.com/pgen0x/azimuth/commit/7d04e6fcf5d1124af8dbc066f33086192d32d4bc))

## [2.7.3](https://github.com/pgen0x/azimuth/compare/v2.7.2...v2.7.3) (2026-08-24)


### Bug Fixes

* **solana:** cap dump-swap impact, tighten turnover OOR fuse, risk-scale ticket size ([#84](https://github.com/pgen0x/azimuth/issues/84)) ([c12005d](https://github.com/pgen0x/azimuth/commit/c12005dae186a5cefa30127fd2fd70e1a46f8fc8))

## [2.7.2](https://github.com/pgen0x/azimuth/compare/v2.7.1...v2.7.2) (2026-08-24)


### Bug Fixes

* **indicators:** fetch 1m candles at entry, add Birdeye fallback for GT 429 ([#80](https://github.com/pgen0x/azimuth/issues/80)) ([4521b92](https://github.com/pgen0x/azimuth/commit/4521b9237fcfab4960018a0e108d2b2a1727bc55))

## [2.7.1](https://github.com/pgen0x/azimuth/compare/v2.7.0...v2.7.1) (2026-08-22)


### Bug Fixes

* **scanner:** stop reject-tally reasonKey from erasing the gate name ([6b5efef](https://github.com/pgen0x/azimuth/commit/6b5efef32d173e5157676377b6e976271cc20077))
* **solana:** close turnover stale-ticket hole, kill phantom losses, fix reject tally ([ee40cfd](https://github.com/pgen0x/azimuth/commit/ee40cfd398c4a6de35254df3194f5372074622ed))
* **solana:** stop booking losses that never happened, and cut the drawdown tail earlier ([2566622](https://github.com/pgen0x/azimuth/commit/256662249368d7d7d183de425efc78c0a6750818))
* **solana:** widen suspect-read guard to catch shallower indexing-lag misreads ([06bc9d1](https://github.com/pgen0x/azimuth/commit/06bc9d1b18547130028ca426ca39de5d5d0d1e9b))

## [2.7.0](https://github.com/pgen0x/azimuth/compare/v2.6.3...v2.7.0) (2026-08-17)


### Features

* **solana:** close the turnover stale-ticket hole, and journal what it needs ([26bde90](https://github.com/pgen0x/azimuth/commit/26bde90becadd136a5ddf8bea490aade3b062b1b))
* **solana:** close the turnover stale-ticket hole, and journal what it needs ([7151c73](https://github.com/pgen0x/azimuth/commit/7151c7378976f9e7ebf72334d22619856a487801))


### Bug Fixes

* **robinhood:** bound the repeat-fill cooldown at 24h, not 72h ([3429ea5](https://github.com/pgen0x/azimuth/commit/3429ea51932eeefe6f46bb5c9a5474b10573fd31))
* **robinhood:** bound the repeat-fill cooldown at 24h, not 72h ([a60ecc7](https://github.com/pgen0x/azimuth/commit/a60ecc79f8213bcacb987b023cb80bd38b2fa872))
* **robinhood:** retry an empty gateway leaderboard, and log the funnel ([eac6244](https://github.com/pgen0x/azimuth/commit/eac62449327a0f18e03aab8da36cb299ce0ec8a0))
* **robinhood:** retry an empty gateway leaderboard, and log the funnel ([145aa92](https://github.com/pgen0x/azimuth/commit/145aa92e04708a97007db7b20d2ae6b3bebc43e9))

## [2.6.3](https://github.com/pgen0x/azimuth/compare/v2.6.2...v2.6.3) (2026-08-16)


### Bug Fixes

* **install:** skip non-files when copying the cron pre-run scripts ([1b3bcc9](https://github.com/pgen0x/azimuth/commit/1b3bcc9a139b6b78dec7271ece8f5ecdbc6b024d))

## [2.6.2](https://github.com/pgen0x/azimuth/compare/v2.6.1...v2.6.2) (2026-08-16)


### Bug Fixes

* **solana:** stop a 5m price candle from writing a 30-day ban ([88d5408](https://github.com/pgen0x/azimuth/commit/88d540899f00227c2cebe3b9bcb468306a06f23a))
* **solana:** stop a 5m price candle from writing a 30-day ban ([752b37a](https://github.com/pgen0x/azimuth/commit/752b37ac06071b5a1b1ff6fb465998da8d8bb961))

## [2.6.1](https://github.com/pgen0x/azimuth/compare/v2.6.0...v2.6.1) (2026-08-14)


### Bug Fixes

* **momentum:** read our own pool's price, not a dead pool's ([ad4ad2b](https://github.com/pgen0x/azimuth/commit/ad4ad2b695a59fd339f0cd5f549c1ddc77f2ec77))
* **momentum:** read our own pool's price, not a dead pool's ([a424001](https://github.com/pgen0x/azimuth/commit/a4240017fb1e192c05cf27d4fdc6277c6eb9aba9))

## [2.6.0](https://github.com/pgen0x/azimuth/compare/v2.5.1...v2.6.0) (2026-08-14)


### Features

* **robinhood:** screen the tail of the volume ranking, and stop muting a clean close ([671f317](https://github.com/pgen0x/azimuth/commit/671f3177931e2beb41519931ae1abe867c3b5b8d))
* **robinhood:** screen the tail of the volume ranking, not its head ([d309ac7](https://github.com/pgen0x/azimuth/commit/d309ac7c2d7138240532dc0c7f6298118e1d3d35))


### Bug Fixes

* **solana:** stop paying for depth the market never reaches ([49e2af3](https://github.com/pgen0x/azimuth/commit/49e2af33db0b4d19d1e0471851cab0de8a6c1967))
* **solana:** stop paying for depth the market never reaches ([5d17178](https://github.com/pgen0x/azimuth/commit/5d17178c3c8d16c2b506749871db877b6c065eef))
* **turnover:** stop muting a clean close for two hours ([5f805f4](https://github.com/pgen0x/azimuth/commit/5f805f4fcde77d82f190f5f347eca67c38cec861))
* **turnover:** widen the ranked feed, and stop muting a clean close ([9c0f34a](https://github.com/pgen0x/azimuth/commit/9c0f34a4c5907542dcb3d2ae77176d7ffe7c802c))

## [2.5.1](https://github.com/pgen0x/azimuth/compare/v2.5.0...v2.5.1) (2026-08-13)


### Bug Fixes

* **turnover:** judge a four-minute position on a four-minute horizon ([1bb6b0f](https://github.com/pgen0x/azimuth/commit/1bb6b0fa71ee856b8c842c8e69edbbe39dc77a63))
* **turnover:** judge a four-minute position on a four-minute horizon ([3561534](https://github.com/pgen0x/azimuth/commit/3561534614e37db72f28cf2c45a7779a30f5b291))

## [2.5.0](https://github.com/pgen0x/azimuth/compare/v2.4.0...v2.5.0) (2026-08-13)


### Features

* **exit:** give the LLM one power over exits — deferring a close ([708452a](https://github.com/pgen0x/azimuth/commit/708452aa6499c3f5bc146badd0ea08353b0e3304))
* give the LLM a subtractive role in exits, and stop paying for holds nothing earns ([bbd6704](https://github.com/pgen0x/azimuth/commit/bbd6704ad61e823114ac219c2d70f208288025d8))
* **monitor:** let an AI hold be rehearsed before it is placed ([43ff905](https://github.com/pgen0x/azimuth/commit/43ff905060f308b4aa332f8294e5b3805be89dc6))
* **proposal:** a daily job that proposes thresholds and cannot apply them ([edfed72](https://github.com/pgen0x/azimuth/commit/edfed7210e007ff73252ea69d50a1c5a20a68fdc))
* **robinhood:** settle a filled rung in quote, and stop trusting a mark ([a9751a7](https://github.com/pgen0x/azimuth/commit/a9751a78cf54dd30583a3c585fcaf1b0be371e6d))


### Bug Fixes

* **exit-review:** move the low-yield band back in front of the rule it guards ([6edd77b](https://github.com/pgen0x/azimuth/commit/6edd77b7030595af2e1b54128e8099e79b515ca1))
* **pulse:** stop giving a five-minute signal an hour to prove itself ([9d7d80d](https://github.com/pgen0x/azimuth/commit/9d7d80de3da965e931a78c49bd3e63a505d395b7))
* **weights:** stop the learner ratcheting into its own clamps ([3a447d2](https://github.com/pgen0x/azimuth/commit/3a447d28ef7f8e2df3122657ec2856e3d34dfd75))

## [2.4.0](https://github.com/pgen0x/azimuth/compare/v2.3.0...v2.4.0) (2026-08-12)


### Features

* **robinhood:** carry launches forward for a first-day WETH ladder ([f9bc7c9](https://github.com/pgen0x/azimuth/commit/f9bc7c9f530bd19c35b1c6c7ac7a1e87db2cf36b))
* **robinhood:** carry the pulse registry across restarts ([37afe46](https://github.com/pgen0x/azimuth/commit/37afe46ce49fa99287cc0b05dc5e5317ac57413b))
* **robinhood:** rank the book by churn, and stop nursing a filled rung ([8fe0c03](https://github.com/pgen0x/azimuth/commit/8fe0c03b4834f9870126587c8fe1932b1f84d15d))
* **robinhood:** re-list a filled rung as an ask instead of dumping it ([6e68b77](https://github.com/pgen0x/azimuth/commit/6e68b775160972a9db7a022660555ae20eb213fe))
* **robinhood:** replace the ladders with a churn loop that re-centers ([c3ad3dc](https://github.com/pgen0x/azimuth/commit/c3ad3dcafcc52bbf6479e48d3d233a10c8839c41))


### Bug Fixes

* **robinhood:** a honeypot verdict must outlive the cycle that saw it ([1672201](https://github.com/pgen0x/azimuth/commit/16722012cbc3c6f7b51e7cde2b1190050c1c6e70))
* **robinhood:** a one-sided close pays back in quote, not in swap proceeds ([d7f393e](https://github.com/pgen0x/azimuth/commit/d7f393ed0594ec633ea48d20a952fd57b4457c55))
* **robinhood:** a WETH pin means ether, not the wrapper ([c8ee1a8](https://github.com/pgen0x/azimuth/commit/c8ee1a893173beb157d5caf6241143ce5d697d8f))
* **robinhood:** give up on a close that can never land ([829087b](https://github.com/pgen0x/azimuth/commit/829087b021851694d8b0cd259b344008dc78f1bc))
* **robinhood:** make the ladder answer for the walls nobody trades ([55b8526](https://github.com/pgen0x/azimuth/commit/55b8526f42760720b76b9d7681a79def040353c2))
* **robinhood:** measure a rung's drift from its pin, not from its edge ([a22c6e6](https://github.com/pgen0x/azimuth/commit/a22c6e68809f2bff7138f61e0f6cc2d7f0542e3c))
* **robinhood:** recalibrate turnover gates against this venue's own book ([f67c53d](https://github.com/pgen0x/azimuth/commit/f67c53dfea471db705c89d4dfa5343ee82a5e626))
* **robinhood:** replace the ladders with a re-centering turnover rung, and make its closes honest ([4b52d80](https://github.com/pgen0x/azimuth/commit/4b52d8005b94fa34707c9ccfa336bfd5fea5a7c1))
* **robinhood:** rescue the quote side when a honeypot holds collect hostage ([29f8763](https://github.com/pgen0x/azimuth/commit/29f87634fb543466928b44f1cfe7d9a571907d33))
* **robinhood:** stop a broke wallet from silencing its own candidates ([f20bde6](https://github.com/pgen0x/azimuth/commit/f20bde69bb75cca7b71ba0dd6f3f160bd3d0f10e))
* **robinhood:** stop the pulse sweep from starving its own feed ([09f7d54](https://github.com/pgen0x/azimuth/commit/09f7d54ea54f979adab6955b25e4da8402ac8ff4))
* **robinhood:** turnover rests one rung where the fees were ([578cffe](https://github.com/pgen0x/azimuth/commit/578cffe7411b9744dd3f0d3baded077e2dfbf895))
* **solana:** let the blocklists and the loss floor both expire ([c47b4f6](https://github.com/pgen0x/azimuth/commit/c47b4f67316625bdf00ff3d26ea8962b4f09f217))
* **solana:** let the rug blacklist and pool memory forget ([1ce32d4](https://github.com/pgen0x/azimuth/commit/1ce32d4f531064b53955bb0c0b912b0f71189927))
* **turnover:** stop cutting the SOL side of the book two minutes early ([3eaecf6](https://github.com/pgen0x/azimuth/commit/3eaecf6bb1468f23e266769299a5be2271cae2c5))


### Performance Improvements

* **robinhood:** tick the exit loop at 20s, not ~84s ([e5575f4](https://github.com/pgen0x/azimuth/commit/e5575f4b4394a026c26b03dabfdf1ab41fbac07c))

## [2.3.0](https://github.com/pgen0x/azimuth/compare/v2.2.0...v2.3.0) (2026-08-06)


### Features

* **robinhood:** add gas-topup — buy ETH gas with USDG ([a91be07](https://github.com/pgen0x/azimuth/commit/a91be073eb4a7a813dc538a450e8feb350e869d9))
* **robinhood:** add the ladder idle exit and widen the USDG rungs ([ad6d0a7](https://github.com/pgen0x/azimuth/commit/ad6d0a7bff38d9a444825f25e5a5e9918e87fbc8))
* **robinhood:** add the one-sided ladder modes for WETH and USDG ([66db788](https://github.com/pgen0x/azimuth/commit/66db78868b9f2a3b1b370005688c4fc3855c2b71))
* **robinhood:** cap ladders per underlying, throttle GeckoTerminal ([2026ade](https://github.com/pgen0x/azimuth/commit/2026adec2b21b22b64d40781fb6f75ffe385cfa4))
* **robinhood:** give the stock ladder its own dedup window ([7ba0fa8](https://github.com/pgen0x/azimuth/commit/7ba0fa8d42e22f645f0f27ba2b89873b25ca3739))
* **robinhood:** measure ladder fees on-chain in the state read ([6c5d507](https://github.com/pgen0x/azimuth/commit/6c5d507b61bd13df3b87ffe7424c90c4a986337c))
* **robinhood:** mint the ladder on Uniswap v4 ([14337dd](https://github.com/pgen0x/azimuth/commit/14337dd6618ef0e8ae10a29fe04d6479bead0485))
* **robinhood:** one-sided WETH + USDG ladder modes, v3 and v4 ([1dc93f5](https://github.com/pgen0x/azimuth/commit/1dc93f540c2ff7977cd00e6749ec7e8ab78230a0))
* **robinhood:** read real ladder fees from the Krystal position API ([5698192](https://github.com/pgen0x/azimuth/commit/5698192396ebe17b034d9eb569b4c471f2bcf409))
* **robinhood:** union the ladder feed with a cached trending page ([6756719](https://github.com/pgen0x/azimuth/commit/675671976b26b6b7d4390c69b89dead06e0a77f4))


### Bug Fixes

* **robinhood:** drop the stock-ladder TVL floor to $20k ([a864096](https://github.com/pgen0x/azimuth/commit/a864096efe1cd306079b18e8e2cb8e02cad67bee))
* **robinhood:** judge ladder idleness per wall, not per rung ([7d1fc45](https://github.com/pgen0x/azimuth/commit/7d1fc450d327f3b6b9cbb50c7c49c07fad1b8905))
* **robinhood:** live within GeckoTerminal's real request budget ([1b5e555](https://github.com/pgen0x/azimuth/commit/1b5e5558fcb562dcab826d8a59560b65e1be3789))
* **robinhood:** reject quote/quote pools and stop closing ladder rungs on error payloads ([2080a6b](https://github.com/pgen0x/azimuth/commit/2080a6bbe353ffe5b0399bbf1640ad19c07b70b0))
* **robinhood:** release a fee-dead ladder on age, not a rolling window ([f2fe794](https://github.com/pgen0x/azimuth/commit/f2fe794851e45446b4eec9d5da73be3ca27b25be))

## [2.2.0](https://github.com/pgen0x/azimuth/compare/v2.1.0...v2.2.0) (2026-08-01)


### Features

* **pulse:** screen 30m volatility and drop the momentum gate ([404e3d5](https://github.com/pgen0x/azimuth/commit/404e3d57ea0a026e5193fbe6edfb66e27dbd2040))
* **pulse:** screen 30m volatility and drop the momentum gate ([b3b9b72](https://github.com/pgen0x/azimuth/commit/b3b9b72f215b29b2b09b8961f54ba1d65d977160))
* **pulse:** screen the 5m trending window alongside turnover ([cd3b14f](https://github.com/pgen0x/azimuth/commit/cd3b14f78828f94a435f583b554c2c9dafd56b70))

## [2.1.0](https://github.com/pgen0x/azimuth/compare/v2.0.0...v2.1.0) (2026-07-30)


### Features

* **turnover:** fee-capture mode, Azimuth rename, chain-verified closes ([ac3f2ba](https://github.com/pgen0x/azimuth/commit/ac3f2ba44b0e7d503e5f99edf763d9137b6a6272))


### Bug Fixes

* **deploy:** journal the post-conviction gate that killed a batch ([05a787c](https://github.com/pgen0x/azimuth/commit/05a787cd107911d483482b756d52a9a837b97255))
* **monitor:** verify closes against the chain before believing a failure ([635c2a2](https://github.com/pgen0x/azimuth/commit/635c2a275619e7b1c1e57be8b30416bc2773cb90))
* **turnover:** admit unverified tokens, unstick momentum rejects ([c033f9b](https://github.com/pgen0x/azimuth/commit/c033f9b32dc111602405c171dcd0c3d3ac29d446))

## [2.0.0](https://github.com/pgen0x/azimuth/compare/v1.15.0...v2.0.0) (2026-07-28)


### ⚠ BREAKING CHANGES

* the binary, the Go module path and all three systemd unit names changed. Re-run install.sh, then remove the old units: `systemctl --user disable --now meteora-dlmm-trading-bot sol-dlmm-monitor`.

### Features

* **systemd:** ship all three user units in install.sh ([a99683e](https://github.com/pgen0x/azimuth/commit/a99683eaa7655919d3b70423caf0a6250e736153))
* **turnover:** realign screen bands, arm a tight trailing TP, drop half-size ([127e799](https://github.com/pgen0x/azimuth/commit/127e7996ebf69e2e8ea04fdc85699eb953e497d8))


### Code Refactoring

* rename project to Azimuth ([cc591cd](https://github.com/pgen0x/azimuth/commit/cc591cdb5cba221baecc5742e4e98237da03f882))

## [1.15.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.14.1...v1.15.0) (2026-07-27)


### Features

* turnover fee-capture with sol_bidask entry + churn reseed ([209016b](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/209016b066c7ddfd260ef50fa168f276e30ed6f0))
* turnover fee-capture with sol_bidask entry + churn reseed ([6977ae0](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/6977ae049cfeeff3601272c6425f0255163f72f9))

## [1.14.1](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.14.0...v1.14.1) (2026-07-22)


### Bug Fixes

* give release-please a parseable commit for the sol_bidask merge (PR [#39](https://github.com/pgen0x/meteora-dlmm-trading-bot/issues/39)) ([bc937d2](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/bc937d28cafbe30478a8847706e5e905f90edd18))

## [1.14.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.13.0...v1.14.0) (2026-07-21)


### Features

* sol_bidask default strategy + asymmetric exit overhaul ([bb9ed72](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/bb9ed7273e09a959b9362bc3744d3fe68d29bddf))


### Bug Fixes

* GUARD hard floor matches the new -25% SL and cites the rug gate ([75a5aea](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/75a5aea40d1df73ff35333a3f44e1acf820773db))

## [1.13.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.12.0...v1.13.0) (2026-07-17)


### Features

* auto-unwrap WETH to keep a native-ETH gas reserve ([255d20d](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/255d20d3cc7516317d9298ecc07dc07f80b564a7))
* automatic direct-deploy dispatch for Robinhood Chain (ROBINHOOD_DEPLOY_ENABLED) ([f1504bf](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/f1504bfba4bb6c61a6e7def82776041ca9110bf1))
* copycat guard for Robinhood venue — intra-batch same-symbol collision ([e0ce2f0](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/e0ce2f01f46ca86fe6df55e742b9c41b92ebc862))
* dynamic position sizing for the Robinhood venue (port of compute_deploy_amount) ([11ab447](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/11ab447c8952135545518894eb3dd95481f279f3))
* monitor walks both executors so v4 positions get exits ([14a8af7](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/14a8af70dbb18e6db0b1dd93ac879f29a4a321bf))
* pad gas estimates 30% and label v3 positions by pair ([bfde144](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/bfde144eb18cc3faddd79da4b2706b49cebd54be))
* port external screening + exit upgrades ([8aaa241](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/8aaa241e155a8af42f680ba983de01bf9e46c3d9))
* rh-mature mode — established fee-printers via Uniswap's own gateway ([2853812](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/2853812c60223afc8f4653a51f29d04b2389204e))
* Robinhood Chain venue — GeckoTerminal discovery, screening, GMGN/Blockscout safety gates (observe-only) ([fe9f8f9](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/fe9f8f98ea105b7b26371265940550efe806dec7))
* screening recalibration from the 14d close journal ([3208589](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/3208589629afc93317682d5b5418acc6e5be3c00))
* supertrend/RSI timing gates for the Robinhood venue ([f305db9](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/f305db97e5648805b8fd67108b494bb307634ba1))
* uni_executor.js — Uniswap v3 executor for Robinhood Chain (viem) ([21372c2](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/21372c29b1863b6d68a700c5175429760af414b1))
* uni_monitor.py --report-only + rh_dlmm_position_monitor Hermes cron ([bbcd7e8](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/bbcd7e8b7ab03747ab93a1b26efd3d554a8d3f21))
* uni_monitor.py — Robinhood Chain position monitor with Solana exit rulebook ([77cdc67](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/77cdc671faa329174627588c07685998df252d05))
* Uniswap v4 + USDG — discovery, screening, and live execution (Phases 6+7) ([4057171](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/40571716980ba3133aebc9560427ef601a32d4c0))


### Bug Fixes

* a failed exit sell no longer strands the token side of a close ([1b3e28b](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/1b3e28b2e6639f9b26f875b53193d9599345fb3b))
* GeckoTerminal keyless tier throttles ~4 req/min, not 30 — shrink discovery budget ([44a2a72](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/44a2a727cefef844c6102454c3023e2c8d29c087))
* MinReserveUSD 8000-&gt;2500, was killing 73% of pools before any real gate ran ([3f003b6](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/3f003b62fd98d7584f4764f1575d93cdfda062e1))
* monitor loops froze DRY_RUN at launch; GeckoTerminal 403'd the Python UA ([61f5423](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/61f5423c55fa77dac0a628456b5fd628dd26ec3f))
* never journal tokenId="unknown" — orphan disables monitor SL/TP ([5fe73e8](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/5fe73e826c09532cd74f7d2625cbf03384ceb0f5))
* price the position at what the mint actually took, not what we offered ([09e1a8e](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/09e1a8ed54bb87ea4002d7349857c6a539cd00b9))
* strip executor JSON tail from the Robinhood deploy report line ([9ccef1a](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/9ccef1a2e41ec284084a35daebb83bae37e71b64))

## [1.12.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.11.2...v1.12.0) (2026-07-13)


### Features

* deterministic batch picker (direct deploy mode) ([d438b9e](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/d438b9eb9ec99639d5c81f91a4aaa2054f49dfd3))

## [1.11.2](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.11.1...v1.11.2) (2026-07-10)


### Bug Fixes

* version badge lost color segment on release-please bump ([f7fae01](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/f7fae01e9999d44c00372899fd32d6381a0d5996))

## [1.11.1](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.11.0...v1.11.1) (2026-07-10)


### Bug Fixes

* guard against phantom -100% PnL reads from the Portfolio API ([d0a0132](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/d0a0132c1de8fa6be1380e36c514d7844c1d244e))
* guard against phantom -100% PnL reads from the Portfolio API ([77c14d0](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/77c14d07e5510465886a05a46eff61b750765e89))

## [1.11.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.10.0...v1.11.0) (2026-07-10)


### Features

* balanced_tight two-sided strategy + GMGN insider/bundler hard gate ([a09d775](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/a09d775e2d5550919f8b333b7fe38fc5db11d8d7))
* balanced_tight two-sided strategy, GMGN rug gate, unmark-on-close ([b1b99b3](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/b1b99b3f3521164b59a6f776dca7548853f2c073))
* clear signal-seen marker on position close (unmark-on-close) ([5d81a33](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/5d81a3358947cd9101f3f4c01f03924fb1b1c616))

## [1.10.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.9.0...v1.10.0) (2026-07-09)


### Features

* GMGN holder-quality enrichment for signal candidates ([7309540](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/7309540e6f49d88135a8e1b65c1ae6483783b113))
* GMGN holder-quality enrichment for signal candidates ([e715bb5](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/e715bb531b27f61ae1cff32d389ff270861197fe))
* mode-scoped dedup window for casual (CASUAL_SEEN_TTL, default 6h) ([fb383c5](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/fb383c55f4dc1eb5801f3f335171d00d2bff0e12))
* mode-scoped dedup window for casual (CASUAL_SEEN_TTL, default 6h) ([66ba00d](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/66ba00daafecc5d8f5dd939c867e76de851eb9a8))

## [1.9.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.8.0...v1.9.0) (2026-07-09)


### Features

* **cron:** 1h-momentum override in position-monitor GUARD ([75d1008](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/75d1008e0d868ccd888c38885aedae8d18b6f537))
* **monitor:** sustained-downtrend exit rule in the 20s loop ([6edce3a](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/6edce3ad0ea51f864a40dc6c0e7210a7486b9455))
* **turnover:** fast-cycle — no trailing TP, 2h dedup window ([18d868d](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/18d868dcdd12d18d1a000c8b87eaa406b90e735c))


### Bug Fixes

* **cron:** forbid fee/TVL as HOLD justification for OOR positions ([784633d](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/784633d7c62324768afca6c68a0126a2257f373f))
* exit discipline + turnover fast-cycle ([d685923](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/d68592333303ca83ada145669f3142d8ac01e22c))
* remove hardcoded wallet address fallback from web3 scripts ([3148c70](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/3148c7046a7a9af268e8c58c87b4c50db8f1e715))

## [1.8.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.7.0...v1.8.0) (2026-07-08)


### Features

* **skill:** dlmm_stats.py scoreboard + operator-configurable report timezone ([fe96923](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/fe96923b6c9bfdf4c656466a991747e71f4fbcd6))
* **skill:** fast-cycle scoreboard + operator-configurable report timezone ([afd9da8](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/afd9da81c85e3ee68adecd183688dd0ff89b91f6))

## [1.7.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.6.0...v1.7.0) (2026-07-08)


### Features

* **skill:** instant script-side event alerts + 30m monitor cron ([4aa6315](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/4aa6315180c959f0509ec81b503c8017f7adcc6e))
* **skill:** instant script-side event alerts, stretch monitor cron to 30m ([b708caf](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/b708caf56f934d88965ed857d9407feaf0466728))

## [1.6.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.5.0...v1.6.0) (2026-07-08)


### Features

* **install:** ship the 20s monitor-loop systemd service ([06d7d94](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/06d7d941aabe7be0970c6c77c45da38b01db5fb8))
* **skill:** turnover fast-cycle — 2m OOR fuse, PnL circuit breaker, fee compounding ([ba294c9](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/ba294c97477f00ea2dfc5b2813c0163eda9c5cc7))
* **skill:** turnover fast-cycle — 2m OOR fuse, PnL circuit breaker, fee compounding ([330a854](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/330a8544aad5238dc9d84b0e5cfb8d2a4c2692a7))

## [1.5.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.4.0...v1.5.0) (2026-07-08)


### Features

* **skill:** extend OOR rebalance to casual and multiday modes ([362cfba](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/362cfbafd4b084045a6770c8646a2636a2cd5be6))
* **skill:** extend OOR rebalance to casual and multiday modes ([2eb4bae](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/2eb4bae92b7152a6f9f824de3ffe3ab21b9046a7))

## [1.4.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.3.0...v1.4.0) (2026-07-08)


### Features

* **skill:** bid_ask bin shapes + fast-cycle turnover OOR rebalance ([6c2a2e3](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/6c2a2e35b65d8d2faabd88a63946401e6fb0ea9b))
* **skill:** bid_ask bin shapes + turnover OOR rebalance ([7833c3d](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/7833c3d681a83c1727faa64d884f4d30d0a57a65))

## [1.3.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.2.0...v1.3.0) (2026-07-07)


### Features

* **scanner:** cooldown-aware screening + shorter casual harvest cooldown ([0e52fc7](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/0e52fc7ea5281c11013cffb466dc65a2b2ad2e78))
* **scanner:** cooldown-aware screening, PVP rival detection, casual harvest cooldown ([59b79c3](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/59b79c38c8a584ed0f3bc165060bc746d24e1911))

## [1.2.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.1.0...v1.2.0) (2026-07-07)


### Features

* **hermes:** weights-aware pick, audit hard-reject, lone-candidate rule ([f5c7daf](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/f5c7daf0ddf75b1b41d0cfb96e27068b1ef352b2))
* **scanner,skill:** degen fallback, pool-history payload, low-yield pool cooldown ([63a7363](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/63a736385b754a66096c6fad69c8b2a0c072ad3e))
* **scanner:** audit gate, lone-candidate conviction gate, degen payload fields ([129dbb5](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/129dbb5705ea26f89327b1cd3b5d39b3645c6cec))
* **skill:** pool memory, repeat-deploy cooldown, darwinian signal weights ([e14bd9c](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/e14bd9cbd558841f97f35433561d0bf58f0bdee3))


### Bug Fixes

* **hermes:** forbid execute_code wrappers, treat empty stdout as failure ([7f829af](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/7f829af6c33f47f04d7c176639c8de2702a06137))
* **install:** preserve profile secret/delivery/model on subscription re-merge ([b6e5f71](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/b6e5f71eebfeb79dda93045c445b5ccf7fad4232))

## [1.1.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v1.0.0...v1.1.0) (2026-07-06)


### Features

* **monitor:** compact position status card ([022d84b](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/022d84b9d30298ae347db72c514e7748931ba85e))
* **monitor:** script-side report delivery via hermes send ([9e2531b](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/9e2531bd8b775eb5c243eeb5053572e6f605706a))
* **scanner:** add turnover fee-capture mode ([53f7af0](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/53f7af0ca91516fcb0e2b1aae46664befd58c6cd))


### Bug Fixes

* **hermes:** require execution proof before DEPLOYED reports ([b9be444](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/b9be444a762e245791a6e6fa58a3213d1fb912ce))
* **pipeline:** validate --from-signal record before use ([e116975](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/e1169750f194aaa8fe92962f52918581f8cefaeb))

## [1.0.0](https://github.com/pgen0x/meteora-dlmm-trading-bot/compare/v0.1.0...v1.0.0) (2026-07-05)


### ⚠ BREAKING CHANGES

* rename repo to meteora-dlmm-trading-bot for SEO, add keyword-rich README intro

### Features

* loosen casual fee gate, trailing gap-through grace, reject tally; scrub instance-specific refs ([e0b3fc0](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/e0b3fc05174f301bd8bd2d231741823767e61162))
* **skill:** asymmetric-exit fixes — emergency SL floor, profit ratchet, journal reconciliation ([c4c4369](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/c4c4369a8763c87ccc5c4f927ea538001485bd28))


### Miscellaneous Chores

* rename repo to meteora-dlmm-trading-bot for SEO, add keyword-rich README intro ([768ed17](https://github.com/pgen0x/meteora-dlmm-trading-bot/commit/768ed17f54da62035772b3c6a3f265d4cd817bb5))

## [Unreleased]

### Changed
- Casual screening `MinFeeTVL` lowered 0.3 → 0.1. The discovery API's
  `fee_tvl_ratio` is scoped to the queried timeframe, so for the 30m casual
  window 0.3 demanded a ~14.4%/day fee pace and passed ~0 pools outside meme
  frenzies (live probe: 30m median ratio ~0.01%). Diverges intentionally from
  the Python pipeline's `max(0.3, 0.15)` — see the comment in `screen.go`.
- Scanner cycle log now appends a per-gate reject tally
  (`rejects[fee/TVL=36 non-SOL_pool=12 ...]`) so screening behavior is
  observable without a custom probe.
- Trailing take-profit gained a one-tick gap-through grace: when PnL wicks
  below both the ratchet floor and the +0.3% round-trip-cost lock between
  monitor ticks, the close is deferred one cycle instead of realizing a loss
  labeled "take-profit". Slow bleeds still close one tick later; the
  emergency stop-loss floor is unaffected.
- Template and asset copy scrubbed of instance-specific references (agent
  name, wallet-history stats) — the repo is public; deployment personalizes
  via the profile.

### Added
- `dlmm_reconcile.py`: audits the local close journal against the Meteora
  portfolio API (ground truth) — flags unjournaled closes and PnL divergences.
- Weekly journal-reconciliation cron job (Monday 09:00) added to the cron
  template; template regenerated from the live profile jobs (all 5 jobs,
  chat ids and profile paths re-templated).
- Monitor journals every close to `memories/dlmm_closes.jsonl` with a uniform,
  API-verified schema (previously the journal missed ~95% of closes).
- Emergency stop-loss floor 3pp below the configured hard SL: closes
  immediately, bypassing the age grace, AI holds, indicator timing, and
  `--report-only` (opt out with the new `--no-enforce` flag).

### Changed
- Trailing take-profit now uses a profit-ratchet floor (peak ≥5% locks +2%,
  ≥10% locks +6%, ≥20% locks 70% of peak) instead of a flat drop from peak;
  SOUL trigger lowered 5% → 3% (close-history analysis showed the 5% trigger
  almost never activated).
- Hard-SL grace period is now conditional (young AND in-range AND
  fee/TVL ≥ 10%) instead of unconditional 15 minutes — the unconditional
  grace let dumping positions ride far past the SL before it fired.
- Emergency close reasons can no longer be overwritten by softer rules
  (pumped-above / OOR / low-yield) that fire in the same cycle.

## [0.1.0] - 2026-07-02

Initial beta release. Everything below was consolidated from pre-release
development history into this first tagged version.

### Added
- Go daemon (`mdtb`): continuous poll ▸ screen ▸ dedup ▸ forward loop against
  Meteora's public pool-discovery API.
- Dual-mode screening: `casual` (30m, volume-spike plays) and `multiday`
  (24h, quality holds), each with independent thresholds and isolated
  position budgets.
- Layered risk gates: TVL, fee/TVL, market cap, holder count, organic score,
  top-10/dev supply concentration, mint/freeze authority, Jupiter shield
  status, and a best-effort DexScreener downtrend filter (the reference bot
  degen-score and bin-step gates ported from the upstream Python pipeline).
- Batch AI-Pick signalling: one HMAC-signed webhook per cycle carries every
  qualifying pool as an array, replacing first-come-per-pool sends so the
  agent compares the full batch before deploying.
- Pluggable dedup store: in-memory, or Redis with a per-pool rolling TTL
  (`SetNX`, not a shared-set `SAdd`+`Expire`, so pools don't dedupe forever).
- `solana-dlmm` skill: `dlmm_pipeline.py` (ingestion/deploy), `dlmm_monitor.py`
  (exit management — stop-loss, trailing take-profit, out-of-range, and a
  Close GUARD that refuses to close a healthy in-range high-fee position),
  `dlmm_executor.js` (on-chain execution).
- `install.sh`: wires the skill, webhook subscription, SOUL.md section-9
  template, and DLMM-relevant cron job templates (5m position monitor, daily
  self-improvement review) into a Hermes profile, and builds the daemon.
- `docs/SIGNAL_SCHEMA.md`: the webhook payload contract.
- `CLAUDE.md`: architecture and convention notes for AI-assisted development.
- `./mdtb -version` / `main.Version` for reporting the running build version.

### Changed
- `assets/skill/scripts/` is symlinked into installed profiles instead of
  copied + `sed`-rewritten — edits in this repo now take effect in every
  installed profile immediately. Scripts resolve their own profile directory
  at runtime instead of relying on an install-time path substitution.
- `dlmm_executor.js` resolves its own path via `process.argv[1]` rather than
  `__dirname`, since Node always resolves symlinks for the latter (unlike
  Python's `__file__`), which broke wallet-key lookup once scripts became
  symlinked.
- npm dependencies for the skill are installed at the repo level
  (`assets/skill/node_modules`), not per-profile, since `require()` resolution
  follows the same realpath-through-symlinks behavior as `__dirname`.

### Fixed
- Webhook report formatting switched to a native pipe-table (code-block
  fencing was falling back to legacy MarkdownV2 and leaking literal escape
  characters).
- Audit-token reject gate loosened to stop over-rejecting on non-critical
  risk levels.

### Security
- Removed hardcoded Helius/QuickNode RPC provider keys that had been
  committed in plaintext since the initial commit. `dlmm_executor.js` now
  reads `SOLANA_RPC_URLS` from the profile `.env`, falling back to the public
  mainnet-beta RPC if unset. Git history was scrubbed
  (`git filter-repo --replace-text`) and force-pushed; the original keys were
  rotated at the provider regardless, since history rewrites don't un-expose
  something GitHub already cached.
