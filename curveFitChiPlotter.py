import sys
import matplotlib.pyplot as plt
import matplotlib.collections as cl
import numpy as np

def findChi(modelPath, dataPath):

    modelFile = open(modelPath, 'r')
    modelText = modelFile.read()
    modelLines = modelText.splitlines()

    dataFile = open(dataPath, "r")
    dataText = dataFile.read()
    dataLines = dataText.splitlines()

    modelDataLines = modelLines[1:]
    dataLines = dataLines[3:]

    modelLam, modelFlux = [], []
    dataLam, dataFlux, error, names = [], [], [], []

    def getLine(point1, point2):
        return (point1, (point2[1]-point1[1])/(point2[0]-point1[0]))

    def findIntercept(modelPoint, line):
        x = modelPoint[0]
        y = line[1]*(x-line[0][0]) + line[0][1]
        return (x, y)

    for i in range(len(modelDataLines)): # intentionally discarding the second and third columns because flux is 0
        valueslist2 = modelDataLines[i].split("     ")
        modelLam.append(float(valueslist2[1]))
        modelFlux.append(float(valueslist2[2]))

    for i in range(len(dataLines)):
        valueslist = dataLines[i].split(" ")
        if valueslist[3] != 'nan' and float(valueslist[3]) != 0 and float(valueslist[0])*10**6 != 4.35:
            dataLam.append(float(valueslist[0])*10**6)
            names.append(valueslist[1])
            dataFlux.append(float(valueslist[2]))
            error.append(float(valueslist[3]))
    
    listOfRanges = []
    xyerrTuples = [(dataLam[i],dataFlux[i],error[i]) for i in range(len(dataLam))]
    modelTuples = [(modelLam[i],modelFlux[i]) for i in range(len(modelLam))]
    fitPts = [[dataLam[i],dataFlux[i],error[i]] for i in range(len(dataLam))]
    xyerrTuples.sort()
    fitPts.sort()
    pointDict, modelPointDict = {}, {'x':[], 'y':[]}
    
    for i in range(len(names)): # Creating a dictionary of the data points based on author
        names[i] = names[i].split(":")[0]
        if pointDict.get(names[i]) == None:
            pointDict[names[i]] = [list(xyerrTuples[i])]
        else:
            pointDict[names[i]] += [list(xyerrTuples[i])]

    for tuple in modelTuples:
        modelPointDict['x'] += [tuple[0]]
        modelPointDict['y'] += [tuple[1]]

    count = 0
    for j in range(len(xyerrTuples)-1): 
        if xyerrTuples[j][0] == xyerrTuples[j+1][0]: # If two points have the same x val, take the average of the y vals and errors
            fitPts[count][1] = (xyerrTuples[j][1] + xyerrTuples[j+1][1])/2 
            fitPts[count][2] = (xyerrTuples[j][2] + xyerrTuples[j+1][2])/2
            fitPts.pop(count+1)
        else:
            xmin, xmax = xyerrTuples[j][0], xyerrTuples[j+1][0]
            listOfRanges.append((xmin, xmax, count))
            count += 1 # Count is the index for points with unique x vals

    dictOfBins = {"nearIr":{ranges:[] for ranges in listOfRanges[:14]}, "midIr":{ranges:[] for ranges in listOfRanges[14:25]}, 
                    "farIr":{ranges:[] for ranges in listOfRanges[25:31]}, "micro":{ranges:[] for ranges in listOfRanges[31:]}}

    for point in modelTuples:
        for i in range(len(listOfRanges)):
            valuerange = listOfRanges[i]
            if valuerange[0] < point[0] and valuerange[1] >= point[0]:
                if i < 14: # If the point lies in the nearIR spectrum
                    dictOfBins["nearIr"][valuerange] += [(point, valuerange[2])] #point and index
                elif 14 <= i and i < 25: 
                    dictOfBins["midIr"][valuerange] += [(point, valuerange[2])]
                elif 25 <= i and i < 31:
                    dictOfBins["farIr"][valuerange] += [(point, valuerange[2])]
                else:
                    dictOfBins["micro"][valuerange] += [(point, valuerange[2])]

    plt.figure(facecolor='#808080')
    ax = plt.axes()
    ax.set_facecolor("#404040")
    plt.plot(modelPointDict['x'], modelPointDict['y'], color="white", alpha=0.75)

    nearIrChi, midIrChi, farIrChi, microChi = 0, 0, 0, 0
    for irBin in dictOfBins:
        for valuerange in dictOfBins[irBin]:
            valuesInBin = dictOfBins[irBin][valuerange]
            binIndex = valuerange[2]
            binPoint1 = (fitPts[binIndex][0],fitPts[binIndex][1])
            binPoint2 = (fitPts[binIndex + 1][0],fitPts[binIndex + 1][1])
            for value in dictOfBins[irBin][valuerange]:
                modelPoint = value[0]
                binLine = getLine(binPoint1, binPoint2)
                expPoint = findIntercept(modelPoint, binLine)
                errorValue = fitPts[binIndex][2]
                variance = (modelPoint[1]-errorValue)**2
                d_chi = (modelPoint[1]-expPoint[1])**2 / expPoint[1] **2
                if irBin == "nearIr":
                    nearIrChi += d_chi
                elif irBin == "midIr":
                    midIrChi += d_chi
                elif irBin == "farIr":
                    farIrChi += d_chi
                else:
                    microChi += d_chi
        
    # Weighting the Chi values based on the number of data points
    nearIrChi = (nearIrChi * len(listOfRanges)) / len(listOfRanges[:14])
    midIrChi = (midIrChi * len(listOfRanges)) / len(listOfRanges[14:25]) 
    farIrChi = (farIrChi * len(listOfRanges)) / len(listOfRanges[25:31])
    microChi = (microChi * len(listOfRanges)) / len(listOfRanges[31:])
    
    # Plotting the graph based on wavelength ranges
    plt.plot([fitPts[i][0] for i in range(len(fitPts[:15]))],[fitPts[i][1] for i in range(len(fitPts[:15]))], color="#FFCC00", alpha=0.75)
    plt.plot([fitPts[i+14][0] for i in range(len(fitPts[14:26]))],[fitPts[i+14][1] for i in range(len(fitPts[14:26]))], color="#FF6600", alpha=0.75)
    plt.plot([fitPts[i+25][0] for i in range(len(fitPts[25:31]))],[fitPts[i+25][1] for i in range(len(fitPts[25:31]))], color="#FF3300", alpha=0.75)
    plt.plot([fitPts[i+30][0] for i in range(len(fitPts[30:]))],[fitPts[i+30][1] for i in range(len(fitPts[30:]))], color="#CC0066", alpha=0.75)
    
    # Plotting data points and error bars
    for key in pointDict:
        xVals, yVals, errVals = [],[],[]
        for val in pointDict[key]:
            xVals += [val[0]]
            yVals += [val[1]]
            errVals += [val[2]]
        plt.scatter(xVals, yVals, marker="o", linewidths=0.5, label = str(key), alpha = 0.75)
        plt.errorbar(xVals, yVals, yerr = errVals, fmt = 'None', ecolor='white', alpha=0.5)

    return (nearIrChi,midIrChi,farIrChi, microChi)



def plotModel(modelPath, dataPath):
    filename2 = modelPath.split('/')[-2]
    chiVals = findChi(modelPath, dataPath)

    plt.title("Near IR $\chi^2$: " + str(f'{chiVals[0]:.3f}') +" Mid IR $\chi^2$:" + str(f'{chiVals[1]:.3f}') + "\nFar IR $\chi^2$: " 
              + str(f'{chiVals[2]:.3f}')+" Micro $\chi^2$: " + str(f'{chiVals[3]:.3f}'), fontsize = '8',x=0.1)
    plt.suptitle("SED for " + filename2, fontsize = '16', y = 0.96)
    plt.xlabel('lambda (microns)')
    plt.ylabel('flux ${W}/{m^2}$')
    plt.xscale('log')
    plt.yscale('log')
    
    plt.legend()

    plt.show()

modelPath = str(sys.argv[1])
#modelPath = "/Users/jakeschaefer/Desktop/SED/sed68_inc042.dat"
dataPath = "/Users/jakeschaefer/Desktop/mwc275_phot_cleaned_0.dat"
def main(modelPath, dataPath):
    plotModel(modelPath, dataPath)

if __name__ == '__main__':
    main(modelPath, dataPath)