# AGENTS.md

# MCW LINK IRC Projektas

## Projekto paskirtis
Šis projektas yra **MCW LINK IRC** sistema, kuriama su **Python**.

Agentas privalo dirbti tiksliai, nuosekliai ir laikytis šiame faile apibrėžtų taisyklių.  
Visi pakeitimai turi būti atliekami atsakingai, išlaikant aiškią versijų kontrolę, tvarkingą buildų struktūrą ir nuoseklų release procesą.

---

# 1. Pagrindiniai principai

## 1.1 Kalba ir tech stack
- **Pagrindinė kalba:** Python
- Jei projekte yra **client-side** ir **server-side** dalys, jos turi būti tvarkomos atskirai, bet nuosekliai.
- Visi pakeitimai turi būti pritaikyti pagal esamą projekto architektūrą.
- Negalima daryti bereikalingų perrašymų, jei užtenka tikslaus ir saugaus pataisymo.
- Turi būti išlaikytas suderinamumas su dabartine projekto struktūra, nebent aiškiai daromas didesnis architektūrinis pakeitimas.

---

# 2. Privalomas informavimas prieš build

Kai tik užbaigiami client-side ir/arba server-side pakeitimai:

**Prieš darant naują buildą būtina aiškiai informuoti, kad dabar bus daromas buildas.**

Leistini pavyzdžiai:
- „Client pakeitimai užbaigti, dabar darysiu naują buildą.“
- „Server pakeitimai užbaigti, dabar darysiu naują buildą.“
- „Client ir server pakeitimai užbaigti, dabar darysiu naują buildą.“

Šis žingsnis yra **privalomas** ir negali būti praleistas.

---

# 3. Buildų vieta ir struktūra

## 3.1 Client buildai
Visi **client release buildai** turi būti dedami tik į:

`server-deploy/releases`

Taisyklės:
- Čia turi gulėti tik **client release buildai**
- Negalima maišyti kitų serverio runtime ar deploy failų
- Buildai turi būti tvarkingi, aiškiai suversijuoti ir lengvai identifikuojami

---

## 3.2 Server failai
Visi **serverio failai** turi būti laikomi tik:

`server-deploy`

Taisyklės:
- Serverio runtime failai
- Deploy failai
- Serverio konfigūracija
- Visi kiti server-side failai

**Negalima dėti serverio failų į `server-deploy/releases`, nebent tai būtų aiškiai išskirtas client release paketas.**

---

# 4. Privalomi client buildų targetai

Kai daromas **client buildas**, jis privalo būti paruoštas **abiejoms platformoms**:

- **Windows build**
- **Linux build**

## 4.1 Privaloma taisyklė
Jeigu daromas naujas client release:
- nepakanka sugeneruoti tik vieną platformą
- turi būti paruošti **abu buildai**
- abu buildai turi būti įdėti į `server-deploy/releases`

## 4.2 Platformų pilnumas
Client release laikomas pilnai paruoštu tik tada, kai:
- yra Windows buildas
- yra Linux buildas
- versija atnaujinta
- manifestas atnaujintas
- buildai padėti į teisingą vietą

Jeigu trūksta bent vieno iš šių dviejų buildų, release negali būti laikomas pilnai užbaigtu.

---

# 5. Versijavimo taisyklės

Naudojamas semantinis formatas:

`MAJOR.MINOR.PATCH`

Agentas privalo įvertinti pakeitimų dydį ir pasirinkti **mažiausią logiškai teisingą versijos bump**.

---

## 5.1 Patch versija — `0.0.X`
Didinama, kai:
- pataisomos smulkios klaidos
- atliekami maži UI/UX pataisymai
- atliekami maži logikos taisymai
- atliekami stabilumo ar tekstiniai pataisymai
- nėra naujo funkcionalumo ar architektūrinių pokyčių

Pavyzdžiai:
- bug fix
- tekstų pataisymas
- mažas behavior fix
- nedidelis stabilumo pagerinimas

Pvz:
- `1.2.3` → `1.2.4`

---

## 5.2 Minor versija — `0.X.0`
Didinama, kai:
- pridedama nauja funkcija
- atsiranda naujas modulis
- reikšmingai pagerinamas funkcionalumas
- keičiamas client arba server elgesys be breaking changes
- atliekami didesni, bet suderinami patobulinimai

Pavyzdžiai:
- naujas panelis
- naujas commands funkcionalumas
- auth ar settings patobulinimas
- reikšmingas UI/UX išplėtimas

Pvz:
- `1.2.4` → `1.3.0`

---

## 5.3 Major versija — `X.0.0`
Didinama, kai:
- daromi breaking changes
- keičiamas protokolas
- keičiasi sistemos veikimo principai
- client/server tampa nebesuderinami su sena versija
- atliekamas reikšmingas architektūrinis perdirbimas

Pavyzdžiai:
- auth sistemos overhaul
- protocol pakeitimai
- client/server nesuderinami pakeitimai
- didelis visos sistemos perrašymas

Pvz:
- `1.3.2` → `2.0.0`

