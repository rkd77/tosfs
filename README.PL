Zestaw programów tosfs przeznaczony jest do obsługi obrazów dysków .DSK
z systemem TOS (Timex Operating System).
W skład zestawu wchodzą:

*tosfs.py* - skrypt Pythona (wymagany fuse-python) obsługujący system plików
TOSa w przestrzeni użytkownika.
Montowanie systemu plików:
./tosfs.py IMAGE.DSK mountpoint
Odmontowanie:
fusermount -u mountpoint

*mctosfs.py* - skrypt Pythona dla extfs mc (Midnight Commandera).
Należy skopiować plik mctosfs.py, tak żeby znalazł się w PATH, np.
do /usr/local/bin

Plik /etc/mc/mc.ext skopiować do ~/.config/mc/
i dopisać do tego pliku:
# TOSFS
regex/\.([dD][sS][kK])$
	Open=%cd %p/tosfs://
	View=%view{ascii} mctosfs.py list %f

Należy utworzyć katalog (mkdir -p ~/.local/share/mc/extfs.d )
i symlink:
cd ~/.local/share/mc/extfs.d
ln -s /usr/local/bin/mctosfs.py tosfs

Teraz już można używać mc do podglądu i kopiowania plików z obrazów dyskietek
TOSa.

Jest jeszcze *dsk2tap.py*.
Ten skrypt służy kopiowania plików wyciągniętych z "dyskietek" na pliki .tap,
./dsk2tap.py plik plik.tap
W przypadku programów BASICowych skrypt zamienia
LOAD * na LOAD spacja
W ten sposób łatwiej przenieść programy z dysku na taśmę.

Algorytm jest następujący:
- wyciągnąć pliki z obrazów dyskietki
- dla każdego pliku wykonać dsk2tap.py z odpowiednimi nazwami plików
- połączyć wynikowe .tapy

UWAGA:
Programy są w stadium alfa. Nie do końca działają poprawnie.
Nie ma jeszcze napisanego kopiowania plików w drugą stronę,
czyli na obrazy dyskietek. Nie są obsługiwane gęste "dyskietki" ani
podkatalogi. Są też problemy z poprawnym ustaleniem wielkości pliku
i odczytem.
