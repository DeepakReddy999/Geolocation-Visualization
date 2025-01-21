#!/usr/bin/env python
# coding: utf-8

# In[1]:


import urllib.request, urllib.parse, urllib.error
import sqlite3
import json
import time
import ssl
# in the above line we are importing different libraries
# this is the base URL that is a proxy for the rate limited API
serviceurl = 'https://py4e-data.dr-chuck.net/opengeo?'

# Optional: Enable debugging
# http.client.HTTPConnection.debuglevel = 1

# we are getting connected to the opengeo.sqlite3 if it is exiting or the database will be created
conn = sqlite3.connect('opengeo.sqlite')
cur = conn.cursor() # creating the cursor to execute the sql commands

# Creating a table if it doesn't already exist with the columns address and geodata(used to store the geolocation data)
cur.execute('''
CREATE TABLE IF NOT EXISTS Locations (address TEXT, geodata TEXT)''')

# Ignoring SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# opening the file where.data in which we have the locations list
fh = open("where.data.txt")
count = 0 # intializing the count and nofound to zero
nofound = 0  

# Looping through each line in the file and as the base url is the proxy it slows down as it is rate limited so
# after the 100 locations it stops and we need to restart the program to get the locations again
for line in fh:
    address = line.strip() # it strips the empty spaces from the line
    print('')
    cur.execute("SELECT geodata FROM Locations WHERE address= ? ", (address, )) # this command selects the geodata from the
    # Locations table and the addresses are the address object above

    # we are trying to fetch the location and if it is found in the database it doesnt run the code and add it the database
    # it skips that loop and continues to the other
    try:
        data = cur.fetchone()[0]
        print("Found in database", address)
        continue
    except: # if the location is not found it continues with the process
        pass

    # we are creating an empty dictionary and adding a key named 'q' and adding values to it from the addres that we have 
    # created, we are creating the complete url by adding the service url and encoding the location to the exact url format
    # by using the urlencode and we are parsing the url by using the urllib.parse
    parms = dict()
    parms['q'] = address # here the address from the where.data is stored into the 'q' the query parameters
    # and it is embedded into the url
    url = serviceurl + urllib.parse.urlencode(parms)

    print('Retrieving', url) # we will print out the retrieved url
    uh = urllib.request.urlopen(url, context=ctx) # creating an object of the url data naming it as uh
    data = uh.read().decode() # decoding the data in the url
    print('Retrieved', len(data), 'characters', data[:20].replace('\n',' ')) # counting the len(data) and getting first
    # 20 characters 

    try:
        js = json.loads(data) # we are converting the content in the data because it is in the json format. we are convertin
        # it into the python dictionary
    except:
        print(data)  # Print raw data in case of an error
        continue

    # Check for download or data errors
    if not js or 'features' not in js:
        print('==== Download error ====')
        continue

    # Handle case where no geodata is found
    if len(js['features']) == 0:
        print('==== Object not found ====')
        nofound = nofound + 1
        continue

    # here we are inserting the address and geodata into the database and we use memoryview() allows the address and data
    # to be stored in binary by converting them into encoded byte arrays
    cur.execute('''INSERT INTO Locations(address, geodata) VALUES(?, ?)''', 
                (memoryview(address.encode()), memoryview(data.encode())))
    conn.commit() # commiting the transctions

    count = count + 1 # increamenting the count by 1 for every location

    # Pause after every 10 requests
    if count % 10 == 0: # for every 10 counts we are pausing for 5 seconds and this can be done by the time library and 
        # sleep() function
        print('Pausing for a bit...')
        time.sleep(5)

# Print the number of locations that couldn't be found
if nofound > 0:
    print('Number of features that location cannot be found:', nofound)


# In[2]:


import sqlite3
import json
import codecs
# in the above code we are importing the libraries. The codecs library is used to decode() and encode() the data

# connecting to the sqlite database named opengeo.sqlite and creating the cursor object to implement commands
conn = sqlite3.connect('opengeo.sqlite')
cur = conn.cursor()

# Execute query to select all rows from the Locations table
cur.execute('''SELECT * FROM Locations''')

# opening the javascript file where.js and in utf-8 format. In the second line of the code we are writing in the file
# we are starting a java script array [\n indicate the start of an array
fhand = codecs.open('where.js', 'w', 'utf-8')
fhand.write('mydata=[\n')

count = 0
# Loop through the rows in the database
for row in cur:
    # the second row in the database is decoded and converted into the string and added to the object named data
    # and it loops all the rows starting from the row[1] which contains the information of one location
    print(f"Processing row: {row}")  # Print the entire row
    data = str(row[1].decode())  # Decode the geodata
    print(f"Decoded geodata: {data}")  # Print the JSON string
    
    try:
        # and here we are parsing the above data object which we have attained above in to the dictionary format by using
        # json.loads()
        # the data from an API is always in the json, so when we are trying to retrieve the information we need to parse
        # the data using the json.load()
        js = json.loads(str(data))
    except:
        continue

    # and if the count of above js features(dictionary) is 0 then it skips the loop
    if len(js['features']) == 0:
        continue

    try:
        lat = js['features'][0]['geometry']['coordinates'][1]  # Latitude
        lng = js['features'][0]['geometry']['coordinates'][0]  # Longitude
        where = js['features'][0]['properties']['formatted']  # Location name
        where = where.replace("'", "")  # Remove single quotes for JavaScript compatibility
    except KeyError as e:
        print(f"KeyError: {e}")
        print("JSON structure has unexpected format.")
        continue

    # Printing the data what we have retrieved and incrementing the count
    print(where, lat, lng)
    count = count + 1

    # if the count is greater than 1 then we are writing the information into the javascript file where.js in
    # next lines of the code and separating the information according to the javascript rules
    output = "[" + str(lat) + "," + str(lng) + ",'" + where + "']"
    print(f"Writing to where.js: {output}")  # Debug: Print what's being written

    if count > 1:
        fhand.write(",\n")
    fhand.write(output)

# Finalize the JavaScript array and close the file
fhand.write('\n];')
fhand.close()


# In[3]:


jupyter notebook


# In[ ]:




