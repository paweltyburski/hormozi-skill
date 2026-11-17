# Skill hormozi (wersja do udostępniania, prywatna)

Doradca biznesowy dla Claude oparty na notatkach z materiałów Alexa Hormoziego. Folder `hormozi/` to gotowy skill (`SKILL.md`, `playbook/`, `ekstrakcje/`, `scripts/szukaj.py`). Instrukcja dla odbiorców: `INSTRUKCJA.md`.

Zawartość to wyłącznie notatki własnymi słowami (atomy wiedzy i zestawienia tematów). Nie ma tu transkrypcji ani bazy `index.sqlite`. Repozytorium ma być prywatne i dostępne tylko dla zaproszonych osób.

- Claude Code: sklonuj repozytorium i podlinkuj `hormozi/` do `~/.claude/skills/hormozi` (szczegóły w `INSTRUKCJA.md`).
- Aplikacja Claude: wgraj `hormozi.zip` (Ustawienia, Możliwości, Skills). Zip zbudujesz poleceniem `./zbuduj_zip.sh`.
- Wyszukiwarka: `python3 hormozi/scripts/szukaj.py "zapytanie"`; indeks buduje się sam przy pierwszym użyciu i nie trafia do repozytorium (`.gitignore`).
