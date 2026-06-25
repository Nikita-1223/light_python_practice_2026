import sys
import os


def print_help():
    """Выводит справку по использованию утилиты."""
    print("=" * 50)
    print("ИНДЕКСАТОР ПАПОК — СПРАВКА")
    print("=" * 50)
    print()
    print("НАЗНАЧЕНИЕ:")
    print("  Обходит папку, показывает структуру и формирует отчёт.")
    print()
    print("ИСПОЛЬЗОВАНИЕ:")
    print("  py src/main.py ПУТЬ_К_ПАПКЕ [--filter РАСШИРЕНИЕ]")
    print()
    print("ПАРАМЕТРЫ:")
    print("  ПУТЬ_К_ПАПКЕ          Папка для обхода (обязательный)")
    print("  --filter РАСШИРЕНИЕ   Показать только файлы с этим расширением")
    print("  --help                Показать эту справку")
    print()
    print("ПРИМЕРЫ:")
    print("  py src/main.py C:\\Users\\User\\Documents")
    print("  py src/main.py C:\\Users\\User\\Documents --filter .txt")
    print("  py src/main.py --help")
    print("=" * 50)


def scan_folder(folder_path, indent=0, stats=None, filter_ext=None):
    """
    Рекурсивно обходит папку, выводит содержимое и собирает статистику.
    """
    if stats is None:
        stats = {"files": 0, "folders": 0, "size": 0}

    try:
        items = sorted(os.listdir(folder_path))
    except PermissionError:
        print(" " * indent + f"[Нет доступа] {folder_path}")
        return stats

    for item in items:
        full_path = os.path.join(folder_path, item)
        prefix = " " * indent

        if os.path.isdir(full_path):
            stats["folders"] += 1
            print(f"{prefix}[ПАПКА] {item}")
            scan_folder(full_path, indent + 4, stats, filter_ext)
        else:
            size = os.path.getsize(full_path)
            _, ext = os.path.splitext(item)

            stats["files"] += 1
            stats["size"] += size

            if filter_ext is None or ext.lower() == filter_ext.lower():
                print(f"{prefix}{item} ({size} байт)")

    return stats


def print_report(stats, folder_path, filter_ext=None):
    """Выводит итоговый отчёт."""
    print("\n" + "=" * 50)
    print("ОТЧЁТ")
    print("=" * 50)
    print(f"Папка: {folder_path}")
    if filter_ext:
        print(f"Фильтр по расширению: {filter_ext}")
    print(f"Файлов: {stats['files']}")
    print(f"Папок: {stats['folders']}")
    print(f"Общий размер: {stats['size']} байт")

    size_kb = stats["size"] / 1024
    if size_kb >= 1024:
        print(f"Общий размер: {size_kb / 1024:.2f} МБ")
    else:
        print(f"Общий размер: {size_kb:.2f} КБ")
    print("=" * 50)


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--help":
        print_help()
        return

    if len(sys.argv) < 2:
        print("ОШИБКА: не указан путь к папке.")
        print("Введите 'py src/main.py --help' для справки.")
        return

    if sys.argv[1] == "--help":
        print_help()
        return

    folder_path = sys.argv[1]
    filter_ext = None

    if len(sys.argv) >= 4 and sys.argv[2] == "--filter":
        filter_ext = sys.argv[3]
        if not filter_ext.startswith("."):
            filter_ext = "." + filter_ext

    if not os.path.exists(folder_path):
        print(f"Ошибка: папка '{folder_path}' не найдена.")
        return

    if not os.path.isdir(folder_path):
        print(f"Ошибка: '{folder_path}' — это не папка.")
        return

    print(f"Обход папки: {folder_path}")
    if filter_ext:
        print(f"Фильтр: показываем только *{filter_ext}\n")
    else:
        print()

    stats = scan_folder(folder_path, filter_ext=filter_ext)
    print_report(stats, folder_path, filter_ext)


if __name__ == "__main__":
    main()