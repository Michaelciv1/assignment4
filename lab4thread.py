import requests 
import json
import tkinter as tk
import time
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

def plotStates(state_data):
    """Plots graph based on the passed data from lab2"""
    start = time.time()
    print(state_data[0])
    print(state_data[1])
    print(state_data[2])
    for state in state_data:
        plt.plot(np.arange(1,NUMBER_OF_WAVES+1), 
        state_data[1], 
        label=state_data[0])
    end = time.time()
    print(round((end-start),2),"seconds")

    plt.ylabel("% of Population Willing to Accept Vaccine", fontsize = 18)
    plt.xlabel("Wave (two week increments beginning 07/06/2020)", fontsize = 18)
    plt.title("Vaccination Data for Selected States")
    plt.legend(loc="best")
    plt.xticks(np.arange(1,NUMBER_OF_WAVES+1), rotation=90, fontsize=12)
    #plt.show()


def plotVaccinationRate(state_data):
    for state in state_data:
        plt.bar(state_data[0], state_data[2], label=state_data[0])

    plt.ylabel("% of Population Vaccinated", fontsize = 12)
    plt.xlabel("State", fontsize = 12)
    plt.title("Vaccination Rate for Selected States")
    plt.legend(loc="best")
    plt.xticks(rotation=90, fontsize=12)

def getVaccineDataForStates(state_list):
    state_data = []
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
                    print("not enough data")
                    break
                else:
                    acceptance_rate = 0
                    pass
            
            acceptance_rate_list.append(acceptance_rate)

        for idx, x in enumerate(acceptance_rate_list):
            if x == 0:
                acceptance_rate_list[idx] = (acceptance_rate_list[idx-1] + acceptance_rate_list[idx + 1])/2

        state_data.append((state, acceptance_rate_list, final_percent_vaccinated))
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

        button.config(command=self.setSelection) #check this

    def setSelection(self):
        """Sets selection to whatever user has selected in listbox"""
        self.state_list = [self.listbox.get(idx) for idx in self.listbox.curselection()]
        state_data = getVaccineDataForStates(self.state_list)
        self.Plot(plotStates, state_data)
        self.Plot(plotVaccinationRate, state_data)

    def Plot(self, plot, state_data):
        pw = PlotWindow(self, plot, state_data)


class PlotWindow(tk.Toplevel):
    def __init__(self, master, plot, state_data):
        super().__init__(master)
        self.title("Population")
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