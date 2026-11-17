# Binwalk GUI (PyQt6 dla Binwalk v2.4.3)

Nowoczesna aplikacja okienkowa w **PyQt6** dla narzędzia **Binwalk v2.4.3**, zaprojektowana do szybkiego rozpakowywania obrazów firmware (`.bin`, `.img`, `.fw`, `.rom`, `.ubi`, `.squashfs`, `.trx` i innych) oraz wygodnego korzystania ze **wszystkich 54 flag CLI** bez konieczności zapamiętywania składni terminala.

---

## Najważniejsze funkcje

- **Szybkie rozpakowywanie plików `.bin`**:
  - Dodawanie plików metodą **Drag & Drop** (na listę plików lub główne okno), przez przycisk **`Dodaj plik(i)...`** lub jako argumenty uruchomienia programu.
  - Zmiana kolejności plików (`W górę` / `W dół`) — szczególnie przydatna podczas binarnego porównywania plików (`-W`).
  - Przyciski szybkich akcji: **`Rozpakuj teraz (-e)`**, **`Skanuj sygnatury (-B)`**, **`Uruchom wybrane opcje`** oraz **`Stop`** (`SIGTERM`, a po 2 s `SIGKILL`).
- **Pełne pokrycie 54 opcji CLI Binwalk v2.4.3**:
  - 7 czytelnych zakładek tematycznych oraz **wyszukiwarka na żywo** filtrująca po krótkiej fladze (np. `-M`), długiej fladze (`--matryoshka`), nazwie, opisie i polu modelu wraz z licznikiem dopasowań na każdej zakładce.
  - Przełącznik trybu flag: krótkie (`-e`) vs długie (`--extract`).
  - Podgląd bezpiecznie zacytowanego polecenia CLI (`shlex.join`) w czasie rzeczywistym z przyciskiem **`Kopiuj komendę`** i **`Resetuj opcje`**.
  - Automatyczne wykrywanie binarki `binwalk` (`/usr/bin/binwalk`, `PATH`, `~/.local/bin/binwalk`) oraz możliwość wpisania własnej ścieżki.
- **Walidacja i ergonomia przed uruchomieniem**:
  - Podświetlanie błędnych wartości liczbowych (dziesiętnych i szesnastkowych `0x...` oraz zmiennoprzecinkowych z `.` lub `,`).
  - Ostrzeżenia bezpieczeństwa i spójności (np. dla `-1 / --preserve-symlinks`, `-c` bez `-f`, `-E` bez `-N`/`-J`).
  - Automatyczne tworzenie nieistniejącego katalogu docelowego `-C` podczas uruchamiania ekstrakcji (`-e` / `-D`), z walidacją czy ścieżka `-C` nie wskazuje na istniejący zwykły plik.
  - Bezpośrednie uruchomienie pomocy `binwalk -h` (`F1` lub menu `Akcje` / `Pomoc`) bez konieczności wybierania plików wejściowych i bez nadpisywania skonfigurowanych opcji.
- **Pasek menu i skróty klawiszowe**:
  - Menu **`Plik`**, **`Akcje`**, **`Widok`** i **`Pomoc`** (w tym dialog skrótów klawiszowych oraz `O programie...`).
- **Panel wyników (`Konsola wyjścia`, `Rozpakowane pliki`, `Wykres entropii`)**:
  - **Konsola wyjścia**: asynchroniczny strumień `stdout`/`stderr` (`QProcess` z `PYTHONUNBUFFERED=1`), konwersja kodów kolorów ANSI SGR na HTML (np. kolorowy diff `-W`), normalizacja CRLF, limit 20 000 linii w widoku konsoli, czyszczenie i zapis logu do pliku.
  - **Rozpakowane pliki**: wbudowany eksplorator drzewa katalogów (`QTreeView`) z automatycznym przełączaniem na nowo utworzony lub zmodyfikowany katalog `*.extracted`, czytelnym komunikatem i przyciskiem **`Utwórz katalog`** gdy wskazany folder `-C` jeszcze nie istnieje, otwieraniem elementów podwójnym kliknięciem, otwieraniem w menedżerze plików i kopiowaniem ścieżki.
  - **Wykres entropii**: automatyczne wykrywanie nowo zapisanych wykresów `.png` (np. przy `-E -J -N`), podgląd w oknie i otwieranie w domyślnej przeglądarce obrazów.

