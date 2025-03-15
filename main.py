import requests
import sqlite3
#to grab all the data using Listbox and insert them into SQL Table
# to create GUI
from tkinter import *
from tkinter import messagebox
# to encode and decode binary data in order to get all data from Wufoo Forms
import base64
# A module that  improves the code for multiple executions
from threading import Thread

# collect data using API key, Hash and subdomain
WUFOO_API_KEY = '5CIM-NC2N-L4XZ-JMSE'
WUFOO_FORM_HASH = 'z19268d108zqexb'
WUFOO_SUBDOMAIN = 'qichao'  #  Wufoo subdomain
DATABASE_NAME = 'form_data.db'


# Function to get headers
def get_headers():
    encoded_key = base64.b64encode(f"{WUFOO_API_KEY}:".encode()).decode()
    return {
        'Authorization': f'Basic {encoded_key}',
        'Content-Type': 'application/json'
    }  


# Function to create a database and table
def create_database():
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS form_entries')
        cursor.execute(''' 
           CREATE TABLE IF NOT EXISTS form_entries ( 
               ID INTEGER PRIMARY KEY, 
               Name TEXT, 
               Email TEXT, 
               Address TEXT,
               HouseType TEXT,
               YearBuilt INTEGER,
               MonthlyBill INTEGER,
               Appliance TEXT,
               TotalConsumption INTEGER
           )
       ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


# Function to fetch data from Wufoo
def fetch_data_from_wufoo():
    url = f'https://{WUFOO_SUBDOMAIN}.wufoo.com/api/v3/forms/{WUFOO_FORM_HASH}/entries.json'
    headers = get_headers()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json().get('Entries', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


# Function to insert data into the database
def insert_data(entries):
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        for entry in entries:
            full_name = f"{entry.get('Field1', 'Unknown')} {entry.get('Field2', 'Unknown')}"
            email = entry.get('Field10', 'Unknown')
            address = f"{entry.get('Field4', 'Unknown')} {entry.get('Field6', 'Unknown')} {entry.get('Field7', 'Unknown')} {entry.get('Field8', 'Unknown')} {entry.get('Field9', 'Unknown')}"
            house_type = entry.get('Field118') or entry.get('Field119') or entry.get('Field120', 'Unknown')
            year_built = entry.get('Field218', 'Unknown')
            monthly_bill = entry.get('Field115', 'Unknown')
            appliance = entry.get('Field224', 'Unknown')
            total_consumption = entry.get('Field228', 'Unknown')

            cursor.execute(''' 
               INSERT INTO form_entries (Name, Email, Address, HouseType, YearBuilt, MonthlyBill, Appliance, TotalConsumption)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ''', (full_name, email, address, house_type, year_built, monthly_bill, appliance, total_consumption))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Insert error: {e}")
    finally:
        if conn:
            conn.close()


# Function to provide product recommendations
# Function to provide product recommendations
def recommend_products(total_consumption, appliance):
    recommendations = []
    # monthly consumption of over 1000kwh is considered too high for a single family house, condo or apartment
    # we only give our recommended products to those whose consumption of over 1000 kwh

    if total_consumption > 1000:
        recommendations.append("Consider switching to energy-efficient appliances, such as Energy Star-rated products.")
        if "air conditioner" in appliance.lower():
            recommendations.append("Replace with an ENERGY STAR-certified model. Use a smart thermostat.")
        if "refrigerator" in appliance.lower():
            recommendations.append("Upgrade to a high-efficiency ENERGY STAR-certified refrigerator.")
        if "heater" in appliance.lower():
            recommendations.append("Upgrade to a smart thermostat to optimize heating.")
        if "light" in appliance.lower():
            recommendations.append("Switch to LED light bulbs for better efficiency.")
        if "washer" in appliance.lower() or "dryer" in appliance.lower():
            recommendations.append("Look for washers and dryers with eco-friendly modes.")
        if "ceiling fan" in appliance.lower():
            recommendations.append("Use a smart ceiling fan switch")
        if "television" in appliance.lower():
            recommendations.append("Switch to an ENERGY STAR certified television")
    # otherwise, encourage users to use Smart Power Strips or upgrade their pipe insulation
    if not recommendations:
        general_advice = (
            "Your energy usage is within an acceptable range. Keep up the good work!. "
            "General Advice: "
            "Pipe Insulation: insulation for hot and cold water pipes to reduce heat loss. "
            "Smart Power Strips: power strips that cut power to devices in standby mode. "
            "Home Insulation Upgrade: improved insulation for attics, walls, and basements to maintain temperature. "
            "Smart Home Energy Monitor: device that tracks energy usage in real-time."
        )

        # Split the general advice into individual sentences
        # to print them out line by line
        advice_lines = general_advice.split(". ")
        # Check if the line is not empty
        for line in advice_lines:
            if line:
                recommendations.append(f"- {line.strip()}.")

    return recommendations



# Function to fetch and display data based on user-provided ID
def fetch_and_display_by_id():
    # user_id from SQL Table
    user_id = id_entry.get()
    if not user_id.isdigit():
        messagebox.showerror("Invalid Input", "Please enter a valid numeric ID.")
        return

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM form_entries WHERE ID = ?', (user_id,))
        row = cursor.fetchone()
        listbox.delete(0, END)  # Clear the listbox


#insert
        if row:
            listbox.insert(END, f"ID: {row[0]}")
            listbox.insert(END, f"Name: {row[1]}")
            listbox.insert(END, f"Email: {row[2]}")
            listbox.insert(END, f"Address: {row[3]}")
            listbox.insert(END, f"House Type: {row[4]}")
            listbox.insert(END, f"Year Built: {row[5]}")
            listbox.insert(END, f"Monthly Bill: ${row[6]}")

            # Printing appliances line by line
            listbox.insert(END, "Appliance(s):")
            appliances = row[7].split(",")  # using Split method to split appliances, refer to Appliance Box in Wufoo Form
            for appliance in appliances:
                listbox.insert(END, f"- {appliance.strip()}")

            listbox.insert(END, f"Total Consumption: {row[8]} kWh")

            # Providing recommendations
            recommendations = recommend_products(row[8], row[7])
            listbox.insert(END, "Recommendations:")
            for recommendation in recommendations:
                listbox.insert(END, f"- {recommendation}")
# error checking in case user input wrong information.
        else:
            listbox.insert(END, "No record found for the provided ID.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()


# GUI setup
root = Tk()
root.title("Wufoo Form Data Fetcher")

# Input field for user ID
frame = Frame(root)
frame.pack(pady=10)
Label(frame, text="Enter User ID:").grid(row=0, column=0, padx=5)
id_entry = Entry(frame, width=10)
id_entry.grid(row=0, column=1, padx=5)
fetch_button = Button(frame, text="Fetch Data", command=fetch_and_display_by_id)
fetch_button.grid(row=0, column=2, padx=5)

# Listbox to display data
listbox = Listbox(root, width=80, height=20)
listbox.pack(pady=20)

# Create database and table
create_database()


# passed the result of fetch_data_from_wufoo()  and called to retrieve the data from Wufoo Forms
Thread(target=lambda: insert_data(fetch_data_from_wufoo())).start()

# Start the GUI loop
root.mainloop()
