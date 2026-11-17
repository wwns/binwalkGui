"""Model opcji Binwalk v2.4.3, metadane flag CLI oraz gotowe presety."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Literal

OptionKind = Literal[
    "bool",
    "int_hex",
    "float",
    "str",
    "file",
    "dir",
    "save_file",
    "list",
    "list_file",
]


@dataclass(frozen=True)
class OptionSpec:
    """Metadane pojedynczej opcji CLI narzędzia binwalk."""

    field_name: str
    short_flag: str
    long_flag: str
    category: str
    kind: OptionKind
    label: str
    tooltip: str
    placeholder: str = ""
    warning: str = ""


CATEGORIES: tuple[tuple[str, str], ...] = (
    ("extraction", "Rozpakowywanie"),
    ("signature", "Skan sygnatur"),
    ("entropy", "Entropia"),
    ("hexdiff", "Diff / Hexdump"),
    ("compression", "Kompresja surowa"),
    ("disasm", "Dezasemblacja"),
    ("general", "Ogólne"),
)


OPTION_SPECS: tuple[OptionSpec, ...] = (
    # --- Extraction Options (-e, -D, -M, -d, -C, -j, -n, -0, -1, -r, -z, -V) ---
    OptionSpec(
        field_name="extract",
        short_flag="-e",
        long_flag="--extract",
        category="extraction",
        kind="bool",
        label="Automatyczne rozpakowanie (-e / --extract)",
        tooltip="Automatycznie wycina i rozpakowuje rozpoznane typy plików.",
    ),
    OptionSpec(
        field_name="matryoshka",
        short_flag="-M",
        long_flag="--matryoshka",
        category="extraction",
        kind="bool",
        label="Rekurencyjne rozpakowanie / Matryoshka (-M / --matryoshka)",
        tooltip="Rekurencyjnie skanuje i rozpakowuje nowo wydobyte pliki.",
    ),
    OptionSpec(
        field_name="depth",
        short_flag="-d",
        long_flag="--depth",
        category="extraction",
        kind="int_hex",
        label="Maksymalna głębokość rekurencji (-d / --depth)",
        tooltip="Limit głębokości rekurencji dla trybu Matryoshka (domyślnie w binwalk: 8).",
        placeholder="np. 8",
    ),
    OptionSpec(
        field_name="directory",
        short_flag="-C",
        long_flag="--directory",
        category="extraction",
        kind="dir",
        label="Katalog docelowy rozpakowania (-C / --directory)",
        tooltip="Własny folder docelowy dla rozpakowanych plików i katalogów.",
        placeholder="Domyślnie: obok pliku .bin",
    ),
    OptionSpec(
        field_name="dd_rules",
        short_flag="-D",
        long_flag="--dd",
        category="extraction",
        kind="list",
        label="Reguły wycinania i uruchamiania (--dd / -D)",
        tooltip="Format: <typ[:rozszerzenie[:komenda]]>, np. 'squashfs:sqsh:unsquashfs %e' lub 'gzip:gz'. Można dodać wiele reguł.",
        placeholder="typ[:ext[:cmd]] np. zip:zip",
    ),
    OptionSpec(
        field_name="max_size",
        short_flag="-j",
        long_flag="--size",
        category="extraction",
        kind="int_hex",
        label="Limit rozmiaru pliku wyjściowego (-j / --size)",
        tooltip="Maksymalny rozmiar w bajtach każdego pojedynczego wyodrębnionego pliku (np. 10485760 lub 0x100000).",
        placeholder="bajty (dec lub 0x...)",
    ),
    OptionSpec(
        field_name="max_count",
        short_flag="-n",
        long_flag="--count",
        category="extraction",
        kind="int_hex",
        label="Limit liczby plików (-n / --count)",
        tooltip="Maksymalna liczba wyodrębnionych plików.",
        placeholder="np. 100",
    ),
    OptionSpec(
        field_name="run_as",
        short_flag="-0",
        long_flag="--run-as",
        category="extraction",
        kind="str",
        label="Uruchom ekstraktory jako użytkownik (-0 / --run-as)",
        tooltip="Uruchamia zewnętrzne narzędzia rozpakowujące z uprawnieniami wskazanego użytkownika.",
        placeholder="nazwa użytkownika",
    ),
    OptionSpec(
        field_name="preserve_symlinks",
        short_flag="-1",
        long_flag="--preserve-symlinks",
        category="extraction",
        kind="bool",
        label="Zachowaj niebezpieczne dowiązania symboliczne (-1 / --preserve-symlinks)",
        tooltip="Nie oczyszcza symlinków wskazujących poza katalog ekstrakcji.",
        warning="Uwaga bezpieczeństwa: symlinki wskazujące poza katalog docelowy mogą stwarzać ryzyko zapisu/odczytu poza folderem ekstrakcji.",
    ),
    OptionSpec(
        field_name="rm_carved",
        short_flag="-r",
        long_flag="--rm",
        category="extraction",
        kind="bool",
        label="Usuń pliki pośrednie po rozpakowaniu (-r / --rm)",
        tooltip="Usuwa wycięte pliki tymczasowe po zakończeniu działania ekstraktora.",
    ),
    OptionSpec(
        field_name="carve",
        short_flag="-z",
        long_flag="--carve",
        category="extraction",
        kind="bool",
        label="Tylko wytnij dane bez uruchamiania ekstraktorów (-z / --carve)",
        tooltip="Wycina fragmenty binarne do plików bez uruchamiania zewnętrznych dekompresorów.",
    ),
    OptionSpec(
        field_name="subdirs",
        short_flag="-V",
        long_flag="--subdirs",
        category="extraction",
        kind="bool",
        label="Podkatalogi nazwane offsetem (-V / --subdirs)",
        tooltip="Rozpakowuje zawartość do podfolderów nazwanych według offsetu znaleziska.",
    ),
    # --- Signature Scan Options (-B, -R, -A, -m, -b, -I, -x, -y) ---
    OptionSpec(
        field_name="signature",
        short_flag="-B",
        long_flag="--signature",
        category="signature",
        kind="bool",
        label="Skan sygnatur plików (-B / --signature)",
        tooltip="Skanuje plik(i) w poszukiwaniu znanych sygnatur nagłówków i systemów plików.",
    ),
    OptionSpec(
        field_name="opcodes",
        short_flag="-A",
        long_flag="--opcodes",
        category="signature",
        kind="bool",
        label="Skan kodów maszynowych / opcodes (-A / --opcodes)",
        tooltip="Wyszukuje popularne sekwencje instrukcji wykonywalnych CPU.",
    ),
    OptionSpec(
        field_name="raw_bytes",
        short_flag="-R",
        long_flag="--raw",
        category="signature",
        kind="list",
        label="Szukaj własnej sekwencji bajtów (-R / --raw)",
        tooltip="Skanuje pliki pod kątem podanej sekwencji bajtów (np. \\xaa\\xbb lub tekst). Obsługuje wiele wpisów.",
        placeholder="np. \\x1f\\x8b\\x08 lub ciąg ASCII",
    ),
    OptionSpec(
        field_name="magic_files",
        short_flag="-m",
        long_flag="--magic",
        category="signature",
        kind="list_file",
        label="Własny plik magic (-m / --magic)",
        tooltip="Ścieżka do niestandardowego pliku sygnatur libmagic. Można dodać wiele plików.",
        placeholder="ścieżka do pliku magic",
    ),
    OptionSpec(
        field_name="dumb",
        short_flag="-b",
        long_flag="--dumb",
        category="signature",
        kind="bool",
        label="Wyłącz inteligentne słowa kluczowe (-b / --dumb)",
        tooltip="Wyłącza heurystyki smart signature keywords podczas skanowania.",
    ),
    OptionSpec(
        field_name="invalid",
        short_flag="-I",
        long_flag="--invalid",
        category="signature",
        kind="bool",
        label="Pokaż wyniki oznaczone jako nieprawidłowe (-I / --invalid)",
        tooltip="Wyświetla również trafienia odfiltrowane normalnie jako false-positive.",
    ),
    OptionSpec(
        field_name="exclude_filters",
        short_flag="-x",
        long_flag="--exclude",
        category="signature",
        kind="list",
        label="Wyklucz wyniki pasujące do tekstu (-x / --exclude)",
        tooltip="Ukrywa trafienia, których opis zawiera podany ciąg znaków. Można dodać wiele filtrów.",
        placeholder="np. copyright lub JFFS2",
    ),
    OptionSpec(
        field_name="include_filters",
        short_flag="-y",
        long_flag="--include",
        category="signature",
        kind="list",
        label="Pokaż tylko wyniki pasujące do tekstu (-y / --include)",
        tooltip="Ogranicza wyniki wyłącznie do wpisów pasujących do podanego ciągu. Można dodać wiele filtrów.",
        placeholder="np. squashfs lub ELF",
    ),
    # --- Entropy Options (-E, -F, -J, -Q, -N, -H, -L) ---
    OptionSpec(
        field_name="entropy",
        short_flag="-E",
        long_flag="--entropy",
        category="entropy",
        kind="bool",
        label="Oblicz entropię pliku (-E / --entropy)",
        tooltip="Analizuje rozkład entropii bajtów w pliku (pomocne przy wykrywaniu szyfrowania i kompresji).",
    ),
    OptionSpec(
        field_name="fast_entropy",
        short_flag="-F",
        long_flag="--fast",
        category="entropy",
        kind="bool",
        label="Szybsza, mniej szczegółowa analiza (-F / --fast)",
        tooltip="Używa szybszego algorytmu obliczania entropii (zlib).",
    ),
    OptionSpec(
        field_name="save_plot",
        short_flag="-J",
        long_flag="--save",
        category="entropy",
        kind="bool",
        label="Zapisz wykres entropii jako PNG (-J / --save)",
        tooltip="Generuje i zapisuje wykres entropii w pliku .png.",
    ),
    OptionSpec(
        field_name="nlegend",
        short_flag="-Q",
        long_flag="--nlegend",
        category="entropy",
        kind="bool",
        label="Ukryj legendę na wykresie (-Q / --nlegend)",
        tooltip="Pomija legendę na wygenerowanym wykresie entropii.",
    ),
    OptionSpec(
        field_name="nplot",
        short_flag="-N",
        long_flag="--nplot",
        category="entropy",
        kind="bool",
        label="Nie otwieraj okna wykresu (-N / --nplot)",
        tooltip="Pomija generowanie interaktywnego okna wykresu (przydatne z -J lub w trybie tekstowym).",
    ),
    OptionSpec(
        field_name="entropy_high",
        short_flag="-H",
        long_flag="--high",
        category="entropy",
        kind="float",
        label="Próg narastający entropii (-H / --high)",
        tooltip="Ustawia górny próg wyzwalania entropii (domyślnie w binwalk: 0.95).",
        placeholder="0.00 - 1.00 (dom. 0.95)",
    ),
    OptionSpec(
        field_name="entropy_low",
        short_flag="-L",
        long_flag="--low",
        category="entropy",
        kind="float",
        label="Próg opadający entropii (-L / --low)",
        tooltip="Ustawia dolny próg wyzwalania entropii (domyślnie w binwalk: 0.85).",
        placeholder="0.00 - 1.00 (dom. 0.85)",
    ),
    # --- Binary Diffing Options (-W, -G, -i, -U, -u, -w) ---
    OptionSpec(
        field_name="hexdump",
        short_flag="-W",
        long_flag="--hexdump",
        category="hexdiff",
        kind="bool",
        label="Hexdump / porównanie binarne plików (-W / --hexdump)",
        tooltip="Wyświetla zrzut szesnastkowy pojedynczego pliku lub porównanie różnic wielu plików.",
    ),
    OptionSpec(
        field_name="diff_green",
        short_flag="-G",
        long_flag="--green",
        category="hexdiff",
        kind="bool",
        label="Tylko bajty identyczne we wszystkich plikach (-G / --green)",
        tooltip="Pokazuje wyłącznie linie zawierające bajty identyczne we wszystkich porównywanych plikach.",
    ),
    OptionSpec(
        field_name="diff_red",
        short_flag="-i",
        long_flag="--red",
        category="hexdiff",
        kind="bool",
        label="Tylko bajty różne we wszystkich plikach (-i / --red)",
        tooltip="Pokazuje wyłącznie linie zawierające bajty różniące się między wszystkimi plikami.",
    ),
    OptionSpec(
        field_name="diff_blue",
        short_flag="-U",
        long_flag="--blue",
        category="hexdiff",
        kind="bool",
        label="Tylko bajty różne w części plików (-U / --blue)",
        tooltip="Pokazuje wyłącznie linie, w których bajty różnią się tylko pomiędzy wybranymi plikami.",
    ),
    OptionSpec(
        field_name="diff_similar",
        short_flag="-u",
        long_flag="--similar",
        category="hexdiff",
        kind="bool",
        label="Wyświetl tylko identyczne linie (-u / --similar)",
        tooltip="Wyświetla wyłącznie linie jednakowe pomiędzy wszystkimi plikami.",
    ),
    OptionSpec(
        field_name="diff_terse",
        short_flag="-w",
        long_flag="--terse",
        category="hexdiff",
        kind="bool",
        label="Zwięzły diff — hexdump tylko pierwszego pliku (-w / --terse)",
        tooltip="Porównuje wszystkie pliki, ale drukuje hexdump wyłącznie pierwszego pliku.",
    ),
    # --- Raw Compression Options (-X, -Z, -P, -S) ---
    OptionSpec(
        field_name="deflate",
        short_flag="-X",
        long_flag="--deflate",
        category="compression",
        kind="bool",
        label="Skanuj surowe strumienie Deflate (-X / --deflate)",
        tooltip="Szuka surowych strumieni kompresji deflate nawet bez nagłówków kontenera.",
    ),
    OptionSpec(
        field_name="lzma",
        short_flag="-Z",
        long_flag="--lzma",
        category="compression",
        kind="bool",
        label="Skanuj surowe strumienie LZMA (-Z / --lzma)",
        tooltip="Szuka surowych strumieni kompresji LZMA.",
    ),
    OptionSpec(
        field_name="partial",
        short_flag="-P",
        long_flag="--partial",
        category="compression",
        kind="bool",
        label="Skan powierzchowny / szybszy (-P / --partial)",
        tooltip="Wykonuje płytsze, ale znacznie szybsze skanowanie kompresji surowej.",
    ),
    OptionSpec(
        field_name="stop_first",
        short_flag="-S",
        long_flag="--stop",
        category="compression",
        kind="bool",
        label="Zatrzymaj po pierwszym wyniku (-S / --stop)",
        tooltip="Kończy skanowanie kompresji po znalezieniu pierwszego poprawnego strumienia.",
    ),
    # --- Disassembly Scan Options (-Y, -T, -k) ---
    OptionSpec(
        field_name="disasm",
        short_flag="-Y",
        long_flag="--disasm",
        category="disasm",
        kind="bool",
        label="Rozpoznaj architekturę CPU (Capstone) (-Y / --disasm)",
        tooltip="Identyfikuje architekturę procesora na podstawie kodu maszynowego (wymaga binwalk z modułem capstone).",
    ),
    OptionSpec(
        field_name="minsn",
        short_flag="-T",
        long_flag="--minsn",
        category="disasm",
        kind="int_hex",
        label="Minimalna liczba kolejnych instrukcji (-T / --minsn)",
        tooltip="Minimalna liczba poprawnych kolejnych instrukcji wymagana do uznania trafienia (domyślnie: 500).",
        placeholder="np. 500",
    ),
    OptionSpec(
        field_name="continue_disasm",
        short_flag="-k",
        long_flag="--continue",
        category="disasm",
        kind="bool",
        label="Kontynuuj po pierwszym trafieniu (-k / --continue)",
        tooltip="Nie zatrzymuje skanowania dezasemblacji na pierwszym znalezionym bloku architektury.",
    ),
    # --- General Options (-l, -o, -O, -K, -g, -f, -c, -t, -q, -v, -h, -a, -p, -s) ---
    OptionSpec(
        field_name="length",
        short_flag="-l",
        long_flag="--length",
        category="general",
        kind="int_hex",
        label="Liczba bajtów do przeskanowania (-l / --length)",
        tooltip="Ogranicza skanowanie do podanej liczby bajtów (obsługuje dec i hex 0x...).",
        placeholder="np. 65536 lub 0x10000",
    ),
    OptionSpec(
        field_name="offset",
        short_flag="-o",
        long_flag="--offset",
        category="general",
        kind="int_hex",
        label="Offset początkowy skanu (-o / --offset)",
        tooltip="Rozpoczyna skanowanie od podanego przesunięcia w pliku (dec lub 0x...).",
        placeholder="np. 0x1000",
    ),
    OptionSpec(
        field_name="base_addr",
        short_flag="-O",
        long_flag="--base",
        category="general",
        kind="int_hex",
        label="Adres bazowy dla offsetów (-O / --base)",
        tooltip="Dodaje stały adres bazowy do wszystkich wyświetlanych offsetów (dec lub 0x...).",
        placeholder="np. 0x80000000",
    ),
    OptionSpec(
        field_name="block_size",
        short_flag="-K",
        long_flag="--block",
        category="general",
        kind="int_hex",
        label="Rozmiar bloku pliku (-K / --block)",
        tooltip="Ustawia rozmiar bloku używanego podczas odczytu i analizy.",
        placeholder="np. 1024",
    ),
    OptionSpec(
        field_name="swap_bytes",
        short_flag="-g",
        long_flag="--swap",
        category="general",
        kind="int_hex",
        label="Odwróć co N bajtów przed skanem (-g / --swap)",
        tooltip="Zamienia kolejność bajtów (endianness swap) w blokach po N bajtów przed analizą.",
        placeholder="np. 2 lub 4",
    ),
    OptionSpec(
        field_name="log_file",
        short_flag="-f",
        long_flag="--log",
        category="general",
        kind="save_file",
        label="Zapisz wyniki do pliku logu (-f / --log)",
        tooltip="Zapisuje wynik działania binwalka do wskazanego pliku.",
        placeholder="ścieżka do pliku wynikowego",
    ),
    OptionSpec(
        field_name="csv",
        short_flag="-c",
        long_flag="--csv",
        category="general",
        kind="bool",
        label="Format CSV dla pliku logu (-c / --csv)",
        tooltip="Zapisuje wyniki w formacie CSV (używane z -f / --log).",
    ),
    OptionSpec(
        field_name="term",
        short_flag="-t",
        long_flag="--term",
        category="general",
        kind="bool",
        label="Dopasuj formatowanie do terminala (-t / --term)",
        tooltip="Formatuje szerokość kolumn wyjścia pod terminal.",
    ),
    OptionSpec(
        field_name="quiet",
        short_flag="-q",
        long_flag="--quiet",
        category="general",
        kind="bool",
        label="Tryb cichy (-q / --quiet)",
        tooltip="Wycisza standardowe wyjście stdout.",
    ),
    OptionSpec(
        field_name="verbose",
        short_flag="-v",
        long_flag="--verbose",
        category="general",
        kind="bool",
        label="Tryb szczegółowy (-v / --verbose)",
        tooltip="Włącza rozszerzone komunikaty diagnostyczne.",
    ),
    OptionSpec(
        field_name="finclude",
        short_flag="-a",
        long_flag="--finclude",
        category="general",
        kind="str",
        label="Skanuj tylko nazwy plików pasujące do regex (-a / --finclude)",
        tooltip="Filtruje wejściowe/rekurencyjne pliki według wyrażenia regularnego.",
        placeholder="regex nazwy pliku, np. .*\\.bin$",
    ),
    OptionSpec(
        field_name="fexclude",
        short_flag="-p",
        long_flag="--fexclude",
        category="general",
        kind="str",
        label="Pomiń nazwy plików pasujące do regex (-p / --fexclude)",
        tooltip="Pomija pliki o nazwach pasujących do wyrażenia regularnego.",
        placeholder="regex nazwy pliku, np. .*\\.log$",
    ),
    OptionSpec(
        field_name="status_port",
        short_flag="-s",
        long_flag="--status",
        category="general",
        kind="int_hex",
        label="Port serwera statusu postępu (-s / --status)",
        tooltip="Uruchamia lokalny serwer TCP raportujący postęp na podanym porcie.",
        placeholder="np. 8088",
    ),
    OptionSpec(
        field_name="show_help",
        short_flag="-h",
        long_flag="--help",
        category="general",
        kind="bool",
        label="Pokaż pomoc CLI (-h / --help)",
        tooltip="Wyświetla pełną pomoc z flagami używanej binarki binwalk.",
    ),
)

SPEC_BY_FIELD: dict[str, OptionSpec] = {spec.field_name: spec for spec in OPTION_SPECS}


@dataclass
class BinwalkOptions:
    """Pełny stan wszystkich opcji Binwalk v2.4.3 i plików wejściowych."""

    binwalk_executable: str = "binwalk"
    use_long_flags: bool = False
    target_files: list[str] = field(default_factory=list)

    # Extraction
    extract: bool = False
    matryoshka: bool = False
    depth: str = ""
    directory: str = ""
    dd_rules: list[str] = field(default_factory=list)
    max_size: str = ""
    max_count: str = ""
    run_as: str = ""
    preserve_symlinks: bool = False
    rm_carved: bool = False
    carve: bool = False
    subdirs: bool = False

    # Signature
    signature: bool = False
    opcodes: bool = False
    raw_bytes: list[str] = field(default_factory=list)
    magic_files: list[str] = field(default_factory=list)
    dumb: bool = False
    invalid: bool = False
    exclude_filters: list[str] = field(default_factory=list)
    include_filters: list[str] = field(default_factory=list)

    # Entropy
    entropy: bool = False
    fast_entropy: bool = False
    save_plot: bool = False
    nlegend: bool = False
    nplot: bool = False
    entropy_high: str = ""
    entropy_low: str = ""

    # Binary Diffing
    hexdump: bool = False
    diff_green: bool = False
    diff_red: bool = False
    diff_blue: bool = False
    diff_similar: bool = False
    diff_terse: bool = False

    # Raw Compression
    deflate: bool = False
    lzma: bool = False
    partial: bool = False
    stop_first: bool = False

    # Disassembly
    disasm: bool = False
    minsn: str = ""
    continue_disasm: bool = False

    # General
    length: str = ""
    offset: str = ""
    base_addr: str = ""
    block_size: str = ""
    swap_bytes: str = ""
    log_file: str = ""
    csv: bool = False
    term: bool = False
    quiet: bool = False
    verbose: bool = False
    finclude: str = ""
    fexclude: str = ""
    status_port: str = ""
    show_help: bool = False

    def copy(self) -> BinwalkOptions:
        """Zwraca głęboką kopię konfiguracji bez współdzielenia list."""
        copied_kwargs = {}
        for f in fields(self):
            val = getattr(self, f.name)
            copied_kwargs[f.name] = list(val) if isinstance(val, list) else val
        return BinwalkOptions(**copied_kwargs)


PRESETS: dict[str, dict[str, object]] = {
    "Szybkie rozpakowanie (-e)": {"extract": True},
    "Głębokie rozpakowanie (-e -M)": {"extract": True, "matryoshka": True},
    "Wycięcie surowe bez dekompresji (-e -z)": {"extract": True, "carve": True},
    "Skan sygnatur (-B)": {"signature": True},
    "Analiza entropii + zapis PNG (-E -J -N)": {
        "entropy": True,
        "save_plot": True,
        "nplot": True,
    },
    "Porównanie binarne / Hexdump (-W)": {"hexdump": True},
    "Dezasemblacja architektury (-Y)": {"disasm": True},
    "Kompresja surowa (-X -Z)": {"deflate": True, "lzma": True},
    "Wyczyść wszystkie opcje": {},
}


def apply_preset(base: BinwalkOptions, preset_name: str) -> BinwalkOptions:
    """Tworzy nową konfigurację z zachowaniem plików i binarki, ale z opcjami z presetu."""
    new_opts = BinwalkOptions(
        binwalk_executable=base.binwalk_executable,
        use_long_flags=base.use_long_flags,
        target_files=list(base.target_files),
        directory=base.directory,
    )
    overrides = PRESETS.get(preset_name, {})
    for key, val in overrides.items():
        setattr(new_opts, key, list(val) if isinstance(val, list) else val)
    return new_opts