---

## Wymagania

- **Python**: `>= 3.10` (przetestowano na `/usr/bin/python3` — Python `3.13.5`)
- **PyQt6**: `>= 6.4`
- **Binwalk**: `v2.4.3` dostępny w systemie (np. `/usr/bin/binwalk`, w `PATH` lub `~/.local/bin/binwalk`)

---

## Instalacja i uruchamianie

### Bezpośrednio ze źródeł

```bash
cd /home/dev/Downloads/binwalkGui
/usr/bin/python3 main.py
```

Możesz także od razu otworzyć wybrane pliki binarne z linii poleceń:

```bash
/usr/bin/python3 main.py /sciezka/do/firmware.bin
```

Lub uruchomić jako moduł Pythona:

```bash
/usr/bin/python3 -m binwalk_gui.ui.main_window [plik1.bin plik2.bin ...]
```

### Instalacja pakietu (`pyproject.toml`)

```bash
pip install -e .
binwalk-gui [plik1.bin ...]
```

---

## Szybkie rozpakowywanie pliku `.bin` (krok po kroku)

1. Uruchom aplikację (`/usr/bin/python3 main.py`).
2. Przeciągnij plik `.bin` na okno aplikacji lub kliknij **`Dodaj plik(i)...`**.
3. Opcjonalnie w górnym pasku ustaw **`Folder docelowy (-C)`** (jeśli zostawisz puste pole, binwalk utworzy katalog `_<nazwa_pliku>.extracted` obok pliku `.bin`), zaznacz **`Rekurencyjnie (-M)`** lub **`Tylko wytnij (-z)`**.
4. Kliknij **`Rozpakuj teraz (-e)`**.
5. Po zakończeniu pracy:
   - log wykonania zobaczysz w zakładce **Konsola wyjścia**,
   - aplikacja automatycznie wskaże katalog `*.extracted` i przełączy widok na zakładkę **Rozpakowane pliki**.

---

## Pasek menu i skróty klawiszowe

Okno główne udostępnia menu **`Plik`**, **`Akcje`**, **`Widok`** i **`Pomoc`** oraz następujące skróty klawiszowe:

| Skrót | Akcja | Menu / Kontekst |
|---|---|---|
| `Ctrl+O` | Dodaj pliki `.bin`... | `Plik` / Lista plików |
| `Delete` | Usuń zaznaczony wpis z listy | Lista plików / Listy powtarzalne (`-D`, `-R`, `-m`, `-x`, `-y`) |
| `Ctrl+S` | Zapisz log konsoli... | `Plik` |
| `Ctrl+Q` | Zakończ aplikację | `Plik` |
| `F5` / `Ctrl+Return` / `Ctrl+Enter` | Rozpakuj teraz (`-e`) | `Akcje` |
| `F6` | Skanuj sygnatury (`-B`) | `Akcje` |
| `Ctrl+Shift+Return` / `Ctrl+Shift+Enter` | Uruchom wybrane opcje | `Akcje` |
| `Esc` | Zatrzymaj uruchomiony proces `binwalk` | `Akcje` |
| `F1` | Pokaż pomoc Binwalk CLI (`-h`) bez plików wejściowych | `Akcje` / `Pomoc` |
| `Ctrl+F` | Przejdź do wyszukiwarki opcji (`Esc` czyści filtr) | `Widok` / Wyszukiwarka |
| `Ctrl+L` | Wyczyść konsolę wyjścia | `Widok` |
| `Ctrl+Shift+C` | Kopiuj komendę CLI do schowka | `Widok` |
| `Ctrl+R` | Resetuj wszystkie opcje | `Widok` |
| `Ctrl+1` / `Ctrl+2` / `Ctrl+3` | Przełącz zakładkę wyników (`Konsola wyjścia` / `Rozpakowane pliki` / `Wykres entropii`) | `Widok` |

