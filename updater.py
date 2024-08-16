import os
import shutil
import subprocess
import stat

# Функция для выполнения команды оболочки и возврата True, если успешна
def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Произошла ошибка: {e}")
        return False

def replace_file_if_exists(src_path, dest_path):
    if os.path.exists(src_path):
        try:
            shutil.copy2(src_path, dest_path)
            print(f"Файл {os.path.basename(src_path)} успешно заменён.")
        except Exception as e:
            print(f"Ошибка при замене файла {os.path.basename(src_path)}: {e}")

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def main():
    print("==============================")
    print("ПРЕДУПРЕЖДЕНИЕ ОБ ОБНОВЛЕНИИ")
    print("==============================")
    print("Все файлы в текущем каталоге будут заменены на файлы из репозитория.")
    print("Пожалуйста, сделайте бекап всех файлов .json, если это необходимо.")
    input("Нажмите ENTER, чтобы продолжить или CTRL+C для отмены.")

    repo_url = "https://github.com/swiftmessage/swiftmessageexeapp.git"
    repo_temp_dir = "repo_temp"  # Временная директория для клонирования

    # Клонирование в временную директорию
    if os.path.exists(repo_temp_dir):
        shutil.rmtree(repo_temp_dir, onerror=remove_readonly)

    git_command = f"git clone {repo_url} {repo_temp_dir}"

    # Выполнение команды git clone
    if not execute_command(git_command):
        print("Произошла ошибка при клонировании репозитория.")
        print("Проверьте соединение с Интернетом или URL репозитория.")
        return

    # Список файлов, которые нужно проверить и заменить
    files_to_check = ['update.bat', 'updater.py']

    # Замена файлов в текущем каталоге на те, что из репозитория, если они существуют
    for file_name in files_to_check:
        repo_file_path = os.path.join(repo_temp_dir, file_name)
        current_file_path = os.path.join('.', file_name)
        replace_file_if_exists(repo_file_path, current_file_path)

    # Копирование других файлов и директорий из временной директории в текущую
    for item in os.listdir(repo_temp_dir):
        item_path = os.path.join(repo_temp_dir, item)
        current_item_path = os.path.join('.', item)
        if item not in files_to_check:
            try:
                if os.path.isdir(item_path):
                    # Если директория существует, удалить её перед копированием
                    if os.path.exists(current_item_path):
                        shutil.rmtree(current_item_path, onerror=remove_readonly)
                    shutil.copytree(item_path, current_item_path)
                else:
                    shutil.copy2(item_path, current_item_path)
            except Exception as e:
                print(f"Ошибка при копировании {item}: {e}")

    # Очистка временной директории
    shutil.rmtree(repo_temp_dir, onerror=remove_readonly)

    print("Файлы успешно обновлены из репозитория.")
    print("Обновление завершено успешно.")

if __name__ == "__main__":
    main()
