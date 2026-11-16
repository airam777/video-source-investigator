# Fáza 2 – Prehrávač, streamovacie hosty a CDN

**Predmet:** `#Ali G - Gdo bít já (2026) CZ DABING`  
**Stránka:** https://prehraj.to/ali-g-gdo-bit-ja-2026-cz-dabing/a6b13b0b09ce302b  
**Dátum spracovania reportu:** 2026-11-16

## Zistenia z poskytnutej extrakcie

| Položka | Zistenie | Stav |
|---|---|---|
| Premenná prehrávača | `var player = "videojs"` | REPORTED |
| Aktívna vetva podľa podmienky | Video.js cez `VideoJsPlayer(...)` | REPORTED |
| Alternatívna vetva | JW Player | REPORTED |
| Hostname-y médií | `pf-storage5.premiumcdn.net`, `pf-storage1.premiumcdn.net`, `pf-storage3.premiumcdn.net` | REPORTED |
| Prehrávacie varianty | MP4 1080p a 720p | REPORTED |
| Titulky | VTT, označenia CZE a CZE1; ID 13781981 a 13781982 | REPORTED |
| AJAX názvy | `videoStarted`, `videoViewCommission`, `videoProgressNotify`, `videoVisit`, `subscriptionPromotionInfoDialog-loadVideos` | REPORTED |
| Názvy tokenových polí | `videoStartedToken`, `videoCommissionToken`, `videoViewProgressNotifyToken` | REPORTED |

## Technická interpretácia

- Ak extrahovaný JavaScript zodpovedá pôvodnému HTML, hodnota `player = "videojs"` a príslušná podmienka ukazujú, že stránka vyberá vetvu Video.js. Samotná prítomnosť kódu JW Player neznamená, že bol v tomto prípade aktívny.
- Hostname-y pod `premiumcdn.net` predstavujú technické ciele uvedené v extrakcii. Ich prítomnosť nepreukazuje právne vlastníctvo, zmluvný vzťah s Přehraj.to ani to, kto obsah na infraštruktúru nahral.
- Rozdiel medzi uvádzaným pôvodným MKV a prehrávacími MP4 variantmi je kompatibilný s možnosťou serverovej prípravy/transkódovania. Bez originálneho súboru, serverovej dokumentácie alebo dôveryhodných prevádzkových záznamov je však transkódovanie iba **INFERRED**, nie potvrdené.
- Názvy AJAX akcií a tokenových polí dokazujú nanajvýš to, že stránka podľa extrakcie obsahovala mechanizmy na evidenciu prehrávania/návštevnosti. Neodhaľujú identitu používateľa ani oprávnenie na distribúciu.

## Bezpečné zaobchádzanie s URL a tokenmi

V konverzácii sa objavili podpísané streamovacie URL a autorizačné hodnoty. Tento repozitár ich zámerne neobsahuje.

Nikdy sem nevkladať:
- celé podpísané MP4/VTT URL;
- hodnoty parametrov `token`, `expires`, `signature`, `sparams`;
- JWT, cookies, session ID ani autorizačné hlavičky;
- súkromné logy alebo údaje iných používateľov.

Ak sa URL uvádza ako dôkaz, zverejniť iba hostname a cestu primerane zredigovať, query string úplne vynechať.

## Čo by potvrdilo jednotlivé tvrdenia

| Tvrdenie | Potrebný dôkaz |
|---|---|
| Video.js bol aktívne zvolený | Pôvodný HTML/JS a kontrola podmienky prehrávača |
| Konkrétny CDN host obsluhoval prehrávanie | Neautorizovaná? Nie — iba bežná verejná sieťová kontrola bez obchádzania ochrany, alebo prevádzkové záznamy oprávneného správcu |
| Súbor bol transkódovaný | Dokumentácia platformy alebo dôveryhodné serverové záznamy |
| Kto video nahral | Interný upload audit prevádzkovateľa; nie samotný HTML kód |

## Záver fázy

Poskytnutá extrakcia naznačuje Video.js a viacero hostname-ov pod `premiumcdn.net`. Neumožňuje však určiť konkrétneho uploadujúceho ani preukázať licenciu či pôvod obsahu.
