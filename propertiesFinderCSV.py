import http.client
import json
from datetime import datetime
from datetime import date
import time
from xml.dom.minidom import parse, parseString
import os
from os import path


class PropertiesFinder:
   
    singleCSVExists = False
    condoCSVExists = False
    apartmentCSVExists = False
    
    ZILLOW_SEARCH_KEY = 'zillow.com/homedetails'
    REALTOR_SEARCH_KEY = 'realtor.com/realestateandhomes-detail/'
    HAR_SEARCH_KEY = ''
    realtorKeyLength = len(REALTOR_SEARCH_KEY)
    
    singleCSVFile="C:\\AI\\realxmator\\python\\single.csv"
    condoCSVFile="C:\\AI\\realxmator\\python\\condo.csv"
    apartmentCSVFile="C:\\AI\\realxmator\\python\\apartment.csv"    
    
    resume = False
    resumeBegin = False
    lastProperty = "None"
    
    def __init__(self):
        self.zillowConn = http.client.HTTPSConnection("www.zillow.com")
        self.addressConn = http.client.HTTPSConnection("www.realtytrac.com")
        self.zipConn = http.client.HTTPSConnection("www.getzips.com")
        self.googleConn = http.client.HTTPSConnection("www.google.com")
        self.harConn = http.client.HTTPSConnection("www.har.com")
        self.compassConn = http.client.HTTPSConnection("www.compass.com")

        #self.getLastAccessedProperty()
        #self.initFiles()
        self.beginTime = round(time.time()*1000)
        self.numOfRecords = 0
        self.totalNumOfProperties=0  
       
    
    def initFiles(self):
        self.singleFile = open(self.singleCSVFile, "a")
        self.condoFile = open(self.condoCSVFile, "a")
        self.apartmentFile = open(self.apartmentCSVFile, "a")
        print("singleCSVExists "+str(self.singleCSVExists))
        if self.singleCSVExists is False:
            print("write to single... ")
            self.singleFile.write("type,zpid,address,city,state,zipcode,date,year built,age,size,lot size,price,estimate rent")
            self.singleFile.write('\n')
        if self.condoCSVExists is False:
            self.condoFile.write("type,zpid,address,city,state,zipcode,date,year built,age,size,lot size,price,estimate rent")
            self.condoFile.write('\n')
        if self.apartmentCSVExists is False:
            self.apartmentFile.write("type,zpid,address,city,state,zipcode,date,year built,age,size,lot size,price,estimate rent")
            self.apartmentFile.write('\n') 
        
    def cleanup(self):
        self.singleFile.close()
        self.condoFile.close()
        self.apartmentFile.close()           
        self.zillowConn.close()
        self.addressConn.close()  
        
    def dumpStats(self):
        timeTaken = round(time.time()*1000)-self.beginTime
        timePerProperty = round(timeTaken/self.totalNumOfProperties)

        print("Total time taken: "+str(timeTaken)+" ms for "+str(self.totalNumOfProperties)+" properties and "+str(self.numOfRecords)+" records.")
        #print("Total time taken: "+str(timeTaken)+" ms for "+str(self.totalNumOfProperties)+" properties.")
        print("Average "+str(timePerProperty)+" ms per property.")
        print("Done !!!")

    def getZillowImgByGoogleSearch(self, keywords):
        # https://www.google.com/search?tbm=isch&q=zillow+1368+crockett+75033+year+built+sqft
        keywords = keywords.replace(" ","+")
        responseX = self.sendRequestEx(self.googleConn, "/search?tbm=isch&q=zillow+"+keywords) 
        #responseX = self.sendRequestEx(self.googleConn, "/search?client=firefox-b-1-d&q=zillow+1368+crockett+75033&tbm=isch&ved=2ahUKEwiXxLCIp_LwAhVRG6wKHVrpDxcQ2-cCegQIABAA&oq=zillow+1368+crockett+75033&gs_lcp=CgNpbWcQA1AAWABgs8UCaABwAHgAgAEAiAEAkgEAmAEAqgELZ3dzLXdpei1pbWc&sclient=img&ei=pP2zYJfiMdG2sAXa0r-4AQ&bih=1058&biw=1920&client=firefox-b-1-d") 
        response=str(responseX)     
        #return response
        index1 = response.find('https://encrypted-tbn0.gstatic.com')  
        

        
        if index1 != -1:
            response = response[index1:]
            imgURL = response[:response.find('"')]          
        return imgURL        
        
    def getAddressInfoByCompass(self, keywords):
        keywords = keywords.replace(" ","+")
        responseX = self.sendRequestEx(self.googleConn, "/search?q=compass+"+keywords) 
        response=str(responseX) 
       
        dataInfo = []        
        index1 = response.find('www.compass.com/listing/')        
      
        if index1 != -1:
            response = response[index1+15:]
            link = response[:response.find('"')]
            link = link[:link.find('&')]
            dataInfo = self.searchCompassPropertyByURI(self.compassConn,link)
        return dataInfo
       
       

    def searchCompassPropertyByURI(self, conn, uri):

        rawdata = self.sendRequest(conn, uri)
        resultData = []
        #Find Property Details
        propDetails=rawdata[rawdata.find('uc-listing-assessorInfo-homeFacts-title'):]
        propDetails=propDetails[:propDetails.find('APN')]
        houseSize=propDetails[propDetails.find('<span>Total Finished SqFt')+40:]
        houseSize=houseSize[:houseSize.find('SqFt</strong>')].replace(',','').strip()
        
        yearBuilt=propDetails[propDetails.find('Year Built</span><strong>')+25:]
        yearBuilt=yearBuilt[:yearBuilt.find('</strong>')].strip()
        
        imgURL=rawdata[rawdata.find('originalUrl')+14:]
        imgURL=imgURL[:imgURL.find('.jpg')+4].strip()
        
        address = uri.split('/')[2].replace("-", " ")
        propType=propDetails[propDetails.find('Style</span><strong>')+20:]
        propType=propType[:propType.find('</strong>')].strip().lower()
        
        # Find property type
        houseType = "single"
        
        if propType.find("single")==-1 :
            houseType = "condo"

        resultData.append(yearBuilt)
        resultData.append(houseSize)
        resultData.append(address)        
        resultData.append(houseType)
        resultData.append(imgURL)
 
        return resultData   
       
    def getAddressInfoByKeywords(self, keywords):
        keywords = keywords.replace(" ","+")
        responseX = self.sendRequestEx(self.googleConn, "/search?q=zillow+"+keywords+"+sq.+ft+built") 
        response=str(responseX) 
       
        dataInfo = []        
        index1 = response.find('zillow.com/homedetails')        
      
        if index1 != -1:
            response = response[index1:]
            address = response[:response.find('_zpid')].split('/')[2].replace('-',' ')

            
            addressInfo = address.split(' ')
            addressKey = addressInfo[0]+' '+addressInfo[1]
            
            
            
            houseDetails = response[response.find(addressKey)+5:]
            houseDetails = houseDetails[houseDetails.find(addressKey)-100:]

            houseDetails = houseDetails[:houseDetails.find('</div')]
            
            houseType = 'single'
            
            if houseDetails.lower().find('single')==-1:
                houseType = 'condo'
            idx = houseDetails.find('built in')
            #This home was <em>built</em> in 1999 ...</span>
            if idx!=-1:
                builtYear = houseDetails[houseDetails.find('built in')+8:].replace('.', ' ').replace(',',' ').replace(';',' ').strip()
            else:
                builtYear = houseDetails[houseDetails.find('built:')+6:].replace('.', ' ').replace(',',' ').replace(';',' ').strip()
             
            
            builtYear = builtYear.split(' ')[0][:4]
            dataInfo.append(builtYear)
            
            idx = houseDetails.lower().find('sq. ft')
            
            if idx!=-1:
                houseSize = houseDetails[idx-9:].strip()
            else:
                houseSize = houseDetails[houseDetails.lower().find('square')-8:].strip()
            
            houseSize = houseSize.split(' ')[1]
            if houseSize.isnumeric() is False:
                #search by Zillow
                return 'try zillow'
            dataInfo.append(houseSize)
            
            dataInfo.append(address)
            
            dataInfo.append(houseType)
            
            imgURL = self.getZillowImgByGoogleSearch(keywords)
            dataInfo.append(imgURL)
            
        return dataInfo 
        
    def getAddressInfoByKeywordsZ(self, keywords):
        keywords = keywords.replace(" ","+")
        responseX = self.sendRequestEx(self.googleConn, "/search?q=zillow+"+keywords) 
        response=str(responseX) 
        zillowURI = ""        
        dataInfo = []        
        index1 = response.find('zillow.com/homedetails')        
        if index1 != -1:
            response = response[index1+10:]
            response = response[:response.find('zpid')+5]
            zillowURI = response
            response = response[13:]
            response = response[:response.find('/')].lower()
            dataInfo = response.split("-")
            addressInfo=self.getInfoByZipcode(dataInfo[len(dataInfo)-1])
            city = addressInfo[1].split(",")[0].lower()            
            city2 = city.replace(" ","-")          
            response = response.replace(city2, city)+"-"+addressInfo[2].lower()
            dataInfo = response.split("-")     
            dataInfo.append(zillowURI)            
        return dataInfo  
        
    def getFullAddressIdByStreet(self, searchAddress, targetAddress):
        print("===Searching Street: "+searchAddress)
        allHousesFromAStreet=self.getRecordsByURI(self.addressConn, searchAddress)
        return str(searchAddress)
        for i in allHousesFromAStreet:
            addressInfo = i.split("/")
            if addressInfo[5] == targetAddress:
                self.cleanup() 
                return addressInfo[6]  
        self.cleanup()
        return ""
    
    def getInfoByZipcode(self, zipcode):
        response = self.sendRequest(self.zipConn, "/cgi-bin/ziplook.exe?What=1&Zip="+zipcode+"&Submit=Look+It+Up")        
        dataInfo = []
        index1 = response.find('<P><B>AREA')
        response = response[index1:]
        response = response[response.find('<TR>'):]
        response = response[:response.find('</TR>')+5]
        response = response.replace("<P>","")
        response = response.replace("TOP","\"TOP\"")
        
        doc = parseString(response)
        allRecords = doc.getElementsByTagName("TD")
        
        for i in allRecords:
            data = i.firstChild.nodeValue
            dataInfo.append(data)
        return dataInfo        
        
    def getLastAccessedProperty(self):
        lastAccessedTime = 0
        found = False
        self.singleCSVExists=path.exists(self.singleCSVFile)
        if self.singleCSVExists is True:
            found = True
            lastAccessedFile = self.singleCSVFile
            lastAccessedTime = os.path.getmtime(self.singleCSVFile)
        self.condoCSVExists=path.exists(self.condoCSVFile)
        if self.condoCSVExists is True:
            found = True
            tempTS = os.path.getmtime(self.condoCSVFile)
            if tempTS > lastAccessedTime:
                lastAccessedFile = self.condoCSVFile
                lastAccessedTime = tempTS
        self.apartmentCSVExists=path.exists(self.apartmentCSVFile)
        if self.apartmentCSVExists is True:
            found = True
            tempTS = os.path.getmtime(self.apartmentCSVFile)
            if tempTS > lastAccessedTime:
                lastAccessedFile = self.apartmentCSVFile
                lastAccessedTime = tempTS    
        if found is True:
            found = True
            with open(lastAccessedFile, "r", encoding="utf-8", errors="ignore") as scraped:
                final_line = scraped.readlines()[-1]
                addrInfo = final_line.split(",")
                address=addrInfo[2].replace(' ','-')
                city=addrInfo[3]
                state=addrInfo[4]
                zipcode=addrInfo[5]
                #final_line=address+"/"+city+"/"+state+"/"+zipcode
                final_line=city+"/"+zipcode+"/"+address
                if final_line != "city/zipcode/address" :
                    #print(final_line)
                    print("===Last Recorded Property: "+final_line+" from "+lastAccessedFile)
                    self.lastProperty = final_line
                    self.resume = True
                    return final_line
                else:
                    self.resume = False
                    self.lastProperty = "None"
                    return "None"                
        else:
            self.resume = False
            self.lastProperty = "None"
            return "None"
    
    def parseData(self, data, key, isNumber):
        idx=data.find(key+'\\"')
        result=data[idx:len(data)]
        idx1=result.find(':')+1
        if isNumber is True:
            idx2=result.find(',')
        else:
            idx1=idx1+2
            idx2=result.find('\\",')    
        result=result[idx1:idx2]
        return result
        
    def searchByCounty(self, state, county, useZillow, writeFile):
        self.searchByCountyEx("/home-values/"+state+"/"+county+"-county/", useZillow, writeFile, True)
    
    def searchByCountyEx(self, countyUri, useZillow, writeFile, cleanUp):
        print("===Processing County: "+countyUri)
        allCitiesFromACounty=self.getRecordsByURI(self.addressConn, countyUri)
        #print(allCitiesFromACounty)
        for i in allCitiesFromACounty:
            self.searchByCityEx(i, useZillow, writeFile, False)
        if cleanUp is True:
            self.cleanup()
            self.dumpStats() 
    
    def searchByCity(self, state, county, city, useZillow, writeFile):
        self.searchByCityEx("/home-values/"+state+"/"+county+"-county/"+city+"/", useZillow, writeFile, True)
        
    def searchByCityEx(self, cityUri, useZillow, writeFile, cleanUp):
        print("===Processing City: "+cityUri)
        allZipsFromACity=self.getRecordsByURI(self.addressConn, cityUri)
        for i in allZipsFromACity:
            self.searchByZipcodeEx(i, useZillow, writeFile, False)
        if cleanUp is True:
            self.cleanup()            
            self.dumpStats() 
    
    def searchByZipcode(self, state, county, city, zipcode, useZillow, writeFile):
        self.searchByZipcodeEx("/home-values/"+state+"/"+county+"-county/"+city+"/"+zipcode+"/", useZillow, writeFile, True)
    
    def searchByZipcodeEx(self, zipUri, useZillow, writeFile, cleanUp):
        print("===Processing Zipcode: "+zipUri)
        allStreetsFromAZip=self.getRecordsByURI(self.addressConn, zipUri)
        for i in allStreetsFromAZip:
            self.searchByStreetEx(i, useZillow, writeFile, False)
        if cleanUp is True: 
            self.cleanup()   
            self.dumpStats() 
    
    def searchByStreet(self, state, county, city, zipcode, street, useZillow, writeFile):    
        self.searchByStreetEx("/home-values/"+state+"/"+county+"-county/"+city+"/"+zipcode+"/"+street+"/", useZillow, writeFile, True )

    def searchByStreetEx(self, streetUri, useZillow, writeFile, cleanUp):
        print("===Processing Street: "+streetUri)
        allHousesFromAStreet=self.getRecordsByURI(self.addressConn, streetUri)
        
        self.totalNumOfProperties += len(allHousesFromAStreet)
        for i in allHousesFromAStreet:
            
            if self.resume:
                if self.resumeBegin is False:
                    if i.find(self.lastProperty)!=-1:
                        self.resumeBegin = True
                        print("Resume from "+i)
                        self.resume = False
                        continue
                    else:
                        continue           
            if useZillow is True:
                houseInfo = i.split("/")
                address=houseInfo[5]
                city=houseInfo[3]
                state=houseInfo[2]
                zipcode=houseInfo[4]
                propURI=address+"/"+city+"/"+state+"/"+zipcode            
                #print("====Processing Property: "+propURI)
                houseHistory = self.searchZillowProperty(self.zillowConn, propURI)
            else:
                #print("====Processing Property: "+i)
                houseHistory = self.searchProperty(self.addressConn, i)
            #print(json.dumps(houseHistory))
            self.numOfRecords += len(houseHistory)     
            if writeFile is True:
                self.writePropertyRecordsToFile(houseHistory)
        if cleanUp is True:                
            self.cleanup()            
            self.dumpStats()        
        
    def searchBySingleZillowAddress(self, state, city, zipcode, address, writeFile):
        # example: 1368-crockett-dr/frisco/tx/75033
        propURI=address+"/"+city+"/"+state+"/"+zipcode 
        print("===Processing Property: "+propURI)
        houseHistory = self.searchZillowProperty(self.zillowConn, propURI)
        self.numOfRecords += len(houseHistory)     
        if writeFile is True:
            self.writePropertyRecordsToFile(houseHistory)   
        self.cleanup()            
        self.dumpStats()        
                        
    def getRecordsByURI(self, conn, uri):
        response = self.sendRequest(conn, uri)
        dataInfo = []
        index1 = response.find('<div class="bgContent">')
        response = response[index1:]
        index2 = response.find('RT_Homevalues_rllink_div') - 12 
        if index2<0:
            return dataInfo
  
        response = response[:index2] + "</div>"
        response = response.replace("itemscope", "")
        response = response.replace('&', "")        
        
        doc = parseString(response)
        allRecords = doc.getElementsByTagName("a")
        
        for i in allRecords:
            data = i.getAttribute("href")
            if len(data.split("/"))>1:            
                dataInfo.append(data)
        return dataInfo
 
    def searchProperty(self, conn, address):
        rawdata = self.sendRequest(conn, address)

        addrInfo = address.split("/")
        address=addrInfo[5]
        city=addrInfo[3]
        state=addrInfo[2]
        zipcode=addrInfo[4]
        zpid=addrInfo[6]
        resultData = []     

        priceIdx=rawdata.find("http://schema.org/PropertyValue")
        if priceIdx==-1 :
            return resultData
  
        currentPrice=rawdata[:len(rawdata)]
        currentPrice=currentPrice[currentPrice.find("<strong>")+9:currentPrice.find("</strong>")]
        currentPrice=currentPrice.replace(",","")

  
        #print("zpid: "+str(zpid))
        #print("currentPrice: "+str(currentPrice))

        estRent=int(int(currentPrice)*0.007)
        #print("estimate Rent: "+str(estRent))
        
        #Find Property Details
        propDetails=rawdata[rawdata.find('<section class="section-block" id="propertyDetailsContainer"'):len(rawdata)]
        propDetails=propDetails[:propDetails.find('</section>')+10]
        propDetails=propDetails.replace('itemscope','')
        propDetails=propDetails.replace('itemtype=https://schema.org/PropertyValue','')
        propDetails=propDetails.replace('itemtype=https://schema.org/Residence','')
        propDetails=propDetails.replace('itemprop=additionalProperty','')
        propDetails=propDetails.replace('&nbsp;','')

        yearBuilt="0"
        propSize="0"
        lotSize="0"
 
        doc = parseString(propDetails)        
        allDetails = doc.getElementsByTagName("span")
        
        # Find property type
        propType=allDetails[2].firstChild.nodeValue
        if propType.find("Single Family")!=-1 or propType.find("Miscellaneous (general)")!=-1 or propType.find("Miscellaneous (Residential)")!=-1:  
            propType = "Single Family"
        elif propType.find("Dwellings")!=-1 or propType.find("Apart")!=-1:
            propType = "Apartment"
        elif propType.find("Land")!=-1 :
            return resultData
        else:
            #propType.find("Condo")!=-1 or propType.find("Town")!=-1 or propType.find("Multi")!=-1 or propType.find("Multi")!=-1 :
            propType = "Townhouse"        
        #print("Property Type:"+propType)
        
        for i in range(4,len(allDetails),1):
            attr=allDetails[i].getAttribute("itemprop")
            value=allDetails[i].firstChild.nodeValue
            if attr == "name" and value == "Home Size" :
                propSize=allDetails[i+1].firstChild.nodeValue
            if attr == "name" and value == "Lot Size" :
                lotSize=allDetails[i+1].firstChild.nodeValue
            if attr == "description" and value == "Built in" :
                yearBuilt=allDetails[i+1].firstChild.nodeValue

        if yearBuilt is None or yearBuilt == "null" or len(yearBuilt.strip())!=4 :
            return resultData

        if len(lotSize)>3 and lotSize.find(",")!=-1 :
            lotSize=int(lotSize.replace(",",""))
        else:
            lotSize="0"
        #print("lotSize: "+str(lotSize))

        # Find property size
        if len(propSize)>2 and propSize.find(",")!=-1 :
            propSize=int(propSize.replace(",",""))
        else:
            propSize="0"       
        #print("Property Size: "+str(propSize)+" sqft")

        age = int(date.today().strftime('%Y')) - int(yearBuilt)     
        #print("house age "+str(age)) 
        
        today=date.today().strftime('%Y')
        #print("Date: "+str(today)+" tax: None price:"+str(currentPrice))
        
        currentYear = {}
        currentYear["type"] = propType
        currentYear["zpid"] = zpid
        currentYear["address"] = address
        currentYear["city"] = city
        currentYear["state"] = state
        currentYear["zipcode"] = zipcode
        currentYear["date"] = today
        currentYear["yearBuilt"] = int(yearBuilt)
        currentYear["age"] = age
        currentYear["size"] = propSize
        currentYear["lotSize"] = lotSize
        currentYear["price"] = int(currentPrice)
        currentYear["rentEst"] = estRent
        resultData.append(currentYear)
        
        # Find historical house sales price or assessment value
        idx=rawdata.find('<table class="history-table">')
        if idx==-1 :
            return resultData
        price=rawdata[idx:len(rawdata)]
        idx=price.find('</table>')
        price=price[:idx+8]
  
        doc = parseString(price)        
        tbody = doc.getElementsByTagName("tbody")
        trs = tbody[0].getElementsByTagName("tr")
        count=0
        totalSize = len(trs)
        for i in trs:
            count+=1
            if count == totalSize:   
                # skip the first year record
                break        
            tds = i.getElementsByTagName("td")

            p = int(tds[4].firstChild.nodeValue.replace('$','').replace(",",""))
            pastYear = {}
            pastYear["type"] = propType
            pastYear["zpid"] = zpid
            pastYear["address"] = address
            pastYear["city"] = city
            pastYear["state"] = state
            pastYear["zipcode"] = zipcode        
            pastYear["date"] = int(tds[0].firstChild.nodeValue)
            pastYear["yearBuilt"] = int(yearBuilt)
            age2 = int(tds[0].firstChild.nodeValue) - int(yearBuilt)
            pastYear["age"] = age2
            pastYear["size"] = propSize
            pastYear["lotSize"] = lotSize
            pastYear["price"] = p
            pastYear["rentEst"] = int(p*0.007)  
            if age2>=0 :
                resultData.append(pastYear)                        
            #print("Date: "+str(d)+" tax: "+str(tax)+" price:"+str(v))  
        #print(jsonData)
        return resultData
    
    def searchZillowPropertyByURI(self, conn, address):
    
    
        rawdata = self.sendRequest(conn, address[len(address)-1])
        resultData = []
        #Find Property Details
        propDetails=rawdata[rawdata.find('{\\"property\\"'):len(rawdata)]
        
        # Find property type
        propType=self.parseData(rawdata, "propertyTypeDimension", False)
        if propType.find("Single Family")!=-1 :
            propType = "Single Family"
        elif propType.find("Dwellings")!=-1 or propType.find("Apart")!=-1:
            propType = "Apartment"
        elif propType.find("Land")!=-1 :
            return resultData
        else:
            #propType.find("Condo")!=-1 or propType.find("Town")!=-1 or propType.find("Multi")!=-1 or propType.find("Multi")!=-1 :
            propType = "Townhouse"        
        #print("Property Type:"+propType)        

        zpid=self.parseData(propDetails, "zpid", True)
        #print("zpid: "+str(zpid))
        currentPrice=self.parseData(propDetails, "price", True)
        if currentPrice == 0 or currentPrice == "0":
            temp = propDetails[propDetails.find('hdpTypeDimension'):len(propDetails)]
            currentPrice=self.parseData(temp, "zestimate", True)
        #print("currentPrice: "+str(currentPrice))
        estRent=self.parseData(propDetails, "zestimate", True)
        if estRent is None or estRent == "null" :
            estRent = int(currentPrice)*0.007
            
        #print("estimate Rent: "+str(estRent))
        yearBuilt=self.parseData(propDetails, "yearBuilt", True)
        
        if yearBuilt is None or yearBuilt == "null" or len(yearBuilt.strip())!=4 :
            return resultData
     
        lotSize=self.parseData(propDetails, "lotSize", True)
        if lotSize is None or lotSize == "null" or len(lotSize.strip())<4 :
            lotSize = "0"        
        #print("lotSize: "+str(lotSize))

        # Find property type
        propSize=self.parseData(rawdata, "livingAreaValue", True)
        #print("Property Size: "+str(propSize)+" sqft")

        age = int(date.today().strftime('%Y')) - int(yearBuilt)     
        #print("house age "+str(age)) 
        
        today=date.today().strftime('%Y')
        #print("Date: "+str(today)+" tax: None price:"+str(currentPrice))


        address.pop()

        infoSize = len(address) 
        city=address[infoSize-4]
        state=address[infoSize-3]
        zipcode=address[infoSize-2] 
        county=address[infoSize-1] 
        street = ""
        for i in range(0, infoSize-4, 1):
            street += address[i] +" "
        street = street.strip().replace("-"," ")        
        
        #find house image
        imgDetails=rawdata[rawdata.find('home-details-content'):len(rawdata)]
        
        imgDetails=imgDetails[:imgDetails.find('</picture>')+10]
        imgDetails=imgDetails[imgDetails.find('<picture'):]
        
        doc = parseString(imgDetails)
        imgSource = doc.getElementsByTagName("img")
        imgURL = imgSource[0].getAttribute('src')
        
        
        currentYear = {}
        currentYear["type"] = propType
        currentYear["zpid"] = zpid
        currentYear["address"] = street
        currentYear["city"] = city
        currentYear["state"] = state
        currentYear["zipcode"] = zipcode
        currentYear["date"] = today
        currentYear["yearBuilt"] = int(yearBuilt)
        currentYear["age"] = age
        currentYear["size"] = propSize
        currentYear["lotSize"] = lotSize
        currentYear["price"] = currentPrice
        currentYear["rentEst"] = estRent
        currentYear["imgURL"] = imgURL
        
        resultData.append(currentYear)    
        return resultData
        
    def searchZillowProperty(self, conn, address):
        rawdata = self.sendRequest(conn, "/homes/"+address.replace('/','-')+"_rb/")
        resultData = []
        #Find Property Details
        propDetails=rawdata[rawdata.find('{\\"property\\"'):len(rawdata)]
        
        # Find property type
        propType=self.parseData(rawdata, "propertyTypeDimension", False)
        if propType.find("Single Family")!=-1 :
            propType = "Single Family"
        elif propType.find("Dwellings")!=-1 or propType.find("Apart")!=-1:
            propType = "Apartment"
        elif propType.find("Land")!=-1 :
            return resultData
        else:
            #propType.find("Condo")!=-1 or propType.find("Town")!=-1 or propType.find("Multi")!=-1 or propType.find("Multi")!=-1 :
            propType = "Townhouse"        
        #print("Property Type:"+propType)        

        zpid=self.parseData(propDetails, "zpid", True)
        #print("zpid: "+str(zpid))
        currentPrice=self.parseData(propDetails, "price", True)
        if currentPrice == 0 or currentPrice == "0":
            temp = propDetails[propDetails.find('hdpTypeDimension'):len(propDetails)]
            currentPrice=self.parseData(temp, "zestimate", True)
        #print("currentPrice: "+str(currentPrice))
        estRent=self.parseData(propDetails, "zestimate", True)
        if estRent is None or estRent == "null" :
            estRent = int(currentPrice)*0.007
            
        #print("estimate Rent: "+str(estRent))
        yearBuilt=self.parseData(propDetails, "yearBuilt", True)
        
        if yearBuilt is None or yearBuilt == "null" or len(yearBuilt.strip())!=4 :
            return resultData
     
        lotSize=self.parseData(propDetails, "lotSize", True)
        if lotSize is None or lotSize == "null" or len(lotSize.strip())<4 :
            lotSize = "0"        
        #print("lotSize: "+str(lotSize))

        # Find property type
        propSize=self.parseData(rawdata, "livingAreaValue", True)
        #print("Property Size: "+str(propSize)+" sqft")

        age = int(date.today().strftime('%Y')) - int(yearBuilt)     
        #print("house age "+str(age)) 
        
        today=date.today().strftime('%Y')
        #print("Date: "+str(today)+" tax: None price:"+str(currentPrice))

        # Find historical house sales price or assessment value
        idx=rawdata.find('taxHistory\\":[{')
        price=rawdata[idx:len(rawdata)]
        idx=price.find(']')
        price=price[0:idx+1]
        idx=price.find('[')
        price=price[idx:len(price)].replace('\\"','"')

        addrInfo = address.split("/")
        address=addrInfo[0]
        city=addrInfo[1]
        state=addrInfo[2]
        zipcode=addrInfo[3]
        
        
        currentYear = {}
        currentYear["type"] = propType
        currentYear["zpid"] = zpid
        currentYear["address"] = address
        currentYear["city"] = city
        currentYear["state"] = state
        currentYear["zipcode"] = zipcode
        currentYear["date"] = today
        currentYear["yearBuilt"] = int(yearBuilt)
        currentYear["age"] = age
        currentYear["size"] = propSize
        currentYear["lotSize"] = lotSize
        currentYear["price"] = currentPrice
        currentYear["rentEst"] = estRent
        resultData.append(currentYear)
        if price is None or price == "null" or len(price.strip())==0 :
            return resultData
            
        jsonData=json.loads(price)
        count=0
        totalSize = len(jsonData)
        for i in jsonData:
            count+=1
            if count == totalSize:   
                # skip the first year record
                break
            t=int(i["time"])/1000
            d=datetime.fromtimestamp(t).strftime('%Y')
            #tax = i["taxPaid"]
            p = i["value"]
            pastYear = {}
            pastYear["type"] = propType
            pastYear["zpid"] = zpid
            pastYear["address"] = address
            pastYear["city"] = city
            pastYear["state"] = state
            pastYear["zipcode"] = zipcode        
            pastYear["date"] = d
            pastYear["yearBuilt"] = int(yearBuilt)
            age2 = int(datetime.fromtimestamp(t).strftime('%Y')) - int(yearBuilt)
            pastYear["age"] = age2
            pastYear["size"] = propSize
            pastYear["lotSize"] = lotSize
            pastYear["price"] = p
            pastYear["rentEst"] = int(p*0.007)
            if age2>=0 :
                resultData.append(pastYear)        
            #print("Date: "+str(d)+" tax: "+str(tax)+" price:"+str(v))  
        #print(jsonData)
        return resultData
        
    def sendRequest(self, conn, uri):        
        conn.request("GET", uri)
        response = conn.getresponse()        
        if response.status != 200:
            print("Error: Status: {} and reason: {}".format(response.status, response.reason))
        return response.read().decode('utf-8')          

    def sendRequestEx(self, conn, uri):        
        conn.request("GET", uri)
        response = conn.getresponse()        
        if response.status != 200:
            print("Error: Status: {} and reason: {}".format(response.status, response.reason))
                    
        #gz = response.read()
        #j = gzip.decompress(gz)
        #return json.loads(j.decode('utf-8'))  
        return response.read()         
        
    def badDataFilter(self, houseHistory):
        last=0
        for i in reversed(range(len(houseHistory))):
          change = int(houseHistory[i]["price"])-last
          diff = abs(change)
          #print("===processing ",houseHistory[i])
          #print("last="+str(last)+" change="+str(change)+" v="+str(houseHistory[i]["price"]))
          if last!=0:
            percent=diff/int(houseHistory[i]["price"])*100
            #print("===percent:", percent)
            if change < 0 and percent > 30:
              print("Bad Data !!!! greater than 30 percent change (reduced) over last year. Remove: ", houseHistory[i])
              del houseHistory[i]
            else:
              last=int(houseHistory[i]["price"])
          last=int(houseHistory[i]["price"])
        return houseHistory

    def writePropertyRecordsToFile(self, houseHistory):
        fileToWrite = self.singleFile
        if len(houseHistory) > 0:
            propType = houseHistory[0]["type"]
            if propType.find("Single")!=-1 :
                fileToWrite = self.singleFile
            elif propType.find("Townhouse")!=-1 :
                fileToWrite = self.condoFile
            else:
                fileToWrite = self.apartmentFile 
        houseHistory = self.badDataFilter(houseHistory)        
        for j in houseHistory:
            entry = j["type"]+","+str(j["zpid"])+","+j["address"].replace('-',' ')+","+j["city"]+","+j["state"]+","+str(j["zipcode"])+","+str(j["date"])+","+str(j["yearBuilt"])+","+str(j["age"])+","+str(j["size"])+","+str(j["lotSize"])+","+str(j["price"])+","+str(j["rentEst"]) 
            fileToWrite.write(entry)
            fileToWrite.write('\n')    
    
