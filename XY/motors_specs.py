
motors_specs={
    'TMCM-1161':{
        "serial_addr":1,
        "ramp_mode":0,
        "max_current":255, # Max 255
        "standby_current":10, # Max 255
        "microstep_resolution": 3, # Remember to change beagleg config
        "freewheeling_delay":0,
        "steps_per_rotation":200,
        "max_acceleration":100,
        "max_positioning_speed":300,
        "direction":1, #Not implemented yed
        "step_direction_mode":1,
        "step_interpolation_enable":0
    }
}
