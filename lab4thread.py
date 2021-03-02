import requests 
import json
import tkinter as tk
import time
import queue
import threading
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

statesDict = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY'
}   

NUMBER_OF_WAVES = 16

my_queue = queue.Queue()

def storeInQueue(function):
  def wrapper(*args):
    my_queue.put(function(*args))
  return wrapper

def plotStates(state_data):
    for state in state_data:
        plt.plot(np.arange(1,NUMBER_OF_WAVES+1), state[1], label=state[0])
    
    plt.ylabel("% of Population Willing to Accept Vaccine", fontsize = 18)
    plt.xlabel("Wave (two week increments beginning 07/06/2020)", fontsize = 18)
    plt.title("Vaccination Data for Selected States")
    plt.legend(loc="best")
    plt.xticks(np.arange(1,NUMBER_OF_WAVES+1), rotation=90, fontsize=12)

def plotVaccinationRate(state_data):
    for state in state_data:
        plt.bar(state[0], state[2], label=state[0])

    plt.ylabel("% of Population Vaccinated", fontsize = 12)
    plt.xlabel("State", fontsize = 12)
    plt.title("Vaccination Rate for Selected States")
    plt.legend(loc="best")
    plt.xticks(rotation=90, fontsize=12)

def getVaccineDataForStates(state_list):
    start = time.time()
    state_data = []
    no_data_states = []
    for state in state_list:
        acceptance_rate_list = []
        final_percent_vaccinated = 0

        for x in range(1,NUMBER_OF_WAVES+1):
            print("Wave",x)
            try: 
                response = requests.get("http://covidsurvey.mit.edu:5000/query?wave=wave" + str(x) + "&country=US&us_state=" + statesDict[state] + "&signal=vaccine_accept").text
                jsonData = json.loads(response)

                percent_yes = float(jsonData['vaccine_accept']['weighted']['Yes'])
                percent_vaccinated = 0
                try:
                    if x == NUMBER_OF_WAVES:
                        final_percent_vaccinated = float(jsonData['vaccine_accept']['weighted']['I have already been vaccinated'])
                    percent_vaccinated += float(jsonData['vaccine_accept']['weighted']['I have already been vaccinated'])
                except KeyError:
                    pass
                acceptance_rate = percent_yes + percent_vaccinated
            except KeyError:
                if x == 1:
                    no_data_states.append(state)
                    break
                else:
                    acceptance_rate = 0
                    pass
            
            acceptance_rate_list.append(acceptance_rate)

        for idx, x in enumerate(acceptance_rate_list):
            if x == 0:
                acceptance_rate_list[idx] = (acceptance_rate_list[idx-1] + acceptance_rate_list[idx + 1])/2

        if state not in no_data_states:
            state_data.append((state, acceptance_rate_list, final_percent_vaccinated))
    end = time.time()
    print(round((end-start),2),"seconds")
    return (state_data, no_data_states)

@storeInQueue
def getVaccineDataForState(state):
    state_data = []
    acceptance_rate_list = []
    final_percent_vaccinated = 0

    for x in range(1,NUMBER_OF_WAVES+1):
        print("Wave",x)
        try: 
            response = requests.get("http://covidsurvey.mit.edu:5000/query?wave=wave" + str(x) + "&country=US&us_state=" + statesDict[state] + "&signal=vaccine_accept").text
            jsonData = json.loads(response)

            percent_yes = float(jsonData['vaccine_accept']['weighted']['Yes'])
            percent_vaccinated = 0
            try:
                if x == NUMBER_OF_WAVES:
                    final_percent_vaccinated = float(jsonData['vaccine_accept']['weighted']['I have already been vaccinated'])
                percent_vaccinated += float(jsonData['vaccine_accept']['weighted']['I have already been vaccinated'])
            except KeyError:
                pass
            acceptance_rate = percent_yes + percent_vaccinated
        except KeyError:
            if x == 1:
                break
            else:
                acceptance_rate = 0
                pass
        
        acceptance_rate_list.append(acceptance_rate)

    for idx, x in enumerate(acceptance_rate_list):
        if x == 0:
            acceptance_rate_list[idx] = (acceptance_rate_list[idx-1] + acceptance_rate_list[idx + 1])/2

    state_data = (state, acceptance_rate_list, final_percent_vaccinated)
    return (state_data)

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.state_list = None

        self.title("Vaccine Survey")
        self.geometry("400x220")

        label1 = tk.Label(self, text= "Click on state names to choose states")
        label1.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(self, selectmode="multiple")
        self.listbox.grid(row=1, column=0, columnspan=2, sticky="nsew")
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=1, column=1, sticky="nse")
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)

        button = tk.Button(self, text="Ok")
        button.grid(row=3)

        for state in statesDict.keys():
            self.listbox.insert(tk.END, state)

        button.config(command=self.selectedStates) #check this

    def selectedStates(self):
        """Sets selection to whatever user has selected in listbox"""
        self.state_list = [self.listbox.get(idx) for idx in self.listbox.curselection()]
        state_data = []
        states_missing_data = []
        threads = []
        start = time.time()
        for state in self.state_list:
            t = threading.Thread(target = getVaccineDataForState, args=(state,))
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()
            state = my_queue.get()
            if state[1] == []:
                states_missing_data.append(state[0])
            else:
                state_data.append(state)

        end = time.time()
        print(round((end-start),2),"seconds")
        
        if states_missing_data:
            missing_states = ', '.join(states_missing_data)
            tk.messagebox.showinfo(title="Missing Data", message="No data for " + missing_states)
        if state_data != []:
            self.Plot(plotStates, state_data)
            self.Plot(plotVaccinationRate, state_data)

    def Plot(self, plot, state_data):
        pw = PlotWindow(self, plot, state_data)


class PlotWindow(tk.Toplevel):
    def __init__(self, master, plot, state_data):
        super().__init__(master)
        self.title("Vaccine Data")
        self.transient(master)

        fig = plt.figure(figsize=(15, 10))
        plot(state_data)
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.get_tk_widget().grid()
        canvas.draw()

def main():
    m = MainWindow()
    m.mainloop()
    
    

if __name__ == '__main__':
    main()