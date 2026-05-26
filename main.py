from datetime import time
from typing import Optional
import os
import json

from coursework_core import DayOfWeek, Teacher, Schedule, Lecture, Practice, Exam

def prompt_time(label: str) -> time:
    while True:
        raw = input(f"{label} (HH:MM): ").strip()
        try:
            h, m = map(int, raw.split(":"))
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError
            return time(h, m)
        except Exception:
            print("[Input Error] Час має бути у форматі HH:MM, напр. 08:30.")

def prompt_nonempty(label: str) -> str:
    while True:
        s = input(f"{label}: ").strip()
        if s:
            return s
        print("[Input Error] Поле не може бути порожнім.")

def choose_event_type() -> str:
    while True:
        print("Оберіть тип події: 1 - Lecture, 2 - Practice, 3 - Exam")
        ch = input("Ваш вибір (1/2/3): ").strip()
        if ch in ("1", "2", "3"):
            return {"1": "Lecture", "2": "Practice", "3": "Exam"}[ch]
        print("[Input Error] Дозволені значення: 1, 2 або 3.")

def add_event_flow(sch: Schedule, teacher_cache: Optional[Teacher] = None) -> Teacher:
    print("\n=== Додавання нової події ===")
    subject = prompt_nonempty("Предмет")
    room = prompt_nonempty("Аудиторія")
    start_t = prompt_time("Час початку")
    end_t = prompt_time("Час завершення")

    use_prev = ""
    if teacher_cache:
        use_prev = input(
            f"Використати попереднього викладача ({teacher_cache.name}, {teacher_cache.department})? [y/N]: "
        ).strip().lower()
    if use_prev == "y,yes,+" and teacher_cache:
        teacher = teacher_cache
    else:
        t_name = prompt_nonempty("ПІБ викладача")
        t_dept = prompt_nonempty("Кафедра")
        teacher = Teacher(t_name, t_dept)

    kind = choose_event_type()
    if kind == "Lecture":
        ev = Lecture(subject, teacher, room, start_t, end_t)
    elif kind == "Practice":
        ev = Practice(subject, teacher, room, start_t, end_t)
    else:
        assistant = prompt_nonempty("Асистент (для Exam)")
        ev = Exam(subject, teacher, room, start_t, end_t, assistant)

    sch.add_event(ev)
    return teacher

def print_all_events(sch: Schedule):
    # Тепер тут пише, на який день цей розклад
    print(f"\n=== Перелік подій на {sch.day.name} (відсортовано за часом) ===")
    empty = True
    for item in sch:
        print(" -", item)
        empty = False
    if empty:
        print(" (порожньо)")

def print_menu(is_admin: bool):
    print("\n================= Меню =================")
    print("1) Показати всі події")
    
    if is_admin:
        print("2) Додати подію")
        print("3) Зберегти стан (Pickle)")
        print("4) Завантажити стан (Pickle)")
        print("5) Експортувати звіт (CSV)")
        
    print("6) Фільтр за аудиторією")
    print("7) Пагінація")
    
    if is_admin:
        print("8) Скасувати пару")
        
    print("9) Пошук за викладачем")
    print("10) Пошук вільної аудиторії")
    print("0) Вихід (з автозбереженням)")
    print("========================================")

def pagination_flow(sch: Schedule):
    print("\n=== Пагінація ===")
    print(f"Поточний ліміт із config.json: {sch.default_page_size}")
    raw = input("Вкажіть розмір сторінки або Enter для поточного: ").strip()
    page_size = sch.default_page_size
    if raw:
        try:
            page_size = max(1, int(raw))
        except ValueError:
            print("[Input Warning] Некоректне число — використовую значення з конфігурації.")
    for idx, page in enumerate(sch.paginate_schedule(page_size), 1):
        print(f"Сторінка {idx}:")
        for it in page:
            print(" -", it)

def room_filter_flow(sch: Schedule):
    room = prompt_nonempty("Введіть номер аудиторії для фільтру")
    print(f"\nПодії в аудиторії {room}:")
    itr = sch.filter_by_room(room)
    found = False
    for ev in itr:
        print(" -", ev)
        found = True
    if not found:
        print(" (нічого не знайдено)")

