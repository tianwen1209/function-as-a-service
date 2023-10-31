import sys
sys.path.append('./')

from hybrid_policy_c import main

if __name__ == "__main__":

    # function_id, app_id, start_time, trigger, function_duration, function_memory
    # function_list = [
    #     Function(0, 0, 0, 'HTTP', 3, 1), 
    #     Function(0, 0, 2, 'HTTP', 5, 1), 
    #     Function(0, 0, 7.5, 'HTTP', 4, 1), 
    #     Function(0, 0, 13, 'HTTP', 4, 1), 
    #     Function(2, 1, 5, 'HTTP', 4, 1),
    #     Function(3, 1, 11, 'HTTP', 1, 1),
    #     Function(4, 1, 15, 'HTTP', 4, 1),
    #     Function(5, 1, 20, 'HTTP', 1, 1)
    # ]
    for pt1 in [0,1,5]:
        for pt2 in [90, 95, 99]:
            for window_period in [0.5,0.65,0.75,0.85,0.9]:
                main(app=200,pt1=5,pt2=95,window_period=window_period)