---

## Gotowe presety

Menu **`Preset:`** w górnym pasku pozwala jednym kliknięciem ustawić typowe zestawy flag (z zachowaniem wybranych plików docelowych, ścieżki do `binwalk`, trybu długich flag i folderu `-C`):

| Preset | Ustawiane flagi | Zastosowanie |
|---|---|---|
| `Szybkie rozpakowanie (-e)` | `-e` | Standardowe wydobycie znanych archiwów i systemów plików |
| `Głębokie rozpakowanie (-e -M)` | `-e -M` | Rekurencyjne rozpakowywanie zagnieżdżonych kontenerów (Matryoshka) |
| `Wycięcie surowe bez dekompresji (-e -z)` | `-e -z` | Wycięcie samych fragmentów binarnych bez uruchamiania zewnętrznych ekstraktorów |
| `Skan sygnatur (-B)` | `-B` | Rozpoznanie sygnatur bez zapisu plików na dysk |
| `Analiza entropii + zapis PNG (-E -J -N)` | `-E -J -N` | Obliczenie entropii i zapis wykresu `.png` bez otwierania osobnego okna matplotlib |
| `Porównanie binarne / Hexdump (-W)` | `-W` | Hexdump jednego pliku lub kolorowy diff wielu plików |
| `Dezasemblacja architektury (-Y)` | `-Y` | Identyfikacja architektury CPU (wymaga binwalk z modułem `capstone`) |
| `Kompresja surowa (-X -Z)` | `-X -Z` | Skan surowych strumieni Deflate oraz LZMA |
| `Wyczyść wszystkie opcje` | *(brak)* | Zeruje wszystkie flagi opcji, zachowując pliki i ścieżkę binarki |

---

## Pełna dokumentacja wszystkich 54 flag CLI i plików docelowych

### Pliki docelowe (`target_files`)

Na końcu polecenia `binwalk` aplikacja dołącza listę wybranych plików wejściowych:

```text
binwalk [OPCJE] [PLIK1] [PLIK2] ...
```

- Pliki mogą mieć dowolne rozszerzenie (`.bin`, `.img`, `.fw`, `.rom`, `.ubi`, `.squashfs`, `.trx` i inne).
- Uruchomienie bez wybranych plików wejściowych jest dozwolone wyłącznie wtedy, gdy włączona jest opcja **`-h` / `--help`**.

### 1. Rozpakowywanie (`extraction` — 12 opcji)

| Krótka | Długa | Typ wartości | Opis |
|---|---|---|---|
| `-e` | `--extract` | przełącznik | Automatycznie wycina i rozpakowuje rozpoznane typy plików |
| `-M` | `--matryoshka` | przełącznik | Rekurencyjnie skanuje i rozpakowuje nowo wydobyte pliki |
| `-d` | `--depth` | liczba (dec / `0x...`) | Limit głębokości rekurencji dla trybu Matryoshka (domyślnie w binwalk: `8`) |
| `-C` | `--directory` | katalog | Własny katalog docelowy dla rozpakowanych plików i folderów |
| `-D` | `--dd` | lista (powtarzalna) | Reguły wycinania i uruchamiania w formacie `<typ[:rozszerzenie[:komenda]]>`, np. `squashfs:sqsh:unsquashfs %e` lub `gzip:gz` |
| `-j` | `--size` | liczba (dec / `0x...`) | Maksymalny rozmiar w bajtach każdego pojedynczego wyodrębnionego pliku |
| `-n` | `--count` | liczba (dec / `0x...`) | Maksymalna liczba wyodrębnionych plików |
| `-0` | `--run-as` | tekst | Uruchamia zewnętrzne ekstraktory z uprawnieniami wskazanego użytkownika |
| `-1` | `--preserve-symlinks` | przełącznik | Nie oczyszcza dowiązań symbolicznych wskazujących poza katalog ekstrakcji *(ostrzeżenie bezpieczeństwa)* |
| `-r` | `--rm` | przełącznik | Usuwa wycięte pliki pośrednie po zakończeniu działania ekstraktora |
| `-z` | `--carve` | przełącznik | Tylko wycina fragmenty binarne bez uruchamiania zewnętrznych dekompresorów |
| `-V` | `--subdirs` | przełącznik | Rozpakowuje zawartość do podfolderów nazwanych według offsetu znaleziska |

