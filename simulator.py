from Function import Function
import numpy as np



class Simulator:
    def __init__(self, workload):
        """_summary_

        Args:
            workload (list of Function objects): _description_
        """
        self.seconds_one_day = 24*60*60
        self.current_time = 0
        self.start_cold = 0
        self.start_warm = 0
        # {key: application id, value: [application object, list of invocations, load_time, last_finish_time, pre_warm_time, keep_alive_time]}
        self.application_in_memory = {}
        self.max_memory = 0

        if isinstance(workload, str):
            self.workload = []
            function_array = np.load(workload)
            function_array = function_array.astype(object) 
            print("size of workload: ", function_array.shape[0]) #size of workload:  3691
            '''
            def __init__(self, function_id, app_id, start_time, trigger, function_duration, function_memory)
            print(function_array[0][0]) function_id
            print(function_array[0][1]) app_id
            print(function_array[0][2]) start_time
            print(function_array[0][3]) trigger
            print(function_array[0][4]) function_duration
            print(function_array[0][5]) function_memory                   
            21
            2
            10091.231581854454
            http
            7.047086412106442
            144.303358036344
            '''
            for i in range(len(function_array)):
                self.workload.append(Function(function_array[i][0], function_array[i][1], float(function_array[i][2]), function_array[i][3], float(function_array[i][4]), float(function_array[i][5])))            
        else:
            self.workload = workload
        self.workload = self.workload[:10]
        self.wasted_memory_time = 0
    def simulation_fixed_keep_alive(self, keep_live_time):
        self.workload.sort(key=lambda x:x.start_time)
        for invocation in self.workload:
            self.current_time = invocation.start_time
            self.check_alive(keep_live_time)

            # if the application is not in memory, cold start
            if not invocation.app_id in self.application_in_memory:
                self.start_cold += 1
                self.application_in_memory[invocation.app_id] = [invocation.app, invocation, invocation.start_time, invocation.end_time, invocation.end_time + keep_live_time]
             # if the application is already in memory, warm start
            else:
                self.start_warm += 1
                current_app_state = self.application_in_memory[invocation.app_id]
                # update memory waste time
                if current_app_state[3] < invocation.start_time:
                    self.wasted_memory_time += invocation.start_time - current_app_state[3]
                current_app_state[1] = invocation
                # if the new invocation of the application ends later than all existing invocations, updated the end_time and keep_alive_until time
                if invocation.end_time > current_app_state[3]:
                    current_app_state[3] = invocation.end_time
                    current_app_state[4] = invocation.end_time + keep_live_time
                # if the new invocation uses more memory, update memory usage
                if invocation.app.app_memory > current_app_state[0].app_memory:
                    current_app_state[0] = invocation.app
            
            current_memory_usage = self.get_memory_usage()
            if current_memory_usage > self.max_memory:
                self.max_memory = current_memory_usage

    def add_invocation(self, invocation, keep_live_time, pre_warm_time):
        # if the application is not in memory, cold start
        if not invocation.app_id in self.application_in_memory:
            self.start_cold += 1
            self.application_in_memory[invocation.app_id] = [invocation.app, invocation, invocation.start_time, invocation.end_time, pre_warm_time, keep_live_time]
            # if the application has been loaded before, check if warm start
        else:
            current_app_state = self.application_in_memory[invocation.app_id]
            # if warm start
            last_finish_time = current_app_state[3]
            if last_finish_time > invocation.start_time:
                self.start_warm += 1
                # updated the end_time and keep_alive_until time
                if invocation.end_time > last_finish_time:
                    current_app_state[1] = invocation
                    current_app_state[3] = invocation.end_time
                    current_app_state[4] = pre_warm_time
                    current_app_state[5] = keep_live_time
            else:
                previous_pre_warm_time = current_app_state[4]
                pre_warm_load_time = last_finish_time + previous_pre_warm_time
                if pre_warm_load_time <= self.current_time:
                    self.start_warm += 1
                    # update memory waste time (only happens for the case of pre-warm)
                    self.wasted_memory_time += invocation.start_time - current_app_state[2]
                    current_app_state[1] = invocation
                    current_app_state[3] = invocation.end_time
                    current_app_state[4] = pre_warm_time
                    current_app_state[5] = keep_live_time
                else:
                    self.start_cold += 1
                    self.application_in_memory[invocation.app_id] = [invocation.app, invocation, invocation.start_time, invocation.end_time, pre_warm_time, keep_live_time]

    def simulation_pre_warm(self, keep_live_time, pre_warm_time):
        self.workload.sort(key=lambda x:x.start_time)
        for invocation in self.workload:
            self.current_time = invocation.start_time
            self.check_alive_pre_warm(invocation.app_id)
            # print(self.application_in_memory)
            self.add_invocation(invocation=invocation, pre_warm_time=pre_warm_time, keep_live_time=keep_live_time)
            
            current_memory_usage = self.get_memory_usage()
            if current_memory_usage > self.max_memory:
                self.max_memory = current_memory_usage

    def get_memory_usage(self):
        total_memory = 0
        for app_id in self.application_in_memory:
            last_finish_time = self.application_in_memory[app_id][3]
            if last_finish_time > self.current_time:
                current_memory= self.application_in_memory[app_id][1].function_memory
                total_memory += current_memory
        return total_memory

    def check_alive(self, keep_live_time):
        for app_id in self.application_in_memory:
            current_app_alive_until = self.application_in_memory[app_id][4]
            if current_app_alive_until <= self.current_time:
                # update memory waste time
                self.wasted_memory_time += keep_live_time
                del self.application_in_memory[app_id]
    
    def check_alive_pre_warm(self, app_id):
        if app_id in self.application_in_memory:
        # {key: application id, value: [application object, list of invocations, load_time, last_finish_time, pre_warm_time, keep_live_time]}
            pre_warm_time = self.application_in_memory[app_id][4]
            keep_live_time = self.application_in_memory[app_id][5]
            last_finish_time = self.application_in_memory[app_id][3]
            # if prewarm+keep live finishes before current time, record wast time.
            if last_finish_time < self.current_time:
                # print(current_app_alive_until)
                # print(pre_warm_time)
                pre_warm_load_time = last_finish_time + pre_warm_time
                if pre_warm_load_time <= self.current_time:
                    if pre_warm_load_time + keep_live_time < self.current_time:
                        del self.application_in_memory[app_id]
                        # update memory waste time
                        self.wasted_memory_time += keep_live_time
        else:
            return


    def get_all_app_full_IT_trace(self):
        # output a dict, key: app_id, value: [helper (useless), list of IT, list of idle end time]
        self.workload.sort(key=lambda x:x.start_time)
        all_app_full_IT_trace = {}
        for invocation in self.workload:
            if invocation.app_id not in all_app_full_IT_trace.keys():
                last_call_end_time = invocation.start_time + invocation.function_duration
                idle_duration=[]
                idle_end_time=[]
                all_app_full_IT_trace[invocation.app_id] = [last_call_end_time, idle_duration, idle_end_time]
            else:
                if invocation.start_time > all_app_full_IT_trace[invocation.app_id][0]:
                    idle_time = invocation.start_time - all_app_full_IT_trace[invocation.app_id][0]
                    all_app_full_IT_trace[invocation.app_id][2].append(invocation.start_time)
                    all_app_full_IT_trace[invocation.app_id][1].append(idle_time)
                    all_app_full_IT_trace[invocation.app_id][0] = invocation.start_time + invocation.function_duration
                else:
                    all_app_full_IT_trace[invocation.app_id][0] = max(all_app_full_IT_trace[invocation.app_id][0], invocation.start_time+invocation.function_duration)
        # print(all_app_full_IT_trace)
        return all_app_full_IT_trace
    
    def slice_app_IT_trace(self, all_app_full_IT_trace, start_time, length):
        # slice a time window from all app full IT trace
        # output a dict, key: app_id, value: list of IT
        sliced_app_ITs = {}
        # for all apps
        for app_id in all_app_full_IT_trace.keys():
            _, all_ITs, ITs_end_time = all_app_full_IT_trace[app_id]
            for i in range(len(all_ITs)):
                if ITs_end_time[i]>=start_time and ITs_end_time[i]<(start_time+length):
                    if app_id not in sliced_app_ITs.keys():
                        sliced_app_ITs[app_id]=[all_ITs[i]]
                    else:
                        sliced_app_ITs[app_id].append(all_ITs[i])

        # print('sliced_ITs:', sliced_app_ITs)
        return sliced_app_ITs

    def find_OOB_app(self, sliced_app_ITs):
        # output a list of app_id which has more than 25% values larger than 4 hours
        OOB_duration = 4*60*60
        OOB_apps = []
        for id in sliced_app_ITs.keys():
            data = sliced_app_ITs[id]
            # check how many IT larger than max duration
            percent = sum[data>OOB_duration]/len(data)
            if percent>0.25:
                OOB_apps.append(id)

        return OOB_apps

    # Policy ARIMA
    def simulation_auto_arima(self, all_app_full_IT_trace):

        # predict next IT
        for invocation in self.workload:
            self.current_time = invocation.start_time
            _, ITs, ITs_end_time = all_app_full_IT_trace[invocation.app_id]
            idx = -1
            for t in ITs_end_time:
                if t <= self.current_time:
                    idx += 1
                else:
                    break
            # k training data window
            k = 2
            s = max(0,idx-k+1)
            training_data = ITs[s:idx+1]
            print('train:', training_data)
            if len(training_data)==0:
                # can do nothing as no data at all
                next_IT=None
            elif len(training_data)<k:
                # not enough training data, predict the same as last value
                next_IT=training_data[-1]
            else:
                # enough k data, do ARIMA
                next_IT = 999 # to be predicted
                # arima = pm.auto_arima(training_data, error_action='ignore', trace=True,
                #                         suppress_warnings=True, maxiter=5,
                #                         seasonal=True, m=12)
                # next_IT = arima.predict(n_periods=1)

            print('log', invocation.app_id, 'predict', next_IT)

            if next_IT:
                next_invocation_time = self.current_time + invocation.function_duration + next_IT
                pre_warm_load_time = next_invocation_time - 10 # set pre-warm window elapse just before the next invocation (assume 10s)
                keep_live_time = 30 # a short keep-alive window (assume 30s)
                current_app_alive_until = pre_warm_load_time+keep_live_time

        return

