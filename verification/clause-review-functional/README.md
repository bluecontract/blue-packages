# Natywna kwalifikacja klauzul i szablonów z przeglądu 24 listopada 2026

Testy używają dwóch ścieżek. `CancellationRefreshConformance`, `ScheduleReservationConformance` i `WholeOrderCancellationConformance` wykonują rzeczywiste operacje Contracts na typach z dokładnie przypiętych archiwów zbudowanych lokalnie. `CatalogOrderAttachmentConformance` dodatkowo tworzy dokumenty z pliku Agreement wyemitowanego przez Go i wykonuje podpisane operacje w Coordination. Potwierdzenia płatności pochodzą od testowego, uprawnionego gwaranta.

## Punkt odniesienia

- Archiwa Packages z commitu `09c8208ecafc56c9c32b4233c145b2882be6a98b`, indeks `5e1d4093379e91b722b78f7fa5cc0b05ba5d3c0d9aa9ed99f3563c77a4e51bf8`.
- Agreement `service-only` z Go `a8b9be88251f61129df1d751f72a94ab3a9352fa` (/15), SHA-256 `e8b9cf1a459a4d076006573fad37236da536b7eb12f0decea7d857a33fc35e03`.
- Agreement `scheduled-both` z tego samego Go, SHA-256 `eeec846066b1fdd828961cb7933eaa8156d03f80487169456df64dd5bc0b7812`.
- Natywny runtime Core `376059aa2f9230795c46bf4c4aa6c096c557a56a`. SHA-256 użytego pliku z classpath `de672b5a92868adec8ed6e92c68772972ef627853df806fdec52e6bfba1517a4`.
- Logi lokalne są w `reports/clause-review-functional/`. Porównanie T01 (/15) kończy się oczekiwanym błędem testu po zatwierdzeniu rezerwacji. Order jest aktywny, ma potwierdzony termin i stale zapisane `beforeConfirmation=true`, bez terminu bezpłatnego anulowania.
- Na poprzednim indeksie przechodzą kontrola C17, kwalifikowany relay i catch-up rzeczywistej PI, podpisana odmowa podmiany płatności oraz granice Commerce i zegara. Plik `T08-T10-baseline-plus-identical-selectors.log` potwierdza T08–T10 dla stock Schedule i Activation; ostatnia próba w tym pliku celowo używa nowych referencji R02, których ten indeks jeszcze nie rozwiązuje.

## Piny nowej kwalifikacji

- Źródło archiwów Packages `41153640c83cf498907f6fc00d249cbf2e8a8b9b`, z `53ad03e`. Indeks SHA-256 `60ee068db2bde828c35e41edb0289bc562b36adeeffbf82ad74512ad88c23898`.
- Źródła Agreement /16 z Go `71698777b5dbc2ef255332c2c406b3c2d89eb33c`. SHA-256 `service-only` `220dfa09ec06bf4c3e3c688d21aa39ce10a8663b7254b25187ea168237f1b33c`, `scheduled-both` `6ce6d1b6086a9f94f4182698e680424dbeb33f5ead64f3482048dd4fdba14590`, `manual` `c0348f7c2e947e7e827b605db62c770e30d8ae58533e4df1940faa8d07b21f76`.
- Natywny runtime Core `376059aa2f9230795c46bf4c4aa6c096c557a56a`. Zakwalifikowany lokalny plik `core-schedule-activation-runtime/reports/core-http-test-classpath.txt` ma SHA-256 `823d488c28fdbd5dbd31b88a4274b7b61233596fc76d88007f35107895fc1e79`.
- Pierwszy artefakt diagnostyczny `service-only` (`405252f9…`, Go `4c3264b…`) zakończył się przed inicjalizacją. Generator dowodów przeniósł przypięcie z zachowanego /15 do artefaktu /16. Próba pozostaje w logu `candidate-60ee068d/T01-T02-service-only-signed-go16.log`.

