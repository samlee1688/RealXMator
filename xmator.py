import pandas as pd  
from sklearn.linear_model import LinearRegression
import pickle
from os import path
from sklearn.preprocessing import PolynomialFeatures  


class realXMator:

    singleModel = pickle.load(open('xMator-single.model', 'rb'))
    condoModel = pickle.load(open('xMator-condo.model', 'rb'))
    
    def __init__(self):        
        self.poly_regs= PolynomialFeatures(degree= 2)

    def train(self, modelFile):
        modelFileExists=path.exists(modelFile)
        if modelFileExists is True:
            model = pickle.load(open(modelFile, 'rb'))
            #print('used exisiting')
            return model
    
        #print('new created')
        self.df = pd.read_csv(file)
        X = self.df[['date','age','size']].values.reshape(-1,3)
        y = self.df['price'].values.reshape(-1,1)
         
        x_poly= self.poly_regs.fit_transform(X)  
        
        model =LinearRegression()  
        model.fit(x_poly, y)  
    
        #model = TransformedTargetRegressor(
                                        #regressor=RidgeCV(),
                                        #transformer=QuantileTransformer(n_quantiles=900,
                                       # output_distribution='normal'))
        #model = TransformedTargetRegressor(regressor=LinearRegression(),transformer=QuantileTransformer(n_quantiles=900,output_distribution='normal'),func=np.exp, inverse_func=np.log)
        #model.fit(X, y)
    
        #pred = model.predict(X_test)
        pickle.dump(model, open(modelFile, 'wb'))
        return model
    
    def pred(self, testData, propType):
        if len(testData) == 3:
            if propType.find("single")!=-1 :
                model = self.singleModel
            else:
                model = self.condoModel
            predictions = model.predict(self.poly_regs.fit_transform([testData]))
            
            #predictions = model.predict([testData])
            return predictions
        else:
            return []
	
if __name__ == "__main__":
    xMator0 = realXMator()
    model = xMator0.train('xMator-single.model')




