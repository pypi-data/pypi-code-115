#Importing the headers for processing the dataframes.
import numpy as np
import pandas as pd

#Importing the headers to create the folders.
import os

#_____________________________________________

#Feeds Data to the FolderSplitter functio based on maximum uniques.n.
def using_maxUniques(filepath, max_uniques, output_folderpath):
    '''Returns a Folder Structure of the tables
    in the csv.
    *filepath -> Your csv file.
    *max_uniques -> Max uniques allowed.
    *output_folderpath -> Folder within which sub folders
    will be formed.
    '''
  
    #It's uhmm, the parent_folder within which the sub folders will be formed.
    parent_folder = output_folderpath
    
    #Importing the csv as a df.
    data_csv = pd.read_csv(filepath)
    
    #IF condition to check the folder's existence.
    if not os.path.exists(parent_folder):
                
        #Create the folder.
        os.makedirs(parent_folder)
        
    
    #Total count of rows.
    rows_total = len(data_csv)
    
    #Total count of columns.
    cols_total = data_csv.shape[1]
    
    #Current column.
    col_current = 0
    
    #Passing the data into FolderSplitter.
    FolderSplitter2(data_csv, max_uniques, col_current, cols_total, parent_folder)

#_____________________________________________

#The recursive code to split folders.
def FolderSplitter2(data_csv, max_uniques, col_current, cols_total, parent_folder):
    
    #Is the current column within the total columns limit?
    if col_current < cols_total:

        #Unique values in the current column.
        current_uniqueValues = pd.unique(data_csv.iloc[:, col_current])
        
        #Count of unique values in current column.
        col_uniqueCount = len(current_uniqueValues)
        
        #current column name.
        current_colname = data_csv.columns[col_current]
            
        #Check if current column is within the limits of max_uniques.
        if col_uniqueCount < (max_uniques + 1):           
            
            #Directory_maker(folder_path) 
            #parent_folder = parent_folder + '\\' +  str(current_colname)
            
            #IF condition to check the folder's existence.
            if not os.path.exists(parent_folder):
                #Create the folder.
                os.makedirs(parent_folder)
                
            
            #Writing data to the csv.
            data_csv.to_csv(parent_folder + '\Output_' + str(current_colname) + '.csv', index = False)
            
            
            #For condition to cycle through the unique values.
            for value in current_uniqueValues:

                #Creating the folder path.
                #folder_path = os.path.join(parent_folder, data_csv.columns[col_current])
                #folder_path = os.path.join(parent_folder, str(value))
                folder_path = parent_folder + '\\' + str(value)                 

            
                #Temporary sub dataframe.
                data_temp = data_csv[data_csv[current_colname] == value]
                
                #Writing the csv to the created folder_path.
                ##data_temp.to_csv(folder_path + '\Output_' + str(value) + '.csv', index = False)
                
                
                if col_current == (cols_total - 1):
                
                    #IF condition to check the folder's existence.
                    if not os.path.exists(folder_path):
                        
                        #Create the folder.
                        os.makedirs(folder_path)
                        
                    data_temp.to_csv(folder_path + '\Output_' + str(value) + '.csv', index = False)         
                
                
                #Sweet Sweet Recursion baby!
                FolderSplitter2(data_temp, max_uniques, (col_current + 1), cols_total, folder_path)
            
            
        else:

            #When the uniques are out of hand/ beyond the maximum specified, this recursive code is called in.
            #So basically, more recursion baby!
            FolderSplitter2(data_csv, max_uniques, (col_current + 1), cols_total, parent_folder)
        
    #The main else condition.
    else:

        #I dont even know if this is necessary, oh well, gotta return something :-P .
        return 0
    
    
#_____________________________________________


