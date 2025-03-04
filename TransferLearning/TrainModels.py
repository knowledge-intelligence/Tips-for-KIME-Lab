#!/usr/bin/env python3

# from __future__ import print_function 
# from __future__ import division
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt
import time
import os
import copy
import argparse


"""
Function:   train_model

[Ref - Source Code]
https://pytorch.org/tutorials/beginner/finetuning_torchvision_models_tutorial.html
[Ref - Additioanl]
https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html
"""
def train_model(model, dataloaders, criterion, optimizer, device, train_name, val_name, num_epochs=25, is_inception=False):
    since = time.time()

    val_acc_history = []
    
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        # Each epoch has a training and validation phase
        for phase in [train_name, val_name]:
            if phase == train_name:
                model.train()  # Set model to training mode
            else:
                model.eval()   # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == train_name):
                    # Get model outputs and calculate loss
                    # Special case for inception because in training it has an auxiliary output. In train
                    #   mode we calculate the loss by summing the final output and the auxiliary output
                    #   but in testing we only consider the final output.
                    if is_inception and phase == train_name:
                        # From https://discuss.pytorch.org/t/how-to-optimize-inception-model-with-auxiliary-classifiers/7958
                        outputs, aux_outputs = model(inputs)
                        loss1 = criterion(outputs, labels)
                        loss2 = criterion(aux_outputs, labels)
                        loss = loss1 + 0.4*loss2
                    else:
                        outputs = model(inputs)
                        loss = criterion(outputs, labels)

                    _, preds = torch.max(outputs, 1)

                    # backward + optimize only if in training phase
                    if phase == train_name:
                        loss.backward()
                        optimizer.step()

                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(dataloaders[phase].dataset)
            epoch_acc = running_corrects.double() / len(dataloaders[phase].dataset)

            print('{} Loss: {:.4f} Acc: {:.4f}'.format(phase, epoch_loss, epoch_acc))

            # deep copy the model
            if phase == val_name and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())
            if phase == val_name:
                val_acc_history.append(epoch_acc)

        print()

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
    print('Best val Acc: {:4f}'.format(best_acc))

    # load best model weights
    model.load_state_dict(best_model_wts)
    return model, val_acc_history

"""
Function:   set_parameter_requires_grad
"""
def set_parameter_requires_grad(model, feature_extracting):
    if feature_extracting:
        for param in model.parameters():
            param.requires_grad = False

