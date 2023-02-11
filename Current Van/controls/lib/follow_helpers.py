from dataclasses import dataclass
from common.numpy_fast import interp

# Variables that change braking profiles
ONE_BAR_DISTANCE = 1.0
TWO_BAR_DISTANCE = 1.3
THREE_BAR_DISTANCE = .95
FOUR_BAR_DISTANCE = 1.8
STOPPING_DISTANCE = 0.5
SNG_DISTANCE = 1.8
SNG_SPEED = 5
CITY_SPEED = 16
HIGHWAY_SPEED = 27
COSTS_TR = [0.9, 1.8, 2.0]
COSTS_DISTANCE = [1., 0.1, 0.1]


@dataclass
class vEgoProfile:
  vEgo: float
  v_rel: list
  TR: list

@dataclass
class FollowProfile:
  vEgoProfiles: tuple

  def __post_init__(self):
    self.speeds = []
    self.arrs = []

    for profile in sorted(self.vEgoProfiles, key=lambda profile: profile.vEgo):
      self.speeds.append(profile.vEgo)
      self.arrs.append((profile.v_rel, profile.TR))


ONE_BAR_PROFILE = FollowProfile(
  vEgoProfiles=(
    vEgoProfile(vEgo=SNG_SPEED, v_rel=[0], TR=[SNG_DISTANCE]),
    vEgoProfile(vEgo=CITY_SPEED, v_rel=[-0.1, 2.75], TR=[ONE_BAR_DISTANCE, 2.1]),
    vEgoProfile(vEgo=HIGHWAY_SPEED, v_rel=[-0.01, 1.25], TR=[ONE_BAR_DISTANCE, ONE_BAR_DISTANCE-0.2]),))
TWO_BAR_PROFILE = FollowProfile(
  vEgoProfiles=(
    vEgoProfile(vEgo=SNG_SPEED, v_rel=[0], TR=[SNG_DISTANCE]),
    vEgoProfile(vEgo=CITY_SPEED, v_rel=[-0.1, 1.5], TR=[TWO_BAR_DISTANCE, 2.1]),
    vEgoProfile(vEgo=HIGHWAY_SPEED, v_rel=[0.0, 3.0], TR=[TWO_BAR_DISTANCE, TWO_BAR_DISTANCE+0.0]),))
THREE_BAR_PROFILE = FollowProfile(
  vEgoProfiles=(
    vEgoProfile(vEgo=SNG_SPEED, v_rel=[0], TR=[SNG_DISTANCE]),
    vEgoProfile(vEgo=CITY_SPEED,  v_rel=[0, 4.0], TR=[THREE_BAR_DISTANCE, 2.1]),
    vEgoProfile(vEgo=HIGHWAY_SPEED, v_rel=[0.0, 4.0], TR=[THREE_BAR_DISTANCE, THREE_BAR_DISTANCE+0.0]),))
FOUR_BAR_PROFILE = FollowProfile(
  vEgoProfiles=(
    vEgoProfile(vEgo=SNG_SPEED, v_rel=[0], TR=[SNG_DISTANCE]),
    vEgoProfile(vEgo=CITY_SPEED, v_rel=[0], TR=[FOUR_BAR_DISTANCE]),
    vEgoProfile(vEgo=HIGHWAY_SPEED, v_rel=[0], TR=[FOUR_BAR_DISTANCE]),))
DEFAULT_PROFILE = FollowProfile(
  vEgoProfiles=(
    vEgoProfile(vEgo=SNG_SPEED, v_rel=[0], TR=[SNG_DISTANCE]),))

PROFILES = {
  1: ONE_BAR_PROFILE,
  2: TWO_BAR_PROFILE,
  3: THREE_BAR_PROFILE,
  4: FOUR_BAR_PROFILE,
}


def get_distance_cost(TR):
  return interp(TR, COSTS_TR, COSTS_DISTANCE)


def get_follow_profile(CS):
  return PROFILES.get(CS.readdistancelines, DEFAULT_PROFILE)