---

## 5.4 Versijos parinkimo taisyklė
Jeigu pakeitimas yra:
- minimalus arba taisymo pobūdžio → **Patch**
- naujas funkcionalumas be breaking changes → **Minor**
- keičiantis pagrindinį sistemos veikimą ar suderinamumą → **Major**

Jeigu kyla abejonė:
- rinktis **mažiausią logiškai teisingą bump**
- nekelti `major`, jei to nereikia
- nekelti `minor`, jei tai tik smulkus fix

---

# 6. Manifesto atnaujinimas

## 6.1 Manifestas privalo būti atnaujintas
Po kiekvieno release, kai pakeliama versija:

- **Visada atnaujinti manifestą su nauja versija**
- Manifestas turi atspindėti tikrą ir naujausią release versiją
- Negalima palikti seno versijos numerio po buildo ar release

## 6.2 Jei yra keli versijų failai
Jeigu projekte naudojami keli failai, susiję su versija ar release logika:
- reikia atnaujinti **visus susijusius manifestus / version failus**
- negalima palikti neatitikimų tarp release ir manifestų

---

# 7. Standartinis release procesas

Kai daromi pakeitimai, agentas privalo laikytis šios sekos:

1. Atlikti reikalingus client/server pakeitimus
2. Įvertinti pakeitimų dydį
3. Nustatyti tinkamą versijos bump:
   - Patch
   - Minor
   - Major
4. Atnaujinti versiją
5. Atnaujinti manifestą / manifestus
6. Informuoti, kad dabar bus daromas naujas buildas
7. Sugeneruoti buildą
8. Jei buildinamas client:
   - sugeneruoti **Windows buildą**
   - sugeneruoti **Linux buildą**
9. Padėti client buildus į `server-deploy/releases`
10. Užtikrinti, kad serverio failai liktų `server-deploy`
11. Patikrinti `release-notify.env`
12. Paklausti, ar reikia išsiųsti Discord notification

---

# 8. Discord notification taisyklė

## 8.1 Privaloma paklausti
Po release paruošimo arba prieš pilnai užbaigiant release procesą:

**Būtina paklausti, ar reikia išsiųsti Discord notification naudojant webhooką.**

Pavyzdinis tekstas:
- „Release paruoštas. Ar reikia išsiųsti Discord notification per webhooką? Patikrinsiu `release-notify.env`.“

---

## 8.2 release-notify.env naudojimas
Kai kalba eina apie release pranešimus:
- būtina patikrinti `release-notify.env`
- webhook konfigūracija turi būti imama iš ten
- negalima ignoruoti šio failo, jei daromas release notification procesas

---

# 9. Agento elgesio taisyklės

Agentas privalo:
- laikytis projekto struktūros
- nekeisti failų vietų savavališkai
- tvarkingai valdyti versijas
- visada atnaujinti manifestą
- visada informuoti prieš buildą
- visada paruošti **Windows + Linux** client buildus
- visada paklausti dėl Discord notification
- remtis `release-notify.env`, kai kalba eina apie release pranešimus

---

# 10. Ko agentas negali ignoruoti

Negalima:
- praleisti versijos bump
- praleisti manifesto atnaujinimo
- daryti buildo neinformavus iš anksto
- sugeneruoti tik vieną client platformos buildą
- pamiršti Windows buildą
- pamiršti Linux buildą
- sumaišyti client buildų ir server failų vietų
- pamiršti paklausti dėl Discord notification
- ignoruoti `release-notify.env`

---

# 11. Trumpa atmintinė agentui

- Python projektas
- Užbaigus pakeitimus → **pirma informuoti**, tada buildinti
- Client buildai → `server-deploy/releases`
- Server failai → `server-deploy`
- Client release visada turi turėti:
  - **Windows buildą**
  - **Linux buildą**
- Patch = smulkūs pakeitimai
- Minor = naujas funkcionalumas
- Major = breaking / architektūriniai pakeitimai
- **Visada atnaujinti manifestą**
- **Visada paklausti dėl Discord webhook notification**
- **Tikrink `release-notify.env`**

---

# 12. Rekomenduojamas veikimo šablonas

1. Pakeičiau client/server logiką
2. Įvertinau pakeitimų dydį
3. Pakėliau versiją
4. Atnaujinau manifestą
5. Informuoju: „Pakeitimai baigti, dabar darysiu naują buildą.“
6. Padarau buildą
7. Jei tai client release:
   - padarau **Windows buildą**
   - padarau **Linux buildą**
8. Abu client buildus įdedu į `server-deploy/releases`
9. Server failus palieku `server-deploy`
10. Patikrinu `release-notify.env`
11. Paklausiu: „Ar reikia išsiųsti Discord notification per webhooką?“

---

# 13. Finalinė taisyklė

Jeigu agentas daro release susijusį darbą, prioritetų seka visada yra:

**teisinga versija → atnaujintas manifestas → informavimas prieš buildą → Windows + Linux client buildai → teisinga build vieta → klausimas dėl Discord notification**