from multiprocessing import cpu_count
from subprocess import Popen, check_output 
from time import time, sleep
from smbus import SMBus
import os, signal

# the file that data should be logged to 
filename = '/home/pi/stress.csv'

# how many idle seconds should be logged before and after the stress test
idle = 60

# how many seconds should the stress test last
duration = 300

# the interval between data logging events. 
interval = 1.0

class stress(object):
    def __init__(self, filename, idle, duration, interval):
        self.filename = filename
        self.idle = idle
        self.duration = duration
        self.interval = interval

        self.bus = SMBus(10)
        self.address = 0X2F
        self.fanPwmReg = 0x30

        self.stress = None
        self.fp = None

    def getCpuTemp(self):
        f = open('/sys/class/thermal/thermal_zone0/temp')
        temp = float(f.read().strip()) / 1000
        f.close()
        return '{:.2f}'.format(round(temp,2))

    def getCpuFreq(self):
        out = check_output(["vcgencmd", "measure_clock arm"]).decode("utf-8")
        return '{:.2f}'.format(round(float(out.split("=")[1]) / 1000000,2))

    def getPwm(self):
        pwm = self.bus.read_byte_data(self.address, self.fanPwmReg)
        #pwm = 10
        return '{:.2f}'.format(round(pwm / 255 * 100,2))

    def openFile(self):
        if self.fp is None:
            self.fp = open(self.filename, 'w')
            labels = [
                'Time (s)',
                'Temperature (C)', 
                'CPU Frequency (MHz)', 
                'PWM Duty Cycle (%)'
            ]
            self.writeToFile(labels)

    def closeFile(self):
        if self.fp is not None:
            self.fp.close()
            self.fp = None

    def writeToFile(self, args):
        self.openFile()
        self.fp.write(','.join(args) + "\n")

    def logData(self, time):
        args = [
            str(round(time,2)),
            self.getCpuTemp(),
            self.getCpuFreq(),
            self.getPwm()
        ]
        self.writeToFile(args)

        args = [
            '{:>10}'.format('{:.2f}'.format(round(time,2)) + 's'),
            '{:>7}'.format(self.getCpuTemp() + 'c'),
            '{:>10}'.format(self.getCpuFreq() + 'MHz'),
            '{:>7}'.format(self.getPwm() + '%')
        ]
        print('  '.join(args))

    def startStress(self):
        if self.stress is None:
            cpus = cpu_count()
            self.stress = Popen(['stress', '-q', '-c', str(cpus), '-t', str(self.duration)], preexec_fn=os.setsid);

    def stopStress(self):
        if self.stress is not None:
            os.killpg(self.stress.pid, signal.SIGINT)
            self.stress = None

    def run(self):
        start = time()

        now = time()
        ref = self.idle
        while now - start <= ref:
            self.logData(now - start)
            sleep(self.interval)
            now = time()

        self.startStress()

        ref = self.idle + self.duration
        while now - start <= ref:
            self.logData(now - start)
            sleep(self.interval)
            now = time() 

        self.stopStress()

        ref = self.idle + self.duration + self.idle
        while now - start <= ref:
            self.logData(now - start)
            sleep(self.interval)
            now = time() 

try:
    stress = stress(filename, idle, duration, interval)
    stress.run()
except (Exception) as e:
    print(e)
except KeyboardInterrupt:
    pass
finally:
    stress.closeFile()
    stress.stopStress()