Kolejne lokalne archiwa z `99de8755f36e02cf445c640db79880098ed0b356` mają indeks SHA-256 `b66096cfc04ba9495ba853a50f6e4cccc7f97ed4c7e09ba30069de2b47b01ed9`. Względem `60ee068d…` zmieniły się archiwa `clause-payment` i `myos`; pozostałe 40 ma identyczne SHA-256. Porównanie dziesięciu wspólnych źródeł Agreement z Go `71698777…` i `1d8eaeb0fa0ad05f0ef032b2c96cf4db8163af7d` wskazuje wyłącznie zmianę `/clauses/receipts/type/blueId`. Źródło `service-only` z tego Go ma SHA-256 `3b4bbc9cf1154a018efd218b7764adc1a937287548dddd624e3c9200f31c44e6`.

## Próby

| Przypadek | Wejście i sprawdzany wynik |
| --- | --- |
| T01 | Podpisane `timed-cancellation-service-refresh` na zwykłym Agreement `service-only`. Po potwierdzeniu finansowanego terminu aktualizują się obie granice i znika zwolnienie przed potwierdzeniem. Źródło nie deklaruje zegara elapsed. |
| T02 | `CancellationRefreshConformance` rozróżnia dwie rzeczywiste managed PI o tej samej kwocie. Tylko potwierdzony capture wybranego źródła usuwa blokadę późnej opłaty. Podpisany wariant T01 potwierdza dodatkowo odświeżenie przez zwykły Agreement z Go. |
| T03 | `CancellationRefreshConformance baseline` potwierdza, że lokalna obserwacja pola pomija zastąpienie przodka i zapis z managed PI. Obserwator rodzica oraz dokładny zapis pola dostarczają osobnych pozytywnych kontroli. |
| T04 | `CancellationRefreshConformance` dołącza rzeczywiście zakończoną PI przez natywne `provide` i odczytuje zachowany wynik po typowanym `Document Attached`. Dołączenie nie emituje ponownie wyniku operatora, a ponowienie zachowuje dostępność i brak decyzji. Księgowanie potwierdzają osobne testy finansowe. |
| T05–T07 | Niezależny zestaw `ActivationConnectionReferencesConformance`. `ScheduleReservationConformance` sprawdza także złożenie prawdziwych Commerce i Schedule z logicznymi referencjami. |
| T08 | `ScheduleReservationConformance` sprawdza dokładnego aktora, tożsamość zapisu i requestu, propozycję, rewizję i wycofanie nieudanej próby bez trwałych efektów. Podpisane `timed-accept-alternative` sprawdza poprawny tok sprzedawcy i kupującego. |
| T09 | `ScheduleReservationConformance` uruchamia niezależne zgody hotelu i restauracji przy tej samej kwocie, test zmiany podstawy drugiej rezerwacji i samodzielną klauzulę Schedule. |
| T10 | `ScheduleReservationConformance` pozwala osobno zmienić SKU lub ilość za tę samą sumę oraz sprawdza odmowy dla zmiany kwoty, waluty, sprzedawcy, niewłaściwej osoby i nieaktualnej propozycji. Podpisany `timed-accept-alternative` zmienia SKU i ilość przy tej samej kwocie, zachowuje pierwotny `orderSnapshot` i sprawdza odmowę przed faktycznym zabezpieczeniem wybranej PI. |
| T11 | Podpisany `timed-payment-admission` odrzuca błędny request, błędny ref przygotowanego wymagania i drugą PI o tej samej kwocie i walucie przed wyborem. Przyjmuje oryginał i odrzuca późniejszą podmianę bez zmiany wyboru. Odrębny `OrderDecisionConformance` bada predykat capture dla pól tożsamości, warunków i rewizji. |
| T12 | Niezależne testy finansowe obejmują `DeclarativeReceiptsConformance` i podpisane przebiegi z potwierdzeniem wyniku. |
| T13 | Podpisane `timed-reject-first` i `timed-cancel-first` potwierdzają jedną operację VOID na wybranej PI i brak nowego capture. Późny wynik już rozpoczętej próby capture sprawdzają odrębne testy Payment. |
| T14 | `WholeOrderCancellationConformance` sprawdza granice okien, zaokrąglenia i brak zmiany decyzji przy powtórzeniu. `ClockCompositionProof` sprawdza rzeczywiste pierwsze zatwierdzenie, brakujący czas i fallback oraz zachowanie przy ponowieniu. |

R04 obejmuje odmowę identycznych selektorów zdarzeń. Planer porównuje wartości selektorów. Rozłączność dwóch różnych filtrów po uwzględnieniu dziedziczenia typów nie została zakwalifikowana.

