import requests 
import json
import tkinter as tk
import time
import os
import queue
import threading
import numpy as np
import multiprocessing as mp
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

NUMBER_OF_WAVES = 15

my_queue = mp.Queue()

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

def getVaccineDataForState(state):
    state_data = []
    acceptance_rate_list = []
    final_percent_vaccinated = 0

    response = requests.get(f"http://covidsurvey.mit.edu:5000/query?country=US&us_state={statesDict[state]}&signal=vaccine_accept&timeseries=true").text
    jsonData = json.loads(response)

    if "all" in jsonData:
        del jsonData["all"]
    print("Getting data for",state)
    for x, wave in enumerate(jsonData, 1):
        print("Wave",x)
        try:
            percent_yes = float(jsonData[wave]['vaccine_accept']['weighted']['Yes'])
            percent_vaccinated = 0
            try:
                if wave == "wave"+str(NUMBER_OF_WAVES):
                    final_percent_vaccinated = float(jsonData[wave]['vaccine_accept']['weighted']['I have already been vaccinated'])
                percent_vaccinated += float(jsonData[wave]['vaccine_accept']['weighted']['I have already been vaccinated'])
            except KeyError:
                pass
            acceptance_rate = percent_yes + percent_vaccinated
        except KeyError:
            "If the first wave is missing data, I assume the rest of the data is empty as well"
            if x == 1:
                break
            else:
                acceptance_rate = 0
                pass
        
        acceptance_rate_list.append(acceptance_rate)

    for idx, x in enumerate(acceptance_rate_list):
        if x == 0:
            try:
                acceptance_rate_list[idx] = (acceptance_rate_list[idx-1] + acceptance_rate_list[idx + 1])/2
            except IndexError:
                acceptance_rate_list[idx] = acceptance_rate_list[idx-1]

    state_data = (state, acceptance_rate_list, final_percent_vaccinated)
    my_queue.put(state_data)

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
        self.protocol("WM_DELETE_WINDOW", self.quit)

    def selectedStates(self):
        """Sets selection to whatever user has selected in listbox"""
        self.state_list = [self.listbox.get(idx) for idx in self.listbox.curselection()]
        state_data = []
        states_missing_data = []
        processes = []
        start = time.time()
        for state in self.state_list:
            print('stop')
            p = mp.Process(target = getVaccineDataForState, args=(state,))
            p.start()
            processes.append(p)

        for process in processes:
            print('stop here')
            # process.join()
            state = my_queue.get()
            if state[1] == [0]:
                states_missing_data.append(state[0])
            else:
                state_data.append(state)
        
        for process in processes:
            process.join()

        end = time.time()
        print(round((end-start),2),"seconds")
        
        if states_missing_data:
            missing_states = ', '.join(states_missing_data)
            tk.messagebox.showinfo(title="Missing Data", message="No data for " + missing_states)
        if state_data:
            self.Plot(plotStates, state_data)
            self.Plot(plotVaccinationRate, state_data)
            self.saveData(state_data)

    def Plot(self, plot, state_data):
        pw = PlotWindow(self, plot, state_data)
        self.wait_window(pw)

    def saveData(self,state_data):
        save_message = tk.messagebox.askokcancel(title="Save Data", message="Save result to file?")
        if save_message:
            current_directory = tk.filedialog.askdirectory(initialdir='.')
            if not os.path.isdir('lab4dir') :
                os.mkdir('lab4dir')
            os.chdir('lab4dir')
        #def writeFile(filename, str) :
            with open("lab4out.txt", 'w') as fh:
                for state in state_data: 
                    fh.write(str(state[0]) + ":\n")
                    fh.write("approve:"+', '.join([str(x) for x in state[1]])+"\n")
                    fh.write("vaccinated: "+ str(state[2]) + "\n")

        

class PlotWindow(tk.Toplevel):
    def __init__(self, master, plot, state_data):
        super().__init__(master)
        self.title("Vaccine Data")
        self.transient(master)

        fig = plt.figure(figsize=(10, 10))
        plot(state_data)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.get_tk_widget().grid()
        canvas.draw()
        


def main():
    m = MainWindow()
    m.mainloop()

if __name__ == '__main__':
    main()