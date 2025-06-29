from flask import Flask, render_template, request
import math
import random
from datetime import date
import propertiesFinder as pf
import xmator as xm

propFinder = pf.PropertiesFinder()
app = Flask(__name__)

xMator = xm.realXMator()
 

def getYearlyData(yearsHold, yearBuilt, houseSize, propType, principal, monthlyRate,mortTerm, downPayment):
    today=date.today().strftime('%Y')
    countYear = int(today)
    currentAge = int(today)-int(yearBuilt)
    remainingBalance = 0
    countAge = currentAge
    hoa = 0.001
    mgmtAndMaintenance = 0.16
    propertyTax = 0.018
    homeInsurance = 0.005
    expenseRatio = hoa + propertyTax + homeInsurance
    numPayments = int(mortTerm)*12
    
    if principal>0 :
        monthlyPayment = round(principal*monthlyRate*(math.pow((1+monthlyRate), numPayments))/((math.pow((1+monthlyRate), numPayments))-1) , 0)
    else:
        monthlyPayment = 0
    
    if mortTerm > yearsHold:
        remainingBalance = round(principal*(math.pow((1+monthlyRate), numPayments) - math.pow((1+monthlyRate), (yearsHold*12)))/((math.pow((1+monthlyRate), numPayments))-1) , 0)    
    
       
    totalProfit=0
    allYearsData = []
    for x in range(int(yearsHold)):
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
    
    data2 = {}
    totalNetProfit = round(priceForYear*0.97 - remainingBalance + totalProfit - downPayment,0)
    
    data2["TotalNetProfit"] = totalNetProfit
    data2["SalePrice"] = priceForYear
    data2["MortgateBalance"] = remainingBalance
    data2["NetRentalIncome"] = totalProfit
    data2["downPayment"] = downPayment
    data2["yearlyData"] = allYearsData
    
    return data2

@app.route('/estimate', methods=['POST'])
def estimate():

    housebgImg="housebg"+str(random.randint(1, 6))+".jpg"
    propertyAddress = request.form['propertyAddress']
    yearBuilt = request.form['yearBuilt']
    houseSize = request.form['houseSize']
    propType = request.form['propType']
    price = request.form['price']
    numYrs = int(request.form['numYrs'])
    mortRate = float(request.form['mortRate'])
    mortTerm = int(request.form['mortTerm'])
    monthlyRate = mortRate/1200
    calBalance = False
    remainingBalance = 0
    downPayment = float(request.form['downPayment'])
    principal = int(int(price)-downPayment)
    downPercent = round(float(downPayment/int(price)*100),1)
    today=date.today().strftime('%Y')
    saleYear=int(today)+numYrs
    #User input
    originalEstimate = getYearlyData(numYrs, yearBuilt, houseSize, propType, principal, monthlyRate, mortTerm, downPayment)    
    totalNetProfit = originalEstimate['TotalNetProfit']
    priceForYear = originalEstimate['SalePrice']
    rentalIncome = originalEstimate['NetRentalIncome']
    remainingBalance = originalEstimate['MortgateBalance']

    animal = originalEstimate
    #Comparison
    plusFiveEstimate = {}
    minusFiveEstimate = {}
    comparePlus5 = ''
    Plus5Year = ''
    compareMinus5 = ''
    Minus5Year = ''
    compareNote = ""
    
    if numYrs <= 25:
        plusFiveEstimate = getYearlyData(numYrs+5, yearBuilt, houseSize, propType, principal, monthlyRate, 15, downPayment)
        Plus5Year = str(numYrs+5) + " years: "
        compareNote += str(numYrs+5) + " years" 
        comparePlus5 = "$"+str(plusFiveEstimate['TotalNetProfit'])
        

    if numYrs >= 10:
        if len(Plus5Year):
            compareNote += " and "     
        minusFiveEstimate = getYearlyData(numYrs-5, yearBuilt, houseSize, propType, principal, monthlyRate, 15, downPayment)   
        Minus5Year = str(numYrs-5) + " years: "
        compareNote += str(numYrs-5) + " years" 
        compareMinus5 = "$"+str(minusFiveEstimate['TotalNetProfit'])
        
    return render_template("result.html", ollie=animal, propertyAddress=propertyAddress, yearBuilt=yearBuilt, 
    houseSize=houseSize, estimatedPrice = price, housebgImg=housebgImg, totalNetProfit=totalNetProfit,
    salePrice=priceForYear, mortgageBalance=remainingBalance, rentalIncome=rentalIncome, saleYear=saleYear,
    mortgageRate=mortRate, downPayment=downPayment, numYrs=numYrs, mortTerm=mortTerm, propType=propType,
    downPercent=downPercent, plusFive = plusFiveEstimate, minusFive = minusFiveEstimate, comparePlus5 = comparePlus5,
    compareMinus5 = compareMinus5, Plus5Year = Plus5Year, Minus5Year = Minus5Year, compareNote=compareNote)
    
@app.route('/search_address', methods=['POST'])
def search_address():
    housebgImg="housebg"+str(random.randint(1, 6))+".jpg"
    data = request.form['propAddress'] 
    error = ''
    propInfo=propFinder.getAddressInfoByCompass(data)
    
    print("Compass result "+str(propInfo))
    #return str(propInfo)
    if len(propInfo) != 5:
        print("Trying Zillow: "+data)
        propInfo=propFinder.getAddressInfoByKeywords(data)
        if len(propInfo) != 5:
            print("Trying Realtor "+data)
            propInfo=propFinder.getAddressInfoByRealtorKeywords(data)
            if len(propInfo) != 5:
                error = "Could not find property. "+data     
                return render_template("RealXmator.html", error = error) 

    address = propInfo[2]
    addressInfo = address.split(" ")
    supportedZip = False
    zipcode = int(addressInfo[len(addressInfo)-1].strip())
    if zipcode>75000 and zipcode < 76671 :
        supportedZip = True

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
    downPercent = 25
    return render_template("search.html", propertyAddress=address,yearBuilt=yearBuilt, 
    houseSize=houseSize, estimatedPrice = price, downPayment=downPayment, 
    estimatedRent=rent,houseImage=imgURL, propType=propType, housebgImg=housebgImg, 
    error=error, zipcode=zipcode, supportedZip=supportedZip, downPercent=downPercent)  
   
   
@app.route('/research')
def research():
    return render_template("research.html")
    
@app.route('/aboutsam')
def aboutsam():
    return render_template("sam.html")

@app.route('/contactus')
def contactus():
    return render_template("contactus.html")

@app.route('/')
def home():
    #return 'Hello, World!'  
    animal = 'Yahooo'
    #return render_template('RealXmator.html', ollie=animal)
    return render_template("RealXmator.html")
    
    
if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)