T05–T07 przeszły na ograniczonym indeksie `f79fe52dbfd2bebeac2c180cb5d7227605991cf43782f9778855fa6649083390` z Core `376059aa…`. Oryginalny log jest skopiowany do `reports/clause-review-functional/T05-T07-r02-reduced-native.log`, SHA-256 `71904f9ef3f21ae59beab4569bb33d0625880ff743fa206cd5ce3d6a49c8ce75`. Indeks obejmuje m.in. Schedule, Orders i Commerce. Wspólna próba T06 na pełnym indeksie jest w tabeli poniżej.

## Wyniki na indeksie `60ee068d…`

Logi tych prób są w `reports/clause-review-functional/candidate-60ee068d/`.

| Log | Wynik |
| --- | --- |
| `T01-T02-service-only-71698777-recovered.log` | PASS. Przy podpisanej zgodzie po pełnym hold potwierdzony start `1796126169000000` daje `beforeConfirmation=false` i `freeUntil=1796039769000000` (start minus 24 godziny). Potwierdzenie capture 7 200 minor aktualizuje dostępność z tej samej PI bez działania na Order. |
| `T02-T04-native.log` | PASS. Dwie managed PI mają tę samą kwotę i różne pochodzenie. Potwierdzenie obcej PI nie zmienia projekcji wybranej. Właściwy capture i dołączenie zachowanego wyniku odświeżają dostępność. Negatywne kontrole C17 i powtórzenie pozostają zielone. |
| `T06-T08-T10-native.log` | PASS. Samodzielny Schedule, rzeczywiste logiczne referencje Commerce/Schedule, odmowa przy niezgodnym zapisie lub żądaniu bez częściowego efektu, osobne zgody o tej samej kwocie, szersza alternatywa, odrzucenie identycznych selektorów. |
| `T08-T10-reviewed-alternative-71698777-signed.log` | PASS. Przed oryginalnym hold odmowa propozycji, po hold podpisany sprzedawca proponuje inne SKU i ilość przy USD 72. Kupujący może przyjąć aktualną propozycję. Pierwotne `orderSnapshot`, rewizja i warunki zachowane. Jedno żądanie capture na oryginalnej PI. |
| `T09-T10-funding-native.log` | PASS. Stock Schedule potwierdza, proponuje alternatywę i przyjmuje ją zależnie od wyniku wybranej managed PI. Brak hold, trwający capture, zmienione warunki lub rewizja, pending void i zamknięta PI nie dają wymaganej podstawy. |
| `T11-capture-predicate-native.log` | PASS. Wybrana instrukcja, wymaganie, pierwotne pochodzenie, bieżąca rewizja, warunki, kwota, waluta i dostęp muszą odpowiadać zdefiniowanej regule capture. Lokalna próba predykatu uzupełnia podpisane `providePayment`. |
| `T11-payment-admission-71698777-signed.log` | PASS. Podpisane `providePayment` odrzuca zły request, zły ref wymagania i inną USD 72 PI. Pierwotne przygotowanie pozostaje nienaruszone. Po przyjęciu prawdziwej PI druga próba podmiany nie zmienia wyboru. |
| `T13-timed-reject-first-71698777-signed.log` | PASS. Podpisane odrzucenie blokuje obie operacje anulowania i późniejszą zgodę. Oryginalna USD 72 PI dostaje jeden VOID także po powtórzeniu odrzucenia. Potwierdzenie gwaranta zamyka VOID z capture i refund równymi zero. |
| `T13-timed-cancel-first-71698777-signed.log` | PASS. Podpisane anulowanie klienta zamyka datowaną rezerwację z podanym powodem. Późniejsze odrzucenie i zgoda nie przechodzą. Powtórzenie anulowania utrzymuje jeden VOID na pierwotnej PI, capture i refund pozostają zero. |
| `T14-boundaries-recovered.log`, `T14-clock-recovered.log` | PASS. Sześć przypadków Commerce i osiem przypadków zegara. Czas pierwszej zgody 10:03 ma pierwszeństwo nad SECURE 10:00. Poprawny fallback wymaga brakującego czasu aktywacji i zachowuje oryginalną wartość po dołączeniu lub powtórzeniu. |
| `T01-T02-service-only-71698777-signed.log` | Aplikacja przerwała próbę po skutecznym przygotowaniu i dołączeniu PI oraz oczekiwanej odmowie zgody przed hold. Wznowienie używa osobnego logu. |