"""
Function:   initialize_model

Ref:        https://pytorch.org/tutorials/beginner/finetuning_torchvision_models_tutorial.html
"""
def initialize_model(model_name, num_classes, feature_extract, use_pretrained=True):
    # Initialize these variables which will be set in this if statement. Each of these
    #   variables is model specific.
    model_ft = None
    input_size = 0

    if model_name == "resnet":
        """ Resnet18
        """
        model_ft = models.resnet18(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        num_ftrs = model_ft.fc.in_features
        model_ft.fc = nn.Linear(num_ftrs, num_classes)
        input_size = 224

    elif model_name == "alexnet":
        """ Alexnet
        """
        model_ft = models.alexnet(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        num_ftrs = model_ft.classifier[6].in_features
        model_ft.classifier[6] = nn.Linear(num_ftrs,num_classes)
        input_size = 224

    elif model_name == "vgg":
        """ VGG11_bn
        """
        model_ft = models.vgg11_bn(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        num_ftrs = model_ft.classifier[6].in_features
        model_ft.classifier[6] = nn.Linear(num_ftrs,num_classes)
        input_size = 224

    elif model_name == "squeezenet":
        """ Squeezenet
        """
        model_ft = models.squeezenet1_0(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        model_ft.classifier[1] = nn.Conv2d(512, num_classes, kernel_size=(1,1), stride=(1,1))
        model_ft.num_classes = num_classes
        input_size = 224

    elif model_name == "densenet":
        """ Densenet
        """
        model_ft = models.densenet121(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        num_ftrs = model_ft.classifier.in_features
        model_ft.classifier = nn.Linear(num_ftrs, num_classes) 
        input_size = 224

    elif model_name == "inception":
        """ Inception v3 
        Be careful, expects (299,299) sized images and has auxiliary output
        """
        model_ft = models.inception_v3(pretrained=use_pretrained)
        set_parameter_requires_grad(model_ft, feature_extract)
        # Handle the auxilary net
        num_ftrs = model_ft.AuxLogits.fc.in_features
        model_ft.AuxLogits.fc = nn.Linear(num_ftrs, num_classes)
        # Handle the primary net
        num_ftrs = model_ft.fc.in_features
        model_ft.fc = nn.Linear(num_ftrs,num_classes)
        input_size = 299

    else:
        print("Invalid model name, exiting...")
        exit()
    
    return model_ft, input_size












# """
# Function:   test_model
# """
# def test_model(model, dataloaders, criterion, optimizer, device, test_name, num_epochs=25, is_inception=False):
#     since = time.time()

#     val_acc_history = []
    
#     best_model_wts = copy.deepcopy(model.state_dict())
#     best_acc = 0.0

#     for epoch in range(num_epochs):
#         print('Epoch {}/{}'.format(epoch, num_epochs - 1))
#         print('-' * 10)

#         # Each epoch has a training and validation phase
#             phase = test_name
#             model.eval()   # Set model to evaluate mode

#             running_loss = 0.0
#             running_corrects = 0

#             # Iterate over data.
#             for inputs, labels in dataloaders[phase]:
#                 inputs = inputs.to(device)
#                 labels = labels.to(device)

#                 # zero the parameter gradients
#                 optimizer.zero_grad()

#                 # forward
#                 # track history if only in train
#                 with torch.set_grad_enabled(phase == 'train'):
#                     # Get model outputs and calculate loss
#                     # Special case for inception because in training it has an auxiliary output. In train
#                     #   mode we calculate the loss by summing the final output and the auxiliary output
#                     #   but in testing we only consider the final output.

#                     outputs = model(inputs)
#                     loss = criterion(outputs, labels)

#                     _, preds = torch.max(outputs, 1)


#                 # statistics
#                 running_loss += loss.item() * inputs.size(0)
#                 running_corrects += torch.sum(preds == labels.data)

#             epoch_loss = running_loss / len(dataloaders[phase].dataset)
#             epoch_acc = running_corrects.double() / len(dataloaders[phase].dataset)

#             print('{} Loss: {:.4f} Acc: {:.4f}'.format(phase, epoch_loss, epoch_acc))

#             # deep copy the model
#             if phase == 'val' and epoch_acc > best_acc:
#                 best_acc = epoch_acc
#             if phase == 'val':
#                 val_acc_history.append(epoch_acc)

#         print()

#     time_elapsed = time.time() - since
#     print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
#     print('Best val Acc: {:4f}'.format(best_acc))

#     # load best model weights
#     model.load_state_dict(best_model_wts)
#     return model, val_acc_history









# ###################################################
# # Main
# ###################################################
# # The way to get one batch from the data_loader
# from LoadData import get_data_loader
# if __name__ == "__main__":
#     torch.multiprocessing.freeze_support() #Window 환경에서의 RuntimeError 방지 (DataLoader의 num_workers 관련)

#     print("PyTorch Version: ",torch.__version__)
#     print("Torchvision Version: ",torchvision.__version__)

#     # Detect if we have a GPU available
#     device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

#     # Define argparser
#     parser = argparse.ArgumentParser(description='NeuroImage_Neuron')
#     args, unknown = parser.parse_known_args()


#     """
#     Experiment Parameters
#     """
#     # Top level data directory. Here we assume the format of the directory conforms 
#     #   to the ImageFolder structure
#     def GetUpperDir():
#         return os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
#     args.data_dir = os.path.join(GetUpperDir(), "data/hymenoptera_data")

#     # Models to choose from [resnet, alexnet, vgg, squeezenet, densenet, inception]
#     args.model_name = "squeezenet"

#     # Number of classes in the dataset
#     args.num_classes = 2

#     # Batch size for training (change depending on how much memory you have)
#     args.batch_size = 8
#     args.batch_size = 64

#     # Number of epochs to train for 
#     args.num_epochs = 15

#     # Flag for feature extracting. When False, we finetune the whole model, 
#     #   when True we only update the reshaped layer params
#     args.feature_extract = True




#     # Initialize the model for this run
#     model_ft, input_size = initialize_model(args.model_name, args.num_classes, args.feature_extract, use_pretrained=True)

#     # Print the model we just instantiated
#     print(model_ft)


#     """
#     Load Data
#     """
#     # Data augmentation and normalization for training
#     # Just normalization for validation
#     data_transforms = {
#         'train': transforms.Compose([
#             transforms.RandomResizedCrop(input_size),
#             transforms.RandomHorizontalFlip(),
#             transforms.ToTensor(),
#             transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
#         ]),
#         'val': transforms.Compose([
#             transforms.Resize(input_size),
#             transforms.CenterCrop(input_size),
#             transforms.ToTensor(),
#             transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
#         ]),
#     }

#     print("Initializing Datasets and Dataloaders...")

#     # Create training and validation datasets
#     image_datasets = {x: datasets.ImageFolder(os.path.join(args.data_dir, x), data_transforms[x]) for x in ['train', 'val']}
#     # Create training and validation dataloaders
#     dataloaders_dict = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=args.batch_size, shuffle=True, num_workers=4) for x in ['train', 'val']}

#     # data_loaders = get_data_loader()

#     # for i in range(10):
#     #     batch_x, batch_y = next(iter(data_loaders['test']))
#     #     print(np.shape(batch_x), batch_y)




#     """
#     Create the Optimizer
#     """
#     # Send the model to GPU
#     model_ft = model_ft.to(device)

#     # Gather the parameters to be optimized/updated in this run. If we are
#     #  finetuning we will be updating all parameters. However, if we are 
#     #  doing feature extract method, we will only update the parameters
#     #  that we have just initialized, i.e. the parameters with requires_grad
#     #  is True.
#     params_to_update = model_ft.parameters()
#     print("Params to learn:")
#     if args.feature_extract:
#         params_to_update = []
#         for name,param in model_ft.named_parameters():
#             if param.requires_grad == True:
#                 params_to_update.append(param)
#                 print("\t",name)
#     else:
#         for name,param in model_ft.named_parameters():
#             if param.requires_grad == True:
#                 print("\t",name)

#     # Observe that all parameters are being optimized
#     optimizer_ft = optim.SGD(params_to_update, lr=0.001, momentum=0.9)



#     """"
#     Run Training and Validation Step
#     """
#     # Setup the loss fxn
#     criterion = nn.CrossEntropyLoss()

#     # Train and evaluate
#     model_ft, hist = train_model(model_ft, dataloaders_dict, criterion, optimizer_ft, num_epochs=args.num_epochs, is_inception=(args.model_name=="inception"))




#     # Initialize the non-pretrained version of the model used for this run
#     scratch_model,_ = initialize_model(args.model_name, args.num_classes, feature_extract=False, use_pretrained=False)
#     scratch_model = scratch_model.to(device)
#     scratch_optimizer = optim.SGD(scratch_model.parameters(), lr=0.001, momentum=0.9)
#     scratch_criterion = nn.CrossEntropyLoss()
#     _,scratch_hist = train_model(scratch_model, dataloaders_dict, scratch_criterion, scratch_optimizer, num_epochs=args.num_epochs, is_inception=(args.model_name=="inception"))

#     # Plot the training curves of validation accuracy vs. number 
#     #  of training epochs for the transfer learning method and
#     #  the model trained from scratch
#     ohist = []
#     shist = []

#     ohist = [h.cpu().numpy() for h in hist]
#     shist = [h.cpu().numpy() for h in scratch_hist]

#     plt.title("Validation Accuracy vs. Number of Training Epochs")
#     plt.xlabel("Training Epochs")
#     plt.ylabel("Validation Accuracy")
#     plt.plot(range(1,args.num_epochs+1),ohist,label="Pretrained")
#     plt.plot(range(1,args.num_epochs+1),shist,label="Scratch")
#     plt.ylim((0,1.))
#     plt.xticks(np.arange(1, args.num_epochs+1, 1.0))
#     plt.legend()
#     plt.show()
