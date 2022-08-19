################################################################################
#
# Compass module for pocket1090
#
# N.B. Currently hardwired to always return true north
#
# TODO
#  * implement the interface to the chosen flux-gate magnetometer
#
################################################################################

from enum import Enum

from Adafruit_BNO055 import BNO055

from __init__ import * #### FIXME


I2C_DEVICE = "/dev/i2c-2"


# From BNO055 datasheet section 4.3.58
class SystemStatus(Enum):
    SYSTEM_IDLE  = 0
    SYSTEM_ERROR = 1
    PERIPH_INIT  = 2
    SYSTEM_INIT  = 3
    SELF_TESTING = 4
    FUSION       = 5
    NO_FUSION    = 6

SYSTEM_STATUS = {
    SYSTEM_IDLE:  "System idle",
    SYSTEM_ERROR: "System error",
    PERIPH_INIT:  "Initializing peripherals",
    SYSTEM_INIT:  "System initialization",
    SELF_TESTING: "Executing self-test",
    FUSION:       "Sensor fusion algorithm running",
    NO_FUSION:    "System running without sensor fusion algorithm"
}

# From BNO055 datasheet section 4.3.59
# These codes are valid if the SYS_STATUS register == 0x01 (SYSTEM_ERROR)
class SystemErrorCode(Enum):
    NO_ERROR        = 0
    PERIPH_ERROR    = 1
    SYS_INIT_ERROR  = 2
    SELF_TEST_FAIL  = 3
    REG_MAP_VAL_OOR = 4
    REG_MAP_ADR_OOR = 5
    REG_MAP_WR_ERR  = 6
    NO_LOW_POWER    = 7
    NO_ACCL_POWER   = 8
    FUSION_ERROR    = 9
    SENSOR_ERROR    = 10

SYSTEM_ERROR_CODE = {
    NO_ERROR:        "No error",
    PERIPH_ERROR:    "Peripheral initialization error",
    SYS_INIT_ERROR:  "System initialization error",
    SELF_TEST_FAIL:  "Self-test result failed",
    REG_MAP_VAL_OOR: "Register map value out of range",
    REG_MAP_ADR_OOR: "Register map address out of range",
    REG_MAP_WR_ERR:  "Register map write error",
    NO_LOW_POWER:    "BNO low power mode not available",
    NO_ACCL_POWER:   "Accelerometer power mode not available",
    FUSION_ERROR:    "Fusion algorithm configuration error",
    SENSOR_ERROR:    "Sensor configuration error"
}

# From BNO055 datasheet section 4.3.59
class SelfTestResult(Enum):
    ACCEL_ST = (1 << 0)
    MAGNT_ST = (1 << 1)
    GYRO_ST  = (1 << 2)
    MCU_ST   = (1 << 3)

# bit vector -- if bit is set, the test passed
SELF_TEST_RESULTS = {
    ACCEL_ST: "Accelerometer",
    MAGNT_ST: "Magnetometer",
    GYRO_ST:  "Gyroscope",
    MCU_ST:   "MCU"
}

ALL_SELF_TEST_PASS = (ACCEL_ST & MAGNT_ST & GYRO_ST & MCU_ST)


class Compass():
    def __init__(self):
        self.bno = BNO055.BNO055(serial_port=I2C_DEVICE, rst=5)
        if not self.bno.begin():
            logging.error("Failed to init the compass")
            raise RuntimeError("BNO055 Initialization Error")

        status, selfTest, err = self.bno.get_system_status()
        msg = f"BNO055 Status: {SYSTEM_STATUS[status]} '0x{status:02X}'"
        if status == 0x01:
            msg += f", System Error: {SYSTEM_ERROR_CODE[err]} '0x{err:02X}'"
        logging.info(msg)
        if selfTest != ALL_SELF_TEST_PASS:
            failedUnits = [unitName for bitNumber, unitName in SELF_TEST_RESULTS.items() if (selfTest & bitNumber)]
            logging.info(f"BNO055 Self-Tests Failed: {failedUnits.join(",")}")

        sw, bl, accel, magn, gyro = self.bno.get_revision()
        logging.info(f"Software version: {sw}, Bootloader version: {bl}, Accelerometer Id: 0x{accel:02X}, Magnetometer Id: 0x{magn}, Gyroscope Id: 0x{gyro}")

    def calibrate(self):
        """ #### TODO
        """
        raise NotImplementedError("TBD")
        return self.getCalibrationStatus()

    def getCalibrationStatus(self):
        """Read and return the calibration status

           0=uncalibrated and 3=fully calibrated
          #### TODO
        """
        sys, gyro, accel, mag = self.bno.get_calibration_status()
        return sys, gyro, accel, mag

    def getEulerAngles(self):
        """Read and return the Euler angles for heading, roll, pitch (all in degrees)
          #### TODO
        """
        heading, roll, pitch = self.bno.read_euler()
        return heading, roll, pitch

    def getOrientation(self):
        """Read and return the orientation as a quaternion
          #### TODO
        """
        x, y, z, w = self.bno.read_quaterion()
        return x, y, z, w

    def getSensorTemp(self):
        """ #### TODO
          in degrees C
        """
        return self.bno.read_temp()

    def getMagnetometer(self):
        """ #### TODO
        in micro-Teslas
        """
        x, y, z = self.bno.read_magnetometer()
        return x, y, z

    def getGyroscope(self):
        """ #### TODO
          in degrees per second
        """
        x, y, z = self.bno.read_gyroscope()
        return x, y, z

    def getAccelerometer(self):
        """ #### TODO
          in meters per second squared
        """
        x, y, z = self.bno.read_accelerometer()
        return x, y, z

    def getLinearAcceleration(self):
        """ #### TODO
          acceleration from movement, not gravity-- in meters per second squared
        """
        x, y, z = self.bno.read_linear_acceleration()
        return x, y, z

    def getGravity(self):
        """ #### TODO
          acceleration just from gravity -- in meters per second squared
        """
        x, y, z = self.bno.read_gravity()
        return x, y, z

    def getAzimuth(self):
        return 0.0, 0.0

