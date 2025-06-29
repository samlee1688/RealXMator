from flask import Flask, render_template, request
import json
import math
import sys
import random
from datetime import date
import propertiesFinder as pf
import xmator as xm

propFinder = pf.PropertiesFinder()
app = Flask(__name__)

xMator = xm.realXMator('C:\\AI\\realxmator\\single-75035.csv')
#model = xMator.train(0.2, 'C:\\AI\\realxmator\\xMator.model')

@app.route('/estimate', methods=['POST'])
def estimate():
    #xMator = xm.realXMator('C:\\AI\\realxmator\\single-75035.csv')
    #model = xMator.train(0.2, 'C:\\AI\\realxmator\\xMator.model')
    housebgImg="housebg"+str(random.randint(1, 6))+".jpg"
    propertyAddress = request.form['propertyAddress']
    yearBuilt = request.form['yearBuilt']
    houseSize = request.form['houseSize']
    propType = request.form['propType']
    price = request.form['price']
    numYrs = int(request.form['numYrs'])
    mortRate = float(request.form['mortRate'])
    mortTerm = int(request.form['mortTerm'])
    calBalance = False
    remainingBalance = 0
    downPayment = float(request.form['downPayment'])

    today=date.today().strftime('%Y')
    sellYear = numYrs+ int(today)
    age=sellYear-int(yearBuilt)
    currentAge = int(today)-int(yearBuilt)
    
    #calculate monthly payment
    monthlyRate = mortRate/1200
    numPayments = mortTerm*12
    principal = int(int(price)-downPayment)
    countYear = int(today)
    countAge = currentAge
    totalProfit = 0  
    if principal>0 :
        monthlyPayment = round(principal*monthlyRate*(math.pow((1+monthlyRate), numPayments))/((math.pow((1+monthlyRate), numPayments))-1) , 0)
    else:
        monthlyPayment = 0
        
    if mortTerm > numYrs:
        remainingBalance = round(principal*(math.pow((1+monthlyRate), numPayments) - math.pow((1+monthlyRate), (numYrs*12)))/((math.pow((1+monthlyRate), numPayments))-1) , 0)

    hoa = 0.001
    mgmtAndMaintenance = 0.16
    propertyTax = 0.018
    homeInsurance = 0.005
    expenseRatio = hoa + propertyTax + homeInsurance
    
    debug = ""
    
    allYearsData = []
    for x in range(int(numYrs)):
        countYear += 1
        countAge += 1
        
        if x >= mortTerm:
            monthlyPayment = 0
        
        priceForYear = round(xMator.pred([int(countYear),int(countAge), int(houseSize)], propType)[0][0],0)
        rentForYear = round(priceForYear*0.0065,0)
        expenses = round(priceForYear*(expenseRatio) + rentForYear*mgmtAndMaintenance*12, 0)  
        netProfitYear = round(rentForYear*12 - monthlyPayment*12 - expenses, 0)
        yearlyData = {}
        yearlyData["year"] = countYear
        yearlyData["price"] = priceForYear
        yearlyData["rent"] = rentForYear
        yearlyData["expenses"] = expenses
        allYearsData.append(yearlyData)
        
        totalProfit += netProfitYear
        debug += " Year "+str(countYear)+" NetProfit="+str(netProfitYear)+" Rent="+str(rentForYear)+' EstPrice='+str(priceForYear)+' MonthMortgage='+str(monthlyPayment)+'  Expenses='+str(expenses)+" "
    data2 = {}
    totalNetProfit = round(priceForYear*0.97 - remainingBalance + totalProfit - downPayment,0)
    
    data2["TotalNetProfit"] = totalNetProfit
    data2["SalePrice"] = priceForYear
    data2["MortgateBalance"] = remainingBalance
    data2["NetRentalIncome"] = totalProfit
    data2["downPayment"] = downPayment
    data2["yearlyData"] = allYearsData

    animal = data2
    saleYear=countYear
    return render_template("result.html", ollie=animal, propertyAddress=propertyAddress, yearBuilt=yearBuilt, 
    houseSize=houseSize, estimatedPrice = price, housebgImg=housebgImg, totalNetProfit=totalNetProfit,
    salePrice=priceForYear, mortgageBalance=remainingBalance, rentalIncome=totalProfit, saleYear=saleYear,
    mortgageRate=mortRate, downPayment=downPayment, numYrs=numYrs, mortTerm=mortTerm, propType=propType)
    
