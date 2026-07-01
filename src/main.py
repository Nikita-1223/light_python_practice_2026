import sys
import os
import hashlib


def print_help():
    print("=" * 50)
    print("ИНДЕКСАТОР ПАПОК — СПРАВКА")
    print("=" * 50)
    print()
    print("НАЗНАЧЕНИЕ:")
    print("  Обходит папку, показывает структуру, находит дубликаты")
    print("  и сравнивает с бэкапом.")
    print()
    print("ИСПОЛЬЗОВАНИЕ:")
    print("  py src/main.py ПУТЬ_К_ПАПКЕ [--filter РАСШИРЕНИЕ] [--backup ПУТЬ_К_БЭКАПУ]")
    print()
    print("ПАРАМЕТРЫ:")
    print("  ПУТЬ_К_ПАПКЕ          Папка для обхода (обязательный)")
    print("  --filter РАСШИРЕНИЕ   Показать только файлы с этим расширением")
    print("  --backup ПУТЬ         Сравнить с резервной копией")
    print("  --help                Показать эту справку")
    print()
    print("ПРИМЕРЫ:")
    print("  py src/main.py C:\\Users\\User\\Documents")
    print("  py src/main.py C:\\Users\\User\\Documents --filter .txt")
    print("  py src/main.py C:\\Users\\User\\Documents --backup D:\\Backup")
    print("  py src/main.py --help")
    print("=" * 50)


def get_file_hash(filepath):
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return None


def scan_folder(folder_path):
    entries = []

    try:
        items = sorted(os.listdir(folder_path))
    except PermissionError:
        entry = {
            "path": folder_path,
            "name": os.path.basename(folder_path),
            "is_dir": True,
            "size": 0,
            "hash": None,
            "no_access": True
        }
        return [entry]

    for item in items:
        full_path = os.path.join(folder_path, item)

        if os.path.isdir(full_path):
            entry = {
                "path": full_path,
                "name": item,
                "is_dir": True,
                "size": 0,
                "hash": None
            }
            entries.append(entry)
            entries.extend(scan_folder(full_path))
        else:
            size = os.path.getsize(full_path)
            file_hash = get_file_hash(full_path)
            entry = {
                "path": full_path,
                "name": item,
                "is_dir": False,
                "size": size,
                "hash": file_hash
            }
            entries.append(entry)

    return entries


def print_structure(entries, filter_ext=None, base_path=None):
    if base_path is None:
        base_path = ""

    for entry in entries:
        path = entry["path"]
        name = entry["name"]
        is_dir = entry["is_dir"]
        size = entry["size"]

        if not path.startswith(base_path):
            continue

        relative = path[len(base_path):].lstrip(os.sep)
        depth = relative.count(os.sep) if relative else 0
        indent = " " * (depth * 4)

        if entry.get("no_access"):
            print(f"{indent}[Нет доступа] {name}")
        elif is_dir:
            print(f"{indent}[ПАПКА] {name}")
        else:
            _, ext = os.path.splitext(name)
            if filter_ext is None or ext.lower() == filter_ext.lower():
                print(f"{indent}{name} ({size} байт)")


def find_duplicates(entries):
    hashes = {}
    for entry in entries:
        if entry["is_dir"] or entry.get("no_access"):
            continue
        file_hash = entry["hash"]
        if file_hash is None:
            continue
        if file_hash not in hashes:
            hashes[file_hash] = []
        hashes[file_hash].append(entry["path"])

    duplicates = {h: p for h, p in hashes.items() if len(p) >= 2}
    return duplicates


def print_duplicates(duplicates):
    print("\n" + "=" * 50)
    print("ДУБЛИКАТЫ")
    print("=" * 50)

    if not duplicates:
        print("Дубликаты не найдены.")
        print("=" * 50)
        return

    for file_hash, paths in duplicates.items():
        print(f"\nХеш: {file_hash[:16]}...")
        for path in paths:
            size = os.path.getsize(path)
            print(f"  - {path} ({size} байт)")
    print("=" * 50)