### 2. Skan sygnatur (`signature` — 8 opcji)

| Krótka | Długa | Typ wartości | Opis |
|---|---|---|---|
| `-B` | `--signature` | przełącznik | Skanuje pliki w poszukiwaniu znanych sygnatur nagłówków i systemów plików |
| `-A` | `--opcodes` | przełącznik | Wyszukuje popularne sekwencje instrukcji wykonywalnych CPU |
| `-R` | `--raw` | lista (powtarzalna) | Skanuje pod kątem własnej sekwencji bajtów (np. `\x1f\x8b\x08` lub ciąg ASCII) |
| `-m` | `--magic` | lista plików (powtarzalna) | Ścieżka do niestandardowego pliku sygnatur `libmagic` |
| `-b` | `--dumb` | przełącznik | Wyłącza heurystyki *smart signature keywords* |
| `-I` | `--invalid` | przełącznik | Wyświetla również wyniki odfiltrowane normalnie jako *false-positive* |
| `-x` | `--exclude` | lista (powtarzalna) | Wyklucza wyniki, których opis zawiera podany ciąg znaków |
| `-y` | `--include` | lista (powtarzalna) | Pokazuje wyłącznie wyniki pasujące do podanego ciągu znaków |

### 3. Entropia (`entropy` — 7 opcji)

| Krótka | Długa | Typ wartości | Opis |
|---|---|---|---|
| `-E` | `--entropy` | przełącznik | Analizuje rozkład entropii bajtów w pliku |
| `-F` | `--fast` | przełącznik | Używa szybszego, mniej szczegółowego algorytmu obliczania entropii (`zlib`) |
| `-J` | `--save` | przełącznik | Generuje i zapisuje wykres entropii jako plik `.png` |
| `-Q` | `--nlegend` | przełącznik | Pomija legendę na wygenerowanym wykresie entropii |
| `-N` | `--nplot` | przełącznik | Nie otwiera interaktywnego okna wykresu (przydatne z `-J` lub w trybie tekstowym) |
| `-H` | `--high` | liczba zmiennoprzecinkowa | Górny próg wyzwalania entropii (`0.00`–`1.00`, domyślnie w binwalk: `0.95`) |
| `-L` | `--low` | liczba zmiennoprzecinkowa | Dolny próg wyzwalania entropii (`0.00`–`1.00`, domyślnie w binwalk: `0.85`) |

### 4. Diff / Hexdump (`hexdiff` — 6 opcji)

| Krótka | Długa | Typ wartości | Opis |
|---|---|---|---|
| `-W` | `--hexdump` | przełącznik | Wyświetla zrzut szesnastkowy jednego pliku lub porównanie różnic wielu plików |
| `-G` | `--green` | przełącznik | Pokazuje wyłącznie linie z bajtami identycznymi we wszystkich plikach |
| `-i` | `--red` | przełącznik | Pokazuje wyłącznie linie z bajtami różnymi między wszystkimi plikami |
| `-U` | `--blue` | przełącznik | Pokazuje wyłącznie linie z bajtami różnymi tylko w części plików |
| `-u` | `--similar` | przełącznik | Wyświetla wyłącznie linie identyczne we wszystkich plikach |
| `-w` | `--terse` | przełącznik | Porównuje wszystkie pliki, ale drukuje hexdump wyłącznie pierwszego pliku |

