from flask import Flask, render_template, request
import os
import http.client
import propertiesFinder as pf

propFinder = pf.PropertiesFinder()
app = Flask(__name__)

@app.route("/")
def about():
    zillowConn = http.client.HTTPSConnection("www.har.com")
    data = "1368 crockett dr frisco tx 75033"   
    propInfo=propFinder.getAddressInfoByKeywords(data)
    #houseHistory = propFinder.searchZillowPropertyByURI(propFinder.zillowConn, propInfo)

    uri = propInfo[len(propInfo)-1]
    #uri = "/dave.php?id=yaoooo"
    uri = "/CA/Fremont/222-Marquis-Ter-94536/home/612905"
    #return uri
    uri ="/homedetail/1368-crockett-dr-frisco-tx-75033/1852867?sid=1947500"
    zillowConn.request("GET", uri)
    response = zillowConn.getresponse()        
    if response.status != 200:
        print("Error: Status: {} and reason: {}".format(response.status, response.reason))
  
    animal = str(response.read().decode('ascii', 'ignore'))
    return render_template("about.html", ollie=animal)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)