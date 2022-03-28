
import argparse
import numpy as np
from hyperopt import hp
import torch

def parameters(path, debug):

    # args=DefaultParameters(path)
    args={}
    args['path'] = path

    # Use optimized parameters depending on the experiment.
    if 'STK11' in path:            
        
        # Patch contrastive learning parameters
        args['PCL_CNN_Architecture']='resnet50' # or resnet18
        args['PCL_N_Workers']=2 # Number of data loading workers 
        args['PCL_Epochs']=80 # Number of total epoch to run
        args['PCL_N_Crops_per_Image']=110 # Number of crops chosen per image
        args['PCL_Patch_Size']=30 # Size of patches in pixels
        args['PCL_Stride']=0 # Size of stride between consecutive patches
        args['PCL_Alpha_L']=1.15 # size ratio between image crop and image patch
        args['PCL_Z_Score']= True # Whether to apply z score per channel/marker
        args['PCL_Batch_Size']= 4 # Number of images per iteration
        args['PCL_Weight_Decay']= 1e-4 # Weight Decay
        args['PCL_Out_Dimensions']= 128 # Feature dimensions of patch
        args['PCL_Learning_Rate']= 0.003 # Learning Rate
        args['PCL_Temperature']= 0.07 # Softmax temperature                
        args['PCL_eliminate_Black_Background'] = True
        args['PCL_eliminate_White_Background'] = False
        args['PCL_GPU_INDEX']= torch.device('cuda:0') # GPU where the training is carried out 
        args['PCL_Color_perturbation_Augmentation'] = False # Color augmentation for H&E tissue staining.


        # Label you want to infer with respect the images.
        args['experiment_Label'] = ['Mutation'] 

        # Architecture Search parameters
        args['num_samples_architecture_search'] = 800  

        # Optimization Parameters
        args['NaroNet_n_workers'] = 1
        args['epochs'] = 3 if debug=='Index' else hp.choice('epochs',[6,15,30,100]) if debug=='Object' else 100
        args['lr_decay_factor'] = 0.25# if debug else hp.uniform('lr_decay_factor', 0, 0.75)
        args['lr_decay_step_size'] = 11000#max(int(args['epochs']/2),1)# if debug else hp.quniform('lr_decay_step_size', 2, 20, 1)        
        args['weight_decay'] = 4 if debug=='Index' else hp.choice('weight_decay',[0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0
        args['batch_size'] = 2 if debug=='Index' else hp.choice('batch_size', [2, 4, 8, 14, 24]) if debug=='Object' else 8
        args['lr'] = 0 if debug=='Index' else hp.choice('lr', [1,0.1,0.01,0.001,0.0001]) if debug=='Object' else 1

        # General
        args['training_MODE'] = 'TrainALL' # TrainALL, NestedCrossValidation, CrossValidation # Whether to use nested cross validation or cross validation.        
        args['folds'] = 1
        args['device'] = 'cuda:0'
        args['Batch_Normalization'] = True
        args['dataAugmentationPerc'] = 0 #0 if debug=='Index' else hp.choice("dataAugmentationPerc", [0,0.0001,0.001]) if debug=='Object' else 0  

        # Neural Network
        args['N_Phenotypes'] = 0 if debug=='Index' else hp.choice('clusters1',[8,10,15,20]) if debug=='Object' else 8     
        args['N_Neighborhoods'] = 2 if debug=='Index' else hp.choice('clusters2',[6,11,16,21]) if debug=='Object' else 16
        args['N_Areas'] = 1 if debug=='Index' else hp.choice('clusters3',[2,4,7]) if debug=='Object' else 4      
        args['Phenotype_Learning'] = True  
        args['Neighborhood_Learning'] = True
        args['Area_Learning'] = True
        args['dropoutRate'] = 0 if debug=='Index' else hp.choice('dropoutRate', [0, 0.25]) if debug=='Object' else 0
        args['attntnThreshold'] = 0 if debug=='Index' else hp.choice('attntnThreshold', [0,.1,.2]) if debug=='Object' else 0 
        args['1Patch1Cluster'] = False# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  
        
        # Losses
        args['ContrastACC_Pheno'] = 1# if debug=='Index' else hp.choice("ContrastACC_Pheno", [1,0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0.01
        args['ContrastACC_Neigh'] = 1# if debug=='Index' else hp.choice("ContrastACC_Neigh", [1, 0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 1
        args['ContrastACC_Area'] = 1#4 if debug=='Index' else hp.choice("ContrastACC_Area", [1, 0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0.0001
        args['PatchEntropy_Pheno'] = 0#1 if debug=='Index' else hp.choice("PatchEntropy_Pheno", [1,0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0.1   
        args['PatchEntropy_Neigh'] = 0#1 if debug=='Index' else hp.choice("PatchEntropy_Neigh", [1,0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0.1
        args['PatchEntropy_Area'] = 0#4 if debug=='Index' else hp.choice("PatchEntropy_Area", [1,0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0.0001                                             

        # Bioinsights parameters
        args['Bio_save_Orig_im'] = False
        args['TSNE_Perc_Pat'] = 0.5 # Percentage of patients to use to generate the tsne. 


    elif 'Melanoma_ProgressionvsBaseline' in path:            
        # Patch contrastive learning parameters
        args['PCL_CNN_Architecture']='resnet50' # or resnet18
        args['PCL_N_Workers']=0 # Number of data loading workers 
        args['PCL_Epochs']=60 # Number of total epoch to run
        args['PCL_N_Crops_per_Image']=70 # Number of crops chosen per image
        args['PCL_Patch_Size']=50 # Size of patches in pixels
        args['PCL_Stride']=0 # Size of stride between consecutive patches
        args['PCL_Alpha_L']=1.15 # size ratio between image crop and image patch
        args['PCL_Z_Score']= True # Whether to apply z score per channel/marker 
        args['PCL_Batch_Size']= 5 # Number of images per iteration
        args['PCL_Weight_Decay']= 1e-4 # Weight Decay
        args['PCL_Out_Dimensions']= 128 # Feature dimensions of patch
        args['PCL_Learning_Rate']= 0.0003 # Learning Rate
        args['PCL_Temperature']= 0.07 # Softmax temperature                
        args['PCL_eliminate_Black_Background'] = False
        args['PCL_eliminate_White_Background'] = True   
        args['PCL_GPU_INDEX']= torch.device('cuda:0') # GPU where the training is carried out 
        args['PCL_Color_perturbation_Augmentation'] = True # Color augmentation for H&E tissue staining.

        # Label you want to infer with respect the images.
        args['experiment_Label'] = ['Sample_type'] 

        # Architecture Search parameters
        args['num_samples_architecture_search'] = 700  

        # Optimization Parameters
        args['epochs'] = 80# if debug else hp.quniform('epochs', 5, 25, 1)
        args['lr_decay_factor'] = 0.1# if debug else hp.uniform('lr_decay_factor', 0, 0.75)
        args['lr_decay_step_size'] = 10000#max(int(args['epochs']/3),1)# if debug else hp.quniform('lr_decay_step_size', 2, 20, 1)        
        args['weight_decay'] = 0#3 if debug=='Index' else hp.choice('weight_decay',[0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0.0001
        args['batch_size'] = 4 if debug=='Index' else hp.choice('batch_size', [2, 4, 8, 16, 28]) if debug=='Object' else 28
        args['lr'] = 1 if debug=='Index' else hp.choice('lr', [1,0.5,0.01,0.001,0.0001]) if debug=='Object' else 0.5

        # General        
        args['training_MODE'] = 'TrainALL' # TrainALL, NestedCrossValidation, CrossValidation # Whether to use nested cross validation or cross validation.            
        args['folds'] = 1
        args['device'] = 'cuda:0'
        args['Batch_Normalization'] = True
        args['dataAugmentationPerc'] = 0 #0 if debug=='Index' else hp.choice("dataAugmentationPerc", [0,0.0001,0.001]) if debug=='Object' else 0  

        # Neural Network
        args['N_Phenotypes'] = 1 if debug=='Index' else hp.choice('clusters1',[5,8,15,20]) if debug=='Object' else 8     
        args['N_Neighborhoods'] = 2 if debug=='Index' else hp.choice('clusters2',[6,11,16,21]) if debug=='Object' else 16 
        args['N_Areas'] = 1 if debug=='Index' else hp.choice('clusters3',[2,4,7]) if debug=='Object' else 4      
        args['Phenotype_Learning'] = True  
        args['Neighborhood_Learning'] = True  
        args['Area_Learning'] = True
        args['dropoutRate'] = 0# 1 if debug=='Index' else hp.choice('dropoutRate', [0.1, 0.2, 0.3,0.4]) if debug=='Object' else 0.2        
        args['attntnThreshold'] = 0# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  
        args['1Patch1Cluster'] = True# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  

        # Losses 
        args['ContrastACC_Pheno'] = 1#.001#4 if debug=='Index' else hp.choice("orthoColor_Lambda0", [1,0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                
        args['ContrastACC_Neigh'] = 1#.001#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['ContrastACC_Area'] = 1#.0001#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['PatchEntropy_Pheno'] = 0#.01#3 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda0", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.001   
        args['PatchEntropy_Neigh'] = 0#.01#4 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda1", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0
        args['PatchEntropy_Area'] = 0#.0001#1 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda2", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.1                                  

        # Bioinsights parameters
        args['Bio_save_Orig_im'] = False

    elif 'LF_Recurrence' in path:            
        # Patch contrastive learning parameters
        args['PCL_CNN_Architecture']='resnet50' # or resnet18
        args['PCL_N_Workers']=8 # Number of data loading workers 
        args['PCL_Epochs']=400 # Number of total epoch to run
        args['PCL_N_Crops_per_Image']=70 # Number of crops chosen per image
        args['PCL_Patch_Size']=30 # Size of patches in pixels
        args['PCL_Stride']=0 # Size of stride between consecutive patches
        args['PCL_Alpha_L']=1.1 # size ratio between image crop and image patch
        args['PCL_Z_Score']= True # Whether to apply z score per channel/marker 
        args['PCL_Batch_Size']= 8 # Number of images per iteration
        args['PCL_Weight_Decay']= 1e-4 # Weight Decay
        args['PCL_Out_Dimensions']= 128 # Feature dimensions of patch
        args['PCL_Learning_Rate']= 0.0003 # Learning Rate
        args['PCL_Temperature']= 0.07 # Softmax temperature    
        args['PCL_eliminate_Black_Background'] = True
        args['PCL_eliminate_White_Background'] = False
        args['PCL_GPU_INDEX']= torch.device('cuda:0') # GPU where the training is carried out 
        args['PCL_Color_perturbation_Augmentation'] = False # Color augmentation for H&E tissue staining.

        # Label you want to infer with respect the images.
        args['experiment_Label'] = ['Relapse'] 

        # Architecture Search parameters
        args['num_samples_architecture_search'] = 700  

        # Optimization Parameters
        args['NaroNet_n_workers'] = 1
        args['epochs'] = 200# if debug else hp.quniform('epochs', 5, 25, 1)
        args['lr_decay_factor'] = 0.1# if debug else hp.uniform('lr_decay_factor', 0, 0.75)
        args['lr_decay_step_size'] = 309#max(int(args['epochs']/3),1)# if debug else hp.quniform('lr_decay_step_size', 2, 20, 1)        
        args['weight_decay'] = 0#3 if debug=='Index' else hp.choice('weight_decay',[0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0.0001
        args['batch_size'] = 4 if debug=='Index' else hp.choice('batch_size', [2, 4, 8, 12, 28]) if debug=='Object' else 28
        args['lr'] = 1 if debug=='Index' else hp.choice('lr', [1,0.1,0.01,0.001,0.0001]) if debug=='Object' else 0.1

        # General        
        args['training_MODE'] = 'TrainALL' # TrainALL, NestedCrossValidation, CrossValidation # Whether to use nested cross validation or cross validation.            
        args['folds'] = 1
        args['device'] = 'cuda:0'
        args['Batch_Normalization'] = True
        args['dataAugmentationPerc'] = 0 #0 if debug=='Index' else hp.choice("dataAugmentationPerc", [0,0.0001,0.001]) if debug=='Object' else 0  

        # Neural Network
        args['N_Phenotypes'] = 1 if debug=='Index' else hp.choice('clusters1',[5,8,15,20]) if debug=='Object' else 8     
        args['N_Neighborhoods'] = 2 if debug=='Index' else hp.choice('clusters2',[6,11,16,21]) if debug=='Object' else 16 
        args['N_Areas'] = 1 if debug=='Index' else hp.choice('clusters3',[2,4,7]) if debug=='Object' else 4      
        args['Phenotype_Learning'] = True  
        args['Neighborhood_Learning'] = False  
        args['Area_Learning'] = False
        args['dropoutRate'] = 0# 1 if debug=='Index' else hp.choice('dropoutRate', [0.1, 0.2, 0.3,0.4]) if debug=='Object' else 0.2        
        args['attntnThreshold'] = 0# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  
        args['1Patch1Cluster'] = False# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  

        # Losses 
        args['ContrastACC_Pheno'] = 1000#.001#4 if debug=='Index' else hp.choice("orthoColor_Lambda0", [1,0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                
        args['ContrastACC_Neigh'] = 0#.001#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['ContrastACC_Area'] = 0#.0001#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['PatchEntropy_Pheno'] = 0#.01#3 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda0", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.001   
        args['PatchEntropy_Neigh'] = 0#.01#4 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda1", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0
        args['PatchEntropy_Area'] = 0#.0001#1 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda2", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.1                                  

        # Bioinsights parameters
        args['Bio_save_Orig_im'] = False
        args['TSNE_Perc_Pat'] = 0.5 # Percentage of patients to use to generate the tsne. 


    elif 'LF_19H' in path:            
        # Patch contrastive learning parameters
        args['PCL_CNN_Architecture']='resnet50' # or resnet18
        args['PCL_N_Workers']=0 # Number of data loading workers 
        args['PCL_Epochs']=400 # Number of total epoch to run
        args['PCL_N_Crops_per_Image']=200 # Number of crops chosen per image
        args['PCL_Patch_Size']=30 # Size of patches in pixels
        args['PCL_Stride']=0 # Size of stride between consecutive patches
        args['PCL_Alpha_L']=1.15 # size ratio between image crop and image patch
        args['PCL_Z_Score']= True # Whether to apply z score per channel/marker 
        args['PCL_Batch_Size']= 6 # Number of images per iteration
        args['PCL_Weight_Decay']= 1e-4 # Weight Decay
        args['PCL_Out_Dimensions']= 128 # Feature dimensions of patch
        args['PCL_Learning_Rate']= 0.0003 # Learning Rate
        args['PCL_Temperature']= 0.07 # Softmax temperature         
        args['PCL_eliminate_Black_Background'] = True
        args['PCL_eliminate_White_Background'] = False       
        args['PCL_GPU_INDEX']= torch.device('cuda:0') # GPU where the training is carried out 
        args['PCL_Color_perturbation_Augmentation'] = False # Color augmentation for H&E tissue staining.

        # Label you want to infer with respect the images.
        args['experiment_Label'] = ['Relapse'] 

        # Architecture Search parameters
        args['num_samples_architecture_search'] = 700  

        # Optimization Parameters
        args['epochs'] = 8# if debug else hp.quniform('epochs', 5, 25, 1)
        args['lr_decay_factor'] = 0.1# if debug else hp.uniform('lr_decay_factor', 0, 0.75)
        args['lr_decay_step_size'] = 10000#max(int(args['epochs']/3),1)# if debug else hp.quniform('lr_decay_step_size', 2, 20, 1)        
        args['weight_decay'] = 0#3 if debug=='Index' else hp.choice('weight_decay',[0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0.0001
        args['batch_size'] = 26# if debug=='Index' else hp.choice('batch_size', [2, 4, 8, 16, 22]) if debug=='Object' else 22
        args['lr'] = 0.1#0 if debug=='Index' else hp.choice('lr', [1,0.1,0.01]) if debug=='Object' else 1

        # General        
        args['training_MODE'] = 'TrainALL' # TrainALL, NestedCrossValidation, CrossValidation # Whether to use nested cross validation or cross validation.            
        args['folds'] = 1
        args['device'] = 'cuda:0'
        args['Batch_Normalization'] = True
        args['dataAugmentationPerc'] = 0 #0 if debug=='Index' else hp.choice("dataAugmentationPerc", [0,0.0001,0.001]) if debug=='Object' else 0  

        # Neural Network
        args['N_Phenotypes'] = 1 if debug=='Index' else hp.choice('clusters1',[5,8,15,20]) if debug=='Object' else 8     
        args['N_Neighborhoods'] = 2 if debug=='Index' else hp.choice('clusters2',[6,11,16,21]) if debug=='Object' else 16 
        args['N_Areas'] = 1 if debug=='Index' else hp.choice('clusters3',[2,4,7]) if debug=='Object' else 4      
        args['Phenotype_Learning'] = True  
        args['Neighborhood_Learning'] = True  
        args['Area_Learning'] = True
        args['dropoutRate'] = 0# 1 if debug=='Index' else hp.choice('dropoutRate', [0.1, 0.2, 0.3,0.4]) if debug=='Object' else 0.2        
        args['attntnThreshold'] = 0# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  
        args['1Patch1Cluster'] = False# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  


        # Losses
        args['ContrastACC_Pheno'] = 1#.001#4 if debug=='Index' else hp.choice("orthoColor_Lambda0", [1,0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                
        args['ContrastACC_Neigh'] = 1#.001#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['ContrastACC_Area'] = 1#.0001#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['PatchEntropy_Pheno'] = 0#.01#3 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda0", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.001   
        args['PatchEntropy_Neigh'] = 0#.01#4 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda1", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0
        args['PatchEntropy_Area'] = 0#.0001#1 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda2", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.1                                  

        # Bioinsights parameters
        args['Bio_save_Orig_im'] = False

    elif 'Urothelial_ClinBen' in path:            
        
        # Patch contrastive learning parameters
        args['PCL_CNN_Architecture']='resnet50' # or resnet18
        args['PCL_N_Workers']=8 # Number of data loading workers 
        args['PCL_Epochs']=80 # Number of total epoch to run
        args['PCL_N_Crops_per_Image']=40 # Number of crops chosen per image
        args['PCL_Patch_Size']=30 # Size of patches in pixels
        args['PCL_Stride']=0 # Size of stride between consecutive patches
        args['PCL_Alpha_L']=1.15 # size ratio between image crop and image patch
        args['PCL_Z_Score']= True # Whether to apply z score per channel/marker
        args['PCL_Batch_Size']= 8 # Number of images per iteration
        args['PCL_Weight_Decay']= 1e-4 # Weight Decay
        args['PCL_Out_Dimensions']= 128 # Feature dimensions of patch
        args['PCL_Learning_Rate']= 0.003 # Learning Rate
        args['PCL_Temperature']= 0.07 # Softmax temperature    
        args['PCL_eliminate_Black_Background'] = False
        args['PCL_eliminate_White_Background'] = False            
        args['PCL_GPU_INDEX']= torch.device('cuda:0') # GPU where the training is carried out 

        # Label you want to infer with respect the images.
        args['experiment_Label'] = ['Clinical_Benefit'] 

        # Architecture Search parameters
        args['num_samples_architecture_search'] = 1500  

        # Optimization Parameters
        args['NaroNet_n_workers'] = 1
        args['epochs'] = 1000# if debug else hp.quniform('epochs', 5, 25, 1)
        args['lr_decay_factor'] = 0.1# if debug else hp.uniform('lr_decay_factor', 0, 0.75)
        args['lr_decay_step_size'] = 10000#max(int(args['epochs']/5),1)# if debug else hp.quniform('lr_decay_step_size', 2, 20, 1)        
        args['weight_decay'] = 4 if debug=='Index' else hp.choice('weight_decay',[0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0
        args['batch_size'] = 3 if debug=='Index' else hp.choice('batch_size', [2, 4, 8, 24]) if debug=='Object' else 24
        args['lr'] = 1 if debug=='Index' else hp.choice('lr', [1,0.1,0.01,0.001,0.0001]) if debug=='Object' else 0.1

        # General
        args['training_MODE'] = 'TrainALL' # TrainALL, NestedCrossValidation, CrossValidation # Whether to use nested cross validation or cross validation.        
        args['folds'] = 1
        args['device'] = 'cuda:0'
        args['Batch_Normalization'] = True
        args['dataAugmentationPerc'] = 0 #0 if debug=='Index' else hp.choice("dataAugmentationPerc", [0,0.0001,0.001]) if debug=='Object' else 0  

        # Neural Network
        args['N_Phenotypes'] = 8#2 if debug=='Index' else hp.choice('clusters1',[5,10,15,20]) if debug=='Object' else 15     
        args['N_Neighborhoods'] = 10#1 if debug=='Index' else hp.choice('clusters2',[6,11,16,21]) if debug=='Object' else 11 
        args['N_Areas'] = 4#0 if debug=='Index' else hp.choice('clusters3',[2,4,7]) if debug=='Object' else 2      
        args['Phenotype_Learning'] = True  
        args['Neighborhood_Learning'] = True
        args['Area_Learning'] = True
        args['dropoutRate'] = 0# 1 if debug=='Index' else hp.choice('dropoutRate', [0.1, 0.2, 0.3,0.4]) if debug=='Object' else 0.2        
        args['attntnThreshold'] = 0# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  
        args['1Patch1Cluster'] = False# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  
                
        # Losses
        args['ContrastACC_Pheno'] = 10#4 if debug=='Index' else hp.choice("orthoColor_Lambda0", [1,0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                
        args['ContrastACC_Neigh'] = 10#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['ContrastACC_Area'] = 0#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['PatchEntropy_Pheno'] = 0#3 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda0", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.001   
        args['PatchEntropy_Neigh'] = 0#4 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda1", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0
        args['PatchEntropy_Area'] = 0#1 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda2", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.1          
        
        # Bioinsights parameters
        args['Bio_save_Orig_im'] = True

    elif 'Tumor_subtype' in path:            
        
        # Patch contrastive learning parameters
        args['PCL_CNN_Architecture']='resnet50' # or resnet18
        args['PCL_N_Workers']=8 # Number of data loading workers 
        args['PCL_Epochs']=80 # Number of total epoch to run
        args['PCL_N_Crops_per_Image']=40 # Number of crops chosen per image
        args['PCL_Patch_Size']=30 # Size of patches in pixels
        args['PCL_Stride']=0 # Size of stride between consecutive patches
        args['PCL_Alpha_L']=1.15 # size ratio between image crop and image patch
        args['PCL_Z_Score']= True # Whether to apply z score per channel/marker
        args['PCL_Batch_Size']= 8 # Number of images per iteration
        args['PCL_Weight_Decay']= 1e-4 # Weight Decay
        args['PCL_Out_Dimensions']= 128 # Feature dimensions of patch
        args['PCL_Learning_Rate']= 0.003 # Learning Rate
        args['PCL_Temperature']= 0.07 # Softmax temperature                
        args['PCL_eliminate_Black_Background'] = False
        args['PCL_eliminate_White_Background'] = False
        args['PCL_GPU_INDEX']= torch.device('cuda:0') # GPU where the training is carried out 

        # Label you want to infer with respect the images.
        args['experiment_Label'] = ['Clinical_Benefit'] 

        # Architecture Search parameters
        args['num_samples_architecture_search'] = 1500  

        # Optimization Parameters
        args['epochs'] = 500
        args['lr_decay_factor'] = 0.1
        args['lr_decay_step_size'] = 10000
        args['weight_decay'] = 0
        args['batch_size'] = 24
        args['lr'] = 1 

        # General
        args['training_MODE'] = 'TrainALL' # TrainALL, NestedCrossValidation, CrossValidation # Whether to use nested cross validation or cross validation.        
        args['folds'] = 1
        args['device'] = 'cuda:0'
        args['Batch_Normalization'] = True
        args['dataAugmentationPerc'] = 0 #0 if debug=='Index' else hp.choice("dataAugmentationPerc", [0,0.0001,0.001]) if debug=='Object' else 0  

        # Neural Network
        args['N_Phenotypes'] = 8#2 if debug=='Index' else hp.choice('clusters1',[5,10,15,20]) if debug=='Object' else 15     
        args['N_Neighborhoods'] = 16#1 if debug=='Index' else hp.choice('clusters2',[6,11,16,21]) if debug=='Object' else 11 
        args['N_Areas'] = 4#0 if debug=='Index' else hp.choice('clusters3',[2,4,7]) if debug=='Object' else 2      
        args['Phenotype_Learning'] = True  
        args['Neighborhood_Learning'] = True
        args['Area_Learning'] = True
        args['dropoutRate'] = 0# 1 if debug=='Index' else hp.choice('dropoutRate', [0.1, 0.2, 0.3,0.4]) if debug=='Object' else 0.2        
        args['attntnThreshold'] = 0# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  
                
        # Losses
        args['ContrastACC_Pheno'] = 0#4 if debug=='Index' else hp.choice("orthoColor_Lambda0", [1,0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                
        args['ContrastACC_Neigh'] = 0#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['ContrastACC_Area'] = 0#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['PatchEntropy_Pheno'] = 0#3 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda0", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.001   
        args['PatchEntropy_Neigh'] = 0#4 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda1", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0
        args['PatchEntropy_Area'] = 0#1 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda2", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.1          
        
        # Bioinsights parameters
        args['Bio_save_Orig_im'] = False

    else:
        
        # Patch contrastive learning parameters
        args['PCL_CNN_Architecture']='resnet50' # or resnet18
        args['PCL_N_Workers']=8 # Number of data loading workers 
        args['PCL_Epochs']=80 # Number of total epoch to run
        args['PCL_N_Crops_per_Image']=40 # Number of crops chosen per image
        args['PCL_Patch_Size']=30 # Size of patches in pixels
        args['PCL_Stride']=0 # Size of stride between consecutive patches
        args['PCL_Alpha_L']=1.15 # size ratio between image crop and image patch
        args['PCL_Z_Score']= True # Whether to apply z score per channel/marker
        args['PCL_Batch_Size']= 1 # Number of images per iteration
        args['PCL_Weight_Decay']= 1e-4 # Weight Decay
        args['PCL_Out_Dimensions']= 128 # Feature dimensions of patch
        args['PCL_Learning_Rate']= 0.003 # Learning Rate
        args['PCL_Temperature']= 0.07 # Softmax temperature    
        args['PCL_eliminate_Black_Background'] = False
        args['PCL_eliminate_White_Background'] = False            
        args['PCL_GPU_INDEX']= torch.device('cuda:0') # GPU where the training is carried out 

        # Label you want to infer with respect the images.
        args['experiment_Label'] = ['Clinical_Benefit'] 

        # Architecture Search parameters
        args['num_samples_architecture_search'] = 1500  

        # Optimization Parameters
        args['epochs'] = 1000# if debug else hp.quniform('epochs', 5, 25, 1)
        args['lr_decay_factor'] = 0.1# if debug else hp.uniform('lr_decay_factor', 0, 0.75)
        args['lr_decay_step_size'] = 10000#max(int(args['epochs']/5),1)# if debug else hp.quniform('lr_decay_step_size', 2, 20, 1)        
        args['weight_decay'] = 4 if debug=='Index' else hp.choice('weight_decay',[0.1,0.01,0.001,0.0001,0]) if debug=='Object' else 0
        args['batch_size'] = 3 if debug=='Index' else hp.choice('batch_size', [2, 4, 8, 24]) if debug=='Object' else 24
        args['lr'] = 0 if debug=='Index' else hp.choice('lr', [1,0.1,0.01,0.001,0.0001]) if debug=='Object' else 1

        # General
        args['training_MODE'] = 'TrainALL' # TrainALL, NestedCrossValidation, CrossValidation # Whether to use nested cross validation or cross validation.        
        args['folds'] = 1
        args['device'] = 'cuda:0'
        args['Batch_Normalization'] = True
        args['dataAugmentationPerc'] = 0 #0 if debug=='Index' else hp.choice("dataAugmentationPerc", [0,0.0001,0.001]) if debug=='Object' else 0  

        # Neural Network
        args['N_Phenotypes'] = 8#2 if debug=='Index' else hp.choice('clusters1',[5,10,15,20]) if debug=='Object' else 15     
        args['N_Neighborhoods'] = 16#1 if debug=='Index' else hp.choice('clusters2',[6,11,16,21]) if debug=='Object' else 11 
        args['N_Areas'] = 4#0 if debug=='Index' else hp.choice('clusters3',[2,4,7]) if debug=='Object' else 2      
        args['Phenotype_Learning'] = True  
        args['Neighborhood_Learning'] = True
        args['Area_Learning'] = True
        args['dropoutRate'] = 0# 1 if debug=='Index' else hp.choice('dropoutRate', [0.1, 0.2, 0.3,0.4]) if debug=='Object' else 0.2        
        args['attntnThreshold'] = 0# if debug=='Index' else hp.choice('attntnThreshold', [0,.2,.4,.6,.8]) if debug=='Object' else 0  
                
        # Losses
        args['ContrastACC_Pheno'] = 0.01#4 if debug=='Index' else hp.choice("orthoColor_Lambda0", [1,0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                
        args['ContrastACC_Neigh'] = 0.01#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['ContrastACC_Area'] = 0.0001#4 if debug=='Index' else hp.choice("orthoColor_Lambda1", [1, 0.1,0.01,0.001,0.0001,0.00001]) if debug=='Object' else 0.0001                                              
        args['PatchEntropy_Pheno'] = 0.01#3 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda0", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.001   
        args['PatchEntropy_Neigh'] = 0.01#4 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda1", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0
        args['PatchEntropy_Area'] = 0.0001#1 if debug=='Index' else hp.choice("min_Cell_entropy_Lambda2", [1,0.1,0.01,0.001,0]) if debug=='Object' else 0.1          
        
        # Bioinsights parameters
        args['Bio_save_Orig_im'] = True


    return args