### 5. Kompresja surowa (`compression` — 4 opcje)

| Krótka | Długa | Typ wartości | Opis |
|---|---|---|---|
| `-X` | `--deflate` | przełącznik | Skanuje surowe strumienie kompresji Deflate bez nagłówków kontenera |
| `-Z` | `--lzma` | przełącznik | Skanuje surowe strumienie kompresji LZMA |
| `-P` | `--partial` | przełącznik | Wykonuje płytsze, ale znacznie szybsze skanowanie kompresji surowej |
| `-S` | `--stop` | przełącznik | Kończy skanowanie po znalezieniu pierwszego poprawnego strumienia |

### 6. Dezasemblacja (`disasm` — 3 opcje)

| Krótka | Długa | Typ wartości | Opis |
|---|---|---|---|
| `-Y` | `--disasm` | przełącznik | Identyfikuje architekturę CPU na podstawie kodu maszynowego (wymaga `capstone`) |
| `-T` | `--minsn` | liczba (dec / `0x...`) | Minimalna liczba kolejnych poprawnych instrukcji (domyślnie: `500`) |
| `-k` | `--continue` | przełącznik | Nie przerywa skanowania dezasemblacji po pierwszym trafieniu |

### 7. Ogólne (`general` — 14 opcji)

| Krótka | Długa | Typ wartości | Opis |
|---|---|---|---|
| `-l` | `--length` | liczba (dec / `0x...`) | Liczba bajtów do przeskanowania |
| `-o` | `--offset` | liczba (dec / `0x...`) | Offset początkowy skanu |
| `-O` | `--base` | liczba (dec / `0x...`) | Stały adres bazowy dodawany do wszystkich wyświetlanych offsetów |
| `-K` | `--block` | liczba (dec / `0x...`) | Rozmiar bloku odczytu i analizy |
| `-g` | `--swap` | liczba (dec / `0x...`) | Odwraca kolejność bajtów (*endianness swap*) w blokach po N bajtów przed skanem |
| `-f` | `--log` | plik zapisu | Zapisuje wynik działania binwalka do wskazanego pliku |
| `-c` | `--csv` | przełącznik | Zapisuje wyniki w formacie CSV (używane z `-f / --log`) |
| `-t` | `--term` | przełącznik | Dopasowuje formatowanie szerokości kolumn do terminala |
| `-q` | `--quiet` | przełącznik | Tryb cichy — wycisza standardowe wyjście `stdout` |
| `-v` | `--verbose` | przełącznik | Tryb szczegółowy — włącza rozszerzone komunikaty diagnostyczne |
| `-a` | `--finclude` | tekst (regex) | Skanuje wyłącznie pliki o nazwach pasujących do wyrażenia regularnego |
| `-p` | `--fexclude` | tekst (regex) | Pomija pliki o nazwach pasujących do wyrażenia regularnego |
| `-s` | `--status` | liczba (dec / `0x...`) | Uruchamia lokalny serwer TCP raportujący postęp na podanym porcie |
| `-h` | `--help` | przełącznik | Wyświetla pełną pomoc CLI używanej binarki `binwalk` |

---

## Testy i weryfikacja

Projekt używa standardowego modułu `unittest`. Testy UI działają również w trybie bezekranowym dzięki `QT_QPA_PLATFORM=offscreen`:

```bash
QT_QPA_PLATFORM=offscreen /usr/bin/python3 -m unittest discover -s tests -v
```

Sprawdzenie składni i kompilacji bajtkodu wszystkich plików Pythona:

```bash
/usr/bin/python3 -m compileall binwalk_gui tests main.py
```

