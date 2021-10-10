from smbus import SMBus
from time import sleep

# keys are the cpu temperature, and values are the desired fan duty cycle in %
# keys and values must be numeric
# keys and values must lie between 0 and 100
# keys must be sorted in ascending order
#
# If the measured cpu temp is below the first keys value the pwm duty cycle 
# will be set to 0% (off)
#
# If the measured cpu temp is above the last keys value the pwm duty cycle 
# will be set to 100% (max)
curve = {
30: 30,
45: 32,
47: 34,
53: 55,
55: 57,
70: 59,
}

# the time in seconds between cpu temperature readings
interval = 0.1

# the number of readings used to calculate a moving temperate average. 
# Averaging multiple values helps reduce noise and thus fan hunting. 
readings = 30

# Even though the fan curve duty cycle is a float value between 0 and 100 the 
# EMC2301 is only an 8 bit devise. Thus after the duty cycle is calculated 
# in % it gets scaled and rounded to a discrete integer value (0-255).
# a min step size is a second level of noise reduction. if the current value 
# is not minSteps or more away from the previous value, the duty cycle 
# will not be set to the current value.   
minStep = 3

class pwmFan(object):
    def __init__(self, curve, interval, readings, minStep):
        self.curve = curve
        self.interval = interval
        self.readings = readings
        self.minStep = minStep
        self.validate()

        # connect to bus
        self.bus = SMBus(10)

        # EMC2301 address 
        self.address = 0X2F

        # fan max step size used internally by the EMC2301 
        # valid decimal values range between 0 and 63
        self.fanMaxStepReg = 0x37
        self.fanMaxStepVal = 0x0A   

        # fan configuration 1 - is used to set the EMC2301 drive mode and 
        # update interval. In Driect drive mode valid values are as follows  
        # 0x00 100ms update interval
        # 0x01 200ms update interval
        # 0x02 300ms update interval
        # 0x03 400ms update interval
        # 0x04 500ms update interval
        # 0x05 800ms update interval
        # 0x06 1200ms update interval
        # 0x07 1600ms update interval
        self.fanConOneReg = 0x32
        self.fanConOneVal = 0x00

        # fan configuration 2 - does not need to be changed when working in 
        # direct drive mode as its only need to enable ramp control.
        # ramp control uses max step size, & update interval to limit how fast 
        # the duty cycle can be changed 
        self.fanConTwoReg = 0x33
        self.fanConTwoVal = 0x40

        # fan PWM register 
        self.fanPwmReg = 0x30

        # the previous pwm value
        self.previousPwm = 0

        # the readings used to calculate the moving average
        self.samples = []

        # the temperature values from the fan curve
        self.temps = list(self.curve)

        # the number of line segments in the fan curve
        self.segments = len(self.temps) - 1

        # The minimum temperature in the fan curve
        self.min = self.temps[0]

        # The maximum temperature in the fan curve
        self.max = self.temps[-1]

    def updateReg(self, reg, val):
        self.bus.write_byte_data(self.address, reg, val)

    def getCpuTemp(self):
        f = open('/sys/class/thermal/thermal_zone0/temp')
        temp = float(f.read().strip())/1000
        f.close()
        return temp

    def getPwm(self, temp):
        if temp < self.min:
            # turn the fan off
            return 0;

        if temp > self.max:
            # run the fan at 100%
            return 255;

        i = 0
        while i < self.segments:
            if temp >= self.temps[i] and temp <= self.temps[i+1]:
                # linear interpolation of 2 points
                x1 = self.temps[i]
                x2 = self.temps[i+1]
                y1 = self.curve[x1]
                y2 = self.curve[x2]
                m = (y2 - y1) / (x2 - x1)
                b = y1 - m * x1
                y = m * temp + b
                return round(y / 100 * 255)

            i += 1

        # default to 100%
        return 255;

    def run(self):
        self.updateReg(self.fanMaxStepReg, self.fanMaxStepVal)
        self.updateReg(self.fanConOneReg, self.fanConOneVal) 
        self.updateReg(self.fanConTwoReg, self.fanConTwoVal) 
    
        while True:
            self.samples.append(self.getCpuTemp())

            if len(self.samples) > self.readings:
                self.samples.pop(0)

            avg = sum(self.samples)/len(self.samples)
            pwm = self.getPwm(avg)

            if pwm == 0:
                # ensure the fan can always be turned off regardless of 
                # what self.minStep is set to
                self.previousPwm = 0 
                self.updateReg(self.fanPwmReg, 0)
            elif pwm == 255:
                # ensure the fan can always be turned up to 100% regardless of
                # what self.minStep is set to
                self.previousPwm = 255 
                self.updateReg(self.fanPwmReg, 255)
            else:
                if abs(self.previousPwm - pwm) >= self.minStep:
                    self.previousPwm = pwm 
                    self.updateReg(self.fanPwmReg, pwm)

            sleep(self.interval)

    def validate(self):
        if not isinstance(self.curve, dict):
            raise Exception('Error - curve must be a dict')

        if not isinstance(self.interval, (int, float)):
            raise Exception('Error - interval is not numeric')

        if not isinstance(self.readings, int):
            raise Exception('Error - readings must be an integer')

        if not isinstance(self.minStep, int):
            raise Exception('Error - minStep must be an integer')

        if len(self.curve) < 2:
            raise Exception('Error - curve must contain at least 2 key:value pairs')

        previous = -1
        for key, val in self.curve.items():
            if not isinstance(key, (int, float)):
                raise Exception('Error - a curve key is not numeric')

            if not isinstance(val, (int, float)):
                raise Exception('Error - a curve value is not numeric')

            if key < 0 or key > 100:
                raise Exception('Error - a curve key is out of range')

            if val < 0 or val > 100:
                raise Exception('Error - a curve value is out of range')

            if key <= previous:
                raise Exception('Error - curve keys are not sorted in ascending order')
            else:
                previous = key
    
try:
    fan = pwmFan(curve, interval, readings, minStep)
    fan.run()
except (Exception) as e:
    print(e)
except KeyboardInterrupt:
    pass