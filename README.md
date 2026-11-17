# Doradca Hormozi dla Claude

Skill dla Claude, który odpowiada na pytania o firmę tak, jak zrobiłby to Alex Hormozi, ale z dowodami: każda rada ma źródło, czyli oznaczenie nagrania i minuty oraz link, pod którym można to sprawdzić.

> **Repozytorium prywatne.** Zawiera notatki z częściowo płatnych materiałów. Nie udostępniaj go dalej i nie zmieniaj widoczności na publiczną.

## Do czego służy

Opisujesz swoją firmę (co sprzedajesz, za ile, ilu masz klientów, skąd przychodzą), a Claude:

- stawia **diagnozę** i wskazuje główne ograniczenie firmy,
- liczy na **twoich liczbach**, a braki nazywa wprost,
- daje najwyżej trzy **zalecenia** z krokami i miernikiem sukcesu,
- osobno pokazuje, co mówi Hormozi (z cytowaniem), a co jest wnioskiem Claude dla twojej firmy,
- mówi, **gdzie Hormozi nie pasuje** (jego przykłady to głównie USA, usługi, siłownie, edukacja, oprogramowanie).

Tematy: oferta, ceny i podwyżki, pozyskiwanie klientów, sprzedaż i obiekcje, retencja i LTV, zatrudnianie, zarządzanie, skalowanie.

Tryby: **pytanie** (domyślny, konkretna sprawa), **diagnoza** (cała firma), **przegląd** (co zmieniło się od ostatnich zaleceń).

## Co jest w środku

| Zawartość | Opis |
|---|---|
| 1828 nagrań i lekcji | 4 kursy $100M (Offers, Leads, Money Models, Scaling), filmy YouTube, livestreamy, klipy, podcast The Game |
| 15 503 atomy wiedzy | pojedyncze reguły, liczby, taktyki, skrypty i przypadki, własnymi słowami, każdy z minutą nagrania |
| 299 przypadków | rozmowy Hormoziego z właścicielami firm, pogrupowane wg rodzaju działalności |
| playbook | metoda diagnozy, rejestr frameworków, zestawienie liczb, 17 stron tematów, lista luk (czego materiał nie obejmuje) |
| wyszukiwarka | jeden plik w czystym Pythonie, bez zależności |

**Czego tu nie ma:** transkrypcji ani tekstów kursów i książek. To wyłącznie notatki własnymi słowami. Pełne brzmienie sprawdzisz pod linkiem do nagrania (YouTube, podcast); materiały kursowe mają oznaczenie „materiał kursu, bez linku".

## Jak zacząć

Pełna instrukcja krok po kroku jest w [INSTRUKCJA.md](INSTRUKCJA.md). W skrócie:

### Aplikacja Claude (komputer lub przeglądarka)

1. Zbuduj zip poleceniem `./zbuduj_zip.sh` albo użyj gotowego `hormozi.zip`.
2. Ustawienia, Możliwości: włącz wykonywanie kodu i tworzenie plików.
3. W Skills wgraj `hormozi.zip` i włącz skill.
4. Zadaj pytanie w nowej rozmowie.

### Claude Code (terminal)

```bash
git clone https://github.com/TybuRak/hormozi-skill.git ~/hormozi-skill
mkdir -p ~/.claude/skills
ln -s ~/hormozi-skill/hormozi ~/.claude/skills/hormozi
```

Potem uruchom `claude` w folderze swojej firmy i wpisz `/hormozi` albo po prostu zapytaj. Aktualizacja: `cd ~/hormozi-skill && git pull`.

## Przykładowe pytania

- „Prowadzę studio fotograficzne. Sesja kosztuje 600 zł, marża ok. 60%, mam 20 klientów miesięcznie. Zrób diagnozę według Hormoziego."
- „Chcę podnieść ceny o 20%. Jak to zrobić wobec obecnych klientów?"
- „Jak zbudować ofertę, którą trudno odrzucić?"
- „Jeden klient daje mi większość przychodu. Co radzi Hormozi?"

Im więcej konkretnych liczb podasz, tym lepsza odpowiedź. Materiały są po angielsku, odpowiedzi dostaniesz po polsku.

## Wyszukiwarka

Skill sam z niej korzysta, ale można ją uruchomić ręcznie, żeby przeglądać bazę:

```bash
cd hormozi
python3 scripts/szukaj.py "raise prices existing customers" --k 5
python3 scripts/szukaj.py "one client most of revenue" --konsultacje
python3 scripts/szukaj.py "capacity constraint" --typ DECISION_RULE
python3 scripts/szukaj.py --doc YT-Gy-RmpRif-I --around 00:01:30
python3 scripts/szukaj.py --info
```

Wymaga tylko Pythona 3. Indeks (SQLite FTS5) buduje się sam przy pierwszym użyciu w ciągu kilku sekund i trafia do `.cache/` (poza repozytorium) albo do katalogu tymczasowego. Gdy FTS5 jest niedostępny, wyszukiwarka szuka w pamięci. Zapytania działają najlepiej po angielsku. Filtry: `--typ`, `--temat`, `--kolekcja`, `--od`, `--do`, `--k`, `--pelne`.

## Struktura

```text
hormozi-skill/
├── README.md             ten plik
├── INSTRUKCJA.md         instrukcja dla odbiorców (aplikacja Claude i Claude Code)
├── zbuduj_zip.sh         buduje hormozi.zip do wgrania w aplikacji Claude
└── hormozi/              właściwy skill (to się kopiuje do ~/.claude/skills/)
    ├── SKILL.md          instrukcje dla Claude: tryby, przebieg, zasady rzetelności, format odpowiedzi
    ├── playbook/         metoda, przypadki, frameworki, liczby, tematy, luki
    ├── ekstrakcje/       atomy wiedzy z jednego nagrania lub lekcji, plus _dokumenty.tsv (tytuły i linki)
    └── scripts/szukaj.py wyszukiwarka
```

## Zasady rzetelności wbudowane w skill

- Pod „Hormozi mówi" trafia tylko to, co atom stwierdza wprost. Wnioski i uogólnienia są oznaczone jako wnioskowanie Claude.
- Liczby i reguły, na których opiera się zalecenie, są sprawdzane w atomie pod cytowaniem i oznaczane jako pochodzące z notatki.
- Przy braku źródła Claude mówi to wprost i nie przypisuje Hormoziemu poglądów z pamięci.
- Przy sprzeczności źródeł wygrywają kursy i książki oraz nowsze nagrania.
- Rzeczy, których materiał nie obejmuje (np. produkcja na zamówienie, lokalne prawo i podatki), są wypisane w `playbook/GAPS.md`.

## Aktualizacja i budowanie zipa

Po zmianach w `hormozi/` uruchom `./zbuduj_zip.sh`. Skrypt tworzy `hormozi.zip` z folderem `hormozi/` w korzeniu, bez pamięci podręcznej. Zip jest w `.gitignore`, więc nie trafia do repozytorium.
