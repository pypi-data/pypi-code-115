from gym.envs.registration import register

register(
    id='Dym_Env-v0',
    entry_point='Dym_Env.envs:DymEnv',
)