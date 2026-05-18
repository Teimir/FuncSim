# 13 — GUI-отладчик (`cli.debug_gui`)

```bash
pip install -e ".[dev]"
python -m cli.debug_gui --hex examples/smoke.hex
# или
e32c-debug-gui --hex examples/smoke.hex --mmio
e32c-debug-gui --core tn9k --hex examples/smoke.hex
python examples/launch_smoke_gui.py
python examples/launch_smoke_gui.py --core tn9k
```

Флаги запуска — как у [12-cli-debug-repl.md](12-cli-debug-repl.md) (`debug_common`), включая **`--core full|tn9k|lite`**.

В окне: заголовок `E32C debugger — core <variant>` и строка состояния `core=…` (вкладка SPR показывает `CORE_INFO` / `FEATURES` для выбранного профиля).

**Смена ядра** — только при перезапуске GUI с другим `--core` (во время сессии вариант не переключается).

## Панель инструментов


| Элемент                       | Действие                            |
| ----------------------------- | ----------------------------------- |
| Step (F7)                     | Один шаг                            |
| Run N (F6)                    | N шагов; большие N — в фоне         |
| N: + пресеты 1/100/1000/10000 | Быстрый ввод                        |
| Continue… (F8)                | До max steps или halt/break         |
| max: + пресеты                | Лимит для Continue                  |
| Reset (Ctrl+R)                | Сброс CPU (breakpoints сохраняются) |
| Auto + ms + burst             | Периодический burst шагов (Ctrl+A)  |


## Меню File


| Пункт                   | Действие             |
| ----------------------- | -------------------- |
| Open binary… (Ctrl+B)   | Загрузить bin        |
| Open hex… (Ctrl+O)      | Загрузить hex        |
| Export snapshot (JSON)… | Снимок regs/mem/mmio |
| Exit                    | Закрыть              |


## Меню Execute

Step, Run N, Continue…, Reset CPU — дублируют toolbar.

## Меню View


| Пункт                      | Описание                                |
| -------------------------- | --------------------------------------- |
| UART terminal… (Ctrl+U)    | Окно TX/RX; Enter отправляет строку     |
| Fast refresh               | Пропуск тяжёлого trace/MMIO текста      |
| Density: default / compact | Размер шрифтов и строк таблиц           |
| Status: minimal / full     | Строка состояния: кратко или IPS/cycles |


### UART terminal

- Ввод с `\n` для протоколов вроде `uart_calculator` (`HALT\n`).
- История и режимы — см. `examples/uart_calculator_gui.py`.

## Меню Help → Shortcuts

F7 Step · F6 Run N · F8 Continue · Ctrl+R Reset · Ctrl+U UART · Ctrl+A Auto · Ctrl+O hex · Ctrl+B bin.

## Вкладка CPU / Memory


| Область               | Взаимодействие                                      |
| --------------------- | --------------------------------------------------- |
| Registers             | Double-click — правка значения                      |
| Flags / SPR           | Просмотр (SPR: saved PC, vector, mask, CORE_INFO…)  |
| Next instruction @ PC | Текущая инструкция                                  |
| Disassembly           | `⇒` PC, `●` breakpoint; **ПКМ** — toggle breakpoint |
| ±lines + Apply        | Радиус листинга вокруг PC                           |
| Memory page           | Base, ◀▶, Sync PC; **double-click** слова RAM       |


## Вкладка MMIO

Текстовый снимок: GPIO, UART (очереди, STATUS), Timer (counter/period/CTRL), SD.

**Feed UART RX** — hex-байты в RX-очередь (например `0a` для LF).

## Вкладка Storage


| Кнопка         | Действие                         |
| -------------- | -------------------------------- |
| Browse / Mount | Подключить `--sd-image` к сессии |
| Unmount        | Отключить                        |
| Create & mount | Пустой образ N секторов          |


Требуется MMIO при старте или mount во время сессии.

## Вкладка Trace

Таблица последних шагов: PC, word, disasm, cycles, halted. **Clear trace**.

## Вкладка Breakpoints

Добавить/удалить адреса (hex, выровненные). Синхронизация с листингом (ПКМ).

## Status bar

- **minimal:** PC, halted, steps
- **full:** + avg/burst IPS, cycles (адаптивные единицы)

## Сценарии

```bash
# MMIO demo
python examples/device_demo_gui.py

# SD
python examples/launch_sd_gui_demo.py

# UART REPL
python examples/uart_calculator_gui.py
```

## Дальше

[14-gdb-remote.md](14-gdb-remote.md)