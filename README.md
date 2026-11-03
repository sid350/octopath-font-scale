# OCTOPATH TRAVELER: larger text

`octopath_font_scale.py` builds a small patch pak for OCTOPATH TRAVELER on the Switch (update 1.0.5, `010057D006492000`). The pak makes the game's text 1.5 times larger. Windows, frames and pictures keep their size, and the line spacing stays as it was.

The pak is made from your own copy of the game. This repository holds no game files.

## How it works

The game draws its text with FreeType from TrueType fonts in its paks (`Kingship/Content/UI/Font/*.ufont`). The script changes six of them: the Latin text fonts `KS_Skech_*`, `KS_Meldir_*` and `KS_NewCinema_Std_D`.

- **Glyph size.** Each font's `unitsPerEm` is divided by the scale, so the glyphs and their advances grow by that factor.
- **Line spacing.** Unreal Engine 4.18 takes a line's height and baseline from the font's bounding box (`head` `yMin` / `yMax`). The script shrinks the box by the same factor, so the lines keep their spacing. The `hhea` and `OS/2` line metrics are shrunk to match, for other readers.

The fonts go into `Kingship-Switch_9_P.pak`, a version 4 pak of stored files. The engine mounts paks named `*_<n>_P.pak` after the game's own, so this one wins over the originals.

Japanese, Chinese and Korean fonts are not changed.

## Use

Python 3.8 or later, no other packages:

```
python octopath_font_scale.py <RomFS>/Kingship/Content/Paks
python octopath_font_scale.py <RomFS>/Kingship/Content/Paks -s 1.3 -o Kingship-Switch_9_P.pak
```

The folder is the game's extracted RomFS with the update. It holds `Kingship-Switch.pak`, and the update's `Kingship-Switch_0_P.pak`, which wins over the base game's fonts. The script writes `Kingship-Switch_9_P.pak` beside them.

`-s` sets the text scale, from 1 to 3. The default is 1.5.

Where to put the pak:

- **nx2android (Android).** Put it into the installed game's data, in `/sdcard/Android/data/<package>/files/RomFS/Kingship/Content/Paks/`. Then start the game again.
- **nxnative (Mac / iPhone).** Put it into the extracted RomFS (`Kingship/Content/Paks/`) before the app is built, so it is packed with the game files. Not tested yet.
- **Switch with Atmosphère.** Put it in `atmosphere/contents/010057D006492000/romfs/Kingship/Content/Paks/`.

To undo the change, delete `Kingship-Switch_9_P.pak`.

## Tested

On Android, with nx2android on a Red Magic Astra, the scale was 1.5. These screens were checked: the title, the traveler selection, Cyrus's opening and its dialogue boxes.

Long lines in places not looked at yet may not fit their boxes.

---

# OCTOPATH TRAVELER: крупный текст

Скрипт собирает из файлов вашей копии игры патч-пак, с которым текст становится в 1.5 раза крупнее. Окна, рамки и межстрочный интервал остаются как в оригинале. Самих файлов игры в репозитории нет.

```
python octopath_font_scale.py <RomFS>/Kingship/Content/Paks
```

Получится файл `Kingship-Switch_9_P.pak`. Куда его положить:

- **Android (nx2android):** в `files/RomFS/Kingship/Content/Paks/` в данных установленной игры.
- **Mac или iPhone (nxnative):** в распакованный RomFS перед сборкой приложения. Этот вариант ещё не проверялся.
- **Switch:** в `atmosphere/contents/010057D006492000/romfs/Kingship/Content/Paks/`.

Чтобы вернуть обычный размер, удалите этот пак.
