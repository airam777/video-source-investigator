# Fáza 3 – Verejný výskum atribučných stôp

**Predmet:** `#Ali G - Gdo bít já (2026) CZ DABING`  
**Dátum rešerše:** 2026-11-16

## 1. File & Image Uploader (z-o-o-m.eu)

**Verejný zdroj:** https://z-o-o-m.eu/  
**Pomocník:** https://z-o-o-m.eu/help.htm  
**Fórum:** https://forum.z-o-o-m.eu/

Oficiálna stránka opisuje aplikáciu ako File & Image Uploader a uvádza podporu veľkého množstva súborových, obrazových a video hostingov. Dokumentácia vysvetľuje výber hostingu, frontu súborov a samotný proces uploadu.

**Stav: CONFIRMED (existencia a deklarovaná funkcia softvéru).**

V HTML extrakcii predmetnej stránky sa podľa poskytnutých údajov nachádza text:

`ABC- File Uploader (z-o-o-m.eu)- File Uploader (z-o-o-m.eu)`

**Stav: REPORTED (výskyt textu v extrakcii).**

**Čo z toho nemožno vyvodiť:** text nepreukazuje, že konkrétny používateľ aplikáciu skutočne použil, že cez ňu nahral práve tento súbor, ani kto tú osobu predstavuje. Označenie môže byť textom preneseným z iného zdroja alebo generickým popisom.

## 2. PremiumCDN a ServerZone

**Verejný sekundárny zdroj:** https://webrate.org/site/premiumcdn.net/

Záznam WeRate zobrazuje pre doménu `premiumcdn.net` väzbu na ServerZone s.r.o. a uvádza ASN 51586 s názvom ServerZone s.r.o. Záznam obsahuje aj informácie odvodené z RIPE databázy.

**Stav: CONFIRMED ako verejne publikovaný údaj v sekundárnom agregátore; nie ako nezávislé potvrdenie vlastníctva konkrétnych serverov.**

V extrakcii stránky sa uvádzajú hostname-y:
- `pf-storage5.premiumcdn.net`
- `pf-storage1.premiumcdn.net`
- `pf-storage3.premiumcdn.net`

**Stav: REPORTED.**

**Obmedzenie:** všeobecný záznam o doméne/ASN nepreukazuje, kto prevádzkuje každý konkrétny storage uzol, aký je vzťah medzi CDN a Přehraj.to, ani kto obsah nahral. Údaje o iných subdoménach sa nesmú automaticky prenášať na tieto hostname-y.

## 3. Súhrnná matica dôkazov

| Tvrdenie | Stav | Poznámka |
|---|---|---|
| Existuje aplikácia z_o_o_m File & Image Uploader | CONFIRMED | Oficiálna stránka a dokumentácia |
| Aplikácia podporuje upload na rôzne hostingy | CONFIRMED | Deklarované výrobcom |
| Text o aplikácii sa nachádza v extrakcii predmetnej stránky | REPORTED | Pôvodný HTML súbor nebol v tejto fáze znovu overený |
| Aplikácia bola použitá pri tomto konkrétnom videu | UNKNOWN | Samotný text v popise nestačí |
| `premiumcdn.net` je vo verejnom agregátore spojená so ServerZone s.r.o. | CONFIRMED (as published) | Sekundárny agregátor; nie právny dôkaz |
| Uvedené storage hostname-y sa objavili v extrakcii | REPORTED | Bez nezávislého opätovného načítania HTML |
| ServerZone vlastní alebo prevádzkuje konkrétne storage uzly | UNKNOWN | Potrebné dôveryhodné prevádzkové/registrátorské potvrdenie |
| Konkrétna osoba nahrala súbor | UNKNOWN | Nie je verejne preukázané |
| Distribúcia súboru je licencovaná | UNKNOWN | HTML a CDN metadata to nepreukazujú |

## 4. Hranice atribúcie

Z verejných zdrojov nemožno spoľahlivo zistiť:
- meno alebo účet konkrétneho uploadujúceho;
- IP adresu a časovú stopu uploadu;
- zdrojový súbor, z ktorého bol obsah získaný;
- či uploadujúci mal právo obsah distribuovať.

Tieto údaje môžu byť dostupné iba prevádzkovateľovi služby v interných záznamoch a ich sprístupnenie podlieha príslušnému právnemu procesu. Tento projekt sa nepokúša obchádzať autentifikáciu, podpisy URL, ochranu prehrávača ani získavať neverejné logy.

## 5. Zdroje

1. Oficiálna stránka File & Image Uploader – https://z-o-o-m.eu/
2. Oficiálna dokumentácia aplikácie – https://z-o-o-m.eu/help.htm
3. Verejné fórum aplikácie – https://forum.z-o-o-m.eu/
4. Sekundárny doménový/ASN agregátor pre premiumcdn.net – https://webrate.org/site/premiumcdn.net/

## Záver fázy

Výskum podporuje existenciu nástroja z_o_o_m a verejnú asociáciu domény premiumcdn.net so ServerZone s.r.o. Neexistuje však dostatok verejných dôkazov na spojenie týchto stôp s konkrétnou osobou, ktorá nahrala predmetné video, ani na určenie právneho pôvodu súboru.