## Wyniki na indeksie `b66096cf…`

- Podpisana próba T01 i T02 `service-only` przeszła. Potwierdzony start `1796127143000000` daje `beforeConfirmation=false` i `freeUntil=1796040743000000`. Natywne potwierdzenie capture na oryginalnej PI zmienia dostępność bez dodatkowej operacji na Order. Log `reports/clause-review-functional/final-b66096cf/T01-T02-service-only-1d8eaeb0-signed.log`. SHA-256 `95eb26e7aa0e2665531587a89f447c20547e91cddbe8a0a19ec4e3848a9077d9`.
- T02–T04 przeszły ponownie na pełnym indeksie. Log `reports/clause-review-functional/final-b66096cf/T02-T04-native.log`. T05–T07 również przeszły na pełnym indeksie, łącznie z rzeczywistym rozwiązywaniem stock Schedule i Commerce oraz aneksami. Log `reports/clause-review-functional/final-b66096cf/T05-T07-native.log`.
- T12 w podpisanej próbie finansowej potwierdza zerowe wpływy i naliczenie po hold oraz pending capture. Pierwszy potwierdzony capture daje 7 200 minor wpływów i 900 minor prowizji. Powtórzenie utrzymuje ten wynik. Log `reports/review-finance/final-b66096cf/signed/timed-late-refund-after-payout-agreement-readiness/native.log`.
- T13 ma odrębny dowód Payment. Rzeczywisty wynik testowego gwaranta po niejednoznacznym wyniku rozpoczętego capture prowadzi do jednego pełnego refundu. Brak równoległego VOID. Log `reports/review-finance/final-b66096cf/standalone/refund-readiness.log`.

## Polecenia odtworzenia

Z katalogu Blue Packages z kodem testów ustaw `archives` na katalog z dokładnym indeksem i archiwami, `core_cpfile` na plik ze ścieżką klas Core, `source` na wskazany plik wyemitowany przez Go. Każdy podpisany przypadek uruchamiaj w osobnej JVM. Potrzebny jest JDK 21.

```bash
classes=$(mktemp -d)
classpath=$(cat "$core_cpfile")
javac -cp "$classpath" -d "$classes" tools/{QualificationRuntime,ActivationConnectionReferencesConformance,CancellationRefreshConformance,ScheduleReservationConformance,WholeOrderCancellationConformance,CatalogOrderAttachmentConformance,OperationInputs,BuildPaymentFamily,BuildFinalGas,OperationInputConformance,OrderDecisionConformance}.java
classpath="$classes:$classpath"
java -XX:ActiveProcessorCount=4 -Xmx1800m -cp "$classpath" CancellationRefreshConformance "$archives"
java -XX:ActiveProcessorCount=3 -Xmx1700m -cp "$classpath" ActivationConnectionReferencesConformance "$archives"
java -XX:ActiveProcessorCount=4 -Xmx1800m -cp "$classpath" ScheduleReservationConformance "$archives"
java -XX:ActiveProcessorCount=4 -Xmx1500m -cp "$classpath" WholeOrderCancellationConformance "$archives"
java -XX:ActiveProcessorCount=3 -Xmx1500m -cp "$classpath" OrderDecisionConformance "$archives"
bash verification/independent-clauses/time/run.sh "$archives" "$core_cpfile" --exported
java -XX:ActiveProcessorCount=4 -Xmx2400m -Dblue.packages.signedConformanceWaitSeconds=300 \
  -cp "$classpath" blue.core.CatalogOrderAttachmentConformance "$archives" "$source" "$mode"
```

Dla kontroli T03 dopisz `baseline` po ścieżce do archiwów. `timed-cancellation-service-refresh` używa źródła `service-only`, `timed-accept-alternative` oraz `timed-cancel-first` używają `scheduled-both`, `timed-payment-admission` działa na `service-only`, a `timed-reject-first` używa niedatowanego źródła `manual` z anulowaniem.