@app.route('/search_address', methods=['POST'])
def search_address():
    housebgImg="housebg"+str(random.randint(1, 6))+".jpg"
    data = request.form['propAddress'] 
    error = ''
    propInfo=propFinder.getAddressInfoByCompass(data)
    if propInfo is None or len(propInfo) != 5:
        propInfo=propFinder.getAddressInfoByCompass(data)
        if len(propInfo) != 5:
            print('using googl')
         
            propInfo=propFinder.getAddressInfoByKeywords(data)
           # propInfo=propFinder.getAddressInfoByGoogle(data)
    #if len(propInfo) != 5:
    #    error = "Could not find property."
   
    address = propInfo[2]
    yearBuilt = propInfo[0]
    houseSize = propInfo[1]
    propType = propInfo[3]
    imgURL = propInfo[4]
    
    #return str(propInfo)
    year=date.today().strftime('%Y')
    age = int(year)-int(yearBuilt)
    priceForYear = xMator.pred([int(year),age, int(houseSize)],propType)
    #price = houseDetail['price']
    price = int(priceForYear[0][0])
    downPayment = int(price)*0.25
    rent = round(price*0.0065,2)

    #return render_template("test.html", ollie=animal)
    return render_template("search.html", propertyAddress=address,yearBuilt=yearBuilt, 
    houseSize=houseSize, estimatedPrice = price, downPayment=downPayment, 
    estimatedRent=rent,houseImage=imgURL, propType=propType, housebgImg=housebgImg, error = error)  

    
@app.route('/search_addressX', methods=['POST'])
def search_addressX():
    housebgImg="housebg"+str(random.randint(1, 6))+".jpg"
    data = request.form['propAddress']    
    propInfo=propFinder.getAddressInfoByKeywords(data)
    #return propInfo
    #houseHistory = propFinder.searchZillowPropertyByURI(propFinder.zillowConn, propInfo)
    address = propInfo[2]
    yearBuilt = propInfo[0]
    houseSize = propInfo[1]
    propType = propInfo[3]
    #return str(propInfo)
    year=date.today().strftime('%Y')
    age = int(year)-int(yearBuilt)
    priceForYear = xMator.pred([int(year),age, int(houseSize)],propType)
    #price = houseDetail['price']
    price = int(priceForYear[0][0])
    downPayment = int(price)*0.25
    rent = round(price*0.0065,2)
    imgURL = propFinder.getZillowImgByGoogleSearch(data)

    #animal = propFinder.sendRequest(propFinder.addressConn, allHousesFromAStreet[0])
    #return render_template("test.html", ollie=animal)
    return render_template("search.html", propertyAddress=address,yearBuilt=yearBuilt, 
    houseSize=houseSize, estimatedPrice = price, downPayment=downPayment, 
    estimatedRent=rent,houseImage=imgURL, propType=propType, housebgImg=housebgImg)  

@app.route('/handle_data', methods=['POST'])
def handle_data():
    data = request.form['projectFilepath']

    houseInfo = data.split(" ")
    street=houseInfo[0]+"-"+houseInfo[1]
    city=houseInfo[2]
    state=houseInfo[3]
    zipcode=houseInfo[4]
    county=houseInfo[5]
    streetUri="/home-values/"+state+"/"+county+"-county/"+city+"/"+zipcode+"/"+street+"/"
    
    allHousesFromAStreet=propFinder.getRecordsByURI(propFinder.addressConn, streetUri)
    houseHistory = propFinder.searchProperty(propFinder.addressConn, allHousesFromAStreet[0])
    animal = json.dumps(houseHistory[0])
    #animal = propFinder.sendRequest(propFinder.addressConn, allHousesFromAStreet[0])
    return render_template("test.html", ollie=animal)


@app.route('/dave')
def dave():
    #return 'Hello, World!'  
    animal = 'Yahooo'
    #return render_template('RealXmator.html', ollie=animal)
    return render_template("RealXmator.html")
    
@app.route('/')
def home():
    #return 'Hello, World!'  
    animal = 'Yahooo'
    #return render_template('RealXmator.html', ollie=animal)
    return render_template("RealXmator.html")
    
@app.route("/about")
def about():
    animal = 'Yahooo'
    return render_template("about.html", ollie=animal)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)