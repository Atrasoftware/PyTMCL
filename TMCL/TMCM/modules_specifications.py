
motors_specs={
    'PD281021':{
        "num_motors":1,
        "num_banks":4,
        "max_output":(2), #output
        "max_velocity":2000000, #pps
        "max_coordinate":21,
        "max_position":2**23, #steps
        "max_current":256, #mA, TMCM 1021 Hardware manual
    }

    'TMCM-1161':{
        "num_motors":1,
        "num_banks":4,
        "max_output":(2), #output
        "max_velocity":2047, #pps
        "max_acceleration":2047, #pps
        "max_coordinate":21,
        "max_position":2**23, #steps
        "max_current":256, #mA, TMCM 1021 Hardware manual
    }
}
