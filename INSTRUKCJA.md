# Doradca Hormozi: instrukcja

Doradca biznesowy dla Claude, oparty na kursach, książkach, filmach i podcaście Alexa Hormoziego. Zadajesz pytanie o swoją firmę (oferta, ceny, klienci, sprzedaż, zatrudnianie, wzrost), a Claude odpowiada na Twoich liczbach i podaje, skąd pochodzi każda rada, razem z linkiem do minuty nagrania.

Co jest w środku: notatki własnymi słowami z ok. 1800 nagrań i lekcji (reguły, liczby, taktyki, przypadki) oraz zestawienia tematów. Czego nie ma: pełnych transkrypcji ani tekstów kursów i książek. Materiały Hormoziego są częściowo płatne, więc ta paczka jest tylko dla Ciebie. Nie przesyłaj jej dalej i nie wrzucaj do internetu.

Materiały są po angielsku. Odpowiedzi Claude dostaniesz po polsku.

## Wariant A: aplikacja Claude (komputer lub przeglądarka)

Potrzebujesz pliku `hormozi.zip`, który dostałeś od Pawła. Nie rozpakowuj go.

1. Otwórz Claude i wejdź w Ustawienia, potem Możliwości (po angielsku: Settings, Capabilities).
2. Włącz opcję wykonywania kodu i tworzenia plików (Code execution and file creation). Bez niej wyszukiwarka w paczce nie ruszy.
3. W tym samym miejscu znajdź Skills (Umiejętności) i wybierz dodanie nowego skilla przez wgranie pliku. Wskaż `hormozi.zip`.
4. Gdy skill pojawi się na liście, upewnij się, że jest włączony (przełącznik).
5. Zacznij nową rozmowę i zadaj pytanie. Pierwsze użycie trwa dłużej, bo Claude buduje wtedy indeks wyszukiwania (kilka sekund).

Nazwy w menu mogą się trochę różnić w zależności od wersji aplikacji. Jeśli w ogóle nie widzisz Skills, ta funkcja nie jest jeszcze dostępna w Twoim planie lub wersji: napisz do Pawła.

Przykładowe pytania (podstaw swoje liczby):

1. „Prowadzę [rodzaj firmy]. Sprzedaję [co] za [cena], marża ok. [X]%. Miesięcznie mam [N] klientów. Zrób diagnozę mojej firmy według Hormoziego i powiedz, co jest głównym ograniczeniem.”
2. „Chcę podnieść ceny o 20%. Jak to zrobić wobec obecnych klientów i co mówi o tym Hormozi?”
3. „Jak zbudować ofertę, którą trudno odrzucić? Moja obecna oferta to: [opis].”
4. „Skąd brać nowych klientów, jeśli mam budżet [kwota] miesięcznie i sprzedaję [co]?”
5. „Mam jednego klienta, który przynosi większość przychodu. Co radzi Hormozi w takiej sytuacji?”
6. „Kiedy zatrudnić pierwszą osobę do sprzedaży i jak ją rozliczać?”

Wskazówki: im więcej konkretnych liczb podasz (ceny, marże, liczba klientów, skąd przychodzą, ile wydajesz na reklamę), tym lepsza odpowiedź. Claude ma prawo dopytać. Przy każdej poradzie zobaczysz, co jest słowami Hormoziego (z linkiem do nagrania), a co jest wnioskiem Claude dla Twojej firmy. Liczby z notatek warto sprawdzić w nagraniu pod linkiem.

## Wariant B: Claude Code (terminal)

Potrzebujesz Pythona 3 (sprawdź: `python3 --version`; na Windowsie bywa `python`). Nic się nie instaluje.

Opcja 1, z pliku zip:

```bash
mkdir -p ~/.claude/skills
unzip hormozi.zip -d ~/.claude/skills/
ls ~/.claude/skills/hormozi/SKILL.md
```

Opcja 2, z prywatnego repozytorium na GitHubie (łatwiejsze aktualizacje). Paweł zaprasza Cię do repozytorium, a potem:

```bash
git clone https://github.com/TybuRak/hormozi-skill.git ~/hormozi-skill
mkdir -p ~/.claude/skills
ln -s ~/hormozi-skill/hormozi ~/.claude/skills/hormozi
```

Aktualizacja później: `cd ~/hormozi-skill && git pull`. Na Windowsie zamiast `ln -s` skopiuj folder `hormozi` do `%USERPROFILE%\.claude\skills\`.

Użycie: uruchom `claude` w folderze swojej firmy lub projektu, wpisz `/hormozi` albo po prostu zapytaj, np. „co zrobiłby Hormozi z moim cennikiem?”. Tryby: pytanie (domyślny), diagnoza (cała firma), przegląd (co się zmieniło od ostatnich zaleceń). Jeśli w folderze jest plik `CLAUDE.md` albo opis firmy, doradca go przeczyta.

Wyszukiwarkę można też odpalić ręcznie, żeby przeglądać materiał samemu:

```bash
cd ~/.claude/skills/hormozi
python3 scripts/szukaj.py "raise prices existing customers" --k 5
python3 scripts/szukaj.py --info
```

## Gdy coś nie działa

1. Skill się nie pojawia: sprawdź, czy plik `SKILL.md` leży bezpośrednio w `hormozi/` (nie w `hormozi/hormozi/`), i uruchom nową rozmowę.
2. Brak wyników wyszukiwania: zapytania działają najlepiej po angielsku i w krótkich frazach (np. „price increase”, „lead getters”).
3. Błąd o braku Pythona lub brak możliwości uruchamiania kodu: w aplikacji Claude włącz wykonywanie kodu (Wariant A, krok 2); w terminalu zainstaluj Pythona 3.
4. Pierwsze zapytanie trwa kilka sekund dłużej: to jednorazowe budowanie indeksu.
