#!/usr/bin/python

'''
This provides the L1 through L3 ontology levels for data flow analysis/processing.
'''

data_type_categories_ontology = {
    "Identifiers": {                    ## level 1 (top most keys)
        "Personal Identifiers": [       ## level 2 (sub keys)
            "Name",                     ## level 3 (in the array)
            "Linked Personal Identifiers",
            "Contact Information",
            "Reasonably Linked Personal Identifiers",
            "Aliases",
            "Customer Numbers",
            "Login Information"
        ],
        "Device Identifiers": [
            "Device Hardware Identifiers",
            "Device Software Identifiers",
            "Device Information" 
        ]
    },
    "Personal Information": {
        "Personal Characteristics": [
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
        ],
        "Personal History": [
            "Personal History"
        ],
        "Geolocation": [
            "Precise Geolocation",
            "Coarse Geolocation",
            "Location Time",
        ],
        "User Communications": [
            "User Communications",
            "Contacts",
            "User Internet Activity",
            "Network Connection Information",
        ],
        "Sensors": [
            "Sensors"
        ],
        "User Interests and Behaviors": [
            "Products and Advertising",
            "App or Service Usage",
            "Account Settings",
            "Service Information",
            "Inference About Users"
        ]
    },
}