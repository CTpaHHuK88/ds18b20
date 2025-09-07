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