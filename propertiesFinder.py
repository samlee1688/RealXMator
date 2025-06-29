import http.client

class PropertiesFinder:

    
    def __init__(self):
        self.googleConn = http.client.HTTPSConnection("www.google.com")
        self.compassConn = http.client.HTTPSConnection("www.compass.com")
        
    def getAddressInfoByCompass(self, keywords):
        dataInfo = []
        keywords = keywords.replace(" ","+")
        responseX = self.sendRequestEx(self.googleConn, "/search?q=compass+"+keywords) 
        response=str(responseX).strip() 
        
        #print("Dave Response from Google search result of Compass : "+response)
        
        if len(response) == 0:
            return dataInfo
        #test
        index = response.find('www.compass.com/listing/')
        if index != -1 and index < 23000:
            response = response[index+15:]
            link = response[:response.find('"')]
            link = link[:link.find('&')]
            dataInfo = self.searchCompassPropertyByURI(self.compassConn,link)
        return dataInfo

    def searchCompassPropertyByURI(self, conn, uri):
        resultData = []
        rawdata = self.sendRequest(conn, uri)
        if len(rawdata) == 0:
            return resultData
        
        #Find Property Details
        houseSize = rawdata[rawdata.find('og:description')+30:]
        houseSize = houseSize[:houseSize.find('sqft')].strip()        
        houseSizeInfo = houseSize.split(' ')
        houseSize = houseSizeInfo[len(houseSizeInfo)-1].replace(',','').strip()        
        if houseSize.isnumeric() is False:
            return resultData
        
        # Find property type
        houseInfo = rawdata[rawdata.find('MLS Type'):]
        propType = houseInfo[houseInfo.find('--strong')+10:houseInfo.find('</td>')].lower()
        if propType.lower().find("land")!=-1:
            return resultData        
        houseType = "condo"        
        if propType.find("single")!=-1 or propType.find("house")!=-1 :
            houseType = "single"  
              
        yearBuilt=houseInfo[houseInfo.find('Year Built')+25:]
        yearBuilt = yearBuilt[yearBuilt.find('--strong')+10:yearBuilt.find('</td>')].strip()
        if yearBuilt.isnumeric() is False:
            return resultData
        imgURL=rawdata[rawdata.find('originalUrl')+14:]
        imgURL=imgURL[:imgURL.find('.jpg')+4].strip()
        
        address = uri.split('/')[2].replace("-", " ")
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
            if len(addressInfo) < 2: 
                return dataInfo              
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
            
            if builtYear.isnumeric() is False:
                return dataInfo
            
            dataInfo.append(builtYear)
            
            idx = houseDetails.lower().find('sq. ft')
            
            if idx!=-1:
                houseSize = houseDetails[idx-9:].strip()
            else:
                houseSize = houseDetails[houseDetails.lower().find('square')-8:].strip()
            
            houseSize = houseSize.split(' ')[1]
            if houseSize.isnumeric() is False:
                #search by Zillow
                return dataInfo
            dataInfo.append(houseSize)            
            dataInfo.append(address)            
            dataInfo.append(houseType)            
            imgURL = self.getZillowImgByGoogleSearch(keywords)
            dataInfo.append(imgURL)            
        return dataInfo 

    def getAddressInfoByRealtorKeywords(self, keywords):
        keywords = keywords.replace(" ","+")
        responseX = self.sendRequestEx(self.googleConn, "/search?q=realtor+"+keywords+"+sq.+ft+built") 
        response=str(responseX)
        dataInfo = []    
        # "https://www.realtor.com/realestateandhomes-detail/900-Bristlewood-Dr_McKinney_TX_75072_M80385-79749"
        index1 = response.find('realtor.com/')        
        
        if index1 != -1:
            response = response[index1:]
            address = response[:response.find('"')].split('/')[2]
            address = address[:address.find("&amp")]
            address = address[:address.rfind("_")].replace('-',' ').replace('_',' ')            
            addressInfo = address.split(' ')
            if len(addressInfo) < 2: 
                return dataInfo            
            addressKey = addressInfo[0]+' '+addressInfo[1]
            
            houseDetails = response[response.find(addressKey)+5:]
            temp = houseDetails[:houseDetails.find(addressKey)+20]
            idx = temp.rfind("<div ")
            houseDetails = houseDetails[idx:]            
            houseDetails = houseDetails[:houseDetails.find('</div>')].lower()

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
            
            if builtYear.isnumeric() is False: 
                return dataInfo
            
            dataInfo.append(builtYear)
            
            idx = houseDetails.find('sq. ft')
            
            if idx!=-1:
                houseSize = houseDetails[idx-9:].strip()
            else:
                houseSize = houseDetails[houseDetails.lower().find('square')-8:].strip()
            
            houseSize = houseSize.split(' ')[1]
            if houseSize.isnumeric() is False: 
                return dataInfo
            dataInfo.append(houseSize)            
            dataInfo.append(address)            
            dataInfo.append(houseType)            
            imgURL = self.getZillowImgByGoogleSearch(keywords)
            dataInfo.append(imgURL)                
        return dataInfo 

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
        
    def sendRequest(self, conn, uri): 
        success = False
        for i in range(10):
            try:
                conn.request("GET", uri)
                response = conn.getresponse()        
                if response.status != 200:
                    print("Error: Status: {} and reason: {}".format(response.status, response.reason))
                else:
                    success = True
                    break
            except http.client.RemoteDisconnected:
                print("Got RemoteDisconnected for "+uri+" Retry.") 
            except http.client.CannotSendRequest:
                print("Got CannotSendRequest for "+uri+" Retry.") 
            except http.client.ResponseNotReady:
                print("Got ResponseNotReady for "+uri+" Retry.") 
            except http.client.HTTPException:
                print("Got HTTPException for "+uri+" Retry.") 
            except Exception:
                print("Got Exception for "+uri+" Retry.") 
            #print("==resetting compass connection")
            self.compassConn = http.client.HTTPSConnection("www.compass.com")                
        if success is True:
            #return json.loads(j.decode('utf-8'))  
            return response.read().decode('utf-8')
        else:
            return ""       

    def sendRequestEx(self, conn, uri):
        
        success = False
        for i in range(10):
            try:
                conn.request("GET", uri)
                response = conn.getresponse()        
                if response.status != 200:
                    print("Error: Status: {} and reason: {}".format(response.status, response.reason))
                else:
                    success = True 
                    break
            except http.client.RemoteDisconnected:
                print("Got RemoteDisconnected for "+uri+" Retry.")         
            except http.client.CannotSendRequest:
                print("Got CannotSendRequest for "+uri+" Retry.") 
            except http.client.ResponseNotReady:
                print("Got ResponseNotReady for "+uri+" Retry.") 
            except http.client.HTTPException:
                print("Got HTTPException for "+uri+" Retry.") 
            except Exception:
                print("Got Exception for "+uri+" Retry.") 
            #print("==resetting google connection")    
            self.googleConn = http.client.HTTPSConnection("www.google.com")
               
                
        if success is True:
            #return json.loads(j.decode('utf-8'))  
            return response.read()
        else:
            return ""
