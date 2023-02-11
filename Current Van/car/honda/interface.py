#!/usr/bin/env python3
from cereal import car
from panda import Panda
from common.numpy_fast import interp
from common.params import Params
from common.realtime import DT_CTRL
from selfdrive.swaglog import cloudlog
from selfdrive.controls.lib.events import ET
from selfdrive.car.honda.hondacan import disable_radar
from selfdrive.car.honda.values import CarControllerParams, CruiseButtons, CruiseSetting, CAR, HONDA_BOSCH, HONDA_BOSCH_ALT_BRAKE_SIGNAL
from selfdrive.car import STD_CARGO_KG, CivicParams, scale_rot_inertia, scale_tire_stiffness, gen_empty_fingerprint
from selfdrive.car.interfaces import CarInterfaceBase, ACCEL_MAX, ACCEL_MIN
from selfdrive.config import Conversions as CV


ButtonType = car.CarState.ButtonEvent.Type
EventName = car.CarEvent.EventName
TransmissionType = car.CarParams.TransmissionType


class CarInterface(CarInterfaceBase):
  def __init__(self, CP, CarController, CarState):
    super().__init__(CP, CarController, CarState)

    self.last_enable_pressed = 0
    self.last_enable_sent = 0

  @staticmethod
  def get_pid_accel_limits(CP, current_speed, cruise_speed):
    # NIDECs don't allow acceleration near cruise_speed,
    # so limit limits of pid to prevent windup
    ACCEL_MAX_VALS = [ACCEL_MAX, 3.2]
    ACCEL_MAX_BP = [cruise_speed - 2.0, cruise_speed - .2]
    return ACCEL_MIN, ACCEL_MAX

  @staticmethod
  def get_params(candidate, fingerprint=gen_empty_fingerprint(), car_fw=[]):  # pylint: disable=dangerous-default-value
    ret = CarInterfaceBase.get_std_params(candidate, fingerprint)
    ret.carName = "honda"

    if candidate in HONDA_BOSCH:
      ret.safetyModel = car.CarParams.SafetyModel.hondaBoschHarness
      ret.radarOffCan = True

      # Disable the radar and let openpilot control longitudinal
      # WARNING: THIS DISABLES AEB!
      ret.openpilotLongitudinalControl = Params().get_bool("DisableRadar")

      ret.pcmCruise = not ret.openpilotLongitudinalControl
      ret.communityFeature = ret.openpilotLongitudinalControl
    else:
      ret.safetyModel = car.CarParams.SafetyModel.hondaNidec
      ret.enableGasInterceptor = 0x201 in fingerprint[0]
      ret.openpilotLongitudinalControl = True

      ret.pcmCruise = not ret.enableGasInterceptor
      ret.communityFeature = ret.enableGasInterceptor

    if candidate == CAR.CRV_5G:
      ret.enableBsm = 0x12f8bfa7 in fingerprint[0]

    # Accord 1.5T CVT has different gearbox message
    if candidate == CAR.ACCORD and 0x191 in fingerprint[1]:
      ret.transmissionType = TransmissionType.cvt

    # Certain Hondas have an extra steering sensor at the bottom of the steering rack,
    # which improves controls quality as it removes the steering column torsion from feedback.
    # Tire stiffness factor fictitiously lower if it includes the steering column torsion effect.
    # For modeling details, see p.198-200 in "The Science of Vehicle Dynamics (2014), M. Guiggiani"
    ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0], [0]]
    ret.lateralTuning.pid.kiBP, ret.lateralTuning.pid.kpBP = [[0.], [0.]]
    ret.lateralTuning.pid.kf = 0.00006  # conservative feed-forward

    # https://github.com/commaai/openpilot/wiki/Tuning#how-the-breakpoint-and-value-lists-work
    # default longitudinal tuning for all hondas
    if Params().get_bool('ChillTune'):
      # default longitudinal tuning for all hondas
      ret.longitudinalTuning.kpBP = [0., 5., 35.]
      ret.longitudinalTuning.kpV = [1.2, 0.8, 0.5]
      ret.longitudinalTuning.kiBP = [0., 35.]
      ret.longitudinalTuning.kiV = [0.24, 0.18]
      
    eps_modified = False
    for fw in car_fw:
      if fw.ecu == "eps" and b"," in fw.fwVersion:
        eps_modified = True

    if candidate == CAR.CIVIC:
      stop_and_go = True
      ret.mass = CivicParams.MASS
      ret.wheelbase = CivicParams.WHEELBASE
      ret.centerToFront = CivicParams.CENTER_TO_FRONT
      ret.steerRatio = 15.38  # 10.93 is end-to-end spec
      if eps_modified:
        # stock request input values:     0x0000, 0x00DE, 0x014D, 0x01EF, 0x0290, 0x0377, 0x0454, 0x0610, 0x06EE
        # stock request output values:    0x0000, 0x0917, 0x0DC5, 0x1017, 0x119F, 0x140B, 0x1680, 0x1680, 0x1680
        # modified request output values: 0x0000, 0x0917, 0x0DC5, 0x1017, 0x119F, 0x140B, 0x1680, 0x2880, 0x3180
        # stock filter output values:     0x009F, 0x0108, 0x0108, 0x0108, 0x0108, 0x0108, 0x0108, 0x0108, 0x0108
        # modified filter output values:  0x009F, 0x0108, 0x0108, 0x0108, 0x0108, 0x0108, 0x0108, 0x0400, 0x0480
        # note: max request allowed is 4096, but request is capped at 3840 in firmware, so modifications result in 2x max
        ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 2560, 8000], [0, 2560, 3840]]
        ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.3], [0.1]]
      else:
        ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 2560], [0, 2560]]
        ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[1.1], [0.33]]
      tire_stiffness_factor = 1.

    elif candidate in (CAR.CIVIC_BOSCH, CAR.CIVIC_BOSCH_DIESEL):
      stop_and_go = True
      ret.mass = CivicParams.MASS
      ret.wheelbase = CivicParams.WHEELBASE
      ret.centerToFront = CivicParams.CENTER_TO_FRONT
      ret.steerRatio = 15.38  # 10.93 is end-to-end spec
      if eps_modified:
        ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 2564, 8000], [0, 2564, 3840]]
        ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.4], [0.12]]
      else:
        ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 4096], [0, 4096]]  # TODO: determine if there is a dead zone at the top end
        ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.8], [0.24]]
      tire_stiffness_factor = 1.

    elif candidate in (CAR.ACCORD, CAR.ACCORDH):
      stop_and_go = True
      ret.mass = 3279. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 2.83
      ret.centerToFront = ret.wheelbase * 0.39
      ret.steerRatio = 16.33  # 11.82 is spec end-to-end
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 4096], [0, 4096]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.8467

      if eps_modified:
        ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.3], [0.09]]
      else:
        ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.6], [0.18]]
        
    elif candidate == CAR.ACURA_ILX:
      stop_and_go = False
      ret.mass = 3095. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 2.67
      ret.centerToFront = ret.wheelbase * 0.37
      ret.steerRatio = 18.61  # 15.3 is spec end-to-end
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 3840], [0, 3840]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.72
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.8], [0.24]]

    elif candidate in (CAR.CRV, CAR.CRV_EU):
      stop_and_go = False
      ret.mass = 3572. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 2.62
      ret.centerToFront = ret.wheelbase * 0.41
      ret.steerRatio = 16.89  # as spec
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 1000], [0, 1000]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.444
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.8], [0.24]]

    elif candidate == CAR.CRV_5G:
      stop_and_go = True
      ret.mass = 3410. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 2.66
      ret.centerToFront = ret.wheelbase * 0.41
      ret.steerRatio = 16.0  # 12.3 is spec end-to-end
      if eps_modified:
        # stock request input values:     0x0000, 0x00DB, 0x01BB, 0x0296, 0x0377, 0x0454, 0x0532, 0x0610, 0x067F
        # stock request output values:    0x0000, 0x0500, 0x0A15, 0x0E6D, 0x1100, 0x1200, 0x129A, 0x134D, 0x1400
        # modified request output values: 0x0000, 0x0500, 0x0A15, 0x0E6D, 0x1100, 0x1200, 0x1ACD, 0x239A, 0x2800
        ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 2560, 10000], [0, 2560, 3840]]
        ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.21], [0.07]]
      else:
        ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 3840], [0, 3840]]
        ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.64], [0.192]]
      tire_stiffness_factor = 0.677

    elif candidate == CAR.CRV_HYBRID:
      stop_and_go = True
      ret.mass = 1667. + STD_CARGO_KG  # mean of 4 models in kg
      ret.wheelbase = 2.66
      ret.centerToFront = ret.wheelbase * 0.41
      ret.steerRatio = 16.0  # 12.3 is spec end-to-end
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 4096], [0, 4096]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.677
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.6], [0.18]]

    elif candidate == CAR.FIT:
      stop_and_go = False
      ret.mass = 2644. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 2.53
      ret.centerToFront = ret.wheelbase * 0.39
      ret.steerRatio = 13.06
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 4096], [0, 4096]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.75
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.2], [0.05]]

    elif candidate == CAR.HRV:
      stop_and_go = False
      ret.mass = 3125 * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 2.61
      ret.centerToFront = ret.wheelbase * 0.41
      ret.steerRatio = 15.2
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 4096], [0, 4096]]
      tire_stiffness_factor = 0.5
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.16], [0.025]]

    elif candidate == CAR.ACURA_RDX:
      stop_and_go = False
      ret.mass = 3935. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 2.68
      ret.centerToFront = ret.wheelbase * 0.38
      ret.steerRatio = 15.0  # as spec
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 1000], [0, 1000]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.444
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.8], [0.24]]

    elif candidate == CAR.ACURA_RDX_3G:
      stop_and_go = True
      ret.mass = 4068. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 2.75
      ret.centerToFront = ret.wheelbase * 0.41
      ret.steerRatio = 16.0 #11.95 is spec
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 3840], [0, 3840]]
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.4], [0.12]]
      tire_stiffness_factor = 0.8
      ret.lateralTuning.pid.kf = 0.00007818594

    elif candidate == CAR.ODYSSEY:
      stop_and_go = False
      ret.mass = 4471. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 3.00
      ret.centerToFront = ret.wheelbase * 0.41
      ret.steerRatio = 16.00  # as spec
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 4096], [0, 4096]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.82
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.28], [0.08]]

    elif candidate == CAR.ODYSSEY_CHN:
      stop_and_go = False
      ret.mass = 1849.2 + STD_CARGO_KG  # mean of 4 models in kg
      ret.wheelbase = 2.90
      ret.centerToFront = ret.wheelbase * 0.41  # from CAR.ODYSSEY
      ret.steerRatio = 14.35
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 32767], [0, 32767]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.82
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.28], [0.08]]

    elif candidate in (CAR.PILOT, CAR.PILOT_2019):
      stop_and_go = False
      ret.mass = 4204. * CV.LB_TO_KG + STD_CARGO_KG  # average weight
      ret.wheelbase = 2.82
      ret.centerToFront = ret.wheelbase * 0.428
      ret.steerRatio = 17.25  # as spec
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 4096], [0, 4096]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.444
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.38], [0.11]]

    elif candidate == CAR.RIDGELINE:
      stop_and_go = False
      ret.mass = 4515. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 3.18
      ret.centerToFront = ret.wheelbase * 0.41
      ret.steerRatio = 15.59  # as spec
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 4096], [0, 4096]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.444
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.38], [0.11]]

    elif candidate == CAR.INSIGHT:
      stop_and_go = True
      ret.mass = 2987. * CV.LB_TO_KG + STD_CARGO_KG
      ret.wheelbase = 2.7
      ret.centerToFront = ret.wheelbase * 0.39
      ret.steerRatio = 15.0  # 12.58 is spec end-to-end
      ret.lateralParams.torqueBP, ret.lateralParams.torqueV = [[0, 4096], [0, 4096]]  # TODO: determine if there is a dead zone at the top end
      tire_stiffness_factor = 0.82
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.6], [0.18]]

    else:
      raise ValueError("unsupported car %s" % candidate)

    # These cars use alternate user brake msg (0x1BE)
    if candidate in HONDA_BOSCH_ALT_BRAKE_SIGNAL:
      ret.safetyParam |= Panda.FLAG_HONDA_ALT_BRAKE

    if ret.openpilotLongitudinalControl and candidate in HONDA_BOSCH:
      ret.safetyParam |= Panda.FLAG_HONDA_BOSCH_LONG

    # min speed to enable ACC. if car can do stop and go, then set enabling speed
    # to a negative value, so it won't matter. Otherwise, add 0.5 mph margin to not
    # conflict with PCM acc
    ret.minEnableSpeed = -1. if (stop_and_go or ret.enableGasInterceptor) else 25.5 * CV.MPH_TO_MS

    # TODO: get actual value, for now starting with reasonable value for
    # civic and scaling by mass and wheelbase
    ret.rotationalInertia = scale_rot_inertia(ret.mass, ret.wheelbase)

    # TODO: start from empirically derived lateral slip stiffness for the civic and scale by
    # mass and CG position, so all cars will have approximately similar dyn behaviors
    ret.tireStiffnessFront, ret.tireStiffnessRear = scale_tire_stiffness(ret.mass, ret.wheelbase, ret.centerToFront,
                                                                         tire_stiffness_factor=tire_stiffness_factor)

    ret.startAccel = 0.5

    ret.steerActuatorDelay = 0.1
    ret.steerRateCost = 0.5
    ret.steerLimitTimer = 0.8

    return ret

  @staticmethod
  def init(CP, logcan, sendcan):
    if CP.carFingerprint in HONDA_BOSCH and CP.openpilotLongitudinalControl:
      disable_radar(logcan, sendcan)

  # returns a car.CarState
  def update(self, c, can_strings):
    # ******************* do can recv *******************
    self.cp.update_strings(can_strings)
    self.cp_cam.update_strings(can_strings)
    if self.cp_body:
      self.cp_body.update_strings(can_strings)

    ret = self.CS.update(self.cp, self.cp_cam, self.cp_body)

    ret.canValid = self.cp.can_valid and self.cp_cam.can_valid and (self.cp_body is None or self.cp_body.can_valid)
    ret.yawRate = self.VM.yaw_rate(ret.steeringAngleDeg * CV.DEG_TO_RAD, ret.vEgo)

    ret.lkasEnabled = self.CS.lkasEnabled
    ret.accEnabled = self.CS.accEnabled
    ret.leftBlinkerOn = self.CS.leftBlinkerOn
    ret.rightBlinkerOn = self.CS.rightBlinkerOn
    ret.automaticLaneChange = self.CS.automaticLaneChange
    ret.belowLaneChangeSpeed = self.CS.belowLaneChangeSpeed
    ret.readdistancelines = self.CS.read_distance_lines
    ret.engineRPM = self.CS.engineRPM
    
    buttonEvents = []

    if self.CS.cruise_buttons != self.CS.prev_cruise_buttons:
      be = car.CarState.ButtonEvent.new_message()
      be.type = ButtonType.unknown
      if self.CS.cruise_buttons != 0:
        be.pressed = True
        but = self.CS.cruise_buttons
      else:
        be.pressed = False
        but = self.CS.prev_cruise_buttons
      if but == CruiseButtons.RES_ACCEL:
        be.type = ButtonType.accelCruise
      elif but == CruiseButtons.DECEL_SET:
        be.type = ButtonType.decelCruise
      elif but == CruiseButtons.CANCEL:
        be.type = ButtonType.cancel
      elif but == CruiseButtons.MAIN:
        be.type = ButtonType.altButton3
      buttonEvents.append(be)

    if self.CS.cruise_setting != self.CS.prev_cruise_setting:
      be = car.CarState.ButtonEvent.new_message()
      be.type = ButtonType.unknown
      if self.CS.cruise_setting != 0:
        be.pressed = True
        but = self.CS.cruise_setting
      else:
        be.pressed = False
        but = self.CS.prev_cruise_setting
      if but == CruiseSetting.LKAS_BUTTON:
        be.type = ButtonType.altButton1
      # TODO: more buttons?
      buttonEvents.append(be)
    ret.buttonEvents = buttonEvents

    extraGears = [car.CarState.GearShifter.sport, car.CarState.GearShifter.low]

    extraGears = []
    if not (self.CS.CP.openpilotLongitudinalControl or self.CS.CP.enableGasInterceptor):
      extraGears = [car.CarState.GearShifter.sport, car.CarState.GearShifter.low]

    # events
    events = self.create_common_events(ret, extra_gears=extraGears, pcm_enable=False)
    if self.CS.brake_error:
      events.add(EventName.brakeUnavailable)
    if self.CS.brake_hold and self.CS.CP.openpilotLongitudinalControl:
      if (self.CS.lkasEnabled):
        self.CS.disengageByBrake = True
      if (ret.cruiseState.enabled):
        events.add(EventName.brakeHold)
      else:
        events.add(EventName.silentBrakeHold)
    if self.CS.park_brake:
      events.add(EventName.parkBrake)

    #if self.CP.pcmCruise and ret.vEgo < self.CP.minEnableSpeed:
      #events.add(EventName.belowEngageSpeed)

    self.CS.disengageByBrake = self.CS.disengageByBrake or ret.disengageByBrake

    #if self.CP.pcmCruise:
      # we engage when pcm is active (rising edge)
      #if ret.cruiseState.enabled and not self.CS.out.cruiseState.enabled:
        #events.add(EventName.pcmEnable)
      #if not ret.cruiseState.enabled and (c.actuators.brake <= 0. or not self.CP.openpilotLongitudinalControl):
        # it can happen that car cruise disables while comma system is enabled: need to
        # keep braking if needed or if the speed is very low
        #if ret.vEgo < self.CP.minEnableSpeed + 2.:
          # non loud alert if cruise disables below 25mph as expected (+ a little margin)
          #events.add(EventName.speedTooLow)
        #else:
          #events.add(EventName.cruiseDisabled)

    if self.CS.CP.minEnableSpeed > 0 and ret.vEgo < 0.001:
      events.add(EventName.manualRestart)

    cur_time = self.frame * DT_CTRL
    enable_pressed = False
    enable_from_brake = False

    if self.CS.disengageByBrake and not ret.brakePressed and not self.CS.brake_hold and self.CS.lkasEnabled:
      self.last_enable_pressed = cur_time
      enable_pressed = True
      enable_from_brake = True

    if not ret.brakePressed and not self.CS.brake_hold:
      self.CS.disengageByBrake = False
      ret.disengageByBrake = False
    
    # handle button presses
    for b in ret.buttonEvents:

      # do enable on both accel and decel buttons
      if b.type in [ButtonType.accelCruise, ButtonType.decelCruise] and not b.pressed:
        self.last_enable_pressed = cur_time
        enable_pressed = True

      # do disable on LKAS button if ACC is disabled
      if b.type in [ButtonType.altButton1] and b.pressed:
        if not self.CS.lkasEnabled: #disabled LKAS
          if not ret.cruiseState.enabled:
            events.add(EventName.buttonCancel)
          else:
            events.add(EventName.manualSteeringRequired)
        else: #enabled LKAS
          if not ret.cruiseState.enabled:
            self.last_enable_pressed = cur_time
            enable_pressed = True

      # do disable on button down
      if b.type == ButtonType.cancel and b.pressed:
        if not self.CS.lkasEnabled:
          events.add(EventName.buttonCancel)
        else:
          events.add(EventName.manualLongitudinalRequired)

    if self.CP.pcmCruise:
      # KEEP THIS EVENT LAST! send enable event if button is pressed and there are
      # NO_ENTRY events, so controlsd will display alerts. Also not send enable events
      # too close in time, so a no_entry will not be followed by another one.
      # TODO: button press should be the only thing that triggers enable
      if ((cur_time - self.last_enable_pressed) < 0.2 and
          (cur_time - self.last_enable_sent) > 0.2 and
          (ret.cruiseState.enabled or self.CS.lkasEnabled)) or \
         (enable_pressed and events.any(ET.NO_ENTRY)):
        if enable_from_brake:
          events.add(EventName.silentButtonEnable)
        else:
          events.add(EventName.buttonEnable)
        self.last_enable_sent = cur_time
    elif enable_pressed:
      if enable_from_brake:
        events.add(EventName.silentButtonEnable)
      else:
        events.add(EventName.buttonEnable)

    ret.events = events.to_msg()

    self.CS.out = ret.as_reader()
    return self.CS.out

  # pass in a car.CarControl
  # to be called @ 100hz
  def apply(self, c):
    if c.hudControl.speedVisible:
      hud_v_cruise = c.hudControl.setSpeed * CV.MS_TO_KPH
    else:
      hud_v_cruise = 255

    can_sends = self.CC.update(c.enabled, self.CS, self.frame,
                               c.actuators,
                               c.cruiseControl.cancel,
                               hud_v_cruise,
                               c.hudControl.lanesVisible,
                               hud_show_car=c.hudControl.leadVisible,
                               hud_alert=c.hudControl.visualAlert)

    self.frame += 1
    return can_sends
