# %% Modules
import datetime as dt

import numpy as np
import pandas as pd


# %%
def ColNum2ColName(n):
    convertString = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base = 26
    i = n - 1

    if i < base:
        return convertString[i]
    return ColNum2ColName(i // base) + convertString[i % base]


# %%
def build_rand_df(randRange=100, colNum=10, rowNum=100, columns=None, absNums=True, intOnly=True):
    if columns is None:
        columns = []
    list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    # if columns == []: columns = colList[:colNum]
    columns = [ColNum2ColName(i) for i in range(1, colNum + 1)]
    # for i in range(1,colNum+1):
    #     print(i, ColNum2ColName(i))

    startRange = 0 if absNums else randRange * -1

    if intOnly:
        return pd.DataFrame(
            np.random.randint(startRange, randRange, size=(rowNum, colNum)), columns=columns
        )
    return pd.DataFrame(
        np.random.uniform(startRange, randRange, size=(rowNum, colNum)), columns=columns
    )


def dataframe_size_in_mb(df):
    # Get memory usage of each column
    memory_usage_per_column = df.memory_usage(deep=True)

    # Total memory usage in bytes
    total_memory_usage = memory_usage_per_column.sum()

    # Convert bytes to megabytes
    return total_memory_usage / (1024 * 1024)


# %% Data Type Parsing
def type_check(val):
    dataTypes = {
        "str": (0, str),
        # 'timeStamp': (1,pd._libs.tslibs.timestamps.Timestamp),
        "timeStamp": (1, "datetime64[ns]"),  # TIMESTAMP WITHOUT TIME ZONE
        "float": (2, float),
        "int": (3, "Int64"),
    }

    try:
        dt.datetime.strptime(val, "%Y-%m-%d")
        return dataTypes["timeStamp"]
    except Exception:
        pass
        # print('ERROR PARSING TYPE',val,e)

    try:
        dt.datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        return dataTypes["timeStamp"]
    except Exception:
        pass
        # print('ERROR PARSING TYPE',val,e)
    try:
        # if isinstance(val,pd._libs.tslibs.timestamps.Timestamp):
        #     # print(val)
        #     print('is instance')
        #     return dataTypes['timeStamp']

        # if parse(val, fuzzy=True):
        #     print('Parse Date')
        #     return dataTypes['timeStamp']

        containsDecimal = str(val).find(".") >= 0
        isNumber = False

        # print(str(val).count('-')<= 1,str(val).count('.')<= 1)
        if str(val).count("-") <= 1 and str(val).count(".") <= 1:
            isNumber = str(val).replace(".", "").replace("-", "").isdigit()

        # print(val, containsDecimal, isNumber)
        if isNumber:
            if containsDecimal:
                if (
                    len(str(val).split(".")) == 2
                    and str(val).split(".")[0] != ""
                    and str(val).split(".")[1] != ""
                ):
                    return dataTypes["float"]
                return dataTypes["str"]
            return dataTypes["int"]
        return dataTypes["str"]
    except Exception as e:
        print("ERROR PARSING TYPE", val, e)
        return dataTypes["str"]


## Gets most inclusive data type for a dataframe column
def getColType(col):
    # print()
    # set col to temp variable and remove null Values
    tempCol = col
    # tempCol = col.replace('', np.nan)
    tempCol = tempCol.dropna()
    tempCol.infer_objects()
    # print(tempCol.info())
    if not tempCol.empty:
        dataTypes = set(tempCol.apply(type_check))
        # print(dataTypes)
        dataTypes = dict(dataTypes)
        # print(col.name, dataTypes)
        dType = dataTypes[min(dataTypes.keys())]
        # print('SET TO DATATYPE:', dType)
        try:
            tempList = set(tempCol.to_list())
            if dType == "Int64":
                tempCol = tempCol.astype(float).astype(dType)
            else:
                tempCol = tempCol.astype(dType)
        except:
            print("INT MESSUP")
            try:
                val = ""
                for _i, v in enumerate(tempList):
                    val = v
                    int(v)
            except Exception as e:
                print(val, e)
    else:
        tempCol = tempCol.astype(str)
    return tempCol.dtype


## Takes a dataframe and returns with columns datatypes auto defined
def autoConvert(df):
    # normalizing NULL values
    df = df.replace(to_replace="", value=np.nan)
    df = df.replace(to_replace="None", value=np.nan)

    dfColDefs = df.apply(getColType)
    # print(dfColDefs)
    for i in dfColDefs.index:
        # print(i)
        if dfColDefs.loc[i] == "Int64":
            # print('converting int',dfColDefs.loc[i])
            df[i] = df[i].astype(float).astype(dfColDefs.loc[i])
            # df[i] = df[i].astype(float).astype(dfColDefs.loc[i], errors='ignore')
        else:
            df[i] = df[i].astype(dfColDefs.loc[i])
    return df


def normalize_col_names(cols):
    # CHECK FOR first character as number and duplicates
    acceptableChars = "abcdefghijklmnopqrstuvwxyz0123456789_"
    # print(acceptableChars)
    newCols = []
    for col in cols:
        newCol = ""
        col = col.replace(" ", "_")
        for c in col:
            if c.lower() in acceptableChars:
                newCol += c
        newCols.append(newCol.upper())
    return newCols
