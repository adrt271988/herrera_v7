{
    "name" : "Topologia de Venezuela",
    "version": "1.0",
    "depends" : ["base"],
    "author" : "Herrera C.A.",
    "description" : """
    ¿Que hace este módulo?:

        Este módulo se encarga de la topología de venezuela, contiene informacion de todos los estados, 
    municipios, parroquias y sectores de Venezuela con sus códigos postales y codigos de la ciudad.

			""",
    "website" : "http://www.herrera.com.ve",
    "category" : "Topology",
    "init_xml" : [
                    "data/states_ve_data.xml",
                    "data/city_ve_data.xml",
                    "data/municipality_data.xml",
                    "data/ciudades.xml",
        ],
    "demo_xml" : [    ],
    "test": [
    ],
    "update_xml" : [
                    "view/municipality_view.xml",
                    "view/city_view.xml",
                    "view/parish_view.xml",
                    "view/zipcode_view.xml",
                    #~ "view/sector_view.xml",
                    "view/state_view.xml",
                    #~ "security/ir.model.access.csv",
                    "data/zip_code_data.xml"
                    ],
    "active": False,
    "installable": True,
}
