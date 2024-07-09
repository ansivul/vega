import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from stegano import exifHeader

# Тексты на английском и русском языках
texts = {
    'en': {
        'title': 'Steganography Tool',
        'action': 'Action:',
        'hide_payload': 'Hide Payload',
        'extract_payload': 'Extract Payload',
        'generate_keys': 'Generate Keys',
        'image_file': 'Image File:',
        'payload_file': 'Payload File:',
        'browse': 'Browse...',
        'execute': 'Execute',
        'success': 'Success',
        'keys_generated': 'Keys generated successfully!',
        'error': 'Error',
        'public_key_not_found': 'Public key file not found!\nPath: ',
        'private_key_not_found': 'Private key file not found!\nPath: ',
        'payload_hidden': 'Payload successfully hidden in the image! Saved as ',
        'no_payload': 'No payload found in the image.',
        'payload_extracted': 'Payload extracted and saved as ',
        'input_error': 'Input Error',
        'select_files': 'Please select all required files.',
        'select_image': 'Please select an image file.',
        'selection_error': 'Selection Error',
        'select_action': 'Please select an action.'
    },
    'ru': {
        'title': 'Инструмент Стеганографии',
        'action': 'Действие:',
        'hide_payload': 'Скрыть информацию',
        'extract_payload': 'Извлечь информацию',
        'generate_keys': 'Сгенерировать ключи',
        'image_file': 'Файл изображения:',
        'payload_file': 'Текстовый файл:',
        'browse': 'Обзор...',
        'execute': 'Выполнить',
        'success': 'Успех',
        'keys_generated': 'Ключи успешно сгенерированы!',
        'error': 'Ошибка',
        'public_key_not_found': 'Файл публичного ключа не найден!\nПуть: ',
        'private_key_not_found': 'Файл приватного ключа не найден!\nПуть: ',
        'payload_hidden': 'Информация успешно скрыта в изображении! Сохранено как ',
        'no_payload': 'Информация в изображении не найдена.',
        'payload_extracted': 'Информация извлечена и сохранена как ',
        'input_error': 'Ошибка ввода',
        'select_files': 'Пожалуйста, выберите все необходимые файлы.',
        'select_image': 'Пожалуйста, выберите файл изображения.',
        'selection_error': 'Ошибка выбора',
        'select_action': 'Пожалуйста, выберите действие.'
    }
}

# Функция для изменения языка
def change_language(*args):
    lang = language_var.get()
    root.title(texts[lang]['title'])
    action_label.config(text=texts[lang]['action'])
    hide_radiobutton.config(text=texts[lang]['hide_payload'])
    extract_radiobutton.config(text=texts[lang]['extract_payload'])
    generate_keys_radiobutton.config(text=texts[lang]['generate_keys'])
    image_label.config(text=texts[lang]['image_file'])
    payload_label.config(text=texts[lang]['payload_file'])
    browse_image_button.config(text=texts[lang]['browse'])
    browse_payload_button.config(text=texts[lang]['browse'])
    execute_button.config(text=texts[lang]['execute'])

# Генерация ключей
def generate_keys():
    try:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

        with open(os.path.join(base_dir, "private_key.pem"), "wb") as priv_file:
            priv_file.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(os.path.join(base_dir, "public_key.pem"), "wb") as pub_file:
            pub_file.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

        messagebox.showinfo(texts[language_var.get()]['success'], texts[language_var.get()]['keys_generated'])
    except Exception as e:
        messagebox.showerror(texts[language_var.get()]['error'], str(e))

