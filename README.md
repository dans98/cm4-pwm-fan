# How it works
You define a series of control points that represent a pwm temperature control curve like you would see in the bios of a typical desktop computer. The python script linearly interpolates the points, and adjusts the fan pwm duty cycle accordingly. The script also supports the following specialty features.

* Auto on/off - The fan will not turn on until the cpu temperature rises above the lowest temperature control point in the fan curve. If the temperature falls below the lowest control point, the fan will automatically shut off.
* Auto Max fan - If the cpu temperature goes above the highest control point temperature, the fan will automatically go to 100%. The fan will stay at 100% until the cpu temperature drops below the highest control point temperature.   

The following is an example pwm curve.
```Python
curve = {
30: 30,
45: 30,
47.5: 30.625,
50: 32,
52.5: 34.125,
55: 37,
57.5: 40.625,
60: 45,
62.5: 50.125,
65: 56,
67.5: 62.625,
70: 70,
}
```
![Fan Curve](https://raw.githubusercontent.com/dans98/cm4-pwm-fan/main/fanCurve.png)    


# Installation
1. in /boot/config.txt add "dtparam=i2c_vc=on" and comment out "dtparam=audio=on"
2. install the needed package
    ```
    sudo apt-get install python3-smbus
    ```
3. If you want to stress test your Pi using the included stress.py script, install the following package.
    ```
    sudo apt-get install stress
    ```

# stress testing
Included in the repo is a stess testing script thats generates a csv file. The csv file can be used to generate a graph like the one below.  Being able to easilly visualize everyhting allows you to tune the script tyo your needs.     
![Stress Test Results](https://raw.githubusercontent.com/dans98/cm4-pwm-fan/main/stress.png)    
