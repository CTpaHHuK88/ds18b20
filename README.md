# Подключение датчика температуры DS18B20 к Raspberry Pi Zero 2W

## Необходимые компоненты
- Raspberry Pi Zero 2W
- Датчик температуры DS18B20
- Резистор 4.7 кОм
- Монтажные провода
- Макетная плата (опционально)

## Схема подключения

```
DS18B20:
    ┌──────────────┐
    │              │
    │  DS18B20     │
    │              │
    └───┬───┬───┬──┘
        │   │   │
        │   │   │
       VDD DQ GND
        │   │   │
        │   │   │
    3.3V│   │   │GND
    ┌───┴───┴───┴───┐
    │   Raspberry   │
    │   Pi Zero 2W  │
    └───────────────┘
```

### Подключение по контактам:
- **VDD (Красный)** → 3.3V (контакт 1 или 17)
- **DQ (Желтый/Белый)** → GPIO4 (контакт 7) + резистор 4.7к к 3.3V
- **GND (Черный)** → GND (контакт 6, 9, 14, 20, 25, 30, 34, 39)

## Пошаговая инструкция

### 1. Активация 1-Wire интерфейса
```bash
# Открываем конфигурацию Raspberry Pi
sudo raspi-config

# Или редактируем конфиг вручную
sudo nano /boot/config.txt
```

Добавляем в конец файла:
```
dtoverlay=w1-gpio
```

Сохраняем (Ctrl+X, Y, Enter) и перезагружаем:
```bash
sudo reboot
```

### 2. Проверка подключения
После перезагрузки проверяем, видит ли система датчик:
```bash
# Подключаем модуль ядра
sudo modprobe w1-gpio
sudo modprobe w1-therm

# Проверяем наличие устройства
ls /sys/bus/w1/devices/
```

Должны увидеть что-то вроде:
```
28-011931eaf5ee  w1_bus_master1
```

### 3. Чтение температуры
```bash
# Переходим в директорию датчика
cd /sys/bus/w1/devices/28-*

# Читаем данные
cat w1_slave
```

Пример вывода:
```
a0 01 4b 46 7f ff 0c 10 71 : crc=71 YES
a0 01 4b 46 7f ff 0c 10 71 t=23125
```

Температура = 23125 / 1000 = 23.125°C

## Python скрипт для чтения температуры

Создайте файл `ds18b20.py`:

```python
#!/usr/bin/env python3
import os
import glob
import time

class DS18B20:
    def __init__(self):
        self.base_dir = '/sys/bus/w1/devices/'
        self.device_folder = glob.glob(self.base_dir + '28*')[0]
        self.device_file = self.device_folder + '/w1_slave'
    
    def read_temp_raw(self):
        with open(self.device_file, 'r') as f:
            lines = f.readlines()
        return lines
    
    def read_temp(self):
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.read_temp_raw()
        
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return temp_c, temp_f
    
    def continuous_read(self, interval=2):
        try:
            while True:
                temp_c, temp_f = self.read_temp()
                print(f"Температура: {temp_c:.2f}°C / {temp_f:.2f}°F")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nОстановлено пользователем")

if __name__ == "__main__":
    sensor = DS18B20()
    print("Начинаем чтение температуры. Для остановки нажмите Ctrl+C")
    sensor.continuous_read()
```

Сделайте скрипт исполняемым и запустите:
```bash
chmod +x ds18b20.py
python3 ds18b20.py
```

## Упрощенная версия скрипта

```python
#!/usr/bin/env python3
import glob
import time

def read_temperature():
    try:
        device_file = glob.glob('/sys/bus/w1/devices/28*/w1_slave')[0]
        
        with open(device_file, 'r') as f:
            lines = f.readlines()
        
        if lines[0].strip()[-3:] == 'YES':
            temp_pos = lines[1].find('t=')
            if temp_pos != -1:
                temp = float(lines[1][temp_pos+2:]) / 1000.0
                return temp
        return None
    except:
        return None

# Бесконечный цикл чтения
while True:
    temp = read_temperature()
    if temp is not None:
        print(f"Температура: {temp:.2f}°C")
    else:
        print("Ошибка чтения датчика")
    
    time.sleep(2)
```

## Автозагрузка скрипта при запуске

Создайте сервис для автоматического запуска:

```bash
sudo nano /etc/systemd/system/temp_monitor.service
```

Добавьте содержимое:
```ini
[Unit]
Description=Temperature Monitor Service
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/pi/temperature_monitor.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable temp_monitor.service
sudo systemctl start temp_monitor.service
```

## Возможные проблемы и решения

1. **Датчик не обнаружен**:
   - Проверьте подключение проводов
   - Убедитесь, что резистор 4.7кОм подключен правильно
   - Проверьте активацию 1-Wire в raspi-config

2. **Некорректные показания**:
   - Проверьте питание (3.3V, не 5V)
   - Убедитесь в надежности соединений

3. **Несколько датчиков**:
   - Каждый датчик имеет уникальный ID
   - Модифицируйте скрипт для поддержки нескольких устройств

## Дополнительные возможности

- Логирование температуры в файл
- Отправка данных на сервер
- Создание веб-интерфейса для мониторинга
- Настройка оповещений при превышении температуры

Теперь у вас должна работать система мониторинга температуры на Raspberry Pi Zero 2W!
