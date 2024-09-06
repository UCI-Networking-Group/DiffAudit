#!/usr/bin/python

'''
This provides the L3 to L1 direct connection from the ontology for data flow analysis/processing.
'''

data_type_categories_ontology_direct = {
        "Name": "Personal Identifiers",
        "Linked Personal Identifiers": "Personal Identifiers",
        "Contact Information": "Personal Identifiers",
        "Reasonably Linkable Personal Identifiers": "Personal Identifiers",
        "Aliases": "Personal Identifiers",
        "Customer Numbers": "Personal Identifiers",
        "Login Information": "Personal Identifiers",

        "Device Hardware Identifiers": "Device Identifiers",
        "Device Software Identifiers": "Device Identifiers",
        "Device Information": "Device Identifiers",

        "Race": "Personal Characteristics",
        "Gender/Sex": "Personal Characteristics",
        "Age": "Personal Characteristics",
        "Language": "Personal Characteristics",
        "Religion": "Personal Characteristics",
        "Marital Status": "Personal Characteristics",
        "Military or veteran status": "Personal Characteristics",
        "Medical Conditions": "Personal Characteristics",
        "Genetic Information": "Personal Characteristics",
        "Disabilities": "Personal Characteristics",
        "Biometrics": "Personal Characteristics",
    
        "Personal History": "Personal History",
        
        "Precise Geolocation": "Geolocation",
        "Coarse Geolocation": "Geolocation",
        "Location Time": "Geolocation",
    
        "User Communications": "User Communications",
        "Contacts": "User Communications",
        "User Internet Activity": "User Communications",
        "Network Connection Information": "User Communications",
    
        "Sensors": "Sensors",
    
        "Products and Advertising": "User Interests and Behaviors",
        "App or Service Usage": "User Interests and Behaviors",
        "Account Settings": "User Interests and Behaviors",
        "Service Information": "User Interests and Behaviors",
        "Inference About Users": "User Interests and Behaviors",
}