### Zakres testów

- [`tests/test_command_builder.py`](tests/test_command_builder.py): weryfikacja pokrycia wszystkich 54 flag CLI (krótkich i długich), powtarzalnych opcji (`-D`, `-x`, `-y`), parsowania liczb `dec`/`hex`/`float`, walidacji błędów i ostrzeżeń, działania presetów oraz wyznaczania katalogu roboczego.
- [`tests/test_ansi_and_integration.py`](tests/test_ansi_and_integration.py): testy konwertera `ansi_to_html` / `strip_ansi`, prawdziwego uruchomienia `binwalk -e` na syntetycznym pliku `.bin` z osadzonym strumieniem `gzip`, startu okna `MainWindow` w trybie `offscreen` oraz asynchronicznego wykonania w `BinwalkRunner` (`QProcess`).
- [`tests/test_ui_shortcuts_and_edge_cases.py`](tests/test_ui_shortcuts_and_edge_cases.py): testy skrótów klawiszowych i paska menu, uruchamiania `-h` bez plików wejściowych, walidacji i paska nieistniejącego katalogu `-C` w `ResultsViewWidget`, przełączania zakładek wyników, kopiowania komendy, resetu presetów, wyszukiwarki oraz stanów przycisków w `FileDropListWidget`.

---

## Konfiguracja VS Code

Repozytorium zawiera gotową konfigurację dla Visual Studio Code w katalogu `.vscode/`:

- `.vscode/settings.json` — interpreter `/usr/bin/python3` oraz wykrywanie testów `unittest` w katalogu `tests/`.
- `.vscode/launch.json` — profile uruchamiania i debugowania: **`Run Binwalk GUI`** (`main.py`) oraz **`Run Unit Tests`** (`unittest discover -s tests -v` z `QT_QPA_PLATFORM=offscreen`).
- `.vscode/tasks.json` — domyślne zadanie testowe **`Run Tests offscreen`**.

---

## Struktura projektu

```text
binwalkGui/
├── main.py                              # Punkt wejścia aplikacji (run_app)
├── pyproject.toml                       # Konfiguracja pakietu Python i skryptu binwalk-gui
├── README.md                            # Dokumentacja projektu
├── .gitignore                           # Ignorowane artefakty Python/PyQt6/Binwalk
├── .vscode/
│   ├── launch.json                      # Konfiguracje debugowania GUI i testów
│   ├── settings.json                    # Interpreter Pythona i unittest
│   └── tasks.json                       # Zadanie testowe offscreen
├── binwalk_gui/
│   ├── __init__.py                      # Metadane pakietu i wersja
│   ├── models.py                        # Definicje 54 flag OPTION_SPECS, BinwalkOptions i PRESETS
│   ├── command_builder.py               # Wykrywanie binwalka, walidacja, budowanie argv i katalog roboczy
│   ├── runner.py                        # Asynchroniczny BinwalkRunner (QProcess) i wykrywanie artefaktów
│   ├── ansi.py                          # Konwersja kodów ANSI SGR na HTML i strip_ansi
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py               # Główne okno, pasek menu, skróty, szybkie akcje, podgląd CLI, ciemny motyw
│       ├── option_tabs.py               # 7 zakładek opcji CLI i wyszukiwarka na żywo
│       ├── results_view.py              # Konsola wyjścia, drzewo rozpakowanych plików i wykres PNG
│       └── widgets.py                   # FileDropListWidget, PathPicker, ValidatedLineEdit, RepeatableListEditor
└── tests/
    ├── test_command_builder.py          # Testy jednostkowe opcji, walidacji i budowania poleceń
    ├── test_ansi_and_integration.py     # Testy ANSI, integracji z binwalk CLI i PyQt6 offscreen
    └── test_ui_shortcuts_and_edge_cases.py # Testy menu, skrótów klawiszowych i przypadków brzegowych UI
```