def collect_files(folder_path):
    files = {}

    try:
        items = os.listdir(folder_path)
    except PermissionError:
        return files

    for item in items:
        full_path = os.path.join(folder_path, item)
        if os.path.isdir(full_path):
            sub_files = collect_files(full_path)
            for sub_path, sub_info in sub_files.items():
                files[os.path.join(item, sub_path)] = sub_info
        else:
            size = os.path.getsize(full_path)
            file_hash = get_file_hash(full_path)
            files[item] = (size, file_hash)

    return files


def compare_folders(source_path, backup_path):
    print("\n" + "=" * 50)
    print("СРАВНЕНИЕ С БЭКАПОМ")
    print("=" * 50)
    print(f"Исходная папка: {source_path}")
    print(f"Бэкап:          {backup_path}")

    if not os.path.exists(backup_path):
        print(f"\nОшибка: папка бэкапа '{backup_path}' не найдена.")
        return

    if not os.path.isdir(backup_path):
        print(f"\nОшибка: '{backup_path}' — это не папка.")
        return

    source_files = collect_files(source_path)
    backup_files = collect_files(backup_path)

    source_names = set(source_files.keys())
    backup_names = set(backup_files.keys())

    new_files = source_names - backup_names
    deleted_files = backup_names - source_names
    common_files = source_names & backup_names

    changed_files = []
    for name in common_files:
        if source_files[name] != backup_files[name]:
            changed_files.append(name)

    if new_files:
        print(f"\nНовые файлы (отсутствуют в бэкапе) [{len(new_files)}]:")
        for name in sorted(new_files):
            size = source_files[name][0]
            print(f"  + {name} ({size} байт)")

    if deleted_files:
        print(f"\nУдалённые файлы (есть в бэкапе, но нет в исходной) [{len(deleted_files)}]:")
        for name in sorted(deleted_files):
            size = backup_files[name][0]
            print(f"  - {name} ({size} байт)")

    if changed_files:
        print(f"\nИзменённые файлы [{len(changed_files)}]:")
        for name in sorted(changed_files):
            src_size = source_files[name][0]
            bak_size = backup_files[name][0]
            print(f"  ~ {name} (исх: {src_size} байт, бэкап: {bak_size} байт)")

    if not new_files and not deleted_files and not changed_files:
        print("\nРазличий нет. Папки идентичны.")

    print("=" * 50)


def parse_args():
    if len(sys.argv) < 2:
        return None, None, None, True

    if sys.argv[1] == "--help":
        return None, None, None, True

    folder_path = sys.argv[1]
    filter_ext = None
    backup_path = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--filter" and i + 1 < len(args):
            filter_ext = args[i + 1]
            if not filter_ext.startswith("."):
                filter_ext = "." + filter_ext
            i += 2
        elif args[i] == "--backup" and i + 1 < len(args):
            backup_path = args[i + 1]
            i += 2
        else:
            i += 1

    return folder_path, filter_ext, backup_path, False


def main():
    folder_path, filter_ext, backup_path, show_help = parse_args()

    if show_help:
        if folder_path is None and filter_ext is None:
            print_help()
        else:
            print("ОШИБКА: не указан путь к папке.")
            print("Введите 'py src/main.py --help' для справки.")
        return

    if not os.path.exists(folder_path):
        print(f"Ошибка: папка '{folder_path}' не найдена.")
        return

    if not os.path.isdir(folder_path):
        print(f"Ошибка: '{folder_path}' — это не папка.")
        return

    print(f"Обход папки: {folder_path}")
    if filter_ext:
        print(f"Фильтр: показываем только *{filter_ext}")
    print()

    entries = scan_folder(folder_path)
    print_structure(entries, filter_ext, folder_path)

    duplicates = find_duplicates(entries)
    print_duplicates(duplicates)

    if backup_path:
        compare_folders(folder_path, backup_path)


if __name__ == "__main__":
    main()