# Загрузка публичного ключа
def load_public_key():
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    public_key_path = os.path.join(base_dir, "public_key.pem")
    
    if not os.path.exists(public_key_path):
        messagebox.showerror(texts[language_var.get()]['error'], f"{texts[language_var.get()]['public_key_not_found']}{public_key_path}")
        return None

    with open(public_key_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(key_file.read())
    return public_key

# Загрузка приватного ключа
def load_private_key():
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    private_key_path = os.path.join(base_dir, "private_key.pem")
    
    if not os.path.exists(private_key_path):
        messagebox.showerror(texts[language_var.get()]['error'], f"{texts[language_var.get()]['private_key_not_found']}{private_key_path}")
        return None

    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return private_key

# Шифрование сообщения
def encrypt_message(message, public_key):
    encrypted_message = public_key.encrypt(
        message.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_message

# Дешифрование сообщения
def decrypt_message(encrypted_message, private_key):
    decrypted_message = private_key.decrypt(
        encrypted_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_message.decode()

# Скрытие полезной нагрузки
def hide_payload(image_path, payload_path):
    try:
        public_key = load_public_key()
        if public_key is None:
            return
        
        with open(payload_path, 'r', encoding='utf-8') as file:
            payload = file.read()
        encrypted_payload = encrypt_message(payload, public_key)
        
        directory, filename = os.path.split(image_path)
        output_path = os.path.join(directory, f"output_{filename}")
        
        exifHeader.hide(image_path, output_path, encrypted_payload)
        messagebox.showinfo(texts[language_var.get()]['success'], f"{texts[language_var.get()]['payload_hidden']}{output_path}")
    except Exception as e:
        messagebox.showerror(texts[language_var.get()]['error'], str(e))

# Извлечение полезной нагрузки
def extract_payload(image_path):
    try:
        private_key = load_private_key()
        if private_key is None:
            return
        
        encrypted_payload = exifHeader.reveal(image_path)
        if encrypted_payload:
            payload = decrypt_message(encrypted_payload, private_key)
            
            directory, filename = os.path.split(image_path)
            output_filename = f"extracted_{os.path.splitext(filename)[0]}.txt"
            output_path = os.path.join(directory, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(payload)
            messagebox.showinfo(texts[language_var.get()]['success'], f"{texts[language_var.get()]['payload_extracted']}{output_path}")
        else:
            messagebox.showwarning(texts[language_var.get()]['no_payload'], texts[language_var.get()]['no_payload'])
    except Exception as e:
        messagebox.showerror(texts[language_var.get()]['error'], str(e))

# Функции выбора файлов
def select_image():
    file_path = filedialog.askopenfilename(title=texts[language_var.get()]['browse'], filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if file_path:
        image_path_entry.delete(0, tk.END)
        image_path_entry.insert(0, file_path)

def select_payload():
    file_path = filedialog.askopenfilename(title=texts[language_var.get()]['browse'], filetypes=[("Text files", "*.txt")])
    if file_path:
        payload_path_entry.delete(0, tk.END)
        payload_path_entry.insert(0, file_path)

# Обновление видимости элементов интерфейса в зависимости от выбора действия
def update_visibility():
    action = action_var.get()
    if action == "generate_keys":
        image_path_entry.grid_remove()
        payload_path_entry.grid_remove()
        browse_image_button.grid_remove()
        browse_payload_button.grid_remove()
        image_label.grid_remove()
        payload_label.grid_remove()
    elif action == "hide":
        image_path_entry.grid()
        payload_path_entry.grid()
        browse_image_button.grid()
        browse_payload_button.grid()
        image_label.grid()
        payload_label.grid()
    elif action == "extract":
        image_path_entry.grid()
        payload_path_entry.grid_remove()
        browse_image_button.grid()
        browse_payload_button.grid_remove()
        image_label.grid()
        payload_label.grid_remove()

# Выполнение выбранного действия
def on_execute():
    action = action_var.get()
    if action == "generate_keys":
        generate_keys()
    elif action == "hide":
        image_path = image_path_entry.get()
        payload_path = payload_path_entry.get()
        if image_path and payload_path:
            hide_payload(image_path, payload_path)
        else:
            messagebox.showwarning(texts[language_var.get()]['input_error'], texts[language_var.get()]['select_files'])
    elif action == "extract":
        image_path = image_path_entry.get()
        if image_path:
            extract_payload(image_path)
        else:
            messagebox.showwarning(texts[language_var.get()]['input_error'], texts[language_var.get()]['select_image'])
    else:
        messagebox.showwarning(texts[language_var.get()]['selection_error'], texts[language_var.get()]['select_action'])

def main():
    global root, language_var, action_var, action_label, hide_radiobutton, extract_radiobutton, generate_keys_radiobutton
    global image_label, payload_label, image_path_entry, payload_path_entry, browse_image_button, browse_payload_button, execute_button

    root = tk.Tk()

    language_var = tk.StringVar(value='en')
    language_var.trace("w", change_language)

    action_var = tk.StringVar(value="hide")
    action_var.trace("w", lambda *args: update_visibility())

    # Создание и размещение элементов GUI
    tk.Label(root, text="Language:").grid(row=0, column=0, padx=10, pady=5)
    tk.Radiobutton(root, text="En", variable=language_var, value='en').grid(row=0, column=1, padx=10, pady=5)
    tk.Radiobutton(root, text="Рус", variable=language_var, value='ru').grid(row=0, column=2, padx=10, pady=5)

    action_label = tk.Label(root, text="Action:")
    action_label.grid(row=1, column=0, padx=10, pady=5)
    hide_radiobutton = tk.Radiobutton(root, text="Hide Payload", variable=action_var, value="hide")
    hide_radiobutton.grid(row=1, column=1, padx=10, pady=5)
    extract_radiobutton = tk.Radiobutton(root, text="Extract Payload", variable=action_var, value="extract")
    extract_radiobutton.grid(row=1, column=2, padx=10, pady=5)
    generate_keys_radiobutton = tk.Radiobutton(root, text="Generate Keys", variable=action_var, value="generate_keys")
    generate_keys_radiobutton.grid(row=1, column=3, padx=10, pady=5)

    image_label = tk.Label(root, text="Image File:")
    image_label.grid(row=2, column=0, padx=10, pady=5)
    image_path_entry = tk.Entry(root, width=50)
    image_path_entry.grid(row=2, column=1, columnspan=3, padx=10, pady=5)
    browse_image_button = tk.Button(root, text="Browse...", command=select_image)
    browse_image_button.grid(row=2, column=4, padx=10, pady=5)

    payload_label = tk.Label(root, text="Payload File:")
    payload_label.grid(row=3, column=0, padx=10, pady=5)
    payload_path_entry = tk.Entry(root, width=50)
    payload_path_entry.grid(row=3, column=1, columnspan=3, padx=10, pady=5)
    browse_payload_button = tk.Button(root, text="Browse...", command=select_payload)
    browse_payload_button.grid(row=3, column=4, padx=10, pady=5)

    execute_button = tk.Button(root, text="Execute", command=on_execute)
    execute_button.grid(row=4, column=1, columnspan=3, padx=10, pady=20)

    update_visibility()
    change_language()

    root.mainloop()

if __name__ == '__main__':
    main()