if __name__ == "__main__":
    # function1 = Function(0, 0, 0, 'http', 3, 1)
    # function2 = Function(1, 0, 5, 'http', 3, 1)
    # function3 = Function(2, 1, 3, 'http', 5, 1)
    # function4 = Function(0, 0, 7.5, 'http', 1, 1)
    # function_list = [function1, function2, function3, function4]
    # function_list = [
    #     Function(0, 0, 0, 3), 
    #     Function(0, 0, 2, 5), 
    #     Function(0, 0, 7.5, 4), 
    #     Function(0, 0, 13, 4), 
    #     # Function(0, 0, 15, 2), 
    #     # Function(0, 0, 13, 1), 
    #     # Function(0, 0, 18, 2), 
    #     # Function(1, 0, 7, 4),
    #     Function(2, 1, 5, 4),
    #     Function(3, 1, 11, 1),
    #     Function(4, 1, 15, 4),
    #     Function(5, 1, 20, 1)
    # ]
    # simulator = Simulator(function_list)
    simulator = Simulator('day1.npy')
    # simulator.simulation_fixed_keep_alive(10)
    simulator.simulation_pre_warm(0, 0)

    print("number of cold start: {}".format(simulator.start_cold))
    print("number of warm start: {}".format(simulator.start_warm))
    print("cold start rate: {}".format(simulator.start_cold/(simulator.start_cold + simulator.start_warm)))
    print("Maximum memory usage: {}".format(simulator.max_memory))
    print("memory waste time: {}".format(simulator.wasted_memory_time))

    # x = simulator.get_all_app_full_IT_trace()
    # print(x)
    # simulator.simulation_auto_arima(x)