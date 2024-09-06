#!/usr/bin/python

'''
This provides the L1 directly to L3 ontology connection (no L2) for data flow analysis/processing.
'''

data_type_categories_ontology_L3_to_L1 = {
    "Identifiers":                     ## level 1 (top most keys)
        [   "Name",                     ## level 3 (in the array)
            "Linked Personal Identifiers",
            "Contact Information",
            "Reasonably Linked Personal Identifiers",
            "Aliases",
            "Customer Numbers",
            "Login Information",
            "Device Hardware Identifiers",
            "Device Software Identifiers",
            "Device Information" 
        ]
    ,
    "Personal Information": [
            "Race",
            "Gender/Sex",
            "Age",
            "Language",
            "Religion",
            "Marital Status",
            "Military or veteran status",
            "Medical Conditions",
            "Genetic Information",
            "Disabilities",
            "Biometrics",
            "Personal History",
            "Precise Geolocation",
            "Coarse Geolocation",
            "Location Time",
            "User Communications",
            "Contacts",
            "User Internet Activity",
            "Network Connection Information",
            "Sensors",
            "Products and Advertising",
            "App or Service Usage",
            "Account Settings",
            "Service Information",
            "Inference About Users"
        ]
}