def main():
    # Завантаження базових налаштувань (назва закладу)
    if not os.path.exists("config.json"):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump({"institution_name": "ВНТУ", "default_page_size": 2}, f)

    temp_schedule = Schedule(DayOfWeek.MONDAY)
    temp_schedule.load_config("config.json")
    print(f"\nПрацюю для інституції: {temp_schedule.institution_name}")
    
    # --- ВИБІР ДНЯ ТИЖНЯ ---
    print("\n=== Налаштування розкладу ===")
    print("На який день тижня створюємо розклад?")
    print("1 - Понеділок\n2 - Вівторок\n3 - Середа\n4 - Четвер\n5 - П'ятниця")
    day_choice = input("Ваш вибір (1-5): ").strip()
    
    days_map = {
        "1": DayOfWeek.MONDAY,
        "2": DayOfWeek.TUESDAY,
        "3": DayOfWeek.WEDNESDAY,
        "4": DayOfWeek.THURSDAY,
        "5": DayOfWeek.FRIDAY
    }
    # Якщо користувач введе літеру чи щось не те, прога автоматично поставить Понеділок
    selected_day = days_map.get(day_choice, DayOfWeek.MONDAY)
    
    # Створюємо фінальний об'єкт розкладу з обраним днем
    schedule = Schedule(selected_day)
    schedule.institution_name = temp_schedule.institution_name 
    schedule.default_page_size = temp_schedule.default_page_size
    print(f"[System] Створено розклад на: {selected_day.name}")
    
    # --- БЛОК АВТОРИЗАЦІЇ ---
    print("\n=== Авторизація ===")
    print("1) Увійти як Студент (тільки перегляд та пошук)")
    print("2) Увійти як Диспетчер (повний доступ до бази)")
    role_choice = input("Ваш вибір (1 або 2): ").strip()
    
    is_admin = (role_choice == "2")
    if is_admin:
        print("Вітаємо, Диспетчере! Всі функції розблоковано.")
    else:
        print("Вітаємо, Студенте! Права обмежено режимом читання.")
    # ------------------------

    last_teacher: Optional[Teacher] = None

    while True:
        print_menu(is_admin)
        try:
            cmd = input("Оберіть пункт меню: ").strip()
            
            # Перевірка прав для адмінських команд
            if cmd in ["2", "3", "4", "5", "8"] and not is_admin:
                print("[Відмова в доступі] Ця функція доступна тільки Диспетчеру!")
                continue

            match cmd:
                case "1":
                    print_all_events(schedule)
                case "2":
                    last_teacher = add_event_flow(schedule, last_teacher)
                case "3":
                    schedule.save_system_state()
                case "4":
                    schedule.load_system_state()
                case "5":
                    schedule.export_to_csv()
                case "6":
                    room_filter_flow(schedule)
                case "7":
                    pagination_flow(schedule)
                case "8":
                    subj = prompt_nonempty("Введіть назву предмета, який хочете відмінити")
                    if schedule.remove_event(subj):
                        print(f"[Успіх] Пару '{subj}' відмінено! Можна йти пити каву.")
                    else:
                        print(f"[Помилка] Не знайшли такої пари: '{subj}'.")
                case "9":
                    t_name = prompt_nonempty("Введіть ім'я викладача (або частину)")
                    found = schedule.search_by_teacher(t_name)
                    if found:
                        print(f"\n=== Знайдені заняття для викладача '{t_name}' ===")
                        for ev in found:
                            print(" -", ev)
                    else:
                        print(f"Викладач '{t_name}' пар не веде.")
                case "10":
                    print("\n=== Пошук вільної аудиторії ===")
                    print("Введіть проміжок часу, на який шукаємо вільне місце:")
                    s_time = prompt_time("Початок")
                    e_time = prompt_time("Кінець")
                    
                    if s_time >= e_time:
                        print("[Помилка] Час початку не може бути пізніше або дорівнювати часу завершення!")
                    else:
                        free_rooms = schedule.find_free_rooms(s_time, e_time)
                        if free_rooms:
                            print(f"[Знайдено] Вільні аудиторії на цей час: {', '.join(free_rooms)}")
                        else:
                            print("[Пусто] Глухо. Всі відомі аудиторії зайняті у цей час (або їх ще взагалі немає в базі).")
                case "0":
                    if is_admin:
                        print("[System] Автозбереження перед виходом...")
                        schedule.save_system_state()
                    print("[System] Завершення роботи. Bye!")
                    break
                case _:
                    print("[Menu] Невідома команда. Оберіть пункт із переліку.")
        except Exception as e:
            print(f"[Error] Некоректне введення або помилка виконання: {e}")
            print("[Info] Повертаюся у головне меню...")

if __name__ == "__main__":
    main()